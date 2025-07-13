"""
App List Builder & Lookup Utility

This script manages and looks up macOS applications by their names and bundle IDs. It is designed to help you programmatically find bundle IDs for app names (and vice versa), keep an up-to-date list of installed user-visible macOS apps, and automate tasks that require bundle IDs.

====================
PURPOSE
====================
- Scans standard macOS application directories for .app bundles.
- Extracts app names and bundle IDs from each found application.
- Caches the app list as a JSONL file (location is configurable via your environment).
- Provides fast lookup utilities to get an app name from a bundle ID, or a bundle ID from an app name.
- Offers a command-line interface (CLI) for refreshing the app list, performing lookups, and checking existence.

====================
KEY FEATURES
====================
- Automatic caching: The app list is cached and only rebuilt if:
    * The cache file is missing, invalid, or older than 1 day.
    * The --refresh flag is used.
- Lookups (all with fuzzy fallback!):
    * get_app_name(bundle_id) returns the app name for a given bundle ID (fuzzy fallback if no exact match).
    * get_bundle_id(app_name) returns the bundle ID for a given app name (case-insensitive, fuzzy fallback if no exact match).
    * app_name_exists(app_name) returns True if the app name exists (case-insensitive, fuzzy fallback if no exact match).
    * bundle_id_exists(bundle_id) returns True if the bundle ID exists (fuzzy fallback if no exact match).
- Python API: You can import and use get_app_name, get_bundle_id, app_name_exists, and bundle_id_exists in your own code.
- CLI Usage:
    * --refresh                Force rebuild of the app list
    * --bundle-to-name <id>    Lookup app name from bundle ID (fuzzy fallback)
    * --name-to-bundle <name>  Lookup bundle ID from app name (fuzzy fallback)
    * --bundle-exists <id>     Check if a bundle ID exists (True/False, fuzzy fallback)
    * --name-exists <name>     Check if an app name exists (True/False, fuzzy fallback)

====================
HOW IT WORKS
====================
1. Scanning: Recursively scans standard macOS app directories (like /Applications, /System/Applications, etc.) for .app bundles.
2. Filtering: Filters out background-only and non-user-visible apps.
3. Extracting Info: For each app, reads the Info.plist to get the app's name and bundle ID.
4. Caching: Results are cached in a JSONL file for fast future lookups.
5. Lookups: Uses in-memory dictionaries for fast name <-> bundle ID lookups, with fuzzy fallback using rapidfuzz if no exact match is found (score threshold: 80).

====================
PYTHON API USAGE EXAMPLES
====================
from ome.utils.builder.app.appList_controller import get_app_name, get_bundle_id, app_name_exists, bundle_id_exists

# Lookup app name from bundle ID
print(get_app_name('com.apple.mail'))        # 'Mail' (exact match)
print(get_app_name('com.apple.mial'))        # 'Mail' (fuzzy match)
print(get_app_name('com.apple.notarealapp')) # None (does not exist)

# Lookup bundle ID from app name
print(get_bundle_id('Safari'))        # 'com.apple.Safari' (exact match)
print(get_bundle_id('Safri'))         # 'com.apple.Safari' (fuzzy match)
print(get_bundle_id('NotARealApp'))   # None (does not exist)

# Check if app name exists
print(app_name_exists('Safari'))      # True (exact match)
print(app_name_exists('Safri'))       # True (fuzzy match)
print(app_name_exists('NotARealApp')) # False (does not exist)

# Check if bundle ID exists
print(bundle_id_exists('com.apple.mail'))        # True (exact match)
print(bundle_id_exists('com.apple.mial'))        # True (fuzzy match)
print(bundle_id_exists('com.apple.notarealapp')) # False (does not exist)

====================
COMMAND LINE USAGE EXAMPLES
====================
# Rebuild the app list cache
python -m ome.utils.builder.app.appList_controller --refresh

# Lookup app name from bundle ID
python -m ome.utils.builder.app.appList_controller --bundle-to-name com.apple.mail
# Output: Mail
python -m ome.utils.builder.app.appList_controller --bundle-to-name com.apple.mial
# Output: Mail (fuzzy match)
python -m ome.utils.builder.app.appList_controller --bundle-to-name com.apple.notarealapp
# Output: [NOT FOUND] No app name for bundle ID: com.apple.notarealapp

# Lookup bundle ID from app name
python -m ome.utils.builder.app.appList_controller --name-to-bundle Safari
# Output: com.apple.Safari
python -m ome.utils.builder.app.appList_controller --name-to-bundle Safri
# Output: com.apple.Safari (fuzzy match)
python -m ome.utils.builder.app.appList_controller --name-to-bundle NotARealApp
# Output: [NOT FOUND] No bundle ID for app name: NotARealApp

# Check if an app name exists (returns canonical name or None)
python -m ome.utils.builder.app.appList_controller --name-exists Safari
# Output: safari
python -m ome.utils.builder.app.appList_controller --name-exists Safri
# Output: safari (fuzzy match)
python -m ome.utils.builder.app.appList_controller --name-exists NotARealApp
# Output: None

# Check if a bundle ID exists (returns canonical bundle ID or None)
python -m ome.utils.builder.app.appList_controller --bundle-exists com.apple.mail
# Output: com.apple.mail
python -m ome.utils.builder.app.appList_controller --bundle-exists com.apple.mial
# Output: com.apple.mail (fuzzy match)
python -m ome.utils.builder.app.appList_controller --bundle-exists com.apple.notarealapp
# Output: None

If no options are provided, the script will print the number of apps in the current app list cache.

====================
WHEN TO USE
====================
- When you need to programmatically find the bundle ID for a given app name (or vice versa), even if you have a typo or partial name.
- When you want to keep an up-to-date list of installed, user-visible macOS apps.
- When you want to script or automate app launching, focusing, or accessibility tasks that require bundle IDs.

"""
import os
import json
from pathlib import Path
from ome.utils.env.env import APP_LIST_DIR  # Only need the directory now
import plistlib
import time
from rapidfuzz import process

# Directories to scan for macOS apps
APP_DIRS = [
    Path("/Applications"),
    Path("/Applications/Utilities"),
    Path("/System/Applications"),
    Path("/System/Library/CoreServices"),  # For Finder and user-facing system apps
]

# Path to the JSONL cache file
JSONL_PATH = APP_LIST_DIR / "app_list.jsonl"

def extract_bundle_id_from_path(app_path):
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

def is_user_visible_app(app_path):
    """
    Returns True if the app is user-visible (not LSUIElement or LSBackgroundOnly, and has a display name or bundle name).
    """
    info_plist = app_path / "Contents" / "Info.plist"
    if not info_plist.exists():
        return False
    try:
        with open(info_plist, "rb") as f:
            plist = plistlib.load(f)
        if plist.get("LSUIElement") in ("1", 1) or plist.get("LSBackgroundOnly") in ("1", 1):
            return False
        if not (plist.get("CFBundleDisplayName") or plist.get("CFBundleName")):
            return False
        return True
    except Exception:
        return False

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
                if not is_user_visible_app(item):
                    continue
                bundle_id = extract_bundle_id_from_path(item)
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
    Loads cached app list from disk (JSONL). If not found, invalid, or refresh=True,
    or if the file is older than 1 day, it rebuilds the list by scanning the system.

    Args:
        refresh (bool): Force rebuild of the app list.

    Returns:
        list: List of apps (dicts with "name").
    """
    max_age_seconds = 24 * 60 * 60  # 1 day
    t0 = time.time()
    if JSONL_PATH.exists():
        mtime = JSONL_PATH.stat().st_mtime
        if (time.time() - mtime) > max_age_seconds:
            refresh = True

    if not refresh and JSONL_PATH.exists():
        try:
            apps = []
            with open(JSONL_PATH, "r") as f:
                for line in f:
                    app = json.loads(line)
                    if "name" in app:
                        apps.append(app)
            if apps:
                print(f"[TIMER] Loaded app list from cache in {time.time() - t0:.3f} seconds.")
                return apps
        except Exception:
            print("⚠️ Failed to load cached app list. Rebuilding...")

    # 🔄 Rebuild the app list and save it
    t1 = time.time()
    apps = scan_apps()
    APP_LIST_DIR.mkdir(parents=True, exist_ok=True)
    with open(JSONL_PATH, "w") as f:
        for app in apps:
            f.write(json.dumps(app, ensure_ascii=False) + "\n")
    print(f"[REFRESH] App list rebuilt and saved in {time.time() - t1:.3f} seconds.")
    print(f"[TIMER] Total time for rebuild and save: {time.time() - t0:.3f} seconds.")
    return apps

# ===================================================
# 🔄 Lookup utilities
# ===================================================

# Internal cache for lookups
_bundle_id_to_name = None
_name_to_bundle_id = None


def _build_lookup_dicts(refresh=False):
    """
    Builds or refreshes the internal lookup dictionaries for fast app name <-> bundle ID lookups.
    """
    global _bundle_id_to_name, _name_to_bundle_id
    apps = load_app_list(refresh=refresh)
    _bundle_id_to_name = {a["bundle_id"]: a["name"] for a in apps if a["bundle_id"]}
    _name_to_bundle_id = {a["name"].lower(): a["bundle_id"] for a in apps if a["bundle_id"]}


def get_app_name(bundle_id, refresh=False):
    """
    Returns the app name for a given bundle ID, or None if not found.
    If no exact match, uses fuzzy matching as a fallback (score >= 80).
    """
    global _bundle_id_to_name
    t0 = time.time()
    if _bundle_id_to_name is None or refresh:
        _build_lookup_dicts(refresh=refresh)
    result = _bundle_id_to_name.get(bundle_id)
    if result is not None:
        print(f"[TIMER] Lookup for bundle_id '{bundle_id}' took {time.time() - t0:.3f} seconds.")
        return result
    # Fuzzy fallback
    bundle_ids = list(_bundle_id_to_name.keys())
    match = process.extractOne(bundle_id, bundle_ids, score_cutoff=80)
    if match:
        best_id, score, _ = match
        print(f"[FUZZY] Closest bundle_id match: {best_id} (score={score})")
        return _bundle_id_to_name[best_id]
    print(f"[TIMER] Lookup for bundle_id '{bundle_id}' took {time.time() - t0:.3f} seconds.")
    return None


def get_bundle_id(app_name, refresh=False):
    """
    Returns the bundle ID for a given app name (case-insensitive), or None if not found.
    If no exact match, uses fuzzy matching as a fallback (score >= 80).
    """
    global _name_to_bundle_id
    t0 = time.time()
    if _name_to_bundle_id is None or refresh:
        _build_lookup_dicts(refresh=refresh)
    result = _name_to_bundle_id.get(app_name.lower())
    if result is not None:
        print(f"[TIMER] Lookup for app_name '{app_name}' took {time.time() - t0:.3f} seconds.")
        return result
    # Fuzzy fallback
    names = list(_name_to_bundle_id.keys())
    match = process.extractOne(app_name.lower(), names, score_cutoff=80)
    if match:
        best_name, score, _ = match
        print(f"[FUZZY] Closest app_name match: {best_name} (score={score})")
        return _name_to_bundle_id[best_name]
    print(f"[TIMER] Lookup for app_name '{app_name}' took {time.time() - t0:.3f} seconds.")
    return None

def app_name_exists(app_name):
    """
    Returns the canonical app name if the given app name (case-insensitive) exists in the cached app list (exact or fuzzy), otherwise None.
    Uses fuzzy matching as a fallback (score >= 80).
    """
    global _name_to_bundle_id
    if _name_to_bundle_id is None:
        _build_lookup_dicts()
    if app_name.lower() in _name_to_bundle_id:
        # Return the canonical name
        for k in _name_to_bundle_id:
            if k == app_name.lower():
                return k.capitalize() if k.islower() else k
    # Fuzzy fallback
    names = list(_name_to_bundle_id.keys())
    match = process.extractOne(app_name.lower(), names, score_cutoff=80)
    if match:
        best_name, score, _ = match
        return best_name.capitalize() if best_name.islower() else best_name
    return None


def bundle_id_exists(bundle_id):
    """
    Returns the canonical bundle ID if the given bundle ID exists in the cached app list (exact or fuzzy), otherwise None.
    Uses fuzzy matching as a fallback (score >= 80).
    """
    global _bundle_id_to_name, _name_to_bundle_id
    if _bundle_id_to_name is None or _name_to_bundle_id is None:
        _build_lookup_dicts()
    # 1. Exact bundle ID match
    if bundle_id in _bundle_id_to_name:
        return bundle_id
    # 2. Fuzzy bundle ID match
    bundle_ids = list(_bundle_id_to_name.keys())
    match = process.extractOne(bundle_id, bundle_ids, score_cutoff=80)
    if match:
        best_id, score, _ = match
        return best_id
    # 3. Exact app name match
    if bundle_id.lower() in _name_to_bundle_id:
        return _name_to_bundle_id[bundle_id.lower()]
    # 4. Fuzzy app name match
    names = list(_name_to_bundle_id.keys())
    match = process.extractOne(bundle_id.lower(), names, score_cutoff=80)
    if match:
        best_name, score, _ = match
        return _name_to_bundle_id[best_name]
    # 5. Not found
    return None

def rebuild_app_list(refresh=True):
    """
    Rebuilds the app list and writes the JSONL file. Returns the app list.

    Args:
        refresh (bool): Force rebuild of the app list.

    Returns:
        list: The rebuilt app list.
    """
    apps = scan_apps()
    APP_LIST_DIR.mkdir(parents=True, exist_ok=True)
    with open(JSONL_PATH, "w") as f:
        for app in apps:
            f.write(json.dumps(app, ensure_ascii=False) + "\n")
    print("[REFRESH] App list rebuilt and saved.")
    return apps

def resolve_bundle_id(input_id):
    """
    Resolves the input as either a bundle ID or app name (with fuzzy matching).
    Returns the canonical bundle ID if found, otherwise None.
    """
    bid = bundle_id_exists(input_id)
    if bid:
        return bid
    bid = get_bundle_id(input_id)
    if bid:
        return bid
    return None

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Build or refresh the app list JSONL file, or perform lookups.")
    parser.add_argument("--refresh", action="store_true", help="Force refresh the app list")
    parser.add_argument("--bundle-to-name", type=str, help="Lookup app name from bundle ID")
    parser.add_argument("--name-to-bundle", type=str, help="Lookup bundle ID from app name")
    parser.add_argument("--bundle-exists", type=str, help="Check if a bundle ID exists (True/False, fuzzy match)")
    parser.add_argument("--name-exists", type=str, help="Check if an app name exists (True/False, fuzzy match)")
    args = parser.parse_args()

    if args.refresh:
        rebuild_app_list(refresh=True)
    elif args.bundle_to_name:
        name = get_app_name(args.bundle_to_name, refresh=args.refresh)
        print(name if name else f"[NOT FOUND] No app name for bundle ID: {args.bundle_to_name}")
    elif args.name_to_bundle:
        bundle_id = get_bundle_id(args.name_to_bundle, refresh=args.refresh)
        print(bundle_id if bundle_id else f"[NOT FOUND] No bundle ID for app name: {args.name_to_bundle}")
    elif args.bundle_exists:
        print(bundle_id_exists(args.bundle_exists))
    elif args.name_exists:
        print(app_name_exists(args.name_exists))
    else:
        apps = load_app_list(refresh=args.refresh)
        print(f"[INFO] App list contains {len(apps)} apps.")
