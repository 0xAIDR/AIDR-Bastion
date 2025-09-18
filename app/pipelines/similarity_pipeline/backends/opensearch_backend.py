from typing import List, Dict, Any

from app.modules.logger import pipeline_logger
from app.modules.opensearch import AsyncOpenSearchClient
from app.pipelines.similarity_pipeline.backends.base import VectorSearchBackend, SearchResult
from settings import get_settings, OpenSearchSettings


class OpenSearchBackend(VectorSearchBackend):
    """
    OpenSearch implementation of vector search backend.

    Wraps the existing AsyncOpenSearchClient to provide compatibility
    with the VectorSearchBackend interface. Supports vector similarity
    search using OpenSearch k-NN functionality.

    Attributes:
        client: AsyncOpenSearchClient instance
        settings: OpenSearch configuration settings
        collection_name: Index name for storing vectors
    """

    def __init__(self, os_settings: OpenSearchSettings = None, collection_name: str = None):
        """
        Initialize OpenSearch backend.

        Args:
            os_settings: OpenSearch configuration settings
            collection_name: Index name for storing vectors
        """
        settings = get_settings()
        self.settings = os_settings or settings.OS
        self.collection_name = collection_name or settings.SIMILARITY_PROMPT_INDEX
        self.client: AsyncOpenSearchClient = None
        self._connected = False

        if self.settings:
            self.client = AsyncOpenSearchClient(
                os_settings=self.settings,
                similarity_prompt_index=self.collection_name
            )

    async def connect(self) -> None:
        """Initialize connection to OpenSearch server."""
        if not self.client:
            pipeline_logger.error("OpenSearch client not configured")
            return

        try:
            await self.client.connect()
            if self.client.client:
                self._connected = True
                pipeline_logger.info(f"Connected to OpenSearch at {self.settings.host}:{self.settings.port}")
            else:
                self._connected = False
                pipeline_logger.error("Failed to establish OpenSearch connection")
        except Exception as e:
            pipeline_logger.error(f"Error connecting to OpenSearch: {e}")
            self._connected = False

    async def close(self) -> None:
        """Close connection to OpenSearch server."""
        if self.client:
            try:
                await self.client.close()
                self._connected = False
                pipeline_logger.info("OpenSearch connection closed")
            except Exception as e:
                pipeline_logger.error(f"Error closing OpenSearch connection: {e}")

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
            pipeline_logger.error("OpenSearch client not connected")
            return []

        try:
            # Use existing OpenSearch client method
            documents = await self.client.search_similar_documents(vector)

            results = []
            for doc in documents:
                # Convert OpenSearch response format to SearchResult
                source = doc.get("_source", {})
                score = doc.get("_score", 0.0)

                # Filter by minimum score
                if score < min_score:
                    continue

                result = SearchResult(
                    doc_id=source.get("id", str(doc.get("_id", ""))),
                    text=source.get("text", ""),
                    details=source.get("details", ""),
                    category=source.get("category", ""),
                    score=score,
                    metadata=source.get("metadata", {})
                )
                results.append(result)

                # Respect limit
                if len(results) >= limit:
                    break

            pipeline_logger.info(f"Found {len(results)} similar documents in OpenSearch")
            return results

        except Exception as e:
            pipeline_logger.error(f"Error searching OpenSearch: {e}")
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

        Note: This is a simplified implementation. For production use,
        consider implementing proper document indexing via OpenSearch client.

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
            pipeline_logger.error("OpenSearch client not connected")
            return False

        try:
            # Create document body
            doc_body = {
                "id": doc_id,
                "text": text,
                "details": details,
                "category": category,
                "vector": vector,
                "metadata": metadata or {}
            }

            # Use OpenSearch client to index document
            response = await self.client.client.index(
                index=self.collection_name,
                id=doc_id,
                body=doc_body
            )

            if response.get("result") in ["created", "updated"]:
                pipeline_logger.info(f"Indexed document {doc_id} in OpenSearch")
                return True
            else:
                pipeline_logger.error(f"Failed to index document {doc_id}: {response}")
                return False

        except Exception as e:
            pipeline_logger.error(f"Error indexing document in OpenSearch: {e}")
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
            pipeline_logger.error("OpenSearch client not connected")
            return False

        try:
            response = await self.client.client.delete(
                index=self.collection_name,
                id=doc_id
            )

            if response.get("result") == "deleted":
                pipeline_logger.info(f"Deleted document {doc_id} from OpenSearch")
                return True
            else:
                pipeline_logger.error(f"Failed to delete document {doc_id}: {response}")
                return False

        except Exception as e:
            pipeline_logger.error(f"Error deleting document from OpenSearch: {e}")
            return False

    async def create_collection(self, collection_name: str, vector_size: int) -> bool:
        """
        Create a new index for storing vectors.

        Args:
            collection_name: Name of the index
            vector_size: Dimension of the vectors

        Returns:
            True if creation successful, False otherwise
        """
        if not self.client or not self._connected:
            pipeline_logger.error("OpenSearch client not connected")
            return False

        try:
            # Define index mapping for vectors
            index_body = {
                "mappings": {
                    "properties": {
                        "id": {"type": "keyword"},
                        "text": {"type": "text"},
                        "details": {"type": "text"},
                        "category": {"type": "keyword"},
                        "vector": {
                            "type": "knn_vector",
                            "dimension": vector_size,
                            "method": {
                                "name": "hnsw",
                                "space_type": "cosinesimil",
                                "engine": "nmslib"
                            }
                        },
                        "metadata": {"type": "object"}
                    }
                },
                "settings": {
                    "index": {
                        "knn": True,
                        "knn.algo_param.ef_search": 100
                    }
                }
            }

            response = await self.client.client.indices.create(
                index=collection_name,
                body=index_body
            )

            if response.get("acknowledged"):
                pipeline_logger.info(f"Created OpenSearch index '{collection_name}' with vector size {vector_size}")
                return True
            else:
                pipeline_logger.error(f"Failed to create OpenSearch index: {response}")
                return False

        except Exception as e:
            pipeline_logger.error(f"Error creating OpenSearch index: {e}")
            return False

    @property
    def is_connected(self) -> bool:
        """Check if backend is connected and ready."""
        return self._connected and self.client is not None and self.client.client is not None

    @property
    def backend_name(self) -> str:
        """Name of the backend implementation."""
        return "OpenSearch"