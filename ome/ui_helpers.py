import ome
import ome.cleanup
import time
import os
import json
from env import UI_MENU_EXPORT_DIR, UI_WINDOW_MAXIMIZE_DELAY, UI_RETRY_DELAY

from ome._a11y import ErrorUnsupported, ErrorCannotComplete, ErrorAPIDisabled, ErrorInvalidUIElement

# Use env.py values once at the top
WINDOW_MAXIMIZE_DELAY = UI_WINDOW_MAXIMIZE_DELAY
RETRY_DELAY = UI_RETRY_DELAY

# Helper to scan children of a UI element, with optional filtering and depth

def scan_children(element, filters=None, depth=1, parent_path=None):
    """
    Returns a list of child metadata dicts for JSONL, not live objects.
    Robust to accessibility errors: skips children that raise errors.
    """
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

# Helper to find a node in a JSONL structure by path

def find_json_node(jsonl, path):
    """
    Recursively find the node in the JSONL structure matching the path.
    Returns the node dict or None if not found.
    """
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

# Helper to update a node's children in JSONL by path

def update_jsonl_with_children(jsonl, path, children):
    """
    Update the node in JSONL matching path with new children.
    If not found, add as a new root node.
    """
    node = find_json_node(jsonl, path)
    if node:
        node["children"] = children
    else:
        # If not found, add as new root node
        jsonl.append({
            "path": path,
            "children": children
        })

# Helper to ensure the app is running and in focus before navigation

def ensure_app_focus(app_bundle_id):
    """
    Ensure the app is running and in focus.
    - If not running, launch it.
    - Activate the app to bring it to the foreground.
    - Wait briefly to ensure focus.
    - Maximize the window if possible.
    Returns the app reference.
    """
    try:
        app = ome.getAppRefByBundleId(app_bundle_id)
    except Exception:
        ome.launchAppByBundleId(app_bundle_id)
        # Wait for app to launch
        for _ in range(20):
            try:
                app = ome.getAppRefByBundleId(app_bundle_id)
                break
            except Exception:
                time.sleep(0.5)
        else:
            raise RuntimeError(f"App {app_bundle_id} did not launch.")
    # Activate the app
    try:
        app.activate()
        time.sleep(0.3)
    except Exception:
        pass
    # Maximize the window if possible
    try:
        enter_full_screen(app, debug=False)
    except Exception:
        pass
    return app

def extract_menu_metadata(menu_item, path):
    """
    Extracts metadata for a menu item for JSONL export.
    Returns a dict with title, role, path, has_children, etc.
    """
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
    """
    Recursively traverses a menu and returns a list of metadata dicts for all menu items and their children.
    Handles AXMenu containers between parent menu items and their children.
    """
    items = []
    meta = extract_menu_metadata(menu_item, path)
    items.append(meta)
    try:
        children = getattr(menu_item, 'AXChildren', [])
    except (ErrorUnsupported, ErrorCannotComplete, ErrorAPIDisabled, ErrorInvalidUIElement, AttributeError):
        children = []
    # If the only child is an AXMenu container, descend into it
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

def extract_window_metadata(window, path):
    """
    Extracts metadata for a window for JSONL export.
    Returns a dict with title, role, path, has_children, etc.
    """
    try:
        title = getattr(window, 'AXTitle', None)
        role = getattr(window, 'AXRole', None)
        children = getattr(window, 'AXChildren', [])
        has_children = bool(children)
        coords = getattr(window, 'AXPosition', None)
        size = getattr(window, 'AXSize', None)
        active = getattr(window, 'AXMain', False)
    except (ErrorUnsupported, ErrorCannotComplete, ErrorAPIDisabled, ErrorInvalidUIElement, AttributeError):
        title = role = coords = size = None
        has_children = False
        active = False
        children = []
    return {
        "path": path,
        "title": title,
        "role": role,
        "has_children": has_children,
        "coords": coords,
        "size": size,
        "active": active
    }

def traverse_windows_to_json(app):
    """
    Traverses all windows of an app and returns a list of metadata dicts for each window and its children.
    """
    items = []
    try:
        windows = app.windows()
    except Exception:
        windows = []
    for i, window in enumerate(windows):
        path = [f"Window_{i}"]
        items.extend(_traverse_window_children(window, path))
    return items

def _traverse_window_children(element, path):
    """
    Helper to recursively traverse window children for JSONL export.
    Skips children that raise errors for unsupported attributes.
    """
    items = []
    meta = extract_window_metadata(element, path)
    items.append(meta)
    try:
        children = getattr(element, 'AXChildren', [])
    except (ErrorUnsupported, ErrorCannotComplete, ErrorAPIDisabled, ErrorInvalidUIElement, AttributeError):
        children = []
    for idx, child in enumerate(children):
        try:
            child_title = getattr(child, 'AXTitle', None)
        except (ErrorUnsupported, ErrorCannotComplete, ErrorAPIDisabled, ErrorInvalidUIElement, AttributeError):
            child_title = None
        child_path = path + [child_title] if child_title else path + [f"Child_{idx}"]
        try:
            items.extend(_traverse_window_children(child, child_path))
        except Exception:
            # Skip this child if traversal fails
            continue
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
        results.append(attrs)
        try:
            children = getattr(element, 'AXChildren', [])
            if children is None:
                children = []
        except Exception:
            children = []
        if isinstance(children, list) and len(children) == 1 and getattr(children[0], 'AXRole', None) == 'AXMenu':
            try:
                subchildren = getattr(children[0], 'AXChildren', [])
                if subchildren is None:
                    subchildren = []
                children = subchildren
            except Exception:
                children = []
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
        os.makedirs(UI_MENU_EXPORT_DIR, exist_ok=True)
        output_path = os.path.join(UI_MENU_EXPORT_DIR, f"menu_attributes_{bundle_id}.jsonl")
    with open(output_path, 'w', encoding='utf-8') as f:
        for item in all_results:
            f.write(json.dumps(item, ensure_ascii=False) + '\n')
    return output_path

def press_menu_path(menu_path, bundle_id, fullscreen=True):
    """
    Ensure the app is running and focused, optionally put it in full screen, resolve the menu item by path, and press it.
    - menu_path: list of str, e.g. ["File", "New Message"]
    - bundle_id: str, e.g. "com.apple.mail"
    - fullscreen: bool, if True, will attempt to put the app in full screen
    Returns True if the menu item was found and pressed, False otherwise.
    """
    app = ensure_app_focus(bundle_id)
    if fullscreen:
        # Try to put the frontmost window in full screen if possible
        try:
            windows = app.windows()
            if windows:
                win = windows[0]
                # Try to find and press the "Enter Full Screen" menu item if it exists
                try:
                    fs_item = app.menuItem("Window", "Enter Full Screen")
                    if fs_item and getattr(fs_item, "AXEnabled", False):
                        fs_item.Press()
                        time.sleep(1.0)
                except Exception:
                    pass
        except Exception:
            pass
    menu_item = resolve_ui_element_by_path([app.getLocalizedName()] + menu_path, bundle_id)
    if menu_item:
        menu_item.Press()
        return True
    return False

def enter_full_screen(app, retries=3, debug=True):
    """
    Attempt to put the given app in full screen by:
    1. Getting the frontmost window.
    2. If the minimize button is enabled, press the full screen button.
    3. After pressing, retry fetching the window and buttons up to 5 times to check if the minimize button is now disabled or missing (indicating full screen).
    4. If not, retry pressing the full screen button up to `retries` times.
    Uses timing values from env.py.
    Returns True if successful, False otherwise.
    """
    for attempt in range(1, retries + 1):
        try:
            windows = app.windows()
            if windows:
                win = windows[0]
                # Try to get the minimize and full screen buttons
                try:
                    min_btn = win.findFirst(AXRole='AXButton', AXSubrole='AXMinimizeButton')
                    fs_btn = win.findFirst(AXRole='AXButton', AXSubrole='AXFullScreenButton')
                except Exception:
                    min_btn = fs_btn = None
                if debug:
                    print(f"[Attempt {attempt}] Minimize button: {min_btn}, enabled: {getattr(min_btn, 'AXEnabled', None)}")
                    print(f"[Attempt {attempt}] FullScreen button: {fs_btn}, enabled: {getattr(fs_btn, 'AXEnabled', None)}")
                # If minimize is enabled, try to press full screen
                if min_btn and getattr(min_btn, 'AXEnabled', False):
                    if fs_btn and getattr(fs_btn, 'AXEnabled', False):
                        if debug:
                            print(f"[Attempt {attempt}] Pressing full screen button...")
                        fs_btn.Press()
                        time.sleep(WINDOW_MAXIMIZE_DELAY)
                        # Retry fetching window and buttons up to 5 times
                        for sub_attempt in range(1, 6):
                            try:
                                windows = app.windows()
                                if windows:
                                    win = windows[0]
                                    min_btn = win.findFirst(AXRole='AXButton', AXSubrole='AXMinimizeButton')
                                    if debug:
                                        print(f"[Attempt {attempt}.{sub_attempt}] After press, minimize enabled: {getattr(min_btn, 'AXEnabled', None)}")
                                    # Success if minimize is missing or disabled
                                    if min_btn is None or not getattr(min_btn, 'AXEnabled', True):
                                        if debug:
                                            print(f"[Attempt {attempt}.{sub_attempt}] Success: window is full screen.")
                                        return True
                                time.sleep(RETRY_DELAY)
                            except Exception as e:
                                if debug:
                                    print(f"[Attempt {attempt}.{sub_attempt}] Exception: {e}")
                                time.sleep(RETRY_DELAY)
                # If minimize is now missing or disabled, window is full screen (in case it changed before the press loop)
                if min_btn is None or not getattr(min_btn, 'AXEnabled', True):
                    if debug:
                        print(f"[Attempt {attempt}] Success: window is full screen.")
                    return True
        except Exception as e:
            if debug:
                print(f"[Attempt {attempt}] Exception: {e}")
        time.sleep(RETRY_DELAY)
    if debug:
        print("Failed to enter full screen after retries.")
    return False

def get_menu_parents(app_bundle_id):
    """
    Focus the app and return a list of top-level menu parent titles.
    Returns a list of strings (menu titles).
    """
    app = ensure_app_focus(app_bundle_id)
    try:
        menu_bar = app.AXMenuBar
        parents = getattr(menu_bar, 'AXChildren', [])
        return [getattr(m, 'AXTitle', None) for m in parents]
    except Exception:
        return []

def resolve_ui_element_by_path(path, bundle_id):
    """
    Given a list of menu path components and a bundle_id, resolve and return the corresponding UI element.
    Example: ["Mail", "File", "New Message"]
    Returns the menu item UI element or None if not found.
    """
    app = ome.getAppRefByBundleId(bundle_id)
    menu_bar = app.AXMenuBar
    current = menu_bar
    for title in path[1:]:  # skip the app name at path[0]
        children = getattr(current, 'AXChildren', [])
        # If the only child is an AXMenu container, descend into it
        if len(children) == 1 and getattr(children[0], 'AXRole', None) == 'AXMenu':
            children = getattr(children[0], 'AXChildren', [])
        found = None
        for child in children:
            if getattr(child, 'AXTitle', None) == title:
                found = child
                break
        if not found:
            return None
        current = found
    return current 