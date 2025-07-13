import time
import json
import os
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from ome.utils.builder.mail.mailMessageList_controller import extract_first_n_rows_fields
import ome

MAIL_JSONL = 'ome/data/windows/win_com.apple.mail.jsonl'
TARGET_WINDOW_REF_PREFIX = 'Mail.messageViewer'

class MailWindowWatcher(FileSystemEventHandler):
    def __init__(self, file_path, app_object):
        self.file_path = os.path.abspath(file_path)
        self.last_window_ref = None
        self.last_window_title = None
        self.app_object = app_object
        print(f"[WATCHDOG] Watching {self.file_path}")

    def on_modified(self, event):
        if os.path.abspath(event.src_path) != self.file_path:
            return
        try:
            with open(self.file_path, 'r', encoding='utf-8') as f:
                state = json.load(f)
            active_target = state.get('active_target', {})
            window_ref = active_target.get('window_ref')
            window_title = active_target.get('window_title')
        except Exception as e:
            print(f"[WATCHDOG] Error reading {self.file_path}: {e}")
            window_ref = None
            window_title = None

        # Only trigger if window_ref starts with the prefix and window_title changed
        if window_ref and window_ref.startswith(TARGET_WINDOW_REF_PREFIX):
            if window_title != self.last_window_title:
                print(f"[WATCHDOG] window_title changed to '{window_title}', extracting message list...")
                extract_first_n_rows_fields(row_index=1, app_object=self.app_object)
        self.last_window_ref = window_ref
        self.last_window_title = window_title

def main():
    app = ome.getAppRefByBundleId("com.apple.mail")
    event_handler = MailWindowWatcher(MAIL_JSONL, app)
    observer = Observer()
    observer.schedule(event_handler, path=os.path.dirname(MAIL_JSONL), recursive=False)
    observer.start()
    print("[WATCHDOG] Mail message list watcher started.")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()

if __name__ == '__main__':
    main() 