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
    while True:
        try:
            # 🔄 Refresh the in-memory execution tree from file
            tree = load_tree(refresh=True)

            # 🔧 Inject default input_args into all actions
            inject_input_args(tree)

            # 🎯 The entire tree IS the goal, since goal is root
            goal = tree

            # ⚙️ Run one tick of the goal execution engine (executes one action)
            result = run_goal(goal)

            # 💾 Save updated tree state (statuses, timestamps, etc.)
            write_full_tree(tree)

            # 🧾 Log the outcome
            log_event("INFO", "runner", f"Goal execution status: {result['status']}")

            # 🖨️ Show current progress path
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

            # ✅ Goal fully executed — exit loop
            if result["status"] == "complete":
                print("🎉 Goal completed.")
                break

            # ❌ Execution error or failure in task/action — halt here
            elif result["status"] in ("error", "failed"):
                print("❌ Execution failed or halted. Preparing for AI recovery...")
                break

            # ⏸️ Small delay before next execution pass
            #time.sleep(1)

        except Exception as e:
            # 🔥 Unhandled error — log and abort
            import traceback
            traceback.print_exc() # Print the full traceback
            log_event("ERROR", "runner", "Fatal error during execution", {"error": traceback.format_exc()})
            print(f"❌ Fatal error: {e}")
            break

if __name__ == "__main__":
    main()
