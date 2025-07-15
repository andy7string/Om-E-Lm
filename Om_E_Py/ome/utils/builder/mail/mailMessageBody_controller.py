"""
Mail Message Body Controller

This script extracts and saves the body content of Apple Mail messages using PyXA and the macOS accessibility API.
It is designed to help you programmatically extract message bodies, attachments, and metadata from the currently
focused or selected Apple Mail message, and save them in structured formats for further processing.

====================
PURPOSE
====================
- Extracts the body content of the currently focused/selected Apple Mail message.
- Captures message metadata (subject, sender, recipients, date, attachments).
- Saves extracted data in both JSON and JSONL formats for flexibility.
- Integrates with the message list controller for consistent message key generation.
- Launches background attachment finder for enhanced file discovery.

====================
KEY FEATURES
====================
- PyXA Integration: Uses PyXA for direct Apple Mail API access and message content extraction.
- Accessibility API: Leverages macOS accessibility features for robust message selection.
- Message Key Consistency: Uses the same message key system as the message list controller.
- Dual Output Formats: Saves data in both human-readable JSON and efficient JSONL formats.
- Attachment Processing: Automatically launches background attachment finder for file discovery.
- Row Data Integration: Can accept row data from message list extraction for consistent keys.
- CLI Interface: Provides command-line interface for standalone operation or subprocess calls.

====================
HOW IT WORKS
====================
1. App Focus: Ensures Apple Mail is focused and accessible using the accessibility API.
2. PyXA Initialization: Initializes PyXA application reference for Apple Mail.
3. Message Selection: Gets the currently selected message or falls back to the first message in the frontmost mailbox.
4. Data Extraction: Extracts message metadata, body content, and attachment information using PyXA.
5. Message Key Generation: Uses provided row data or generates a consistent message key.
6. File Output: Saves extracted data to JSON and JSONL files in the configured output directory.
7. Background Processing: Launches attachment finder as a non-blocking subprocess.

====================
PYTHON API USAGE EXAMPLES
====================
from ome.utils.builder.mail.mailMessageBody_controller import main

# Extract body for the currently selected message
main()

# Extract with specific row data (for integration with message list controller)
row_data = {
    'message_key': '20250617_1726_Andr_Sent',
    'sender': 'Andrew Orsmond',
    'subject': 'Test Message',
    'date': '2025/06/17, 17:26',
    'mailbox': 'Sent',
    'row_index': 3
}

# This would be called via subprocess with --row-data argument

====================
COMMAND LINE USAGE EXAMPLES
====================
# Extract body for the currently selected message
python -m ome.utils.builder.mail.mailMessageBody_controller

# Extract with specific row data (for integration)
python -m ome.utils.builder.mail.mailMessageBody_controller --row-data '{"message_key":"20250617_1726_Andr_Sent","sender":"Andrew Orsmond"}'

# Specify custom output directory
python -m ome.utils.builder.mail.mailMessageBody_controller --out /path/to/output/dir

# Use specific row index for key generation
python -m ome.utils.builder.mail.mailMessageBody_controller --row 5

====================
OUTPUT FORMATS
====================
JSON Format (mail_<message_key>.json):
{
  "message_key": "20250617_1726_Andr_Sent",
  "subject": "Test Message",
  "sender": "Andrew Orsmond <andrew@example.com>",
  "date_sent": "2025-06-17 17:26:00 +0000",
  "recipients": ["recipient@example.com"],
  "body_lines": ["Hi there,", "This is the message body."],
  "attachments": [
    {"name": "document.pdf", "extension": ".pdf", "best_guess_path": null}
  ],
  "mailbox": "Sent",
  "row_index": 3
}

JSONL Format (mail_<message_key>.jsonl):
{"message_key": "20250617_1726_Andr_Sent", "subject": "Test Message", ...}

====================
INTEGRATION WITH MESSAGE LIST CONTROLLER
====================
This controller is designed to work seamlessly with mailMessageList_controller.py:

1. Message list controller extracts message list and focuses on a specific row
2. Message list controller calls this body controller as a subprocess
3. Body controller receives row data via --row-data argument
4. Body controller uses the same message key for consistent file naming
5. Both controllers maintain data consistency and avoid duplication

====================
WHEN TO USE
====================
- When you need to extract the full body content of Apple Mail messages.
- When you want to capture message metadata and attachments programmatically.
- When you're building automated email processing workflows.
- When you need structured data for email analysis or archiving.
- When integrating with the message list controller for complete message extraction.

====================
DEPENDENCIES
====================
- PyXA: For Apple Mail API access and message content extraction
- macOS Accessibility API: For app focusing and message selection
- Apple Mail: Must be installed and accessible
- find_attachments.py: For background attachment processing (optional)

====================
PERFORMANCE CONSIDERATIONS
====================
- Message selection: ~0.1-0.3 seconds
- Data extraction: ~0.1-0.5 seconds (varies with message size)
- File writing: ~0.01-0.05 seconds
- Total execution: ~0.5-1.0 seconds for typical messages
- Background attachment finder runs independently

====================
ERROR HANDLING
====================
- Graceful handling of missing or invalid message selection
- Fallback mechanisms for message key generation
- Safe attribute access with error recovery
- Comprehensive logging for debugging
- Non-blocking subprocess management

# [INFO] This script is now intended to be called in-process from the message list controller for single-message extraction.
# The main() function remains for standalone use, but subprocess usage is discouraged in favor of direct function calls.

"""

import sys
import argparse
import time
import json
import os
import getpass
from datetime import datetime, timedelta
import glob
import subprocess
import hashlib

# Add the project root to the Python path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

import ome
from Om_E_Py.ome.utils.builder.app.app_focus import ensure_app_focus
from env import UI_MESSAGE_EXPORT_DIR

try:
    import PyXA
except ImportError:
    print("mac-pyxa is not installed. Please install it with 'pip install mac-pyxa'.")
    sys.exit(1)

def safe_getattr(obj, attr):
    """
    Safely gets an attribute from an object, returning None if not present or on error.
    
    Args:
        obj: The object to get the attribute from
        attr (str): The attribute name to retrieve
        
    Returns:
        The attribute value or None if not found or on error
    """
    try:
        return getattr(obj, attr, None)
    except Exception:
        return None

def extract_omeclick(element):
    """
    Given an accessibility element, returns the center point [x, y] for clicking, or None if not available.
    
    Args:
        element: Accessibility element with AXPosition and AXSize attributes
        
    Returns:
        list: [x, y] coordinates for clicking, or None if not available
    """
    try:
        pos = safe_getattr(element, 'AXPosition')
        size = safe_getattr(element, 'AXSize')
        if pos and size and isinstance(pos, (list, tuple)) and isinstance(size, (list, tuple)):
            return [float(pos[0]) + float(size[0])/2, float(pos[1]) + float(size[1])/2]
    except Exception:
        pass
    return None

def get_ax_path(element):
    """
    Builds a hierarchical path string representing the element's position in the accessibility tree.
    
    Args:
        element: Accessibility element to trace
        
    Returns:
        str: Hierarchical path string (e.g., "AXWindow:Main > AXGroup:Content > AXStaticText:Label")
    """
    path = []
    current = element
    while current is not None:
        role = safe_getattr(current, 'AXRole')
        title = safe_getattr(current, 'AXTitle')
        value = safe_getattr(current, 'AXValue')
        label = title or value or ''
        path.append(f"{role}:{label}")
        current = safe_getattr(current, 'AXParent')
    return ' > '.join(reversed(path))

def find_label_for_field(field, sibling_static_texts):
    """
    Attempts to find an appropriate label for a form field by checking multiple sources.
    
    Args:
        field: The form field element to find a label for
        sibling_static_texts: List of static text elements that might be labels
        
    Returns:
        str: The found label text or None if no label is found
        
    Strategy:
        1. Check for label attributes on the field itself
        2. Check nearest preceding static text sibling
        3. Check parent for label-like attributes
    """
    # 1. Check for label attributes on the field itself
    for attr in ('AXTitle', 'AXDescription', 'AXHelp', 'AXPlaceholderValue'):
        label = safe_getattr(field, attr)
        if label:
            return label
    # 2. Check nearest preceding static text sibling
    if sibling_static_texts:
        return safe_getattr(sibling_static_texts[-1], 'AXValue')
    # 3. Check parent for label-like attributes
    parent = safe_getattr(field, 'AXParent')
    if parent:
        for attr in ('AXTitle', 'AXDescription', 'AXHelp'):
            label = safe_getattr(parent, attr)
            if label:
                return label
    return None

def crawl_and_pair(element, bundle_id=None, path=None, results=None, args=None):
    """
    Recursively crawls the accessibility tree to extract UI elements and their properties.
    
    Args:
        element: Root accessibility element to start crawling from
        bundle_id (str, optional): Bundle ID of the application for context-specific processing
        path (list, optional): Current path in the accessibility tree
        results (list, optional): List to accumulate results
        args (object, optional): Additional arguments for processing
        
    Returns:
        list: List of extracted UI element data
        
    Notes:
        - Skips certain structural roles (AXTable, AXList, AXRow, AXFinderRow)
        - Special handling for AXWebArea to extract mail body content
        - Processes text fields, search fields, and other interactive elements
    """
    if results is None:
        results = []
    role = safe_getattr(element, 'AXRole')
    SKIP_ROLES = {'AXTable', 'AXList', 'AXRow', 'AXFinderRow'}
    if role in SKIP_ROLES:
        return results  # Skip these containers and their children
    title = safe_getattr(element, 'AXTitle')
    value = safe_getattr(element, 'AXValue')
    # If this is a parent with children, process children as siblings
    children = safe_getattr(element, 'AXChildren') or []
    if children:
        sibling_static_texts = []
        for idx, child in enumerate(children):
            child_role = safe_getattr(child, 'AXRole')
            child_value = safe_getattr(child, 'AXValue')
            child_title = safe_getattr(child, 'AXTitle')
            if child_role == 'AXStaticText':
                sibling_static_texts.append(child)
            elif child_role in ('AXTextField', 'AXSearchField'):
                if bundle_id == "com.apple.finder" and child_role in ("AXTextField", "AXSearchField"):
                    label = "Search Field"
                else:
                    label = find_label_for_field(child, sibling_static_texts)
                omeClick = extract_omeclick(child)
                entry = {
                    'AXRole': child_role,
                    'AXTitle': label,
                    'AXDescription': 'Text Input Field',
                    'value': child_value,
                    'omeClick': omeClick
                }
                results.append(entry)
            elif child_role in ('AXWebArea', 'AXTextArea'):
                if child_role == 'AXWebArea':
                    # Improved extraction: avoid visiting the same node twice
                    def extract_structured_mail_body(element, visited=None):
                        """
                        Extracts structured mail body content while avoiding circular references.
                        
                        Args:
                            element: Accessibility element to extract from
                            visited (set, optional): Set of already visited element IDs
                            
                        Returns:
                            list: Lines of extracted text content
                        """
                        if visited is None:
                            visited = set()
                        if id(element) in visited:
                            return []
                        visited.add(id(element))
                        role = safe_getattr(element, 'AXRole')
                        children = safe_getattr(element, 'AXChildren') or []
                        lines = []
                        if role == 'AXStaticText':
                            value = safe_getattr(element, 'AXValue')
                            if value and value.strip() and value.strip() != '\xa0':
                                lines.append(value.strip())
                        elif role in ('AXTable', 'AXRow', 'AXCell', 'AXGroup', 'AXLink'):
                            for c in children:
                                lines.extend(extract_structured_mail_body(c, visited))
                        else:
                            for c in children:
                                lines.extend(extract_structured_mail_body(c, visited))
                        return lines
                    mail_lines = extract_structured_mail_body(child)
                    mail_body = '\n'.join(mail_lines)
                    print(f"\n[MAIL BODY EXTRACTED - NO REVISIT]\n{mail_body}\n{'='*40}\n")
                    results.append({'AXRole': 'AXWebArea', 'mail_body': mail_body})
                else:
                    omeClick = extract_omeclick(child)
                    entry = {
                        'AXRole': child_role,
                        'AXTitle': 'Body',
                        'AXDescription': 'Text Input Field',
                        'value': child_value,
                        'omeClick': omeClick
                    }
                    results.append(entry)
            # Recurse into each child
            crawl_and_pair(child, bundle_id=bundle_id, results=results, args=args)
    return results

def clean_body_lines(body_lines):
    """
    Removes empty lines and non-breaking spaces from body text lines.
    
    Args:
        body_lines (list): List of text lines to clean
        
    Returns:
        list: Cleaned list of text lines with empty lines removed
    """
    cleaned = []
    for line in body_lines:
        # Remove lines that are only whitespace or non-breaking spaces
        if line.strip() == "" or line.strip().replace('\u00a0', '') == "":
            continue
        cleaned.append(line)
    return cleaned

def make_message_key(mailbox, row_index, sender, date, subject):
    """
    Creates a unique message key using a hash of the message metadata.
    
    Args:
        mailbox (str): Mailbox name
        row_index (int): Row index in the message list
        sender (str): Sender name/email
        date (str): Message date
        subject (str): Message subject
        
    Returns:
        str: 12-character hexadecimal hash key
        
    Note:
        This function is kept for backward compatibility but is superseded by
        the unique ID system in the message list controller.
    """
    key_str = f"{mailbox}|{row_index}|{sender}|{date}|{subject}"
    # Use first 12 characters of SHA1 for shorter, readable keys
    return hashlib.sha1(key_str.encode('utf-8')).hexdigest()[:12]

def main():
    """
    Main function that orchestrates the entire message body extraction process.
    
    Process Flow:
    1. Parse command line arguments
    2. Focus Apple Mail application
    3. Initialize PyXA for Apple Mail access
    4. Select the target message
    5. Extract message data and metadata
    6. Generate or use message key
    7. Save data to JSON and JSONL files
    8. Launch background attachment finder
    
    Command Line Arguments:
        --out: Custom output directory (optional)
        --row: Row index for key generation (default: 1)
        --row-data: JSON string of row data from message list extraction
    """
    parser = argparse.ArgumentParser(description="Extract info from the focused/selected Apple Mail message and output as JSONL.")
    parser.add_argument('--out', type=str, default=None, help='Output JSONL file for message info (optional)')
    parser.add_argument('--row', type=int, default=1, help='Row index (1-based) to use for key (default: 1)')
    parser.add_argument('--row-data', type=str, default=None, help='JSON string of row data from list extraction')
    args = parser.parse_args()

    total_start = time.time()

    # 1. Ensure Apple Mail is focused
    # This step ensures the Apple Mail application is active and accessible
    # for both accessibility API and PyXA operations
    t0 = time.time()
    focus_result = ensure_app_focus("com.apple.mail", fullscreen=False)
    t1 = time.time()
    print(f"[TIMER] Focus Apple Mail: {t1-t0:.3f} sec")
    if not (isinstance(focus_result, dict) and focus_result.get('status') == 'success'):
        print(f"Could not focus app: {focus_result}")
        sys.exit(1)
    time.sleep(0.5)  # Allow time for app to fully activate

    # 2. PyXA initialization
    # Initialize PyXA application reference for direct Apple Mail API access
    # This provides access to message content, metadata, and attachments
    t2 = time.time()
    app = PyXA.Application("Mail")
    t3 = time.time()
    print(f"[TIMER] PyXA init: {t3-t2:.3f} sec")

    # 3. Message selection
    # Get the currently selected message or fall back to the first message
    # in the frontmost mailbox if no message is explicitly selected
    t4 = time.time()
    selected_messages = app.selection
    msg = None
    if selected_messages and len(selected_messages) > 0:
        msg = selected_messages[0]  # Use the first selected message
    else:
        # Fallback: try to get the first message in the frontmost mailbox
        try:
            viewers = app.message_viewers()
            if viewers and len(viewers) > 0:
                mailbox = viewers[0].selected_mailbox
                messages = mailbox.messages()
                if messages and len(messages) > 0:
                    msg = messages[0]
        except Exception:
            pass
    t5 = time.time()
    print(f"[TIMER] Message selection: {t5-t4:.3f} sec")
    if msg is None:
        print("No message is selected or focused in Apple Mail.")
        sys.exit(0)

    # 4. Data extraction
    # Extract all relevant message data including metadata, body content,
    # and attachment information using PyXA's comprehensive API
    t6 = time.time()
    
    # Extract recipients (To field)
    recipients = []
    try:
        recipients = [str(r) for r in getattr(msg, 'to_recipients', [])]
    except Exception:
        pass
    
    # Extract date sent
    date_sent = None
    try:
        date_sent = str(msg.date_sent)
    except Exception:
        pass
    
    # Extract mailbox information
    mailbox = None
    try:
        mailbox = str(msg.mailbox)
    except Exception:
        pass
    
    # Extract and clean body content
    body = str(msg.content)
    body_lines = body.splitlines()
    body_lines = clean_body_lines(body_lines)
    
    # Extract attachment information
    attachments = []
    for att in msg.mail_attachments():
        name = str(att.name)
        ext = os.path.splitext(name)[1] if '.' in name else ''
        attachments.append({
            'name': name,
            'extension': ext,
            'best_guess_path': None  # Will be populated by attachment finder
        })
    t7 = time.time()
    print(f"[TIMER] Data extraction: {t7-t6:.3f} sec")

    # 5. Message key generation
    # Use provided row data from message list extraction if available,
    # otherwise generate a key from PyXA data for consistency
    if args.row_data:
        try:
            row_data = json.loads(args.row_data)
            message_key = row_data.get('message_key')
            if not message_key:
                # Fallback to generating from row data
                message_key = make_message_key(
                    row_data.get('mailbox', ''),
                    row_data.get('row_index', args.row),
                    row_data.get('sender', ''),
                    row_data.get('date', ''),
                    row_data.get('subject', '')
                )
        except Exception as e:
            print(f"[WARNING] Could not parse row data: {e}")
            message_key = make_message_key(
                mailbox or '',
                args.row,
                str(msg.sender) or '',
                date_sent or '',
                str(msg.subject) or ''
            )
    else:
        # Generate message_key from PyXA data (fallback)
        message_key = make_message_key(
            mailbox or '',
            args.row,
            str(msg.sender) or '',
            date_sent or '',
            str(msg.subject) or ''
        )

    # 6. Prepare output data structure
    # Create a comprehensive data structure containing all extracted information
    entry = {
        'message_key': message_key,
        'subject': str(msg.subject),
        'sender': str(msg.sender),
        'date_sent': date_sent,
        'recipients': recipients,
        'body_lines': body_lines,
        'attachments': attachments,
        'mailbox': mailbox,
        'row_index': args.row
    }
    
    # 7. Output as pretty JSON and JSONL
    # Save the extracted data in both human-readable JSON format
    # and efficient JSONL format for different use cases
    t9 = time.time()
    if args.out and os.path.isdir(args.out):
        output_dir = args.out
    elif args.out:
        output_dir = os.path.dirname(args.out)
    else:
        output_dir = UI_MESSAGE_EXPORT_DIR
    
    if not output_dir:
        output_dir = UI_MESSAGE_EXPORT_DIR

    os.makedirs(output_dir, exist_ok=True)

    filename = f"mail_{message_key}.json"
    out_file = os.path.join(output_dir, filename)
    jsonl_out = os.path.splitext(out_file)[0] + '.jsonl'

    # Write JSON format (human-readable)
    with open(out_file, 'w', encoding='utf-8') as f:
        json.dump(entry, f, ensure_ascii=False, indent=2)
    
    # Write JSONL format (efficient for processing)
    with open(jsonl_out, 'w', encoding='utf-8') as f:
        f.write(json.dumps(entry, ensure_ascii=False) + '\n')
    
    print(f"[INFO] Wrote message to {out_file}")
    print(f"[INFO] Wrote message to {jsonl_out}")

    # 8. Start attachment finder as non-blocking subprocess
    # Launch the attachment finder in the background to search for
    # attachment files on the filesystem and update the JSON file
    print(f"[INFO] Starting attachment finder in background...")
    subprocess.Popen([
        sys.executable,
        "find_attachments.py",
        "--in", out_file,
        "--timeout", "60"  # 60 second timeout
    ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    
    print(f"[INFO] Attachment finder started in background")
    print(f"[INFO] Attachment search will update {out_file} when complete")
    print(f"[INFO] Body extraction complete - all processes running independently")

    t10 = time.time()
    print(f"[TIMER] Output writing: {t10-t9:.3f} sec")

    total_elapsed = time.time() - total_start
    print(f"[TIMER] TOTAL: {total_elapsed:.3f} sec")
    print(f"[SUCCESS] Message body extracted and background processes started")

if __name__ == "__main__":
    main() 