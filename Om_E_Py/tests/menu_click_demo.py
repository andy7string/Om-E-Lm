import ome
import time

def click_top_menu_items(num_to_click=3):
    app = ome.getFrontmostApp()
    app.activate()
    time.sleep(0.5)
    menu_bar = app.menuBar()
    print("Top-level menu items:")
    for i, menu in enumerate(menu_bar.AXChildren):
        print(f"{i}: {menu.AXTitle}")
        if i < num_to_click:
            try:
                # Click the first item in each top-level menu
                first_item = menu.AXChildren[0].AXChildren[0]
                print(f"Clicking '{menu.AXTitle}' > '{first_item.AXTitle}'")
                first_item.Press()
                time.sleep(1)
            except Exception as e:
                print(f"Could not click menu '{menu.AXTitle}': {e}")

if __name__ == "__main__":
    click_top_menu_items(3) 