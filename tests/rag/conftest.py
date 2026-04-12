"""Shared pytest fixtures for RAG tests."""

from __future__ import annotations

import json
from collections.abc import Callable
from pathlib import Path
from typing import Any

import pytest


@pytest.fixture
def create_test_cases_file() -> Callable[[Path, dict[str, Any]], Path]:
    """Factory for creating test case files.

    Returns:
        A function that creates a test cases JSON file from dict data.
    """

    def _create(tmp_path: Path, test_data: dict[str, Any]) -> Path:
        file_path = tmp_path / "test_cases.json"
        file_path.write_text(json.dumps(test_data, indent=2))
        return file_path

    return _create


@pytest.fixture
def basic_test_data() -> dict[str, Any]:
    """Basic test case data structure for testing.

    Returns:
        Dict with minimal valid test cases structure.
    """
    return {
        "description": "Test cases",
        "version": "1.0",
        "test_cases": [
            {
                "id": "test_01",
                "query": "What is X?",
                "category": "test",
                "expected_sections": ["Section 1"],
                "expected_lesson": 1,
                "min_score": 0.5,
            },
            {
                "id": "test_02",
                "query": "How to do Y?",
                "category": "test",
                "expected_sections": ["Section 2", "Section 3"],
                "expected_lesson": 1,
                "min_score": 0.4,
            },
        ],
    }
