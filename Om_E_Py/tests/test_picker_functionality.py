#!/usr/bin/env python3
"""
test_picker_functionality.py

Test script to demonstrate picker functionality in navBigDaDDy.
Shows how to load cached picker data and get fresh picker data.

Usage:
    python tests/test_picker_functionality.py
"""

import os
import sys

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from ome.utils.uiNav.navBigDaDDy import navBigDaDDy
import subprocess
import json

def test_cached_picker_data():
    """Test loading cached picker data from navBigDaDDy."""
    print("=== Testing Cached Picker Data ===")
    
    # Initialize navBigDaDDy for Mail app
    nav = navBigDaDDy("com.apple.mail")
    
    # Load picker data (this loads from cached JSONL files)
    picker_data = nav.get_picker_data()
    
    if picker_data:
        print(f"✅ Loaded {len(picker_data)} cached picker items")
        
        # Show first few items
        print("\n📋 Sample cached picker items:")
        for i, item in enumerate(picker_data[:5]):
            print(f"  {i+1}. {item.get('title', 'No title')} - {item.get('type', 'No type')}")
            if 'omeClick' in item:
                print(f"     Click at: {item['omeClick']}")
        
        if len(picker_data) > 5:
            print(f"  ... and {len(picker_data) - 5} more items")
    else:
        print("❌ No cached picker data found")
    
    return picker_data is not None

def test_fresh_picker_data():
    """Test getting fresh picker data by running the picker builder directly."""
    print("\n=== Testing Fresh Picker Data ===")
    
    # Path to the picker builder script
    picker_script = "ome/utils/builder/mail/appPicker_builder.py"
    
    if not os.path.exists(picker_script):
        print(f"❌ Picker builder script not found: {picker_script}")
        return False
    
    print(f"🔧 Running picker builder: {picker_script}")
    
    try:
        # Run the picker builder to get fresh data
        result = subprocess.run(
            ["python", picker_script],
            capture_output=True,
            text=True,
            cwd=project_root
        )
        
        if result.returncode == 0:
            print("✅ Picker builder completed successfully")
            print("📝 Output:")
            print(result.stdout)
        else:
            print("❌ Picker builder failed")
            print("📝 Error output:")
            print(result.stderr)
            return False
            
    except Exception as e:
        print(f"❌ Error running picker builder: {e}")
        return False
    
    return True

def test_picker_interaction():
    """Test picker interaction functionality."""
    print("\n=== Testing Picker Interaction ===")
    
    # Initialize navBigDaDDy
    nav = navBigDaDDy("com.apple.mail")
    
    # Load picker data
    picker_data = nav.get_picker_data()
    
    if not picker_data:
        print("❌ No picker data available for interaction test")
        return False
    
    # Find a picker item with omeClick coordinates
    clickable_item = None
    for item in picker_data:
        if 'omeClick' in item and item.get('type') == 'picker':
            clickable_item = item
            break
    
    if clickable_item:
        print(f"🎯 Found clickable picker item: {clickable_item.get('title')}")
        print(f"📍 Coordinates: {clickable_item['omeClick']}")
        
        # Note: We won't actually click here to avoid interfering with the UI
        print("💡 To test actual clicking, you would call:")
        print(f"   nav.click_at_coordinates({clickable_item['omeClick'][0]}, {clickable_item['omeClick'][1]}, 'picker test')")
        
        return True
    else:
        print("❌ No clickable picker items found")
        return False

def show_picker_data_structure():
    """Show the structure of picker data files."""
    print("\n=== Picker Data Structure ===")
    
    # Check for picker data files
    picker_dir = os.path.join(project_root, "ome", "data", "pickers")
    
    if os.path.exists(picker_dir):
        print(f"📁 Picker data directory: {picker_dir}")
        
        # List picker files
        picker_files = [f for f in os.listdir(picker_dir) if f.endswith('.jsonl')]
        
        if picker_files:
            print(f"📄 Found {len(picker_files)} picker data files:")
            for file in picker_files:
                file_path = os.path.join(picker_dir, file)
                file_size = os.path.getsize(file_path)
                print(f"  - {file} ({file_size} bytes)")
                
                # Show sample data from first file
                if file == picker_files[0]:
                    try:
                        with open(file_path, 'r') as f:
                            lines = f.readlines()
                            if lines:
                                sample = json.loads(lines[0])
                                print(f"    Sample item: {sample.get('title', 'No title')} - {sample.get('type', 'No type')}")
                    except Exception as e:
                        print(f"    Error reading sample: {e}")
        else:
            print("❌ No picker data files found")
    else:
        print(f"❌ Picker directory not found: {picker_dir}")

def main():
    """Run all picker tests."""
    print("🚀 Starting Picker Functionality Tests\n")
    
    try:
        # Show picker data structure
        show_picker_data_structure()
        
        # Test cached picker data
        cached_ok = test_cached_picker_data()
        
        # Test fresh picker data
        fresh_ok = test_fresh_picker_data()
        
        # Test picker interaction
        interaction_ok = test_picker_interaction()
        
        print("\n📊 Test Summary:")
        print(f"  Cached picker data: {'✅' if cached_ok else '❌'}")
        print(f"  Fresh picker data: {'✅' if fresh_ok else '❌'}")
        print(f"  Picker interaction: {'✅' if interaction_ok else '❌'}")
        
        print("\n✅ All picker tests completed!")
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 