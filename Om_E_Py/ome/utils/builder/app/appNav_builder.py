"""
Om_E_Py/ome/utils/builder/app/appNav_builder.py

This module is part of the Om_E_Lm project. It dynamically crawls the active window or sheet of a macOS application, focusing on actionable UI elements (buttons, popups, rows, etc.) using the accessibility API.

Main Purpose:
- Focuses a macOS application and finds the active window or sheet.
- Dynamically crawls the accessibility tree, efficiently extracting actionable elements.
- Only queries expensive attributes (title, description, etc.) for actionable elements, avoiding slow queries on containers/structural nodes.
- Outputs a JSONL file with one actionable element per line, suitable for navigation, automation, or UI testing.
- Configurable via JSONL config for roles, max depth, max lines, and more (set by env.py and .env at the project root).

Key Features:
- Actionable Element Extraction: Finds and exports actionable UI elements (buttons, popups, rows, etc.) for the focused window/sheet.
- Efficient Attribute Fetching: Only fetches expensive attributes for actionable roles, not for containers.
- Finder/File Row Heuristics: Special logic for Finder/file rows to extract file names, kinds, and other metadata.
- Config-Driven: Reads roles, max depth, and other parameters from a JSONL config file per app/window context.
- Output: Saves results as a JSONL file in the navigation export directory (set by env.py), with each line representing an actionable element.
- Command-Line Interface: Can be run directly to crawl any app by bundle ID.
- Debugging: Optionally prints the accessibility tree structure for inspection.

How to Use (Command Line):
    python -m Om_E_Py.ome.utils.builder.app.appNav_builder --bundle com.apple.mail [--force] [--debug]

Arguments:
    --bundle: The bundle ID of the app (default: com.apple.mail)
    --force: Overwrite output file if it exists
    --debug: Print the accessibility tree structure (first 3 levels)

Example:
    python -m Om_E_Py.ome.utils.builder.app.appNav_builder --bundle com.apple.mail --force
    # Crawls the Mail app's main window and exports actionable elements.

Output:
- A JSONL file named appNav_<bundle_id>_<window_ref>.jsonl in the navigation export directory (set by env.py).
- Each line is a JSON object representing an actionable element, with attributes like AXRole, AXTitle, omeClick, and more.

When to Use:
- To analyze, automate, or navigate the UI of a macOS app window.
- For accessibility, UI testing, or building custom navigation tools.

"""
import sys
import argparse
import time
import concurrent.futures
import json
import re
import os
from collections import defaultdict
import time as _time

import Om_E_Py.ome as ome
from Om_E_Py.ome.utils.builder.app.app_focus import ensure_app_focus
from env import UI_RETRY_DELAY, UI_NAV_EXPORT_DIR, UI_WINDOW_REF_MAP_CONFIG
from Om_E_Py.ome.utils.uiNav.navBigDaDDy import get_active_target_and_windows_from_file
from Om_E_Py.ome._a11y import Error as OMEA11yError


# Timing stats
timing_stats = defaultdict(float)

def safe_getattr(obj, attr):
    t0 = _time.perf_counter()
    try:
        result = getattr(obj, attr, None)
    except (Exception, OMEA11yError):
        # Handle AX Error -25200 and similar: attribute does not exist or is invalid
        result = None
    timing_stats['safe_getattr'] += _time.perf_counter() - t0
    return result

def safe_get_children(element, timeout=0.1):
    t0 = _time.perf_counter()
    def get_children():
        try:
            return getattr(element, 'AXChildren', None)
        except (Exception, OMEA11yError):
            # Handle AX Error -25200 and similar: attribute does not exist or is invalid
            return []
    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
        future = executor.submit(get_children)
        try:
            result = future.result(timeout=timeout)
        except concurrent.futures.TimeoutError:
            result = []
        timing_stats['safe_get_children'] += _time.perf_counter() - t0
        return result

# Roles considered actionable for buttons
BUTTON_ROLES = {'AXButton', 'AXMenuButton', 'AXPopUpButton', 'AXCheckBox', 'AXCell'}
# Roles considered structural/containers
STRUCTURAL_ROLES = {
    'AXWindow', 'AXSheet', 'AXGroup', 'AXScrollArea', 'AXSplitGroup', 'AXTabGroup',
    'AXToolbar', 'AXDrawer', 'AXPopover', 'AXSidebar', 'AXUnknown', 'AXOutline'
}
SKIP_ROLES = {'AXTable'}

def find_active_window_or_sheet(app):
    win = safe_getattr(app, 'AXFocusedWindow')
    if win:
        sheets = [c for c in (safe_getattr(win, 'AXChildren') or []) if safe_getattr(c, 'AXRole') == 'AXSheet']
        if sheets:
            return sheets[0], 'AXSheet'
        return win, 'AXWindow'
    windows = safe_getattr(app, 'AXWindows') or []
    if windows:
        return windows[0], 'AXWindow'
    return None, None

def extract_omeclick_with_role(element, role):
    """
    Extracts the click point for an element, given its AXRole.
    Returns the center point if AXPosition and AXSize are available.
    """
    try:
        pos = safe_getattr(element, 'AXPosition')
        size = safe_getattr(element, 'AXSize')
        if pos and size and isinstance(pos, (list, tuple)) and isinstance(size, (list, tuple)):
            return [float(pos[0]) + float(size[0])/2, float(pos[1]) + float(size[1])/2]
    except Exception:
        pass
    return None

def extract_cell_details(cell):
    details = []
    children = safe_get_children(cell) or []
    for child in children:
        role = safe_getattr(child, 'AXRole')
        if role in {'AXTextField', 'AXStaticText'}:
            value = safe_getattr(child, 'AXValue')
            title = safe_getattr(child, 'AXTitle')
            details.append({
                'role': role,
                'value': value,
                'title': title
            })
        # Optionally, go deeper for nested cells or buttons
        elif role in BUTTON_ROLES:
            # Recursively extract details for nested actionable elements
            nested = {
                'role': role,
                'title': safe_getattr(child, 'AXTitle'),
                'description': safe_getattr(child, 'AXDescription'),
                'omeClick': extract_omeclick_with_role(child, role)
            }
            details.append(nested)
    return details

def classify_finder_value(val):
    if not isinstance(val, str):
        return None
    # Size: e.g., "13 KB", "128 bytes"
    if re.match(r"^\d+[.,]?\d*\s*(KB|MB|GB|bytes)$", val, re.IGNORECASE):
        return 'Size'
    # Date Modified: e.g., "21 Apr 2024 at 17:07"
    if re.match(r"\d{1,2} \w{3,9} \d{4}( at \d{1,2}:\d{2})?", val):
        return 'Date Modified'
    # Kind: e.g., "Folder", "Document", "Alias", etc.
    if val.lower() in {'folder', 'document', 'alias', 'application', 'plain text', 'python source', 'markdown document'}:
        return 'Kind'
    # File name: fallback if it looks like a filename
    if re.match(r".+\.[a-zA-Z0-9]+$", val):
        return 'Name'
    return None

def extract_row_details(axrow):
    # Extract all AXCell children and classify all details into the correct fields only for AXRow or FinderFileRow
    children = safe_get_children(axrow) or []
    cells = [c for c in children if safe_getattr(c, 'AXRole') == 'AXCell']
    role = safe_getattr(axrow, 'AXRole')
    row_obj = {"AXRole": role}
    y = None
    # Remove parent info from output
    found_fields = set()
    first_value = None
    for idx, cell in enumerate(cells):
        omeClick = extract_omeclick_with_role(cell, 'AXCell')
        if omeClick and y is None:
            y = omeClick[1]
            row_obj['omeClick'] = omeClick
        details = extract_cell_details(cell)
        for detail in details:
            value = detail.get('value')
            if value is None:
                continue
            if first_value is None:
                first_value = value
            # Only apply heuristics to AXRow or FinderFileRow
            if role in ('AXRow', 'FinderFileRow'):
                field = classify_finder_value(value)
                if field and field not in found_fields:
                    row_obj[field] = value
                    found_fields.add(field)
    # Fallback: if no Name found, use the first non-empty value
    name_value = row_obj.get('Name')
    if not name_value and first_value is not None:
        name_value = first_value
    # Standardize main label as AXTitle
    ax_title = safe_getattr(axrow, 'AXTitle')
    if not ax_title:
        ax_title = safe_getattr(axrow, 'AXDescription')
    if not ax_title:
        ax_title = name_value
    # Do NOT skip row if ax_title is missing or 'unknown' -- always output row
    row_obj['AXTitle'] = ax_title if ax_title else 'unknown'
    # Remove Name and description fields if present
    row_obj.pop('Name', None)
    row_obj.pop('description', None)
    return row_obj

def print_ax_tree(element, depth=0, max_depth=5):
    if depth > max_depth:
        return
    role = safe_getattr(element, 'AXRole')
    title = safe_getattr(element, 'AXTitle')
    indent = '  ' * depth
    print(f"{indent}- {role!r} {title!r}")
    children = safe_get_children(element) or []
    for child in children:
        print_ax_tree(child, depth+1, max_depth)

# Add a set of known kind types for matching
KNOWN_KIND_TYPES = {"folder", "document", "alias", "application", "plain text", "python source", "markdown document", "pdf", "image", "movie", "text", "source", "markdown", "patch"}

def find_kind_in_row(element):
    children = safe_get_children(element) or []
    for child in children:
        value = safe_getattr(child, 'AXValue')
        if value and isinstance(value, str) and value.strip().lower() in KNOWN_KIND_TYPES:
            return value
        # Recurse into children
        kind = find_kind_in_row(child)
        if kind:
            return kind
    return None

def extract_finder_file_row(axgroup, row_number=None):
    details = {}
    omeClick = None
    kind = None
    def recurse(element):
        nonlocal omeClick
        children = safe_get_children(element) or []
        for child in children:
            role = safe_getattr(child, 'AXRole')
            value = safe_getattr(child, 'AXValue')
            pos = safe_getattr(child, 'AXPosition')
            size = safe_getattr(child, 'AXSize')
            if omeClick is None and role == 'AXTextField' and pos and size:
                omeClick = [float(pos[0]) + float(size[0])/2, float(pos[1]) + float(size[1])/2]
            elif omeClick is None and pos and size:
                omeClick = [float(pos[0]) + float(size[0])/2, float(pos[1]) + float(size[1])/2]
            if role in ('AXStaticText', 'AXTextField') and value:
                key = safe_getattr(child, 'AXTitle') or f"{role}_{len(details)}"
                details[key] = value
            recurse(child)
    recurse(axgroup)
    file_name = None
    for v in details.values():
        if isinstance(v, str) and v.endswith('.app'):
            file_name = v
            break
        elif isinstance(v, str) and not file_name:
            file_name = v
    # Robustly extract Kind
    kind = find_kind_in_row(axgroup)
    row = {
        "AXRole": "FinderFileRow",
        "details": details
    }
    if file_name:
        row["file_name"] = file_name
    if kind:
        row["Kind"] = kind
    if omeClick:
        row["omeClick"] = omeClick
    return row

def extract_finder_file_rows_from_any(element):
    rows = []
    def recurse(el):
        file_name = None
        kind = None
        omeClick = None
        children = safe_get_children(el) or []
        for child in children:
            role = safe_getattr(child, 'AXRole')
            if role == 'AXStaticText':
                value = safe_getattr(child, 'AXValue')
                if value and not file_name:
                    file_name = value
                if value and (value.lower() in {"application", "folder", "alias", "document"}):
                    kind = value
            if role == 'AXCell' and not omeClick:
                omeClick = extract_omeclick_with_role(child, 'AXCell')
            # Recurse into all children
            recurse(child)
        if file_name:
            out = {"AXRole": "FinderFileRow", "file_name": file_name}
            if kind:
                out["Kind"] = kind
            if omeClick:
                out["omeClick"] = omeClick
            rows.append(out)
    recurse(element)
    return rows

def dynamic_crawl(element, results=None, max_depth=10, depth=0, parent_role=None, max_results=None, button_roles=None, structural_roles=None, skip_roles=None, parent_path=None, skip_identifiers=None, skip_descriptions=None):
    t0 = _time.perf_counter()
    if results is None:
        results = []
    if parent_path is None:
        parent_path = []
    if skip_identifiers is None:
        skip_identifiers = []
    if skip_descriptions is None:
        skip_descriptions = []
    if max_results is not None and len(results) >= max_results:
        return results
    role = safe_getattr(element, 'AXRole')
    identifier = safe_getattr(element, 'AXIdentifier')
    description = safe_getattr(element, 'AXDescription')
    # Build the new path for this element
    this_path = parent_path + [{
        'role': role,
        'identifier': identifier,
        'description': description
    }]
    # Skip by identifier or description from config
    if (skip_identifiers and identifier in skip_identifiers) or (skip_descriptions and description and any(skip_desc.lower() in description.lower() for skip_desc in skip_descriptions)):
        timing_stats['dynamic_crawl'] += _time.perf_counter() - t0
        return results
    # Skip roles should be completely ignored, regardless of other role classifications
    if skip_roles and role in skip_roles:
        timing_stats['dynamic_crawl'] += _time.perf_counter() - t0
        return results
    # For structural/container roles, only fetch children, do not fetch any other attributes
    if structural_roles and role in structural_roles:
        if depth < max_depth:
            children = safe_get_children(element) or []
            for idx, child in enumerate(children):
                if max_results is not None and len(results) >= max_results:
                    break
                t1 = _time.perf_counter()
                dynamic_crawl(child, results, max_depth, depth+1, parent_role=role, max_results=max_results,
                              button_roles=button_roles, structural_roles=structural_roles, skip_roles=skip_roles, parent_path=this_path, skip_identifiers=skip_identifiers, skip_descriptions=skip_descriptions)
                timing_stats['dynamic_crawl_recursion'] += _time.perf_counter() - t1
        timing_stats['dynamic_crawl'] += _time.perf_counter() - t0
        return results
    # Restore Finder-specific logic for AXList
    if role == 'AXList':
        children = safe_get_children(element) or []
        value = safe_getattr(element, 'AXTitle')
        if value is None:
            value = safe_getattr(element, 'AXValue')
        for idx, child in enumerate(children):
            if max_results is not None and len(results) >= max_results:
                break
            child_role = safe_getattr(child, 'AXRole')
            child_value = safe_getattr(child, 'AXTitle')
            if child_value is None:
                child_value = safe_getattr(child, 'AXValue')
            child_path = this_path + [{"role": role, "index": idx, "value": value}]
            if child_role == 'AXGroup':
                row_obj = extract_finder_file_row(child)
                row_obj['parent_path'] = child_path
                results.append(row_obj)
                if max_results is not None and len(results) >= max_results:
                    break
                continue
            t1 = _time.perf_counter()
            dynamic_crawl(child, results, max_depth, depth+1, parent_role=role, max_results=max_results,
                          button_roles=button_roles, structural_roles=structural_roles, skip_roles=skip_roles, parent_path=child_path, skip_identifiers=skip_identifiers, skip_descriptions=skip_descriptions)
            timing_stats['dynamic_crawl_recursion'] += _time.perf_counter() - t1
        timing_stats['dynamic_crawl'] += _time.perf_counter() - t0
        return results
    # Only fetch attributes for actionable roles
    if (button_roles and role in button_roles):
        ax_title = safe_getattr(element, 'AXTitle')
        if not ax_title:
            ax_title = safe_getattr(element, 'AXDescription')
        if not ax_title:
            ax_title = safe_getattr(element, 'title')
        if not ax_title or ax_title == 'unknown':
            timing_stats['dynamic_crawl'] += _time.perf_counter() - t0
            return results  # Skip this element if no identifiable information
        entry = {
            'AXRole': role,
            'AXTitle': ax_title,
            'AXHelp': safe_getattr(element, 'AXHelp'),
            'AXVisible': safe_getattr(element, 'AXVisible'),
            'AXFocused': safe_getattr(element, 'AXFocused'),
            'omeClick': extract_omeclick_with_role(element, role),
            'parent_path': this_path
        }
        if role == 'AXCell':
            entry['cell_details'] = extract_cell_details(element)
        results.append(entry)
        if max_results is not None and len(results) >= max_results:
            timing_stats['dynamic_crawl'] += _time.perf_counter() - t0
            return results
        timing_stats['dynamic_crawl'] += _time.perf_counter() - t0
        return results
    # If this is an AXRow, consolidate its AXCell children into one row object
    if role == 'AXRow':
        row_obj = extract_row_details(element)
        if row_obj is not None:
            row_obj['parent_path'] = this_path
            results.append(row_obj)
            if max_results is not None and len(results) >= max_results:
                timing_stats['dynamic_crawl'] += _time.perf_counter() - t0
                return results
        timing_stats['dynamic_crawl'] += _time.perf_counter() - t0
        return results
    # Fallback: if not in any set, just recurse
    if depth < max_depth:
        children = safe_get_children(element) or []
        for idx, child in enumerate(children):
            if max_results is not None and len(results) >= max_results:
                break
            t1 = _time.perf_counter()
            dynamic_crawl(child, results, max_depth, depth+1, parent_role=role, max_results=max_results,
                          button_roles=button_roles, structural_roles=structural_roles, skip_roles=skip_roles, parent_path=this_path, skip_identifiers=skip_identifiers, skip_descriptions=skip_descriptions)
            timing_stats['dynamic_crawl_recursion'] += _time.perf_counter() - t1
    timing_stats['dynamic_crawl'] += _time.perf_counter() - t0
    return results

def clean_entry(entry):
    # Recursively remove keys with None values
    if isinstance(entry, dict):
        return {k: clean_entry(v) for k, v in entry.items() if v is not None}
    elif isinstance(entry, list):
        return [clean_entry(i) for i in entry]
    else:
        return entry

def ordered_entry(entry):
    # Build an ordered dict for output
    from collections import OrderedDict
    out = OrderedDict()
    role = entry.get('AXRole')
    out['AXRole'] = role
    # Always put AXTitle second if present
    if 'AXTitle' in entry and entry['AXTitle'] is not None:
        out['AXTitle'] = entry['AXTitle']
    # For AXRow, add the rest except AXRole, AXTitle
    if role == 'AXRow':
        for k, v in entry.items():
            if k not in {'AXRole', 'AXTitle'} and v is not None:
                out[k] = v
    else:
        for k, v in entry.items():
            if k not in {'AXRole', 'AXTitle'} and v is not None:
                out[k] = v
    return out

def extract_omeclick(element):
    """
    Compatibility wrapper for external imports (e.g., appPicker_builder).
    Extracts the click point for an element, using its AXRole.
    """
    role = safe_getattr(element, 'AXRole')
    return extract_omeclick_with_role(element, role)

def build_nav_for_window(bundle_id, window_number=None, is_sheet=False, sheet_index=None, out_path=None, force=False, app_object=None):
    """
    Compatibility function for winD_controller.py and other modules.
    Calls the main() logic of the crawler with the appropriate arguments.
    """
    import sys
    sys.argv = ['appNav_builder.py', '--bundle', bundle_id]
    if out_path:
        sys.argv += ['--out', out_path]
    if force:
        sys.argv += ['--force']
    main(app_object=app_object)

def safe_getattr_textfield(obj, attr):
    try:
        return getattr(obj, attr, None)
    except (Exception, OMEA11yError):
        # Handle AX Error -25200 and similar: attribute does not exist or is invalid
        return None

def extract_omeclick_textfield(element):
    try:
        pos = safe_getattr_textfield(element, 'AXPosition')
        size = safe_getattr_textfield(element, 'AXSize')
        if pos and size and isinstance(pos, (list, tuple)) and isinstance(size, (list, tuple)):
            return [float(pos[0]) + float(size[0])/2, float(pos[1]) + float(size[1])/2]
    except Exception:
        pass
    return None

def find_label_for_field(field, sibling_static_texts):
    for attr in ('AXTitle', 'AXDescription', 'AXHelp', 'AXPlaceholderValue'):
        label = safe_getattr_textfield(field, attr)
        if label:
            return label
    if sibling_static_texts:
        return safe_getattr_textfield(sibling_static_texts[-1], 'AXValue')
    parent = safe_getattr_textfield(field, 'AXParent')
    if parent:
        for attr in ('AXTitle', 'AXDescription', 'AXHelp'):
            label = safe_getattr_textfield(parent, attr)
            if label:
                return label
    return None

def crawl_and_pair_textfields(element, bundle_id=None, results=None, custom_labels=None):
    if results is None:
        results = []
    if custom_labels is None:
        custom_labels = {}
    role = safe_getattr_textfield(element, 'AXRole')
    SKIP_ROLES = {'AXTable', 'AXList', 'AXRow', 'AXFinderRow'}
    if role in SKIP_ROLES:
        return results
    children = safe_getattr_textfield(element, 'AXChildren') or []
    if children:
        sibling_static_texts = []
        textfield_idx = 0
        for idx, child in enumerate(children):
            child_role = safe_getattr_textfield(child, 'AXRole')
            child_value = safe_getattr_textfield(child, 'AXValue')
            if child_role == 'AXStaticText':
                sibling_static_texts.append(child)
            elif child_role in ('AXTextField', 'AXSearchField'):
                # Use custom label if provided for this index
                label = None
                if str(textfield_idx) in custom_labels:
                    label = custom_labels[str(textfield_idx)]
                elif bundle_id == "com.apple.finder" and child_role in ("AXTextField", "AXSearchField"):
                    label = "Search Field"
                else:
                    label = find_label_for_field(child, sibling_static_texts)
                omeClick = extract_omeclick_textfield(child)
                entry = {
                    'AXRole': child_role,
                    'AXTitle': label,
                    'AXDescription': 'Text Input Field',
                    'value': child_value,
                    'omeClick': omeClick
                }
                results.append(entry)
                textfield_idx += 1
            elif child_role in ('AXWebArea', 'AXTextArea'):
                omeClick = extract_omeclick_textfield(child)
                entry = {
                    'AXRole': child_role,
                    'AXTitle': 'Body',
                    'AXDescription': 'Text Input Field',
                    'value': child_value,
                    'omeClick': omeClick
                }
                results.append(entry)
            crawl_and_pair_textfields(child, bundle_id=bundle_id, results=results, custom_labels=custom_labels)
    return results

def main(app_object=None):
    import time as _time
    wall_clock_start = _time.time()
    parser = argparse.ArgumentParser(description="Dynamically crawl the active window/sheet of a macOS app for actionable elements. Optionally, also crawl for text fields and labels.")
    parser.add_argument('--bundle', type=str, nargs='?', default=None, help='App bundle ID (default: current active bundle)')
    parser.add_argument('--debug', action='store_true', help='Print the accessibility tree structure for the first 3 levels')
    parser.add_argument('--force', action='store_true', help='Force overwrite of output file if it exists')
    parser.add_argument('--textfields', dest='textfields', action='store_true', help='Include text field/label output in the JSONL file (default: enabled)')
    parser.add_argument('--no-textfields', dest='textfields', action='store_false', help='Do NOT include text field/label output in the JSONL file')
    parser.set_defaults(textfields=True)
    args = parser.parse_args()

    bundle_id = args.bundle
    if not bundle_id:
        # Read from active_target_Bundle_ID.json
        active_target_path = os.path.join("ome", "data", "windows", "active_target_Bundle_ID.json")
        try:
            with open(active_target_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            bundle_id = data.get("active_bundle_id")
            if not bundle_id:
                print(f"[ERROR] No active_bundle_id found in {active_target_path}")
                sys.exit(1)
            print(f"[INFO] No bundle_id provided, using active_bundle_id from {active_target_path}: {bundle_id}")
        except Exception as e:
            print(f"[ERROR] Could not read {active_target_path}: {e}")
            sys.exit(1)

    # Time ensure_app_focus
    t_focus_start = _time.perf_counter()
    if app_object is not None:
        # Use provided app object (fast path)
        focus_result = {'status': 'success', 'app': app_object, 'bundle_id': bundle_id}
        print(f"[INFO] Using provided app object for {bundle_id}")
    else:
        # Focus app (slow path)
        focus_result = ensure_app_focus(bundle_id, fullscreen=True)
    t_focus_end = _time.perf_counter()
    timing_stats['ensure_app_focus'] = t_focus_end - t_focus_start

    if not (isinstance(focus_result, dict) and focus_result.get('status') == 'success'):
        print(f"Could not focus app: {focus_result}")
        sys.exit(1)
    canonical_bundle_id = focus_result.get('bundle_id')
    app = focus_result.get('app')

    # Time get_active_target_and_windows
    t_winD_start = _time.perf_counter()
    winD_info = get_active_target_and_windows_from_file(bundle_id=canonical_bundle_id)
    t_winD_end = _time.perf_counter()
    timing_stats['get_active_target_and_windows'] = t_winD_end - t_winD_start

    active_target = winD_info.get('active_target', {})
    window_ref = active_target.get('window_ref') or '*'
    bundle_id = canonical_bundle_id

    # Load config and resolve for this bundle_id and window_ref
    def load_crawler_config(config_path):
        with open(config_path, 'r', encoding='utf-8') as f:
            return [json.loads(line) for line in f if line.strip()]
    def get_config_for_context(config, bundle_id, window_ref):
        for rule in config:
            if rule['bundle_id'] == bundle_id and rule['window_ref'] == window_ref:
                return rule
        for rule in config:
            if rule['bundle_id'] == bundle_id and rule['window_ref'] == '*':
                return rule
        for rule in config:
            if rule['bundle_id'] == '*' and rule['window_ref'] == '*':
                return rule
        return {}
    config = load_crawler_config(UI_WINDOW_REF_MAP_CONFIG)
    context_config = get_config_for_context(config, bundle_id, window_ref)
    BUTTON_ROLES = set(context_config.get('button_roles', ["AXButton", "AXMenuButton", "AXPopUpButton", "AXCheckBox", "AXCell"]))
    STRUCTURAL_ROLES = set(context_config.get('structural_roles', [
        "AXWindow", "AXSheet", "AXGroup", "AXScrollArea", "AXSplitGroup", "AXTabGroup",
        "AXToolbar", "AXDrawer", "AXPopover", "AXSidebar", "AXUnknown", "AXOutline"
    ]))
    SKIP_ROLES = set(context_config.get('skip_roles', []))
    SKIP_IDENTIFIERS = set(context_config.get('skip_identifiers', []))
    SKIP_DESCRIPTIONS = set(context_config.get('skip_descriptions', []))
    MAX_DEPTH = context_config.get('max_depth', 10)
    MAX_LINES = context_config.get('max_lines', 120)
    custom_textfield_labels = context_config.get('textfield_labels', {})
    if window_ref:
        out_filename = f"appNav_{bundle_id}_{window_ref}.jsonl"
        out_path = os.path.join(UI_NAV_EXPORT_DIR, out_filename)
        os.makedirs(os.path.dirname(out_path), exist_ok=True)
    else:
        out_path = os.path.join(UI_NAV_EXPORT_DIR, "dynamic_window_crawler_output.jsonl")
        os.makedirs(os.path.dirname(out_path), exist_ok=True)

    # Add force check before writing output
    if os.path.exists(out_path) and not args.force:
        print(f"[INFO] Output file already exists: {out_path}. Use --force to overwrite.")
        sys.exit(0)

    container, context = find_active_window_or_sheet(app)
    if not container:
        print("No active window or sheet found.")
        sys.exit(1)
    if args.debug:
        print("\n[DEBUG] Accessibility tree structure (first 3 levels):")
        print_ax_tree(container, max_depth=3)
    print(f"Crawling {context} for actionable elements...")
    t_crawl_start = _time.perf_counter()
    results = dynamic_crawl(container, max_depth=MAX_DEPTH, max_results=MAX_LINES, button_roles=BUTTON_ROLES, structural_roles=STRUCTURAL_ROLES, skip_roles=SKIP_ROLES, skip_identifiers=SKIP_IDENTIFIERS, skip_descriptions=SKIP_DESCRIPTIONS)
    t_crawl_end = _time.perf_counter()
    print(f"\nFound {len(results)} actionable elements.")
    # Assign group priority and sort all results in one pass
    def get_priority(entry):
        if 'Kind' in entry:
            return 3
        if 'file_name' in entry and 'Kind' not in entry:
            return 2
        if ('Size' in entry or 'Date Modified' in entry) and 'Kind' not in entry and 'file_name' not in entry:
            return 1
        return 0
    def get_yx(entry):
        oc = entry.get('omeClick')
        if isinstance(oc, list) and len(oc) > 1:
            return (oc[1], oc[0])
        return (float('inf'), float('inf'))
    # Sort by (priority, y, x)
    results_sorted = sorted(results, key=lambda e: (get_priority(e), get_yx(e)))
    # Time file writing
    actionable_out_path = out_path
    if os.path.exists(actionable_out_path) and not args.force:
        print(f"[INFO] Output file already exists: {actionable_out_path}. Use --force to overwrite.")
        sys.exit(0)
    t_write_start = _time.perf_counter()
    with open(actionable_out_path, 'w', encoding='utf-8') as f:
        if args.textfields:
            print(f"Crawling {context} for text fields and labels (writing first)...")
            textfield_results = crawl_and_pair_textfields(container, bundle_id=bundle_id, custom_labels=custom_textfield_labels)
            for item in textfield_results:
                clean_item = {k: v for k, v in item.items() if v not in (None, "")}
                # Reorder keys: AXRole, AXTitle, AXDescription, then the rest
                ordered = {}
                for key in ['AXRole', 'AXTitle', 'AXDescription']:
                    if key in clean_item:
                        ordered[key] = clean_item.pop(key)
                ordered.update(clean_item)
                f.write(json.dumps(ordered, ensure_ascii=False) + '\n')
            print(f"[INFO] Wrote {len(textfield_results)} text field/label/body pairs to {actionable_out_path} (first)")
            # Write a separator line
            f.write('# --- ACTIONABLE ELEMENTS BELOW ---\n')
        for entry in results_sorted:
            clean = clean_entry(entry)
            ordered = ordered_entry(clean)
            f.write(json.dumps(ordered, ensure_ascii=False) + '\n')
    t_write_end = _time.perf_counter()
    timing_stats['file_write'] = t_write_end - t_write_start
    # Print group counts for info
    n_others = sum(1 for e in results_sorted if get_priority(e) == 0)
    n_size_date = sum(1 for e in results_sorted if get_priority(e) == 1)
    n_file_name = sum(1 for e in results_sorted if get_priority(e) == 2)
    n_kind = sum(1 for e in results_sorted if get_priority(e) == 3)
    print(f"Output written to {actionable_out_path} (textfields first: {args.textfields}) ({len(results)} actionable elements: {n_others} others, {n_size_date} size/date, {n_file_name} file_name-only, {n_kind} Kind)")
    print(f"Window ref: {window_ref}")
    wall_clock_end = _time.time()
    print(f"Total wall-clock time (all steps): {wall_clock_end - wall_clock_start:.2f} seconds.")
    print("\n[Timing Stats]")
    print(f"  ensure_app_focus: {timing_stats['ensure_app_focus']:.4f} s")
    print(f"  get_active_target_and_windows: {timing_stats['get_active_target_and_windows']:.4f} s")
    print(f"  safe_getattr: {timing_stats['safe_getattr']:.4f} s")
    print(f"  safe_get_children: {timing_stats['safe_get_children']:.4f} s")
    print(f"  file_write: {timing_stats['file_write']:.4f} s")

if __name__ == "__main__":
    main() 