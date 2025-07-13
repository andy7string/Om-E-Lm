# Om-E-py (OME)
 source venv/bin/activate
## Project Overview & Philosophy

**Om-E-py** is a modern, extensible Python 3.11+ library for macOS UI automation and accessibility. It is a fork and evolution of the ATOMac project, reimagined for:
- **Modern Python and macOS:** Full support for Python 3.11+ and recent macOS versions (Sonoma, Ventura, etc.)
- **Robust, scriptable automation:** Automate, test, and inspect any macOS application using accessibility APIs
- **Data-driven workflows:** All UI scanning, navigation, and action is driven by JSONL metadata, enabling scalable, maintainable, and auditable automation
- **Extensibility:** The codebase is modular, thoroughly commented, and designed for advanced customization and integration
- **Best practices:** Emphasizes separation of scanning/action, metadata-only storage, and robust error handling

### Why Om-E-py?
- **ATOMac, modernized:** The original ATOMac was a breakthrough for Mac UI automation, but was limited to Python 2 and older macOS. Om-E-py brings this power to the modern Python/macOS ecosystem.
- **JSONL-first architecture:** By separating UI scanning (metadata extraction) from action/navigation, Om-E-py enables workflows that are scalable, testable, and easy to debug or audit. All UI structure is stored as JSONL, never as live objects.
- **Scriptable and hackable:** Every part of the workflow—from app focus, to menu/window scanning, to navigation and action—is exposed as a Python API, with clear extension points for advanced users.
- **Accessibility and reliability:** Built on top of macOS accessibility APIs, Om-E-py is robust to UI changes, supports error handling, and can be used for both automation and accessibility auditing.

### High-Level Architecture
- **Core API:** The `ome` package exposes the main automation classes (`NativeUIElement`, `Clipboard`, `Prefs`, etc.) for direct UI interaction.
- **Utils Layer:** The `ome/utils/` directory contains all supported helpers for app focus, environment configuration, menu/window extraction, navigation, and more. This is the canonical place for all automation workflows.
- **JSONL Workflows:** All menu and window structures are exported as JSONL files, which are then used for navigation, action, and auditing. This enables both lazy and eager loading, and makes it easy to diff, test, or share UI metadata.
- **Extensible and testable:** The codebase is designed for maintainability, with clear separation of concerns, robust error handling, and extensive docstrings and comments.

---

*The following sections provide a comprehensive guide to setup, usage, architecture, best practices, and advanced workflows in Om-E-py.*

## Features
- Python 3.11+ compatibility
- Modern, robust macOS UI automation and accessibility
- Menu and window scanning, traversal, and action (JSONL-driven)
- App focus and full screen helpers
- Clipboard and preferences utilities
- Environment/delay configuration via `.env`
- Thoroughly commented and extensible codebase

## Setup & Requirements

### Supported Platforms
- **Python:** 3.11 or newer (recommended for best compatibility and performance)
- **macOS:** Recent versions (tested on Sonoma, Ventura, and Monterey)
- **Architecture:** Apple Silicon (M1/M2) and Intel Macs supported

### Core Dependencies
- `mac-pyxa` — Modern, generic app automation for macOS
- `appscript` — AppleScript bridge for Python
- `requests` — HTTP requests (used for some automation workflows)
- `beautifulsoup4` — HTML parsing (used for some UI extraction)
- `macimg` — macOS image helpers (optional, for screenshots)
- `future` — Python 2/3 compatibility (legacy, but required by some modules)
- `psutil` — Process stats and management
- `python-dotenv` — Environment variable management
- `pyautogui` — Mouse/keyboard automation (used in some workflows)
- `rapidfuzz` — Fast fuzzy string matching (for menu path finding)

> All core dependencies are listed in `requirements.txt` and are pinned for compatibility. Do not upgrade without testing.

### Development & Testing Dependencies
- `pytest` — Testing framework
- (Add others as needed in `requirements-dev.txt`)

### Accessibility Permissions
- **Required:** Om-E-py uses macOS Accessibility APIs. You must grant your terminal (or Python interpreter) Accessibility permissions in System Settings > Privacy & Security > Accessibility.
- If automation fails with permission errors, check and re-grant these permissions.

### Environment Configuration (.env)
- All delays, export directories, and environment variables are managed via a `.env` file (see `ome/utils/env/`).
- Example `.env` entries:
  ```
  MENU_EXPORT_DIR=ome/data/menus
  ACTION_DELAY=0.5
  WINDOW_WAIT_TIMEOUT=10.0
  ```
- See `ome/utils/env/env.py` for all supported variables and defaults.

### Step-by-Step Setup
1. **Clone the repository:**
   ```sh
   git clone <your-repo-url>
   cd Om-E-py
   ```
2. **Create and activate a virtual environment:**
   ```sh
   python3.11 -m venv venv
   ¸
   ```
3. **Install core dependencies:**
   ```sh
   pip install -r requirements.txt
   ```
4. **(Optional) Install development/testing dependencies:**
   ```sh
   pip install -r requirements-dev.txt
   ```
5. **Install the package in editable mode:**
   ```sh
   pip install -e .
   ```
6. **(Recommended) Copy and edit the example `.env` file:**
   ```sh
   cp ome/utils/env/.env.example ome/utils/env/.env
   # Edit as needed for your environment
   ```
7. **Grant Accessibility permissions:**
   - Open System Settings > Privacy & Security > Accessibility
   - Add your terminal (or Python interpreter) and ensure it is checked

### Troubleshooting Setup
- **Permission errors:** Double-check Accessibility permissions and restart your terminal.
- **Dependency issues:** Ensure you are using Python 3.11+ and a clean virtual environment. Do not mix system/site packages.
- **.env not loaded:** Ensure your `.env` file is in `ome/utils/env/` and is readable.
- **Apple Silicon issues:** If using M1/M2, ensure all dependencies are installed for arm64 (not x86_64 emulation).
- **Updating dependencies:** Only update packages after testing for compatibility. Some macOS/pyobjc packages are sensitive to version changes.

---

*You are now ready to use Om-E-py for robust, modern macOS UI automation. The following sections cover scanning/action architecture, workflows, and API usage in detail.*

## Scanning & Action Architecture (JSONL-Driven Workflows)

Om-E-py is built around a robust, scalable, and auditable two-phase workflow for UI automation, using JSONL metadata files as the backbone for all scanning, navigation, and action. This architecture is designed for reliability, maintainability, and advanced automation scenarios.

### Why Separate Scanning and Action?
- **Robustness:** By scanning and storing UI structure as metadata, you decouple automation from live UI state, making scripts more reliable and less brittle to UI changes.
- **Auditability:** JSONL files provide a clear, versionable record of the UI structure at any point in time. You can diff, test, and review changes easily.
- **Maintainability:** Keeping scanning and action logic separate makes it easier to debug, extend, and maintain large automation projects.
- **Performance:** Lazy loading and targeted scanning mean you only extract or update what you need, when you need it.

### Scanning Phase: Extracting UI Metadata
- **Purpose:** Walk the app's menus or windows, extract all relevant metadata, and store it as JSONL (one object per line).
- **How:** Use helpers like `build_menu` (for menus) or your own window extraction scripts.
- **What is stored:**
  - `menu_path` or `path`: Unique identifier for the element (e.g., `["Mail", "File", "New Message"]`)
  - `title`: Displayed title of the element
  - `role`: Accessibility role (e.g., `AXMenuItem`)
  - `AXEnabled`: Whether the item is enabled
  - `shortcut_modifiers`, `AXIdentifier`, `AXHelp`, etc.: All actionable metadata
  - `omeClick`: Fallback click coordinates (if available)
  - `children_titles`, `child_count`: For navigation and UI mapping
- **Filtering:** Extract only enabled, disabled, or all items as needed. Use filters to exclude unwanted roles/titles.
- **JSONL Example:**
  ```json
  {"title": "New Message", "menu_path": ["Mail", "File", "New Message"], "AXEnabled": true, "shortcut_modifiers": "⌘N", "omeClick": [100, 200]}
  ```

#### Example: Scanning and Exporting Menus
```python
from ome.utils.builder.app.appMenu_builder import build_menu
items = build_menu('com.apple.mail', filter_mode='enabled')
# Output: ome/data/menus/menu_com.apple.mail_enabled.jsonl
```

### Action Phase: Navigation and Automation
- **Purpose:** Load the relevant JSONL file, resolve the path to the desired UI element, and perform actions (click, type, etc.).
- **How:** Use helpers like `get_menu_path_by_title` and `menu_nav` to resolve and activate menu items.
- **Lazy Loading:** If a node in the JSONL has `has_children` but no `children`, trigger a scan for that branch and update the JSONL on the fly.
- **Updating Metadata:** After navigation or action, update the JSONL to reflect any new structure or state.
- **Always cleanup:** Call `ome.cleanup.cleanup()` after actions to release resources.

#### Example: Navigating and Pressing a Menu Item
```python
from ome.utils.uiNav.menuPath_controller import get_menu_path_by_title, menu_nav
result = get_menu_path_by_title('settings', 'com.apple.mail')
menu_nav('title', 'settings', 'com.apple.mail')
```

### Best Practices
- **Always separate scanning and action logic.**
- **Store only metadata in JSONL, never live objects.**
- **Always cleanup after scans or actions.**
- **Use filtering to keep your JSONL clean and actionable.**
- **Use separate JSONL files for menus and windows, prefixed with `menu_` and `win_` for clarity.**
- **Version and diff your JSONL files** to track UI changes over time.

### Advanced Usage
- **Lazy loading:** Only scan children as you navigate deeper, updating the JSONL as needed.
- **Diffing menu structures:** Use JSONL files to compare UI changes between app versions or states.
- **Troubleshooting:** If navigation fails, inspect the JSONL for missing/incorrect paths, or rescan the relevant branch.
- **Custom metadata:** Extend the scanning helpers to include additional fields as needed for your automation.

### Field Reference: JSONL Structure
- `menu_path` / `path`: List of strings representing the unique path to the element
- `title`: The displayed title of the menu/window/item
- `role`: Accessibility role (e.g., `AXMenuItem`, `AXWindow`)
- `AXEnabled`: Boolean, whether the item is enabled
- `shortcut_modifiers`: String, e.g., `⌘N` (if available)
- `AXIdentifier`: Unique identifier (if available)
- `AXHelp`: Help text (if available)
- `omeClick`: [x, y] coordinates for fallback clicking
- `children_titles`: List of child item titles
- `child_count`: Number of children
- (Add more fields as needed for your workflow)

---

*This architecture enables robust, scalable, and maintainable UI automation for any macOS application. The following sections cover menu/window extraction, navigation, and advanced API usage in detail.*

## Menu and Window Extraction, Export, and Navigation

Om-E-py provides robust, scriptable helpers for extracting, exporting, and navigating menus and windows in any macOS application. All workflows are built on top of the JSONL-driven architecture described above.

### Menu Extraction & Export
- **Canonical helper:** `ome/utils/builder/appMenu_builder.py` (`build_menu`)
- **Purpose:** Walks the app's menu bar and all submenus, extracts actionable metadata, and exports it as JSONL.
- **Filtering:** Extract all, only enabled, or only disabled menu items for efficiency and clarity.
- **Output:** JSONL file(s) in the directory specified by `MENU_EXPORT_DIR` (from your `.env`).
  - Example: `ome/data/menus/menu_com.apple.mail_enabled.jsonl`
- **How to interpret:** Each line is a JSON object representing a menu item, with fields like `title`, `menu_path`, `AXEnabled`, `shortcut_modifiers`, `omeClick`, etc.

**Example: Export enabled menu items for Mail.app**
```python
from ome.utils.builder.app.appMenu_builder import build_menu
items = build_menu('com.apple.mail', filter_mode='enabled')
# Output: ome/data/menus/menu_com.apple.mail_enabled.jsonl
```

- **Best practices:**
  - Always filter out irrelevant roles/titles for clean, actionable JSONL
  - Regenerate/export JSONL after major app updates or UI changes
  - Version and diff your JSONL files to track changes

### Window Extraction & Export
- **Canonical helper:** (If you have a custom window extraction script, document it here. Otherwise, adapt the menu extraction pattern.)
- **Purpose:** Walks all windows of an app, extracts actionable metadata, and exports as JSONL.
- **Output:** JSONL file(s) in a directory of your choice (e.g., `win_<bundleid>.jsonl`)
- **How to extend:** Use the same pattern as menu extraction—walk windows, extract metadata, and write to JSONL.

**Example: (Pseudo-code for window extraction)**
```python
# Example: You may need to implement or adapt a window extraction helper
from ome.AXClasses import NativeUIElement
app = NativeUIElement.getAppRefByBundleId('com.apple.mail')
for window in app.windows():
    # Extract metadata, write to JSONL
    pass
```

### Menu Navigation & Activation
- **Canonical helper:** `ome/utils/uiNav/menuPath_controller.py` (`get_menu_path_by_title`, `menu_nav`)
- **Purpose:** Resolve a fuzzy label or path to the best-matching menu item, and activate it (if enabled).
- **How it works:**
  - Loads the relevant menu JSONL file (e.g., `menu_com.apple.mail_enabled.jsonl`)
  - Uses fuzzy matching to resolve the label/path
  - Focuses the app, walks the menu hierarchy, and activates the menu item
- **Output:** Activates the menu item in the UI, returns metadata for inspection

**Example: Fuzzy match and activate a menu item**
```python
from ome.utils.uiNav.menuPath_controller import get_menu_path_by_title, menu_nav
result = get_menu_path_by_title('settings', 'com.apple.mail')
print(result)  # {'title': 'Settings…', 'menu_path': ['Mail', 'Settings…']}
menu_nav('title', 'settings', 'com.apple.mail')
```

- **Best practices:**
  - Always use the latest exported JSONL for navigation
  - If a menu item is missing, rescan/export the menu structure
  - Use fuzzy matching for robust navigation, but verify results for ambiguous labels

### Troubleshooting & Tips
- **Missing menu items:** Rescan/export the menu structure, check for filtering issues
- **Path resolution fails:** Inspect the JSONL for typos, missing nodes, or ambiguous paths
- **Menu item not enabled:** Check the app state, or try exporting with `filter_mode='all'` to see all items
- **Window extraction:** If you need advanced window scanning, extend the menu extraction pattern for your app
- **Performance:** For large apps, use filtering and lazy loading to keep JSONL files manageable

---

*With these helpers and best practices, you can build robust, maintainable, and scalable menu/window automation workflows for any macOS application.*

## Core API and Main Classes

Om-E-py exposes a powerful, extensible API for macOS UI automation. The following are the main classes and helpers you will use in real-world automation workflows.

### NativeUIElement (`ome.AXClasses`)
**Purpose:** The main class for interacting with UI elements and applications. Use this for all direct UI queries, actions, and navigation.

**Key Methods:**
- `getAppRefByBundleId(bundle_id: str) -> NativeUIElement`: Get the top-level element for an app by bundle ID
- `findFirst(**criteria) -> NativeUIElement or None`: Find the first child matching criteria (e.g., `AXRole='AXButton'`)
- `findAll(**criteria) -> list[NativeUIElement]`: Find all children matching criteria
- `menuItem(*args) -> NativeUIElement`: Traverse the menu bar to find a menu item by path
- `sendKey(keychr: str)`, `sendKeys(keystr: str)`: Simulate keypresses
- `activate()`: Bring the app/window to the foreground
- `waitFor(timeout, notification, **kwargs)`: Wait for a UI event/notification
- `windows()`: List all windows for the app

**Example:**
```python
from ome.AXClasses import NativeUIElement
app = NativeUIElement.getAppRefByBundleId('com.apple.mail')
button = app.findFirst(AXRole='AXButton')
if button:
    button.Press()
```

**Best Practices:**
- Use `findFirst`/`findAll` with accessibility attributes for robust element search
- Always call `activate()` before performing actions if the app may be in the background
- Use `waitFor` and related methods for reliable, event-driven automation

---

### Clipboard (`ome.Clipboard`)
**Purpose:** Interact with the macOS clipboard for text, RTF, images, and more. Useful for copy/paste automation and data transfer.

**Key Methods:**
- `Clipboard.copy(data)`: Set clipboard data (string or list)
- `Clipboard.paste()`: Get clipboard data (string)
- `Clipboard.clearAll()`: Clear clipboard contents and properties
- `Clipboard.isEmpty(datatype=None)`: Check if clipboard is empty for a given type

**Example:**
```python
from ome.Clipboard import Clipboard
Clipboard.copy("Hello, world!")
text = Clipboard.paste()
```

**Best Practices:**
- Always clear the clipboard before setting new data in automation workflows
- Use `isEmpty()` to verify clipboard state before/after actions

---

### Prefs (`ome.Prefs`)
**Purpose:** Read and write macOS application preferences (NSUserDefaults). Useful for preparing or inspecting app state before automation.

**Key Methods:**
- `Prefs(bundleID, bundlePath=None, defaultsPlistName='Defaults')`: Create a Prefs instance for an app
- `p[key]`, `p.get(key)`: Read a preference
- `p[key] = value`, `p.set(key, value)`: Write a preference

**Example:**
```python
from ome.Prefs import Prefs
prefs = Prefs('com.apple.mail')
prefs['SomeKey'] = 'SomeValue'
```

**Best Practices:**
- Always create a new Prefs instance before reading/writing to ensure you have the latest state
- Use this to set up app state before launching for automation

---

### cleanup (`ome.cleanup`)
**Purpose:** Manage and clean up UI elements/resources to prevent memory leaks and ensure resources are released after automation tasks.

**Key Methods:**
- `cleanup.register(obj)`: Register a UI element or resource for cleanup
- `cleanup.cleanup()`: Cleanup all registered elements and force garbage collection
- `cleanup.clear()`: Clear the registry without cleanup

**Example:**
```python
import ome.cleanup
ome.cleanup.register(my_ui_element)
ome.cleanup.cleanup()
```

**Best Practices:**
- Always call `ome.cleanup.cleanup()` after automation tasks, scans, or actions
- Register any UI element that may hold system resources

---

### Utilities (`ome/utils/`)
**Purpose:** All supported helpers for app focus, environment configuration, menu/window extraction, navigation, and more.

**Key Modules:**
- `app_focus.py`: `ensure_app_focus(bundle_id, fullscreen=True)` — Ensures the app is running, focused, and optionally full screen
- `env/env.py`: Loads `.env` config, exposes delay constants, export directories, and helpers like `get_env`, `verify_env`
- `builder/appMenu_builder.py`: `build_menu(bundle_id, filter_mode='enabled')` — Extract and export menu structures
- `uiNav/menuPath_controller.py`: `get_menu_path_by_title(label, bundle_id)`, `menu_nav(mode, label, bundle_id)` — Fuzzy menu path finding and navigation

**Example:**
```python
from ome.utils.builder.app.appMenu_builder import build_menu
result = build_menu('com.apple.mail')
if result['status'] == 'success':
    app = result['app']
    # Now safe to automate
```

**Best Practices:**
- Use these helpers for all automation workflows; do not use deprecated modules
- Customize or extend helpers as needed for advanced workflows

---

*For advanced usage, see the source code and docstrings in each module. All new automation should use these classes and helpers for robust, maintainable workflows.*

## Core API and Usage

- **NativeUIElement:** Main class for UI automation (find, click, type, etc.)
- **Clipboard:** Copy/paste text and more
- **Prefs:** Read/write app preferences
- **cleanup:** Manage and cleanup UI resources
- **App focus:** `ensure_app_focus(bundle_id)`
- **Menu extraction/navigation:** See above

**Example:**
```python
from ome.AXClasses import NativeUIElement
app = NativeUIElement.getAppRefByBundleId('com.apple.mail')
button = app.findFirst(AXRole='AXButton')
if button:
    button.Press()
```

## Utilities (`ome/utils/`)
- **App focus:** `app_focus.py`
- **Environment:** `env/env.py`
- **Menu extraction:** `builder/appMenu_builder.py`
- **Menu navigation:** `uiNav/menuPath_controller.py`
- **Other helpers:** See submodules for advanced workflows

---

**License:** MIT (or as specified in LICENSE)

**Note:** For advanced usage, see the source code and docstrings in each module. All new automation should use the helpers in `ome/utils/` and the main API classes above.