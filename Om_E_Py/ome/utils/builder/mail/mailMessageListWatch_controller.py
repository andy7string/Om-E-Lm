"""
Self-contained Mail Message List Watcher & Extractor

- Watches ome/data/comControl/mailMessageList_selector.jsonl for commands (row selection, send_keys, readbody).
- Performs extraction of the Apple Mail message list using the macOS accessibility API.
- Writes output to the appropriate JSONL file.
- Marks commands as executed after processing.
- All logic is in this file (no import from mailMessageList_controller.py).
- Pattern: OME/controller writes a command file, this script reads and acts on it.
"""
import time
import json
import os
import argparse
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from ome.utils.env.env import COM_CONTROL_DIR
from ome.utils.builder.app.app_focus import ensure_app_focus
from datetime import datetime
import re
import ome

MAIL_JSONL = 'ome/data/windows/win_com.apple.mail.jsonl'
ACTIVE_BUNDLE_JSON = 'ome/data/windows/active_target_Bundle_ID.json'
MAIL_BUNDLE_ID = 'com.apple.mail'
MAIL_SELECTOR_FILE = os.path.join(COM_CONTROL_DIR, 'mailMessageList_selector.jsonl')
MAX_ROWS = 10
RETRY_DELAY = 0.2
ACTION_DELAY = 0.1

# --- Extraction logic (self-contained) ---
def safe_getattr(obj, attr):
    try:
        return getattr(obj, attr, None)
    except Exception:
        return None

def is_date(val):
    return isinstance(val, str) and re.search(r"(\d{4}/\d{2}/\d{2}|\d{4}-\d{2}-\d{2}|\d{1,2} [A-Za-z]{3,9} \d{4}|\d{1,2}/\d{1,2}/\d{2,4})", val)

def is_subject(val):
    return isinstance(val, str) and not is_date(val) and len(val) < 100

def is_sender(val):
    return isinstance(val, str) and not is_date(val) and val.istitle() and len(val) < 50

def classify_value(val):
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
    mailbox_part = (mailbox[:4] if mailbox else "____").ljust(4, '_')
    sender_part = (sender[:4] if sender else "____").ljust(4, '_')
    subject_part = (subject[:4] if subject else "____").ljust(4, '_')
    date_formatted = ""
    try:
        if date:
            if ' ' in date and len(date) > 10:
                date_part = date.split(' ')[0]
                time_part = date.split(' ')[1] if len(date.split(' ')) > 1 else "00:00:00"
                if '/' in date_part:
                    year, month, day = date_part.split('/')
                elif '-' in date_part:
                    year, month, day = date_part.split('-')
                else:
                    now = datetime.now()
                    year, month, day = str(now.year), str(now.month).zfill(2), str(now.day).zfill(2)
                    time_part = f"{now.hour:02d}:{now.minute:02d}:{now.second:02d}"
                if ':' in time_part:
                    time_parts = time_part.split(':')
                    hour = time_parts[0]
                    minute = time_parts[1] if len(time_parts) > 1 else "00"
                    second = time_parts[2] if len(time_parts) > 2 else "00"
                else:
                    hour, minute, second = "00", "00", "00"
                date_formatted = f"{year}{month.zfill(2)}{day.zfill(2)}_{hour.zfill(2)}{minute.zfill(2)}{second.zfill(2)}"
            else:
                now = datetime.now()
                date_formatted = f"{now.year}{now.month:02d}{now.day:02d}_{now.hour:02d}{now.minute:02d}{now.second:02d}"
        else:
            now = datetime.now()
            date_formatted = f"{now.year}{now.month:02d}{now.day:02d}_{now.hour:02d}{now.minute:02d}{now.second:02d}"
    except Exception:
        now = datetime.now()
        date_formatted = f"{now.year}{now.month:02d}{now.day:02d}_{now.hour:02d}{now.minute:02d}{now.second:02d}"
    key = f"{mailbox_part}_{sender_part}_{subject_part}_{date_formatted}"
    key = re.sub(r'[^\w\-_]', '_', key)
    return key

def extract_row_type_based_fast(children, row_index, mailbox=None):
    values = [safe_getattr(child, 'AXValue') for child in children]
    if len(values) > 5 and values[1] and ("Inbox - " in values[1] or "@" in values[1]):
        fields = {
            'row_index': row_index,
            'sender': values[0],
            'date': values[2],
            'subject': values[4],
        }
    else:
        fields = {
            'row_index': row_index,
            'sender': None,
            'subject': None,
            'date': None,
            'attachment': None,
        }
        for child in children:
            val = safe_getattr(child, 'AXValue')
            if val and val.strip():
                fields['sender'] = val
                break
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
        for idx, child in enumerate(children):
            val = safe_getattr(child, 'AXValue')
            if val in ('TO', 'Re:') and idx+1 < len(children):
                next_val = safe_getattr(children[idx+1], 'AXValue')
                if next_val:
                    subj = f"{val} {next_val}".strip()
                    if not fields['subject'] or len(subj) > len(fields['subject']):
                        fields['subject'] = subj
    message_key = make_message_key(
        mailbox or '',
        fields.get('row_index', ''),
        fields.get('sender', ''),
        fields.get('date', ''),
        fields.get('subject', '')
    )
    fields['message_key'] = message_key
    return {k: v for k, v in fields.items() if v is not None or k == 'sender'}

def extract_first_n_rows_fields(n=MAX_ROWS, row_index=None, app_object=None, send_keys_after_select=False):
    if n is None:
        n = MAX_ROWS
    bundle_id = MAIL_BUNDLE_ID
    messages = []
    app = app_object
    t0 = time.time()
    try:
        window = app.AXFocusedWindow
    except Exception:
        print("Could not get focused window. Retrying after delay...")
        try:
            app.activate()
            time.sleep(RETRY_DELAY)
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
    except Exception:
        pass
    try:
        rows = getattr(table, 'AXRows', [])
        if rows is None or not rows:
            return {"status": "success", "messages": messages, "row_count": len(messages)}
    except Exception:
        return {"status": "success", "messages": messages, "row_count": len(messages)}
    t3 = time.time()
    if row_index is not None:
        total_rows = len(rows)
        center = row_index - 1
        if row_index < 1 or row_index > total_rows:
            selected_rows = rows[:MAX_ROWS]
            row_offset = 0
            if rows:
                try:
                    rows[0].AXSelected = True
                except Exception:
                    pass
        else:
            half_window = MAX_ROWS // 2
            start = max(center - half_window, 0)
            end = start + MAX_ROWS
            if end > total_rows:
                end = total_rows
                start = max(end - MAX_ROWS, 0)
            try:
                rows[center].AXSelected = True
                print(f"[INFO] Selected row {row_index} via accessibility API")
                if send_keys_after_select:
                    print(f"[INFO] Waiting ACTION_DELAY ({ACTION_DELAY}s) before sending Enter key...")
                    time.sleep(ACTION_DELAY)
                    import Quartz
                    enter_key_code = 36
                    event_down = Quartz.CGEventCreateKeyboardEvent(None, enter_key_code, True)
                    event_up = Quartz.CGEventCreateKeyboardEvent(None, enter_key_code, False)
                    Quartz.CGEventPost(Quartz.kCGHIDEventTap, event_down)
                    Quartz.CGEventPost(Quartz.kCGHIDEventTap, event_up)
                    print("[INFO] Enter key sent.")
                    time.sleep(1)
            except Exception as e:
                print(f"[WARNING] Could not select row {row_index} via accessibility API: {e}")
            selected_rows = rows[start:end]
            row_offset = start
    else:
        selected_rows = rows[:MAX_ROWS]
        row_offset = 0
        if rows:
            try:
                rows[0].AXSelected = True
            except Exception:
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
                rich_cell = row_children[0]
        except Exception:
            pass
        if not rich_cell:
            continue
        children = getattr(rich_cell, 'AXChildren', [])
        row_data = extract_row_type_based_fast(children, current_row_index)
        messages.append(row_data)
    t6 = time.time()
    out_path_inbox = os.path.join('ome/data/messages/messages', f"mail_{bundle_id}.inbox.jsonl")
    os.makedirs(os.path.dirname(out_path_inbox), exist_ok=True)
    with open(out_path_inbox, 'w') as f_inbox:
        for item in messages:
            filtered = {k: item[k] for k in display_keys if k in item and item[k] is not None}
            f_inbox.write(json.dumps(filtered, ensure_ascii=False) + '\n')
    t7 = time.time()
    print(f"[PERF] App focus: {t1-t0:.3f}s | Find table: {t2-t1:.3f}s | Get rows: {t3-t2:.3f}s | Select/output rows: {t4-t3:.3f}s | Extract: {t6-t5:.3f}s | Write: {t7-t6:.3f}s | Total: {t7-t0:.3f}s | Rows: {len(messages)}")
    return {"status": "success", "messages": messages, "row_count": len(messages)}

# --- Watcher logic ---
class MailWindowWatcher(FileSystemEventHandler):
    def __init__(self, selector_file, mail_jsonl):
        self.selector_file = os.path.abspath(selector_file)
        self.mail_jsonl = os.path.abspath(mail_jsonl)
        self.last_window_ref = None
        self.last_window_title = None
        print(f"[WATCHDOG] Watching {self.selector_file} and {self.mail_jsonl}")

    def on_modified(self, event):
        event_path = os.path.abspath(event.src_path)
        # If the event is the window state file, check for window changes
        if event_path == self.mail_jsonl:
            try:
                with open(self.mail_jsonl, 'r', encoding='utf-8') as f:
                    state = json.load(f)
                active_target = state.get('active_target', {})
                window_ref = active_target.get('window_ref')
                window_title = active_target.get('window_title')
            except Exception as e:
                print(f"[WATCHDOG] Error reading {self.mail_jsonl}: {e}")
                window_ref = None
                window_title = None
            # Only scan if window_ref starts with Mail.messageViewer and window_title changed
            if window_ref and window_ref.startswith('Mail.messageViewer'):
                if window_title != self.last_window_title:
                    print(f"[WATCHDOG] window_title changed to '{window_title}', extracting message list...")
                    focus_result = ensure_app_focus(MAIL_BUNDLE_ID, fullscreen=False)
                    if focus_result["status"] == "success" and focus_result["app"]:
                        app_object = focus_result["app"]
                        extract_first_n_rows_fields(app_object=app_object)
                    else:
                        print("[WATCHDOG] Could not focus or access Mail app for extraction.")
            self.last_window_ref = window_ref
            self.last_window_title = window_title
        # If the event is the selector file, handle row selection/commands
        if event_path == self.selector_file:
            self.handle_selector_file()

    def handle_selector_file(self):
        try:
            with open(self.selector_file, 'r') as f:
                line = f.readline()
                if not line.strip():
                    # Even if the file is empty, still try to extract the message list
                    focus_result = ensure_app_focus(MAIL_BUNDLE_ID, fullscreen=False)
                    if focus_result["status"] == "success" and focus_result["app"]:
                        app_object = focus_result["app"]
                        extract_first_n_rows_fields(app_object=app_object)
                    else:
                        print("[WATCHDOG] Could not focus or access Mail app for extraction.")
                    return
                command = json.loads(line)
            if command.get('executed'):
                # Still extract the message list even if already executed
                focus_result = ensure_app_focus(MAIL_BUNDLE_ID, fullscreen=False)
                if focus_result["status"] == "success" and focus_result["app"]:
                    app_object = focus_result["app"]
                    extract_first_n_rows_fields(app_object=app_object)
                else:
                    print("[WATCHDOG] Could not focus or access Mail app for extraction.")
                return
            row_index = command.get('row_index', 1)
            send_keys = command.get('send_keys_after_select', False)
            readbody = command.get('readbody', False)
            print(f"[WATCHDOG] Selector file command: row_index={row_index}, send_keys={send_keys}, readbody={readbody}")
            focus_result = ensure_app_focus(MAIL_BUNDLE_ID, fullscreen=False)
            if focus_result["status"] == "success" and focus_result["app"]:
                app_object = focus_result["app"]
                extract_first_n_rows_fields(row_index=row_index, app_object=app_object, send_keys_after_select=send_keys)
            else:
                print("[WATCHDOG] Could not focus or access Mail app for extraction.")
            command['executed'] = True
            with open(self.selector_file, 'w') as f:
                f.write(json.dumps(command) + '\n')
            print(f"[WATCHDOG] Marked selector command as executed.")
        except Exception as e:
            print(f"[WATCHDOG] Error handling selector file: {e}")

def run_watcher():
    event_handler = MailWindowWatcher(MAIL_SELECTOR_FILE, MAIL_JSONL)
    observer = Observer()
    observer.schedule(event_handler, path=os.path.dirname(MAIL_SELECTOR_FILE), recursive=False)
    observer.schedule(event_handler, path=os.path.dirname(MAIL_JSONL), recursive=False)
    observer.start()
    print("[WATCHDOG] Mail message list watcher started.")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()

def main():
    parser = argparse.ArgumentParser(description="Mail message list watcher and extractor (self-contained, file-based control).")
    parser.add_argument('--watch', action='store_true', help='Run in event-driven watcher mode')
    args = parser.parse_args()
    if args.watch:
        run_watcher()
    else:
        print("Please use --watch mode for file-based control.")

if __name__ == '__main__':
    main() 