import json
import os
import argparse
from ome.utils.env.env import COM_CONTROL_DIR

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
    out_path = os.path.join(COM_CONTROL_DIR, "mailMessageList_selector.jsonl")
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