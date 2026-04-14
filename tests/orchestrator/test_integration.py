"""Integration tests for multi-agent orchestration.

Tests multi-turn workflows and agent interactions that go beyond single-turn tests.
For single-turn smoke tests, see test_graph.py.

Focus:
- Multi-turn conversation flows (lesson cycle, multiple exercises)
- State persistence across multiple turns
- Error handling and recovery across agent transitions
"""

from unittest.mock import Mock

import pytest

from src.orchestrator.graph import create_teaching_graph, run_conversation_turn
from src.orchestrator.state import Exercise, SystemState


class TestMultiTurnWorkflows:
    """Test multi-turn teaching workflows (unique to integration tests)."""

    @pytest.fixture
    def mock_agents(self):
        """Create mock agents for testing orchestrator behavior."""
        teaching_agent = Mock()
        grading_agent = Mock()
        content_agent = Mock()

        # Configure teaching agent responses
        teaching_agent.start_lesson.return_value = (
            "Welcome to Lesson 1! Let's learn about gender and definite articles."
        )
        teaching_agent.handle_user_message.return_value = (
            "Great! I'll generate an exercise for you."
        )
        teaching_agent.provide_feedback.return_value = "Excellent work! You got it right."

        # Configure content agent responses
        content_agent.generate_exercise.return_value = (
            '```json\n{"question": "Translate: book", "answer": "كِتَاب", "type": "translation"}\n```'
        )

        # Configure grading agent responses
        grading_agent.grade_answer.return_value = "Correct! ✓"

        return {
            "teaching": teaching_agent,
            "grading": grading_agent,
            "content": content_agent,
        }

    @pytest.fixture
    def graph(self, mock_agents):
        """Create teaching graph with mock agents."""
        return create_teaching_graph(
            teaching_agent=mock_agents["teaching"],
            grading_agent=mock_agents["grading"],
            content_agent=mock_agents["content"],
        )

    @pytest.fixture
    def initial_state(self):
        """Create fresh state for testing."""
        return SystemState(user_id="test_user", session_id="test_session")

    def test_grading_to_feedback_handoff(self, graph, initial_state, mock_agents):
        """Test automatic grading → teaching handoff for feedback (unique to integration)."""
        # Setup: state after grading
        initial_state.add_message(
            "agent2",
            "Correct! ✓",
            metadata={
                "user_answer": "كِتَاب",
                "correct_answer": "كِتَاب",
                "is_correct": True,
            },
        )
        initial_state.last_agent = "agent2"
        initial_state.next_agent = "agent1"
        initial_state.record_exercise_result(True)

        # Run next turn - should invoke teaching agent for feedback
        state = run_conversation_turn(graph, initial_state)

        # Verify teaching agent was called for feedback
        mock_agents["teaching"].provide_feedback.assert_called_once()
        call_args = mock_agents["teaching"].provide_feedback.call_args[0][0]
        assert call_args["is_correct"] is True
        assert call_args["user_answer"] == "كِتَاب"
        assert call_args["correct_answer"] == "كِتَاب"

        # Verify state
        assert state.last_agent == "agent1"
        assert len(state.conversation_history) == 2  # grading + feedback

    def test_complete_lesson_cycle(self, graph, initial_state, mock_agents):
        """Test complete multi-turn cycle: teach → exercise → answer → grade → feedback."""
        # 1. Start lesson
        state = run_conversation_turn(graph, initial_state)
        assert state.last_agent == "agent1"
        assert len(state.conversation_history) == 1

        # 2. User says ready - teaching response triggers exercise generation
        state = run_conversation_turn(graph, state, user_input="I'm ready to learn!")
        # Note: TeachingNode response contains "exercise" which auto-triggers content generation
        assert len(state.conversation_history) == 4  # agent1, user, agent1, agent3
        assert state.pending_exercise is not None
        assert state.awaiting_user_answer is True
        assert state.last_agent == "agent3"

        # 3. User submits answer (grading + feedback happen in one turn)
        state = run_conversation_turn(graph, state, user_input="كِتَاب")
        # Note: grading → teaching is automatic edge, so both execute in one turn
        assert state.last_agent == "agent1"  # Teaching is last (provides feedback)
        assert state.pending_exercise is None
        assert state.total_exercises_completed == 1
        # Should have: agent1, user, agent1, agent3, user, agent2, agent1
        assert len(state.conversation_history) == 7  # +user +agent2 +agent1

        # Verify feedback was provided
        mock_agents["teaching"].provide_feedback.assert_called_once()

    def test_incorrect_answer_workflow(self, graph, initial_state, mock_agents):
        """Test multi-turn workflow with incorrect answer (unique path)."""
        # Configure grading to return incorrect
        mock_agents["grading"].grade_answer.return_value = "Incorrect. The correct answer is كِتَاب."

        # Setup: state with pending exercise
        exercise = Exercise(
            exercise_id="ex_1",
            exercise_type="translation",
            question="Translate: book",
            answer="كِتَاب",
            difficulty="beginner",
        )
        initial_state.set_pending_exercise(exercise)
        initial_state.add_message("agent3", "Exercise generated")
        initial_state.last_agent = "agent3"

        # User submits incorrect answer
        state = run_conversation_turn(graph, initial_state, user_input="مَدْرَسَة")

        # Verify grading marked as incorrect
        grading_msg = next(msg for msg in state.conversation_history if msg.role == "agent2")
        assert grading_msg.metadata.get("is_correct") is False
        assert state.total_exercises_completed == 1
        assert state.total_correct_answers == 0

        # Feedback should include is_correct=False
        state = run_conversation_turn(graph, state)
        feedback_call = mock_agents["teaching"].provide_feedback.call_args[0][0]
        assert feedback_call["is_correct"] is False


class TestStateTransitions:
    """Test state management across agent transitions."""

    @pytest.fixture
    def mock_agents(self):
        """Minimal mock agents."""
        teaching = Mock()
        grading = Mock()
        content = Mock()

        teaching.start_lesson.return_value = "Lesson started"
        teaching.handle_user_message.return_value = "Handling message"
        teaching.provide_feedback.return_value = "Feedback"
        grading.grade_answer.return_value = "Correct"
        content.generate_exercise.return_value = '{"question": "Q", "answer": "A", "type": "t"}'

        return {"teaching": teaching, "grading": grading, "content": content}

    @pytest.fixture
    def graph(self, mock_agents):
        """Create graph with mock agents."""
        return create_teaching_graph(
            teaching_agent=mock_agents["teaching"],
            grading_agent=mock_agents["grading"],
            content_agent=mock_agents["content"],
        )

    def test_conversation_history_accumulates(self, graph):
        """Test that conversation history accumulates correctly."""
        state = SystemState(user_id="test", session_id="test")

        # Turn 1: lesson start
        state = run_conversation_turn(graph, state)
        assert len(state.conversation_history) == 1
        assert state.conversation_history[0].role == "agent1"

        # Turn 2: user message
        state = run_conversation_turn(graph, state, user_input="Hello")
        assert len(state.conversation_history) == 3  # agent1, user, agent1

        # Turn 3: generate exercise
        state.next_agent = "agent3"
        state = run_conversation_turn(graph, state)
        assert len(state.conversation_history) == 4  # +agent3

        # Verify all roles present
        roles = [msg.role for msg in state.conversation_history]
        assert roles == ["agent1", "user", "agent1", "agent3"]

    def test_pending_exercise_lifecycle(self, graph):
        """Test pending exercise set → cleared lifecycle."""
        state = SystemState(user_id="test", session_id="test")

        # Initially no pending exercise
        assert state.pending_exercise is None
        assert state.awaiting_user_answer is False

        # Generate exercise
        state.next_agent = "agent3"
        state = run_conversation_turn(graph, state)

        # Should have pending exercise
        assert state.pending_exercise is not None
        assert state.awaiting_user_answer is True

        # Submit answer (grading clears exercise)
        state = run_conversation_turn(graph, state, user_input="answer")

        # Should be cleared
        assert state.pending_exercise is None
        assert state.awaiting_user_answer is False

    def test_exercise_result_tracking(self, graph, mock_agents):
        """Test exercise result tracking across multiple exercises."""
        state = SystemState(user_id="test", session_id="test")

        # Exercise 1: correct
        state.next_agent = "agent3"
        state = run_conversation_turn(graph, state)
        mock_agents["grading"].grade_answer.return_value = "Correct"
        state = run_conversation_turn(graph, state, user_input="answer1")

        assert state.total_exercises_completed == 1
        assert state.total_correct_answers == 1
        assert state.get_accuracy() == 100.0

        # Exercise 2: incorrect
        state.next_agent = "agent3"
        state = run_conversation_turn(graph, state)
        mock_agents["grading"].grade_answer.return_value = "Incorrect"
        state = run_conversation_turn(graph, state, user_input="answer2")

        assert state.total_exercises_completed == 2
        assert state.total_correct_answers == 1
        assert state.get_accuracy() == 50.0

    def test_last_agent_tracking(self, graph):
        """Test last_agent tracking across transitions."""
        state = SystemState(user_id="test", session_id="test")

        # Start: agent1
        state = run_conversation_turn(graph, state)
        assert state.last_agent == "agent1"

        # User message: agent1
        state = run_conversation_turn(graph, state, user_input="msg")
        assert state.last_agent == "agent1"

        # Generate exercise: agent3
        state.next_agent = "agent3"
        state = run_conversation_turn(graph, state)
        assert state.last_agent == "agent3"

        # Submit answer: grading → teaching (automatic edge)
        state = run_conversation_turn(graph, state, user_input="answer")
        assert state.last_agent == "agent1"  # Teaching provides feedback after grading


class TestErrorHandling:
    """Test error handling and recovery in orchestrator."""

    @pytest.fixture
    def mock_agents(self):
        """Create agents that can be configured to fail."""
        teaching = Mock()
        grading = Mock()
        content = Mock()

        # Default success responses
        teaching.start_lesson.return_value = "Started"
        teaching.handle_user_message.return_value = "Handled"
        teaching.provide_feedback.return_value = "Feedback"
        grading.grade_answer.return_value = "Graded"
        content.generate_exercise.return_value = '{"question":"Q","answer":"A","type":"t"}'

        return {"teaching": teaching, "grading": grading, "content": content}

    @pytest.fixture
    def graph(self, mock_agents):
        """Create graph with mock agents."""
        return create_teaching_graph(
            teaching_agent=mock_agents["teaching"],
            grading_agent=mock_agents["grading"],
            content_agent=mock_agents["content"],
        )

    def test_teaching_agent_error_recovery(self, graph, mock_agents):
        """Test recovery when teaching agent throws error."""
        state = SystemState(user_id="test", session_id="test")

        # Configure teaching agent to fail
        mock_agents["teaching"].start_lesson.side_effect = Exception("Model error")

        # Should not crash
        state = run_conversation_turn(graph, state)

        # Should add error message to history
        assert any(msg.role == "system" for msg in state.conversation_history)
        error_msg = next(msg for msg in state.conversation_history if msg.role == "system")
        assert "error" in error_msg.content.lower()

        # Should fallback to user
        assert state.next_agent == "user"

    def test_grading_agent_error_recovery(self, graph, mock_agents):
        """Test recovery when grading agent throws error."""
        state = SystemState(user_id="test", session_id="test")

        # Setup: pending exercise
        exercise = Exercise(
            exercise_id="ex_1",
            exercise_type="translation",
            question="Q",
            answer="A",
            difficulty="beginner",
        )
        state.set_pending_exercise(exercise)
        state.add_message("agent3", "Exercise")
        state.last_agent = "agent3"

        # Configure grading to fail
        mock_agents["grading"].grade_answer.side_effect = Exception("Grading error")

        # Submit answer
        state = run_conversation_turn(graph, state, user_input="answer")

        # Should add error message
        assert any(msg.role == "system" for msg in state.conversation_history)

        # Should fallback to user (error recovery pattern)
        assert state.next_agent == "user"

    def test_content_agent_error_recovery(self, graph, mock_agents):
        """Test recovery when content agent throws error."""
        state = SystemState(user_id="test", session_id="test")
        state.next_agent = "agent3"

        # Configure content agent to fail
        mock_agents["content"].generate_exercise.side_effect = Exception("Generation error")

        # Generate exercise
        state = run_conversation_turn(graph, state)

        # Should add error message
        assert any(msg.role == "system" for msg in state.conversation_history)

        # Should fallback to user (error recovery pattern)
        assert state.next_agent == "user"

        # Should not have pending exercise
        assert state.pending_exercise is None

    def test_grading_without_pending_exercise(self, graph):
        """Test grading node handles missing pending exercise gracefully."""
        state = SystemState(user_id="test", session_id="test")
        state.add_message("user", "Some answer")
        state.next_agent = "agent2"

        # Should not crash
        state = run_conversation_turn(graph, state)

        # GradingNode detects missing exercise and routes to teaching
        # Teaching then executes and sets next_agent to "user"
        assert state.next_agent == "user"

        # Verify no grading happened (no exercise results recorded)
        assert state.total_exercises_completed == 0
