"""RAG ingestion pipeline for processing and uploading documents to vector database."""

from __future__ import annotations

import hashlib
import json
import logging
from pathlib import Path
from typing import Any

from src.rag.embedding_model import EmbeddingModel
from src.rag.markdown_parser import MarkdownParser
from src.rag.vector_database import VectorDatabase

logger = logging.getLogger(__name__)


class RAGIngestion:
    """Pipeline for ingesting RAG documents into vector database."""

    def __init__(
        self,
        parser: MarkdownParser,
        embedder: EmbeddingModel,
        vector_db: VectorDatabase,
    ):
        """
        Initialize RAG ingestion pipeline.

        Args:
            parser: Markdown parser for extracting chunks
            embedder: Embedding model for generating vectors
            vector_db: Vector database for storing embeddings
        """
        self.parser = parser
        self.embedder = embedder
        self.vector_db = vector_db

    def process_directory(
        self,
        directory: Path,
        show_progress: bool = False,
        batch_size: int = 100,
    ) -> dict[str, Any]:
        """
        Process all markdown files in directory and upload to vector database.

        Args:
            directory: Directory containing markdown files
            show_progress: Show progress bar during embedding
            batch_size: Batch size for vector database upload

        Returns:
            Dict with processing statistics
        """
        # Parse all markdown files
        chunks = self.parser.parse_directory(directory)

        if not chunks:
            return {
                "chunks_parsed": 0,
                "vectors_created": 0,
            }

        # Extract texts for embedding
        texts = [chunk["text"] for chunk in chunks]

        # Generate embeddings
        embeddings = self.embedder.embed_batch(texts, show_progress=show_progress)

        # Create vectors with metadata
        vectors = self._create_vectors_from_chunks(chunks, embeddings)

        # Upload to vector database
        upsert_result = self.vector_db.upsert(vectors, batch_size=batch_size)

        # Handle API response with proper error detection
        upserted_count = upsert_result.get("upserted_count")
        if upserted_count is None:
            logger.warning(
                "Vector database did not return upserted_count, using vectors_created as fallback"
            )
            upserted_count = len(vectors)

        # Detect potential issues with partial failures
        mismatch = upserted_count != len(vectors)
        if mismatch:
            logger.warning(
                f"Upsert mismatch detected: created {len(vectors)} vectors, "
                f"but upserted {upserted_count}"
            )

        return {
            "chunks_parsed": len(chunks),
            "vectors_created": len(vectors),
            "upserted_count": upserted_count,
            "batches": upsert_result.get("batches", 0),
            "mismatch": mismatch,
        }

    def _create_vectors_from_chunks(
        self, chunks: list[dict[str, Any]], embeddings: list[list[float]]
    ) -> list[dict[str, Any]]:
        """
        Create vector database entries from chunks and embeddings.

        Args:
            chunks: Parsed chunks with text and metadata
            embeddings: Embedding vectors

        Returns:
            List of vectors ready for upload
        """
        vectors = []
        for chunk, embedding in zip(chunks, embeddings, strict=True):
            # Sanitize metadata for Pinecone (only supports simple types)
            sanitized_metadata = self._sanitize_metadata(chunk["metadata"])
            sanitized_metadata["text"] = chunk["text"]

            vector = {
                "id": self._generate_vector_id(chunk),
                "values": embedding,
                "metadata": sanitized_metadata,
            }
            vectors.append(vector)

        return vectors

    def _sanitize_metadata(self, metadata: dict[str, Any]) -> dict[str, Any]:
        """
        Sanitize metadata to only contain Pinecone-compatible types.

        Pinecone supports: str, int, float, bool, list of str.
        Complex types (dicts, lists of dicts, etc.) are converted to JSON strings.

        Args:
            metadata: Original metadata dict

        Returns:
            Sanitized metadata dict
        """
        sanitized = {}
        for key, value in metadata.items():
            if value is None:
                # Skip None values
                continue
            elif isinstance(value, str | int | float | bool):
                # Simple types are fine
                sanitized[key] = value
            elif isinstance(value, list):
                # Check if it's a list of strings
                if all(isinstance(item, str) for item in value):
                    sanitized[key] = value
                else:
                    # Convert complex lists to JSON string
                    sanitized[key] = json.dumps(value)
            else:
                # Convert complex types (dicts, etc.) to JSON string
                sanitized[key] = json.dumps(value)

        return sanitized

    def _generate_vector_id(self, chunk: dict[str, Any]) -> str:
        """
        Generate deterministic unique ID for a chunk.

        Args:
            chunk: Chunk with text and metadata

        Returns:
            Unique ID string
        """
        # Create ID from source file, section title, and text content hash
        # This ensures uniqueness even for multiple chunks from the same section
        source = chunk["metadata"].get("source_file", "unknown")
        section = chunk["metadata"].get("section_title", "unknown")
        text_hash = hashlib.sha256(chunk["text"].encode()).hexdigest()[:8]
        id_string = f"{source}::{section}::{text_hash}"

        # Use hash for deterministic, short IDs
        return hashlib.sha256(id_string.encode()).hexdigest()[:16]
