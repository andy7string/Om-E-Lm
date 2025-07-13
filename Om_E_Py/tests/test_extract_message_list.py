import json
import sys
import os
from ome.utils.builder.app.app_focus import ensure_app_focus
import pyautogui
import time

def extract_omeclick(element):
    try:
        pos = getattr(element, 'AXPosition', None)
        size = getattr(element, 'AXSize', None)
        if pos and size and isinstance(pos, (list, tuple)) and isinstance(size, (list, tuple)):
            return [float(pos[0]) + float(size[0])/2, float(pos[1]) + float(size[1])/2]
    except Exception:
        pass
    return None

def deep_walk_collect_rows(element, path=None, found=None, max_rows=10):
    if path is None:
        path = []
    if found is None:
        found = []
    if len(found) >= max_rows:
        return found  # Stop recursion if we have enough
    try:
        children = getattr(element, 'AXChildren', [])
        if not isinstance(children, list):
            children = []
    except Exception:
        children = []
    values = []
    for child in children:
        try:
            val = getattr(child, 'AXValue', None)
            if val:
                values.append(val)
        except Exception:
            continue
    if len(values) >= 2 and len(found) < max_rows:
        found.append({
            'path': path,
            'sender': values[0],
            'subject': values[1] if len(values) > 1 else None,
            'date': values[2] if len(values) > 2 else None,
            'omeClick': extract_omeclick(element)
        })
        print(f"[MESSAGES] {len(found)}: {values[0]} | {values[1] if len(values) > 1 else None} | {values[2] if len(values) > 2 else None}")
    # Only recurse if we still need more
    if len(found) < max_rows:
        for idx, child in enumerate(children):
            if len(found) >= max_rows:
                break
            child_path = path + [f"Child_{idx}"]
            deep_walk_collect_rows(child, child_path, found, max_rows)
    return found

def resolve_element_by_path(window, path):
    current = window
    for step in path[1:]:  # skip the window title
        try:
            children = getattr(current, 'AXChildren', [])
            if not isinstance(children, list):
                children = []
        except Exception:
            children = []
        found = None
        if step.startswith("Child_"):
            try:
                idx = int(step.split("_")[1])
                if 0 <= idx < len(children):
                    found = children[idx]
            except Exception:
                pass
        else:
            for child in children:
                try:
                    title = getattr(child, 'AXTitle', None)
                except Exception:
                    title = None
                if title == step:
                    found = child
                    break
        if not found:
            print(f"Could not resolve step '{step}' in path.")
            return None
        current = found
    return current

def press_message_by_index(window, jsonl_path, index):
    with open(jsonl_path) as f:
        messages = [json.loads(line) for line in f]
    if index >= len(messages):
        print(f"No message at index {index}.")
        return
    msg = messages[index]
    print(f"Attempting to press message {index+1}: {msg.get('sender')} | {msg.get('subject')}")
    elem = resolve_element_by_path(window, msg['path'])
    if elem:
        try:
            elem.Press()
            print("Pressed the message via AX API!")
            return
        except Exception as e:
            print(f"Error pressing message: {e}")
    # Fallback: search for a row with matching sender/subject/date
    print("Path resolution failed, trying attribute-based search...")
    try:
        for row in window.findAllR(AXRole='AXRow'):
            try:
                children = getattr(row, 'AXChildren', [])
                values = []
                for child in children:
                    try:
                        val = getattr(child, 'AXValue', None)
                        if val:
                            values.append(val)
                    except Exception:
                        continue
                if (len(values) >= 2 and
                    values[0] == msg.get('sender') and
                    values[1] == msg.get('subject') and
                    (len(values) < 3 or values[2] == msg.get('date'))):
                    row.Press()
                    print("Pressed the message via attribute-based search!")
                    return
            except Exception:
                continue
        print("Could not find message by attributes either.")
    except Exception as e:
        print(f"Error in attribute-based search: {e}")

def scan_and_write_message_list_jsonl(bundle_id, out_path, max_rows=10):
    app = ensure_app_focus(bundle_id)
    try:
        window = app.AXFocusedWindow
    except Exception:
        print("Could not get focused window.")
        return
    window_title = getattr(window, 'AXTitle', None) or 'Window'
    messages = deep_walk_collect_rows(window, [window_title], max_rows=max_rows)
    print(f"Writing {len(messages)} messages to {out_path}")
    with open(out_path, 'w') as f:
        for item in messages:
            f.write(json.dumps(item, ensure_ascii=False) + '\n')
    print(f"Message list JSONL written to {out_path}")
    return messages

def select_mail(omeClick, drag_time=0.4):
    if omeClick and isinstance(omeClick, list) and len(omeClick) == 2:
        print(f"[SELECT_MAIL] Moving mouse to {omeClick} and clicking...")
        pyautogui.moveTo(omeClick[0], omeClick[1], duration=drag_time)
        pyautogui.click()
        print("[SELECT_MAIL] Mouse click sent!")
    else:
        print("[SELECT_MAIL] Invalid omeClick coordinates.")

def select_message_by_index_mouse(jsonl_path, index, drag_time=0.4):
    with open(jsonl_path) as f:
        messages = [json.loads(line) for line in f]
    if index >= len(messages):
        print(f"No message at index {index}.")
        return
    msg = messages[index]
    print(f"Attempting to mouse-click message {index+1}: {msg.get('sender')} | {msg.get('subject')}")
    select_mail(msg.get('omeClick'), drag_time=drag_time)

def select_mail_by_index(jsonl_path, index, bundle_id, drag_time=0.4, focus_wait=1.0):
    with open(jsonl_path) as f:
        messages = [json.loads(line) for line in f]
    if index >= len(messages):
        print(f"No message at index {index}.")
        return
    msg = messages[index]
    omeClick = msg.get('omeClick')
    app = ensure_app_focus(bundle_id)
    time.sleep(focus_wait)
    if omeClick and isinstance(omeClick, list) and len(omeClick) == 2:
        print(f"[SELECT_MAIL] Moving mouse to {omeClick} and clicking...")
        pyautogui.moveTo(omeClick[0], omeClick[1], duration=drag_time)
        pyautogui.click()
        print("[SELECT_MAIL] Mouse click sent!")
    else:
        print("[SELECT_MAIL] Invalid omeClick coordinates.")

if __name__ == '__main__':
    bundle_id = "com.apple.mail"
    out_path = "ome/data/windows/window_com.apple.mail_message_list.jsonl"
    messages = scan_and_write_message_list_jsonl(bundle_id, out_path, max_rows=10)
    # Test: select the 7th message (index 6) using the mouse
    select_mail_by_index(out_path, 6, bundle_id, drag_time=0.4, focus_wait=1.0) 