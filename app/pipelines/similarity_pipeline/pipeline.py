import asyncio

from app.core.enums import PipelineNames, RuleAction
from app.models.pipeline import PipelineResult, TriggeredRuleData
from app.modules.logger import pipeline_logger
from app.pipelines.base import BasePipeline
from app.pipelines.similarity_pipeline.backends.factory import VectorBackendFactory
from app.pipelines.similarity_pipeline.backends.base import VectorSearchBackend
from app.pipelines.similarity_pipeline.utils import split_text_into_sentences
from app.utils import text_embedding
from settings import get_settings

settings = get_settings()


class SimilarityPipeline(BasePipeline):
    """
    Similarity-based pipeline for detecting similar content using vector embeddings.

    This pipeline uses vector embeddings and configurable backends (Qdrant/OpenSearch)
    to find similar documents in a knowledge base. It splits prompts into sentences,
    converts them to embeddings, and searches for similar content using cosine similarity.
    Results are deduplicated and scored based on similarity thresholds.

    Attributes:
        name (PipelineNames): Pipeline name (similarity)
        enabled (bool): Whether pipeline is active (depends on backend availability)
        backend (VectorSearchBackend): Vector search backend instance
    """

    name = PipelineNames.similarity

    def __init__(self):
        super().__init__()
        self.backend: VectorSearchBackend = None

        # Create vector backend using factory
        try:
            backend_type = settings.VECTOR_BACKEND
            self.backend = VectorBackendFactory.create_backend(backend_type)

            if self.backend:
                self.enabled = True
                pipeline_logger.info(f"[{self}] loaded successfully using {self.backend.backend_name} backend")
            else:
                pipeline_logger.error(f"[{self}] Failed to create vector backend")

        except Exception as e:
            pipeline_logger.error(f"[{self}] Error initializing backend: {e}")
            self.backend = None

    def __split_prompt_into_sentences(self, prompt: str) -> list[str]:
        """
        Split prompt into sentences and return them as a list.

        Args:
            prompt (str): Text prompt to split

        Returns:
            list[str]: List of sentences from the prompt
        """
        return split_text_into_sentences(prompt)

    async def __search_similar_documents(self, chunk: str) -> list[dict]:
        """
        Search for similar documents using vector embeddings.

        Converts text chunk to vector embedding and searches the configured
        vector backend for similar documents. Filters results by similarity
        threshold and formats them for further processing.

        Args:
            chunk (str): Text chunk to search for similar content

        Returns:
            list[dict]: List of similar documents with metadata and scores
        """
        if not self.backend or not self.backend.is_connected:
            pipeline_logger.warning(f"[{self}] Backend not available for search")
            return []

        vector = text_embedding(chunk)
        search_results = await self.backend.search_similar_documents(
            vector=vector,
            limit=10,
            min_score=settings.SIMILARITY_NOTIFY_THRESHOLD
        )

        return [
            {
                "action": self._get_action(result.score),
                "doc_id": result.doc_id,
                "name": result.category,
                "details": result.details,
                "body": result.text,
                "score": result.score,
            }
            for result in search_results
        ]

    async def __prepare_triggered_rules(self, similar_documents: list[dict]) -> list[TriggeredRuleData]:
        """
        Prepare rules with deduplication by doc_id.

        For identical documents, preference is given to those with higher score.
        Converts similar documents to TriggeredRuleData objects.

        Args:
            similar_documents (list[dict]): List of documents with search results

        Returns:
            list[TriggeredRuleData]: List of unique TriggeredRuleData objects
        """
        deduplicated_docs = {}
        for doc in similar_documents:
            doc_id = doc["doc_id"]
            if doc_id not in deduplicated_docs or doc["score"] > deduplicated_docs[doc_id]["score"]:
                deduplicated_docs[doc_id] = doc
        return [
            TriggeredRuleData(
                action=doc["action"], id=doc["doc_id"], name=doc["name"], details=doc["details"], body=doc["body"]
            )
            for doc in deduplicated_docs.values()
        ]

    async def run(self, prompt: str, **kwargs) -> PipelineResult:
        """
        Analyzes prompt for similar content using vector similarity search.

        Splits the prompt into sentences, processes them in batches,
        and searches for similar documents using vector embeddings.
        Returns analysis results with triggered rules for similar content.

        Args:
            prompt (str): Text prompt to analyze for similar content
            **kwargs: Additional keyword arguments (unused)

        Returns:
            PipelineResult: Analysis result with triggered rules and status
        """
        # Ensure backend is connected
        if not self.backend:
            pipeline_logger.error(f"[{self}] No backend available")
            return PipelineResult(name=str(self), status=self._pipeline_status([]), triggered_rules=[])

        if not self.backend.is_connected:
            try:
                await self.backend.connect()
            except Exception as e:
                pipeline_logger.error(f"[{self}] Failed to connect backend: {e}")
                return PipelineResult(name=str(self), status=self._pipeline_status([]), triggered_rules=[])

        similar_documents = []
        chunks = self.__split_prompt_into_sentences(prompt)
        pipeline_logger.info(f"Analyzing {len(chunks)} sentences using {self.backend.backend_name} backend")

        batch_size = 5
        for i in range(0, len(chunks), batch_size):
            batch = chunks[i : i + batch_size]
            tasks = [self.__search_similar_documents(chunk) for chunk in batch]
            batch_results = await asyncio.gather(*tasks)
            for result in batch_results:
                similar_documents.extend(result)
        triggered_rules = await self.__prepare_triggered_rules(similar_documents)
        pipeline_logger.info(f"Found {len(triggered_rules)} similar documents")
        return PipelineResult(
            name=str(self), status=self._pipeline_status(triggered_rules), triggered_rules=triggered_rules
        )

    @staticmethod
    def _get_action(score: float) -> RuleAction:
        """
        Determines action based on similarity score.

        Compares the similarity score against configured thresholds
        to determine whether to block or notify.

        Args:
            score (float): Similarity score from vector search

        Returns:
            RuleAction: BLOCK if score exceeds block threshold, otherwise NOTIFY
        """
        if score >= settings.SIMILARITY_BLOCK_THRESHOLD:
            return RuleAction.BLOCK
        return RuleAction.NOTIFY
