#!/usr/bin/env python3

import sys
import os
import json
import time
import subprocess
sys.path.append(os.path.join(os.path.dirname(__file__), 'ome'))

from ome.utils.uiNav.navBigDaDDy import navBigDaDDy
from ome.utils.builder.app.app_focus import ensure_app_focus
from ome.utils.windows.winD_controller import get_active_target_and_windows
import Quartz

# Helper to type a string using Quartz events
def type_string_quartz(text):
    for char in text:
        keycode = char_to_keycode(char)
        if keycode is not None:
            # For uppercase, hold shift
            if char in SHIFT_CHARS:
                flags = Quartz.kCGEventFlagMaskShift
            else:
                flags = 0
            # Key down
            event_down = Quartz.CGEventCreateKeyboardEvent(None, keycode, True)
            Quartz.CGEventSetFlags(event_down, flags)
            Quartz.CGEventPost(Quartz.kCGHIDEventTap, event_down)
            # Key up
            event_up = Quartz.CGEventCreateKeyboardEvent(None, keycode, False)
            Quartz.CGEventSetFlags(event_up, flags)
            Quartz.CGEventPost(Quartz.kCGHIDEventTap, event_up)
            time.sleep(0.01)
        else:
            print(f"No keycode for char: {char}")

# Simple US keyboard mapping for letters
US_KEYCODES = {
    'a': 0, 'b': 11, 'c': 8, 'd': 2, 'e': 14, 'f': 3, 'g': 5, 'h': 4, 'i': 34, 'j': 38, 'k': 40, 'l': 37, 'm': 46, 'n': 45, 'o': 31, 'p': 35, 'q': 12, 'r': 15, 's': 1, 't': 17, 'u': 32, 'v': 9, 'w': 13, 'x': 7, 'y': 16, 'z': 6,
    'A': 0, 'B': 11, 'C': 8, 'D': 2, 'E': 14, 'F': 3, 'G': 5, 'H': 4, 'I': 34, 'J': 38, 'K': 40, 'L': 37, 'M': 46, 'N': 45, 'O': 31, 'P': 35, 'Q': 12, 'R': 15, 'S': 1, 'T': 17, 'U': 32, 'V': 9, 'W': 13, 'X': 7, 'Y': 16, 'Z': 6,
}
SHIFT_CHARS = set('ABCDEFGHIJKLMNOPQRSTUVWXYZ')

def char_to_keycode(char):
    return US_KEYCODES.get(char)

def clear_search_field():
    """Clear the search field using Cmd+A and Delete"""
    print("Clearing search field...")
    
    # Select all text (Cmd+A)
    cmd_a_event = Quartz.CGEventCreateKeyboardEvent(None, 0, True)  # 'a' key
    Quartz.CGEventSetFlags(cmd_a_event, Quartz.kCGEventFlagMaskCommand)
    Quartz.CGEventPost(Quartz.kCGHIDEventTap, cmd_a_event)
    
    cmd_a_event_up = Quartz.CGEventCreateKeyboardEvent(None, 0, False)  # 'a' key up
    Quartz.CGEventSetFlags(cmd_a_event_up, Quartz.kCGEventFlagMaskCommand)
    Quartz.CGEventPost(Quartz.kCGHIDEventTap, cmd_a_event_up)
    
    time.sleep(0.1)
    
    # Delete selected text
    delete_event = Quartz.CGEventCreateKeyboardEvent(None, 51, True)  # Delete key
    Quartz.CGEventPost(Quartz.kCGHIDEventTap, delete_event)
    
    delete_event_up = Quartz.CGEventCreateKeyboardEvent(None, 51, False)  # Delete key up
    Quartz.CGEventPost(Quartz.kCGHIDEventTap, delete_event_up)
    
    time.sleep(0.1)
    print("✅ Search field cleared")

def run_winD():
    """Run window detection and return the active target"""
    print("  🔍 Running window detection...")
    try:
        output = get_active_target_and_windows("com.apple.mail")
        active_target = output.get('active_target')
        windows = output.get('windows')
        print(f"  📋 Active target: {active_target}")
        return active_target, windows
    except Exception as e:
        print(f"  ❌ Error running winD: {e}")
        return None, None

def load_navigation_for_window(active_target):
    """Load navigation items for the current window reference"""
    if not active_target:
        return []
    
    nav_map_name = active_target.get('nav_map_name')
    if not nav_map_name:
        print(f"  ❌ No nav_map_name in active_target: {active_target}")
        return []
    
    nav_file = f"ome/data/navigation/{nav_map_name}"
    if not os.path.exists(nav_file):
        print(f"  ❌ Navigation file not found: {nav_file}")
        return []
    
    navigation_items = []
    try:
        with open(nav_file, 'r') as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                if line and not line.startswith('#'):
                    try:
                        item = json.loads(line)
                        # Only include mailbox navigation items (left sidebar)
                        if (item.get('AXRole') == 'AXRow' and 
                            item.get('omeClick') and 
                            len(item.get('omeClick', [])) == 2):
                            item['line_number'] = line_num
                            navigation_items.append(item)
                    except json.JSONDecodeError:
                        continue
        print(f"  ✅ Loaded {len(navigation_items)} navigation items from {nav_map_name}")
        return navigation_items
    except Exception as e:
        print(f"  ❌ Error loading navigation: {e}")
        return []

def click_navigation_item(nav, item, index, active_target):
    """Click a single navigation item and monitor window state"""
    title = item.get('AXTitle', f'Item {index}')
    omeClick = item.get('omeClick')
    
    if omeClick and len(omeClick) == 2:
        x, y = omeClick
        print(f"  {index:2d}. Clicking: {title} at ({x}, {y})")
        
        # Click the item
        nav.click_at_coordinates(x, y)
        time.sleep(0.5)
        
        # Run winD to check window state change
        new_active_target, new_windows = run_winD()
        
        # Check if window reference changed
        if new_active_target and active_target:
            old_ref = active_target.get('window_ref')
            new_ref = new_active_target.get('window_ref')
            if old_ref != new_ref:
                print(f"  🔄 Window reference changed: {old_ref} → {new_ref}")
                return new_active_target, True  # Indicate window changed
            else:
                print(f"  ✅ Window reference unchanged: {old_ref}")
                return new_active_target, False
        else:
            print(f"  ⚠️  Could not determine window state change")
            return new_active_target, False
        
        return True
    else:
        print(f"  {index:2d}. Skipping: {title} (no coordinates)")
        return active_target, False

def run_mail_automation():
    """Run the optimized mail automation after navigation testing"""
    print("\n" + "="*60)
    print("🚀 RUNNING MAIL AUTOMATION AFTER NAVIGATION TEST")
    print("="*60)
    
    # Focus Mail app once
    print("1. Focusing Mail app...")
    focus_result = ensure_app_focus("com.apple.mail", fullscreen=False)
    if focus_result.get('status') != 'success':
        print(f"Failed to focus Mail: {focus_result}")
        return
    print("✅ Mail app focused")
    
    # Run winD to get current state
    active_target, windows = run_winD()
    if not active_target:
        print("❌ Could not get active target")
        return
    
    # Click search field
    print("2. Clicking search field...")
    nav = navBigDaDDy("com.apple.mail")
    search_coords = [2385.5, 51.0]
    nav.click_at_coordinates(search_coords[0], search_coords[1])
    time.sleep(0.2)
    print("✅ Search field clicked")
    
    # Clear and type search term
    print("3. Clearing search field...")
    clear_search_field()
    
    print("4. Typing 'AliExpress'...")
    type_string_quartz("AliExpress")
    time.sleep(0.5)
    print("✅ Search term typed")
    
    # Test multiple row selections
    test_rows = [1, 5, 10, 15, 20]
    for row_num in test_rows:
        print(f"\n5.{test_rows.index(row_num)+1}. Selecting row {row_num}...")
        try:
            cmd = [
                sys.executable,
                "-m", "ome.utils.builder.mail.mailMessageList_controller",
                "--row", str(row_num),
                "--no-focus"
            ]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            if result.returncode == 0:
                print(f"✅ Row {row_num} selected successfully")
            else:
                print(f"❌ Error selecting row {row_num}: {result.stderr.strip()}")
        except Exception as e:
            print(f"❌ Exception selecting row {row_num}: {e}")
        
        # Pause between row selections
        time.sleep(2)
    
    print("🎉 MAIL AUTOMATION COMPLETE!")

def test_mailbox_navigation():
    """Test mailbox navigation with window state monitoring"""
    print("🔥 MAILBOX NAVIGATION TEST (With Window State Monitoring)")
    print("="*60)
    
    # Step 1: Focus Mail app once
    print("1. Focusing Mail app...")
    focus_result = ensure_app_focus("com.apple.mail", fullscreen=False)
    if focus_result.get('status') != 'success':
        print(f"❌ Failed to focus Mail: {focus_result}")
        return
    print("✅ Mail app focused")
    
    # Step 2: Initial window detection
    print("2. Initial window detection...")
    active_target, windows = run_winD()
    if not active_target:
        print("❌ Could not get initial active target")
        return
    
    # Step 3: Initialize navBigDaDDy
    print("3. Initializing navigation controller...")
    nav = navBigDaDDy("com.apple.mail")
    print("✅ Navigation controller ready")
    
    # Step 4: Click through mailbox navigation items with window monitoring
    print("4. Testing mailbox navigation with window state monitoring...")
    print("-" * 60)
    
    successful_clicks = 0
    window_changes = 0
    current_active_target = active_target
    
    # Load initial navigation items
    navigation_items = load_navigation_for_window(current_active_target)
    if not navigation_items:
        print("❌ No navigation items found for initial window")
        return
    
    total_items = len(navigation_items)
    item_index = 0
    
    while item_index < total_items:
        item = navigation_items[item_index]
        
        try:
            # Click the item and check for window changes
            new_active_target, window_changed = click_navigation_item(nav, item, item_index + 1, current_active_target)
            
            if new_active_target:
                current_active_target = new_active_target
                successful_clicks += 1
                
                if window_changed:
                    window_changes += 1
                    print(f"  🔄 Loading new navigation map for window: {current_active_target.get('window_ref')}")
                    
                    # Load navigation items for the new window
                    new_navigation_items = load_navigation_for_window(current_active_target)
                    if new_navigation_items:
                        navigation_items = new_navigation_items
                        total_items = len(navigation_items)
                        item_index = 0  # Start over with new navigation items
                        print(f"  ✅ Loaded {total_items} new navigation items")
                        continue  # Skip the increment to start from beginning
                    else:
                        print(f"  ⚠️  No navigation items found for new window, continuing...")
            
        except Exception as e:
            print(f"  {item_index + 1:2d}. ❌ Error clicking {item.get('AXTitle', 'Unknown')}: {e}")
        
        item_index += 1
        
        # Progress indicator every 5 items
        if item_index % 5 == 0:
            print(f"    Progress: {item_index}/{total_items} mailboxes clicked")
        
        # Add a small delay between clicks
        time.sleep(0.3)
    
    print("-" * 60)
    print(f"✅ Mailbox navigation test complete!")
    print(f"   Successfully clicked: {successful_clicks} mailboxes")
    print(f"   Window changes detected: {window_changes}")
    print(f"   Final window reference: {current_active_target.get('window_ref') if current_active_target else 'Unknown'}")
    
    # Step 5: Run the mail automation with multiple row tests
    run_mail_automation()

if __name__ == "__main__":
    test_mailbox_navigation() 