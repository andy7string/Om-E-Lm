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

def scan_and_write_window_jsonl(bundle_id, out_path, max_depth=5):
    app = ensure_app_focus(bundle_id)
    try:
        window = app.AXFocusedWindow
    except Exception:
        print("Could not get focused window.")
        return
    window_title = None
    try:
        window_title = getattr(window, 'AXTitle', None)
    except Exception:
        window_title = None
    window_title = window_title or 'Window'
    all_entries = []
    def walk_window(element, path=None, depth=0):
        if path is None:
            path = []
        try:
            role = getattr(element, 'AXRole', None)
        except Exception:
            role = None
        try:
            title = getattr(element, 'AXTitle', None)
        except Exception:
            title = None
        if not title:
            try:
                title = getattr(element, 'AXDescription', None)
            except Exception:
                title = None
        try:
            description = getattr(element, 'AXDescription', None)
        except Exception:
            description = None
        try:
            omeClick = extract_omeclick(element)
        except Exception:
            omeClick = None
        entry = {
            'path': path,
            'AXRole': role,
            'title': title,
            'description': description,
            'omeClick': omeClick
        }
        all_entries.append(entry)
        if depth < max_depth:
            try:
                children = getattr(element, 'AXChildren', [])
                for idx, child in enumerate(children):
                    try:
                        child_title = getattr(child, 'AXTitle', None)
                    except Exception:
                        child_title = None
                    child_path = path + [child_title] if child_title else path + [f"Child_{idx}"]
                    walk_window(child, child_path, depth+1)
            except Exception:
                pass
    walk_window(window, [window_title], 0)
    print(f"Writing {len(all_entries)} items to {out_path}")
    with open(out_path, 'w') as f:
        for item in all_entries:
            f.write(json.dumps(item, ensure_ascii=False) + '\n')
    print(f"Window JSONL written to {out_path}")

if __name__ == '__main__':
    bundle_id = "com.apple.mail"
    out_path = "ome/data/windows/window_com.apple.mail_ss.jsonl"
    scan_and_write_window_jsonl(bundle_id, out_path, max_depth=5) 