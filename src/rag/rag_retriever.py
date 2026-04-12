"""RAG retrieval interface for querying vector database."""

from __future__ import annotations

from typing import Any

from src.rag.embedding_model import EmbeddingModel
from src.rag.vector_database import VectorDatabase


class RAGRetriever:
    """Interface for retrieving relevant documents from vector database."""

    def __init__(self, embedder: EmbeddingModel, vector_db: VectorDatabase):
        """
        Initialize RAG retriever.

        Args:
            embedder: Embedding model for query encoding
            vector_db: Vector database for similarity search
        """
        self.embedder = embedder
        self.vector_db = vector_db

    def retrieve(
        self,
        query: str,
        top_k: int = 5,
        metadata_filter: dict[str, Any] | None = None,
        min_score: float | None = None,
    ) -> list[dict[str, Any]]:
        """
        Retrieve relevant documents for a query.

        Args:
            query: Query string
            top_k: Number of results to return
            metadata_filter: Optional metadata filter (e.g., {"lesson_number": 1})
            min_score: Optional minimum similarity score threshold

        Returns:
            List of results with text, score, and metadata
        """
        query_embedding = self.embedder.embed(query)

        response = self.vector_db.query(
            vector=query_embedding, top_k=top_k, filter=metadata_filter, include_metadata=True
        )

        results = self._format_results(response.get("matches", []))

        if min_score is not None:
            results = [r for r in results if r["score"] >= min_score]

        return results

    def retrieve_by_lesson(
        self, query: str, lesson_number: int, top_k: int = 5
    ) -> list[dict[str, Any]]:
        """Retrieve relevant documents filtered by lesson number."""
        return self.retrieve(query, top_k=top_k, metadata_filter={"lesson_number": lesson_number})

    def retrieve_by_grammar_point(
        self, query: str, grammar_point: str, top_k: int = 5
    ) -> list[dict[str, Any]]:
        """Retrieve relevant documents filtered by grammar point."""
        return self.retrieve(query, top_k=top_k, metadata_filter={"grammar_point": grammar_point})

    def retrieve_by_difficulty(
        self, query: str, difficulty: str, top_k: int = 5
    ) -> list[dict[str, Any]]:
        """Retrieve relevant documents filtered by difficulty level."""
        return self.retrieve(query, top_k=top_k, metadata_filter={"difficulty": difficulty})

    def _format_results(self, matches: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Format raw vector database matches into result objects."""
        results = []
        for match in matches:
            original_metadata = match.get("metadata", {})
            metadata = dict(original_metadata)

            text = metadata.pop("text", "")

            result = {
                "text": text,
                "score": match.get("score", 0.0),
                "metadata": metadata,
            }
            results.append(result)

        return results
