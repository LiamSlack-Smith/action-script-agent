"""
Vector Database: The system's long-term memory store.
"""
import faiss
import numpy as np
import uuid
import datetime

from src.utils.embedding import get_embedding

class VectorDB:
    def __init__(self, dimension: int = 384): # Dimension for 'all-MiniLM-L6-v2'
        self.dimension = dimension
        self.index = faiss.IndexFlatL2(dimension)
        self.memories = {}

    def add_memory(self, rich_memory_object: dict):
        """
        Adds a new rich memory object to the database.
        """
        content_text = rich_memory_object["content_text"]
        embedding = get_embedding(content_text)
        
        memory_id = str(uuid.uuid4())
        rich_memory_object["memory_id"] = memory_id
        rich_memory_object["content_embedding"] = embedding.tolist()
        rich_memory_object["creation_timestamp_utc"] = datetime.datetime.utcnow().isoformat() + "Z"

        # FAISS expects a 2D array
        embedding_np = np.array([embedding]).astype('float32')
        self.index.add(embedding_np)
        
        # Store the rich object, linking it by its index in FAISS
        self.memories[self.index.ntotal - 1] = rich_memory_object
        print(f"Added memory {memory_id} to VectorDB.")

    def search_memories(self, query: str, top_k: int) -> list[dict]:
        """
        Searches for the top_k most relevant memories.
        """
        if self.index.ntotal == 0:
            return []

        query_embedding = get_embedding(query)
        query_embedding_np = np.array([query_embedding]).astype('float32')

        distances, indices = self.index.search(query_embedding_np, top_k)

        results = []
        for i in indices[0]:
            if i != -1: # FAISS returns -1 for no result
                results.append(self.memories[i])
        
        return results
