#!/usr/bin/env python3
"""
Script to print all mailboxes using MailController
"""

from ome.controllers.mail.mail_controller import MailController

def main():
    print("=== Mail Mailboxes List ===")
    
    # Initialize the mail controller
    mail_controller = MailController()
    
    # Get current context to see if app initialized
    context = mail_controller.get_current_context()
    
    if not context['app_initialized']:
        print("❌ Failed to initialize Mail app")
        return
    
    print(f"✅ Mail app initialized successfully")
    print(f"📧 Available accounts: {len(context['available_accounts'])}")
    
    # Get all accounts data
    accounts_data = mail_controller.get_accounts_data()
    
    if not accounts_data:
        print("❌ No accounts found")
        return
    
    print("\n📋 All Mailboxes by Account:")
    print("=" * 50)
    
    for account_name, account_info in accounts_data.items():
        print(f"\n🏠 Account: {account_name}")
        print(f"   📁 Mailboxes ({account_info['mailbox_count']}):")
        
        if account_info['mailboxes']:
            for i, mailbox_name in enumerate(account_info['mailboxes'], 1):
                print(f"   {i:2d}. {mailbox_name}")
        else:
            print("   (No mailboxes found)")
    
    print("\n" + "=" * 50)
    print(f"📊 Summary: {len(accounts_data)} accounts, {sum(acc['mailbox_count'] for acc in accounts_data.values())} total mailboxes")

if __name__ == "__main__":
    main() 