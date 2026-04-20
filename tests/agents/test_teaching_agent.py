"""Tests for TeachingAgent (Agent 1)."""

import pytest


@pytest.fixture
def mock_teaching_model():
    """Mock teaching model."""

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
        pad_token_id = 0

        def apply_chat_template(self, messages, tokenize=False, add_generation_prompt=True):
            return "mocked_prompt"

        def __call__(self, texts, return_tensors=None):
            class MockTensor:
                shape = (1, 3)  # batch size 1, sequence length 3

                def __iter__(self):
                    return iter([[1, 2, 3]])

                def __len__(self):
                    return 1

                def __getitem__(self, index):
                    return [1, 2, 3]

            class TokenizerOutput(dict):
                def __init__(self):
                    super().__init__(input_ids=MockTensor())
                    self.input_ids = MockTensor()

                def to(self, device):
                    return self

            return TokenizerOutput()

        def batch_decode(self, ids, skip_special_tokens=True):
            return ["مرحباً! Welcome to the lesson."]

    return MockTokenizer()


def test_teaching_agent_initialization(mock_teaching_model, mock_tokenizer):
    """Test TeachingAgent can be initialized with model and tokenizer."""
    from src.agents.teaching_agent import TeachingAgent

    agent = TeachingAgent(mock_teaching_model, mock_tokenizer)

    assert agent.model == mock_teaching_model
    assert agent.tokenizer == mock_tokenizer


def test_teaching_agent_respond_returns_string(mock_teaching_model, mock_tokenizer):
    """Test respond method returns a string."""
    from src.agents.teaching_agent import TeachingAgent

    agent = TeachingAgent(mock_teaching_model, mock_tokenizer)

    prompt = "You are a teacher. Welcome the student."
    response = agent.respond(prompt)

    assert isinstance(response, str)
    assert len(response) > 0


def test_teaching_agent_respond_uses_model(mock_teaching_model, mock_tokenizer):
    """Test respond method calls model.generate()."""
    from src.agents.teaching_agent import TeachingAgent

    agent = TeachingAgent(mock_teaching_model, mock_tokenizer)

    prompt = "Test prompt"
    response = agent.respond(prompt)

    # Should return the mocked response
    assert "مرحباً" in response


def test_teaching_agent_respond_handles_chat_format(mock_teaching_model, mock_tokenizer):
    """Test respond method formats prompt as chat messages."""
    from src.agents.teaching_agent import TeachingAgent

    agent = TeachingAgent(mock_teaching_model, mock_tokenizer)

    prompt = "Mode: lesson_start\n\nLesson 1 Overview"
    response = agent.respond(prompt)

    # Should successfully process and return response
    assert isinstance(response, str)


def test_teaching_agent_respond_with_custom_params(mock_teaching_model, mock_tokenizer):
    """Test respond method accepts generation parameters."""
    from src.agents.teaching_agent import TeachingAgent

    agent = TeachingAgent(mock_teaching_model, mock_tokenizer)

    prompt = "Test prompt"
    response = agent.respond(prompt, max_new_tokens=128, temperature=0.8)

    # Should still return valid response
    assert isinstance(response, str)
