import platform
import os
from PIL import ImageGrab
import dotenv
from env import TREE_SCALE_X, TREE_SCALE_Y

if platform.system() == "Darwin":
    import Quartz

ENV_PATH = os.path.join(os.getcwd(), ".env")

def get_real_display_resolution():
    if platform.system() == "Darwin":
        display = Quartz.CGMainDisplayID()
        return Quartz.CGDisplayPixelsWide(display), Quartz.CGDisplayPixelsHigh(display)
    else:
        import pyautogui
        return pyautogui.size()

def get_screenshot_resolution():
    img = ImageGrab.grab()
    return img.size  # (width, height)

def calculate_scaling():
    real_w, real_h = get_real_display_resolution()
    shot_w, shot_h = get_screenshot_resolution()
    scale_x = real_w / shot_w
    scale_y = real_h / shot_h
    return {
        "REAL_WIDTH": real_w,
        "REAL_HEIGHT": real_h,
        "SHOT_WIDTH": shot_w,
        "SHOT_HEIGHT": shot_h,
        "SCALE_X": scale_x,
        "SCALE_Y": scale_y
    }

def update_env_with_scaling():
    scaling = calculate_scaling()

    dotenv.load_dotenv(ENV_PATH)
    new_lines = []
    for k, v in scaling.items():
        new_lines.append(f"{k}={round(v, 6)}")

    with open(ENV_PATH, "r") as f:
        lines = f.readlines()

    # Overwrite or append new values
    existing_keys = [line.split("=")[0] for line in lines if "=" in line]
    for keyval in new_lines:
        key = keyval.split("=")[0]
        if key in existing_keys:
            lines = [kv if not kv.startswith(key + "=") else keyval + "\n" for kv in lines]
        else:
            lines.append(keyval + "\n")

    with open(ENV_PATH, "w") as f:
        f.writelines(lines)

    print("[✅] .env updated with screen scaling and resolution")
    return scaling
def load_scaling_from_env():
    return TREE_SCALE_X, TREE_SCALE_Y
