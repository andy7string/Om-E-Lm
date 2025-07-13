#!/usr/bin/env python3
"""
appMenu_builder.py

Scans the macOS menu bar of a given application (via bundle ID) and outputs a flattened JSONL file
containing each menu item's path, role, enabled state, and centre screen coordinates.

Fully dynamic:
- Skips the Apple menu (always the first top-level item)
- Processes only visible app menus for the focused application
- Does NOT include shortcut key logic (cleaner + faster)

USAGE:
    python appMenu_builder.py --bundle-id com.apple.mail

Output:
    JSONL file written to ome/data/menu_maps/<bundle_id>_menuMap.jsonl
"""

import sys
import time
import json
import argparse
import subprocess
import os

from env import TREE_MENU_MAPS_DIR as MENU_MAPS_DIR

import Om_E_Py.ome as ome
from Om_E_Tree.ome.handlers import system_handler

# === GLOBAL DELAY SETTINGS ===
APP_LAUNCH_DELAY = 2.0
SUBMENU_POPULATE_DELAY = 0.4
FULLSCREEN_WAIT_DELAY = 2.0
FOCUS_AFTER_LAUNCH_DELAY = 1.0
GENERIC_RETRY_DELAY = 1.0  # Used in send_fullscreen_shortcut
PARENT_MENU_SCAN_DELAY = 0.5  # Delay between parent menu scans

# Ensure the app is running; launch it if not
def ensure_app_running(bundle_id, fullscreen=True):
    print(f"[DEBUG] Ensuring app with bundle_id={bundle_id} is running and focused (fullscreen={fullscreen})...")
    success = system_handler.focus_app(bundle_id, fullscreen=fullscreen)
    if not success:
        print(f"[ERROR] Could not focus app with bundle_id={bundle_id}")
        return None
    app = ome.getAppRefByBundleId(bundle_id)
    if not app:
        print(f"[ERROR] App with bundle_id={bundle_id} not found after focus.")
        return None
    return app

# Extract key info from a single menu item
def get_menu_item_info(item):
    title = getattr(item, 'AXTitle', None) or getattr(item, 'AXDescription', None) or '[No Title]'
    role = getattr(item, 'AXRole', '[No Role]')
    enabled = getattr(item, 'AXEnabled', None)
    pos = getattr(item, 'AXPosition', None)
    size = getattr(item, 'AXSize', None)
    center = None

    # Calculate centre of the menu item (used for click targeting)
    try:
        if pos and size and hasattr(pos, 'x') and hasattr(size, 'width'):
            center = [float(pos.x) + float(size.width)/2, float(pos.y) + float(size.height)/2]
    except Exception:
        pass

    return {
        'title': title,
        'role': role,
        'enabled': enabled,
        'center': center
    }

# Recursively flatten submenus (with full path tracking)
def flatten_menu_bar(menu, path=None, flat=None, max_depth=4, depth=1):
    if flat is None: flat = []
    if path is None: path = []

    try:
        items = getattr(menu, 'AXChildren', [])
    except Exception:
        return flat

    for item in items:
        info = get_menu_item_info(item)
        current_path = path + [info['title']] if info['title'] != '[No Title]' else path

        # Dive into submenus if they exist
        submenus = [c for c in getattr(item, 'AXChildren', []) if getattr(c, 'AXRole', None) == 'AXMenu']
        if submenus and depth < max_depth:
            try:
                item.Press()
                time.sleep(SUBMENU_POPULATE_DELAY)  # brief delay to allow submenu to populate
            except Exception:
                pass
            for submenu in submenus:
                flatten_menu_bar(submenu, current_path, flat, max_depth, depth+1)
        else:
            flat.append({
                'title': info['title'],
                'menu_path': current_path,
                'role': info['role'],
                'enabled': info['enabled'],
                'center': info['center']
            })

    return flat

def get_front_window_bounds(app_name):
    script = f'''
    tell application "{app_name}"
        set b to bounds of front window
        return b as string
    end tell
    '''
    result = subprocess.check_output(['osascript', '-e', script]).decode().strip()
    return result

def send_fullscreen_shortcut(app_name, retries=3, delay=1.0):
    # Get initial bounds
    try:
        before = get_front_window_bounds(app_name)
    except Exception:
        before = None
    for attempt in range(retries):
        script = '''
        tell application "System Events"
            keystroke "f" using {control down, command down}
        end tell
        '''
        subprocess.run(['osascript', '-e', script])
        time.sleep(delay)
        try:
            after = get_front_window_bounds(app_name)
        except Exception:
            after = None
        if before and after and before != after:
            print(f"[INFO] Fullscreen shortcut succeeded on attempt {attempt+1}.")
            return
        print(f"[WARN] Fullscreen shortcut did not expand window (attempt {attempt+1}). Retrying...")
    print("[WARN] Fullscreen shortcut did not expand window after retries.")

# Main scan function: run this for any bundle ID
def scan_menu_flat(bundle_id):
    print(f"[menu-scan] Scanning menus for: {bundle_id}")
    app = ensure_app_running(bundle_id)
    if not app:
        print(f"[ERROR] Could not get app for bundle id: {bundle_id}")
        sys.exit(1)
    app.activate()
    time.sleep(FOCUS_AFTER_LAUNCH_DELAY)

    # Resolve output path
    os.makedirs(MENU_MAPS_DIR, exist_ok=True)
    out_file = os.path.join(MENU_MAPS_DIR, f"{bundle_id.replace('.', '_')}_menuMap.jsonl")

    # Get app menu bar — app menus start from index 1 (index 0 is Apple menu)
    menu_bar = getattr(app, 'menuBar', None) or getattr(app, 'AXMenuBar', None)
    if not menu_bar:
        print("[ERROR] No menu bar found.")
        sys.exit(1)

    flat_menu = []

    top_level_items = getattr(menu_bar, 'AXChildren', [])[1:]  # skip Apple menu
    for item in top_level_items:
        info = get_menu_item_info(item)
        try:
            item.Press()  # expand top-level menu to access its submenu
        except Exception:
            continue
        submenu = next((c for c in getattr(item, 'AXChildren', []) if getattr(c, 'AXRole', None) == 'AXMenu'), None)
        if submenu:
            flatten_menu_bar(submenu, path=[info['title']], flat=flat_menu)
        time.sleep(PARENT_MENU_SCAN_DELAY)  # Delay between parent menu scans

    # Write to JSONL with real UTF-8 characters (no unicode escapes)
    with open(out_file, 'w', encoding='utf-8') as f:
        for item in flat_menu:
            if item['title'] and item['title'] != '[No Title]':
                f.write(json.dumps(item, ensure_ascii=False, separators=(',', ':')) + '\n')

    print(f"[menu-scan] ✅ Done. Saved: {out_file}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--bundle-id", required=True, help="Bundle ID of the app to scan")
    args = parser.parse_args()
    scan_menu_flat(args.bundle_id)
