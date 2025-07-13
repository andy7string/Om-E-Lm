import os
import json
import time
from typing import List, Dict
from ome._a11y import ErrorUnsupported, ErrorCannotComplete, ErrorAPIDisabled, ErrorInvalidUIElement
import ome

def build_menu(bundle_id: str, filter_mode: str = 'all') -> List[Dict]:
    """
    Canonical menu builder for Om-E-Mac.
    Scans all menu items for the given app (by bundle_id), outputs a JSONL, and returns a filtered list.
    filter_mode: 'all', 'enabled', or 'disabled'
    """
    from ome.utils.env.env import MENU_EXPORT_DIR
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
    DEFAULT_POSITION = [0.0, 1440.0]
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
    # Save to JSONL
    os.makedirs(MENU_EXPORT_DIR, exist_ok=True)
    output_path = os.path.join(MENU_EXPORT_DIR, f"menu_{bundle_id}.jsonl")
    with open(output_path, 'w', encoding='utf-8') as f:
        for item in all_results:
            f.write(json.dumps(item, ensure_ascii=False) + '\n')
    # Filter if needed
    if filter_mode == 'enabled':
        filtered = [item for item in all_results if item.get('AXEnabled')]
    elif filter_mode == 'disabled':
        filtered = [item for item in all_results if not item.get('AXEnabled')]
    else:
        filtered = all_results
    return filtered 