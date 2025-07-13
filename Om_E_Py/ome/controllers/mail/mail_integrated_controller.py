#!/usr/bin/env python3
"""
ome/controllers/mail/mail_integrated_controller.py

Integrated Mail Controller that maps PyXA actions to Om-E UI actions

This controller ensures that every PyXA operation is accompanied by the corresponding
UI interaction via Om-E, creating a complete automation experience.

For account and mailbox operations, this controller focuses on the MainWindow context
and handles the ever-changing environment by refreshing state after actions.
"""

import os
import sys
import time

# Add the project root to the Python path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from ome.controllers.mail import MailController
from ome.controllers.mail.mail_nav_controller import MailNavController

class MailIntegratedController:
    """
    Integrated Mail Controller that maps PyXA actions to Om-E UI actions.
    
    Every PyXA operation is paired with its corresponding UI interaction:
    - PyXA: Handles the logical operations (account switching, mailbox selection)
    - Om-E: Handles the UI interactions (clicking sidebar elements, menu navigation)
    
    For account and mailbox operations, focuses on MainWindow context.
    """
    
    def __init__(self):
        self.mail_controller = MailController()  # PyXA-based
        self.nav_controller = MailNavController()  # Om-E-based
        self.current_account = None
        self.current_mailbox = None
    
    def _ensure_main_window_context(self):
        """
        Ensure we're in the MainWindow context for account/mailbox operations.
        Returns True if we're in the right context, False otherwise.
        """
        try:
            # Refresh navBigDaDDy to get current window state
            self.nav_controller.refresh_nav()
            
            # Check if we're in MainWindow
            context = self.nav_controller.get_current_context()
            window_ref = context.get('window_ref')
            
            if window_ref == 'MainWindow':
                print(f"[MailIntegratedController] ✓ In MainWindow context")
                return True
            else:
                print(f"[MailIntegratedController] ⚠️ Not in MainWindow context (current: {window_ref})")
                return False
        except Exception as e:
            print(f"[MailIntegratedController] Error checking window context: {e}")
            return False
    
    def _refresh_after_action(self):
        """
        Refresh state after an action to handle the ever-changing environment.
        """
        try:
            print("[MailIntegratedController] Refreshing state after action...")
            self.nav_controller.refresh_nav()
            time.sleep(0.5)  # Give time for UI to settle
        except Exception as e:
            print(f"[MailIntegratedController] Error refreshing state: {e}")
    
    def switch_account(self, account_name):
        """
        Switch to account using PyXA + Om-E integration.
        
        PyXA Action: Switch account logically
        Om-E Action: Click account in sidebar or use menu navigation
        
        Focuses on MainWindow context for account operations.
        """
        print(f"[MailIntegratedController] Switching to account: {account_name}")
        
        # Ensure we're in MainWindow context for account operations
        if not self._ensure_main_window_context():
            print(f"[MailIntegratedController] Cannot switch account - not in MainWindow context")
            return False
        
        # Step 1: PyXA does the heavy lifting
        pyxa_success = self.mail_controller.switch_account(account_name)
        if not pyxa_success:
            print(f"[MailIntegratedController] PyXA failed to switch to account: {account_name}")
            return False
        
        self.current_account = account_name
        print(f"[MailIntegratedController] PyXA successfully switched to account: {account_name}")
        
        # Step 2: Om-E helps with UI interaction
        # Try sidebar clicking first
        ome_success = self.nav_controller.navigate_to_mailbox_via_sidebar(account_name)
        if ome_success:
            print(f"[MailIntegratedController] Om-E successfully clicked account in sidebar: {account_name}")
        else:
            # Fallback to menu navigation
            ome_success = self.nav_controller.switch_to_account(account_name)
            if ome_success:
                print(f"[MailIntegratedController] Om-E successfully switched account via menu: {account_name}")
            else:
                print(f"[MailIntegratedController] Om-E failed to interact with account UI: {account_name}")
        
        # Refresh state after action
        self._refresh_after_action()
        
        return pyxa_success and ome_success
    
    def switch_mailbox(self, mailbox_name, account_name=None):
        """
        Switch to mailbox using PyXA + Om-E integration.
        
        PyXA Action: Switch mailbox logically
        Om-E Action: Click mailbox in sidebar
        
        Focuses on MainWindow context for mailbox operations.
        """
        print(f"[MailIntegratedController] Switching to mailbox: {mailbox_name}")
        
        # Ensure we're in MainWindow context for mailbox operations
        if not self._ensure_main_window_context():
            print(f"[MailIntegratedController] Cannot switch mailbox - not in MainWindow context")
            return False
        
        # Step 1: PyXA does the heavy lifting
        if account_name:
            self.switch_account(account_name)
        
        pyxa_success = self.mail_controller.switch_mailbox(mailbox_name)
        if not pyxa_success:
            print(f"[MailIntegratedController] PyXA failed to switch to mailbox: {mailbox_name}")
            return False
        
        self.current_mailbox = mailbox_name
        print(f"[MailIntegratedController] PyXA successfully switched to mailbox: {mailbox_name}")
        
        # Step 2: Om-E helps with UI interaction
        ome_success = self.nav_controller.navigate_to_mailbox_via_sidebar(mailbox_name)
        if ome_success:
            print(f"[MailIntegratedController] Om-E successfully clicked mailbox in sidebar: {mailbox_name}")
        else:
            print(f"[MailIntegratedController] Om-E failed to click mailbox in sidebar: {mailbox_name}")
        
        # Refresh state after action
        self._refresh_after_action()
        
        return pyxa_success and ome_success
    
    def navigate_to_account_inbox(self, account_name):
        """
        Navigate to account's inbox using PyXA + Om-E integration.
        
        PyXA Action: Switch to account and select inbox
        Om-E Action: Navigate through sidebar: All Inboxes -> Account -> Inbox
        
        Focuses on MainWindow context for inbox navigation.
        """
        print(f"[MailIntegratedController] Navigating to {account_name} inbox")
        
        # Ensure we're in MainWindow context for inbox navigation
        if not self._ensure_main_window_context():
            print(f"[MailIntegratedController] Cannot navigate to inbox - not in MainWindow context")
            return False
        
        # Step 1: PyXA does the heavy lifting
        pyxa_success = self.mail_controller.switch_account(account_name)
        if pyxa_success:
            pyxa_success = self.mail_controller.switch_mailbox("Inbox")
        
        if not pyxa_success:
            print(f"[MailIntegratedController] PyXA failed to navigate to {account_name} inbox")
            return False
        
        self.current_account = account_name
        self.current_mailbox = "Inbox"
        print(f"[MailIntegratedController] PyXA successfully navigated to {account_name} inbox")
        
        # Step 2: Om-E helps with UI interaction
        ome_success = self.nav_controller.navigate_to_account_inbox(account_name)
        if ome_success:
            print(f"[MailIntegratedController] Om-E successfully navigated UI to {account_name} inbox")
        else:
            print(f"[MailIntegratedController] Om-E failed to navigate UI to {account_name} inbox")
        
        # Refresh state after action
        self._refresh_after_action()
        
        return pyxa_success and ome_success
    
    def get_accounts(self):
        """
        Get accounts using PyXA + Om-E integration.
        
        PyXA Action: Get account list from Mail app
        Om-E Action: Get account list from menu data
        """
        # PyXA gets the real account data
        pyxa_accounts = self.mail_controller.get_account_names()
        
        # Om-E gets the UI-discoverable accounts
        ome_accounts = self.nav_controller.get_available_accounts()
        
        print(f"[MailIntegratedController] PyXA accounts: {pyxa_accounts}")
        print(f"[MailIntegratedController] Om-E accounts: {ome_accounts}")
        
        # Return the intersection (accounts that both can see)
        common_accounts = list(set(pyxa_accounts) & set(ome_accounts))
        print(f"[MailIntegratedController] Common accounts: {common_accounts}")
        
        return common_accounts
    
    def get_mailboxes(self, account_name=None):
        """
        Get mailboxes using PyXA + Om-E integration.
        
        PyXA Action: Get mailbox list from Mail app
        Om-E Action: Get mailbox list from navigation data
        """
        # PyXA gets the real mailbox data
        pyxa_mailboxes = self.mail_controller.get_mailbox_names(account_name)
        
        # Om-E gets the UI-discoverable mailboxes
        ome_mailboxes = self.nav_controller.get_available_mailboxes()
        
        print(f"[MailIntegratedController] PyXA mailboxes for {account_name}: {pyxa_mailboxes}")
        print(f"[MailIntegratedController] Om-E mailboxes: {len(ome_mailboxes)} total")
        
        # Return PyXA mailboxes (more accurate) but note Om-E availability
        return pyxa_mailboxes
    
    def get_current_context(self):
        """
        Get current context from both PyXA and Om-E.
        """
        pyxa_context = self.mail_controller.get_current_context()
        ome_context = self.nav_controller.get_current_context()
        
        integrated_context = {
            'pyxa': pyxa_context,
            'ome': ome_context,
            'current_account': self.current_account,
            'current_mailbox': self.current_mailbox,
            'integration_status': 'active',
            'main_window_context': ome_context.get('window_ref') == 'MainWindow'
        }
        
        return integrated_context
    
    def refresh(self):
        """
        Refresh both PyXA and Om-E controllers.
        """
        print("[MailIntegratedController] Refreshing both controllers...")
        
        # Refresh PyXA
        self.mail_controller.refresh_app()
        
        # Refresh Om-E
        self.nav_controller.refresh_nav()
        
        print("[MailIntegratedController] Both controllers refreshed")
    
    def quit(self):
        """
        Quit Mail app using PyXA.
        """
        print("[MailIntegratedController] Quitting Mail app...")
        return self.mail_controller.quit_app()

def main():
    """Test the integrated controller."""
    print("=== Testing Mail Integrated Controller ===")
    
    controller = MailIntegratedController()
    
    # Get accounts
    print("\n1. Getting accounts:")
    accounts = controller.get_accounts()
    print(f"Available accounts: {accounts}")
    
    # Check current context
    print(f"\n2. Current context:")
    context = controller.get_current_context()
    print(f"MainWindow context: {context['main_window_context']}")
    print(f"Window ref: {context['ome']['window_ref']}")
    
    # Switch to andy7string@gmail.com
    if "andy7string@gmail.com" in accounts:
        print(f"\n3. Switching to andy7string@gmail.com:")
        success = controller.switch_account("andy7string@gmail.com")
        print(f"Result: {'✓ Success' if success else '✗ Failed'}")
        
        # Navigate to inbox
        print(f"\n4. Navigating to inbox:")
        success = controller.navigate_to_account_inbox("andy7string@gmail.com")
        print(f"Result: {'✓ Success' if success else '✗ Failed'}")
        
        # Get updated context
        print(f"\n5. Updated context:")
        updated_context = controller.get_current_context()
        print(f"PyXA account: {updated_context['pyxa']['current_account']}")
        print(f"Om-E window: {updated_context['ome']['window_ref']}")
        print(f"MainWindow context: {updated_context['main_window_context']}")
    
    print("\n=== Test Complete ===")

if __name__ == "__main__":
    main() 