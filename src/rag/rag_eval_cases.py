"""RAG evaluation test cases loader and manager."""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any


class RAGEvalCases:
    """Manager for RAG evaluation test cases."""

    REQUIRED_FIELDS = ["id", "query", "category", "expected_sections", "expected_lesson"]

    def __init__(
        self,
        test_cases: list[dict[str, Any]],
        description: str | None = None,
        version: str | None = None,
    ):
        """
        Initialize RAG evaluation cases.

        Args:
            test_cases: List of test case dictionaries
            description: Optional description of test suite
            version: Optional version string
        """
        self.test_cases = test_cases
        self.description = description
        self.version = version
        self._cases_by_id = {case["id"]: case for case in test_cases}

    @classmethod
    def load_from_file(cls, file_path: Path | str) -> RAGEvalCases:
        """
        Load test cases from JSON file.

        Args:
            file_path: Path to JSON file

        Returns:
            RAGEvalCases instance

        Raises:
            ValueError: If required fields are missing
            FileNotFoundError: If file doesn't exist
        """
        file_path = Path(file_path)

        if not file_path.exists():
            raise FileNotFoundError(f"Test cases file not found: {file_path}")

        with open(file_path) as f:
            data = json.load(f)

        test_cases = data.get("test_cases", [])

        # Validate required fields
        for i, case in enumerate(test_cases):
            for field in cls.REQUIRED_FIELDS:
                if field not in case:
                    raise ValueError(
                        f"Test case {i} (id: {case.get('id', 'unknown')}): "
                        f"Missing required field '{field}'"
                    )

        return cls(
            test_cases=test_cases,
            description=data.get("description"),
            version=data.get("version"),
        )

    @classmethod
    def load_default(cls) -> RAGEvalCases:
        """
        Load test cases from default location.

        Returns:
            RAGEvalCases instance
        """
        # Assume script is in src/rag, go up to project root
        project_root = Path(__file__).parent.parent.parent
        default_path = project_root / "data" / "evaluation" / "rag_test_cases.json"
        return cls.load_from_file(default_path)

    def get_all(self) -> list[dict[str, Any]]:
        """
        Get all test cases.

        Returns:
            List of test case dictionaries
        """
        return self.test_cases

    def get_by_id(self, test_id: str) -> dict[str, Any] | None:
        """
        Get specific test case by ID.

        Args:
            test_id: Test case ID

        Returns:
            Test case dictionary or None if not found
        """
        return self._cases_by_id.get(test_id)

    def get_by_category(self, category: str) -> list[dict[str, Any]]:
        """
        Get test cases filtered by category.

        Args:
            category: Category to filter by

        Returns:
            List of matching test cases
        """
        return [case for case in self.test_cases if case["category"] == category]

    def get_categories(self) -> list[str]:
        """
        Get list of all unique categories.

        Returns:
            List of category names
        """
        categories = {case["category"] for case in self.test_cases}
        return sorted(categories)

    def count_by_category(self) -> dict[str, int]:
        """
        Count test cases by category.

        Returns:
            Dictionary mapping category to count
        """
        return dict(Counter(case["category"] for case in self.test_cases))
