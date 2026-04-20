"""Tests for orchestrator module."""

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
    """Mock teaching model that returns a simple response."""

    class MockModel:
        def generate(self, **kwargs):
            # Return mock token IDs
            return [[1, 2, 3, 4, 5]]

        @property
        def device(self):
            return "cpu"

    return MockModel()


@pytest.fixture
def mock_tokenizer():
    """Mock tokenizer."""

    class MockTokenizer:
        def apply_chat_template(self, messages, tokenize=False, add_generation_prompt=True):
            return "mocked_prompt"

        def __call__(self, texts, return_tensors=None):
            class TokenizerOutput(dict):
                def __init__(self):
                    super().__init__(input_ids=[[1, 2, 3]])
                    self.input_ids = [[1, 2, 3]]

                def to(self, device):
                    return self

            return TokenizerOutput()

        def batch_decode(self, ids, skip_special_tokens=True):
            return ["مرحباً! Welcome to Lesson 1: Gender and Definite Article. Let's begin!"]

    return MockTokenizer()


def test_orchestrator_start_lesson_gets_content_from_cache(
    mock_lesson_cache, mock_sessions, mock_teaching_model, mock_tokenizer
):
    """Test that start_lesson retrieves content from cache."""
    from src.orchestrator.orchestrator import Orchestrator

    orch = Orchestrator(mock_lesson_cache, mock_sessions, mock_teaching_model, mock_tokenizer)

    session_id = "test123"
    lesson_number = 1

    result = orch.start_lesson(session_id, lesson_number)

    # Should return welcome message
    assert "welcome" in result.lower() or "مرحباً" in result

    # Should update session with new structure
    assert session_id in mock_sessions
    assert mock_sessions[session_id]["lesson_number"] == 1
    assert mock_sessions[session_id]["current_progress"] == "lesson_start"

    # Check vocabulary structure
    vocab = mock_sessions[session_id]["vocabulary"]
    assert "words" in vocab
    assert "current_batch" in vocab
    assert "quizzed_words" in vocab
    assert vocab["current_batch"] == 1
    assert len(vocab["words"]) == 2  # Mock has 2 words
    assert vocab["quizzed_words"] == []

    # Check grammar structure
    grammar = mock_sessions[session_id]["grammar"]
    assert "topics" in grammar
    assert "masculine_feminine_nouns" in grammar["topics"]
    assert grammar["topics"]["masculine_feminine_nouns"]["taught"] is False


def test_orchestrator_start_lesson_updates_session_with_task(
    mock_lesson_cache, mock_sessions, mock_teaching_model, mock_tokenizer
):
    """Test that start_lesson sets current_progress in session."""
    from src.orchestrator.orchestrator import Orchestrator

    orch = Orchestrator(mock_lesson_cache, mock_sessions, mock_teaching_model, mock_tokenizer)

    session_id = "test456"
    orch.start_lesson(session_id, 1)

    assert mock_sessions[session_id]["current_progress"] == "lesson_start"
    assert mock_sessions[session_id]["status"] == "active"


def test_orchestrator_start_lesson_creates_prompt_with_vocab_and_grammar(
    mock_lesson_cache, mock_sessions, mock_teaching_model, mock_tokenizer
):
    """Test that start_lesson builds prompt with lesson content."""
    from src.orchestrator.orchestrator import Orchestrator

    orch = Orchestrator(mock_lesson_cache, mock_sessions, mock_teaching_model, mock_tokenizer)

    # Capture the prompt that was built
    session_id = "test789"
    orch.start_lesson(session_id, 1)

    # Session should have the prompt stored for debugging
    assert "last_prompt" in mock_sessions[session_id]
    prompt = mock_sessions[session_id]["last_prompt"]

    # Prompt should contain lesson details from LESSON_WELCOME template
    assert "Lesson 1" in prompt
    assert "Mode: lesson_start" in prompt
    assert "masculine_feminine_nouns" in prompt
    assert "Vocabulary: 2 words" in prompt


def test_orchestrator_start_lesson_returns_model_output(
    mock_lesson_cache, mock_sessions, mock_teaching_model, mock_tokenizer
):
    """Test that start_lesson returns the model's welcome message."""
    from src.orchestrator.orchestrator import Orchestrator

    orch = Orchestrator(mock_lesson_cache, mock_sessions, mock_teaching_model, mock_tokenizer)

    result = orch.start_lesson("test_sid", 1)

    # Should return the mocked model output
    assert isinstance(result, str)
    assert len(result) > 0


def test_orchestrator_start_lesson_lesson_not_in_cache(
    mock_lesson_cache, mock_sessions, mock_teaching_model, mock_tokenizer
):
    """Test error handling when lesson not in cache."""
    from src.orchestrator.orchestrator import Orchestrator

    orch = Orchestrator(mock_lesson_cache, mock_sessions, mock_teaching_model, mock_tokenizer)

    result = orch.start_lesson("test_sid", 999)  # Lesson doesn't exist

    # Should return error message
    assert "not found" in result.lower() or "error" in result.lower()
