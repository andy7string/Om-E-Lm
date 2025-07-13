import time
import ome

def wait_for_app_focus(app, timeout=0.5, poll_interval=0.05):
    """
    Poll until the app is focused or timeout is reached.
    Returns True if focused, False if timeout.
    """
    start = time.time()
    while time.time() - start < timeout:
        try:
            if getattr(app, 'AXFocused', False) or getattr(app, 'isFrontmost', lambda: False)():
                return True
        except Exception:
            pass
        time.sleep(poll_interval)
    return False

def ensure_app_focus(bundle_id, fullscreen=True):
    """
    Launches or focuses the app with the given bundle_id, brings it to the foreground, and maximizes the window if possible (fullscreen=True). Returns the app reference.
    """
    app = ome.getAppRefByBundleId(bundle_id)
    try:
        if not app.isFrontmost():
            app.activate()
            wait_for_app_focus(app)
    except Exception:
        app.activate()
        wait_for_app_focus(app)
    # Try to maximize (full screen) the frontmost window if possible
    if fullscreen:
        try:
            if hasattr(app, 'AXWindows'):
                win = app.AXWindows[0]
                if hasattr(win, 'AXFullScreen') and not getattr(win, 'AXFullScreen', False):
                    setattr(win, 'AXFullScreen', True)
                    time.sleep(1.0)
        except Exception:
            pass
    return app 