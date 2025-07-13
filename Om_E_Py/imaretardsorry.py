import time
import json
import os
import threading
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from http.server import BaseHTTPRequestHandler, HTTPServer

from ome.utils.builder.mail.mailMessageList_controller import extract_first_n_rows_fields
import ome

MAIL_JSONL = 'ome/data/windows/win_com.apple.mail.jsonl'
ACTIVE_BUNDLE_JSON = 'ome/data/windows/active_target_Bundle_ID.json'
TARGET_WINDOW_REF_PREFIX = 'Mail.messageViewer'
MAIL_BUNDLE_ID = 'com.apple.mail'

class MailWindowWatcher(FileSystemEventHandler):
    def __init__(self, mail_jsonl, active_bundle_json):
        self.mail_jsonl = os.path.abspath(mail_jsonl)
        self.active_bundle_json = os.path.abspath(active_bundle_json)
        self.last_window_ref = None
        self.last_window_title = None
        self.app_object = None
        self.mail_running = False
        self.initial_extracted = False
        self.selected_row_index = 1  # Default row
        self.selection_requested = False  # Flag for HTTP-triggered selection
        print(f"[WATCHDOG] Watching {self.mail_jsonl} and {self.active_bundle_json}")
        self.check_mail_status(force=True)

    def check_mail_status(self, force=False):
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
            if not self.initial_extracted:
                print(f"[WATCHDOG] First extraction after Mail starts, extracting message list...")
                extract_first_n_rows_fields(row_index=self.selected_row_index, app_object=self.app_object)
                self.initial_extracted = True
            elif window_title != self.last_window_title:
                print(f"[WATCHDOG] window_title changed to '{window_title}', extracting message list...")
                extract_first_n_rows_fields(row_index=self.selected_row_index, app_object=self.app_object)
        self.last_window_ref = window_ref
        self.last_window_title = window_title

def start_http_server(get_watcher_func, port=8765):
    class CommandHandler(BaseHTTPRequestHandler):
        def do_POST(self):
            if self.path == '/select_row':
                content_length = int(self.headers.get('Content-Length', 0))
                post_data = self.rfile.read(content_length)
                try:
                    data = json.loads(post_data)
                    row = data.get('row')
                    if row is not None:
                        watcher = get_watcher_func()
                        watcher.selected_row_index = row
                        watcher.selection_requested = True  # Set the flag!
                        print(f"[HTTP] Updated selected_row_index to: {row}")
                        self.send_response(200)
                        self.end_headers()
                        self.wfile.write(b'OK')
                        return
                except Exception as e:
                    print(f"[HTTP] Error: {e}")
            self.send_response(400)
            self.end_headers()
            self.wfile.write(b'Bad Request')
        def log_message(self, format, *args):
            return
    def serve():
        server = HTTPServer(('localhost', port), CommandHandler)
        print(f"[HTTP] Command server running on http://localhost:{port}")
        server.serve_forever()
    thread = threading.Thread(target=serve, daemon=True)
    thread.start()
    return thread

def run_watcher():
    event_handler = MailWindowWatcher(MAIL_JSONL, ACTIVE_BUNDLE_JSON)
    observer = Observer()
    observer.schedule(event_handler, path=os.path.dirname(MAIL_JSONL), recursive=False)
    observer.schedule(event_handler, path=os.path.dirname(ACTIVE_BUNDLE_JSON), recursive=False)
    observer.start()
    start_http_server(lambda: event_handler)
    print("[WATCHDOG] Mail message list watcher started.")
    try:
        while True:
            # Check if a selection was requested via HTTP
            if event_handler.selection_requested and event_handler.mail_running and event_handler.app_object is not None:
                print(f"[WATCHDOG] HTTP row selection requested, extracting row {event_handler.selected_row_index}...")
                extract_first_n_rows_fields(row_index=event_handler.selected_row_index, app_object=event_handler.app_object)
                event_handler.selection_requested = False
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()

if __name__ == '__main__':
    run_watcher() 