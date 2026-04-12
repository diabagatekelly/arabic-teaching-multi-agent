"""Run RAG evaluation and generate report."""

from __future__ import annotations

import json
import os
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv

from src.rag.pinecone_client import PineconeClient
from src.rag.rag_eval_cases import RAGEvalCases
from src.rag.rag_evaluator import RAGEvaluator
from src.rag.rag_retriever import RAGRetriever
from src.rag.sentence_transformer_client import SentenceTransformerClient

# Load environment variables
load_dotenv()

# Configuration constants
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
EMBEDDING_DIMENSION = int(os.getenv("EMBEDDING_DIMENSION", "384"))
PINECONE_INDEX = os.getenv("PINECONE_INDEX", "arabic-teaching")
EVAL_TOP_K = int(os.getenv("EVAL_TOP_K", "3"))
MIN_PASS_RATE = float(os.getenv("MIN_PASS_RATE", "0.8"))


def format_sections(sections: list[str], empty_label: str = "None") -> str:
    """
    Format section list for display.

    Args:
        sections: List of section titles
        empty_label: Label to show if list is empty

    Returns:
        Comma-separated section list or empty label
    """
    return ", ".join(sections) if sections else empty_label


def main() -> None:
    """Run RAG evaluation and print report."""
    print("=" * 80)
    print("RAG EVALUATION REPORT")
    print("=" * 80)
    print()

    # Initialize components
    print("Initializing RAG components...")
    print(f"  Embedding model: {EMBEDDING_MODEL}")
    print(f"  Vector database: {PINECONE_INDEX}")
    print(f"  Top-K: {EVAL_TOP_K}")

    embedder = SentenceTransformerClient(model_name=EMBEDDING_MODEL, dimension=EMBEDDING_DIMENSION)

    vector_db = PineconeClient(index_name=PINECONE_INDEX, dimension=EMBEDDING_DIMENSION)

    retriever = RAGRetriever(embedder=embedder, vector_db=vector_db)

    # Load test cases
    print("Loading test cases...")
    test_cases = RAGEvalCases.load_default()
    print(f"Loaded {len(test_cases.get_all())} test cases")
    print()

    # Run evaluation
    print("Running evaluation (lesson content retrieval)...")
    print("Note: Filtering by lesson_number to reduce noise from exercise templates")
    evaluator = RAGEvaluator(retriever=retriever, test_cases=test_cases)

    start_time = datetime.now()
    results = evaluator.evaluate(top_k=EVAL_TOP_K)
    end_time = datetime.now()
    print()

    # Print overall metrics
    print("OVERALL METRICS")
    print("-" * 80)
    print(f"Test Cases: {results['num_test_cases']}")
    print(f"Hit Rate@{EVAL_TOP_K}: {results['hit_rate']:.2%}")
    print(f"Mean Reciprocal Rank: {results['mean_reciprocal_rank']:.4f}")
    print(f"Average Score: {results['avg_score']:.4f}")
    print(f"Evaluation Time: {(end_time - start_time).total_seconds():.2f}s")
    print()

    # Print per-category metrics
    print("METRICS BY CATEGORY")
    print("-" * 80)
    for category, metrics in sorted(results["by_category"].items()):
        print(f"\n{category.upper()}:")
        print(f"  Cases: {metrics['num_cases']}")
        print(f"  Hit Rate@{EVAL_TOP_K}: {metrics['hit_rate']:.2%}")
        print(f"  Mean Reciprocal Rank: {metrics['mean_reciprocal_rank']:.4f}")
        print(f"  Average Score: {metrics['avg_score']:.4f}")
    print()

    # Print individual results
    print("INDIVIDUAL TEST CASE RESULTS")
    print("-" * 80)
    for result in results["results"]:
        test_case = test_cases.get_by_id(result["test_id"])
        status = "✓ HIT" if result["hit"] else "✗ MISS"
        print(f"\n{result['test_id']}: {status}")
        print(f"  Query: {test_case['query']}")
        print(f"  Expected: {format_sections(test_case['expected_sections'], 'N/A')}")
        print(f"  Retrieved: {format_sections(result['retrieved_sections'])}")
        print(f"  Reciprocal Rank: {result['reciprocal_rank']:.4f}")
        print(f"  Avg Score: {result['avg_score']:.4f}")
    print()

    # Identify failures
    failures = [r for r in results["results"] if not r["hit"]]
    if failures:
        print("FAILURES (No Relevant Results)")
        print("-" * 80)
        for failure in failures:
            test_case = test_cases.get_by_id(failure["test_id"])
            print(f"\n{failure['test_id']}: {test_case['query']}")
            print(f"  Expected: {format_sections(test_case['expected_sections'], 'N/A')}")
            print(f"  Retrieved sections: {format_sections(failure['retrieved_sections'])}")
            print(f"  Category: {test_case['category']}")
            print(f"  Avg Score: {failure['avg_score']:.4f}")

            if failure.get("retrieved_texts"):
                print("  Retrieved content:")
                for i, (section, text) in enumerate(
                    zip(failure["retrieved_sections"], failure["retrieved_texts"], strict=True),
                    1,
                ):
                    print(f"    {i}. [{section}] {text}")
        print()

    # Save results to JSON with metadata
    output_dir = Path(__file__).parent.parent / "data" / "evaluation"
    output_file = output_dir / "rag_evaluation_results.json"
    output_dir.mkdir(parents=True, exist_ok=True)

    # Add evaluation metadata
    results_with_metadata = {
        "timestamp": start_time.isoformat(),
        "duration_seconds": (end_time - start_time).total_seconds(),
        "config": {
            "embedding_model": EMBEDDING_MODEL,
            "embedding_dimension": EMBEDDING_DIMENSION,
            "index_name": PINECONE_INDEX,
            "top_k": EVAL_TOP_K,
            "min_pass_rate": MIN_PASS_RATE,
        },
        **results,
    }

    with open(output_file, "w") as f:
        json.dump(results_with_metadata, f, indent=2)

    print(f"Results saved to: {output_file}")
    print()

    # Overall assessment
    print("=" * 80)
    if results["hit_rate"] >= MIN_PASS_RATE:
        print(f"✓ EVALUATION PASSED - Hit rate >= {MIN_PASS_RATE:.0%}")
    else:
        print(
            f"✗ EVALUATION NEEDS IMPROVEMENT - Hit rate {results['hit_rate']:.1%} < {MIN_PASS_RATE:.0%}"
        )
    print("=" * 80)


if __name__ == "__main__":
    main()
