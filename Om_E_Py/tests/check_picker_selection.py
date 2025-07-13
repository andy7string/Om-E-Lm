#!/usr/bin/env python3
"""
check_picker_selection.py

Quick script to check the current selection state in the picker.
"""

import os
import sys
import json

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

def check_picker_selection():
    """Check which row is currently selected in the picker."""
    picker_path = os.path.join(project_root, "ome", "data", "pickers", "picker_com.apple.mail.jsonl")
    
    if not os.path.exists(picker_path):
        print("❌ Picker file not found")
        return
    
    print("=== Current Picker Selection State ===")
    
    with open(picker_path, 'r') as f:
        for line_num, line in enumerate(f, 1):
            try:
                item = json.loads(line.strip())
                row_index = item.get('row_index')
                file_name = item.get('file_name', 'No name')
                selected = item.get('selected', False)
                
                if selected:
                    print(f"✅ Row {row_index}: {file_name} - SELECTED")
                else:
                    print(f"   Row {row_index}: {file_name}")
                    
            except json.JSONDecodeError:
                continue
    
    print("\n💡 If no row shows as SELECTED, try running the selection test again.")

if __name__ == "__main__":
    check_picker_selection() 