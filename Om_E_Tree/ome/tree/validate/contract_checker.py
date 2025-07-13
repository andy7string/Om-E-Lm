import json
import jsonschema
from Om_E_Tree.ome.utils.schema_loader import get_schema_path, get_action_path
from Om_E_Tree.ome.utils.logger import log_event

# ======================================================
# ✅ GOAL / OBJECTIVE / TASK VALIDATION
# ======================================================

def validate_goal(goal: dict):
    """Validate a goal object against its schema contract."""
    schema = load_structure_schema("goal")
    _validate_schema(goal, schema, "Goal")

def validate_objective(obj: dict):
    """Validate an objective object against contract."""
    schema = load_structure_schema("objective")
    _validate_schema(obj, schema, "Objective")

def validate_task(task: dict):
    """Validate a task object against contract."""
    schema = load_structure_schema("task")
    _validate_schema(task, schema, "Task")

def validate_action(action: dict):
    """
    Validate an action against:
    1. Structure schema
    2. Action source + name
    3. Required input_args from action library
    """
    schema = load_structure_schema("action")
    _validate_schema(action, schema, "Action")

    _validate_action_source_and_name(action)

    source = action["source"]
    name = action["name"]
    action_spec = load_action_spec(source, name)
    _validate_input_args_against_library(action, action_spec)

# ======================================================
# 🧠 SCHEMA FIELD + ENUM CHECKING
# ======================================================

def _validate_schema(obj: dict, schema: dict, label: str):
    _validate_required_fields(obj, schema.get("required", []), label)
    for field, allowed in schema.get("enums", {}).items():
        if field in obj:
            _validate_enum(field, obj[field], allowed, label)

def _validate_required_fields(obj: dict, required: list, label: str):
    for field in required:
        if field not in obj:
            raise ValueError(f"❌ {label} is missing required field: '{field}'")

def _validate_enum(field: str, value: str, allowed: list, label: str):
    if value not in allowed:
        raise ValueError(
            f"❌ {label} field '{field}' has invalid value '{value}'. Allowed: {allowed}"
        )

# ======================================================
# ✅ ACTION VALIDATION AGAINST SOURCE
# ======================================================

def _validate_action_source_and_name(action: dict):
    source = action.get("source")
    name = action.get("name")

    if not source or not name:
        raise ValueError("❌ Action must have both 'source' and 'name'.")

    lib_path = get_action_path(source)
    if not lib_path.exists():
        raise FileNotFoundError(f"❌ No action library found for source '{source}'")

    with open(lib_path, "r") as f:
        library = json.load(f)

    matches = []

    # ✅ Top-level object with "actions" list
    if isinstance(library, dict):
        if "actions" in library and isinstance(library["actions"], list):
            for entry in library["actions"]:
                if entry.get("name") == name:
                    matches.append("actions list")
                    break

        # ✅ Optional dict-style direct name match
        if name in library:
            matches.append("top-level dict")

    # ✅ Flat list format
    elif isinstance(library, list):
        for entry in library:
            if entry.get("name") == name:
                matches.append("direct list")
                break

    if not matches:
        raise ValueError(f"❌ Action name '{name}' not found in any supported format in '{source}.json'")

    log_event("INFO", "contract_checker", f"🧠 Action '{name}' matched in: {matches[0]}")

def _validate_input_args_against_library(action: dict, spec: dict):
    args = action.get("input_args", {})
    required = spec.get("input_args", {})

    if isinstance(required, list):
        # ✅ Legacy: ["x", "y"]
        missing = [arg for arg in required if arg not in args]
    elif isinstance(required, dict):
        # ✅ Structured: { "x": {...}, "y": {...} }
        missing = [arg for arg in required.keys() if arg not in args]
    else:
        raise ValueError("❌ Invalid format for input_args in action spec.")

    if missing:
        raise ValueError(f"❌ Missing required input_arg(s): {', '.join(missing)}")

# ======================================================
# 📥 STRUCTURE + ACTION SPEC LOADING
# ======================================================

def load_structure_schema(name: str) -> dict:
    path = get_schema_path(name)
    if not path.exists():
        raise FileNotFoundError(f"❌ Schema file not found for {name}: {path}")
    with open(path, "r") as f:
        return json.load(f)

def load_action_spec(source: str, name: str) -> dict:
    path = get_action_path(source)
    if not path.exists():
        raise FileNotFoundError(f"❌ Action source file not found: {path}")
    
    with open(path, "r") as f:
        data = json.load(f)

    # 🔍 Check 'actions' list inside a dict
    if isinstance(data, dict) and "actions" in data and isinstance(data["actions"], list):
        for entry in data["actions"]:
            if entry.get("name") == name:
                return entry
        raise ValueError(f"❌ Action '{name}' not found in 'actions' list of {source}.json")

    # 🔍 Flat list support
    if isinstance(data, list):
        for entry in data:
            if entry.get("name") == name:
                return entry
        raise ValueError(f"❌ Action '{name}' not found in list in {source}.json")

    # 🔍 Legacy dict-style direct key
    if name in data:
        return data[name]

    raise ValueError(f"❌ Action '{name}' not found in any supported format in {source}.json")
