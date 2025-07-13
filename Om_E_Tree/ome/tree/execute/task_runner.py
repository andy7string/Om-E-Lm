from datetime import datetime, timezone
from Om_E_Tree.ome.tree.execute.action_runner import run_action
from Om_E_Tree.ome.tree.sync import save_task
from Om_E_Tree.ome.utils.logger import log_event

# ===================================================
# ▶️ TASK EXECUTION ENGINE
# ===================================================

def run_task(task: dict, objective_id: str) -> dict:
    """
    Executes the next incomplete action in a task.
    Updates task state and saves to disk.
    Halts on first failed action and returns status.

    Args:
        task (dict): Task node from the in-memory execution tree
        objective_id (str): ID of the parent objective

    Returns:
        dict: {
            "status": "complete" | "in_progress" | "failed",
            "last_action_result": dict (optional)
        }
    """
    task_id = task.get("task_id", "unknown")
    actions = task.get("actions", [])

    # ✅ No actions = complete immediately
    if not actions:
        log_event("WARN", "task_runner", "⚠️ No actions found in task", {"task_id": task_id})
        task["status"] = "complete"
        task["completed_at"] = datetime.now(timezone.utc).isoformat()
        task["objective_id"] = objective_id
        save_task(task)
        return {"status": "complete"}

    # 🔁 Run the next incomplete action only
    for i, action in enumerate(actions):
        if action.get("status") not in ("complete", "success"):
            log_event("INFO", "task_runner", "▶️ Running action", {
                "task_id": task_id,
                "action_name": action.get("name"),
                "source": action.get("source")
            })

            result = run_action(action)

            # 🔄 Reflect action result into task
            action["status"] = result.get("status", "failed")
            action["state"] = "complete"
            action["completed_at"] = datetime.now(timezone.utc).isoformat()
            if action["status"] == "failed":
                action["last_error"] = result.get("error", "Unknown failure")
            
            # ✅ Update action in list
            actions[i] = action
            task["actions"] = actions
            task["objective_id"] = objective_id
            save_task(task)

            # ❌ Stop on failure and return
            if result.get("status") == "failed":
                log_event("ERROR", "task_runner", "❌ Action failed, stopping task", {
                    "task_id": task_id,
                    "action_name": action.get("name"),
                    "result": result
                })
                task["status"] = "failed"
                task["completed_at"] = datetime.now(timezone.utc).isoformat()
                save_task(task)
                return {"status": "failed", "last_action_result": result}

            # 🔁 Partial
            return {"status": "in_progress", "last_action_result": result}

    # ✅ All actions completed successfully
    task["status"] = "complete"
    task["completed_at"] = datetime.now(timezone.utc).isoformat()
    task["objective_id"] = objective_id
    log_event("INFO", "task_runner", "✅ Task completed", {"task_id": task_id})
    save_task(task)
    return {"status": "complete"}
