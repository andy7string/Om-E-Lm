#!/usr/bin/env python3
"""
Test script to detect picker windows using the ome accessibility framework.

This script uses the same foundational setup patterns as winD_controller.py:
1. App focus with bundle ID resolution
2. Safe attribute access
3. Timing stats
4. Error handling

Usage:
    python test_picker_detection.py com.apple.mail
"""

import sys
import os
import time
import json
from datetime import datetime

# Add the project root to the Python path
project_root = os.path.dirname(os.path.abspath(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

def get_attr_safe(obj, attr):
    """
    Safely gets an attribute from an object, returning None if not present or if an exception occurs.
    """
    try:
        return getattr(obj, attr, None)
    except Exception:
        return None

def identify_sheet_type_with_ome(bundle_id):
    """
    Use the ome accessibility framework to identify the type of sheet window.
    Returns: 'FILE_PICKER', 'ALERT', 'MODAL', or 'UNKNOWN'
    """
    timing_stats = {'ome_init': 0.0, 'window_scan': 0.0, 'sheet_analysis': 0.0, 'total': 0.0}
    t_total_start = time.perf_counter()
    
    try:
        from ome.AXClasses import NativeUIElement
        
        t_ome_start = time.perf_counter()
        
        # Get app name from bundle ID (same pattern as navBigDaDDy)
        app_name = bundle_id.split('.')[-1].title()  # "com.apple.mail" -> "Mail"
        print(f"[OME] Attempting to connect to app: {app_name}")
        
        # Use the same pattern as winD_controller.py
        app = NativeUIElement.getAppRefByBundleId(bundle_id)
        timing_stats['ome_init'] = time.perf_counter() - t_ome_start
        
        t_window_start = time.perf_counter()
        windows = app.windows()
        print(f"[OME] Found {len(windows)} windows")
        timing_stats['window_scan'] = time.perf_counter() - t_window_start
        
        t_sheet_start = time.perf_counter()
        
        for window_idx, window in enumerate(windows):
            print(f"\n[OME] Analyzing window {window_idx}:")
            print(f"  Title: {get_attr_safe(window, 'AXTitle')}")
            print(f"  Role: {get_attr_safe(window, 'AXRole')}")
            print(f"  Subrole: {get_attr_safe(window, 'AXSubrole')}")
            print(f"  Description: {get_attr_safe(window, 'AXRoleDescription')}")
            
            # Check if window has sheets
            try:
                sheets = window.sheets()
                print(f"  Found {len(sheets)} sheets")
                
                for sheet_idx, sheet in enumerate(sheets):
                    print(f"\n  [OME] Analyzing sheet {sheet_idx}:")
                    
                    # OME sheet properties that might help identify pickers
                    sheet_props = {
                        'title': get_attr_safe(sheet, 'AXTitle'),
                        'role': get_attr_safe(sheet, 'AXRole'),
                        'subrole': get_attr_safe(sheet, 'AXSubrole'),
                        'description': get_attr_safe(sheet, 'AXRoleDescription'),
                        'identifier': get_attr_safe(sheet, 'AXIdentifier'),
                        'help': get_attr_safe(sheet, 'AXHelp'),
                        'value': get_attr_safe(sheet, 'AXValue'),
                        'focused': get_attr_safe(sheet, 'AXFocused'),
                        'enabled': get_attr_safe(sheet, 'AXEnabled'),
                        'size': get_attr_safe(sheet, 'AXSize'),
                        'position': get_attr_safe(sheet, 'AXPosition'),
                    }
                    
                    for prop_name, prop_value in sheet_props.items():
                        if prop_value is not None:
                            print(f"    {prop_name}: {prop_value}")
                    
                    # Check for picker-specific identifiers
                    sheet_id = str(sheet_props['identifier'] or "")
                    sheet_desc = str(sheet_props['description'] or "")
                    sheet_title = str(sheet_props['title'] or "")
                    
                    print(f"\n  [OME] Picker detection analysis:")
                    
                    # File picker indicators
                    picker_indicators = ["open-panel", "file-panel", "choose", "select"]
                    for indicator in picker_indicators:
                        if indicator in sheet_id.lower():
                            print(f"    ✅ Found picker indicator '{indicator}' in identifier")
                            timing_stats['sheet_analysis'] = time.perf_counter() - t_sheet_start
                            timing_stats['total'] = time.perf_counter() - t_total_start
                            return "FILE_PICKER", sheet_props, timing_stats
                        if indicator in sheet_desc.lower():
                            print(f"    ✅ Found picker indicator '{indicator}' in description")
                            timing_stats['sheet_analysis'] = time.perf_counter() - t_sheet_start
                            timing_stats['total'] = time.perf_counter() - t_total_start
                            return "FILE_PICKER", sheet_props, timing_stats
                    
                    # Alert indicators
                    alert_indicators = ["alert", "dialog", "warning", "error"]
                    for indicator in alert_indicators:
                        if indicator in sheet_id.lower():
                            print(f"    ✅ Found alert indicator '{indicator}' in identifier")
                            timing_stats['sheet_analysis'] = time.perf_counter() - t_sheet_start
                            timing_stats['total'] = time.perf_counter() - t_total_start
                            return "ALERT", sheet_props, timing_stats
                        if indicator in sheet_desc.lower():
                            print(f"    ✅ Found alert indicator '{indicator}' in description")
                            timing_stats['sheet_analysis'] = time.perf_counter() - t_sheet_start
                            timing_stats['total'] = time.perf_counter() - t_total_start
                            return "ALERT", sheet_props, timing_stats
                    
                    print(f"    ❓ No specific indicators found")
                    
                    # Try to analyze sheet content for picker patterns using OME methods
                    print(f"\n  [OME] Content analysis:")
                    
                    # Look for picker-specific elements using OME's convenience methods
                    try:
                        buttons = sheet.buttons()
                        print(f"    Found {len(buttons)} buttons")
                        for button in buttons:
                            button_title = get_attr_safe(button, 'AXTitle')
                            if button_title:
                                print(f"      Button: {button_title}")
                                picker_buttons = ["Choose File", "Cancel", "Show Options", "Open", "Save", "Choose"]
                                if any(picker_btn in button_title for picker_btn in picker_buttons):
                                    print(f"      ✅ Found picker button: {button_title}")
                                    timing_stats['sheet_analysis'] = time.perf_counter() - t_sheet_start
                                    timing_stats['total'] = time.perf_counter() - t_total_start
                                    return "FILE_PICKER", sheet_props, timing_stats
                    except Exception as e:
                        print(f"    Error analyzing buttons: {e}")
                    
                    # Look for file-related static text
                    try:
                        static_texts = sheet.staticTexts()
                        print(f"    Found {len(static_texts)} static texts")
                        for text in static_texts:
                            text_value = get_attr_safe(text, 'AXValue')
                            if text_value:
                                print(f"      Text: {text_value}")
                                picker_text_indicators = ["favourites", "recent", "desktop", "documents", "applications", "downloads"]
                                if any(indicator in str(text_value).lower() for indicator in picker_text_indicators):
                                    print(f"      ✅ Found picker text indicator: {text_value}")
                                    timing_stats['sheet_analysis'] = time.perf_counter() - t_sheet_start
                                    timing_stats['total'] = time.perf_counter() - t_total_start
                                    return "FILE_PICKER", sheet_props, timing_stats
                    except Exception as e:
                        print(f"    Error analyzing static texts: {e}")
                    
                    # Look for groups that might contain file lists
                    try:
                        groups = sheet.groups()
                        print(f"    Found {len(groups)} groups")
                        for group in groups:
                            group_desc = get_attr_safe(group, 'AXRoleDescription')
                            if group_desc:
                                print(f"      Group: {group_desc}")
                                if "list" in group_desc.lower() or "table" in group_desc.lower():
                                    print(f"      ✅ Found list/table group: {group_desc}")
                                    timing_stats['sheet_analysis'] = time.perf_counter() - t_sheet_start
                                    timing_stats['total'] = time.perf_counter() - t_total_start
                                    return "FILE_PICKER", sheet_props, timing_stats
                    except Exception as e:
                        print(f"    Error analyzing groups: {e}")
                    
            except Exception as e:
                print(f"  Error accessing sheets: {e}")
                print(f"  No sheets found")
        
        timing_stats['sheet_analysis'] = time.perf_counter() - t_sheet_start
        timing_stats['total'] = time.perf_counter() - t_total_start
        return "UNKNOWN", {}, timing_stats
                    
    except Exception as e:
        print(f"[OME] Error: {e}")
        timing_stats['total'] = time.perf_counter() - t_total_start
        return "ERROR", {}, timing_stats

def main():
    """Main test function using the same patterns as winD_controller.py"""
    
    if len(sys.argv) != 2:
        print("Usage: python test_picker_detection.py <bundle_id>")
        print("Example: python test_picker_detection.py com.apple.mail")
        sys.exit(1)
    
    input_id = sys.argv[1]
    
    print("🔍 OME Picker Detection Test")
    print("=" * 50)
    
    # Use the same bundle ID resolution pattern as winD_controller.py
    try:
        from ome.utils.builder.app.appList_controller import bundle_id_exists, get_bundle_id
        
        print(f"[Setup] Resolving bundle ID for: {input_id}")
        canonical_bundle_id = bundle_id_exists(input_id)
        if not canonical_bundle_id:
            possible_bundle_id = get_bundle_id(input_id)
            if possible_bundle_id:
                canonical_bundle_id = bundle_id_exists(possible_bundle_id)
                if not canonical_bundle_id:
                    raise ValueError(f"'{input_id}' is neither a valid bundle ID nor a known app name.")
            else:
                raise ValueError(f"'{input_id}' is neither a valid bundle ID nor a known app name.")
        
        resolved_bundle_id = canonical_bundle_id
        print(f"[Setup] Resolved bundle ID: {resolved_bundle_id}")
        
    except Exception as e:
        print(f"❌ Bundle ID resolution error: {e}")
        sys.exit(1)
    
    # Use the same app focus pattern as winD_controller.py
    try:
        from ome.utils.builder.app.app_focus import ensure_app_focus
        
        print(f"[Setup] Focusing app: {resolved_bundle_id}")
        focus_result = ensure_app_focus(resolved_bundle_id, fullscreen=True)
        
        if not (isinstance(focus_result, dict) and focus_result.get('status') == 'success'):
            raise RuntimeError(f"Could not focus app with bundle ID '{resolved_bundle_id}'. Result: {focus_result}")
        
        print(f"✅ App focused successfully")
        
    except Exception as e:
        print(f"❌ App focus error: {e}")
        sys.exit(1)
    
    print()
    print("🔍 Analyzing window properties with OME...")
    print("=" * 50)
    
    # Test OME picker detection
    sheet_type, sheet_props, timing_stats = identify_sheet_type_with_ome(resolved_bundle_id)
    
    print()
    print("📊 Results")
    print("=" * 50)
    print(f"Sheet type: {sheet_type}")
    
    if sheet_props:
        print(f"Sheet properties: {json.dumps(sheet_props, indent=2, default=str)}")
    
    print()
    print("⏱️ Timing Stats")
    print("=" * 50)
    for stat_name, stat_value in timing_stats.items():
        print(f"  {stat_name}: {stat_value:.4f} s")
    
    print()
    print("💡 Recommendations")
    print("=" * 50)
    
    if sheet_type == "FILE_PICKER":
        print("✅ This is a file picker window")
        print("   - Can be mapped to window_ref: 'FilePicker'")
        print("   - Should trigger picker-specific automation logic")
        print("   - Can use sheet.buttons() to find 'Choose File', 'Cancel', etc.")
    elif sheet_type == "ALERT":
        print("✅ This is an alert dialog")
        print("   - Can be mapped to window_ref: 'Alert'")
        print("   - Should trigger alert-specific automation logic")
    elif sheet_type == "UNKNOWN":
        print("❓ Sheet type could not be determined")
        print("   - May need additional OME property analysis")
        print("   - Consider fallback to content-based detection")
    elif sheet_type == "ERROR":
        print("❌ Error occurred during OME analysis")
        print("   - Check OME installation and permissions")
        print("   - Consider fallback to accessibility API")

if __name__ == "__main__":
    main() 