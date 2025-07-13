#!/usr/bin/env python3
"""
Clean Event Listener - Simple and focused window monitoring for Mail app

This script monitors the Mail application for new window creation events using
a polling approach instead of the problematic PyObjC callback system. It provides:

1. Real-time window detection for the Mail app
2. Mouse corner exit functionality (move mouse to top-right corner to exit)
3. Robust window tracking using position and size for unique identification
4. Clean error handling and graceful shutdown

Usage:
    python clean_event_listener.py

Features:
    - Automatically focuses the Mail app on startup
    - Detects new windows as they appear
    - Provides detailed window information (title, role, position, size)
    - Mouse corner exit for easy termination
    - 2-second polling interval for responsive detection

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

# Add ome to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'ome'))

from ome.AXClasses import NativeUIElement
from ome.utils.builder.app.app_focus import ensure_app_focus

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

def get_window_info(window):
    """Get basic info about a window"""
    try:
        title = getattr(window, 'AXTitle', 'Unknown')
        role = getattr(window, 'AXRole', 'Unknown')
        # Try to get a more unique identifier
        try:
            position = getattr(window, 'AXPosition', None)
            size = getattr(window, 'AXSize', None)
            if position and size:
                return f"{title} ({role}) at {position} size {size}"
        except:
            pass
        return f"{title} ({role})"
    except Exception as e:
        return f"Unknown window (error: {e})"

def get_window_signature(window):
    """Get a unique signature for a window to track it properly"""
    try:
        title = getattr(window, 'AXTitle', 'Unknown')
        role = getattr(window, 'AXRole', 'Unknown')
        # Use position and size for uniqueness
        try:
            position = getattr(window, 'AXPosition', None)
            size = getattr(window, 'AXSize', None)
            if position and size:
                return f"{title}|{role}|{position}|{size}"
        except:
            pass
        return f"{title}|{role}"
    except Exception as e:
        return f"unknown|{e}"

def main():
    print("=" * 50)
    print("CLEAN EVENT LISTENER")
    print("=" * 50)
    
    # Initialize
    bundle_id = "com.apple.mail"
    mouse_monitor = MouseExitMonitor()
    
    try:
        # Focus app once
        print("Focusing Mail app...")
        result = ensure_app_focus(bundle_id)
        if result['status'] != 'success':
            print(f"Failed to focus app: {result.get('error')}")
            return
        
        # Get app reference
        print("Getting app reference...")
        app = NativeUIElement.getAppRefByBundleId(bundle_id)
        
        # Start mouse monitor
        mouse_monitor.start()
        
        print("Event listener ready!")
        print("Move mouse to top-right corner to exit")
        print("=" * 50)
        
        # Track existing windows
        existing_windows = set()
        try:
            current_windows = app.windows()
            for window in current_windows:
                window_info = get_window_info(window)
                window_sig = get_window_signature(window)
                existing_windows.add(window_sig)
                print(f"Existing window: {window_info}")
        except Exception as e:
            print(f"Error getting initial windows: {e}")
        
        # Main event loop - poll for new windows
        while True:
            try:
                print("Checking for new windows...")
                current_windows = app.windows()
                current_window_infos = set()
                
                for window in current_windows:
                    window_info = get_window_info(window)
                    window_sig = get_window_signature(window)
                    current_window_infos.add(window_sig)
                    
                    if window_sig not in existing_windows:
                        print(f"NEW WINDOW DETECTED: {window_info}")
                        # You can add your window processing logic here
                
                # Update existing windows set
                existing_windows = current_window_infos
                
                # Wait before next check
                time.sleep(2)
                    
            except KeyboardInterrupt:
                print("Interrupted by user")
                break
            except Exception as e:
                print(f"Event error: {e}")
                time.sleep(1)
                
    except Exception as e:
        print(f"Setup error: {e}")
    finally:
        mouse_monitor.stop()
        print("Cleanup complete")

if __name__ == "__main__":
    main()
