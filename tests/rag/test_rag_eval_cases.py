"""Tests for RAG evaluation test cases loader."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from typing import Any

import pytest

from src.rag.rag_eval_cases import RAGEvalCases


class TestRAGEvalCases:
    """Test suite for RAGEvalCases."""

    @pytest.fixture
    def test_cases_file(
        self,
        tmp_path: Path,
        create_test_cases_file: Callable[[Path, dict[str, Any]], Path],
        basic_test_data: dict[str, Any],
    ) -> Path:
        """Create a temporary test cases file."""
        return create_test_cases_file(tmp_path, basic_test_data)

    def test_load_and_retrieve_test_cases(self, test_cases_file: Path) -> None:
        """Test loading test cases from file and retrieving all."""
        cases = RAGEvalCases.load_from_file(test_cases_file)

        # Verify load worked
        assert len(cases.test_cases) == 2
        assert cases.description == "Test cases"
        assert cases.version == "1.0"

        # Verify retrieval works
        all_cases = cases.get_all()
        assert len(all_cases) == 2
        assert all_cases[0]["id"] == "test_01"
        assert all_cases[1]["id"] == "test_02"

    def test_get_by_category(self, test_cases_file: Path) -> None:
        """Test filtering test cases by category."""
        cases = RAGEvalCases.load_from_file(test_cases_file)
        test_category = cases.get_by_category("test")

        assert len(test_category) == 2
        assert all(case["category"] == "test" for case in test_category)

    def test_get_by_id(self, test_cases_file: Path) -> None:
        """Test getting specific test case by ID."""
        cases = RAGEvalCases.load_from_file(test_cases_file)
        case = cases.get_by_id("test_01")

        assert case is not None
        assert case["query"] == "What is X?"
        assert case["expected_lesson"] == 1

    def test_get_by_id_not_found(self, test_cases_file: Path) -> None:
        """Test getting non-existent test case returns None."""
        cases = RAGEvalCases.load_from_file(test_cases_file)
        case = cases.get_by_id("nonexistent")

        assert case is None

    def test_validate_required_fields(
        self, tmp_path: Path, create_test_cases_file: Callable[[Path, dict[str, Any]], Path]
    ) -> None:
        """Test validation catches missing required fields."""
        invalid_data: dict[str, Any] = {
            "test_cases": [
                {
                    "id": "test_01",
                    "category": "test",
                }
            ]
        }

        file_path = create_test_cases_file(tmp_path, invalid_data)

        with pytest.raises(ValueError, match="Missing required field"):
            RAGEvalCases.load_from_file(file_path)

    def test_load_default_file(self) -> None:
        """Test loading from default location.

        Validates structure and content quality of all test cases,
        including edge cases with empty expected_sections for
        out-of-scope queries.
        """
        cases = RAGEvalCases.load_default()

        assert len(cases.test_cases) >= 5, "Expected at least 5 test cases"
        assert cases.version == "1.0"

        for test_case in cases.get_all():
            assert "id" in test_case
            assert "query" in test_case
            assert "expected_sections" in test_case
            assert isinstance(test_case["expected_sections"], list)

    def test_count_by_category(self, test_cases_file: Path) -> None:
        """Test counting test cases by category."""
        cases = RAGEvalCases.load_from_file(test_cases_file)
        counts = cases.count_by_category()

        assert counts["test"] == 2
