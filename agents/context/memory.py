"""
ChiliHead OpsManager v2.1 - Context Memory System
Qdrant vector store integration for 30-day historical context
"""

import os
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from loguru import logger

try:
    from qdrant_client import QdrantClient
    from qdrant_client.models import Distance, VectorParams, PointStruct, Filter, FieldCondition, Range
    QDRANT_AVAILABLE = True
except ImportError:
    logger.warning("Qdrant client not installed - memory system will be disabled")
    QDRANT_AVAILABLE = False


class ContextMemory:
    """
    Vector-based memory system for historical context retrieval

    Uses Qdrant vector database to store and retrieve email interactions
    from the past 30 days for contextual analysis.
    """

    def __init__(
        self,
        collection_name: str = "email_history",
        vector_size: int = 1536,  # OpenAI ada-002 embedding size
        host: Optional[str] = None,
        port: Optional[int] = None
    ):
        """
        Initialize context memory system

        Args:
            collection_name: Qdrant collection name
            vector_size: Embedding vector dimension
            host: Qdrant host (default from env)
            port: Qdrant port (default from env)
        """
        self.collection_name = collection_name
        self.vector_size = vector_size

        if not QDRANT_AVAILABLE:
            logger.warning("Qdrant not available - memory features disabled")
            self.client = None
            return

        # Get connection details from environment
        self.host = host or os.getenv("QDRANT_HOST", "localhost")
        self.port = port or int(os.getenv("QDRANT_PORT", "6333"))

        try:
            # Initialize Qdrant client
            self.client = QdrantClient(
                host=self.host,
                port=self.port,
                timeout=30
            )

            # Ensure collection exists
            self._ensure_collection()

            logger.info(f"Context memory initialized: {self.host}:{self.port}")

        except Exception as e:
            logger.error(f"Failed to initialize Qdrant client: {e}")
            self.client = None

    def _ensure_collection(self) -> None:
        """Ensure Qdrant collection exists with proper schema"""
        if not self.client:
            return

        try:
            # Check if collection exists
            collections = self.client.get_collections().collections
            collection_names = [c.name for c in collections]

            if self.collection_name not in collection_names:
                # Create collection
                self.client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=VectorParams(
                        size=self.vector_size,
                        distance=Distance.COSINE
                    )
                )
                logger.info(f"Created Qdrant collection: {self.collection_name}")

        except Exception as e:
            logger.error(f"Failed to ensure collection: {e}")

    async def search_similar(
        self,
        query: str,
        limit: int = 10,
        days_back: int = 30,
        min_score: float = 0.5
    ) -> List[Dict[str, Any]]:
        """
        Search for similar historical interactions

        Args:
            query: Search query text
            limit: Maximum results to return
            days_back: Days of history to search
            min_score: Minimum similarity score (0-1)

        Returns:
            List of matching historical items
        """
        if not self.client:
            logger.warning("Qdrant client not available")
            return []

        try:
            # Generate query embedding
            query_vector = await self._generate_embedding(query)

            if not query_vector:
                return []

            # Calculate date filter
            cutoff_date = (datetime.now() - timedelta(days=days_back)).timestamp()

            # Search Qdrant
            results = self.client.search(
                collection_name=self.collection_name,
                query_vector=query_vector,
                limit=limit,
                score_threshold=min_score,
                query_filter=Filter(
                    must=[
                        FieldCondition(
                            key="timestamp",
                            range=Range(gte=cutoff_date)
                        )
                    ]
                )
            )

            # Format results
            formatted = []
            for result in results:
                formatted.append({
                    "id": result.id,
                    "score": result.score,
                    "email_id": result.payload.get("email_id"),
                    "category": result.payload.get("category"),
                    "summary": result.payload.get("summary"),
                    "date": result.payload.get("date"),
                    "metadata": result.payload.get("metadata", {})
                })

            logger.info(f"Found {len(formatted)} similar interactions")

            return formatted

        except Exception as e:
            logger.error(f"Failed to search similar items: {e}")
            return []

    async def store_interaction(
        self,
        email_id: str,
        category: str,
        summary: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Store interaction in vector database

        Args:
            email_id: Email identifier
            category: Email category
            summary: Brief summary for embedding
            metadata: Additional metadata

        Returns:
            True if stored successfully
        """
        if not self.client:
            logger.warning("Qdrant client not available")
            return False

        try:
            # Generate embedding from summary
            vector = await self._generate_embedding(summary)

            if not vector:
                return False

            # Create point
            point = PointStruct(
                id=email_id,  # Use email_id as point ID
                vector=vector,
                payload={
                    "email_id": email_id,
                    "category": category,
                    "summary": summary,
                    "date": datetime.now().isoformat(),
                    "timestamp": datetime.now().timestamp(),
                    "metadata": metadata or {}
                }
            )

            # Upsert to Qdrant
            self.client.upsert(
                collection_name=self.collection_name,
                points=[point]
            )

            logger.debug(f"Stored interaction {email_id} in memory")

            return True

        except Exception as e:
            logger.error(f"Failed to store interaction: {e}")
            return False

    async def _generate_embedding(self, text: str) -> Optional[List[float]]:
        """
        Generate embedding vector for text

        Args:
            text: Text to embed

        Returns:
            Embedding vector or None
        """
        # TODO: Implement actual embedding generation
        # Options:
        # 1. OpenAI embeddings API (text-embedding-ada-002)
        # 2. Local sentence-transformers model
        # 3. Ollama embeddings endpoint

        # For now, return None to indicate not implemented
        # This will cause memory features to be disabled gracefully
        logger.warning("Embedding generation not implemented - using mock")

        # Mock embedding (should be replaced with actual implementation)
        return None

    async def cleanup_old_entries(self, days_to_keep: int = 30) -> int:
        """
        Remove entries older than specified days

        Args:
            days_to_keep: Number of days to retain

        Returns:
            Number of entries deleted
        """
        if not self.client:
            return 0

        try:
            cutoff_date = (datetime.now() - timedelta(days=days_to_keep)).timestamp()

            # Delete old points
            # Note: This is a placeholder - actual implementation would need
            # to use Qdrant's delete by filter functionality

            logger.info(f"Cleaned up entries older than {days_to_keep} days")

            return 0  # Return actual count when implemented

        except Exception as e:
            logger.error(f"Failed to cleanup old entries: {e}")
            return 0

    def get_stats(self) -> Dict[str, Any]:
        """
        Get memory system statistics

        Returns:
            Statistics dictionary
        """
        if not self.client:
            return {
                "status": "unavailable",
                "total_entries": 0
            }

        try:
            collection_info = self.client.get_collection(self.collection_name)

            return {
                "status": "active",
                "total_entries": collection_info.points_count,
                "vector_size": collection_info.config.params.vectors.size,
                "distance_metric": collection_info.config.params.vectors.distance
            }

        except Exception as e:
            logger.error(f"Failed to get stats: {e}")
            return {
                "status": "error",
                "error": str(e)
            }
