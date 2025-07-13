# ome/ai.py

from ome.handlers import vision_openai_handler

result = vision_openai_handler.describe_screen({
    "image_path": "ome/data/screenshots/grid_test_1748938782.png",
    "prompt": """

📐 The screen has been divided into 32 blocks, labeled Q0 to Q31, arranged in 4 rows and 8 columns:
- Q0 is the top-left
- Q7 is the top-right
- Q8 starts the second row
- Q31 is bottom-right

Your task is to identify the exact sub-block that contains the BIN icon on the Mac, this is usually located at the end of the toolbar

✅ Before answering:
1. Double-check what the icon looks like and **where it normally appears**.
2. Look carefully at the **top-right area** of the screen.
3. Choose the block that **most closely** contains the icon.

"""
})

print("🧠 GPT-4 Vision Result:")
print(result)
