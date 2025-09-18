from typing import Optional

from app.modules.logger import pipeline_logger
from app.pipelines.similarity_pipeline.backends.base import VectorSearchBackend
from app.pipelines.similarity_pipeline.backends.opensearch_backend import OpenSearchBackend
from app.pipelines.similarity_pipeline.backends.qdrant_backend import QdrantBackend
from settings import get_settings


class VectorBackendFactory:
    """
    Factory class for creating vector search backend instances.

    Provides a centralized way to create and configure different
    vector search backends based on configuration settings.
    """

    @staticmethod
    def create_backend(backend_type: str = None) -> Optional[VectorSearchBackend]:
        """
        Create a vector search backend instance.

        Args:
            backend_type: Type of backend to create ('qdrant', 'opensearch', 'auto')
                        If None or 'auto', will auto-detect based on available settings

        Returns:
            VectorSearchBackend instance or None if creation failed
        """
        settings = get_settings()

        # Auto-detect backend if not specified
        if not backend_type or backend_type == "auto":
            backend_type = VectorBackendFactory._auto_detect_backend()

        backend_type = backend_type.lower()

        try:
            if backend_type == "qdrant":
                return VectorBackendFactory._create_qdrant_backend()
            elif backend_type == "opensearch":
                return VectorBackendFactory._create_opensearch_backend()
            else:
                pipeline_logger.error(f"Unknown backend type: {backend_type}")
                return None

        except Exception as e:
            pipeline_logger.error(f"Failed to create {backend_type} backend: {e}")
            return None

    @staticmethod
    def _auto_detect_backend() -> str:
        """
        Auto-detect which backend to use based on available settings.

        Returns:
            String name of the backend to use
        """
        settings = get_settings()

        # Check for Qdrant settings
        qdrant_host = getattr(settings, 'QDRANT_HOST', None)
        qdrant_port = getattr(settings, 'QDRANT_PORT', None)

        # Check for OpenSearch settings
        opensearch_available = settings.OS is not None

        # Prefer Qdrant if available, fallback to OpenSearch
        if qdrant_host:
            pipeline_logger.info("Auto-detected Qdrant configuration, using Qdrant backend")
            return "qdrant"
        elif opensearch_available:
            pipeline_logger.info("Auto-detected OpenSearch configuration, using OpenSearch backend")
            return "opensearch"
        else:
            pipeline_logger.warning("No vector backend configuration found, defaulting to OpenSearch")
            return "opensearch"

    @staticmethod
    def _create_qdrant_backend() -> QdrantBackend:
        """
        Create Qdrant backend instance.

        Returns:
            QdrantBackend instance
        """
        settings = get_settings()

        # Get Qdrant settings with defaults
        host = getattr(settings, 'QDRANT_HOST', 'localhost')
        port = getattr(settings, 'QDRANT_PORT', 6333)
        collection_name = getattr(settings, 'QDRANT_COLLECTION_NAME', settings.SIMILARITY_PROMPT_INDEX)

        pipeline_logger.info(f"Creating Qdrant backend: {host}:{port}, collection: {collection_name}")

        return QdrantBackend(
            host=host,
            port=port,
            collection_name=collection_name
        )

    @staticmethod
    def _create_opensearch_backend() -> OpenSearchBackend:
        """
        Create OpenSearch backend instance.

        Returns:
            OpenSearchBackend instance
        """
        settings = get_settings()

        pipeline_logger.info(f"Creating OpenSearch backend: collection: {settings.SIMILARITY_PROMPT_INDEX}")

        return OpenSearchBackend(
            os_settings=settings.OS,
            collection_name=settings.SIMILARITY_PROMPT_INDEX
        )

    @staticmethod
    def get_available_backends() -> list[str]:
        """
        Get list of available backends.

        Returns:
            List of backend names that can be created
        """
        return ["qdrant", "opensearch"]

    @staticmethod
    def is_backend_available(backend_type: str) -> bool:
        """
        Check if a specific backend type is available.

        Args:
            backend_type: Name of the backend to check

        Returns:
            True if backend can be created, False otherwise
        """
        settings = get_settings()

        if backend_type.lower() == "qdrant":
            try:
                from qdrant_client import QdrantClient
                return True
            except ImportError:
                return False

        elif backend_type.lower() == "opensearch":
            return settings.OS is not None

        return False