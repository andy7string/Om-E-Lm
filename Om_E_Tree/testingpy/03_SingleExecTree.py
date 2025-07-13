from ome.tree.memory import load_tree
from ome.tree.execute.goal_runner import run_goal
from ome.tree.sync import write_full_tree
from ome.utils.logger import log_event

def main():
    try:
        tree = load_tree(refresh=True)               # 🔄 Load latest in-memory tree
        goal = tree                                  # 📌 Grab the current goal

        result = run_goal(goal)                      # 🚀 Run the goal-level executor

        write_full_tree(tree)                        # 💾 Persist the updated tree

        log_event("INFO", "runner", f"Goal execution status: {result['status']}")

        if result["status"] == "complete":
            print("🎉 Goal completed.")
        else:
            print("✅ Progress made. Rerun runner.py to continue.")

    except Exception as e:
        log_event("ERROR", "runner", "Fatal error during execution", {"error": str(e)})
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()
