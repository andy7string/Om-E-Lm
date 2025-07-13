import time
import ome
import ome.cleanup
from ome.ui_helpers import ensure_app_focus
from ome._a11y import ErrorUnsupported, ErrorCannotComplete, ErrorAPIDisabled, ErrorInvalidUIElement

MAIL_BUNDLE_ID = "com.apple.mail"

def log(msg):
    print(f"[TEST] {msg}")

def traverse_menu(menu_item, path):
    # Log the menu item, do not press
    try:
        name = getattr(menu_item, 'AXTitle', None)
        log(f"Found menu: {' > '.join(path)}")
        # Recursively traverse children if any
        try:
            children = getattr(menu_item, 'AXChildren', [])
        except (ErrorUnsupported, ErrorCannotComplete, ErrorAPIDisabled, ErrorInvalidUIElement, AttributeError):
            children = []
        for child in children:
            try:
                child_title = getattr(child, 'AXTitle', None)
            except (ErrorUnsupported, ErrorCannotComplete, ErrorAPIDisabled, ErrorInvalidUIElement, AttributeError):
                child_title = "<no title>"
            child_path = path + [child_title] if child_title else path + ["<no title>"]
            traverse_menu(child, child_path)
    except (ErrorUnsupported, ErrorCannotComplete, ErrorAPIDisabled, ErrorInvalidUIElement, AttributeError):
        # Skip this menu item if any accessibility error occurs
        return

def main():
    # Ensure Mail.app is running and in focus
    app = ensure_app_focus(MAIL_BUNDLE_ID)
    # Get menu bar and parent menus
    menu_bar = app.AXMenuBar
    parent_menus = menu_bar.AXChildren
    # Traverse all parent menus and their children recursively
    for menu in parent_menus:
        try:
            title = getattr(menu, 'AXTitle', None)
        except (ErrorUnsupported, ErrorCannotComplete, ErrorAPIDisabled, ErrorInvalidUIElement, AttributeError):
            title = "<no title>"
        path = [title] if title else ["<no title>"]
        # Open the parent menu (to make children accessible)
        try:
            menu.Press()
            time.sleep(0.2)
        except Exception:
            pass
        traverse_menu(menu, path)
        ome.cleanup.cleanup()
    log("All menu items traversal (without pressing) complete.")

if __name__ == "__main__":
    main() 