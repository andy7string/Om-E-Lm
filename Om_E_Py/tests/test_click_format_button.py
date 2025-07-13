import sys
import os
from ome.utils.builder.app.app_focus import ensure_app_focus

if __name__ == '__main__':
    bundle_id = "com.apple.mail"
    app = ensure_app_focus(bundle_id)
    try:
        window = app.AXFocusedWindow
    except Exception:
        window = None
    if not window:
        print("Could not get focused window.")
        sys.exit(1)
       # Try to find the Delete button by AXTitle or AXDescription
    delete_button = window.findFirst(AXRole='AXButton', AXTitle='Delete')
    if not delete_button:
        delete_button = window.findFirst(AXRole='AXButton', AXDescription='Delete')
    if not delete_button:
        # Fallback: search all AXButtons for either attribute
        for btn in window.findAllR(AXRole='AXButton'):
            try:
                title = getattr(btn, 'AXTitle', None)
            except Exception:
                title = None
            try:
                desc = getattr(btn, 'AXDescription', None)
            except Exception:
                desc = None
            if (title and title == 'Delete') or (desc and desc == 'Delete'):
                delete_button = btn
                break
    if delete_button:
        try:
            delete_button.Press()
            print("Clicked the Delete button!")
        except Exception as e:
            print(f"Error pressing Delete button: {e}")
    else:
        print("Delete button not found via AXTitle/AXDescription search.") 