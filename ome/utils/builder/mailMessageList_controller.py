import json
import sys
import os
from ome.omeMenus import ensure_app_focus
import pyautogui
import time
from ome.utils.env.env import MAX_ROWS, MESSAGE_EXPORT_DIR

# mailMessageList_controller.py
#
# This module provides functions to extract and interact with the list of mail messages
# from a macOS application's accessibility tree (such as Apple Mail), using accessibility APIs.
# It includes logic to scan the message list, extract sender, date, subject, preview, and click coordinates,
# and output this information in a structured format for automation or analysis.

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
    """
    Recursively traverse the accessibility tree starting from 'element',
    collecting up to 'max_rows' mail message rows. For each row, extract:
      - sender: The sender of the message (from the first AXValue)
      - date: The date/time string (from the second AXValue)
      - omeClick: The center coordinates for clicking (from the element's position/size)
      - subject: The subject of the message (from the third AXValue, if present)
      - preview: The message preview/summary (from the child with summaryLabel AXIdentifier)
      - Only include messages whose omeClick coordinates are both positive and the element is visible.

    Args:
        element: The root accessibility element to start from (e.g., the message list container).
        path: (Optional) List tracking the path to the current element (used for recursion).
        found: (Optional) List accumulating found message rows (used for recursion).
        max_rows: (Optional, default 10) Maximum number of message rows to collect.

    Returns:
        found: List of dicts, each with keys: sender, date, omeClick, subject, preview.
    """
    if path is None:
        path = []
    if found is None:
        found = []
    # Stop recursion if we have enough rows
    if len(found) >= max_rows:
        return found
    # Get children of the current element
    try:
        children = getattr(element, 'AXChildren', [])
        if not isinstance(children, list):
            children = []
    except Exception:
        children = []
    values = []
    preview = None
    # Extract values and preview from children
    for child in children:
        try:
            val = getattr(child, 'AXValue', None)
            identifier = getattr(child, 'AXIdentifier', None)
            if val:
                values.append(val)
            # If this child is the summary/preview label, save its value
            if identifier == "Mail.messageList.cell.view.summaryLabel":
                preview = val
        except Exception:
            continue
    # If we have at least sender and date, and the element is visible, add this row to the results
    is_visible = True
    try:
        is_visible = getattr(element, 'AXVisible', True)
    except Exception:
        is_visible = True
    ome_click = extract_omeclick(element)
    if (
        len(values) >= 2
        and len(found) < max_rows
        and is_visible
        and ome_click
        and ome_click[0] > 0
        and ome_click[1] > 0
    ):
        found.append({
            'message_index': len(found) + 1,  # Numbering starts at 1
            'sender': values[0],  # First AXValue is usually the sender
            'date': values[1] if len(values) > 1 else None,  # Second AXValue is usually the date
            'omeClick': ome_click,  # Center coordinates for clicking
            'subject': values[2] if len(values) > 2 else None,  # Third AXValue is usually the subject
            'preview': preview  # Preview/summary if available
        })
        print(f"[MESSAGES] {len(found)}: {values[0]} | {values[1] if len(values) > 1 else None} | {values[2] if len(values) > 2 else None} | preview={preview}")
    # Only recurse if we still need more rows
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

def scroll_table_to_top(window):
    """
    Find the first AXTable in the window and scroll its first row to the top (if possible).
    """
    try:
        # Recursively search for the first AXTable in the window
        def find_table(element):
            try:
                role = getattr(element, 'AXRole', None)
            except Exception:
                role = None
            if role == 'AXTable':
                return element
            try:
                children = getattr(element, 'AXChildren', [])
                if not isinstance(children, list):
                    children = []
            except Exception:
                children = []
            for child in children:
                table = find_table(child)
                if table:
                    return table
            return None
        table = find_table(window)
        if not table:
            print("No AXTable found in window.")
            return
        rows = getattr(table, 'AXRows', [])
        if not rows:
            print("No rows found in AXTable.")
            return
        first_row = rows[0]
        # Try to call AXScrollToVisible on the first row
        try:
            if hasattr(first_row, 'AXScrollToVisible'):
                first_row.AXScrollToVisible()
                print("Scrolled first row to visible using AXScrollToVisible.")
            elif hasattr(first_row, 'AXShowMenu'):
                first_row.AXShowMenu()
                print("Tried to show menu for first row (fallback).")
            else:
                print("First row does not support AXScrollToVisible or AXShowMenu.")
        except Exception as e:
            print(f"Error scrolling first row to visible: {e}")
    except Exception as e:
        print(f"Error in scroll_table_to_top: {e}")

def scan_and_write_message_list_jsonl(bundle_id, out_path, max_rows=None):
    if max_rows is None:
        max_rows = MAX_ROWS
    app = ensure_app_focus(bundle_id)
    try:
        window = app.AXFocusedWindow
    except Exception:
        print("Could not get focused window.")
        return
    # Scroll the message list to the top before scanning
    scroll_table_to_top(window)
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
    import time
    bundle_id = "com.apple.mail"
    messages_dir = os.path.join(MESSAGE_EXPORT_DIR, "messages")
    os.makedirs(messages_dir, exist_ok=True)
    out_path = os.path.join(messages_dir, f"mail_{bundle_id}.jsonl")
    start_time = time.time()
    messages = scan_and_write_message_list_jsonl(bundle_id, out_path)
    elapsed = time.time() - start_time
    print(f"[TIMER] Scanning and writing message list took {elapsed:.2f} seconds.")
    # Test: select the 7th message (index 6) using the mouse
    #select_mail_by_index(out_path, 6, bundle_id, drag_time=0.4, focus_wait=1.0) 