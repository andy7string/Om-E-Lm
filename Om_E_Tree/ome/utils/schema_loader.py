import json
from pathlib import Path
from env import TREE_SCHEMA_DIR, TREE_ACTIONS_DIR

SCHEMA_DIR = Path(TREE_SCHEMA_DIR)
ACTIONS_DIR = Path(TREE_ACTIONS_DIR)

# ===================================================
# 📂 Resolve schema JSON path by name
# ===================================================

def get_schema_path(schema_name: str) -> Path:
    """
    Get the full path to a JSON schema file based on schema_name.
    
    Args:
        schema_name (str): Name of the schema (e.g. "action")

    Returns:
        Path: Resolved path to the schema JSON file
    """
    return SCHEMA_DIR / f"{schema_name}.json"

# ===================================================
# 📂 Resolve action library JSON path by source
# ===================================================

def get_action_path(source: str) -> Path:
    """
    Get the full path to a JSON action file (e.g., mouse.json, system.json).

    Args:
        source (str): The action source

    Returns:
        Path: Resolved path to the action library
    """
    return ACTIONS_DIR / f"{source}.json"

# ===================================================
# 📥 Load a full action library from disk
# ===================================================

def load_action_library(name: str) -> dict:
    """
    Loads a JSON action library by name (e.g. "mouse", "keyboard").

    Args:
        name (str): Action source name

    Returns:
        dict: Parsed JSON action dictionary

    Raises:
        FileNotFoundError: If the library JSON doesn't exist
    """
    path = ACTIONS_DIR / f"{name}.json"
    if not path.exists():
        raise FileNotFoundError(f"❌ Action library '{name}' not found at {path}")
    with open(path, "r") as f:
        return json.load(f)
