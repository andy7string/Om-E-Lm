#!/usr/bin/env python3
"""
test_picker_visual_selection.py

Test script to visually demonstrate picker row selection.
Includes pauses and clear feedback so you can see the selection happening.

Usage:
    python tests/test_picker_visual_selection.py
"""

import os
import sys
import time

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from ome.utils.uiNav.navBigDaDDy import navBigDaDDy

def test_visual_row_selection():
    """Test row selection with visual feedback and pauses."""
    print("=== Visual Picker Row Selection Test ===")
    print("This test will help you see the row selection happening.")
    print("Make sure the Mail picker window is visible and in focus.\n")
    
    nav = navBigDaDDy("com.apple.mail")
    picker_data = nav.get_picker_data()
    
    if not picker_data:
        print("❌ No picker data found")
        return False
    
    print(f"✅ Loaded {len(picker_data)} picker items")
    
    # Find row 5
    row_5 = None
    for item in picker_data:
        if item.get('row_index') == 5:
            row_5 = item
            break
    
    if not row_5:
        print("❌ Row 5 not found in picker data")
        return False
    
    print(f"\n🎯 Row 5 details:")
    print(f"   File: {row_5.get('file_name', 'No name')}")
    print(f"   Coordinates: {row_5.get('omeClick', 'No coordinates')}")
    
    print(f"\n⏳ Starting visual selection test in 3 seconds...")
    print("   Please make sure the Mail picker window is visible!")
    time.sleep(3)
    
    print(f"\n🖱️ Step 1: Clicking directly at row 5 coordinates...")
    x, y = row_5['omeClick']
    success = nav.click_at_coordinates(x, y, "row 5 visual test")
    
    if success:
        print("✅ Click successful!")
    else:
        print("❌ Click failed!")
    
    print(f"\n⏳ Waiting 2 seconds to see the result...")
    time.sleep(2)
    
    print(f"\n🔧 Step 2: Using direct accessibility selection...")
    success = nav.select_picker_row(5)
    
    if success:
        print("✅ Direct selection successful!")
    else:
        print("❌ Direct selection failed!")
    
    print(f"\n⏳ Waiting 2 seconds to see the result...")
    time.sleep(2)
    
    print(f"\n🎯 Step 3: Clicking again to confirm...")
    success = nav.click_at_coordinates(x, y, "row 5 final test")
    
    if success:
        print("✅ Final click successful!")
    else:
        print("❌ Final click failed!")
    
    print(f"\n✅ Visual selection test completed!")
    print("   Did you see row 5 being selected in the picker?")
    
    return True

def test_multiple_rows():
    """Test selecting multiple rows to see the difference."""
    print("\n=== Multiple Row Selection Test ===")
    print("This will select different rows so you can see the selection changing.\n")
    
    nav = navBigDaDDy("com.apple.mail")
    
    test_rows = [1, 5, 10, 15]
    
    for row_index in test_rows:
        print(f"\n🎯 Selecting row {row_index}...")
        success = nav.select_picker_row(row_index)
        
        if success:
            print(f"✅ Row {row_index} selected successfully!")
        else:
            print(f"❌ Failed to select row {row_index}")
        
        print(f"⏳ Waiting 3 seconds...")
        time.sleep(3)
    
    print(f"\n✅ Multiple row selection test completed!")
    print("   Did you see the selection moving between different rows?")

def main():
    """Run the visual selection tests."""
    print("🚀 Starting Visual Picker Selection Tests\n")
    
    try:
        # Test visual row selection
        visual_ok = test_visual_row_selection()
        
        if visual_ok:
            # Test multiple rows
            test_multiple_rows()
        
        print("\n✅ All visual tests completed!")
        print("\n💡 If you didn't see the selection happening:")
        print("   - Make sure the Mail picker window is visible and in focus")
        print("   - Check that row 5 is actually visible in the picker")
        print("   - Try running the test again")
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 