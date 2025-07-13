#!/usr/bin/env python3
"""
appWindow_builder.py

Scans the focused macOS app window and outputs a flat UI map as JSONL.
Includes toolbar elements, adds smart flags, skips unlabeled AXRows, and groups output by role.

USAGE:
    python appWindow_builder.py --bundle-id com.apple.mail
"""

import sys, time, json, argparse, os
from pathlib import Path
from collections import defaultdict
from ome.utils.env.env import MAX_CHILDREN, WINDOW_DEPTH, TOOLBAR_DEPTH, WINDOW_MAPS_DIR
from ome.handlers import system_handler

WINDOW_MAPS_DIR.mkdir(parents=True, exist_ok=True)

import atomacos as atomac
import subprocess

def ensure_app_running(bundle_id, retries=10, delay=1.0):
    # Use system_handler to focus and fullscreen the app
    success = system_handler.focus_app(bundle_id, fullscreen=True)
    if not success:
        print(f"[ERROR] Could not focus app with bundle_id={bundle_id}")
        return None
    app = atomac.getAppRefByBundleId(bundle_id)
    if not app:
        print(f"[ERROR] App with bundle_id={bundle_id} not found after focus.")
        return None
    return app

def add_flags(role, children):
    return {
        "is_menu": role in ("AXMenuButton", "AXPopUpButton"),
        "has_children": bool(children),
        "likely_triggers_ui_change": role in ("AXButton", "AXMenuButton", "AXPopUpButton") and bool(children)
    }

def serialize_element(element, depth=0, max_depth=4, path=None, flat=None, tag_toolbar=False):
    if flat is None: flat = []
    if path is None: path = []

    if depth > max_depth:
        return flat
    try:
        role = getattr(element, 'AXRole', None)
        desc = getattr(element, 'AXDescription', None)
        title = getattr(element, 'AXTitle', None)
        value = getattr(element, 'AXValue', None)
        identifier = getattr(element, 'AXIdentifier', None)
        helptext = getattr(element, 'AXHelp', None)
        pos = getattr(element, 'AXPosition', None)
        size = getattr(element, 'AXSize', None)
        children = getattr(element, 'AXChildren', [])[:MAX_CHILDREN] if hasattr(element, 'AXChildren') else []

        label = title or desc or value or identifier or helptext

        # Skip unlabeled AXRows
        if role == "AXRow" and not label:
            return flat

        this_path = path + [label] if label else path
        center = [pos.x + size.width / 2, pos.y + size.height / 2] if pos and size else None

        node = {
            "role": role,
            "label": label,
            "path": this_path,
            "center": center,
            "size": {"width": size.width, "height": size.height} if size else None,
            "flags": add_flags(role, children)
        }
        if tag_toolbar:
            node["is_toolbar"] = True
        flat.append(node)

        for child in children:
            serialize_element(child, depth + 1, max_depth, this_path, flat, tag_toolbar)
    except Exception as e:
        print(f"[serialize_element] error at depth={depth}: {e}")
    return flat

def find_toolbar(window):
    for child in getattr(window, 'AXChildren', []):
        if getattr(child, 'AXRole', None) == 'AXToolbar':
            return child
    return None

def dedupe_entries(entries):
    seen = {}
    result = []
    for item in entries:
        key = (item.get("label"), tuple(item.get("center") or []))
        existing = seen.get(key)
        if existing:
            if not existing.get("is_toolbar") and item.get("is_toolbar"):
                seen[key] = item
        else:
            seen[key] = item
    return list(seen.values())

def group_by_role(entries):
    groups = defaultdict(list)
    for item in entries:
        groups[item.get("role")].append(item)

    ordered_roles = [
        "AXToolbar", "AXButton", "AXMenuButton", "AXCheckBox", "AXPopUpButton", "AXGroup",
        "AXStaticText", "AXTextField", "AXRow", "AXScrollArea", "AXOutline", "AXTable",
        "AXSplitGroup", "AXSplitter", "AXScrollBar", "AXWindow"
    ]
    sorted_entries = []
    for role in ordered_roles:
        sorted_entries.extend(groups.pop(role, []))
    # Append any remaining roles
    for remaining in sorted(groups.keys()):
        sorted_entries.extend(groups[remaining])
    return sorted_entries

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

def scan_window(bundle_id):
    app = ensure_app_running(bundle_id)
    if not app:
        sys.exit(1)
    app.activate()
    time.sleep(1.0)

    win = None
    for _ in range(3):
        win = getattr(app, 'AXFocusedWindow', None)
        if win:
            break
        time.sleep(1)
    if not win:
        wins = getattr(app, 'AXWindows', [])
        if wins:
            win = wins[0]
            print("[WARN] Using AXWindows[0] as fallback.")
        else:
            print("[ERROR] No usable window found.")
            sys.exit(1)

    print(f"[INFO] Scanning: {bundle_id}")
    flat_index = []

    serialize_element(win, max_depth=WINDOW_DEPTH, flat=flat_index)

    toolbar = find_toolbar(win)
    if toolbar:
        serialize_element(toolbar, max_depth=TOOLBAR_DEPTH, path=["Toolbar"], flat=flat_index, tag_toolbar=True)
    else:
        print("[INFO] No AXToolbar found.")

    deduped = dedupe_entries(flat_index)
    grouped = group_by_role(deduped)

    out_file = WINDOW_MAPS_DIR / f"{bundle_id.replace('.', '_')}_windowMap.jsonl"
    with open(out_file, 'w', encoding='utf-8') as f:
        for item in grouped:
            f.write(json.dumps(item, ensure_ascii=False, separators=(',', ':')) + '\n')

    print(f"[DONE] Output written to: {out_file}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Scan and flatten the focused app window into JSONL.")
    parser.add_argument("--bundle-id", required=True, help="Bundle ID of the app to scan")
    args = parser.parse_args()
    scan_window(args.bundle_id)
