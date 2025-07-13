import json
import sys
import os
import time
from ome.utils.builder.app.app_focus import ensure_app_focus
from ome import getAllWindows
import Quartz

def extract_has_children(element):
    try:
        children = getattr(element, 'AXChildren', [])
        if not isinstance(children, list):
            children = []
        return bool(children), len(children)
    except Exception:
        return False, 0

def resolve_element_by_path(window, path):
    current = window
    for step in path[1:]:  # skip the window title
        children = getattr(current, 'AXChildren', [])
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
            return None
        current = found
    return current

def extract_attributes(element, path):
    attrs = {'path': path}
    # Robustly extract only the essentials
    for attr in [
        'AXRole', 'AXSubrole', 'AXRoleDescription', 'AXIdentifier', 'AXEnabled',
        'AXTitle', 'AXDescription', 'AXHelp', 'AXMenuItemCmdModifiers', 'AXMenuItemCmdChar'
    ]:
        try:
            value = getattr(element, attr, None)
        except Exception:
            value = None
        if value not in (None, '', []):
            attrs[attr] = value
    # Title/description mapping
    attrs['title'] = attrs.pop('AXTitle', None) or attrs.get('AXDescription')
    attrs['description'] = attrs.pop('AXHelp', None) or attrs.get('AXDescription')
    # omeClick
    try:
        pos = getattr(element, 'AXPosition', None)
        size = getattr(element, 'AXSize', None)
        if pos and size and isinstance(pos, (list, tuple)) and isinstance(size, (list, tuple)):
            attrs['omeClick'] = [float(pos[0]) + float(size[0])/2, float(pos[1]) + float(size[1])/2]
    except Exception:
        pass
    # Shortcuts
    if 'AXMenuItemCmdModifiers' in attrs:
        attrs['shortcut_modifiers'] = attrs.pop('AXMenuItemCmdModifiers')
    if 'AXMenuItemCmdChar' in attrs:
        attrs['shortcut_key'] = attrs.pop('AXMenuItemCmdChar')
    # Remove any remaining AX* keys not in the essentials
    for k in list(attrs.keys()):
        if k.startswith('AX') and k not in ('AXRole', 'AXSubrole', 'AXRoleDescription', 'AXIdentifier', 'AXEnabled'):
            del attrs[k]
    return {k: v for k, v in attrs.items() if v not in (None, '', [])}

def click_then_rescan(app, elem, wait_time=1.0, max_wait=2.0):
    try:
        elem.Press()
        time.sleep(wait_time)
        start = time.time()
        orig_window = app.AXFocusedWindow
        while time.time() - start < max_wait:
            new_window = app.AXFocusedWindow
            if new_window != orig_window:
                return new_window._generateChildrenR(), new_window
            time.sleep(0.1)
        # If no new window, fallback to original
        return orig_window._generateChildrenR(), orig_window
    except Exception as e:
        print(f"Error in click_then_rescan: {e}")
        return [], None

def get_all_system_windows():
    """
    Returns a list of dictionaries for all visible windows on macOS using Quartz.
    Each dict contains at least 'kCGWindowNumber', 'kCGWindowOwnerName', 'kCGWindowName'.
    """
    windows = Quartz.CGWindowListCopyWindowInfo(
        Quartz.kCGWindowListExcludeDesktopElements | Quartz.kCGWindowListOptionOnScreenOnly,
        Quartz.kCGNullWindowID
    )
    return windows

def click_then_rescan_any_window(app, elem, wait_time=3.0, max_wait=3.0):
    try:
        elem.Press()
        time.sleep(wait_time)
        # Capture all system windows before
        before_windows = {w['kCGWindowNumber'] for w in get_all_system_windows()}
        start = time.time()
        while time.time() - start < max_wait:
            after_windows = get_all_system_windows()
            after_numbers = {w['kCGWindowNumber'] for w in after_windows}
            new_numbers = after_numbers - before_windows
            if new_numbers:
                for w in after_windows:
                    if w['kCGWindowNumber'] in new_numbers:
                        print(f"[INFO] New system window detected: {w.get('kCGWindowName', None)} (Owner: {w.get('kCGWindowOwnerName', None)})")
                        # Try to find the corresponding AX window in Om-E-Mac
                        # Fallback: return empty list, as we can't get the AXUIElement directly from CGWindowNumber
                        return [], None
            time.sleep(0.1)
        return [], None
    except Exception as e:
        print(f"[ERROR] in system-aware rescan: {e}")
        return [], None

def extract_omeclick(element):
    try:
        pos = getattr(element, 'AXPosition', None)
        size = getattr(element, 'AXSize', None)
        if pos and size and isinstance(pos, (list, tuple)) and isinstance(size, (list, tuple)):
            return [float(pos[0]) + float(size[0])/2, float(pos[1]) + float(size[1])/2]
    except Exception:
        pass
    return None

def extract_sidebar_mailboxes(window, parent_path):
    sidebar = window.findFirst(AXRole='AXSidebar') or window.findFirst(AXRole='AXOutline')
    mailboxes = []
    if sidebar:
        try:
            for idx, child in enumerate(getattr(sidebar, 'AXChildren', [])):
                try:
                    name = getattr(child, 'AXTitle', None) or getattr(child, 'AXDescription', None)
                except Exception:
                    name = None
                omeClick = extract_omeclick(child)
                path = parent_path + [name] if name else parent_path + [f"Child_{idx}"]
                mailbox_entry = {
                    'path': path,
                    'AXRole': getattr(child, 'AXRole', None),
                    'title': name,
                    'description': getattr(child, 'AXDescription', None),
                    'omeClick': omeClick
                }
                print(f"[SIDENAV] Found mailbox: {name} at path {path}")
                mailboxes.append(mailbox_entry)
        except Exception as e:
            print(f"[SIDENAV] Error extracting sidebar mailboxes: {e}")
    else:
        print("[SIDENAV] Sidebar not found in window.")
    return mailboxes

def extract_toolbar_buttons(window, parent_path):
    toolbar = window.findFirst(AXRole='AXToolbar')
    buttons = []
    if toolbar:
        try:
            for idx, child in enumerate(getattr(toolbar, 'AXChildren', [])):
                try:
                    title = getattr(child, 'AXTitle', None) or getattr(child, 'AXDescription', None)
                except Exception:
                    title = None
                omeClick = extract_omeclick(child)
                path = parent_path + [title] if title else parent_path + [f"Child_{idx}"]
                button_entry = {
                    'path': path,
                    'AXRole': getattr(child, 'AXRole', None),
                    'title': title,
                    'description': getattr(child, 'AXDescription', None),
                    'omeClick': omeClick
                }
                print(f"[TOOLBAR] Found button: {title} at path {path}")
                buttons.append(button_entry)
        except Exception as e:
            print(f"[TOOLBAR] Error extracting toolbar buttons: {e}")
    else:
        print("[TOOLBAR] Toolbar not found in window.")
    return buttons

def extract_top_n_messages(window, parent_path, max_rows=20):
    msg_list = window.findFirst(AXRole='AXTable') or window.findFirst(AXRole='AXOutline')
    messages = []
    if msg_list:
        try:
            for idx, row in enumerate(getattr(msg_list, 'AXChildren', [])[:max_rows]):
                sender = subject = date = None
                for child in getattr(row, 'AXChildren', []):
                    val = getattr(child, 'AXValue', None)
                    # Heuristic: assign sender, subject, date based on order or class
                    if not sender:
                        sender = val
                    elif not subject:
                        subject = val
                    elif not date:
                        date = val
                omeClick = extract_omeclick(row)
                path = parent_path + [f"row_{idx}"]
                message_entry = {
                    'path': path,
                    'AXRole': getattr(row, 'AXRole', None),
                    'sender': sender,
                    'subject': subject,
                    'date': date,
                    'omeClick': omeClick
                }
                print(f"[MESSAGES] Found message: {sender} | {subject} | {date} at path {path}")
                messages.append(message_entry)
        except Exception as e:
            print(f"[MESSAGES] Error extracting messages: {e}")
    else:
        print("[MESSAGES] Message list not found in window.")
    return messages

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