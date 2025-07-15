"""
App Picker List Extractor

This script focuses a macOS application's file picker window (e.g., Mail's attachment picker), walks its accessibility tree, and extracts file list rows (file names and related metadata) into a JSONL file. It is designed to help you programmatically discover and automate file selection in macOS app pickers.

====================
PURPOSE
====================
- Focuses the target app and its file picker window (e.g., 'New Message' in Mail).
- Traverses the accessibility (AX) tree to find the file list (AXOutline) and its rows (AXRow).
- Extracts file name and click point (omeClick) for each row.
- Outputs a structured list of file picker rows as JSONL for automation or analysis.
- **Optionally sends the Enter key after selecting a row, for automation workflows.**

====================
KEY FEATURES
====================
- Robustly focuses the app and its picker window, retrying if needed.
- Traverses the AX tree to locate the file list (AXOutline) and its rows (AXRow).
- Extracts file name, AXTextField class, and omeClick (center point for clicking) for each row.
- Supports selecting a specific row or a window of rows around a target.
- **Supports sending the Enter key after row selection via --send-keys-after-select.**
- CLI for specifying bundle ID, row index, and number of rows.
- Outputs to ome/data/pickers/picker_{bundle_id}.jsonl using a consistent naming convention.

====================
CLI USAGE EXAMPLES
====================
# Extract the first N rows from the Mail file picker (default N=MAX_ROWS)
python -m ome.utils.builder.app.appPicker_builder --bundle com.apple.mail

# Extract a specific row (e.g., row 5)
python -m ome.utils.builder.app.appPicker_builder --bundle com.apple.mail --row 5

# Extract N rows around a specific row
python -m ome.utils.builder.app.appPicker_builder --bundle com.apple.mail --row 10 --n 20

# Select a row and send Enter after selection (mouse click)
python -m ome.utils.builder.app.appPicker_builder --select-row 3 --send-keys-after-select

# Select a row and send Enter after selection (direct accessibility)
python -m ome.utils.builder.app.appPicker_builder --select-row-direct 5 --send-keys-after-select

====================
WHEN TO USE
====================
- When you need to programmatically extract and cache file picker row data from a macOS app.
- When building automation, accessibility, or testing tools for file selection dialogs.
- When you want to script or automate file picker interactions, including confirming selection with Enter.
"""
import sys
import os
import json
import time
import argparse
from Om_E_Py.ome.utils.builder.app.app_focus import ensure_app_focus
import ome
from Om_E_Py.ome.utils.builder.app.appNav_builder import extract_omeclick, extract_omeclick_textfield, safe_getattr_textfield
from env import UI_MAX_ROWS, UI_RETRY_DELAY, UI_PICKER_EXPORT_DIR, UI_ACTION_DELAY
from Om_E_Py.ome.utils.uiNav.navBigDaDDy import get_active_target_and_windows_from_file
from ome.AXKeyboard import RETURN
import Quartz

# Picker-specific constants
MAX_PICKER_ROWS = 20  # Limit picker extraction to 20 files for performance

def safe_getattr(obj, attr):
    """Safely get an attribute from an object, returning None on error."""
    try:
        return getattr(obj, attr, None)
    except Exception:
        return None

def extract_file_picker_rows(bundle_id="com.apple.mail", n=None, row_index=None, app_object=None):
    """
    Focuses the app, finds the file picker window, and extracts file list rows.
    Returns a list of dicts with row_index, file_name, axtextfield_class, and omeClick.
    Only processes a window of n rows around the selected row (if specified), or the first n rows otherwise.
    
    Args:
        bundle_id: The bundle ID of the app
        n: Number of rows to process (default: MAX_PICKER_ROWS)
        row_index: Center row for windowed processing
        app_object: Optional pre-focused app object to use instead of focusing
    """
    import time
    t0 = time.time()
    if n is None:
        n = MAX_PICKER_ROWS  # Use picker-specific limit instead of MAX_ROWS
    
    # 1. Get app object (use provided or focus fresh)
    t_focus_start = time.time()
    if app_object is not None:
        # Use provided app object (fast path)
        app = app_object
        print(f"[INFO] Using provided app object for {bundle_id}")
    else:
        # Focus app (slow path)
        focus_result = ensure_app_focus(bundle_id, fullscreen=True)
        t_focus_end = time.time()
        if not (isinstance(focus_result, dict) and focus_result.get('status') == 'success'):
            print(f"Could not focus app: {focus_result}")
            sys.exit(1)
        app = focus_result.get('app')
        if app is None:
            print(f"Could not get app object from ensure_app_focus for bundle {bundle_id}.")
            sys.exit(1)
        time.sleep(UI_RETRY_DELAY)
    
    t_focus_end = time.time()
    
    # 2. Tree navigation and row collection
    t_tree_start = time.time()
    windows = safe_getattr_textfield(app, 'AXWindows') or []
    current = None
    for win in windows:
        children = safe_getattr_textfield(win, 'AXChildren') or []
        if any(safe_getattr_textfield(child, 'AXRole') == 'AXSheet' for child in children):
            current = win
            break
    if not current:
        print("Could not find a window with an AXSheet child (file picker window).")
        sys.exit(1)
    steps = [
        {"AXRole": "AXSheet"},
        {"AXRole": "AXSplitGroup"},
        {"AXRole": "AXSplitGroup"},
        {"AXRole": "AXScrollArea"},
        {"AXRole": "AXOutline"},
    ]
    for step in steps:
        children = safe_getattr_textfield(current, 'AXChildren') or []
        found = None
        for child in children:
            role = safe_getattr_textfield(child, 'AXRole')
            if role == step["AXRole"]:
                found = child
                break
        if not found:
            print(f"Could not find {step['AXRole']}")
            sys.exit(1)
        current = found
    outline = current
    rows = [c for c in (safe_getattr_textfield(outline, 'AXChildren') or []) if safe_getattr_textfield(c, 'AXRole') == 'AXRow']
    total_rows = len(rows)
    t_tree_end = time.time()
    print(f"[INFO] Found {total_rows} total rows, limiting to {n} for performance")
    # 3. Window selection and processing
    t_proc_start = time.time()
    if row_index is not None:
        center = row_index - 1
        half_window = n // 2
        start = max(center - half_window, 0)
        end = min(start + n, total_rows)
        selected_rows = rows[start:end]
        row_offset = start
    else:
        selected_rows = rows[:n]  # Limit to MAX_PICKER_ROWS
        row_offset = 0
    results = []
    for i, row in enumerate(selected_rows, start=row_offset + 1):
        cells = [c for c in (safe_getattr_textfield(row, 'AXChildren') or []) if safe_getattr_textfield(c, 'AXRole') == 'AXCell']
        file_name = None
        for cell in cells:
            textfields = [c for c in (safe_getattr_textfield(cell, 'AXChildren') or []) if safe_getattr_textfield(c, 'AXRole') == 'AXTextField']
            for tf in textfields:
                # Try multiple properties to find the file name
                value = safe_getattr_textfield(tf, 'AXValue')
                title = safe_getattr_textfield(tf, 'AXTitle')
                description = safe_getattr_textfield(tf, 'AXDescription')
                
                # Use the first non-empty value we find
                if value:
                    file_name = value
                elif title:
                    file_name = title
                elif description:
                    file_name = description
                
                class_name = type(tf).__name__
                omeClick = extract_omeclick_textfield(tf)
                results.append({
                    "row_index": i,
                    "file_name": file_name,
                    "axtextfield_class": class_name,
                    "omeClick": omeClick
                })
    t_proc_end = time.time()
    t1 = time.time()
    print(f"[PERF] App focus: {(t_focus_end-t_focus_start):.3f}s | Tree navigation/row collection: {(t_tree_end-t_tree_start):.3f}s | Window processing: {(t_proc_end-t_proc_start):.3f}s | TOTAL: {(t1-t0):.3f}s")
    return results

def map_visual_to_accessibility_row(rows, visual_row_index):
    """
    Map visual row index (what user sees) to accessibility row index (what API reports).
    Handles header rows and other non-file rows that should be skipped.
    
    Args:
        rows: List of accessibility row elements
        visual_row_index: 1-based visual row index (what user counts)
    
    Returns:
        accessibility_row_index: 1-based accessibility row index, or None if not found
    """
    if not rows:
        return None
    
    # Check if first row is a header
    is_header_row = False
    if rows:
        try:
            first_row_children = safe_getattr_textfield(rows[0], 'AXChildren') or []
            if first_row_children:
                first_child = first_row_children[0]
                first_child_children = safe_getattr_textfield(first_child, 'AXChildren') or []
                if first_child_children:
                    text_field = first_child_children[0]
                    value = safe_getattr_textfield(text_field, 'AXValue')
                    if value and ('Name' in value or 'Date' in value or 'Size' in value):
                        is_header_row = True
                        print(f"[DEBUG] Detected header row: '{value}'")
        except Exception:
            pass
    
    # Map visual index to accessibility index
    if is_header_row:
        # When header row present, visual row 1 maps to accessibility row 2
        accessibility_row_index = visual_row_index + 1
        print(f"[DEBUG] Visual row {visual_row_index} maps to accessibility row {accessibility_row_index} (JSONL already accounts for header)")
    else:
        # No header row, direct mapping
        accessibility_row_index = visual_row_index + 1
        print(f"[DEBUG] No header detected, visual row {visual_row_index} maps to accessibility row {accessibility_row_index}")
    
    # Validate the mapped index
    if accessibility_row_index < 1 or accessibility_row_index > len(rows):
        print(f"[ERROR] Mapped accessibility row {accessibility_row_index} out of range (1-{len(rows)})")
        return None
    
    return accessibility_row_index

def update_picker_jsonl(bundle_id, rows, selected_row_index=None, max_rows=MAX_PICKER_ROWS):
    """
    Update the picker JSONL file with current picker state, similar to mailMessageList_controller.py.
    Only processes and outputs a window of max_rows rows around the selected row (if specified), or the first max_rows rows otherwise.
    """
    picker_data = []
    total_rows = len(rows)
    # Determine window
    if selected_row_index is not None:
        center = selected_row_index - 1
        half_window = max_rows // 2
        start = max(center - half_window, 0)
        end = min(start + max_rows, total_rows)
        selected_rows = rows[start:end]
        row_offset = start
    else:
        selected_rows = rows[:max_rows]
        row_offset = 0
    # Skip header row if present (windowed)
    start_index = 1
    if selected_rows:
        try:
            first_row_children = safe_getattr_textfield(selected_rows[0], 'AXChildren') or []
            if first_row_children:
                first_child = first_row_children[0]
                first_child_children = safe_getattr_textfield(first_child, 'AXChildren') or []
                if first_child_children:
                    text_field = first_child_children[0]
                    value = safe_getattr_textfield(text_field, 'AXValue')
                    if value and ('Name' in value or 'Date' in value or 'Size' in value):
                        start_index = 2  # Skip header row
        except Exception:
            pass
    row_count = 0
    for i, row in enumerate(selected_rows[start_index-1:], start=row_offset + start_index):
        if row_count >= max_rows:
            break
        try:
            file_name = None
            omeClick = None
            children = safe_getattr_textfield(row, 'AXChildren') or []
            for child in children:
                if safe_getattr_textfield(child, 'AXRole') == 'AXCell':
                    cell_children = safe_getattr_textfield(child, 'AXChildren') or []
                    for cell_child in cell_children:
                        if safe_getattr_textfield(cell_child, 'AXRole') == 'AXTextField':
                            value = safe_getattr_textfield(cell_child, 'AXValue')
                            if value:
                                file_name = value
                            omeClick = extract_omeclick_textfield(cell_child)
                            break
                    if file_name:
                        break
            if file_name:
                picker_data.append({
                    "row_index": i,
                    "file_name": file_name,
                    "axtextfield_class": "NativeUIElement",
                    "omeClick": omeClick,
                    "selected": (i == selected_row_index) if selected_row_index else False
                })
                row_count += 1
        except Exception as e:
            print(f"[WARNING] Error extracting row {i}: {e}")
    os.makedirs(UI_PICKER_EXPORT_DIR, exist_ok=True)
    out_path = os.path.join(UI_PICKER_EXPORT_DIR, f"picker_{bundle_id}.jsonl")
    with open(out_path, 'w') as f:
        for item in picker_data:
            f.write(json.dumps(item, ensure_ascii=False) + '\n')
    print(f"[INFO] Updated picker JSONL with {len(picker_data)} rows (limited to {max_rows})")
    if selected_row_index:
        print(f"[INFO] Row {selected_row_index} marked as selected")
    return picker_data

def select_row(bundle_id, row_index, send_keys_after_select=False):
    """
    Select/focus a specific row in the file picker by clicking on it using pyautogui.
    Optionally send Enter after selection (set send_keys_after_select=True).
    Args:
        bundle_id: The bundle ID of the app
        row_index: The 1-based visual row index to select (what user sees)
        send_keys_after_select: Whether to send Enter key after selecting the row
    """
    import pyautogui
    
    # Extract picker rows to get click coordinates
    rows = extract_file_picker_rows(bundle_id, n=MAX_PICKER_ROWS)
    
    # Find the target row
    target_row = None
    for row in rows:
        if row["row_index"] == row_index:
            target_row = row
            break
    
    if not target_row:
        print(f"Row {row_index} not found in picker data")
        return False
    
    # Click on the row using omeClick coordinates
    omeClick = target_row.get("omeClick")
    if not omeClick:
        print(f"No click coordinates found for row {row_index}")
        return False
    
    try:
        x, y = omeClick
        pyautogui.click(x, y)
        print(f"[SELECT_ROW] Clicked on row {row_index} at coordinates ({x}, {y})")
        if send_keys_after_select:
            print(f"[SELECT_ROW] Waiting {UI_ACTION_DELAY} seconds before sending Enter key...")
            time.sleep(UI_ACTION_DELAY)
            print("[SELECT_ROW] Sending Enter key after selection...")
            Quartz.CGEventPost(Quartz.kCGHIDEventTap, Quartz.CGEventCreateKeyboardEvent(None, RETURN, True))
            Quartz.CGEventPost(Quartz.kCGHIDEventTap, Quartz.CGEventCreateKeyboardEvent(None, RETURN, False))
        return True
    except Exception as e:
        print(f"[SELECT_ROW] Failed to click on row {row_index}: {e}")
        return False

def select_row_direct(bundle_id, row_index, app_object=None, send_keys_after_select=False):
    """
    Select/focus a specific row in the file picker using direct accessibility API control.
    Optionally send Enter after selection (set send_keys_after_select=True).
    Args:
        bundle_id: The bundle ID of the app
        row_index: The 1-based visual row index to select (what user sees)
        app_object: Optional pre-focused app object to use instead of focusing
        send_keys_after_select: Whether to send Enter key after selecting the row
    """
    # Use provided app object or focus fresh one
    if app_object is not None:
        # Use provided app object (fast path)
        app = app_object
        print(f"[INFO] Using provided app object for {bundle_id}")
        time.sleep(UI_RETRY_DELAY)
    else:
        # Focus app (slow path)
        focus_result = ensure_app_focus(bundle_id, fullscreen=True)
        if not (isinstance(focus_result, dict) and focus_result.get('status') == 'success'):
            print(f"Could not focus app: {focus_result}")
            return False
        
        app = focus_result.get('app')
        time.sleep(UI_RETRY_DELAY)
    
    # Find the window with an AXSheet child (where the file picker appears)
    windows = safe_getattr_textfield(app, 'AXWindows') or []
    current = None
    for win in windows:
        children = safe_getattr_textfield(win, 'AXChildren') or []
        if any(safe_getattr_textfield(child, 'AXRole') == 'AXSheet' for child in children):
            current = win
            break
    
    if not current:
        print("Could not find a window with an AXSheet child (file picker window).")
        return False
    
    # Traverse the accessibility tree to reach the AXOutline (file list)
    steps = [
        {"AXRole": "AXSheet"},
        {"AXRole": "AXSplitGroup"},
        {"AXRole": "AXSplitGroup"},
        {"AXRole": "AXScrollArea"},
        {"AXRole": "AXOutline"},
    ]
    
    for step in steps:
        children = safe_getattr_textfield(current, 'AXChildren') or []
        found = None
        for child in children:
            role = safe_getattr_textfield(child, 'AXRole')
            if role == step["AXRole"]:
                found = child
                break
        if not found:
            print(f"Could not find {step['AXRole']}")
            return False
        current = found
    
    outline = current
    
    # Get all AXRow children (each row represents a file)
    rows = [c for c in (safe_getattr_textfield(outline, 'AXChildren') or []) if safe_getattr_textfield(c, 'AXRole') == 'AXRow']
    
    print(f"[DEBUG] Total rows found in accessibility tree: {len(rows)}")
    print(f"[DEBUG] Requested visual row index: {row_index}")
    
    # Map visual row index to accessibility row index
    accessibility_row_index = map_visual_to_accessibility_row(rows, row_index)
    if accessibility_row_index is None:
        return False
    
    target_row = rows[accessibility_row_index - 1]  # Convert to 0-based
    
    # Direct selection using accessibility API (like mailMessageList_controller.py)
    try:
        # Set the row as selected
        safe_setattr(target_row, 'AXSelected', True)
        
        # Enhanced scrolling - try multiple methods to ensure the row is visible
        scroll_success = False
        
        # Method 1: Use AXScrollToVisible on the row itself
        try:
            safe_setattr(target_row, 'AXScrollToVisible', True)
            scroll_success = True
            print(f"[SCROLL] Used AXScrollToVisible on row")
        except Exception as e:
            print(f"[SCROLL] AXScrollToVisible failed: {e}")
        
        # Method 2: If that fails, try scrolling the outline container
        if not scroll_success:
            try:
                # Get the scroll area and try to scroll it
                scroll_area = None
                for step in steps:
                    if step["AXRole"] == "AXScrollArea":
                        scroll_area = current
                        break
                
                if scroll_area:
                    # Try to scroll the scroll area to bring the row into view
                    safe_setattr(scroll_area, 'AXScrollToVisible', True)
                    scroll_success = True
                    print(f"[SCROLL] Used AXScrollToVisible on scroll area")
            except Exception as e:
                print(f"[SCROLL] Scroll area scroll failed: {e}")
        
        # Method 3: If still no success, try to get the row's position and manually scroll
        if not scroll_success:
            try:
                # Get the row's position and try to scroll to it
                pos = safe_getattr_textfield(target_row, 'AXPosition')
                if pos:
                    print(f"[SCROLL] Row position: {pos}")
                    # Try scrolling the outline to this position
                    safe_setattr(outline, 'AXScrollToVisible', True)
                    scroll_success = True
                    print(f"[SCROLL] Used AXScrollToVisible on outline")
            except Exception as e:
                print(f"[SCROLL] Manual scroll failed: {e}")
        
        if scroll_success:
            print(f"[SCROLL] Successfully scrolled to row")
        else:
            print(f"[SCROLL] Warning: Could not scroll to row - it may not be visible")
        
        print(f"[SELECT_ROW_DIRECT] Directly selected visual row {row_index} (accessibility row {accessibility_row_index})")
        
        # Update the picker JSONL file with current state
        update_picker_jsonl(bundle_id, rows, accessibility_row_index)
        
        if send_keys_after_select:
            print(f"[SELECT_ROW_DIRECT] Waiting {UI_ACTION_DELAY} seconds before sending Enter key...")
            time.sleep(UI_ACTION_DELAY)
            print("[SELECT_ROW_DIRECT] Sending Enter key after selection...")
            Quartz.CGEventPost(Quartz.kCGHIDEventTap, Quartz.CGEventCreateKeyboardEvent(None, RETURN, True))
            Quartz.CGEventPost(Quartz.kCGHIDEventTap, Quartz.CGEventCreateKeyboardEvent(None, RETURN, False))
        
        return True
    except Exception as e:
        print(f"[SELECT_ROW_DIRECT] Failed to select row directly: {e}")
        return False

def safe_setattr(obj, attr, value):
    """Safely set an attribute on an object, returning True on success."""
    try:
        setattr(obj, attr, value)
        return True
    except Exception:
        return False

def build_picker_data(bundle_id, app_object=None):
    """
    Build picker data and write to JSONL file. Can be called directly with an app object.
    
    Args:
        bundle_id: The bundle ID of the app
        app_object: Optional pre-focused app object to use instead of focusing
    
    Returns:
        dict: Result with status and file path
    """
    try:
        # Extract picker rows using the provided app object (fast path)
        rows = extract_file_picker_rows(bundle_id=bundle_id, app_object=app_object)
        
        # Write to JSONL file
        os.makedirs(UI_PICKER_EXPORT_DIR, exist_ok=True)
        out_path = os.path.join(UI_PICKER_EXPORT_DIR, f"picker_{bundle_id}.jsonl")
        
        with open(out_path, 'w') as f:
            for item in rows:
                f.write(json.dumps(item, ensure_ascii=False) + '\n')
        
        return {
            "status": "success",
            "file_path": out_path,
            "row_count": len(rows)
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e)
        }

def main():
    """Parse CLI arguments and extract picker rows, writing them to JSONL.
    --send-keys-after-select: If used with --select-row or --select-row-direct, sends Enter after row selection.
    """
    parser = argparse.ArgumentParser(description="Extract file picker rows via accessibility API.")
    parser.add_argument('--bundle', type=str, nargs='?', default=None, help='Bundle ID of the app (default: current active bundle)')
    parser.add_argument('--row', '-r', type=int, default=None, help='Row index (1-based) to extract. If not set, extracts the first N rows.')
    parser.add_argument('--n', type=int, default=None, help='Number of rows to extract (default: MAX_ROWS)')
    parser.add_argument('--select-row', type=int, default=None, help='Row index (1-based) to select/focus by clicking on it.')
    parser.add_argument('--select-row-direct', type=int, default=None, help='Row index (1-based) to select/focus using direct accessibility API control.')
    parser.add_argument('--send-keys-after-select', action='store_true', help='Send Enter key after selecting the row.')
    args = parser.parse_args()
    
    bundle_id = args.bundle
    if not bundle_id:
        try:
            bundle_id = get_active_target_and_windows_from_file().get('bundle_id')
            if not bundle_id:
                print("[ERROR] No active bundle_id found via navBigDaDDy")
                sys.exit(1)
            print(f"[INFO] No bundle_id provided, using active_bundle_id from navBigDaDDy: {bundle_id}")
        except Exception as e:
            print(f"[ERROR] Could not get bundle_id from navBigDaDDy: {e}")
            sys.exit(1)

    # Handle direct row selection (like mailMessageList_controller.py)
    if args.select_row_direct is not None:
        if not bundle_id:
            print("[ERROR] No bundle_id available for --select-row-direct")
            sys.exit(1)
        success = select_row_direct(bundle_id=bundle_id, row_index=args.select_row_direct, send_keys_after_select=args.send_keys_after_select)
        if success:
            print(f"Successfully selected row {args.select_row_direct} using direct accessibility control")
        else:
            print(f"Failed to select row {args.select_row_direct}")
        return

    # Handle mouse-click row selection
    if args.select_row is not None:
        if not bundle_id:
            print("[ERROR] No bundle_id available for --select-row")
            sys.exit(1)
        success = select_row(bundle_id=bundle_id, row_index=args.select_row, send_keys_after_select=args.send_keys_after_select)
        if success:
            print(f"Successfully selected row {args.select_row}")
        else:
            print(f"Failed to select row {args.select_row}")
        return

    # Handle row extraction
    rows = extract_file_picker_rows(bundle_id=bundle_id, n=args.n, row_index=args.row)
    os.makedirs(UI_PICKER_EXPORT_DIR, exist_ok=True)
    out_path = os.path.join(UI_PICKER_EXPORT_DIR, f"picker_{bundle_id}.jsonl")
    with open(out_path, 'w') as f:
        for item in rows:
            f.write(json.dumps(item, ensure_ascii=False) + '\n')
    print(f"Wrote {len(rows)} rows to {out_path}")

if __name__ == "__main__":
    main() 