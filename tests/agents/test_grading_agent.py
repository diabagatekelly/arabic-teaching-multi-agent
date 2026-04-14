"""Tests for GradingAgent (Agent 2)."""

from unittest.mock import MagicMock, patch

import pytest
import torch

from src.agents import GradingAgent


@pytest.fixture
def mock_model():
    """Create mock model for grading agent."""
    model = MagicMock()
    model.device = "cpu"
    model.generate.return_value = torch.tensor([[1, 2, 3, 4, 5]])
    return model


@pytest.fixture
def mock_tokenizer():
    """Create mock tokenizer for grading agent."""
    tokenizer = MagicMock()
    tokenizer.eos_token_id = 2

    # Create a mock that behaves like tokenizer output with .to() method
    mock_tokens = MagicMock()
    mock_tokens.to.return_value = mock_tokens  # .to() returns itself
    mock_tokens.__getitem__ = lambda self, key: torch.tensor([[1, 2, 3, 4, 5]])

    tokenizer.return_value = mock_tokens
    return tokenizer


@pytest.fixture
def grading_agent(mock_model, mock_tokenizer):
    """Create GradingAgent with mocked model and tokenizer."""
    return GradingAgent(model=mock_model, tokenizer=mock_tokenizer, max_new_tokens=50)


class TestGradingAgentInit:
    """Tests for GradingAgent initialization."""

    @pytest.mark.parametrize(
        "max_new_tokens,expected",
        [
            (None, 50),  # Default value
            (100, 100),  # Custom value
        ],
    )
    def test_init_with_max_tokens(self, mock_model, mock_tokenizer, max_new_tokens, expected):
        """Test initialization with default or custom max_new_tokens."""
        if max_new_tokens is None:
            agent = GradingAgent(model=mock_model, tokenizer=mock_tokenizer)
        else:
            agent = GradingAgent(
                model=mock_model, tokenizer=mock_tokenizer, max_new_tokens=max_new_tokens
            )

        assert agent.model is mock_model
        assert agent.tokenizer is mock_tokenizer
        assert agent.max_new_tokens == expected


class TestGenerateResponse:
    """Tests for generate_response method."""

    def test_generate_response_basic(self, grading_agent, mock_tokenizer, mock_model):
        """Test response generation with deterministic sampling, prompt stripping, and max tokens."""
        # Mock tokenizer decode to return prompt + response
        prompt = "Test prompt"
        expected_response = '{"correct": true}'
        mock_tokenizer.decode.return_value = f"{prompt}{expected_response}"

        response = grading_agent.generate_response(prompt)

        # Verify tokenizer was called with prompt
        mock_tokenizer.assert_called_with(prompt, return_tensors="pt")

        # Verify model.generate was called with correct parameters
        mock_model.generate.assert_called_once()
        call_kwargs = mock_model.generate.call_args[1]
        assert call_kwargs["do_sample"] is False
        assert call_kwargs["max_new_tokens"] == 50

        # Verify response has prompt stripped
        assert response == expected_response


class TestGradeVocab:
    """Tests for grade_vocab method."""

    @patch("src.agents.grading_agent.GRADING_VOCAB")
    def test_grade_vocab_correct_answer(self, mock_prompt, grading_agent, mock_tokenizer):
        """Test grading correct vocabulary answer."""
        mock_prompt.format.return_value = "formatted prompt"
        mock_tokenizer.decode.return_value = 'formatted prompt{"correct": true}'

        input_data = {
            "word": "كِتَاب",
            "student_answer": "book",
            "correct_answer": "book",
        }

        response = grading_agent.grade_vocab(input_data)

        # Verify prompt was formatted with input data
        mock_prompt.format.assert_called_once_with(
            word="كِتَاب", student_answer="book", correct_answer="book"
        )

        # Verify response is JSON string
        assert isinstance(response, str)
        assert '{"correct": true}' in response

    @patch("src.agents.grading_agent.GRADING_VOCAB")
    def test_grade_vocab_incorrect_answer(self, mock_prompt, grading_agent, mock_tokenizer):
        """Test grading incorrect vocabulary answer."""
        mock_prompt.format.return_value = "formatted prompt"
        mock_tokenizer.decode.return_value = 'formatted prompt{"correct": false}'

        input_data = {
            "word": "مَدْرَسَة",
            "student_answer": "house",
            "correct_answer": "school",
        }

        response = grading_agent.grade_vocab(input_data)

        # Verify prompt was formatted with input data
        mock_prompt.format.assert_called_once_with(
            word="مَدْرَسَة", student_answer="house", correct_answer="school"
        )

        # Verify response is JSON string
        assert isinstance(response, str)
        assert '{"correct": false}' in response


class TestGradeGrammarQuiz:
    """Tests for grade_grammar_quiz method."""

    @patch("src.agents.grading_agent.GRADING_GRAMMAR_QUIZ")
    def test_grade_grammar_quiz_correct(self, mock_prompt, grading_agent, mock_tokenizer):
        """Test grading correct grammar answer."""
        mock_prompt.format.return_value = "formatted prompt"
        mock_tokenizer.decode.return_value = 'formatted prompt{"correct": true}'

        input_data = {
            "question": "Is مَدْرَسَة masculine or feminine?",
            "student_answer": "feminine",
            "correct_answer": "feminine",
        }

        response = grading_agent.grade_grammar_quiz(input_data)

        # Verify prompt was formatted with input data
        mock_prompt.format.assert_called_once_with(
            question="Is مَدْرَسَة masculine or feminine?",
            student_answer="feminine",
            correct_answer="feminine",
        )

        # Verify response is JSON string
        assert isinstance(response, str)
        assert '{"correct": true}' in response

    @patch("src.agents.grading_agent.GRADING_GRAMMAR_QUIZ")
    def test_grade_grammar_quiz_incorrect(self, mock_prompt, grading_agent, mock_tokenizer):
        """Test grading incorrect grammar answer."""
        mock_prompt.format.return_value = "formatted prompt"
        mock_tokenizer.decode.return_value = 'formatted prompt{"correct": false}'

        input_data = {
            "question": "Is كِتَاب masculine or feminine?",
            "student_answer": "feminine",
            "correct_answer": "masculine",
        }

        response = grading_agent.grade_grammar_quiz(input_data)

        # Verify prompt was formatted with input data
        mock_prompt.format.assert_called_once_with(
            question="Is كِتَاب masculine or feminine?",
            student_answer="feminine",
            correct_answer="masculine",
        )

        # Verify response is JSON string
        assert isinstance(response, str)
        assert '{"correct": false}' in response


class TestGradeGrammarTest:
    """Tests for grade_grammar_test method."""

    @patch("src.agents.grading_agent.GRADING_GRAMMAR_TEST")
    def test_grade_grammar_test_single_question(self, mock_prompt, grading_agent, mock_tokenizer):
        """Test grading grammar test with single question."""
        mock_prompt.format.return_value = "formatted prompt"
        mock_tokenizer.decode.return_value = 'formatted prompt{"total_score": "1/1", "results": [{"question_id": "q1", "correct": true}]}'

        input_data = {
            "lesson_number": 3,
            "answers": [
                {
                    "question": "Is مَدْرَسَة masculine or feminine?",
                    "student_answer": "feminine",
                    "correct_answer": "feminine",
                }
            ],
        }

        response = grading_agent.grade_grammar_test(input_data)

        # Verify prompt was formatted
        mock_prompt.format.assert_called_once()
        call_kwargs = mock_prompt.format.call_args[1]
        assert call_kwargs["lesson_number"] == 3
        assert "Q1:" in call_kwargs["answers_formatted"]
        assert "feminine" in call_kwargs["answers_formatted"]

        # Verify response is JSON string with test structure
        assert isinstance(response, str)
        assert "total_score" in response
        assert "results" in response

    @patch("src.agents.grading_agent.GRADING_GRAMMAR_TEST")
    def test_grade_grammar_test_multiple_questions(
        self, mock_prompt, grading_agent, mock_tokenizer
    ):
        """Test grading grammar test with multiple questions."""
        mock_prompt.format.return_value = "formatted prompt"
        mock_tokenizer.decode.return_value = (
            'formatted prompt{"total_score": "1/2", '
            '"results": [{"question_id": "q1", "correct": true}, {"question_id": "q2", "correct": false}]}'
        )

        input_data = {
            "lesson_number": 3,
            "answers": [
                {
                    "question": "Is مَدْرَسَة masculine or feminine?",
                    "student_answer": "feminine",
                    "correct_answer": "feminine",
                },
                {
                    "question": "Is كِتَاب masculine or feminine?",
                    "student_answer": "feminine",
                    "correct_answer": "masculine",
                },
            ],
        }

        response = grading_agent.grade_grammar_test(input_data)

        # Verify prompt includes all questions
        mock_prompt.format.assert_called_once()
        call_kwargs = mock_prompt.format.call_args[1]
        assert call_kwargs["lesson_number"] == 3
        formatted = call_kwargs["answers_formatted"]
        assert "Q1:" in formatted
        assert "Q2:" in formatted
        assert "مَدْرَسَة" in formatted
        assert "كِتَاب" in formatted

        # Verify response structure
        assert isinstance(response, str)
        assert "total_score" in response
        assert "results" in response

    @patch("src.agents.grading_agent.GRADING_GRAMMAR_TEST")
    def test_grade_grammar_test_formats_answers_correctly(
        self, mock_prompt, grading_agent, mock_tokenizer
    ):
        """Test that answers are formatted correctly for prompt."""
        mock_prompt.format.return_value = "formatted prompt"
        mock_tokenizer.decode.return_value = 'formatted prompt{"total_score": "2/2", "results": []}'

        input_data = {
            "lesson_number": 5,
            "answers": [
                {
                    "question": "Question 1?",
                    "student_answer": "Answer 1",
                    "correct_answer": "Answer 1",
                },
                {
                    "question": "Question 2?",
                    "student_answer": "Answer 2",
                    "correct_answer": "Answer 2",
                },
            ],
        }

        grading_agent.grade_grammar_test(input_data)

        # Verify formatting includes Q1, Q2 prefixes and proper structure
        call_kwargs = mock_prompt.format.call_args[1]
        formatted = call_kwargs["answers_formatted"]

        assert "Q1: Question 1?" in formatted
        assert "Student: Answer 1" in formatted
        assert "Correct: Answer 1" in formatted

        assert "Q2: Question 2?" in formatted
        assert "Student: Answer 2" in formatted
        assert "Correct: Answer 2" in formatted
