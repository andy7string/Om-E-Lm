# omeMenus.py - Dedicated menu helpers for OME
import ome
import ome.cleanup
import time
import os
import json
from ome.utils.env.env import MENU_EXPORT_DIR
from ome.utils.env import env
from ome._a11y import ErrorUnsupported, ErrorCannotComplete, ErrorAPIDisabled, ErrorInvalidUIElement


WINDOW_MAXIMIZE_DELAY = env.WINDOW_MAXIMIZE_DELAY
RETRY_DELAY = env.RETRY_DELAY

def scan_children(element, filters=None, depth=1, parent_path=None):
    filters = filters or {}
    children = []
    try:
        ax_children = getattr(element, "AXChildren", [])
    except (ErrorUnsupported, ErrorCannotComplete, ErrorAPIDisabled, ErrorInvalidUIElement, AttributeError):
        return children
    for child in ax_children:
        try:
            role = getattr(child, "AXRole", None)
            title = getattr(child, "AXTitle", None)
        except (ErrorUnsupported, ErrorCannotComplete, ErrorAPIDisabled, ErrorInvalidUIElement, AttributeError):
            continue
        if role in filters.get("exclude_roles", []) or title in filters.get("exclude_titles", []):
            continue
        child_path = (parent_path or []) + [title]
        meta = {
            "path": child_path,
            "role": role,
            "has_children": False,
            "children": [],
            "coords": None,
            "active": None
        }
        try:
            meta["has_children"] = bool(getattr(child, "AXChildren", []))
        except (ErrorUnsupported, ErrorCannotComplete, ErrorAPIDisabled, ErrorInvalidUIElement, AttributeError):
            pass
        try:
            meta["coords"] = getattr(child, "AXPosition", None)
        except (ErrorUnsupported, ErrorCannotComplete, ErrorAPIDisabled, ErrorInvalidUIElement, AttributeError):
            pass
        try:
            meta["active"] = getattr(child, "AXEnabled", None)
        except (ErrorUnsupported, ErrorCannotComplete, ErrorAPIDisabled, ErrorInvalidUIElement, AttributeError):
            pass
        if depth > 1 and meta["has_children"]:
            meta["children"] = scan_children(child, filters, depth-1, child_path)
        children.append(meta)
    return children

def find_json_node(jsonl, path):
    def _find(node, path):
        if node["path"] == path:
            return node
        for child in node.get("children", []):
            found = _find(child, path)
            if found:
                return found
        return None
    for node in jsonl:
        found = _find(node, path)
        if found:
            return found
    return None

def update_jsonl_with_children(jsonl, path, children):
    node = find_json_node(jsonl, path)
    if node:
        node["children"] = children
    else:
        jsonl.append({
            "path": path,
            "children": children
        })

def extract_menu_metadata(menu_item, path):
    try:
        title = getattr(menu_item, 'AXTitle', None)
        role = getattr(menu_item, 'AXRole', None)
        enabled = getattr(menu_item, 'AXEnabled', True)
        children = getattr(menu_item, 'AXChildren', [])
        has_children = bool(children)
        coords = getattr(menu_item, 'AXPosition', None)
        active = enabled
    except (ErrorUnsupported, ErrorCannotComplete, ErrorAPIDisabled, ErrorInvalidUIElement, AttributeError):
        title = role = coords = None
        has_children = False
        active = False
        children = []
    return {
        "path": path,
        "title": title,
        "role": role,
        "has_children": has_children,
        "coords": coords,
        "active": active
    }

def traverse_menu_to_json(menu_item, path=[]):
    items = []
    meta = extract_menu_metadata(menu_item, path)
    items.append(meta)
    try:
        children = getattr(menu_item, 'AXChildren', [])
    except (ErrorUnsupported, ErrorCannotComplete, ErrorAPIDisabled, ErrorInvalidUIElement, AttributeError):
        children = []
    if len(children) == 1 and getattr(children[0], 'AXRole', None) == 'AXMenu':
        try:
            children = getattr(children[0], 'AXChildren', [])
        except (ErrorUnsupported, ErrorCannotComplete, ErrorAPIDisabled, ErrorInvalidUIElement, AttributeError):
            children = []
    for child in children:
        try:
            child_title = getattr(child, 'AXTitle', None)
        except (ErrorUnsupported, ErrorCannotComplete, ErrorAPIDisabled, ErrorInvalidUIElement, AttributeError):
            child_title = None
        child_path = path + [child_title] if child_title else path + ["<no title>"]
        items.extend(traverse_menu_to_json(child, child_path))
    return items

def export_menu_attributes(bundle_id, output_path=None, filters=None):
    """
    Export all menu attributes for the given app bundle_id to a JSONL file.
    - bundle_id: str, e.g. 'com.apple.mail'
    - output_path: str or None. If None, uses MENU_EXPORT_DIR/menu_attributes_{bundle_id}.jsonl
    - filters: dict or None. If None, uses default filter logic (exclude certain attrs, etc.)
    """
    import ome
    import time
    from ome._a11y import ErrorUnsupported, ErrorCannotComplete, ErrorAPIDisabled, ErrorInvalidUIElement

    # Default filters (from test_menu_attributes_jsonl.py)
    EXCLUDE_ATTRS = {
        'AXFrame', 'AXParent', 'AXTopLevelMenuBar', 'AXTopLevelUIElement',
        'AXServesAsTitleForUIElements', 'AXSubrole', 'AXSelected', 'AXFocused',
        'AXAlternateUIVisible',
    }
    RENAME_ATTRS = {
        'AXRoleDescription': 'AXDescription',
        'AXMenuItemCmdModifiers': 'ShortModifier',
        'AXMenuItemCmdChar': 'ShortKey',
    }
    SPECIAL_VALUE_ATTRS = {
        'AXMenuItemPrimaryUIElement': True,
    }
    REMOVE_ATTRS = {
        'AXMenuItemPrimaryUIElement', 'AXRole', 'AXMenuItemCmdGlyph', 'AXChildren'
    }
    DEFAULT_POSITION = [0.0, 1440.0]
    MODIFIER_MAP = {
        0: '', 1: '⇧', 2: '⌃', 4: '⌥', 8: '⌘', 10: '⌃⌘', 12: '⌥⌘', 9: '⇧⌘', 5: '⇧⌥', 3: '⇧⌃', 6: '⌃⌥', 24: '⌘⇧⌥', 28: '⌘⌥⇧', 13: '⇧⌃⌘', 14: '⌃⌥⌘', 15: '⇧⌃⌥⌘',
    }
    if filters is None:
        filters = dict(
            EXCLUDE_ATTRS=EXCLUDE_ATTRS,
            RENAME_ATTRS=RENAME_ATTRS,
            SPECIAL_VALUE_ATTRS=SPECIAL_VALUE_ATTRS,
            REMOVE_ATTRS=REMOVE_ATTRS,
            DEFAULT_POSITION=DEFAULT_POSITION,
            MODIFIER_MAP=MODIFIER_MAP,
        )

    def get_all_attributes(element):
        try:
            attr_names = element.getAttributes() if hasattr(element, 'getAttributes') else element._getAttributes()
        except Exception as e:
            return {"error": f"Could not get attribute names: {e}"}
        attrs = {}
        for attr in attr_names:
            if attr in filters['EXCLUDE_ATTRS'] or attr in filters['REMOVE_ATTRS']:
                continue
            try:
                value = element._getAttribute(attr)
                if value is None:
                    continue
                if attr in filters['RENAME_ATTRS']:
                    out_attr = filters['RENAME_ATTRS'][attr]
                elif attr in filters['SPECIAL_VALUE_ATTRS']:
                    out_attr = attr
                    value = repr(value)
                else:
                    out_attr = attr
                try:
                    json.dumps(value)
                except TypeError:
                    value = repr(value)
                attrs[out_attr] = value
            except Exception:
                continue
        # Add AXHelp if available
        try:
            help_value = element._getAttribute('AXHelp')
            if help_value:
                attrs['AXHelp'] = help_value
        except Exception:
            pass
        # Title logic
        title = attrs.get('AXTitle')
        if not title:
            title = attrs.get('AXDescription', '<no title>')
        attrs.pop('AXTitle', None)
        attrs.pop('AXDescription', None)
        menu_path = attrs.pop('menu_path', None)
        pos = attrs.pop('AXPosition', None)
        size = attrs.pop('AXSize', None)
        omeClick = None
        if (
            pos and size and
            isinstance(pos, (list, tuple)) and isinstance(size, (list, tuple)) and
            pos != filters['DEFAULT_POSITION'] and size != [0.0, 0.0]
        ):
            try:
                omeClick = [float(pos[0]) + float(size[0])/2, float(pos[1]) + float(size[1])/2]
            except Exception:
                omeClick = None
        clean_attrs = {k: v for k, v in attrs.items() if v is not None}
        out = {}
        out['title'] = title
        out['menu_path'] = menu_path
        if omeClick and omeClick != filters['DEFAULT_POSITION']:
            out['omeClick'] = omeClick
        short_mod = clean_attrs.get('ShortModifier')
        if short_mod is not None:
            out['shortcut_modifiers'] = filters['MODIFIER_MAP'].get(short_mod, str(short_mod))
        if 'AXIdentifier' in clean_attrs:
            out['AXIdentifier'] = clean_attrs.pop('AXIdentifier')
        if 'AXHelp' in clean_attrs:
            out['AXHelp'] = clean_attrs.pop('AXHelp')
        out.update(clean_attrs)
        return out

    def safe_get_title(element):
        for attr in ["AXTitle", "AXDescription"]:
            try:
                value = element._getAttribute(attr)
                if value:
                    return value
            except Exception:
                continue
        return "<no title>"

    def walk_menu(element, path=None, results=None, max_depth=10, depth=0):
        if results is None:
            results = []
        if path is None:
            path = []
        attrs = get_all_attributes(element)
        attrs['menu_path'] = list(path)
        # --- Add child_count and children_titles if this node has children ---
        try:
            children = getattr(element, 'AXChildren', [])
            if children is None:
                children = []
        except Exception:
            children = []
        # If the only child is an AXMenu container, descend into it
        if isinstance(children, list) and len(children) == 1 and getattr(children[0], 'AXRole', None) == 'AXMenu':
            try:
                subchildren = getattr(children[0], 'AXChildren', [])
                if subchildren is None:
                    subchildren = []
                children = subchildren
            except Exception:
                children = []
        # Add child_count and children_titles if there are children
        if children:
            attrs['child_count'] = len(children)
            attrs['children_titles'] = []
            for child in children:
                try:
                    title = safe_get_title(child)
                except Exception:
                    title = '<no title>'
                attrs['children_titles'].append(title)
        results.append(attrs)
        if depth < max_depth:
            for child in children:
                title = safe_get_title(child)
                walk_menu(child, path + [title], results, max_depth, depth+1)
        return results

    app = ome.getAppRefByBundleId(bundle_id)
    menu_bar = app.AXMenuBar
    app_menus = getattr(menu_bar, 'AXChildren', [])[1:]
    all_results = []
    for parent in app_menus:
        title = safe_get_title(parent)
        try:
            parent.Press()
            time.sleep(0.4)
        except Exception:
            pass
        walk_menu(parent, path=[title], results=all_results)
    if output_path is None:
        os.makedirs(MENU_EXPORT_DIR, exist_ok=True)
        output_path = os.path.join(MENU_EXPORT_DIR, f"menu_attributes_{bundle_id}.jsonl")
    with open(output_path, 'w', encoding='utf-8') as f:
        for item in all_results:
            f.write(json.dumps(item, ensure_ascii=False) + '\n')
    return output_path

def resolve_ui_element_by_path(path, bundle_id):
    """
    Traverse the menu hierarchy for the given path and bundle_id.
    Presses each parent menu item (except the last) to ensure submenus are open.
    Returns the final menu item UI element (do not press it here).
    """
    import time
    app = ome.getAppRefByBundleId(bundle_id)
    menu_bar = app.AXMenuBar
    current = menu_bar
    for i, title in enumerate(path[1:]):  # skip the app name at path[0]
        children = getattr(current, 'AXChildren', [])
        if len(children) == 1 and getattr(children[0], 'AXRole', None) == 'AXMenu':
            children = getattr(children[0], 'AXChildren', [])
        found = None
        for child in children:
            if getattr(child, 'AXTitle', None) == title:
                found = child
                break
        if not found:
            return None
        # Press parent menu items to open submenus, except for the last item
        if i < len(path[1:]) - 1:
            try:
                found.Press()
                time.sleep(RETRY_DELAY)
            except Exception:
                pass
        current = found
    return current

def load_menu_jsonl(jsonl_path):
    """
    Load a menu JSONL file and return a list of dicts (one per menu item).
    """
    items = []
    with open(jsonl_path, 'r', encoding='utf-8') as f:
        for line in f:
            items.append(json.loads(line))
    return items

def find_paths_by_title(jsonl, title):
    """
    Return a list of menu paths for all items with the given title.
    Handles duplicates by returning all matches.
    """
    paths = []
    for item in jsonl:
        if item.get('title') == title and 'menu_path' in item:
            paths.append(item['menu_path'])
    return paths

def save_menu_jsonl(jsonl, path):
    """
    Write the in-memory JSONL list back to disk.
    """
    with open(path, 'w', encoding='utf-8') as f:
        for item in jsonl:
            f.write(json.dumps(item, ensure_ascii=False) + '\n')

def navigate_and_press_by_title(jsonl, title, bundle_id, fullscreen=True):
    """
    Find all menu paths for a given title, press the first one found, and return the result.
    Returns (success, paths) where paths is the list of all found paths.
    """
    paths = find_paths_by_title(jsonl, title)
    if not paths:
        return False, []
    from ome.omeMenus import press_menu_path
    success = press_menu_path(paths[0], bundle_id, fullscreen=fullscreen)
    return success, paths

def menu_jsonl_orchestrator(jsonl_path, title, bundle_id, update_dict=None, save_path=None, fullscreen=True):
    """
    High-level example orchestration for JSONL-driven menu navigation and update.
    - Loads the JSONL file.
    - Finds all menu paths for the given title.
    - Navigates and presses the first found path.
    - Optionally updates the node with new info (update_dict).
    - Optionally saves the updated JSONL back to disk.
    
    Args:
        jsonl_path (str): Path to the JSONL file.
        title (str): Menu item title to search for.
        bundle_id (str): App bundle id.
        update_dict (dict, optional): Dict of updates to apply to the found node.
        save_path (str, optional): Where to save the updated JSONL (defaults to jsonl_path).
        fullscreen (bool): Whether to try to full screen the app before pressing.
    Returns:
        dict: Results including pressed status, found paths, and updated node (if any).
    """
    # 1. Load the JSONL file into memory
    menu_json = load_menu_jsonl(jsonl_path)

    # 2. Find all menu paths for the given title
    paths = find_paths_by_title(menu_json, title)
    if not paths:
        return {'pressed': False, 'paths': [], 'updated_node': None}

    # 3. Navigate and press the first matching menu item
    pressed = False
    from ome.omeMenus import press_menu_path
    pressed = press_menu_path(paths[0], bundle_id, fullscreen=fullscreen)

    # 4. Optionally update the in-memory JSONL node
    updated_node = None
    if update_dict:
        node = find_json_node(menu_json, paths[0])
        if node:
            node.update(update_dict)
            updated_node = node

    # 5. Optionally save the updated JSONL back to disk
    if update_dict and (save_path or save_path is None):
        save_menu_jsonl(menu_json, save_path or jsonl_path)

    # 6. Return results for inspection
    return {
        'pressed': pressed,
        'paths': paths,
        'updated_node': updated_node
    }

def press_menu_path(menu_path, bundle_id, fullscreen=True):
    """
    Focus the app, optionally enter fullscreen, resolve the menu item by path, and press it.
    Returns True if successful, False otherwise.
    """
    import ome
    try:
        app = ome.getAppRefByBundleId(bundle_id)
        if fullscreen and hasattr(app, 'AXWindows'):
            try:
                win = app.AXWindows[0]
                if hasattr(win, 'AXFullScreen') and not getattr(win, 'AXFullScreen', False):
                    setattr(win, 'AXFullScreen', True)
            except Exception:
                pass
        # Removed Cancel() to avoid closing the menu before scanning
        menu_item = resolve_ui_element_by_path([app.getLocalizedName()] + menu_path, bundle_id)
        if menu_item is None:
            return False
        menu_item.Press()
        return True
    except Exception:
        return False

def ensure_app_focus(bundle_id, fullscreen=False):
    """
    Launches or focuses the app with the given bundle_id, brings it to the foreground, and maximizes the window if possible (if fullscreen=True). Returns the app reference.
    """
    import ome
    import time
    app = ome.getAppRefByBundleId(bundle_id)
    try:
        if not app.isFrontmost():
            app.activate()
            time.sleep(0.3)
    except Exception:
        app.activate()
        time.sleep(0.3)
    # Try to maximize (full screen) the frontmost window if possible
    if fullscreen:
        try:
            if hasattr(app, 'AXWindows'):
                win = app.AXWindows[0]
                if hasattr(win, 'AXFullScreen') and not getattr(win, 'AXFullScreen', False):
                    setattr(win, 'AXFullScreen', True)
                    time.sleep(1.0)
        except Exception:
            pass
    return app

def export_menu_attributes_from_element(element, output_path=None, filters=None, path=None):
    """
    Recursively walk the menu starting from the given element (e.g., 'Services') and export all attributes to a JSONL file.
    If output_path is None, print the results to the terminal instead of saving.
    - element: The menu item to start from (AXUIElement)
    - output_path: Path to save JSONL, or None to print
    - filters: Attribute filters (same as export_menu_attributes)
    - path: Path to the current element (list of titles)
    """
    import json
    import time
    from ome._a11y import ErrorUnsupported, ErrorCannotComplete, ErrorAPIDisabled, ErrorInvalidUIElement

    # Default filters (copied from export_menu_attributes)
    EXCLUDE_ATTRS = {
        'AXFrame', 'AXParent', 'AXTopLevelMenuBar', 'AXTopLevelUIElement',
        'AXServesAsTitleForUIElements', 'AXSubrole', 'AXSelected', 'AXFocused',
        'AXAlternateUIVisible',
    }
    RENAME_ATTRS = {
        'AXRoleDescription': 'AXDescription',
        'AXMenuItemCmdModifiers': 'ShortModifier',
        'AXMenuItemCmdChar': 'ShortKey',
    }
    SPECIAL_VALUE_ATTRS = {
        'AXMenuItemPrimaryUIElement': True,
    }
    REMOVE_ATTRS = {
        'AXMenuItemPrimaryUIElement', 'AXRole', 'AXMenuItemCmdGlyph', 'AXChildren'
    }
    DEFAULT_POSITION = [0.0, 1440.0]
    MODIFIER_MAP = {
        0: '', 1: '⇧', 2: '⌃', 4: '⌥', 8: '⌘', 10: '⌃⌘', 12: '⌥⌘', 9: '⇧⌘', 5: '⇧⌥', 3: '⇧⌃', 6: '⌃⌥', 24: '⌘⇧⌥', 28: '⌘⌥⇧', 13: '⇧⌃⌘', 14: '⌃⌥⌘', 15: '⇧⌃⌥⌘',
    }
    if filters is None:
        filters = dict(
            EXCLUDE_ATTRS=EXCLUDE_ATTRS,
            RENAME_ATTRS=RENAME_ATTRS,
            SPECIAL_VALUE_ATTRS=SPECIAL_VALUE_ATTRS,
            REMOVE_ATTRS=REMOVE_ATTRS,
            DEFAULT_POSITION=DEFAULT_POSITION,
            MODIFIER_MAP=MODIFIER_MAP,
        )

    def get_all_attributes(element):
        try:
            attr_names = element.getAttributes() if hasattr(element, 'getAttributes') else element._getAttributes()
        except Exception as e:
            return {"error": f"Could not get attribute names: {e}"}
        attrs = {}
        for attr in attr_names:
            if attr in filters['EXCLUDE_ATTRS'] or attr in filters['REMOVE_ATTRS']:
                continue
            try:
                value = element._getAttribute(attr)
                if value is None:
                    continue
                if attr in filters['RENAME_ATTRS']:
                    out_attr = filters['RENAME_ATTRS'][attr]
                elif attr in filters['SPECIAL_VALUE_ATTRS']:
                    out_attr = attr
                    value = repr(value)
                else:
                    out_attr = attr
                try:
                    json.dumps(value)
                except TypeError:
                    value = repr(value)
                attrs[out_attr] = value
            except Exception:
                continue
        # Add AXHelp if available
        try:
            help_value = element._getAttribute('AXHelp')
            if help_value:
                attrs['AXHelp'] = help_value
        except Exception:
            pass
        # Title logic
        title = attrs.get('AXTitle')
        if not title:
            title = attrs.get('AXDescription', '<no title>')
        attrs.pop('AXTitle', None)
        attrs.pop('AXDescription', None)
        menu_path = attrs.pop('menu_path', None)
        pos = attrs.pop('AXPosition', None)
        size = attrs.pop('AXSize', None)
        omeClick = None
        if (
            pos and size and
            isinstance(pos, (list, tuple)) and isinstance(size, (list, tuple)) and
            pos != filters['DEFAULT_POSITION'] and size != [0.0, 0.0]
        ):
            try:
                omeClick = [float(pos[0]) + float(size[0])/2, float(pos[1]) + float(size[1])/2]
            except Exception:
                omeClick = None
        clean_attrs = {k: v for k, v in attrs.items() if v is not None}
        out = {}
        out['title'] = title
        out['menu_path'] = menu_path if menu_path is not None else (path or [])
        if omeClick and omeClick != filters['DEFAULT_POSITION']:
            out['omeClick'] = omeClick
        short_mod = clean_attrs.get('ShortModifier')
        if short_mod is not None:
            out['shortcut_modifiers'] = filters['MODIFIER_MAP'].get(short_mod, str(short_mod))
        if 'AXIdentifier' in clean_attrs:
            out['AXIdentifier'] = clean_attrs.pop('AXIdentifier')
        if 'AXHelp' in clean_attrs:
            out['AXHelp'] = clean_attrs.pop('AXHelp')
        out.update(clean_attrs)
        return out

    def safe_get_title(element):
        for attr in ["AXTitle", "AXDescription"]:
            try:
                value = element._getAttribute(attr)
                if value:
                    return value
            except Exception:
                continue
        return "<no title>"

    def walk_menu(element, path=None, results=None, max_depth=10, depth=0):
        if results is None:
            results = []
        if path is None:
            path = []
        attrs = get_all_attributes(element)
        attrs['menu_path'] = list(path)
        # --- Add child_count and children_titles if this node has children ---
        try:
            children = getattr(element, 'AXChildren', [])
            if children is None:
                children = []
        except Exception:
            children = []
        # If the only child is an AXMenu container, descend into it
        if isinstance(children, list) and len(children) == 1 and getattr(children[0], 'AXRole', None) == 'AXMenu':
            try:
                subchildren = getattr(children[0], 'AXChildren', [])
                if subchildren is None:
                    subchildren = []
                children = subchildren
            except Exception:
                children = []
        # Add child_count and children_titles if there are children
        if children:
            attrs['child_count'] = len(children)
            attrs['children_titles'] = []
            for child in children:
                try:
                    title = safe_get_title(child)
                except Exception:
                    title = '<no title>'
                attrs['children_titles'].append(title)
        results.append(attrs)
        if depth < max_depth:
            for child in children:
                title = safe_get_title(child)
                walk_menu(child, path + [title], results, max_depth, depth+1)
        return results

    all_results = walk_menu(element, path=path or [], results=[], max_depth=10, depth=0)
    if output_path:
        with open(output_path, 'w', encoding='utf-8') as f:
            for item in all_results:
                f.write(json.dumps(item, ensure_ascii=False) + '\n')
        return output_path
    else:
        for item in all_results:
            print(item)
        return all_results

def is_submenu_open(parent_elem):
    """Return True if the submenu for this parent menu element is open (has visible children)."""
    try:
        children = getattr(parent_elem, 'AXChildren', [])
        if children and getattr(children[0], 'AXRole', None) == 'AXMenu':
            submenu = children[0]
            submenu_children = getattr(submenu, 'AXChildren', [])
            return bool(submenu_children)
    except Exception:
        pass
    return False

def enrich_menu_jsonl_with_omeclicks(bundle_id, jsonl_path=None, save_path=None, delay=None, max_items=None):
    """
    Enrich the menu JSONL for the given bundle_id by filling in missing omeClick values and adding new children if found.
    For each item missing omeClick, navigates to its parent, opens submenu if needed, scans children, and updates JSONL.
    Repeats until no more missing omeClick items remain or no further progress is made.
    Writes to disk at the end. Logs a summary of new children and omeClick updates.
    If max_items is specified, only process up to max_items missing omeClick entries per run.
    """
    from ome.omeMouseNav import get_omeclick_path_for_menu, mouse_nav_menu_path
    import pyautogui
    # Ensure the app is focused before any mouse navigation
    ensure_app_focus(bundle_id)
    delay = delay if delay is not None else env.MENU_ITEM_CLICK_DELAY
    if jsonl_path is None:
        jsonl_path = os.path.join(MENU_EXPORT_DIR, f"menu_attributes_{bundle_id}.jsonl")
    if save_path is None:
        save_path = jsonl_path
    # Load JSONL
    menu_items = load_menu_jsonl(jsonl_path)
    menu_index = {tuple(item['menu_path']): item for item in menu_items if 'menu_path' in item}
    total_new_children = 0
    total_omeclick_updates = 0
    round_num = 0
    while True:
        round_num += 1
        missing_clicks = [item for item in menu_items if not item.get('omeClick')]
        if not missing_clicks:
            print(f"[INFO] All menu items have omeClick. Done after {round_num} rounds.")
            break
        if max_items is not None:
            missing_clicks = missing_clicks[:max_items]
        print(f"[INFO] Round {round_num}: {len(missing_clicks)} items missing omeClick.")
        progress = False
        for idx, item in enumerate(missing_clicks):
            menu_path = item['menu_path']
            print(f"[DEBUG] Processing missing omeClick for: {menu_path}")
            if not menu_path or len(menu_path) < 2:
                print(f"[DEBUG] Skipping malformed or root menu_path: {menu_path}")
                continue
            parent_path = menu_path[:-1]
            parent_path_tuple = tuple(parent_path)
            # Get parent omeClick
            parent_omeclick = None
            parent_node = menu_index.get(parent_path_tuple)
            if parent_node and 'omeClick' in parent_node:
                parent_omeclick = parent_node['omeClick']
            if not parent_omeclick:
                print(f"[WARN] No omeClick for parent path: {parent_path}, skipping.")
                continue
            # Mouse navigate to parent (explicit move/click for each step)
            omeclick_path = get_omeclick_path_for_menu(menu_items, parent_path)
            for step in omeclick_path:
                coords = step['omeClick']
                if coords:
                    print(f"[DEBUG] Moving mouse to {coords} for '{step['title']}' and clicking")
                    pyautogui.moveTo(coords[0], coords[1], duration=0.3)
                    pyautogui.click()
                    time.sleep(env.MENU_ITEM_CLICK_DELAY)
                else:
                    print(f"[WARN] No omeClick for step: {step['title']} in path {parent_path}")
            # Get parent element
            parent_elem = resolve_ui_element_by_path([ome.getAppRefByBundleId(bundle_id).getLocalizedName()] + parent_path, bundle_id)
            if not parent_elem:
                print(f"[WARN] Could not resolve parent element for path: {parent_path}")
                continue
            # Check if submenu is open
            if not is_submenu_open(parent_elem):
                print(f"[DEBUG] Submenu not open, clicking parent omeClick at {parent_omeclick}")
                pyautogui.moveTo(parent_omeclick[0], parent_omeclick[1], duration=0.3)
                pyautogui.click()
                time.sleep(env.MENU_ITEM_CLICK_DELAY)
            # Scan children using export_menu_attributes_from_element (returns list of dicts)
            children_attrs = export_menu_attributes_from_element(parent_elem, output_path=None, path=parent_path)
            time.sleep(env.MENU_ITEM_CLICK_DELAY)
            new_info = False
            for child in children_attrs:
                child_path_tuple = tuple(child['menu_path'])
                if child_path_tuple not in menu_index:
                    menu_items.append(child)
                    menu_index[child_path_tuple] = child
                    total_new_children += 1
                    progress = True
                    new_info = True
                    print(f"[DEBUG] Added new child: {child['menu_path']}")
                else:
                    existing = menu_index[child_path_tuple]
                    if 'omeClick' not in existing and 'omeClick' in child and child['omeClick']:
                        existing['omeClick'] = child['omeClick']
                        total_omeclick_updates += 1
                        progress = True
                        new_info = True
                        print(f"[DEBUG] Updated omeClick for: {child['menu_path']}")
            if not new_info:
                print(f"[DEBUG] No new children or omeClick updates for parent {parent_path}")
            time.sleep(env.ACTION_DELAY)
        if not progress:
            print(f"[INFO] No further progress in round {round_num}, stopping.")
            break
    # Final write
    with open(save_path, 'w', encoding='utf-8') as f:
        for item in menu_items:
            f.write(json.dumps(item, ensure_ascii=False) + '\n')
    print(f"[INFO] Enriched menu JSONL saved to {save_path} (total new children: {total_new_children}, total omeClick updates: {total_omeclick_updates})")
    return save_path

# Usage example (do not run on import):
# result = menu_jsonl_orchestrator(
#     jsonl_path='ome/data/menus/menu_attributes_com.apple.mail.jsonl',
#     title='New Message',
#     bundle_id='com.apple.mail',
#     update_dict={'AXEnabled': False, 'custom_note': 'Pressed via orchestrator'},
#     save_path=None,
#     fullscreen=True
# )
# print(result) 