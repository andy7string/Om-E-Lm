"""
Menu Path Finder Utility (menuPath_controller.py)

This module provides functions to resolve a fuzzy menu label or menu path to the best-matching
menu item path for a given macOS application, using a JSONL-based menu map.

====================
PURPOSE
====================
- Given a fuzzy label (e.g., "settings", "send mail") or a fuzzy menu path (e.g., "File > Import Mailboxes…") and a menu map file,
  finds the best-matching menu item by title or by path.
- Returns the full menu path as a list of strings, suitable for UI automation.

====================
KEY FEATURES
====================
- Fuzzy matching: Uses rapidfuzz to match the label to menu item titles or to the joined menu path.
- Path search: All query tokens must be present in the menu path for a match to be considered.
- Normalization: Matching is case-insensitive and ignores punctuation and special characters.
- Menu map file selection: The menu map file is always menu_<bundle_id>.jsonl.
- Two APIs: get_menu_path_by_title(label, bundle_id) and get_menu_path_by_path(path_label, bundle_id).
- Simple CLI: Run as a module to use either mode from the command line.
- Stateless: Builds the menu map file path from bundle_id on each call for up-to-date results.

====================
PYTHON API USAGE EXAMPLES
====================
from ome.utils.uiNav.menuPath_controller import get_menu_path_by_title, get_menu_path_by_path

# Fuzzy match by title
result = get_menu_path_by_title("settings", "com.apple.mail")
print(result)  # {'title': 'Settings…', 'menu_path': ['Mail', 'Settings…']}

# Fuzzy match by path
result = get_menu_path_by_path("File > Import Mailboxes", "com.apple.mail")
print(result)  # {'title': 'Import Mailboxes…', 'menu_path': ['File', 'Import Mailboxes…']}

====================
COMMAND LINE USAGE EXAMPLES
====================
# Fuzzy match by title
PYTHONPATH=. python -m ome.utils.uiNav.menuPath_controller title "settings" com.apple.mail

# Fuzzy match by path
PYTHONPATH=. python -m ome.utils.uiNav.menuPath_controller nav title "Quit" com.apple.mail

# Navigation mode
PYTHONPATH=. python -m ome.utils.uiNav.menuPath_controller nav path "Style Underline" com.apple.mail

# Test normalization (should match even with extra spaces/punctuation)
PYTHONPATH=. python -m ome.utils.uiNav.menuPath_controller nav path "Mailbox VIPs" com.apple.mail

====================
WHEN TO USE
====================
- When you need to programmatically resolve a fuzzy menu label or menu path to a menu path
  for macOS UI automation, using a single unified menu map file.
"""

import json
import time
import re
import subprocess
import os
from typing import List, Dict, Optional
from rapidfuzz import fuzz
import ome
from ome import NativeUIElement
from ome.utils.builder.app.appList_controller import bundle_id_exists


def get_default_menu_map_path(bundle_id: str) -> str:
    """
    Returns the default menu map path for a given bundle ID.
    Validates the bundle ID using appList_controller.
    Raises ValueError if the bundle ID is invalid.
    """
    from ome.utils.env.env import MENU_EXPORT_DIR
    canonical_bundle_id = bundle_id_exists(bundle_id)
    if not canonical_bundle_id:
        raise ValueError(f"Invalid bundle ID: {bundle_id}")
    filename = f"menu_{canonical_bundle_id}.jsonl"
    return os.path.join(MENU_EXPORT_DIR, filename)


def _load_menu_map(menu_map_path: str) -> List[Dict]:
    """
    Loads the menu map from a JSONL file.
    Each line should be a JSON object with at least 'title' and 'menu_path' fields.
    Returns a list of menu entry dicts.
    """
    menu_entries = []
    with open(menu_map_path, 'r', encoding='utf-8') as f:
        for line in f:
            try:
                entry = json.loads(line)
                if 'title' in entry and 'menu_path' in entry:
                    menu_entries.append({
                        'title': entry['title'],
                        'menu_path': entry['menu_path']
                    })
            except json.JSONDecodeError:
                # Skip lines that are not valid JSON
                continue
    return menu_entries


def get_menu_path_by_title(label: str, bundle_id: str) -> Optional[Dict]:
    """
    Fuzzy match the label against the 'title' field of each menu entry.
    Returns the best match (longest menu_path if tie), or None if no match is found.
    If the menu map file does not exist, attempts to build it using appMenu_builder.py.
    """
    menu_map_path = get_default_menu_map_path(bundle_id)
    t0 = time.time()
    best_score = -1
    best_entries = []
    try:
        with open(menu_map_path, 'r', encoding='utf-8') as f:
            for line in f:
                try:
                    entry = json.loads(line)
                    if 'title' in entry and 'menu_path' in entry:
                        score = fuzz.token_set_ratio(label, entry['title'])
                        if score > best_score:
                            best_score = score
                            best_entries = [{
                                'title': entry['title'],
                                'menu_path': entry['menu_path']
                            }]
                        elif score == best_score:
                            best_entries.append({
                                'title': entry['title'],
                                'menu_path': entry['menu_path']
                            })
                except json.JSONDecodeError:
                    continue
    except FileNotFoundError:
        print(f"[INFO] Menu map file '{menu_map_path}' not found. Attempting to build it...")
        result = subprocess.run([
            "python", "-m", "ome.utils.builder.app.appMenu_builder",
            bundle_id, "--filter", "all"
        ])
        if result.returncode != 0:
            print(f"[ERROR] Failed to build menu map file for {bundle_id}.")
            return None
        # Try again
        try:
            with open(menu_map_path, 'r', encoding='utf-8') as f:
                for line in f:
                    try:
                        entry = json.loads(line)
                        if 'title' in entry and 'menu_path' in entry:
                            score = fuzz.token_set_ratio(label, entry['title'])
                            if score > best_score:
                                best_score = score
                                best_entries = [{
                                    'title': entry['title'],
                                    'menu_path': entry['menu_path']
                                }]
                            elif score == best_score:
                                best_entries.append({
                                    'title': entry['title'],
                                    'menu_path': entry['menu_path']
                                })
                    except json.JSONDecodeError:
                        continue
        except Exception as e:
            print(f"[ERROR] Still could not open menu map file: {e}")
            return None
    if not best_entries:
        print(f"[TIMER] Search for '{label}' in '{menu_map_path}' took {time.time() - t0:.4f} seconds. No match found.")
        return None
    result = max(best_entries, key=lambda e: len(e['menu_path']))
    print(f"[TIMER] Search for '{label}' in '{menu_map_path}' took {time.time() - t0:.4f} seconds. Best match: {result['title']}")
    return result


def normalize(s):
    """
    Normalizes a string for fuzzy matching:
    - Removes punctuation and special characters
    - Lowercases
    - Strips whitespace
    """
    s = s.replace('"', '').replace('…', '')
    s = re.sub(r'[^a-zA-Z0-9 ]', '', s)
    return s.lower().strip()


def get_menu_path_by_path(path_label: str, bundle_id: str) -> Optional[Dict]:
    """
    Fuzzy match the path_label against the joined menu_path (joined by ' > ') for each menu entry.
    All query tokens must be present in the path for a match to be considered.
    Returns the best match (longest menu_path if tie), or None if no match is found.
    If the menu map file does not exist, attempts to build it using appMenu_builder.py.
    """
    menu_map_path = get_default_menu_map_path(bundle_id)
    t0 = time.time()
    best_score = -1
    best_entries = []
    query_tokens = set(normalize(path_label).split())
    try:
        with open(menu_map_path, 'r', encoding='utf-8') as f:
            for line in f:
                try:
                    entry = json.loads(line)
                    if 'title' in entry and 'menu_path' in entry:
                        joined_path = ' '.join(str(p) for p in entry['menu_path'])
                        norm_path = normalize(joined_path)
                        path_tokens = set(norm_path.split())
                        if not query_tokens.issubset(path_tokens):
                            continue
                        score = fuzz.token_sort_ratio(normalize(path_label), norm_path)
                        if score > best_score:
                            best_score = score
                            best_entries = [{
                                'title': entry['title'],
                                'menu_path': entry['menu_path']
                            }]
                        elif score == best_score:
                            best_entries.append({
                                'title': entry['title'],
                                'menu_path': entry['menu_path']
                            })
                except json.JSONDecodeError:
                    continue
    except FileNotFoundError:
        print(f"[INFO] Menu map file '{menu_map_path}' not found. Attempting to build it...")
        result = subprocess.run([
            "python", "-m", "ome.utils.builder.app.appMenu_builder",
            bundle_id, "--filter", "all"
        ])
        if result.returncode != 0:
            print(f"[ERROR] Failed to build menu map file for {bundle_id}.")
            return None
        # Try again
        try:
            with open(menu_map_path, 'r', encoding='utf-8') as f:
                for line in f:
                    try:
                        entry = json.loads(line)
                        if 'title' in entry and 'menu_path' in entry:
                            joined_path = ' '.join(str(p) for p in entry['menu_path'])
                            norm_path = normalize(joined_path)
                            path_tokens = set(norm_path.split())
                            if not query_tokens.issubset(path_tokens):
                                continue
                            score = fuzz.token_sort_ratio(normalize(path_label), norm_path)
                            if score > best_score:
                                best_score = score
                                best_entries = [{
                                    'title': entry['title'],
                                    'menu_path': entry['menu_path']
                                }]
                            elif score == best_score:
                                best_entries.append({
                                    'title': entry['title'],
                                    'menu_path': entry['menu_path']
                                })
                    except json.JSONDecodeError:
                        continue
        except Exception as e:
            print(f"[ERROR] Still could not open menu map file: {e}")
            return None
    if not best_entries:
        print(f"[TIMER] Path search for '{path_label}' in '{menu_map_path}' took {time.time() - t0:.4f} seconds. No match found.")
        return None
    result = max(best_entries, key=lambda e: len(e['menu_path']))
    print(f"[TIMER] Path search for '{path_label}' in '{menu_map_path}' took {time.time() - t0:.4f} seconds. Best match: {result['title']}")
    return result


def get_visible_menu_item(app, menu_path):
    """
    Walks the menu path, pressing each parent, and returns the final menu item AXUIElement.
    Ensures the menu item is visible so AXPosition/AXSize are valid.
    """
    current = app.AXMenuBar
    for i, part in enumerate(menu_path):
        children = getattr(current, 'AXChildren', [])
        # If the only child is an AXMenu, descend into it
        if len(children) == 1 and getattr(children[0], 'AXRole', None) == 'AXMenu':
            children = getattr(children[0], 'AXChildren', [])
        # Debug print: show all available AXTitle values at this level
        print(f"[DEBUG] Looking for '{part}' among: {[getattr(child, 'AXTitle', None) for child in children]}")
        found = None
        for child in children:
            if getattr(child, 'AXTitle', None) == part:
                found = child
                break
        if not found:
            return None
        # Press parent menu items to open submenus, except for the last item
        if i < len(menu_path) - 1:
            try:
                found.Press()
                time.sleep(0.2)  # Give the system time to open the menu
            except Exception:
                pass
        current = found
    return current  # This should be the visible menu item


def menu_nav(mode: str, label: str, bundle_id: str):
    """
    Shell function for navigation: resolves the menu path by title or path and (eventually) performs navigation.
    Validates the bundle ID using appList_controller.
    Focuses the app before any menu actions.
    Args:
        mode (str): 'title' or 'path'
        label (str): The menu label or path
        bundle_id (str): The app's bundle identifier
    Raises ValueError if the bundle ID is invalid.
    """
    from ome.utils.builder.app.app_focus import ensure_app_focus

    canonical_bundle_id = bundle_id_exists(bundle_id)
    
    if not canonical_bundle_id:
        raise ValueError(f"Invalid bundle ID: {bundle_id}")
    
    # Focus the app before any menu actions
    focus_result = ensure_app_focus(canonical_bundle_id)
    
    if focus_result['status'] != 'success':
        print(f"[ERROR] Could not focus app: {focus_result.get('error')}")
        return
    if mode == "title":
        result = get_menu_path_by_title(label, canonical_bundle_id)
    elif mode == "path":
        result = get_menu_path_by_path(label, canonical_bundle_id)
    else:
        print(f"Unknown nav mode: {mode}")
        return
    if not result or not result.get('menu_path'):
        print(f"[ERROR] Could not resolve menu path for label '{label}' and bundle_id '{canonical_bundle_id}'")
        return
    menu_path = result['menu_path']
    print(f"[MENU_NAV] Navigating to: {menu_path}")
    try:
        app = focus_result['app']
        # Always use the full menu_path
        menu_args = menu_path
        menu_item = get_visible_menu_item(app, menu_args)
        if not menu_item:
            print("[MENU_NAV] Could not find menu item in UI hierarchy.")
            return
        click_coords = get_menu_item_click_coords(menu_item, menu_path=menu_path, bundle_id=canonical_bundle_id)
        if click_coords:
            print(f"[MENU_NAV] Click coordinates: {click_coords}")
        else:
            print("[MENU_NAV] Could not determine click coordinates for menu item.")
        enabled = getattr(menu_item, 'AXEnabled', None)
        print(f"[MENU_NAV] AXEnabled: {enabled}")
        if enabled is not True:
            print("[MENU_NAV] Menu item is disabled, not clicking.")
            return
        menu_item.Press()
        print(f"[MENU_NAV] Activated menu item: {result['title']}")
    except Exception as e:
        print(f"[ERROR] Failed to activate menu item: {e}")


def get_menu_item_click_coords(menu_item, menu_path=None, bundle_id=None):
    """
    Returns the (x, y) click coordinates of the menu item if available, else None.
    For menu items, use the center if AXSize is available, else use AXPosition.
    """
    pos = getattr(menu_item, 'AXPosition', None)
    size = getattr(menu_item, 'AXSize', None)
    if (
        pos and len(pos) == 2 and pos != [0.0, 1440.0] and
        size and len(size) == 2 and size != [0.0, 0.0]
    ):
        try:
            return (float(pos[0]) + float(size[0]) / 2, float(pos[1]) + float(size[1]) / 2)
        except Exception:
            pass
    if pos and len(pos) == 2 and pos != [0.0, 1440.0]:
        try:
            return tuple(float(x) for x in pos)
        except Exception:
            pass
    # Fallback: look up omeClick in the menu map JSONL
    if menu_path and bundle_id:
        menu_map_path = get_default_menu_map_path(bundle_id)
        try:
            with open(menu_map_path, 'r', encoding='utf-8') as f:
                for line in f:
                    try:
                        entry = json.loads(line)
                        if entry.get('menu_path') == menu_path and 'omeClick' in entry:
                            return tuple(entry['omeClick'])
                    except Exception:
                        continue
        except Exception:
            pass
    return None


if __name__ == "__main__":
    import sys
    # Command line interface for testing each function
    if len(sys.argv) < 3:
        print("Usage: python -m ome.utils.uiNav.menuPath_controller <mode: title|path|nav> <label> <bundle_id>")
        print("\nExamples:")
        print("  python -m ome.utils.uiNav.menuPath_controller title 'settings' com.apple.mail")
        print("  python -m ome.utils.uiNav.menuPath_controller path 'File > Import Mailboxes' com.apple.mail")
        print("  python -m ome.utils.uiNav.menuPath_controller nav title 'settings' com.apple.mail")
        print("  python -m ome.utils.uiNav.menuPath_controller nav path 'File > Import Mailboxes' com.apple.mail")
        sys.exit(1)
    mode = sys.argv[1]
    if mode == "nav":
        if len(sys.argv) < 5:
            print("Usage: python -m ome.utils.uiNav.menuPath_controller nav <title|path> <label> <bundle_id>")
            sys.exit(1)
        submode = sys.argv[2]
        label = sys.argv[3]
        bundle_id = sys.argv[4]
        menu_nav(submode, label, bundle_id)
    else:
        label = sys.argv[2]
        bundle_id = sys.argv[3]
        if mode == "title":
            result = get_menu_path_by_title(label, bundle_id)
            print(f"\n[CLI TEST] get_menu_path_by_title('{label}', '{bundle_id}')\nResult: {result}")
        elif mode == "path":
            result = get_menu_path_by_path(label, bundle_id)
            print(f"\n[CLI TEST] get_menu_path_by_path('{label}', '{bundle_id}')\nResult: {result}")
        else:
            print("Mode must be 'title', 'path', or 'nav'")
            sys.exit(1) 