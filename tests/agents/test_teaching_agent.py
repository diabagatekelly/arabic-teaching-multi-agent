"""Tests for TeachingAgent (Agent 1)."""

from unittest.mock import MagicMock, Mock, patch

import pytest
import torch

from src.agents import TeachingAgent


@pytest.fixture
def mock_model():
    """Create mock model."""
    model = MagicMock()
    model.device = "cpu"
    model.generate.return_value = torch.tensor([[1, 2, 3, 4, 5]])
    return model


@pytest.fixture
def mock_tokenizer():
    """Create mock tokenizer."""
    tokenizer = MagicMock()
    tokenizer.eos_token_id = 2

    # Create a mock that behaves like tokenizer output with .to() method
    mock_tokens = MagicMock()
    mock_tokens.to.return_value = mock_tokens  # .to() returns itself
    mock_tokens.__getitem__ = lambda self, key: torch.tensor([[1, 2, 3, 4, 5]])

    tokenizer.return_value = mock_tokens
    return tokenizer


@pytest.fixture
def teaching_agent(mock_model, mock_tokenizer):
    """Create TeachingAgent with mocked model and tokenizer."""
    return TeachingAgent(model=mock_model, tokenizer=mock_tokenizer, max_new_tokens=256)


class TestTeachingAgentInit:
    """Tests for TeachingAgent initialization."""

    def test_init_with_required_params(self, mock_model, mock_tokenizer):
        """Test initialization with required parameters."""
        agent = TeachingAgent(model=mock_model, tokenizer=mock_tokenizer)

        assert agent.model is mock_model
        assert agent.tokenizer is mock_tokenizer
        assert agent.max_new_tokens == 256  # Default value
        assert agent.content_agent is None
        assert agent.grading_agent is None

    def test_init_with_optional_agents(self, mock_model, mock_tokenizer):
        """Test initialization with optional agent dependencies."""
        mock_content_agent = Mock()
        mock_grading_agent = Mock()

        agent = TeachingAgent(
            model=mock_model,
            tokenizer=mock_tokenizer,
            content_agent=mock_content_agent,
            grading_agent=mock_grading_agent,
            max_new_tokens=512,
        )

        assert agent.content_agent is mock_content_agent
        assert agent.grading_agent is mock_grading_agent
        assert agent.max_new_tokens == 512


class TestGenerateResponse:
    """Tests for generate_response method."""

    def test_generate_response_basic(self, teaching_agent, mock_tokenizer, mock_model):
        """Test basic response generation."""
        # Mock tokenizer decode to return prompt + response
        prompt = "Test prompt"
        expected_response = "Generated response"
        mock_tokenizer.decode.return_value = f"{prompt}{expected_response}"

        response = teaching_agent.generate_response(prompt)

        # Verify tokenizer was called with prompt
        mock_tokenizer.assert_called_with(prompt, return_tensors="pt")

        # Verify model.generate was called
        mock_model.generate.assert_called_once()

        # Verify response has prompt stripped
        assert response == expected_response

    def test_generate_response_strips_prompt(self, teaching_agent, mock_tokenizer):
        """Test that prompt is correctly stripped from response."""
        prompt = "Hello, how are you?"
        full_response = "Hello, how are you?I'm doing great!"

        mock_tokenizer.decode.return_value = full_response

        response = teaching_agent.generate_response(prompt)

        assert response == "I'm doing great!"
        assert prompt not in response


class TestHandleLessonStart:
    """Tests for handle_lesson_start method."""

    @patch(
        "src.agents.teaching_agent.LESSON_WELCOME",
        "Welcome {student_name} to lesson {lesson_number}!",
    )
    def test_handle_lesson_start_basic(self, teaching_agent, mock_tokenizer):
        """Test lesson start with basic input."""
        input_data = {
            "mode": "lesson_start",
            "student_name": "Ahmed",
            "lesson_number": "1",
        }

        mock_tokenizer.decode.return_value = "Welcome prompt response here"

        response = teaching_agent.handle_lesson_start(input_data)

        # Verify response is returned
        assert isinstance(response, str)
        assert len(response) > 0

    @patch("src.agents.teaching_agent.LESSON_WELCOME", "Welcome {student_name}!")
    def test_handle_lesson_start_calls_generate(self, teaching_agent, mock_tokenizer):
        """Test that handle_lesson_start calls generate_response."""
        input_data = {"mode": "lesson_start", "student_name": "Sara"}

        mock_tokenizer.decode.return_value = "response"

        with patch.object(
            teaching_agent, "generate_response", return_value="mocked response"
        ) as mock_gen:
            response = teaching_agent.handle_lesson_start(input_data)

            mock_gen.assert_called_once()
            assert response == "mocked response"


class TestHandleTeachingVocab:
    """Tests for handle_teaching_vocab method."""

    @patch("src.agents.teaching_agent.VOCAB_BATCH_INTRO", "Vocab: {words_formatted}")
    def test_handle_teaching_vocab_basic(self, teaching_agent, mock_tokenizer):
        """Test vocabulary teaching with word list."""
        input_data = {
            "mode": "teaching_vocab",
            "sub_mode": "batch_introduction",
            "words": [{"arabic": "كِتَاب", "pronunciation": "kitaab", "english": "book"}],
        }

        mock_tokenizer.decode.return_value = "Vocab response"

        response = teaching_agent.handle_teaching_vocab(input_data)

        assert isinstance(response, str)
        assert len(response) > 0


class TestHandleTeachingGrammar:
    """Tests for handle_teaching_grammar method."""

    @patch("src.agents.teaching_agent.GRAMMAR_EXPLANATION", "Grammar: {grammar_topic}")
    def test_handle_teaching_grammar_basic(self, teaching_agent, mock_tokenizer):
        """Test grammar teaching with topic."""
        input_data = {
            "mode": "teaching_grammar",
            "sub_mode": "topic_explanation",
            "grammar_topic": "Definite Articles",
            "examples": [{"arabic": "الكتاب", "english": "the book"}],
        }

        mock_tokenizer.decode.return_value = "Grammar response"

        response = teaching_agent.handle_teaching_grammar(input_data)

        assert isinstance(response, str)
        assert len(response) > 0


class TestHandleFeedbackVocab:
    """Tests for handle_feedback_vocab method."""

    @patch("src.agents.teaching_agent.FEEDBACK_VOCAB_CORRECT", "Correct! {word_arabic}")
    @patch(
        "src.agents.teaching_agent.FEEDBACK_VOCAB_INCORRECT",
        "Not quite, {word_arabic} means {english}",
    )
    def test_handle_feedback_vocab_correct(self, teaching_agent, mock_tokenizer):
        """Test correct vocabulary feedback."""
        input_data = {
            "mode": "feedback_vocab",
            "word_arabic": "كِتَاب",
            "student_answer": "book",
            "is_correct": True,
            "english": "book",
        }

        mock_tokenizer.decode.return_value = "Correct! response"

        response = teaching_agent.handle_feedback_vocab(input_data)

        assert isinstance(response, str)

    @patch("src.agents.teaching_agent.FEEDBACK_VOCAB_CORRECT", "Correct! {word_arabic}")
    @patch(
        "src.agents.teaching_agent.FEEDBACK_VOCAB_INCORRECT",
        "Not quite, {word_arabic} means {english}",
    )
    def test_handle_feedback_vocab_incorrect(self, teaching_agent, mock_tokenizer):
        """Test incorrect vocabulary feedback."""
        input_data = {
            "mode": "feedback_vocab",
            "word_arabic": "مَدْرَسَة",
            "student_answer": "house",
            "is_correct": False,
            "english": "school",
        }

        mock_tokenizer.decode.return_value = "Not quite response"

        response = teaching_agent.handle_feedback_vocab(input_data)

        assert isinstance(response, str)


class TestHandleFeedbackGrammar:
    """Tests for handle_feedback_grammar method."""

    @patch("src.agents.teaching_agent.FEEDBACK_GRAMMAR_CORRECT", "Perfect! {question}")
    @patch(
        "src.agents.teaching_agent.FEEDBACK_GRAMMAR_INCORRECT",
        "Not quite, correct: {correct_answer}",
    )
    def test_handle_feedback_grammar_correct(self, teaching_agent, mock_tokenizer):
        """Test correct grammar feedback."""
        input_data = {
            "mode": "feedback_grammar",
            "question": "What is the definite article?",
            "student_answer": "al",
            "is_correct": True,
        }

        mock_tokenizer.decode.return_value = "Perfect! response"

        response = teaching_agent.handle_feedback_grammar(input_data)

        assert isinstance(response, str)

    @patch("src.agents.teaching_agent.FEEDBACK_GRAMMAR_CORRECT", "Perfect! {question}")
    @patch(
        "src.agents.teaching_agent.FEEDBACK_GRAMMAR_INCORRECT",
        "Not quite, correct: {correct_answer}",
    )
    def test_handle_feedback_grammar_incorrect(self, teaching_agent, mock_tokenizer):
        """Test incorrect grammar feedback."""
        input_data = {
            "mode": "feedback_grammar",
            "question": "What is the definite article?",
            "student_answer": "el",
            "is_correct": False,
            "correct_answer": "al (ال)",
        }

        mock_tokenizer.decode.return_value = "Not quite response"

        response = teaching_agent.handle_feedback_grammar(input_data)

        assert isinstance(response, str)


class TestHandleInput:
    """Tests for handle_input method (future implementation)."""

    def test_handle_input_returns_placeholder(self, teaching_agent):
        """Test that handle_input returns placeholder message."""
        response = teaching_agent.handle_input(
            user_input="start lesson 1",
            conversation_history=[],
            student_context={},
        )

        assert isinstance(response, str)
        assert "still learning" in response.lower() or "not fully implemented" in response.lower()
