"""Abstract interface for vector database operations."""

from typing import Any, Protocol


class VectorDatabase(Protocol):
    """Protocol defining the interface for vector database operations."""

    def upsert(self, vectors: list[dict[str, Any]], batch_size: int = 100) -> dict[str, Any]:
        """
        Upsert vectors to the database.

        Args:
            vectors: List of dicts with {id, values, metadata}
            batch_size: Number of vectors per batch

        Returns:
            Dict with at least:
            - batches: Number of batches processed
            - total_vectors: Number of input vectors
            Implementations may include additional fields like:
            - upserted_count: Actual count from database (may differ if errors occur)
        """
        ...

    def query(
        self,
        vector: list[float],
        top_k: int = 5,
        filter: dict[str, Any] | None = None,
        include_metadata: bool = True,
    ) -> dict[str, Any]:
        """
        Query database for similar vectors.

        Args:
            vector: Query embedding vector
            top_k: Number of results to return
            filter: Metadata filter
            include_metadata: Include metadata in response

        Returns:
            Query results from database
        """
        ...

    def delete_all(self) -> None:
        """Delete all vectors from the database."""
        ...

    def get_stats(self) -> dict[str, Any]:
        """Get database statistics."""
        ...
