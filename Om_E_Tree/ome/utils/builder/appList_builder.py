import os
import json
from pathlib import Path
from env import TREE_APP_LIST_PATH, TREE_APP_LIST_DIR
import plistlib
import time

APP_LIST_PATH = Path(TREE_APP_LIST_PATH)
APP_LIST_DIR = Path(TREE_APP_LIST_DIR)

# Directories to scan for macOS apps
APP_DIRS = [
    Path("/Applications"),
    Path("/System/Applications"),
    Path("/System/Library/CoreServices")  # ✅ This adds Finder
]

def get_bundle_id(app_path):
    """
    Given a .app Path, returns its bundle ID from Info.plist, or None if not found.
    """
    info_plist = app_path / "Contents" / "Info.plist"
    if info_plist.exists():
        try:
            with open(info_plist, "rb") as f:
                plist = plistlib.load(f)
                return plist.get("CFBundleIdentifier")
        except Exception:
            return None
    return None

# ===================================================
# 🔍 Scan for installed .app bundles (recursively)
# ===================================================

def scan_apps():
    """
    Recursively scans known macOS application directories for installed apps.
    Returns:
        list: Sorted list of dicts with app names and bundle IDs.
    """
    apps = []
    for app_dir in APP_DIRS:
        if app_dir.exists():
            for item in app_dir.rglob("*.app"):
                bundle_id = get_bundle_id(item)
                apps.append({
                    "name": item.stem,
                    "bundle_id": bundle_id
                })
    # Remove duplicates (some apps may appear in multiple locations)
    seen = set()
    unique_apps = []
    for app in apps:
        key = (app["name"].lower(), app["bundle_id"])
        if key not in seen:
            seen.add(key)
            unique_apps.append(app)
    return sorted(unique_apps, key=lambda x: x["name"].lower())

# ===================================================
# 📦 Load or rebuild application list
# ===================================================

def load_app_list(refresh=False):
    """
    Loads cached app list from disk. If not found, invalid, or refresh=True,
    or if the file is older than 1 day, it rebuilds the list by scanning the system.

    Args:
        refresh (bool): Force rebuild of the app list.

    Returns:
        list: List of apps (dicts with "name").
    """
    max_age_seconds = 24 * 60 * 60  # 1 day
    if APP_LIST_PATH.exists():
        mtime = APP_LIST_PATH.stat().st_mtime
        if (time.time() - mtime) > max_age_seconds:
            refresh = True

    if not refresh and APP_LIST_PATH.exists():
        try:
            with open(APP_LIST_PATH, "r") as f:
                data = json.load(f)
                if isinstance(data, list) and all("name" in a for a in data):
                    return data
        except Exception:
            print("⚠️ Failed to load cached app list. Rebuilding...")

    # 🔄 Rebuild the app list and save it
    apps = scan_apps()
    APP_LIST_DIR.mkdir(parents=True, exist_ok=True)
    with open(APP_LIST_PATH, "w") as f:
        json.dump(apps, f, indent=2)
    print("[REFRESH] App list rebuilt and saved.")
    return apps

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Build or refresh the app list JSON file.")
    parser.add_argument("--refresh", action="store_true", help="Force refresh the app list")
    args = parser.parse_args()
    apps = load_app_list(refresh=args.refresh)
    print(f"[INFO] App list contains {len(apps)} apps.")
