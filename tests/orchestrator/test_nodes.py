"""Tests for agent node wrappers."""

from unittest.mock import Mock

import pytest

from src.orchestrator.nodes import ContentNode, GradingNode, TeachingNode
from src.orchestrator.state import Exercise, SystemState


class TestTeachingNode:
    """Test TeachingNode wrapper."""

    @pytest.fixture
    def mock_agent(self):
        """Create mock teaching agent."""
        agent = Mock()
        agent.start_lesson.return_value = "Welcome to Lesson 1!"
        agent.handle_user_message.return_value = "Let's learn some vocabulary."
        agent.provide_feedback.return_value = "Great job!"
        return agent

    @pytest.fixture
    def state(self):
        """Create fresh state."""
        return SystemState(user_id="test", session_id="test")

    def test_lesson_start(self, mock_agent, state):
        """Test handling lesson start (no conversation history)."""
        node = TeachingNode(mock_agent)
        result = node(state)

        # Check agent was called correctly
        mock_agent.start_lesson.assert_called_once()
        call_args = mock_agent.start_lesson.call_args[0][0]
        assert call_args["lesson_number"] == 1
        assert call_args["mode"] == "vocabulary"

        # Check state updates
        assert len(result.conversation_history) == 1
        assert result.conversation_history[0].role == "agent1"
        assert result.conversation_history[0].content == "Welcome to Lesson 1!"
        assert result.last_agent == "agent1"
        assert result.next_agent == "user"

    def test_handle_user_message(self, mock_agent, state):
        """Test handling user message."""
        state.add_message("user", "I'm ready to learn!")
        state.add_learned_item("test_item")

        node = TeachingNode(mock_agent)
        result = node(state)

        # Check agent was called correctly
        mock_agent.handle_user_message.assert_called_once()
        call_args = mock_agent.handle_user_message.call_args[0][0]
        assert call_args["user_input"] == "I'm ready to learn!"
        assert call_args["learned_items"] == ["test_item"]
        assert call_args["mode"] == "vocabulary"

        # Check state updates
        assert len(result.conversation_history) == 2
        assert result.conversation_history[1].role == "agent1"
        assert result.last_agent == "agent1"

    def test_handle_feedback(self, mock_agent, state):
        """Test providing feedback after grading."""
        # Setup: grading just completed
        state.last_agent = "agent2"
        state.add_message(
            "agent2",
            "Your answer is correct!",
            metadata={"user_answer": "الكِتَاب", "correct_answer": "الكِتَاب"},
        )

        node = TeachingNode(mock_agent)
        result = node(state)

        # Check agent was called correctly
        mock_agent.provide_feedback.assert_called_once()
        call_args = mock_agent.provide_feedback.call_args[0][0]
        assert call_args["is_correct"] is True
        assert call_args["user_answer"] == "الكِتَاب"
        assert call_args["correct_answer"] == "الكِتَاب"

        # Check state updates
        assert result.last_agent == "agent1"
        assert result.next_agent == "user"

    def test_error_handling(self, mock_agent, state):
        """Test error handling in teaching node."""
        mock_agent.start_lesson.side_effect = Exception("Model error")

        node = TeachingNode(mock_agent)
        result = node(state)

        # Should add error message and fallback to user
        assert any(msg.role == "system" for msg in result.conversation_history)
        assert result.next_agent == "user"


class TestGradingNode:
    """Test GradingNode wrapper."""

    @pytest.fixture
    def mock_agent(self):
        """Create mock grading agent."""
        agent = Mock()
        agent.grade_answer.return_value = "Correct! Well done."
        return agent

    @pytest.fixture
    def state(self):
        """Create state with pending exercise."""
        state = SystemState(user_id="test", session_id="test")
        exercise = Exercise(
            exercise_id="ex_1",
            exercise_type="translation",
            question="Translate: book",
            answer="الكِتَاب",
            difficulty="beginner",
        )
        state.set_pending_exercise(exercise)
        state.add_message("user", "الكِتَاب")
        return state

    @pytest.mark.parametrize(
        "response,expected_correct,expected_correct_count",
        [
            ("Correct! Well done.", True, 1),
            ("✓ Correct!", True, 1),
            ("Incorrect. The correct answer is...", False, 0),
        ],
    )
    def test_grade_answer(
        self, mock_agent, state, response, expected_correct, expected_correct_count
    ):
        """Test grading with correctness detection."""
        mock_agent.grade_answer.return_value = response

        node = GradingNode(mock_agent)
        result = node(state)

        # Check agent was called correctly
        mock_agent.grade_answer.assert_called_once()
        call_args = mock_agent.grade_answer.call_args[0][0]
        assert call_args["user_answer"] == "الكِتَاب"
        assert call_args["correct_answer"] == "الكِتَاب"
        assert call_args["question"] == "Translate: book"

        # Check state updates
        assert len(result.conversation_history) == 2
        assert result.conversation_history[1].role == "agent2"
        assert result.conversation_history[1].metadata["is_correct"] is expected_correct
        assert result.pending_exercise is None
        assert result.awaiting_user_answer is False
        assert result.total_exercises_completed == 1
        assert result.total_correct_answers == expected_correct_count
        assert result.last_agent == "agent2"
        assert result.next_agent == "agent1"

    def test_grade_without_pending_exercise(self, mock_agent):
        """Test grading when no exercise is pending."""
        state = SystemState(user_id="test", session_id="test")
        state.add_message("user", "Some answer")

        node = GradingNode(mock_agent)
        result = node(state)

        # Should not call agent, route back to teaching
        mock_agent.grade_answer.assert_not_called()
        assert result.next_agent == "agent1"

    def test_error_handling(self, mock_agent, state):
        """Test error handling in grading node."""
        mock_agent.grade_answer.side_effect = Exception("Grading error")

        node = GradingNode(mock_agent)
        result = node(state)

        # Should add error message and route to teaching
        assert any(msg.role == "system" for msg in result.conversation_history)
        assert result.next_agent == "agent1"


class TestContentNode:
    """Test ContentNode wrapper."""

    @pytest.fixture
    def mock_agent(self):
        """Create mock content agent."""
        agent = Mock()
        agent.generate_exercise.return_value = (
            '```json\n{"question": "Translate: book", '
            '"answer": "الكِتَاب", "type": "translation", '
            '"difficulty": "beginner"}\n```'
        )
        return agent

    @pytest.fixture
    def state(self):
        """Create state with teaching agent requesting exercise."""
        state = SystemState(user_id="test", session_id="test")
        state.add_learned_item("كِتَاب")
        state.add_message("agent1", "Let's do an exercise.")
        return state

    def test_generate_exercise(self, mock_agent, state):
        """Test exercise generation."""
        node = ContentNode(mock_agent)
        result = node(state)

        # Check agent was called correctly
        mock_agent.generate_exercise.assert_called_once()
        call_args = mock_agent.generate_exercise.call_args[0][0]
        assert call_args["exercise_type"] == "translation"
        assert call_args["difficulty"] == "beginner"
        assert call_args["lesson_number"] == 1

        # Check state updates
        assert result.pending_exercise is not None
        assert result.pending_exercise.question == "Translate: book"
        assert result.pending_exercise.answer == "الكِتَاب"
        assert result.awaiting_user_answer is True
        assert len(result.conversation_history) == 2
        assert result.conversation_history[1].role == "agent3"
        assert result.last_agent == "agent3"
        assert result.next_agent == "user"

    def test_error_handling_invalid_json(self, mock_agent, state):
        """Test error handling with invalid JSON response."""
        mock_agent.generate_exercise.return_value = "This is not JSON"

        node = ContentNode(mock_agent)
        result = node(state)

        # Should add error message and route back to teaching
        assert any(msg.role == "system" for msg in result.conversation_history)
        assert result.next_agent == "agent1"
        assert result.pending_exercise is None

    def test_error_handling_agent_exception(self, mock_agent, state):
        """Test error handling when agent throws exception."""
        mock_agent.generate_exercise.side_effect = Exception("Model error")

        node = ContentNode(mock_agent)
        result = node(state)

        # Should add error message and route back to teaching
        assert any(msg.role == "system" for msg in result.conversation_history)
        assert result.next_agent == "agent1"
