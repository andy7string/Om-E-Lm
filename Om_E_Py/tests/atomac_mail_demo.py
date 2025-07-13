import ome
import time
import subprocess

BUNDLE_ID = "com.apple.mail"

def get_app():
    app = ome.getAppRefByBundleId(BUNDLE_ID)
    if not app:
        print("Launching Mail...")
        ome.launchAppByBundleId(BUNDLE_ID)
        time.sleep(2)
        app = ome.getAppRefByBundleId(BUNDLE_ID)
    app.activate()
    return app

def get_focused_window(app):
    win = app.AXFocusedWindow
    print("Window title:", win.AXTitle)
    return win

def set_mail_window_position_and_size_applescript():
    print("Trying AppleScript to set window bounds...")
    script = '''
    tell application "Mail"
        set bounds of front window to {100, 100, 1000, 800}
    end tell
    '''
    result = subprocess.run(['osascript', '-e', script], capture_output=True, text=True)
    if result.returncode == 0:
        print("AppleScript: Window bounds set.")
    else:
        print("AppleScript failed:", result.stderr)

def print_and_set_window(win):
    print("Current position:", win.AXPosition)
    print("Current size:", win.AXSize)
    # Try to set new position and size with ome
    position_set = False
    size_set = False
    try:
        win.AXPosition = (100, 100)
        print("New position:", win.AXPosition)
        position_set = True
    except Exception as e:
        print("Could not set position with ome:", e)
    try:
        win.AXSize = (900, 700)
        print("New size:", win.AXSize)
        size_set = True
    except Exception as e:
        print("Could not set size with ome:", e)
    # If either failed, try AppleScript fallback
    if not (position_set and size_set):
        set_mail_window_position_and_size_applescript()

def bring_to_front(win):
    try:
        win.AXRaise()
        win.AXFocused = True
        print("Window brought to front and focused.")
    except Exception as e:
        print("Could not bring window to front:", e)

def close_window(win):
    print("Closing window...")
    try:
        win.AXCloseButton.Press()
        time.sleep(1)
    except Exception as e:
        print("Could not close window:", e)

def list_menu_items(app):
    print("Top-level menu items:")
    try:
        menu_bar = app.menuBar()
        for menu in menu_bar.AXChildren:
            print("-", menu.AXTitle)
    except Exception as e:
        print("Could not list menu items:", e)

def click_about_mail(app):
    try:
        menu_bar = app.menuBar()
        mail_menu = [m for m in menu_bar.AXChildren if m.AXTitle == "Mail"][0]
        about_item = [i for i in mail_menu.AXChildren[0].AXChildren if i.AXTitle == "About Mail"][0]
        about_item.Press()
        print("Clicked 'About Mail'.")
    except Exception as e:
        print("Could not click 'About Mail':", e)

def main():
    app = get_app()
    time.sleep(1)
    win = get_focused_window(app)
    print_and_set_window(win)
    bring_to_front(win)
    list_menu_items(app)
    click_about_mail(app)
    time.sleep(2)
    close_window(win)

if __name__ == "__main__":
    main() 