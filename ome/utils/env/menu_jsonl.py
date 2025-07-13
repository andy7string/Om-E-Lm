import json

def load_menu_jsonl(jsonl_path):
    """
    Load a menu JSONL file and return a list of dicts (one per menu item).
    """
    items = []
    with open(jsonl_path, 'r', encoding='utf-8') as f:
        for line in f:
            try:
                items.append(json.loads(line))
            except Exception:
                continue
    return items 