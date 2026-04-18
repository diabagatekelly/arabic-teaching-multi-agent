#!/usr/bin/env python3
"""Test script for RAG retrieval against real Pinecone data."""

import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv  # noqa: E402

from src.rag.pinecone_client import PineconeClient  # noqa: E402
from src.rag.rag_retriever import RAGRetriever  # noqa: E402
from src.rag.sentence_transformer_client import SentenceTransformerClient  # noqa: E402


def main():
    """Test RAG retrieval with sample queries."""
    load_dotenv()

    print("Initializing RAG retrieval system...")
    print("=" * 70)

    # Initialize components
    embedder = SentenceTransformerClient(
        model_name="sentence-transformers/all-MiniLM-L6-v2", dimension=384
    )
    vector_db = PineconeClient(index_name="arabic-teaching", dimension=384)
    retriever = RAGRetriever(embedder=embedder, vector_db=vector_db)

    # Test queries
    test_queries = [
        ("What is noun gender in Arabic?", 3),
        ("How do I use the definite article?", 3),
        ("Explain masculine and feminine nouns", 2),
    ]

    for query, top_k in test_queries:
        print(f"\n{'=' * 70}")
        print(f"Query: {query}")
        print(f"Top-{top_k} Results:")
        print("-" * 70)

        results = retriever.retrieve(query, top_k=top_k, min_score=0.5)

        if not results:
            print("No results found (score >= 0.5)")
            continue

        for i, result in enumerate(results, 1):
            print(f"\n[{i}] Score: {result['score']:.3f}")
            print(f"Source: {result['metadata'].get('source_file', 'unknown')}")
            print(f"Section: {result['metadata'].get('section_title', 'unknown')}")
            print(f"Text: {result['text'][:150]}...")

    # Test filtering by lesson
    print(f"\n{'=' * 70}")
    print("Testing lesson filtering...")
    print("-" * 70)
    print("Query: 'gender' | Lesson: 1 | Top-3")

    results = retriever.retrieve_by_lesson("gender", lesson_number=1, top_k=3)
    print(f"Found {len(results)} results from lesson 1")
    for i, result in enumerate(results[:2], 1):
        print(f"  [{i}] {result['metadata'].get('section_title')} (score: {result['score']:.3f})")

    print(f"\n{'=' * 70}")
    print("✅ RAG retrieval test complete!")


if __name__ == "__main__":
    main()
