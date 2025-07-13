import time
import ome

MAIL_BUNDLE_ID = "com.apple.finder"

# 1. Launch Mail.app
ome.launchAppByBundleId(MAIL_BUNDLE_ID)

# 2. Wait for the app to appear and get its reference
for _ in range(20):  # Wait up to 10 seconds
    try:
        app = ome.getAppRefByBundleId(MAIL_BUNDLE_ID)
        windows = app.windows()
        if windows:
            break
    except Exception:
        pass
    time.sleep(0.5)
else:
    print("Mail.app window did not appear.")
    exit(1)

main_window = windows[0]

# 3. Try to set full screen via AXFullScreen attribute
try:
    if hasattr(main_window, 'AXFullScreen'):
        main_window.AXFullScreen = True
        time.sleep(1)
        if main_window.AXFullScreen:
            print("Successfully set Mail.app to full screen via AXFullScreen.")
        else:
            print("Tried to set AXFullScreen, but it did not take effect.")
    else:
        raise AttributeError
except Exception:
    # Fallback: try pressing the green (zoom) button
    try:
        zoom_button = main_window.findFirst(AXRole='AXButton', AXSubrole='AXFullScreenButton')
        if zoom_button:
            zoom_button.Press()
            print("Pressed the green full screen button.")
        else:
            print("Could not find the full screen (zoom) button.")
    except Exception as e:
        print(f"Failed to set Mail.app to full screen: {e}") 