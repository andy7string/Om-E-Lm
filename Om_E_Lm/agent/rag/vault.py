import os

class Vault:
    """
    Manages the persistent text storage (the "vault") for the agent.
    """
    def __init__(self, vault_path: str = None):
        """
        Initializes the Vault.
        """
        if vault_path:
            self.vault_path = vault_path
        else:
            # Construct a robust path from this file's location
            script_dir = os.path.dirname(os.path.realpath(__file__))
            self.vault_path = os.path.join(script_dir, '../../data/vault/vault.txt')
            self.vault_path = os.path.normpath(self.vault_path)
        
        os.makedirs(os.path.dirname(self.vault_path), exist_ok=True)

    def add_entry(self, text: str) -> bool:
        """Appends a new text entry to the vault file."""
        try:
            with open(self.vault_path, 'a', encoding='utf-8') as f:
                f.write(text.strip() + '\n')
            return True
        except Exception as e:
            print(f"🔴 [Vault Error] Failed to add entry: {e}")
            return False

    def get_all_entries(self) -> list[str]:
        """Retrieves all entries from the vault file."""
        if not os.path.exists(self.vault_path):
            return []
        try:
            with open(self.vault_path, 'r', encoding='utf-8') as f:
                return [line.strip() for line in f if line.strip()]
        except Exception as e:
            print(f"🔴 [Vault Error] Failed to read entries: {e}")
            return []

    def delete_all_entries(self) -> bool:
        """Deletes all content from the vault file."""
        try:
            with open(self.vault_path, 'w', encoding='utf-8') as f:
                pass
            return True
        except Exception as e:
            print(f"🔴 [Vault Error] Failed to delete entries: {e}")
            return False 