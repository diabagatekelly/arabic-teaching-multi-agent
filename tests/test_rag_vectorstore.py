"""Tests for RAG vectorstore functionality."""

from __future__ import annotations

import tempfile

import pytest

from rag.vectorstore import VectorStore


@pytest.fixture
def temp_vectorstore() -> VectorStore:
    """Create a temporary vectorstore for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield VectorStore(persist_directory=tmpdir)


def test_vectorstore_initialization(temp_vectorstore: VectorStore) -> None:
    """Test vectorstore initializes correctly."""
    assert temp_vectorstore.collection_name == "exercise_templates"
    assert temp_vectorstore.get_count() == 0


def test_add_documents(temp_vectorstore: VectorStore) -> None:
    """Test adding documents to vectorstore."""
    documents = ["Test document 1", "Test document 2"]
    metadatas = [{"lesson": 1, "type": "vocab"}, {"lesson": 2, "type": "grammar"}]
    ids = ["doc1", "doc2"]

    temp_vectorstore.add_documents(documents, metadatas, ids)

    assert temp_vectorstore.get_count() == 2


def test_query_documents(temp_vectorstore: VectorStore) -> None:
    """Test querying documents from vectorstore."""
    documents = ["vocabulary practice", "grammar exercise"]
    metadatas = [{"lesson": 1}, {"lesson": 2}]
    ids = ["doc1", "doc2"]

    temp_vectorstore.add_documents(documents, metadatas, ids)

    results = temp_vectorstore.query(query_texts=["vocabulary"], n_results=1)

    assert len(results["documents"][0]) == 1
    assert "vocabulary" in results["documents"][0][0]


def test_query_with_metadata_filter(temp_vectorstore: VectorStore) -> None:
    """Test querying with metadata filters."""
    documents = ["lesson 1 vocab", "lesson 2 grammar"]
    metadatas = [{"lesson": 1, "type": "vocab"}, {"lesson": 2, "type": "grammar"}]
    ids = ["doc1", "doc2"]

    temp_vectorstore.add_documents(documents, metadatas, ids)

    results = temp_vectorstore.query(
        query_texts=["vocab"],
        n_results=5,
        where={"lesson": 1},
    )

    assert len(results["documents"][0]) == 1
    assert results["metadatas"][0][0]["lesson"] == 1


def test_reset_collection(temp_vectorstore: VectorStore) -> None:
    """Test resetting the collection."""
    documents = ["test"]
    metadatas = [{"lesson": 1}]
    ids = ["doc1"]

    temp_vectorstore.add_documents(documents, metadatas, ids)
    assert temp_vectorstore.get_count() == 1

    temp_vectorstore.reset()
    assert temp_vectorstore.get_count() == 0
