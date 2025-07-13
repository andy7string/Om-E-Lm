#!/usr/bin/env python3
"""
ome/utils/uiNav/navBigDaDDy.py

========================================
navBigDaDDy Command Line Interface & Arguments Reference
========================================

This is the definitive, up-to-date list of ALL CLI arguments and flags supported by navBigDaDDy.
Each argument is shown with its purpose and example usage. All options are grouped by functionality.

-----------------------------
General/Info/Help
-----------------------------
--info, --status, --debug
    Show current window state, data counts, and debug info.
    Example: python -m ome.utils.uiNav.navBigDaDDy com.apple.mail --info
--help, -h
    Show help message and exit.
    Example: python -m ome.utils.uiNav.navBigDaDDy --help

-----------------------------
Element Find/Click
-----------------------------
--find DESCRIPTION
    Find an element by description (no click).
    Example: python -m ome.utils.uiNav.navBigDaDDy com.apple.mail --find "Send"
--click DESCRIPTION
    Find and click an element.
    Example: python -m ome.utils.uiNav.navBigDaDDy com.apple.mail --click "Send"

-----------------------------
Menu Find/Click/Navigate
-----------------------------
--find-menu TITLE
    Find a menu item by title (no click).
    Example: python -m ome.utils.uiNav.navBigDaDDy com.apple.mail --find-menu "File"
--click-menu TITLE
    Find and click a menu item.
    Example: python -m ome.utils.uiNav.navBigDaDDy com.apple.mail --click-menu "File"
--nav-menu PATH [PATH ...], --navigate PATH [PATH ...]
    Navigate a menu path (e.g., File > New Message).
    Example: python -m ome.utils.uiNav.navBigDaDDy com.apple.mail --nav-menu File "New Message"

-----------------------------
Element/Menu/Picker/Message List Listing
-----------------------------
--list-elements, --elements
    List all available actionable elements in the current window.
    Example: python -m ome.utils.uiNav.navBigDaDDy com.apple.mail --list-elements
--list-menus, --menus
    List all available menu items.
    Example: python -m ome.utils.uiNav.navBigDaDDy com.apple.mail --list-menus
--list-pickers, --pickers
    List all available picker items.
    Example: python -m ome.utils.uiNav.navBigDaDDy com.apple.mail --list-pickers
--list-messages, --messages
    List all available messages in the message list.
    Example: python -m ome.utils.uiNav.navBigDaDDy com.apple.mail --list-messages

-----------------------------
Picker Find/Click/Select/Show/Refresh
-----------------------------
--find-picker TITLE
    Find a picker item by title (no click).
    Example: python -m ome.utils.uiNav.navBigDaDDy com.apple.mail --find-picker "document.pdf"
--click-picker TITLE
    Find and click a picker item.
    Example: python -m ome.utils.uiNav.navBigDaDDy com.apple.mail --click-picker "document.pdf"
--select-picker-row [N]
    Select/focus a specific picker row (1-based, defaults to 1 if no value).
    Example: python -m ome.utils.uiNav.navBigDaDDy com.apple.mail --select-picker-row 3
             python -m ome.utils.uiNav.navBigDaDDy com.apple.mail --select-picker-row
--show-picker-jsonl, --picker-jsonl
    Show raw picker JSONL data.
    Example: python -m ome.utils.uiNav.navBigDaDDy com.apple.mail --show-picker-jsonl
--show-picker-path, --picker-path
    Show path to picker JSONL file.
    Example: python -m ome.utils.uiNav.navBigDaDDy com.apple.mail --show-picker-path
--refresh-picker
    Force refresh picker data.
    Example: python -m ome.utils.uiNav.navBigDaDDy com.apple.mail --refresh-picker

-----------------------------
Message List Find/Click/Select/Show/Refresh
-----------------------------
--find-message CRITERIA
    Find a message by subject (default, partial match, case-insensitive).
    Example: python -m ome.utils.uiNav.navBigDaDDy com.apple.mail --find-message "Meeting"
    Advanced (Python only): nav.find_message("bob@example.com", search_type="sender_email")
    search_type options: 'subject', 'sender', 'sender_email', 'message_key', 'row_index'
--click-message CRITERIA
    Find and click a message by subject.
    Example: python -m ome.utils.uiNav.navBigDaDDy com.apple.mail --click-message "Meeting"
--select-message-row [N]
    Select/focus a specific message row (1-based, defaults to 1 if no value).
    Example: python -m ome.utils.uiNav.navBigDaDDy com.apple.mail --select-message-row 5
             python -m ome.utils.uiNav.navBigDaDDy com.apple.mail --select-message-row
--send-keys-after-select
    (Used with --select-message-row) Send Enter key after selecting the message row (for opening message in a new window).
    Example: python -m ome.utils.uiNav.navBigDaDDy com.apple.mail --select-message-row 5 --send-keys-after-select
--show-message-jsonl, --message-jsonl
    Show raw message JSONL data.
    Example: python -m ome.utils.uiNav.navBigDaDDy com.apple.mail --show-message-jsonl
--show-message-path, --message-path
    Show path to message JSONL file.
    Example: python -m ome.utils.uiNav.navBigDaDDy com.apple.mail --show-message-path
--refresh-messages
    Force refresh message list data.
    Example: python -m ome.utils.uiNav.navBigDaDDy com.apple.mail --refresh-messages

-----------------------------
Window Controls
-----------------------------
--close
    Close the current window.
    Example: python -m ome.utils.uiNav.navBigDaDDy com.apple.mail --close
--minimize
    Minimize the current window.
    Example: python -m ome.utils.uiNav.navBigDaDDy com.apple.mail --minimize
--maximize
    Maximize the current window.
    Example: python -m ome.utils.uiNav.navBigDaDDy com.apple.mail --maximize
--window-controls
    List available window control buttons.
    Example: python -m ome.utils.uiNav.navBigDaDDy com.apple.mail --window-controls

-----------------------------
Menu Data Refresh
-----------------------------
--refresh-menu
    Force refresh menu data.
    Example: python -m ome.utils.uiNav.navBigDaDDy com.apple.mail --refresh-menu

-----------------------------
Legacy/Positional Arguments
-----------------------------
bundle_id
    The bundle ID of the app (e.g., com.apple.mail). Required for most commands.
command, args
    Legacy command/argument support (not recommended; use --flags above).

========================================

Unified Navigation Controller for Om-E-Mac

Main Purpose:
- Reads real-time window state and active_target from event-listener-updated files (win_<bundleid>.jsonl).
- Loads the actionable elements for the current window (from appNav JSONL).
- Loads the menu structure (from menu JSONL).
- Loads associated data (e.g., picker files) based on config.
- Auto-builds missing nav and menu files using appNav_builder and appMenu_builder.
- Exposes helpers to find elements in the current window or menu.
- Designed to be the single source of navigation truth for automation workflows.

Key Features:
- Always fresh: Reads win_<bundleid>.jsonl on instantiation for current window state.
- Auto-builds missing files: Calls appNav_builder and appMenu_builder as needed.
- Works for any app with the correct nav/menu files.
- Config-driven associations: Loads extra data (pickers, etc.) based on bundle_id + window_ref.
- Uses all env variables: Properly references NAV_EXPORT_DIR, MENU_EXPORT_DIR, etc.
- Simple API: .active_target, .window_nav_entries, .menu_entries, .picker_entries, .find_element(), .find_menu_item()
- No cache or temp files; only reads from ome/data/.

How to Use (Import):
    from ome.utils.uiNav.navBigDaDDy import navBigDaDDy
    nav = navBigDaDDy("com.apple.mail")
    print(nav.active_target)
    el = nav.find_element("Send")
    picker_el = nav.find_picker_item("document.pdf")

When to Use:
- To get the current actionable UI elements and menu structure for an app.
- For automation, accessibility, or UI testing.
- As the navigation layer for higher-level workflow controllers.
"""

import os
import sys
import json
import time
import subprocess

# Add the project root to the Python path so we can import ome modules
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from ome.utils.env.env import NAV_EXPORT_DIR, MENU_EXPORT_DIR, PICKER_EXPORT_DIR, ACTION_DELAY, MENU_ITEM_CLICK_DELAY
from ome.utils.builder.app.app_focus import ensure_app_focus

def get_active_target_and_windows_from_file(bundle_id=None):
    """
    Preferred method: Reads the active bundle id from active_target_Bundle_ID.json and loads
    the corresponding win_<bundleid>.jsonl file, returning the same structure as get_active_target_and_windows.
    If bundle_id is not provided, it is read from the JSON file.
    """
    import json
    import os
    def get_active_bundle_id(json_path="ome/data/windows/active_target_Bundle_ID.json"):
        try:
            with open(json_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            return data.get("active_bundle_id")
        except Exception as e:
            print(f"[navBigDaDDy] Error reading active bundle ID: {e}")
            return None

    if not bundle_id:
        bundle_id = get_active_bundle_id()
    if not bundle_id:
        raise ValueError("No active bundle ID found.")
    win_file = f"ome/data/windows/win_{bundle_id}.jsonl"
    if not os.path.exists(win_file):
        raise FileNotFoundError(f"Window state file not found: {win_file}")
    with open(win_file, "r", encoding="utf-8") as f:
        data = json.load(f)
    return {
        "active_target": data.get("active_target"),
        "windows": data.get("windows", []),
        "bundle_id": data.get("bundle_id"),
        "app_name": data.get("app_name"),
        "last_updated": data.get("last_updated"),
        "source": data.get("source"),
    }

class navBigDaDDy:
    """
    Unified navigation controller for a given app (by bundle_id).
    Reads real-time window state and navigation data from event-listener-updated files (win_<bundleid>.jsonl).
    Auto-builds missing files using appNav_builder and appMenu_builder.
    """
    def __init__(self, bundle_id, app=None):
        t0 = time.time()
        self.bundle_id = bundle_id
        self._cached_app = app
        self._cached_focus_time = time.time() if app else 0
        self.config_path = "ome/utils/uiNav/config/navBigDaDDy_config.jsonl"
        self._focus_cache_duration = 5.0
        self._picker_cache_time = 0
        self._picker_cache_duration = 30.0
        self._message_list_cache_time = 0
        self._message_list_cache_duration = 60.0
        self._menu_cache_time = 0
        self._menu_cache_duration = 60.0
        self.active_target = {}
        self.windows = []
        # Always ensure app is focused before reading nav state
        # (App focus is required for reliable navigation and UI automation)
        from ome.utils.builder.app.app_focus import ensure_app_focus
        focus_result = ensure_app_focus(self.bundle_id, fullscreen=True)
        if focus_result.get('status') == 'success':
            self._cached_app = focus_result.get('app')
            self._cached_focus_time = time.time()
        self._get_fresh_window_state()
        t1 = time.time()
        print(f"[TIMER] navBigDaDDy._get_fresh_window_state: {t1-t0:.3f}s")
        t2 = time.time()
        print(f"[TIMER] navBigDaDDy.__init__ total: {t2-t0:.3f}s")

    def _get_cached_or_fresh_app(self):
        """Get cached app object or focus fresh one if needed"""
        current_time = time.time()
        # Use provided app if available
        if self._cached_app:
            return self._cached_app
        # Focus fresh app and cache it
        focus_result = ensure_app_focus(self.bundle_id, fullscreen=True)
        if focus_result.get('status') == 'success':
            self._cached_app = focus_result.get('app')
            self._cached_focus_time = current_time
            return self._cached_app
        return None

    def _get_fresh_window_state(self):
        t0 = time.time()
        """Reads file-based window state for real-time event-listener-updated state (win_<bundleid>.jsonl)"""
        from ome.utils.env.env import MENU_WAIT_DELAY
        time.sleep(MENU_WAIT_DELAY)
        # app = self._get_cached_or_fresh_app()  # No longer needed for file-based
        t1 = time.time()
        win_state = get_active_target_and_windows_from_file(bundle_id=self.bundle_id)
        t2 = time.time()
        print(f"[TIMER] get_active_target_and_windows_from_file: {t2-t1:.3f}s")
        if win_state is None:
            self.active_target = {}
            self.windows = []
            self.nav_map_name = None
            return
        self.active_target = win_state.get('active_target', {})
        self.windows = win_state.get('windows', [])
        if self.active_target is None:
            self.active_target = {}
        self.nav_map_name = self.active_target.get('nav_map_name')
        t3 = time.time()
        print(f"[TIMER] _get_fresh_window_state (core): {t3-t0:.3f}s")
        
        # Load all navigation data based on current active_target
        self._load_config()
        t4 = time.time()
        print(f"[TIMER] navBigDaDDy._load_config: {t4-t3:.3f}s")
        self._load_window_nav()
        t5 = time.time()
        print(f"[TIMER] navBigDaDDy._load_window_nav: {t5-t4:.3f}s")
        self._load_menu_nav()
        t6 = time.time()
        print(f"[TIMER] navBigDaDDy._load_menu_nav: {t6-t5:.3f}s")
        self._load_associations()
        t7 = time.time()
        print(f"[TIMER] navBigDaDDy._load_associations: {t7-t6:.3f}s")

        # Always refresh picker data if this is a FilePicker window
        if self.active_target.get('window_ref') == "FilePicker":
            pass  # or comment out
            print("[navBigDaDDy] Detected FilePicker window - always refreshing picker data for fresh state")
            self.refresh_picker_data()
        t8 = time.time()
        print(f"[TIMER] navBigDaDDy.__init__ total: {t8-t0:.3f}s")

    def _load_config(self):
        """
        Loads the navigation config to determine what associated data to load.
        Sets self.current_config (dict) and self.associations (dict).
        """
        if not os.path.exists(self.config_path):
            self.current_config = {}
            self.associations = {}
            return
        
        # Handle case where app is closed and active_target is empty
        if not self.active_target:
            pass  # or comment out
            print(f"[navBigDaDDy] App {self.bundle_id} appears to be closed - using default config")
            self.current_config = {}
            self.associations = {}
            return
            
        configs = []
        with open(self.config_path, 'r', encoding='utf-8') as f:
            for line in f:
                try:
                    config = json.loads(line.strip())
                    configs.append(config)
                except json.JSONDecodeError:
                    continue
        # Find config for current bundle_id and window_ref
        window_ref = self.active_target.get('window_ref')
        self.current_config = {}
        self.associations = {}
        
        # First try exact match
        for config in configs:
            if (config.get('bundle_id') == self.bundle_id and 
                config.get('window_ref') == window_ref):
                self.current_config = config
                self.associations = config.get('associations', {})
                return
        
        # Fallback to wildcard match
        for config in configs:
            if (config.get('bundle_id') == self.bundle_id and 
                config.get('window_ref') == '*'):
                self.current_config = config
                self.associations = config.get('associations', {})
                return

    def _load_window_nav(self):
        """
        Loads the actionable elements for the current window (from appNav JSONL).
        Uses nav_map_name from the real-time state file if available, otherwise falls back to old logic.
        Sets self.window_nav_entries (list).
        """
        if not isinstance(self.active_target, dict) or not self.active_target:
            pass  # or comment out
            print(f"[navBigDaDDy] No active target, attempting to focus app...")
            self._get_fresh_window_state()
            if not isinstance(self.active_target, dict) or not self.active_target:
                print(f"[navBigDaDDy] Still no active target after focusing app. Aborting window nav load.")
                self.window_nav_entries = []
                return

        nav_path = None
        window_ref = self.active_target.get('window_ref')
        if hasattr(self, 'nav_map_name') and self.nav_map_name:
            from ome.utils.env.env import NAV_EXPORT_DIR
            nav_path = os.path.join(NAV_EXPORT_DIR, self.nav_map_name)
        else:
            if not window_ref:
                self.window_nav_entries = []
                return
            nav_filename = f"appNav_{self.bundle_id}_{window_ref}.jsonl"
            from ome.utils.env.env import NAV_EXPORT_DIR
            nav_path = os.path.join(NAV_EXPORT_DIR, nav_filename)

        # Refined logic for when to rebuild nav files
        if window_ref in ["FilePicker", "SendMessageAlert"]:
            should_build = True  # Always rebuild for these
            force_rebuild = True
        elif window_ref and window_ref.startswith("_NS:"):
            should_build = nav_path is None or not os.path.exists(nav_path)  # Only build if missing
            force_rebuild = False
        elif window_ref and "sheet" in window_ref.lower():
            should_build = True  # Always rebuild for sheets
            force_rebuild = True
        else:
            should_build = nav_path is None or not os.path.exists(nav_path)
            force_rebuild = False

        if should_build:
            pass  # or comment out
            print(f"[navBigDaDDy] Nav file not found or always-rebuild window: {nav_path}")
            print(f"[navBigDaDDy] Building nav for {self.bundle_id} window_ref: {window_ref}")
            try:
                from ome.utils.builder.app.appNav_builder import build_nav_for_window
                build_nav_for_window(self.bundle_id, app_object=self._cached_app, force=force_rebuild)
                print(f"[navBigDaDDy] Successfully built nav file: {nav_path}")
            except Exception as e:
                print(f"[navBigDaDDy] Failed to build nav file: {e}")
                self.window_nav_entries = []
                return
        entries = []
        if nav_path and os.path.exists(nav_path):
            with open(nav_path, 'r', encoding='utf-8') as f:
                for line in f:
                    try:
                        entry = json.loads(line.strip())
                        entries.append(entry)
                    except json.JSONDecodeError:
                        continue
        self.window_nav_entries = entries

    def _load_menu_nav(self):
        """
        Loads the menu structure for the app (from menu JSONL).
        Uses exact same logic as appMenu_builder: menu_{bundle_id}.jsonl
        If menu file doesn't exist, calls appMenu_builder to create it.
        Sets self.menu_entries (list).
        """
        # Menu file naming convention: menu_{bundle_id}.jsonl (same as appMenu_builder)
        menu_filename = f"menu_{self.bundle_id}.jsonl"
        menu_path = os.path.join(MENU_EXPORT_DIR, menu_filename)
        
        # Priority 1: If file exists, use it (fast path)
        if os.path.exists(menu_path):
            # Load the menu entries
            entries = []
            with open(menu_path, 'r', encoding='utf-8') as f:
                for line in f:
                    try:
                        entry = json.loads(line.strip())
                        entries.append(entry)
                    except json.JSONDecodeError:
                        continue
            self.menu_entries = entries
            print(f"[navBigDaDDy] Loaded {len(entries)} menu entries from existing file: {menu_path}")
            return
        
        # Priority 2: Only build if file doesn't exist
        print(f"[navBigDaDDy] Menu file not found: {menu_path}")
        print(f"[navBigDaDDy] Building menu for {self.bundle_id}")
        
        try:
            from ome.utils.builder.app.appMenu_builder import build_menu
            
            # Call builder with cached app object to avoid double focusing
            build_menu(self.bundle_id, filter_mode='all', app_object=self._cached_app)
            print(f"[navBigDaDDy] Successfully built menu file: {menu_path}")
            
            # Load the newly built menu entries
            entries = []
            with open(menu_path, 'r', encoding='utf-8') as f:
                for line in f:
                    try:
                        entry = json.loads(line.strip())
                        entries.append(entry)
                    except json.JSONDecodeError:
                        continue
            self.menu_entries = entries
            print(f"[navBigDaDDy] Loaded {len(entries)} menu entries from newly built file")
            
        except Exception as e:
            print(f"[navBigDaDDy] Failed to build menu file: {e}")
            self.menu_entries = []

    def _load_associations(self):
        """
        Loads associated data files based on config associations.
        Uses env.py paths and resolves placeholders like <PICKER_EXPORT_DIR>.
        Only loads data files if they exist. Does not run builder scripts on every window/context load.
        """
        # Always initialize these attributes
        self.picker_entries = []
        self.message_list_entries = []
        
        if not self.current_config or not self.current_config.get('associations'):
            return
        associations = self.current_config['associations']
        # Handle picker associations
        if 'picker_jsonl' in associations:
            picker_jsonl_path = associations['picker_jsonl']
            if '<PICKER_EXPORT_DIR>' in picker_jsonl_path:
                from ome.utils.env.env import PICKER_EXPORT_DIR
                picker_jsonl_path = picker_jsonl_path.replace('<PICKER_EXPORT_DIR>', PICKER_EXPORT_DIR)
            if os.path.exists(picker_jsonl_path):
                try:
                    with open(picker_jsonl_path, 'r', encoding='utf-8') as f:
                        for line in f:
                            try:
                                entry = json.loads(line.strip())
                                self.picker_entries.append(entry)
                            except json.JSONDecodeError:
                                continue
                    print(f"[navBigDaDDy] Loaded {len(self.picker_entries)} picker entries from {picker_jsonl_path}")
                except Exception as e:
                    print(f"[navBigDaDDy] Error loading picker data: {e}")
            else:
                print(f"[navBigDaDDy] Picker JSONL file not found: {picker_jsonl_path}")
                # TODO: Run builder script on demand if needed
        # Handle message list associations
        if 'message_list_jsonl' in associations:
            message_list_jsonl_path = associations['message_list_jsonl']
            if '<MESSAGE_EXPORT_DIR>' in message_list_jsonl_path:
                from ome.utils.env.env import MESSAGE_EXPORT_DIR
                message_list_jsonl_path = message_list_jsonl_path.replace('<MESSAGE_EXPORT_DIR>', MESSAGE_EXPORT_DIR)
            if os.path.exists(message_list_jsonl_path):
                try:
                    with open(message_list_jsonl_path, 'r', encoding='utf-8') as f:
                        for line in f:
                            try:
                                entry = json.loads(line.strip())
                                self.message_list_entries.append(entry)
                            except json.JSONDecodeError:
                                continue
                    print(f"[navBigDaDDy] Loaded {len(self.message_list_entries)} message list entries from {message_list_jsonl_path}")
                except Exception as e:
                    print(f"[navBigDaDDy] Error loading message list data: {e}")
            else:
                print(f"[navBigDaDDy] Message list JSONL file not found: {message_list_jsonl_path}")
                # TODO: Run builder script on demand if needed

    def refresh(self):
        """
        Smart refresh: calls winD_controller and only reloads data if active_target changed.
        Much faster than full refresh - only updates what's needed.
        """
        # COMMENTED OUT - user wants direct control
        # print(f"[navBigDaDDy] Smart refresh for {self.bundle_id}")
        # 
        # # Get fresh window state
        # old_active_target = self.active_target
        # self._get_fresh_window_state()
        # new_active_target = self.active_target
        # 
        # # Check if active_target changed
        # if old_active_target.get('window_ref') != new_active_target.get('window_ref'):
        #     print(f"[navBigDaDDy] Active target changed: {old_active_target.get('window_ref')} -> {new_active_target.get('window_ref')}")
        #     
        #     # Reload config and nav data for new window
        #     self._load_config()
        #     self._load_window_nav()
        #     self._load_associations()
        #     
        #     print(f"[navBigDaDDy] Loaded nav data for new window: {len(self.window_nav_entries)} entries")
        # else:
        #     print(f"[navBigDaDDy] Active target unchanged: {new_active_target.get('window_ref')}")
        #     # Only reload nav data if file is missing (in case it was deleted)
        #     window_ref = self.active_target.get('window_ref')
        #     if window_ref:
        #         nav_filename = f"appNav_{self.bundle_id}_{window_ref}.jsonl"
        #         nav_path = os.path.join(NAV_EXPORT_DIR, nav_filename)
        #         if not os.path.exists(nav_path):
        #             print(f"[navBigDaDDy] Nav file missing, rebuilding...")
        #             self._load_config()
        #             self._load_window_nav()
        #             self._load_associations()
        # 
        # print(f"[navBigDaDDy] Smart refresh complete - Active target: {self.active_target.get('window_ref')}")
        pass

    def _ensure_app_focus_before_action(self):
        """
        Ensures the app is focused before performing any action.
        Calls winD_controller to refresh window state.
        """
        try:
            # Call the app focus function
            ensure_app_focus(self.bundle_id)
            # Refresh window state
            self._get_fresh_window_state()
            return True
        except Exception as e:
            print(f"[navBigDaDDy] Error ensuring app focus: {e}")
            return False

    def ensure_app_focus(self):
        """
        Public method to ensure app focus.
        Returns True if successful, False otherwise.
        """
        return self._ensure_app_focus_before_action()
    
    def refresh_picker_data(self):
        """
        Force refresh picker data by clearing cache and rebuilding.
        Returns True if successful, False otherwise.
        """
        try:
            from ome.utils.builder.app.appPicker_builder import build_picker_data
            print(f"[navBigDaDDy] Refreshing picker data for {self.bundle_id}")
            
            # Build fresh picker data using cached app object
            result = build_picker_data(self.bundle_id, app_object=self._cached_app)
            
            if result.get("status") == "success":
                row_count = result.get('row_count', 0)
                print(f"[navBigDaDDy] Successfully rebuilt picker data: {row_count} rows")
                # Reload the picker data
                self._picker_cache_time = 0  # Clear cache
                self._load_associations()  # This will reload the newly built picker data
                return True
            else:
                error_msg = result.get('error', 'Unknown error')
                print(f"[navBigDaDDy] Failed to rebuild picker data: {error_msg}")
                return False
        except Exception as e:
            print(f"[navBigDaDDy] Error refreshing picker data: {e}")
            return False
    def _call_winD_after_action(self):
        """
        Refreshes window state and associations after every action because the UI may have changed.
        Now uses the real-time event-listener-updated state file (win_<bundleid>.jsonl).
        """
        old_active_target = self.active_target.copy() if self.active_target else {}
        self._get_fresh_window_state()
        new_active_target = self.active_target
        
        # Check if active target changed (e.g., different mailbox selected)
        if (old_active_target.get('window_ref') != new_active_target.get('window_ref') or
            old_active_target.get('window_title') != new_active_target.get('window_title')):
            print(f"[navBigDaDDy] Active target changed after action: {old_active_target.get('window_ref')} -> {new_active_target.get('window_ref')}")
            print(f"[navBigDaDDy] Reloading associations for new context...")
            
            # Reload config and associations for new window context
            self._load_config()
            self._load_associations()
            
            print(f"[navBigDaDDy] Associations reloaded - message list: {len(self.message_list_entries)} entries, picker: {len(self.picker_entries)} entries")
        else:
            print(f"[navBigDaDDy] Called winD after action - Active target unchanged: {new_active_target.get('window_ref')}")

    def find_element(self, description):
        """
        Finds an actionable element in the current window by AXTitle (exact or partial match).
        Returns the element dict or None if not found.
        """
        for entry in self.window_nav_entries:
            if entry.get('AXTitle') == description:
                return entry
        for entry in self.window_nav_entries:
            if description.lower() in entry.get('AXTitle', '').lower():
                return entry
        return None

    def find_menu_item(self, title):
        """
        Finds a menu item using menuPath_controller's robust path-based search.
        This provides better outcomes for things like "send message".
        Returns the menu item dict or None if not found.
        """
        try:
            from ome.utils.uiNav.menuPath_controller import get_menu_path_by_path
            result = get_menu_path_by_path(title, self.bundle_id)
            return result
        except Exception as e:
            print(f"[navBigDaDDy] Error finding menu item '{title}': {e}")
            return None

    def find_picker_item(self, title):
        """
        Finds a picker item by file_name or AXTitle (exact or partial match).
        Returns the picker item dict or None if not found.
        """
        for entry in self.picker_entries:
            # Check file_name first (picker entries)
            if entry.get('file_name') == title:
                return entry
            # Check AXTitle (navigation elements)
            if entry.get('AXTitle') == title:
                return entry
        for entry in self.picker_entries:
            # Partial match on file_name
            if title.lower() in entry.get('file_name', '').lower():
                return entry
            # Partial match on AXTitle
            if title.lower() in entry.get('AXTitle', '').lower():
                return entry
        return None

    def click_at_coordinates(self, x, y, description="custom click"):
        """
        Clicks at specific coordinates, then does smart refresh.
        Returns True if successful, False otherwise.
        
        Args:
            x (int): X coordinate to click
            y (int): Y coordinate to click
            description (str): Description for logging purposes
        """
        import pyautogui
        try:
            print(f"[navBigDaDDy] Clicking {description} at ({x}, {y})")
            pyautogui.click(x, y)
            # Only refresh state after the click
            self._call_winD_after_action()
            return True
        except Exception as e:
            print(f"[navBigDaDDy] Error clicking at coordinates ({x}, {y}): {e}")
            return False

    def click_element(self, description):
        """
        Finds and clicks an element, then does smart refresh.
        Returns True if successful, False otherwise.
        """
        import pyautogui
        # Ensure app is focused
        if not self._ensure_app_focus_before_action():
            return False
        element = self.find_element(description)
        if element and element.get('omeClick'):
            x, y = element['omeClick']
            print(f"[navBigDaDDy] Clicking {description} at ({x}, {y})")
            pyautogui.click(x, y)
            time.sleep(ACTION_DELAY)
            # Call winD after action because 'shit changes'
            self._call_winD_after_action()
            return True
        print(f"[navBigDaDDy] Element '{description}' not found or has no omeClick")
        return False

    def click_picker_item(self, title):
        """
        Finds and clicks a picker item, then does smart refresh.
        Returns True if successful, False otherwise.
        """
        import pyautogui
        # Ensure app is focused
        if not self._ensure_app_focus_before_action():
            return False
        item = self.find_picker_item(title)
        if item and item.get('omeClick'):
            x, y = item['omeClick']
            print(f"[navBigDaDDy] Clicking picker item {title} at ({x}, {y})")
            pyautogui.click(x, y)
            time.sleep(ACTION_DELAY)
            # Call winD after action because 'shit changes'
            self._call_winD_after_action()
            return True
        print(f"[navBigDaDDy] Picker item '{title}' not found or has no omeClick")
        return False

    def click_menu_item(self, title):
        """
        Finds and clicks a menu item using menuPath_controller's robust navigation.
        This provides better outcomes for things like "send message".
        Returns True if successful, False otherwise.
        """
        # Ensure app is focused
        if not self._ensure_app_focus_before_action():
            return False
        try:
            from ome.utils.uiNav.menuPath_controller import menu_nav
            print(f"[navBigDaDDy] Clicking menu item using menuPath_controller: {title}")
            
            # Use menuPath_controller's tested navigation
            menu_nav("path", title, self.bundle_id)
            
            time.sleep(MENU_ITEM_CLICK_DELAY)
            # Call winD after action because 'shit changes'
            self._call_winD_after_action()
            return True
                
        except Exception as e:
            print(f"[navBigDaDDy] Error clicking menu item '{title}': {e}")
            return False

    def navigate_menu_path(self, menu_path):
        """
        Navigates a menu path using menuPath_controller's robust navigation.
        This provides better outcomes for things like "send message".
        Returns True if successful, False otherwise.
        """
        # Ensure app is focused
        if not self._ensure_app_focus_before_action():
            return False
        try:
            from ome.utils.uiNav.menuPath_controller import menu_nav
            print(f"[navBigDaDDy] Navigating menu path using menuPath_controller: {' > '.join(menu_path)}")
            
            # Join the menu path for menuPath_controller
            path_label = ' > '.join(menu_path)
            
            # Use menuPath_controller's tested navigation
            menu_nav("path", path_label, self.bundle_id)
            
            time.sleep(MENU_ITEM_CLICK_DELAY)
            # Call winD after action because 'shit changes'
            self._call_winD_after_action()
            return True
                
        except Exception as e:
            print(f"[navBigDaDDy] Error navigating menu path: {e}")
            return False

    def select_picker_row(self, row_index):
        """
        Select/focus a specific row in the picker using direct accessibility API control.
        Uses appPicker_builder's select_row_direct logic.
        Returns True if successful, False otherwise.
        """
        # Ensure app is focused
        if not self._ensure_app_focus_before_action():
            return False
        
        try:
            from ome.utils.builder.app.appPicker_builder import select_row_direct
            print(f"[navBigDaDDy] Selecting picker row {row_index} using direct accessibility control")
            
            # Use appPicker_builder's tested row selection with cached app object
            success = select_row_direct(self.bundle_id, row_index, app_object=self._cached_app)
            
            if success:
                time.sleep(ACTION_DELAY)
                # Call winD after action because 'shit changes'
                self._call_winD_after_action()
                return True
            else:
                print(f"[navBigDaDDy] Failed to select picker row {row_index}")
                return False
                
        except Exception as e:
            print(f"[navBigDaDDy] Error selecting picker row {row_index}: {e}")
            return False

    def get_picker_jsonl_path(self):
        """
        Returns the path to the picker JSONL file for the current bundle_id.
        Uses env.py PICKER_EXPORT_DIR.
        """
        from ome.utils.env.env import PICKER_EXPORT_DIR
        return os.path.join(PICKER_EXPORT_DIR, f"picker_{self.bundle_id}.jsonl")

    def get_picker_data(self):
        """
        Returns the raw picker JSONL data as a list of dicts.
        Useful for seeing what's in the picker.
        """
        picker_path = self.get_picker_jsonl_path()
        if not os.path.exists(picker_path):
            print(f"[navBigDaDDy] Picker JSONL not found: {picker_path}")
            return []
        
        picker_data = []
        try:
            with open(picker_path, 'r', encoding='utf-8') as f:
                for line in f:
                    try:
                        entry = json.loads(line.strip())
                        picker_data.append(entry)
                    except json.JSONDecodeError:
                        continue
            print(f"[navBigDaDDy] Loaded {len(picker_data)} picker entries from {picker_path}")
        except Exception as e:
            print(f"[navBigDaDDy] Error loading picker data: {e}")
        
        return picker_data

    def get_active_window_object(self):
        """
        Gets the active window object directly from the app using the same logic as app_focus.py.
        Returns the window object or None if not found.
        """
        try:
            from ome.utils.builder.app.app_focus import ensure_app_focus
            
            # Focus the app to get the app object
            focus_result = ensure_app_focus(self.bundle_id)
            if focus_result.get('status') != 'success':
                print(f"[navBigDaDDy] Could not focus app: {focus_result.get('error')}")
                return None
            
            app = focus_result.get('app')
            if not app:
                return None
            
            # Get the active window using the same logic as app_focus.py
            if hasattr(app, 'AXWindows') and app.AXWindows:
                # Return the first window (usually the active one)
                return app.AXWindows[0]
            
            return None
            
        except Exception as e:
            print(f"[navBigDaDDy] Error getting active window: {e}")
            return None

    def get_window_control_buttons(self):
        """
        Gets window control buttons directly from window properties (AXCloseButton, AXMinimizeButton, AXZoomButton).
        Much more efficient than crawling the hierarchy.
        Returns a list of window control buttons with their coordinates.
        """
        window = self.get_active_window_object()
        if not window:
            return []
        
        controls = []
        
        try:
            # Get window control buttons directly from window properties
            close_button = getattr(window, 'AXCloseButton', None)
            minimize_button = getattr(window, 'AXMinimizeButton', None)
            zoom_button = getattr(window, 'AXZoomButton', None)
            
            # Process close button
            if close_button:
                try:
                    pos = getattr(close_button, 'AXPosition', None)
                    size = getattr(close_button, 'AXSize', None)
                    
                    if pos and size and len(pos) == 2 and len(size) == 2:
                        x = pos[0] + size[0] / 2
                        y = pos[1] + size[1] / 2
                        
                        controls.append({
                            'title': getattr(close_button, 'AXTitle', 'Close'),
                            'role': getattr(close_button, 'AXRole', 'AXButton'),
                            'type': 'close',
                            'omeClick': [x, y],
                            'position': pos,
                            'size': size
                        })
                except Exception as e:
                    print(f"[navBigDaDDy] Error processing close button: {e}")
            
            # Process minimize button
            if minimize_button:
                try:
                    pos = getattr(minimize_button, 'AXPosition', None)
                    size = getattr(minimize_button, 'AXSize', None)
                    
                    if pos and size and len(pos) == 2 and len(size) == 2:
                        x = pos[0] + size[0] / 2
                        y = pos[1] + size[1] / 2
                        
                        controls.append({
                            'title': getattr(minimize_button, 'AXTitle', 'Minimize'),
                            'role': getattr(minimize_button, 'AXRole', 'AXButton'),
                            'type': 'minimize',
                            'omeClick': [x, y],
                            'position': pos,
                            'size': size
                        })
                except Exception as e:
                    print(f"[navBigDaDDy] Error processing minimize button: {e}")
            
            # Process zoom button
            if zoom_button:
                try:
                    pos = getattr(zoom_button, 'AXPosition', None)
                    size = getattr(zoom_button, 'AXSize', None)
                    
                    if pos and size and len(pos) == 2 and len(size) == 2:
                        x = pos[0] + size[0] / 2
                        y = pos[1] + size[1] / 2
                        
                        controls.append({
                            'title': getattr(zoom_button, 'AXTitle', 'Zoom'),
                            'role': getattr(zoom_button, 'AXRole', 'AXButton'),
                            'type': 'maximize',
                            'omeClick': [x, y],
                            'position': pos,
                            'size': size
                        })
                except Exception as e:
                    print(f"[navBigDaDDy] Error processing zoom button: {e}")
            
        except Exception as e:
            print(f"[navBigDaDDy] Error getting window control buttons: {e}")
        
        return controls

    def _close_window_pyxa(self):
        """
        Closes the current window using PyXA.
        Returns True if successful, False otherwise.
        """
        try:
            import PyXA
            
            print(f"[navBigDaDDy] Attempting to close window via PyXA")
            
            # Try to get the app using PyXA - try bundle ID first, then app name
            app = None
            try:
                app = PyXA.Application(self.bundle_id)
            except:
                # Try with app name (e.g., "Mail" instead of "com.apple.mail")
                app_name = self.bundle_id.split('.')[-1].title()  # "mail" -> "Mail"
                try:
                    app = PyXA.Application(app_name)
                except:
                    print(f"[navBigDaDDy] Could not find app via PyXA with bundle ID '{self.bundle_id}' or name '{app_name}'")
                    return False
            
            windows = app.windows()
            
            if not windows:
                print(f"[navBigDaDDy] No windows found via PyXA")
                return False
            
            # Close the first window (usually the active one)
            windows[0].close()
            print(f"[navBigDaDDy] PyXA close successful")
            time.sleep(ACTION_DELAY)
            self._call_winD_after_action()
            return True
            
        except Exception as e:
            print(f"[navBigDaDDy] PyXA close error: {e}")
            return False

    def _minimize_window_pyxa(self):
        """
        Minimizes the current window using PyXA.
        Returns True if successful, False otherwise.
        """
        try:
            import PyXA
            
            print(f"[navBigDaDDy] Attempting to minimize window via PyXA")
            
            # Try to get the app using PyXA - try bundle ID first, then app name
            app = None
            try:
                app = PyXA.Application(self.bundle_id)
            except:
                # Try with app name (e.g., "Mail" instead of "com.apple.mail")
                app_name = self.bundle_id.split('.')[-1].title()  # "mail" -> "Mail"
                try:
                    app = PyXA.Application(app_name)
                except:
                    print(f"[navBigDaDDy] Could not find app via PyXA with bundle ID '{self.bundle_id}' or name '{app_name}'")
                    return False
            
            windows = app.windows()
            
            if not windows:
                print(f"[navBigDaDDy] No windows found via PyXA")
                return False
            
            # Set the window to miniaturized (minimized)
            windows[0].miniaturized = True
            print(f"[navBigDaDDy] PyXA minimize successful")
            time.sleep(ACTION_DELAY)
            self._call_winD_after_action()
            return True
            
        except Exception as e:
            print(f"[navBigDaDDy] PyXA minimize error: {e}")
            return False

    def _maximize_window_pyxa(self):
        """
        Maximizes the current window using PyXA.
        Returns True if successful, False otherwise.
        """
        try:
            import PyXA
            
            print(f"[navBigDaDDy] Attempting to maximize window via PyXA")
            
            # Try to get the app using PyXA - try bundle ID first, then app name
            app = None
            try:
                app = PyXA.Application(self.bundle_id)
            except:
                # Try with app name (e.g., "Mail" instead of "com.apple.mail")
                app_name = self.bundle_id.split('.')[-1].title()  # "mail" -> "Mail"
                try:
                    app = PyXA.Application(app_name)
                except:
                    print(f"[navBigDaDDy] Could not find app via PyXA with bundle ID '{self.bundle_id}' or name '{app_name}'")
                    return False
            
            windows = app.windows()
            
            if not windows:
                print(f"[navBigDaDDy] No windows found via PyXA")
                return False
            
            # Set the window to zoomed (maximized)
            windows[0].zoomed = True
            print(f"[navBigDaDDy] PyXA maximize successful")
            time.sleep(ACTION_DELAY)
            self._call_winD_after_action()
            return True
            
        except Exception as e:
            print(f"[navBigDaDDy] PyXA maximize error: {e}")
            return False

    def close_window(self):
        """
        Closes the current window using PyXA.
        Returns True if successful, False otherwise.
        """
        return self._close_window_pyxa()

    def minimize_window(self):
        """
        Minimizes the current window using PyXA.
        Returns True if successful, False otherwise.
        """
        return self._minimize_window_pyxa()

    def maximize_window(self):
        """
        Maximizes the current window using PyXA.
        Returns True if successful, False otherwise.
        """
        return self._maximize_window_pyxa()

    def list_window_controls(self):
        """
        Lists available window control buttons by crawling the window directly.
        Returns a list of available controls.
        """
        return self.get_window_control_buttons()

    def refresh_menu_data(self):
        """
        Force refresh menu data by clearing cache and rebuilding.
        Returns True if successful, False otherwise.
        """
        try:
            self._menu_cache_time = 0  # Clear cache
            self._load_menu_nav()  # This will rebuild menu data
            return True
        except Exception as e:
            print(f"[navBigDaDDy] Error refreshing menu data: {e}")
            return False

    def get_message_list_data(self):
        """
        Returns the loaded message list entries (from JSONL file).
        """
        if not self._can_use_message_list():
            print("[navBigDaDDy] Message list actions are only allowed in MainWindow context.")
            return []
        return self.message_list_entries

    def refresh_message_list_data(self):
        """
        Force refresh message list data by rebuilding the JSONL file and reloading.
        """
        if not self._can_use_message_list():
            print("[navBigDaDDy] Message list actions are only allowed in MainWindow context.")
            return False
        try:
            associations = self.current_config.get('associations', {})
            if 'message_list_jsonl' in associations:
                message_list_jsonl_path = associations['message_list_jsonl']
                if '<MESSAGE_EXPORT_DIR>' in message_list_jsonl_path:
                    from ome.utils.env.env import MESSAGE_EXPORT_DIR
                    message_list_jsonl_path = message_list_jsonl_path.replace('<MESSAGE_EXPORT_DIR>', MESSAGE_EXPORT_DIR)
                # Build the message list data file using the controller
                from ome.utils.builder.mail.mailMessageList_controller import extract_first_n_rows_fields
                print(f"[navBigDaDDy] Refreshing message list data for {self.bundle_id}")
                extract_first_n_rows_fields(app_object=self._cached_app)
                # Reload the data
                self._load_associations()
                print(f"[navBigDaDDy] Message list data refreshed: {len(self.message_list_entries)} entries")
                return True
            else:
                print(f"[navBigDaDDy] No message_list_jsonl association found for {self.bundle_id}")
                return False
        except Exception as e:
            print(f"[navBigDaDDy] Error refreshing message list data: {e}")
            return False

    def _can_use_message_list(self):
        """
        Returns True if the current window_ref allows message list actions (i.e., is 'MainWindow').
        """
        return self.active_target.get('window_ref') == 'MainWindow'

    def find_message(self, criteria, search_type='subject'):
        """
        Finds a message by various criteria.
        
        Args:
            criteria (str): The search criteria (subject, sender, etc.)
            search_type (str): Type of search ('subject', 'sender', 'sender_email', 'message_key')
            
        Returns:
            dict: Message entry or None if not found
        """
        if not self._can_use_message_list():
            print("[navBigDaDDy] Message list actions are only allowed in MainWindow context.")
            return None
        if not self.message_list_entries:
            print("[navBigDaDDy] No message list data available")
            return None
        
        criteria_lower = criteria.lower()
        
        for entry in self.message_list_entries:
            if search_type == 'subject':
                subject = entry.get('subject', '')
                if criteria_lower in subject.lower():
                    return entry
            elif search_type == 'sender':
                sender = entry.get('sender', '')
                if criteria_lower in sender.lower():
                    return entry
            elif search_type == 'sender_email':
                sender_email = entry.get('sender_email', '')
                if criteria_lower in sender_email.lower():
                    return entry
            elif search_type == 'message_key':
                message_key = entry.get('message_key', '')
                if criteria_lower == message_key.lower():
                    return entry
            elif search_type == 'row_index':
                try:
                    row_index = int(criteria)
                    if entry.get('row_index') == row_index:
                        return entry
                except ValueError:
                    continue
        
        return None

    def select_message_row(self, row_index, send_keys_after_select=False):
        """
        Select/focus a specific message row using direct accessibility API control.
        If send_keys_after_select is True, sends Enter key after selecting the row (for opening message in new window).
        Args:
            row_index (int): The 1-based row index to select
            send_keys_after_select (bool): If True, send Enter key after selecting
        Returns:
            bool: True if successful, False otherwise
        """
        if not self._can_use_message_list():
            print("[navBigDaDDy] Message list actions are only allowed in MainWindow context.")
            return False
        # Ensure app is focused before selection
        if not self._ensure_app_focus_before_action():
            return False
        try:
            from ome.utils.builder.mail.mailMessageList_controller import extract_first_n_rows_fields
            print(f"[navBigDaDDy] Selecting message row {row_index} using direct accessibility control")
            # Pass the send_keys_after_select flag through to the message list controller
            extract_first_n_rows_fields(row_index=row_index, app_object=self._cached_app, send_keys_after_select=send_keys_after_select)
            time.sleep(ACTION_DELAY)
            self._call_winD_after_action()
            return True
        except Exception as e:
            print(f"[navBigDaDDy] Error selecting message row {row_index}: {e}")
            return False

    def click_message(self, criteria, search_type='subject'):
        """
        Finds and clicks on a message by criteria.
        
        Args:
            criteria (str): The search criteria (subject, sender, etc.)
            search_type (str): Type of search ('subject', 'sender', 'sender_email', 'message_key', 'row_index')
            
        Returns:
            bool: True if successful, False otherwise
        """
        if not self._can_use_message_list():
            print("[navBigDaDDy] Message list actions are only allowed in MainWindow context.")
            return False
        message = self.find_message(criteria, search_type)
        if not message:
            print(f"[navBigDaDDy] Message not found with criteria '{criteria}' (type: {search_type})")
            return False
        
        # Get the row index and click coordinates
        row_index = message.get('row_index')
        omeClick = message.get('omeClick')
        
        if omeClick and len(omeClick) == 2:
            # Click at the message coordinates
            x, y = omeClick
            print(f"[navBigDaDDy] Clicking message '{message.get('subject', 'No Subject')}' at ({x}, {y})")
            return self.click_at_coordinates(x, y, f"message: {message.get('subject', 'No Subject')}")
        elif row_index:
            # Use direct row selection if coordinates not available
            print(f"[navBigDaDDy] Using direct row selection for message '{message.get('subject', 'No Subject')}'")
            return self.select_message_row(row_index)
        else:
            print(f"[navBigDaDDy] No click coordinates or row index available for message")
            return False

# =========================
# Command Line Interface
# =========================
def main():
    
    import sys
    import argparse
    
    # Create argument parser for more flexible command line usage
    parser = argparse.ArgumentParser(
        description="navBigDaDDy - Unified Navigation Controller for Om-E-Mac",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    
    # Add bundle_id as positional argument
    parser.add_argument('bundle_id', nargs='?', help='Bundle ID of the app (e.g., com.apple.mail)')
    
    # Info commands
    parser.add_argument('--info', action='store_true', help='Show current window state and data counts')
    parser.add_argument('--status', action='store_true', help='Show current status (same as --info)')
    parser.add_argument('--debug', action='store_true', help='Show debug information')
    
    # Find commands
    parser.add_argument('--find', metavar='DESCRIPTION', help='Find an element by description (no click)')
    parser.add_argument('--find-menu', metavar='TITLE', help='Find a menu item by title (no click)')
    parser.add_argument('--find-picker', metavar='TITLE', help='Find a picker item by title (no click)')
    parser.add_argument('--find-message', metavar='CRITERIA', help='Find a message by criteria (no click)')
    
    # Click commands
    parser.add_argument('--click', metavar='DESCRIPTION', help='Find and click an element')
    parser.add_argument('--click-menu', metavar='TITLE', help='Find and click a menu item')
    parser.add_argument('--click-picker', metavar='TITLE', help='Find and click a picker item')
    parser.add_argument('--click-message', metavar='CRITERIA', help='Find and click a message')
    
    # Navigation commands
    parser.add_argument('--nav-menu', nargs='+', metavar='PATH', help='Navigate menu path (e.g., File New Message)')
    parser.add_argument('--navigate', nargs='+', metavar='PATH', help='Navigate menu path (alias for --nav-menu)')
    
    # List commands
    parser.add_argument('--list-elements', action='store_true', help='List all available elements')
    parser.add_argument('--list-menus', action='store_true', help='List all available menu items')
    parser.add_argument('--list-pickers', action='store_true', help='List all available picker items')
    parser.add_argument('--list-messages', action='store_true', help='List all available messages')
    parser.add_argument('--elements', action='store_true', help='List all available elements (alias for --list-elements)')
    parser.add_argument('--menus', action='store_true', help='List all available menu items (alias for --list-menus)')
    parser.add_argument('--pickers', action='store_true', help='List all available picker items (alias for --list-pickers)')
    parser.add_argument('--messages', action='store_true', help='List all available messages (alias for --list-messages)')
    
    # Picker commands
    parser.add_argument('--select-picker-row', type=int, nargs='?', const=1, default=None, metavar='N', help='Select picker row by number (1-based, defaults to 1 if no value)')
    parser.add_argument('--show-picker-jsonl', action='store_true', help='Show raw picker JSONL data')
    parser.add_argument('--show-picker-path', action='store_true', help='Show path to picker JSONL file')
    parser.add_argument('--picker-jsonl', action='store_true', help='Show raw picker JSONL data (alias for --show-picker-jsonl)')
    parser.add_argument('--picker-path', action='store_true', help='Show path to picker JSONL file (alias for --show-picker-path)')
    
    # Message commands
    parser.add_argument('--select-message-row', type=int, nargs='?', const=1, default=None, metavar='N', help='Select message row by number (1-based, defaults to 1 if no value)')
    parser.add_argument('--show-message-jsonl', action='store_true', help='Show raw message JSONL data')
    parser.add_argument('--show-message-path', action='store_true', help='Show path to message JSONL file')
    parser.add_argument('--message-jsonl', action='store_true', help='Show raw message JSONL data (alias for --show-message-jsonl)')
    parser.add_argument('--message-path', action='store_true', help='Show path to message JSONL file (alias for --show-message-path)')
    
    # Window commands
    parser.add_argument('--close', action='store_true', help='Close current window')
    parser.add_argument('--minimize', action='store_true', help='Minimize current window')
    parser.add_argument('--maximize', action='store_true', help='Maximize current window')
    parser.add_argument('--window-controls', action='store_true', help='List available window control buttons')
    
    # Refresh commands
    parser.add_argument('--refresh-picker', action='store_true', help='Force refresh picker data')
    parser.add_argument('--refresh-menu', action='store_true', help='Force refresh menu data')
    parser.add_argument('--refresh-messages', action='store_true', help='Force refresh message list data')
    
    # New command
    parser.add_argument('--send-keys-after-select', action='store_true', help='Send Enter key after selecting the message row')
    
    # Legacy command support
    parser.add_argument('command', nargs='?', help='Legacy command (info, find, click, etc.)')
    parser.add_argument('args', nargs='*', help='Legacy command arguments')
    
    # Parse arguments
    args = parser.parse_args()
    
    # Handle help without bundle_id
    if not args.bundle_id and len(sys.argv) == 1:
        parser.print_help()
        return
    
    # Handle help with bundle_id
    if args.bundle_id and len(sys.argv) == 2:
        print(f"navBigDaDDy Command Line Interface for {args.bundle_id}")
        print("=" * 60)
        print("Usage: python navBigDaDDy.py <bundle_id> <command> [args...]")
        print()
        print("Commands:")
        print("  --info                    - Show current window state and data counts")
        print("  --find <description>      - Find an element by description (no click)")
        print("  --find-menu <title>       - Find a menu item by title (no click)")
        print("  --find-picker <title>     - Find a picker item by title (no click)")
        print("  --find-message <criteria>  - Find a message by criteria (no click)")
        print("  --click <description>     - Find and click an element")
        print("  --click-menu <title>      - Find and click a menu item")
        print("  --click-picker <title>    - Find and click a picker item")
        print("  --click-message <criteria> - Find and click a message")
        print("  --nav-menu <path...>      - Navigate menu path (e.g., 'File' 'New Message')")
        print("  --list-elements           - List all available elements")
        print("  --list-menus              - List all available menu items")
        print("  --list-pickers            - List all available picker items")
        print("  --list-messages           - List all available messages")
        print("  --select-picker-row <n>   - Select picker row by number (1-based)")
        print("  --show-picker-jsonl       - Show raw picker JSONL data")
        print("  --show-picker-path        - Show path to picker JSONL file")
        print("  --close                   - Close current window")
        print("  --minimize                - Minimize current window")
        print("  --maximize                - Maximize current window")
        print("  --window-controls         - List available window control buttons")
        print("  --refresh-picker          - Force refresh picker data")
        print("  --refresh-menu            - Force refresh menu data")
        print("  --refresh-messages        - Force refresh message list data")
        print()
        print("Examples:")
        print(f"  python navBigDaDDy.py {args.bundle_id} --info")
        print(f"  python navBigDaDDy.py {args.bundle_id} --click 'Send'")
        print(f"  python navBigDaDDy.py {args.bundle_id} --nav-menu 'File' 'New Message'")
        return
    
    # If no bundle_id provided, show error
    if not args.bundle_id:
        print("Error: Bundle ID is required")
        print("Usage: python navBigDaDDy.py <bundle_id> [options]")
        return
    
    try:
        print(f"Creating navBigDaDDy for {args.bundle_id}...")
        nav = navBigDaDDy(args.bundle_id)
        
        # Handle info commands
        if args.info or args.status or args.debug or args.command == "info":
            print(f"Active target: {nav.active_target}")
            if isinstance(nav.active_target, dict) and nav.active_target:
                print(f"Window ref: {nav.active_target.get('window_ref')}")
                print(f"Window title: {nav.active_target.get('window_title')}")
            else:
                print("Window ref: No active window")
                print("Window title: No active window")
            print(f"Window nav entries: {len(nav.window_nav_entries)}")
            print(f"Menu entries: {len(nav.menu_entries)}")
            print(f"Picker entries: {len(nav.picker_entries)}")
            print(f"Message list entries: {len(nav.message_list_entries)}")
            
        # Handle find commands
        elif args.find or args.command == "find":
            description = args.find or (args.args[0] if args.args else None)
            if not description:
                print("Error: Need description for find command")
                return
            element = nav.find_element(description)
            if element:
                print(f"✓ Found element: {element}")
            else:
                print(f"✗ Element '{description}' not found")
                
        elif args.find_menu or args.command == "find-menu":
            title = args.find_menu or (args.args[0] if args.args else None)
            if not title:
                print("Error: Need title for find-menu command")
                return
            menu_item = nav.find_menu_item(title)
            if menu_item:
                print(f"✓ Found menu item: {menu_item}")
            else:
                print(f"✗ Menu item '{title}' not found")
                
        elif args.find_picker or args.command == "find-picker":
            title = args.find_picker or (args.args[0] if args.args else None)
            if not title:
                print("Error: Need title for find-picker command")
                return
            picker_item = nav.find_picker_item(title)
            if picker_item:
                print(f"✓ Found picker item: {picker_item}")
            else:
                print(f"✗ Picker item '{title}' not found")
                
        elif args.find_message or args.command == "find-message":
            criteria = args.find_message or (args.args[0] if args.args else None)
            if not criteria:
                print("Error: Need criteria for find-message command")
                return
            message = nav.find_message(criteria)
            if message:
                print(f"✓ Found message: {message}")
            else:
                print(f"✗ Message not found with criteria '{criteria}'")
                
        # Handle click commands
        elif args.click or args.command == "click":
            description = args.click or (args.args[0] if args.args else None)
            if not description:
                print("Error: Need description for click command")
                return
            print(f"Clicking element: {description}")
            success = nav.click_element(description)
            if success:
                print("✓ Click successful")
            else:
                print("✗ Click failed")
                
        elif args.click_menu or args.command == "click-menu":
            title = args.click_menu or (args.args[0] if args.args else None)
            if not title:
                print("Error: Need title for click-menu command")
                return
            print(f"Clicking menu item: {title}")
            success = nav.click_menu_item(title)
            if success:
                print("✓ Menu click successful")
            else:
                print("✗ Menu click failed")
                
        elif args.click_picker or args.command == "click-picker":
            title = args.click_picker or (args.args[0] if args.args else None)
            if not title:
                print("Error: Need title for click-picker command")
                return
            print(f"Clicking picker item: {title}")
            success = nav.click_picker_item(title)
            if success:
                print("✓ Picker click successful")
            else:
                print("✗ Picker click failed")
                
        elif args.click_message or args.command == "click-message":
            criteria = args.click_message or (args.args[0] if args.args else None)
            if not criteria:
                print("Error: Need criteria for click-message command")
                return
            print(f"Clicking message: {criteria}")
            success = nav.click_message(criteria)
            if success:
                print("✓ Message click successful")
            else:
                print("✗ Message click failed")
                
        # Handle navigation commands
        elif args.nav_menu or args.navigate or args.command == "nav-menu":
            menu_path = args.nav_menu or args.navigate or args.args
            if not menu_path:
                print("Error: Need menu path for nav-menu command")
                return
            print(f"Navigating menu path: {' > '.join(menu_path)}")
            success = nav.navigate_menu_path(menu_path)
            if success:
                print("✓ Menu navigation successful")
            else:
                print("✗ Menu navigation failed")
                
        # Handle list commands
        elif args.list_elements or args.elements or args.command == "list-elements":
            print(f"Available elements ({len(nav.window_nav_entries)} total):")
            for i, element in enumerate(nav.window_nav_entries[:20]):  # Show first 20
                title = element.get('AXTitle', 'No Title')
                role = element.get('AXRole', 'No Role')
                print(f"  {i+1}. {title} ({role})")
            if len(nav.window_nav_entries) > 20:
                print(f"  ... and {len(nav.window_nav_entries) - 20} more")
                
        elif args.list_menus or args.menus or args.command == "list-menus":
            print(f"Available menu items ({len(nav.menu_entries)} total):")
            for i, menu in enumerate(nav.menu_entries[:20]):  # Show first 20
                title = menu.get('title', 'No Title')
                path = menu.get('menu_path', [])
                path_str = ' > '.join(path) if path else 'No Path'
                print(f"  {i+1}. {title} ({path_str})")
            if len(nav.menu_entries) > 20:
                print(f"  ... and {len(nav.menu_entries) - 20} more")
                
        elif args.list_pickers or args.pickers or args.command == "list-pickers":
            print(f"Available picker items ({len(nav.picker_entries)} total):")
            for i, picker in enumerate(nav.picker_entries[:20]):  # Show first 20
                # Use file_name for picker entries, fallback to AXTitle
                title = picker.get('file_name') or picker.get('AXTitle', 'No Title')
                row_index = picker.get('row_index', 'N/A')
                print(f"  {i+1}. {title} (row {row_index})")
            if len(nav.picker_entries) > 20:
                print(f"  ... and {len(nav.picker_entries) - 20} more")
                
        elif args.list_messages or args.messages or args.command == "list-messages":
            print(f"Available messages ({len(nav.message_list_entries)} total):")
            for i, message in enumerate(nav.message_list_entries[:20]):  # Show first 20
                subject = message.get('subject', 'No Subject')
                print(f"  {i+1}. {subject}")
            if len(nav.message_list_entries) > 20:
                print(f"  ... and {len(nav.message_list_entries) - 20} more")
                
        # Handle picker commands
        elif args.select_picker_row is not None or args.command == "select-picker-row":
            if args.select_picker_row is not None:
                row_index = args.select_picker_row
            elif args.command == "select-picker-row":
                if args.args and len(args.args) > 0:
                    try:
                        row_index = int(args.args[0])
                    except Exception:
                        row_index = 1
                else:
                    row_index = 1
            else:
                row_index = 1
            print(f"Selecting picker row {row_index}")
            success = nav.select_picker_row(row_index)
            if success:
                print("✓ Picker row selected")
            else:
                print("✗ Failed to select picker row")
                
        elif args.show_picker_jsonl or args.picker_jsonl or args.command == "show-picker-jsonl":
            print(f"Picker JSONL path: {nav.get_picker_jsonl_path()}")
            picker_data = nav.get_picker_data()
            print(f"Raw picker JSONL data ({len(picker_data)} entries):")
            for i, entry in enumerate(picker_data[:10]):  # Show first 10
                print(f"  {i+1}. {json.dumps(entry, indent=2)}")
            if len(picker_data) > 10:
                print(f"  ... and {len(picker_data) - 10} more entries")
                
        elif args.show_picker_path or args.picker_path or args.command == "show-picker-path":
            print(f"Picker JSONL path: {nav.get_picker_jsonl_path()}")
            if os.path.exists(nav.get_picker_jsonl_path()):
                print("✓ File exists")
            else:
                print("✗ File does not exist")
                
        # Handle message commands
        elif args.select_message_row is not None or args.command == "select-message-row":
            if args.select_message_row is not None:
                row_index = args.select_message_row
            elif args.command == "select-message-row":
                if args.args and len(args.args) > 0:
                    try:
                        row_index = int(args.args[0])
                    except Exception:
                        row_index = 1
                else:
                    row_index = 1
            else:
                row_index = 1
            print(f"Selecting message row {row_index}")
            success = nav.select_message_row(row_index, send_keys_after_select=args.send_keys_after_select)
            if success:
                print("✓ Message row selected")
            else:
                print("✗ Failed to select message row")
                
        elif args.show_message_jsonl or args.message_jsonl or args.command == "show-message-jsonl":
            print(f"Message JSONL path: {os.path.join('ome/data/messages', 'mail_com.apple.mail.inbox.jsonl')}")
            message_data = nav.get_message_list_data()
            print(f"Raw message JSONL data ({len(message_data)} entries):")
            for i, entry in enumerate(message_data[:10]):  # Show first 10
                print(f"  {i+1}. {json.dumps(entry, indent=2)}")
            if len(message_data) > 10:
                print(f"  ... and {len(message_data) - 10} more entries")
                
        elif args.show_message_path or args.message_path or args.command == "show-message-path":
            message_path = os.path.join('ome/data/messages', 'mail_com.apple.mail.inbox.jsonl')
            print(f"Message JSONL path: {message_path}")
            if os.path.exists(message_path):
                print("✓ File exists")
            else:
                print("✗ File does not exist")
                
        # Handle window commands
        elif args.close or args.command == "close-window":
            print(f"Closing window for {args.bundle_id}")
            success = nav.close_window()
            if success:
                print("✓ Window closed successfully")
            else:
                print("✗ Failed to close window")
                
        elif args.minimize or args.command == "minimize-window":
            print(f"Minimizing window for {args.bundle_id}")
            success = nav.minimize_window()
            if success:
                print("✓ Window minimized successfully")
            else:
                print("✗ Failed to minimize window")
                
        elif args.maximize or args.command == "maximize-window":
            print(f"Maximizing window for {args.bundle_id}")
            success = nav.maximize_window()
            if success:
                print("✓ Window maximized successfully")
            else:
                print("✗ Failed to maximize window")
                
        elif args.window_controls or args.command == "list-window-controls":
            print(f"Available window controls for {args.bundle_id}:")
            controls = nav.list_window_controls()
            for i, control in enumerate(controls[:20]):  # Show first 20
                print(f"  {i+1}. {control['title']} ({control['role']})")
            if len(controls) > 20:
                print(f"  ... and {len(controls) - 20} more")
                
        # Handle refresh commands
        elif args.refresh_picker or args.command == "refresh-picker":
            print(f"Refreshing picker data for {args.bundle_id}")
            success = nav.refresh_picker_data()
            if success:
                print("✓ Picker data refreshed successfully")
            else:
                print("✗ Failed to refresh picker data")
                
        elif args.refresh_menu or args.command == "refresh-menu":
            print(f"Refreshing menu data for {args.bundle_id}")
            success = nav.refresh_menu_data()
            if success:
                print("✓ Menu data refreshed successfully")
            else:
                print("✗ Failed to refresh menu data")
                
        elif args.refresh_messages or args.command == "refresh-messages":
            print(f"Refreshing message list data for {args.bundle_id}")
            success = nav.refresh_message_list_data()
            if success:
                print("✓ Message list data refreshed successfully")
            else:
                print("✗ Failed to refresh message list data")
                
        # Handle legacy commands
        elif args.command:
            print(f"Legacy command '{args.command}' with args: {args.args}")
            print("Please use the new --flag syntax instead")
            
        else:
            print("No command specified. Use --help for usage information.")
            
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main() 