"""Routing logic for multi-agent orchestration.

Determines which agent should handle the next step based on:
- Current state
- Last agent's output
- User's input
- System events
"""

import logging

from .state import SystemState

logger = logging.getLogger(__name__)


def route_next_node(state: SystemState) -> str:
    """
    Determine which node should process next.

    Routing flow:
    1. User starts session → "teaching" (Agent 1)
    2. Teaching needs exercise → "content" (Agent 3)
    3. User answers exercise → "grading" (Agent 2)
    4. Grading complete → "teaching" (Agent 1 for feedback)
    5. Teaching complete → "end"

    Args:
        state: Current system state

    Returns:
        Node name: "teaching", "grading", "content", "user", or "end"
    """
    # Check for session end conditions
    if _should_end_session(state):
        logger.info("Session ending: completion criteria met")
        return "end"

    # Route based on next_agent field (set by previous node)
    if state.next_agent == "agent1":
        return "teaching"
    elif state.next_agent == "agent2":
        return "grading"
    elif state.next_agent == "agent3":
        return "content"
    elif state.next_agent == "user":
        return "user"  # Wait for user input
    elif state.next_agent == "end":
        return "end"

    # Default: start with teaching
    logger.warning(f"Unknown next_agent: {state.next_agent}, defaulting to teaching")
    return "teaching"


def should_wait_for_user(state: SystemState) -> bool:
    """
    Determine if system should wait for user input.

    Returns True when:
    - An exercise is pending (awaiting user answer)
    - Teaching agent asked a question
    - System is waiting for user acknowledgment

    Args:
        state: Current system state

    Returns:
        True if should wait for user, False otherwise
    """
    if state.awaiting_user_answer:
        return True

    if not state.conversation_history:
        return False

    last_msg = state.conversation_history[-1]
    if last_msg.role == "agent1":
        # Check if teaching agent is waiting for user response
        content_lower = last_msg.content.lower()
        if any(
            indicator in content_lower
            for indicator in ["?", "ready", "answer", "translate", "choose", "fill in"]
        ):
            return True

    return False


def should_generate_exercise(state: SystemState) -> bool:
    """
    Determine if content agent should generate an exercise.

    Returns True when:
    - Teaching agent explicitly requests exercise
    - Time for practice after teaching
    - Quiz/test generation requested

    Args:
        state: Current system state

    Returns:
        True if should generate exercise, False otherwise
    """
    if not state.conversation_history:
        return False

    last_msg = state.conversation_history[-1]
    if last_msg.role != "agent1":
        return False

    # Check for exercise generation indicators
    content_lower = last_msg.content.lower()
    exercise_indicators = [
        "exercise",
        "practice",
        "question",
        "quiz",
        "test",
        "translate",
        "choose the correct",
        "fill in",
    ]

    return any(indicator in content_lower for indicator in exercise_indicators)


def should_grade_answer(state: SystemState) -> bool:
    """
    Determine if grading agent should evaluate user's answer.

    Returns True when:
    - There's a pending exercise
    - User just submitted an answer
    - Last message is from user (not empty)

    Args:
        state: Current system state

    Returns:
        True if should grade, False otherwise
    """
    if not state.pending_exercise:
        return False

    if not state.conversation_history:
        return False

    last_msg = state.conversation_history[-1]
    if last_msg.role != "user":
        return False

    # User submitted an answer
    return bool(last_msg.content.strip())


def _should_end_session(state: SystemState) -> bool:
    """
    Check if session should end.

    End conditions:
    - User explicitly requests to end
    - Lesson completed (all vocabulary + grammar done)
    - Error threshold exceeded
    - Session timeout

    Args:
        state: Current system state

    Returns:
        True if session should end, False otherwise
    """
    # Check for explicit end request
    if state.conversation_history:
        last_msg = state.conversation_history[-1]
        if last_msg.role == "user":
            content_lower = last_msg.content.lower()
            if any(
                phrase in content_lower for phrase in ["quit", "exit", "stop", "bye", "goodbye"]
            ):
                return True

    # Check for lesson completion (placeholder - would need more logic)
    # if state.current_mode == "complete":
    #     return True

    # Check for error threshold (placeholder)
    # if state.total_exercises_completed > 10:
    #     accuracy = state.get_accuracy()
    #     if accuracy < 30:  # Less than 30% accuracy
    #         return True

    return False


def get_next_agent_from_user_input(user_input: str, state: SystemState) -> str:
    """
    Determine next agent based on user input.

    Args:
        user_input: User's message
        state: Current system state

    Returns:
        Agent name: "agent1", "agent2", or "agent3"
    """
    # If there's a pending exercise, user is answering it → grade
    if state.pending_exercise and state.awaiting_user_answer:
        return "agent2"

    # Otherwise, user is talking to teaching agent
    return "agent1"
