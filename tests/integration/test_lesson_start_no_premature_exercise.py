"""Test that lesson start doesn't prematurely trigger exercise generation.

Bug: If welcome message mentions "exercise" or "quiz", keyword detection
incorrectly routes to content agent instead of waiting for user.
"""

import pytest

from src.orchestrator.state import SystemState


@pytest.mark.integration
def test_lesson_start_welcome_does_not_trigger_exercise(real_orchestrator):
    """
    Test that lesson start welcome message doesn't trigger exercise generation.

    Even if the welcome message mentions "exercise" or "practice", it should
    wait for user input, not immediately route to content agent.
    """
    # Create initial state for lesson start
    state = SystemState(
        user_id="test_user",
        session_id="test_session",
        current_lesson=1,
        conversation_history=[],
        next_agent="teaching",
        last_agent="",
    )

    # Run orchestrator (should call teaching agent for lesson start)
    result = real_orchestrator.invoke(state)

    # Check that we got a welcome message
    assert len(result["conversation_history"]) > 0
    welcome_msg = result["conversation_history"][-1]

    # Verify it's from teaching agent
    assert welcome_msg.role == "agent1"

    # The message should be a welcome/introduction
    content = welcome_msg.content.lower()
    # Note: With mocked LLM, response may be generic
    # Just verify it's not an exercise
    assert "translate" not in content, f"Should not be exercise, got: {content[:200]}"

    # CRITICAL: Even if message mentions "exercise" or "practice",
    # next_agent should be "user" (waiting for input), NOT "agent3" (exercise generation)
    assert result["next_agent"] == "user", (
        f"Lesson start should wait for user input, not trigger exercise generation. "
        f"Got next_agent='{result['next_agent']}', expected 'user'. "
        f"Message content: {content[:200]}"
    )

    # Should NOT have a pending exercise yet
    assert result.get("pending_exercise") is None, "Lesson start should not create an exercise yet"

    # Should NOT be awaiting user answer (no exercise presented yet)
    assert not result.get(
        "awaiting_user_answer"
    ), "Should not be awaiting answer until user requests exercise"


@pytest.mark.integration
def test_welcome_mentioning_exercise_does_not_trigger_exercise(
    real_teaching_agent, real_grading_agent, real_content_agent, mock_llm
):
    """
    Test the specific bug: if welcome message contains word "exercise",
    the keyword detection should NOT trigger exercise generation.

    This test explicitly checks the buggy scenario by forcing the mock
    to return a welcome message with "exercise" in it (like real model does).
    """
    from src.orchestrator.graph import create_teaching_graph

    # Make mock return a welcome message that mentions "exercise" (like real model)
    mock_llm.generate.return_value = (
        "Welcome to Lesson 1!\n\n"
        "### Structure:\n"
        "1. Vocabulary - learn 10 words\n"
        "2. Grammar - 2 topics\n"
        "3. Practice - complete exercises\n\n"
        "What would you like to start with?"
    )

    # Create orchestrator with the mocked response
    orchestrator = create_teaching_graph(
        teaching_agent=real_teaching_agent,
        grading_agent=real_grading_agent,
        content_agent=real_content_agent,
    )

    state = SystemState(
        user_id="test_user",
        session_id="test_session",
        current_lesson=1,
        conversation_history=[],
        next_agent="teaching",
        last_agent="",
    )

    result = orchestrator.invoke(state)

    # Get the welcome message
    assert len(result["conversation_history"]) > 0
    welcome_msg = result["conversation_history"][-1]
    content = welcome_msg.content.lower()

    # If the message mentions "exercise" or "practice" (common in welcome messages)
    if "exercise" in content or "practice" in content:
        # BUG CHECK: next_agent should still be "user", NOT "agent3"
        assert result["next_agent"] == "user", (
            f"BUG: Welcome message mentions 'exercise/practice' but should wait for user input. "
            f"next_agent='{result['next_agent']}' (expected 'user'). "
            f"Content: {content[:300]}"
        )


@pytest.mark.integration
def test_lesson_start_does_not_skip_teaching_phase(real_orchestrator):
    """
    Test that lesson doesn't skip directly from welcome to exercise.

    User should have opportunity to:
    1. See welcome message
    2. Request vocabulary teaching
    3. Learn vocabulary
    4. THEN get exercises
    """
    # Start lesson
    state = SystemState(
        user_id="test_user",
        session_id="test_session",
        current_lesson=1,
        conversation_history=[],
        next_agent="teaching",
        last_agent="",
    )

    result = real_orchestrator.invoke(state)

    # After lesson start, should be waiting for user to choose direction
    assert result["next_agent"] == "user"

    # No exercise should be pending
    assert result.get("pending_exercise") is None

    # Conversation should have exactly 1 message (welcome)
    assert len(result["conversation_history"]) == 1
    assert result["conversation_history"][0].role == "agent1"
