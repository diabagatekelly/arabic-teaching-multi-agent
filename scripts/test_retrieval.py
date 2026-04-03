"""
Test retrieval functionality with sample queries.
"""

from __future__ import annotations

import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from rag.retriever import ExerciseRetriever


def print_result(result_num: int, result: any) -> None:
    """Print a single retrieval result."""
    print(f"\n  Result {result_num}:")
    print(f"    Type: {result.metadata.get('exercise_type', 'N/A')}")
    print(f"    Skill: {result.metadata.get('skill_focus', 'N/A')}")
    print(f"    Lesson: {result.metadata.get('lesson', 'N/A')}")
    print(f"    Distance: {result.distance:.4f}")
    print(f"    Preview: {result.content[:100]}...")


def main() -> None:
    """Run test queries."""
    retriever = ExerciseRetriever()

    print("=" * 70)
    print("RAG RETRIEVAL TEST")
    print("=" * 70)

    print("\n1. Query: 'practice gender agreement with adjectives'")
    results = retriever.retrieve(
        query="practice gender agreement with adjectives",
        n_results=3,
    )
    for i, result in enumerate(results, 1):
        print_result(i, result)

    print("\n" + "=" * 70)
    print("\n2. Query: 'vocabulary translation exercise' (Lesson 1 only)")
    results = retriever.retrieve(
        query="vocabulary translation exercise",
        lesson=1,
        n_results=3,
    )
    for i, result in enumerate(results, 1):
        print_result(i, result)

    print("\n" + "=" * 70)
    print("\n3. Query: 'pronoun practice' (Lesson 2 only)")
    results = retriever.retrieve(
        query="pronoun practice",
        lesson=2,
        n_results=3,
    )
    for i, result in enumerate(results, 1):
        print_result(i, result)

    print("\n" + "=" * 70)
    print("\n4. Query: 'error correction for common mistakes'")
    results = retriever.retrieve(
        query="error correction for common mistakes",
        n_results=3,
    )
    for i, result in enumerate(results, 1):
        print_result(i, result)

    print("\n" + "=" * 70)
    print("\n5. Metadata filter: All fill-in-blank exercises")
    results = retriever.get_by_metadata(
        exercise_type="fill_in_blank",
        limit=5,
    )
    print(f"Found {len(results)} fill-in-blank exercises")
    for i, result in enumerate(results[:3], 1):
        print_result(i, result)

    print("\n" + "=" * 70)
    print("\n✓ Retrieval tests complete!")


if __name__ == "__main__":
    main()
