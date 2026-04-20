"""Tests for ContentAgent (Agent 3)."""

import json
from unittest.mock import MagicMock, patch

import pytest

from src.agents.content_agent import ContentAgent


@pytest.fixture
def mock_model():
    """Create mock model for content agent."""
    model = MagicMock()
    model.device = "cpu"
    model.generate.return_value = MagicMock()
    return model


@pytest.fixture
def mock_tokenizer():
    """Create mock tokenizer for content agent."""
    tokenizer = MagicMock()
    tokenizer.eos_token_id = 2
    tokenizer.pad_token_id = 0

    # Mock apply_chat_template (not used in content agent but for completeness)
    tokenizer.apply_chat_template.return_value = "formatted_text"

    # Mock tokenizer call
    mock_tokens = MagicMock()
    mock_tokens.to.return_value = mock_tokens
    mock_tokens.input_ids = [[1, 2, 3, 4, 5]]
    tokenizer.return_value = mock_tokens

    # Mock decode
    tokenizer.decode.return_value = '{"question": "test", "answer": "test"}'

    return tokenizer


@pytest.fixture
def content_agent(mock_model, mock_tokenizer):
    """Create ContentAgent with mocked model and tokenizer."""
    return ContentAgent(model=mock_model, tokenizer=mock_tokenizer, max_new_tokens=512)


class TestContentAgentInit:
    """Tests for ContentAgent initialization."""

    def test_init_with_default_max_tokens(self, mock_model, mock_tokenizer):
        """Test initialization with default max_new_tokens."""
        agent = ContentAgent(model=mock_model, tokenizer=mock_tokenizer)

        assert agent.model is mock_model
        assert agent.tokenizer is mock_tokenizer
        assert agent.max_new_tokens == 512

    def test_init_with_custom_max_tokens(self, mock_model, mock_tokenizer):
        """Test initialization with custom max_new_tokens."""
        agent = ContentAgent(model=mock_model, tokenizer=mock_tokenizer, max_new_tokens=1024)

        assert agent.max_new_tokens == 1024

    def test_init_loads_exercise_templates(self, mock_model, mock_tokenizer):
        """Test that initialization loads exercise templates."""
        agent = ContentAgent(model=mock_model, tokenizer=mock_tokenizer)

        # Should have loaded templates from RAG database
        assert isinstance(agent.exercise_templates, dict)

    def test_init_loads_lessons(self, mock_model, mock_tokenizer):
        """Test that initialization loads lessons."""
        agent = ContentAgent(model=mock_model, tokenizer=mock_tokenizer)

        # Should have loaded lessons from RAG database
        assert isinstance(agent.lessons, dict)


class TestGenerateResponse:
    """Tests for generate_response method."""

    def test_generate_response_basic(self, content_agent, mock_tokenizer, mock_model):
        """Test response generation."""
        prompt = "Generate an exercise"
        expected_response = '{"question": "What is X?", "answer": "Y"}'

        # Mock tokenizer decode
        mock_tokenizer.decode.return_value = f"{prompt}{expected_response}"

        response = content_agent.generate_response(prompt)

        # Verify model.generate was called
        mock_model.generate.assert_called_once()
        call_kwargs = mock_model.generate.call_args[1]
        assert call_kwargs["do_sample"] is True
        assert call_kwargs["temperature"] == 0.3
        assert call_kwargs["max_new_tokens"] == 512

        # Verify response has prompt stripped
        assert response == expected_response


class TestGenerateExercise:
    """Tests for generate_exercise method."""

    @patch("src.agents.content_agent.ContentAgent.generate_response")
    def test_generate_exercise_returns_json(self, mock_generate, content_agent):
        """Test generate_exercise returns JSON string."""
        mock_generate.return_value = (
            '{"question": "Translate: كِتَاب", "answer": "book", "difficulty": "beginner"}'
        )

        input_data = {
            "exercise_type": "translation",
            "difficulty": "beginner",
            "learned_items": ["كِتَاب - book"],
            "count": 1,
        }

        response = content_agent.generate_exercise(input_data)

        # Should return JSON
        assert isinstance(response, str)
        data = json.loads(response)
        assert "question" in data
        assert "answer" in data

    @patch("src.agents.content_agent.ContentAgent.generate_response")
    def test_generate_exercise_extracts_json_from_markdown(self, mock_generate, content_agent):
        """Test generate_exercise extracts JSON from markdown code blocks."""
        mock_generate.return_value = '```json\n{"question": "test", "answer": "test"}\n```'

        input_data = {
            "exercise_type": "translation",
            "difficulty": "beginner",
            "learned_items": ["test"],
        }

        response = content_agent.generate_exercise(input_data)

        # Should extract JSON from markdown
        assert response == '{"question": "test", "answer": "test"}'

    @patch("src.agents.content_agent.ContentAgent.generate_response")
    def test_generate_exercise_with_lesson_context(self, mock_generate, content_agent):
        """Test generate_exercise uses lesson context when available."""
        mock_generate.return_value = '{"question": "test", "answer": "test"}'

        # Add a lesson to the agent's lessons
        content_agent.lessons[1] = {
            "metadata": {"vocabulary": ["كِتَاب - book"]},
            "content": "Lesson 1 content",
        }

        input_data = {
            "exercise_type": "translation",
            "difficulty": "beginner",
            "learned_items": ["كِتَاب"],
            "lesson_number": 1,
        }

        content_agent.generate_exercise(input_data)

        # Should call generate_response with lesson vocab in prompt
        mock_generate.assert_called_once()
        prompt = mock_generate.call_args[0][0]
        assert "كِتَاب - book" in prompt


class TestRetrieveContent:
    """Tests for retrieve_content method."""

    def test_retrieve_content_returns_lesson_data(self, content_agent):
        """Test retrieve_content returns lesson metadata."""
        # Add a lesson to the agent's lessons
        content_agent.lessons[1] = {
            "metadata": {
                "lesson_name": "Arabic Basics",
                "difficulty": "beginner",
                "vocabulary": ["كِتَاب - book"],
                "grammar_points": ["noun_gender"],
            },
            "content": "Full lesson content here...",
            "file": "lesson_1.md",
        }

        input_data = {"lesson_number": 1, "content_type": "all"}

        response = content_agent.retrieve_content(input_data)

        # Should return JSON with lesson data
        data = json.loads(response)
        assert data["lesson"] == 1
        assert data["lesson_name"] == "Arabic Basics"
        assert "vocabulary" in data
        assert "grammar_points" in data

    def test_retrieve_content_vocab_only(self, content_agent):
        """Test retrieve_content returns only vocabulary when requested."""
        content_agent.lessons[1] = {
            "metadata": {
                "lesson_name": "Arabic Basics",
                "vocabulary": ["كِتَاب - book"],
                "grammar_points": ["noun_gender"],
            },
            "content": "",
        }

        input_data = {"lesson_number": 1, "content_type": "vocab"}

        response = content_agent.retrieve_content(input_data)

        data = json.loads(response)
        assert "vocabulary" in data
        assert "grammar_points" not in data

    def test_retrieve_content_grammar_only(self, content_agent):
        """Test retrieve_content returns only grammar when requested."""
        content_agent.lessons[1] = {
            "metadata": {
                "lesson_name": "Arabic Basics",
                "vocabulary": ["كِتَاب - book"],
                "grammar_points": ["noun_gender"],
            },
            "content": "## Grammar Point\nRule here",
        }

        input_data = {"lesson_number": 1, "content_type": "grammar"}

        response = content_agent.retrieve_content(input_data)

        data = json.loads(response)
        assert "grammar_points" in data
        assert "vocabulary" not in data

    def test_retrieve_content_lesson_not_found(self, content_agent):
        """Test retrieve_content returns error for non-existent lesson."""
        input_data = {"lesson_number": 999}

        response = content_agent.retrieve_content(input_data)

        data = json.loads(response)
        assert "error" in data
        assert "available_lessons" in data
