#!/usr/bin/env python3
"""
ome/controllers/mail/mail_action_controller.py

Mail Action Controller that uses fuzzy matching between PyXA output and JSONL action mappings.

This controller:
1. Takes PyXA output (like "Inbox - Google", "Flagged - Red")
2. Fuzzy matches against our JSONL action mappings
3. Executes the corresponding UI action sequences
4. Falls back to menu navigation when needed
"""

import os
import sys
import json
import time
from fuzzywuzzy import fuzz
from fuzzywuzzy import process

# Add the project root to the Python path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from ome.controllers.mail import MailController
from ome.utils.uiNav.navBigDaDDy import navBigDaDDy

class MailActionController:
    """
    Mail Action Controller that uses fuzzy matching between PyXA output and JSONL action mappings.
    
    Instead of hardcoded mappings, this controller:
    1. Takes PyXA logical output (e.g., "Inbox - Google")
    2. Fuzzy matches against JSONL action mappings
    3. Executes the best matching UI action sequence
    4. Falls back to menu navigation when needed
    """
    
    def __init__(self):
        self.mail_controller = MailController()  # PyXA-based
        self.nav = None
        self.action_mappings = []
        self._init_nav()
        self._load_action_mappings()
    
    def _init_nav(self):
        """Initialize navBigDaDDy for UI interactions."""
        try:
            self.nav = navBigDaDDy("com.apple.mail")
            print("[MailActionController] navBigDaDDy initialized")
        except Exception as e:
            print(f"[MailActionController] Error initializing navBigDaDDy: {e}")
            self.nav = None
    
    def _load_action_mappings(self):
        """Load action mappings from JSONL file."""
        try:
            mappings_file = os.path.join(project_root, "ome", "data", "navigation", "mail_action_mappings.jsonl")
            
            if not os.path.exists(mappings_file):
                print(f"[MailActionController] Action mappings file not found: {mappings_file}")
                return
            
            with open(mappings_file, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line:
                        mapping = json.loads(line)
                        self.action_mappings.append(mapping)
            
            print(f"[MailActionController] Loaded {len(self.action_mappings)} action mappings")
        except Exception as e:
            print(f"[MailActionController] Error loading action mappings: {e}")
    
    def _get_current_window_context(self):
        """
        Get current window context from win_com.apple.mail.jsonl.
        Parses the dynamic window title to extract current account/mailbox info.
        
        Returns:
            Dict with parsed window context or None
        """
        try:
            window_file = os.path.join(project_root, "ome", "data", "windows", "win_com.apple.mail.jsonl")
            
            if not os.path.exists(window_file):
                print(f"[MailActionController] Window file not found: {window_file}")
                return None
            
            with open(window_file, 'r') as f:
                window_data = json.load(f)
            
            active_target = window_data.get('active_target', {})
            window_title = active_target.get('window_title', '')
            
            if not window_title:
                return None
            
            print(f"[MailActionController] Current window title: {window_title}")
            
            # Handle different window title formats:
            # Format 1: "Inbox – andy7string@gmail.com – Transactions · 410 messages, 167 unread"
            # Format 2: "Orange – 2 messages" (simple format)
            # Format 3: "Mailbox – Account – Type · Message info"
            
            if ' – ' in window_title and ' · ' in window_title:
                # Format 1: Complex format with account and message info
                parts = window_title.split(' – ')
                if len(parts) >= 2:
                    mailbox_name = parts[0].strip()
                    account_info = parts[1].strip()
                    
                    # Extract account name (remove any additional info after account)
                    account_name = account_info.split(' – ')[0].strip()
                    
                    # Extract message info if present
                    message_info = ""
                    if ' · ' in window_title:
                        message_info = window_title.split(' · ')[1].strip()
                    
                    context = {
                        'mailbox_name': mailbox_name,
                        'account_name': account_name,
                        'message_info': message_info,
                        'full_title': window_title,
                        'window_ref': active_target.get('window_ref'),
                        'timestamp': active_target.get('timestamp'),
                        'format_type': 'complex'
                    }
                    
                    print(f"[MailActionController] Parsed complex context: {context}")
                    return context
            
            elif ' – ' in window_title:
                # Format 2: Simple format like "Orange – 2 messages"
                parts = window_title.split(' – ')
                if len(parts) >= 2:
                    mailbox_name = parts[0].strip()
                    message_info = parts[1].strip()
                    
                    context = {
                        'mailbox_name': mailbox_name,
                        'account_name': None,  # No account info in simple format
                        'message_info': message_info,
                        'full_title': window_title,
                        'window_ref': active_target.get('window_ref'),
                        'timestamp': active_target.get('timestamp'),
                        'format_type': 'simple'
                    }
                    
                    print(f"[MailActionController] Parsed simple context: {context}")
                    return context
            
            # Fallback: return basic info
            context = {
                'mailbox_name': None,
                'account_name': None,
                'message_info': window_title,
                'full_title': window_title,
                'window_ref': active_target.get('window_ref'),
                'timestamp': active_target.get('timestamp'),
                'format_type': 'unknown'
            }
            
            print(f"[MailActionController] Parsed fallback context: {context}")
            return context
            
        except Exception as e:
            print(f"[MailActionController] Error parsing window context: {e}")
            return None
    
    def _validate_fuzzy_match_with_context(self, mapping, window_context):
        """
        Validate fuzzy match against current window context.
        
        Args:
            mapping: Action mapping from fuzzy match
            window_context: Current window context from window title
        
        Returns:
            True if match is valid, False otherwise
        """
        if not window_context:
            return True  # No context to validate against
        
        # If window context has no account info (simple format), skip account validation
        if not window_context.get('account_name'):
            print(f"[MailActionController] No account info in window context, skipping account validation")
            return True
        
        # Check if account matches
        if mapping.get('account_name') and window_context.get('account_name'):
            if mapping['account_name'] != window_context['account_name']:
                print(f"[MailActionController] Account mismatch: mapping='{mapping['account_name']}', context='{window_context['account_name']}'")
                return False
        
        # Check if mailbox matches (for mailbox navigation)
        if mapping.get('mailbox_name') and window_context.get('mailbox_name'):
            if mapping['mailbox_name'] != window_context['mailbox_name']:
                print(f"[MailActionController] Mailbox mismatch: mapping='{mapping['mailbox_name']}', context='{window_context['mailbox_name']}'")
                return False
        
        print(f"[MailActionController] ✓ Context validation passed")
        return True
    
    def _ensure_app_focus(self):
        """Ensure Mail app is focused."""
        if not self.nav:
            return False
        
        try:
            return self.nav.ensure_app_focus()
        except Exception as e:
            print(f"[MailActionController] Error ensuring app focus: {e}")
            return False
    
    def _fuzzy_match_action(self, pyxa_output, action_type=None, threshold=60):
        """
        Fuzzy match PyXA output against action mappings.
        
        Args:
            pyxa_output: String from PyXA (e.g., "Inbox - Google", "Flagged - Red")
            action_type: Optional filter for action type
            threshold: Minimum similarity score (0-100)
        
        Returns:
            Best matching action mapping or None
        """
        if not self.action_mappings:
            return None
        
        # Get current window context for validation
        window_context = self._get_current_window_context()
        
        # Filter mappings by action type if specified
        candidates = self.action_mappings
        if action_type:
            candidates = [m for m in self.action_mappings if m.get('action_type') == action_type]
        
        if not candidates:
            return None
        
        # Create search strings for each mapping
        search_strings = []
        for mapping in candidates:
            # Build search string from mapping components
            search_parts = []
            
            if mapping.get('account_name'):
                search_parts.append(mapping['account_name'])
            
            if mapping.get('mailbox_name'):
                search_parts.append(mapping['mailbox_name'])
            
            if mapping.get('action_type'):
                search_parts.append(mapping['action_type'])
            
            search_string = " - ".join(search_parts)
            search_strings.append(search_string)
        
        # Find best match using fuzzywuzzy
        try:
            best_match = process.extractOne(pyxa_output, search_strings, scorer=fuzz.token_sort_ratio)
            
            if best_match and best_match[1] >= threshold:
                best_string, score = best_match
                print(f"[MailActionController] Fuzzy match: '{pyxa_output}' -> '{best_string}' (score: {score})")
                
                # Find the corresponding mapping
                for mapping in candidates:
                    search_parts = []
                    if mapping.get('account_name'):
                        search_parts.append(mapping['account_name'])
                    if mapping.get('mailbox_name'):
                        search_parts.append(mapping['mailbox_name'])
                    if mapping.get('action_type'):
                        search_parts.append(mapping['action_type'])
                    
                    if " - ".join(search_parts) == best_string:
                        # Validate against window context
                        if self._validate_fuzzy_match_with_context(mapping, window_context):
                            return mapping
                        else:
                            print(f"[MailActionController] Context validation failed for mapping")
                            # Continue to next candidate
                            continue
            else:
                print(f"[MailActionController] No good fuzzy match found for '{pyxa_output}' (best score: {best_match[1] if best_match else 0})")
        
        except Exception as e:
            print(f"[MailActionController] Error in fuzzy matching: {e}")
        
        return None
    
    def _execute_ui_sequence(self, mapping):
        """
        Execute the UI sequence from a mapping.
        
        Args:
            mapping: Action mapping with ui_sequence
        
        Returns:
            True if successful, False otherwise
        """
        if not self.nav or not mapping.get('ui_sequence'):
            return False
        
        if not self._ensure_app_focus():
            return False
        
        ui_sequence = mapping['ui_sequence']
        
        for step in ui_sequence:
            step_type = step.get('type')
            description = step.get('description', 'Unknown step')
            
            print(f"[MailActionController] Executing: {description}")
            
            if step_type == 'click':
                target = step.get('target')
                omeClick = step.get('omeClick')
                
                if omeClick:
                    # Use omeClick coordinates for precise clicking
                    x, y = omeClick
                    if self.nav.click_at_coordinates(x, y):
                        print(f"[MailActionController] ✓ Clicked at coordinates ({x}, {y})")
                    else:
                        print(f"[MailActionController] ✗ Failed to click at coordinates ({x}, {y})")
                        return False
                elif target:
                    # Use hierarchical search to find the element
                    print(f"[MailActionController] Searching for sidebar element: '{target}'")
                    
                    # Parse target to extract account and mailbox
                    # For now, assume target is in format "account mailbox" or just "mailbox"
                    parts = target.split()
                    if len(parts) >= 2:
                        # Assume first part is account, rest is mailbox
                        account_name = parts[0]
                        mailbox_name = " ".join(parts[1:])
                        element = self._find_sidebar_element_hierarchical(account_name, mailbox_name)
                    else:
                        # Single word - assume it's a mailbox name
                        mailbox_name = target
                        # Try to find it under any account
                        element = self._find_sidebar_element_hierarchical("andy7string@gmail.com", mailbox_name)
                    
                    if element:
                        x, y = element['omeClick']
                        if self.nav.click_at_coordinates(x, y):
                            print(f"[MailActionController] ✓ Clicked '{element['title']}' at ({x}, {y})")
                        else:
                            print(f"[MailActionController] ✗ Failed to click '{element['title']}' at ({x}, {y})")
                            return False
                    else:
                        # Fallback to direct element clicking
                        if self.nav.click_element(target):
                            print(f"[MailActionController] ✓ Clicked element '{target}' (fallback)")
                        else:
                            print(f"[MailActionController] ✗ Failed to click element '{target}'")
                            return False
                else:
                    print(f"[MailActionController] ✗ No click target specified")
                    return False
            
            elif step_type == 'wait':
                duration = step.get('duration', 1)
                print(f"[MailActionController] Waiting {duration}s...")
                time.sleep(duration)
            
            elif step_type == 'menu_navigate':
                menu_path = step.get('menu_path', [])
                if self.nav.navigate_menu_path(menu_path):
                    print(f"[MailActionController] ✓ Navigated menu path: {' > '.join(menu_path)}")
                else:
                    print(f"[MailActionController] ✗ Failed to navigate menu path: {' > '.join(menu_path)}")
                    return False
        
        return True
    
    def _fallback_menu_navigation(self, mapping):
        """
        Fallback to menu navigation if UI sequence fails.
        
        Args:
            mapping: Action mapping with fallback_menu_path
        
        Returns:
            True if successful, False otherwise
        """
        if not self.nav or not mapping.get('fallback_menu_path'):
            return False
        
        if not self._ensure_app_focus():
            return False
        
        menu_path = mapping['fallback_menu_path']
        print(f"[MailActionController] Trying fallback menu navigation: {' > '.join(menu_path)}")
        
        if self.nav.navigate_menu_path(menu_path):
            print(f"[MailActionController] ✓ Fallback menu navigation successful")
            return True
        else:
            print(f"[MailActionController] ✗ Fallback menu navigation failed")
            return False
    
    def switch_account(self, account_name):
        """
        Switch account using fuzzy matching.
        
        Args:
            account_name: Account name from PyXA
        
        Returns:
            True if successful, False otherwise
        """
        print(f"[MailActionController] Switching to account: {account_name}")
        
        # Step 1: PyXA does the logical switch
        pyxa_success = self.mail_controller.switch_account(account_name)
        if not pyxa_success:
            print(f"[MailActionController] PyXA failed to switch account: {account_name}")
            return False
        
        # Step 2: Fuzzy match and execute UI action
        mapping = self._fuzzy_match_action(account_name, action_type="switch_account")
        
        if mapping:
            # Try UI sequence first
            if self._execute_ui_sequence(mapping):
                print(f"[MailActionController] ✓ UI sequence successful for account: {account_name}")
                return True
            
            # Fallback to menu navigation
            if self._fallback_menu_navigation(mapping):
                print(f"[MailActionController] ✓ Fallback menu navigation successful for account: {account_name}")
                return True
        
        print(f"[MailActionController] ✗ No matching action found for account: {account_name}")
        return False
    
    def switch_mailbox(self, mailbox_name, account_name=None):
        """
        Switch mailbox using fuzzy matching.
        
        Args:
            mailbox_name: Mailbox name from PyXA
            account_name: Optional account name for context
        
        Returns:
            True if successful, False otherwise
        """
        print(f"[MailActionController] Switching to mailbox: {mailbox_name}")
        
        # Build search string for fuzzy matching
        if account_name:
            search_string = f"{mailbox_name} - {account_name}"
        else:
            search_string = mailbox_name
        
        # Step 1: PyXA does the logical switch
        if account_name:
            self.switch_account(account_name)
        
        pyxa_success = self.mail_controller.switch_mailbox(mailbox_name)
        if not pyxa_success:
            print(f"[MailActionController] PyXA failed to switch mailbox: {mailbox_name}")
            return False
        
        # Step 2: Fuzzy match and execute UI action
        # Try account-specific mailbox first
        mapping = self._fuzzy_match_action(search_string, action_type="navigate_mailbox")
        
        if not mapping and not account_name:
            # Try global mailbox
            mapping = self._fuzzy_match_action(mailbox_name, action_type="navigate_global")
        
        if mapping:
            # Try UI sequence first
            if self._execute_ui_sequence(mapping):
                print(f"[MailActionController] ✓ UI sequence successful for mailbox: {mailbox_name}")
                return True
            
            # Fallback to menu navigation
            if self._fallback_menu_navigation(mapping):
                print(f"[MailActionController] ✓ Fallback menu navigation successful for mailbox: {mailbox_name}")
                return True
        
        print(f"[MailActionController] ✗ No matching action found for mailbox: {mailbox_name}")
        return False
    
    def navigate_to_inbox(self, account_name):
        """
        Navigate to account inbox using fuzzy matching.
        
        Args:
            account_name: Account name from PyXA
        
        Returns:
            True if successful, False otherwise
        """
        print(f"[MailActionController] Navigating to inbox for account: {account_name}")
        
        # Step 1: PyXA does the logical navigation
        pyxa_success = self.mail_controller.switch_account(account_name)
        if pyxa_success:
            pyxa_success = self.mail_controller.switch_mailbox("INBOX")  # Use correct PyXA name
        
        if not pyxa_success:
            print(f"[MailActionController] PyXA failed to navigate to inbox: {account_name}")
            return False
        
        # Step 2: Fuzzy match and execute UI action
        mapping = self._fuzzy_match_action(account_name, action_type="navigate_to_inbox")
        
        if mapping:
            # Try UI sequence first
            if self._execute_ui_sequence(mapping):
                print(f"[MailActionController] ✓ UI sequence successful for inbox: {account_name}")
                return True
            
            # Fallback to menu navigation
            if self._fallback_menu_navigation(mapping):
                print(f"[MailActionController] ✓ Fallback menu navigation successful for inbox: {account_name}")
                return True
        
        print(f"[MailActionController] ✗ No matching action found for inbox: {account_name}")
        return False
    
    def get_accounts(self):
        """Get accounts from PyXA."""
        return self.mail_controller.get_account_names()
    
    def get_mailboxes(self, account_name=None):
        """Get mailboxes from PyXA."""
        return self.mail_controller.get_mailbox_names(account_name)
    
    def get_current_context(self):
        """Get current context from PyXA and window title."""
        pyxa_context = self.mail_controller.get_current_context()
        window_context = self._get_current_window_context()
        
        integrated_context = {
            'pyxa': pyxa_context,
            'window': window_context,
            'integration_status': 'active',
            'context_source': 'pyxa_and_window_title'
        }
        
        return integrated_context
    
    def refresh(self):
        """Refresh both PyXA and navBigDaDDy."""
        print("[MailActionController] Refreshing controllers...")
        
        # Refresh PyXA
        self.mail_controller.refresh_app()
        
        # Refresh navBigDaDDy
        if self.nav:
            self.nav.refresh_nav()
        
        print("[MailActionController] Controllers refreshed")
    
    def quit(self):
        """Quit Mail app using PyXA."""
        return self.mail_controller.quit_app()
    
    def _find_sidebar_element_hierarchical(self, account_name, mailbox_name):
        """
        Find sidebar element using hierarchical structure (Provider -> Account -> Mailbox).
        
        Args:
            account_name: Account name (e.g., "andy7string@gmail.com")
            mailbox_name: Mailbox name (e.g., "Inbox", "Drafts", "Sent")
        
        Returns:
            Dict with omeClick coordinates for the provider (first click needed)
        """
        try:
            # Load sidebar elements from appNav file
            appnav_file = os.path.join(project_root, "ome", "data", "navigation", "appNav_com.apple.mail_MainWindow.jsonl")
            
            if not os.path.exists(appnav_file):
                print(f"[MailActionController] AppNav file not found: {appnav_file}")
                return None
            
            # Read sidebar elements (AXRow elements)
            sidebar_elements = []
            with open(appnav_file, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and '"AXRole": "AXRow"' in line:
                        try:
                            element = json.loads(line)
                            if element.get('AXTitle') and element.get('omeClick'):
                                sidebar_elements.append(element)
                        except json.JSONDecodeError:
                            continue
            
            if not sidebar_elements:
                print(f"[MailActionController] No sidebar elements found")
                return None
            
            print(f"[MailActionController] Found {len(sidebar_elements)} sidebar elements")
            
            # Find the provider that contains this account
            # Look for account first to find which provider it belongs to
            account_indices = []
            for i, element in enumerate(sidebar_elements):
                if element['AXTitle'] == account_name:
                    account_indices.append(i)
            
            if not account_indices:
                print(f"[MailActionController] Account '{account_name}' not found")
                return None
            
            print(f"[MailActionController] Found {len(account_indices)} occurrences of account '{account_name}'")
            
            # For each account occurrence, find the provider above it
            for account_idx in account_indices:
                print(f"[MailActionController] Checking account at index {account_idx}")
                
                # Look for provider above the account
                provider_idx = None
                for i in range(account_idx - 1, -1, -1):
                    element = sidebar_elements[i]
                    # Common provider names
                    if element['AXTitle'] in ["Google", "iCloud", "Outlook", "Yahoo", "Exchange"]:
                        provider_idx = i
                        break
                
                if provider_idx is None:
                    print(f"[MailActionController] No provider found above account at index {account_idx}")
                    continue
                
                provider_name = sidebar_elements[provider_idx]['AXTitle']
                print(f"[MailActionController] Found provider '{provider_name}' at index {provider_idx}")
                
                # Verify this account has the target mailbox
                start_idx = account_idx + 1
                
                # Find the next account to know where to stop
                next_account_idx = None
                for i in range(start_idx, len(sidebar_elements)):
                    if sidebar_elements[i]['AXTitle'] == account_name:
                        next_account_idx = i
                        break
                
                # Search for mailbox between current account and next account
                end_idx = next_account_idx if next_account_idx else len(sidebar_elements)
                
                for i in range(start_idx, end_idx):
                    element = sidebar_elements[i]
                    if element['AXTitle'] == mailbox_name:
                        print(f"[MailActionController] Found '{mailbox_name}' at index {i} under account '{account_name}'")
                        print(f"[MailActionController] Provider '{provider_name}' coordinates: {sidebar_elements[provider_idx]['omeClick']}")
                        
                        return {
                            'omeClick': sidebar_elements[provider_idx]['omeClick'],
                            'provider_title': provider_name,
                            'provider_index': provider_idx,
                            'account_index': account_idx,
                            'mailbox_index': i,
                            'account_title': account_name,
                            'mailbox_title': mailbox_name
                        }
            
            print(f"[MailActionController] Mailbox '{mailbox_name}' not found under account '{account_name}'")
            return None
                
        except Exception as e:
            print(f"[MailActionController] Error in hierarchical sidebar search: {e}")
            return None

def main():
    """Test the action controller with fuzzy matching."""
    print("=== Testing Mail Action Controller with Fuzzy Matching ===")
    
    controller = MailActionController()
    
    # Get accounts
    print("\n1. Getting accounts:")
    accounts = controller.get_accounts()
    print(f"Available accounts: {accounts}")
    
    # Test fuzzy matching for account switching
    if "andy7string@gmail.com" in accounts:
        print(f"\n2. Testing fuzzy matching for account switching:")
        success = controller.switch_account("andy7string@gmail.com")
        print(f"Result: {'✓ Success' if success else '✗ Failed'}")
        
        # Test fuzzy matching for mailbox switching
        print(f"\n3. Testing fuzzy matching for mailbox switching:")
        success = controller.switch_mailbox("Inbox", "andy7string@gmail.com")
        print(f"Result: {'✓ Success' if success else '✗ Failed'}")
        
        # Test fuzzy matching for inbox navigation
        print(f"\n4. Testing fuzzy matching for inbox navigation:")
        success = controller.navigate_to_inbox("andy7string@gmail.com")
        print(f"Result: {'✓ Success' if success else '✗ Failed'}")
    
    print("\n=== Test Complete ===")

if __name__ == "__main__":
    main() 