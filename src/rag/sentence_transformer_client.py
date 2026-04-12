"""SentenceTransformer-based embedding client."""

from __future__ import annotations

from sentence_transformers import SentenceTransformer


class SentenceTransformerClient:
    """Client for generating embeddings using SentenceTransformers."""

    def __init__(
        self,
        model_name: str = "sentence-transformers/all-MiniLM-L6-v2",
        dimension: int = 384,
    ):
        """
        Initialize SentenceTransformer client.

        Args:
            model_name: HuggingFace model name
            dimension: Expected embedding dimension
        """
        self.model_name = model_name
        self.dimension = dimension
        self.model = SentenceTransformer(model_name)

    def embed(self, text: str) -> list[float]:
        """
        Generate embedding for a single text.

        Args:
            text: Text to embed

        Returns:
            List of floats representing the embedding vector
        """
        embeddings = self.model.encode([text], convert_to_numpy=False, show_progress_bar=False)
        return embeddings[0]

    def embed_batch(self, texts: list[str], show_progress: bool = False) -> list[list[float]]:
        """
        Generate embeddings for multiple texts.

        Args:
            texts: List of texts to embed
            show_progress: Show progress bar during embedding

        Returns:
            List of embedding vectors
        """
        if not texts:
            return []

        embeddings = self.model.encode(
            texts, convert_to_numpy=False, show_progress_bar=show_progress
        )

        # Convert numpy arrays to lists if needed
        return embeddings.tolist() if hasattr(embeddings, "tolist") else embeddings

    def get_dimension(self) -> int:
        """
        Get the dimension of embedding vectors.

        Returns:
            Embedding dimension
        """
        return self.dimension
