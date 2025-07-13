import os
from pathlib import Path
from dotenv import load_dotenv
import ome.utils.env.env as env

# ===========================
# 🧪 Load .env manually
# ===========================
def load_env_file():
    env_path = Path(__file__).parent / ".env"
    if env_path.exists():
        with open(env_path, "r") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                if "=" in line:
                    key, value = line.split("=", 1)
                    os.environ[key.strip()] = value.strip()

load_env_file()

# === DELAY CONFIGURATIONS ===
# General delay between actions
ACTION_DELAY = float(os.getenv("ACTION_DELAY", "0.5"))

# Window and UI related delays
WINDOW_WAIT_TIMEOUT = float(os.getenv("WINDOW_WAIT_TIMEOUT", "10.0"))
MENU_WAIT_DELAY = float(os.getenv("MENU_WAIT_DELAY", "0.3"))
APP_LAUNCH_DELAY = float(os.getenv("APP_LAUNCH_DELAY", "2.0"))
WINDOW_MAXIMIZE_DELAY = float(os.getenv("WINDOW_MAXIMIZE_DELAY", "1.0"))
MENU_ITEM_CLICK_DELAY = float(os.getenv("MENU_ITEM_CLICK_DELAY", "0.3"))

# Retry related delays
RETRY_DELAY = float(os.getenv("RETRY_DELAY", "0.2"))
MAX_RETRIES = int(os.getenv("MAX_RETRIES", "3"))

# System related delays
SYSTEM_HANDLER_DELAY = float(os.getenv("SYSTEM_HANDLER_DELAY", "5.0"))

# === MENU EXPORT DIRECTORY ===
MENU_EXPORT_DIR = os.getenv("MENU_EXPORT_DIR", str(Path.home() / "menu_exports"))

def get_env(key, default=None):
    """Get an environment variable from .env or the system."""
    return os.getenv(key, default)

# ===========================
# ✅ TESTING FUNCTIONS
# ===========================

def verify_env():
    print("🔍 Verifying delay configurations\n")

    def show(label, value):
        print(f"{label:<30} = {value}")

    show("ACTION_DELAY", ACTION_DELAY)
    show("WINDOW_WAIT_TIMEOUT", WINDOW_WAIT_TIMEOUT)
    show("MENU_WAIT_DELAY", MENU_WAIT_DELAY)
    show("APP_LAUNCH_DELAY", APP_LAUNCH_DELAY)
    show("WINDOW_MAXIMIZE_DELAY", WINDOW_MAXIMIZE_DELAY)
    show("MENU_ITEM_CLICK_DELAY", MENU_ITEM_CLICK_DELAY)
    show("RETRY_DELAY", RETRY_DELAY)
    show("MAX_RETRIES", MAX_RETRIES)
    show("SYSTEM_HANDLER_DELAY", SYSTEM_HANDLER_DELAY)
    show("MENU_EXPORT_DIR", MENU_EXPORT_DIR)

    print("\n✅ If all values look right, delay configurations loaded successfully.")

# ===========================
# 🔗 Export helpers to module
# ===========================

def _export_test_helpers():
    globals()["verify_env"] = verify_env

_export_test_helpers()

if __name__ == "__main__":
    verify_env() 