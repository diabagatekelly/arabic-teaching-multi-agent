"""Tests for SystemState and related data structures."""

import pytest

from src.orchestrator.state import Exercise, SystemState


class TestSystemState:
    """Test SystemState management."""

    @pytest.fixture
    def state(self):
        """Create a fresh system state."""
        return SystemState(user_id="test_user", session_id="session_001")

    def test_state_initialization(self, state):
        """Test initial state values."""
        assert state.user_id == "test_user"
        assert state.session_id == "session_001"
        # Test business logic defaults
        assert state.next_agent == "agent1"
        assert state.current_mode == "vocabulary"

    def test_add_message(self, state):
        """Test adding messages to conversation history."""
        metadata = {"intent": "greeting"}
        state.add_message("user", "Hello", metadata=metadata)
        assert len(state.conversation_history) == 1
        assert state.conversation_history[0].role == "user"
        assert state.conversation_history[0].content == "Hello"
        assert state.conversation_history[0].metadata == metadata

    def test_set_pending_exercise(self, state):
        """Test setting a pending exercise."""
        exercise = Exercise(
            exercise_id="ex_1",
            exercise_type="translation",
            question="Test question",
            answer="Test answer",
            difficulty="beginner",
        )
        state.set_pending_exercise(exercise)
        assert state.pending_exercise == exercise
        assert state.awaiting_user_answer is True

    def test_clear_pending_exercise(self, state):
        """Test clearing pending exercise."""
        exercise = Exercise(
            exercise_id="ex_1",
            exercise_type="translation",
            question="Test",
            answer="Test",
            difficulty="beginner",
        )
        state.set_pending_exercise(exercise)
        state.clear_pending_exercise()
        assert state.pending_exercise is None
        assert state.awaiting_user_answer is False

    def test_add_learned_item(self, state):
        """Test adding learned vocabulary/grammar."""
        state.add_learned_item("كِتَاب (kitaab) - book")
        assert "كِتَاب (kitaab) - book" in state.learned_items
        assert len(state.learned_items) == 1

    def test_add_learned_item_no_duplicates(self, state):
        """Test that learned items don't duplicate."""
        item = "كِتَاب (kitaab) - book"
        state.add_learned_item(item)
        state.add_learned_item(item)
        assert state.learned_items.count(item) == 1

    def test_get_accuracy_zero_exercises(self, state):
        """Test accuracy calculation with no exercises."""
        assert state.get_accuracy() == 0.0

    def test_get_accuracy_all_correct(self, state):
        """Test accuracy calculation with exercises."""
        state.record_exercise_result(correct=True)
        state.record_exercise_result(correct=True)
        assert state.get_accuracy() == 100.0
        assert state.total_exercises_completed == 2
        assert state.total_correct_answers == 2

    def test_state_serialization(self, state):
        """Test converting state to dict."""
        state.add_learned_item("test_item")
        state.record_exercise_result(correct=True)

        data = state.to_dict()

        assert data["user_id"] == "test_user"
        assert data["session_id"] == "session_001"
        assert data["learned_items"] == ["test_item"]
        assert data["total_exercises_completed"] == 1
        assert data["total_correct_answers"] == 1
        assert "session_start_time" in data

    def test_state_deserialization(self, state):
        """Test creating state from dict with pending exercise."""
        state.add_learned_item("test_item")
        state.record_exercise_result(correct=True)
        exercise = Exercise(
            exercise_id="ex_1",
            exercise_type="translation",
            question="Test",
            answer="Test",
            difficulty="beginner",
        )
        state.set_pending_exercise(exercise)

        data = state.to_dict()
        restored_state = SystemState.from_dict(data)

        assert restored_state.user_id == state.user_id
        assert restored_state.session_id == state.session_id
        assert restored_state.learned_items == state.learned_items
        assert restored_state.total_exercises_completed == state.total_exercises_completed
        assert restored_state.total_correct_answers == state.total_correct_answers
        assert restored_state.pending_exercise is not None
        assert restored_state.pending_exercise.exercise_id == "ex_1"
        assert restored_state.awaiting_user_answer is True
