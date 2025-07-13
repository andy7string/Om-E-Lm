import json
import sys
import os
import time
from ome.utils.builder.app.app_focus import ensure_app_focus

def extract_omeclick(element):
    try:
        pos = getattr(element, 'AXPosition', None)
        size = getattr(element, 'AXSize', None)
        if pos and size and isinstance(pos, (list, tuple)) and isinstance(size, (list, tuple)):
            return [float(pos[0]) + float(size[0])/2, float(pos[1]) + float(size[1])/2]
    except Exception:
        pass
    return None

def extract_toolbar_buttons(window, parent_path):
    toolbar = window.findFirst(AXRole='AXToolbar')
    buttons = []
    actionable_roles = {'AXButton', 'AXMenuButton', 'AXPopUpButton'}
    def walk_toolbar(elem, path):
        try:
            role = getattr(elem, 'AXRole', None)
        except Exception:
            role = None
        try:
            title = getattr(elem, 'AXTitle', None) or getattr(elem, 'AXDescription', None)
        except Exception:
            title = None
        omeClick = extract_omeclick(elem)
        if role in actionable_roles:
            button_entry = {
                'path': path,
                'AXRole': role,
                'title': title,
                'description': getattr(elem, 'AXDescription', None),
                'omeClick': omeClick
            }
            print(f"[TOOLBAR] Found button: {title} at path {path}")
            buttons.append(button_entry)
        # Recurse into children
        try:
            children = getattr(elem, 'AXChildren', [])
            for idx, child in enumerate(children):
                child_path = path + [title] if title else path + [f"Child_{idx}"]
                walk_toolbar(child, child_path)
        except Exception:
            pass
    if toolbar:
        walk_toolbar(toolbar, parent_path)
    else:
        print("[TOOLBAR] Toolbar not found in window.")
    return buttons

def scan_and_write_toolbar_jsonl(bundle_id, out_path):
    app = ensure_app_focus(bundle_id)
    try:
        window = app.AXFocusedWindow
    except Exception:
        print("Could not get focused window.")
        return
    window_title = getattr(window, 'AXTitle', None) or 'Window'
    toolbar_entries = extract_toolbar_buttons(window, [window_title, "toolbar"])
    print(f"Writing {len(toolbar_entries)} toolbar items to {out_path}")
    with open(out_path, 'w') as f:
        for item in toolbar_entries:
            f.write(json.dumps(item, ensure_ascii=False) + '\n')
    print(f"Toolbar JSONL written to {out_path}")

if __name__ == '__main__':
    bundle_id = "com.apple.mail"
    out_path = "ome/data/windows/window_com.apple.mail_toolbar.jsonl"
    scan_and_write_toolbar_jsonl(bundle_id, out_path) 