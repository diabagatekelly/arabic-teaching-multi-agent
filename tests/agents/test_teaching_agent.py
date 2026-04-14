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

        # Mock decode to return a welcome message
        mock_tokenizer.decode.return_value = "formatted promptWelcome Ahmed to lesson 1!"

        response = teaching_agent.handle_lesson_start(input_data)

        # Verify response is generated and contains student name
        assert isinstance(response, str)
        assert "Ahmed" in response or "lesson" in response.lower()

    @patch("src.agents.teaching_agent.LESSON_WELCOME", "Welcome {student_name}!")
    def test_handle_lesson_start_calls_generate(self, teaching_agent, mock_tokenizer):
        """Test that handle_lesson_start calls generate_response."""
        input_data = {"mode": "lesson_start", "student_name": "Sara"}

        expected_response = "mocked response"
        mock_tokenizer.decode.return_value = "response"

        with patch.object(
            teaching_agent, "generate_response", return_value=expected_response
        ) as mock_gen:
            response = teaching_agent.handle_lesson_start(input_data)

            mock_gen.assert_called_once()
            assert response == expected_response


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

        # Mock vocab teaching response
        mock_tokenizer.decode.return_value = "formatted promptLet's learn: كِتَاب means book"

        response = teaching_agent.handle_teaching_vocab(input_data)

        # Verify response contains vocab content
        assert isinstance(response, str)
        assert "كِتَاب" in response or "book" in response.lower()


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

        # Mock grammar teaching response
        mock_tokenizer.decode.return_value = (
            "formatted promptToday we'll learn about Definite Articles"
        )

        response = teaching_agent.handle_teaching_grammar(input_data)

        # Verify response contains grammar topic
        assert isinstance(response, str)
        assert "Definite" in response or "grammar" in response.lower() or "Articles" in response


class TestHandleFeedbackVocab:
    """Tests for handle_feedback_vocab method."""

    @pytest.mark.parametrize(
        "is_correct,word_arabic,student_answer,english",
        [
            (True, "كِتَاب", "book", "book"),
            (False, "مَدْرَسَة", "house", "school"),
        ],
    )
    @patch("src.agents.teaching_agent.FEEDBACK_VOCAB_CORRECT", "Correct! {word_arabic}")
    @patch(
        "src.agents.teaching_agent.FEEDBACK_VOCAB_INCORRECT",
        "Not quite, {word_arabic} means {english}",
    )
    def test_handle_feedback_vocab(
        self, teaching_agent, mock_tokenizer, is_correct, word_arabic, student_answer, english
    ):
        """Test vocabulary feedback for correct and incorrect answers."""
        input_data = {
            "mode": "feedback_vocab",
            "word_arabic": word_arabic,
            "student_answer": student_answer,
            "is_correct": is_correct,
            "english": english,
        }

        # Mock feedback response
        feedback_text = "Great!" if is_correct else "Try again"
        mock_tokenizer.decode.return_value = f"formatted prompt{feedback_text}"

        response = teaching_agent.handle_feedback_vocab(input_data)

        # Verify response contains feedback
        assert isinstance(response, str)
        assert len(response) > 5  # More than minimal
        # Response should contain feedback keywords or Arabic word
        assert word_arabic in response or any(
            keyword in response.lower() for keyword in ["great", "try", "correct", "excellent"]
        )


class TestHandleFeedbackGrammar:
    """Tests for handle_feedback_grammar method."""

    @pytest.mark.parametrize(
        "is_correct,question,student_answer,correct_answer",
        [
            (True, "What is the definite article?", "al", None),
            (False, "What is the definite article?", "el", "al (ال)"),
        ],
    )
    @patch("src.agents.teaching_agent.FEEDBACK_GRAMMAR_CORRECT", "Perfect! {question}")
    @patch(
        "src.agents.teaching_agent.FEEDBACK_GRAMMAR_INCORRECT",
        "Not quite, correct: {correct_answer}",
    )
    def test_handle_feedback_grammar(
        self, teaching_agent, mock_tokenizer, is_correct, question, student_answer, correct_answer
    ):
        """Test grammar feedback for correct and incorrect answers."""
        input_data = {
            "mode": "feedback_grammar",
            "question": question,
            "student_answer": student_answer,
            "is_correct": is_correct,
        }
        if correct_answer:
            input_data["correct_answer"] = correct_answer

        # Mock feedback response
        feedback_text = "Perfect!" if is_correct else "Not quite"
        mock_tokenizer.decode.return_value = f"formatted prompt{feedback_text}"

        response = teaching_agent.handle_feedback_grammar(input_data)

        # Verify response contains meaningful feedback
        assert isinstance(response, str)
        assert len(response) > 10  # More than just "Great!"
        # Should contain question context or feedback keyword
        assert any(
            keyword in response.lower()
            for keyword in ["perfect", "great", "not quite", "try", "correct"]
        )


class TestHandleInput:
    """Tests for handle_input method (future implementation)."""

    @pytest.mark.skip(reason="Feature not yet implemented - placeholder only")
    def test_handle_input_returns_placeholder(self, teaching_agent):
        """Test that handle_input returns placeholder message."""
        response = teaching_agent.handle_input(
            user_input="start lesson 1",
            conversation_history=[],
            student_context={},
        )

        assert isinstance(response, str)


class TestOrchestratorAdapters:
    """Tests for adapter methods that orchestrator nodes expect (TDD)."""

    @patch("src.agents.teaching_agent.LESSON_WELCOME", "Welcome {lesson_number}!")
    def test_start_lesson_adapter_calls_handle_lesson_start(self, teaching_agent, mock_tokenizer):
        """start_lesson() should delegate to handle_lesson_start()."""
        input_data = {"lesson_number": "1", "mode": "lesson_start"}
        mock_tokenizer.decode.return_value = "formatted promptWelcome to lesson 1"

        response = teaching_agent.start_lesson(input_data)

        # Verify correct delegation - response should contain lesson info
        assert isinstance(response, str)
        assert "lesson" in response.lower() or "1" in response

    @pytest.mark.parametrize(
        "input_data,mock_template",
        [
            (
                {
                    "mode": "vocabulary",
                    "is_correct": True,
                    "word_arabic": "كِتَاب",
                    "student_answer": "book",
                    "english": "book",
                },
                "FEEDBACK_VOCAB_CORRECT",
            ),
            (
                {
                    "mode": "grammar",
                    "is_correct": True,
                    "question": "What is the definite article?",
                    "student_answer": "al",
                },
                "FEEDBACK_GRAMMAR_CORRECT",
            ),
            (
                {
                    # No mode - should default to vocabulary
                    "is_correct": True,
                    "word_arabic": "كِتَاب",
                    "student_answer": "book",
                    "english": "book",
                },
                "FEEDBACK_VOCAB_CORRECT",
            ),
        ],
    )
    def test_provide_feedback_routing(
        self, teaching_agent, mock_tokenizer, input_data, mock_template
    ):
        """Test provide_feedback routes correctly to vocab/grammar based on mode."""
        with patch(f"src.agents.teaching_agent.{mock_template}", "Mocked template"):
            mock_tokenizer.decode.return_value = "formatted promptGreat work!"

            response = teaching_agent.provide_feedback(input_data)

            # Verify correct routing with meaningful feedback
            assert isinstance(response, str)
            assert len(response) > 10  # More than minimal response
            # Should contain feedback keywords
            assert any(
                keyword in response.lower()
                for keyword in ["great", "work", "excellent", "perfect", "good"]
            )

    def test_handle_user_message_adapter_exists(self, teaching_agent):
        """handle_user_message() adapter should exist for orchestrator compatibility."""
        input_data = {"user_input": "What does كِتَاب mean?", "mode": "vocabulary"}

        # Should have this method (may return placeholder for now)
        assert hasattr(teaching_agent, "handle_user_message")
        response = teaching_agent.handle_user_message(input_data)
        assert isinstance(response, str)

    def test_provide_feedback_validates_mode(self, teaching_agent):
        """Should raise ValueError for unsupported mode values (addressing code review)."""
        input_data = {
            "mode": "invalid_mode",  # Unsupported mode
            "is_correct": True,
            "word_arabic": "كِتَاب",
            "student_answer": "book",
            "english": "book",
        }

        with pytest.raises(ValueError, match="mode.*invalid|unsupported"):
            teaching_agent.provide_feedback(input_data)

    @patch("src.agents.teaching_agent.FEEDBACK_VOCAB_CORRECT", "Great job!")
    @patch("src.agents.teaching_agent.FEEDBACK_GRAMMAR_CORRECT", "Perfect!")
    def test_provide_feedback_accepts_valid_modes(self, teaching_agent, mock_tokenizer):
        """Should accept 'vocabulary' and 'grammar' modes without error."""
        mock_tokenizer.decode.return_value = "Great!"

        # Vocabulary mode
        vocab_data = {
            "mode": "vocabulary",
            "is_correct": True,
            "word_arabic": "كِتَاب",
            "student_answer": "book",
            "english": "book",
        }
        response = teaching_agent.provide_feedback(vocab_data)
        assert isinstance(response, str)

        # Grammar mode
        grammar_data = {
            "mode": "grammar",
            "is_correct": True,
            "question": "Q?",
            "student_answer": "ans",
        }
        response = teaching_agent.provide_feedback(grammar_data)
        assert isinstance(response, str)
