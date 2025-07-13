import json
from pathlib import Path
from datetime import datetime, timezone
from env import TREE_LOGS_DIR, TREE_LOG_FILE_PREFIX

LOGS_DIR = Path(TREE_LOGS_DIR)

# ===================================================
# 📁 Prepare log directory and file
# ===================================================

# Ensure logs directory exists
LOGS_DIR.mkdir(parents=True, exist_ok=True)

# Generate a timestamped log file name
timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
LOG_FILE = LOGS_DIR / f"{TREE_LOG_FILE_PREFIX}{timestamp}.jsonl"

# ===================================================
# 🧠 Unified Event Logger
# ===================================================

def log_event(level: str, source: str, message: str, payload: dict = None):
    """
    Logs a structured event to both the terminal and a JSONL log file.

    Args:
        level (str): Log level (e.g., INFO, DEBUG, ERROR, WARN)
        source (str): Subsystem or component name
        message (str): Message describing the event
        payload (dict, optional): Optional structured context
    """
    entry = {
        "time": datetime.now(timezone.utc).isoformat(),
        "level": level.upper(),
        "source": source,
        "message": message,
        "payload": payload or {}
    }

    # Output to terminal
    print(f"[{entry['level']}] {entry['source']}: {entry['message']}")

    # Write to JSONL log file
    try:
        with open(LOG_FILE, "a") as f:
            f.write(json.dumps(entry) + "\n")
    except Exception as e:
        print(f"[ERROR] logger: Failed to write log file: {e}")
