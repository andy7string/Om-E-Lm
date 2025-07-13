import time
from datetime import datetime, timezone

from Om_E_Tree.ome.tree.validate.contract_checker import validate_action
from Om_E_Tree.ome.utils.logger import log_event
from Om_E_Tree.ome.handlers.handler_map import handler_map
from env import TREE_ACTION_RETRIES, TREE_ACTION_RETRY_DELAY, TREE_ACTION_DELAY
from Om_E_Tree.ome.utils.schema_loader import get_schema_path
from Om_E_Tree.ome.utils.system.system_checker import list_installed_apps

ACTION_DELAY = TREE_ACTION_DELAY
ACTION_RETRIES = TREE_ACTION_RETRIES
ACTION_RETRY_DELAY = TREE_ACTION_RETRY_DELAY

# Shared context between actions (e.g. passing positions between vision + mouse)
shared_context = {}

# ===================================================
# 🧠 INPUT ARG VARIABLE RESOLUTION
# ===================================================

def resolve_vars(input_args, context):
    """
    Replaces $context.lookups in input_args using shared_context.
    Example: "$last_position.x" → context["last_position"]["x"]
    """
    if not isinstance(input_args, dict):
        return input_args

    resolved = {}
    for key, val in input_args.items():
        if isinstance(val, str) and val.startswith("$"):
            parts = val[1:].split(".")
            obj = context
            for part in parts:
                obj = obj.get(part)
                if obj is None:
                    break
            resolved[key] = obj
        else:
            resolved[key] = val
    return resolved

# ===================================================
# ▶️ ACTION EXECUTION ENTRYPOINT
# ===================================================

def run_action(action: dict, delay: float = 0.0) -> dict:
    """
    Executes a single action using its mapped handler.
    Supports input var resolution, retry logic, and shared context updates.

    Args:
        action (dict): The action node from the execution tree
        delay (float): Optional delay before first execution attempt

    Returns:
        dict: Result object with at least 'status' key
    """
    # Use the global delay from env.py
    delay = ACTION_DELAY

    # ✅ Contract validation
    try:
        validate_action(action)
    except Exception as e:
        return _mark_failed(action, f"Validation failed: {e}")

    # 🔍 Handler resolution
    source = action.get("source")
    name = action.get("name")
    handler_key = f"{source}.{name}"
    handler = handler_map.get(handler_key)
    if not handler:
        return _mark_failed(action, f"No handler found for '{handler_key}'")

    # 🎯 Resolve input args using shared context
    raw_args = action.get("input_args", {})
    if not isinstance(raw_args, dict):
        return _mark_failed(action, "Invalid or missing input_args")
    args = resolve_vars(raw_args, shared_context)

    # ⏱ Optional delay before starting
    if delay > 0:
        time.sleep(delay)

    # 🔁 Execute with retry logic
    max_retries = action.get("retries", ACTION_RETRIES)
    retry_delay = ACTION_RETRY_DELAY
    action["attempts"] = 0
    result = {}

    for attempt in range(max_retries + 1):
        log_event("INFO", "action_runner", f"Attempt {attempt + 1} for action", {
            "name": name,
            "source": source,
            "input_args": args,
            "retries": max_retries
        })

        result = handler(args)
        action["attempts"] += 1

        # ✅ Success — break loop
        if result.get("status") in ("success", "complete"):
            break

        # 🛟 First failure fallback (e.g. replace with Chrome)
        if result.get("status") == "failed" and attempt == 0:
            if "browser" in args or "application" in args:
                fallback = "Google Chrome"
                target_key = "browser" if "browser" in args else "application"
                original = args.get(target_key, "")

                if fallback in list_installed_apps() and original != fallback:
                    log_event("INFO", "action_runner", f"🔁 Retrying with fallback app: {fallback}")
                    args[target_key] = fallback
                    action["input_args"][target_key] = fallback
                    continue

        # ⏲ Wait before next retry
        if attempt < max_retries:
            time.sleep(retry_delay)

    # 💾 Store any position/info into shared context
    store_key = action.get("store_result_as", name)
    if "position" in result:
        shared_context[store_key] = result["position"]
        shared_context["last_position"] = result["position"]
    if "info" in result:
        shared_context[f"{store_key}_info"] = result["info"]

    # 🧾 Mark action complete with final status
    action["completed_at"] = datetime.now(timezone.utc).isoformat()
    action["state"] = "complete"
    action["status"] = result.get("status", "failed")
    if action["status"] not in ("success", "complete"):
        action["last_error"] = result.get("error", "Unknown failure")

    # 📜 Logging
    log_event("INFO", "action_runner", "✅ Action completed", {
        "name": name,
        "source": source,
        "status": action["status"],
        "attempts": action["attempts"],
        "result": result
    })

    # 🖨️ Terminal feedback
    print(f"🧪 Action result: {result}")
    return result

# ===================================================
# ❌ FAILURE MARKER
# ===================================================

def _mark_failed(action: dict, error_msg: str) -> dict:
    """
    Marks the given action as failed and logs the reason.

    Args:
        action (dict): The action being executed
        error_msg (str): Failure reason

    Returns:
        dict: Result object with 'failed' status and error message
    """
    action["status"] = "failed"
    action["state"] = "complete"
    action["completed_at"] = datetime.now(timezone.utc).isoformat()
    action["last_error"] = error_msg
    action["attempts"] = action.get("attempts", 0) + 1

    log_event("ERROR", "action_runner", error_msg, {
        "name": action.get("name"),
        "source": action.get("source")
    })

    return {"status": "failed", "error": error_msg}
