import os
import logging
import numpy as np
from typing import List, Optional
from google import genai
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

class BaseEmbedder:
    """
    Abstract interface for embedding models.
    NovaDB is agnostic to the underlying model.
    """
    def encode(self, text: str) -> np.ndarray:
        raise NotImplementedError
        
    def encode_batch(self, texts: List[str]) -> List[np.ndarray]:
        raise NotImplementedError
    
    @property
    def dims(self) -> Optional[int]:
        return None

class LocalEmbedder(BaseEmbedder):
    """
    Local embedder using sentence-transformers.
    No external dependencies, fully offline.
    Model: all-MiniLM-L6-v2 (384 dims)
    RAM: ~500 MB
    """
    
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        try:
            from sentence_transformers import SentenceTransformer
            self.model = SentenceTransformer(model_name)
            self._dims = 384
            logger.info("LocalEmbedder initialized with model: %s", model_name)
        except ImportError:
            logger.error("sentence-transformers not installed. Run: pip install sentence-transformers")
            raise ImportError("sentence-transformers required for LocalEmbedder")
    
    @property
    def dims(self) -> int:
        return self._dims
    
    def encode(self, text: str) -> np.ndarray:
        """Encode single text to vector."""
        return self.model.encode(text, convert_to_numpy=True)
    
    def encode_batch(self, texts: List[str]) -> List[np.ndarray]:
        """Encode batch of texts."""
        embeddings = self.model.encode(texts, convert_to_numpy=True)
        return [emb for emb in embeddings]

class GeminiEmbedder(BaseEmbedder):
    """
    Embedder implementation using Google Gemini (with the new google-genai SDK).
    Generates 768-dimensional vectors.
    Requires environment variable: GEMINI_API_KEY
    """
    def __init__(self, model_name: str = 'gemini-embedding-001'):
        self.model_name = model_name
        api_key = os.environ.get("GEMINI_API_KEY")
        
        if not api_key:
            raise ValueError("GEMINI_API_KEY fallback trigger")
            
        self.client = genai.Client(api_key=api_key)
            
    def encode(self, text: str) -> np.ndarray:
        """Convert a text string into a NumPy vector."""
        if not self.client:
            logger.error("Gemini client not initialized, missing API_KEY")
            raise ValueError("GEMINI_API_KEY not configured")
            
        result = self.client.models.embed_content(
            model=self.model_name,
            contents=text
        )
        return np.array(result.embeddings[0].values, dtype=np.float32)

    def encode_batch(self, texts: List[str]) -> List[np.ndarray]:
        """Convert a list of texts via a single API call."""
        if not self.client:
            logger.error("Gemini client not initialized, missing API_KEY")
            raise ValueError("GEMINI_API_KEY not configured")
            
        result = self.client.models.embed_content(
            model=self.model_name,
            contents=texts
        )
        return [np.array(emb.values, dtype=np.float32) for emb in result.embeddings]
