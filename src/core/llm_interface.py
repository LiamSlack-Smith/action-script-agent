"""
LLM Interface: Manages all interactions with the language model via litellm.
"""
import os
import litellm
from dotenv import load_dotenv

class LLMInterface:
    def __init__(self):
        load_dotenv()
        self.api_key = os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY not found in .env file")
        litellm.api_key = self.api_key

    def get_completion_stream(self, messages: list[dict], model: str):
        """
        Gets a streaming completion from the specified model.

        Args:
            messages: A list of messages in the conversation.
            model: The model to use (e.g., 'gemini/gemini-2.5-flash-lite').

        Returns:
            A litellm streaming response object.
        """
        return litellm.completion(
            model=model,
            messages=messages,
            stream=True
        )

    def get_completion(self, messages: list[dict], model: str) -> str:
        """
        Gets a single, non-streaming completion.
        """
        response = litellm.completion(
            model=model,
            messages=messages
        )
        return response.choices[0].message.content
