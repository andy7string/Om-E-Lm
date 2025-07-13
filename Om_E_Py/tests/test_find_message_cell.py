import json
import sys
import os

def walk_find_message_by_subject(node, subject, path=None):
    if path is None:
        path = []
    # If this is a cell, check its children for the subject
    if node.get('role') == 'cell':
        for child in node.get('children', []):
            if child.get('role') == 'text' and child.get('AXValue') == subject:
                return path + [node.get('name') or node.get('role') or 'cell'], node
    # Otherwise, walk children
    for idx, child in enumerate(node.get('children', [])):
        child_path = path + [child.get('name') or child.get('role') or f'Child_{idx}']
        result = walk_find_message_by_subject(child, subject, child_path)
        if result:
            return result
    return None

def main():
    json_path = "ome/data/windows/mail_window_sample.json"  # Replace with your JSON file path
    subject = "The Surfer starring Nicolas Cage"  # The subject to search for
    if not os.path.exists(json_path):
        print(f"JSON file not found: {json_path}")
        sys.exit(1)
    with open(json_path) as f:
        window_json = json.load(f)
    result = walk_find_message_by_subject(window_json, subject)
    if result:
        found_path, cell = result
        print(f"Found message cell with subject '{subject}':")
        print(f"Path: {found_path}")
        print(f"Cell contents: {json.dumps(cell, indent=2)}")
    else:
        print(f"Message with subject '{subject}' not found.")

if __name__ == '__main__':
    main() 