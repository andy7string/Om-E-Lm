import os
import shutil
from pathlib import Path
from collections import deque
from datetime import datetime

# Load env config or use defaults
MAX_RECENT_SCREENSHOTS = int(os.getenv("MAX_RECENT_SCREENSHOTS", 10))
SCREENSHOT_DIR = Path(os.getenv("SCREENSHOT_DIR", "ome/data/screenshots")).resolve()
ARCHIVE_DIR = Path(os.getenv("SCREENSHOT_ARCHIVE_DIR", "ome/data/archive/screenshots")).resolve()

# Ensure directories exist
SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)
ARCHIVE_DIR.mkdir(parents=True, exist_ok=True)

# In-memory tracker
recent_screenshots = deque(maxlen=MAX_RECENT_SCREENSHOTS)


# 🧠 Track new screenshot and auto-archive old ones
def track_screenshot(filepath):
    filepath = Path(filepath).resolve()

    if filepath.exists():
        recent_screenshots.append(filepath)

        # Archive if over capacity (deque handles size)
        while len(recent_screenshots) > MAX_RECENT_SCREENSHOTS:
            to_archive = recent_screenshots.popleft()
            archive_path = ARCHIVE_DIR / to_archive.name
            shutil.move(str(to_archive), str(archive_path))
            print(f"[📦 Archived screenshot] {archive_path}")


# 📥 Save a screenshot from desktop or source into the known directory
def import_screenshot_from_desktop():
    desktop = Path("~/Desktop").expanduser()
    screenshots = sorted(desktop.glob("Screen Shot *.png"), key=os.path.getmtime, reverse=True)

    if not screenshots:
        return None

    latest = screenshots[0]
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    target_path = SCREENSHOT_DIR / f"screenshot_{timestamp}.png"
    shutil.move(str(latest), str(target_path))
    track_screenshot(target_path)
    print(f"[📸 Imported screenshot] {target_path}")
    return str(target_path)


# 📚 Get list of tracked screenshots (paths)
def get_recent_screenshots():
    return list(recent_screenshots)


# 📄 Get the latest screenshot path (or None)
def get_latest_screenshot():
    return recent_screenshots[-1] if recent_screenshots else None


# 🧼 Reset screenshot tracker (clear memory only)
def reset_tracker():
    recent_screenshots.clear()
