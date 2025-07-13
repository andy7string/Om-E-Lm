import json
import os
import time
import sys
from ome.omeMenus import resolve_ui_element_by_path, ensure_app_focus

# --- SAFETY REMINDER ---
print('Move your mouse to the TOP-LEFT corner of the screen at any time to immediately stop automation (pyautogui.FAILSAFE).')

# Use package-style imports for modules in ome/
import ome.utils.env.env as env

def load_menu_jsonl(jsonl_path):
    with open(jsonl_path, "r") as f:
        return [json.loads(line) for line in f]

def save_menu_jsonl(menu_items, jsonl_path):
    with open(jsonl_path, "w") as f:
        for item in menu_items:
            f.write(json.dumps(item, ensure_ascii=False) + '\n')

def build_menu_index(menu_items):
    return {tuple(item["menu_path"]): item for item in menu_items}

def enrich_menu_item(menu_path, bundle_id, app):
    ax_path = [app.getLocalizedName()] + menu_path
    elem = resolve_ui_element_by_path(ax_path, bundle_id)
    if not elem:
        return None
    updates = {}
    # omeClick (center of AXPosition + AXSize)
    pos = getattr(elem, "AXPosition", None)
    size = getattr(elem, "AXSize", None)
    if pos and size:
        updates["omeClick"] = [float(pos[0]) + float(size[0])/2, float(pos[1]) + float(size[1])/2]
    # Shortcut info
    shortcut_mod = getattr(elem, "AXMenuItemCmdModifiers", None)
    if shortcut_mod is not None:
        updates["shortcut_modifiers"] = shortcut_mod
    shortcut_key = getattr(elem, "AXMenuItemCmdChar", None)
    if shortcut_key is not None:
        updates["shortcut_key"] = shortcut_key
    # AXHelp
    help_text = getattr(elem, "AXHelp", None)
    if help_text:
        updates["AXHelp"] = help_text
    # MarkChar (checked/toggled)
    mark_char = getattr(elem, "AXMenuItemMarkChar", None)
    if mark_char:
        updates["AXMenuItemMarkChar"] = mark_char
    # Visible
    visible = getattr(elem, "AXVisible", None)
    if visible is not None:
        updates["AXVisible"] = visible
    # Selected
    selected = getattr(elem, "AXSelected", None)
    if selected is not None:
        updates["AXSelected"] = selected
    # Focused
    focused = getattr(elem, "AXFocused", None)
    if focused is not None:
        updates["AXFocused"] = focused
    return updates

if __name__ == "__main__":
    bundle_id = "com.apple.mail"
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    jsonl_path = os.path.join(project_root, "data", "menus", f"menu_attributes_{bundle_id}.jsonl")
    if not os.path.exists(jsonl_path):
        print(f"Menu JSONL not found: {jsonl_path}")
        exit(1)

    # Parse command-line args for fullscreen flag
    fullscreen = False
    if "--fullscreen" in sys.argv:
        fullscreen = True
    print(f"[INFO] App will {'open in FULLSCREEN' if fullscreen else 'NOT open in fullscreen'} mode.")

    menu_items = load_menu_jsonl(jsonl_path)
    menu_index = build_menu_index(menu_items)
    print(f"Loaded {len(menu_items)} menu items.")
    app = ensure_app_focus(bundle_id, fullscreen=fullscreen)
    updated_count = 0
    for idx, item in enumerate(menu_items):
        menu_path = item.get("menu_path")
        if not menu_path:
                continue
        updates = enrich_menu_item(menu_path, bundle_id, app)
        if updates:
            for k, v in updates.items():
                if v is not None:
                    item[k] = v
            updated_count += 1
            if updated_count % 25 == 0:
                print(f"  Updated {updated_count} items so far...")
        elif idx % 25 == 0:
            print(f"[{idx+1}/{len(menu_items)}] Processed.")
    print(f"\nEnriched {updated_count} menu items using native AX API.")
    save_menu_jsonl(menu_items, jsonl_path)
    print(f"Saved enriched menu JSONL to {jsonl_path}") 