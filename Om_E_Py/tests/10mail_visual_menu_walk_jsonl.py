import json
import time
import ome
import ome.cleanup
from ome.ui_helpers import ensure_app_focus

MAIL_BUNDLE_ID = "com.apple.mail"
JSONL_FILE = f"menu_visual_walk_{MAIL_BUNDLE_ID}.jsonl"
KEY_DELAY = 0.35
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

def walk_menu(menu, path, seen, results, depth=1, max_depth=6):
    # Focus the first item
    children = getattr(menu, 'AXChildren', [])
    if not children:
        return
    last_info = None
    repeat_count = 0
    i = 0
    while True:
        # Find the currently focused child
        focused_child = None
        for c in children:
            if getattr(c, 'AXFocused', False):
                focused_child = c
                break
        if not focused_child:
            focused_child = children[i] if i < len(children) else children[-1]
        info = get_menu_item_info(focused_child, path + [getattr(focused_child, 'AXTitle', '[No Title]')])
        info_key = (info['title'], info['role'], tuple(info['menu_path']))
        if info_key in seen:
            repeat_count += 1
            if repeat_count > 1:
                break  # End of menu reached
        else:
            seen.add(info_key)
            results.append(info)
            repeat_count = 0
        # If the focused child has a submenu, enter it
        submenus = [c for c in getattr(focused_child, 'AXChildren', []) if getattr(c, 'AXRole', None) == 'AXMenu']
        if submenus and depth < max_depth:
            try:
                menu.sendKey('<cursor_right>')
                time.sleep(KEY_DELAY)
                walk_menu(submenus[0], path + [info['title']], seen, results, depth+1, max_depth)
                menu.sendKey('<cursor_left>')
                time.sleep(KEY_DELAY)
            except Exception:
                pass
        # Move to next item
        try:
            menu.sendKey('<cursor_down>')
            time.sleep(KEY_DELAY)
        except Exception:
            break
        i += 1

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
    results = []
    seen = set()
    for parent in app_menus:
        try:
            parent.Press()
            time.sleep(PARENT_MENU_SCAN_DELAY)
        except Exception:
            continue
        # The AXMenu container for this parent
        submenu = next((c for c in getattr(parent, 'AXChildren', []) if getattr(c, 'AXRole', None) == 'AXMenu'), None)
        if submenu:
            walk_menu(submenu, path=[getattr(parent, 'AXTitle', '[No Title]')], seen=seen, results=results)
        # Close the menu (Escape)
        try:
            submenu.sendKey('<escape>')
            time.sleep(0.2)
        except Exception:
            pass
    # Write to JSONL, one item per line
    with open(JSONL_FILE, 'w', encoding='utf-8') as f:
        for item in results:
            if item['title'] and item['title'] != '[No Title]':
                f.write(json.dumps(item, ensure_ascii=False, separators=(',', ':')) + '\n')
    print(f"[menu-visual-walk] ✅ Done. Saved: {JSONL_FILE}")
    ome.cleanup.cleanup()

if __name__ == "__main__":
    main() 