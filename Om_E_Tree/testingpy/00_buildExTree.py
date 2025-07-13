from datetime import datetime, timezone
from pathlib import Path
import json

from ome.utils.builder.input_args_builder import inject_input_args
from ome.tree.sync import write_full_tree
from ome.utils.builder.appList_builder import load_app_list

execution_tree = {
  "goal_id": "goal_001",
  "description": "Goal to simulate hotkey actions.",
  "status": "in_progress",
  "created_at": "2025-05-31T07:07:00Z",
  "objectives": [
    {
      "objective_id": "objective_001",
      "goal_id": "goal_001",
      "description": "Simulate keyboard hotkey action.",
      "status": "in_progress",
      "created_at": "2025-05-31T07:07:01Z",
      "tasks": [
        {
          "task_id": "task_001",
          "objective_id": "objective_001",
          "description": "Press hotkey: Ctrl + C",
          "status": "in_progress",
          "created_at": "2025-05-31T07:07:02Z",
          "actions": [
            {
              "name": "hotkey",
              "source": "keyboard",
              "input_args": {
                "keys": ["ctrl", "l"]
              },
              "status": "not_started",
              "attempts": 0
            }
          ]
        }
      ]
    }
  ]
}






inject_input_args(execution_tree)
write_full_tree(execution_tree)
print("✅ Input args injected and tree saved.")
