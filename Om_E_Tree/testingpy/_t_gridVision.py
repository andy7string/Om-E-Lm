import cv2
import numpy as np
from PIL import ImageGrab
import pyautogui
import os
import time
from dotenv import load_dotenv
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from Om_E_Tree.ome.utils.system.display import update_env_with_scaling, load_scaling_from_env

# === CONFIG ===
GRID_BLOCKS = 32
SUBGRID_ROWS = 8
SUBGRID_COLS = 8

# Main Grid Style
GRID_COLOR = (57, 255, 20)
GRID_THICKNESS = 5
DOT_COLOR = (0, 0, 255)
DOT_RADIUS = 10

# Subgrid Style
SUBGRID_THICKNESS = 2
SUBGRID_DOT_RADIUS = 6

# Labels
DRAW_LABELS = True
LABEL_COLOR = (255, 255, 255)
FONT = cv2.FONT_HERSHEY_SIMPLEX
FONT_SCALE = 1
FONT_THICKNESS = 2
SUBFONT_SCALE = 0.7
SUBFONT_THICKNESS = 1

# Output folder
SCREENSHOT_DIR = os.path.join("ome", "data", "screenshots")
os.makedirs(SCREENSHOT_DIR, exist_ok=True)

# === GRID UTILS ===
def draw_grid(image, rows, cols, prefix="Q", draw_labels=True, thickness=GRID_THICKNESS, dot_radius=DOT_RADIUS,
              font_scale=FONT_SCALE, font_thickness=FONT_THICKNESS):
    h, w = image.shape[:2]
    block_w = w // cols
    block_h = h // rows
    blocks = []

    for r in range(rows):
        for c in range(cols):
            idx = r * cols + c
            x = c * block_w
            y = r * block_h
            cv2.rectangle(image, (x, y), (x + block_w, y + block_h), GRID_COLOR, thickness)
            if draw_labels:
                text = f"{prefix}{idx}"
                text_size, _ = cv2.getTextSize(text, FONT, font_scale, font_thickness)
                text_x = x + block_w - text_size[0] - 6
                text_y = y + block_h - 6
                cv2.putText(image, text, (text_x, text_y), FONT, font_scale, LABEL_COLOR, font_thickness)
            blocks.append(((x, y), (x + block_w, y + block_h)))

    for r in range(rows + 1):
        for c in range(cols + 1):
            cx = c * block_w
            cy = r * block_h
            cv2.circle(image, (cx, cy), dot_radius, DOT_COLOR, -1)

    return image, blocks


def get_center(coords):
    (x1, y1), (x2, y2) = coords
    return (x1 + x2) // 2, (y1 + y2) // 2

def scale_coords(x, y):
    sx, sy = load_scaling_from_env()
    return int(x * sx), int(y * sy)

# === MAIN ===
if __name__ == "__main__":
    update_env_with_scaling()
    timestamp = str(int(time.time()))
    screenshot = ImageGrab.grab()
    screen_np = np.array(screenshot)
    screen_bgr = cv2.cvtColor(screen_np, cv2.COLOR_RGB2BGR)

    # === Layer 1: Main Grid ===
    grid_img, grid_blocks = draw_grid(
        screen_bgr.copy(),
        rows=4,
        cols=8,
        prefix="Q",
        draw_labels=DRAW_LABELS,
        thickness=GRID_THICKNESS,
        dot_radius=DOT_RADIUS,
        font_scale=FONT_SCALE,
        font_thickness=FONT_THICKNESS
    )
    grid_path = os.path.join(SCREENSHOT_DIR, f"grid_test_{timestamp}.png")
    cv2.imwrite(grid_path, grid_img)
    print(f"[💾] Saved main grid: {grid_path}")

    selected = input("Select block (Q0–Q31): ").strip().lower()
    if not selected.startswith("q") or not selected[1:].isdigit():
        print("❌ Invalid selection.")
        exit()
    block_idx = int(selected[1:])
    if block_idx < 0 or block_idx >= len(grid_blocks):
        print("❌ Out of range.")
        exit()

    (x1, y1), (x2, y2) = grid_blocks[block_idx]
    cropped = screen_bgr[y1:y2, x1:x2]

    # === Layer 2: Subgrid ===
    sub_img, sub_blocks = draw_grid(
        cropped.copy(),
        rows=SUBGRID_ROWS,
        cols=SUBGRID_COLS,
        prefix="Q",
        draw_labels=DRAW_LABELS,
        thickness=SUBGRID_THICKNESS,
        dot_radius=SUBGRID_DOT_RADIUS,
        font_scale=SUBFONT_SCALE,
        font_thickness=SUBFONT_THICKNESS
    )
    sub_path = os.path.join(SCREENSHOT_DIR, f"subgrid_test_{timestamp}.png")
    cv2.imwrite(sub_path, sub_img)
    print(f"[💾] Saved subgrid: {sub_path}")

    sub = input("Select sub-block (Q0–Q63): ").strip().lower()
    if not sub.startswith("q") or not sub[1:].isdigit():
        print("❌ Invalid sub-selection.")
        exit()
    sub_idx = int(sub[1:])
    if sub_idx < 0 or sub_idx >= len(sub_blocks):
        print("❌ Sub-block out of range.")
        exit()

    local_cx, local_cy = get_center(sub_blocks[sub_idx])
    global_cx = x1 + local_cx
    global_cy = y1 + local_cy
    sx, sy = scale_coords(global_cx, global_cy)

    print(f"[🧠] Right click → Logical: ({global_cx}, {global_cy}) → Scaled: ({sx}, {sy})")
    pyautogui.moveTo(sx, sy)
    pyautogui.rightClick()
