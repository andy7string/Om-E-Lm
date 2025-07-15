"""
Mail Message List Controller

This script manages and extracts mail message data from Apple Mail using the macOS accessibility API.
It is designed to help you programmatically extract, classify, and cache message metadata (subject, sender, date, etc.)
from the Apple Mail message list, and automate tasks that require message details.

====================
PURPOSE
====================
- Scans the Apple Mail message table for visible messages.
- Extracts message metadata (subject, sender, date, etc.) from each row.
- Caches the message list as a JSONL file (location is configurable via your environment).
- Provides a command-line interface (CLI) for extracting and saving message data.

====================
KEY FEATURES
====================
- Automatic extraction: Extracts message data from the currently focused Apple Mail window.
- Heuristic classification: Classifies row values as subject, sender, date, etc. using heuristics.
- Caching: Saves extracted messages as a JSONL file for later use.
- Accessibility API Integration: Uses macOS accessibility API for reliable message selection.
- PyXA Body Extraction: Extracts full message body content using PyXA when a specific row is selected.
- CLI Usage:
    * --row <n>   Select and extract data for a specific row (1-based index), or extract the first N rows by default.

====================
HOW IT WORKS
====================
1. Focuses the Apple Mail app and finds the main message table using the accessibility API.
2. Uses the accessibility API to select specific messages when row_index is provided.
3. Extracts rows and classifies each cell's value as subject, sender, date, etc.
4. Writes the extracted message data to a JSONL file in the configured export directory.
5. If a specific row is selected, extracts the full message body using PyXA.

====================
PYTHON API USAGE EXAMPLES
====================
from ome.utils.builder.mail.mailMessageList_controller import extract_first_n_rows_fields

# Extract and save the first N rows (default N=MAX_ROWS)
extract_first_n_rows_fields()

# Extract and save a specific row (e.g., row 5)
extract_first_n_rows_fields(row_index=5)

====================
COMMAND LINE USAGE EXAMPLES
====================
# Extract and save the first N rows (default N=MAX_ROWS)
python -m ome.utils.builder.mail.mailMessageList_controller

# Extract and save a specific row (e.g., row 5)
python -m ome.utils.builder.mail.mailMessageList_controller --row 5

====================
WHEN TO USE
====================
- When you need to programmatically extract and cache message metadata from Apple Mail.
- When you want to automate workflows that require message details (subject, sender, etc.).
- When you want to script or automate mail-related data extraction tasks.
- When you need to extract the full body content of specific messages.

"""

import sys
import os
import json
import time
import re
import argparse
import hashlib
from Om_E_Py.ome.utils.builder.app.app_focus import ensure_app_focus
from env import UI_MESSAGE_EXPORT_DIR, UI_MAX_ROWS, UI_RETRY_DELAY, UI_ACTION_DELAY
from datetime import datetime

# PyXA import removed - accessibility API selection works reliably

def safe_getattr(obj, attr):
    """
    Safely gets an attribute from an object, returning None if not present or on error.
    """
    try:
        return getattr(obj, attr, None)
    except Exception:
        return None

def is_date(val):
    """
    Returns True if the value looks like a date string (various formats).
    """
    # Match common date formats
    return isinstance(val, str) and re.search(r"(\d{4}/\d{2}/\d{2}|\d{4}-\d{2}-\d{2}|\d{1,2} [A-Za-z]{3,9} \d{4}|\d{1,2}/\d{1,2}/\d{2,4})", val)

def is_subject(val):
    """
    Returns True if the value looks like a subject (not a date, size, or email, and short enough).
    """
    # Heuristic: not a date, not a size, not an email, not summary
    return isinstance(val, str) and not is_date(val) and len(val) < 100

def is_sender(val):
    """
    Returns True if the value looks like a sender name (capitalized, not a date, size, or email).
    """
    # Heuristic: capitalized name, not a date, not a size, not an email
    return isinstance(val, str) and not is_date(val) and val.istitle() and len(val) < 50

def classify_value(val):
    """
    Classifies a string value as 'date', 'sender', or 'subject'.
    Returns the field name or None if not classified.
    """
    if not isinstance(val, str) or not val.strip():
        return None
    if is_date(val):
        return 'date'
    if is_sender(val):
        return 'sender'
    if is_subject(val):
        return 'subject'
    return None

def make_message_key(mailbox, row_index, sender, date, subject):
    """
    Creates a message key in format: mailbox_first4_sender_first4_subject_first4_complete_date_seconds
    """
    # Get first 4 characters of each field, pad with underscores if needed
    mailbox_part = (mailbox[:4] if mailbox else "____").ljust(4, '_')
    sender_part = (sender[:4] if sender else "____").ljust(4, '_')
    subject_part = (subject[:4] if subject else "____").ljust(4, '_')
    
    # Parse and format the date
    date_formatted = ""
    try:
        if date:
            # Handle various date formats
            if ' ' in date and len(date) > 10:
                # Format like "2025-06-16 02:57:13 +0000" or "2025/06/16, 17:26"
                date_part = date.split(' ')[0]
                time_part = date.split(' ')[1] if len(date.split(' ')) > 1 else "00:00:00"
                
                # Handle different date formats
                if '/' in date_part:
                    # Format: "2025/06/16"
                    year, month, day = date_part.split('/')
                elif '-' in date_part:
                    # Format: "2025-06-16"
                    year, month, day = date_part.split('-')
                else:
                    # Fallback to current time
                    now = datetime.now()
                    year, month, day = str(now.year), str(now.month).zfill(2), str(now.day).zfill(2)
                    time_part = f"{now.hour:02d}:{now.minute:02d}:{now.second:02d}"
                
                # Handle time format
                if ':' in time_part:
                    time_parts = time_part.split(':')
                    hour = time_parts[0]
                    minute = time_parts[1] if len(time_parts) > 1 else "00"
                    second = time_parts[2] if len(time_parts) > 2 else "00"
                else:
                    hour, minute, second = "00", "00", "00"
                    
                date_formatted = f"{year}{month.zfill(2)}{day.zfill(2)}_{hour.zfill(2)}{minute.zfill(2)}{second.zfill(2)}"
            else:
                # Try to parse other formats or use current time
                now = datetime.now()
                date_formatted = f"{now.year}{now.month:02d}{now.day:02d}_{now.hour:02d}{now.minute:02d}{now.second:02d}"
        else:
            # Use current time if no date provided
            now = datetime.now()
            date_formatted = f"{now.year}{now.month:02d}{now.day:02d}_{now.hour:02d}{now.minute:02d}{now.second:02d}"
    except Exception:
        # Fallback to current time
        now = datetime.now()
        date_formatted = f"{now.year}{now.month:02d}{now.day:02d}_{now.hour:02d}{now.minute:02d}{now.second:02d}"
    
    # Create the key: mailbox_first4_sender_first4_subject_first4_complete_date_seconds
    key = f"{mailbox_part}_{sender_part}_{subject_part}_{date_formatted}"
    
    # Clean up any special characters that might cause issues
    key = re.sub(r'[^\w\-_]', '_', key)
    
    return key

def extract_row_type_based_fast(children, row_index, mailbox=None):
    """
    Robust extraction: uses index-based extraction for All Inboxes, fallback to old logic for others.
    """
    # Collect all values for analysis
    values = [safe_getattr(child, 'AXValue') for child in children]

    # Detect All Inboxes layout: second value is "Inbox - ..." or contains "@"
    if len(values) > 5 and values[1] and ("Inbox - " in values[1] or "@" in values[1]):
        # All Inboxes layout
        fields = {
            'row_index': row_index,
            'sender': values[0],
            'date': values[2],
            'subject': values[4],
        }
        # Optionally add preview/summary if you want:
        # fields['preview'] = values[6] if len(values) > 6 else None
    else:
        # Fallback to old logic for other mailboxes
        fields = {
            'row_index': row_index,
            'sender': None,
            'subject': None,
            'date': None,
            'attachment': None,
        }
        # First pass: find sender (first non-empty value)
        for child in children:
            val = safe_getattr(child, 'AXValue')
            if val and val.strip():
                fields['sender'] = val
                break

        # Second pass: classify remaining values
        for child in children:
            val = safe_getattr(child, 'AXValue')
            if not val or val == fields['sender']:
                continue
            if val.strip().startswith('Attachment:'):
                fields['attachment'] = val
                continue
            field = classify_value(val)
            if field and fields.get(field) is None:
                fields[field] = val

        # Handle special subject cases (TO, Re:)
        for idx, child in enumerate(children):
            val = safe_getattr(child, 'AXValue')
            if val in ('TO', 'Re:') and idx+1 < len(children):
                next_val = safe_getattr(children[idx+1], 'AXValue')
                if next_val:
                    subj = f"{val} {next_val}".strip()
                    if not fields['subject'] or len(subj) > len(fields['subject']):
                        fields['subject'] = subj

    # Generate message key
    message_key = make_message_key(
        mailbox or '',
        fields.get('row_index', ''),
        fields.get('sender', ''),
        fields.get('date', ''),
        fields.get('subject', '')
    )
    fields['message_key'] = message_key

    return {k: v for k, v in fields.items() if v is not None or k == 'sender'}

def extract_mail_body_for_selected_row_pyxa(row_data=None):
    """
    Extracts the mail body for the currently selected/focused message using PyXA, in-process.
    This function is called after the mail list controller sets focus to a specific row.
    """
    if not row_data:
        print("[ERROR] No row data provided for body extraction.")
        return
    try:
        print(f"[INFO] [IN-PROCESS] Extracting body for message: {row_data.get('sender', '')} - {row_data.get('subject', '')}")
        import PyXA
        import os, json
        app = PyXA.Application("Mail")
        selected_messages = app.selection
        msg = None
        if selected_messages and len(selected_messages) > 0:
            msg = selected_messages[0]
        else:
            viewers = app.message_viewers()
            if viewers and len(viewers) > 0:
                mailbox = viewers[0].selected_mailbox
                messages = mailbox.messages()
                if messages and len(messages) > 0:
                    msg = messages[0]
        if msg is None:
            print("No message is selected or focused in Apple Mail.")
            return
        recipients = []
        try:
            recipients = [str(r) for r in getattr(msg, 'to_recipients', [])]
        except Exception:
            pass
        date_sent = None
        try:
            date_sent = str(msg.date_sent)
        except Exception:
            pass
        mailbox = None
        try:
            mailbox = str(msg.mailbox)
        except Exception:
            pass
        body = str(msg.content)
        body_lines = body.splitlines()
        body_lines = [line for line in body_lines if line.strip() and line.strip().replace('\u00a0', '') != ""]
        attachments = []
        for att in msg.mail_attachments():
            name = str(att.name)
            ext = os.path.splitext(name)[1] if '.' in name else ''
            attachments.append({
                'name': name,
                'extension': ext,
                'best_guess_path': None
            })
        message_key = row_data.get('message_key')
        entry = {
            'message_key': message_key,
            'subject': str(msg.subject),
            'sender': str(msg.sender),
            'date_sent': date_sent,
            'recipients': recipients,
            'body_lines': body_lines,
            'attachments': attachments,
            'mailbox': mailbox,
            'row_index': row_data.get('row_index')
        }
        output_dir = os.path.join(UI_MESSAGE_EXPORT_DIR, 'mailMessageBody')
        os.makedirs(output_dir, exist_ok=True)
        filename = f"mail_{message_key}.json"
        out_file = os.path.join(output_dir, filename)
        out_file_jsonl = os.path.splitext(out_file)[0] + '.jsonl'
        with open(out_file, 'w', encoding='utf-8') as f:
            json.dump(entry, f, ensure_ascii=False, indent=2)
        with open(out_file_jsonl, 'w', encoding='utf-8') as f:
            f.write(json.dumps(entry, ensure_ascii=False) + '\n')
        print(f"[INFO] [IN-PROCESS] Wrote message to {out_file}")
        print(f"[INFO] [IN-PROCESS] Wrote message to {out_file_jsonl}")
    except Exception as e:
        print(f"[WARNING] [IN-PROCESS] Could not extract body: {e}")

def extract_first_n_rows_fields(n=None, row_index=None, app_object=None, send_keys_after_select=False):
    """
    Extracts and saves the first N rows (default N=MAX_ROWS) or a specific row from the Apple Mail message list.
    If send_keys_after_select is True, sends Enter key after selecting the row (for opening message in new window).
    """
    if n is None:
        n = UI_MAX_ROWS
    bundle_id = "com.apple.mail"
    messages = []  # Always define messages at the start
    
    # Use provided app object if available, otherwise focus fresh app
    if app_object is not None:
        app = app_object
        print(f"[INFO] Using provided app object for {bundle_id}")
        time.sleep(UI_RETRY_DELAY)  # Add delay for cached app objects
    else:
        focus_result = ensure_app_focus(bundle_id, fullscreen=True)
        if focus_result["status"] != "success" or not focus_result["app"]:
            print(f"[ERROR] Could not focus or access app: {focus_result.get('error')}")
            return {"status": "error", "error": "Could not get focused window"}
        app = focus_result["app"]
        time.sleep(UI_RETRY_DELAY)
    
    t0 = time.time()
    try:
        window = app.AXFocusedWindow
    except Exception:
        print("Could not get focused window. Retrying after delay...")
        try:
            app.activate()
            time.sleep(UI_RETRY_DELAY)
            window = app.AXFocusedWindow
        except Exception:
            print("[ERROR] Still could not get focused window after retry.")
            return {"status": "error", "error": "Could not get focused window"}
    t1 = time.time()
    
    def find_mail_table(element):
        try:
            children = getattr(element, 'AXChildren', [])
            if children is None:
                children = []
        except Exception:
            return None
        for child in children:
            try:
                role = getattr(child, 'AXRole', None)
            except Exception:
                role = None
            if role == 'AXTable':
                return child
        for child in children:
            table = find_mail_table(child)
            if table:
                return table
        return None
    
    table = find_mail_table(window)
    if not table:
        return {"status": "error", "error": "Could not get focused window"}
    t2 = time.time()
    
    try:
        if hasattr(table, 'AXScrollToVisible'):
            table.AXScrollToVisible()
        pass
    except Exception as e:
        pass
    
    try:
        rows = getattr(table, 'AXRows', [])
        if rows is None or not rows:
            return {"status": "success", "messages": messages, "row_count": len(messages)}
    except Exception:
        return {"status": "success", "messages": messages, "row_count": len(messages)}
    t3 = time.time()
    
    # Use accessibility API for message selection
    if row_index is not None:
        total_rows = len(rows)
        center = row_index - 1  # zero-based
        if row_index < 1 or row_index > total_rows:
            selected_rows = rows[:UI_MAX_ROWS]
            row_offset = 0
            if rows:
                try:
                    rows[0].AXSelected = True
                except Exception as e:
                    pass
        else:
            half_window = UI_MAX_ROWS // 2
            start = max(center - half_window, 0)
            end = start + UI_MAX_ROWS
            if end > total_rows:
                end = total_rows
                start = max(end - UI_MAX_ROWS, 0)
            try:
                rows[center].AXSelected = True
                print(f"[INFO] Selected row {row_index} via accessibility API")
                if send_keys_after_select:
                    print(f"[INFO] Waiting ACTION_DELAY ({UI_ACTION_DELAY}s) before sending Enter key...")
                    time.sleep(UI_ACTION_DELAY)
                    from Om_E_Py.ome.AXKeyboard import modKeyFlagConstants
                    import Quartz
                    enter_key_code = 36
                    event_down = Quartz.CGEventCreateKeyboardEvent(None, enter_key_code, True)
                    event_up = Quartz.CGEventCreateKeyboardEvent(None, enter_key_code, False)
                    Quartz.CGEventPost(Quartz.kCGHIDEventTap, event_down)
                    Quartz.CGEventPost(Quartz.kCGHIDEventTap, event_up)
                    print("[INFO] Enter key sent.")
                    time.sleep(1)  # Optional: wait for window to open
            except Exception as e:
                print(f"[WARNING] Could not select row {row_index} via accessibility API: {e}")
            selected_rows = rows[start:end]
            row_offset = start
    else:
        selected_rows = rows[:UI_MAX_ROWS]
        row_offset = 0
        if rows:
            try:
                rows[0].AXSelected = True
            except Exception as e:
                pass
    t4 = time.time()
    
    display_keys = ['row_index', 'message_key', 'sender', 'subject', 'date', 'attachment']
    t5 = time.time()
    
    for i, first_row in enumerate(selected_rows, start=1):
        current_row_index = row_offset + i
        rich_cell = None
        try:
            row_children = getattr(first_row, 'AXChildren', [])
            for child in row_children:
                if 'RichMessageCellView' in str(type(child)):
                    rich_cell = child
                    break
            if not rich_cell and row_children:
                rich_cell = row_children[0]  # fallback
        except Exception:
            pass
        if not rich_cell:
            continue
        children = getattr(rich_cell, 'AXChildren', [])
        row_data = extract_row_type_based_fast(children, current_row_index)
        messages.append(row_data)
    t6 = time.time()
    
    out_path_inbox = os.path.join(UI_MESSAGE_EXPORT_DIR, "messages", f"mail_{bundle_id}.inbox.jsonl")
    os.makedirs(os.path.dirname(out_path_inbox), exist_ok=True)
    with open(out_path_inbox, 'w') as f_inbox:
        for item in messages:
            filtered = {k: item[k] for k in display_keys if k in item and item[k] is not None}
            f_inbox.write(json.dumps(filtered, ensure_ascii=False) + '\n')
    t7 = time.time()
    
    print(f"[PERF] App focus: {t1-t0:.3f}s | Find table: {t2-t1:.3f}s | Get rows: {t3-t2:.3f}s | Select/output rows: {t4-t3:.3f}s | Extract: {t6-t5:.3f}s | Write: {t7-t6:.3f}s | Total: {t7-t0:.3f}s | Rows: {len(messages)}")
    
    if row_index is not None:
        print(f"[INFO] Row {row_index} was selected, extracting mail body...")
        time.sleep(1)
        # Find the row data for the selected row
        selected_row_data = None
        for msg in messages:
            if msg.get('row_index') == row_index:
                selected_row_data = msg
                break
        if selected_row_data:
            extract_mail_body_for_selected_row_pyxa(selected_row_data)
        else:
            print(f"[WARNING] Could not find selected row {row_index} in final message list")
    return {"status": "success", "messages": messages, "row_count": len(messages)}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Extract Apple Mail table row data via accessibility API.")
    parser.add_argument('--row', '-r', type=int, default=None, help='Row index (1-based) to select/focus. If not set, selects the first row.')
    parser.add_argument('--send-keys-after-select', action='store_true', help='Send Enter key after selecting the row (for opening message in new window)')
    args = parser.parse_args()

    extract_first_n_rows_fields(n=UI_MAX_ROWS, row_index=args.row, send_keys_after_select=args.send_keys_after_select) 