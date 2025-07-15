"""
Om_E_Py/ome/utils/builder/app/appMenu_builder.py

This module is part of the Om_E_Lm project. It extracts, processes, and exports the menu structure of a macOS application, given its bundle ID.

Main Purpose:
- Scans and extracts all menu items from a specified macOS app (using its bundle ID).
- Processes and filters menu item attributes for clarity and usability.
- Exports the menu structure as a JSONL file (one menu item per line) to a directory set by the central env.py and .env at the project root.
- Allows filtering of menu items (all, enabled, or disabled) **at extraction time for efficiency**.
- Can be run as a script from the command line.

Key Features:
- Menu Extraction: Uses macOS accessibility APIs (via the Om_E_Py.ome package) to walk through the menu bar and all submenus of the target app.
- Attribute Processing: Cleans up, renames, and filters menu item attributes for easier downstream use (e.g., for automation, accessibility, or UI testing).
- **Filter-Aware Extraction:** Filtering (all, enabled, disabled) is now applied during the menu walk, so only relevant items are processed and exported. This improves performance and reduces memory usage.
- **Efficient Attribute Extraction:** Attributes are only extracted for menu items that match the filter criteria.
- Export: Saves the processed menu structure as a JSONL file in a configurable export directory (set by env.py).
- Command-Line Interface: You can run the script directly and specify the app and filter mode.
- **Default Behavior:** If no filter is provided, only enabled menu items are extracted (default is 'enabled').

How to Use (Command Line):
    python -m Om_E_Py.ome.utils.builder.app.appMenu_builder <bundle_id> [--filter all|enabled|disabled]

Arguments:
    <bundle_id>: The bundle ID of the app (e.g., com.apple.mail)
    --filter: (optional) Filter mode for menu items (all, enabled, or disabled). Default is enabled.

Example:
    python -m Om_E_Py.ome.utils.builder.app.appMenu_builder com.apple.mail --filter enabled
    # This will export all enabled menu items from the Mail app.

Output:
- A JSONL file named menu_<bundle_id>.jsonl in the directory specified by UI_MENU_EXPORT_DIR (from env.py).
- Each line in the file is a JSON object representing a menu item, with attributes like title, shortcut, enabled/disabled state, and more.

When to Use:
- To analyze or automate the menus of a macOS app.
- For accessibility or UI testing.
- To build custom menu navigation tools or overlays.

"""
import os
import json
import time
from typing import List, Dict
from ome._a11y import ErrorUnsupported, ErrorCannotComplete, ErrorAPIDisabled, ErrorInvalidUIElement
import ome
from Om_E_Py.ome.utils.builder.app.app_focus import ensure_app_focus
from env import UI_MENU_EXPORT_DIR, UI_DEFAULT_POSITION
from Om_E_Py.ome.utils.builder.app.appList_controller import bundle_id_exists, get_bundle_id
from Om_E_Py.ome.utils.uiNav.navBigDaDDy import get_active_target_and_windows_from_file

def build_menu(bundle_id: str, filter_mode: str = 'all', app_object=None) -> List[Dict]:
    """
    Canonical menu builder for Om-E-Mac.
    Scans all menu items for the given app (by bundle_id), outputs a JSONL, and returns a filtered list.
    filter_mode: 'all', 'enabled', or 'disabled'
    app_object: Optional pre-focused app object to use instead of focusing
    """
    t0 = time.time()
    # Default filters (from omeMenus.py)
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
    DEFAULT_POSITION = tuple(map(float, UI_DEFAULT_POSITION.split(',')))
    MODIFIER_MAP = {
        0: '', 1: '⇧', 2: '⌃', 4: '⌥', 8: '⌘', 10: '⌃⌘', 12: '⌥⌘', 9: '⇧⌘', 5: '⇧⌥', 3: '⇧⌃', 6: '⌃⌥', 24: '⌘⇧⌥', 28: '⌘⌥⇧', 13: '⇧⌃⌘', 14: '⌃⌥⌘', 15: '⇧⌃⌥⌘',
    }
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

    def walk_menu(element, path=None, results=None, max_depth=10, depth=0, filter_mode='all'):
        """
        Recursively walks the menu structure, applying filter_mode during traversal.
        Only menu items matching the filter are included, and only appropriate children are walked:
        - 'all': include all items and walk all children
        - 'enabled': include only enabled items, and only walk children of enabled parents
        - 'disabled': include only disabled items, do not walk children of disabled parents
        This makes extraction efficient and filter-aware.
        """
        if results is None:
            results = []
        if path is None:
            path = []
        try:
            is_enabled = element._getAttribute('AXEnabled')
        except Exception:
            is_enabled = None

        # Should we include this item?
        include = (
            filter_mode == 'all' or
            (filter_mode == 'enabled' and is_enabled is True) or
            (filter_mode == 'disabled' and is_enabled is False)
        )

        # Should we walk this item's children?
        if filter_mode == 'all':
            walk_children = True
        elif filter_mode == 'enabled':
            walk_children = is_enabled is True
        elif filter_mode == 'disabled':
            walk_children = is_enabled is True  # Only walk children of enabled parents
        else:
            walk_children = False

        title = safe_get_title(element)
        # Only include in path if title is not '<no title>'
        new_path = path if title == '<no title>' else path + [title]

        if include:
            attrs = get_all_attributes(element)
            attrs['menu_path'] = list(new_path)
            # --- Add child_count and children_titles if this node has children ---
            try:
                children = getattr(element, 'AXChildren', [])
                if children is None:
                    children = []
            except Exception:
                children = []
            if children:
                attrs['child_count'] = len(children)
                attrs['children_titles'] = []
                for child in children:
                    try:
                        child_title = safe_get_title(child)
                    except Exception:
                        child_title = '<no title>'
                    attrs['children_titles'].append(child_title)
            results.append(attrs)

        if walk_children and depth < max_depth:
            try:
                children = getattr(element, 'AXChildren', [])
                if children is None:
                    children = []
            except Exception:
                children = []
            for child in children:
                walk_menu(child, new_path, results, max_depth, depth+1, filter_mode=filter_mode)
        return results

    app_focus_start = time.time()
    # Use provided app object or focus fresh one
    if app_object is not None:
        # Use provided app object (fast path)
        app = app_object
        print(f"[INFO] Using provided app object for {bundle_id}")
    else:
        # Focus app (slow path)
        app = ensure_app_focus(bundle_id, fullscreen=True)
        # If ensure_app_focus returns a PyXA app, get the bundle id for OME
        # Try to get the OME app reference as before
        app = ome.getAppRefByBundleId(bundle_id)
    
    print(f"[TIMER] App focus/load for {bundle_id} took {time.time() - app_focus_start:.3f} seconds.")
    walk_start = time.time()
    menu_bar = app.AXMenuBar
    app_menus = getattr(menu_bar, 'AXChildren', [])[1:]
    all_results = []
    for parent in app_menus:
        try:
            parent.Press()
            time.sleep(0.4)
        except Exception:
            pass
        walk_menu(parent, path=[], results=all_results, filter_mode=filter_mode)
    print(f"[TIMER] Menu walk for {bundle_id} took {time.time() - walk_start:.3f} seconds.")
    # Save filtered results to JSONL (apply filter as you write)
    os.makedirs(UI_MENU_EXPORT_DIR, exist_ok=True)
    output_base = os.path.join(UI_MENU_EXPORT_DIR, f"menu_{bundle_id}")
    written_items = []
    if filter_mode == 'all':
        def dedup(items):
            seen = set()
            deduped = []
            for item in items:
                menu_path_tuple = tuple(item.get('menu_path', []))
                if menu_path_tuple in seen:
                    continue
                seen.add(menu_path_tuple)
                deduped.append(item)
            return deduped
        all_items = dedup(all_results)
        # Write all items to menu_<bundleid>.jsonl
        with open(output_base + '.jsonl', 'w', encoding='utf-8') as f:
            for item in all_items:
                f.write(json.dumps(item, ensure_ascii=False) + '\n')
        written_items = all_items
    elif filter_mode == 'enabled':
        def dedup(items):
            seen = set()
            deduped = []
            for item in items:
                menu_path_tuple = tuple(item.get('menu_path', []))
                if menu_path_tuple in seen:
                    continue
                seen.add(menu_path_tuple)
                deduped.append(item)
            return deduped
        enabled_items = dedup([item for item in all_results if ('AXEnabled' in item and item['AXEnabled'] is True)])
        with open(output_base + '_enabled.jsonl', 'w', encoding='utf-8') as f:
            for item in enabled_items:
                f.write(json.dumps(item, ensure_ascii=False) + '\n')
        written_items = enabled_items
    elif filter_mode == 'disabled':
        def dedup(items):
            seen = set()
            deduped = []
            for item in items:
                menu_path_tuple = tuple(item.get('menu_path', []))
                if menu_path_tuple in seen:
                    continue
                seen.add(menu_path_tuple)
                deduped.append(item)
            return deduped
        disabled_items = dedup([item for item in all_results if ('AXEnabled' in item and item['AXEnabled'] is False)])
        with open(output_base + '_disabled.jsonl', 'w', encoding='utf-8') as f:
            for item in disabled_items:
                f.write(json.dumps(item, ensure_ascii=False) + '\n')
        written_items = disabled_items
    else:
        seen_menu_paths = set()
        output_path = output_base + f'_{filter_mode}.jsonl'
        with open(output_path, 'w', encoding='utf-8') as f:
            for item in all_results:
                if filter_mode == 'enabled' and not (item.get('AXEnabled') is True):
                    continue
                if filter_mode == 'disabled' and not (item.get('AXEnabled') is False):
                    continue
                menu_path_tuple = tuple(item.get('menu_path', []))
                if menu_path_tuple in seen_menu_paths:
                    continue
                seen_menu_paths.add(menu_path_tuple)
                f.write(json.dumps(item, ensure_ascii=False) + '\n')
                written_items.append(item)
    print(f"[TIMER] Total build_menu time for {bundle_id}: {time.time() - t0:.3f} seconds.")
    return written_items

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Build and export app menus as JSONL.")
    parser.add_argument("bundle_id", nargs="?", help="The bundle ID of the app (e.g., com.apple.mail) or app name (e.g., Mail)")
    parser.add_argument("--filter", choices=["all", "enabled", "disabled"], default="all", help="Filter mode for menu items")
    args = parser.parse_args()

    input_id = args.bundle_id
    if not input_id:
        # Read from active_target_Bundle_ID.json
        import json, os
        active_target_path = os.path.join("Om_E_Py/ome", "data", "windows", "active_target_Bundle_ID.json")
        try:
            with open(active_target_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            input_id = data.get("active_bundle_id")
            if not input_id:
                print(f"[ERROR] No active_bundle_id found in {active_target_path}")
                exit(1)
            print(f"[INFO] No bundle_id provided, using active_bundle_id from {active_target_path}: {input_id}")
        except Exception as e:
            print(f"[ERROR] Could not read {active_target_path}: {e}")
            exit(1)
    from Om_E_Py.ome.utils.builder.app.appList_controller import bundle_id_exists, get_bundle_id
    canonical_bundle_id = bundle_id_exists(input_id)
    if not canonical_bundle_id:
        # Try to resolve as app name
        possible_bundle_id = get_bundle_id(input_id)
        if possible_bundle_id:
            canonical_bundle_id = bundle_id_exists(possible_bundle_id)
            if canonical_bundle_id:
                print(f"[INFO] Resolved app name '{input_id}' to bundle ID '{canonical_bundle_id}'.")
            else:
                print(f"[ERROR] '{input_id}' is neither a valid bundle ID nor a known app name.")
                exit(1)
        else:
            print(f"[ERROR] '{input_id}' is neither a valid bundle ID nor a known app name.")
            exit(1)
    if canonical_bundle_id != input_id:
        print(f"[INFO] Using closest matching bundle ID: '{canonical_bundle_id}' (input was '{input_id}')")
    resolved_bundle_id = canonical_bundle_id

    results = build_menu(resolved_bundle_id, filter_mode=args.filter)
    print(f"Exported {len(results)} menu items for {resolved_bundle_id} (filter: {args.filter})")
    # Call winD_controller to set the active target after menu JSONL write
    try:
        win_state = get_active_target_and_windows_from_file(bundle_id=resolved_bundle_id)
        print(f"[INFO] navBigDaDDy active target: {win_state['active_target']}")
    except Exception as e:
        print(f"[ERROR] Could not read active target from file: {e}") 