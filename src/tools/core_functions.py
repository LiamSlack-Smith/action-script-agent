"""
Core API and Function Signatures injected into the Action Script's scope.
"""

class ControlFlowException(Exception):
    """Base exception for control flow signals."""
    pass

class RespondException(ControlFlowException):
    """Raised to signal a final response to the user."""
    def __init__(self, message):
        self.message = message

class ContinueTurnException(ControlFlowException):
    """Raised to signal the end of the current script and the start of a new turn."""
    pass

def respond(response: str) -> None:
    """Terminates the agent's turn and sends the final response string to the user."""
    raise RespondException(response)

def continue_turn() -> None:
    """Terminates the current script execution and immediately triggers a new agent turn."""
    raise ContinueTurnException()

def reflect(analysis: str) -> None:
    """Logs the agent's self-assessment of the previous turn's actions."""
    # In a real system, this would write to a structured log or monitoring system.
    print(f"--- AGENT REFLECTION ---\n{analysis}\n------------------------")

# These are state management tools but are core to the agent's operation
def delete_state_key(global_state_instance, key: str) -> bool:
    """Removes a top-level key from the global_state dictionary."""
    return global_state_instance.delete_key(key)

def summarize_state(global_state_instance, llm_interface_instance) -> str:
    """Invokes an LLM call to create a concise summary of the global_state."""
    state_str = global_state_instance.get_pretty_string()
    prompt = f"Please provide a concise, natural language summary of the following state dictionary:\n\n{state_str}"
    summary = llm_interface_instance.get_completion(
        messages=[{"role": "user", "content": prompt}],
        model="gemini/gemini-2.5-flash-lite"
    )
    return summary
