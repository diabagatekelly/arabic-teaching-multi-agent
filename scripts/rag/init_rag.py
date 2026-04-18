"""Initialize RAG vector database with lesson content.

Run this script once to populate the Pinecone vector database
with content from data/rag_database/.
"""

import logging
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

from src.rag.markdown_parser import MarkdownParser
from src.rag.pinecone_client import PineconeClient
from src.rag.rag_ingestion import RAGIngestion
from src.rag.sentence_transformer_client import SentenceTransformerClient

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def main():
    """Initialize RAG database with lesson content."""
    load_dotenv()

    MODEL_NAME = os.getenv("EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
    EMBEDDING_DIM = int(os.getenv("EMBEDDING_DIMENSION", "384"))
    INDEX_NAME = os.getenv("PINECONE_INDEX", "arabic-teaching")
    PINECONE_CLOUD = os.getenv("PINECONE_CLOUD", "aws")
    PINECONE_REGION = os.getenv("PINECONE_REGION", "us-east-1")

    logger.info("🔵 Initializing RAG vector database...")

    logger.info(f"Loading embedding model ({MODEL_NAME})...")
    embedder = SentenceTransformerClient(model_name=MODEL_NAME, dimension=EMBEDDING_DIM)

    logger.info(
        f"Connecting to Pinecone (index: {INDEX_NAME}, {PINECONE_CLOUD}/{PINECONE_REGION})..."
    )
    vector_db = PineconeClient(
        index_name=INDEX_NAME,
        dimension=EMBEDDING_DIM,
        cloud=PINECONE_CLOUD,
        region=PINECONE_REGION,
    )

    if embedder.get_dimension() != vector_db.dimension:
        logger.error("❌ ERROR: Dimension mismatch detected!")
        logger.error(f"   Embedder dimension: {embedder.get_dimension()}")
        logger.error(f"   Vector DB dimension: {vector_db.dimension}")
        logger.error("Please ensure EMBEDDING_DIMENSION matches your Pinecone index configuration.")
        sys.exit(1)

    logger.info("Setting up ingestion pipeline...")
    parser = MarkdownParser()
    ingestion = RAGIngestion(parser, embedder, vector_db)

    data_dir = Path(__file__).parent.parent.parent / "data" / "rag_database"
    logger.info(f"Processing RAG database from: {data_dir}")

    if not data_dir.exists():
        logger.error(f"Data directory not found: {data_dir}")
        sys.exit(1)

    result = ingestion.process_directory(data_dir, show_progress=True, batch_size=100)

    logger.info("✅ RAG initialization complete!")
    logger.info(f"   Chunks parsed: {result['chunks_parsed']}")
    logger.info(f"   Vectors created: {result['vectors_created']}")
    logger.info(f"   Upserted to DB: {result.get('upserted_count', 0)}")

    if result.get("mismatch"):
        logger.warning("⚠️  Mismatch detected between vectors created and upserted")


if __name__ == "__main__":
    main()
