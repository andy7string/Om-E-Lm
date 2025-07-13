# ome/utils/builder/window_builder.py
# Window builder for Om-E-Mac: scans app windows and outputs window JSONLs.
import os
import json
import time
from typing import List, Dict, Optional
from ome._a11y import ErrorUnsupported, ErrorCannotComplete, ErrorAPIDisabled, ErrorInvalidUIElement
import ome
from ome.omeMenus import ensure_app_focus

# === Main Scan Functions ===
def build_window(bundle_id: str, window_id: str = None, fullscreen: bool = True, regions: Optional[List[str]] = None) -> List[Dict]:
    """
    Canonical window builder for Om-E-Mac.
    Scans actionable UI elements in the current window for the given app (by bundle_id), outputs a JSONL, and returns a list.
    window_id: Optional identifier for the window (AXTitle or generated)
    fullscreen: If True, puts the window in fullscreen before scanning
    regions: List of AXRole regions to scan (default: ['AXToolbar', 'AXSidebar']).
        Pass regions=['AXToolbar'] to exclude the sidebar.
    Prints start and end time for performance measurement.
    """
    from ome.utils.env.env import MENU_EXPORT_DIR
    start_time = time.time()
    print(f"[window_builder] Scan started at {time.strftime('%X', time.localtime(start_time))}")
    # Ensure the app is running and focused
    app = ensure_app_focus(bundle_id, fullscreen=fullscreen)
    if regions is None:
        regions = ['AXToolbar', 'AXSidebar']
    exclude_roles = {'AXSplitter', 'AXStaticText', 'AXImage', 'AXScrollArea'}
    skip_deep_roles = {'AXTable', 'AXOutline', 'AXRow', 'AXCell'}
    try:
        window = app.AXFocusedWindow
    except Exception:
        window = app.AXWindows[0] if hasattr(app, 'AXWindows') and app.AXWindows else None
    if not window:
        raise RuntimeError("No window found for app.")
    win_title = getattr(window, 'AXTitle', None)
    window_id = window_id or (win_title if win_title else 'main')
    output_dir = os.path.join(MENU_EXPORT_DIR, '..', 'windows')
    os.makedirs(output_dir, exist_ok=True)
    safe_title = str(window_id).replace(' ', '_').replace('/', '_')
    output_path = os.path.join(output_dir, f"window_{bundle_id}_{safe_title}.jsonl")

    def get_navigation_attributes(element, path):
        attrs = {
            'path': path,
            'AXRole': None,
            'AXSubrole': None,
            'AXRoleDescription': None,
            'AXIdentifier': None,
            'AXEnabled': None,
            'title': None,
            'description': None,
            'center': None,
        }
        # Robust attribute access
        try:
            attrs['AXRole'] = getattr(element, 'AXRole', None)
        except Exception:
            pass
        try:
            attrs['AXSubrole'] = getattr(element, 'AXSubrole', None)
        except Exception:
            pass
        try:
            attrs['AXRoleDescription'] = getattr(element, 'AXRoleDescription', None)
        except Exception:
            pass
        try:
            attrs['AXIdentifier'] = getattr(element, 'AXIdentifier', None)
        except Exception:
            pass
        try:
            attrs['AXEnabled'] = getattr(element, 'AXEnabled', None)
        except Exception:
            pass
        # Title/description mapping
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
        if title:
            attrs['title'] = title
        elif desc:
            attrs['title'] = desc
        if help_text:
            attrs['description'] = help_text
        elif desc and not attrs.get('description'):
            attrs['description'] = desc
        # Center
        try:
            pos = getattr(element, 'AXPosition', None)
            size = getattr(element, 'AXSize', None)
            if pos and size and isinstance(pos, (list, tuple)) and isinstance(size, (list, tuple)):
                attrs['center'] = [float(pos[0]) + float(size[0])/2, float(pos[1]) + float(size[1])/2]
        except Exception:
            pass
        # Remove null/empty values
        return {k: v for k, v in attrs.items() if v not in (None, '', [])}

    def is_editable_body(element):
        try:
            role = getattr(element, 'AXRole', None)
            value = getattr(element, 'AXValue', None)
            title = getattr(element, 'AXTitle', None)
            desc = getattr(element, 'AXDescription', None)
            # Heuristic: WebArea or Group/Unknown with AXValue and no title/desc
            if role in {'AXWebArea', 'AXGroup', 'AXUnknown'} and value is not None and not title and not desc:
                return True
        except Exception:
            pass
        return False

    def walk_window(element, path=None, results=None, max_depth=5, depth=0, parent_role=None):
        if results is None:
            results = []
        if path is None:
            path = []
        # Safely get role and title
        try:
            role = getattr(element, 'AXRole', None)
        except Exception:
            role = None
        try:
            title = getattr(element, 'AXTitle', None)
        except Exception:
            title = None
        actionable_roles = {
            'AXButton', 'AXToolbar', 'AXSidebar', 'AXTextField', 'AXMenuButton',
            'AXPopUpButton', 'AXComboBox', 'AXWebArea', 'AXTextArea'
        }
        container_roles = {'AXToolbar', 'AXSidebar'}
        # Only output actionable elements, top-level containers, or editable body
        if role in actionable_roles or (role in container_roles and depth == 0) or is_editable_body(element):
            node = get_navigation_attributes(element, path)
            results.append(node)
        # Always walk through containers, actionable, or root
        if role in {'AXSplitGroup', 'AXGroup'} or depth == 0 or role in container_roles:
            try:
                children = getattr(element, 'AXChildren', [])
                if not isinstance(children, list):
                    children = []
            except Exception:
                children = []
            for idx, child in enumerate(children):
                if not hasattr(child, 'AXRole'):
                    continue
                try:
                    child_title = getattr(child, 'AXTitle', None)
                except Exception:
                    child_title = None
                child_path = path + [child_title] if child_title else path + [f"Child_{idx}"]
                try:
                    walk_window(child, child_path, results, max_depth, depth+1, parent_role=role)
                except Exception as e:
                    print(f"  Error walking child {idx}: {e}")
        return results

    all_results = walk_window(window, path=[window_id], results=[], max_depth=5, depth=0)
    with open(output_path, 'w', encoding='utf-8') as f:
        for item in all_results:
            f.write(json.dumps(item, ensure_ascii=False) + '\n')
    end_time = time.time()
    print(f"[window_builder] Scan ended at {time.strftime('%X', time.localtime(end_time))} (duration: {end_time - start_time:.2f}s)")
    return all_results

def scan_window_region(bundle_id: str, region: str, window_id: str = None) -> List[Dict]:
    """
    Scans only a specific region (e.g., 'toolbar', 'sidebar', 'main') of the current window.
    Updates the window JSONL incrementally.
    Returns the list of scanned elements for the region.
    """
    pass

def update_window_jsonl(window_id: str, updates: List[Dict]):
    """
    Updates the window JSONL with new/changed elements.
    Archives the previous version for rollback/debugging.
    """
    pass 