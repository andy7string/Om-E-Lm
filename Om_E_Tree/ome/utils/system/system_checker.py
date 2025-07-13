from pathlib import Path
from env import TREE_APPLICATION_PATH as APPLICATION_PATH

# ===================================================
# 🧠 List installed macOS apps
# ===================================================

def list_installed_apps() -> list:
    """
    Scans the configured APPLICATION_PATH for .app bundles
    and returns a sorted list of installed application names.

    Returns:
        list[str]: Alphabetically sorted app names (without .app extension)

    Raises:
        FileNotFoundError: If the configured application path does not exist.
    """
    if not APPLICATION_PATH.exists():
        raise FileNotFoundError(f"❌ Application path does not exist: {APPLICATION_PATH}")

    apps = [
        item.stem
        for item in APPLICATION_PATH.iterdir()
        if item.suffix == ".app"
    ]
    return sorted(apps)
