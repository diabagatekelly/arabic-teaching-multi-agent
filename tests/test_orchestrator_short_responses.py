"""Test orchestrator handling of short responses without LLM.

Short responses include:
- Numbers: "1", "2"
- Affirmative: "yes", "yeah", "ok", "sure", "yep", "yup", "alright"
- Negative: "no", "nope", "nah"

Orchestrator should:
1. Detect short response
2. Look at last agent message for context
3. Transform to clear intent before sending to LLM
"""

import pytest

from src.orchestrator.short_response_handler import transform_short_response
from src.orchestrator.state import create_initial_state


class TestNumberedResponses:
    """Test numeric responses like '1', '2'"""

    def test_number_1_after_vocabulary_or_grammar_choice(self):
        """User says '1' after 'Want 1. vocabulary or 2. grammar?'"""
        state = create_initial_state(lesson_number=1, user_id="test_user")
        state.add_message("assistant", "Want 1. vocabulary or 2. grammar?")

        transformed = transform_short_response("1", state.conversation_history)

        assert transformed == "vocabulary"

    def test_number_2_after_vocabulary_or_grammar_choice(self):
        """User says '2' after 'Want 1. vocabulary or 2. grammar?'"""
        state = create_initial_state(lesson_number=1, user_id="test_user")
        state.add_message("assistant", "Want 1. vocabulary or 2. grammar?")

        transformed = transform_short_response("2", state.conversation_history)

        assert transformed == "grammar"

    def test_number_without_numbered_options_returns_original(self):
        """User says '1' but last message had no numbered options"""
        state = create_initial_state(lesson_number=1, user_id="test_user")
        state.add_message("assistant", "Ready for Batch 2?")

        transformed = transform_short_response("1", state.conversation_history)

        # Should return original since no numbered options in context
        assert transformed == "1"


class TestAffirmativeResponses:
    """Test affirmative responses like 'yes', 'ok', 'sure'"""

    def test_yes_after_batch_question(self):
        """User says 'yes' after 'Ready for Batch 2?'"""
        state = create_initial_state(lesson_number=1, user_id="test_user")
        state.add_message("assistant", "Ready for Batch 2?")

        transformed = transform_short_response("yes", state.conversation_history)

        assert transformed == "give me batch 2"

    def test_ok_after_quiz_question(self):
        """User says 'ok' after 'Want to take a quiz?'"""
        state = create_initial_state(lesson_number=1, user_id="test_user")
        state.add_message("assistant", "Want to take a quiz?")

        transformed = transform_short_response("ok", state.conversation_history)

        assert transformed == "start quiz"

    def test_sure_after_quiz_question(self):
        """User says 'sure' after 'Ready to start your quiz?'"""
        state = create_initial_state(lesson_number=1, user_id="test_user")
        state.add_message("assistant", "Ready to start your quiz?")

        transformed = transform_short_response("sure", state.conversation_history)

        assert transformed == "start quiz"

    def test_yeah_after_batch_question(self):
        """User says 'yeah' after 'Continue with Batch 2?'"""
        state = create_initial_state(lesson_number=1, user_id="test_user")
        state.add_message("assistant", "Continue with Batch 2?")

        transformed = transform_short_response("yeah", state.conversation_history)

        assert transformed == "give me batch 2"

    def test_yep_after_quiz_question(self):
        """User says 'yep' after 'Want a quiz?'"""
        state = create_initial_state(lesson_number=1, user_id="test_user")
        state.add_message("assistant", "Want a quiz?")

        transformed = transform_short_response("yep", state.conversation_history)

        assert transformed == "start quiz"

    def test_alright_after_grammar_question(self):
        """User says 'alright' after 'Want to learn grammar?'"""
        state = create_initial_state(lesson_number=1, user_id="test_user")
        state.add_message("assistant", "Want to learn grammar?")

        transformed = transform_short_response("alright", state.conversation_history)

        assert transformed == "teach me grammar"


class TestNegativeResponses:
    """Test negative responses like 'no', 'nope', 'nah'"""

    def test_no_after_batch_question(self):
        """User says 'no' after 'Ready for Batch 2?'"""
        state = create_initial_state(lesson_number=1, user_id="test_user")
        state.add_message("assistant", "Ready for Batch 2?")

        transformed = transform_short_response("no", state.conversation_history)

        assert transformed == "not yet"

    def test_nope_after_quiz_question(self):
        """User says 'nope' after 'Want to take a quiz?'"""
        state = create_initial_state(lesson_number=1, user_id="test_user")
        state.add_message("assistant", "Want to take a quiz?")

        transformed = transform_short_response("nope", state.conversation_history)

        assert transformed == "not yet"

    def test_nah_after_any_question(self):
        """User says 'nah' after 'Ready to continue?'"""
        state = create_initial_state(lesson_number=1, user_id="test_user")
        state.add_message("assistant", "Ready to continue?")

        transformed = transform_short_response("nah", state.conversation_history)

        assert transformed == "not yet"


class TestEdgeCases:
    """Test edge cases and boundary conditions"""

    def test_non_short_response_returns_original(self):
        """Regular user input should pass through unchanged"""
        state = create_initial_state(lesson_number=1, user_id="test_user")
        state.add_message("assistant", "Ready for Batch 2?")

        transformed = transform_short_response(
            "I want to learn vocabulary", state.conversation_history
        )

        assert transformed == "I want to learn vocabulary"

    def test_short_response_with_empty_history(self):
        """Short response with no conversation history"""
        state = create_initial_state(lesson_number=1, user_id="test_user")

        transformed = transform_short_response("yes", state.conversation_history)

        # Should return original since no context
        assert transformed == "yes"

    def test_case_insensitive_matching(self):
        """Short responses should work regardless of case"""
        state = create_initial_state(lesson_number=1, user_id="test_user")
        state.add_message("assistant", "Ready for Batch 2?")

        transformed_upper = transform_short_response("YES", state.conversation_history)
        transformed_mixed = transform_short_response("Yes", state.conversation_history)

        assert transformed_upper == "give me batch 2"
        assert transformed_mixed == "give me batch 2"

    def test_whitespace_handling(self):
        """Short responses with extra whitespace"""
        state = create_initial_state(lesson_number=1, user_id="test_user")
        state.add_message("assistant", "Want a quiz?")

        transformed = transform_short_response("  ok  ", state.conversation_history)

        assert transformed == "start quiz"


class TestKeywordDetection:
    """Test keyword detection in last agent message"""

    def test_detect_batch_keyword_variations(self):
        """Detect 'batch' keyword in various forms"""
        state = create_initial_state(lesson_number=1, user_id="test_user")

        # Test variations
        variations = [
            "Ready for Batch 2?",
            "Continue with the next batch?",
            "Want to start batch 3?",
        ]

        for msg in variations:
            state.conversation_history = []
            state.add_message("assistant", msg)
            transformed = transform_short_response("yes", state.conversation_history)
            assert "batch" in transformed.lower()

    def test_detect_quiz_keyword_variations(self):
        """Detect 'quiz' keyword in various forms"""
        state = create_initial_state(lesson_number=1, user_id="test_user")

        variations = [
            "Want to take a quiz?",
            "Ready for your quiz?",
            "Start the quiz now?",
        ]

        for msg in variations:
            state.conversation_history = []
            state.add_message("assistant", msg)
            transformed = transform_short_response("ok", state.conversation_history)
            assert "quiz" in transformed.lower()

    def test_detect_vocabulary_keyword_variations(self):
        """Detect 'vocabulary' keyword in various forms"""
        state = create_initial_state(lesson_number=1, user_id="test_user")

        variations = [
            "Want to learn vocabulary?",
            "Ready for vocab words?",
            "Start with vocabulary?",
        ]

        for msg in variations:
            state.conversation_history = []
            state.add_message("assistant", msg)
            transformed = transform_short_response("sure", state.conversation_history)
            assert "vocab" in transformed.lower()

    def test_detect_grammar_keyword_variations(self):
        """Detect 'grammar' keyword in various forms"""
        state = create_initial_state(lesson_number=1, user_id="test_user")

        variations = [
            "Want to learn grammar?",
            "Ready for grammar lesson?",
            "Start with grammar?",
        ]

        for msg in variations:
            state.conversation_history = []
            state.add_message("assistant", msg)
            transformed = transform_short_response("yeah", state.conversation_history)
            assert "grammar" in transformed.lower()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
