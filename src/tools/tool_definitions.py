"""
Placeholder for user-defined and system tools.
"""
import inspect, os
from typing import List
from src.tools import core_functions
from src.tools.ast_tools import find_function_definitions, find_class_definitions, find_imports
def search_web(query: str) -> dict:
    """Searches the web for a given query and returns the top results.

    Returns:
        dict: A dictionary with a 'results' key containing a list of search results.
              Each result is a dictionary with 'title' and 'url' keys.
              Example: {'results': [{'title': 'Paris - Wikipedia', 'url': 'http://example.com/paris'}]}
    """
    print(f"--- TOOL: Simulating web search for: {query} ---")
    # Simulate a more realistic result for the query
    if "capital of france" in query.lower():
        return {
            "results": [
                {"title": "Paris - Wikipedia", "url": "http://example.com/paris"},
                {"title": "What is the capital of France?", "url": "http://example.com/france-capital"}
            ]
        }
    return {
        "results": [
            {"title": "Example Result 1", "url": "http://example.com/1"},
            {"title": "Example Result 2", "url": "http://example.com/2"}
        ]
    }
def load_tools() -> dict:
    """Loads all available tools."""
    return {
        "read_files": read_files,
        "write_file": write_file,
        "list_files": list_files,
        "search_web": search_web,
        "find_function_definitions": find_function_definitions,
        "find_class_definitions": find_class_definitions,
        "find_imports": find_imports,
    }
def get_tool_signatures(tools: dict) -> str:
    """
    Generates a string containing the function signatures and docstrings for all tools.
    """
    signatures = "\n# --- Available Tools ---\n"
    for name, func in tools.items():
        try:
            sig = inspect.signature(func)
            doc = inspect.getdoc(func)
            # The full docstring now includes the schema, which is critical for the agent.
            signatures += f"def {name}{sig}:\n    \"\"\"{doc}\"\"\"\n\n"
        except Exception:
            signatures += f"# Could not generate signature for tool: {name}\n"
    return signatures
def read_files(file_paths: List[str]) -> dict:
    """Reads the content of one or more files.

    Args:
        file_paths: A list of relative paths to the files to be read.

    Returns:
        dict: A dictionary where keys are the file paths and values are either the
              file content or an error message if the file could not be read.
    """
    results = {}
    for path in file_paths:
        try:
            with open(path, 'r', encoding='utf-8') as f:
                results[path] = f.read()
        except Exception as e:
            results[path] = f"Error reading file: {e}"
    return results
def write_file(file_path: str, content: str) -> dict:
    """Writes content to a specific file, creating directories if necessary.

    Args:
        file_path: The relative path to the file to be written.
        content: The content to write to the file.

    Returns:
        dict: A dictionary containing a status message.
    """
    try:
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        return {"status": f"Successfully wrote to {file_path}"}
    except Exception as e:
        return {"status": f"Error writing to file: {e}"}
def load_core_tools_for_prompt() -> dict:
    """Returns a dictionary of core functions for prompt generation.

    This provides the raw functions so their signatures can be inspected.
    """
    return {
        "respond": core_functions.respond,
        "continue_turn": core_functions.continue_turn,
        "reflect": core_functions.reflect,
        "delete_state_key": core_functions.delete_state_key,
        "summarize_state": core_functions.summarize_state,
    }
