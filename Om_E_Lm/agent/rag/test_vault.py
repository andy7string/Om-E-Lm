import os
import sys

# Adjust path to include the project root
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

from Om_E_Lm.agent.rag.vault import Vault

def run_test():
    """Tests the Vault functionality."""
    print("--- Running Vault Test ---")
    
    # 1. Initialize Vault
    vault = Vault()
    print(f"Vault file path: {vault.vault_path}")

    # 2. Clear any previous test data
    print("\nClearing vault...")
    vault.delete_all_entries()
    
    # 3. Add entries
    print("\nAdding entries...")
    vault.add_entry("First test entry.")
    vault.add_entry("This is the second entry.")
    vault.add_entry("  And a third one with leading spaces.  ")
    print("Entries added.")
    
    # 4. Read and verify entries
    print("\nReading all entries:")
    entries = vault.get_all_entries()
    assert len(entries) == 3
    assert entries[0] == "First test entry."
    assert entries[1] == "This is the second entry."
    assert entries[2] == "And a third one with leading spaces."
    for i, entry in enumerate(entries, 1):
        print(f"{i}: {entry}")
    
    # 5. Delete all entries
    print("\nDeleting all entries...")
    vault.delete_all_entries()
    
    # 6. Verify vault is empty
    print("\nVerifying vault is empty:")
    entries = vault.get_all_entries()
    assert len(entries) == 0
    print("Vault is empty as expected.")
    
    print("\n--- Vault Test Passed ---")

if __name__ == "__main__":
    run_test() 