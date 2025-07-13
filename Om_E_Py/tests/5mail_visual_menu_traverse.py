import time
import ome
import ome.cleanup
from ome.utils.builder.app.app_focus import ensure_app_focus

MAIL_BUNDLE_ID = "com.apple.mail"

# How long to wait between key events (seconds)
KEY_DELAY = 0.4

# This script loads the entire menu structure into memory for traversal (not lazy loading).

# Helper to send a key to the app's main window
def send_key(element, key):
    try:
        element.sendKey(key)
        time.sleep(KEY_DELAY)
    except Exception as e:
        print(f"[TEST] Failed to send key {key}: {e}")

# Recursively navigate a menu visually using arrow keys
# menu: the menu element to open
# depth: current depth in the menu tree
# parent: the parent menu element (for sending Left to return)
def navigate_menu_with_arrows(menu, depth=0, parent=None):
    # Open the menu
    try:
        menu.Press()
        time.sleep(KEY_DELAY)
    except Exception:
        return
    # Get children
    try:
        children = getattr(menu, 'AXChildren', [])
    except Exception:
        children = []
    for i, child in enumerate(children):
        # Visually move selector to this item
        if i > 0:
            send_key(menu, "<cursor_down>")
        # Log the current path
        title = getattr(child, 'AXTitle', '<no title>')
        print(f"[VISUAL] {'  '*depth}Selected: {title}")
        # If this item has children (submenu), enter it
        try:
            if getattr(child, "AXChildren", []):
                send_key(menu, "<cursor_right>")
                # Recursively navigate the submenu
                navigate_menu_with_arrows(child, depth+1, menu)
                # After returning, send Left to go back to parent menu
                send_key(menu, "<cursor_left>")
        except Exception:
            continue
    # Close the menu (ESC)
    send_key(menu, "<escape>")
    time.sleep(KEY_DELAY)


def main():
    app = ensure_app_focus(MAIL_BUNDLE_ID)
    menu_bar = app.AXMenuBar
    parent_menus = menu_bar.AXChildren
    for menu in parent_menus:
        title = getattr(menu, 'AXTitle', '<no title>')
        print(f"[VISUAL] Navigating parent menu: {title}")
        navigate_menu_with_arrows(menu)
        ome.cleanup.cleanup()
    print("[VISUAL] Full visual menu traversal complete.")

if __name__ == "__main__":
    main() 