import sys
from ome.omeMenus import scan_children
import ome

# Change this to a bundle id you have running, e.g. 'com.apple.finder' or 'com.apple.mail'
BUNDLE_ID = 'com.apple.finder'

def main():
    try:
        app = ome.getAppRefByBundleId(BUNDLE_ID)
        # Try menu bar first, fallback to first window
        try:
            element = app.AXMenuBar
        except Exception:
            windows = app.windows()
            if not windows:
                print('No windows found for app.')
                return
            element = windows[0]
        result = scan_children(element, depth=2)
        print('scan_children result:')
        for item in result:
            print(item)
    except Exception as e:
        print(f'Error: {e}')
        sys.exit(1)

if __name__ == '__main__':
    main() 