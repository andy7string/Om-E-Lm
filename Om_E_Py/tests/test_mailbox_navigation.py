#!/usr/bin/env python3
"""
test_mailbox_navigation.py

Test script to verify mailbox navigation functionality in MailController.
Tests both PyXA mailbox switching and the new omeClick navigation integration.

Usage:
    python tests/test_mailbox_navigation.py
"""

import os
import sys

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from ome.controllers.mail.mail_controller import MailController
import json

def test_mailbox_navigation():
    """Test mailbox navigation functionality."""
    print("=== Testing Mailbox Navigation ===")
    
    # Initialize controller
    controller = MailController()
    
    if not controller.app:
        print("❌ Failed to initialize Mail app")
        return False
    
    print("✅ Mail app initialized successfully")
    
    # Get accounts
    accounts = controller.get_account_names()
    print(f"📧 Available accounts: {accounts}")
    
    if not accounts:
        print("❌ No accounts found")
        return False
    
    # Test with first account
    test_account = accounts[0]
    print(f"\n🔍 Testing with account: {test_account}")
    
    # Get mailboxes for the account
    mailboxes = controller.get_mailbox_names(test_account)
    print(f"📁 Available mailboxes: {mailboxes}")
    
    if not mailboxes:
        print("❌ No mailboxes found")
        return False
    
    # Test mailbox navigation lookup (without clicking)
    print(f"\n🧭 Testing mailbox navigation lookup...")
    for mailbox in mailboxes[:3]:  # Test first 3 mailboxes
        nav_result = controller.handle_navigation_action({
            'action': 'switch_mailbox',
            'account_name': test_account,
            'mailbox_name': mailbox,
            'execute_click': False
        })
        
        if nav_result.get('status') == 'success':
            omeClick = nav_result.get('omeClick')
            nav_mailbox_name = nav_result.get('nav_mailbox_name')
            print(f"✅ Found navigation for '{mailbox}' (mapped to '{nav_mailbox_name}') at {omeClick}")
        else:
            print(f"❌ No navigation found for '{mailbox}': {nav_result.get('message')}")
    
    # Test mailbox switching with omeClick
    print(f"\n🖱️ Testing mailbox switching with omeClick...")
    test_mailbox = mailboxes[0]  # Use first mailbox
    
    print(f"Switching to mailbox: {test_mailbox}")
    success = controller.switch_mailbox(test_mailbox, test_account, use_omeclick=True)
    
    if success:
        print(f"✅ Successfully switched to mailbox: {test_mailbox}")
        
        # Check current context
        context = controller.get_current_context()
        print(f"📊 Current context: {context}")
    else:
        print(f"❌ Failed to switch to mailbox: {test_mailbox}")
    
    # Test mailbox switching without omeClick
    print(f"\n🔄 Testing mailbox switching without omeClick...")
    if len(mailboxes) > 1:
        test_mailbox2 = mailboxes[1]
        print(f"Switching to mailbox: {test_mailbox2}")
        success = controller.switch_mailbox(test_mailbox2, test_account, use_omeclick=False)
        
        if success:
            print(f"✅ Successfully switched to mailbox: {test_mailbox2}")
        else:
            print(f"❌ Failed to switch to mailbox: {test_mailbox2}")
    
    return True

def test_navigation_data_integrity():
    """Test the integrity of navigation data."""
    print("\n=== Testing Navigation Data Integrity ===")
    
    controller = MailController()
    
    # Get hierarchical navigation data
    nav_items = controller.get_hierarchical_nav()
    print(f"📋 Found {len(nav_items)} navigation items")
    
    # Analyze mailbox paths
    mailbox_paths = []
    for item in nav_items:
        path = item.get('path', [])
        if len(path) >= 3 and path[0] == 'accounts':
            account_name = path[1]
            mailbox_name = path[2]
            mailbox_paths.append({
                'account': account_name,
                'mailbox': mailbox_name,
                'omeClick': item.get('omeClick'),
                'title': item.get('title')
            })
    
    print(f"📁 Found {len(mailbox_paths)} mailbox navigation entries:")
    for path in mailbox_paths[:5]:  # Show first 5
        print(f"  - {path['account']} > {path['mailbox']} at {path['omeClick']}")
    
    if len(mailbox_paths) > 5:
        print(f"  ... and {len(mailbox_paths) - 5} more")
    
    return len(mailbox_paths) > 0

def test_mailbox_name_mapping():
    """Test mailbox name mapping functionality."""
    print("\n=== Testing Mailbox Name Mapping ===")
    
    controller = MailController()
    
    # Test mapping
    test_cases = [
        ('INBOX', 'Inbox'),
        ('Sent Mail', 'Sent'),
        ('Spam', 'Junk'),
        ('Trash', 'Bin'),
        ('Inbox', 'Inbox'),
        ('Drafts', 'Drafts'),
        ('Unknown Mailbox', 'Unknown Mailbox')  # Should return unchanged
    ]
    
    for pyxa_name, expected_nav_name in test_cases:
        mapped_name = controller._map_mailbox_name(pyxa_name)
        if mapped_name == expected_nav_name:
            print(f"✅ '{pyxa_name}' -> '{mapped_name}'")
        else:
            print(f"❌ '{pyxa_name}' -> '{mapped_name}' (expected '{expected_nav_name}')")

def main():
    """Run all tests."""
    print("🚀 Starting Mailbox Navigation Tests\n")
    
    try:
        # Test mailbox name mapping
        test_mailbox_name_mapping()
        
        # Test navigation data integrity
        nav_data_ok = test_navigation_data_integrity()
        
        if nav_data_ok:
            # Test actual navigation
            test_mailbox_navigation()
        else:
            print("❌ Navigation data integrity test failed - skipping navigation tests")
        
        print("\n✅ All tests completed!")
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 