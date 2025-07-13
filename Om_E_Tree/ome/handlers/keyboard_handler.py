import pyautogui
import platform
import time
import os
from pathlib import Path
from Om_E_Tree.ome.utils.builder.input_args_builder import build_input_args
from env import TREE_ACTION_RETRIES, TREE_ACTION_RETRY_DELAY
from Om_E_Tree.ome.utils.logger import log_event

# Aliases for backward compatibility
ACTION_RETRIES = TREE_ACTION_RETRIES
ACTION_RETRY_DELAY = TREE_ACTION_RETRY_DELAY

is_mac = platform.system() == "Darwin"

# ----------------------------------------
# Keyboard Shortcuts Functions for macOS
# ----------------------------------------

def press_key(args):
    try:
        # Use build_input_args to check for missing arguments and fill defaults
        args = build_input_args("keyboard", "press_key")
        
        # If 'key' argument is still missing, use the default value
        if "key" not in args:
            args["key"] = "enter"  # Default key if not provided
        
        pyautogui.press(args["key"])
        print(f"Pressed key: {args['key']}")
        return {"status": "complete"}
    except Exception as e:
        return {"status": "failed", "error": str(e)}

def type_text(args):
    try:
        # Use build_input_args to check for missing arguments and fill defaults
        args = build_input_args("keyboard", "type_text")
        
        # If 'text' argument is still missing, use the default value
        if "text" not in args:
            args["text"] = "hello from Om-E"  # Default text if not provided
        
        pyautogui.write(args["text"])
        print(f"Typed text: {args['text']}")
        return {"status": "complete"}
    except Exception as e:
        return {"status": "failed", "error": str(e)}

import pyautogui
import time
from Om_E_Tree.ome.utils.builder.input_args_builder import build_input_args
import platform

is_mac = platform.system() == "Darwin"

import pyautogui
import time
from Om_E_Tree.ome.utils.builder.input_args_builder import build_input_args
import platform

is_mac = platform.system() == "Darwin"

import pyautogui
import time
from Om_E_Tree.ome.utils.builder.input_args_builder import build_input_args
import platform

is_mac = platform.system() == "Darwin"

import pyautogui
import time
from Om_E_Tree.ome.utils.builder.input_args_builder import build_input_args
import platform

is_mac = platform.system() == "Darwin"

def hotkey(args):
    try:
        # Use build_input_args to check for missing arguments and fill defaults
        args = build_input_args("keyboard", "hotkey")
        
        # Ensure 'keys' is a valid list and use default if missing
        if "keys" not in args or not isinstance(args["keys"], list):
            args["keys"] = ["ctrl", "c"]  # Default hotkey if not provided
        
        # Log keys to check if they're correct
        print(f"Attempting to press hotkey combination: {args['keys']}")

        # Define valid modifier keys (ctrl, shift, etc.)
        valid_modifier_keys = ["ctrl", "shift", "alt", "cmd", "command"]
        
        # Check if the first key is a modifier key, if not, swap them
        if args["keys"]:
            if args["keys"][0] not in valid_modifier_keys:
                print(f"[WARN] First key '{args['keys'][0]}' is not a valid modifier. Swapping the first two keys.")
                args["keys"] = [args["keys"][1], args["keys"][0]]  # Swap the order if first key is not a modifier

        # Validate modifier keys and allow other keys (letters, numbers, etc.)
        for key in args["keys"]:
            if key not in valid_modifier_keys and not isinstance(key, str):
                raise ValueError(f"Invalid key: {key}. Allowed modifier keys are {valid_modifier_keys}.")

        # Perform the hotkey action with retry logic
        retries = 3
        for i in range(retries):
            try:
                print(f"Simulating hotkey: {args['keys']}, Attempt {i + 1}")
                pyautogui.hotkey(*args["keys"])
                time.sleep(0.1)  # Adding a small delay for better key press handling
                return {"status": "complete"}
            except Exception as e:
                if i == retries - 1:  # Last retry, then fail
                    print(f"Failed to execute hotkey action after {retries} attempts: {e}")
                    return {"status": "failed", "error": str(e)}
                else:
                    print(f"Retrying hotkey action... Attempt {i + 1}")

    except Exception as e:
        print(f"Error in hotkey function: {e}")
        return {"status": "failed", "error": str(e)}






def key_down(args):
    try:
        # Use build_input_args to check for missing arguments and fill defaults
        args = build_input_args("keyboard", "key_down")
        
        # If 'key' argument is still missing, use the default value
        if "key" not in args:
            args["key"] = "shift"  # Default key if not provided
        
        pyautogui.keyDown(args["key"])
        print(f"Key down: {args['key']}")
        return {"status": "complete"}
    except Exception as e:
        return {"status": "failed", "error": str(e)}

def key_up(args):
    try:
        # Use build_input_args to check for missing arguments and fill defaults
        args = build_input_args("keyboard", "key_up")
        
        # If 'key' argument is still missing, use the default value
        if "key" not in args:
            args["key"] = "shift"  # Default key if not provided
        
        pyautogui.keyUp(args["key"])
        print(f"Key up: {args['key']}")
        return {"status": "complete"}
    except Exception as e:
        return {"status": "failed", "error": str(e)}

def write_slow(args):
    try:
        # Only fill in missing arguments, do not overwrite provided ones
        defaults = build_input_args("keyboard", "write_slow")
        for key, value in defaults.items():
            if key not in args or args[key] is None:
                args[key] = value
        
        # If 'text' argument is still missing, use the default value
        if "text" not in args:
            args["text"] = "Typing slowly..."  # Default text if not provided
        
        interval = args.get("interval", 0.1)
        pyautogui.write(args["text"], interval=interval)
        print(f"Typed text slowly: {args['text']} with interval: {interval}s")
        return {"status": "complete"}
    except Exception as e:
        return {"status": "failed", "error": str(e)}

def press_keys_sequence(args):
    try:
        # Use build_input_args to check for missing arguments and fill defaults
        args = build_input_args("keyboard", "press_keys_sequence")
        
        # If 'keys' argument is missing, use the default value
        if "keys" not in args or not isinstance(args["keys"], list):
            args["keys"] = ["a", "b", "c"]  # Default sequence if not provided
        
        for key in args["keys"]:
            pyautogui.press(key)
            print(f"Pressed key: {key}")
        return {"status": "complete"}
    except Exception as e:
        return {"status": "failed", "error": str(e)}

# ----------------------------------------
# macOS-specific Shortcuts
# ----------------------------------------

def open_spotlight(args):
    try:
        pyautogui.hotkey("command", "space")
        return {"status": "complete"}
    except Exception as e:
        return {"status": "failed", "error": str(e)}

def switch_apps(args):
    try:
        pyautogui.hotkey("command", "tab")
        return {"status": "complete"}
    except Exception as e:
        return {"status": "failed", "error": str(e)}

def lock_screen(args):
    try:
        pyautogui.hotkey("command", "control", "q")
        return {"status": "complete"}
    except Exception as e:
        return {"status": "failed", "error": str(e)}

def screenshot(args):
    try:
        pyautogui.hotkey("command", "shift", "4")
        return {"status": "complete"}
    except Exception as e:
        return {"status": "failed", "error": str(e)}

def minimize_window(args):
    try:
        pyautogui.hotkey("command", "m")
        return {"status": "complete"}
    except Exception as e:
        return {"status": "failed", "error": str(e)}

def quit_application(args):
    try:
        pyautogui.hotkey("command", "q")
        return {"status": "complete"}
    except Exception as e:
        return {"status": "failed", "error": str(e)}
    
def copy_selected_text(args):
    try:
        # Use build_input_args to fill in any missing arguments with defaults from the contract
        args = build_input_args("keyboard", "copy_selected_text")
        
        # Ensure the 'key' argument is set correctly (default to 'command' for macOS or 'ctrl' for Windows)
        if "key" not in args or not isinstance(args["key"], str):
            args["key"] = "command" if is_mac else "ctrl"  # Default to "command" for macOS, "ctrl" for Windows
        
        # Log the final key to be used for copy operation
        print(f"Using key: {args['key']} for copy operation")

        # Perform the copy operation (cmd/c for macOS or ctrl/c for Windows)
        if is_mac:
            pyautogui.hotkey("command", "c")
        else:
            pyautogui.hotkey("ctrl", "c")

        # Log success message
        print(f"Copied selected text using {'command' if is_mac else 'ctrl'} + 'c'")

        return {"status": "complete"}

    except ValueError as ve:
        # Handle specific value errors (e.g., missing or invalid arguments)
        print(f"[ERROR] ValueError: {ve}")
        return {"status": "failed", "error": str(ve)}

    except Exception as e:
        # General exception handling to catch any unexpected errors
        print(f"[ERROR] Unexpected error during copy action: {e}")
        return {"status": "failed", "error": str(e)}

    
def refresh_browser(args):
    try:
        # Use build_input_args to check for missing arguments and fill defaults
        args = build_input_args("keyboard", "refresh_browser")
        
        # Perform the refresh action (cmd/r for macOS or ctrl/r for Windows)
        if is_mac:
            pyautogui.hotkey("command", "r")
        else:
            pyautogui.hotkey("ctrl", "r")

        # Log the action for debugging purposes
        print("Refreshed browser.")
        return {"status": "complete"}
    except Exception as e:
        return {"status": "failed", "error": str(e)}

def paste_clipboard(args):
    try:
        # Use build_input_args to check for missing arguments and fill defaults
        args = build_input_args("keyboard", "paste_clipboard")
        
        # Perform the paste action (cmd/v for macOS or ctrl/v for Windows)
        if is_mac:
            pyautogui.hotkey("command", "v")
        else:
            pyautogui.hotkey("ctrl", "v")

        # Log the action for debugging purposes
        print("Pasted clipboard contents using {'command' if is_mac else 'ctrl'} + 'v'")
        return {"status": "complete"}
    
    except Exception as e:
        # Handle any error that occurs during the paste operation
        return {"status": "failed", "error": str(e)}
def focus_address_bar(args):
    try:
        # Use build_input_args to check for missing arguments and fill defaults
        args = build_input_args("keyboard", "focus_address_bar")
        
        # Perform the focus action (cmd+l for macOS or ctrl+l for Windows)
        if is_mac:
            pyautogui.hotkey("command", "l")
        else:
            pyautogui.hotkey("ctrl", "l")

        # Log the action for debugging purposes
        print("Focused on the address bar.")
        return {"status": "complete"}
    
    except Exception as e:
        return {"status": "failed", "error": str(e)}
def new_tab(args):
    try:
        # Use build_input_args to check for missing arguments and fill defaults
        args = build_input_args("keyboard", "new_tab")
        
        # Perform the new tab action (cmd+t for macOS or ctrl+t for Windows)
        if is_mac:
            pyautogui.hotkey("command", "t")
        else:
            pyautogui.hotkey("ctrl", "t")

        # Log the action for debugging purposes
        print("Opened a new browser tab.")
        return {"status": "complete"}
    
    except Exception as e:
        return {"status": "failed", "error": str(e)}
def close_tab(args):
    try:
        # Use build_input_args to check for missing arguments and fill defaults
        args = build_input_args("keyboard", "close_tab")
        
        # Perform the close tab action (cmd+w for macOS or ctrl+w for Windows)
        if is_mac:
            pyautogui.hotkey("command", "w")
        else:
            pyautogui.hotkey("ctrl", "w")

        # Log the action for debugging purposes
        print("Closed the current browser tab.")
        return {"status": "complete"}
    
    except Exception as e:
        return {"status": "failed", "error": str(e)}
def navigate_back(args):
    try:
        # Use build_input_args to check for missing arguments and fill defaults
        args = build_input_args("keyboard", "navigate_back")
        
        # Perform the navigate back action (cmd+[ for macOS or alt+left for Windows)
        if is_mac:
            pyautogui.hotkey("command", "[")
        else:
            pyautogui.hotkey("alt", "left")

        # Log the action for debugging purposes
        print("Navigated back in the browser.")
        return {"status": "complete"}
    
    except Exception as e:
        return {"status": "failed", "error": str(e)}
def navigate_forward(args):
    try:
        # Use build_input_args to check for missing arguments and fill defaults
        args = build_input_args("keyboard", "navigate_forward")
        
        # Perform the navigate forward action (cmd+] for macOS or alt+right for Windows)
        if is_mac:
            pyautogui.hotkey("command", "]")
        else:
            pyautogui.hotkey("alt", "right")

        # Log the action for debugging purposes
        print("Navigated forward in the browser.")
        return {"status": "complete"}
    
    except Exception as e:
        return {"status": "failed", "error": str(e)}
def hold_and_press(args):
    try:
        # Use build_input_args to check for missing arguments and fill defaults
        args = build_input_args("keyboard", "hold_and_press")
        
        # Ensure we have the necessary arguments: key_to_hold, key_to_press, repeat_count
        key_to_hold = args.get("key_to_hold", "command")  # Default to "command" key if not provided
        key_to_press = args.get("key_to_press", "tab")  # Default to "tab" key if not provided
        repeat_count = args.get("repeat_count", 8)  # Default to 8 repetitions if not provided
        
        # Hold down the first key
        pyautogui.keyDown(key_to_hold)
        print(f"Holding down {key_to_hold}")

        # Press the second key 'repeat_count' times
        for _ in range(repeat_count):
            pyautogui.press(key_to_press)
            time.sleep(0.5)  # Optional delay between presses

        # Release the first key after pressing the second key
        pyautogui.keyUp(key_to_hold)
        print(f"Released {key_to_hold}")

        return {"status": "complete"}

    except Exception as e:
        return {"status": "failed", "error": str(e)}
def key_hold(args):
    try:
        # Use build_input_args to check for missing arguments and fill defaults
        args = build_input_args("keyboard", "key_hold")
        
        # Ensure we have the necessary arguments: key, duration
        key = args.get("key", "shift")  # Default to "shift" key if not provided
        duration = args.get("duration", 2)  # Default to 2 seconds if duration not provided
        
        # Hold down the key
        pyautogui.keyDown(key)
        print(f"Holding down {key} for {duration} seconds.")
        
        # Hold the key for the specified duration
        time.sleep(duration)
        
        # Release the key after the specified duration
        pyautogui.keyUp(key)
        print(f"Released {key} after {duration} seconds.")

        return {"status": "complete"}

    except Exception as e:
        return {"status": "failed", "error": str(e)}
def type_with_delay(args):
    try:
        # Use build_input_args to check for missing arguments and fill defaults
        args = build_input_args("keyboard", "type_with_delay")
        
        # If 'text' argument is still missing, use the default value
        if "text" not in args:
            args["text"] = "Hello from Om-E"  # Default text if not provided
        
        # If 'delay_between_keys' is missing, use the default value
        delay_between_keys = args.get("delay_between_keys", 0.3)  # Default delay of 0.3s

        # Type text with delay between each keystroke
        for char in args["text"]:
            pyautogui.write(char)
            time.sleep(delay_between_keys)  # Add delay between keystrokes

        print(f"Typed text with delay: {args['text']} (delay: {delay_between_keys}s)")
        return {"status": "complete"}

    except Exception as e:
        return {"status": "failed", "error": str(e)}
