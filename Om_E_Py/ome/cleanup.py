"""
ome.cleanup - Global cleanup utility for UI elements and resources.

Usage:
    import ome.cleanup
    ome.cleanup.register(obj)  # Register UI element for cleanup
    ome.cleanup.cleanup()      # Cleanup all registered elements and free memory
    ome.cleanup.clear()        # Clear the registry (optional)

You can call cleanup() after automation tasks, tests, or externally as needed.
"""
import gc

# Registry of objects to clean up
_tracked_elements = set()

def register(obj):
    """Register a UI element or resource for cleanup."""
    _tracked_elements.add(obj)

def cleanup():
    """Cleanup all registered UI elements and force garbage collection."""
    global _tracked_elements
    for obj in list(_tracked_elements):
        # Try to call a .cleanup() or .release() method if present
        if hasattr(obj, 'cleanup') and callable(obj.cleanup):
            try:
                obj.cleanup()
            except Exception:
                pass
        elif hasattr(obj, 'release') and callable(obj.release):
            try:
                obj.release()
            except Exception:
                pass
        # Remove strong reference
        try:
            _tracked_elements.remove(obj)
        except KeyError:
            pass
        del obj
    gc.collect()

def clear():
    """Clear the registry of tracked elements."""
    _tracked_elements.clear() 