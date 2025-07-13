#!/usr/bin/env python3
"""
tests/test_mail_nav_controller.py

Test script for MailNavController using navBigDaDDy

This script demonstrates how to use the Mail navigation controller
to navigate through accounts and mailboxes using menu paths.
"""

import os
import sys
import json
import time

# Add the project root to the Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from ome.controllers.mail.mail_nav_controller import MailNavController

def test_mail_navigation():
    """Test the Mail navigation controller."""
    print("=== Testing Mail Navigation Controller ===")
    
    # Initialize the controller
    controller = MailNavController()
    
    # Get current context
    print("\n1. Getting current context...")
    context = controller.get_current_context()
    print(f"Current context: {json.dumps(context, indent=2)}")
    
    # List available accounts and mailboxes
    print("\n2. Discovering available accounts and mailboxes...")
    accounts = controller.get_available_accounts()
    mailboxes = controller.get_available_mailboxes()
    
    print(f"Available accounts: {accounts}")
    print(f"Available mailboxes: {mailboxes}")
    
    # Show some menu items for debugging
    print("\n3. Sample menu items (filtered by 'Mailbox'):")
    menu_items = controller.list_menu_items("Mailbox")
    for item in menu_items[:5]:  # Show first 5
        print(f"  - {item['title']} -> {item['path_string']}")
    
    # Test account switching
    if accounts:
        print(f"\n4. Testing account switching...")
        for account in accounts:
            print(f"Switching to account: {account}")
            success = controller.switch_to_account(account)
            print(f"  Result: {'✓ Success' if success else '✗ Failed'}")
            time.sleep(2)  # Wait between switches
    
    # Test mailbox navigation
    print(f"\n5. Testing mailbox navigation...")
    common_mailboxes = ["All Inboxes", "Inbox", "Sent", "Drafts", "Bin", "Junk"]
    
    for mailbox in common_mailboxes:
        if mailbox in mailboxes:
            print(f"Navigating to {mailbox}...")
            success = controller.navigate_to_mailbox(mailbox)
            print(f"  Result: {'✓ Success' if success else '✗ Failed'}")
            time.sleep(2)  # Wait between navigations
    
    # Test specific mailbox methods
    print(f"\n6. Testing specific mailbox methods...")
    
    methods_to_test = [
        ("All Inboxes", controller.go_to_all_inboxes),
        ("Inbox", controller.go_to_inbox),
        ("Sent", controller.go_to_sent),
        ("Drafts", controller.go_to_drafts),
        ("Trash", controller.go_to_trash),
        ("Junk", controller.go_to_junk)
    ]
    
    for mailbox_name, method in methods_to_test:
        print(f"Testing {mailbox_name}...")
        success = method()
        print(f"  Result: {'✓ Success' if success else '✗ Failed'}")
        time.sleep(1)
    
    print("\n=== Test Complete ===")

def test_menu_exploration():
    """Explore the menu structure to understand available navigation options."""
    print("\n=== Menu Structure Exploration ===")
    
    controller = MailNavController()
    
    # Show all menu items related to accounts
    print("\nAccount-related menu items:")
    account_items = controller.list_menu_items("account")
    for item in account_items:
        print(f"  - {item['title']} -> {item['path_string']}")
    
    # Show all menu items related to mailboxes
    print("\nMailbox-related menu items:")
    mailbox_items = controller.list_menu_items("mailbox")
    for item in mailbox_items:
        print(f"  - {item['title']} -> {item['path_string']}")
    
    # Show menu items with "Go to" in the path
    print("\n'Go to' menu items:")
    goto_items = controller.list_menu_items("Go to")
    for item in goto_items:
        print(f"  - {item['title']} -> {item['path_string']}")
    
    # Show menu items with "Move to" in the path
    print("\n'Move to' menu items:")
    move_items = controller.list_menu_items("Move to")
    for item in move_items:
        print(f"  - {item['title']} -> {item['path_string']}")

def main():
    """Main test function."""
    print("Mail Navigation Controller Test")
    print("=" * 50)
    
    try:
        # Test basic navigation
        test_mail_navigation()
        
        # Explore menu structure
        test_menu_exploration()
        
    except Exception as e:
        print(f"Error during testing: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main() 