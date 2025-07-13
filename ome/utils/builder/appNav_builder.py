import json
import os
import sys
import time
from ome.omeMenus import ensure_app_focus
import argparse

# List of roles considered as actionable button-like elements
BUTTON_ROLES = ['AXButton', 'AXMenuButton', 'AXPopUpButton', 'AXCheckBox', 'AXCell']
# Roles to skip entirely (e.g., large tables/lists that are not actionable)
SKIP_ROLES = {'AXTable', 'AXList'}


def extract_omeclick(element):
    """
    Calculate the center point (omeClick) for an element based on its position and size.
    Returns a [x, y] list or None if not available.
    """
    try:
        pos = getattr(element, 'AXPosition', None)
        size = getattr(element, 'AXSize', None)
        if pos and size and isinstance(pos, (list, tuple)) and isinstance(size, (list, tuple)):
            return [float(pos[0]) + float(size[0])/2, float(pos[1]) + float(size[1])/2]
    except Exception:
        pass
    return None


def walk_all_buttons_and_cells(element, path=None, results=None, max_depth=8, depth=0, parent_role=None, parent_desc=None):
    """
    Recursively walk the accessibility tree starting from 'element',
    collecting all actionable button-like elements and their attributes.
    - path: list of steps taken to reach the element (for reconstructing the path)
    - results: list to accumulate found elements
    - max_depth: limits recursion to avoid runaway traversal
    - parent_role/parent_desc: used to annotate child elements with their logical parent
    Returns a list of dicts, each representing a button-like element.
    """
    if results is None:
        results = []
    if path is None:
        path = []
    # Get the role of the current element
    try:
        role = getattr(element, 'AXRole', None)
    except Exception:
        role = None
    # Skip large, non-actionable containers
    if role in SKIP_ROLES:
        return results
    # Get key attributes, handling exceptions gracefully
    try:
        title = getattr(element, 'AXTitle', None)
    except Exception:
        title = None
    try:
        desc = getattr(element, 'AXDescription', None)
    except Exception:
        desc = None
    try:
        help_text = getattr(element, 'AXHelp', None)
    except Exception:
        help_text = None
    try:
        visible = getattr(element, 'AXVisible', None)
    except Exception:
        visible = None
    try:
        focused = getattr(element, 'AXFocused', None)
    except Exception:
        focused = None
    omeClick = extract_omeclick(element)
    entry = None
    # If this element is actionable, build its output dict
    if role in BUTTON_ROLES:
        entry = {
            'path': path,  # The path to reach this element in the tree
            'AXRole': role,
            'title': title,  # AXTitle if available
            'AXHelp': help_text,  # AXHelp if available
            'AXVisible': visible,  # Visibility state
            'AXFocused': focused  # Focused state
        }
        # If the parent is an AXCell with a description, annotate this element with its parent
        if parent_role == 'AXCell' and parent_desc:
            entry['parent_description'] = parent_desc
        entry['description'] = desc  # AXDescription if available
        entry['omeClick'] = omeClick  # Center point for clicking (if available)
        results.append(entry)
    # Recurse into children if not too deep
    if depth < max_depth:
        try:
            children = getattr(element, 'AXChildren', [])
            for idx, child in enumerate(children):
                # Build the path for the child
                try:
                    child_title = getattr(child, 'AXTitle', None)
                except Exception:
                    child_title = None
                child_path = path + [child_title] if child_title else path + [f"Child_{idx}"]
                # Pass current role/desc as parent_role/parent_desc for the child
                walk_all_buttons_and_cells(child, child_path, results, max_depth, depth+1, parent_role=role, parent_desc=desc)
        except Exception:
            pass
    return results


def build_toolbar_jsonl(bundle_id, out_path=None):
    """
    Main entry point: Focus the app, get the focused window, walk the tree,
    and write all actionable elements to a JSONL file.
    - bundle_id: the app's bundle identifier (e.g., 'com.apple.mail')
    - out_path: optional output path for the JSONL file
    """
    start_time = time.time()  # Start timer
    app = ensure_app_focus(bundle_id)
    try:
        window = app.AXFocusedWindow
    except Exception:
        print("Could not get focused window.")
        return
    window_title = getattr(window, 'AXTitle', None) or 'Window'
    # Start walking from the window root, path starts with window title
    all_buttons = walk_all_buttons_and_cells(window, [window_title])
    print(f"Found {len(all_buttons)} button-like elements in the window.")
    if out_path is None:
        out_path = f"ome/data/navigation/appNav_{bundle_id}.jsonl"
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    seen_keys = set()  # Used for deduplication
    with open(out_path, 'w', encoding='utf-8') as f:
        for item in all_buttons:
            # Skip entries with no title and no description
            if not (item.get('title') or item.get('description')):
                continue
            # Deduplicate by (description, path) and (title, path)
            desc = item.get('description')
            title = item.get('title')
            path_tuple = tuple(item.get('path', []))
            key_desc = (desc, path_tuple) if desc else None
            key_title = (title, path_tuple) if title else None
            if key_desc and key_desc in seen_keys:
                continue
            if key_title and key_title in seen_keys:
                continue
            if key_desc:
                seen_keys.add(key_desc)
            if key_title:
                seen_keys.add(key_title)
            # Remove all attributes with None values for clean output
            clean_item = {k: v for k, v in item.items() if v is not None}
            f.write(json.dumps(clean_item, ensure_ascii=False) + '\n')
    print(f"Button JSONL written to {out_path}")
    elapsed = time.time() - start_time
    print(f"Toolbar build completed in {elapsed:.2f} seconds.")


if __name__ == '__main__':
    # Parse command-line arguments for bundle id and output path
    parser = argparse.ArgumentParser(description="Build a JSONL of all button-like elements in a window for a given app bundle ID.")
    parser.add_argument('--bundle', type=str, default='com.apple.mail', nargs='?', help='App bundle ID (default: com.apple.mail)')
    parser.add_argument('--out', type=str, default=None, help='Output JSONL path (optional)')
    args = parser.parse_args()
    build_toolbar_jsonl(args.bundle, args.out) 