import sys
import os
import json
import time
import re
import argparse
from ome.utils.app_focus import ensure_app_focus
from env import UI_MESSAGE_EXPORT_DIR, UI_MAX_ROWS

def extract_omeclick(element):
    try:
        pos = getattr(element, 'AXPosition', None)
        size = getattr(element, 'AXSize', None)
        if pos and size and isinstance(pos, (list, tuple)) and isinstance(size, (list, tuple)):
            return [float(pos[0]) + float(size[0])/2, float(pos[1]) + float(size[1])/2]
    except Exception:
        pass
    return None

def safe_getattr(obj, attr):
    try:
        return getattr(obj, attr, None)
    except Exception:
        return None

def extract_first_n_rows_fields(n=None, row_index=None):
    if n is None:
        n = UI_MAX_ROWS
    bundle_id = "com.apple.mail"
    app = ensure_app_focus(bundle_id)
    t0 = time.time()
    try:
        window = app.AXFocusedWindow
    except Exception:
        sys.exit(1)
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
        sys.exit(1)
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
            sys.exit(0)
    except Exception:
        sys.exit(0)
    t3 = time.time()
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
            except Exception as e:
                pass
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
    display_keys = ['row_index', 'omeClick', 'mailbox', 'sender', 'subject', 'date', 'attachment', 'attachment_size', 'summary', 'sender_email']
    messages = []
    t5 = time.time()
    size_pattern = re.compile(r"\\b(\\d+[.,]?\\d*)\\s*(KB|MB|GB)\\b", re.IGNORECASE)
    for i, first_row in enumerate(selected_rows, start=1):
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
        row_data = {}
        row_data['row_index'] = row_offset + i  # actual row number in the table
        row_data['omeClick'] = extract_omeclick(first_row)

        mailbox_val = safe_getattr(children[1], 'AXValue') if len(children) > 1 else None
        if mailbox_val and isinstance(mailbox_val, str) and mailbox_val.startswith('Inbox -'):
            mailbox_row = {}
            mailbox_row['row_index'] = row_data['row_index']
            mailbox_row['omeClick'] = row_data['omeClick']
            mailbox_row['sender'] = safe_getattr(children[0], 'AXValue') if len(children) > 0 else None
            mailbox_row['mailbox'] = mailbox_val
            mailbox_row['date'] = safe_getattr(children[2], 'AXValue') if len(children) > 2 else None
            # Subject logic
            subject = None
            if len(children) > 3 and safe_getattr(children[3], 'AXValue') == 'TO':
                subject = f"TO {safe_getattr(children[4], 'AXValue') or ''}".strip()
            else:
                subject = safe_getattr(children[4], 'AXValue') if len(children) > 4 else None
            mailbox_row['subject'] = subject if subject else "(No Subject)"
            # Attachment size
            attachment_size = None
            if len(children) > 5:
                val = safe_getattr(children[5], 'AXValue')
                if isinstance(val, str) and re.match(r"^\s*\d+[.,]?\d*\s*(KB|MB|GB|bytes)\b", val, re.IGNORECASE):
                    attachment_size = val
            if attachment_size:
                mailbox_row['attachment_size'] = attachment_size
            # Summary: prefer children[7], then [6]
            summary = ''
            for idx in [7, 6]:
                if len(children) > idx:
                    val = safe_getattr(children[idx], 'AXValue')
                    if isinstance(val, str) and val and len(val) > len(summary):
                        summary = val
            if summary:
                mailbox_row['summary'] = summary
            # Sender email from any child with '@' in AXValue
            sender_email = None
            for child in children:
                val = safe_getattr(child, 'AXValue')
                if isinstance(val, str) and '@' in val:
                    sender_email = val
                    break
            if sender_email:
                mailbox_row['sender_email'] = sender_email
            messages.append(mailbox_row)
            continue  # Done with this row
        elif len(children) > 1 and children[0] is None and children[1] is None:
            offset_row = {}
            offset_row['row_index'] = row_data['row_index']
            offset_row['omeClick'] = row_data['omeClick']
            offset_row['sender'] = safe_getattr(children[2], 'AXValue') if len(children) > 2 else None
            offset_row['mailbox'] = safe_getattr(children[3], 'AXValue') if len(children) > 3 else None
            offset_row['date'] = safe_getattr(children[4], 'AXValue') if len(children) > 4 else None
            # Subject logic
            subject = None
            if len(children) > 5 and safe_getattr(children[5], 'AXValue') == 'TO':
                subject = f"TO {safe_getattr(children[6], 'AXValue') or ''}".strip()
            else:
                subject = safe_getattr(children[6], 'AXValue') if len(children) > 6 else None
            offset_row['subject'] = subject if subject else "(No Subject)"
            # Attachment size
            attachment_size = None
            if len(children) > 7:
                val = safe_getattr(children[7], 'AXValue')
                if isinstance(val, str) and re.match(r"^\s*\d+[.,]?\d*\s*(KB|MB|GB|bytes)\b", val, re.IGNORECASE):
                    attachment_size = val
            if attachment_size:
                offset_row['attachment_size'] = attachment_size
            # Summary: children[8]
            summary = safe_getattr(children[8], 'AXValue') if len(children) > 8 else None
            if summary:
                offset_row['summary'] = summary
            # Sender email from any child with '@' in AXValue
            sender_email = None
            for child in children:
                val = safe_getattr(child, 'AXValue')
                if isinstance(val, str) and '@' in val:
                    sender_email = val
                    break
            if sender_email:
                offset_row['sender_email'] = sender_email
            messages.append(offset_row)
            continue  # Done with this row
        else:
            row_data['sender'] = safe_getattr(children[0], 'AXValue') if len(children) > 0 else None
            # If sender is present, use a dedicated mapping for sent items
            if row_data['sender']:
                sent_row = {}
                sent_row['row_index'] = row_data['row_index']
                sent_row['omeClick'] = row_data['omeClick']
                sent_row['sender'] = row_data['sender']
                sent_row['date'] = safe_getattr(children[1], 'AXValue') if len(children) > 1 else None
                subject = safe_getattr(children[2], 'AXValue') if len(children) > 2 else None
                # If subject contains 'TO', concatenate with children[3].AXValue
                if subject and 'TO' in subject and len(children) > 3:
                    subject = f"{subject} {safe_getattr(children[3], 'AXValue') or ''}".strip()
                sent_row['subject'] = subject if subject else "(No Subject)"
                # Attachment size from children[3], children[4], or children[5]
                attachment_size = None
                for idx in [3, 4, 5]:
                    if len(children) > idx:
                        val = safe_getattr(children[idx], 'AXValue')
                        if isinstance(val, str) and re.match(r"^\s*\d+[.,]?\d*\s*(KB|MB|GB|bytes)\b", val, re.IGNORECASE):
                            attachment_size = val
                            break
                if attachment_size:
                    sent_row['attachment_size'] = attachment_size
                # Attachment file name from any child
                attachment = None
                for child in children:
                    val = safe_getattr(child, 'AXValue')
                    if isinstance(val, str) and val.strip().startswith("Attachment:"):
                        attachment = val
                        break
                if attachment:
                    sent_row['attachment'] = attachment
                # Summary: longest unused string
                used_values = {sent_row.get('sender'), sent_row.get('date'), sent_row.get('subject'), attachment, attachment_size, "(No Subject)"}
                summary = ''
                for child in children:
                    val = safe_getattr(child, 'AXValue')
                    if (
                        isinstance(val, str)
                        and val
                        and val not in used_values
                        and not re.match(r"^\s*\d+[.,]?\d*\s*(KB|MB|GB|bytes)\b", val, re.IGNORECASE)
                        and not val.strip().startswith("Attachment:")
                        and len(val) > len(summary)
                    ):
                        summary = val
                if summary:
                    sent_row['summary'] = summary
                # Sender email
                sender_email = None
                if sent_row['sender'] and "@" in sent_row['sender']:
                    sender_email = sent_row['sender']
                else:
                    for child in children:
                        val = safe_getattr(child, 'AXValue')
                        if isinstance(val, str) and "@" in val and val != sent_row['sender']:
                            sender_email = val
                            break
                if sender_email:
                    sent_row['sender_email'] = sender_email
                messages.append(sent_row)
                continue  # Skip the rest of the loop for sent items
        row_data['date'] = safe_getattr(children[1], 'AXValue') if len(children) > 1 else None
        subject = safe_getattr(children[2], 'AXValue') if len(children) > 2 else None
        row_data['subject'] = subject if subject else "(No Subject)"
        # Attachment size from children[3]
        attachment_size = None
        if len(children) > 3:
            val = safe_getattr(children[3], 'AXValue')
            if isinstance(val, str) and re.match(r"^\s*\d+[.,]?\d*\s*(KB|MB|GB|bytes)\b", val, re.IGNORECASE):
                attachment_size = val
        if attachment_size:
            row_data['attachment_size'] = attachment_size
        # Attachment file name from any child
        attachment = None
        for child in children:
            val = safe_getattr(child, 'AXValue')
            if isinstance(val, str) and val.strip().startswith("Attachment:"):
                attachment = val
                break
        if attachment:
            row_data['attachment'] = attachment
        # Summary: longest unused string
        used_values = {row_data.get('sender'), row_data.get('date'), row_data.get('subject'), attachment, attachment_size}
        summary = ''
        for child in children:
            val = safe_getattr(child, 'AXValue')
            if isinstance(val, str) and val and val not in used_values and len(val) > len(summary):
                summary = val
        if summary:
            row_data['summary'] = summary
        # Sender email from any child with '@' in AXValue
        sender_email = None
        for child in children:
            val = safe_getattr(child, 'AXValue')
            if isinstance(val, str) and '@' in val:
                sender_email = val
                break
        if sender_email:
            row_data['sender_email'] = sender_email
        # Print all AXValue attributes for each child for debugging
        for idx, child in enumerate(children):
            val = safe_getattr(child, 'AXValue')
            print(f"  children[{idx}].AXValue: {val!r}")
        messages.append(row_data)
    t6 = time.time()
    out_path = os.path.join(UI_MESSAGE_EXPORT_DIR, "messages", f"mail_{bundle_id}.jsonl")
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, 'w') as f:
        for item in messages:
            mailbox_val = item.get('mailbox')
            if mailbox_val:
                # Match common date formats (e.g., 2024/06/13, 13:45 or 13 Jun 2024, 13:45 or 2024-06-13)
                date_pattern = re.compile(r"(\d{4}/\d{2}/\d{2}|\d{4}-\d{2}-\d{2}|\d{1,2} [A-Za-z]{3,9} \d{4}|\d{1,2}/\d{1,2}/\d{2,4})")
                if isinstance(mailbox_val, str) and date_pattern.search(mailbox_val):
                    item['date'] = mailbox_val
                    item.pop('mailbox', None)
            filtered = {k: item[k] for k in display_keys if k in item and item[k] is not None and (k != 'mailbox' or not (isinstance(item.get('mailbox'), str) and date_pattern.search(item.get('mailbox'))))}
            f.write(json.dumps(filtered, ensure_ascii=False) + '\n')
    t7 = time.time()
    print(f"[PERF] App focus: {t1-t0:.3f}s | Find table: {t2-t1:.3f}s | Get rows: {t3-t2:.3f}s | Select/output rows: {t4-t3:.3f}s | Extract: {t6-t5:.3f}s | Write: {t7-t6:.3f}s | Total: {t7-t0:.3f}s | Rows: {len(messages)}")
    sys.exit(0)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Extract Apple Mail table row data via accessibility API.")
    parser.add_argument('--row', '-r', type=int, default=None, help='Row index (1-based) to select/focus. If not set, selects the first row.')
    args = parser.parse_args()

    extract_first_n_rows_fields(n=UI_MAX_ROWS, row_index=args.row) 