"""
ContextBuilder: Loads and prunes context from project files for the agent.
"""

class ContextBuilder:
    def __init__(self, data_dir: str):
        self.data_dir = data_dir

    def build_context(self) -> dict:
        """Load and prune context for the agent prompt."""
        return {}
