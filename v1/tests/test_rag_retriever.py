"""Tests for RAG retriever functionality."""

from __future__ import annotations

import tempfile

import pytest

from rag.retriever import ExerciseRetriever, RetrievalResult
from rag.vectorstore import VectorStore


@pytest.fixture
def populated_retriever() -> ExerciseRetriever:
    """Create a retriever with sample data."""
    with tempfile.TemporaryDirectory() as tmpdir:
        vectorstore = VectorStore(persist_directory=tmpdir)

        documents = [
            "Fill in the blank vocabulary exercise for lesson 1",
            "Multiple choice grammar exercise for lesson 1",
            "Translation exercise for lesson 2 vocabulary",
        ]
        metadatas = [
            {
                "exercise_type": "fill_in_blank",
                "skill_focus": "vocabulary",
                "lesson": 1,
            },
            {
                "exercise_type": "multiple_choice",
                "skill_focus": "grammar",
                "lesson": 1,
            },
            {
                "exercise_type": "translation",
                "skill_focus": "vocabulary",
                "lesson": 2,
            },
        ]
        ids = ["ex1", "ex2", "ex3"]

        vectorstore.add_documents(documents, metadatas, ids)
        yield ExerciseRetriever(vectorstore)


def test_retrieval_result_model() -> None:
    """Test RetrievalResult pydantic model."""
    result = RetrievalResult(
        content="test content",
        metadata={"lesson": 1},
        distance=0.5,
    )

    assert result.content == "test content"
    assert result.metadata["lesson"] == 1
    assert result.distance == 0.5


def test_retrieve_basic(populated_retriever: ExerciseRetriever) -> None:
    """Test basic retrieval without filters."""
    results = populated_retriever.retrieve(
        query="vocabulary practice",
        n_results=2,
    )

    assert len(results) <= 2
    assert all(isinstance(r, RetrievalResult) for r in results)


def test_retrieve_with_lesson_filter(populated_retriever: ExerciseRetriever) -> None:
    """Test retrieval with lesson filter."""
    results = populated_retriever.retrieve(
        query="vocabulary",
        lesson=1,
        n_results=5,
    )

    assert all(r.metadata.get("lesson") == 1 for r in results)


def test_retrieve_with_exercise_type_filter(
    populated_retriever: ExerciseRetriever,
) -> None:
    """Test retrieval with exercise type filter."""
    results = populated_retriever.retrieve(
        query="exercise",
        exercise_type="fill_in_blank",
        n_results=5,
    )

    assert all(r.metadata.get("exercise_type") == "fill_in_blank" for r in results)


def test_retrieve_with_skill_filter(populated_retriever: ExerciseRetriever) -> None:
    """Test retrieval with skill focus filter."""
    results = populated_retriever.retrieve(
        query="practice",
        skill_focus="vocabulary",
        n_results=5,
    )

    assert all(r.metadata.get("skill_focus") == "vocabulary" for r in results)


def test_retrieve_with_multiple_filters(
    populated_retriever: ExerciseRetriever,
) -> None:
    """Test retrieval with multiple filters."""
    results = populated_retriever.retrieve(
        query="vocabulary",
        lesson=1,
        exercise_type="fill_in_blank",
        skill_focus="vocabulary",
        n_results=5,
    )

    assert all(r.metadata.get("lesson") == 1 for r in results)
    assert all(r.metadata.get("exercise_type") == "fill_in_blank" for r in results)
    assert all(r.metadata.get("skill_focus") == "vocabulary" for r in results)


def test_get_by_metadata(populated_retriever: ExerciseRetriever) -> None:
    """Test metadata-only retrieval."""
    results = populated_retriever.get_by_metadata(
        lesson=1,
        limit=10,
    )

    assert len(results) == 2
    assert all(r.metadata.get("lesson") == 1 for r in results)
    assert all(r.distance == 0.0 for r in results)


def test_get_by_metadata_no_filters(populated_retriever: ExerciseRetriever) -> None:
    """Test metadata retrieval with no filters returns empty."""
    results = populated_retriever.get_by_metadata(limit=10)

    assert len(results) == 0


def test_retrieve_empty_results() -> None:
    """Test retrieval with no matching documents."""
    with tempfile.TemporaryDirectory() as tmpdir:
        vectorstore = VectorStore(persist_directory=tmpdir)
        retriever = ExerciseRetriever(vectorstore)

        results = retriever.retrieve(
            query="nonexistent topic",
            n_results=5,
        )

        assert len(results) == 0
