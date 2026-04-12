"""Pinecone client for vector database operations."""

import os
from typing import Any

from dotenv import load_dotenv
from pinecone import Pinecone, ServerlessSpec


class PineconeClient:
    """
    Pinecone implementation of VectorDatabase protocol.

    Provides vector database operations using Pinecone's serverless infrastructure.
    """

    def __init__(
        self,
        api_key: str | None = None,
        index_name: str = "arabic-teaching",
        dimension: int = 384,  # all-MiniLM-L6-v2 embedding size
    ):
        """
        Initialize Pinecone client.

        Args:
            api_key: Falls back to PINECONE_API_KEY environment variable
            dimension: Must match embedding model (384 for all-MiniLM-L6-v2)
        """
        if api_key is None:
            load_dotenv()
            api_key = os.getenv("PINECONE_API_KEY")

        self.api_key = api_key
        if not self.api_key:
            raise ValueError("PINECONE_API_KEY not found in environment")

        self.index_name = index_name
        self.dimension = dimension

        self.pc = Pinecone(api_key=self.api_key)
        self.index = self._get_or_create_index()

    def _get_or_create_index(self) -> Any:
        """Get existing index or create new one if it doesn't exist."""
        existing_indexes = [index.name for index in self.pc.list_indexes()]

        if self.index_name not in existing_indexes:
            self.pc.create_index(
                name=self.index_name,
                dimension=self.dimension,
                metric="cosine",
                spec=ServerlessSpec(cloud="aws", region="us-east-1"),
            )

        return self.pc.Index(self.index_name)

    def upsert(self, vectors: list[dict[str, Any]], batch_size: int = 100) -> dict[str, Any]:
        """
        Upsert vectors to Pinecone index.

        Args:
            vectors: List of dicts with {id, values, metadata}
            batch_size: Number of vectors per batch

        Returns:
            Upsert response with batches count and total vectors
        """
        results = []
        for i in range(0, len(vectors), batch_size):
            batch = vectors[i : i + batch_size]
            result = self.index.upsert(vectors=batch)
            results.append(result)
        return {"batches": len(results), "total_vectors": len(vectors)}

    def query(
        self,
        vector: list[float],
        top_k: int = 5,
        filter: dict[str, Any] | None = None,
        include_metadata: bool = True,
    ) -> dict[str, Any]:
        """
        Query Pinecone index for similar vectors.

        Args:
            vector: Query embedding vector
            top_k: Number of results to return
            filter: Metadata filter (e.g., {"lesson_number": 1})
            include_metadata: Include metadata in response

        Returns:
            Query results from Pinecone
        """
        return self.index.query(
            vector=vector,
            top_k=top_k,
            filter=filter,
            include_metadata=include_metadata,
        )

    def delete_all(self) -> None:
        """Delete all vectors from the index."""
        self.index.delete(delete_all=True)

    def get_stats(self) -> dict[str, Any]:
        """Get index statistics."""
        return self.index.describe_index_stats()
