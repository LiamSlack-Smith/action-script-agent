"""
Utility for generating sentence embeddings.
"""
from sentence_transformers import SentenceTransformer
import numpy as np

# Load the model only once
model = SentenceTransformer('all-MiniLM-L6-v2')

def get_embedding(text: str) -> np.ndarray:
    """Generates an embedding for the given text."""
    return model.encode(text)
