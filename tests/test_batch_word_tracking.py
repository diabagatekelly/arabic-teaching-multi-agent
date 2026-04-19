"""Test batch word tracking to ensure no word is quizzed twice in a batch.

Scenario: User completes a batch quiz
Expected: Each word tested exactly once, no repeats
"""

from unittest.mock import Mock

from src.orchestrator.nodes import ContentNode, GradingNode, TeachingNode
from src.orchestrator.state import create_initial_state


def test_batch_words_tested_once_no_repeats():
    """
    Scenario: Complete batch quiz with 3 words
    Expected: Each word tested exactly once, tracked in batch_quizzed_words

    Flow:
    1. Request quiz → ContentAgent generates quiz for word 1
    2. Answer word 1 → GradingAgent grades → back to Teaching
    3. Teaching gives feedback → auto-triggers next quiz (word 2)
    4. Answer word 2 → graded → feedback → auto-trigger (word 3)
    5. Answer word 3 → graded → feedback → batch complete

    Verify:
    - batch_quizzed_words tracks all 3 words
    - No word appears twice
    - Each word from batch is tested
    """

    # ===== SETUP =====
    state = create_initial_state(lesson_number=1, user_id="test_user")
    state.current_mode = "teaching_vocab"
    state.current_vocab_batch = 1
    state.cached_vocab_words = [
        {"arabic": "كِتَاب", "transliteration": "kitaabun", "english": "book", "word_id": "w1"},
        {"arabic": "بَيْت", "transliteration": "baytun", "english": "house", "word_id": "w2"},
        {"arabic": "قَلَم", "transliteration": "qalamun", "english": "pen", "word_id": "w3"},
    ]
    state.lesson_initialized = True  # Skip lesson initialization in ContentNode

    # Mock agents
    mock_teaching_agent = Mock()
    mock_content_agent = Mock()
    mock_grading_agent = Mock()

    teaching_node = TeachingNode(agent=mock_teaching_agent, content_agent=mock_content_agent)
    content_node = ContentNode(agent=mock_content_agent)
    grading_node = GradingNode(agent=mock_grading_agent)

    print("\\n" + "=" * 80)
    print("BATCH WORD TRACKING TEST - 3 Words, No Repeats")
    print("=" * 80)

    # ===== WORD 1: كِتَاب (book) =====
    print("\\n--- Word 1: كِتَاب (book) ---")

    # User requests quiz
    state.add_message("user", "quiz me")
    mock_teaching_agent.handle_user_message.return_value = "Great! Let me prepare your quiz."
    state = teaching_node(state)

    print("Step 1 - Quiz requested")
    print(f"  next_agent: {state.next_agent}")
    assert state.next_agent == "agent3", "Should route to ContentAgent"

    # ContentAgent generates quiz for word 1
    mock_content_agent.generate_exercise.return_value = """```json
{
    "exercise_id": "ex_001",
    "exercise_type": "translation",
    "question": "What does كِتَاب mean?",
    "answer": "book",
    "difficulty": "beginner",
    "metadata": {"word_arabic": "كِتَاب", "word_id": "w1"}
}
```"""
    state.last_agent = "agent3"
    state = content_node(state)

    print("Step 2 - Quiz generated for كِتَاب")
    print(f"  batch_quizzed_words: {state.batch_quizzed_words}")
    assert "كِتَاب" in state.batch_quizzed_words, "Word 1 should be tracked"
    assert len(state.batch_quizzed_words) == 1, "Only 1 word quizzed so far"

    # Present exercise
    state.last_agent = "agent3"
    state = teaching_node(state)
    assert state.awaiting_user_answer is True

    # User answers
    state.add_message("user", "book")
    mock_grading_agent.handle_grading.return_value = {
        "is_correct": True,
        "feedback": "Correct! كِتَاب means book.",
    }
    state = grading_node(state)

    print("Step 3 - User answered correctly")
    print(f"  next_agent: {state.next_agent}")
    assert state.next_agent == "agent1", "Should route to Teaching for feedback"

    # Teaching gives feedback with "next word" keyword
    state.last_agent = "agent2"
    mock_teaching_agent.handle_feedback_vocab.return_value = "Correct! ✓ كِتَاب = book. Next word."
    state = teaching_node(state)

    print("Step 4 - Feedback given with 'next word' keyword")
    print(f"  next_agent: {state.next_agent}")
    print(f"  batch_quizzed_words: {state.batch_quizzed_words}")
    assert state.next_agent == "agent3", "Should auto-trigger next quiz"
    assert len(state.batch_quizzed_words) == 1, "Still only word 1 tracked"

    # ===== WORD 2: بَيْت (house) =====
    print("\\n--- Word 2: بَيْت (house) ---")

    # ContentAgent generates quiz for word 2 (avoiding already quizzed words)
    mock_content_agent.generate_exercise.return_value = """```json
{
    "exercise_id": "ex_002",
    "exercise_type": "translation",
    "question": "What does بَيْت mean?",
    "answer": "house",
    "difficulty": "beginner",
    "metadata": {"word_arabic": "بَيْت", "word_id": "w2"}
}
```"""
    state.last_agent = "agent3"
    state = content_node(state)

    print("Step 5 - Quiz generated for بَيْت")
    print(f"  batch_quizzed_words: {state.batch_quizzed_words}")
    assert "بَيْت" in state.batch_quizzed_words, "Word 2 should be tracked"
    assert "كِتَاب" in state.batch_quizzed_words, "Word 1 still tracked"
    assert len(state.batch_quizzed_words) == 2, "2 words quizzed"
    assert len(set(state.batch_quizzed_words)) == 2, "No duplicates!"

    # Present exercise
    state.last_agent = "agent3"
    state = teaching_node(state)

    # User answers
    state.add_message("user", "house")
    mock_grading_agent.handle_grading.return_value = {
        "is_correct": True,
        "feedback": "Perfect! بَيْت means house.",
    }
    state = grading_node(state)

    # Teaching gives feedback
    state.last_agent = "agent2"
    mock_teaching_agent.handle_feedback_vocab.return_value = "Perfect! ✓ بَيْت = house. Next word."
    state = teaching_node(state)

    print("Step 6 - Feedback given, auto-triggering word 3")
    print(f"  next_agent: {state.next_agent}")
    assert state.next_agent == "agent3"

    # ===== WORD 3: قَلَم (pen) - LAST WORD =====
    print("\\n--- Word 3: قَلَم (pen) - Last Word ---")

    # ContentAgent generates quiz for word 3
    mock_content_agent.generate_exercise.return_value = """```json
{
    "exercise_id": "ex_003",
    "exercise_type": "translation",
    "question": "What does قَلَم mean?",
    "answer": "pen",
    "difficulty": "beginner",
    "metadata": {"word_arabic": "قَلَم", "word_id": "w3"}
}
```"""
    state.last_agent = "agent3"
    state = content_node(state)

    print("Step 7 - Quiz generated for قَلَم")
    print(f"  batch_quizzed_words: {state.batch_quizzed_words}")
    assert "قَلَم" in state.batch_quizzed_words, "Word 3 should be tracked"
    assert len(state.batch_quizzed_words) == 3, "All 3 words quizzed"
    assert len(set(state.batch_quizzed_words)) == 3, "No duplicates!"

    # Present exercise
    state.last_agent = "agent3"
    state = teaching_node(state)

    # User answers
    state.add_message("user", "pen")
    mock_grading_agent.handle_grading.return_value = {
        "is_correct": True,
        "feedback": "Excellent! قَلَم means pen.",
    }
    state.batch_correct_count = 3  # Simulate 3/3 correct
    state = grading_node(state)

    # Teaching gives feedback - BATCH COMPLETE (no more words)
    state.last_agent = "agent2"
    mock_teaching_agent.handle_feedback_vocab.return_value = """Perfect! ✓ قَلَم = pen.

Batch 1 complete! 🎉 Score: 3/3

Ready for Batch 2?"""
    state = teaching_node(state)

    print("Step 8 - Batch complete feedback")
    print(f"  next_agent: {state.next_agent}")
    print(f"  batch_quizzed_words: {state.batch_quizzed_words}")

    # ===== FINAL VERIFICATION =====
    print("\\n" + "=" * 80)
    print("FINAL VERIFICATION")
    print("=" * 80)

    # 1. All words tested
    assert (
        len(state.batch_quizzed_words) == 3
    ), f"Expected 3 words tested, got {len(state.batch_quizzed_words)}"

    # 2. No duplicates
    assert (
        len(set(state.batch_quizzed_words)) == 3
    ), f"Found duplicate words! {state.batch_quizzed_words}"

    # 3. All expected words present
    expected_words = ["كِتَاب", "بَيْت", "قَلَم"]
    for word in expected_words:
        assert word in state.batch_quizzed_words, f"Word '{word}' not found in batch_quizzed_words"

    # 4. Waits for user after batch complete
    assert (
        state.next_agent == "user"
    ), f"Should wait for user decision after batch, got '{state.next_agent}'"

    # 5. Batch complete message shown
    last_message = state.conversation_history[-1].content
    assert (
        "Batch 1 complete" in last_message
    ), f"Expected batch complete message, got: {last_message}"

    print("\\n✅ ALL CHECKS PASSED!")
    print(f"   Words tested: {state.batch_quizzed_words}")
    print(f"   No repeats: {len(state.batch_quizzed_words) == len(set(state.batch_quizzed_words))}")
    print("   Batch complete: Yes")
    print(f"   Waiting for user: {state.next_agent == 'user'}")


if __name__ == "__main__":
    test_batch_words_tested_once_no_repeats()
    print("\\n" + "=" * 80)
    print("✅ Batch word tracking test PASSED!")
    print("=" * 80)
