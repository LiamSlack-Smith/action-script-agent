"""
Action Script Execution Environment: Executes Python scripts from the Execution Agent.
"""
import datetime
import uuid
from typing import Any, Callable

from src.data_stores.global_state import GlobalState
from src.tools.core_functions import ControlFlowException

class ScriptExecutionError(Exception):
    """Custom exception for errors that occur during script execution."""
    pass

class ActionScriptExecutionEnvironment:
    def __init__(self, global_state: GlobalState, tools: dict[str, Callable], core_functions: dict[str, Callable]):
        self.global_state = global_state
        self.execution_scope = self._create_execution_scope(tools, core_functions)

    def _create_execution_scope(self, tools: dict, core_functions: dict) -> dict[str, Any]:
        """
        Prepares the global scope for the exec() environment.
        """
        scope = {}
        scope.update(tools)
        scope.update(core_functions)
        return scope

    def execute_script(self, script: str):
        """
        Executes the provided Action Script and manages state updates.

        Args:
            script (str): The Python script to execute.
        
        Raises:
            ScriptExecutionError: If any exception occurs during script execution.
            ControlFlowException: If a control flow signal is raised.
        """
        wrapped_scope = self.execution_scope.copy()
        for name, func in self.execution_scope.items():
            if callable(func):
                wrapped_scope[name] = self._wrap_tool_call(name, func)

        try:
            exec(script, wrapped_scope)
        except ControlFlowException:
            # This is a signal for the main loop (e.g., respond, continue_turn). Re-raise it.
            raise
        except Exception as e:
            # This is a genuine execution error. Wrap it in our custom exception.
            raise ScriptExecutionError(f"Script execution failed with error: {e}") from e

    def _wrap_tool_call(self, tool_name: str, func: Callable) -> Callable:
        """
        A wrapper to automatically update global_state with a tool's result.
        """
        def wrapper(*args, **kwargs):
            result = func(*args, **kwargs)
            
            if result is not None:
                turn_id = str(uuid.uuid4())
                timestamp = datetime.datetime.utcnow().isoformat() + "Z"
                
                state_entry = {
                    "result": result,
                    "metadata": {
                        "timestamp_utc": timestamp,
                        "turn_id": turn_id
                    }
                }
                self.global_state.update_state(tool_name, state_entry)
                print(f"\n--- GLOBAL STATE UPDATED for '{tool_name}' ---")
            return result
        return wrapper
