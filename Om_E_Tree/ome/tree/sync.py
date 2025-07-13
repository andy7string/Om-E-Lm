import json
from pathlib import Path
from Om_E_Tree.ome.tree import memory
from Om_E_Tree.ome.utils.logger import log_event
from env import TREE_TREE_PATH

TREE_PATH = Path(TREE_TREE_PATH)

# ===================================================
# 🌳 Save the full execution tree to disk
# ===================================================

def write_full_tree(tree: dict):
    """
    Save the entire execution tree to disk and reload the in-memory cache.

    Args:
        tree (dict): The full tree structure (must match contract).
    """
    try:
        with open(TREE_PATH, "w") as f:
            json.dump(tree, f, indent=2)
        log_event("INFO", "sync", f"✅ Tree saved to: {TREE_PATH}")
        memory.load_tree(refresh=True)
    except Exception as e:
        raise RuntimeError(f"❌ Failed to write execution tree: {e}")

# ===================================================
# 🎯 Save goal-level update
# ===================================================

def save_goal(goal_obj: dict):
    """
    Replace the current goal-level object in the tree and persist.

    Args:
        goal_obj (dict): Must contain goal_id and objectives.
    """
    tree = memory.get_full_tree()
    if tree.get("goal_id") != goal_obj.get("goal_id"):
        raise ValueError("❌ Mismatched goal_id — cannot save.")
    
    tree.update(goal_obj)
    write_full_tree(tree)

# ===================================================
# 🧭 Save objective-level update
# ===================================================

def save_objective(objective_obj: dict):
    """
    Update a specific objective node in the tree and persist.

    Args:
        objective_obj (dict): Must contain objective_id.
    """
    tree = memory.get_full_tree()
    updated = False

    for i, obj in enumerate(tree.get("objectives", [])):
        if obj["objective_id"] == objective_obj["objective_id"]:
            tree["objectives"][i] = objective_obj
            updated = True
            break

    if not updated:
        raise ValueError(f"❌ Objective '{objective_obj['objective_id']}' not found.")
    
    write_full_tree(tree)

# ===================================================
# ⚙️ Save task-level update
# ===================================================

def save_task(task_obj: dict):
    """
    Update a task node inside its parent objective and persist.

    Args:
        task_obj (dict): Must contain task_id and objective_id.
    """
    tree = memory.get_full_tree()
    updated = False

    for obj in tree.get("objectives", []):
        if obj["objective_id"] == task_obj["objective_id"]:
            for i, task in enumerate(obj.get("tasks", [])):
                if task["task_id"] == task_obj["task_id"]:
                    obj["tasks"][i] = task_obj
                    updated = True
                    break

    if not updated:
        raise ValueError(f"❌ Task '{task_obj['task_id']}' not found under its objective.")

    write_full_tree(tree)
