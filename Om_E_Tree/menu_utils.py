import time
import atomacos as atomac
import pyautogui

def expand_menu_children(bundle_id, center, parent_path, click_fn=None, keep_open=False, retries=3, delay=0.3):
    """
    Clicks a menu item, retrieves children, marks as expanded, and optionally closes the menu.

    Args:
        bundle_id (str): App bundle ID.
        center (list): [x, y] of menu item to click.
        parent_path (list): Path of parent menu in the clickmap.
        click_fn (func): Optional function to click (x, y).
        keep_open (bool): If True, does not press 'esc' after scanning.
        retries (int): Retry attempts to get children.
        delay (float): Delay between retries.
    
    Returns:
        List of serialized child elements (flat format).
    """
    app = atomac.getAppRefByBundleId(bundle_id)
    app.activate()
    time.sleep(0.5)

    if click_fn:
        click_fn(center[0], center[1])
    else:
        pyautogui.moveTo(center[0], center[1])
        pyautogui.click()
    time.sleep(delay)

    try:
        from atomacos import getElementAtPosition
        element = getElementAtPosition(center[0], center[1])
    except Exception:
        element = None

    if not element:
        print(f"[ERROR] No element found at {center}")
        return []

    # Retry if AXChildren are not populated yet
    children = getattr(element, 'AXChildren', [])
    attempt = 0
    while not children and attempt < retries:
        time.sleep(delay)
        children = getattr(element, 'AXChildren', [])
        attempt += 1

    flat = []
    for child in children:
        try:
            role = getattr(child, 'AXRole', None)
            label = getattr(child, 'AXTitle', None) or getattr(child, 'AXDescription', None)
            pos = getattr(child, 'AXPosition', None)
            size = getattr(child, 'AXSize', None)
            center_child = [pos.x + size.width / 2, pos.y + size.height / 2] if pos and size else None
            node = {
                "role": role,
                "label": label,
                "path": parent_path + [label] if label else parent_path,
                "center": center_child,
                "size": {"width": size.width, "height": size.height} if size else None,
                "flags": {
                    "is_menu": role in ("AXMenuButton", "AXPopUpButton"),
                    "has_children": bool(getattr(child, 'AXChildren', [])),
                    "likely_triggers_ui_change": role in ("AXButton", "AXMenuButton", "AXPopUpButton") and bool(getattr(child, 'AXChildren', []))
                }
            }
            flat.append(node)
        except Exception as e:
            print(f"[expand_menu_children] error: {e}")

    # Optional: Close menu
    if not keep_open:
        pyautogui.press('esc')
        time.sleep(0.1)

    # Add expanded tag to parent if children were found
    if flat:
        flat.append({
            "role": "AXMarker",
            "label": None,
            "path": parent_path + ["__expanded__"],
            "center": None,
            "size": None,
            "flags": {"is_menu": False, "has_children": False, "likely_triggers_ui_change": False}
        })

    return flat
