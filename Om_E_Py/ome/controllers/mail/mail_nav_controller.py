#!/usr/bin/env python3
"""
ome/controllers/mail/mail_nav_controller.py

Mail Navigation Controller using navBigDaDDy

This controller uses navBigDaDDy to navigate through Mail accounts and mailboxes
using both menu navigation and direct element clicking from appNav data.

Key Features:
- Account switching via menu navigation
- Mailbox navigation via direct element clicking using appNav data
- Integration with navBigDaDDy for robust navigation
- Uses the same app focus pattern as other controllers
"""

import os
import sys
import json
import time

# Add the project root to the Python path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from ome.utils.uiNav.navBigDaDDy import navBigDaDDy
from ome.utils.builder.app.app_focus import ensure_app_focus

class MailNavController:
    """
    Mail Navigation Controller using navBigDaDDy for navigation.
    """
    
    def __init__(self):
        self.bundle_id = "com.apple.mail"
        self.nav = None
        self._init_nav()
    
    def _init_nav(self):
        """Initialize navBigDaDDy for Mail app."""
        try:
            self.nav = navBigDaDDy(self.bundle_id)
            print(f"[MailNavController] Initialized navBigDaDDy for {self.bundle_id}")
        except Exception as e:
            print(f"[MailNavController] Error initializing navBigDaDDy: {e}")
            self.nav = None
    
    def _ensure_app_focus(self):
        """Ensure Mail app is focused before navigation."""
        try:
            focus_result = ensure_app_focus(self.bundle_id)
            if focus_result.get('status') != 'success':
                print(f"[MailNavController] Could not focus Mail app: {focus_result.get('error')}")
                return False
            return True
        except Exception as e:
            print(f"[MailNavController] Error focusing app: {e}")
            return False
    
    def refresh_nav(self):
        """Refresh the navigation state."""
        if self.nav:
            self.nav.refresh()
            print("[MailNavController] Refreshed navigation state")
    
    def get_available_accounts(self):
        """
        Get available accounts from menu structure.
        Returns list of account names found in menu items.
        """
        if not self.nav:
            return []
        
        accounts = set()
        
        # Look for account names in menu items
        for menu_item in self.nav.menu_entries:
            title = menu_item.get('title', '')
            menu_path = menu_item.get('menu_path', [])
            
            # Check for account-related menu paths
            if any('Online Status' in path for path in menu_path):
                # Extract account name from menu items like "Take "account@email.com" Offline"
                if '"' in title:
                    account_name = title.split('"')[1] if len(title.split('"')) > 1 else title
                    accounts.add(account_name)
            
            # Also check for account names in other menu paths
            if any('Get New Mail' in path for path in menu_path) or any('Synchronise' in path for path in menu_path):
                if title and not title.startswith('Take') and not title.startswith('Get') and not title.startswith('Synchronise'):
                    accounts.add(title)
        
        return sorted(list(accounts))
    
    def get_available_mailboxes(self):
        """
        Get available mailboxes from navigation elements.
        Returns list of mailbox names found in appNav data.
        """
        if not self.nav:
            return []
        
        mailboxes = set()
        
        # Look for mailbox names in navigation elements
        for nav_element in self.nav.window_nav_entries:
            title = nav_element.get('AXTitle', '')
            role = nav_element.get('AXRole', '')
            
            # Focus on AXRow elements which are the sidebar navigation items
            if role == 'AXRow' and title:
                mailboxes.add(title)
        
        return sorted(list(mailboxes))
    
    def switch_to_account(self, account_name):
        """
        Switch to a specific account using menu navigation.
        Uses menu paths like ["Mailbox", "Get New Mail", account_name]
        """
        if not self.nav:
            print("[MailNavController] Navigation not initialized")
            return False
        
        if not self._ensure_app_focus():
            return False
        
        # Try different menu paths to switch accounts
        menu_paths_to_try = [
            ["Mailbox", "Get New Mail", account_name],
            ["Mailbox", "Synchronise", account_name],
            ["Mailbox", "Online Status", f'Take "{account_name}" Offline']
        ]
        
        for menu_path in menu_paths_to_try:
            print(f"[MailNavController] Trying to switch to account '{account_name}' via menu path: {' > '.join(menu_path)}")
            
            if self.nav.navigate_menu_path(menu_path):
                print(f"[MailNavController] Successfully switched to account '{account_name}'")
                time.sleep(1)  # Give time for the switch to take effect
                return True
        
        print(f"[MailNavController] Failed to switch to account '{account_name}'")
        return False
    
    def navigate_to_mailbox_via_sidebar(self, mailbox_name):
        """
        Navigate to a specific mailbox by clicking on the sidebar element.
        Uses navBigDaDDy's click_element method with the mailbox title.
        """
        if not self.nav:
            print("[MailNavController] Navigation not initialized")
            return False
        
        if not self._ensure_app_focus():
            return False
        
        print(f"[MailNavController] Clicking on sidebar element: '{mailbox_name}'")
        
        # Use navBigDaDDy's click_element method
        if self.nav.click_element(mailbox_name):
            print(f"[MailNavController] Successfully clicked on '{mailbox_name}'")
            time.sleep(1)  # Give time for the navigation to take effect
            return True
        else:
            print(f"[MailNavController] Failed to click on '{mailbox_name}'")
            return False
    
    def navigate_to_mailbox(self, mailbox_name):
        """
        Navigate to a specific mailbox using both sidebar clicking and menu navigation.
        """
        # First try sidebar clicking (more direct)
        if self.navigate_to_mailbox_via_sidebar(mailbox_name):
            return True
        
        # Fallback to menu navigation
        if not self.nav:
            print("[MailNavController] Navigation not initialized")
            return False
        
        if not self._ensure_app_focus():
            return False
        
        # Try different menu paths to navigate to mailbox
        menu_paths_to_try = [
            ["Mailbox", "Go to Favourite Mailbox", mailbox_name],
            ["Message", "Move to", mailbox_name],
            ["Message", "Copy to", mailbox_name]
        ]
        
        for menu_path in menu_paths_to_try:
            print(f"[MailNavController] Trying to navigate to mailbox '{mailbox_name}' via menu path: {' > '.join(menu_path)}")
            
            if self.nav.navigate_menu_path(menu_path):
                print(f"[MailNavController] Successfully navigated to mailbox '{mailbox_name}'")
                time.sleep(1)  # Give time for the navigation to take effect
                return True
        
        print(f"[MailNavController] Failed to navigate to mailbox '{mailbox_name}'")
        return False
    
    def navigate_to_account_inbox(self, account_name):
        """
        Navigate to a specific account's inbox using sidebar clicking.
        Path: All Inboxes -> account_name -> Inbox
        """
        if not self.nav:
            print("[MailNavController] Navigation not initialized")
            return False
        
        if not self._ensure_app_focus():
            return False
        
        print(f"[MailNavController] Navigating to {account_name} inbox via sidebar...")
        
        # Step 1: Click on "All Inboxes"
        if not self.navigate_to_mailbox_via_sidebar("All Inboxes"):
            print(f"[MailNavController] Failed to click on 'All Inboxes'")
            return False
        
        time.sleep(1)
        
        # Step 2: Click on the account name
        if not self.navigate_to_mailbox_via_sidebar(account_name):
            print(f"[MailNavController] Failed to click on account '{account_name}'")
            return False
        
        time.sleep(1)
        
        # Step 3: Click on "Inbox"
        if not self.navigate_to_mailbox_via_sidebar("Inbox"):
            print(f"[MailNavController] Failed to click on 'Inbox'")
            return False
        
        print(f"[MailNavController] Successfully navigated to {account_name} inbox")
        return True
    
    def go_to_all_inboxes(self):
        """Navigate to All Inboxes."""
        return self.navigate_to_mailbox_via_sidebar("All Inboxes")
    
    def go_to_inbox(self):
        """Navigate to Inbox."""
        return self.navigate_to_mailbox_via_sidebar("Inbox")
    
    def go_to_sent(self):
        """Navigate to Sent."""
        return self.navigate_to_mailbox_via_sidebar("Sent")
    
    def go_to_drafts(self):
        """Navigate to Drafts."""
        return self.navigate_to_mailbox_via_sidebar("Drafts")
    
    def go_to_trash(self):
        """Navigate to Trash/Bin."""
        return self.navigate_to_mailbox_via_sidebar("Bin")
    
    def go_to_junk(self):
        """Navigate to Junk."""
        return self.navigate_to_mailbox_via_sidebar("Junk")
    
    def get_current_context(self):
        """
        Get current navigation context.
        Returns dict with current window state and available elements.
        """
        if not self.nav:
            return {}
        
        return {
            'active_target': self.nav.active_target,
            'window_ref': self.nav.active_target.get('window_ref'),
            'available_accounts': self.get_available_accounts(),
            'available_mailboxes': self.get_available_mailboxes(),
            'window_elements': len(self.nav.window_nav_entries),
            'menu_items': len(self.nav.menu_entries)
        }
    
    def list_navigation_elements(self, filter_text=None):
        """
        List all navigation elements, optionally filtered by text.
        Useful for debugging and discovering available sidebar elements.
        """
        if not self.nav:
            return []
        
        elements = []
        for nav_element in self.nav.window_nav_entries:
            title = nav_element.get('AXTitle', '')
            role = nav_element.get('AXRole', '')
            omeClick = nav_element.get('omeClick', [])
            
            if filter_text is None or filter_text.lower() in title.lower():
                elements.append({
                    'title': title,
                    'role': role,
                    'omeClick': omeClick
                })
        
        return elements
    
    def list_menu_items(self, filter_text=None):
        """
        List all menu items, optionally filtered by text.
        Useful for debugging and discovering available menu paths.
        """
        if not self.nav:
            return []
        
        items = []
        for menu_item in self.nav.menu_entries:
            title = menu_item.get('title', '')
            menu_path = menu_item.get('menu_path', [])
            
            if filter_text is None or filter_text.lower() in title.lower():
                items.append({
                    'title': title,
                    'menu_path': menu_path,
                    'path_string': ' > '.join(menu_path)
                })
        
        return items

def main():
    """Test function for MailNavController."""
    print("Testing MailNavController...")
    
    controller = MailNavController()
    
    # Get current context
    context = controller.get_current_context()
    print(f"Current context: {json.dumps(context, indent=2)}")
    
    # List available accounts and mailboxes
    accounts = controller.get_available_accounts()
    mailboxes = controller.get_available_mailboxes()
    
    print(f"\nAvailable accounts: {accounts}")
    print(f"Available mailboxes: {mailboxes}")
    
    # Test navigation to andy7string@gmail.com inbox
    if "andy7string@gmail.com" in accounts:
        print(f"\nTesting navigation to andy7string@gmail.com inbox...")
        success = controller.navigate_to_account_inbox("andy7string@gmail.com")
        print(f"Result: {'Success' if success else 'Failed'}")
    
    # Test navigation to common mailboxes
    print("\nTesting mailbox navigation...")
    
    test_mailboxes = ["All Inboxes", "Inbox", "Sent", "Drafts"]
    for mailbox in test_mailboxes:
        if mailbox in mailboxes:
            print(f"Navigating to {mailbox}...")
            success = controller.navigate_to_mailbox_via_sidebar(mailbox)
            print(f"Result: {'Success' if success else 'Failed'}")
            time.sleep(2)  # Wait between navigations

if __name__ == "__main__":
    main() 