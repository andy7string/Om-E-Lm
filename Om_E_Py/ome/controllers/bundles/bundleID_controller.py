"""
ome/controllers/bundles/bundleID_controller.py

This script provides a centralized controller for managing active bundle IDs across the entire
navigation system, enabling app switching and refresh functionality.

Module Path: ome.controllers.bundles.bundleID_controller

Main Purpose:
- Manages the active bundle ID for the entire navigation system
- Provides refresh functionality for apps that quit and relaunch
- Enables app switching across all navigation components
- Handles automatic and manual refresh requests
- Integrates with appList_controller.py for bundle ID resolution

Key Features:
- Active Bundle ID Management: Central file-based tracking of which app is currently active
- Refresh System: Automatic refresh when apps quit/relaunch, plus manual refresh requests
- App Switching: Seamless switching between different macOS applications
- Error Recovery: Automatic refresh requests when navigation errors occur
- File-Based Triggers: Uses file system for inter-process communication
- Bundle ID Resolution: Uses appList_controller.py for fuzzy matching and validation

How to Use:

Command Line Interface:
    # Get the active bundle ID
    python -m ome.controllers.bundles.bundleID_controller --get
    
    # Switch to a different app (supports app names or bundle IDs with fuzzy matching)
    python -m ome.controllers.bundles.bundleID_controller --set "Safari"  # App name
    python -m ome.controllers.bundles.bundleID_controller --set "com.apple.mail"  # Bundle ID
    python -m ome.controllers.bundles.bundleID_controller --set "safri"  # Fuzzy match
    
    # Request a refresh
    python -m ome.controllers.bundles.bundleID_controller --refresh "Mail" --reason "app_quit_relaunch"
    python -m ome.controllers.bundles.bundleID_controller --refresh "com.apple.Safari" --reason "manual_request"
    
    # Show full state
    python -m ome.controllers.bundles.bundleID_controller --state
    
    # Watch for changes
    python -m ome.controllers.bundles.bundleID_controller --watch
    
    # Resolve bundle ID or app name (with fuzzy matching)
    python -m ome.controllers.bundles.bundleID_controller --resolve "safri"
    
    # Validate bundle ID or app name
    python -m ome.controllers.bundles.bundleID_controller --validate "Mail"

Programmatic Usage:
    # Get the active bundle ID
    bundle_manager = BundleIDController()
    active_id = bundle_manager.get_active_bundle_id()
    
    # Switch to a different app (supports app names or bundle IDs)
    bundle_manager.set_active_bundle_id("Safari", "manual")  # App name
    bundle_manager.set_active_bundle_id("com.apple.mail", "manual")  # Bundle ID
    
    # Request a refresh
    bundle_manager.request_refresh("Mail", "app_quit_relaunch")  # App name
    bundle_manager.request_refresh("com.apple.Safari", "manual_request")  # Bundle ID
    
    # Watch for changes
    bundle_manager.watch_for_changes(callback_function)

File Structure:
    ome/data/windows/
    ├── active_target_Bundle_ID.json     # Central bundle ID tracker
    ├── refresh_com.apple.mail.trigger   # App-specific refresh triggers
    └── refresh_com.apple.Safari.trigger

When to Use:
- When you need to switch between different macOS applications
- When apps quit and relaunch (automatic refresh)
- When navigation components need to coordinate app state
- For error recovery and system resilience
"""

import os
import sys
import json
import time
import warnings
from datetime import datetime
from typing import Optional, Dict, Any, Callable

# Suppress the specific RuntimeWarning about module loading
warnings.filterwarnings("ignore", message=".*found in sys.modules after import.*", category=RuntimeWarning)

# Always add the project root to sys.path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Import bundle ID resolution functions from appList_controller
from ome.utils.builder.app.appList_controller import (
    bundle_id_exists, 
    get_bundle_id, 
    get_app_name,
    resolve_bundle_id
)


class BundleIDController:
    """
    Centralized controller for managing active bundle IDs and refresh functionality.
    Provides a single source of truth for which app is currently active across
    the entire navigation system. Integrates with appList_controller.py for
    bundle ID resolution and validation.
    """
    
    def __init__(self, data_dir="ome/data/windows"):
        """
        Initialize the BundleIDController.
        
        Args:
            data_dir (str): Directory for storing bundle ID and refresh files
        """
        self.data_dir = data_dir
        self.bundle_id_file = os.path.join(data_dir, "active_target_Bundle_ID.json")
        self._ensure_data_dir()
        self._initialize_if_needed()
    
    def _ensure_data_dir(self):
        """Ensure the data directory exists"""
        os.makedirs(self.data_dir, exist_ok=True)
    
    def _initialize_if_needed(self):
        """Initialize the bundle ID file if it doesn't exist"""
        if not os.path.exists(self.bundle_id_file):
            print(f"[BundleIDController] Initializing bundle ID file with default: com.apple.mail")
            self.set_active_bundle_id("com.apple.mail", "initialization")
    
    def resolve_bundle_id(self, input_id: str) -> Optional[str]:
        """
        Resolve input as either a bundle ID or app name using appList_controller.
        This function will automatically correct typos and find the closest match.
        
        Args:
            input_id (str): Bundle ID or app name to resolve (can be misspelled)
            
        Returns:
            str: Canonical bundle ID if found, None otherwise
            
        Examples:
            resolve_bundle_id("safri") -> "com.apple.Safari"
            resolve_bundle_id("com.apple.mial") -> "com.apple.mail"
            resolve_bundle_id("Mail") -> "com.apple.mail"
        """
        if not input_id:
            return None
            
        # Use the existing resolve_bundle_id function from appList_controller
        resolved_id = resolve_bundle_id(input_id)
        if resolved_id:
            if resolved_id != input_id:
                print(f"[BundleIDController] Resolved '{input_id}' to bundle ID '{resolved_id}'")
            return resolved_id
        else:
            print(f"[BundleIDController] Could not resolve '{input_id}' to a valid bundle ID")
            return None
    
    def get_active_bundle_id(self) -> Optional[str]:
        """
        Get the currently active bundle ID.
        
        Returns:
            str: The active bundle ID, or None if file cannot be read
        """
        try:
            with open(self.bundle_id_file, 'r') as f:
                data = json.load(f)
                return data.get("active_bundle_id")
        except Exception as e:
            print(f"[BundleIDController] Failed to read bundle ID file: {e}")
            return None
    
    def get_full_state(self) -> Dict[str, Any]:
        """
        Get the complete state of the bundle ID file.
        
        Returns:
            dict: Complete state including bundle ID, refresh flags, timestamps, etc.
        """
        try:
            with open(self.bundle_id_file, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"[BundleIDController] Failed to read bundle ID file: {e}")
            return {}
    
    def set_active_bundle_id(self, bundle_id_or_name: str, source: str = "manual", 
                           refresh: bool = False, refresh_reason: str = None):
        """
        Set the active bundle ID, resolving app names to bundle IDs.
        This function will automatically correct typos and find the closest match.
        Also updates the individual app's JSONL file to reflect the active target.
        
        Args:
            bundle_id_or_name (str): Bundle ID or app name to set as active (can be misspelled)
            source (str): Source of the change (manual, bigdaddy, event_listener, etc.)
            refresh (bool): Whether to request a refresh
            refresh_reason (str): Reason for the refresh request
            
        Examples:
            set_active_bundle_id("safri") -> Sets to "com.apple.Safari"
            set_active_bundle_id("com.apple.mial") -> Sets to "com.apple.mail"
            set_active_bundle_id("Mail") -> Sets to "com.apple.mail"
        """
        # Resolve the input to a canonical bundle ID (with fuzzy matching)
        resolved_bundle_id = self.resolve_bundle_id(bundle_id_or_name)
        if not resolved_bundle_id:
            print(f"[BundleIDController] Cannot set active bundle ID: '{bundle_id_or_name}' not found")
            return
        
        data = {
            "active_bundle_id": resolved_bundle_id,
            "last_updated": datetime.utcnow().isoformat() + "Z",
            "source": source,
            "status": "active",
            "refresh": refresh,
            "refresh_reason": refresh_reason
        }
        
        try:
            with open(self.bundle_id_file, 'w') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            print(f"[BundleIDController] Set active bundle ID to '{resolved_bundle_id}' (source: {source})")
            if refresh:
                print(f"[BundleIDController] Refresh requested: {refresh_reason}")
            
            # Update the individual app's JSONL file to reflect this as the active target
            self._update_app_jsonl_file(resolved_bundle_id, source)
            
        except Exception as e:
            print(f"[BundleIDController] Failed to write bundle ID file: {e}")
    
    def _update_app_jsonl_file(self, bundle_id: str, source: str):
        """
        Update the individual app's JSONL file to reflect it as the active target.
        
        Args:
            bundle_id (str): The bundle ID of the app
            source (str): Source of the change
        """
        jsonl_file = os.path.join(self.data_dir, f"win_{bundle_id}.jsonl")
        
        # Get app name for display
        app_name = self.get_app_name_for_bundle_id(bundle_id) or bundle_id
        
        # Create active target data
        active_target = {
            "type": "window",
            "window_title": f"{app_name} (Active via {source})",
            "window_ref": f"{bundle_id}.active",
            "nav_map_name": f"appNav_{bundle_id}_active.jsonl",
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
        
        # Create the JSONL content
        jsonl_data = {
            "active_target": active_target,
            "bundle_id": bundle_id,
            "app_name": app_name,
            "source": source,
            "last_updated": datetime.utcnow().isoformat() + "Z"
        }
        
        try:
            with open(jsonl_file, 'w', encoding='utf-8') as f:
                json.dump(jsonl_data, f, ensure_ascii=False, indent=2)
            print(f"[BundleIDController] Updated {jsonl_file} with active target")
        except Exception as e:
            print(f"[BundleIDController] Failed to update JSONL file {jsonl_file}: {e}")
    
    def request_refresh(self, bundle_id_or_name: str, reason: str = "manual_request"):
        """
        Request a refresh for the specified bundle ID or app name.
        If the specified app is not currently active, this will also switch the
        active app to the new one.
        This function will automatically correct typos and find the closest match.
        
        Args:
            bundle_id_or_name (str): Bundle ID or app name to refresh (can be misspelled)
            reason (str): Reason for the refresh request
        """
        # Resolve the input to a canonical bundle ID (with fuzzy matching)
        resolved_bundle_id = self.resolve_bundle_id(bundle_id_or_name)
        if not resolved_bundle_id:
            print(f"[BundleIDController] Cannot request refresh: '{bundle_id_or_name}' not found")
            return
        
        # This now behaves like `set_active_bundle_id` but with refresh always true
        self.set_active_bundle_id(
            bundle_id_or_name=resolved_bundle_id,
            source="refresh_request",
            refresh=True,
            refresh_reason=reason
        )
    
    def clear_refresh_flag(self):
        """Clear the refresh flag after handling it"""
        current_data = self.get_full_state()
        current_data.update({
            "refresh": False,
            "refresh_reason": None,
            "last_updated": datetime.utcnow().isoformat() + "Z"
        })
        
        try:
            with open(self.bundle_id_file, 'w') as f:
                json.dump(current_data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"[BundleIDController] Failed to clear refresh flag: {e}")
    
    def create_refresh_trigger(self, bundle_id_or_name: str):
        """
        Create a refresh trigger file for the specified app.
        This function will automatically correct typos and find the closest match.
        
        Args:
            bundle_id_or_name (str): Bundle ID or app name to create a trigger for (can be misspelled)
            
        Examples:
            create_refresh_trigger("safri") -> Creates trigger for "com.apple.Safari"
            create_refresh_trigger("com.apple.mial") -> Creates trigger for "com.apple.mail"
        """
        # Resolve the input to a canonical bundle ID (with fuzzy matching)
        resolved_bundle_id = self.resolve_bundle_id(bundle_id_or_name)
        if not resolved_bundle_id:
            print(f"[BundleIDController] Cannot create refresh trigger: '{bundle_id_or_name}' not found")
            return
        
        trigger_file = os.path.join(self.data_dir, f"refresh_{resolved_bundle_id}.trigger")
        try:
            with open(trigger_file, 'w') as f:
                f.write(datetime.utcnow().isoformat() + "Z")
            print(f"[BundleIDController] Created refresh trigger for '{resolved_bundle_id}'")
        except Exception as e:
            print(f"[BundleIDController] Failed to create refresh trigger: {e}")
    
    def check_refresh_trigger(self, bundle_id_or_name: str) -> bool:
        """
        Check if a refresh trigger exists and consume it.
        This function will automatically correct typos and find the closest match.
        
        Args:
            bundle_id_or_name (str): Bundle ID or app name to check for triggers (can be misspelled)
            
        Returns:
            bool: True if a trigger was found and consumed, False otherwise
            
        Examples:
            check_refresh_trigger("safri") -> Checks for "com.apple.Safari" trigger
            check_refresh_trigger("com.apple.mial") -> Checks for "com.apple.mail" trigger
        """
        # Resolve the input to a canonical bundle ID (with fuzzy matching)
        resolved_bundle_id = self.resolve_bundle_id(bundle_id_or_name)
        if not resolved_bundle_id:
            return False
        
        trigger_file = os.path.join(self.data_dir, f"refresh_{resolved_bundle_id}.trigger")
        if os.path.exists(trigger_file):
            try:
                os.remove(trigger_file)  # Consume the trigger
                print(f"[BundleIDController] Consumed refresh trigger for '{resolved_bundle_id}'")
                return True
            except Exception as e:
                print(f"[BundleIDController] Failed to consume refresh trigger: {e}")
        return False
    
    def watch_for_changes(self, callback: Callable[[Dict[str, Any], Dict[str, Any]], None], 
                         poll_interval: float = 1.0):
        """
        Watch for bundle ID changes and call callback when changes occur.
        
        Args:
            callback (callable): Function to call when changes are detected
                                Signature: callback(new_state, old_state)
            poll_interval (float): How often to check for changes (seconds)
        """
        last_state = None
        print(f"[BundleIDController] Starting bundle ID watcher (poll interval: {poll_interval}s)")
        
        while True:
            try:
                current_state = self.get_full_state()
                
                # Check if state changed
                if last_state != current_state:
                    if last_state is not None:  # Not the first run
                        print(f"[BundleIDController] State change detected")
                        callback(current_state, last_state)
                    last_state = current_state
                
                time.sleep(poll_interval)
                
            except KeyboardInterrupt:
                print("[BundleIDController] Stopping bundle ID watcher")
                break
            except Exception as e:
                print(f"[BundleIDController] Error in bundle ID watcher: {e}")
                time.sleep(poll_interval)
    
    def is_refresh_requested(self) -> bool:
        """
        Check if a refresh is currently requested.
        
        Returns:
            bool: True if refresh is requested, False otherwise
        """
        state = self.get_full_state()
        return state.get("refresh", False)
    
    def get_refresh_reason(self) -> Optional[str]:
        """
        Get the reason for the current refresh request.
        
        Returns:
            str: The refresh reason, or None if no refresh is requested
        """
        state = self.get_full_state()
        return state.get("refresh_reason") if state.get("refresh", False) else None
    
    def get_app_name_for_bundle_id(self, bundle_id: str) -> Optional[str]:
        """
        Get the app name for a given bundle ID.
        
        Args:
            bundle_id (str): Bundle ID to look up
            
        Returns:
            str: App name if found, None otherwise
        """
        return get_app_name(bundle_id)
    
    def validate_bundle_id(self, bundle_id_or_name: str) -> bool:
        """
        Validate that a bundle ID or app name exists.
        This function will automatically correct typos and find the closest match.
        
        Args:
            bundle_id_or_name (str): Bundle ID or app name to validate (can be misspelled)
            
        Returns:
            bool: True if valid, False otherwise
            
        Examples:
            validate_bundle_id("safri") -> True (resolves to "com.apple.Safari")
            validate_bundle_id("com.apple.mial") -> True (resolves to "com.apple.mail")
            validate_bundle_id("NotRealApp") -> False
        """
        return self.resolve_bundle_id(bundle_id_or_name) is not None


def main():
    """
    Command-line interface for testing the BundleIDController.
    
    Usage Examples:
        # Get current active app
        python -m ome.controllers.bundles.bundleID_controller --get
        
        # Switch to Safari (with fuzzy matching)
        python -m ome.controllers.bundles.bundleID_controller --set "safri"
        
        # Request refresh for Mail
        python -m ome.controllers.bundles.bundleID_controller --refresh "Mail" --reason "app_quit_relaunch"
        
        # Watch for changes
        python -m ome.controllers.bundles.bundleID_controller --watch
        
        # Resolve fuzzy app name
        python -m ome.controllers.bundles.bundleID_controller --resolve "safri"
        
        # Validate app name
        python -m ome.controllers.bundles.bundleID_controller --validate "Mail"
    """
    import argparse
    
    parser = argparse.ArgumentParser(description="BundleID Controller CLI")
    parser.add_argument("--get", action="store_true", help="Get the active bundle ID")
    parser.add_argument("--set", type=str, help="Set the active bundle ID (supports app names and fuzzy matching)")
    parser.add_argument("--refresh", type=str, help="Request refresh for bundle ID or app name (supports fuzzy matching)")
    parser.add_argument("--reason", type=str, help="Reason for refresh request")
    parser.add_argument("--state", action="store_true", help="Show full state")
    parser.add_argument("--watch", action="store_true", help="Watch for changes")
    parser.add_argument("--resolve", type=str, help="Resolve bundle ID or app name (with fuzzy matching)")
    parser.add_argument("--validate", type=str, help="Validate bundle ID or app name (with fuzzy matching)")
    
    args = parser.parse_args()
    
    controller = BundleIDController()
    
    if args.get:
        bundle_id = controller.get_active_bundle_id()
        app_name = controller.get_app_name_for_bundle_id(bundle_id) if bundle_id else None
        print(f"Active bundle ID: {bundle_id}")
        if app_name:
            print(f"App name: {app_name}")
    
    elif args.set:
        controller.set_active_bundle_id(args.set, "cli")
        print(f"Set active bundle ID to: {args.set}")
    
    elif args.refresh:
        reason = args.reason or "manual_request"
        controller.request_refresh(args.refresh, reason)
        print(f"Requested refresh for: {args.refresh} (reason: {reason})")
    
    elif args.state:
        state = controller.get_full_state()
        print(json.dumps(state, indent=2))
    
    elif args.resolve:
        resolved = controller.resolve_bundle_id(args.resolve)
        app_name = controller.get_app_name_for_bundle_id(resolved) if resolved else None
        print(f"Resolved '{args.resolve}' to: {resolved}")
        if app_name:
            print(f"App name: {app_name}")
    
    elif args.validate:
        is_valid = controller.validate_bundle_id(args.validate)
        print(f"'{args.validate}' is {'valid' if is_valid else 'invalid'}")
    
    elif args.watch:
        def on_change(new_state, old_state):
            print(f"Change detected:")
            print(f"  Old: {old_state.get('active_bundle_id')}")
            print(f"  New: {new_state.get('active_bundle_id')}")
            if new_state.get('refresh'):
                print(f"  Refresh: {new_state.get('refresh_reason')}")
        
        controller.watch_for_changes(on_change)
    
    else:
        # Default: show current state
        bundle_id = controller.get_active_bundle_id()
        app_name = controller.get_app_name_for_bundle_id(bundle_id) if bundle_id else None
        state = controller.get_full_state()
        print(f"Active bundle ID: {bundle_id}")
        if app_name:
            print(f"App name: {app_name}")
        print(f"Full state: {json.dumps(state, indent=2)}")


if __name__ == "__main__":
    main() 