"""
Execution Agent: The primary conversational and reasoning agent.
"""
from src.core.llm_interface import LLMInterface

class ExecutionAgent:
    def __init__(self, llm_interface: LLMInterface):
        self.llm_interface = llm_interface
    def generate_action_script(self, messages: list[dict]):
        """
        Generates the Action Script by streaming the response from the LLM.

        Args:
            messages: The full conversational history including few-shot examples.

        Yields:
            str: A stream of tokens representing the Action Script.
        """
        print("--- EXECUTION AGENT: GENERATING SCRIPT (with few-shot examples) ---")
        # The last message is the current prompt, which is very long. We'll just print a confirmation.
        # print(messages[-1]['content'])
        print("---------------------------------------------------------------------")

        response_stream = self.llm_interface.get_completion_stream(
            messages=messages,
            model="gemini/gemini-2.5-flash"
        )
        for part in response_stream:
            if content := part.choices[0].delta.content:
                yield content
