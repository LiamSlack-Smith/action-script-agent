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
from src.tools.tool_definitions import load_tools, get_tool_signatures, load_core_tools_for_prompt
from src.core.action_script_execution_environment import ActionScriptExecutionEnvironment, ScriptExecutionError

class AgentController:
    def __init__(self):
        self.llm_interface = LLMInterface()
        self.vector_db = VectorDB()
        self.global_state = GlobalState()
        
        self.memory_retrieval_agent = MemoryRetrievalAgent(self.vector_db)
        self.execution_agent = ExecutionAgent(self.llm_interface)
        self.memory_consolidation_agent = MemoryConsolidationAgent(self.llm_interface, self.vector_db)
        
        # Restore full tool loading for prompt consistency
        self.tools = load_tools()
        core_tools_for_prompt = load_core_tools_for_prompt()
        all_tools_for_prompt = {**self.tools, **core_tools_for_prompt}
        self.tool_signatures = get_tool_signatures(all_tools_for_prompt)
        
        core_funcs_map = self._get_core_functions()
        
        self.linter = IncrementalLinter(allowed_functions=list(all_tools_for_prompt.keys()))
        self.execution_environment = ActionScriptExecutionEnvironment(self.global_state, self.tools, core_funcs_map)
        
        self.conversation_id = str(uuid.uuid4())
        self.conversation_history = ""
        # Restore few-shot examples
        self.few_shot_examples = self._get_few_shot_examples()

        self._inject_initial_state()

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

# Rules
1.  Your response MUST be ONLY a Python script. Do not add any commentary, explanations, or markdown formatting.
2.  The script must end by calling either `respond(response: str)` to give the final answer to the user, or `continue_turn()` to continue the thought process in the next turn.
3.  You can use the `reflect(analysis: str)` function at the start of your script to analyze the situation and plan your steps.
4.  When using the `write_file` tool, you MUST use triple quotes (\"\"\") for the `file_content` argument to prevent syntax errors with nested quotes.
5.  Do not use any Python features that are not provided (e.g., `import`, defining classes, etc.). Only call the provided tools and core functions.

# User Query
{user_query}

# Long-Term Memories
Here are some memories from past interactions that might be relevant:
{memories_str}

# Current State (Short-Term Memory)
This dictionary contains the results of all tools executed in the current session. It is read-only from your script's perspective.
{state_str}

# Available Tools
{self.tool_signatures}

# Your Action Script:
"""
    def run(self, initial_query: str):
        print(f"--- NEW SESSION: {self.conversation_id} ---")
        
        retrieved_memories = self.memory_retrieval_agent.retrieve_memories(initial_query)
        system_prompt = self._construct_system_prompt(initial_query, retrieved_memories)
        
        # Restore few-shot examples to the message history
        messages = self.few_shot_examples + [{"role": "user", "content": system_prompt}]

        turn_in_progress = True
        while turn_in_progress:
            correction_attempts = 0
            max_correction_attempts = 3
            
            while correction_attempts < max_correction_attempts:
                action_script = ""
                try:
                    script_stream = self.execution_agent.generate_action_script(messages)
                    
                    print("--- AGENT STREAMING SCRIPT ---")
                    action_script_parts = []
                    validated_stream = self.linter.validate_stream(script_stream)
                    for token in validated_stream:
                        print(token, end="", flush=True)
                        action_script_parts.append(token)
                    action_script = "".join(action_script_parts)
                    print("\n-------------------------------")

                    messages.append({"role": "assistant", "content": action_script})

                    self.execution_environment.execute_script(action_script)
                    
                    messages.pop()
                    raise ScriptExecutionError("Script completed without calling respond() or continue_turn().")

                except LinterError as e:
                    correction_attempts += 1
                    print(f"\n--- LINTER ERROR (Attempt {correction_attempts}) ---")
                    # Error handling logic here...
                    messages.append({"role": "user", "content": f"Your last script failed with a syntax error: {e}. Please provide a corrected script."})
                    continue
                
                except ScriptExecutionError as e:
                    correction_attempts += 1
                    if messages and messages[-1]["role"] == "assistant":
                        messages.pop()
                    print(f"\n--- SCRIPT EXECUTION ERROR (Attempt {correction_attempts}) ---")
                    # Error handling logic here...
                    messages.append({"role": "user", "content": f"Your last script failed during execution: {e}. Please analyze the error and provide a corrected script."})
                    continue

                except core_functions.RespondException as e:
                    print(f"--- FINAL RESPONSE TO USER ---\n{e.message}\n------------------------------")
                    self.conversation_history += f"User: {initial_query}\nAgent: {e.message}"
                    self.memory_consolidation_agent.consolidate_memory(self.conversation_history, self.conversation_id)
                    turn_in_progress = False
                    break

                except core_functions.ContinueTurnException:
                    print("--- CONTINUING TURN ---")
                    self.conversation_history += f"User: {initial_query}\nAgent: [Internal State Update]"
                    retrieved_memories = self.memory_retrieval_agent.retrieve_memories(initial_query)
                    system_prompt = self._construct_system_prompt(initial_query, retrieved_memories)
                    messages.append({"role": "user", "content": system_prompt})
                    break
            
            if correction_attempts >= max_correction_attempts:
                print("Max correction attempts reached. Aborting.")
                turn_in_progress = False
    def _inject_initial_state(self):
        """Injects initial, helpful information into the global state."""
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
    def _get_few_shot_examples(self) -> list[dict]:
        """Returns a list of few-shot examples for the agent."""
        return [
            {
                "role": "user",
                "content": "Your task is to find out the current weather in London."
            },
            {
                "role": "assistant",
                "content": "reflect(\"The user wants the weather in London. I will use the `search_web` tool for this and respond directly.\")\nsearch_web(query=\"current weather in London\")\nrespond(\"The weather in London is currently sunny with a high of 22C.\")"
            },
            {
                "role": "user",
                "content": "Your task is to read the `README.md` file and then write a summary of it to a new file called `summary.txt`."
            },
            {
                "role": "assistant",
                "content": "reflect(\"This is a complex, multi-step task. First, I need to read the `README.md` file. Then, in the next turn, I will process its content and write the summary. Step 1: Read the file.\")\nread_files(relative_file_paths=[\"README.md\"])\ncontinue_turn()"
            },
            {
                "role": "user",
                "content": "Your task is to create a file named `hello.txt` with the content `Hello, World!`."
            },
            {
                "role": "assistant",
                "content": "reflect(\"The user wants to create a new file with specific content. I will use the `write_file` tool. To avoid issues with quotes inside the content, I will use triple quotes for the `file_content` argument.\")\nwrite_file(relative_file_path=\"hello.txt\", file_content=\"\"\"Hello, World!\"\"\")\nrespond(\"I have successfully created the file `hello.txt`.\")"
            }
        ]

if __name__ == "__main__":
    controller = AgentController()
    controller.run("Summarise the current project.")
