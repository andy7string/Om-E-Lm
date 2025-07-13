from datetime import datetime, timezone
from Om_E_Tree.ome.tree.execute.task_runner import run_task
from Om_E_Tree.ome.tree.sync import save_objective
from Om_E_Tree.ome.utils.logger import log_event

# ===================================================
# 🎯 OBJECTIVE EXECUTION ENGINE
# ===================================================

def run_objective(objective: dict) -> dict:
    """
    Executes the next incomplete task in the objective.
    Stops on failure. Marks objective complete if all tasks are done.

    Args:
        objective (dict): The in-memory objective node.

    Returns:
        dict: {
            "status": "complete" | "in_progress" | "failed" | "error",
            "last_task_result": dict (if applicable)
        }
    """
    objective_id = objective.get("objective_id", "unknown")
    tasks = objective.get("tasks", [])

    try:
        # 🔁 Loop over tasks and execute the next incomplete one
        for i, task in enumerate(tasks):
            if task.get("status") not in ("complete", "success"):
                result = run_task(task, objective_id)

                # 🔄 Reflect updated task state back into objective
                tasks[i] = task
                objective["tasks"] = tasks
                objective["last_task_id"] = task.get("task_id")
                objective["status"] = "in_progress"  # ✅ ADDED HERE
                save_objective(objective)

                # ❌ Stop on task failure
                if result.get("status") == "failed":
                    log_event("ERROR", "objective_runner", "❌ Task failed — halting objective", {
                        "objective_id": objective_id,
                        "task_id": task.get("task_id"),
                        "result": result
                    })
                    objective["status"] = "failed"
                    objective["completed_at"] = datetime.now(timezone.utc).isoformat()
                    save_objective(objective)
                    return {"status": "failed", "last_task_result": result}

                # 🔁 More tasks to go
                return {"status": "in_progress", "last_task_result": result}

        # ✅ All tasks complete
        objective["status"] = "complete"
        objective["completed_at"] = datetime.now(timezone.utc).isoformat()
        save_objective(objective)
        log_event("INFO", "objective_runner", "✅ Objective complete", {"objective_id": objective_id})
        return {"status": "complete"}

    except Exception as e:
        import traceback
        log_event("ERROR", "objective_runner", f"❌ Exception during run_objective", {
            "objective_id": objective_id,
            "error": str(e),
            "traceback": traceback.format_exc() # Add full traceback to log
        })
        objective["status"] = "error"
        objective["completed_at"] = datetime.now(timezone.utc).isoformat()
        save_objective(objective)
        return {"status": "error", "error": str(e)}
