from ome.utils.builder.menu_builder import build_menu
import json

if __name__ == '__main__':
    bundle_id = "com.apple.mail"
    items = build_menu(bundle_id, filter_mode='all')
    print(f"Scanned {len(items)} menu items.")
    print(json.dumps(items[:3], indent=2)) 