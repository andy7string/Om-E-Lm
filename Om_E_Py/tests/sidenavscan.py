import json
import sys
import os
import time
from ome.utils.builder.app.app_focus import ensure_app_focus
import pyautogui

def extract_omeclick(element):
    try:
        pos = getattr(element, 'AXPosition', None)
        size = getattr(element, 'AXSize', None)
        if pos and size and isinstance(pos, (list, tuple)) and isinstance(size, (list, tuple)):
            return [float(pos[0]) + float(size[0])/2, float(pos[1]) + float(size[1])/2]
    except Exception:
        pass
    return None

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

def select_sidebar_mailbox_by_index(jsonl_path, index, bundle_id, focus_wait=1.0):
    with open(jsonl_path) as f:
        mailboxes = [json.loads(line) for line in f]
    if index >= len(mailboxes):
        print(f"No mailbox at index {index}.")
        return
    mailbox = mailboxes[index]
    path = mailbox['path']
    app = ensure_app_focus(bundle_id)
    time.sleep(focus_wait)
    try:
        window = app.AXFocusedWindow
    except Exception:
        print("Could not get focused window for sidebar nav.")
        return
    elem = resolve_element_by_path(window, path)
    if elem:
        # If the element is not actionable, try its children
        if not hasattr(elem, 'Press'):
            try:
                children = getattr(elem, 'AXChildren', [])
                for child in children:
                    if hasattr(child, 'Press'):
                        child.Press()
                        print(f"Pressed mailbox: {mailbox.get('title')} (via child)")
                        return
                print("No actionable child found to press.")
            except Exception as e:
                print(f"Error accessing children: {e}")
        else:
            try:
                elem.Press()
                print(f"Pressed mailbox: {mailbox.get('title')}")
            except Exception as e:
                print(f"Error pressing mailbox: {e}")
    else:
        print("Could not resolve mailbox element by path.")

def select_sidebar_label_by_title(jsonl_path, title, bundle_id, focus_wait=1.0):
    with open(jsonl_path) as f:
        mailboxes = [json.loads(line) for line in f]
    found = None
    for mailbox in mailboxes:
        if mailbox.get('title') == title:
            found = mailbox
            break
    if not found:
        print(f"No mailbox found with title '{title}'.")
        return
    path = found['path']
    app = ensure_app_focus(bundle_id)
    time.sleep(focus_wait)
    try:
        window = app.AXFocusedWindow
    except Exception:
        print("Could not get focused window for sidebar nav.")
        return
    elem = resolve_element_by_path(window, path)
    if elem:
        try:
            elem.Press()
            print(f"Pressed label: {title}")
        except Exception as e:
            print(f"Error pressing label: {e}")
    else:
        print("Could not resolve label element by path.")

def find_axcell_by_label(element, label):
    try:
        role = getattr(element, 'AXRole', None)
    except Exception:
        role = None
    try:
        title = getattr(element, 'AXTitle', None) or getattr(element, 'AXDescription', None)
    except Exception:
        title = None
    if role == 'AXCell' and title == label:
        return element
    # Recurse into children
    try:
        children = getattr(element, 'AXChildren', [])
        if not isinstance(children, list):
            children = []
    except Exception:
        children = []
    for child in children:
        found = find_axcell_by_label(child, label)
        if found:
            return found
    return None

def select_sidebar_label_axcell(jsonl_path, label, bundle_id, focus_wait=1.0):
    with open(jsonl_path) as f:
        mailboxes = [json.loads(line) for line in f]
    app = ensure_app_focus(bundle_id)
    time.sleep(focus_wait)
    try:
        window = app.AXFocusedWindow
    except Exception:
        print("Could not get focused window for sidebar nav.")
        return
    cell = find_axcell_by_label(window, label)
    if cell:
        try:
            cell.Press()
            print(f"Pressed sidebar label/cell: {label}")
        except Exception as e:
            print(f"Error pressing AXCell: {e}")
    else:
        print(f"AXCell with title '{label}' not found in window.")

def select_sidebar_label_mouse(jsonl_path, label, bundle_id, drag_time=0.8, focus_wait=1.0):
    with open(jsonl_path) as f:
        mailboxes = [json.loads(line) for line in f]
    mailbox = next((m for m in mailboxes if m.get('title') == label), None)
    if not mailbox:
        print(f"Label '{label}' not found in JSONL.")
        return
    omeClick = mailbox.get('omeClick')
    app = ensure_app_focus(bundle_id)
    time.sleep(focus_wait)
    if omeClick and isinstance(omeClick, list) and len(omeClick) == 2:
        print(f"[SELECT_NAV] Moving mouse to {omeClick} and clicking...")
        pyautogui.moveTo(omeClick[0], omeClick[1], duration=drag_time)
        pyautogui.click()
        print(f"[SELECT_NAV] Mouse click sent for label: {label}")
    else:
        print("[SELECT_NAV] Invalid omeClick coordinates.")

if __name__ == '__main__':
    bundle_id = "com.apple.mail"
    jsonl_path = "ome/data/windows/window_com.apple.mail_sidenav.jsonl"
    # Test: select the 'Orange' label in the sidebar using the mouse
    select_sidebar_label_mouse(jsonl_path, "Orange", bundle_id, drag_time=0.8, focus_wait=1.0) 