from abc import ABC, abstractmethod
from typing import List, Dict, Any


class SearchResult:
    """Result from vector search containing document data and similarity score."""

    def __init__(self, doc_id: str, text: str, details: str, category: str, score: float, metadata: Dict[str, Any] = None):
        self.doc_id = doc_id
        self.text = text
        self.details = details
        self.category = category
        self.score = score
        self.metadata = metadata or {}


class VectorSearchBackend(ABC):
    """
    Abstract base class for vector search backends.

    This class defines the interface that all vector search implementations
    must follow, allowing easy switching between different vector databases
    like Qdrant, OpenSearch, Pinecone, etc.
    """

    @abstractmethod
    async def connect(self) -> None:
        """Initialize connection to the vector database."""
        pass

    @abstractmethod
    async def close(self) -> None:
        """Close connection to the vector database."""
        pass

    @abstractmethod
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
        pass

    @abstractmethod
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
        pass

    @abstractmethod
    async def delete_document(self, doc_id: str) -> bool:
        """
        Delete a document from the index.

        Args:
            doc_id: Unique document identifier

        Returns:
            True if deletion successful, False otherwise
        """
        pass

    @abstractmethod
    async def create_collection(self, collection_name: str, vector_size: int) -> bool:
        """
        Create a new collection/index for storing vectors.

        Args:
            collection_name: Name of the collection
            vector_size: Dimension of the vectors

        Returns:
            True if creation successful, False otherwise
        """
        pass

    @property
    @abstractmethod
    def is_connected(self) -> bool:
        """Check if backend is connected and ready."""
        pass

    @property
    @abstractmethod
    def backend_name(self) -> str:
        """Name of the backend implementation."""
        pass