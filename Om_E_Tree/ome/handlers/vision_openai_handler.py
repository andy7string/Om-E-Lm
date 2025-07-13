import openai
import base64
import os
from pathlib import Path
from dotenv import load_dotenv
from Om_E_Tree.ome.utils.system.display import load_scaling_from_env
from env import TREE_OPENAI_API_KEY

# ===========================
# 🔑 Auth & Client Setup
# ===========================

def get_openai_client():
    api_key = TREE_OPENAI_API_KEY

    if not api_key:
        raise ValueError("TREE_OPENAI_API_KEY not set in root .env file.")

    return openai.OpenAI(api_key=api_key)

# ===========================
# 🧠 Scaling Helper
# ===========================

def scale_coordinates(x, y):
    scale_x, scale_y = load_scaling_from_env()
    return int(x * scale_x), int(y * scale_y)


# ===========================
# 📤 Image Submission
# ===========================

def encode_image_base64(image_path):
    with open(image_path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")

def call_vision_api(image_path, prompt):
    if not image_path or not Path(image_path).exists():
        raise ValueError(f"Invalid or missing image path: {image_path}")

    base64_image = encode_image_base64(image_path)
    client = get_openai_client()

    response = client.chat.completions.create(
        model="gpt-4.1-mini",
        messages=[
            {
                "role": "user",
                "content": [
                    { "type": "text", "text": prompt },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/png;base64,{base64_image}"
                        }
                    }
                ]
            }
        ],
        max_tokens=1000
    )

    return response.choices[0].message.content

# ===========================
# 🎯 Action Functions
# ===========================

def describe_screen(args):
    try:
        return {
            "status": "success",
            "result": call_vision_api(args.get("image_path"), args.get("prompt"))
        }
    except Exception as e:
        return { "status": "failed", "error": str(e) }

def extract_text(args):
    try:
        return {
            "status": "success",
            "result": call_vision_api(args.get("image_path"), "Extract all visible text from this image.")
        }
    except Exception as e:
        return { "status": "failed", "error": str(e) }

def locate_button(args):
    try:
        label = args.get("button_label", "")
        raw = call_vision_api(args.get("image_path"), f"Return only the (x, y) coordinates of the button labeled '{label}'. No explanation.")
        # Attempt to parse coordinates
        if "(" in raw and "," in raw:
            x = int(raw.split("(")[1].split(",")[0].strip())
            y = int(raw.split(",")[1].split(")")[0].strip())
            x_scaled, y_scaled = scale_coordinates(x, y)
            return {
                "status": "success",
                "logical_coords": [x, y],
                "scaled_coords": [x_scaled, y_scaled],
                "raw": raw
            }
        return {
            "status": "partial",
            "raw": raw
        }
    except Exception as e:
        return { "status": "failed", "error": str(e) }

def summarise_ui_structure(args):
    try:
        return {
            "status": "success",
            "result": call_vision_api(args.get("image_path"), "Summarise the layout and structure of this UI.")
        }
    except Exception as e:
        return { "status": "failed", "error": str(e) }

def classify_screen_type(args):
    try:
        return {
            "status": "success",
            "result": call_vision_api(args.get("image_path"), "What kind of screen is this? (e.g., login, dashboard, error)")
        }
    except Exception as e:
        return { "status": "failed", "error": str(e) }

def find_text_location(args):
    try:
        text = args.get("text", "")
        raw = call_vision_api(args.get("image_path"), f"Return the (x, y) screen coordinates of the text: '{text}' only. No explanation.")
        if "(" in raw and "," in raw:
            x = int(raw.split("(")[1].split(",")[0].strip())
            y = int(raw.split(",")[1].split(")")[0].strip())
            x_scaled, y_scaled = scale_coordinates(x, y)
            return {
                "status": "success",
                "logical_coords": [x, y],
                "scaled_coords": [x_scaled, y_scaled],
                "raw": raw
            }
        return {
            "status": "partial",
            "raw": raw
        }
    except Exception as e:
        return { "status": "failed", "error": str(e) }

def interpret_chart_or_graph(args):
    try:
        return {
            "status": "success",
            "result": call_vision_api(args.get("image_path"), "Interpret this chart or graph. What is it showing?")
        }
    except Exception as e:
        return { "status": "failed", "error": str(e) }

def validate_visual_result(args):
    try:
        expected = args.get("expected_result", "")
        return {
            "status": "success",
            "result": call_vision_api(args.get("image_path"), f"Does the screen show the expected result: '{expected}'?")
        }
    except Exception as e:
        return { "status": "failed", "error": str(e) }
