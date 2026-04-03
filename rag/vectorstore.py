"""
ChromaDB vectorstore configuration and initialization.
"""

from __future__ import annotations

import os
from typing import Any

import chromadb
from chromadb.config import Settings


class VectorStore:
    """Manages ChromaDB vectorstore for exercise templates."""

    def __init__(self, persist_directory: str = "data/vectorstore") -> None:
        """
        Initialize ChromaDB client.

        Args:
            persist_directory: Directory to persist the vectorstore
        """
        self.persist_directory = persist_directory
        os.makedirs(persist_directory, exist_ok=True)

        self.client = chromadb.PersistentClient(
            path=persist_directory,
            settings=Settings(anonymized_telemetry=False),
        )

        self.collection_name = "exercise_templates"
        self._collection: chromadb.Collection | None = None

    @property
    def collection(self) -> chromadb.Collection:
        """Get or create the exercise templates collection."""
        if self._collection is None:
            self._collection = self.client.get_or_create_collection(
                name=self.collection_name,
                metadata={"description": "Arabic learning exercise templates"},
            )
        return self._collection

    def add_documents(
        self,
        documents: list[str],
        metadatas: list[dict[str, Any]],
        ids: list[str],
    ) -> None:
        """
        Add documents to the collection.

        Args:
            documents: List of document texts
            metadatas: List of metadata dicts
            ids: List of unique document IDs
        """
        self.collection.add(
            documents=documents,
            metadatas=metadatas,  # type: ignore
            ids=ids,
        )

    def query(
        self,
        query_texts: list[str],
        n_results: int = 5,
        where: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """
        Query the collection.

        Args:
            query_texts: List of query strings
            n_results: Number of results to return
            where: Optional metadata filter

        Returns:
            Query results with documents, metadatas, and distances
        """
        result = self.collection.query(
            query_texts=query_texts,
            n_results=n_results,
            where=where,
        )
        return result  # type: ignore

    def get_count(self) -> int:
        """Get the number of documents in the collection."""
        return self.collection.count()  # type: ignore

    def reset(self) -> None:
        """Delete and recreate the collection."""
        self.client.delete_collection(name=self.collection_name)
        self._collection = None
