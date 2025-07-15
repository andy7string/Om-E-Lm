"""
ome/controllers/comControl/comC_mailMessageListWatch.py

This script provides a command-line interface to create a command file that
instructs the mail message list watcher to perform specific actions, such as
selecting a row in Apple Mail's message list.

Module Path: ome.controllers.comControl.comC_mailMessageListWatch

Main Purpose:
- Creates a JSONL command file in a predefined directory.
- This file acts as a trigger for another process (the watcher) to perform an action.
- Supports specifying a row index and optional follow-up actions like sending the 'Enter' key or reading the message body.

Key Features:
- Command-Line Interface: Simple and direct way to issue commands to the mail watcher.
- Decoupled Communication: Uses a file-based trigger system, allowing different processes to communicate without direct coupling.
- Extensible: The command format is a simple JSON object, which can be easily extended with new actions or parameters.

How to Use (Command Line):
    # Select row 5 in the mail message list
    python -m Om_E_Py.ome.controllers.comControl.comC_mailMessageListWatch --row 5

    # Select row 3 and then simulate pressing the Enter key
    python -m Om_E_Py.ome.controllers.comControl.comC_mailMessageListWatch --row 3 --enter

    # Select row 2 and trigger a read of the message body
    python -m Om_E_Py.ome.controllers.comControl.comC_mailMessageListWatch --row 2 --readbody

File Structure:
    Om_E_Py/ome/data/comControl/
    └── mailMessageList_selector.jsonl  # The command file created by this script.

How It Works:
- The script parses command-line arguments (--row, --enter, --readbody).
- It constructs a JSON object representing the command.
- It writes this JSON object to the `mailMessageList_selector.jsonl` file, overwriting any previous command.
- A separate watcher process (like mailMessageListWatch_controller.py) monitors this file for changes and executes the command.

When to Use:
- To programmatically control the selection of messages in Apple Mail from a separate process or script.
- As part of a larger automation workflow where you need to trigger actions in the mail client.
- For testing UI interactions with the mail message list in a controlled way.
"""
import json
import os
import argparse

def write_mail_message_list_selection(row_index, send_keys_after_select=False, readbody=False):
    """
    Write a command to select a row in the mail message list.
    Args:
        row_index (int): The 1-based index of the row to select.
        send_keys_after_select (bool): Whether to send Enter key after selection.
        readbody (bool): Whether to extract the mail body after selection.
    """
    command = {
        "row_index": row_index,
        "send_keys_after_select": send_keys_after_select,
        "executed": False,
        "readbody": readbody
    }
    out_path = os.path.join("Om_E_Py/ome/data/comControl", "mailMessageList_selector.jsonl")
    with open(out_path, "w") as f:
        f.write(json.dumps(command) + "\n")
    print(f"Wrote mail message list selection command: {command} to {out_path}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Write a mail message list selection command.")
    parser.add_argument("--row", type=int, required=True, help="Row index (1-based) to select.")
    parser.add_argument("--enter", action="store_true", help="Send Enter key after selecting the row.")
    parser.add_argument("--readbody", action="store_true", help="Extract mail body after selecting the row.")
    args = parser.parse_args()
    write_mail_message_list_selection(args.row, send_keys_after_select=args.enter, readbody=args.readbody) 