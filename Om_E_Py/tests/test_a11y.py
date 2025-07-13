import ome

def test_accessibility():
    # Example: Try to get the Finder app and print its menu bar children
    try:
        app = ome.getAppRefByBundleId('com.apple.finder')
        menu_bar = app.AXMenuBar
        children = getattr(menu_bar, 'AXChildren', [])
        print('Menu bar children:')
        for child in children:
            print(getattr(child, 'AXTitle', None))
    except Exception as e:
        print(f'Accessibility test failed: {e}')

if __name__ == '__main__':
    test_accessibility() 