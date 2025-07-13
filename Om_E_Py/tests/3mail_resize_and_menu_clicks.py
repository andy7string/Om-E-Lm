import time
import ome
import ome.cleanup

MAIL_BUNDLE_ID = "com.apple.mail"

def log(msg):
    print(f"[TEST] {msg}")

def get_main_window(app):
    windows = app.windows()
    if not windows:
        raise Exception("No windows found for Mail.app")
    return windows[0]

def resize_window(window):
    # Full screen
    if hasattr(window, 'AXFullScreen'):
        window.AXFullScreen = True
        time.sleep(1)
        log("Set to full screen.")
        window.AXFullScreen = False
        time.sleep(1)
        log("Restored from full screen.")
    # Minimize
    if hasattr(window, 'AXMinimized'):
        window.AXMinimized = True
        time.sleep(1)
        log("Minimized window.")
        window.AXMinimized = False
        time.sleep(1)
        log("Restored from minimized.")

def click_parent_menus(app):
    menu_bar = app.AXMenuBar
    parent_menus = menu_bar.AXChildren
    for menu in parent_menus:
        name = getattr(menu, 'AXTitle', None)
        try:
            menu.Press()
            log(f"Pressed parent menu: {name}")
            time.sleep(0.5)
        except Exception as e:
            log(f"Failed to press menu: {name} - {e}")

def main():
    log("Launching Mail.app...")
    ome.launchAppByBundleId(MAIL_BUNDLE_ID)
    # Wait for app and window
    for _ in range(20):
        try:
            app = ome.getAppRefByBundleId(MAIL_BUNDLE_ID)
            window = get_main_window(app)
            break
        except Exception:
            time.sleep(0.5)
    else:
        log("Mail.app window did not appear.")
        return
    # Resize actions
    resize_window(window)
    ome.cleanup.cleanup()
    # Click parent menus
    click_parent_menus(app)
    ome.cleanup.cleanup()
    log("Test complete.")

if __name__ == "__main__":
    main() 