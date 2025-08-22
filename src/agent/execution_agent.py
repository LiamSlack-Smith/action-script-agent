"""
Execution Agent: The primary conversational and reasoning agent.
"""
from src.core.llm_interface import LLMInterface

class ExecutionAgent:
    def __init__(self, llm_interface: LLMInterface):
        self.llm_interface = llm_interface
    def generate_action_script(self, system_prompt: str):
        """
        Generates the Action Script by streaming the response from the LLM.

        Args:
            system_prompt: The fully constructed system prompt.

        Yields:
            str: A stream of tokens representing the Action Script.
        """
        print("--- EXECUTION AGENT: GENERATING SCRIPT ---")
        print(system_prompt)
        print("---------------------------------------------")

        # The linter will attach to this stream
        # Gemini API does not support the 'system' role. We use the 'user' role instead.
        response_stream = self.llm_interface.get_completion_stream(
            messages=[{"role": "user", "content": system_prompt}],
            model="gemini/gemini-2.5-flash-lite"
        )
        for part in response_stream:
            if content := part.choices[0].delta.content:
                yield content
