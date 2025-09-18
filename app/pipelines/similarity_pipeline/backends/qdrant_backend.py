import asyncio
from typing import List, Dict, Any, Optional

from app.modules.logger import pipeline_logger
from app.pipelines.similarity_pipeline.backends.base import VectorSearchBackend, SearchResult

from qdrant_client import QdrantClient
from qdrant_client.http import models
from qdrant_client.http.exceptions import UnexpectedResponse



class QdrantBackend(VectorSearchBackend):
    """
    Qdrant implementation of vector search backend.

    Provides high-performance vector similarity search using Qdrant database.
    Optimized for fast vector operations with HNSW indexing.

    Attributes:
        client: Qdrant client instance
        collection_name: Name of the collection storing vectors
        host: Qdrant server host
        port: Qdrant server port
    """

    def __init__(self, host: str = "localhost", port: int = 6333, collection_name: str = "similarity-prompts"):
        """
        Initialize Qdrant backend.

        Args:
            host: Qdrant server host
            port: Qdrant server port
            collection_name: Collection name for storing vectors
        """
        self.host = host
        self.port = port
        self.collection_name = collection_name
        self.client: Optional[QdrantClient] = None
        self._connected = False


    async def connect(self) -> None:
        """Initialize connection to Qdrant server."""

        try:
            # Create async client (Qdrant client handles async internally)
            self.client = QdrantClient(host=self.host, port=self.port)

            # Test connection
            self.client.get_collections()
            self._connected = True

            pipeline_logger.info(f"Connected to Qdrant at {self.host}:{self.port}")

            # Ensure collection exists
            await self._ensure_collection_exists()

        except Exception as e:
            pipeline_logger.error(f"Failed to connect to Qdrant: {e}")
            self._connected = False
            self.client = None

    async def close(self) -> None:
        """Close connection to Qdrant server."""
        if self.client:
            try:
                self.client.close()
                self._connected = False
                pipeline_logger.info("Qdrant connection closed")
            except Exception as e:
                pipeline_logger.error(f"Error closing Qdrant connection: {e}")

    async def _ensure_collection_exists(self) -> None:
        """Ensure the collection exists, create if necessary."""
        if not self.client:
            return

        try:
            # Check if collection exists
            self.client.get_collection(self.collection_name)
            pipeline_logger.info(f"Collection '{self.collection_name}' already exists")
        except UnexpectedResponse as e:
            if "doesn't exist" in str(e).lower():
                # Collection doesn't exist, create it
                await self.create_collection(self.collection_name, vector_size=384)  # Default for sentence transformers
            else:
                raise e

    async def search_similar_documents(
        self,
        vector: List[float],
        limit: int = 10,
        min_score: float = 0.0
    ) -> List[SearchResult]:
        """
        Search for similar documents using vector similarity.

        Args:
            vector: Query vector for similarity search
            limit: Maximum number of results to return
            min_score: Minimum similarity score threshold

        Returns:
            List of SearchResult objects sorted by similarity score
        """
        if not self.client or not self._connected:
            pipeline_logger.error("Qdrant client not connected")
            return []

        try:
            # Perform vector search
            search_result = self.client.search(
                collection_name=self.collection_name,
                query_vector=vector,
                limit=limit,
                score_threshold=min_score
            )

            results = []
            for hit in search_result:
                payload = hit.payload or {}
                result = SearchResult(
                    doc_id=payload.get("id", str(hit.id)),
                    text=payload.get("text", ""),
                    details=payload.get("details", ""),
                    category=payload.get("category", ""),
                    score=float(hit.score),
                    metadata=payload.get("metadata", {})
                )
                results.append(result)

            pipeline_logger.info(f"Found {len(results)} similar documents in Qdrant")
            return results

        except Exception as e:
            pipeline_logger.error(f"Error searching Qdrant: {e}")
            return []

    async def index_document(
        self,
        doc_id: str,
        vector: List[float],
        text: str,
        details: str,
        category: str,
        metadata: Dict[str, Any] = None
    ) -> bool:
        """
        Index a document with its vector embedding.

        Args:
            doc_id: Unique document identifier
            vector: Document vector embedding
            text: Original document text
            details: Document details/description
            category: Document category
            metadata: Additional metadata

        Returns:
            True if indexing successful, False otherwise
        """
        if not self.client or not self._connected:
            pipeline_logger.error("Qdrant client not connected")
            return False

        try:
            payload = {
                "id": doc_id,
                "text": text,
                "details": details,
                "category": category,
                "metadata": metadata or {}
            }

            self.client.upsert(
                collection_name=self.collection_name,
                points=[
                    models.PointStruct(
                        id=doc_id,
                        vector=vector,
                        payload=payload
                    )
                ]
            )

            pipeline_logger.info(f"Indexed document {doc_id} in Qdrant")
            return True

        except Exception as e:
            pipeline_logger.error(f"Error indexing document in Qdrant: {e}")
            return False

    async def delete_document(self, doc_id: str) -> bool:
        """
        Delete a document from the index.

        Args:
            doc_id: Unique document identifier

        Returns:
            True if deletion successful, False otherwise
        """
        if not self.client or not self._connected:
            pipeline_logger.error("Qdrant client not connected")
            return False

        try:
            self.client.delete(
                collection_name=self.collection_name,
                points_selector=models.PointIdsList(
                    points=[doc_id]
                )
            )

            pipeline_logger.info(f"Deleted document {doc_id} from Qdrant")
            return True

        except Exception as e:
            pipeline_logger.error(f"Error deleting document from Qdrant: {e}")
            return False

    async def create_collection(self, collection_name: str, vector_size: int) -> bool:
        """
        Create a new collection for storing vectors.

        Args:
            collection_name: Name of the collection
            vector_size: Dimension of the vectors

        Returns:
            True if creation successful, False otherwise
        """
        if not self.client:
            pipeline_logger.error("Qdrant client not connected")
            return False

        try:
            self.client.create_collection(
                collection_name=collection_name,
                vectors_config=models.VectorParams(
                    size=vector_size,
                    distance=models.Distance.COSINE
                )
            )

            pipeline_logger.info(f"Created Qdrant collection '{collection_name}' with vector size {vector_size}")
            return True

        except Exception as e:
            pipeline_logger.error(f"Error creating Qdrant collection: {e}")
            return False

    @property
    def is_connected(self) -> bool:
        """Check if backend is connected and ready."""
        return self._connected and self.client is not None

    @property
    def backend_name(self) -> str:
        """Name of the backend implementation."""
        return "Qdrant"