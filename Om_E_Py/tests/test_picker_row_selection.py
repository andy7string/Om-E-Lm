#!/usr/bin/env python3
"""
test_picker_row_selection.py

Test script to debug picker row selection issues.
Tests different methods of selecting row 5 in the Mail picker.

Usage:
    python tests/test_picker_row_selection.py
"""

import os
import sys

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from ome.utils.uiNav.navBigDaDDy import navBigDaDDy
import json

def test_picker_data():
    """Test loading and displaying picker data."""
    print("=== Testing Picker Data ===")
    
    nav = navBigDaDDy("com.apple.mail")
    picker_data = nav.get_picker_data()
    
    if not picker_data:
        print("❌ No picker data found")
        return False
    
    print(f"✅ Loaded {len(picker_data)} picker items")
    
    # Show row 5 specifically
    row_5 = None
    for item in picker_data:
        if item.get('row_index') == 5:
            row_5 = item
            break
    
    if row_5:
        print(f"\n🎯 Row 5 data:")
        print(f"   File: {row_5.get('file_name', 'No name')}")
        print(f"   Coordinates: {row_5.get('omeClick', 'No coordinates')}")
        print(f"   Class: {row_5.get('axtextfield_class', 'No class')}")
    else:
        print("❌ Row 5 not found in picker data")
        return False
    
    return True

def test_navbigdaddy_row_selection():
    """Test row selection using navBigDaDDy."""
    print("\n=== Testing navBigDaDDy Row Selection ===")
    
    nav = navBigDaDDy("com.apple.mail")
    
    print("🖱️ Attempting to select row 5 using navBigDaDDy...")
    success = nav.select_picker_row(5)
    
    if success:
        print("✅ navBigDaDDy row selection successful")
    else:
        print("❌ navBigDaDDy row selection failed")
    
    return success

def test_direct_coordinate_click():
    """Test clicking directly at the coordinates for row 5."""
    print("\n=== Testing Direct Coordinate Click ===")
    
    nav = navBigDaDDy("com.apple.mail")
    picker_data = nav.get_picker_data()
    
    # Find row 5 coordinates
    row_5_coords = None
    for item in picker_data:
        if item.get('row_index') == 5:
            row_5_coords = item.get('omeClick')
            break
    
    if not row_5_coords:
        print("❌ Could not find coordinates for row 5")
        return False
    
    print(f"🎯 Clicking directly at coordinates: {row_5_coords}")
    
    try:
        x, y = row_5_coords
        success = nav.click_at_coordinates(x, y, "row 5 direct click")
        
        if success:
            print("✅ Direct coordinate click successful")
        else:
            print("❌ Direct coordinate click failed")
        
        return success
    except Exception as e:
        print(f"❌ Error during direct coordinate click: {e}")
        return False

def test_apppicker_builder_direct():
    """Test using appPicker_builder directly."""
    print("\n=== Testing appPicker_builder Direct Selection ===")
    
    import subprocess
    
    print("🔧 Running appPicker_builder with --select-row-direct 5...")
    
    try:
        result = subprocess.run(
            ["python", "-m", "ome.utils.builder.app.appPicker_builder", 
             "--bundle", "com.apple.mail", "--select-row-direct", "5"],
            capture_output=True,
            text=True,
            cwd=project_root
        )
        
        print("📝 Command output:")
        print(result.stdout)
        
        if result.stderr:
            print("📝 Error output:")
            print(result.stderr)
        
        if result.returncode == 0:
            print("✅ appPicker_builder direct selection completed")
            return True
        else:
            print("❌ appPicker_builder direct selection failed")
            return False
            
    except Exception as e:
        print(f"❌ Error running appPicker_builder: {e}")
        return False

def test_apppicker_builder_click():
    """Test using appPicker_builder with click selection."""
    print("\n=== Testing appPicker_builder Click Selection ===")
    
    import subprocess
    
    print("🔧 Running appPicker_builder with --select-row 5...")
    
    try:
        result = subprocess.run(
            ["python", "-m", "ome.utils.builder.app.appPicker_builder", 
             "--bundle", "com.apple.mail", "--select-row", "5"],
            capture_output=True,
            text=True,
            cwd=project_root
        )
        
        print("📝 Command output:")
        print(result.stdout)
        
        if result.stderr:
            print("📝 Error output:")
            print(result.stderr)
        
        if result.returncode == 0:
            print("✅ appPicker_builder click selection completed")
            return True
        else:
            print("❌ appPicker_builder click selection failed")
            return False
            
    except Exception as e:
        print(f"❌ Error running appPicker_builder: {e}")
        return False

def main():
    """Run all picker row selection tests."""
    print("🚀 Starting Picker Row Selection Tests\n")
    
    try:
        # Test picker data
        data_ok = test_picker_data()
        
        if not data_ok:
            print("❌ Picker data test failed - stopping")
            return False
        
        # Test different selection methods
        print("\n" + "="*50)
        print("TESTING DIFFERENT SELECTION METHODS")
        print("="*50)
        
        # Method 1: navBigDaDDy
        nav_ok = test_navbigdaddy_row_selection()
        
        # Method 2: Direct coordinate click
        coord_ok = test_direct_coordinate_click()
        
        # Method 3: appPicker_builder direct
        builder_direct_ok = test_apppicker_builder_direct()
        
        # Method 4: appPicker_builder click
        builder_click_ok = test_apppicker_builder_click()
        
        print("\n📊 Test Summary:")
        print(f"  Picker data: {'✅' if data_ok else '❌'}")
        print(f"  navBigDaDDy selection: {'✅' if nav_ok else '❌'}")
        print(f"  Direct coordinate click: {'✅' if coord_ok else '❌'}")
        print(f"  appPicker_builder direct: {'✅' if builder_direct_ok else '❌'}")
        print(f"  appPicker_builder click: {'✅' if builder_click_ok else '❌'}")
        
        print("\n💡 Recommendations:")
        if not nav_ok:
            print("  - navBigDaDDy selection failed - check accessibility tree")
        if not coord_ok:
            print("  - Direct coordinate click failed - coordinates may be wrong")
        if not builder_direct_ok:
            print("  - appPicker_builder direct failed - accessibility API issue")
        if not builder_click_ok:
            print("  - appPicker_builder click failed - mouse click issue")
        
        print("\n✅ All tests completed!")
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 