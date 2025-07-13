def get_omeclick_path_for_menu(menu_items, menu_path):
    """
    Given a list of menu_items (dicts from JSONL) and a menu_path (list of titles),
    return a list of dicts for each step in the path, each with at least 'omeClick' and 'title'.
    Skips steps where omeClick is missing.
    """
    path_steps = []
    for i in range(1, len(menu_path) + 1):
        sub_path = menu_path[:i]
        item = next((m for m in menu_items if m.get('menu_path') == sub_path), None)
        if item and 'omeClick' in item:
            path_steps.append({'title': item.get('title'), 'omeClick': item.get('omeClick')})
        else:
            # Still append the step for completeness, but with None for omeClick
            path_steps.append({'title': sub_path[-1], 'omeClick': item.get('omeClick') if item else None})
    return path_steps

# Alias for compatibility
mouse_nav_menu_path = get_omeclick_path_for_menu 