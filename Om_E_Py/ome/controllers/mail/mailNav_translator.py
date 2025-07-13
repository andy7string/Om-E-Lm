"""
Mail Navigation Translator

Translates flat JSONL navigation data into hierarchical structure
that can follow mail_controller.py account/mailbox selections.
Only applicable for Mail app MainWindow JSONL files.

Main Purpose:
- Reads flat JSONL navigation data from appNav_builder.py output
- Translates it into hierarchical structure using PyXA as truth source
- Maps UI elements to actual Mail accounts and mailboxes
- Outputs hierarchical JSONL file for navigation automation

Key Features:
- PyXA Integration: Uses mail_controller.py to get actual account/mailbox data
- Pattern Matching: Applies configurable patterns to classify UI elements
- Hierarchical Output: Creates structured paths like ["accounts", "Gmail", "Inbox"]
- Config-Driven: Uses JSONL config for pattern matching rules
- Command-Line Interface: Can be run directly with various options

How to Use (Command Line):
    python -m ome.controllers.mail.mailNav_translator [--bundle com.apple.mail] [--force] [--debug] [--output filename.jsonl]

Arguments:
    --bundle: The bundle ID of the app (default: com.apple.mail)
    --force: Overwrite output file if it exists
    --debug: Print detailed debugging information
    --output: Custom output filename (optional)
    --no-output: Don't write output file, just print results

Example:
    python -m ome.controllers.mail.mailNav_translator --force
    # Translates Mail app navigation and outputs hierarchical JSONL

Output:
- A JSONL file named hierarchical_<bundle_id>_<window_ref>.jsonl in the translator export directory
- Each line is a JSON object with hierarchical path, omeClick coordinates, and type information

When to Use:
- After running appNav_builder.py to create flat navigation data
- To create hierarchical navigation structure for Mail automation
- For building navigation tools that need account/mailbox context
"""

import json
import os
import sys
import argparse
from typing import List, Dict, Any
from ome.utils.uiNav.navBigDaDDy import get_active_target_and_windows_from_file
from ome.utils.env.env import NAV_EXPORT_DIR, APPNAV_CONFIG_PATH, TRANSLATOR_EXPORT_DIR
from ome.controllers.mail.mail_controller import MailController

class MailNavTranslator:
    """
    Translates flat JSONL navigation data into hierarchical structure.
    Only works with Mail app MainWindow JSONL files.
    """
    
    def __init__(self, bundle_id: str = "com.apple.mail"):
        """
        Initialize translator with bundle ID.
        
        Args:
            bundle_id (str): Bundle ID of the app (default: com.apple.mail)
        """
        self.bundle_id = bundle_id
        self.mailbox_items = []
        self.other_items = []
        self.active_target = None
        self.translator_config = None
    
    def _ensure_config_loaded(self):
        """
        Ensure translator config is loaded, load it if it's None.
        """
        if self.translator_config is None:
            self.load_translator_config()
        # Ensure we always have a dict, even if empty
        if self.translator_config is None:
            self.translator_config = {}
    
    def get_canonical_window_ref(self):
        """
        Return the canonical window_ref (AXIdentifier or mapped value) for the current active window.
        """
        if not self.active_target:
            self.get_active_window_info()
        if self.active_target:
            return self.active_target.get('window_ref', 'MainWindow')
        return 'MainWindow'
    
    def get_active_window_info(self) -> Dict[str, Any]:
        """
        Get active window information using real-time file-based navigation state.
        """
        try:
            window_info = get_active_target_and_windows_from_file(bundle_id=self.bundle_id)
            self.active_target = window_info.get('active_target')
            return self.active_target
        except Exception as e:
            print(f"[MailNavTranslator] Error getting active window: {e}")
            return None
    
    def get_nav_file_path(self) -> str:
        """
        Get the path to the active navigation file based on canonical window_ref.
        Uses the same naming convention as appNav_builder.py.
        Returns:
            str: Path to the navigation JSONL file
        """
        window_ref = self.get_canonical_window_ref()
        nav_filename = f"appNav_{self.bundle_id}_{window_ref}.jsonl"
        nav_file_path = os.path.join(NAV_EXPORT_DIR, nav_filename)
        return nav_file_path
    
    def extract_mailbox_items(self) -> List[Dict[str, Any]]:
        """
        Extract all AXRow items with "description": "mailboxes" from the active nav file.
        
        Returns:
            List[Dict]: List of mailbox items with their properties
        """
        nav_file_path = self.get_nav_file_path()
        
        if not nav_file_path or not os.path.exists(nav_file_path):
            print(f"[MailNavTranslator] Nav file not found: {nav_file_path}")
            return []
        
        mailbox_items = []
        
        try:
            with open(nav_file_path, 'r', encoding='utf-8') as file:
                for line_num, line in enumerate(file, 1):
                    line = line.strip()
                    
                    # Skip empty lines and comments
                    if not line or line.startswith('#'):
                        continue
                    
                    try:
                        item = json.loads(line)
                        
                        # Check if this is a mailbox item (AXRow with mailboxes description)
                        if (item.get('AXRole') == 'AXRow' and 
                            'parent_path' in item and 
                            isinstance(item['parent_path'], list)):
                            
                            # Look for the mailboxes description in parent_path
                            for path_item in item['parent_path']:
                                if (isinstance(path_item, dict) and 
                                    path_item.get('description') == 'mailboxes'):
                                    
                                    mailbox_items.append({
                                        'line_number': line_num,
                                        'data': item
                                    })
                                    break
                    
                    except json.JSONDecodeError as e:
                        print(f"[MailNavTranslator] JSON decode error on line {line_num}: {e}")
                        continue
            
            print(f"[MailNavTranslator] Extracted {len(mailbox_items)} mailbox items from {nav_file_path}")
            return mailbox_items
            
        except Exception as e:
            print(f"[MailNavTranslator] Error reading nav file: {e}")
            return []
    
    def classify_item(self, item_title: str) -> Dict[str, Any]:
        """
        Classify an item based on the translator config patterns.
        
        Args:
            item_title (str): The title of the item to classify
            
        Returns:
            Dict: Classification information
        """
        self._ensure_config_loaded()
        
        title = item_title or ""
        
        # Check each pattern type
        for pattern in self.translator_config.get('account_patterns', []):
            if pattern in title:
                return {'type': 'account', 'name': pattern, 'title': title}
        
        for pattern in self.translator_config.get('mailbox_patterns', []):
            if pattern in title:
                return {'type': 'mailbox', 'name': pattern, 'title': title}
        
        for pattern in self.translator_config.get('aggregate_patterns', []):
            if pattern in title:
                return {'type': 'aggregate', 'name': pattern, 'title': title}
        
        for pattern in self.translator_config.get('flag_patterns', []):
            if pattern in title:
                return {'type': 'flag', 'name': pattern, 'title': title}
        
        for pattern in self.translator_config.get('system_patterns', []):
            if pattern in title:
                return {'type': 'system', 'name': pattern, 'title': title}
        
        return {'type': 'unknown', 'name': title, 'title': title}
    
    def print_mailbox_items(self):
        """
        Print extracted mailbox items for debugging.
        """
        items = self.extract_mailbox_items()
        
        print(f"\n[MailNavTranslator] Found {len(items)} mailbox items:")
        print(f"Active target: {self.active_target}")
        print(f"Nav file: {self.get_nav_file_path()}")
        print(f"Translator config: {self.translator_config}")
        print("-" * 50)
        
        for item in items:
            data = item['data']
            title = data.get('AXTitle', 'No Title')
            classification = self.classify_item(title)
            print(f"Line {item['line_number']}: {title} ({classification['type']}) - {data.get('omeClick', 'No Click')}")
        
        print("-" * 50)

    def get_pyxa_accounts(self):
        """
        Get accounts from mail_controller.py using PyXA.
        
        Returns:
            List: List of account objects from PyXA
        """
        try:
            mail_controller = MailController()
            accounts = mail_controller.get_accounts()
            account_names = mail_controller.get_account_names()
            print(f"[MailNavTranslator] PyXA found {len(accounts)} accounts: {account_names}")
            return accounts, account_names
        except Exception as e:
            print(f"[MailNavTranslator] Error getting PyXA accounts: {e}")
            return [], []

    def get_pyxa_mailboxes(self, account_name=None):
        """
        Get mailboxes for an account from mail_controller.py using PyXA.
        
        Args:
            account_name (str, optional): Account name. If None, gets for current account.
            
        Returns:
            List: List of mailbox names for the account
        """
        try:
            mail_controller = MailController()
            mailboxes = mail_controller.get_mailboxes(account_name)
            mailbox_names = mail_controller.get_mailbox_names(account_name)
            print(f"[MailNavTranslator] PyXA found {len(mailboxes)} mailboxes for account '{account_name or 'current'}': {mailbox_names}")
            return mailboxes, mailbox_names
        except Exception as e:
            print(f"[MailNavTranslator] Error getting PyXA mailboxes: {e}")
            return [], []

    def get_pyxa_accounts_data(self):
        """
        Get all accounts with their mailboxes as structured data from PyXA.
        
        Returns:
            Dict: Structured data with accounts and their mailboxes
        """
        try:
            mail_controller = MailController()
            accounts_data = mail_controller.get_accounts_data()
            print(f"[MailNavTranslator] PyXA accounts data: {accounts_data}")
            return accounts_data
        except Exception as e:
            print(f"[MailNavTranslator] Error getting PyXA accounts data: {e}")
            return {}

    def build_hierarchy_with_rules(self):
        """
        Build hierarchical structure using PyXA as truth and applying mapping rules.
        
        Returns:
            List[Dict]: List of items with proper hierarchical paths
        """
        # Get PyXA data as the truth
        accounts_data = self.get_pyxa_accounts_data()
        
        # Get JSONL items
        jsonl_items = self.extract_mailbox_items()
        
        hierarchical_items = []
        current_account = None
        current_system_item = None
        current_aggregate = None  # Track current aggregate item
        
        for i, item in enumerate(jsonl_items):
            data = item['data']
            title = data.get('AXTitle', '')
            omeClick = data.get('omeClick')
            line_number = item['line_number']
            
            # Rule 1: Check if it's an aggregate item
            if self._is_aggregate_item(title):
                current_aggregate = title
                current_system_item = None  # Reset system item when we hit an aggregate
                hierarchical_items.append({
                    'line_number': line_number,
                    'title': title,
                    'omeClick': omeClick,
                    'path': ['aggregate', title],
                    'type': 'aggregate'
                })
                continue
            
            # Rule 2: Check if it's an account
            matched_account = None
            for account_name in accounts_data.keys():
                if account_name in title:
                    matched_account = account_name
                    current_account = account_name
                    current_system_item = None  # Reset system item when we hit an account
                    break
            
            if matched_account:
                # If we have a current aggregate, make it the parent
                if current_aggregate:
                    path = ['aggregate', current_aggregate, matched_account]
                else:
                    path = ['accounts', matched_account]
                
                hierarchical_items.append({
                    'line_number': line_number,
                    'title': title,
                    'omeClick': omeClick,
                    'path': path,
                    'type': 'account',
                    'pyxa_account': matched_account
                })
                continue
            
            # Rule 3: Check if it's a system item
            if self._is_system_item(title):
                current_system_item = title
                current_aggregate = None  # Reset aggregate when we hit a system item
                hierarchical_items.append({
                    'line_number': line_number,
                    'title': title,
                    'omeClick': omeClick,
                    'path': ['system', title],
                    'type': 'system'
                })
                continue
            
            # Rule 4: Check if it's a flag item
            if self._is_flag_item(title):
                hierarchical_items.append({
                    'line_number': line_number,
                    'title': title,
                    'omeClick': omeClick,
                    'path': ['flags', title],
                    'type': 'flag'
                })
                continue
            
            # Rule 5: Try to match as mailbox for current account
            if current_account:
                matched_mailbox = self._find_matching_mailbox(title, accounts_data[current_account])
                if matched_mailbox:
                    # If we have a current aggregate, include it in the path
                    if current_aggregate:
                        path = ['aggregate', current_aggregate, current_account, matched_mailbox]
                    else:
                        path = ['accounts', current_account, matched_mailbox]
                    
                    hierarchical_items.append({
                        'line_number': line_number,
                        'title': title,
                        'omeClick': omeClick,
                        'path': path,
                        'type': 'mailbox',
                        'pyxa_account': current_account,
                        'pyxa_mailbox': matched_mailbox
                    })
                    continue
            
            # Rule 6: Undefined item - apply two-step logic
            if current_system_item:
                # Step 1: If we have a current system item, assign to it
                hierarchical_items.append({
                    'line_number': line_number,
                    'title': title,
                    'omeClick': omeClick,
                    'path': ['system', current_system_item, title],
                    'type': 'system_item',
                    'parent_system': current_system_item
                })
            elif current_account:
                # Step 2: Otherwise assign to the most recent account
                if current_aggregate:
                    path = ['aggregate', current_aggregate, current_account, title]
                else:
                    path = ['accounts', current_account, title]
                
                hierarchical_items.append({
                    'line_number': line_number,
                    'title': title,
                    'omeClick': omeClick,
                    'path': path,
                    'type': 'unknown_mailbox',
                    'pyxa_account': current_account
                })
            else:
                # Fallback to root if no context
                hierarchical_items.append({
                    'line_number': line_number,
                    'title': title,
                    'omeClick': omeClick,
                    'path': ['root', title],
                    'type': 'unknown'
                })
        
        return hierarchical_items

    def _normalize_mailbox_name(self, name):
        """
        Normalize mailbox names for better matching.
        """
        name = name.lower().strip()
        # Handle common variations
        if name in ['inbox', 'in box']:
            return 'inbox'
        if name in ['junk', 'spam']:
            return 'spam'
        if name in ['trash', 'bin', 'deleted']:
            return 'trash'
        if name in ['sent', 'sent mail']:
            return 'sent'
        if name in ['drafts', 'draft']:
            return 'drafts'
        if name in ['archive', 'archived']:
            return 'archive'
        return name

    def print_hierarchy_with_rules(self):
        """
        Print the hierarchical structure built with rules.
        """
        hierarchy = self.build_hierarchy_with_rules()
        
        print(f"\n[MailNavTranslator] Hierarchical Structure (with rules):")
        print("-" * 60)
        
        for item in hierarchy:
            path_str = " → ".join(item['path']) if item['path'] else "root"
            print(f"Line {item['line_number']}: {path_str} ({item['type']}) - {item['title']}")
            if 'pyxa_account' in item and 'pyxa_mailbox' in item:
                print(f"  └─ Account: {item['pyxa_account']}, Mailbox: {item['pyxa_mailbox']}")
        
        print("-" * 60)

    def print_account_omeclicks(self):
        """
        Print omeClick coordinates for account items to verify UI matching.
        """
        jsonl_items = self.extract_mailbox_items()
        accounts_data = self.get_pyxa_accounts_data()
        
        print(f"\n[MailNavTranslator] Account omeClick Coordinates:")
        print("-" * 50)
        
        for item in jsonl_items:
            data = item['data']
            title = data.get('AXTitle', '')
            omeClick = data.get('omeClick')
            
            # Check if this is an account item
            for account_name in accounts_data.keys():
                if account_name in title:
                    print(f"Account: {title}")
                    print(f"  omeClick: {omeClick}")
                    print(f"  Line: {item['line_number']}")
                    print()
                    break
        
        print("-" * 50)

    def _is_system_item(self, title: str) -> bool:
        """
        Check if an item is a system item.
        
        Args:
            title (str): The title to check
            
        Returns:
            bool: True if it's a system item
        """
        self._ensure_config_loaded()
        system_patterns = self.translator_config.get('system_patterns', [])
        return any(pattern in title for pattern in system_patterns)

    def _is_aggregate_item(self, title: str) -> bool:
        """
        Check if an item is an aggregate item.
        
        Args:
            title (str): The title to check
            
        Returns:
            bool: True if it's an aggregate item
        """
        self._ensure_config_loaded()
        aggregate_patterns = self.translator_config.get('aggregate_patterns', [])
        return any(pattern in title for pattern in aggregate_patterns)

    def _is_flag_item(self, title: str) -> bool:
        """
        Check if an item is a flag item.
        
        Args:
            title (str): The title to check
            
        Returns:
            bool: True if it's a flag item
        """
        self._ensure_config_loaded()
        flag_patterns = self.translator_config.get('flag_patterns', [])
        return any(pattern in title for pattern in flag_patterns)

    def _find_matching_mailbox(self, title: str, pyxa_mailboxes: list) -> str:
        """
        Find a matching mailbox name between JSONL and PyXA data.
        
        Args:
            title (str): The JSONL title
            pyxa_mailboxes (list): List of PyXA mailbox names
            
        Returns:
            str: The matching PyXA mailbox name, or None if no match
        """
        # Direct match
        if title in pyxa_mailboxes:
            return title
        
        # Common mappings
        mappings = {
            'Inbox': 'INBOX',
            'Junk': 'Spam',
            'Sent': 'Sent Mail',
            'Trash': 'Bin'
        }
        
        if title in mappings and mappings[title] in pyxa_mailboxes:
            return mappings[title]
        
        return None

    def load_translator_config(self):
        """
        Load translator configuration from JSONL file using canonical window_ref.
        """
        config_path = os.path.join(os.path.dirname(APPNAV_CONFIG_PATH), "mailNav_translator_config.jsonl")
        if not os.path.exists(config_path):
            print(f"[MailNavTranslator] Translator config not found: {config_path}")
            print(f"[MailNavTranslator] Using default empty config")
            self.translator_config = {}
            return
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                configs = [json.loads(line) for line in f if line.strip()]
            window_ref = self.get_canonical_window_ref()
            def get_config_for_context(configs, bundle_id, window_ref):
                for config in configs:
                    if config['bundle_id'] == bundle_id and config['window_ref'] == window_ref:
                        return config
                for config in configs:
                    if config['bundle_id'] == bundle_id and config['window_ref'] == '*':
                        return config
                for config in configs:
                    if config['bundle_id'] == '*' and config['window_ref'] == '*':
                        return config
                return {}
            self.translator_config = get_config_for_context(configs, self.bundle_id, window_ref)
            print(f"[MailNavTranslator] Loaded config for {self.bundle_id}/{window_ref}: {self.translator_config.get('translator_type', 'unknown')}")
        except Exception as e:
            print(f"[MailNavTranslator] Error loading translator config: {e}")
            print(f"[MailNavTranslator] Using default empty config")
            self.translator_config = {}

    def output_hierarchical_jsonl(self, output_filename: str = None):
        """
        Output the hierarchical structure to a JSONL file using canonical window_ref.
        """
        os.makedirs(TRANSLATOR_EXPORT_DIR, exist_ok=True)
        if not output_filename:
            window_ref = self.get_canonical_window_ref()
            output_filename = f"hierarchical_{self.bundle_id}_{window_ref}.jsonl"
        output_path = os.path.join(TRANSLATOR_EXPORT_DIR, output_filename)
        hierarchy = self.build_hierarchy_with_rules()
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                for item in hierarchy:
                    output_record = {
                        'path': item['path'],
                        'omeClick': item['omeClick'],
                        'title': item['title'],
                        'type': item['type'],
                        'line_number': item['line_number']
                    }
                    if 'pyxa_account' in item:
                        output_record['pyxa_account'] = item['pyxa_account']
                    if 'pyxa_mailbox' in item:
                        output_record['pyxa_mailbox'] = item['pyxa_mailbox']
                    if 'parent_system' in item:
                        output_record['parent_system'] = item['parent_system']
                    f.write(json.dumps(output_record) + '\n')
            print(f"[MailNavTranslator] Output {len(hierarchy)} items to: {output_path}")
            return output_path
        except Exception as e:
            print(f"[MailNavTranslator] Error writing output file: {e}")
            return None


def main():
    """
    Main function with command-line interface for the Mail Navigation Translator.
    """
    parser = argparse.ArgumentParser(
        description="Translate flat JSONL navigation data into hierarchical structure for Mail app automation.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python -m ome.controllers.mail.mailNav_translator --force
  python -m ome.controllers.mail.mailNav_translator --debug --output custom_hierarchy.jsonl
  python -m ome.controllers.mail.mailNav_translator --no-output
        """
    )
    
    parser.add_argument(
        '--bundle', 
        type=str, 
        default='com.apple.mail', 
        help='App bundle ID (default: com.apple.mail)'
    )
    parser.add_argument(
        '--force', 
        action='store_true', 
        help='Force overwrite of output file if it exists'
    )
    parser.add_argument(
        '--debug', 
        action='store_true', 
        help='Print detailed debugging information'
    )
    parser.add_argument(
        '--output', 
        type=str, 
        help='Custom output filename (optional, uses default naming if not specified)'
    )
    parser.add_argument(
        '--no-output', 
        action='store_true', 
        help='Don\'t write output file, just print results to console'
    )
    
    args = parser.parse_args()
    
    print(f"[MailNavTranslator] Starting translation for bundle: {args.bundle}")
    
    # Create translator instance
    translator = MailNavTranslator(args.bundle)
    
    # Check if input navigation file exists
    nav_file_path = translator.get_nav_file_path()
    if not nav_file_path or not os.path.exists(nav_file_path):
        print(f"[ERROR] Input navigation file not found: {nav_file_path}")
        print(f"[ERROR] Please run appNav_builder.py first to create the navigation data")
        sys.exit(1)
    
    print(f"[MailNavTranslator] Using input file: {nav_file_path}")
    
    # Get PyXA data first
    if args.debug:
        print("\n=== PYXA DATA ===")
        accounts_data = translator.get_pyxa_accounts_data()
        
        # Print account omeClick coordinates
        print("\n=== ACCOUNT OMECLICKS ===")
        translator.print_account_omeclicks()
    
    # Extract and print mailbox items
    if args.debug:
        print("\n=== JSONL DATA ===")
        translator.print_mailbox_items()
    
    # Build and print hierarchy with rules
    print("\n=== HIERARCHY WITH RULES ===")
    translator.print_hierarchy_with_rules()
    
    # Output the hierarchical JSONL
    if not args.no_output:
        print("\n=== OUTPUT HIERARCHICAL JSONL ===")
        output_path = translator.output_hierarchical_jsonl(args.output)
        
        if output_path:
            # Check if file exists and force flag
            if os.path.exists(output_path) and not args.force:
                print(f"[INFO] Output file already exists: {output_path}")
                print(f"[INFO] Use --force to overwrite or --no-output to skip file writing")
                sys.exit(0)
            
            print(f"[SUCCESS] Hierarchical navigation data written to: {output_path}")
        else:
            print(f"[ERROR] Failed to write output file")
            sys.exit(1)
    else:
        print("\n[INFO] Skipping file output (--no-output flag used)")
    
    print(f"[MailNavTranslator] Translation completed successfully")


if __name__ == "__main__":
    main()
