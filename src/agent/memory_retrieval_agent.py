"""
Memory Retrieval Agent: Retrieves relevant long-term memories to provide context for the current task.
"""
from src.data_stores.vector_db import VectorDB

class MemoryRetrievalAgent:
    def __init__(self, vector_db: VectorDB):
        self.vector_db = vector_db

    def retrieve_memories(self, query: str, top_k: int = 3) -> list[dict]:
        """
        Embeds the user query and queries the Vector Database for relevant memories.

        Args:
            query: The user's query.
            top_k: The number of memories to retrieve.

        Returns:
            A list of relevant rich memory objects.
        """
        print(f"--- MEMORY RETRIEVAL: Searching for memories related to: '{query}' ---")
        retrieved = self.vector_db.search_memories(query, top_k)
        if retrieved:
            print(f"--- MEMORY RETRIEVAL: Found {len(retrieved)} relevant memories. ---")
        else:
            print("--- MEMORY RETRIEVAL: No relevant memories found. ---")
        return retrieved
