"""Tests for Pinecone client."""

from unittest.mock import Mock, patch

import pytest

from src.rag.pinecone_client import PineconeClient


class TestPineconeClient:
    """Test suite for PineconeClient."""

    @pytest.fixture
    def mock_pinecone(self):
        """Fixture for mocked Pinecone client."""
        with patch("src.rag.pinecone_client.Pinecone") as mock_pinecone_class:
            mock_pc = Mock()
            mock_pinecone_class.return_value = mock_pc
            mock_pc.list_indexes.return_value = []
            mock_index = Mock()
            mock_pc.Index.return_value = mock_index

            yield {
                "pinecone_class": mock_pinecone_class,
                "pc": mock_pc,
                "index": mock_index,
            }

    def test_init_with_api_key(self, mock_pinecone):
        """Test initialization with explicit API key."""
        client = PineconeClient(api_key="test-key-123")

        assert client.api_key == "test-key-123"
        assert client.index_name == "arabic-teaching"
        assert client.dimension == 384
        assert client.pc is mock_pinecone["pc"]
        assert client.index is mock_pinecone["index"]
        mock_pinecone["pinecone_class"].assert_called_once_with(api_key="test-key-123")

    @patch.dict("os.environ", {"PINECONE_API_KEY": "env-key-456"}, clear=True)
    def test_init_from_env(self, mock_pinecone):
        """Test initialization from environment variable."""
        client = PineconeClient()

        assert client.api_key == "env-key-456"
        assert client.pc is mock_pinecone["pc"]
        assert client.index is mock_pinecone["index"]

    @patch.dict("os.environ", {}, clear=True)
    @patch("src.rag.pinecone_client.load_dotenv")
    def test_init_without_api_key_raises_error(self, mock_load_dotenv, mock_pinecone):
        """Test initialization without API key raises ValueError."""
        with pytest.raises(ValueError, match="PINECONE_API_KEY not found"):
            PineconeClient()

    def test_creates_index_if_not_exists(self, mock_pinecone):
        """Test creates new index if it doesn't exist."""
        _client = PineconeClient(api_key="test-key")

        mock_pinecone["pc"].create_index.assert_called_once()
        call_kwargs = mock_pinecone["pc"].create_index.call_args[1]
        assert call_kwargs["name"] == "arabic-teaching"
        assert call_kwargs["dimension"] == 384
        assert call_kwargs["metric"] == "cosine"

        # Verify ServerlessSpec parameters
        spec = call_kwargs["spec"]
        assert spec.cloud == "aws"
        assert spec.region == "us-east-1"

    def test_uses_existing_index(self, mock_pinecone):
        """Test uses existing index if it exists."""
        # Mock list_indexes to return existing index
        mock_index_obj = Mock()
        mock_index_obj.name = "arabic-teaching"
        mock_pinecone["pc"].list_indexes.return_value = [mock_index_obj]

        # Mock describe_index to return matching dimension
        mock_pinecone["pc"].describe_index.return_value = Mock(dimension=384)

        _client = PineconeClient(api_key="test-key")

        mock_pinecone["pc"].create_index.assert_not_called()
        mock_pinecone["pc"].Index.assert_called_once_with("arabic-teaching")
        mock_pinecone["pc"].describe_index.assert_called_once_with("arabic-teaching")

    def test_dimension_mismatch_raises_error(self, mock_pinecone):
        """Test raises error when existing index has different dimension."""
        # Mock list_indexes to return existing index
        mock_index_obj = Mock()
        mock_index_obj.name = "arabic-teaching"
        mock_pinecone["pc"].list_indexes.return_value = [mock_index_obj]

        # Mock describe_index to return DIFFERENT dimension
        mock_pinecone["pc"].describe_index.return_value = Mock(dimension=512)

        with pytest.raises(
            ValueError, match="Index 'arabic-teaching' exists with dimension 512, expected 384"
        ):
            PineconeClient(api_key="test-key")

    def test_custom_cloud_and_region(self, mock_pinecone):
        """Test allows custom cloud and region."""
        _client = PineconeClient(api_key="test-key", cloud="gcp", region="us-central1")

        call_kwargs = mock_pinecone["pc"].create_index.call_args[1]
        spec = call_kwargs["spec"]
        assert spec.cloud == "gcp"
        assert spec.region == "us-central1"

    def test_upsert_single_batch(self, mock_pinecone):
        """Test upsert with single batch returns actual Pinecone counts."""
        mock_pinecone["index"].upsert.return_value = {"upserted_count": 5}

        client = PineconeClient(api_key="test-key")

        vectors = [
            {"id": f"vec{i}", "values": [0.1] * 384, "metadata": {"doc": f"doc{i}"}}
            for i in range(5)
        ]

        result = client.upsert(vectors)

        assert result["batches"] == 1
        assert result["total_vectors"] == 5
        assert result["upserted_count"] == 5  # Actual count from Pinecone
        mock_pinecone["index"].upsert.assert_called_once_with(vectors=vectors)

    def test_upsert_multiple_batches(self, mock_pinecone):
        """Test upsert with multiple batches aggregates actual counts."""
        # Return different counts per batch to simulate real responses
        mock_pinecone["index"].upsert.side_effect = [
            {"upserted_count": 100},
            {"upserted_count": 100},
            {"upserted_count": 50},
        ]

        client = PineconeClient(api_key="test-key")

        # 250 vectors with batch_size=100 should create 3 batches
        vectors = [
            {"id": f"vec{i}", "values": [0.1] * 384, "metadata": {"doc": f"doc{i}"}}
            for i in range(250)
        ]

        result = client.upsert(vectors, batch_size=100)

        assert result["batches"] == 3
        assert result["total_vectors"] == 250
        assert result["upserted_count"] == 250  # Sum of actual counts: 100+100+50
        assert mock_pinecone["index"].upsert.call_count == 3

    def test_upsert_empty_vectors(self, mock_pinecone):
        """Test upsert with empty vector list."""
        client = PineconeClient(api_key="test-key")

        result = client.upsert([])

        assert result["batches"] == 0
        assert result["total_vectors"] == 0
        mock_pinecone["index"].upsert.assert_not_called()

    def test_query(self, mock_pinecone):
        """Test query method."""
        mock_pinecone["index"].query.return_value = {
            "matches": [
                {"id": "vec1", "score": 0.95, "metadata": {"text": "test"}},
                {"id": "vec2", "score": 0.85, "metadata": {"text": "test2"}},
            ]
        }

        client = PineconeClient(api_key="test-key")

        query_vector = [0.5] * 384
        result = client.query(query_vector, top_k=5, filter={"lesson_number": 1})

        mock_pinecone["index"].query.assert_called_once_with(
            vector=query_vector,
            top_k=5,
            filter={"lesson_number": 1},
            include_metadata=True,
        )
        assert len(result["matches"]) == 2

    def test_delete_all(self, mock_pinecone):
        """Test delete_all method."""
        client = PineconeClient(api_key="test-key")
        client.delete_all()

        mock_pinecone["index"].delete.assert_called_once_with(delete_all=True)

    def test_get_stats(self, mock_pinecone):
        """Test get_stats method."""
        mock_pinecone["index"].describe_index_stats.return_value = {
            "total_vector_count": 100,
            "dimension": 384,
        }

        client = PineconeClient(api_key="test-key")
        stats = client.get_stats()

        assert stats["total_vector_count"] == 100
        assert stats["dimension"] == 384
