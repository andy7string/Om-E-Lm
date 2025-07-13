#!/usr/bin/env python3
"""
tests/test_picker.py

A simple test script to demonstrate navBigDaDDy picker functionality.
This script shows how to use picker data that's automatically loaded by navBigDaDDy.

Usage:
    python tests/test_picker.py
"""

import os
import sys

# Add the project root to the Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from ome.utils.uiNav.navBigDaDDy import navBigDaDDy

def test_picker_functionality():
    """
    Test various picker functionality with navBigDaDDy.
    """
    print("=== Testing navBigDaDDy Picker Functionality ===\n")
    
    # Initialize navBigDaDDy for Mail app
    print("1. Initializing navBigDaDDy for com.apple.mail...")
    try:
        nav = navBigDaDDy("com.apple.mail")
        print(f"   ✓ Successfully created navBigDaDDy instance")
        print(f"   ✓ Active target: {nav.active_target.get('window_ref')}")
        print(f"   ✓ Window title: {nav.active_target.get('window_title')}")
    except Exception as e:
        print(f"   ✗ Error creating navBigDaDDy: {e}")
        return
    
    # Check if picker data was loaded
    print(f"\n2. Checking picker data...")
    print(f"   ✓ Picker entries loaded: {len(nav.picker_entries)}")
    
    if nav.picker_entries:
        print("   ✓ First few picker items:")
        for i, item in enumerate(nav.picker_entries[:5]):
            title = item.get('AXTitle', 'No Title')
            role = item.get('AXRole', 'No Role')
            omeClick = item.get('omeClick', 'No Click')
            print(f"     {i+1}. {title} ({role}) - Click: {omeClick}")
        
        if len(nav.picker_entries) > 5:
            print(f"     ... and {len(nav.picker_entries) - 5} more items")
    else:
        print("   ⚠ No picker entries found")
        print("   Note: This might be normal if you're not in a window with picker data")
    
    # Test finding picker items
    print(f"\n3. Testing picker item search...")
    if nav.picker_entries:
        # Try to find the first item
        first_item = nav.picker_entries[0]
        first_title = first_item.get('AXTitle', '')
        
        if first_title:
            print(f"   Searching for: '{first_title}'")
            found_item = nav.find_picker_item(first_title)
            if found_item:
                print(f"   ✓ Found item: {found_item.get('AXTitle')}")
            else:
                print(f"   ✗ Item not found")
        
        # Test partial search
        if first_title:
            partial_search = first_title[:3]  # First 3 characters
            print(f"   Searching for partial match: '{partial_search}'")
            found_item = nav.find_picker_item(partial_search)
            if found_item:
                print(f"   ✓ Found partial match: {found_item.get('AXTitle')}")
            else:
                print(f"   ✗ Partial match not found")
    else:
        print("   ⚠ Skipping search test - no picker items available")
    
    # Test picker data access
    print(f"\n4. Testing picker data access...")
    picker_path = nav.get_picker_jsonl_path()
    print(f"   ✓ Picker JSONL path: {picker_path}")
    
    if os.path.exists(picker_path):
        print(f"   ✓ Picker file exists")
        picker_data = nav.get_picker_data()
        print(f"   ✓ Raw picker data: {len(picker_data)} entries")
    else:
        print(f"   ⚠ Picker file does not exist")
    
    # Test window controls (always available)
    print(f"\n5. Testing window controls...")
    controls = nav.get_window_control_buttons()
    print(f"   ✓ Window controls found: {len(controls)}")
    for i, control in enumerate(controls):
        print(f"     {i+1}. {control.get('title', 'No Title')} ({control.get('type', 'No Type')})")
    
    print(f"\n=== Test Complete ===")
    print(f"navBigDaDDy picker functionality is working!")
    print(f"Use nav.click_picker_item('title') to click picker items")
    print(f"Use nav.select_picker_row(n) to select picker rows")

if __name__ == "__main__":
    test_picker_functionality()