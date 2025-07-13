import json
import os
import sys
import time
from ome.omeMenus import ensure_app_focus
import argparse

BUTTON_ROLES = ['AXButton', 'AXMenuButton', 'AXPopUpButton', 'AXCheckBox', 'AXCell']
SKIP_ROLES = {'AXTable', 'AXList'}


def extract_omeclick(element):
    try:
        pos = getattr(element, 'AXPosition', None)
        size = getattr(element, 'AXSize', None)
        if pos and size and isinstance(pos, (list, tuple)) and isinstance(size, (list, tuple)):
            return [float(pos[0]) + float(size[0])/2, float(pos[1]) + float(size[1])/2]
    except Exception:
        pass
    return None


def walk_all_buttons_and_cells(element, path=None, results=None, max_depth=8, depth=0, parent_role=None, parent_desc=None, grandparent_role=None, grandparent_desc=None):
    if results is None:
        results = []
    if path is None:
        path = []
    try:
        role = getattr(element, 'AXRole', None)
    except Exception:
        role = None
    # SKIP message list panels
    if role in SKIP_ROLES:
        return results
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
    omeClick = extract_omeclick(element)
    entry = None
    if role in BUTTON_ROLES:
        entry = {
            'path': path,
            'AXRole': role,
            'title': title,
            'AXHelp': help_text
        }
        # If grandparent is AXCell and has a description, add grandparent_description before parent_description
        if grandparent_role == 'AXCell' and grandparent_desc:
            entry['grandparent_description'] = grandparent_desc
        # If parent is AXCell and has a description, add parent_description before description
        if parent_role == 'AXCell' and parent_desc:
            entry['parent_description'] = parent_desc
        entry['description'] = desc
        entry['omeClick'] = omeClick  # Always add omeClick last
        results.append(entry)
    # Recurse into children
    if depth < max_depth:
        try:
            children = getattr(element, 'AXChildren', [])
            for idx, child in enumerate(children):
                try:
                    child_title = getattr(child, 'AXTitle', None)
                except Exception:
                    child_title = None
                child_path = path + [child_title] if child_title else path + [f"Child_{idx}"]
                # Pass current and parent role/desc as parent/grandparent for child
                walk_all_buttons_and_cells(child, child_path, results, max_depth, depth+1, parent_role=role, parent_desc=desc, grandparent_role=parent_role, grandparent_desc=parent_desc)
        except Exception:
            pass
    return results


def build_toolbar_jsonl(bundle_id, out_path=None):
    app = ensure_app_focus(bundle_id)
    try:
        window = app.AXFocusedWindow
    except Exception:
        print("Could not get focused window.")
        return
    window_title = getattr(window, 'AXTitle', None) or 'Window'
    all_buttons = walk_all_buttons_and_cells(window, [window_title])
    print(f"Found {len(all_buttons)} button-like elements in the window.")
    if out_path is None:
        out_path = f"ome/data/windows/window_{bundle_id}_toolbar.jsonl"
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    seen_keys = set()
    with open(out_path, 'w', encoding='utf-8') as f:
        for item in all_buttons:
            if not (item.get('title') or item.get('description')):
                continue  # Skip entries with no title and no description
            # Use (description, tuple(path)) and (title, tuple(path)) as deduplication keys
            desc = item.get('description')
            title = item.get('title')
            path_tuple = tuple(item.get('path', []))
            key_desc = (desc, path_tuple) if desc else None
            key_title = (title, path_tuple) if title else None
            if key_desc and key_desc in seen_keys:
                continue  # Skip duplicate description+path
            if key_title and key_title in seen_keys:
                continue  # Skip duplicate title+path
            if key_desc:
                seen_keys.add(key_desc)
            if key_title:
                seen_keys.add(key_title)
            # Remove all attributes with None values
            clean_item = {k: v for k, v in item.items() if v is not None}
            f.write(json.dumps(clean_item, ensure_ascii=False) + '\n')
    print(f"Button JSONL written to {out_path}")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Build a JSONL of all button-like elements in a window for a given app bundle ID.")
    parser.add_argument('--bundle', type=str, default='com.apple.mail', help='App bundle ID (default: com.apple.mail)')
    parser.add_argument('--out', type=str, default=None, help='Output JSONL path (optional)')
    args = parser.parse_args()
    build_toolbar_jsonl(args.bundle, args.out) 