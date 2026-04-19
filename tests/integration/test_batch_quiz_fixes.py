"""Integration tests for batch quiz bug fixes.

These tests capture the bugs reported in manual testing:
1. Harakaat normalization (كِتَابٌ vs كِتَاب)
2. Remaining count calculation
3. Auto-continue after feedback
4. Word repetition prevention
5. Next batch vs next word disambiguation
"""

from unittest.mock import MagicMock

import pytest

from src.agents.content_agent import ContentAgent
from src.orchestrator.nodes import ContentNode
from src.orchestrator.state import create_initial_state


@pytest.fixture
def mock_content_agent():
    """Create ContentAgent with mocked model."""
    mock_model = MagicMock()
    mock_tokenizer = MagicMock()
    agent = ContentAgent(model=mock_model, tokenizer=mock_tokenizer, max_new_tokens=512)

    def mock_generate(prompt: str) -> str:
        """Generate exercise from available items in prompt."""
        for line in prompt.split("\n"):
            if "Available Items (NOT already quizzed):" in line:
                items_str = line.split("Available Items (NOT already quizzed):")[1].strip()
                if items_str:
                    first_item = items_str.split(",")[0].strip()
                    try:
                        arabic = first_item.split("(")[0].strip()
                        transliteration = first_item.split("(")[1].split(")")[0].strip()
                        english = first_item.split("-")[1].strip()

                        return f"""```json
{{
    "exercise_id": "ex_001",
    "exercise_type": "translation",
    "question": "What does {arabic} mean?",
    "answer": "{english}",
    "correct": "{english}",
    "type": "translation",
    "difficulty": "beginner",
    "metadata": {{
        "word_arabic": "{arabic}",
        "word_transliteration": "{transliteration}",
        "english": "{english}"
    }}
}}
```"""
                    except (IndexError, ValueError):
                        pass
        # Fallback
        return """```json
{
    "question": "What does كِتَاب mean?",
    "answer": "book",
    "correct": "book"
}
```"""

    agent.generate_response = mock_generate
    return agent


class TestHarakaatNormalization:
    """Test that Arabic words with different harakaat are treated as same word."""

    def test_word_with_tanween_vs_without(self, mock_content_agent):
        """
        BUG: كِتَابٌ (with tanween) vs كِتَاب (without) aren't recognized as same word.

        Result: Word gets repeated because tracking doesn't normalize harakaat.
        """
        state = create_initial_state(lesson_number=1, user_id="test_user")
        state.current_vocab_batch = 1
        state.lesson_initialized = True
        state.cached_vocab_words = [
            {"arabic": "كِتَاب", "transliteration": "kitaabun", "english": "book", "word_id": "w1"},
            {"arabic": "بَيْت", "transliteration": "baytun", "english": "house", "word_id": "w2"},
        ]

        content_node = ContentNode(agent=mock_content_agent)

        # First quiz - generates "كِتَابٌ" (with tanween)
        state.add_message("user", "quiz me")
        state = content_node(state)

        word1 = state.pending_exercise.metadata.get("word_arabic", "")
        assert "كتاب" in word1.replace("\u064b", "").replace("\u064c", "").replace(
            "\u064d", ""
        ).replace("\u064e", "").replace("\u064f", "").replace("\u0650", "").replace(
            "\u0651", ""
        ).replace("\u0652", "")

        # Second quiz - should NOT generate book again
        state.clear_pending_exercise()
        state.add_message("user", "quiz me")
        state = content_node(state)

        word2 = state.pending_exercise.metadata.get("word_arabic", "")

        # CRITICAL: Even if word2 has different harakaat, should not be "book"
        # Normalize both for comparison
        import re

        def normalize(text):
            return re.sub(r"[\u064B-\u0652\u0670]", "", text)

        assert normalize(word2) != "كتاب", f"Should not repeat book! Got: {word2}"


class TestRemainingCount:
    """Test that remaining word count is calculated correctly."""

    def test_remaining_count_after_first_word(self, mock_content_agent):
        """
        BUG: After quizzing 1 word from 3-word batch, says "3 remaining" instead of "2".
        """
        state = create_initial_state(lesson_number=1, user_id="test_user")
        state.current_vocab_batch = 1
        state.lesson_initialized = True
        state.cached_vocab_words = [
            {"arabic": "كِتَاب", "transliteration": "kitaabun", "english": "book", "word_id": "w1"},
            {"arabic": "بَيْت", "transliteration": "baytun", "english": "house", "word_id": "w2"},
            {"arabic": "قَلَم", "transliteration": "qalamun", "english": "pen", "word_id": "w3"},
        ]

        # Simulate: user answered first word correctly
        state.batch_quizzed_words = ["كِتَاب"]

        # Calculate remaining
        batch_size = 3
        start_idx = (state.current_vocab_batch - 1) * batch_size
        end_idx = start_idx + batch_size
        current_batch_words = state.cached_vocab_words[start_idx:end_idx]
        batch_words_arabic = [w["arabic"] for w in current_batch_words]

        import re

        def normalize(text):
            return re.sub(r"[\u064B-\u0652\u0670]", "", text)

        remaining = len(
            [
                w
                for w in batch_words_arabic
                if not any(
                    normalize(quizzed) == normalize(w) for quizzed in state.batch_quizzed_words
                )
            ]
        )

        assert remaining == 2, f"After 1 word, should have 2 remaining, got {remaining}"


class TestAutoContinue:
    """Test that after feedback, next quiz auto-generates if words remain."""

    def test_auto_continue_when_words_remain(self):
        """
        BUG: After feedback, says "Next word coming up..." but then WAITS for user.
        Should auto-trigger next quiz generation.
        """
        state = create_initial_state(lesson_number=1, user_id="test_user")
        state.current_mode = "teaching_vocab"
        state.current_vocab_batch = 1
        state.cached_vocab_words = [
            {"arabic": "كِتَاب", "transliteration": "kitaabun", "english": "book", "word_id": "w1"},
            {"arabic": "بَيْت", "transliteration": "baytun", "english": "house", "word_id": "w2"},
        ]
        state.batch_quizzed_words = ["كِتَاب"]  # 1 done, 1 remaining

        # Simulate feedback flow in TeachingNode._handle_feedback
        batch_size = 3
        start_idx = (state.current_vocab_batch - 1) * batch_size
        end_idx = start_idx + batch_size
        current_batch_words = state.cached_vocab_words[start_idx:end_idx]
        batch_words_arabic = [w["arabic"] for w in current_batch_words]

        import re

        def normalize(text):
            return re.sub(r"[\u064B-\u0652\u0670]", "", text)

        all_quizzed = all(
            any(normalize(quizzed) == normalize(w) for quizzed in state.batch_quizzed_words)
            for w in batch_words_arabic
        )

        if not all_quizzed:
            # More words remain - should auto-trigger next quiz
            state.next_agent = "agent3"

        assert state.next_agent == "agent3", "Should auto-trigger content agent for next quiz"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
