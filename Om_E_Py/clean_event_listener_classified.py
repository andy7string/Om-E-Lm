#!/usr/bin/env python3
"""
ome/clean_event_listener_classified.py

This script monitors a macOS application for new window creation events using
polling, and classifies windows using logic from winD_controller.py.

Main Purpose:
- Monitors a macOS app (using bundle ID from BundleIDController or command line) for window creation/change events.
- Dynamically switches between apps based on changes to active_target_Bundle_ID.json.
- Classifies window types (FilePicker, messageViewer, sheets, dialogs, etc.).
- Tracks the active target window/sheet for UI automation.
- Provides real-time window detection with mouse-based exit mechanism.
- Exports window state to JSONL for consumption by navigation controllers.
- Handles app refresh requests and error recovery automatically.

Key Features:
- Dynamic App Switching: Automatically switches between apps based on active_target_Bundle_ID.json changes.
- Window Detection: Real-time polling to detect new windows, sheets, and dialogs.
- Window Classification: Identifies window types using AXIdentifier and other attributes.
- Active Target Tracking: Determines which window/sheet should be the navigation target.
- Mouse Corner Exit: Move mouse to top-right corner to gracefully exit.
- Bundle ID Support: Works with any macOS app that supports accessibility.
- Clean Shutdown: Graceful error handling and resource cleanup.
- Refresh Handling: Automatically handles refresh requests when apps quit and relaunch.

How to Use (Command Line):
    python clean_event_listener_classified.py [bundle_id_or_app_name]
    python -m clean_event_listener_classified [bundle_id_or_app_name]

Arguments:
    [bundle_id_or_app_name]: Optional. The bundle ID of the app (e.g., com.apple.mail) or app name (e.g., Mail)
                             If not provided, will use the active bundle ID from BundleIDController

Examples:
    # Monitor using active bundle ID from BundleIDController
    python clean_event_listener_classified.py
    
    # Monitor Safari by bundle ID
    python clean_event_listener_classified.py com.apple.Safari
    
    # Monitor Finder by app name (with fuzzy matching)
    python clean_event_listener_classified.py Finder
    
    # Module usage (can be run from anywhere)
    python -m clean_event_listener_classified Notes
    
    # Set active bundle ID first, then monitor
    python -m ome.controllers.bundles.bundleID_controller --set "Safari"
    python clean_event_listener_classified.py

Output:
- Window state JSONL file: ome/data/windows/win_<bundle_id>.jsonl
- Contains the active target window/sheet information
- Updated in real-time as windows change
- Format: {"active_target": {"type": "window|sheet|float", "window_title": "...", "window_ref": "...", "nav_map_name": "...", "timestamp": "..."}}

When to Use:
- To monitor window events for UI automation
- To track which window/sheet is currently active for navigation
- To detect file pickers, dialogs, and other transient UI elements
- For building adaptive UI automation that responds to window changes
- When you need to dynamically switch between different apps based on user activity
- For coordinating window monitoring across multiple applications in a navigation system

Dependencies:
    - macOS Accessibility API
    - PyObjC (Quartz, AppKit)
    - ome package (local accessibility utilities)

Author: AI Assistant
Date: 2024
"""

import time
import sys
import os
import signal
import threading
import argparse
import json
from datetime import datetime

# Add ome to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'ome'))

from ome.AXClasses import NativeUIElement
from ome.utils.builder.app.app_focus import ensure_app_focus
from ome.utils.builder.app.appList_controller import bundle_id_exists, get_bundle_id
from ome.controllers.bundles.bundleID_controller import BundleIDController

class MouseExitMonitor:
    def __init__(self, corner_size=50):
        self.corner_size = corner_size
        self.is_running = False
        import Quartz
        self.screen_width = Quartz.CGDisplayPixelsWide(Quartz.CGMainDisplayID())
        self.screen_height = Quartz.CGDisplayPixelsHigh(Quartz.CGMainDisplayID())
        print(f"Exit corner: top-right {corner_size}x{corner_size} pixels")
    def _get_mouse_position(self):
        import AppKit
        import Quartz
        loc = AppKit.NSEvent.mouseLocation()
        x = int(loc.x)
        y = int(Quartz.CGDisplayPixelsHigh(Quartz.CGMainDisplayID()) - loc.y)
        return (x, y)
    def _is_in_corner(self, x, y):
        return (x >= self.screen_width - self.corner_size and y <= self.corner_size)
    def _monitor(self):
        while self.is_running:
            try:
                pos = self._get_mouse_position()
                if self._is_in_corner(pos[0], pos[1]):
                    print(f"Mouse in corner! Exiting...")
                    os.kill(os.getpid(), signal.SIGINT)
                    break
                time.sleep(0.1)
            except Exception as e:
                print(f"Mouse monitor error: {e}")
                break
    def start(self):
        self.is_running = True
        self.monitor_thread = threading.Thread(target=self._monitor, daemon=True)
        self.monitor_thread.start()
        print("Mouse exit monitor started")
    def stop(self):
        self.is_running = False

def get_attr_safe(obj, attr):
    try:
        return getattr(obj, attr, None)
    except Exception:
        return None

def get_window_type_or_identifier(window_or_sheet):
    if isinstance(window_or_sheet, dict):
        ax_identifier = window_or_sheet.get('AXIdentifier')
    else:
        ax_identifier = get_attr_safe(window_or_sheet, 'AXIdentifier')
    if ax_identifier == "open-panel":
        return "FilePicker"
    if ax_identifier and "messageViewer" in ax_identifier:
        return ax_identifier
    if ax_identifier == "Mail.sendMessageAlert":
        return "SendMessageAlert"
    if ax_identifier:
        return ax_identifier
    return None

def is_window_active(win, sheets):
    if get_attr_safe(win, 'AXFocused') or get_attr_safe(win, 'AXMain'):
        return True
    for sheet in sheets:
        if sheet.get('is_active'):
            return True
    return False

def scan_sheet(sheet, parent_window_number, sheet_index):
    ax_identifier = get_attr_safe(sheet, 'AXIdentifier')
    detected_type = get_window_type_or_identifier(sheet)
    result = {
        'sheet_index': sheet_index,
        'AXTitle': get_attr_safe(sheet, 'AXTitle'),
        'AXIdentifier': ax_identifier,
        'AXRole': get_attr_safe(sheet, 'AXRole'),
        'AXRoleDescription': get_attr_safe(sheet, 'AXRoleDescription'),
        'AXSubrole': get_attr_safe(sheet, 'AXSubrole'),
        'AXMain': get_attr_safe(sheet, 'AXMain'),
        'AXFocused': get_attr_safe(sheet, 'AXFocused'),
        'AXModal': get_attr_safe(sheet, 'AXModal'),
        'is_active': bool(get_attr_safe(sheet, 'AXFocused') or get_attr_safe(sheet, 'AXModal')),
        'AXSize': list(get_attr_safe(sheet, 'AXSize')) if get_attr_safe(sheet, 'AXSize') else None,
        'timestamp': datetime.utcnow().isoformat() + 'Z',
        'parent_window_number': parent_window_number,
        'window_type': detected_type
    }
    return result

def scan_window(win, window_number):
    ax_identifier = get_attr_safe(win, 'AXIdentifier')
    detected_type = get_window_type_or_identifier(win)
    sheets = []
    children = get_attr_safe(win, 'AXChildren') or []
    for idx, child in enumerate(children):
        if get_attr_safe(child, 'AXRole') in ('AXSheet', 'AXDialog'):
            sheets.append(scan_sheet(child, window_number, idx))
    info = {
        'window_number': window_number,
        'AXTitle': get_attr_safe(win, 'AXTitle'),
        'AXIdentifier': ax_identifier,
        'AXRole': get_attr_safe(win, 'AXRole'),
        'AXRoleDescription': get_attr_safe(win, 'AXRoleDescription'),
        'AXSubrole': get_attr_safe(win, 'AXSubrole'),
        'AXMain': get_attr_safe(win, 'AXMain'),
        'AXFocused': get_attr_safe(win, 'AXFocused'),
        'AXModal': get_attr_safe(win, 'AXModal'),
        'is_active': is_window_active(win, sheets),
        'AXSize': list(get_attr_safe(win, 'AXSize')) if get_attr_safe(win, 'AXSize') else None,
        'timestamp': datetime.utcnow().isoformat() + 'Z',
        'sheets': sheets,
        'window_type': detected_type
    }
    return info

def get_window_info(window):
    try:
        title = getattr(window, 'AXTitle', 'Unknown')
        role = getattr(window, 'AXRole', 'Unknown')
        window_type = get_window_type_or_identifier(window)
        try:
            position = getattr(window, 'AXPosition', None)
            size = getattr(window, 'AXSize', None)
            if position and size:
                type_info = f" [{window_type}]" if window_type else ""
                return f"{title} ({role}){type_info} at {position} size {size}"
        except:
            pass
        type_info = f" [{window_type}]" if window_type else ""
        return f"{title} ({role}){type_info}"
    except Exception as e:
        return f"Unknown window (error: {e})"

def get_window_signature(window):
    try:
        title = getattr(window, 'AXTitle', 'Unknown')
        role = getattr(window, 'AXRole', 'Unknown')
        window_type = get_window_type_or_identifier(window)
        try:
            position = getattr(window, 'AXPosition', None)
            size = getattr(window, 'AXSize', None)
            if position and size:
                return f"{title}|{role}|{window_type}|{position}|{size}"
        except:
            pass
        return f"{title}|{role}|{window_type}"
    except Exception as e:
        return f"unknown|{e}"

def format_window_detection(window_info):
    title = window_info.get('AXTitle', 'Unknown')
    role = window_info.get('AXRole', 'Unknown')
    window_type = window_info.get('window_type', 'Unknown')
    identifier = window_info.get('AXIdentifier', 'None')
    is_active = window_info.get('is_active', False)
    sheets = window_info.get('sheets', [])
    parts = [f"NEW WINDOW: {title}"]
    if window_type and window_type != 'Unknown':
        parts.append(f"Type: {window_type}")
    if identifier and identifier != 'None':
        parts.append(f"ID: {identifier}")
    parts.append(f"Role: {role}")
    if is_active:
        parts.append("ACTIVE")
    if sheets:
        parts.append(f"Sheets: {len(sheets)}")
    return " | ".join(parts)

def get_active_target(windows, bundle_id):
    def get_title_for_window(win):
        title = win.get('AXTitle')
        return title or 'Unknown'

    # 1. If an active window has any sheets, pick the last one as the active target
    for win in windows:
        if win['is_active'] and win.get('sheets'):
            sheet = win['sheets'][-1]
            parent_title = get_title_for_window(win)
            window_ref = get_window_type_or_identifier(sheet)
            if not window_ref:
                window_ref = get_title_for_window(sheet).replace(' ', '_')[:32]
            nav_map_name = f"appNav_{bundle_id}_{window_ref}.jsonl"
            return {
                "type": "sheet",
                "window_title": parent_title,
                "window_ref": window_ref,
                "nav_map_name": nav_map_name,
                "timestamp": sheet.get('timestamp')
            }
    # 2. Check for floating window
    for win in windows:
        if win.get('AXSubrole') == 'AXFloatingWindow':
            title = get_title_for_window(win)
            window_ref = get_window_type_or_identifier(win)
            if not window_ref:
                window_ref = title.replace(' ', '_')[:32]
            nav_map_name = f"appNav_{bundle_id}_{window_ref}.jsonl"
            return {
                "type": "float",
                "window_title": title,
                "window_ref": window_ref,
                "nav_map_name": nav_map_name,
                "timestamp": win.get('timestamp')
            }
    # 3. Fallback: active window
    for win in windows:
        if win['is_active']:
            title = get_title_for_window(win)
            window_ref = get_window_type_or_identifier(win)
            if not window_ref:
                window_ref = title.replace(' ', '_')[:32]
            nav_map_name = f"appNav_{bundle_id}_{window_ref}.jsonl"
            return {
                "type": "window",
                "window_title": title,
                "window_ref": window_ref,
                "nav_map_name": nav_map_name,
                "timestamp": win.get('timestamp')
            }
    return None

def main():
    parser = argparse.ArgumentParser(description="Monitor a macOS app for window events and classify windows.")
    parser.add_argument("bundle_id", nargs='?', default=None,
                        help="The bundle ID of the app (e.g., com.apple.mail) or app name (e.g., Mail). If not provided, will use active bundle ID from BundleIDController.")
    args = parser.parse_args()

    # Initialize BundleIDController for dynamic app switching
    bundle_controller = BundleIDController()
    
    # Determine initial bundle ID
    if args.bundle_id:
        # User provided a bundle ID or app name
        input_id = args.bundle_id
        
        # Resolve bundle ID (following appMenu_builder.py pattern)
        canonical_bundle_id = bundle_id_exists(input_id)
        if not canonical_bundle_id:
            # Try to resolve as app name
            possible_bundle_id = get_bundle_id(input_id)
            if possible_bundle_id:
                canonical_bundle_id = bundle_id_exists(possible_bundle_id)
                if canonical_bundle_id:
                    print(f"[INFO] Resolved app name '{input_id}' to bundle ID '{canonical_bundle_id}'.")
                else:
                    print(f"[ERROR] '{input_id}' is neither a valid bundle ID nor a known app name.")
                    sys.exit(1)
            else:
                print(f"[ERROR] '{input_id}' is neither a valid bundle ID nor a known app name.")
                sys.exit(1)
        
        if canonical_bundle_id != input_id:
            print(f"[INFO] Using closest matching bundle ID: '{canonical_bundle_id}' (input was '{input_id}')")
        
        bundle_id = canonical_bundle_id
        
        # Set this as the active bundle ID
        bundle_controller.set_active_bundle_id(bundle_id, "event_listener")
        print(f"[INFO] Set active bundle ID to: {bundle_id}")
    else:
        # No bundle ID provided, use the active one from BundleIDController
        bundle_id = bundle_controller.get_active_bundle_id()
        if not bundle_id:
            print("[ERROR] No active bundle ID found in BundleIDController. Please set one first or provide a bundle ID argument.")
            print("[INFO] You can set the active bundle ID using:")
            print("    python -m ome.controllers.bundles.bundleID_controller --set 'Mail'")
            sys.exit(1)
        
        app_name = bundle_controller.get_app_name_for_bundle_id(bundle_id)
        print(f"[INFO] Using active bundle ID from BundleIDController: {bundle_id}")
        if app_name:
            print(f"[INFO] App name: {app_name}")

    print("=" * 60)
    print("CLEAN EVENT LISTENER WITH WINDOW CLASSIFICATION")
    print("=" * 60)
    print(f"[INFO] Initial monitoring app: {bundle_id}")
    print(f"[INFO] Will dynamically switch based on active_target_Bundle_ID.json changes")
    
    mouse_monitor = MouseExitMonitor()
    output_path = os.path.join("ome/data/windows", f"win_{bundle_id}.jsonl")
    
    try:
        print(f"Focusing {bundle_id}...")
        result = ensure_app_focus(bundle_id)
        if result['status'] != 'success':
            print(f"Failed to focus app: {result.get('error')}")
            return
        print("Getting app reference...")
        app = NativeUIElement.getAppRefByBundleId(bundle_id)
        mouse_monitor.start()
        print("Event listener ready!")
        print("Move mouse to top-right corner to exit")
        print("=" * 60)
        existing_windows = set()
        last_bundle_id = bundle_id
        last_refresh_check = time.time()
        
        try:
            current_windows = app.windows()
            for idx, window in enumerate(current_windows):
                window_info = scan_window(window, idx)
                window_sig = get_window_signature(window)
                existing_windows.add(window_sig)
                print(f"Existing: {get_window_info(window)}")
        except Exception as e:
            print(f"Error getting initial windows: {e}")
            
        while True:
            try:
                # Check for bundle ID changes every 2 seconds
                current_time = time.time()
                if current_time - last_refresh_check >= 2.0:
                    active_bundle_id = bundle_controller.get_active_bundle_id()
                    
                    # Check if we need to switch apps
                    if active_bundle_id and active_bundle_id != last_bundle_id:
                        print(f"\n[SWITCH] Active bundle ID changed from '{last_bundle_id}' to '{active_bundle_id}'")
                        
                        # Validate the new bundle ID
                        if not bundle_controller.validate_bundle_id(active_bundle_id):
                            print(f"[SWITCH] Invalid bundle ID '{active_bundle_id}', reverting to '{last_bundle_id}'")
                            bundle_id = last_bundle_id
                            output_path = os.path.join("ome/data/windows", f"win_{bundle_id}.jsonl")
                        else:
                            bundle_id = active_bundle_id
                            output_path = os.path.join("ome/data/windows", f"win_{bundle_id}.jsonl")
                            
                            # Get app name for better logging
                            app_name = bundle_controller.get_app_name_for_bundle_id(bundle_id)
                            display_name = app_name or bundle_id
                            
                            # Refresh app handle for new bundle ID
                            print(f"[SWITCH] Refreshing app handle for {display_name}...")
                            result = ensure_app_focus(bundle_id)
                            if result['status'] == 'success':
                                try:
                                    app = NativeUIElement.getAppRefByBundleId(bundle_id)
                                    existing_windows = set()  # Reset window tracking
                                    print(f"[SWITCH] Successfully switched to monitoring '{display_name}'")
                                except Exception as e:
                                    print(f"[SWITCH] Failed to get app reference for {bundle_id}: {e}")
                                    # Revert to previous bundle ID
                                    bundle_id = last_bundle_id
                                    output_path = os.path.join("ome/data/windows", f"win_{bundle_id}.jsonl")
                            else:
                                print(f"[SWITCH] Failed to focus {display_name}: {result.get('error')}")
                                # Revert to previous bundle ID
                                bundle_id = last_bundle_id
                                output_path = os.path.join("ome/data/windows", f"win_{bundle_id}.jsonl")
                    
                    # Check for refresh requests
                    if bundle_controller.is_refresh_requested():
                        refresh_reason = bundle_controller.get_refresh_reason()
                        app_name = bundle_controller.get_app_name_for_bundle_id(bundle_id)
                        display_name = app_name or bundle_id
                        print(f"\n[REFRESH] Refresh requested for {display_name}: {refresh_reason}")
                        
                        # Refresh current app handle
                        print(f"[REFRESH] Refreshing app handle for {display_name}...")
                        result = ensure_app_focus(bundle_id)
                        if result['status'] == 'success':
                            try:
                                app = NativeUIElement.getAppRefByBundleId(bundle_id)
                                existing_windows = set()  # Reset window tracking
                                print(f"[REFRESH] Successfully refreshed app handle for {display_name}")
                            except Exception as e:
                                print(f"[REFRESH] Failed to get app reference for {bundle_id}: {e}")
                        else:
                            print(f"[REFRESH] Failed to refresh {display_name}: {result.get('error')}")
                        
                        bundle_controller.clear_refresh_flag()
                    
                    last_bundle_id = bundle_id
                    last_refresh_check = current_time
                
                print("Checking for new windows...")
                current_windows = app.windows()
                current_window_infos = set()
                all_window_infos = []
                for idx, window in enumerate(current_windows):
                    window_info = scan_window(window, idx)
                    window_sig = get_window_signature(window)
                    current_window_infos.add(window_sig)
                    all_window_infos.append(window_info)
                    if window_sig not in existing_windows:
                        detection_msg = format_window_detection(window_info)
                        print(f"🎯 {detection_msg}")
                        sheets = window_info.get('sheets', [])
                        if sheets:
                            print(f"   📄 Sheets:")
                            for sheet in sheets:
                                sheet_type = sheet.get('window_type', 'Unknown')
                                sheet_title = sheet.get('AXTitle', 'Unknown')
                                print(f"      - {sheet_title} [{sheet_type}]")
                
                # Write the active target to the JSONL file
                active_target = get_active_target(all_window_infos, bundle_id)
                if active_target:
                    # Include additional metadata
                    jsonl_data = {
                        "active_target": active_target,
                        "bundle_id": bundle_id,
                        "app_name": bundle_controller.get_app_name_for_bundle_id(bundle_id),
                        "source": "event_listener",
                        "last_updated": datetime.utcnow().isoformat() + "Z"
                    }
                    with open(output_path, 'w', encoding='utf-8') as f:
                        json.dump(jsonl_data, f, ensure_ascii=False, indent=2)
                
                existing_windows = current_window_infos
                time.sleep(0.2)
            except KeyboardInterrupt:
                print("Interrupted by user")
                break
            except Exception as e:
                print(f"Event error: {e}")
                # Request refresh on errors
                bundle_controller.request_refresh(bundle_id, f"error: {str(e)}")
                time.sleep(1)
    except Exception as e:
        print(f"Setup error: {e}")
    finally:
        mouse_monitor.stop()
        print("Cleanup complete")

if __name__ == "__main__":
    main()
