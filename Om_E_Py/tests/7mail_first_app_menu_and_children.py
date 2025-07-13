import json
import time
import ome
import ome.cleanup
from ome.ui_helpers import ensure_app_focus

MAIL_BUNDLE_ID = "com.apple.mail"
JSONL_FILE = f"menu_first_parent_{MAIL_BUNDLE_ID}.jsonl"

# Helper to get menu item info (title, role, enabled, coords)
def get_menu_item_info(item):
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
        'role': role,
        'enabled': enabled,
        'center': center
    }

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
    parent = app_menus[0]
    parent_info = get_menu_item_info(parent)
    print(f"[INFO] Parent menu: {parent_info['title']}")
    # Press to open the parent menu
    try:
        parent.Press()
        time.sleep(0.5)
    except Exception as e:
        print(f"[ERROR] Could not press parent menu: {e}")
        return
    # Get the AXMenu container and its children
    submenu = next((c for c in getattr(parent, 'AXChildren', []) if getattr(c, 'AXRole', None) == 'AXMenu'), None)
    if not submenu:
        print("[ERROR] No submenu found for parent menu.")
        return
    children = getattr(submenu, 'AXChildren', [])
    children_info = [get_menu_item_info(child) for child in children]
    # Write parent and children to JSONL
    with open(JSONL_FILE, 'w', encoding='utf-8') as f:
        f.write(json.dumps({'parent': parent_info, 'children': children_info}, ensure_ascii=False) + '\n')
    print(f"[INFO] Wrote parent and children to {JSONL_FILE}")
    print(json.dumps({'parent': parent_info, 'children': children_info}, indent=2, ensure_ascii=False))
    ome.cleanup.cleanup()

if __name__ == "__main__":
    main() 