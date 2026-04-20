"""Tests for orchestrator vocabulary flow."""

from unittest.mock import MagicMock

import pytest


@pytest.fixture
def mock_lesson_cache():
    """Mock lesson cache with sample data."""
    return {
        1: {
            "lesson_number": 1,
            "lesson_name": "Gender and Definite Article",
            "vocabulary": [
                {"arabic": "كِتَابٌ", "transliteration": "kitaabun", "english": "book"},
                {"arabic": "طَاوِلَةٌ", "transliteration": "taawilatun", "english": "table"},
                {"arabic": "قَلَمٌ", "transliteration": "qalamun", "english": "pen"},
                {"arabic": "بَيْتٌ", "transliteration": "baytun", "english": "house"},
                {"arabic": "نَافِذَةٌ", "transliteration": "naafidhah", "english": "window"},
                {"arabic": "بَابٌ", "transliteration": "baabun", "english": "door"},
            ],
            "grammar_points": ["masculine_feminine_nouns"],
            "grammar_sections": {"rule": "In Arabic, all nouns have gender..."},
            "difficulty": "beginner",
        }
    }


@pytest.fixture
def mock_sessions():
    """Mock sessions dictionary."""
    return {}


@pytest.fixture
def mock_teaching_model():
    """Mock teaching model."""

    class MockModel:
        def generate(self, **kwargs):
            return [[1, 2, 3, 4, 5]]

        @property
        def device(self):
            return "cpu"

    return MockModel()


@pytest.fixture
def mock_tokenizer():
    """Mock tokenizer."""

    class MockTensor:
        shape = (1, 3)

        def __iter__(self):
            return iter([[1, 2, 3]])

        def __len__(self):
            return 1

        def __getitem__(self, index):
            return [1, 2, 3]

    class MockTokenizer:
        pad_token_id = 0

        def apply_chat_template(self, messages, tokenize=False, add_generation_prompt=True):
            return "mocked_prompt"

        def __call__(self, texts, return_tensors=None):
            class TokenizerOutput(dict):
                def __init__(self):
                    super().__init__(input_ids=MockTensor())
                    self.input_ids = MockTensor()

                def to(self, device):
                    return self

            return TokenizerOutput()

        def batch_decode(self, ids, skip_special_tokens=True):
            return ["Great! Let's learn Batch 1 of 2."]

    return MockTokenizer()


@pytest.fixture
def mock_grading_agent():
    """Mock grading agent."""
    grading_agent = MagicMock()
    grading_agent.grade_answer.return_value = '{"correct": true}'
    return grading_agent


def test_handle_message_start_with_vocabulary(
    mock_lesson_cache, mock_sessions, mock_teaching_model, mock_tokenizer
):
    """Test user choosing to start with vocabulary."""
    from src.orchestrator.orchestrator import Orchestrator

    def model_getter():
        return mock_teaching_model

    orch = Orchestrator(mock_lesson_cache, mock_sessions, model_getter, mock_tokenizer)

    # Start lesson first
    session_id = "test_vocab_flow"
    orch.start_lesson(session_id, 1)

    # User selects "start with vocabulary"
    response = orch.handle_message(session_id, "1")  # Option 1

    # Should update progress and return vocab batch intro
    assert isinstance(response, str)
    # Session should track that we're in vocabulary mode
    assert "vocabulary" in mock_sessions[session_id]


def test_handle_message_quiz_answer(
    mock_lesson_cache, mock_sessions, mock_teaching_model, mock_tokenizer, mock_grading_agent
):
    """Test handling a quiz answer."""
    from src.orchestrator.orchestrator import Orchestrator

    def model_getter():
        return mock_teaching_model

    orch = Orchestrator(mock_lesson_cache, mock_sessions, model_getter, mock_tokenizer)
    orch.grading_agent = mock_grading_agent

    # Set up session in quiz state
    session_id = "test_quiz"
    orch.start_lesson(session_id, 1)

    # Manually set up quiz state (simulating that quiz was started)
    mock_sessions[session_id]["vocabulary"]["quiz_state"] = {
        "current_question": 0,
        "total_questions": 1,
        "words": [{"arabic": "كِتَابٌ", "transliteration": "kitaabun", "english": "book"}],
        "answers": [],
        "score": 0,
        "feedback_shown": False,
    }

    # User answers quiz question
    response = orch.handle_message(session_id, "book")

    # Should grade answer
    assert isinstance(response, str)


def test_start_lesson_creates_session(
    mock_lesson_cache, mock_sessions, mock_teaching_model, mock_tokenizer
):
    """Test that start_lesson creates session structure."""
    from src.orchestrator.orchestrator import Orchestrator

    def model_getter():
        return mock_teaching_model

    orch = Orchestrator(mock_lesson_cache, mock_sessions, model_getter, mock_tokenizer)

    session_id = "test_progress"
    result = orch.start_lesson(session_id, 1)

    # Should create session
    assert session_id in mock_sessions
    assert isinstance(result, str)
    # Should contain lesson info
    assert "vocabulary" in mock_sessions[session_id]
    assert "grammar" in mock_sessions[session_id]
