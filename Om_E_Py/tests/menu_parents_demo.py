import ome
import time
import AppKit
import Quartz


def click_at(x, y):
    # Move and click at (x, y) using Quartz
    event1 = Quartz.CGEventCreateMouseEvent(None, Quartz.kCGEventMouseMoved, (x, y), Quartz.kCGMouseButtonLeft)
    event2 = Quartz.CGEventCreateMouseEvent(None, Quartz.kCGEventLeftMouseDown, (x, y), Quartz.kCGMouseButtonLeft)
    event3 = Quartz.CGEventCreateMouseEvent(None, Quartz.kCGEventLeftMouseUp, (x, y), Quartz.kCGMouseButtonLeft)
    Quartz.CGEventPost(Quartz.kCGHIDEventTap, event1)
    Quartz.CGEventPost(Quartz.kCGHIDEventTap, event2)
    Quartz.CGEventPost(Quartz.kCGHIDEventTap, event3)
    time.sleep(0.2)

def print_menu_parents_and_click():
    app = ome.getFrontmostApp()
    app.activate()
    time.sleep(0.5)
    app_name = getattr(app, 'AXTitle', None) or getattr(app, 'AXDescription', None) or str(app)
    print(f"Frontmost app: {app_name}")
    try:
        menu_bar = app.menuBar()
    except Exception as e:
        print(f"No menu bar found for this app: {e}")
        return
    print("Top-level menu parents:")
    for i, menu in enumerate(menu_bar.AXChildren):
        title = getattr(menu, 'AXTitle', None)
        pos = getattr(menu, 'AXPosition', None)
        size = getattr(menu, 'AXSize', None)
        print(f"{i}: Title='{title}', Position={pos}, Size={size}")
        # Try to click the center of the menu parent if position and size are available
        if pos and size:
            center_x = int(pos[0] + size[0] / 2)
            center_y = int(pos[1] + size[1] / 2)
            print(f"  Clicking at ({center_x}, {center_y})")
            click_at(center_x, center_y)
        else:
            print("  No position/size info, cannot click.")
        time.sleep(0.5)

if __name__ == "__main__":
    print_menu_parents_and_click() 