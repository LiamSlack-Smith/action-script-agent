"""
Incremental Linter Subsystem: Real-time validation of the Action Script stream.
"""
import ast
from typing import Iterator

class LinterError(Exception):
    "Custom exception for linter-detected errors."
    def __init__(self, message, code):
        super().__init__(message)
        self.code = code

class IncrementalLinter:
    def __init__(self, allowed_functions: list[str]):
        self.buffer = ""
        self.allowed_functions = set(allowed_functions)

    def validate_stream(self, token_stream: Iterator[str]) -> Iterator[str]:
        """
        Validates the token stream, checking for syntax errors and disallowed imports.

        Yields:
            str: The token if it's valid.

        Raises:
            LinterError: If a validation error is found.
        """
        self.buffer = ""
        for token in token_stream:
            self.buffer += token
            
            # Rule: No import statements
            if "import " in self.buffer.lstrip():
                raise LinterError("Disallowed 'import' statement found.", self.buffer)

            try:
                # Check if the current buffer is valid, partial Python code
                ast.parse(self.buffer)
                # If it parses, it's a complete statement. We could add more checks here.
                self._check_function_calls(self.buffer)

            except SyntaxError:
                # This is expected for incomplete code, so we continue buffering
                pass
            except LinterError as e:
                raise e # Re-raise our custom error
            except Exception as e:
                # Catch other potential parsing errors
                raise LinterError(f"AST parsing error: {e}", self.buffer)

            yield token
        
        # Final check on the complete script
        try:
            ast.parse(self.buffer)
            self._check_function_calls(self.buffer)
        except Exception as e:
            raise LinterError(f"Final validation failed: {e}", self.buffer)

    def _check_function_calls(self, code: str):
        """
        Parses the code with AST to find all function calls and check them against the allowlist.
        """
        try:
            tree = ast.parse(code)
            for node in ast.walk(tree):
                if isinstance(node, ast.Call):
                    if isinstance(node.func, ast.Name):
                        if node.func.id not in self.allowed_functions:
                            raise LinterError(f"Disallowed function call: {node.func.id}", code)
        except SyntaxError:
            # Ignore syntax errors as the code might be incomplete
            pass
