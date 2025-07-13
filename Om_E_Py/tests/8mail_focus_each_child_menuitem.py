import json
import time
import ome
import ome.cleanup
from ome.ui_helpers import ensure_app_focus

MAIL_BUNDLE_ID = "com.apple.mail"
JSONL_FILE = f"menu_first_parent_focus_walk_{MAIL_BUNDLE_ID}.jsonl"

# Helper to get menu item info (title, role, enabled, coords, focused)
def get_menu_item_info(item):
    title = getattr(item, 'AXTitle', None) or getattr(item, 'AXDescription', None) or '[No Title]'
    role = getattr(item, 'AXRole', '[No Role]')
    enabled = getattr(item, 'AXEnabled', None)
    pos = getattr(item, 'AXPosition', None)
    size = getattr(item, 'AXSize', None)
    focused = getattr(item, 'AXFocused', False)
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
        'center': center,
        'focused': focused
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
    results = []
    # Focus each child in turn using <cursor_down>
    for i, child in enumerate(children):
        if i == 0:
            # The first item is focused by default when menu opens
            pass
        else:
            try:
                submenu.sendKey('<cursor_down>')
                time.sleep(0.3)
            except Exception as e:
                print(f"[WARN] Failed to send <cursor_down>: {e}")
        # After moving, check which child is focused
        focused_child = None
        for c in children:
            if getattr(c, 'AXFocused', False):
                focused_child = c
                break
        if focused_child is None:
            print(f"[WARN] No focused child found at index {i}")
            focused_child = child  # fallback
        info = get_menu_item_info(focused_child)
        print(f"[FOCUS] {info}")
        results.append(info)
    # Write results to JSONL
    with open(JSONL_FILE, 'w', encoding='utf-8') as f:
        for item in results:
            f.write(json.dumps(item, ensure_ascii=False) + '\n')
    print(f"[INFO] Wrote focused walk to {JSONL_FILE}")
    ome.cleanup.cleanup()

if __name__ == "__main__":
    main() 