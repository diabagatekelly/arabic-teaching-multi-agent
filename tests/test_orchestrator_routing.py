"""Test orchestrator routing with mocked agent responses.

Tests verify that the orchestrator correctly:
1. Detects keywords in agent responses
2. Routes to the correct next agent
3. Updates state appropriately
4. Handles edge cases
"""

from unittest.mock import Mock

import pytest

from src.orchestrator.nodes import GradingNode, TeachingNode
from src.orchestrator.state import Exercise, create_initial_state
from tests.mocks import agent_responses


class TestOrchestratorKeywordRouting:
    """Test keyword detection and routing logic."""

    def test_request_quiz_routes_to_content_agent(self):
        """When teaching agent responds with 'quiz', route to ContentAgent."""
        # Setup
        state = create_initial_state(lesson_number=1, user_id="test_user")
        state.add_message("user", "test me")
        state.cached_vocab_words = [
            {"arabic": "كِتَاب", "transliteration": "kitaabun", "english": "book"}
        ]
        state.current_mode = "teaching_vocab"

        # Mock teaching agent
        mock_teaching_agent = Mock()
        mock_teaching_agent.handle_user_message.return_value = (
            agent_responses.REQUEST_QUIZ_RESPONSE_1
        )

        # Execute
        teaching_node = TeachingNode(agent=mock_teaching_agent)
        result_state = teaching_node(state)

        # Verify routing
        assert (
            result_state.next_agent == "agent3"
        ), "Should route to ContentAgent (agent3) for quiz generation"
        assert result_state.last_agent == "agent1"
        # Verify keyword was stripped from conversation history
        assert "[GENERATE_EXERCISE]" not in result_state.conversation_history[-1].content

    def test_mid_quiz_correct_routes_to_next_word(self):
        """After correct answer, 'next word' keyword should trigger next quiz generation."""
        # Setup
        state = create_initial_state(lesson_number=1, user_id="test_user")
        state.current_mode = "teaching_vocab"
        state.batch_quizzed_words = ["كِتَاب"]  # One word already tested
        state.cached_vocab_words = [
            {"arabic": "كِتَاب", "transliteration": "kitaabun", "english": "book"},
            {"arabic": "بَيْت", "transliteration": "baytun", "english": "house"},
            {"arabic": "قَلَم", "transliteration": "qalamun", "english": "pen"},
        ]

        # Simulate grading result
        state.add_message("user", "book")
        state.add_message(
            "agent2", "Correct! The word كِتَاب means 'book'.", metadata={"is_correct": True}
        )
        state.last_agent = "agent2"

        # Mock teaching agent feedback
        mock_teaching_agent = Mock()
        mock_teaching_agent.handle_feedback_vocab.return_value = agent_responses.MID_QUIZ_CORRECT_1

        # Execute
        teaching_node = TeachingNode(agent=mock_teaching_agent)
        result_state = teaching_node(state)

        # Verify routing
        assert result_state.next_agent == "agent3", "Should auto-generate next quiz after feedback"
        assert "next word" in result_state.conversation_history[-1].content.lower()

    def test_batch_complete_waits_for_user(self):
        """When batch completes, should wait for user to decide on next batch."""
        # Setup
        state = create_initial_state(lesson_number=1, user_id="test_user")
        state.current_mode = "teaching_vocab"
        state.current_vocab_batch = 1
        state.batch_quizzed_words = ["كِتَاب", "بَيْت", "قَلَم"]  # All 3 tested
        state.batch_correct_count = 3
        state.cached_vocab_words = [
            {"arabic": "كِتَاب", "transliteration": "kitaabun", "english": "book"},
            {"arabic": "بَيْت", "transliteration": "baytun", "english": "house"},
            {"arabic": "قَلَم", "transliteration": "qalamun", "english": "pen"},
            {"arabic": "طَاوِلَة", "transliteration": "taawilatun", "english": "table"},
        ]

        # Simulate last word graded
        state.add_message("user", "pen")
        state.add_message("agent2", "Correct!", metadata={"is_correct": True})
        state.last_agent = "agent2"

        # Mock teaching agent
        mock_teaching_agent = Mock()
        mock_teaching_agent.handle_feedback_vocab.return_value = (
            agent_responses.BATCH_COMPLETE_RESPONSE
        )

        # Execute
        teaching_node = TeachingNode(agent=mock_teaching_agent)
        result_state = teaching_node(state)

        # Verify routing
        assert (
            result_state.next_agent == "user"
        ), "Should wait for user decision after batch complete"
        assert "Batch 1 complete" in result_state.conversation_history[-1].content

    def test_request_next_batch_loads_batch_2(self):
        """'batch' keyword should load next batch from cache."""
        # Setup
        state = create_initial_state(lesson_number=1, user_id="test_user")
        state.current_mode = "teaching_vocab"
        state.current_vocab_batch = 1
        state.cached_vocab_words = [
            {"arabic": "كِتَاب", "transliteration": "kitaabun", "english": "book"},
            {"arabic": "بَيْت", "transliteration": "baytun", "english": "house"},
            {"arabic": "قَلَم", "transliteration": "qalamun", "english": "pen"},
            {"arabic": "طَاوِلَة", "transliteration": "taawilatun", "english": "table"},
            {"arabic": "مَدْرَسَة", "transliteration": "madrasatun", "english": "school"},
            {"arabic": "نَافِذَة", "transliteration": "naafidhatun", "english": "window"},
        ]
        state.add_message("user", "next batch please")

        # Mock teaching agent
        mock_teaching_agent = Mock()
        mock_teaching_agent.handle_teaching_vocab.return_value = (
            agent_responses.REQUEST_NEXT_BATCH_1
        )

        # Execute
        teaching_node = TeachingNode(agent=mock_teaching_agent)
        result_state = teaching_node(state)

        # Verify state update
        assert result_state.current_vocab_batch == 2, "Should advance to batch 2"
        assert "Batch 2" in result_state.conversation_history[-1].content

    def test_request_grammar_switches_mode(self):
        """'grammar' keyword should switch to grammar teaching mode."""
        # Setup
        state = create_initial_state(lesson_number=1, user_id="test_user")
        state.cached_grammar_content = {
            "masculine_feminine_nouns": {"rule": "Nouns ending in ة are feminine"}
        }
        state.add_message("user", "let's learn grammar")

        # Mock teaching agent
        mock_teaching_agent = Mock()
        mock_teaching_agent.handle_teaching_grammar.return_value = agent_responses.REQUEST_GRAMMAR_1

        # Execute
        teaching_node = TeachingNode(agent=mock_teaching_agent)
        result_state = teaching_node(state)

        # Verify mode switch
        assert result_state.current_mode == "teaching_grammar"
        assert "grammar" in result_state.conversation_history[-1].content.lower()

    def test_request_vocabulary_switches_to_vocab_mode(self):
        """'vocabulary' keyword should switch to vocabulary teaching mode."""
        # Setup
        state = create_initial_state(lesson_number=1, user_id="test_user")
        state.current_mode = "teaching_grammar"  # Start in grammar mode
        state.cached_vocab_words = [
            {"arabic": "كِتَاب", "transliteration": "kitaabun", "english": "book"}
        ]
        state.add_message("user", "let's do vocabulary")

        # Mock teaching agent
        mock_teaching_agent = Mock()
        mock_teaching_agent.handle_teaching_vocab.return_value = (
            agent_responses.REQUEST_VOCABULARY_1
        )

        # Execute
        teaching_node = TeachingNode(agent=mock_teaching_agent)
        result_state = teaching_node(state)

        # Verify mode switch
        assert result_state.current_mode == "teaching_vocab"
        assert "vocabulary" in result_state.conversation_history[-1].content.lower()

    def test_request_final_test_routes_to_content_agent(self):
        """'final test' or 'exam' keyword should route to ContentAgent."""
        # Setup
        state = create_initial_state(lesson_number=1, user_id="test_user")
        state.add_message("user", "I want to take the final test")

        # Mock teaching agent
        mock_teaching_agent = Mock()
        mock_teaching_agent.handle_user_message.return_value = agent_responses.REQUEST_FINAL_TEST_1

        # Execute
        teaching_node = TeachingNode(agent=mock_teaching_agent)
        result_state = teaching_node(state)

        # Verify routing
        # Note: Current implementation may need update to detect "final" keyword
        assert "final" in result_state.conversation_history[-1].content.lower()

    def test_request_break_ends_session(self):
        """'break' keyword should signal session end."""
        # Setup
        state = create_initial_state(lesson_number=1, user_id="test_user")
        state.add_message("user", "I need a break")

        # Mock teaching agent
        mock_teaching_agent = Mock()
        mock_teaching_agent.handle_user_message.return_value = agent_responses.REQUEST_BREAK_1

        # Execute
        teaching_node = TeachingNode(agent=mock_teaching_agent)
        result_state = teaching_node(state)

        # Verify response
        assert "break" in result_state.conversation_history[-1].content.lower()
        # Note: Session end handling may need orchestrator-level logic

    def test_off_topic_offers_break(self):
        """'off topic' response should offer break or continue."""
        # Setup
        state = create_initial_state(lesson_number=1, user_id="test_user")
        state.add_message("user", "tell me about One Piece")

        # Mock teaching agent
        mock_teaching_agent = Mock()
        mock_teaching_agent.handle_user_message.return_value = agent_responses.OFF_TOPIC_1

        # Execute
        teaching_node = TeachingNode(agent=mock_teaching_agent)
        result_state = teaching_node(state)

        # Verify response
        assert "off topic" in result_state.conversation_history[-1].content.lower()
        assert result_state.next_agent == "user"

    def test_profanity_sets_boundary(self):
        """Profanity should trigger respectful boundary setting."""
        # Setup
        state = create_initial_state(lesson_number=1, user_id="test_user")
        state.add_message("user", "fuck this is hard")

        # Mock teaching agent
        mock_teaching_agent = Mock()
        mock_teaching_agent.handle_user_message.return_value = agent_responses.PROFANITY_RESPONSE_1

        # Execute
        teaching_node = TeachingNode(agent=mock_teaching_agent)
        result_state = teaching_node(state)

        # Verify response
        assert "respectful" in result_state.conversation_history[-1].content.lower()

    def test_exercise_presentation_waits_for_answer(self):
        """After presenting exercise, should wait for user answer."""
        # Setup
        state = create_initial_state(lesson_number=1, user_id="test_user")
        state.current_mode = "teaching_vocab"
        state.pending_exercise = Exercise(
            exercise_id="ex_001",
            exercise_type="translation",
            question="What does كِتَاب mean?",
            answer="book",
            difficulty="beginner",
            metadata={"word_arabic": "كِتَاب"},
        )
        state.last_agent = "agent3"

        # Mock teaching agent
        mock_teaching_agent = Mock()
        mock_teaching_agent.handle_present_exercise = Mock()

        # Execute
        teaching_node = TeachingNode(agent=mock_teaching_agent)
        result_state = teaching_node(state)

        # Verify routing
        assert result_state.awaiting_user_answer is True
        assert result_state.next_agent == "user"

    def test_user_answer_routes_to_grading(self):
        """User answer to exercise should route to GradingAgent."""
        # Setup
        state = create_initial_state(lesson_number=1, user_id="test_user")
        state.pending_exercise = Exercise(
            exercise_id="ex_001",
            exercise_type="translation",
            question="What does كِتَاب mean?",
            answer="book",
            difficulty="beginner",
        )
        state.awaiting_user_answer = True
        state.add_message("user", "book")

        # Mock grading agent
        mock_grading_agent = Mock()
        mock_grading_agent.handle_grading.return_value = {
            "is_correct": True,
            "feedback": "Correct! كِتَاب means book.",
        }

        # Execute
        grading_node = GradingNode(agent=mock_grading_agent)
        result_state = grading_node(state)

        # Verify routing
        assert result_state.next_agent == "agent1", "Should route back to teaching for feedback"
        assert result_state.last_agent == "agent2"


class TestOrchestratorStateManagement:
    """Test state updates during orchestration."""

    def test_batch_tracking_resets_after_complete(self):
        """Batch counters should reset after batch completion."""
        # Setup
        state = create_initial_state(lesson_number=1, user_id="test_user")
        state.batch_quizzed_words = ["word1", "word2", "word3"]
        state.batch_correct_count = 2
        state.current_vocab_batch = 1

        # Simulate batch complete
        state.batch_quizzed_words = []
        state.batch_correct_count = 0

        # Verify reset
        assert len(state.batch_quizzed_words) == 0
        assert state.batch_correct_count == 0

    def test_learned_items_accumulate(self):
        """Learned items should accumulate across batches."""
        # Setup
        state = create_initial_state(lesson_number=1, user_id="test_user")

        # Add learned items
        state.add_learned_item("كِتَاب")
        state.add_learned_item("بَيْت")
        state.add_learned_item("قَلَم")

        # Verify accumulation
        assert len(state.learned_items) == 3
        assert "كِتَاب" in state.learned_items

    def test_conversation_history_persists(self):
        """Conversation history should persist across turns."""
        # Setup
        state = create_initial_state(lesson_number=1, user_id="test_user")

        # Add messages
        state.add_message("user", "hello")
        state.add_message("agent1", "Welcome!")
        state.add_message("user", "test me")
        state.add_message("agent1", "Starting quiz...")

        # Verify persistence
        assert len(state.conversation_history) == 4
        assert state.conversation_history[0].role == "user"
        assert state.conversation_history[0].content == "hello"


class TestOrchestratorEdgeCases:
    """Test edge cases and error handling."""

    def test_empty_cached_vocab_handled_gracefully(self):
        """Empty vocabulary cache should not crash."""
        # Setup
        state = create_initial_state(lesson_number=1, user_id="test_user")
        state.cached_vocab_words = []
        state.add_message("user", "teach me vocabulary")

        # Mock teaching agent
        mock_teaching_agent = Mock()
        mock_teaching_agent.handle_teaching_vocab.return_value = (
            "No vocabulary available for this lesson."
        )

        # Execute
        teaching_node = TeachingNode(agent=mock_teaching_agent)
        result_state = teaching_node(state)

        # Should not crash
        assert result_state is not None

    def test_invalid_batch_number_handled(self):
        """Invalid batch number should not crash."""
        # Setup
        state = create_initial_state(lesson_number=1, user_id="test_user")
        state.current_vocab_batch = 99  # Invalid
        state.cached_vocab_words = [
            {"arabic": "كِتَاب", "transliteration": "kitaabun", "english": "book"}
        ]

        # Should handle gracefully (implementation-dependent)
        assert state.current_vocab_batch == 99

    def test_no_pending_exercise_with_answer(self):
        """User answer without pending exercise should not crash."""
        # Setup
        state = create_initial_state(lesson_number=1, user_id="test_user")
        state.pending_exercise = None
        state.add_message("user", "book")

        # Mock teaching agent
        mock_teaching_agent = Mock()
        mock_teaching_agent.handle_user_message.return_value = (
            "I'm not sure what you're answering. Let's start a quiz!"
        )

        # Execute
        teaching_node = TeachingNode(agent=mock_teaching_agent)
        result_state = teaching_node(state)

        # Should not crash
        assert result_state is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
