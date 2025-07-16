"""
Om_E_Lm/ome/utils/rag_manager.py

RAG Manager for OM‑E Voice Assistant.
- Loads voice vault (voice.jsonl)
- Provides keyword-based retrieval (v1)
- CLI for testing
- Scaffolded for future embedding/FAISS support
"""
import json
import os
from env import OME_VAULT_VOICE_PATH

class RAGManager:
    def __init__(self, vault_path=OME_VAULT_VOICE_PATH):
        self.vault_path = vault_path
        self.entries = self._load_vault()

    def _load_vault(self):
        entries = []
        if os.path.exists(self.vault_path):
            with open(self.vault_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line:
                        try:
                            entries.append(json.loads(line))
                        except Exception as e:
                            print(f"[RAGManager] Skipping invalid line: {e}")
        return entries

    def retrieve_context(self, query_text, top_k=3):
        """
        Returns top-K most relevant vault entries for the query (keyword match).
        """
        query = query_text.lower()
        scored = []
        for entry in self.entries:
            text = entry.get('text', '').lower()
            score = sum(1 for word in query.split() if word in text)
            if score > 0:
                scored.append((score, entry))
        scored.sort(reverse=True, key=lambda x: x[0])
        return [entry for score, entry in scored[:top_k]]

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Test RAG keyword retrieval from voice vault.")
    parser.add_argument('--query', type=str, required=True, help='Query text to search vault')
    parser.add_argument('--top_k', type=int, default=3, help='Number of top matches to return')
    args = parser.parse_args()
    rag = RAGManager()
    results = rag.retrieve_context(args.query, top_k=args.top_k)
    print(f"Top {args.top_k} results for query: '{args.query}'\n")
    for i, entry in enumerate(results, 1):
        print(f"[{i}] {entry['text']} (id: {entry['id']})") 