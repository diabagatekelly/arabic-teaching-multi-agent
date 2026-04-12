"""Tests for SentenceTransformer embedding client."""

from unittest.mock import Mock, patch

import pytest

from src.rag.sentence_transformer_client import SentenceTransformerClient


class TestSentenceTransformerClient:
    """Test suite for SentenceTransformerClient."""

    @pytest.fixture
    def mock_model(self):
        """Fixture for mocked SentenceTransformer model."""
        with patch("src.rag.sentence_transformer_client.SentenceTransformer") as mock_st_class:
            mock_model = Mock()
            mock_st_class.return_value = mock_model
            # Mock encode to return dummy embeddings
            mock_model.encode.return_value = [[0.1] * 384, [0.2] * 384]
            yield {"model_class": mock_st_class, "model": mock_model}

    def test_embed_single_text(self, mock_model):
        """Test embedding a single text string."""
        # Mock encode to return single embedding
        mock_model["model"].encode.return_value = [[0.5] * 384]

        client = SentenceTransformerClient()
        embedding = client.embed("This is a test")

        assert len(embedding) == 384
        assert embedding == [0.5] * 384
        mock_model["model"].encode.assert_called_once_with(
            ["This is a test"], convert_to_numpy=False, show_progress_bar=False
        )

    def test_embed_batch_texts(self, mock_model):
        """Test embedding a batch of texts."""
        # Mock encode to return multiple embeddings
        mock_model["model"].encode.return_value = [
            [0.1] * 384,
            [0.2] * 384,
            [0.3] * 384,
        ]

        client = SentenceTransformerClient()
        texts = ["Text 1", "Text 2", "Text 3"]
        embeddings = client.embed_batch(texts)

        assert len(embeddings) == 3
        assert all(len(emb) == 384 for emb in embeddings)
        assert embeddings[0] == [0.1] * 384
        assert embeddings[1] == [0.2] * 384
        assert embeddings[2] == [0.3] * 384
        mock_model["model"].encode.assert_called_once_with(
            texts, convert_to_numpy=False, show_progress_bar=False
        )

    def test_embed_batch_empty_list(self, mock_model):
        """Test embedding empty list returns empty list."""
        client = SentenceTransformerClient()
        embeddings = client.embed_batch([])

        assert embeddings == []
        mock_model["model"].encode.assert_not_called()

    def test_embed_batch_normalizes_to_list(self, mock_model):
        """Test that numpy arrays are converted to lists."""
        import numpy as np

        # Mock encode to return numpy array
        mock_model["model"].encode.return_value = np.array([[0.1] * 384, [0.2] * 384])

        client = SentenceTransformerClient()
        embeddings = client.embed_batch(["Text 1", "Text 2"])

        # Should be converted to Python lists
        assert isinstance(embeddings, list)
        assert all(isinstance(emb, list) for emb in embeddings)
