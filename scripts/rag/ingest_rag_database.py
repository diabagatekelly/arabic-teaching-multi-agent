#!/usr/bin/env python3
"""Script to ingest RAG database content into Pinecone."""

import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv  # noqa: E402

from src.rag.markdown_parser import MarkdownParser  # noqa: E402
from src.rag.pinecone_client import PineconeClient  # noqa: E402
from src.rag.rag_ingestion import RAGIngestion  # noqa: E402
from src.rag.sentence_transformer_client import SentenceTransformerClient  # noqa: E402


def main():
    """Run RAG database ingestion pipeline."""
    # Load environment variables
    load_dotenv()

    # Configuration from environment variables with sensible defaults
    MODEL_NAME = os.getenv("EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
    EMBEDDING_DIM = int(os.getenv("EMBEDDING_DIMENSION", "384"))
    INDEX_NAME = os.getenv("PINECONE_INDEX", "arabic-teaching")
    PINECONE_CLOUD = os.getenv("PINECONE_CLOUD", "aws")
    PINECONE_REGION = os.getenv("PINECONE_REGION", "us-east-1")

    print("Initializing RAG ingestion pipeline...")
    print("=" * 70)

    # Initialize components
    print("\n1. Initializing Markdown parser...")
    parser = MarkdownParser()

    print(f"2. Loading embedding model ({MODEL_NAME})...")
    embedder = SentenceTransformerClient(model_name=MODEL_NAME, dimension=EMBEDDING_DIM)

    print(f"3. Connecting to Pinecone (index: {INDEX_NAME}, {PINECONE_CLOUD}/{PINECONE_REGION})...")
    vector_db = PineconeClient(
        index_name=INDEX_NAME,
        dimension=EMBEDDING_DIM,
        cloud=PINECONE_CLOUD,
        region=PINECONE_REGION,
    )

    # Defensive: Verify dimensions match
    if embedder.get_dimension() != vector_db.dimension:
        print("\n❌ ERROR: Dimension mismatch detected!")
        print(f"   Embedder dimension: {embedder.get_dimension()}")
        print(f"   Vector DB dimension: {vector_db.dimension}")
        print("\nPlease ensure EMBEDDING_DIMENSION matches your Pinecone index configuration.")
        sys.exit(1)

    print("4. Creating ingestion pipeline...")
    ingestion = RAGIngestion(parser=parser, embedder=embedder, vector_db=vector_db)

    # Process RAG database
    rag_db_path = project_root / "data" / "rag_database"

    if not rag_db_path.exists():
        print(f"\nERROR: RAG database not found at {rag_db_path}")
        sys.exit(1)

    print(f"\n5. Processing RAG database at {rag_db_path}...")
    print("   This may take a few minutes...")
    print("-" * 70)

    result = ingestion.process_directory(rag_db_path, show_progress=True, batch_size=100)

    # Print results
    print("\n" + "=" * 70)
    print("INGESTION COMPLETE!")
    print("=" * 70)
    print(f"Chunks parsed:    {result['chunks_parsed']}")
    print(f"Vectors created:  {result['vectors_created']}")
    print(f"Vectors upserted: {result.get('upserted_count', 0)}")
    print(f"Batches:          {result.get('batches', 0)}")

    # Show mismatch warning if detected
    if result.get("mismatch", False):
        print("\n⚠️  WARNING: Mismatch detected between vectors created and upserted!")
        print("   This may indicate partial failures or duplicate IDs.")

    print("=" * 70)

    # Verify with database stats
    print("\nVerifying Pinecone index stats...")
    stats = vector_db.get_stats()
    print(f"Total vectors in index: {stats.get('total_vector_count', 'unknown')}")
    print(f"Index dimension:        {stats.get('dimension', 'unknown')}")

    print("\n✅ RAG database ingestion successful!")


if __name__ == "__main__":
    main()
