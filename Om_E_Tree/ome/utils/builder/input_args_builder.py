import json
from pathlib import Path
from Om_E_Tree.ome.utils.schema_loader import get_action_path
from Om_E_Tree.ome.utils.system.system_checker import list_installed_apps
from Om_E_Tree.ome.utils.env.constants import DEFAULT_INPUT_ARGS

# ===================================================
# 🧠 Build smart default input_args for a given action
# ===================================================

def build_input_args(source: str, name: str) -> dict:
    """
    Constructs a dictionary of default input_args for a given action,
    using contract defaults and common sense fallbacks.
    """
    path = get_action_path(source)

    if not Path(path).exists():
        print(f"[WARN] Skipping input_args: '{source}.json' not found.")
        return {}

    try:
        with open(path, "r") as f:
            data = json.load(f)
    except Exception as e:
        print(f"[WARN] Could not load '{source}.json': {e}")
        return {}

    # 🔥 Legacy combo handler (used only by mousecv)
    if source == "mousecv":
        try:
            action_spec = _find_action_spec(data, name)
        except ValueError as ve:
            print(f"[WARN] {ve}")
            return {}

        required_args = action_spec.get("input_args", [])
        args = {arg: _infer_default(arg) for arg in required_args}
        args["combo"] = name
        return args

    try:
        action_spec = _find_action_spec(data, name)
    except ValueError as ve:
        print(f"[WARN] {ve}")
        return {}

    required_args = action_spec.get("input_args", [])
    default_values = action_spec.get("defaults", {})

    installed_apps = list_installed_apps()
    args = {}

    for arg in required_args:
        if arg == "browser":
            preferred = default_values.get(arg, "Google Chrome")
            args[arg] = preferred if preferred in installed_apps else _fallback_browser(installed_apps)

        elif arg == "app_name":
            requested = default_values.get(arg, "Google Chrome")
            match = _match_fuzzy_app(requested, installed_apps)
            args[arg] = match

        else:
            args[arg] = default_values.get(arg, _infer_default(arg))

    return args

# ===================================================
# 🔍 Locate an action's spec from the JSON contract
# ===================================================

def _find_action_spec(data: dict, name: str) -> dict:
    if isinstance(data, dict) and "actions" in data:
        for entry in data["actions"]:
            if entry.get("name") == name:
                return entry
    elif isinstance(data, list):
        for entry in data:
            if entry.get("name") == name:
                return entry
    raise ValueError(f"❌ Action '{name}' not found in action file.")

# ===================================================
# 🧠 Default guesser for input_args
# ===================================================

def _infer_default(arg_name: str):
    lower = arg_name.lower()
    if "x" in lower or "y" in lower: return 100
    if "duration" in lower or "interval" in lower: return 0.3
    if "text" in lower: return "hello from Om-E"
    if "button" in lower: return "left"
    if "amount" in lower: return 10
    if "label" in lower: return "OK"
    if "path" in lower: return "sample_image.png"
    if "threshold" in lower: return 0.9
    if "key" in lower: return "enter"
    if "keys" in lower: return ["ctrl", "c"]
    if "app" in lower or "application" in lower: return "Google Chrome"
    if "filename" in lower: return "screenshot.png"
    if "width" in lower: return 300
    if "height" in lower: return 100
    return ""

# ===================================================
# 🧠 Browser fallback
# ===================================================

def _fallback_browser(apps: list) -> str:
    for candidate in ["Google Chrome", "Safari", "Firefox", "Brave Browser"]:
        if candidate in apps:
            return candidate
    return "Safari"

def _match_fuzzy_app(name: str, app_list: list) -> str:
    name_lower = name.lower()
    for app in app_list:
        if name_lower == app.lower():
            return app  # ✅ Exact match
    for app in app_list:
        if name_lower in app.lower():
            return app
    return name  # ✅ Return original if no match

# ===================================================
# 🧪 Tree-wide injection
# ===================================================

def inject_input_args(tree: dict):
    installed_apps = list_installed_apps()

    for obj in tree.get("objectives", []):
        for task in obj.get("tasks", []):
            for action in task.get("actions", []):
                args = action.get("input_args", {}) or {}

                if action.get("source") == "system" and action.get("name") == "launch_app":
                    raw_name = args.get("app_name")
                    if raw_name:
                        args["app_name"] = _match_fuzzy_app(raw_name, installed_apps)

                enriched = build_input_args(action["source"], action["name"])
                for key, value in enriched.items():
                    if key not in args or args[key] is None:
                        args[key] = value

                action["input_args"] = args

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Build smart default input_args for a given action.")
    parser.add_argument("source", help="Action source (JSON file name without .json)")
    parser.add_argument("name", help="Action name")
    args = parser.parse_args()
    result = build_input_args(args.source, args.name)
    print(json.dumps(result, indent=2))
