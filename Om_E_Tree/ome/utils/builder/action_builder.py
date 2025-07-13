import json
from Om_E_Tree.ome.utils.schema_loader import get_action_path
from Om_E_Tree.ome.utils.env.constants import DEFAULT_INPUT_ARGS


# ===================================================
# 🧠 Build input_args dictionary with default values
# ===================================================

def build_input_args(source: str, name: str) -> dict:
    """
    Constructs a flat input_args dictionary using the default value mapping
    defined in constants.py. Reads the required input_args for a given
    action and fills them with fallback values.

    Supports both list-style and object-style action definitions.
    """
    path = get_action_path(source)
    if not path.exists():
        raise FileNotFoundError(f"❌ Action source file not found: {path}")
    
    with open(path, "r") as f:
        data = json.load(f)

    # 🧠 Handle object-style {"actions": [...]}
    if isinstance(data, dict) and "actions" in data:
        for action in data["actions"]:
            if action.get("name") == name:
                return _fill_defaults(action.get("input_args", []))

    # 🧠 Handle list-style format
    if isinstance(data, list):
        for action in data:
            if action.get("name") == name:
                return _fill_defaults(action.get("input_args", []))

    raise ValueError(f"❌ Action '{name}' not found in '{source}.json'")


def _fill_defaults(arg_names: list) -> dict:
    """
    Fills a dict of input_args based on known default values
    from constants.py. Any unknown keys receive a placeholder.

    Args:
        arg_names (list): List of input argument names.

    Returns:
        dict: Dict of input_arg values.
    """
    return {arg: DEFAULT_INPUT_ARGS.get(arg, f"<{arg}_value>") for arg in arg_names}


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Build input_args dictionary for a given action.")
    parser.add_argument("source", help="Action source (JSON file name without .json)")
    parser.add_argument("name", help="Action name")
    args = parser.parse_args()
    result = build_input_args(args.source, args.name)
    print(json.dumps(result, indent=2))
