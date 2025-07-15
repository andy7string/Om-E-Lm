"""
app_focus.py

This module is part of the Om_E_Lm project and provides a function to bring a macOS application (by bundle ID) to the foreground and optionally set it to true full screen using the accessibility API. It returns the accessibility app object for further automation if needed.

USAGE:
    # Command line usage (status and bundle_id are printed)
    python -m Om_E_Py.ome.utils.builder.app.app_focus <bundle_id>

    # Python usage (get status and accessibility app object)
    from Om_E_Py.ome.utils.builder.app.app_focus import ensure_app_focus
    result = ensure_app_focus('com.apple.mail')
    if result['status'] == 'success' and result['app']:
        app = result['app']
        # Use app for accessibility automation, e.g.:
        window = app.AXFocusedWindow
        # ...
    else:
        print(f"Failed to focus app: {result.get('error')}")

ARGUMENTS:
    <bundle_id>   (required) The macOS bundle identifier of the app to focus (e.g., com.apple.mail).

NOTES:
    - Uses the central env.py for all environment variables (delivered via .env at the project root).
    - All imports use the Om_E_Py.ome package structure.
    - This function uses the accessibility API for maximum reliability.
    - The returned app object can be used for further accessibility scripting (window manipulation, UI automation, etc.).
    - The function always returns a dictionary with:
        - 'status': 'success' or 'failed'
        - 'bundle_id': the bundle identifier
        - 'app': the accessibility app object (or None on failure)
        - 'error': error message (only present on failure)
    - Only works on macOS (Darwin).
    - Backward compatible: scripts that only check 'status' and 'bundle_id' will continue to work.

"""
import time
import sys
import platform
import os
import subprocess
import Om_E_Py.ome as ome

from Om_E_Py.ome.utils.builder.app.appList_controller import bundle_id_exists
from env import (
    UI_APP_LAUNCH_DELAY,
    UI_SLEEP_AFTER_ACTIVATE,
    UI_ACTION_DELAY,
    UI_SLEEP_AFTER_FULLSCREEN
)


print(f"SLEEP_AFTER_ACTIVATE = {UI_SLEEP_AFTER_ACTIVATE}")


def activate_app(bundle_id):
    """
    Uses AppleScript (osascript) to activate the app with the given bundle_id.
    Special case for Finder.
    """
    if bundle_id == "com.apple.finder":
        script = 'tell application "Finder" to activate'
    else:
        script = f'tell application id "{bundle_id}" to activate'
    subprocess.run(['osascript', '-e', script])
    time.sleep(UI_SLEEP_AFTER_ACTIVATE)  # Use global delay


def ensure_app_focus(bundle_id, fullscreen=True):
    """
    Launches or focuses the app with the given bundle_id using accessibility API,
    brings it to the foreground, waits for a window, and sets it to full screen if requested.

    Args:
        bundle_id (str): The bundle identifier of the app to focus.
        fullscreen (bool): Whether to attempt to set the window to true full screen. Default is True.

    Returns:
        dict: A dictionary with status, bundle_id, and the accessibility app object (key 'app'), or error message.
    """
    if platform.system() != "Darwin":
        return {"status": "failed", "error": "This script only works on macOS.", "app": None, "bundle_id": bundle_id}

    # Check if bundle_id exists (with fuzzy match)
    canonical_bundle_id = bundle_id_exists(bundle_id)
    if not canonical_bundle_id:
        return {"status": "failed", "error": f"Bundle ID '{bundle_id}' does not exist (even with fuzzy match).", "app": None, "bundle_id": bundle_id}

    try:
        # Use AppleScript to activate the app before accessibility logic
        activate_app(canonical_bundle_id)
        ome.launchAppByBundleId(canonical_bundle_id)
        # Wait for the app and its windows to appear
        app = None
        windows = []
        waited = 0
        max_wait = 60  # seconds (can adjust as needed)
        start_time = time.time()
        while True:
            try:
                app = ome.getAppRefByBundleId(canonical_bundle_id)
                windows = app.windows()
                # Debug: print number and titles of windows
                print(f"[DEBUG] Found {len(windows)} windows:")
                for i, win in enumerate(windows):
                    try:
                        title = getattr(win, 'AXTitle', None)
                    except Exception:
                        title = None
                    print(f"    Window {i+1}: title={title}")
                if windows:
                    break
            except Exception as e:
                print(f"[DEBUG] Exception while getting windows: {e}")
            time.sleep(UI_ACTION_DELAY)
            waited = time.time() - start_time
            if waited > max_wait:
                print(f"[ERROR] Timed out waiting for a window for {canonical_bundle_id} after {max_wait} seconds.")
                return {"status": "failed", "error": f"App window did not appear for {canonical_bundle_id} after {max_wait} seconds.", "app": None, "bundle_id": canonical_bundle_id}

        # --- Robust focus and window handling (from app_focus.py) ---
        try:
            if not app.isFrontmost():
                app.activate()
                # Optionally, wait for focus if you have a wait_for_app_focus function
        except Exception:
            app.activate()
            # Optionally, wait for focus if you have a wait_for_app_focus function
        # Un-minimize any minimized windows (handle Dock-minimized case)
        try:
            if hasattr(app, 'AXWindows'):
                for win in app.AXWindows:
                    if hasattr(win, 'AXMinimized') and getattr(win, 'AXMinimized', False):
                        setattr(win, 'AXMinimized', False)
                        time.sleep(UI_ACTION_DELAY)  # Use global delay
        except Exception:
            pass
        # Explicitly set main window as AXMain and AXFocused, and raise it
        try:
            if hasattr(app, 'AXWindows') and app.AXWindows:
                win = app.AXWindows[0]
                if hasattr(win, 'AXMain') and not getattr(win, 'AXMain', False):
                    setattr(win, 'AXMain', True)
                if hasattr(win, 'AXFocused') and not getattr(win, 'AXFocused', False):
                    setattr(win, 'AXFocused', True)
                if hasattr(win, 'AXRaise'):
                    win.AXRaise()
                time.sleep(UI_ACTION_DELAY)
        except Exception:
            pass
        # Try to maximize (full screen) the frontmost window if possible
        if fullscreen:
            try:
                if hasattr(app, 'AXWindows'):
                    win = app.AXWindows[0]
                    if hasattr(win, 'AXFullScreen') and not getattr(win, 'AXFullScreen', False):
                        setattr(win, 'AXFullScreen', True)
                        time.sleep(UI_SLEEP_AFTER_FULLSCREEN)
            except Exception:
                pass
        return {"status": "success", "bundle_id": canonical_bundle_id, "app": app}
    except Exception as e:
        return {"status": "failed", "error": str(e), "app": None, "bundle_id": canonical_bundle_id}

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python -m Om_E_Py.ome.utils.builder.app.app_focus <bundle_id>")
        print("Example: python -m Om_E_Py.ome.utils.builder.app.app_focus com.apple.mail")
        sys.exit(1)
    bundle_id = sys.argv[1]
    print(f"Ensuring focus for bundle_id: {bundle_id}")
    result = ensure_app_focus(bundle_id)
    # Check the bundle_id after ensure_app_focus using bundle_id_exists
    canonical_bundle_id = bundle_id_exists(result.get('bundle_id'))
    if not canonical_bundle_id:
        print(f"[ERROR] Bundle ID '{result.get('bundle_id')}' is not valid or not found in the app list.")
        sys.exit(1)
    print(f"Result: {result}") 