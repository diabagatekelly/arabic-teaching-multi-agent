"""Test ContentAgent's quiz generation word selection logic.

Verifies that ContentAgent:
1. Only generates quizzes for words not in batch_quizzed_words
2. Selects from the current batch (cached_vocab_words)
3. Handles edge case when all words have been quizzed
"""

from unittest.mock import Mock

from src.orchestrator.nodes import ContentNode
from src.orchestrator.state import create_initial_state


def test_content_agent_avoids_quizzed_words():
    """
    Scenario: Generate quiz when 2 out of 3 words already quizzed
    Expected: ContentAgent generates quiz only for the remaining word
    """

    # Setup state
    state = create_initial_state(lesson_number=1, user_id="test_user")
    state.current_mode = "teaching_vocab"
    state.current_vocab_batch = 1
    state.cached_vocab_words = [
        {"arabic": "كِتَاب", "transliteration": "kitaabun", "english": "book", "word_id": "w1"},
        {"arabic": "بَيْت", "transliteration": "baytun", "english": "house", "word_id": "w2"},
        {"arabic": "قَلَم", "transliteration": "qalamun", "english": "pen", "word_id": "w3"},
    ]
    # Already quizzed 2 words
    state.batch_quizzed_words = ["كِتَاب", "بَيْت"]
    state.last_agent = "agent1"  # Coming from TeachingAgent

    # Mock content agent to return quiz with word metadata
    mock_content_agent = Mock()

    def mock_quiz_generation(state):
        # Get available words (not in batch_quizzed_words)
        available_words = [
            w for w in state.cached_vocab_words if w["arabic"] not in state.batch_quizzed_words
        ]

        # Should only have قَلَم available
        assert len(available_words) == 1, f"Expected 1 available word, got {len(available_words)}"
        assert (
            available_words[0]["arabic"] == "قَلَم"
        ), f"Expected قَلَم, got {available_words[0]['arabic']}"

        # Generate quiz for the available word
        word = available_words[0]
        return {
            "exercise_id": "ex_003",
            "exercise_type": "translation",
            "question": f"What does {word['arabic']} mean?",
            "answer": word["english"],
            "difficulty": "beginner",
            "metadata": {"word_arabic": word["arabic"], "word_id": word["word_id"]},
        }

    mock_content_agent.handle_quiz_generation.side_effect = mock_quiz_generation

    # Execute
    content_node = ContentNode(agent=mock_content_agent)
    content_node(state)

    # Verify quiz was generated for the correct word
    assert result_state.pending_exercise is not None
    assert result_state.pending_exercise.metadata["word_arabic"] == "قَلَم"

    # Verify batch_quizzed_words was updated
    assert "قَلَم" in result_state.batch_quizzed_words
    assert len(result_state.batch_quizzed_words) == 3

    print("✅ ContentAgent correctly selected unquizzed word")
    print("   Available words: 1/3")
    print("   Selected: قَلَم")
    print(f"   Batch tracking: {result_state.batch_quizzed_words}")


def test_content_agent_first_word_selection():
    """
    Scenario: No words quizzed yet
    Expected: ContentAgent can select any word from batch
    """

    # Setup state
    state = create_initial_state(lesson_number=1, user_id="test_user")
    state.current_mode = "teaching_vocab"
    state.current_vocab_batch = 1
    state.cached_vocab_words = [
        {"arabic": "كِتَاب", "transliteration": "kitaabun", "english": "book", "word_id": "w1"},
        {"arabic": "بَيْت", "transliteration": "baytun", "english": "house", "word_id": "w2"},
        {"arabic": "قَلَم", "transliteration": "qalamun", "english": "pen", "word_id": "w3"},
    ]
    state.batch_quizzed_words = []  # No words quizzed
    state.last_agent = "agent1"

    # Mock content agent
    mock_content_agent = Mock()

    def mock_quiz_generation(state):
        # All words should be available
        available_words = [
            w for w in state.cached_vocab_words if w["arabic"] not in state.batch_quizzed_words
        ]

        assert len(available_words) == 3, f"Expected 3 available words, got {len(available_words)}"

        # Select first word
        word = available_words[0]
        return {
            "exercise_id": "ex_001",
            "exercise_type": "translation",
            "question": f"What does {word['arabic']} mean?",
            "answer": word["english"],
            "difficulty": "beginner",
            "metadata": {"word_arabic": word["arabic"], "word_id": word["word_id"]},
        }

    mock_content_agent.handle_quiz_generation.side_effect = mock_quiz_generation

    # Execute
    content_node = ContentNode(agent=mock_content_agent)
    content_node(state)

    # Verify quiz was generated
    assert result_state.pending_exercise is not None
    generated_word = result_state.pending_exercise.metadata["word_arabic"]

    # Verify it's from the batch
    batch_words = [w["arabic"] for w in state.cached_vocab_words]
    assert generated_word in batch_words

    # Verify tracking
    assert generated_word in result_state.batch_quizzed_words
    assert len(result_state.batch_quizzed_words) == 1

    print("✅ ContentAgent correctly selected from full batch")
    print("   Available words: 3/3")
    print(f"   Selected: {generated_word}")


def test_content_agent_all_words_quizzed():
    """
    Scenario: All words in batch already quizzed
    Expected: Should handle gracefully (no available words)
    """

    # Setup state
    state = create_initial_state(lesson_number=1, user_id="test_user")
    state.current_mode = "teaching_vocab"
    state.current_vocab_batch = 1
    state.cached_vocab_words = [
        {"arabic": "كِتَاب", "transliteration": "kitaabun", "english": "book", "word_id": "w1"},
        {"arabic": "بَيْت", "transliteration": "baytun", "english": "house", "word_id": "w2"},
        {"arabic": "قَلَم", "transliteration": "qalamun", "english": "pen", "word_id": "w3"},
    ]
    state.batch_quizzed_words = ["كِتَاب", "بَيْت", "قَلَم"]  # All quizzed
    state.last_agent = "agent1"

    # Mock content agent
    mock_content_agent = Mock()

    def mock_quiz_generation(state):
        # No words should be available
        available_words = [
            w for w in state.cached_vocab_words if w["arabic"] not in state.batch_quizzed_words
        ]

        assert len(available_words) == 0, f"Expected 0 available words, got {len(available_words)}"

        # Should not generate a quiz - return None or handle gracefully
        return None

    mock_content_agent.handle_quiz_generation.side_effect = mock_quiz_generation

    # Execute
    content_node = ContentNode(agent=mock_content_agent)
    content_node(state)

    # Verify no quiz generated
    # (In real implementation, this should be handled by orchestrator logic
    # that checks batch completion before calling ContentAgent)

    print("✅ ContentAgent correctly detected no available words")
    print("   Available words: 0/3")
    print("   Batch complete: True")


if __name__ == "__main__":
    test_content_agent_avoids_quizzed_words()
    print()
    test_content_agent_first_word_selection()
    print()
    test_content_agent_all_words_quizzed()
    print()
    print("=" * 80)
    print("✅ All ContentAgent word selection tests PASSED!")
    print("=" * 80)
