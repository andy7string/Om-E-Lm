"""
ome/utils/builder/mail/mailMessageListWatch_controller.py

Mail Message List Watcher & HTTP Command Server for Apple Mail
=============================================================

Main Purpose:
- Watches Mail's window state (via win_com.apple.mail.jsonl and active_target_Bundle_ID.json) and triggers message list extraction when the main message viewer window is active.
- Provides an HTTP server for remote row selection commands (e.g., via curl or other automation tools).
- Ensures message list data is always up-to-date with the current Mail window context.

Key Features:
- File Watcher: Monitors window state files for changes and triggers extraction as needed.
- HTTP API: Accepts POST requests to select a specific row in the message list.
- Robust App State Handling: Detects Mail launch/quit and reacquires the app object as needed.
- Integration: Designed to work with winD_controller.py and the Om-E event-driven automation stack.
- CLI Usage: Can be run in watcher mode or as a one-off row extractor.

How It Works:
1. Watches for changes to Mail's window state and active bundle ID files.
2. When the main message viewer window becomes active, extracts the message list using accessibility APIs.
3. On HTTP POST to /select_row, selects the specified row and triggers extraction.
4. Handles Mail app launch/quit events and reacquires the app object as needed.

Command Line Usage:
-------------------
# Start the watcher and HTTP server:
python -m ome.utils.builder.mail.mailMessageListWatch_controller --watch

# Extract a specific row (one-off):
python -m ome.utils.builder.mail.mailMessageListWatch_controller --row 5

HTTP API Example:
-----------------
curl -X POST -H "Content-Type: application/json" -d '{"row": 5}' http://localhost:8765/select_row

Integration Notes:
------------------
- Expects winD_controller.py to be running and updating the window state files.
- Uses the same extraction logic as mailMessageList_controller.py for consistency.
- Can be extended to support additional commands or apps as needed.

Dependencies:
-------------
- watchdog: For file system event monitoring
- threading, http.server: For HTTP API
- ome: For accessibility and app automation

"""
import time
import json
import os
import argparse
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from ome.utils.builder.mail.mailMessageList_controller import extract_first_n_rows_fields
import ome
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

# File paths for window state and active bundle ID
MAIL_JSONL = 'ome/data/windows/win_com.apple.mail.jsonl'
ACTIVE_BUNDLE_JSON = 'ome/data/windows/active_target_Bundle_ID.json'
TARGET_WINDOW_REF_PREFIX = 'Mail.messageViewer'
MAIL_BUNDLE_ID = 'com.apple.mail'

class MailWindowWatcher(FileSystemEventHandler):
    """
    Watches Mail's window state and triggers message list extraction when appropriate.
    Handles Mail app launch/quit and reacquires app object as needed.
    """
    def __init__(self, mail_jsonl, active_bundle_json):
        self.mail_jsonl = os.path.abspath(mail_jsonl)
        self.active_bundle_json = os.path.abspath(active_bundle_json)
        self.last_window_ref = None
        self.last_window_title = None
        self.app_object = None
        self.mail_running = False
        self.initial_extracted = False
        print(f"[WATCHDOG] Watching {self.mail_jsonl} and {self.active_bundle_json}")
        self.check_mail_status(force=True)

    def check_mail_status(self, force=False):
        """
        Checks if Mail is running and updates app_object accordingly.
        Handles Mail launch/quit events.
        """
        try:
            with open(self.active_bundle_json, 'r', encoding='utf-8') as f:
                data = json.load(f)
            is_mail = data.get('active_bundle_id') == MAIL_BUNDLE_ID
            is_running = data.get('status') == 'running'
            if is_mail and is_running:
                if not self.mail_running or force or self.app_object is None:
                    print("[WATCHDOG] Mail is running, acquiring app object...")
                    self.app_object = ome.getAppRefByBundleId(MAIL_BUNDLE_ID)
                    self.initial_extracted = False  # Reset on new Mail launch
                self.mail_running = True
            else:
                if self.mail_running or force:
                    print("[WATCHDOG] Mail is not running or not active, clearing app object.")
                self.mail_running = False
                self.app_object = None
                self.initial_extracted = False  # Reset so next launch triggers extraction
        except Exception as e:
            print(f"[WATCHDOG] Error reading {self.active_bundle_json}: {e}")
            self.mail_running = False
            self.app_object = None
            self.initial_extracted = False

    def on_modified(self, event):
        """
        Handles file modification events for window state and active bundle ID files.
        Triggers extraction if the main message viewer window becomes active or changes.
        """
        event_path = os.path.abspath(event.src_path)
        if event_path == self.active_bundle_json:
            self.check_mail_status()
            return
        if event_path != self.mail_jsonl:
            return
        self.check_mail_status()
        if not self.mail_running or self.app_object is None:
            return
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
        # Only scan if window_ref starts with Mail.messageViewer
        if window_ref and window_ref.startswith(TARGET_WINDOW_REF_PREFIX):
            # First time extraction after Mail starts
            if not self.initial_extracted:
                print(f"[WATCHDOG] First extraction after Mail starts, extracting message list...")
                extract_first_n_rows_fields(row_index=1, app_object=self.app_object)
                self.initial_extracted = True
            # Only extract if window_title changes
            elif window_title != self.last_window_title:
                print(f"[WATCHDOG] window_title changed to '{window_title}', extracting message list...")
                extract_first_n_rows_fields(row_index=1, app_object=self.app_object)
        self.last_window_ref = window_ref
        self.last_window_title = window_title

def start_http_server(get_app_object_func, port=8765):
    """
    Starts a background HTTP server for row selection commands.
    get_app_object_func: function returning the current app_object (may be None if Mail not running)
    """
    class CommandHandler(BaseHTTPRequestHandler):
        def do_POST(self):
            if self.path == '/select_row':
                content_length = int(self.headers.get('Content-Length', 0))
                post_data = self.rfile.read(content_length)
                try:
                    data = json.loads(post_data)
                    row = data.get('row')
                    if row is not None:
                        app_object = get_app_object_func()
                        if app_object is not None:
                            print(f"[HTTP] Received select_row: {row}")
                            extract_first_n_rows_fields(row_index=row, app_object=app_object)
                            self.send_response(200)
                            self.end_headers()
                            self.wfile.write(b'OK')
                            return
                        else:
                            self.send_response(503)
                            self.end_headers()
                            self.wfile.write(b'Mail app not running')
                            return
                except Exception as e:
                    print(f"[HTTP] Error: {e}")
            self.send_response(400)
            self.end_headers()
            self.wfile.write(b'Bad Request')
        def log_message(self, format, *args):
            # Suppress default logging
            return
    def serve():
        server = HTTPServer(('localhost', port), CommandHandler)
        print(f"[HTTP] Command server running on http://localhost:{port}")
        server.serve_forever()
    thread = threading.Thread(target=serve, daemon=True)
    thread.start()
    return thread

def run_watcher():
    """
    Starts the file watcher and HTTP server for Mail message list monitoring.
    """
    event_handler = MailWindowWatcher(MAIL_JSONL, ACTIVE_BUNDLE_JSON)
    observer = Observer()
    observer.schedule(event_handler, path=os.path.dirname(MAIL_JSONL), recursive=False)
    observer.schedule(event_handler, path=os.path.dirname(ACTIVE_BUNDLE_JSON), recursive=False)
    observer.start()
    # Start HTTP server for row selection
    start_http_server(lambda: event_handler.app_object)
    print("[WATCHDOG] Mail message list watcher started.")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()

def main():
    """
    Command-line entry point. Supports --watch mode and one-off row extraction.
    """
    parser = argparse.ArgumentParser(description="Mail message list controller and watcher.")
    parser.add_argument('--watch', action='store_true', help='Run in event-driven watcher mode')
    parser.add_argument('--row', '-r', type=int, default=None, help='Row index (1-based) to select/focus. If not set, selects the first row.')
    args = parser.parse_args()

    if args.watch:
        run_watcher()
    else:
        extract_first_n_rows_fields(row_index=args.row)

if __name__ == '__main__':
    main() 