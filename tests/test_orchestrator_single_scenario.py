"""Single orchestrator routing test to verify approach.

This test mocks the teaching agent's response and verifies the orchestrator
correctly detects the keyword and routes to the next agent.
"""

from unittest.mock import Mock

from src.orchestrator.nodes import TeachingNode
from src.orchestrator.state import create_initial_state


def test_quiz_request_keyword_routing():
    """
    Scenario: User requests quiz → Teaching agent responds with 'quiz' keyword
    Expected: Orchestrator routes to ContentAgent (agent3) for quiz generation

    Flow:
    1. User says "test me"
    2. Teaching agent (MOCKED) returns "Great! Let me prepare your quiz."
    3. Orchestrator should:
       - Detect "quiz" keyword in response
       - Set next_agent = "agent3" (ContentAgent)
       - Strip any [GENERATE_EXERCISE] markers from conversation history
    """

    # ===== SETUP =====
    # Create initial state
    state = create_initial_state(lesson_number=1, user_id="test_user")

    # User has learned some vocab and is in vocab mode
    state.current_mode = "teaching_vocab"
    state.cached_vocab_words = [
        {"arabic": "كِتَاب", "transliteration": "kitaabun", "english": "book"},
        {"arabic": "بَيْت", "transliteration": "baytun", "english": "house"},
        {"arabic": "قَلَم", "transliteration": "qalamun", "english": "pen"},
    ]

    # User sends message
    state.add_message("user", "test me")

    # ===== MOCK AGENT =====
    # Mock teaching agent to return response with keyword
    mock_teaching_agent = Mock()
    mock_teaching_agent.handle_user_message.return_value = "Great! Let me prepare your quiz."

    # Create teaching node with mocked agent
    teaching_node = TeachingNode(agent=mock_teaching_agent)

    # ===== EXECUTE =====
    result_state = teaching_node(state)

    # ===== VERIFY =====
    # 1. Check routing decision
    assert (
        result_state.next_agent == "agent3"
    ), f"Expected next_agent='agent3' (ContentAgent), got '{result_state.next_agent}'"

    # 2. Check last agent tracking
    assert (
        result_state.last_agent == "agent1"
    ), f"Expected last_agent='agent1' (TeachingAgent), got '{result_state.last_agent}'"

    # 3. Verify response added to conversation
    assert (
        len(result_state.conversation_history) == 2
    ), f"Expected 2 messages (user + agent1), got {len(result_state.conversation_history)}"

    # 4. Check agent response content
    agent_response = result_state.conversation_history[-1].content
    assert (
        "quiz" in agent_response.lower()
    ), f"Expected 'quiz' keyword in response, got: {agent_response}"

    # 5. Verify no control markers in conversation history
    assert (
        "[GENERATE_EXERCISE]" not in agent_response
    ), f"Control marker should be stripped, got: {agent_response}"

    # 6. Verify state not waiting for answer yet (needs ContentAgent first)
    assert (
        result_state.awaiting_user_answer is False
    ), "Should not be awaiting answer until exercise is generated"

    print("✅ Test passed!")
    print(f"   User input: {state.conversation_history[0].content}")
    print(f"   Agent response: {agent_response}")
    print(f"   Next agent: {result_state.next_agent}")
    print("   Keyword detected: 'quiz'")


if __name__ == "__main__":
    # Run test directly
    test_quiz_request_keyword_routing()
    print("\n✅ All checks passed! Orchestrator routing working as expected.")
