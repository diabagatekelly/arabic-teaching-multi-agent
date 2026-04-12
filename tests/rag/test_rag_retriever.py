"""Tests for RAG retrieval interface."""

from unittest.mock import Mock

import pytest

from src.rag.rag_retriever import RAGRetriever


class TestRAGRetriever:
    """Test suite for RAGRetriever."""

    @pytest.fixture
    def mock_embedder(self):
        """Fixture for mocked embedding model."""
        mock = Mock()
        mock.embed.return_value = [0.5] * 384
        return mock

    @pytest.fixture
    def mock_vector_db(self):
        """Fixture for mocked vector database."""
        mock = Mock()
        mock.query.return_value = {
            "matches": [
                {
                    "id": "vec1",
                    "score": 0.95,
                    "metadata": {
                        "text": "Arabic nouns are masculine or feminine.",
                        "source_file": "lesson_01.md",
                        "section_title": "Gender",
                        "lesson_number": 1,
                    },
                },
                {
                    "id": "vec2",
                    "score": 0.85,
                    "metadata": {
                        "text": "The definite article is ال (al-).",
                        "source_file": "lesson_01.md",
                        "section_title": "Definite Article",
                        "lesson_number": 1,
                    },
                },
            ]
        }
        return mock

    def test_retrieve_basic(self, mock_embedder, mock_vector_db):
        """Test basic retrieval without filters."""
        retriever = RAGRetriever(embedder=mock_embedder, vector_db=mock_vector_db)

        results = retriever.retrieve("What is noun gender?", top_k=2)

        # Verify embedder was called
        mock_embedder.embed.assert_called_once_with("What is noun gender?")

        mock_vector_db.query.assert_called_once_with(
            vector=[0.5] * 384, top_k=2, filter=None, include_metadata=True
        )

        # Verify results structure
        assert len(results) == 2
        assert results[0]["text"] == "Arabic nouns are masculine or feminine."
        assert results[0]["score"] == 0.95
        assert results[0]["metadata"]["lesson_number"] == 1
        assert results[1]["score"] == 0.85

    def test_retrieve_with_filter(self, mock_embedder, mock_vector_db):
        """Test retrieval with metadata filters."""
        retriever = RAGRetriever(embedder=mock_embedder, vector_db=mock_vector_db)

        retriever.retrieve("test query", top_k=3, metadata_filter={"lesson_number": 1})

        mock_vector_db.query.assert_called_once()
        assert mock_vector_db.query.call_args[1]["filter"] == {"lesson_number": 1}

    def test_retrieve_empty_results(self, mock_embedder, mock_vector_db):
        """Test retrieval when no matches found."""
        mock_vector_db.query.return_value = {"matches": []}

        retriever = RAGRetriever(embedder=mock_embedder, vector_db=mock_vector_db)
        results = retriever.retrieve("test query")

        assert results == []

    @pytest.mark.parametrize(
        "method,kwargs,expected_filter",
        [
            ("retrieve_by_lesson", {"lesson_number": 1, "top_k": 3}, {"lesson_number": 1}),
            (
                "retrieve_by_grammar_point",
                {"grammar_point": "gender_agreement"},
                {"grammar_point": "gender_agreement"},
            ),
            ("retrieve_by_difficulty", {"difficulty": "beginner"}, {"difficulty": "beginner"}),
        ],
    )
    def test_convenience_filter_methods(
        self, mock_embedder, mock_vector_db, method, kwargs, expected_filter
    ):
        """Test that convenience methods correctly construct filter dicts."""
        retriever = RAGRetriever(embedder=mock_embedder, vector_db=mock_vector_db)

        getattr(retriever, method)("test query", **kwargs)

        mock_vector_db.query.assert_called_once()
        assert mock_vector_db.query.call_args[1]["filter"] == expected_filter

    def test_format_results(self, mock_embedder, mock_vector_db):
        """Test result formatting extracts text, score, and metadata."""
        retriever = RAGRetriever(embedder=mock_embedder, vector_db=mock_vector_db)

        results = retriever.retrieve("test query")

        # Results should be formatted with text, score, and metadata
        assert all("text" in r for r in results)
        assert all("score" in r for r in results)
        assert all("metadata" in r for r in results)

        # text should be extracted from metadata
        assert results[0]["text"] == "Arabic nouns are masculine or feminine."

        # metadata should not contain redundant text field
        assert "text" not in results[0]["metadata"]

    def test_retrieve_with_min_score(self, mock_embedder, mock_vector_db):
        """Test filtering results by minimum score threshold."""
        # Mock results with varying scores
        mock_vector_db.query.return_value = {
            "matches": [
                {
                    "id": "vec1",
                    "score": 0.95,
                    "metadata": {"text": "High relevance", "source_file": "f1.md"},
                },
                {
                    "id": "vec2",
                    "score": 0.60,
                    "metadata": {"text": "Medium relevance", "source_file": "f2.md"},
                },
                {
                    "id": "vec3",
                    "score": 0.30,
                    "metadata": {"text": "Low relevance", "source_file": "f3.md"},
                },
            ]
        }

        retriever = RAGRetriever(embedder=mock_embedder, vector_db=mock_vector_db)
        results = retriever.retrieve("test query", top_k=10, min_score=0.5)

        # Only results with score >= 0.5 should be returned
        assert len(results) == 2
        assert results[0]["score"] == 0.95
        assert results[1]["score"] == 0.60
        assert all(r["score"] >= 0.5 for r in results)
