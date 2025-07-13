import os
import time
from datetime import datetime, timedelta

def search_attachment_file_by_minute(filename, msg_date, window_minutes=4, timeout_seconds=30):
    """
    Search for a file with the given name in Apple Mail data folders, returning the path
    whose modification time is closest to msg_date (within window_minutes).
    
    Args:
        filename: Name of the file to search for
        msg_date: Date string of the message
        window_minutes: Time window in minutes to search around the message date
        timeout_seconds: Maximum time to spend searching (default 30 seconds)
    """
    start_time = time.time()
    user_home = os.path.expanduser("~")
    mail_dirs = [
        os.path.join(user_home, "Library", "Mail"),
        os.path.join(user_home, "Library", "Containers", "com.apple.mail", "Data", "Library", "Mail Downloads"),
    ]
    msg_dt = None
    try:
        try:
            msg_dt = datetime.fromisoformat(msg_date)
        except Exception:
            msg_dt = datetime.strptime(msg_date, "%Y-%m-%d %H:%M:%S %z")
    except Exception:
        pass
    best_path = None
    min_diff = timedelta(minutes=window_minutes+1)
    
    for base_dir in mail_dirs:
        if not os.path.exists(base_dir):
            continue
            
        for root, dirs, files in os.walk(base_dir):
            # Check timeout
            if time.time() - start_time > timeout_seconds:
                print(f"[WARNING] Attachment search timed out after {timeout_seconds} seconds")
                return best_path
                
            for f in files:
                if f == filename:
                    path = os.path.join(root, f)
                    if msg_dt:
                        try:
                            mod_time = datetime.fromtimestamp(os.path.getmtime(path)).astimezone(msg_dt.tzinfo)
                            diff = abs((mod_time - msg_dt).total_seconds())
                            if diff <= window_minutes * 60 and diff < min_diff.total_seconds():
                                best_path = path
                                min_diff = timedelta(seconds=diff)
                        except Exception:
                            continue
    return best_path 