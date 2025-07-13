print("--- EXECUTING NEW MEMORY.PY ---")
import json
from pathlib import Path
from env import TREE_TREE_PATH

TREE_PATH = Path(TREE_TREE_PATH)
from Om_E_Tree.ome.utils.builder.input_args_builder import build_input_args
from Om_E_Tree.ome.utils.logger import log_event

# ===================================================
# 🧠 MEMORY CACHE + ID INDEXES
# ===================================================

_TREE_CACHE = None

# Fast lookup tables for runtime resolution
_INDEXES = {
    "objectives": {},  # objective_id -> full dict
    "tasks": {}        # task_id -> full dict
}

# ===================================================
# 📥 CORE TREE LOADER
# ===================================================

def load_tree(refresh=True):
    """
    Load the full execution tree from disk into memory.
    Injects input_args and builds index maps.

    Args:
        refresh (bool): If True, reload from disk.

    Returns:
        dict: The loaded execution tree
    """
    global _TREE_CACHE

    if refresh or _TREE_CACHE is None:
        try:
            with open(TREE_PATH, "r") as f:
                _TREE_CACHE = json.load(f)
        except FileNotFoundError:
            log_event("ERROR", "memory", f"Tree file not found: {TREE_PATH}")
            raise FileNotFoundError(f"❌ execution_tree.json not found at {TREE_PATH}")
        except json.JSONDecodeError as e:
            log_event("ERROR", "memory", f"Invalid JSON in tree: {e}")
            raise ValueError(f"❌ Invalid JSON in tree file: {e}")

        _inject_input_args()
        _build_indexes()

    return _TREE_CACHE

# ===================================================
# 🧠 INPUT ARGS INJECTION
# ===================================================

def _inject_input_args():
    """
    Inject missing input_args into the tree for all actions.
    Uses contract defaults and builder logic.
    """
    for obj in _TREE_CACHE.get("objectives", []):
        for task in obj.get("tasks", []):
            for action in task.get("actions", []):
                if "input_args" not in action or not action["input_args"]:
                    action["input_args"] = build_input_args(action["source"], action["name"])

# ===================================================
# ⚡ INDEX BUILDING
# ===================================================

def _build_indexes():
    """
    Create fast ID-based access maps for objectives and tasks.
    """
    global _INDEXES
    _INDEXES = {"objectives": {}, "tasks": {}}

    for obj in _TREE_CACHE.get("objectives", []):
        _INDEXES["objectives"][obj["objective_id"]] = obj
        for task in obj.get("tasks", []):
            _INDEXES["tasks"][task["task_id"]] = task

# ===================================================
# 📤 TREE READ ACCESSORS (FROM MEMORY)
# ===================================================

def get_full_tree():
    return _TREE_CACHE

def get_goal(goal_id):
    if not _TREE_CACHE or _TREE_CACHE.get("goal_id") != goal_id:
        raise ValueError(f"⚠️ Goal ID '{goal_id}' does not match current tree.")
    return _TREE_CACHE

def get_objective(objective_id):
    obj = _INDEXES["objectives"].get(objective_id)
    if not obj:
        raise ValueError(f"⚠️ Objective ID '{objective_id}' not found in memory.")
    return obj

def get_task(task_id):
    task = _INDEXES["tasks"].get(task_id)
    if not task:
        raise ValueError(f"⚠️ Task ID '{task_id}' not found in memory.")
    return task

def get_actions(task_id):
    task = get_task(task_id)
    return task.get("actions", [])

# ===================================================
# 📤 TREE READ ACCESSORS (FROM FILE)
# ===================================================

def load_goal_from_file(goal_id):
    with open(TREE_PATH, "r") as f:
        tree = json.load(f)
    if tree.get("goal_id") != goal_id:
        raise ValueError(f"⚠️ Goal ID '{goal_id}' not found in tree file.")
    return tree

def load_objective_from_file(objective_id):
    with open(TREE_PATH, "r") as f:
        tree = json.load(f)
    for obj in tree.get("objectives", []):
        if obj["objective_id"] == objective_id:
            return obj
    raise ValueError(f"⚠️ Objective ID '{objective_id}' not found in file.")

def load_task_from_file(task_id):
    with open(TREE_PATH, "r") as f:
        tree = json.load(f)
    for obj in tree.get("objectives", []):
        for task in obj.get("tasks", []):
            if task["task_id"] == task_id:
                return task
    raise ValueError(f"⚠️ Task ID '{task_id}' not found in file.")
