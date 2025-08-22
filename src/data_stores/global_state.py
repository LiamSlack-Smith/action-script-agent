"""
Global State: Session-specific short-term working memory.
"""
import pprint

class GlobalState:
    def __init__(self):
        self._state = {}

    def get_state(self) -> dict:
        """Returns a copy of the current state."""
        return self._state.copy()

    def update_state(self, key: str, value):
        """Updates or adds a key-value pair to the state."""
        self._state[key] = value

    def delete_key(self, key: str) -> bool:
        """Deletes a key from the state. Returns True if successful, False otherwise."""
        if key in self._state:
            del self._state[key]
            return True
        return False

    def get_pretty_string(self) -> str:
        """Returns a pretty-printed string representation of the state."""
        if not self._state:
            return "{}\n# The global_state is currently empty."
        return pprint.pformat(self._state, indent=2)
