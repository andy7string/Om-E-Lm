import os
import json
from ome.omeMenus import enrich_menu_jsonl_with_omeclicks, load_menu_jsonl
from ome.utils.env.env import MENU_EXPORT_DIR

def count_missing_omeclick(menu_items):
    return sum(1 for item in menu_items if 'omeClick' not in item or not item['omeClick'])

def main():
    bundle_id = 'com.apple.mail'
    jsonl_path = os.path.join(MENU_EXPORT_DIR, f"menu_attributes_{bundle_id}.jsonl")
    print(f"[TEST] Loading menu JSONL: {jsonl_path}")
    menu_items_before = load_menu_jsonl(jsonl_path)
    missing_before = count_missing_omeclick(menu_items_before)
    print(f"[TEST] Menu items before enrichment: {len(menu_items_before)}")
    print(f"[TEST] Items missing omeClick before: {missing_before}")

    print("[TEST] Running enrichment...")
    enrich_menu_jsonl_with_omeclicks(bundle_id, max_items=5)

    menu_items_after = load_menu_jsonl(jsonl_path)
    missing_after = count_missing_omeclick(menu_items_after)
    print(f"[TEST] Menu items after enrichment: {len(menu_items_after)}")
    print(f"[TEST] Items missing omeClick after: {missing_after}")

    if missing_after < missing_before:
        print(f"[PASS] omeClick enrichment reduced missing items from {missing_before} to {missing_after}.")
    elif missing_after == 0:
        print(f"[PASS] All menu items now have omeClick.")
    else:
        print(f"[WARN] omeClick enrichment did not reduce missing items.")

if __name__ == "__main__":
    main() 