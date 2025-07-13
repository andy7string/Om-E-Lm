"""
DeepSeekAgent: Handles prompt construction, LLM calls, and JSONL streaming for Om‑E automation.
"""

class DeepSeekAgent:
    def __init__(self, model: str = "deepseek-r1:1.5b"):
        self.model = model

    def run(self, prompt: str, context: dict) -> None:
        """Send prompt + context to DeepSeek and stream JSONL output."""
        pass
