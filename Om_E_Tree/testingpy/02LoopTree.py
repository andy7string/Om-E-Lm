# To run from the project root:
# python Om_E_Tree/testingpy/02LoopTree.py

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from Om_E_Tree.ome.tree.memory import load_tree                 # 🧠 Load the in-memory execution tree
from Om_E_Tree.ome.tree.execute.goal_runner import run_goal     # 🚀 Core goal execution function
from Om_E_Tree.ome.tree.sync import write_full_tree             # 💾 Persist changes to disk
from Om_E_Tree.ome.utils.logger import log_event                # 📝 Log events to structured logger
from Om_E_Tree.ome.utils.builder.input_args_builder import inject_input_args  # 🧠 Auto-fill missing input_args
import time                                           # ⏱️ For pacing the loop

def main():
    """
    Main execution loop for the Om-E agent.
    This script continuously processes an execution tree, running one action at a time
    until the goal is completed or an error occurs.
    """
    while True:
        try:
            # 1. Load the latest execution tree from disk. `refresh=True` ensures we get the latest state.
            tree = load_tree(refresh=True)

            # 2. Automatically fill in any missing `input_args` with default values defined in the action schemas.
            inject_input_args(tree)

            # 3. The root of the loaded tree is considered the main goal to be executed.
            goal = tree

            # 4. Execute the next pending action in the tree. The engine handles finding the correct action.
            result = run_goal(goal)

            # 5. Persist the updated tree state (e.g., action statuses, timestamps) back to the JSON file.
            write_full_tree(tree)

            # 6. Log the outcome of the current execution tick for monitoring and debugging.
            log_event("INFO", "runner", f"Goal execution status: {result['status']}")

            # 7. Display the current position in the execution tree for real-time feedback.
            current_obj = next((o for o in goal["objectives"] if o["status"] in ["pending", "in_progress"]), None)
            if current_obj:
                current_task = next((t for t in current_obj["tasks"] if t["status"] in ["pending", "in_progress"]), None)
                if current_task:
                    current_action = next((a for a in current_task["actions"] if a["status"] in ["pending", "in_progress"]), None)
                    if current_action:
                        print(f"🔁 Now running: {current_obj['objective_id']} > {current_task['task_id']} > {current_action['name']}")
                    else:
                        print(f"🔁 Now running: {current_obj['objective_id']} > {current_task['task_id']} > (no active action)")
                else:
                    print(f"🔁 Now running: {current_obj['objective_id']} > (no active task)")
            else:
                print(f"🔁 Status: {result['status']}")

            # 8. Check for terminal states to decide whether to continue the loop.
            if result["status"] == "complete":
                print("🎉 Goal completed.")
                break

            # If an action or task fails, the loop halts, allowing for potential AI-driven recovery.
            elif result["status"] in ("error", "failed"):
                print("❌ Execution failed or halted. Preparing for AI recovery...")
                break

            # Optional: A small delay to prevent high CPU usage in the loop.
            #time.sleep(1)

        except Exception as e:
            # Catch any unexpected errors during the loop, log them, and terminate gracefully.
            import traceback
            traceback.print_exc() # Print the full traceback
            log_event("ERROR", "runner", "Fatal error during execution", {"error": traceback.format_exc()})
            print(f"❌ Fatal error: {e}")
            break

if __name__ == "__main__":
    main()
