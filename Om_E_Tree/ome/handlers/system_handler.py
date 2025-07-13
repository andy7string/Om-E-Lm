import os
import subprocess
import socket
import getpass
import time
from pathlib import Path
from difflib import get_close_matches
from PIL import ImageGrab
from Om_E_Tree.ome.utils.logger import log_event
from env import TREE_SYSTEM_HANDLER_DELAY, TREE_SCREENSHOT_DIR, TREE_APPLICATION_PATH, TREE_APP_LIST_PATH, TREE_MAX_RECENT_SCREENSHOTS
from Om_E_Tree.ome.utils.system.platform_config import is_mac, is_windows
from Om_E_Tree.ome.utils.builder.appList_builder import load_app_list
from Om_E_Tree.ome.utils.memory.screenshot_tracker import track_screenshot
import Om_E_Py.ome

# Aliases for backward compatibility
DEFAULT_DELAY = TREE_SYSTEM_HANDLER_DELAY
SCREENSHOT_DIR = Path(TREE_SCREENSHOT_DIR)
APPLICATION_PATH = Path(TREE_APPLICATION_PATH)
APP_LIST_PATH = Path(TREE_APP_LIST_PATH)
MAX_RECENT_SCREENSHOTS = TREE_MAX_RECENT_SCREENSHOTS

# Helper: Get app name from bundle id
def get_app_name_from_bundle_id(bundle_id):
    apps = load_app_list()
    for app in apps:
        if app.get("bundle_id", "").lower() == bundle_id.lower():
            return app["name"]
    return None

# Helper: Get bundle id from app name
def get_bundle_id_from_app_name(app_name):
    apps = load_app_list()
    for app in apps:
        if app["name"].lower() == app_name.lower():
            return app.get("bundle_id")
    return None

# -------------------- ENV CONFIG --------------------

# Some variables might be loaded from env but not used if the logic is self-contained.
# This pass focuses on fixing the imports.

# ✅ Caching logic — only refresh if the file doesn't exist
INSTALLED_APPS = load_app_list(refresh=not APP_LIST_PATH.exists())

#SCREENSHOT_DIR = Path(os.getenv("SCREENSHOT_DIR", "ome/data/screenshots")).resolve()
# -------------------- ENV CONFIG --------------------

# Some variables might be loaded from env but not used if the logic is self-contained.
# This pass focuses on fixing the imports.

# ✅ Caching logic — only refresh if the file doesn't exist
INSTALLED_APPS = load_app_list(refresh=not APP_LIST_PATH.exists())

# -------------------- App Resolution --------------------

def resolve_app_name(requested):
    requested_clean = requested.lower().replace(" ", "")
    candidates = [app["name"] for app in INSTALLED_APPS]
    cleaned_candidates = [c.lower().replace(" ", "") for c in candidates]

    close = get_close_matches(requested_clean, cleaned_candidates, n=1, cutoff=0.6)
    if close:
        index = cleaned_candidates.index(close[0])
        resolved = INSTALLED_APPS[index]["name"]
        print(f"[SMART MATCH] '{requested}' matched to: {resolved}")
        return resolved

    print(f"[FAIL] App '{requested}' not found in app_list.json")
    return None

# -------------------- Applications --------------------

def list_apps(args):
    try:
        return {"status": "success", "apps": os.listdir(APPLICATION_PATH)}
    except Exception as e:
        return {"status": "failed", "error": str(e)}

def launch_app(args):
    try:
        resolved = resolve_app_name(args["app_name"])
        if resolved not in [app["name"] for app in INSTALLED_APPS]:
            return {"status": "failed", "error": f"App '{resolved}' not found"}
        subprocess.run(["open", "-a", resolved])
        time.sleep(DEFAULT_DELAY)
        # Activate the app first
        activate_script = f'''
        tell application "{resolved}"
            activate
        end tell
        '''
        subprocess.run(['osascript', '-e', activate_script])
        time.sleep(0.5)
        if args.get("fullscreen", False):
            bundle_id = get_bundle_id_from_app_name(resolved)
            if bundle_id:
                enforce_app_fullscreen(bundle_id)
        return {"status": "success"}
    except Exception as e:
        return {"status": "failed", "error": str(e)}

def quit_app(args):
    try:
        resolved = resolve_app_name(args["app_name"])
        if not resolved:
            return {"status": "failed", "error": f"App '{args['app_name']}' not found"}
        subprocess.run(["osascript", "-e", f'tell application "{resolved}" to quit'])
        return {"status": "success"}
    except Exception as e:
        return {"status": "failed", "error": str(e)}

def launch_app_by_bundle_id(bundle_id, fullscreen=True, wait_for_build=15):
    """
    Launch an app by its bundle ID, building the app list if needed, and launch in fullscreen.
    Returns a dict with status and app_name or error.
    """
    print(f"[DEBUG] launch_app_by_bundle_id called with bundle_id={bundle_id}")
    if not APP_LIST_PATH.exists():
        print("[INFO] app_list.json missing, building...")
        subprocess.Popen(["python", "-m", "ome.utils.builder.appList_builder", "--refresh"])
        for i in range(wait_for_build):
            if APP_LIST_PATH.exists():
                print(f"[DEBUG] app_list.json found after {i+1} seconds.")
                break
            time.sleep(1)
        else:
            print("[ERROR] app_list.json not created after waiting.")
            return {"status": "failed", "error": "app_list.json not created after waiting."}
    print("[DEBUG] Loading app list...")
    apps = load_app_list()
    app_name = None
    for app in apps:
        bundle = app.get("bundle_id")
        if bundle and bundle.lower() == bundle_id.lower():
            app_name = app["name"]
            break
    print(f"[DEBUG] Lookup result: bundle_id={bundle_id}, app_name={app_name}")
    if not app_name:
        print(f"[ERROR] No app name found for bundle id: {bundle_id}")
        return {"status": "failed", "error": f"No app name found for bundle id: {bundle_id}"}
    print(f"[DEBUG] Launching app: {app_name} (fullscreen={fullscreen})")
    result = launch_app({"app_name": app_name, "fullscreen": fullscreen})
    print(f"[DEBUG] launch_app result: {result}")
    if result["status"] != "success":
        return result
    return {"status": "success", "app_name": app_name}

# -------------------- Filesystem --------------------

def list_files(args):
    try:
        folder = args.get("folder_path", ".")
        return {"status": "success", "files": os.listdir(folder)}
    except Exception as e:
        return {"status": "failed", "error": str(e)}

def write_file(args):
    try:
        with open(args["path"], "w") as f:
            f.write(args["content"])
        return {"status": "success"}
    except Exception as e:
        return {"status": "failed", "error": str(e)}

def delete_file(args):
    try:
        os.remove(args["path"])
        return {"status": "success"}
    except Exception as e:
        return {"status": "failed", "error": str(e)}

def copy_file(args):
    try:
        subprocess.run(["cp", args["src"], args["dst"]])
        return {"status": "success"}
    except Exception as e:
        return {"status": "failed", "error": str(e)}

def move_file(args):
    try:
        subprocess.run(["mv", args["src"], args["dst"]])
        return {"status": "success"}
    except Exception as e:
        return {"status": "failed", "error": str(e)}

# -------------------- System Info --------------------

def get_system_info(args):
    try:
        info = os.uname()
        return {"status": "success", "info": {
            "hostname": info.nodename,
            "system": info.sysname,
            "release": info.release,
            "version": info.version
        }}
    except Exception as e:
        return {"status": "failed", "error": str(e)}

def get_user_info(args):
    try:
        return {"status": "success", "username": getpass.getuser(), "home": os.path.expanduser("~"),
                "full_name": os.popen("id -F").read().strip()}
    except Exception as e:
        return {"status": "failed", "error": str(e)}

def get_ip_address(args):
    try:
        hostname = socket.gethostname()
        ip = socket.gethostbyname(hostname)
        return {"status": "success", "ip": ip, "hostname": hostname}
    except Exception as e:
        return {"status": "failed", "error": str(e)}

def get_current_shell(args):
    try:
        return {"status": "success", "shell": os.environ.get("SHELL", "unknown")}
    except Exception as e:
        return {"status": "failed", "error": str(e)}

def get_uptime(args):
    try:
        output = subprocess.check_output("uptime", shell=True).decode().strip()
        return {"status": "success", "uptime": output}
    except Exception as e:
        return {"status": "failed", "error": str(e)}

def get_logged_in_users(args):
    try:
        users = os.popen("who").read().strip()
        return {"status": "success", "users": users}
    except Exception as e:
        return {"status": "failed", "error": str(e)}

# -------------------- System Hardware --------------------

def list_usb_devices(args):
    try:
        result = subprocess.check_output(["system_profiler", "SPUSBDataType"]).decode()
        return {"status": "success", "devices": result}
    except Exception as e:
        return {"status": "failed", "error": str(e)}

def list_displays(args):
    try:
        result = subprocess.check_output(["system_profiler", "SPDisplaysDataType"]).decode()
        return {"status": "success", "displays": result}
    except Exception as e:
        return {"status": "failed", "error": str(e)}

def list_printers(args):
    try:
        result = subprocess.check_output(["lpstat", "-p"]).decode()
        return {"status": "success", "printers": result}
    except Exception as e:
        return {"status": "failed", "error": str(e)}

# -------------------- System Control --------------------

def open_url(args):
    try:
        resolved = resolve_app_name(args["browser"])
        if not resolved:
            return {"status": "failed", "error": f"Browser '{args['browser']}' not found"}
        subprocess.run(["open", "-a", resolved, args["url"]])
        return {"status": "success"}
    except Exception as e:
        return {"status": "failed", "error": str(e)}

def open_browser(args):
    try:
        resolved = resolve_app_name(args["browser"])
        subprocess.run(["open", "-a", resolved])
        return {"status": "success"}
    except Exception as e:
        return {"status": "failed", "error": str(e)}

def close_browser(args):
    try:
        resolved = resolve_app_name(args["browser"])
        subprocess.run(["osascript", "-e", f'tell application "{resolved}" to quit'])
        return {"status": "success"}
    except Exception as e:
        return {"status": "failed", "error": str(e)}

def lock_screen(args):
    try:
        subprocess.run(["osascript", "-e", 'tell application "System Events" to keystroke "q" using {control down, command down}'])
        return {"status": "success"}
    except Exception as e:
        return {"status": "failed", "error": str(e)}

def take_screenshot(args):
    try:
        # Ensure screenshot directory exists
        SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)

        action_id = args.get("action_id", f"snap_{int(time.time())}")
        filename = f"{action_id}.png"
        path = SCREENSHOT_DIR / filename

        # Take the screenshot
        image = ImageGrab.grab()
        image.save(path, format="PNG")

        # Track it in memory
        track_screenshot(str(path))

        print(f"[🖼️ Screenshot saved] {path}")
        return { "status": "success", "screenshot_path": str(path) }

    except Exception as e:
        return { "status": "failed", "error": str(e) }

def say_text(args):
    try:
        subprocess.run(["say", args["text"]])
        return {"status": "success"}
    except Exception as e:
        return {"status": "failed", "error": str(e)}

def set_volume(args):
    try:
        subprocess.run(["osascript", "-e", f"set volume output volume {int(args['level'])}"])
        return {"status": "success"}
    except Exception as e:
        return {"status": "failed", "error": str(e)}

def sleep_system(args):
    try:
        subprocess.run(["pmset", "sleepnow"])
        return {"status": "success"}
    except Exception as e:
        return {"status": "failed", "error": str(e)}

def restart_system(args):
    try:
        subprocess.run(["sudo", "shutdown", "-r", "now"])
        return {"status": "success"}
    except Exception as e:
        return {"status": "failed", "error": str(e)}

def shutdown_system(args):
    try:
        subprocess.run(["sudo", "shutdown", "-h", "now"])
        return {"status": "success"}
    except Exception as e:
        return {"status": "failed", "error": str(e)}

def enforce_app_fullscreen(bundle_id, timeout=10):
    """
    Ensure the front window of the app with the given bundle_id is in full screen.
    If not, send the fullscreen shortcut and wait until the minimize button is disabled or timeout.
    Returns True if fullscreen enforced, False otherwise.
    """
    app = Om_E_Py.ome.getAppRefByBundleId(bundle_id)
    if not app:
        print(f"[ERROR] App with bundle_id={bundle_id} not found.")
        return False
    app.activate()
    time.sleep(1)
    start = time.time()
    while time.time() - start < timeout:
        win = getattr(app, 'AXFocusedWindow', None)
        if not win:
            wins = getattr(app, 'AXWindows', [])
            win = wins[0] if wins else None
        if not win:
            print("[ERROR] No window found for app.")
            return False
        # Find the minimize button
        min_btn = None
        for child in getattr(win, 'AXChildren', []):
            if getattr(child, 'AXRole', None) == 'AXButton' and getattr(child, 'AXSubrole', None) == 'AXMinimizeButton':
                min_btn = child
                break
        if min_btn:
            enabled = getattr(min_btn, 'AXEnabled', True)
            if not enabled:
                print("[INFO] Window is already in full screen (minimize disabled).")
                return True
            else:
                print("[INFO] Window is not in full screen. Sending fullscreen shortcut...")
                script = '''
                tell application \"System Events\"
                    keystroke \"f\" using {control down, command down}
                end tell
                '''
                subprocess.run(['osascript', '-e', script])
                time.sleep(1.5)
        else:
            print("[INFO] Minimize button not found. Assuming window is in full screen mode.")
            return True
    print("[ERROR] Timed out waiting for window to enter full screen.")
    return False

def focus_app(bundle_id, fullscreen=False, timeout=10):
    """
    Focuses the app with the given bundle_id. If not running, launches it.
    If fullscreen=True, also enforces full screen.
    Returns True if successful, False otherwise.
    """
    try:
        try:
            app = Om_E_Py.ome.getAppRefByBundleId(bundle_id)
        except Exception as e:
            print(f"[INFO] Om_E_Py.ome.getAppRefByBundleId threw: {e}")
            app = None
        if not app:
            print(f"[INFO] App with bundle_id={bundle_id} not running. Launching...")
            result = launch_app_by_bundle_id(bundle_id, fullscreen=fullscreen)
            if result.get("status") != "success":
                print(f"[ERROR] Could not launch app with bundle_id={bundle_id}")
                return False
            # Wait for app to appear
            for _ in range(10):
                try:
                    app = Om_E_Py.ome.getAppRefByBundleId(bundle_id)
                except Exception as e:
                    app = None
                if app:
                    break
                time.sleep(1)
            else:
                print(f"[ERROR] App with bundle_id={bundle_id} did not appear after launch.")
                return False
        app.activate()
        time.sleep(1)
        if fullscreen:
            return enforce_app_fullscreen(bundle_id, timeout=timeout)
        return True
    except Exception as e:
        print(f"[ERROR] Exception in focus_app: {e}")
        return False

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Test launching an app by bundle ID using system_handler.")
    parser.add_argument("--bundle-id", required=True, help="Bundle ID of the app to launch")
    parser.add_argument("--fullscreen", action="store_true", help="Launch the app in fullscreen mode")
    args = parser.parse_args()
    result = launch_app_by_bundle_id(args.bundle_id, fullscreen=args.fullscreen)
    print(f"[RESULT] {result}")
