from datetime import datetime, timezone
from pathlib import Path
from shutil import copyfile

from Om_E_Tree.ome.tree.execute.objective_runner import run_objective
from Om_E_Tree.ome.tree.validate.contract_checker import validate_goal
from Om_E_Tree.ome.utils.logger import log_event
from Om_E_Tree.ome.tree.sync import save_goal
from env import TREE_TREE_PATH, TREE_ARCHIVE_DIR

TREE_ARCHIVE_DIR = Path(TREE_ARCHIVE_DIR)

# ===================================================
# 🚀 GOAL EXECUTION ENGINE
# ===================================================

def run_goal(goal: dict) -> dict:
    """
    Executes the next incomplete objective in the goal.
    Stops on first failure. Marks complete if all objectives done.

    Args:
        goal (dict): In-memory goal node.

    Returns:
        dict: {
            "status": "complete" | "in_progress" | "failed",
            "last_objective_result": dict (optional)
        }
    """
    goal_id = goal.get("goal_id", "unknown")
    objectives = goal.get("objectives", [])

    # ✅ Empty goals complete immediately
    if not objectives:
        log_event("WARN", "goal_runner", "⚠️ No objectives found in goal", {"goal_id": goal_id})
        goal["status"] = "complete"
        goal["completed_at"] = datetime.now(timezone.utc).isoformat()
        save_goal(goal)
        return {"status": "complete"}

    # 🔁 Run next incomplete objective
    for i, objective in enumerate(objectives):
        if objective.get("status") not in ("complete", "success"):
            log_event("INFO", "goal_runner", "▶️ Running objective", {
                "goal_id": goal_id,
                "objective_id": objective.get("objective_id")
            })

            result = run_objective(objective)

            # 🔄 Reflect updated objective into list
            objectives[i] = objective
            goal["objectives"] = objectives
            goal["last_objective_id"] = objective.get("objective_id")
            goal["status"] = "in_progress"  # ✅ CRITICAL LINE
            save_goal(goal)

            if result.get("status") == "failed":
                log_event("ERROR", "goal_runner", "❌ Objective failed — halting goal", {
                    "goal_id": goal_id,
                    "objective_id": objective.get("objective_id")
                })
                goal["status"] = "failed"
                goal["completed_at"] = datetime.now(timezone.utc).isoformat()
                save_goal(goal)
                return {"status": "failed", "last_objective_result": result}

            return {"status": "in_progress", "last_objective_result": result}

    # ✅ All objectives complete
    goal["status"] = "complete"
    goal["completed_at"] = datetime.now(timezone.utc).isoformat()
    log_event("INFO", "goal_runner", "🏁 Goal marked complete", {"goal_id": goal_id})
    save_goal(goal)

    # 🗃️ Archive the tree
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    TREE_ARCHIVE_DIR.mkdir(parents=True, exist_ok=True)
    dst = TREE_ARCHIVE_DIR / f"execution_tree__{timestamp}.json"
    copyfile(TREE_TREE_PATH, dst)
    log_event("INFO", "goal_runner", f"🗃️ Archived completed tree to {dst}")

    return {"status": "complete"}
