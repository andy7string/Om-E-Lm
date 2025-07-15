"""
Om_E_Py/ome/utils/windows/winD_controller.py

This module is part of the Om_E_Lm project. It provides a consolidated event listener and window state manager for macOS applications, combining app quit detection and real-time window classification into a single, robust controller.

Main Purpose:
- Monitors application launch and quit events for a target app (by bundle ID).
- Monitors and classifies all windows for the target app, including main windows, sheets, dialogs, and special windows (e.g., FilePicker).
- Writes real-time window state and active target information to JSONL files for use by navigation and automation layers.
- Replaces the need for separate app_quit_listener.py, clean_event_listener_classified.py, and combined_event_listener.py scripts.
- Uses multiprocessing to run app quit and window event listeners in parallel, ensuring reliability and isolation.

Key Features:
- App Quit Listener: Uses AppKit notifications to detect app launch/quit and updates status in the shared state file.
- Window Event Listener: Polls the accessibility API to detect new windows, focus changes, and classifies window types.
- Real-Time State Files: Writes window state and active target info to Om_E_Py/ome/data/windows/win_<bundleid>.jsonl and updates Om_E_Py/ome/data/windows/active_target_Bundle_ID.json.
- Robust Recovery: Handles app relaunch, switching, and refresh requests gracefully.
- Mouse Corner Exit: Move mouse to top-right corner to exit the listener process.
- Multiprocessing: Runs both listeners in separate processes for maximum reliability.
- Configurable via env.py and .env at the project root.

How to Use (Command Line):
    python -m Om_E_Py.ome.utils.windows.winD_controller [bundle_id_or_app_name]

Arguments:
    [bundle_id_or_app_name]: (optional) The bundle ID or app name to monitor. If omitted, uses the active bundle ID from the shared state file.

Example:
    python -m Om_E_Py.ome.utils.windows.winD_controller com.apple.mail
    # Starts monitoring Mail for app quit/launch and window events.

Output:
- Writes real-time window state to Om_E_Py/ome/data/windows/win_<bundleid>.jsonl
- Updates active bundle ID and status in Om_E_Py/ome/data/windows/active_target_Bundle_ID.json
- Prints status and event information to the console for debugging.

When to Use:
- To provide real-time window and app state for navigation, automation, or accessibility workflows.
- As the backend event/state manager for Om_E_Lm navigation and UI automation layers.
- To replace legacy event listeners with a single, robust, and multiprocessing-aware controller.

"""
import sys
import os

# Get project root from env.py to ensure consistency. This is more robust
# than calculating from __file__, especially when dealing with multiprocessing.
from env import PROJECT_ROOT, UI_POLL_INTERVAL, UI_ACTIVE_BUNDLE_JSON, UI_WIN_LIST_DIR

# Add the project root to the Python path to allow absolute imports from 'ome'
project_root = str(PROJECT_ROOT)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

import time
import signal
import multiprocessing
import threading
import argparse
import json
from datetime import datetime

# ==============================================================================
# SECTION 1: APP QUIT LISTENER LOGIC
# All code related to monitoring application launch/quit events.
# ==============================================================================

def run_app_quit_listener(project_root):
    """
    Monitors for application launch and quit events using AppKit notifications.
    This function is intended to be run in a separate process.
    """
    # No longer need to change directory. We rely on absolute paths from env.py.
    # os.chdir(project_root)

    import objc
    from Foundation import NSObject, NSRunLoop, NSDate
    from AppKit import NSWorkspace

    def is_app_running(bundle_id):
        ws = NSWorkspace.sharedWorkspace()
        running_apps = ws.runningApplications()
        for app in running_apps:
            if app.bundleIdentifier() == bundle_id:
                return True
        return False

    def update_json_status(bundle_id, status):
        try:
            with open(UI_ACTIVE_BUNDLE_JSON, "r", encoding="utf-8") as f:
                data = json.load(f)
            if data.get("active_bundle_id") != bundle_id:
                return
            if data.get("status") == status:
                return
            data["status"] = status
            data["last_updated"] = time.strftime("%Y-%m-%dT%H:%M:%S.%fZ", time.gmtime())
            with open(UI_ACTIVE_BUNDLE_JSON, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"[AppQuitListener ERROR] Could not update status in {UI_ACTIVE_BUNDLE_JSON}: {e}")

    class AppEventListener(NSObject):
        def initWithBundleId_(self, bundle_id):
            self = objc.super(AppEventListener, self).init()
            if self is None: return None
            self.bundle_id = bundle_id
            self.nc = NSWorkspace.sharedWorkspace().notificationCenter()
            self.addObservers()
            return self

        def addObservers(self):
            self.nc.addObserver_selector_name_object_(self, self.appLaunched_, "NSWorkspaceDidLaunchApplicationNotification", None)
            self.nc.addObserver_selector_name_object_(self, self.appTerminated_, "NSWorkspaceDidTerminateApplicationNotification", None)

        def removeObservers(self):
            self.nc.removeObserver_(self)

        def appLaunched_(self, notification):
            app_info = notification.userInfo()
            bundle_id = app_info["NSApplicationBundleIdentifier"]
            if bundle_id == self.bundle_id:
                print(f"🚀 [AppQuitListener] App launched: {bundle_id}")
                update_json_status(self.bundle_id, "running")

        def appTerminated_(self, notification):
            app_info = notification.userInfo()
            bundle_id = app_info["NSApplicationBundleIdentifier"]
            if bundle_id == self.bundle_id:
                print(f"🛑 [AppQuitListener] App quit: {bundle_id}")
                update_json_status(self.bundle_id, "quit")

    def read_active_bundle_id():
        try:
            with open(UI_ACTIVE_BUNDLE_JSON, "r", encoding="utf-8") as f:
                data = json.load(f)
            bundle_id = data.get("active_bundle_id")
            if not bundle_id or not isinstance(bundle_id, str):
                return None
            return bundle_id
        except Exception:
            return None

    print(f"[AppQuitListener] Monitoring for launch/quit events based on {UI_ACTIVE_BUNDLE_JSON}")
    listener = None
    current_bundle_id = None
    last_status = None
    try:
        while True:
            bundle_id = read_active_bundle_id()
            if bundle_id and bundle_id != current_bundle_id:
                if listener:
                    listener.removeObservers()
                listener = AppEventListener.alloc().initWithBundleId_(bundle_id)
                current_bundle_id = bundle_id
                print(f"[AppQuitListener] Now monitoring: {current_bundle_id}")
                status = "running" if is_app_running(current_bundle_id) else "quit"
                update_json_status(current_bundle_id, status)
                last_status = status
            elif bundle_id and current_bundle_id:
                status = "running" if is_app_running(current_bundle_id) else "quit"
                if status != last_status:
                    update_json_status(current_bundle_id, status)
                    last_status = status
            NSRunLoop.currentRunLoop().runUntilDate_(NSDate.dateWithTimeIntervalSinceNow_(UI_POLL_INTERVAL))
    except (KeyboardInterrupt, SystemExit):
        pass
    finally:
        if listener:
            listener.removeObservers()
        print("[AppQuitListener] Shutting down.")


# ==============================================================================
# SECTION 2: WINDOW EVENT LISTENER LOGIC
# All code related to monitoring and classifying windows for an application.
# ==============================================================================

def run_clean_event_listener_classified(project_root, cli_args):
    """
    Monitors and classifies windows for a target application.
    This function is intended to be run in a separate process.
    """
    # Set up the environment for the child process.
    # We add the project root to sys.path but avoid changing the CWD.
    sys.path.insert(0, project_root)

    from Om_E_Py.ome.AXClasses import NativeUIElement
    from Om_E_Py.ome.utils.builder.app.app_focus import ensure_app_focus
    from Om_E_Py.ome.utils.builder.app.appList_controller import bundle_id_exists, get_bundle_id
    from Om_E_Py.ome.controllers.bundles.bundleID_controller import BundleIDController
    
    class MouseExitMonitor:
        def __init__(self, corner_size=50):
            self.corner_size = corner_size
            self.is_running = False
            import Quartz
            self.screen_width = Quartz.CGDisplayPixelsWide(Quartz.CGMainDisplayID())
            self.screen_height = Quartz.CGDisplayPixelsHigh(Quartz.CGMainDisplayID())
        def _get_mouse_position(self):
            import AppKit
            import Quartz
            loc = AppKit.NSEvent.mouseLocation()
            x = int(loc.x)
            y = int(Quartz.CGDisplayPixelsHigh(Quartz.CGMainDisplayID()) - loc.y)
            return (x, y)
        def _is_in_corner(self, x, y):
            return (x >= self.screen_width - self.corner_size and y <= self.corner_size)
        def _monitor(self):
            while self.is_running:
                try:
                    pos = self._get_mouse_position()
                    if self._is_in_corner(pos[0], pos[1]):
                        print(f"[WindowListener] Mouse in exit corner! Shutting down main process...")
                        os.kill(os.getppid(), signal.SIGINT)
                        break
                    time.sleep(0.1)
                except Exception:
                    break
        def start(self):
            self.is_running = True
            self.monitor_thread = threading.Thread(target=self._monitor, daemon=True)
            self.monitor_thread.start()
        def stop(self):
            self.is_running = False

    def get_attr_safe(obj, attr):
        try:
            return getattr(obj, attr, None)
        except Exception:
            return None

    def get_window_type_or_identifier(window_or_sheet):
        if isinstance(window_or_sheet, dict):
            ax_identifier = window_or_sheet.get('AXIdentifier')
        else:
            ax_identifier = get_attr_safe(window_or_sheet, 'AXIdentifier')
        if ax_identifier == "open-panel": return "FilePicker"
        if ax_identifier and "messageViewer" in ax_identifier: return ax_identifier
        if ax_identifier == "Mail.sendMessageAlert": return "SendMessageAlert"
        if ax_identifier: return ax_identifier
        return None

    def is_window_active(win, sheets):
        if get_attr_safe(win, 'AXFocused') or get_attr_safe(win, 'AXMain'): return True
        for sheet in sheets:
            if sheet.get('is_active'): return True
        return False

    def scan_sheet(sheet, parent_window_number, sheet_index):
        ax_identifier = get_attr_safe(sheet, 'AXIdentifier')
        return {
            'sheet_index': sheet_index,
            'AXTitle': get_attr_safe(sheet, 'AXTitle'), 'AXIdentifier': ax_identifier,
            'AXRole': get_attr_safe(sheet, 'AXRole'), 'AXRoleDescription': get_attr_safe(sheet, 'AXRoleDescription'),
            'AXSubrole': get_attr_safe(sheet, 'AXSubrole'), 'AXMain': get_attr_safe(sheet, 'AXMain'),
            'AXFocused': get_attr_safe(sheet, 'AXFocused'), 'AXModal': get_attr_safe(sheet, 'AXModal'),
            'is_active': bool(get_attr_safe(sheet, 'AXFocused') or get_attr_safe(sheet, 'AXModal')),
            'AXSize': list(get_attr_safe(sheet, 'AXSize')) if get_attr_safe(sheet, 'AXSize') else None,
            'timestamp': datetime.utcnow().isoformat() + 'Z', 'parent_window_number': parent_window_number,
            'window_type': get_window_type_or_identifier(sheet)
        }

    def scan_window(win, window_number):
        sheets = []
        children = get_attr_safe(win, 'AXChildren') or []
        for idx, child in enumerate(children):
            if get_attr_safe(child, 'AXRole') in ('AXSheet', 'AXDialog'):
                sheets.append(scan_sheet(child, window_number, idx))
        return {
            'window_number': window_number, 'AXTitle': get_attr_safe(win, 'AXTitle'),
            'AXIdentifier': get_attr_safe(win, 'AXIdentifier'), 'AXRole': get_attr_safe(win, 'AXRole'),
            'AXRoleDescription': get_attr_safe(win, 'AXRoleDescription'), 'AXSubrole': get_attr_safe(win, 'AXSubrole'),
            'AXMain': get_attr_safe(win, 'AXMain'), 'AXFocused': get_attr_safe(win, 'AXFocused'),
            'AXModal': get_attr_safe(win, 'AXModal'), 'is_active': is_window_active(win, sheets),
            'AXSize': list(get_attr_safe(win, 'AXSize')) if get_attr_safe(win, 'AXSize') else None,
            'timestamp': datetime.utcnow().isoformat() + 'Z', 'sheets': sheets,
            'window_type': get_window_type_or_identifier(win)
        }
    
    def get_window_signature(window):
        try:
            return f"{getattr(window, 'AXTitle', '')}|{getattr(window, 'AXRole', '')}|{get_window_type_or_identifier(window)}|{getattr(window, 'AXPosition', '')}|{getattr(window, 'AXSize', '')}"
        except Exception as e:
            return f"unknown|{e}"

    def get_active_target(windows, bundle_id):
        def get_title(item): return item.get('AXTitle') or 'Unknown'
        for win in windows:
            if win['is_active'] and win.get('sheets'):
                sheet = win['sheets'][-1]
                ref = get_window_type_or_identifier(sheet) or get_title(sheet).replace(' ', '_')[:32]
                return {"type": "sheet", "window_title": get_title(win), "window_ref": ref, "nav_map_name": f"appNav_{bundle_id}_{ref}.jsonl", "timestamp": sheet.get('timestamp')}
        for win in windows:
            if win.get('AXSubrole') == 'AXFloatingWindow':
                ref = get_window_type_or_identifier(win) or get_title(win).replace(' ', '_')[:32]
                return {"type": "float", "window_title": get_title(win), "window_ref": ref, "nav_map_name": f"appNav_{bundle_id}_{ref}.jsonl", "timestamp": win.get('timestamp')}
        for win in windows:
            if win['is_active']:
                ref = get_window_type_or_identifier(win) or get_title(win).replace(' ', '_')[:32]
                return {"type": "window", "window_title": get_title(win), "window_ref": ref, "nav_map_name": f"appNav_{bundle_id}_{ref}.jsonl", "timestamp": win.get('timestamp')}
        return None
        
    def reacquire_app_reference(bundle_id):
        """Attempts to focus and get a fresh reference to the application."""
        print(f"[WindowListener] Attempting to re-acquire reference for {bundle_id}...")
        result = ensure_app_focus(bundle_id)
        if result['status'] != 'success':
            print(f"[WindowListener WARNING] Failed to focus {bundle_id} during re-acquisition.")
            return None
        try:
            app_ref = NativeUIElement.getAppRefByBundleId(bundle_id)
            print(f"[WindowListener] Successfully re-acquired reference for {bundle_id}.")
            return app_ref
        except Exception as e:
            print(f"[WindowListener ERROR] Could not get app reference for {bundle_id}: {e}")
            return None

    parser = argparse.ArgumentParser(description="Monitor a macOS app for window events.")
    parser.add_argument("bundle_id", nargs='?', default=None, help="Bundle ID or app name to monitor.")
    args = parser.parse_args(cli_args)

    bundle_controller = BundleIDController()
    bundle_id = None
    if args.bundle_id:
        canonical_id = bundle_id_exists(args.bundle_id) or bundle_id_exists(get_bundle_id(args.bundle_id))
        if canonical_id:
            bundle_id = canonical_id
            bundle_controller.set_active_bundle_id(bundle_id, "winD_controller_init")
        else:
            print(f"[WindowListener ERROR] Cannot find bundle ID for '{args.bundle_id}'. Exiting.")
            return
    else:
        bundle_id = bundle_controller.get_active_bundle_id()
        if not bundle_id:
            print("[WindowListener ERROR] No active bundle ID set. Please provide one or set it first. Exiting.")
            return

    print("=" * 60)
    print(f"[WindowListener] Starting for: {bundle_id}")
    print("=" * 60)
    
    mouse_monitor = MouseExitMonitor()
    mouse_monitor.start()
    
    app = None  # Start with no app reference
    existing_windows = set()
    last_poll_time = 0

    try:
        while True:
            # Main polling loop, targeting configured interval
            if time.time() - last_poll_time < UI_POLL_INTERVAL:
                time.sleep(0.05) # Sleep for a short duration to prevent busy-waiting
                continue
            last_poll_time = time.time()

            # Read the shared state file directly
            state = {}
            try:
                with open(UI_ACTIVE_BUNDLE_JSON, "r") as f:
                    state = json.load(f)
            except (FileNotFoundError, json.JSONDecodeError):
                print(f"[WindowListener WARNING] Could not read state file, will retry. Path attempted: {UI_ACTIVE_BUNDLE_JSON}")
                time.sleep(1)
                continue

            active_bundle_id = state.get("active_bundle_id")
            app_status = state.get("status")
            refresh_needed = state.get("refresh", False)

            # 1. Handle app switching
            if active_bundle_id and active_bundle_id != bundle_id:
                print(f"\n[WindowListener] Switching from '{bundle_id}' to '{active_bundle_id}'")
                bundle_id = active_bundle_id
                app = None  # Reset app reference for new bundle
                existing_windows.clear()
                continue # Restart loop with new app

            # 2. Handle refresh requests or app quits for the CURRENT app
            if refresh_needed or (app_status == 'quit' and app is not None):
                if refresh_needed:
                    print(f"[WindowListener] Refresh requested for {bundle_id}.")
                    bundle_controller.clear_refresh_flag() # Consume the flag
                if app_status == 'quit':
                    print(f"[WindowListener] App '{bundle_id}' has quit. Pausing window scan.")
                
                app = None # Drop the stale reference
                existing_windows.clear()
                # Loop will now wait for status to be 'running' before re-acquiring
            
            # 3. If app is not running, wait.
            if app_status not in ['running', 'active']:
                print(f"[WindowListener] App '{bundle_id}' is not running. Status: '{app_status}'. Waiting...")
                time.sleep(1)
                continue
            
            # 4. If app is running but we have no reference, try to get one
            if app is None:
                print(f"[WindowListener] App '{bundle_id}' is running but no reference. Attempting to acquire...")
                app = reacquire_app_reference(bundle_id)
                if app is None:
                    print(f"[WindowListener] Failed to acquire app reference for '{bundle_id}'. Will retry...")
                    time.sleep(1)
                    continue
            
            # 4. If we have an app reference and it's running, scan for windows
            os.makedirs(UI_WIN_LIST_DIR, exist_ok=True)
            output_path = os.path.join(UI_WIN_LIST_DIR, f"win_{bundle_id}.jsonl")
            try:
                all_window_infos = [scan_window(w, i) for i, w in enumerate(app.windows() or [])]
                current_windows = {get_window_signature(w) for w in (app.windows() or [])}
            except Exception:
                # This can happen if the app quits between our status check and here.
                # The loop will detect the 'quit' status on the next iteration and recover.
                print(f"[WindowListener WARNING] Lost connection to {bundle_id}. Will try to recover.")
                app = None
                continue

            if current_windows != existing_windows:
                print(f"[WindowListener] Window change detected for {bundle_id}.")
                existing_windows = current_windows

            active_target = get_active_target(all_window_infos, bundle_id)
            # Only write if window_title or window_ref changes
            if not hasattr(run_clean_event_listener_classified, 'last_window_title'):
                run_clean_event_listener_classified.last_window_title = None
                run_clean_event_listener_classified.last_window_ref = None
            window_title = active_target.get('window_title') if active_target else None
            window_ref = active_target.get('window_ref') if active_target else None
            if (window_title != run_clean_event_listener_classified.last_window_title) or \
               (window_ref != run_clean_event_listener_classified.last_window_ref):
                jsonl_data = {"active_target": active_target, "bundle_id": bundle_id, "source": "winD_controller"}
                with open(output_path, 'w', encoding='utf-8') as f:
                    json.dump(jsonl_data, f, ensure_ascii=False, indent=2)
                run_clean_event_listener_classified.last_window_title = window_title
                run_clean_event_listener_classified.last_window_ref = window_ref
                print(f"[winD_controller] Wrote new window state for {bundle_id} (title/ref changed)")
            
    except (KeyboardInterrupt, SystemExit):
        pass
    finally:
        mouse_monitor.stop()
        print("[WindowListener] Shutting down.")


# ==============================================================================
# SECTION 3: MAIN ORCHESTRATION
# ==============================================================================

if __name__ == "__main__":
    # The project_root is now defined globally by importing it from env.py.
    # This ensures a single, reliable source of truth for the project path,
    # which is crucial for the multiprocessing context used below.
    cli_args = sys.argv[1:]

    # For macOS, 'fork' is a bit more reliable for inheriting state, but we
    # stick to the safer default ('spawn') and set up the environment explicitly.
    
    print("[winD_controller] Starting event listeners...")
    
    # Pass the absolute project_root string to the subprocesses
    p1 = multiprocessing.Process(target=run_app_quit_listener, args=(project_root,))
    p2 = multiprocessing.Process(target=run_clean_event_listener_classified, args=(project_root, cli_args))
    
    processes = [p1, p2]
    
    p1.start()
    p2.start()

    def shutdown(signum, frame):
        print("\n[winD_controller] Signal received. Shutting down subprocesses...")
        for p in processes:
            if p.is_alive():
                p.terminate() # Send SIGTERM
        
        # Wait a moment for graceful shutdown
        time.sleep(1)
        
        for p in processes:
            if p.is_alive():
                print(f"[winD_controller] Process {p.pid} did not terminate, killing.")
                p.kill() # Send SIGKILL

        print("[winD_controller] All subprocesses stopped.")
        sys.exit(0)

    signal.signal(signal.SIGINT, shutdown)
    signal.signal(signal.SIGTERM, shutdown)

    try:
        # Wait for either process to exit
        while all(p.is_alive() for p in processes):
            time.sleep(0.5)
    except KeyboardInterrupt:
        shutdown(None, None)
    finally:
        # Final cleanup attempt
        shutdown(None, None) 