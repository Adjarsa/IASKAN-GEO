"""
Embedding Service for Semantic Search
Generates embeddings using OpenAI text-embedding-3-small model
"""
import os
import hashlib
import logging
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

# Try to import OpenAI
try:
    from openai import AsyncOpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    AsyncOpenAI = None

# Embedding configuration
EMBEDDING_MODEL = "text-embedding-3-small"
EMBEDDING_DIMENSIONS = 1536
MAX_TOKENS = 8191  # Max for text-embedding-3-small
BATCH_SIZE = 100  # OpenAI allows up to 2048 texts per batch


class EmbeddingService:
    """
    Service for generating and managing text embeddings.
    Uses OpenAI text-embedding-3-small for vector generation.
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """Initialize with API key from param or environment"""
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY")
        self._client = None
        
    @property
    def client(self):
        """Lazy initialization of OpenAI client"""
        if self._client is None and self.api_key and OPENAI_AVAILABLE:
            self._client = AsyncOpenAI(api_key=self.api_key)
        return self._client
    
    def is_available(self) -> bool:
        """Check if embedding service is available"""
        return OPENAI_AVAILABLE and self.api_key is not None
    
    async def generate_embedding(self, text: str) -> Optional[List[float]]:
        """
        Generate embedding for a single text.
        
        Args:
            text: Text to embed (max ~8000 tokens)
            
        Returns:
            List of 1536 floats or None if failed
        """
        if not self.is_available():
            logger.warning("Embedding service not available (no API key or OpenAI not installed)")
            return None
        
        try:
            # Truncate text if too long
            text = self._truncate_text(text)
            
            response = await self.client.embeddings.create(
                model=EMBEDDING_MODEL,
                input=text,
                dimensions=EMBEDDING_DIMENSIONS
            )
            
            return response.data[0].embedding
            
        except Exception as e:
            logger.error(f"Error generating embedding: {e}")
            return None
    
    async def generate_embeddings_batch(
        self, 
        texts: List[str]
    ) -> List[Optional[List[float]]]:
        """
        Generate embeddings for multiple texts in batch.
        
        Args:
            texts: List of texts to embed
            
        Returns:
            List of embeddings (None for failed items)
        """
        if not self.is_available():
            logger.warning("Embedding service not available")
            return [None] * len(texts)
        
        results = []
        
        # Process in batches
        for i in range(0, len(texts), BATCH_SIZE):
            batch = texts[i:i + BATCH_SIZE]
            batch = [self._truncate_text(t) for t in batch]
            
            try:
                response = await self.client.embeddings.create(
                    model=EMBEDDING_MODEL,
                    input=batch,
                    dimensions=EMBEDDING_DIMENSIONS
                )
                
                # Sort by index to maintain order
                sorted_data = sorted(response.data, key=lambda x: x.index)
                for item in sorted_data:
                    results.append(item.embedding)
                    
            except Exception as e:
                logger.error(f"Error generating batch embeddings: {e}")
                results.extend([None] * len(batch))
        
        return results
    
    def _truncate_text(self, text: str, max_chars: int = 30000) -> str:
        """
        Truncate text to fit within token limits.
        Rough estimate: 1 token ≈ 4 chars for English, 2-3 for French
        """
        if len(text) > max_chars:
            return text[:max_chars]
        return text
    
    @staticmethod
    def content_hash(content: str) -> str:
        """Generate SHA256 hash of content for change detection"""
        return hashlib.sha256(content.encode('utf-8')).hexdigest()
    
    @staticmethod
    def cosine_similarity(vec1: List[float], vec2: List[float]) -> float:
        """
        Calculate cosine similarity between two vectors.
        
        Returns:
            Similarity score between -1 and 1
        """
        if not vec1 or not vec2 or len(vec1) != len(vec2):
            return 0.0
        
        dot_product = sum(a * b for a, b in zip(vec1, vec2))
        norm1 = sum(a * a for a in vec1) ** 0.5
        norm2 = sum(b * b for b in vec2) ** 0.5
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        return dot_product / (norm1 * norm2)
    
    @staticmethod
    def find_similar(
        query_embedding: List[float],
        embeddings: List[Tuple[str, List[float]]],
        top_k: int = 10,
        threshold: float = 0.5
    ) -> List[Dict[str, Any]]:
        """
        Find most similar items using cosine similarity.
        For use when pgvector is not available.
        
        Args:
            query_embedding: The query vector
            embeddings: List of (id, embedding) tuples
            top_k: Number of results to return
            threshold: Minimum similarity score
            
        Returns:
            List of {id, similarity} sorted by similarity
        """
        results = []
        
        for item_id, embedding in embeddings:
            similarity = EmbeddingService.cosine_similarity(query_embedding, embedding)
            if similarity >= threshold:
                results.append({
                    "id": item_id,
                    "similarity": round(similarity, 4)
                })
        
        # Sort by similarity descending
        results.sort(key=lambda x: x["similarity"], reverse=True)
        
        return results[:top_k]


# Create default instance
embedding_service = EmbeddingService()
