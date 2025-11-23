"""
ChiliHead OpsManager v2.1 - Qdrant Vector Database Client
Handles context embeddings, similarity search, and 30-day retention
"""

import os
from typing import Any, Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from uuid import UUID, uuid4
from loguru import logger

from qdrant_client import AsyncQdrantClient
from qdrant_client.models import (
    Distance,
    VectorParams,
    PointStruct,
    Filter,
    FieldCondition,
    MatchValue,
    Range,
    SearchParams,
    OptimizersConfigDiff,
    Collection
)
from sentence_transformers import SentenceTransformer


class QdrantVectorClient:
    """Qdrant vector database client for context memory"""

    def __init__(
        self,
        host: Optional[str] = None,
        port: Optional[int] = None,
        collection_name: str = "email_context",
        embedding_model: str = "all-MiniLM-L6-v2"
    ):
        """
        Initialize Qdrant client

        Args:
            host: Qdrant server host (default: env QDRANT_HOST)
            port: Qdrant server port (default: env QDRANT_PORT or 6333)
            collection_name: Vector collection name
            embedding_model: Sentence transformer model for embeddings
        """
        self.host = host or os.getenv("QDRANT_HOST", "localhost")
        self.port = port or int(os.getenv("QDRANT_PORT", "6333"))
        self.collection_name = collection_name

        # Initialize async client
        self.client = AsyncQdrantClient(
            host=self.host,
            port=self.port,
            timeout=30
        )

        # Initialize embedding model
        self.embedding_model = SentenceTransformer(embedding_model)
        self.vector_size = self.embedding_model.get_sentence_embedding_dimension()

        # Retention period (30 days)
        self.retention_days = 30

        logger.info(
            f"QdrantVectorClient initialized: {self.host}:{self.port} "
            f"(collection: {collection_name}, dim: {self.vector_size})"
        )

    async def initialize_collection(self):
        """Initialize collection with proper configuration"""
        try:
            # Check if collection exists
            collections = await self.client.get_collections()
            collection_names = [c.name for c in collections.collections]

            if self.collection_name not in collection_names:
                # Create collection
                await self.client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=VectorParams(
                        size=self.vector_size,
                        distance=Distance.COSINE
                    ),
                    optimizers_config=OptimizersConfigDiff(
                        indexing_threshold=10000,
                        memmap_threshold=20000
                    )
                )

                # Create payload indexes for filtering
                await self.client.create_payload_index(
                    collection_name=self.collection_name,
                    field_name="email_id",
                    field_schema="keyword"
                )

                await self.client.create_payload_index(
                    collection_name=self.collection_name,
                    field_name="timestamp",
                    field_schema="integer"
                )

                await self.client.create_payload_index(
                    collection_name=self.collection_name,
                    field_name="category",
                    field_schema="keyword"
                )

                logger.info(f"Created collection: {self.collection_name}")
            else:
                logger.info(f"Collection already exists: {self.collection_name}")

        except Exception as e:
            logger.error(f"Failed to initialize collection: {e}")
            raise

    def _generate_embedding(self, text: str) -> List[float]:
        """Generate embedding vector from text"""
        embedding = self.embedding_model.encode(text)
        return embedding.tolist()

    async def store_context(
        self,
        email_id: str,
        text: str,
        metadata: Optional[Dict[str, Any]] = None,
        vector_id: Optional[str] = None
    ) -> str:
        """
        Store email context as embedding

        Args:
            email_id: Email identifier
            text: Text to embed
            metadata: Additional metadata to store
            vector_id: Optional vector ID (auto-generated if None)

        Returns:
            Vector ID

        Example:
            vector_id = await qdrant_client.store_context(
                email_id="email_123",
                text="Vendor invoice for catering supplies",
                metadata={
                    "category": "vendor",
                    "vendor_name": "ABC Supplies",
                    "amount": 1500.00
                }
            )
        """
        try:
            # Generate embedding
            vector = self._generate_embedding(text)

            # Generate ID
            point_id = vector_id or str(uuid4())

            # Prepare payload
            payload = {
                "email_id": email_id,
                "text": text,
                "timestamp": int(datetime.now().timestamp()),
                **(metadata or {})
            }

            # Create point
            point = PointStruct(
                id=point_id,
                vector=vector,
                payload=payload
            )

            # Upsert to collection
            await self.client.upsert(
                collection_name=self.collection_name,
                points=[point]
            )

            logger.debug(f"Stored context: {point_id} for email {email_id}")
            return point_id

        except Exception as e:
            logger.error(f"Failed to store context: {e}")
            raise

    async def similarity_search(
        self,
        query_text: str,
        limit: int = 10,
        score_threshold: float = 0.7,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Search for similar context using semantic similarity

        Args:
            query_text: Query text
            limit: Maximum number of results
            score_threshold: Minimum similarity score (0-1)
            filters: Optional metadata filters

        Returns:
            List of similar contexts with scores

        Example:
            results = await qdrant_client.similarity_search(
                query_text="catering supplies invoice",
                limit=5,
                filters={"category": "vendor"}
            )

            for result in results:
                print(f"Score: {result['score']}")
                print(f"Text: {result['text']}")
        """
        try:
            # Generate query embedding
            query_vector = self._generate_embedding(query_text)

            # Build filter if provided
            query_filter = None
            if filters:
                conditions = []
                for key, value in filters.items():
                    conditions.append(
                        FieldCondition(
                            key=key,
                            match=MatchValue(value=value)
                        )
                    )
                query_filter = Filter(must=conditions)

            # Search
            results = await self.client.search(
                collection_name=self.collection_name,
                query_vector=query_vector,
                limit=limit,
                score_threshold=score_threshold,
                query_filter=query_filter,
                with_payload=True,
                with_vectors=False
            )

            # Format results
            formatted_results = []
            for result in results:
                formatted_results.append({
                    "id": result.id,
                    "score": result.score,
                    **result.payload
                })

            logger.debug(f"Similarity search returned {len(formatted_results)} results")
            return formatted_results

        except Exception as e:
            logger.error(f"Failed to perform similarity search: {e}")
            raise

    async def get_email_history(
        self,
        email_id: Optional[str] = None,
        category: Optional[str] = None,
        days: int = 30,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Get historical context for emails

        Args:
            email_id: Specific email ID
            category: Filter by category
            days: Number of days to look back
            limit: Maximum results

        Returns:
            List of historical contexts
        """
        try:
            # Calculate timestamp threshold
            cutoff_timestamp = int(
                (datetime.now() - timedelta(days=days)).timestamp()
            )

            # Build filter conditions
            conditions = [
                FieldCondition(
                    key="timestamp",
                    range=Range(gte=cutoff_timestamp)
                )
            ]

            if email_id:
                conditions.append(
                    FieldCondition(
                        key="email_id",
                        match=MatchValue(value=email_id)
                    )
                )

            if category:
                conditions.append(
                    FieldCondition(
                        key="category",
                        match=MatchValue(value=category)
                    )
                )

            query_filter = Filter(must=conditions)

            # Scroll through results
            results, _ = await self.client.scroll(
                collection_name=self.collection_name,
                scroll_filter=query_filter,
                limit=limit,
                with_payload=True,
                with_vectors=False
            )

            formatted_results = []
            for point in results:
                formatted_results.append({
                    "id": point.id,
                    **point.payload
                })

            logger.debug(f"Retrieved {len(formatted_results)} historical contexts")
            return formatted_results

        except Exception as e:
            logger.error(f"Failed to get email history: {e}")
            raise

    async def find_vendor_context(
        self,
        vendor_name: str,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """
        Find all context related to a specific vendor

        Args:
            vendor_name: Vendor name to search for
            limit: Maximum results

        Returns:
            List of vendor-related contexts
        """
        # Use similarity search to find vendor mentions
        return await self.similarity_search(
            query_text=vendor_name,
            limit=limit,
            filters={"category": "vendor"}
        )

    async def cleanup_old_data(self):
        """Remove data older than retention period (30 days)"""
        try:
            cutoff_timestamp = int(
                (datetime.now() - timedelta(days=self.retention_days)).timestamp()
            )

            # Filter for old data
            old_filter = Filter(
                must=[
                    FieldCondition(
                        key="timestamp",
                        range=Range(lt=cutoff_timestamp)
                    )
                ]
            )

            # Scroll and delete old points
            old_points, _ = await self.client.scroll(
                collection_name=self.collection_name,
                scroll_filter=old_filter,
                limit=1000,
                with_payload=False,
                with_vectors=False
            )

            if old_points:
                point_ids = [point.id for point in old_points]

                await self.client.delete(
                    collection_name=self.collection_name,
                    points_selector=point_ids
                )

                logger.info(f"Cleaned up {len(point_ids)} old vectors")
            else:
                logger.info("No old data to clean up")

        except Exception as e:
            logger.error(f"Failed to cleanup old data: {e}")
            raise

    async def get_collection_stats(self) -> Dict[str, Any]:
        """
        Get collection statistics

        Returns:
            Collection stats including size, vectors count, etc.
        """
        try:
            info = await self.client.get_collection(self.collection_name)

            return {
                "vectors_count": info.vectors_count,
                "points_count": info.points_count,
                "indexed_vectors_count": info.indexed_vectors_count,
                "status": info.status,
                "optimizer_status": info.optimizer_status,
                "vector_size": info.config.params.vectors.size
            }

        except Exception as e:
            logger.error(f"Failed to get collection stats: {e}")
            raise

    async def delete_by_email(self, email_id: str) -> int:
        """
        Delete all vectors associated with an email

        Args:
            email_id: Email identifier

        Returns:
            Number of vectors deleted
        """
        try:
            # Get points for this email
            points, _ = await self.client.scroll(
                collection_name=self.collection_name,
                scroll_filter=Filter(
                    must=[
                        FieldCondition(
                            key="email_id",
                            match=MatchValue(value=email_id)
                        )
                    ]
                ),
                limit=1000,
                with_payload=False,
                with_vectors=False
            )

            if points:
                point_ids = [point.id for point in points]

                await self.client.delete(
                    collection_name=self.collection_name,
                    points_selector=point_ids
                )

                logger.info(f"Deleted {len(point_ids)} vectors for email {email_id}")
                return len(point_ids)

            return 0

        except Exception as e:
            logger.error(f"Failed to delete vectors for email {email_id}: {e}")
            raise

    async def close(self):
        """Close Qdrant client connection"""
        await self.client.close()
        logger.info("Qdrant client closed")
