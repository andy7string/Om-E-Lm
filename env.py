import os
from pathlib import Path
from dotenv import load_dotenv

# Load the root .env file
load_dotenv()

# Define the absolute project root
PROJECT_ROOT = Path(__file__).resolve().parent

# === OM-E Core (OM_E_LM) ===
OME_OPENAI_API_KEY = os.getenv("OME_OPENAI_API_KEY")
OME_ACTION_RETRIES = int(os.getenv("OME_ACTION_RETRIES", 2))
OME_ACTION_RETRY_DELAY = float(os.getenv("OME_ACTION_RETRY_DELAY", 1.0))
OME_LOG_LEVEL = os.getenv("OME_LOG_LEVEL", "INFO")
OME_LOG_FILE_PREFIX = os.getenv("OME_LOG_FILE_PREFIX", "ome_log_")
OME_PLATFORM = os.getenv("OME_PLATFORM", "mac")
OME_APPLICATION_PATH = Path(os.getenv("OME_APPLICATION_PATH", "/Applications"))
OME_APP_LIST_PATH = os.getenv("OME_APP_LIST_PATH", PROJECT_ROOT / "OM_E_LM/ome/data/app_list.json")
OME_SYSTEM_HANDLER_DELAY = float(os.getenv("OME_SYSTEM_HANDLER_DELAY", 2.0))
OME_TREE_PATH = os.getenv("OME_TREE_PATH", PROJECT_ROOT / "OM_E_LM/ome/data/tree/execution_tree.json")
OME_LOGS_DIR = os.getenv("OME_LOGS_DIR", PROJECT_ROOT / "OM_E_LM/ome/data/logs")
OME_ARCHIVE_DIR = os.getenv("OME_ARCHIVE_DIR", PROJECT_ROOT / "OM_E_LM/ome/data/archive")
OME_TREE_ARCHIVE_DIR = os.getenv("OME_TREE_ARCHIVE_DIR", PROJECT_ROOT / "OM_E_LM/ome/data/archive")
OME_SCHEMA_DIR = os.getenv("OME_SCHEMA_DIR", PROJECT_ROOT / "OM_E_LM/ome/library/structures")
OME_SCREENSHOT_DIR = os.getenv("OME_SCREENSHOT_DIR", PROJECT_ROOT / "OM_E_LM/ome/data/screenshots")
OME_TEMPLATE_DIR = os.getenv("OME_TEMPLATE_DIR", PROJECT_ROOT / "OM_E_LM/ome/data/opencvsearchdb/templates")
OME_TEMPLATE_INDEX = os.getenv("OME_TEMPLATE_INDEX", PROJECT_ROOT / "OM_E_LM/ome/data/opencvsearchdb/index.json")
OME_ACTIONS_DIR = os.getenv("OME_ACTIONS_DIR", PROJECT_ROOT / "OM_E_LM/ome/library/actions")
OME_MAX_SCREENSHOTS_TRACKED = int(os.getenv("OME_MAX_SCREENSHOTS_TRACKED", 10))
OME_MAX_RECENT_SCREENSHOTS = int(os.getenv("OME_MAX_RECENT_SCREENSHOTS", 10))
OME_ACTION_DELAY = float(os.getenv("OME_ACTION_DELAY", 0.3))
OME_REAL_WIDTH = int(os.getenv("OME_REAL_WIDTH", 1920))
OME_REAL_HEIGHT = int(os.getenv("OME_REAL_HEIGHT", 1080))
OME_SHOT_WIDTH = int(os.getenv("OME_SHOT_WIDTH", 3840))
OME_SHOT_HEIGHT = int(os.getenv("OME_SHOT_HEIGHT", 2160))
OME_SCALE_X = float(os.getenv("OME_SCALE_X", 0.5))
OME_SCALE_Y = float(os.getenv("OME_SCALE_Y", 0.5))
OME_MENU_MAPS_DIR = os.getenv("OME_MENU_MAPS_DIR", PROJECT_ROOT / "OM_E_LM/ome/data/menu_maps")
OME_WINDOW_MAPS_DIR = os.getenv("OME_WINDOW_MAPS_DIR", PROJECT_ROOT / "OM_E_LM/ome/data/window_maps")
OME_MAX_CHILDREN = int(os.getenv("OME_MAX_CHILDREN", 20))
OME_WINDOW_DEPTH = int(os.getenv("OME_WINDOW_DEPTH", 4))
OME_TOOLBAR_DEPTH = int(os.getenv("OME_TOOLBAR_DEPTH", 6))
OME_SMART_PAUSE_THRESHOLD = float(os.getenv("OME_SMART_PAUSE_THRESHOLD", 5.0))

# === UI Automation (OM_E_Py) ===
UI_USE_FRONT_NAV = os.getenv("UI_USE_FRONT_NAV", "true").lower() in ("1", "true", "yes")
UI_ACTION_DELAY = float(os.getenv("UI_ACTION_DELAY", 0.2))
UI_WINDOW_WAIT_TIMEOUT = float(os.getenv("UI_WINDOW_WAIT_TIMEOUT", 10.0))
UI_MENU_WAIT_DELAY = float(os.getenv("UI_MENU_WAIT_DELAY", 0.3))
UI_APP_LAUNCH_DELAY = float(os.getenv("UI_APP_LAUNCH_DELAY", 2.0))
UI_WINDOW_MAXIMIZE_DELAY = float(os.getenv("UI_WINDOW_MAXIMIZE_DELAY", 1.0))
UI_MENU_ITEM_CLICK_DELAY = float(os.getenv("UI_MENU_ITEM_CLICK_DELAY", 0.3))
UI_RETRY_DELAY = float(os.getenv("UI_RETRY_DELAY", 0.2))
UI_MAX_RETRIES = int(os.getenv("UI_MAX_RETRIES", 3))
UI_SYSTEM_HANDLER_DELAY = float(os.getenv("UI_SYSTEM_HANDLER_DELAY", 5.0))
UI_MENU_EXPORT_DIR = os.getenv("UI_MENU_EXPORT_DIR", PROJECT_ROOT / "OM_E_Py/ome/data/menus")
UI_MAX_ROWS = int(os.getenv("UI_MAX_ROWS", 20))
UI_MESSAGE_EXPORT_DIR = os.getenv("UI_MESSAGE_EXPORT_DIR", PROJECT_ROOT / "OM_E_Py/ome/data/messages")
UI_APP_LIST_DIR = os.getenv("UI_APP_LIST_DIR", PROJECT_ROOT / "OM_E_Py/ome/data/appList")
UI_APP_LIST_PATH = os.getenv("UI_APP_LIST_PATH", PROJECT_ROOT / "OM_E_Py/ome/data/appList/app_list.json")
UI_APP_TEXTFIELD_DIR = os.getenv("UI_APP_TEXTFIELD_DIR", PROJECT_ROOT / "OM_E_Py/ome/data/textInputs")
UI_DEFAULT_SCREEN_WIDTH = int(os.getenv("UI_DEFAULT_SCREEN_WIDTH", 2560))
UI_DEFAULT_SCREEN_HEIGHT = int(os.getenv("UI_DEFAULT_SCREEN_HEIGHT", 1440))
UI_DEFAULT_POSITION = os.getenv("UI_DEFAULT_POSITION", "0.0,1440.0")
UI_NAV_EXPORT_DIR = os.getenv("UI_NAV_EXPORT_DIR", PROJECT_ROOT / "OM_E_Py/ome/data/navigation")
UI_POLL_INTERVAL = float(os.getenv("UI_POLL_INTERVAL", 0.02))
UI_APP_FOCUS_TIMEOUT = float(os.getenv("UI_APP_FOCUS_TIMEOUT", 2.0))
UI_SLEEP_AFTER_ACTIVATE = float(os.getenv("UI_SLEEP_AFTER_ACTIVATE", 0.1))
UI_SLEEP_AFTER_FULLSCREEN = float(os.getenv("UI_SLEEP_AFTER_FULLSCREEN", 0.6))
UI_PICKER_EXPORT_DIR = os.getenv("UI_PICKER_EXPORT_DIR", PROJECT_ROOT / "OM_E_Py/ome/data/pickers")
UI_WIN_LIST_DIR = os.getenv("UI_WIN_LIST_DIR", PROJECT_ROOT / "OM_E_Py/ome/data/windows")
UI_WINDOW_REF_MAP_CONFIG = os.getenv("UI_WINDOW_REF_MAP_CONFIG", PROJECT_ROOT / "OM_E_Py/ome/data/windows/appName_config/window_ref_map.jsonl")
UI_TRANSLATOR_EXPORT_DIR = os.getenv("UI_TRANSLATOR_EXPORT_DIR", PROJECT_ROOT / "OM_E_Py/ome/data/navigation/translator")

# Construct a robust, absolute path for the active bundle JSON.
# This ensures that no matter where the script is run from, it can find this critical file.
UI_ACTIVE_BUNDLE_JSON = PROJECT_ROOT / "Om_E_Py" / "ome" / "data" / "windows" / "active_target_Bundle_ID.json"


# === Workflow Engine (OM_E_Tree) ===
TREE_OPENAI_API_KEY = os.getenv("TREE_OPENAI_API_KEY")
TREE_ACTION_RETRIES = int(os.getenv("TREE_ACTION_RETRIES", 2))
TREE_ACTION_RETRY_DELAY = float(os.getenv("TREE_ACTION_RETRY_DELAY", 1.0))
TREE_LOG_LEVEL = os.getenv("TREE_LOG_LEVEL", "INFO")
TREE_LOG_FILE_PREFIX = os.getenv("TREE_LOG_FILE_PREFIX", "ome_log_")
TREE_PLATFORM = os.getenv("TREE_PLATFORM", "mac")
TREE_APPLICATION_PATH = Path(os.getenv("TREE_APPLICATION_PATH", "/Applications"))
TREE_APP_LIST_PATH = os.getenv("TREE_APP_LIST_PATH", PROJECT_ROOT / "OM_E_Tree/ome/data/app_list.json")
TREE_APP_LIST_DIR = os.getenv("TREE_APP_LIST_DIR", PROJECT_ROOT / "OM_E_Tree/ome/data/appList")
TREE_SYSTEM_HANDLER_DELAY = float(os.getenv("TREE_SYSTEM_HANDLER_DELAY", 2.0))
TREE_TREE_PATH = os.getenv("TREE_TREE_PATH", PROJECT_ROOT / "OM_E_Tree/ome/data/tree/execution_tree.json")
TREE_LOGS_DIR = os.getenv("TREE_LOGS_DIR", PROJECT_ROOT / "OM_E_Tree/ome/data/logs")
TREE_ARCHIVE_DIR = os.getenv("TREE_ARCHIVE_DIR", PROJECT_ROOT / "OM_E_Tree/ome/data/archive")
TREE_TREE_ARCHIVE_DIR = os.getenv("TREE_TREE_ARCHIVE_DIR", PROJECT_ROOT / "OM_E_Tree/ome/data/archive")
TREE_SCHEMA_DIR = os.getenv("TREE_SCHEMA_DIR", PROJECT_ROOT / "OM_E_Tree/ome/library/structures")
TREE_SCREENSHOT_DIR = os.getenv("TREE_SCREENSHOT_DIR", PROJECT_ROOT / "OM_E_Tree/ome/data/screenshots")
TREE_TEMPLATE_DIR = os.getenv("TREE_TEMPLATE_DIR", PROJECT_ROOT / "OM_E_Tree/ome/data/opencvsearchdb/templates")
TREE_TEMPLATE_INDEX = os.getenv("TREE_TEMPLATE_INDEX", PROJECT_ROOT / "OM_E_Tree/ome/data/opencvsearchdb/index.json")
TREE_ACTIONS_DIR = os.getenv("TREE_ACTIONS_DIR", PROJECT_ROOT / "OM_E_Tree/ome/library/actions")
TREE_MAX_SCREENSHOTS_TRACKED = int(os.getenv("TREE_MAX_SCREENSHOTS_TRACKED", 10))
TREE_MAX_RECENT_SCREENSHOTS = int(os.getenv("TREE_MAX_RECENT_SCREENSHOTS", 10))
TREE_ACTION_DELAY = float(os.getenv("TREE_ACTION_DELAY", 0.3))
TREE_REAL_WIDTH = int(os.getenv("TREE_REAL_WIDTH", 1920))
TREE_REAL_HEIGHT = int(os.getenv("TREE_REAL_HEIGHT", 1080))
TREE_SHOT_WIDTH = int(os.getenv("TREE_SHOT_WIDTH", 3840))
TREE_SHOT_HEIGHT = int(os.getenv("TREE_SHOT_HEIGHT", 2160))
TREE_SCALE_X = float(os.getenv("TREE_SCALE_X", 0.5))
TREE_SCALE_Y = float(os.getenv("TREE_SCALE_Y", 0.5))
TREE_MENU_MAPS_DIR = os.getenv("TREE_MENU_MAPS_DIR", PROJECT_ROOT / "OM_E_Tree/ome/data/menu_maps")
TREE_WINDOW_MAPS_DIR = os.getenv("TREE_WINDOW_MAPS_DIR", PROJECT_ROOT / "OM_E_Tree/ome/data/window_maps")
TREE_MAX_CHILDREN = int(os.getenv("TREE_MAX_CHILDREN", 20))
TREE_WINDOW_DEPTH = int(os.getenv("TREE_WINDOW_DEPTH", 4))
TREE_TOOLBAR_DEPTH = int(os.getenv("TREE_TOOLBAR_DEPTH", 6))

# === Helper function ===
def get_env(key, default=None, cast_type=str):
    val = os.getenv(key, default)
    if val is not None and cast_type is not str:
        try:
            return cast_type(val)
        except Exception:
            return default
    return val

AUDIO_DEVICE=3
