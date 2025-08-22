"""
Incremental Linter: Validates the Action Script token by token as it's generated.
"""

class LinterError(Exception):
    """Custom exception for linter errors."""
    def __init__(self, message, code=""):
        super().__init__(message)
        self.code = code

class IncrementalLinter:
    def __init__(self, allowed_functions: list[str]):
        self.allowed_functions = set(allowed_functions)
        self.disallowed_keywords = {'import', 'open', 'eval', 'exec'}
        
        # State machine variables
        self.is_validating = False
        self.trigger_phrase = "# Your Action Script:"
        self.buffer = ""

    def _check_for_disallowed_keywords(self, code_line: str):
        """Checks a line of code for disallowed keywords."""
        # A simple check to avoid flagging keywords in comments or strings
        clean_line = code_line.split('#')[0].strip()
        if not clean_line:
            return

        for keyword in self.disallowed_keywords:
            # Use a simple word boundary check to avoid matching substrings
            if f' {keyword} ' in f' {clean_line} ' or clean_line.startswith(keyword):
                raise LinterError(f"Disallowed '{keyword}' statement found.", code=code_line)

    def validate_stream(self, token_stream):
        """
        A stateful generator that validates a stream of tokens.
        It ignores all tokens until it sees the trigger phrase, then validates thereafter.
        """
        for token in token_stream:
            self.buffer += token
            yield token

            # Process the buffer line by line
            while '\n' in self.buffer:
                line, self.buffer = self.buffer.split('\n', 1)
                
                if not self.is_validating:
                    if self.trigger_phrase in line:
                        self.is_validating = True
                else:
                    # Once validating, check every subsequent line
                    self._check_for_disallowed_keywords(line)

        # After the stream is exhausted, check any remaining content in the buffer
        if self.is_validating and self.buffer:
            self._check_for_disallowed_keywords(self.buffer)
