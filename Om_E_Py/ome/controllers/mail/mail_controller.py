"""
ome/controllers/mail/mail_controller.py

This script provides a high-level controller for automating and managing the Apple Mail app on macOS.

Main Purpose:
- Automates account and mailbox management in the Mail app using accessibility and scripting bridges.
- Provides a command-line interface for testing and interacting with Mail accounts and mailboxes.
- Supports navigation lookups for UI automation (e.g., finding omeClick coordinates for sidebar navigation).

Key Features:
- App Focus Management: Ensures the Mail app is focused and ready for automation.
- Account & Mailbox Management: Lists, switches, and queries accounts and mailboxes.
- Navigation Data Lookup: Finds UI navigation points (omeClick) for accounts/mailboxes using hierarchical JSONL data.
- Command-Line Interface: Run tests and queries directly from the terminal for development and debugging.
- Error Handling: Gracefully handles missing app, accounts, or navigation data.

How to Use (Command Line):
    ¸
    python ome/controllers/mail/mail_controller.py --mailboxes Google
    python ome/controllers/mail/mail_controller.py --test-nav-action Google
    python ome/controllers/mail/mail_controller.py --all

Arguments:
    --accounts: List all available mail accounts
    --mailboxes <account>: List mailboxes for the specified account
    --test-nav: Test hierarchical navigation file reading/building
    --test-nav-action <account>: Test navigation lookup for an account
    --context: Show current account/mailbox context
    --all: Run all tests
    --no-front-nav: Disable front navigation (omeClick); use PyXA only (overrides .env setting)

Output:
- Prints results to the terminal (accounts, mailboxes, navigation lookups, etc.)
- Useful for debugging, development, and integration with other automation tools.

When to Use:
- To automate or test Mail app account/mailbox management.
- For UI automation or navigation using omeClick coordinates.
- For development, debugging, or integration with other Om-E-py modules.
"""

import os
import sys
import time

# Always add the project root to sys.path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

"""
Mail Controller

High-level controller for Mail app, account, and mailbox management.
Uses the same app focus pattern as mailMessageBody_controller.py.
"""

import PyXA
from ome.utils.builder.app.app_focus import ensure_app_focus
from ome.utils.uiNav.navBigDaDDy import navBigDaDDy
import json
import subprocess
from ome.utils.env.env import TRANSLATOR_EXPORT_DIR, USE_FRONT_NAV


class MailController:
    """
    High-level controller for Mail app automation.
    Manages app state, accounts, and mailboxes using the app focus bridge.
    """
    
    # Global bundle ID for Mail app
    BUNDLE_ID = "com.apple.mail"
    
    # Mailbox name mapping: PyXA names -> Navigation names
    MAILBOX_NAME_MAPPING = {
        # Case differences
        'INBOX': 'Inbox',
        
        # Name differences
        'Sent Mail': 'Sent',
        'Spam': 'Junk',
        'Trash': 'Bin',
        
        # Common variations
        'Inbox': 'Inbox',
        'Drafts': 'Drafts',
        'Sent': 'Sent',
        'Junk': 'Junk',
        'Bin': 'Bin',
        'Important': 'Important',
        'Archive': 'Archive',
    }
    
    def __init__(self):
        """
        Initialize the MailController and ensure the Mail app is focused and ready.
        """
        t0 = time.time()
        self.app = None
        self.current_account = None
        self.current_mailbox = None
        self.use_front_nav = USE_FRONT_NAV
        self._nav_cache = {'window_ref': None, 'nav_items': []}  # Cache for nav data
        self._initialize_app()
        t1 = time.time()
        print(f"[TIMER] MailController._initialize_app: {t1-t0:.3f}s")
        self.nav = navBigDaDDy(self.BUNDLE_ID, app=self.app)
        t2 = time.time()
        print(f"[TIMER] navBigDaDDy init: {t2-t1:.3f}s")
    
    def _initialize_app(self):
        """
        Initialize the Mail app using the same pattern as mailMessageBody_controller.py.
        Ensures the app is focused and ready for automation.
        """
        t0 = time.time()
        try:
            focus_result = ensure_app_focus(self.BUNDLE_ID, fullscreen=True)
            if focus_result.get('status') == 'success':
                app_ax = focus_result.get('app')
                self.app = PyXA.Application("Mail")
            else:
                self.app = None
        except Exception as e:
            self.app = None
        t1 = time.time()
        print(f"[TIMER] _initialize_app/ensure_app_focus: {t1-t0:.3f}s")
    
    def get_accounts(self):
        """
        Get all available mail accounts.
        
        Returns:
            list: List of account objects
        """
        if not self.app:
            return []
        
        try:
            accounts = self.app.accounts()
            print(f"[MailController] Found {len(accounts)} accounts")
            return accounts
        except Exception as e:
            print(f"[MailController] Error getting accounts: {e}")
            return []
    
    def get_account_names(self):
        """
        Get names of all available accounts.
        
        Returns:
            list: List of account names
        """
        accounts = self.get_accounts()
        return [account.name for account in accounts]
    
    def _map_mailbox_name(self, mailbox_name):
        """
        Map PyXA mailbox names to navigation names.
        
        Args:
            mailbox_name (str): PyXA mailbox name
            
        Returns:
            str: Navigation mailbox name (or original if no mapping found)
        """
        return self.MAILBOX_NAME_MAPPING.get(mailbox_name, mailbox_name)
    
    def handle_navigation_action(self, action_info):
        """
        Central function to handle navigation actions based on action type and context.
        
        Args:
            action_info (dict): Dictionary containing action details
                - action (str): Type of action (e.g., 'switch_account', 'switch_mailbox')
                - account_name (str): Account name for the action
                - mailbox_name (str, optional): Mailbox name for mailbox actions
                - execute_click (bool, optional): Whether to execute the click (default: False)
                
        Returns:
            dict: Result with status and any relevant data (e.g., omeClick coordinates)
        """
        import time
        t0 = time.time()
        action = action_info.get('action')
        account_name = action_info.get('account_name')
        mailbox_name = action_info.get('mailbox_name')
        execute_click = action_info.get('execute_click', False)
        t1 = time.time()
        print(f"[TIMER] handle_navigation_action: get_hierarchical_nav: {t1-t0:.3f}s")
        
        if action == 'switch_account' and account_name:
            nav_items = self.get_hierarchical_nav()
            t2 = time.time()
            print(f"[TIMER] handle_navigation_action: get_hierarchical_nav: {t2-t1:.3f}s")
            for item in nav_items:
                if (
                    item.get("path") == ["aggregate", "All Inboxes", account_name]
                    and "omeClick" in item
                ):
                    omeClick = item["omeClick"]
                    
                    # Execute click if requested
                    if execute_click and omeClick:
                        t3 = time.time()
                        click_success = self._execute_navigation_click(omeClick, f"account {account_name}")
                        t4 = time.time()
                        print(f"[TIMER] handle_navigation_action: _execute_navigation_click: {t4-t3:.3f}s")
                        return {
                            'status': 'success',
                            'action': action,
                            'account_name': account_name,
                            'omeClick': omeClick,
                            'title': item.get("title"),
                            'type': item.get("type"),
                            'click_executed': click_success
                        }
                    
                    return {
                        'status': 'success',
                        'action': action,
                        'account_name': account_name,
                        'omeClick': omeClick,
                        'title': item.get("title"),
                        'type': item.get("type")
                    }
            
            # If not found in All Inboxes, try direct account lookup
            for item in nav_items:
                if (
                    item.get("path") == ["accounts", account_name]
                    and "omeClick" in item
                ):
                    omeClick = item["omeClick"]
                    
                    # Execute click if requested
                    if execute_click and omeClick:
                        t3 = time.time()
                        click_success = self._execute_navigation_click(omeClick, f"account {account_name}")
                        t4 = time.time()
                        print(f"[TIMER] handle_navigation_action: _execute_navigation_click: {t4-t3:.3f}s")
                        return {
                            'status': 'success',
                            'action': action,
                            'account_name': account_name,
                            'omeClick': omeClick,
                            'title': item.get("title"),
                            'type': item.get("type"),
                            'click_executed': click_success
                        }
                    
                    return {
                        'status': 'success',
                        'action': action,
                        'account_name': account_name,
                        'omeClick': omeClick,
                        'title': item.get("title"),
                        'type': item.get("type")
                    }
            
            return {
                'status': 'not_found',
                'action': action,
                'account_name': account_name,
                'message': f'Account "{account_name}" not found in navigation data'
            }
        
        if action == 'switch_mailbox' and account_name and mailbox_name:
            # Map PyXA mailbox name to navigation name
            nav_mailbox_name = self._map_mailbox_name(mailbox_name)
            
            # Look up the mailbox under the account in the hierarchical nav
            nav_items = self.get_hierarchical_nav()
            t2 = time.time()
            print(f"[TIMER] handle_navigation_action: get_hierarchical_nav: {t2-t1:.3f}s")
            # 1. Try exact match
            for item in nav_items:
                if (
                    item.get("path") == ["accounts", account_name, nav_mailbox_name]
                    and "omeClick" in item
                ):
                    omeClick = item["omeClick"]
                    # Execute click if requested
                    if execute_click and omeClick:
                        t3 = time.time()
                        click_success = self._execute_navigation_click(omeClick, f"mailbox {mailbox_name} in account {account_name}")
                        t4 = time.time()
                        print(f"[TIMER] handle_navigation_action: _execute_navigation_click: {t4-t3:.3f}s")
                        return {
                            'status': 'success',
                            'action': action,
                            'account_name': account_name,
                            'mailbox_name': mailbox_name,
                            'nav_mailbox_name': nav_mailbox_name,
                            'omeClick': omeClick,
                            'title': item.get("title"),
                            'type': item.get("type"),
                            'click_executed': click_success
                        }
                    return {
                        'status': 'success',
                        'action': action,
                        'account_name': account_name,
                        'mailbox_name': mailbox_name,
                        'nav_mailbox_name': nav_mailbox_name,
                        'omeClick': omeClick,
                        'title': item.get("title"),
                        'type': item.get("type")
                    }
            # 2. Try case-insensitive match
            for item in nav_items:
                path = item.get("path")
                if (
                    path and len(path) == 3 and
                    path[0] == "accounts" and
                    path[1].lower() == account_name.lower() and
                    path[2].lower() == nav_mailbox_name.lower() and
                    "omeClick" in item
                ):
                    omeClick = item["omeClick"]
                    if execute_click and omeClick:
                        t3 = time.time()
                        click_success = self._execute_navigation_click(omeClick, f"mailbox {mailbox_name} in account {account_name}")
                        t4 = time.time()
                        print(f"[TIMER] handle_navigation_action: _execute_navigation_click: {t4-t3:.3f}s (case-insensitive)")
                        return {
                            'status': 'success',
                            'action': action,
                            'account_name': account_name,
                            'mailbox_name': mailbox_name,
                            'nav_mailbox_name': nav_mailbox_name,
                            'omeClick': omeClick,
                            'title': item.get("title"),
                            'type': item.get("type"),
                            'click_executed': click_success
                        }
                    return {
                        'status': 'success',
                        'action': action,
                        'account_name': account_name,
                        'mailbox_name': mailbox_name,
                        'nav_mailbox_name': nav_mailbox_name,
                        'omeClick': omeClick,
                        'title': item.get("title"),
                        'type': item.get("type")
                    }
            # 3. Try substring (fuzzy) match
            for item in nav_items:
                path = item.get("path")
                if (
                    path and len(path) == 3 and
                    path[0] == "accounts" and
                    path[1].lower() == account_name.lower() and
                    nav_mailbox_name.lower() in path[2].lower() and
                    "omeClick" in item
                ):
                    omeClick = item["omeClick"]
                    if execute_click and omeClick:
                        t3 = time.time()
                        click_success = self._execute_navigation_click(omeClick, f"mailbox {mailbox_name} in account {account_name}")
                        t4 = time.time()
                        print(f"[TIMER] handle_navigation_action: _execute_navigation_click: {t4-t3:.3f}s (fuzzy)")
                        return {
                            'status': 'success',
                            'action': action,
                            'account_name': account_name,
                            'mailbox_name': mailbox_name,
                            'nav_mailbox_name': nav_mailbox_name,
                            'omeClick': omeClick,
                            'title': item.get("title"),
                            'type': item.get("type"),
                            'click_executed': click_success
                        }
                    return {
                        'status': 'success',
                        'action': action,
                        'account_name': account_name,
                        'mailbox_name': mailbox_name,
                        'nav_mailbox_name': nav_mailbox_name,
                        'omeClick': omeClick,
                        'title': item.get("title"),
                        'type': item.get("type")
                    }
            return {
                'status': 'not_found',
                'action': action,
                'account_name': account_name,
                'mailbox_name': mailbox_name,
                'nav_mailbox_name': nav_mailbox_name,
                'message': f'Mailbox "{mailbox_name}" (mapped to "{nav_mailbox_name}") not found in account "{account_name}"'
            }
        
        return {
            'status': 'error',
            'action': action,
            'message': f'Unknown or invalid action: {action}'
        }
    
    def _execute_navigation_click(self, omeClick, description):
        """
        Execute a click at the given omeClick coordinates using navBigDaDDy.
        
        Args:
            omeClick (list): [x, y] coordinates to click
            description (str): Description for logging purposes
            
        Returns:
            bool: True if click was successful, False otherwise
        """
        import time
        try:
            x, y = omeClick
            print(f"[MailController] Executing navigation click for {description} at ({x}, {y})")
            t0 = time.time()
            success = self.nav.click_at_coordinates(x, y, description)
            t1 = time.time()
            print(f"[TIMER] _execute_navigation_click: click_at_coordinates: {t1-t0:.3f}s")
            if success:
                print(f"[MailController] Navigation click successful for {description}")
            else:
                print(f"[MailController] Navigation click failed for {description}")
            return success
        except Exception as e:
            print(f"[MailController] Error executing navigation click for {description}: {e}")
            return False
    
    def switch_account(self, account_name, use_omeclick=True):
        """
        Switch to a specific account by name.
        
        Args:
            account_name (str): Name of the account to switch to
            use_omeclick (bool): Whether to click the account in the UI (default: True)
            
        Returns:
            bool: True if successful, False otherwise
        """
        if not self.app:
            return False
        try:
            t0 = time.time()
            accounts = self.get_accounts()
            t1 = time.time()
            print(f"[TIMER] switch_account: get_accounts: {t1-t0:.3f}s")
            for account in accounts:
                if account.name == account_name:
                    self.current_account = account
                    print(f"[MailController] Switched to account: {account_name}")
                    # Call the central navigation action handler if omeclick is enabled AND front nav is enabled
                    if self.use_front_nav and use_omeclick:
                        t2 = time.time()
                        action_result = self.handle_navigation_action({
                            'action': 'switch_account',
                            'account_name': account_name,
                            'execute_click': True
                        })
                        t3 = time.time()
                        print(f"[TIMER] switch_account: handle_navigation_action: {t3-t2:.3f}s")
                        if action_result['status'] == 'success':
                            omeClick = action_result.get('omeClick')
                            if omeClick:
                                print(f"[MailController] Found omeClick for {account_name}: {omeClick}")
                            else:
                                print(f"[MailController] No omeClick found for {account_name}")
                        else:
                            print(f"[MailController] Navigation lookup failed: {action_result.get('message')}")
                    return True
            print(f"[MailController] Account '{account_name}' not found")
            return False
        except Exception as e:
            print(f"[MailController] Error switching account: {e}")
            return False
    
    def get_mailboxes(self, account_name=None):
        """
        Get mailboxes for the current or specified account.
        
        Args:
            account_name (str, optional): Account name. If None, uses current account.
            
        Returns:
            list: List of mailbox objects
        """
        if not self.app:
            return []
        
        try:
            # Only switch if account_name is provided AND we don't have a current account
            if account_name and not self.current_account:
                self.switch_account(account_name)
            
            if not self.current_account:
                # Use first available account
                accounts = self.get_accounts()
                if accounts:
                    self.current_account = accounts[0]
                else:
                    return []
            
            mailboxes = self.current_account.mailboxes()
            print(f"[MailController] Found {len(mailboxes)} mailboxes in account '{self.current_account.name}'")
            return mailboxes
        except Exception as e:
            print(f"[MailController] Error getting mailboxes: {e}")
            return []
    
    def get_mailbox_names(self, account_name=None):
        """
        Get names of all mailboxes for the current or specified account.
        
        Args:
            account_name (str, optional): Account name. If None, uses current account.
            
        Returns:
            list: List of mailbox names
        """
        mailboxes = self.get_mailboxes(account_name)
        return [mailbox.name for mailbox in mailboxes]
    
    def switch_mailbox(self, mailbox_name, account_name=None, use_omeclick=True):
        """
        Switch to a specific mailbox by name.
        
        Args:
            mailbox_name (str): Name of the mailbox to switch to
            account_name (str, optional): Account name. If None, uses current account.
            use_omeclick (bool): Whether to click the mailbox in the UI (default: True)
            
        Returns:
            bool: True if successful, False otherwise
        """
        if not self.app:
            return False
        
        try:
            # Determine the account to use
            target_account = account_name
            if not target_account:
                if self.current_account:
                    target_account = self.current_account.name
                else:
                    print("[MailController] No account specified and no current account")
                    return False
            
            # Ensure the correct account is selected
            if not self.current_account or self.current_account.name != target_account:
                self.switch_account(target_account)
            
            # Use navigation action for UI clicking if requested AND front nav is enabled
            if self.use_front_nav and use_omeclick:
                nav_result = self.handle_navigation_action({
                    'action': 'switch_mailbox',
                    'account_name': target_account,
                    'mailbox_name': mailbox_name,
                    'execute_click': True
                })
                
                if nav_result.get('status') == 'success':
                    print(f"[MailController] Navigation click executed for mailbox: {mailbox_name}")
                    # Continue with PyXA switch for state management
                else:
                    print(f"[MailController] Navigation lookup failed: {nav_result.get('message', 'Unknown error')}")
                    # Continue anyway - PyXA switch might still work
            
            # Get mailboxes directly from the current account (no redundant get_mailboxes call)
            mailboxes = self.current_account.mailboxes()
            for mailbox in mailboxes:
                if mailbox.name == mailbox_name:
                    self.current_mailbox = mailbox
                    print(f"[MailController] Switched to mailbox: {mailbox_name}")
                    return True
            
            print(f"[MailController] Mailbox '{mailbox_name}' not found")
            return False
        except Exception as e:
            print(f"[MailController] Error switching mailbox: {e}")
            return False
    
    def get_current_context(self):
        """
        Get current account and mailbox context.
        
        Returns:
            dict: Current context information
        """
        context = {
            'app_initialized': self.app is not None,
            'current_account': self.current_account.name if self.current_account else None,
            'current_mailbox': self.current_mailbox.name if self.current_mailbox else None,
            'available_accounts': self.get_account_names(),
            'available_mailboxes': self.get_mailbox_names() if self.current_account else []
        }
        return context
    
    def refresh_app(self):
        """
        Refresh the app state by re-initializing.
        
        Returns:
            bool: True if successful, False otherwise
        """
        self._initialize_app()
        return self.app is not None
    
    def quit_app(self):
        """
        Quit the Mail application.
        
        Returns:
            bool: True if successful, False otherwise
        """
        if not self.app:
            return False
        
        try:
            self.app.quit()
            self.app = None
            self.current_account = None
            self.current_mailbox = None
            print("[MailController] Mail app quit successfully")
            return True
        except Exception as e:
            print(f"[MailController] Error quitting Mail app: {e}")
            return False
    
    def get_accounts_data(self):
        """
        Get all accounts with their mailboxes as structured data.
        
        Returns:
            dict: Structured data with accounts and their mailboxes
        """
        if not self.app:
            return {}
        
        try:
            accounts_data = {}
            accounts = self.get_accounts()
            
            for account in accounts:
                account_name = account.name
                mailboxes = list(account.mailboxes())
                mailbox_names = [mb.name for mb in mailboxes]
                
                accounts_data[account_name] = {
                    'name': account_name,
                    'mailboxes': mailbox_names,
                    'mailbox_count': len(mailboxes)
                }
            
            return accounts_data
        except Exception as e:
            print(f"[MailController] Error getting accounts data: {e}")
            return {}
    
    def get_mailboxes_for_account(self, account_name):
        """
        Get all mailboxes for a specific account.
        
        Args:
            account_name (str): Name of the account
            
        Returns:
            list: List of mailbox names for the account
        """
        if not self.app:
            return []
        
        try:
            # Switch to the account first
            if self.switch_account(account_name):
                return self.get_mailbox_names()
            else:
                return []
        except Exception as e:
            print(f"[MailController] Error getting mailboxes for account {account_name}: {e}")
            return []
    
    def switch_mailbox_by_name(self, mailbox_name, account_name=None):
        """
        Switch to a specific mailbox by name.
        
        Args:
            mailbox_name (str): Name of the mailbox to switch to
            account_name (str, optional): Account name. If None, uses current account.
            
        Returns:
            dict: Result with status and current context
        """
        if not self.app:
            return {'status': 'failed', 'error': 'App not initialized'}
        
        try:
            # Switch account if specified
            if account_name:
                if not self.switch_account(account_name):
                    return {'status': 'failed', 'error': f'Account {account_name} not found'}
            
            # Switch mailbox
            if self.switch_mailbox(mailbox_name):
                return {
                    'status': 'success',
                    'account': self.current_account.name if self.current_account else None,
                    'mailbox': self.current_mailbox.name if self.current_mailbox else None,
                    'context': self.get_current_context()
                }
            else:
                return {'status': 'failed', 'error': f'Mailbox {mailbox_name} not found'}
        except Exception as e:
            return {'status': 'failed', 'error': str(e)}
    
    def get_current_window_ref(self):
        """
        Get the canonical window_ref for the current active window from navBigDaDDy.
        Returns:
            str: The canonical window_ref (AXIdentifier or mapped value)
        """
        if hasattr(self.nav, 'active_target') and self.nav.active_target:
            return self.nav.active_target.get('window_ref')
        return None

    def get_hierarchical_nav(self, filename=None):
        """
        Read the hierarchical navigation JSONL file, building it if missing.
        Args:
            filename (str, optional): The filename to read. If None, uses canonical window_ref.
        Returns:
            list: List of navigation items (dicts), or [] if file not found or error
        """
        if filename is None:
            window_ref = self.get_current_window_ref() or 'MainWindow'
            filename = f"hierarchical_{self.BUNDLE_ID}_{window_ref}.jsonl"
        nav_path = os.path.join(TRANSLATOR_EXPORT_DIR, filename)
        # Check cache first
        window_ref = filename.split('_')[-1].replace('.jsonl', '')
        if self._nav_cache['window_ref'] == window_ref and self._nav_cache['nav_items']:
            return self._nav_cache['nav_items']
        def read_jsonl(path):
            items = []
            try:
                with open(path, "r", encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if not line or line.startswith("#"):
                            continue
                        try:
                            items.append(json.loads(line))
                        except Exception as e:
                            print(f"[MailController] Error parsing line: {e}")
                return items
            except Exception as e:
                print(f"[MailController] Error reading hierarchical nav file: {e}")
                return []
        # Try to read the file
        if os.path.exists(nav_path):
            nav_items = read_jsonl(nav_path)
            self._nav_cache = {'window_ref': window_ref, 'nav_items': nav_items}
            return nav_items
        # If not found, try to build it
        print(f"[MailController] Hierarchical nav file not found, building with mailNav_translator.py...")
        try:
            # Call the translator as a subprocess
            result = subprocess.run(
                ["python", "-m", "ome.controllers.mail.mailNav_translator", "--force"],
                capture_output=True, text=True
            )
            print(result.stdout)
            if result.returncode != 0:
                print(f"[MailController] mailNav_translator.py failed: {result.stderr}")
                return []
        except Exception as e:
            print(f"[MailController] Error running mailNav_translator.py: {e}")
            return []
        # Try to read again
        if os.path.exists(nav_path):
            nav_items = read_jsonl(nav_path)
            self._nav_cache = {'window_ref': window_ref, 'nav_items': nav_items}
            return nav_items
        else:
            print(f"[MailController] Still could not find {nav_path} after building.")
            return []

    def get_mailbox_names_applescript(self, account_name=None):
        """
        Fetch mailbox names for the specified account using a raw AppleScript command (via subprocess).
        Returns a list of mailbox names and the elapsed time.
        """
        import subprocess
        import time
        if not account_name:
            # Use first available account
            account_names = self.get_account_names()
            if not account_names:
                return [], 0.0
            account_name = account_names[0]
        applescript = f'''
        tell application "Mail"
            set mailboxNames to name of mailboxes of account "{account_name}"
            return mailboxNames
        end tell
        '''
        t0 = time.time()
        try:
            result = subprocess.run(["osascript", "-e", applescript], capture_output=True, text=True, timeout=10)
            t1 = time.time()
            if result.returncode == 0:
                # Parse output: osascript returns names separated by commas
                output = result.stdout.strip()
                mailbox_names = [name.strip() for name in output.split(",") if name.strip()]
                return mailbox_names, t1-t0
            else:
                return [], t1-t0
        except Exception:
            t1 = time.time()
            return [], t1-t0

def main():
    """
    Command-line interface for testing MailController functionality.
    """
    import argparse
    import time
    
    parser = argparse.ArgumentParser(
        description="Test MailController functionality from command line.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python -m ome.controllers.mail.mail_controller --test-nav
  python -m ome.controllers.mail.mail_controller --accounts
  python -m ome.controllers.mail.mail_controller --mailboxes Google
  python -m ome.controllers.mail.mail_controller --context
        """
    )
    
    parser.add_argument(
        '--test-nav', 
        action='store_true', 
        help='Test hierarchical navigation file reading/building'
    )
    parser.add_argument(
        '--accounts', 
        action='store_true', 
        help='List all available accounts'
    )
    parser.add_argument(
        '--mailboxes', 
        type=str, 
        help='List mailboxes for specified account (e.g., "Google")'
    )
    parser.add_argument(
        '--context', 
        action='store_true', 
        help='Show current account/mailbox context'
    )
    parser.add_argument(
        '--test-nav-action', 
        type=str, 
        help='Test handle_navigation_action with account name (e.g., "Google")'
    )
    parser.add_argument(
        '--all', 
        action='store_true', 
        help='Run all tests'
    )
    parser.add_argument(
        '--no-front-nav',
        action='store_true',
        help='Disable front navigation (omeClick); use PyXA only (overrides .env setting)'
    )
    parser.add_argument(
        '--mailbox-names-applescript',
        type=str,
        nargs='?',
        const=None,
        help='Fetch mailbox names for specified account using raw AppleScript (faster, for timing test)'
    )
    parser.add_argument(
        '--mailboxes-pyxa-only',
        type=str,
        nargs='?',
        const=None,
        help='List mailboxes for specified account using only PyXA (no navigation, for timing test)'
    )
    
    args = parser.parse_args()
    
    start_time = time.time()
    t0 = time.time()
    controller = MailController()
    t1 = time.time()
    print(f"[TIMER] MailController total init: {t1-t0:.3f}s")
    if args.mailboxes or args.all:
        if args.mailboxes:
            account_name = args.mailboxes
        else:
            account_names = controller.get_account_names()
            account_name = account_names[0] if account_names else None
        if account_name:
            t2 = time.time()
            mailboxes = controller.get_mailboxes(account_name)
            t3 = time.time()
            print(f"[TIMER] get_mailboxes: {t3-t2:.3f}s")
    if getattr(args, 'mailbox_names_applescript', None) is not None:
        account_name = args.mailbox_names_applescript
        t0 = time.time()
        mailbox_names, elapsed = controller.get_mailbox_names_applescript(account_name)
        t1 = time.time()
        print(f"[TIMER] get_mailbox_names_applescript: {elapsed:.3f}s (wall: {t1-t0:.3f}s)")
        print(f"Mailbox names for account '{account_name or '[default]'}': {mailbox_names}")
        return
    if getattr(args, 'mailboxes_pyxa_only', None) is not None:
        account_name = args.mailboxes_pyxa_only
        t0 = time.time()
        # Only use PyXA, do not call navBigDaDDy or navigation
        if not account_name:
            account_names = controller.get_account_names()
            account_name = account_names[0] if account_names else None
        mailboxes = []
        if account_name:
            # Only use PyXA to get mailboxes
            accounts = controller.get_accounts()
            for account in accounts:
                if account.name == account_name:
                    t1 = time.time()
                    mailboxes = account.mailboxes()
                    t2 = time.time()
                    mailbox_names = [mb.name for mb in mailboxes]
                    print(f"[TIMER] get_mailboxes_pyxa_only: {t2-t1:.3f}s")
                    print(f"Mailbox names for account '{account_name}': {mailbox_names}")
                    break
        return
    end_time = time.time()
    print(f"Total wall-clock time (all steps): {end_time - start_time:.2f} seconds.")


if __name__ == "__main__":
    main() 