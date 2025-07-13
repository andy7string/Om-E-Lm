import os
import time
import cv2
import numpy as np
import base64
from PIL import ImageGrab
import pyautogui
from openai import OpenAI
from dotenv import load_dotenv
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from Om_E_Tree.ome.utils.system.display import update_env_with_scaling, load_scaling_from_env, get_real_display_resolution

# === CONFIG ===
DOT_RADIUS = 6
DOT_COLOR = (0, 0, 255)  # Red
LABEL_COLOR = (0, 255, 255)
FONT = cv2.FONT_HERSHEY_SIMPLEX
FONT_SCALE = 0.5
FONT_THICKNESS = 1
SCREENSHOT_DIR = os.path.join("ome", "data", "screenshots")
os.makedirs(SCREENSHOT_DIR, exist_ok=True)

# === VARIANCE OFFSETS ===
offset_x =  7 # Adjust this if GPT is off horizontally
offset_y = -10  # Adjust this if GPT is off vertically

# === INIT OPENAI ===
load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def encode_image_to_base64(png_path):
    print(f"[🔁] Encoding screenshot to base64 for GPT input...")
    with open(png_path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")

def get_gpt_coords(prompt, base64_image):
    print(f"[📡] Sending prompt to ChatGPT:\n{prompt}")
    response = client.chat.completions.create(
        model="gpt-4.1-mini",
        messages=[
            {
                "role": "user",
                "content": [
                    { "type": "text", "text": prompt },
                    { "type": "image_url", "image_url": { "url": f"data:image/png;base64,{base64_image}" } }
                ]
            }
        ],
        max_tokens=1000
    )
    output = response.choices[0].message.content.strip()
    print(f"[📥] GPT-4.1-mini responded: {output}")
    return output

if __name__ == "__main__":
    print("[🔧] Updating .env with real and screenshot resolution scaling...")
    scaling = update_env_with_scaling()
    sx, sy = load_scaling_from_env()
    real_w, real_h = get_real_display_resolution()

    print(f"[🖥️] Real Display Resolution: {real_w}x{real_h}")
    print(f"[📸] Screenshot Resolution: {scaling['SHOT_WIDTH']}x{scaling['SHOT_HEIGHT']}")
    print(f"[📐] Scale Factors — X: {sx}, Y: {sy}")

    # Take screenshot
    screenshot = ImageGrab.grab()
    screen_np = np.array(screenshot)
    screen_bgr = cv2.cvtColor(screen_np, cv2.COLOR_RGB2BGR)
    height, width = screen_bgr.shape[:2]
    print(f"[📏] Image Shape: {width}x{height}")

    # === Draw 32-block grid (8x4) with dot + label at center of each block ===
    print("[🔴] Drawing 32-block grid with central dots and coordinates...")

    rows = 4
    cols = 8
    block_w = width // cols
    block_h = height // rows

    for r in range(rows):
        for c in range(cols):
            cx = (c * block_w) + block_w // 2
            cy = (r * block_h) + block_h // 2
            cv2.circle(screen_bgr, (cx, cy), DOT_RADIUS, DOT_COLOR, -1)
            cv2.putText(screen_bgr, f"({cx},{cy})", (cx + 8, cy - 8), FONT, FONT_SCALE, LABEL_COLOR, FONT_THICKNESS)

    # Save screenshot
    timestamp = str(int(time.time()))
    screenshot_path = os.path.join(SCREENSHOT_DIR, f"spotlight_grid_{timestamp}.png")
    cv2.imwrite(screenshot_path, screen_bgr)
    print(f"[💾] Screenshot with grid saved: {screenshot_path}")

    # Optional: click screen center
    center_x, center_y = width // 2, height // 2
    real_cx, real_cy = int(center_x * sx), int(center_y * sy)
    print(f"[🖱️] Clicking screen center: Logical ({center_x}, {center_y}) → Scaled ({real_cx}, {real_cy})")
    pyautogui.moveTo(real_cx, real_cy)
    pyautogui.rightClick()
    print("[🕹️] Dragging left 200px for visual cue...")
    pyautogui.moveTo(real_cx, real_cy, duration=0.5)
    pyautogui.dragRel(-200, 0, duration=1.5, button="left")

    # === GPT call
    base64_image = encode_image_to_base64(screenshot_path)
    prompt = (
        f"The image is a macOS screenshot with resolution {width}x{height}. "
        "32 red dots with (x, y) coordinate labels have been placed across the screen as reference points — evenly spaced in a grid. "
        "Find the Spotlight Search icon — a small circular white magnifying glass in the top-right of the menu bar. "
        "Return the (x, y) coordinates of the exact visual centre of the Spotlight icon, formatted exactly like this: (123, 456). "
        "Only respond with the coordinates."
    )

    gpt_response = get_gpt_coords(prompt, base64_image)

    # Parse GPT output and apply variance
    x_str, y_str = gpt_response.strip("()").split(",")
    gpt_x = int(x_str.strip()) + offset_x
    gpt_y = int(y_str.strip()) + offset_y

    scaled_x = int(gpt_x * sx)
    scaled_y = int(gpt_y * sy)
    print(f"[🎯] GPT returned: Logical ({gpt_x}, {gpt_y}) → Scaled ({scaled_x}, {scaled_y})")

    # Final click
    print("[🖱️] Moving to GPT coordinates and right-clicking...")
    pyautogui.moveTo(scaled_x, scaled_y)
    pyautogui.rightClick()
