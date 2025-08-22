"""
Main entrypoint for the Autonomous Agentic Framework.
"""
import os, uuid
import functools

from src.agent.execution_agent import ExecutionAgent
from src.agent.memory_consolidation_agent import MemoryConsolidationAgent
from src.agent.memory_retrieval_agent import MemoryRetrievalAgent
from src.core.incremental_linter import IncrementalLinter, LinterError
from src.core.llm_interface import LLMInterface
from src.data_stores.global_state import GlobalState
from src.data_stores.vector_db import VectorDB
from src.tools import core_functions
from src.core.action_script_execution_environment import ActionScriptExecutionEnvironment, ScriptExecutionError
from src.tools.tool_definitions import load_tools, get_tool_signatures, load_core_tools_for_prompt

class AgentController:
    def __init__(self):
        self.llm_interface = LLMInterface()
        self.vector_db = VectorDB()
        self.global_state = GlobalState()
        
        self.memory_retrieval_agent = MemoryRetrievalAgent(self.vector_db)
        self.execution_agent = ExecutionAgent(self.llm_interface)
        self.memory_consolidation_agent = MemoryConsolidationAgent(self.llm_interface, self.vector_db)
        
        self.tools = load_tools()
        core_tools_for_prompt = load_core_tools_for_prompt()
        all_tools_for_prompt = {**self.tools, **core_tools_for_prompt}
        self.tool_signatures = get_tool_signatures(all_tools_for_prompt)
        
        core_funcs_map = self._get_core_functions()
        
        self.linter = IncrementalLinter(allowed_functions=list(all_tools_for_prompt.keys()))
        
        self.execution_environment = ActionScriptExecutionEnvironment(self.global_state, self.tools, core_funcs_map)
        
        self.conversation_id = str(uuid.uuid4())
        self.conversation_history = ""

        self._inject_initial_state()
        print(f"--- NEW SESSION STARTED: {self.conversation_id} ---")

    def _get_core_functions(self):
        "Binds instance methods to the core function definitions." 
        return {
            "respond": core_functions.respond,
            "continue_turn": core_functions.continue_turn,
            "reflect": core_functions.reflect,
            "delete_state_key": functools.partial(core_functions.delete_state_key, self.global_state),
            "summarize_state": functools.partial(core_functions.summarize_state, self.global_state, self.llm_interface)
        }
    def _construct_system_prompt(self, user_query: str, retrieved_memories: list) -> str:
        memories_str = "\n".join([mem['content_text'] for mem in retrieved_memories]) if retrieved_memories else "No relevant memories found."
        state_str = self.global_state.get_pretty_string()
        
        return f"""# System Instructions
Your task is to act as an autonomous agent. Your primary goal is to address the user's request by generating a Python script (called an Action Script).

# Reasoning Process
1.  **Analyze Context**: First, carefully review the `Long-Term Memories` and `Current State` sections.
2.  **Check for Existing Answers**: If the information needed is already present, respond directly. Do not use tools if you already know the answer.
3.  **Assess Complexity**: Determine if the user's request is simple (can be solved in one step) or complex (requires multiple steps, like reading a file, modifying it, and then writing it).
4.  **Formulate a Plan**: 
    *   For **simple** tasks, outline your single step in the `reflect()` block and execute it.
    *   For **complex** tasks, create a step-by-step plan in your `reflect()` block. **Execute only the first step of your plan**, and then end your script with `continue_turn()`. This allows you to see the result of the first step in the `Current State` on your next turn before proceeding.

# Rules
1.  Your response MUST be ONLY a Python script. Do not add any commentary, explanations, or markdown formatting.
2.  **CRITICAL RULE**: You MUST end every script with a call to `respond(response: str)` or `continue_turn()`.
3.  Use `reflect(analysis: str)` at the start of your script to explain your plan.
4.  Do not use any Python features that are not provided (e.g., `import`).

# User Query
{user_query}

# Long-Term Memories
{memories_str}

# Current State (Short-Term Memory)
{state_str}

# Available Tools
{self.tool_signatures}

# Your Action Script:
"""
    def run(self, user_query: str):
        turn_in_progress = True
        while turn_in_progress:
            # 1. Memory Retrieval & Prompt Construction
            retrieved_memories = self.memory_retrieval_agent.retrieve_memories(user_query)
            system_prompt = self._construct_system_prompt(user_query, retrieved_memories)
            
            # 2. Correction Loop (Generation + Validation + Execution)
            correction_attempts = 0
            max_correction_attempts = 3
            
            while correction_attempts < max_correction_attempts:
                action_script = ""
                try:
                    # 3a. Action Script Generation & Validation
                    script_stream = self.execution_agent.generate_action_script(system_prompt)
                    validated_stream = self.linter.validate_stream(script_stream)
                    
                    # 3b. Stream output to terminal
                    print("--- AGENT STREAMING SCRIPT ---")
                    action_script_parts = []
                    for token in validated_stream:
                        print(token, end="", flush=True)
                        action_script_parts.append(token)
                    action_script = "".join(action_script_parts)
                    print("\n-------------------------------")

                    # 4. Script Execution
                    self.execution_environment.execute_script(action_script)
                    
                    raise ScriptExecutionError("Script completed without calling respond() or continue_turn(). You must end every script with one of these functions.")

                except LinterError as e:
                    correction_attempts += 1
                    print(f"\n--- LINTER ERROR (Attempt {correction_attempts}) ---")
                    print(f"Error: {e}")
                    print(f"Faulty Code:\n{e.code}")
                    print("---------------------------------")
                    system_prompt += f"\n# Previous Attempt Failed (Linter)\nYour last script failed with a syntax or validation error: {e}. The faulty code was:\n```python\n{e.code}```\nPlease provide a corrected script."
                    continue
                
                except ScriptExecutionError as e:
                    correction_attempts += 1
                    print(f"\n--- SCRIPT EXECUTION ERROR (Attempt {correction_attempts}) ---")
                    print(f"Error: {e}")
                    print(f"Faulty Script:\n{action_script}")
                    print("---------------------------------")
                    system_prompt += f"\n# Previous Attempt Failed (Execution)\nYour last script failed during execution with the error: {e}. The full script was:\n```python\n{action_script}```\nPlease analyze the error and the script, and provide a corrected version."
                    continue

                except core_functions.RespondException as e:
                    print(f"--- FINAL RESPONSE TO USER ---\n{e.message}\n------------------------------")
                    self.conversation_history += f"User: {user_query}\nAgent: {e.message}"
                    self.memory_consolidation_agent.consolidate_memory(self.conversation_history, self.conversation_id)
                    turn_in_progress = False
                    break

                except core_functions.ContinueTurnException:
                    print("--- CONTINUING TURN ---")
                    self.conversation_history += f"User: {user_query}\nAgent: [Internal State Update]"
                    break 
            
            if correction_attempts >= max_correction_attempts:
                print("Max correction attempts reached. Aborting.")
                turn_in_progress = False
    def _inject_initial_state(self):
        """Injects initial, helpful information into the global state."""
        # Inject the project file list
        project_files = []
        ignore_dirs = {'.git', '__pycache__', '.idea', '.vscode'}
        for root, dirs, files in os.walk('.'):
            dirs[:] = [d for d in dirs if d not in ignore_dirs]
            for name in files:
                project_files.append(os.path.join(root, name).replace('\\', '/'))
        
        file_list_str = "\n".join(project_files)
        self.global_state.update_state(
            "project_file_list",
            {
                "result": f"The following files exist in the project:\n{file_list_str}",
                "metadata": {
                    "source": "system_initialization"
                }
            }
        )

if __name__ == "__main__":
    controller = AgentController()
    controller.run("Use the web search tool to find out what the capital of France is, then respond with the answer.")
if __name__ == "__main__":
    controller = AgentController()
    while True:
        try:
            user_input = input("\nEnter your command (or 'exit' to quit): ")
            if user_input.lower() in ["exit", "quit"]:
                print("Exiting session. Goodbye!")
                break
            if user_input:
                controller.run(user_input)
        except KeyboardInterrupt:
            print("\nExiting session. Goodbye!")
            break
