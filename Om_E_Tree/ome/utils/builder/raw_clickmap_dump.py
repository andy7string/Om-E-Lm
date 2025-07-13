import json
from ome.utils.clickmap_generator import AppClickmapGenerator
from pathlib import Path
import sys

# Usage: python raw_clickmap_dump.py Notes
if len(sys.argv) != 2:
    print("Usage: python raw_clickmap_dump.py <app_name>")
    sys.exit(1)

app_name = sys.argv[1]
out_path = Path(f"ome/data/clickmaps/{app_name}_raw_elements.json")

generator = AppClickmapGenerator(app_name)
if not generator.app_ref:
    print(f"❌ App not found: {app_name}")
    sys.exit(1)
print(f"✅ Connected to {generator.app_name}")

# Get all elements (no filtering/classification)
elements = generator.get_elements_for_labeling(0)
if not elements:
    print(f"❌ No elements found")
    sys.exit(1)

# Dump all raw elements to JSON
with open(out_path, 'w') as f:
    json.dump(elements, f, indent=2)
print(f"✅ Dumped {len(elements)} raw elements to {out_path}") 