import json
import ome
import ome.cleanup
from ome.ui_helpers import ensure_app_focus, traverse_windows_to_json
from ome.omeMenus import traverse_menu_to_json

MAIL_BUNDLE_ID = "com.apple.mail"
MENU_JSONL = f"menu_{MAIL_BUNDLE_ID}.jsonl"
WIN_JSONL = f"win_{MAIL_BUNDLE_ID}.jsonl"

def log(msg):
    print(f"[EXPORT] {msg}")

def export_menu():
    app = ensure_app_focus(MAIL_BUNDLE_ID)
    # For best results, avoid using the mouse during scanning.
    menu_bar = app.AXMenuBar  # Correct way to access the menu bar
    log("Scanning menu bar...")
    menu_items = traverse_menu_to_json(menu_bar, path=["Mail"])
    with open(MENU_JSONL, "w") as f:
        for item in menu_items:
            f.write(json.dumps(item) + "\n")
    log(f"Exported menu structure to {MENU_JSONL}")
    ome.cleanup.cleanup()

def export_windows():
    app = ensure_app_focus(MAIL_BUNDLE_ID)
    log("Scanning windows...")
    window_items = traverse_windows_to_json(app)
    with open(WIN_JSONL, "w") as f:
        for item in window_items:
            f.write(json.dumps(item) + "\n")
    log(f"Exported window structure to {WIN_JSONL}")
    ome.cleanup.cleanup()

if __name__ == "__main__":
    export_menu()
    export_windows()
    log("Done.") 