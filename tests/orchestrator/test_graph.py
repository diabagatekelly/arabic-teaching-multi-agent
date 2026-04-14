"""Tests for LangGraph orchestration."""

from unittest.mock import Mock

import pytest

from src.orchestrator.graph import (
    create_new_session,
    create_teaching_graph,
    run_conversation_turn,
)
from src.orchestrator.state import Exercise, SystemState


class TestRunConversationTurn:
    """Test conversation turn execution."""

    @pytest.fixture
    def mock_graph(self):
        """Create mock graph."""
        graph = Mock()
        graph.invoke.return_value = SystemState(user_id="test", session_id="test")
        return graph

    @pytest.fixture
    def state(self):
        """Create fresh state."""
        return SystemState(user_id="test", session_id="test")

    def test_run_without_user_input(self, mock_graph, state):
        """Test running turn without user input."""
        result = run_conversation_turn(mock_graph, state)

        # Graph should be invoked
        mock_graph.invoke.assert_called_once_with(state)
        assert isinstance(result, SystemState)

    def test_run_with_user_input(self, mock_graph, state):
        """Test running turn with user input."""
        result = run_conversation_turn(mock_graph, state, user_input="Hello!")

        mock_graph.invoke.assert_called_once()
        call_args = mock_graph.invoke.call_args[0][0]
        assert len(call_args.conversation_history) == 1
        assert call_args.conversation_history[0].role == "user"
        assert call_args.conversation_history[0].content == "Hello!"
        assert call_args.next_agent == "agent1"
        assert isinstance(result, SystemState)

    def test_run_with_pending_exercise(self, mock_graph, state):
        """Test running turn when user is answering exercise."""
        exercise = Exercise(
            exercise_id="ex_1",
            exercise_type="translation",
            question="Test",
            answer="Test",
            difficulty="beginner",
        )
        state.set_pending_exercise(exercise)

        result = run_conversation_turn(mock_graph, state, user_input="الكِتَاب")

        call_args = mock_graph.invoke.call_args[0][0]
        assert call_args.next_agent == "agent2"
        assert isinstance(result, SystemState)

    def test_error_handling(self, mock_graph, state):
        """Test error handling during conversation turn."""
        mock_graph.invoke.side_effect = Exception("Graph error")

        result = run_conversation_turn(mock_graph, state, user_input="Hello")

        # Should return state with error message
        assert isinstance(result, SystemState)
        assert any(msg.role == "system" for msg in result.conversation_history)


class TestGraphIntegration:
    """Integration tests for graph execution."""

    @pytest.fixture
    def mock_agents(self):
        """Create mock agents with realistic behavior."""
        teaching = Mock()
        teaching.start_lesson.return_value = "Welcome to Lesson 1!"
        teaching.handle_user_message.return_value = "Let's learn vocabulary."
        teaching.provide_feedback.return_value = "Great job!"

        grading = Mock()
        grading.grade_answer.return_value = "Correct!"

        content = Mock()
        content.generate_exercise.return_value = (
            '```json\n{"question": "Test", "answer": "Test", '
            '"type": "translation", "difficulty": "beginner"}\n```'
        )

        return teaching, grading, content

    def test_full_lesson_flow(self, mock_agents):
        """Test complete lesson flow through graph."""
        teaching, grading, content = mock_agents
        graph = create_teaching_graph(teaching, grading, content)
        state = create_new_session("test_user", "test_session")

        # Start lesson
        result = run_conversation_turn(graph, state)

        # run_conversation_turn returns SystemState
        assert isinstance(result, SystemState)
        assert len(result.conversation_history) > 0
        assert result.conversation_history[-1].role == "agent1"

    def test_exercise_generation_flow(self, mock_agents):
        """Test exercise generation flow."""
        teaching, grading, content = mock_agents
        # Make teaching agent request exercise
        teaching.handle_user_message.return_value = "Let's do an exercise."

        graph = create_teaching_graph(teaching, grading, content)
        state = create_new_session("test_user", "test_session")

        # User says they're ready
        result = run_conversation_turn(graph, state, user_input="I'm ready!")

        # Should have generated conversation
        assert isinstance(result, SystemState)
        assert len(result.conversation_history) > 0

    def test_grading_flow(self, mock_agents):
        """Test grading flow."""
        teaching, grading, content = mock_agents
        graph = create_teaching_graph(teaching, grading, content)
        state = create_new_session("test_user", "test_session")

        # Setup: exercise is pending
        exercise = Exercise(
            exercise_id="ex_1",
            exercise_type="translation",
            question="Test",
            answer="Test",
            difficulty="beginner",
        )
        state.set_pending_exercise(exercise)

        # User submits answer
        result = run_conversation_turn(graph, state, user_input="Test")

        # Verify the result is returned and has conversation history
        assert isinstance(result, SystemState)
        assert len(result.conversation_history) > 0
