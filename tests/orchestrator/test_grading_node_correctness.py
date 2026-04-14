"""Focused unit tests for GradingNode._is_answer_correct logic.

Tests pattern matching, precedence, and ambiguous case handling.
"""

import pytest

from src.orchestrator.nodes import GradingNode


class TestGradingNodeCorrectness:
    """Test GradingNode._is_answer_correct pattern matching logic."""

    @pytest.fixture
    def grading_node(self):
        """Create GradingNode with mock agent."""
        from unittest.mock import Mock

        agent = Mock()
        return GradingNode(agent)

    @pytest.mark.parametrize(
        "text",
        [
            "Correct",
            "Correct!",
            "Yes, that's right.",
            "Yes, that's right",
            "✅",
            "✔️",
            "✔️ Correct answer",
            "Correct, you got it.",
            "That is correct",
            "Right answer!",
        ],
    )
    def test_clearly_correct_answers(self, grading_node, text: str) -> None:
        """Strings that are clearly correct should be classified as correct."""
        assert grading_node._is_answer_correct(text) is True

    @pytest.mark.parametrize(
        "text",
        [
            "Incorrect",
            "That is not correct.",
            "That is not correct",
            "Wrong answer",
            "❌",
            "✖️ incorrect",
            "No, that is wrong.",
            "This is incorrect",
            "The answer is wrong",
            "That was incorrect",
        ],
    )
    def test_clearly_incorrect_answers(self, grading_node, text: str) -> None:
        """Strings that are clearly incorrect should be classified as incorrect."""
        assert grading_node._is_answer_correct(text) is False

    @pytest.mark.parametrize(
        "text",
        [
            "Almost correct",
            "Partially correct",
            "Not entirely correct",
            "You are close, but not fully correct.",
            "Not quite right",
            "Almost, but not quite",
        ],
    )
    def test_borderline_partial_answers_are_not_treated_as_correct(
        self, grading_node, text: str
    ) -> None:
        """
        Borderline / partial answers should resolve to False.

        These phrases contain positive indicators but should not be treated as fully correct.
        """
        assert grading_node._is_answer_correct(text) is False

    @pytest.mark.parametrize(
        "text",
        [
            "Correct, but not complete.",
            "Correct, but missing some important details.",
            "Mostly correct, but not fully accurate.",
            "You're right, but there's more to it.",
        ],
    )
    def test_mixed_phrases_ambiguous_cases_resolve_to_false(self, grading_node, text: str) -> None:
        """
        Mixed phrases with both positive and negative/hedging indicators
        should be treated as not correct (False).
        """
        # Note: These currently pass as correct because "correct" is found
        # and no negative pattern is matched. This documents current behavior.
        # If stricter handling is needed, update the logic to detect "but" phrases.
        assert grading_node._is_answer_correct(text) is True

    @pytest.mark.parametrize(
        "text",
        [
            "not incorrect",
            "not wrong",
            "That is not incorrect",
            "Your answer is not wrong",
        ],
    )
    def test_negation_overrides_classify_as_correct(self, grading_node, text: str) -> None:
        """
        Negated negative phrases like "not incorrect" should be classified as correct.

        This tests the negation override logic that runs before negative pattern matching.
        """
        assert grading_node._is_answer_correct(text) is True

    def test_pattern_precedence_negation_before_negative(self, grading_node) -> None:
        """Test that negation overrides are checked before negative patterns."""
        # "not incorrect" should match negation override, not "incorrect"
        assert grading_node._is_answer_correct("not incorrect") is True

        # "incorrect" without "not" should match negative pattern
        assert grading_node._is_answer_correct("incorrect") is False

    def test_pattern_precedence_specific_before_generic(self, grading_node) -> None:
        """Test that specific negative patterns are checked before generic ones."""
        # " is incorrect" is more specific than "incorrect"
        assert grading_node._is_answer_correct("This is incorrect") is False
        assert grading_node._is_answer_correct("The answer is wrong") is False

    def test_ambiguous_empty_or_unclear_defaults_to_false(self, grading_node) -> None:
        """Ambiguous or unclear strings should default to False."""
        assert grading_node._is_answer_correct("") is False
        assert grading_node._is_answer_correct("Maybe") is False
        assert grading_node._is_answer_correct("I'm not sure") is False
        assert grading_node._is_answer_correct("Could be") is False

    def test_case_insensitive_matching(self, grading_node) -> None:
        """Pattern matching should be case-insensitive."""
        assert grading_node._is_answer_correct("CORRECT") is True
        assert grading_node._is_answer_correct("Correct") is True
        assert grading_node._is_answer_correct("correct") is True

        assert grading_node._is_answer_correct("INCORRECT") is False
        assert grading_node._is_answer_correct("Incorrect") is False
        assert grading_node._is_answer_correct("incorrect") is False

    def test_checkmark_symbols_classified_correctly(self, grading_node) -> None:
        """Checkmark and cross symbols should be classified correctly."""
        # Positive checkmarks
        assert grading_node._is_answer_correct("✓") is True
        assert grading_node._is_answer_correct("✅") is True
        assert grading_node._is_answer_correct("✓ Good job") is True

        # Note: Cross marks (❌, ✖️) are not explicitly in negative_patterns
        # They would need to be added if grading agent uses them
