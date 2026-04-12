"""RAG evaluation for measuring retrieval performance."""

from __future__ import annotations

from typing import Any

from src.rag.rag_eval_cases import RAGEvalCases
from src.rag.rag_retriever import RAGRetriever

# Constants
TEXT_PREVIEW_LENGTH = 100


class RAGEvaluator:
    """Evaluator for RAG retrieval performance."""

    def __init__(self, retriever: RAGRetriever, test_cases: RAGEvalCases):
        """
        Initialize RAG evaluator.

        Args:
            retriever: RAG retriever to evaluate
            test_cases: Test cases to evaluate against
        """
        self.retriever = retriever
        self.test_cases = test_cases

    def evaluate_single(self, test_case: dict[str, Any], top_k: int = 5) -> dict[str, Any]:
        """
        Evaluate a single test case.

        Args:
            test_case: Test case dictionary with query and expected_sections
            top_k: Number of results to retrieve

        Returns:
            Dictionary with metrics:
            - test_id: Test case ID
            - hit: Whether any expected section was retrieved
            - reciprocal_rank: 1/rank of first relevant result (0 if none)
            - avg_score: Average similarity score of retrieved results
            - num_results: Number of results retrieved
        """
        query = test_case["query"]
        expected_sections = test_case["expected_sections"]
        expected_lesson = test_case.get("expected_lesson")

        metadata_filter = None
        if expected_lesson:
            metadata_filter = {"lesson_number": expected_lesson, "doc_type": "lesson"}

        results = self.retriever.retrieve(query=query, top_k=top_k, metadata_filter=metadata_filter)

        num_results = len(results)
        avg_score = self._safe_average([r["score"] for r in results])
        hit, reciprocal_rank = self._find_first_matching_result(results, expected_sections)

        retrieved_sections = [r["metadata"].get("section_title", "Unknown") for r in results]
        retrieved_texts = [
            r["text"][:TEXT_PREVIEW_LENGTH] + "..."
            if len(r["text"]) > TEXT_PREVIEW_LENGTH
            else r["text"]
            for r in results
        ]

        return {
            "test_id": test_case["id"],
            "hit": hit,
            "reciprocal_rank": reciprocal_rank,
            "avg_score": avg_score,
            "num_results": num_results,
            "retrieved_sections": retrieved_sections,
            "retrieved_texts": retrieved_texts,
        }

    def evaluate(self, top_k: int = 5) -> dict[str, Any]:
        """
        Evaluate all test cases.

        Args:
            top_k: Number of results to retrieve per query

        Returns:
            Dictionary with overall metrics:
            - num_test_cases: Total number of test cases
            - hit_rate: Proportion of queries with at least one relevant result
            - mean_reciprocal_rank: Average MRR across all queries
            - avg_score: Average similarity score across all results
            - results: List of individual test case results
            - by_category: Per-category metrics
        """
        all_cases = self.test_cases.get_all()
        results = []

        # Evaluate each test case
        for test_case in all_cases:
            result = self.evaluate_single(test_case, top_k=top_k)
            results.append(result)

        # Calculate overall metrics
        num_test_cases = len(results)
        num_hits = sum(1 for r in results if r["hit"])
        hit_rate = num_hits / num_test_cases if num_test_cases > 0 else 0.0

        mean_reciprocal_rank = self._safe_average([r["reciprocal_rank"] for r in results])
        avg_score = self._safe_average([r["avg_score"] for r in results])

        # Calculate per-category metrics
        by_category = self._calculate_category_metrics(all_cases, results)

        return {
            "num_test_cases": num_test_cases,
            "hit_rate": hit_rate,
            "mean_reciprocal_rank": mean_reciprocal_rank,
            "avg_score": avg_score,
            "results": results,
            "by_category": by_category,
        }

    def _calculate_category_metrics(
        self, test_cases: list[dict[str, Any]], results: list[dict[str, Any]]
    ) -> dict[str, dict[str, Any]]:
        """Calculate per-category metrics."""
        # Group results by category
        category_results: dict[str, list[dict[str, Any]]] = {}
        for test_case, result in zip(test_cases, results, strict=True):
            category = test_case["category"]
            if category not in category_results:
                category_results[category] = []
            category_results[category].append(result)

        # Calculate metrics for each category
        by_category = {}
        for category, cat_results in category_results.items():
            num_cases = len(cat_results)
            num_hits = sum(1 for r in cat_results if r["hit"])
            hit_rate = num_hits / num_cases if num_cases > 0 else 0.0

            mean_rr = self._safe_average([r["reciprocal_rank"] for r in cat_results])
            avg_score = self._safe_average([r["avg_score"] for r in cat_results])

            by_category[category] = {
                "num_cases": num_cases,
                "hit_rate": hit_rate,
                "mean_reciprocal_rank": mean_rr,
                "avg_score": avg_score,
            }

        return by_category

    def _find_first_matching_result(
        self, results: list[dict[str, Any]], expected_sections: list[str]
    ) -> tuple[bool, float]:
        """
        Find first result matching expected sections.

        Args:
            results: List of retrieval results
            expected_sections: List of expected section titles

        Returns:
            Tuple of (hit, reciprocal_rank)
        """
        for i, result in enumerate(results, start=1):
            section = result["metadata"].get("section_title")
            if self._section_matches(section, expected_sections):
                return True, 1.0 / i
        return False, 0.0

    def _section_matches(self, section: str | None, expected_sections: list[str]) -> bool:
        """
        Check if section matches any expected section.

        Matches exact section names or sections starting with expected prefix.
        Example: "Grammar Point 1" matches "Grammar Point 1: Rule"

        Args:
            section: Retrieved section title
            expected_sections: List of expected section titles

        Returns:
            True if section matches any expected section
        """
        if not section:
            return False
        return any(
            section == expected or section.startswith(expected + ":")
            for expected in expected_sections
        )

    def _safe_average(self, values: list[float]) -> float:
        """
        Calculate average, returning 0.0 for empty list.

        Args:
            values: List of numeric values

        Returns:
            Average of values, or 0.0 if empty
        """
        return sum(values) / len(values) if values else 0.0
