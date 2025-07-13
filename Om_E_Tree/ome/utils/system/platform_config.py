import os
from env import TREE_PLATFORM

# ===================================================
# 🧠 Get platform identifier from environment
# ===================================================

def get_platform():
    """
    Returns the current platform name from the environment,
    defaulting to 'mac' if not set.

    Returns:
        str: Platform string ('mac', 'windows', etc.)
    """
    return TREE_PLATFORM

# ===================================================
# 🍏 macOS check
# ===================================================

def is_mac():
    """
    Checks if the current platform is macOS.

    Returns:
        bool: True if macOS
    """
    return get_platform() == "mac"

# ===================================================
# 🪟 Windows check
# ===================================================

def is_windows():
    """
    Checks if the current platform is Windows.

    Returns:
        bool: True if Windows
    """
    return get_platform() == "windows"
