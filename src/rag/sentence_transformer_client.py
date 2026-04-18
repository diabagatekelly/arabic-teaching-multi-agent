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
        """Initialize SentenceTransformer client."""
        self.model_name = model_name
        self.dimension = dimension
        # For ZeroGPU: Load on CPU to avoid CUDA init during app startup
        self.model = SentenceTransformer(model_name, device="cpu")

    def embed(self, text: str) -> list[float]:
        """Generate embedding for a single text."""
        embeddings = self.model.encode([text], convert_to_numpy=False, show_progress_bar=False)
        embedding = embeddings[0]

        if hasattr(embedding, "tolist"):
            return embedding.tolist()
        return list(embedding)

    def embed_batch(self, texts: list[str], show_progress: bool = False) -> list[list[float]]:
        """Generate embeddings for multiple texts."""
        if not texts:
            return []

        embeddings = self.model.encode(
            texts, convert_to_numpy=False, show_progress_bar=show_progress
        )

        # Convert to plain Python lists
        if hasattr(embeddings, "tolist"):
            return embeddings.tolist()

        # Fallback: convert each embedding individually
        result = []
        for emb in embeddings:
            if hasattr(emb, "tolist"):
                result.append(emb.tolist())
            elif hasattr(emb, "__iter__"):
                result.append(list(emb))
            else:
                result.append([emb])
        return result

    def get_dimension(self) -> int:
        """Get the dimension of embedding vectors."""
        return self.dimension
