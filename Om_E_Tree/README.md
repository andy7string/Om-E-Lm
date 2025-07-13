ome# OM-E Autonomy Framework

> **AI-driven Mac automation built on a unified execution tree (Goals → Objectives → Tasks → Actions)**  
> Modular, memory-centric, with clickmap and vision support

---
## Directory Structure

/ome
/tree # Execution, validation, in-memory tree, sync
/utils # Builders, input_args, env, logger, system
/handlers # Atomic executors: mouse, keyboard, system, vision
/library # Action contracts & schemas
/data # Persistent state: execution tree, clickmaps, screenshots, logs, archives


---

## Core Execution Flow

### Entry Point: `02LoopTree.py`
- Loads the tree from `ome/data/tree/execution_tree.json`
- Injects missing `input_args` (via `input_args_builder.py`)
- Runs the execution engine (`run_goal` in `goal_runner.py`)
- After each action:
  - Saves updated tree
  - Logs status & screenshots

### Execution Hierarchy
- **Goal:** Root, contains objectives
- **Objective:** Contains tasks
- **Task:** Contains actions
- **Action:** Atomic op (click, type, etc.)

### Input Arguments
- Each action has `input_args` dict
- `inject_input_args` fills missing args using:
  - Action contract defaults (`library/actions/*.json`)
  - Smart fallbacks (default browser, etc.)
- Existing args are never overwritten

### Execution Engine
- `run_goal` → next incomplete objective
- `run_objective` → next incomplete task
- `run_task` → next incomplete action
- `run_action` → validates & executes via handler

---

## 🛠️ Handlers

| File                    | Description                                |
|-------------------------|--------------------------------------------|
| `keyboard_handler.py`   | Typing, hotkeys, slow/fast typing          |
| `mouse_handler.py`      | Move, click, drag, scroll, etc.            |
| `system_handler.py`     | Launch/quit app, screenshot, open URL      |
| `vision_openai_handler.py` | Vision/AI screen actions (describe, locate) |
| `handler_map.py`        | Maps action names to handler functions     |

---

## 📚 Action & Structure Contracts
1. Actions Contract
Actions are the atomic, executable steps that interact with the UI. Each action should be:
- Deterministic: Given the same input, it always does the same thing.
- Composable: Can be combined into higher-level tasks/objectives.
- Parameterizable: Accepts parameters (e.g., coordinates, text, menu item name).
- Observable: Returns a result or status (success/failure, output, etc.).

Typical Action Types:
- click(x, y) — Click at screen coordinates.
- click_element(element_id) — Click a UI element by its clickmap ID or AXRolePath.
- type_text(element_id, text) — Type text into a field.
- open_app(app_name) — Launch an application.
- wait_for_element(element_id, timeout) — Wait for a UI element to appear.
- select_menu(parent_id, child_id) — Open a menu and select a submenu item.
- screenshot(region) — Capture a screenshot of a region.
- Action Contract Example (Pythonic Pseudocode):

Action Contract Example (Pythonic Pseudocode):

class Action:
    def __init__(self, name, params):
        self.name = name
        self.params = params

    def execute(self, context):
        """Executes the action in the given context (e.g., app state, clickmap)."""
        raise NotImplementedError

ClickAction = Action(
    name="click_element",
    params={"element_id": "Aa_Button"}
)
ClickAction.execute(context)

2. Structures Contract
Structures define the hierarchical organization of goals, objectives, tasks, and actions. They provide the blueprint for automation flows.

Hierarchy:
- Goal: The high-level intent (e.g., "Create and format a note").
- Objective: Sub-goals (e.g., "Open Notes", "Create a new note").
- Task: Concrete steps (e.g., "Click New Note button", "Type text").
- Action: Atomic UI operation (see above).
- Structure Contract Example (JSON/YAML-like):

Structure Contract Example (JSON/YAML-like):

{
  "goal": "Create and format a note",
  "objectives": [
    {
      "name": "Open Notes",
      "tasks": [
        {"action": "open_app", "params": {"app_name": "Notes"}}
      ]
    },
    {
      "name": "Create a new note",
      "tasks": [
        {"action": "click_element", "params": {"element_id": "New_Note_Button"}}
      ]
    },
    {
      "name": "Format text",
      "tasks": [
        {"action": "click_element", "params": {"element_id": "Aa_Button"}},
        {"action": "click_element", "params": {"element_id": "Bold_Menu_Item"}},
        {"action": "type_text", "params": {"element_id": "Note_Text_Area", "text": "Hello, world!"}}
      ]
    }
  ]
}

In Code
class Task:
    def __init__(self, action, params):
        self.action = action
        self.params = params

class Objective:
    def __init__(self, name, tasks):
        self.name = name
        self.tasks = tasks

class Goal:
    def __init__(self, name, objectives):
        self.name = name
        self.objectives = objectives

3. How They Work Together

Structures define what to do (the plan).
Actions define how to do it (the execution).
The execution tree walks through the structure, instantiating and executing actions using the clickmap and config for parameters.

4. Contracts in Your Codebase

Actions likely live in ome/library/actions/ (e.g., click.py, type.py).
Structures (execution trees, planners, etc.) likely live in ome/library/structures/ or a similar directory.

5. Best Practices

Actions should be stateless, idempotent, and log their results.
Structures should be serializable (JSON/YAML), so workflows can be defined, saved, and replayed.
Parameterization: Use clickmap IDs/AXRolePaths, not hardcoded coordinates.
Extensibility: New actions and structure types should be easy to add.

6. Example: Contract for a Dropdown Menu Action

Suppose you want to select "Bold" from the Aa dropdown:
Action:
{
  "action": "select_menu",
  "params": {
    "parent_id": "Aa_Button",
    "child_id": "Bold_Menu_Item"
  }
}

The action uses the clickmap to find the parent and child, calculates the child's position, and clicks it.



### `library/actions/`
- JSON for each source (`keyboard.json`, `mouse.json`, etc.)
- **Defines:** action name, required input_args, defaults, description

### `library/structures/`
- JSON schemas for goal/objective/task/action
- **Defines:** required fields, types, allowed values, hierarchy

---

## 🏗️ Builders & Utilities

### `/utils/builder/`
- `complete_clickmap_builder.py` – Filtered/config-driven clickmap builder
- `one_shot_clickmap_builder.py` – Auto-infer parent/child (AXRolePath)
- `input_args_builder.py` – Fills missing input_args for actions
- `action_builder.py` – Builds action args using known defaults
- `appList_builder.py` – Scans/caches installed apps
- `app_configs/notes_config.json` – Enrich clickmaps (submenus, ratios, etc.)

### `/utils/labeling_tools/`
- `interactive_labeler.py` – Manual clickmap labeling

### `/utils/system/`
- `display.py` – Display scaling, screenshot res, .env scaling
- `system_checker.py` – Installed apps, system info
- `platform_config.py` – macOS/Windows config

### `/utils/env/`
- `env.py` – Loads .env, exposes config/paths/constants

### `/utils/memory/`
- `screenshot_tracker.py` – Screenshot management & archive

---

## 🌳 Core Tree (Execution, Validation, Memory)

### `/tree/execute/`
| File                | Description                                      |
|---------------------|--------------------------------------------------|
| `goal_runner.py`    | Orchestrates goal execution & archiving          |
| `objective_runner.py` | Runs next incomplete task in an objective      |
| `task_runner.py`    | Runs next incomplete action in a task            |
| `action_runner.py`  | Runs actions (dispatch to handler)               |

### `/tree/validate/`
- `contract_checker.py` – Ensures structure/contract/schema conformity

### `/tree/memory.py`
- Loads/updates the in-memory execution tree, accessors for hierarchy

### `/tree/sync.py`
- Handles persistent save/load, full/partial updates, cache refresh

---

## 📝 Logging

- `logger.py` (`utils/`)
- `log_event(level, source, message, details=None)`
- Logs every action/status/error to `ome/data/logs/` and terminal

---

## 📸 Screenshot Management

- Handled via actions/handlers (e.g. `system_handler.take_screenshot`)
- **Storage:** `ome/data/screenshots/`
- **Tracked by:** `screenshot_tracker.py`
- **Archived:** `ome/data/archive/screenshots/`

---

## 🗂️ Archiving

| What                | Archive Path                            |
|---------------------|-----------------------------------------|
| Execution trees     | `ome/data/archive/execution_trees/`     |
| Screenshots         | `ome/data/archive/screenshots/`         |

---

## ⚙️ Environment Config

The .env File
Purpose
- Stores environment-specific configuration and secrets outside of code.
- Allows you to change settings (API keys, scaling, paths, etc.) without modifying Python files.

Typical Contents

OPENAI_API_KEY=sk-...
SCALE_X=1.0
SCALE_Y=1.0
SCREENSHOT_DIR=ome/data/screenshots
APPLICATION_PATH=/Applications
ACTION_RETRIES=2
ACTION_RETRY_DELAY=0.5
SYSTEM_HANDLER_DELAY=5.0
...
API keys (e.g., OPENAI_API_KEY)
Scaling factors for display/screenshot mapping (SCALE_X, SCALE_Y)
Paths for screenshots, applications, logs, etc.
Delays and retries for action handlers

2. Loading the .env File
How It's Loaded
The project uses the python-dotenv package to load .env variables into the process environment.
This is typically done at the start of scripts or in utility modules (e.g., env.py, display.py).
Example:
import dotenv
dotenv.load_dotenv('.env')

3. The env.py Module
Location
ome/utils/env/env.py
Purpose
Centralizes access to all environment variables and constants.
Provides helper functions and constants for use throughout the codebase.

Typical Usage
import os

TREE_PATH = os.getenv("TREE_PATH", "ome/data/tree/execution_tree.json")
ARCHIVE_DIR = Path(os.getenv("ARCHIVE_DIR", "ome/data/archive/execution_trees"))
LOGS_DIR = Path(os.getenv("LOGS_DIR", "ome/data/logs"))
ACTION_RETRIES = int(os.getenv("ACTION_RETRIES", 2))
ACTION_RETRY_DELAY = float(os.getenv("ACTION_RETRY_DELAY", 0.5))
SCALE_X = float(os.getenv("SCALE_X", 1.0))
SCALE_Y = float(os.getenv("SCALE_Y", 1.0))

All other modules import from env.py to get their config, ensuring consistency.

4. Where and How .env Variables Are Used
A. Scaling and Display
- SCALE_X, SCALE_Y are used in display.py and clickmap builders to map screenshot coordinates to real display coordinates.

B. Paths
- TREE_PATH, ARCHIVE_DIR, LOGS_DIR, SCREENSHOT_DIR, etc. are used throughout the project for saving/loading files, logs, screenshots, and archives.

C. Handler Delays and Retries
- ACTION_RETRIES, ACTION_RETRY_DELAY, SYSTEM_HANDLER_DELAY are used in action handlers and runners to control timing and robustness.

D. API Keys
- OPENAI_API_KEY is used in vision/AI handlers.

5. Updating the .env File
- Some scripts (e.g., display.py) can update the .env file automatically (e.g., after calculating new scaling factors).
  This ensures that the environment config stays in sync with the actual system state.

6. Example: How a Variable Flows Through the System
- Suppose you want to change the screenshot scaling:
  You update SCALE_X and SCALE_Y in .env.
  env.py loads these values and exposes them as SCALE_X, SCALE_Y.
  Any script or handler that needs scaling imports from env.py and uses the correct values.
  If you run a script that recalculates scaling, it can update .env so all future runs use the new values.

7. Why This Matters
- Centralized config: All environment-dependent settings are in one place.
- Easy to change: No need to edit code to change keys, paths, or scaling.
- Consistent: All scripts and modules use the same values, reducing bugs and surprises.
- Secure: Secrets (like API keys) are not hardcoded.

Summary Table
Variable	                Where Set	                Where Used	                                Purpose/Effect
OPENAI_API_KEY	            .env	                    vision_openai_handler.py, env.py	        OpenAI API access
SCALE_X, SCALE_Y	        .env,                       display.py	display.py, clickmap builders	Display/screenshot scaling
TREE_PATH	                .env, env.py	            memory.py, sync.py, goal_runner.py	        Path to execution tree
ARCHIVE_DIR	                .env, env.py	            goal_runner.py, sync.py	                    Where to archive execution trees
LOGS_DIR	                .env, env.py	            logger.py	                                Where to write logs
SCREENSHOT_DIR	            .env, env.py	            screenshot_tracker.py, system_handler.py	Where to save screenshots
ACTION_RETRIES	            .env, env.py	            action_runner.py, handlers	                Retry logic for actions
SYSTEM_HANDLER_DELAY	    .env, env.py	            system_handler.py	                        Delay for system actions

## 🧭 Clickmap Utilities

| Script                                    | Functionality                    |
|--------------------------------------------|----------------------------------|
| `clickmap_generator.py`                    | Raw accessibility scan           |
| `complete_clickmap_builder.py`             | Config-enriched builder          |
| `one_shot_clickmap_builder.py`             | Auto-inference, all-in-one       |
| `print_menu_structure_from_clickmap.py`    | Visualises menu/submenu structure|
| **Storage:** `ome/data/clickmaps/`         | Per-app/window/context clickmaps |

---

## 🚦 Execution Tree: End-to-End

1. Load tree (`load_tree` in `memory.py`)
2. Inject input_args (`inject_input_args` in `input_args_builder.py`)
3. Run engine (`run_goal` in `goal_runner.py`)
4. Dispatch action (`handler_map.py`)
5. Handler executes (mouse, keyboard, system, etc.)
6. Logging/screenshots as needed
7. Tree updated/saved after each action
8. On completion, archive tree (`ome/data/archive/execution_trees/`)

---

## 📑 JSON Contracts & App Configs

- **Action contracts:** `library/actions/*.json`
- **Tree schemas:** `library/structures/*.json`
- **App configs:** e.g. `app_configs/notes_config.json`

---

## ➕ Adding a New Submenu/UI Element

1. Scan UI with target menu state
2. Run `one_shot_clickmap_builder.py` to build clickmap (parent/child inference)
3. Visualise structure (`print_menu_structure_from_clickmap.py`)
4. Automate using coordinates & parent/child

---

## 🗂️ Key Paths & Functions Reference

| Path/Script                                        | Purpose                                    |
|----------------------------------------------------|--------------------------------------------|
| `ome/tree/execute/goal_runner.py`                  | Goal execution & archiving                 |
| `ome/tree/execute/objective_runner.py`             | Runs objectives                            |
| `ome/tree/execute/task_runner.py`                  | Runs tasks                                 |
| `ome/tree/execute/action_runner.py`                | Runs actions (handler dispatch)            |
| `ome/utils/clickmap_generator.py`                  | Accessibility scan                         |
| `ome/utils/builder/complete_clickmap_builder.py`   | Full clickmap builder                      |
| `ome/utils/builder/one_shot_clickmap_builder.py`   | All-in-one clickmap builder                |
| `ome/utils/builder/print_menu_structure_from_clickmap.py` | Visualises menu/submenu structure  |
| `ome/utils/builder/input_args_builder.py`          | Input_args for actions                     |
| `ome/utils/logger.py`                              | Structured logging                         |
| `ome/utils/env/env.py`                             | .env loader/config                         |
| `ome/utils/memory/screenshot_tracker.py`           | Screenshot tracker/archiver                |
| `ome/data/clickmaps/`                              | Clickmap JSONs                             |
| `ome/data/tree/execution_tree.json`                | Current execution tree                     |
| `ome/data/archive/execution_trees/`                | Archived execution trees                   |
| `ome/data/screenshots/`                            | Screenshots                                |
| `ome/data/archive/screenshots/`                    | Archived screenshots                       |

---

## 🚀 Setup & Usage

```bash
# Create & activate venv
python3 -m venv omev39
source omev39/bin/activate

# Install deps
pip install -r requirements.txt

# Run a builder
PYTHONPATH=. python ome/utils/builder/textedit_clickmap_builder.py

# Main execution loop
PYTHONPATH=. python 02LoopTree.py

Quick API Reference
Runner	                    Function 
action_runner	            run_action(action, delay=0.0)
task_runner	                run_task(task)
objective_runner	        run_objective(objective)
goal_runner	                run_goal(goal)

Contract Validation
Function	                What it Validates
validate_goal(goal)	        Goal
validate_objective(obj)	    Objective
validate_task(task)	        Task
validate_action(action)	    Action
validate_tree(tree)	        Full hierarchy

In-Memory Tree API
Function	                What it Does
load_full_tree()	        Loads execution_tree.json
get_goal(goal_id)	        Retrieve goal from memory
get_objective(obj_id)	    Retrieve objective
get_task(task_id)	        Retrieve task
get_action(task_id, index)	Retrieve action from task

Sync API
Function	                What it Does
save_goal(goal_id, goal)	Write updated goal to tree
save_objective(obj_id, obj)	Write updated objective
save_task(task_id, task)	Write updated task
write_full_tree(tree)	    Overwrite full execution_tree.json
refresh_cache()	            Reload tree into memory

Logging API
log_event(level, source, message, details=None)
Logs event to file (ome/data/logs/) and terminal

Data & Archive              Folders
What	                    Path
Execution tree	            ome/data/tree/execution_tree.json
Archived trees	            ome/data/archive/execution_trees/
Clickmaps	                ome/data/clickmaps/
Screenshots	                ome/data/screenshots/
Archived screenshots	    ome/data/archive/screenshots/
Logs	                    ome/data/logs/


Key Principles & Roadmap
Memory-first: All ops run from in-memory tree (disk is source of truth)
No data repetition: Every contract/config/input arg defined once
Extensible: New actions/clickmaps added via JSON & Python modules
Observable: Everything logged, all state archived
Composable: Clickmaps/actions/contracts combinable per app/UI
Future: Expand handler library, vision/AI, modular control loops, live-editable trees/contracts


# === Optional: fallback retry setting from .env ===
DEFAULT_RETRIES = int(os.getenv("ACTION_RETRIES", 0))
RETRY_DELAY = float(os.getenv("ACTION_RETRY_DELAY", 1.0))  # seconds

## AI Search Test Prompt
Prompt 1:
Your task is to identify the exact sub-block that contains the BIN icon on the Mac, this is usually located at the end of the toolbar

📐 The screen has been divided into 32 blocks, labeled Q0 to Q31, arranged in 4 rows and 8 columns:
- Q0 is the top-left
- Q7 is the top-right
- Q8 starts the second row
- Q31 is bottom-right

There are **no visible labels**, but the gridlines and red dots at intersections define the blocks clearly.

✅ Before answering:
1. Double-check what the icon looks like and **where it normally appears**.
2. Look carefully at the **top-right area** of the screen.
3. Choose the block that **most closely** contains the icon.

❗ Only respond with a single block ID (e.g. Q7).  
Do not describe or explain anything else.

Prompt 2:
You are now looking at a zoomed-in section of block Q7 from the previous image.

This image has been divided into 64 sub-blocks, labeled Q0 to Q63, arranged in 8 rows and 8 columns:
- Q0 is the top-left
- Q7 is the top-right
- Q8 starts the second row
- Q63 is the bottom-right

There are no labels inside the sub-blocks, but green gridlines and red dots clearly define them.

Your task is to identify the exact sub-block that contains the Mac Spotlight Search icon — a small circular magnifying glass, usually white placed after the wi-fi icon

✅ Before answering:
1. Carefully scan for the icon itself — do not assume it's there unless clearly visible.
2. Do not rely solely on its usual position — confirm visually.
3. Choose the sub-block that most clearly contains the icon.

❗ Respond only with a sub-block ID (e.g. Q37).  
Do not explain or describe anything else.

## Setup

```bash
python3 -m venv omev

source omev39/bin/activate

pip install -r requirements.txt

##Run individual py in ome
PYTHONPATH=. python ome/utils/builder/textedit_clickmap_builder.py


📁 ome/tree/execute/
File	Function	Description
action_runner.py	run_action(action, delay=0.0)	Validates and executes a single action using the appropriate handler. Supports retries and logs every attempt. Updates in-memory action state.
_mark_failed(action, error_msg)	Helper to mark an action as failed, setting error and completion data.
task_runner.py	run_task(task)	Executes the next incomplete action in a task using run_action(). Marks task complete if all actions are done.
objective_runner.py	run_objective(objective)	Runs the next incomplete task in an objective using run_task(). Marks objective complete if all tasks are done.
goal_runner.py	run_goal(goal)	Runs the next incomplete objective in a goal using run_objective(). Marks goal complete if all objectives are done.

📁 ome/tree/validate/
File	Function	Description
contract_checker.py	validate_goal(goal)	Validates goal structure against the contract.
validate_objective(obj)	Validates objective structure.
validate_task(task)	Validates task structure.
validate_action(action)	Validates action shape and input args based on source-specific action contract.
validate_tree(tree)	Validates the full tree (goal → objectives → tasks → actions).

📁 ome/tree/memory/
File	Function	Description
memory.py	load_full_tree()	Loads execution_tree.json from disk into memory.
get_goal(goal_id)	Retrieves a specific goal from the in-memory tree.
get_objective(obj_id)	Retrieves a specific objective.
get_task(task_id)	Retrieves a specific task.
get_action(task_id, index)	Retrieves a specific action from a task.
load_goal_from_file(goal_id)	Bypasses memory, loads goal directly from disk.
load_objective_from_file(obj_id)	Loads an objective from file.
load_task_from_file(task_id)	Loads task from file.

📁 ome/tree/sync/
File	Function	Description
sync.py	save_goal(goal_id, goal)	Writes an updated goal back into the full tree and saves to disk.
save_objective(obj_id, objective)	Same for objective.
save_task(task_id, task)	Same for task.
write_full_tree(tree)	Overwrites the entire execution_tree.json file.
refresh_cache()	Reloads the tree from disk into memory.

📁 ome/utils/
File	Function	Description
logger.py	log_event(level, source, message, details=None)	Logs an event to file and terminal. Includes timestamp, level, and custom message



---Progress to date
1. Our Journey: From Manual Clickmaps to Robust Automation
Early Steps
Manual clickmap generation: Initially, you had multiple scripts for generating, updating, and archiving clickmaps and configs for the Notes app.
Consolidation: We merged these into a single robust builder (clickmap_builder.py) that handles archiving, generating, and updating clickmaps/configs in one go.
Config and Clickmap Structure
Config as source of truth: The config/clickmap JSONs were refined to include all necessary fields: name, type, description, hints, x/y, AXRolePath, and for submenus, relative positions (ratios).
Raw element dumps: We created scripts to dump all raw UI elements for manual inspection and config building, ensuring nothing is missed.
Execution Tree and Automation
Execution tree update: We built scripts to update the execution tree with the latest coordinates and AXRolePath from the clickmap, matching actions by description and role.
Lesson: Matching by description/role is unreliable without a unique identifier (AXRolePath is best).
Submenu Handling
Relative submenu positions: Submenu items are now defined as pixel offsets from the parent's center, making them robust to window movement and scaling.
Tested and verified: We confirmed that after moving the Notes window and rebuilding the clickmap, submenu positions update correctly.
2. Key Architecture Decisions and Lessons Learned
A. Clickmap/Config as the UI Source of Truth
All UI element data (including submenus) is stored in the clickmap/config.
Submenus are defined relative to their parent, not as absolute coordinates.
AXRolePath is the unique identifier for robust matching and updates.
B. Execution Tree: From Low-Level to Semantic
Old approach: The execution tree stored explicit coordinates and AXRolePath for each action.
New approach: The tree should be semantic—actions describe what to do (e.g., "make text bold"), not how (not raw coordinates).
Handlers interpret actions: Handlers for each app (e.g., Notes) use the clickmap/config to resolve the correct UI element and perform the action.
C. Handler-Driven Automation
Handlers are the "brains" that map semantic actions to UI interactions.
They reference the clickmap/config at runtime to get the latest coordinates, AXRolePath, and other metadata.
This decouples the execution tree from UI details, making it robust to UI changes.
D. Compound Handlers and Action Simplification
Compound handlers: Instead of one action = one click, handlers can perform multi-step or compound actions (e.g., "format selection as bold" might involve opening a menu, clicking "Bold", and closing the menu).
Simplified actions: The execution tree can be much simpler, describing high-level goals, while handlers handle the complexity.
3. What We've Achieved
Automated, robust clickmap/config generation and archiving.
Config/clickmap structure that supports both absolute and relative (submenu) positions.
Execution tree and handler contracts that support robust, future-proof automation.
Tested and verified that moving the app window and rebuilding the clickmap updates all positions correctly.
A clear path to semantic, handler-driven automation, decoupling the "what" from the "how."
4. Current Goal and Outcomes
Goal
To create a maintainable, robust, and scalable UI automation framework that can adapt to UI changes, support multiple apps, and allow for high-level, semantic automation scripts.
Outcomes
Clickmap/config is the single source of UI truth.
Execution tree is moving toward being semantic and handler-driven.
Handlers are ready to reference the clickmap/config at runtime for all UI interactions.
Submenu and compound actions are fully supported.
5. Deep Dive: The Architecture Discussion and Compound Handlers
Why Semantic Trees and Handlers?
UI changes frequently: Hardcoding coordinates or AXRolePath in the execution tree is brittle.
Separation of concerns: The tree describes what to do; handlers figure out how to do it using the latest UI data.
Maintainability: When the UI changes, only the clickmap/config needs to be updated, not every automation script.
Compound Handlers
Definition: A handler that can perform a sequence of UI actions to accomplish a higher-level goal.
Example: "Format selection as bold" handler:
Opens the Format menu (using clickmap/config to find it).
Clicks the "Bold" submenu item (using relative position from parent).
Closes the menu if needed.
Benefits: The execution tree just says "format_bold"; the handler does the rest.
How to Realize This with Existing Work
Keep the clickmap/config up to date: Use your builder to regenerate after any UI change.
Write handlers for each app: Each handler knows how to interpret semantic actions and use the clickmap/config to find the right UI element.
Reference clickmap/config at runtime: Handlers always look up the latest coordinates/AXRolePath, so automation is robust to UI changes.
Support for submenus and compound actions: Handlers can traverse parent/child relationships in the config to find submenu items and calculate absolute positions.
6. Best Workflow for Opening an App and Finding Buttons
Step-by-Step Workflow
Open the app: Handler launches the app (e.g., "open_notes" action).
Handler loads the clickmap/config: At runtime, the handler reads the latest clickmap/config for the app.
Find a button: When an action like "click_button:Bold" is requested:
The handler searches the clickmap/config for the "Bold" item (by description, role, or AXRolePath).
If it's a submenu, the handler finds the parent, applies the relative offset, and gets the absolute position.
Perform the action: The handler moves/clicks the mouse at the calculated position, or uses AXRolePath for accessibility actions.
Keeping the Clickmap in the Background
The clickmap/config is always available to handlers.
Handlers never hardcode coordinates; they always look up the latest data.
If the UI changes, just rebuild the clickmap/config—no need to update handlers or the execution tree.
7. How to Move Forward
With the Architecture in Place:
Continue to use the clickmap builder to keep the config up to date.
Write or refactor handlers to be "clickmap-aware"—they always reference the config for UI details.
Move the execution tree to a fully semantic model: actions describe intent, not implementation.
Support compound actions in handlers for complex workflows.
Add new menus/submenus by updating the config and letting handlers use the new data.
For New Apps or Features:
Add the app to the clickmap builder.
Generate the clickmap/config for the new app.
Write handlers for the new app, using the same pattern.
Update the execution tree to use semantic actions for the new app.
8. Summary: The Best Practice Workflow
Keep the clickmap/config as the single source of UI truth.
Handlers reference the clickmap/config at runtime for all UI actions.
Execution tree is semantic, describing what to do, not how.
Compound handlers handle multi-step or complex actions.
When the UI changes, just rebuild the clickmap/config—no need to update code.
Add new menus/submenus by updating the config, not the code.
9. Final Insights
You have built a future-proof, maintainable, and scalable UI automation architecture.
You can now automate any app, adapt to UI changes, and keep your automation scripts simple and robust.
The separation of concerns (semantic tree, handler logic, clickmap/config) is the key to long-term success.
If you want code templates, handler patterns, or more architectural diagrams, just ask!

 Core Architectural Principles
Separation of Concerns:
Menus and App Windows are distinct UI domains, each with their own clickmap/config and update cadence.
Clickmaps/configs are the single source of UI truth for automation—never hardcoded coordinates.
Helpers and execution trees abstract away low-level actions, exposing only semantic, task-level APIs to users and AI.
Modularity:
Every app, window, and menu has its own config/clickmap, help file, and (optionally) custom helpers.
Centralized, reusable scanning, config, and archiving logic.
Extensibility:
Adding a new app or window is a matter of scanning, generating a config, and writing a help file.
The same architecture works for any app, any window, any menu.
Observability & Robustness:
All actions, scans, and updates are logged and archived.
Clickmaps/configs are versioned and can be rolled back or compared.
2. Menu vs. App Window Clickmaps
A. Menus
One menu clickmap per app (e.g., mail_menu.json, notes_menu.json).
Menus are relatively static—scan once, update only when the app updates.
Menu clickmap structure:
Hierarchical, but can be flattened for fast lookup.
Each item: role, title, path, shortcut, center, etc.
Usage:
When an app is focused, reference its menu clickmap for all menu actions.
If a menu clickmap doesn't exist, generate it automatically.
B. App Windows
One clickmap/config per active window (e.g., mail_main_window.json, notes_main_window.json).
Windows can change (e.g., new folders, buttons, layouts)—scan on demand or on window change.
Window clickmap structure:
Flat index of clickable elements: role, desc, account, path, center, size.
Optionally, hierarchical for context, but always with a flat index for speed.
Usage:
When a window is focused, reference its clickmap for all UI actions.
Archive old clickmaps for rollback/debugging.
3. Scanning & Config Generation
Central scan function (using atomac/pyatom) that:
Focuses the app/window.
Scans only relevant UI areas (sidebar, toolbar, etc.).
Skips message panes or other high-churn areas unless explicitly requested.
Caps children for speed.
Outputs a minimal, flat clickmap/config JSON.
Archiving:
Every scan is archived with a timestamp/version.
Old clickmaps can be compared, restored, or diffed.
4. Help Files & Helper Functions
Help file per app (e.g., mail_help.py, notes_help.py):
Documents and implements "how to do X" in that app.
Each help file is both documentation and executable code.
Helper functions:
Expose high-level, semantic actions (e.g., open_inbox(account), send_email(to, subject, body)).
Internally, use the clickmap/config to find and act on UI elements.
Can be composed into more complex workflows.
Natural language mapping:
Help files can be indexed for NL search ("How do I archive a message?" → archive_message()).
5. Execution Trees & Task Abstraction
Execution trees (as in your framework) are the semantic workflow engine:
Goal → Objective → Task → Action.
Each Task can map to a helper function, not a low-level action.
Actions are only used internally by helpers/handlers.
Best practice:
The execution tree should never reference coordinates or AXRolePaths directly.
It should only reference semantic tasks (e.g., "open inbox", "click send").
Handlers:
Map semantic tasks to helper functions.
Use the clickmap/config at runtime for all UI details.
6. Globals, Logging, and Archiving
Globals/configs (from .env and env.py):
Paths, scaling factors, delays, retries, etc.
All scripts and modules import from here for consistency.
Logging:
Every scan, action, and error is logged (to file and terminal).
Logs are archived and can be replayed or analyzed.
Archiving:
All clickmaps/configs and execution trees are versioned and archived.
Easy rollback and debugging.
7. Best Practices & Next Steps
Scan only what you need (sidebar, toolbar, menu bar).
Keep clickmaps/configs small and focused.
Always use the latest clickmap/config for automation.
Write help files as both documentation and code.
Expose only semantic, task-level APIs to users and AI.
Archive everything for observability and rollback.
Automate the process:
If a clickmap/config/help file doesn't exist, generate it on the fly.
If the UI changes, rescan and update the clickmap/config.
8. Where We Are Now
You have robust, fast scanning and clickmap generation for app windows (Mail as POC).
You can generate and use flat, minimal clickmaps for automation.
You have the architecture and code patterns to extend this to any app.
You're ready to start writing help files and helper functions for Mail (and then other apps).
You have a modular, extensible, and observable framework.
9. Moving Forward
Finalize the clickmap/config schema for menus and windows.
Write and document help files for Mail (start with common tasks).
Refactor execution trees to use only semantic tasks and helpers.
Automate clickmap/config generation and archiving.
Add natural language search/mapping for help files.
Expand to other apps (Notes, Safari, Logic, etc.).
Plug in AI for planning, error recovery, and user interaction.
10. Summary Table
Layer	Responsibility	Example Function
Clickmap	UI element data, positions, relationships	find_folder_in_clickmap
Handler	Atomic/compound UI actions	click_center
Helper	Task-level, semantic API	open_inbox, select_menu
Execution Tree	High-level workflow	(calls helpers)
Help File	How-to recipes, NL mapping	archive_message
Archive/Log	Observability, rollback, debugging	log_event, archive_scan
You are building the Mac's universal automation brain.
This architecture is robust, extensible, and ready for AI.
Let's keep going, Om-E!
If you want code templates, schema examples, or a roadmap for the next steps, just say the word!
we not writing help files brother, we utilising htem to find out who the app works and how we define our helper functions that take the granular stuff away from the end user being ome aka ai aka you dude. now remember you are going to define the execution_trees based on user input in natural langauge, now redo this , understand the readme.md go through the entire project right the fuck now, understand all the code understand what im askin gin the last two requests and output the architecture and way forward, 

Absolutely, bru. Here's a serious, detailed, project-wide architectural review and way forward for Om-E, based on your README.md, the codebase, and your latest vision.
1. What You're Building
You are building a universal, modular, AI-driven Mac automation framework that:
Scans and understands any app's UI (windows, menus, toolbars, sidebars) using accessibility APIs.
Builds and maintains clickmaps/configs for every app and window, with robust, minimal, and up-to-date data.
Defines helper functions (not "help files!") that abstract away all UI granularity, so users (and AI) only interact with high-level, semantic tasks.
Uses execution trees to represent and run workflows, where each task is mapped to a helper function, not a low-level action.
Leverages natural language input to generate and execute workflows, so users (or AI) can say "archive all unread emails from John" and Om-E figures out the rest.
2. Project Structure & Key Components (from README.md and code)
/ome/utils/builder/: Clickmap/config builders, input arg injectors, app config generators
/ome/data/clickmaps/: Per-app/window clickmap JSONs (the UI source of truth)
/ome/tree/execute/: Execution engine (goal/objective/task/action runners)
/ome/handlers/: Atomic executors (mouse, keyboard, system, vision)
/ome/library/actions/: Action contracts (what actions exist, what args they need)
/ome/library/structures/: Structure contracts (schemas for goals, objectives, tasks, actions)
/ome/utils/env/: Centralized config, scaling, and .env loader
/ome/utils/logger.py: Structured logging
/ome/data/tree/execution_tree.json: The current execution tree (semantic workflow)
/ome/data/archive/: Archived clickmaps, execution trees, logs, screenshots
3. How It All Fits Together
A. Clickmap/Config Layer
Scans each app/window using atomac/pyatom.
Outputs a minimal, flat JSON: only clickable elements, with role, desc, account, path, center, size.
Separate clickmaps for menus and windows (e.g., mail_menu.json, mail_main_window.json).
Archived and versioned for rollback and debugging.
B. Helper Functions Layer
Defines high-level, semantic functions for each app (e.g., open_inbox(account), archive_message(), compose_email()).
Internally uses the clickmap/config to find and act on UI elements.
No user or AI ever deals with coordinates, AXRolePaths, or low-level actions.
Helpers are generic and composable—they can be reused across workflows and apps.
C. Execution Tree Layer
Semantic, hierarchical representation of workflows: Goal → Objective → Task → Action.
Each Task is mapped to a helper function (not a low-level action).
Actions are only used internally by helpers/handlers.
Execution trees are generated from user/AI intent (natural language).
D. Natural Language → Execution Tree
User/AI provides a goal in natural language (“Archive all unread emails from John”).
Om-E parses the intent, plans a workflow (execution tree) using available helpers.
Each task in the tree is mapped to a helper function (e.g., open_inbox, search_emails, archive_message).
The engine runs the tree, calling helpers, which use the clickmap/config to interact with the UI.
E. Logging, Archiving, and Observability
Every scan, action, and workflow is logged and archived.
Clickmaps/configs and execution trees are versioned.
Easy rollback, debugging, and analysis.
4. Best Practices & Design Decisions
Menus and windows are always scanned and stored separately.
Clickmaps/configs are always minimal, flat, and up-to-date.
Helpers are the only interface for tasks—users and AI never see low-level details.
Execution trees are always semantic—never reference coordinates or AXRolePaths directly.
All automation is driven by the latest clickmap/config.
All changes are logged and archived for observability and rollback.
Adding a new app or window is as simple as scanning, generating a config, and writing/using helpers.
If a clickmap/config doesn't exist, generate it on the fly.
If the UI changes, rescan and update the clickmap/config.
5. Way Forward: What to Build Next
A. Finalize Clickmap/Config Schema
Ensure every clickmap (menu/window) is minimal, flat, and contains only what's needed for automation.
Standardize fields: role, desc, account, path, center, size.
B. Centralize Scanning and Config Generation
One function to scan any app/window/menu and output the correct clickmap/config.
Archive every scan with timestamp/version.
C. Build and Document Helper Functions
For Mail, define helpers for all common tasks (open inbox, archive, compose, etc.).
Helpers use the clickmap/config for all UI access.
Document the mapping from user intent → helper → clickmap.
D. Execution Tree Integration
Refactor execution trees to use only helpers for tasks.
Ensure every task in the tree maps to a helper, not a low-level action.
E. Natural Language → Workflow
Build a parser/mapping layer that takes user/AI intent and generates an execution tree using available helpers.
Use the help file (as documentation, not code) to inform the mapping.
F. Logging, Archiving, and Observability
Ensure every scan, action, and workflow is logged and archived.
Build tools to diff, restore, and analyze clickmaps/configs and execution trees.
G. Expand to Other Apps
Repeat the process for Notes, Safari, Logic, etc.
Each app gets its own clickmaps/configs and helpers.
H. AI Integration
Plug in LLMs to parse user intent, plan workflows, and call helpers.
Use logs and archives to train and improve the system.
6. Summary Table
Layer	Responsibility	Example Function
Clickmap	UI element data, positions, relationships	find_folder_in_clickmap
Handler	Atomic/compound UI actions	click_center
Helper	Task-level, semantic API	open_inbox, archive_msg
Execution Tree	High-level workflow	(calls helpers)
NL Mapping	User/AI intent → workflow	parse_intent
Archive/Log	Observability, rollback, debugging	log_event, archive_scan
7. Where You Are Now
You have robust, fast scanning and clickmap generation for app windows (Mail as POC).
You can generate and use flat, minimal clickmaps for automation.
You have the architecture and code patterns to extend this to any app.
You're ready to start writing and using helpers for Mail (and then other apps).
You have a modular, extensible, and observable framework.
8. Moving Forward
Finalize and document the clickmap/config schema.
Centralize and automate scanning/config generation.
Write and document helpers for Mail.
Refactor execution trees to use only helpers for tasks.
Build the NL → workflow mapping layer.
Expand to other apps.
Plug in AI for planning, error recovery, and user interaction.
Archive and log everything.
9. Final Thought
You are building a universal, modular, AI-driven Mac automation platform.
The architecture is robust, extensible, and ready for AI.
Helpers are the bridge between user/AI intent and the UI—make them powerful, generic, and easy to extend.
Let's keep going, Om-E!
If you want code templates, schema examples, or a roadmap for the next steps, just say the word!
