"""Tests for RAG ingestion pipeline."""

from pathlib import Path
from unittest.mock import Mock

import pytest

from src.rag.rag_ingestion import RAGIngestion


class TestRAGIngestion:
    """Test suite for RAGIngestion."""

    @pytest.fixture
    def mock_parser(self):
        """Fixture for mocked MarkdownParser."""
        mock = Mock()
        mock.parse_directory.return_value = [
            {
                "text": "Section 1\n\nContent 1",
                "metadata": {
                    "lesson_number": 1,
                    "lesson_name": "Test",
                    "section_title": "Section 1",
                    "source_file": "lesson_01.md",
                    "doc_type": "lesson",
                },
            },
            {
                "text": "Section 2\n\nContent 2",
                "metadata": {
                    "lesson_number": 1,
                    "lesson_name": "Test",
                    "section_title": "Section 2",
                    "source_file": "lesson_01.md",
                    "doc_type": "lesson",
                },
            },
        ]
        return mock

    @pytest.fixture
    def mock_embedder(self):
        """Fixture for mocked embedding model."""
        mock = Mock()
        mock.embed_batch.return_value = [[0.1] * 384, [0.2] * 384]
        mock.get_dimension.return_value = 384
        return mock

    @pytest.fixture
    def mock_vector_db(self):
        """Fixture for mocked vector database."""
        mock = Mock()
        mock.upsert.return_value = {
            "batches": 1,
            "total_vectors": 2,
            "upserted_count": 2,
        }
        return mock

    def test_process_directory(self, mock_parser, mock_embedder, mock_vector_db):
        """Test processing directory end-to-end."""
        ingestion = RAGIngestion(
            parser=mock_parser, embedder=mock_embedder, vector_db=mock_vector_db
        )

        result = ingestion.process_directory(Path("data/rag_database"))

        # Verify parser was called
        mock_parser.parse_directory.assert_called_once_with(Path("data/rag_database"))

        # Verify embedder was called with texts
        mock_embedder.embed_batch.assert_called_once()
        texts_arg = mock_embedder.embed_batch.call_args[0][0]
        assert texts_arg == ["Section 1\n\nContent 1", "Section 2\n\nContent 2"]

        # Verify vector_db was called with vectors
        mock_vector_db.upsert.assert_called_once()
        vectors_arg = mock_vector_db.upsert.call_args[0][0]
        assert len(vectors_arg) == 2
        assert vectors_arg[0]["values"] == [0.1] * 384
        assert vectors_arg[1]["values"] == [0.2] * 384
        assert vectors_arg[0]["metadata"]["lesson_number"] == 1
        assert vectors_arg[0]["metadata"]["section_title"] == "Section 1"

        # Verify result
        assert result["chunks_parsed"] == 2
        assert result["vectors_created"] == 2
        assert result["upserted_count"] == 2
        assert result["mismatch"] is False

    def test_process_directory_empty(self, mock_parser, mock_embedder, mock_vector_db):
        """Test processing directory with no chunks."""
        mock_parser.parse_directory.return_value = []

        ingestion = RAGIngestion(
            parser=mock_parser, embedder=mock_embedder, vector_db=mock_vector_db
        )

        result = ingestion.process_directory(Path("data/rag_database"))

        assert result["chunks_parsed"] == 0
        assert result["vectors_created"] == 0
        mock_embedder.embed_batch.assert_not_called()
        mock_vector_db.upsert.assert_not_called()

    def test_generate_vector_id(self, mock_parser, mock_embedder, mock_vector_db):
        """Test vector ID generation is deterministic and unique."""
        ingestion = RAGIngestion(
            parser=mock_parser, embedder=mock_embedder, vector_db=mock_vector_db
        )

        chunk1 = {
            "text": "Test",
            "metadata": {"source_file": "file1.md", "section_title": "Intro"},
        }
        chunk2 = {
            "text": "Test",
            "metadata": {"source_file": "file1.md", "section_title": "Body"},
        }
        chunk3 = {
            "text": "Test",
            "metadata": {"source_file": "file2.md", "section_title": "Intro"},
        }

        id1 = ingestion._generate_vector_id(chunk1)
        id2 = ingestion._generate_vector_id(chunk2)
        id3 = ingestion._generate_vector_id(chunk3)

        # IDs should be different for different chunks
        assert id1 != id2
        assert id1 != id3
        assert id2 != id3

        # Same chunk should produce same ID (deterministic)
        assert ingestion._generate_vector_id(chunk1) == id1

    def test_generate_vector_id_same_section_different_text(
        self, mock_parser, mock_embedder, mock_vector_db
    ):
        """Test vector IDs are unique even for multiple chunks from same section."""
        ingestion = RAGIngestion(
            parser=mock_parser, embedder=mock_embedder, vector_db=mock_vector_db
        )

        # Multiple chunks from same section (e.g., from chunking long content)
        chunk1 = {
            "text": "First part of content",
            "metadata": {"source_file": "file1.md", "section_title": "Intro"},
        }
        chunk2 = {
            "text": "Second part of content",
            "metadata": {"source_file": "file1.md", "section_title": "Intro"},
        }

        id1 = ingestion._generate_vector_id(chunk1)
        id2 = ingestion._generate_vector_id(chunk2)

        # IDs must be different to avoid collision
        assert id1 != id2

    def test_create_vectors_from_chunks(self, mock_parser, mock_embedder, mock_vector_db):
        """Test vector creation from chunks."""
        ingestion = RAGIngestion(
            parser=mock_parser, embedder=mock_embedder, vector_db=mock_vector_db
        )

        chunks = [
            {
                "text": "Text 1",
                "metadata": {"source_file": "f1.md", "section_title": "S1"},
            },
            {
                "text": "Text 2",
                "metadata": {"source_file": "f2.md", "section_title": "S2"},
            },
        ]
        embeddings = [[0.1] * 384, [0.2] * 384]

        vectors = ingestion._create_vectors_from_chunks(chunks, embeddings)

        assert len(vectors) == 2
        # Verify ID is a non-empty string (not just non-None)
        assert vectors[0]["id"]
        assert isinstance(vectors[0]["id"], str)
        assert len(vectors[0]["id"]) > 0
        assert vectors[0]["values"] == [0.1] * 384
        assert vectors[0]["metadata"] == {
            "source_file": "f1.md",
            "section_title": "S1",
            "text": "Text 1",
        }
        assert vectors[1]["values"] == [0.2] * 384
        assert vectors[1]["metadata"]["text"] == "Text 2"

    def test_sanitize_metadata_complex_types(self, mock_parser, mock_embedder, mock_vector_db):
        """Test metadata sanitization converts complex types to valid JSON."""
        import json

        ingestion = RAGIngestion(
            parser=mock_parser, embedder=mock_embedder, vector_db=mock_vector_db
        )

        metadata = {
            "simple": "test",
            "dict_field": {"key": "value"},
            "list_of_dicts": [{"a": 1}, {"b": 2}],
            "mixed_list": ["string", 123, {"nested": "dict"}],
            "str_list": ["a", "b", "c"],
        }

        sanitized = ingestion._sanitize_metadata(metadata)

        # Simple types pass through
        assert sanitized["simple"] == "test"

        # list[str] should be preserved, not JSON-encoded
        assert "str_list" in sanitized
        assert sanitized["str_list"] == ["a", "b", "c"]

        # Verify complex types are converted to valid JSON (round-trip test)
        assert json.loads(sanitized["dict_field"]) == {"key": "value"}
        assert json.loads(sanitized["list_of_dicts"]) == [{"a": 1}, {"b": 2}]
        assert json.loads(sanitized["mixed_list"]) == ["string", 123, {"nested": "dict"}]

    def test_sanitize_metadata_skips_none(self, mock_parser, mock_embedder, mock_vector_db):
        """Test metadata sanitization skips None values."""
        ingestion = RAGIngestion(
            parser=mock_parser, embedder=mock_embedder, vector_db=mock_vector_db
        )

        metadata = {"field1": "value", "field2": None, "field3": "another"}

        sanitized = ingestion._sanitize_metadata(metadata)

        assert "field1" in sanitized
        assert "field2" not in sanitized
        assert "field3" in sanitized

    def test_process_directory_mismatch_detection(self, mock_parser, mock_embedder, mock_vector_db):
        """Test mismatch detection when upserted count differs from vectors created."""
        # Mock upsert to return different count than vectors created
        mock_vector_db.upsert.return_value = {
            "batches": 1,
            "total_vectors": 2,
            "upserted_count": 1,  # Mismatch: only 1 upserted instead of 2
        }

        ingestion = RAGIngestion(
            parser=mock_parser, embedder=mock_embedder, vector_db=mock_vector_db
        )

        result = ingestion.process_directory(Path("data/rag_database"))

        # Verify mismatch is detected
        assert result["vectors_created"] == 2
        assert result["upserted_count"] == 1
        assert result["mismatch"] is True

    def test_process_directory_missing_upserted_count(
        self, mock_parser, mock_embedder, mock_vector_db
    ):
        """Test handling when API doesn't return upserted_count."""
        # Mock upsert to return response without upserted_count
        mock_vector_db.upsert.return_value = {
            "batches": 1,
            "total_vectors": 2,
            # Missing upserted_count
        }

        ingestion = RAGIngestion(
            parser=mock_parser, embedder=mock_embedder, vector_db=mock_vector_db
        )

        result = ingestion.process_directory(Path("data/rag_database"))

        # Verify fallback to vectors_created
        assert result["upserted_count"] == 2  # Falls back to vectors_created
        assert result["mismatch"] is False
