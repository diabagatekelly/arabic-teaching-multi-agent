"""Abstract interface for embedding model operations."""

from typing import Protocol


class EmbeddingModel(Protocol):
    """Protocol defining the interface for embedding model operations."""

    def embed(self, text: str) -> list[float]:
        """
        Generate embedding for a single text.

        Args:
            text: Text to embed

        Returns:
            List of floats representing the embedding vector
        """
        ...

    def embed_batch(self, texts: list[str], show_progress: bool = False) -> list[list[float]]:
        """
        Generate embeddings for multiple texts.

        Args:
            texts: List of texts to embed
            show_progress: Show progress bar during embedding

        Returns:
            List of embedding vectors
        """
        ...

    def get_dimension(self) -> int:
        """
        Get the dimension of embedding vectors.

        Returns:
            Embedding dimension
        """
        ...
