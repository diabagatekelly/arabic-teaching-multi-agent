"""Integration tests for batch quiz with REAL ContentAgent behavior.

These tests use real agents (or minimal mocking) to verify actual behavior,
not just mocked responses. They catch bugs that unit tests with full mocking miss.

CRITICAL: These tests would have caught the "table" bug where ContentAgent
was being passed wrong learned_items and generating questions for batch 2 words
during batch 1 quiz.
"""

from unittest.mock import MagicMock

import pytest

from src.agents.content_agent import ContentAgent
from src.orchestrator.nodes import ContentNode
from src.orchestrator.state import create_initial_state


@pytest.fixture
def real_content_agent():
    """Create ContentAgent with mocked model but real logic."""
    mock_model = MagicMock()
    mock_tokenizer = MagicMock()

    # Mock generate_response to return valid exercise JSON
    agent = ContentAgent(model=mock_model, tokenizer=mock_tokenizer, max_new_tokens=512)

    # Override generate_response to simulate model output
    def mock_generate(prompt: str) -> str:
        """Generate exercise based on prompt - simulates real model behavior."""
        # Extract available words from prompt
        if "Available Items" in prompt:
            # Parse available items from prompt
            lines = prompt.split("\n")
            for line in lines:
                if "Available Items" in line:
                    # Extract words - should be "كِتَاب (kitaabun) - book, ..." format
                    items_str = line.split("Available Items (NOT already quizzed):")[1].strip()
                    if items_str and items_str != "":
                        # Pick first available word
                        first_item = items_str.split(",")[0].strip()
                        arabic = first_item.split("(")[0].strip()
                        transliteration = first_item.split("(")[1].split(")")[0].strip()
                        english = first_item.split("-")[1].strip()

                        return f"""```json
{{
    "exercise_id": "ex_001",
    "exercise_type": "translation",
    "question": "What does {arabic} mean?\\n({transliteration})",
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

        # Fallback: return first word from lesson vocab if available
        return """```json
{
    "exercise_id": "ex_001",
    "exercise_type": "translation",
    "question": "What does كِتَاب mean?\\n(kitaabun)",
    "answer": "book",
    "correct": "book",
    "type": "translation",
    "difficulty": "beginner",
    "metadata": {
        "word_arabic": "كِتَاب",
        "word_transliteration": "kitaabun",
        "english": "book"
    }
}
```"""

    agent.generate_response = mock_generate
    return agent


class TestBatchQuizRealBehavior:
    """Integration tests using real ContentAgent logic."""

    def test_batch_1_only_uses_batch_1_words(self, real_content_agent):
        """
        CRITICAL TEST: ContentAgent should ONLY generate questions for batch 1 words.

        This test would have caught the bug where "table" (batch 2 word) was
        appearing in batch 1 quiz.

        Batch 1: book, house, pen
        Batch 2: table, school, window

        When quizzing batch 1, should NEVER ask about table/school/window.
        """
        state = create_initial_state(lesson_number=1, user_id="test_user")
        state.current_vocab_batch = 1
        state.lesson_initialized = True

        # Simulate RAG-loaded vocabulary (6 words total, 2 batches of 3)
        state.cached_vocab_words = [
            # Batch 1
            {"arabic": "كِتَاب", "transliteration": "kitaabun", "english": "book", "word_id": "w1"},
            {"arabic": "بَيْت", "transliteration": "baytun", "english": "house", "word_id": "w2"},
            {"arabic": "قَلَم", "transliteration": "qalamun", "english": "pen", "word_id": "w3"},
            # Batch 2
            {
                "arabic": "طَاوِلَةٌ",
                "transliteration": "taawilatun",
                "english": "table",
                "word_id": "w4",
            },
            {
                "arabic": "مَدْرَسَة",
                "transliteration": "madrasatun",
                "english": "school",
                "word_id": "w5",
            },
            {
                "arabic": "نَافِذَة",
                "transliteration": "naafidhatun",
                "english": "window",
                "word_id": "w6",
            },
        ]

        content_node = ContentNode(agent=real_content_agent)

        # Generate exercise for batch 1
        state.add_message("user", "quiz me")
        state = content_node(state)

        # CRITICAL ASSERTIONS
        exercise = state.pending_exercise
        assert exercise is not None, "Should generate exercise"

        # Check metadata for which word was selected
        word_arabic = exercise.metadata.get("word_arabic", "")

        # MUST be one of batch 1 words
        batch_1_words = ["كِتَاب", "بَيْت", "قَلَم"]
        assert word_arabic in batch_1_words, (
            f"ERROR: Generated quiz for '{word_arabic}' but batch 1 only contains {batch_1_words}! "
            f"This is the BUG where ContentAgent gets wrong learned_items."
        )

        # MUST NOT be any batch 2 word
        batch_2_words = ["طَاوِلَةٌ", "مَدْرَسَة", "نَافِذَة"]
        assert word_arabic not in batch_2_words, (
            f"ERROR: Generated quiz for '{word_arabic}' which is a BATCH 2 word! "
            f"Should only use batch 1 words: {batch_1_words}"
        )

    def test_batch_quizzed_words_prevents_repeats(self, real_content_agent):
        """
        Test that batch_quizzed_words actually prevents repeating same word.

        This verifies the filtering logic in ContentAgent.generate_exercise().
        """
        state = create_initial_state(lesson_number=1, user_id="test_user")
        state.current_vocab_batch = 1
        state.lesson_initialized = True

        state.cached_vocab_words = [
            {"arabic": "كِتَاب", "transliteration": "kitaabun", "english": "book", "word_id": "w1"},
            {"arabic": "بَيْت", "transliteration": "baytun", "english": "house", "word_id": "w2"},
            {"arabic": "قَلَم", "transliteration": "qalamun", "english": "pen", "word_id": "w3"},
        ]

        # Mark "book" as already quizzed
        state.batch_quizzed_words = ["كِتَاب"]

        content_node = ContentNode(agent=real_content_agent)

        # Generate exercise
        state.add_message("user", "quiz me")
        state = content_node(state)

        exercise = state.pending_exercise
        word_arabic = exercise.metadata.get("word_arabic", "")

        # Should NOT be the already-quizzed word
        assert word_arabic != "كِتَاب", (
            "ERROR: Generated quiz for 'كِتَاب' (book) even though it's in batch_quizzed_words! "
            "The filtering logic is broken."
        )

        # Should be one of the remaining words
        remaining_words = ["بَيْت", "قَلَم"]
        assert (
            word_arabic in remaining_words
        ), f"Word should be one of {remaining_words}, got '{word_arabic}'"

    def test_learned_items_format_matches_prompt_expectation(self, real_content_agent):
        """
        Verify learned_items are formatted correctly for ContentAgent prompt.

        Format should be: "كِتَاب (kitaabun) - book"
        """
        state = create_initial_state(lesson_number=1, user_id="test_user")
        state.current_vocab_batch = 1
        state.lesson_initialized = True

        state.cached_vocab_words = [
            {"arabic": "كِتَاب", "transliteration": "kitaabun", "english": "book", "word_id": "w1"},
            {"arabic": "بَيْت", "transliteration": "baytun", "english": "house", "word_id": "w2"},
            {"arabic": "قَلَم", "transliteration": "qalamun", "english": "pen", "word_id": "w3"},
        ]

        content_node = ContentNode(agent=real_content_agent)

        # This should call _parse_exercise_request internally
        state.add_message("user", "quiz me")

        # Call the exercise request parser directly to test
        exercise_request = content_node._parse_exercise_request(state)

        learned_items = exercise_request["learned_items"]

        # Verify format
        assert len(learned_items) == 3, "Should have 3 items for batch 1"

        for item in learned_items:
            # Should have format: "Arabic (transliteration) - english"
            assert " (" in item, f"Missing transliteration in '{item}'"
            assert ") - " in item, f"Missing english translation in '{item}'"

        # Verify first item is formatted correctly
        assert learned_items[0] == "كِتَاب (kitaabun) - book"

    def test_batch_2_uses_batch_2_words(self, real_content_agent):
        """
        Verify batch 2 correctly uses words 4-6, not words 1-3.

        Tests the batch slicing logic in _parse_exercise_request.
        """
        state = create_initial_state(lesson_number=1, user_id="test_user")
        state.current_vocab_batch = 2  # Batch 2
        state.lesson_initialized = True

        state.cached_vocab_words = [
            # Batch 1
            {"arabic": "كِتَاب", "transliteration": "kitaabun", "english": "book", "word_id": "w1"},
            {"arabic": "بَيْت", "transliteration": "baytun", "english": "house", "word_id": "w2"},
            {"arabic": "قَلَم", "transliteration": "qalamun", "english": "pen", "word_id": "w3"},
            # Batch 2
            {
                "arabic": "طَاوِلَةٌ",
                "transliteration": "taawilatun",
                "english": "table",
                "word_id": "w4",
            },
            {
                "arabic": "مَدْرَسَة",
                "transliteration": "madrasatun",
                "english": "school",
                "word_id": "w5",
            },
            {
                "arabic": "نَافِذَة",
                "transliteration": "naafidhatun",
                "english": "window",
                "word_id": "w6",
            },
        ]

        content_node = ContentNode(agent=real_content_agent)

        # Generate exercise for batch 2
        state.add_message("user", "quiz me")
        state = content_node(state)

        exercise = state.pending_exercise
        word_arabic = exercise.metadata.get("word_arabic", "")

        # MUST be one of batch 2 words
        batch_2_words = ["طَاوِلَةٌ", "مَدْرَسَة", "نَافِذَة"]
        assert (
            word_arabic in batch_2_words
        ), f"Batch 2 quiz should use batch 2 words {batch_2_words}, got '{word_arabic}'"

        # MUST NOT be any batch 1 word
        batch_1_words = ["كِتَاب", "بَيْت", "قَلَم"]
        assert (
            word_arabic not in batch_1_words
        ), f"Batch 2 quiz should NOT use batch 1 words, but got '{word_arabic}'"


class TestContentAgentPromptConstruction:
    """Test that prompts passed to ContentAgent are correct."""

    def test_batch_quizzed_words_appear_in_prompt(self, real_content_agent):
        """
        Verify batch_quizzed_words are actually passed in the prompt.

        If they're not in the prompt, the model can't avoid them!
        """
        # Spy on generate_response to capture the prompt
        prompts_captured = []
        original_generate = real_content_agent.generate_response

        def spy_generate(prompt: str) -> str:
            prompts_captured.append(prompt)
            return original_generate(prompt)

        real_content_agent.generate_response = spy_generate

        # Setup state with quizzed words
        state = create_initial_state(lesson_number=1, user_id="test_user")
        state.current_vocab_batch = 1
        state.lesson_initialized = True
        state.batch_quizzed_words = ["كِتَاب", "بَيْت"]

        state.cached_vocab_words = [
            {"arabic": "كِتَاب", "transliteration": "kitaabun", "english": "book", "word_id": "w1"},
            {"arabic": "بَيْت", "transliteration": "baytun", "english": "house", "word_id": "w2"},
            {"arabic": "قَلَم", "transliteration": "qalamun", "english": "pen", "word_id": "w3"},
        ]

        content_node = ContentNode(agent=real_content_agent)
        state.add_message("user", "quiz me")
        state = content_node(state)

        # Check the captured prompt
        assert len(prompts_captured) == 1, "Should have called generate_response once"
        prompt = prompts_captured[0]

        # Critical checks
        assert (
            "Words Already Quizzed (DO NOT USE):" in prompt
        ), "Prompt must include 'Words Already Quizzed' section!"
        assert "كِتَاب" in prompt, "Already-quizzed word 'كِتَاب' must appear in prompt"
        assert "بَيْت" in prompt, "Already-quizzed word 'بَيْت' must appear in prompt"

        # Should also have available items section
        assert (
            "Available Items (NOT already quizzed):" in prompt
        ), "Prompt must tell model which words are available!"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
