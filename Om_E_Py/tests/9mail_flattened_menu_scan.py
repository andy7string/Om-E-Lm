import json
import time
import ome
import ome.cleanup
from ome.ui_helpers import ensure_app_focus

MAIL_BUNDLE_ID = "com.apple.mail"
JSONL_FILE = f"menu_flat_{MAIL_BUNDLE_ID}.jsonl"
SUBMENU_POPULATE_DELAY = 0.4
PARENT_MENU_SCAN_DELAY = 0.5

# Helper to get menu item info (title, role, enabled, coords, path)
def get_menu_item_info(item, path):
    title = getattr(item, 'AXTitle', None) or getattr(item, 'AXDescription', None) or '[No Title]'
    role = getattr(item, 'AXRole', '[No Role]')
    enabled = getattr(item, 'AXEnabled', None)
    pos = getattr(item, 'AXPosition', None)
    size = getattr(item, 'AXSize', None)
    center = None
    try:
        if pos and size and hasattr(pos, 'x') and hasattr(size, 'width'):
            center = [float(pos.x) + float(size.width)/2, float(pos.y) + float(size.height)/2]
    except Exception:
        pass
    return {
        'title': title,
        'menu_path': path,
        'role': role,
        'enabled': enabled,
        'center': center
    }

def has_submenu(item):
    children = getattr(item, 'AXChildren', [])
    return any(getattr(child, 'AXRole', None) == 'AXMenu' for child in children)

def flatten_menu_bar(menu, path=None, flat=None, max_depth=4, depth=1):
    if flat is None: flat = []
    if path is None: path = []
    try:
        items = getattr(menu, 'AXChildren', [])
    except Exception:
        return flat
    for item in items:
        info = get_menu_item_info(item, path + [getattr(item, 'AXTitle', '[No Title]')])
        # Dive into submenus if they exist
        submenus = [c for c in getattr(item, 'AXChildren', []) if getattr(c, 'AXRole', None) == 'AXMenu']
        if submenus and depth < max_depth:
            try:
                item.Press()
                time.sleep(SUBMENU_POPULATE_DELAY)
            except Exception:
                pass
            for submenu in submenus:
                flatten_menu_bar(submenu, path + [info['title']], flat, max_depth, depth+1)
        else:
            flat.append(info)
    return flat

def main():
    app = ensure_app_focus(MAIL_BUNDLE_ID)
    # Maximize the main window if possible
    try:
        win = app.windows()[0]
        if hasattr(win, 'AXFullScreen'):
            win.AXFullScreen = True
            time.sleep(1)
    except Exception:
        pass
    # Get the menu bar and skip the Apple menu (index 0)
    menu_bar = app.AXMenuBar
    app_menus = getattr(menu_bar, 'AXChildren', [])[1:]
    if not app_menus:
        print("[ERROR] No application menus found.")
        return
    flat_menu = []
    for parent in app_menus:
        try:
            parent.Press()
            time.sleep(PARENT_MENU_SCAN_DELAY)
        except Exception:
            continue
        flatten_menu_bar(parent, path=[getattr(parent, 'AXTitle', '[No Title]')], flat=flat_menu)
    # Write to JSONL, one item per line
    with open(JSONL_FILE, 'w', encoding='utf-8') as f:
        for item in flat_menu:
            if item['title'] and item['title'] != '[No Title]':
                f.write(json.dumps(item, ensure_ascii=False, separators=(',', ':')) + '\n')
    print(f"[menu-scan] ✅ Done. Saved: {JSONL_FILE}")
    ome.cleanup.cleanup()

if __name__ == "__main__":
    main() 