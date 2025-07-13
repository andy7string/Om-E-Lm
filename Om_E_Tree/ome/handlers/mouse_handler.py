import pyautogui
from Om_E_Tree.ome.utils.logger import log_event
from Om_E_Tree.ome.utils.system.display import get_real_display_resolution

def move_mouse(args):
    try:
        x = int(args["x"])
        y = int(args["y"])
        screen_width, screen_height = pyautogui.size()
        if not (0 <= x < screen_width and 0 <= y < screen_height):
            raise ValueError(f"Coordinates ({x}, {y}) out of screen bounds ({screen_width}, {screen_height})")

        print(f"[DEBUG] Moving mouse to: ({x}, {y}) within screen ({screen_width}, {screen_height})")
        pyautogui.moveTo(x, y)
        return {"status": "complete"}
    except Exception as e:
        print(f"[ERROR] move_mouse failed: {e}")
        return {"status": "failed", "error": str(e)}

def click_mouse(args):
    try:
        x = int(args["x"])
        y = int(args["y"])
        button = args.get("button", "left")
        pyautogui.click(x, y, button=button)
        return {"status": "complete"}
    except Exception as e:
        return {"status": "failed", "error": str(e)}

def double_click_mouse(args):
    try:
        x = int(args["x"])
        y = int(args["y"])
        pyautogui.doubleClick(x, y)
        return {"status": "complete"}
    except Exception as e:
        return {"status": "failed", "error": str(e)}

def right_click_mouse(args):
    try:
        x = int(args["x"])
        y = int(args["y"])
        pyautogui.rightClick(x, y)
        return {"status": "complete"}
    except Exception as e:
        return {"status": "failed", "error": str(e)}

def drag_mouse(args):
    try:
        start_x = int(args["start_x"])
        start_y = int(args["start_y"])
        end_x = int(args["end_x"])
        end_y = int(args["end_y"])
        duration = float(args["duration"])
        button = args.get("button", "left")

        pyautogui.moveTo(start_x, start_y)
        pyautogui.mouseDown(button=button)
        pyautogui.moveTo(end_x, end_y, duration=duration)
        pyautogui.mouseUp(button=button)

        return {"status": "complete"}
    except Exception as e:
        return {"status": "failed", "error": str(e)}

def scroll_mouse(args):
    try:
        amount = int(args["amount"])
        pyautogui.scroll(amount)
        return {"status": "complete"}
    except Exception as e:
        return {"status": "failed", "error": str(e)}

def get_mouse_position(args):
    try:
        x, y = pyautogui.position()
        return {"status": "complete", "position": {"x": x, "y": y}}
    except Exception as e:
        return {"status": "failed", "error": str(e)}

def mouse_down(args):
    try:
        button = args.get("button", "left")
        pyautogui.mouseDown(button=button)
        return {"status": "complete"}
    except Exception as e:
        return {"status": "failed", "error": str(e)}

def mouse_up(args):
    try:
        button = args.get("button", "left")
        pyautogui.mouseUp(button=button)
        return {"status": "complete"}
    except Exception as e:
        return {"status": "failed", "error": str(e)}

# Dispatcher used by handler_map
def run(action_name, input_args):
    actions = {
        "move_mouse": move_mouse,
        "click_mouse": click_mouse,
        "double_click_mouse": double_click_mouse,
        "right_click_mouse": right_click_mouse,
        "drag_mouse": drag_mouse,
        "scroll_mouse": scroll_mouse,
        "get_mouse_position": get_mouse_position,
        "mouse_down": mouse_down,
        "mouse_up": mouse_up,
    }
    fn = actions.get(action_name)
    if fn:
        return fn(input_args)
    return {"status": "failed", "error": f"Unknown action '{action_name}'"}
