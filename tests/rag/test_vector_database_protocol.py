"""Tests demonstrating VectorDatabase protocol usage and benefits."""

from typing import Any

from src.rag.pinecone_client import PineconeClient
from src.rag.vector_database import VectorDatabase


class MockVectorDatabase:
    """Mock implementation of VectorDatabase for testing."""

    def __init__(self) -> None:
        self.vectors: dict[str, dict[str, Any]] = {}
        self.upsert_called = False
        self.query_called = False

    def upsert(self, vectors: list[dict[str, Any]], batch_size: int = 100) -> dict[str, Any]:
        self.upsert_called = True
        for vec in vectors:
            self.vectors[vec["id"]] = vec
        return {"batches": 1, "total_vectors": len(vectors)}

    def query(
        self,
        vector: list[float],
        top_k: int = 5,
        filter: dict[str, Any] | None = None,
        include_metadata: bool = True,
    ) -> dict[str, Any]:
        self.query_called = True
        return {"matches": []}

    def delete_all(self) -> None:
        self.vectors.clear()

    def get_stats(self) -> dict[str, Any]:
        return {"total_vector_count": len(self.vectors)}


def process_documents(vector_db: VectorDatabase, documents: list[dict[str, Any]]) -> int:
    """
    Example function that depends on VectorDatabase abstraction, not concrete implementation.

    This function works with ANY implementation of VectorDatabase (Pinecone, mock, etc.).
    """
    result = vector_db.upsert(documents)
    return result["total_vectors"]


class TestVectorDatabaseProtocol:
    """Test VectorDatabase protocol and dependency inversion."""

    def test_mock_implementation_satisfies_protocol(self) -> None:
        """Test that MockVectorDatabase satisfies VectorDatabase protocol."""
        mock_db: VectorDatabase = MockVectorDatabase()

        vectors = [{"id": "test1", "values": [0.1] * 384, "metadata": {"text": "hello"}}]

        result = mock_db.upsert(vectors)
        assert result["total_vectors"] == 1
        assert mock_db.upsert_called

    def test_pinecone_satisfies_protocol(self) -> None:
        """Test that PineconeClient satisfies VectorDatabase protocol."""
        from unittest.mock import Mock, patch

        with patch("src.rag.pinecone_client.Pinecone") as mock_pinecone_class:
            mock_pc = Mock()
            mock_pinecone_class.return_value = mock_pc
            mock_pc.list_indexes.return_value = []
            mock_index = Mock()
            mock_pc.Index.return_value = mock_index
            mock_index.upsert.return_value = {"upserted_count": 1}

            client: VectorDatabase = PineconeClient(api_key="test-key")

            vectors = [{"id": "test1", "values": [0.1] * 384, "metadata": {"text": "hello"}}]
            result = client.upsert(vectors)

            assert result["total_vectors"] == 1

    def test_function_works_with_any_implementation(self) -> None:
        """
        Test that functions depending on VectorDatabase work with any implementation.

        Demonstrates DIP benefit: easy to test, easy to swap providers.
        """
        mock_db = MockVectorDatabase()

        documents = [
            {"id": "doc1", "values": [0.1] * 384, "metadata": {"text": "test1"}},
            {"id": "doc2", "values": [0.2] * 384, "metadata": {"text": "test2"}},
        ]

        count = process_documents(mock_db, documents)

        assert count == 2
        assert len(mock_db.vectors) == 2
        assert "doc1" in mock_db.vectors
        assert "doc2" in mock_db.vectors
