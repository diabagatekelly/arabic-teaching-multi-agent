"""Tests for routing logic."""

import pytest

from src.orchestrator.routing import (
    route_next_node,
    should_generate_exercise,
    should_grade_answer,
    should_wait_for_user,
)
from src.orchestrator.state import Exercise, SystemState


class TestRouteNextNode:
    """Test main routing function."""

    @pytest.fixture
    def state(self):
        """Create a fresh state."""
        return SystemState(user_id="test", session_id="test")

    @pytest.mark.parametrize(
        "next_agent,expected",
        [
            ("agent1", "teaching"),
            ("agent2", "grading"),
            ("agent3", "content"),
            ("user", "user"),
            ("end", "end"),
            ("unknown", "teaching"),  # default
        ],
    )
    def test_route_next_node(self, state, next_agent, expected):
        """Test routing to different nodes based on next_agent."""
        state.next_agent = next_agent
        assert route_next_node(state) == expected


class TestShouldWaitForUser:
    """Test should_wait_for_user logic."""

    @pytest.fixture
    def state(self):
        """Create a fresh state."""
        return SystemState(user_id="test", session_id="test")

    def test_wait_when_exercise_pending(self, state):
        """Should wait when exercise is pending."""
        exercise = Exercise(
            exercise_id="ex_1",
            exercise_type="translation",
            question="Test",
            answer="Test",
            difficulty="beginner",
        )
        state.set_pending_exercise(exercise)
        assert should_wait_for_user(state) is True

    @pytest.mark.parametrize(
        "message",
        [
            "Are you ready to start?",
            "Translate the following: book",
        ],
    )
    def test_wait_when_agent_expects_response(self, state, message):
        """Should wait when agent asks question or requests action."""
        state.add_message("agent1", message)
        assert should_wait_for_user(state) is True

    def test_dont_wait_when_no_history(self, state):
        """Should not wait when no conversation history."""
        assert should_wait_for_user(state) is False

    def test_dont_wait_when_agent_provides_info(self, state):
        """Should not wait when agent just provides information."""
        state.add_message("agent1", "Here's a grammar rule: nouns have gender.")
        assert should_wait_for_user(state) is False


class TestShouldGenerateExercise:
    """Test should_generate_exercise logic."""

    @pytest.fixture
    def state(self):
        """Create a fresh state."""
        return SystemState(user_id="test", session_id="test")

    @pytest.mark.parametrize(
        "message",
        [
            "Let's practice with an exercise.",
            "Time to practice what you learned!",
            "Let's take a quiz to test your knowledge.",
            "Translate the following to Arabic:",
        ],
    )
    def test_generate_when_agent_requests_exercise(self, state, message):
        """Should generate when agent requests exercise/practice/quiz/translation."""
        state.add_message("agent1", message)
        assert should_generate_exercise(state) is True

    def test_dont_generate_when_no_history(self, state):
        """Should not generate when no history."""
        assert should_generate_exercise(state) is False

    def test_dont_generate_when_last_message_not_agent(self, state):
        """Should not generate when last message is from user."""
        state.add_message("user", "I want to practice")
        assert should_generate_exercise(state) is False

    def test_dont_generate_when_agent_teaches(self, state):
        """Should not generate when agent is just teaching."""
        state.add_message("agent1", "In Arabic, nouns have gender.")
        assert should_generate_exercise(state) is False


class TestShouldGradeAnswer:
    """Test should_grade_answer logic."""

    @pytest.fixture
    def state(self):
        """Create a fresh state."""
        return SystemState(user_id="test", session_id="test")

    def test_grade_when_user_answers_exercise(self, state):
        """Should grade when user submits answer to pending exercise."""
        exercise = Exercise(
            exercise_id="ex_1",
            exercise_type="translation",
            question="Translate: book",
            answer="الكِتَاب",
            difficulty="beginner",
        )
        state.set_pending_exercise(exercise)
        state.add_message("user", "الكِتَاب")
        assert should_grade_answer(state) is True

    def test_dont_grade_without_pending_exercise(self, state):
        """Should not grade when no exercise is pending."""
        state.add_message("user", "I'm ready!")
        assert should_grade_answer(state) is False

    def test_dont_grade_when_last_message_not_user(self, state):
        """Should not grade when last message is from agent."""
        exercise = Exercise(
            exercise_id="ex_1",
            exercise_type="translation",
            question="Test",
            answer="Test",
            difficulty="beginner",
        )
        state.set_pending_exercise(exercise)
        state.add_message("agent1", "Please answer the question")
        assert should_grade_answer(state) is False

    def test_dont_grade_empty_answer(self, state):
        """Should not grade empty answer."""
        exercise = Exercise(
            exercise_id="ex_1",
            exercise_type="translation",
            question="Test",
            answer="Test",
            difficulty="beginner",
        )
        state.set_pending_exercise(exercise)
        state.add_message("user", "   ")
        assert should_grade_answer(state) is False
