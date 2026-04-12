"""Tests for RAG evaluator."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from typing import Any
from unittest.mock import Mock

import pytest

from src.rag.rag_eval_cases import RAGEvalCases
from src.rag.rag_evaluator import RAGEvaluator


class TestRAGEvaluator:
    """Test suite for RAGEvaluator."""

    @pytest.fixture
    def mock_retriever(self) -> Mock:
        """Create a mock retriever."""
        return Mock()

    @pytest.fixture
    def test_cases(
        self, tmp_path: Path, create_test_cases_file: Callable[[Path, dict[str, Any]], Path]
    ) -> RAGEvalCases:
        """Create test cases for evaluation."""
        test_data: dict[str, Any] = {
            "test_cases": [
                {
                    "id": "test_01",
                    "query": "What is X?",
                    "category": "basic",
                    "expected_sections": ["Section A", "Section B"],
                    "expected_lesson": 1,
                    "min_score": 0.5,
                },
                {
                    "id": "test_02",
                    "query": "How to Y?",
                    "category": "basic",
                    "expected_sections": ["Section C"],
                    "expected_lesson": 1,
                    "min_score": 0.4,
                },
            ]
        }

        file_path = create_test_cases_file(tmp_path, test_data)
        return RAGEvalCases.load_from_file(file_path)

    def test_evaluate_single_case_hit(self, mock_retriever: Mock, test_cases: RAGEvalCases) -> None:
        """Test evaluating a single case with a hit."""
        evaluator = RAGEvaluator(mock_retriever, test_cases)

        # Mock retriever returns results with expected section
        mock_retriever.retrieve.return_value = [
            {
                "text": "Content from Section A",
                "score": 0.8,
                "metadata": {"section_title": "Section A", "lesson_number": 1},
            },
            {
                "text": "Content from Section D",
                "score": 0.6,
                "metadata": {"section_title": "Section D", "lesson_number": 1},
            },
        ]

        test_case = test_cases.get_by_id("test_01")
        assert test_case is not None
        result = evaluator.evaluate_single(test_case, top_k=5)

        assert result["hit"] is True
        assert result["reciprocal_rank"] == 1.0
        assert result["avg_score"] == 0.7
        assert result["num_results"] == 2

    def test_evaluate_single_case_miss(
        self, mock_retriever: Mock, test_cases: RAGEvalCases
    ) -> None:
        """Test evaluating a single case with no hits."""
        evaluator = RAGEvaluator(mock_retriever, test_cases)

        # Mock retriever returns results without expected sections
        mock_retriever.retrieve.return_value = [
            {
                "text": "Content from Section D",
                "score": 0.6,
                "metadata": {"section_title": "Section D", "lesson_number": 1},
            },
        ]

        test_case = test_cases.get_by_id("test_01")
        assert test_case is not None
        result = evaluator.evaluate_single(test_case, top_k=5)

        assert result["hit"] is False
        assert result["reciprocal_rank"] == 0.0
        assert result["avg_score"] == 0.6

    def test_evaluate_single_case_hit_at_position_3(
        self, mock_retriever: Mock, test_cases: RAGEvalCases
    ) -> None:
        """Test MRR when hit is at position 3."""
        evaluator = RAGEvaluator(mock_retriever, test_cases)

        mock_retriever.retrieve.return_value = [
            {
                "text": "Content from Section X",
                "score": 0.9,
                "metadata": {"section_title": "Section X", "lesson_number": 1},
            },
            {
                "text": "Content from Section Y",
                "score": 0.8,
                "metadata": {"section_title": "Section Y", "lesson_number": 1},
            },
            {
                "text": "Content from Section A",  # Expected section at position 3
                "score": 0.7,
                "metadata": {"section_title": "Section A", "lesson_number": 1},
            },
        ]

        test_case = test_cases.get_by_id("test_01")
        assert test_case is not None
        result = evaluator.evaluate_single(test_case, top_k=5)

        assert result["hit"] is True
        assert result["reciprocal_rank"] == 1.0 / 3

    def test_evaluate_all_cases(self, mock_retriever: Mock, test_cases: RAGEvalCases) -> None:
        """Test evaluating all test cases."""
        evaluator = RAGEvaluator(mock_retriever, test_cases)

        # First query: hit
        # Second query: miss
        mock_retriever.retrieve.side_effect = [
            [
                {
                    "text": "Content from Section A",
                    "score": 0.8,
                    "metadata": {"section_title": "Section A", "lesson_number": 1},
                }
            ],
            [
                {
                    "text": "Content from Section D",
                    "score": 0.5,
                    "metadata": {"section_title": "Section D", "lesson_number": 1},
                }
            ],
        ]

        results = evaluator.evaluate(top_k=5)

        assert results["num_test_cases"] == 2
        assert results["hit_rate"] == 0.5  # 1 hit out of 2
        assert results["mean_reciprocal_rank"] == 0.5  # (1.0 + 0.0) / 2
        assert "avg_score" in results
        assert "results" in results
        assert len(results["results"]) == 2

    def test_evaluate_with_category_breakdown(
        self, mock_retriever: Mock, test_cases: RAGEvalCases
    ) -> None:
        """Test that evaluation includes per-category metrics."""
        evaluator = RAGEvaluator(mock_retriever, test_cases)

        mock_retriever.retrieve.side_effect = [
            [
                {
                    "text": "Content from Section A",
                    "score": 0.8,
                    "metadata": {"section_title": "Section A", "lesson_number": 1},
                }
            ],
            [
                {
                    "text": "Content from Section C",
                    "score": 0.7,
                    "metadata": {"section_title": "Section C", "lesson_number": 1},
                }
            ],
        ]

        results = evaluator.evaluate(top_k=5)

        assert "by_category" in results
        assert "basic" in results["by_category"]
        category_metrics = results["by_category"]["basic"]
        assert category_metrics["num_cases"] == 2
        assert category_metrics["hit_rate"] == 1.0  # Both hit

    def test_evaluate_single_case_no_results(
        self, mock_retriever: Mock, test_cases: RAGEvalCases
    ) -> None:
        """Test evaluating when retriever returns no results."""
        evaluator = RAGEvaluator(mock_retriever, test_cases)

        mock_retriever.retrieve.return_value = []

        test_case = test_cases.get_by_id("test_01")
        assert test_case is not None
        result = evaluator.evaluate_single(test_case, top_k=5)

        assert result["hit"] is False
        assert result["reciprocal_rank"] == 0.0
        assert result["avg_score"] == 0.0
        assert result["num_results"] == 0

    def test_evaluate_single_case_missing_section_metadata(
        self, mock_retriever: Mock, test_cases: RAGEvalCases
    ) -> None:
        """Test graceful handling of results without section metadata."""
        evaluator = RAGEvaluator(mock_retriever, test_cases)

        mock_retriever.retrieve.return_value = [
            {
                "text": "Some content",
                "score": 0.7,
                "metadata": {"lesson_number": 1},
            },
        ]

        test_case = test_cases.get_by_id("test_01")
        assert test_case is not None
        result = evaluator.evaluate_single(test_case, top_k=5)

        assert result["hit"] is False
        assert result["reciprocal_rank"] == 0.0
        assert result["num_results"] == 1
        assert result["avg_score"] == 0.7

    def test_evaluate_passes_top_k_to_retriever(
        self, mock_retriever: Mock, test_cases: RAGEvalCases
    ) -> None:
        """Test that top_k parameter is correctly passed to retriever.

        This verifies the API contract between evaluator and retriever.
        Actual result limiting is tested in retriever unit tests.
        """
        evaluator = RAGEvaluator(mock_retriever, test_cases)

        mock_retriever.retrieve.return_value = []

        test_case = test_cases.get_by_id("test_01")
        assert test_case is not None
        evaluator.evaluate_single(test_case, top_k=10)

        mock_retriever.retrieve.assert_called_once()
        call_kwargs = mock_retriever.retrieve.call_args[1]
        assert call_kwargs["top_k"] == 10

    def test_evaluate_single_case_malformed_result(
        self, mock_retriever: Mock, test_cases: RAGEvalCases
    ) -> None:
        """Test graceful handling of results with missing metadata key."""
        evaluator = RAGEvaluator(mock_retriever, test_cases)

        mock_retriever.retrieve.return_value = [
            {
                "text": "Some content",
                "score": 0.7,
            },
        ]

        test_case = test_cases.get_by_id("test_01")
        assert test_case is not None
        result = evaluator.evaluate_single(test_case, top_k=5)

        assert result["hit"] is False
        assert result["reciprocal_rank"] == 0.0
        assert result["num_results"] == 1
        assert result["avg_score"] == 0.7
