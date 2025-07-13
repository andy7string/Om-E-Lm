import PyXA

# Connect to Apple Mail
mail = PyXA.Mail()

# List all accounts and their mailboxes
accounts = mail.accounts()
print("Accounts and their Mailboxes in Apple Mail:")
for account in accounts:
    print(f"- {account.name}")
    mailboxes = account.mailboxes()
    for mbox in mailboxes:
        print(f"    - {mbox.name}") 