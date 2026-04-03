"""
Retrieval interface for exercise templates.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel

from rag.vectorstore import VectorStore


class RetrievalResult(BaseModel):
    """Structure for a single retrieval result."""

    content: str
    metadata: dict[str, Any]
    distance: float


class ExerciseRetriever:
    """Retrieve relevant exercise templates based on queries."""

    def __init__(self, vectorstore: VectorStore | None = None) -> None:
        """
        Initialize the retriever.

        Args:
            vectorstore: VectorStore instance (creates new one if None)
        """
        self.vectorstore = vectorstore or VectorStore()

    def retrieve(
        self,
        query: str,
        lesson: int | None = None,
        exercise_type: str | None = None,
        skill_focus: str | None = None,
        n_results: int = 3,
    ) -> list[RetrievalResult]:
        """
        Retrieve relevant exercise templates.

        Args:
            query: Natural language query describing the exercise
            lesson: Filter by lesson number
            exercise_type: Filter by exercise type
            skill_focus: Filter by skill (vocabulary/grammar/mixed)
            n_results: Number of results to return

        Returns:
            List of RetrievalResult objects
        """
        where_filter = self._build_filter(lesson, exercise_type, skill_focus)

        results = self.vectorstore.query(
            query_texts=[query],
            n_results=n_results,
            where=where_filter if where_filter else None,
        )

        return self._format_results(results)

    def _build_filter(
        self,
        lesson: int | None,
        exercise_type: str | None,
        skill_focus: str | None,
    ) -> dict[str, Any] | None:
        """Build metadata filter for ChromaDB query."""
        filters = {}

        if lesson is not None:
            filters["lesson"] = lesson

        if exercise_type is not None:
            filters["exercise_type"] = exercise_type

        if skill_focus is not None:
            filters["skill_focus"] = skill_focus

        return filters if filters else None

    def _format_results(self, raw_results: dict[str, Any]) -> list[RetrievalResult]:
        """Format ChromaDB results into RetrievalResult objects."""
        results = []

        if not raw_results["documents"] or not raw_results["documents"][0]:
            return results

        for doc, metadata, distance in zip(
            raw_results["documents"][0],
            raw_results["metadatas"][0],
            raw_results["distances"][0],
        ):
            results.append(
                RetrievalResult(
                    content=doc,
                    metadata=metadata,
                    distance=distance,
                )
            )

        return results

    def get_by_metadata(
        self,
        lesson: int | None = None,
        exercise_type: str | None = None,
        skill_focus: str | None = None,
        limit: int = 10,
    ) -> list[RetrievalResult]:
        """
        Retrieve templates by metadata only (no semantic search).

        Args:
            lesson: Filter by lesson number
            exercise_type: Filter by exercise type
            skill_focus: Filter by skill focus
            limit: Maximum number of results

        Returns:
            List of RetrievalResult objects
        """
        where_filter = self._build_filter(lesson, exercise_type, skill_focus)

        if not where_filter:
            return []

        results = self.vectorstore.collection.get(
            where=where_filter,
            limit=limit,
        )

        formatted = []
        for doc, metadata in zip(results["documents"], results["metadatas"]):
            formatted.append(
                RetrievalResult(
                    content=doc,
                    metadata=metadata,
                    distance=0.0,
                )
            )

        return formatted
