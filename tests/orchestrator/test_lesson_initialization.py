"""Tests for lesson initialization and caching strategy.

Tests that Agent 3 caches all content upfront and Agent 2 pre-loads grammar rules.
"""

from unittest.mock import Mock

import pytest

from src.orchestrator.graph import initialize_lesson_content
from src.orchestrator.nodes import ContentNode, GradingNode
from src.orchestrator.state import SystemState


class TestLessonInitialization:
    """Test lesson content caching and grammar rules pre-loading."""

    @pytest.fixture
    def mock_content_agent(self):
        """Create mock content agent."""
        agent = Mock()
        return agent

    @pytest.fixture
    def mock_grading_agent(self):
        """Create mock grading agent."""
        agent = Mock()
        return agent

    @pytest.fixture
    def content_node(self, mock_content_agent):
        """Create ContentNode."""
        return ContentNode(mock_content_agent)

    @pytest.fixture
    def grading_node(self, mock_grading_agent):
        """Create GradingNode."""
        return GradingNode(mock_grading_agent)

    @pytest.fixture
    def state(self):
        """Create fresh state."""
        return SystemState(user_id="test", session_id="test", current_lesson=1)

    def test_lesson_initialization(self, state, content_node, grading_node):
        """Test complete lesson initialization."""
        # Initially not initialized
        assert not state.lesson_initialized
        assert len(state.cached_vocab_words) == 0
        assert len(state.cached_grammar_content) == 0
        assert len(state.preloaded_grammar_rules) == 0

        # Initialize lesson
        result = initialize_lesson_content(state, content_node, grading_node)

        # Content should be cached
        assert result.lesson_initialized
        assert len(result.cached_vocab_words) > 0
        assert len(result.cached_grammar_content) > 0

        # Grammar rules should be pre-loaded
        assert len(result.preloaded_grammar_rules) > 0

    def test_content_caching(self, state, content_node):
        """Test that ContentNode caches vocabulary and grammar."""
        # Initialize lesson via content node
        content_node.initialize_lesson(state)

        # Should have cached vocabulary
        assert state.lesson_initialized
        assert len(state.cached_vocab_words) > 0

        # Verify vocabulary structure
        for word in state.cached_vocab_words:
            assert "arabic" in word
            assert "transliteration" in word
            assert "english" in word
            assert "word_id" in word

        # Should have cached grammar
        assert len(state.cached_grammar_content) > 0

        # Verify grammar structure
        for _topic, content in state.cached_grammar_content.items():
            assert "rule" in content
            assert "examples" in content

    def test_grammar_rules_preloading(self, state, content_node, grading_node):
        """Test that GradingNode pre-loads grammar rules."""
        # First cache content
        content_node.initialize_lesson(state)

        # Then pre-load rules
        grading_node.preload_grammar_rules(state)

        # Should have pre-loaded rules
        assert len(state.preloaded_grammar_rules) > 0

        # Verify rules structure
        for _topic, rules in state.preloaded_grammar_rules.items():
            assert "rule" in rules
            assert "examples" in rules
            assert "detection_pattern" in rules

    def test_preloading_without_cached_content(self, state, grading_node):
        """Test pre-loading handles missing cached content gracefully."""
        # No cached content
        assert len(state.cached_grammar_content) == 0

        # Should not crash
        grading_node.preload_grammar_rules(state)

        # Should have no rules (but not error)
        assert len(state.preloaded_grammar_rules) == 0

    def test_content_node_initializes_on_first_call(self, state, content_node, mock_content_agent):
        """Test that ContentNode automatically initializes lesson on first call."""
        # Setup mock to return exercise
        mock_content_agent.generate_exercise.return_value = (
            '{"question": "Q", "answer": "A", "type": "t"}'
        )

        # Initially not initialized
        assert not state.lesson_initialized

        # Call content node (should trigger initialization)
        result = content_node(state)

        # Should have initialized
        assert result.lesson_initialized
        assert len(result.cached_vocab_words) > 0

    def test_content_node_skips_reinitialization(self, state, content_node, mock_content_agent):
        """Test that ContentNode doesn't re-initialize if already done."""
        # Setup mock
        mock_content_agent.generate_exercise.return_value = (
            '{"question": "Q", "answer": "A", "type": "t"}'
        )

        # Pre-initialize
        content_node.initialize_lesson(state)
        initial_vocab_count = len(state.cached_vocab_words)

        # Mark as initialized
        state.lesson_initialized = True

        # Call again
        result = content_node(state)

        # Should not have re-initialized (same cached content)
        assert result.lesson_initialized
        assert len(result.cached_vocab_words) == initial_vocab_count


class TestContentCachingStrategy:
    """Test that cached content is used instead of repeated RAG queries."""

    @pytest.fixture
    def mock_content_agent(self):
        """Create mock content agent with RAG retriever."""
        agent = Mock()
        agent.generate_exercise.return_value = '{"question": "Q", "answer": "A", "type": "t"}'
        return agent

    @pytest.fixture
    def content_node(self, mock_content_agent):
        """Create ContentNode."""
        return ContentNode(mock_content_agent)

    @pytest.fixture
    def state(self):
        """Create state with cached content."""
        state = SystemState(user_id="test", session_id="test", current_lesson=1)
        # Pre-populate cached content (simulating successful initialization)
        state.cached_vocab_words = [
            {"arabic": "كِتَاب", "transliteration": "kitaab", "english": "book", "word_id": "w1"},
            {"arabic": "قَلَم", "transliteration": "qalam", "english": "pen", "word_id": "w2"},
        ]
        state.cached_grammar_content = {
            "gender": {"rule": "Nouns are gendered", "examples": ["كِتَاب (m)"]}
        }
        state.lesson_initialized = True
        return state

    def test_uses_cached_vocabulary(self, state, content_node):
        """Test that exercises use cached vocabulary instead of querying RAG."""
        # Store reference to initial cached content
        initial_vocab_data = state.cached_vocab_words.copy()

        # Generate multiple exercises
        for _ in range(3):
            state = content_node(state)

        # Should still have same cached content (not re-queried)
        # Verify cache wasn't replaced with new data
        assert state.cached_vocab_words == initial_vocab_data
        assert len(state.cached_vocab_words) == 2
        assert state.cached_vocab_words[0]["english"] == "book"


class TestStateSerializationWithCache:
    """Test that cached content persists across state serialization."""

    def test_cached_content_in_to_dict(self):
        """Test that to_dict includes cached content."""
        state = SystemState(user_id="test", session_id="test")
        state.cached_vocab_words = [{"arabic": "كِتَاب", "english": "book"}]
        state.cached_grammar_content = {"gender": {"rule": "test"}}
        state.preloaded_grammar_rules = {"gender": {"rule": "test"}}
        state.lesson_initialized = True

        # Serialize
        state_dict = state.to_dict()

        # Should include caching fields
        assert "cached_vocab_words" in state_dict
        assert "cached_grammar_content" in state_dict
        assert "preloaded_grammar_rules" in state_dict
        assert "lesson_initialized" in state_dict
        assert state_dict["lesson_initialized"] is True

    def test_cached_content_from_dict(self):
        """Test that from_dict restores cached content."""
        data = {
            "user_id": "test",
            "session_id": "test",
            "cached_vocab_words": [{"arabic": "كِتَاب", "english": "book"}],
            "cached_grammar_content": {"gender": {"rule": "test"}},
            "preloaded_grammar_rules": {"gender": {"rule": "test"}},
            "lesson_initialized": True,
        }

        # Deserialize
        state = SystemState.from_dict(data)

        # Should have restored caching fields
        assert len(state.cached_vocab_words) == 1
        assert state.cached_vocab_words[0]["english"] == "book"
        assert "gender" in state.cached_grammar_content
        assert "gender" in state.preloaded_grammar_rules
        assert state.lesson_initialized is True

    def test_learned_items_set_rebuilt_after_deserialization(self):
        """Test that _learned_items_set is correctly rebuilt from learned_items after from_dict."""
        # Create state with learned items (including duplicates to test deduplication)
        data = {
            "user_id": "test",
            "session_id": "test",
            "learned_items": ["كِتَاب", "مَدْرَسَة", "قَلَم", "كِتَاب"],  # duplicate
        }

        # Deserialize
        state = SystemState.from_dict(data)

        # Set should be rebuilt (duplicates removed in set)
        assert len(state._learned_items_set) == 3
        assert "كِتَاب" in state._learned_items_set
        assert "مَدْرَسَة" in state._learned_items_set
        assert "قَلَم" in state._learned_items_set

        # Add existing item - should not duplicate
        initial_length = len(state.learned_items)
        state.add_learned_item("كِتَاب")
        assert len(state.learned_items) == initial_length  # No new item added

        # Add new item - should be added
        state.add_learned_item("بَيْت")
        assert len(state.learned_items) == initial_length + 1
        assert "بَيْت" in state.learned_items
        assert "بَيْت" in state._learned_items_set

    def test_learned_items_helpers_keep_set_in_sync(self):
        """Test that add_learned_item, remove_learned_item, clear_learned_items keep set in sync."""
        state = SystemState(user_id="test", session_id="test")

        # Add items
        state.add_learned_item("word1")
        state.add_learned_item("word2")
        state.add_learned_item("word1")  # duplicate

        assert len(state.learned_items) == 2
        assert len(state._learned_items_set) == 2
        assert "word1" in state.learned_items
        assert "word2" in state.learned_items

        # Remove item
        state.remove_learned_item("word1")
        assert len(state.learned_items) == 1
        assert len(state._learned_items_set) == 1
        assert "word1" not in state.learned_items
        assert "word1" not in state._learned_items_set

        # Remove non-existent item (should be safe)
        state.remove_learned_item("nonexistent")
        assert len(state.learned_items) == 1

        # Clear all
        state.clear_learned_items()
        assert len(state.learned_items) == 0
        assert len(state._learned_items_set) == 0
