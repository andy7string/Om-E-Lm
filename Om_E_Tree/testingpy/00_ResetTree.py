import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import json
from datetime import datetime
from env import TREE_TREE_PATH

TREE_PATH = Path(TREE_TREE_PATH)

def reset_action(action):
    action["state"] = "pending"
    action["status"] = "not_started"
    action["attempts"] = 0
    action.pop("completed_at", None)
    action.pop("last_error", None)
    return action

def clean_tree(tree):
    if "objectives" not in tree:
        return tree

    for obj in tree["objectives"]:
        obj["status"] = "pending"
        obj.pop("completed_at", None)

        for task in obj.get("tasks", []):
            task["status"] = "pending"
            task.pop("completed_at", None)

            for action in task.get("actions", []):
                reset_action(action)

    tree["status"] = "pending"
    tree["created_at"] = datetime.utcnow().isoformat()
    tree.pop("completed_at", None)
    return tree

def main():
    if not TREE_PATH.exists():
        print("❌ Tree file not found.")
        return

    with open(TREE_PATH, "r") as f:
        tree = json.load(f)

    cleaned = clean_tree(tree)

    with open(TREE_PATH, "w") as f:
        json.dump(cleaned, f, indent=2)

    print(f"✅ Tree cleaned and reset: {TREE_PATH}")

if __name__ == "__main__":
    main()
