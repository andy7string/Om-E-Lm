import objc
import json
import os
import time
from Foundation import NSObject, NSRunLoop, NSDate
from AppKit import NSWorkspace

ACTIVE_BUNDLE_JSON = "ome/data/windows/active_target_Bundle_ID.json"
POLL_INTERVAL = 0.2

def is_app_running(bundle_id):
    ws = NSWorkspace.sharedWorkspace()
    running_apps = ws.runningApplications()
    for app in running_apps:
        if app.bundleIdentifier() == bundle_id:
            return True
    return False

def update_json_status(bundle_id, status):
    try:
        with open(ACTIVE_BUNDLE_JSON, "r", encoding="utf-8") as f:
            data = json.load(f)
        if data.get("active_bundle_id") != bundle_id:
            return  # Only update if we're monitoring the current bundle id
        if data.get("status") == status:
            return  # No need to update if status is unchanged
        data["status"] = status
        data["last_updated"] = time.strftime("%Y-%m-%dT%H:%M:%S.%fZ", time.gmtime())
        with open(ACTIVE_BUNDLE_JSON, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"[ERROR] Could not update status in {ACTIVE_BUNDLE_JSON}: {e}")

class AppEventListener(NSObject):
    def initWithBundleId_(self, bundle_id):
        self = objc.super(AppEventListener, self).init()
        if self is None:
            return None
        self.bundle_id = bundle_id
        self.nc = NSWorkspace.sharedWorkspace().notificationCenter()
        self.addObservers()
        return self

    def addObservers(self):
        self.nc.addObserver_selector_name_object_(
            self,
            self.appLaunched_,
            "NSWorkspaceDidLaunchApplicationNotification",
            None
        )
        self.nc.addObserver_selector_name_object_(
            self,
            self.appTerminated_,
            "NSWorkspaceDidTerminateApplicationNotification",
            None
        )

    def removeObservers(self):
        self.nc.removeObserver_(self)

    def appLaunched_(self, notification):
        app_info = notification.userInfo()
        bundle_id = app_info["NSApplicationBundleIdentifier"]
        if bundle_id == self.bundle_id:
            print(f"🚀 App launched: {bundle_id}")
            update_json_status(self.bundle_id, "running")

    def appTerminated_(self, notification):
        app_info = notification.userInfo()
        bundle_id = app_info["NSApplicationBundleIdentifier"]
        if bundle_id == self.bundle_id:
            print(f"🛑 App quit: {bundle_id}")
            update_json_status(self.bundle_id, "quit")

def read_active_bundle_id():
    try:
        with open(ACTIVE_BUNDLE_JSON, "r", encoding="utf-8") as f:
            data = json.load(f)
        bundle_id = data.get("active_bundle_id")
        if not bundle_id or not isinstance(bundle_id, str):
            print(f"[ERROR] active_bundle_id missing or invalid in {ACTIVE_BUNDLE_JSON}")
            return None
        return bundle_id
    except Exception as e:
        print(f"[ERROR] Could not read {ACTIVE_BUNDLE_JSON}: {e}")
        return None

def main():
    print(f"Listening for launch/quit events for bundle ID in: {ACTIVE_BUNDLE_JSON}")
    print("Polling for bundle ID changes every 0.2s. Press Ctrl+C to exit.")
    listener = None
    current_bundle_id = None
    last_status = None
    try:
        while True:
            bundle_id = read_active_bundle_id()
            if bundle_id != current_bundle_id and bundle_id is not None:
                if listener:
                    listener.removeObservers()
                    print(f"[INFO] Stopped monitoring: {current_bundle_id}")
                listener = AppEventListener.alloc().initWithBundleId_(bundle_id)
                current_bundle_id = bundle_id
                print(f"[INFO] Now monitoring: {current_bundle_id}")
                # Immediately update status on switch
                status = "running" if is_app_running(current_bundle_id) else "quit"
                update_json_status(current_bundle_id, status)
                last_status = status
            elif bundle_id is not None and current_bundle_id is not None:
                # Poll app status and update if changed
                status = "running" if is_app_running(current_bundle_id) else "quit"
                if status != last_status:
                    update_json_status(current_bundle_id, status)
                    last_status = status
            NSRunLoop.currentRunLoop().runUntilDate_(NSDate.dateWithTimeIntervalSinceNow_(POLL_INTERVAL))
    except KeyboardInterrupt:
        print("\nExiting...")
    finally:
        if listener:
            listener.removeObservers()
        print("Cleanup complete.")

if __name__ == "__main__":
    main() 