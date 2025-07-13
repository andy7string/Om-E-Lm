import os
import time
import base64
from openai import OpenAI
from PIL import ImageGrab
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from Om_E_Tree.ome.utils.system.display import update_env_with_scaling, load_scaling_from_env, calculate_scaling
import pyautogui
import re

# === CONFIG ===
SCREENSHOT_DIR = os.path.join("ome", "data", "screenshots")
os.makedirs(SCREENSHOT_DIR, exist_ok=True)
client = OpenAI()

# === FUNCTIONS ===
def encode_image(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode("utf-8")

def extract_coordinates(response_text):
    match = re.search(r"\((\d+),\s*(\d+)\)", response_text)
    if match:
        return int(match.group(1)), int(match.group(2))
    return None

# === MAIN ===
if __name__ == "__main__":
    scaling = update_env_with_scaling()
    print("[🧾] Resolution + Scaling Info:")
    for k, v in calculate_scaling().items():
        print(f"  {k}: {v}")

    timestamp = str(int(time.time()))
    screenshot = ImageGrab.grab()
    img_path = os.path.join(SCREENSHOT_DIR, f"click_target_{timestamp}.png")
    screenshot.save(img_path)
    print(f"[📸] Saved screenshot: {img_path}")

    image_b64 = encode_image(img_path)
    width, height = screenshot.size

    prompt = (
        f"The image is a macOS screenshot with resolution {width}x{height}. "
    "Find the Help menu item — it is white text that says 'Help', located in the top menu bar near the top-right of the screen.\n"
    "Return only the (x, y) screen coordinates of the centre of the word 'Help', formatted exactly like this: (123, 45)\n"
    "Do not include any explanation or extra words. Just respond with the coordinates."
)

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:image/png;base64,{image_b64}"}
                    }
                ]
            }
        ],
        max_tokens=50
    )

    reply = response.choices[0].message.content.strip()
    print(f"🔍 GPT-4o Response: {reply}")

    coords = extract_coordinates(reply)
    if coords:
        sx, sy = load_scaling_from_env()
        scaled_x, scaled_y = int(coords[0] * sx), int(coords[1] * sy)
        print(f"[🧠] First click at scaled: ({scaled_x}, {scaled_y})")
        pyautogui.moveTo(scaled_x, scaled_y)
        pyautogui.rightClick()
        print("[⏳] Waiting 5 seconds before second click...")
        time.sleep(5)
        pyautogui.rightClick()
        print("[✅] Second click done.")
    else:
        print("❌ Failed to parse coordinates.")
