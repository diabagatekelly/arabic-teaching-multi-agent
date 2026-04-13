"""Tests for Content Agent (Agent 3)."""

from __future__ import annotations

import pytest

from src.agents.content_agent import ContentAgent

# ========== Initialization Tests ==========


def test_content_agent_initialization():
    """Test ContentAgent initializes correctly."""
    agent = ContentAgent()
    assert agent.rag_config == {}


def test_content_agent_initialization_with_config():
    """Test ContentAgent initializes with custom RAG config."""
    config = {"namespace": "custom-lessons", "top_k": 10}
    agent = ContentAgent(rag_config=config)
    assert agent.rag_config == config


# ========== get_lesson_content Tests ==========


def test_get_lesson_content_calls_retrieve(content_agent, mock_retrieve):
    """Test get_lesson_content calls retrieve with correct parameters."""
    content_agent.get_lesson_content(lesson_number=1, topic="gender")

    # Verify retrieve was called with correct parameters
    mock_retrieve.assert_called_once()
    call_args = mock_retrieve.call_args

    # Check query
    assert "Lesson 1" in call_args.kwargs["query"]
    assert "gender" in call_args.kwargs["query"]

    # Check filters
    assert call_args.kwargs["metadata_filter"]["lesson_number"] == 1
    assert call_args.kwargs["metadata_filter"]["topic"] == "gender"


def test_get_lesson_content_returns_structured_data(content_agent, mock_retrieve):
    """Test get_lesson_content returns properly structured content."""
    result = content_agent.get_lesson_content(lesson_number=1, topic="gender")

    # Verify structure
    assert "vocab" in result
    assert "grammar" in result
    assert "examples" in result
    assert "metadata" in result

    # Verify content types
    assert isinstance(result["vocab"], list)
    assert isinstance(result["grammar"], list)
    assert isinstance(result["examples"], list)
    assert isinstance(result["metadata"], dict)


def test_get_lesson_content_vocab_only(content_agent, mock_retrieve):
    """Test get_lesson_content with content_type='vocab'."""
    content_agent.get_lesson_content(
        lesson_number=1,
        topic="gender",
        content_type="vocab",
    )

    call_args = mock_retrieve.call_args
    assert "vocabulary" in call_args.kwargs["query"]
    assert call_args.kwargs["metadata_filter"]["content_type"] == "vocab"


def test_get_lesson_content_grammar_only(content_agent, mock_retrieve):
    """Test get_lesson_content with content_type='grammar'."""
    content_agent.get_lesson_content(
        lesson_number=1,
        topic="gender",
        content_type="grammar",
    )

    call_args = mock_retrieve.call_args
    assert "grammar" in call_args.kwargs["query"]
    assert call_args.kwargs["metadata_filter"]["content_type"] == "grammar"


def test_get_lesson_content_parses_vocab(content_agent, mock_retrieve):
    """Test get_lesson_content parses vocabulary items correctly."""
    result = content_agent.get_lesson_content(lesson_number=1, topic="gender")

    # Check vocab parsing
    vocab = result["vocab"]
    assert len(vocab) >= 1

    # Check vocab item structure
    vocab_item = vocab[0]
    assert "arabic" in vocab_item
    assert "transliteration" in vocab_item
    assert "english" in vocab_item
    assert "part_of_speech" in vocab_item
    assert "gender" in vocab_item


def test_get_lesson_content_parses_grammar(content_agent, mock_retrieve):
    """Test get_lesson_content parses grammar rules correctly."""
    result = content_agent.get_lesson_content(lesson_number=1, topic="gender")

    # Check grammar parsing
    grammar = result["grammar"]
    assert len(grammar) >= 1

    # Check grammar rule structure
    rule = grammar[0]
    assert "rule" in rule
    assert "category" in rule


def test_get_lesson_content_includes_metadata(content_agent, mock_retrieve):
    """Test get_lesson_content includes lesson metadata."""
    result = content_agent.get_lesson_content(lesson_number=1, topic="gender")

    metadata = result["metadata"]
    assert metadata["lesson_number"] == 1
    assert metadata["topic"] == "gender"
    assert "difficulty" in metadata


# ========== generate_exercises Tests ==========


def test_generate_exercises_fill_in_blank(content_agent, mock_retrieve):
    """Test generate_exercises creates fill-in-blank exercises."""
    exercises = content_agent.generate_exercises(
        lesson_number=1,
        topic="gender",
        exercise_type="fill_in_blank",
        count=3,
    )

    assert len(exercises) > 0
    assert len(exercises) <= 3

    # Check exercise structure
    exercise = exercises[0]
    assert "question" in exercise
    assert "answer" in exercise
    assert "explanation" in exercise
    assert "metadata" in exercise
    assert exercise["metadata"]["exercise_type"] == "fill_in_blank"


def test_generate_exercises_multiple_choice(content_agent, mock_retrieve):
    """Test generate_exercises creates multiple choice exercises."""
    exercises = content_agent.generate_exercises(
        lesson_number=1,
        topic="gender",
        exercise_type="multiple_choice",
        count=3,
    )

    assert len(exercises) > 0
    assert len(exercises) <= 3

    # Check exercise structure
    exercise = exercises[0]
    assert "question" in exercise
    assert "options" in exercise
    assert "answer" in exercise
    assert isinstance(exercise["options"], list)
    assert len(exercise["options"]) > 1
    assert exercise["answer"] in exercise["options"]


def test_generate_exercises_translation(content_agent, mock_retrieve):
    """Test generate_exercises creates translation exercises."""
    exercises = content_agent.generate_exercises(
        lesson_number=1,
        topic="gender",
        exercise_type="translation",
        count=3,
    )

    assert isinstance(exercises, list)
    # May be empty if no examples in content
    if exercises:
        exercise = exercises[0]
        assert "question" in exercise
        assert "answer" in exercise


def test_generate_exercises_error_correction(content_agent, mock_retrieve):
    """Test generate_exercises creates error correction exercises."""
    exercises = content_agent.generate_exercises(
        lesson_number=1,
        topic="gender",
        exercise_type="error_correction",
        count=3,
    )

    assert isinstance(exercises, list)
    if exercises:
        exercise = exercises[0]
        assert "question" in exercise
        assert "answer" in exercise


def test_generate_exercises_invalid_type(content_agent, mock_retrieve):
    """Test generate_exercises raises error for invalid exercise type."""
    with pytest.raises(ValueError, match="Unknown exercise type"):
        content_agent.generate_exercises(
            lesson_number=1,
            topic="gender",
            exercise_type="invalid_type",
        )


def test_generate_exercises_respects_count(content_agent, mock_retrieve):
    """Test generate_exercises respects the count parameter."""
    count = 2
    exercises = content_agent.generate_exercises(
        lesson_number=1,
        topic="gender",
        exercise_type="multiple_choice",
        count=count,
    )

    # Should not exceed requested count
    assert len(exercises) <= count


# ========== format_for_teaching Tests ==========


def test_format_for_teaching_presentation(content_agent, sample_lesson_content):
    """Test format_for_teaching with presentation format."""
    formatted = content_agent.format_for_teaching(
        sample_lesson_content,
        format_type="presentation",
    )

    assert isinstance(formatted, str)
    assert "Lesson 1" in formatted
    assert "gender" in formatted.lower()
    assert "كِتَابٌ" in formatted


def test_format_for_teaching_reference(content_agent, sample_lesson_content):
    """Test format_for_teaching with reference format."""
    formatted = content_agent.format_for_teaching(
        sample_lesson_content,
        format_type="reference",
    )

    assert isinstance(formatted, str)
    assert len(formatted) > 0


def test_format_for_teaching_review(content_agent, sample_lesson_content):
    """Test format_for_teaching with review format."""
    formatted = content_agent.format_for_teaching(
        sample_lesson_content,
        format_type="review",
    )

    assert isinstance(formatted, str)
    assert len(formatted) > 0


def test_format_for_teaching_invalid_type(content_agent, sample_lesson_content):
    """Test format_for_teaching raises error for invalid format type."""
    with pytest.raises(ValueError, match="Unknown format type"):
        content_agent.format_for_teaching(
            sample_lesson_content,
            format_type="invalid_format",
        )


# ========== Integration-style Tests ==========


def test_full_workflow_get_content_and_generate_exercises(content_agent, mock_retrieve):
    """Test full workflow: get content -> generate exercises."""
    # Get content
    content = content_agent.get_lesson_content(lesson_number=1, topic="gender")

    # Generate exercises from content
    exercises = content_agent.generate_exercises(
        lesson_number=1,
        topic="gender",
        exercise_type="multiple_choice",
        count=5,
    )

    # Both should succeed
    assert len(content["vocab"]) > 0 or len(content["grammar"]) > 0
    assert len(exercises) > 0


def test_full_workflow_get_format_present(content_agent, mock_retrieve):
    """Test full workflow: get content -> format -> present."""
    # Get content
    content = content_agent.get_lesson_content(lesson_number=1, topic="gender")

    # Format for teaching
    formatted = content_agent.format_for_teaching(content, format_type="presentation")

    # Should be ready for presentation
    assert isinstance(formatted, str)
    assert len(formatted) > 0
    assert "Lesson 1" in formatted
