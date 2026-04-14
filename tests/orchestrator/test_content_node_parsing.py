"""Unit tests for ContentNode._parse_exercise_response parsing logic.

Tests JSON extraction, validation, and error handling.
"""

import pytest

from src.orchestrator.nodes import ContentNode
from src.orchestrator.state import SystemState


class TestContentNodeParsing:
    """Test ContentNode._parse_exercise_response parsing and validation."""

    @pytest.fixture
    def content_node(self):
        """Create ContentNode with mock agent."""
        from unittest.mock import Mock

        agent = Mock()
        return ContentNode(agent)

    @pytest.fixture
    def state(self):
        """Create basic state for parsing context."""
        return SystemState(user_id="test", session_id="test")

    def test_parse_exercise_response_fenced_json_success(self, content_node, state):
        """Should parse JSON from code fence (primary format)."""
        response = '```json\n{"question": "Q", "answer": "A", "type": "t"}\n```'
        request = {"exercise_type": "translation", "difficulty": "beginner"}

        exercise = content_node._parse_exercise_response(response, request, state)

        assert exercise.question == "Q"
        assert exercise.answer == "A"
        assert exercise.exercise_type == "translation"

    def test_parse_exercise_response_raw_json_success(self, content_node, state):
        """Should handle raw JSON without fences (fallback format)."""
        response = '{"question": "What is 2+2?", "answer": "4", "type": "math"}'
        request = {"exercise_type": "math", "difficulty": "beginner"}

        exercise = content_node._parse_exercise_response(response, request, state)

        assert exercise.question == "What is 2+2?"
        assert exercise.answer == "4"

    @pytest.mark.parametrize(
        "invalid_payload",
        [
            "not json at all",
            "{invalid json}",
            '{"question": "Q", "answer": "A",}',  # trailing comma
            "```json\n{broken\n```",
        ],
    )
    def test_parse_exercise_response_invalid_json_raises_value_error(
        self, content_node, state, invalid_payload
    ):
        """Malformed JSON should raise ValueError with a clear message."""
        request = {"exercise_type": "translation", "difficulty": "beginner"}

        with pytest.raises(ValueError, match="Invalid JSON|Could not parse|Could not find JSON"):
            content_node._parse_exercise_response(invalid_payload, request, state)

    def test_parse_exercise_response_missing_question_raises_value_error(self, content_node, state):
        """Missing 'question' field should raise ValueError."""
        response = '{"answer": "A", "type": "t"}'
        request = {"exercise_type": "translation", "difficulty": "beginner"}

        with pytest.raises((ValueError, KeyError)):
            content_node._parse_exercise_response(response, request, state)

    def test_parse_exercise_response_missing_answer_raises_value_error(self, content_node, state):
        """Missing 'answer' field should raise ValueError."""
        response = '{"question": "Q", "type": "t"}'
        request = {"exercise_type": "translation", "difficulty": "beginner"}

        with pytest.raises((ValueError, KeyError)):
            content_node._parse_exercise_response(response, request, state)

    def test_parse_exercise_response_preserves_metadata(self, content_node, state):
        """Should preserve all fields from JSON as metadata."""
        response = """```json
        {
            "question": "Q",
            "answer": "A",
            "type": "translation",
            "difficulty": "intermediate",
            "hint": "Think about gender",
            "explanation": "This tests noun gender"
        }
        ```"""
        request = {"exercise_type": "translation", "difficulty": "beginner"}

        exercise = content_node._parse_exercise_response(response, request, state)

        # Should have basic fields
        assert exercise.question == "Q"
        assert exercise.answer == "A"

        # Should preserve extra fields in metadata
        assert exercise.metadata.get("hint") == "Think about gender"
        assert exercise.metadata.get("explanation") == "This tests noun gender"

    def test_parse_exercise_response_uses_request_fallbacks(self, content_node, state):
        """Should use request values as fallbacks for missing fields."""
        response = '{"question": "Q", "answer": "A"}'
        request = {"exercise_type": "multiple_choice", "difficulty": "advanced"}

        exercise = content_node._parse_exercise_response(response, request, state)

        # Should use request fallbacks
        assert exercise.exercise_type == "multiple_choice"
        assert exercise.difficulty == "advanced"

    def test_parse_exercise_response_generates_unique_id(self, content_node, state):
        """Should generate unique exercise IDs based on state."""
        response = '{"question": "Q1", "answer": "A1", "type": "t"}'
        request = {"exercise_type": "translation", "difficulty": "beginner"}

        # First exercise
        exercise1 = content_node._parse_exercise_response(response, request, state)
        assert exercise1.exercise_id == "ex_1"

        # Second exercise (after incrementing state counter)
        state.total_exercises_completed = 1
        exercise2 = content_node._parse_exercise_response(response, request, state)
        assert exercise2.exercise_id == "ex_2"

    def test_parse_exercise_response_handles_nested_json_objects(self, content_node, state):
        """Should handle complex nested JSON structures."""
        response = """```json
        {
            "question": "Choose the correct form",
            "answer": "الكِتَاب",
            "type": "multiple_choice",
            "options": ["الكِتَاب", "كِتَاب", "الكتاب"],
            "metadata": {
                "word": "book",
                "grammar_point": "definite_article"
            }
        }
        ```"""
        request = {"exercise_type": "multiple_choice", "difficulty": "beginner"}

        exercise = content_node._parse_exercise_response(response, request, state)

        assert exercise.question == "Choose the correct form"
        assert exercise.answer == "الكِتَاب"
        assert "options" in exercise.metadata
        assert len(exercise.metadata["options"]) == 3
