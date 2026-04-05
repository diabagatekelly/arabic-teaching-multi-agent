"""Tests for Transformers LLM provider."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
import torch
from llm.transformers_provider import TransformersProvider


@pytest.fixture
def mock_model() -> MagicMock:
    """Create mock Transformers model."""
    mock = MagicMock()
    mock.device = torch.device("cpu")
    mock.generate.return_value = torch.tensor([[1, 2, 3, 4, 5]])
    return mock


@pytest.fixture
def mock_tokenizer() -> MagicMock:
    """Create mock tokenizer."""
    mock = MagicMock()
    mock.pad_token_id = 0

    # Create mock return value with .to() method
    mock_inputs = MagicMock()
    mock_inputs.__getitem__ = lambda self, key: torch.tensor([[1, 2, 3]])
    mock.return_value = mock_inputs

    mock.decode.return_value = "Test prompt Generated text"
    return mock


def test_transformers_provider_initialization(
    mock_tokenizer: MagicMock,
    mock_model: MagicMock,
) -> None:
    """Test Transformers provider initialization."""
    with patch(
        "llm.transformers_provider.AutoTokenizer.from_pretrained",
        return_value=mock_tokenizer,
    ):
        with patch(
            "llm.transformers_provider.AutoModelForCausalLM.from_pretrained",
            return_value=mock_model,
        ):
            provider = TransformersProvider(
                model_name="test-model",
                device="cpu",
                max_new_tokens=300,
            )

            assert provider.model_name == "test-model"
            assert provider.max_new_tokens == 300


def test_transformers_provider_generate(
    mock_tokenizer: MagicMock,
    mock_model: MagicMock,
) -> None:
    """Test text generation."""
    with patch(
        "llm.transformers_provider.AutoTokenizer.from_pretrained",
        return_value=mock_tokenizer,
    ):
        with patch(
            "llm.transformers_provider.AutoModelForCausalLM.from_pretrained",
            return_value=mock_model,
        ):
            provider = TransformersProvider(model_name="test-model")
            result = provider.generate("Test prompt")

            assert result == "Generated text"
            mock_model.generate.assert_called_once()


def test_transformers_provider_4bit_loading(
    mock_tokenizer: MagicMock,
    mock_model: MagicMock,
) -> None:
    """Test 4-bit quantization loading."""
    with patch(
        "llm.transformers_provider.AutoTokenizer.from_pretrained",
        return_value=mock_tokenizer,
    ):
        with patch(
            "llm.transformers_provider.AutoModelForCausalLM.from_pretrained",
            return_value=mock_model,
        ) as mock_load:
            TransformersProvider(model_name="test-model", load_in_4bit=True)

            call_kwargs = mock_load.call_args.kwargs
            assert call_kwargs["load_in_4bit"] is True
