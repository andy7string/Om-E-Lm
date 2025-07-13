#!/usr/bin/env python3
"""
Test script to demonstrate dynamic switching functionality of clean_event_listener_classified.py
"""

import time
import subprocess
import sys
import os

# Add ome to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'ome'))

from ome.controllers.bundles.bundleID_controller import BundleIDController

def main():
    print("=" * 60)
    print("DYNAMIC SWITCHING TEST")
    print("=" * 60)
    
    # Initialize bundle controller
    bundle_controller = BundleIDController()
    
    # Start with Mail
    print("1. Setting active bundle ID to Mail...")
    bundle_controller.set_active_bundle_id("Mail", "test")
    time.sleep(1)
    
    # Start the event listener in background
    print("2. Starting event listener (will use active bundle ID: Mail)...")
    listener_process = subprocess.Popen([
        sys.executable, "clean_event_listener_classified.py"
    ], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    
    # Give it time to start
    time.sleep(3)
    
    # Switch to Safari
    print("3. Switching active bundle ID to Safari...")
    bundle_controller.set_active_bundle_id("Safari", "test")
    time.sleep(3)
    
    # Switch to Finder
    print("4. Switching active bundle ID to Finder...")
    bundle_controller.set_active_bundle_id("Finder", "test")
    time.sleep(3)
    
    # Switch back to Mail
    print("5. Switching back to Mail...")
    bundle_controller.set_active_bundle_id("Mail", "test")
    time.sleep(3)
    
    # Stop the listener
    print("6. Stopping event listener...")
    listener_process.terminate()
    listener_process.wait()
    
    print("=" * 60)
    print("TEST COMPLETE")
    print("=" * 60)
    print("Check the output above to see if the event listener")
    print("dynamically switched between apps as the active bundle ID changed.")
    print("You should see [SWITCH] messages in the listener output.")

if __name__ == "__main__":
    main() 