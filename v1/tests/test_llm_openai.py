"""Tests for OpenAI LLM provider."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from llm.openai_provider import OpenAIProvider


@pytest.fixture
def mock_openai_client() -> MagicMock:
    """Create mock OpenAI client."""
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = "Generated response"

    mock_client = MagicMock()
    mock_client.chat.completions.create.return_value = mock_response

    return mock_client


def test_openai_provider_initialization() -> None:
    """Test OpenAI provider initialization."""
    with patch("llm.openai_provider.OpenAI"):
        provider = OpenAIProvider(
            api_key="test-key",
            model="gpt-4",
            temperature=0.5,
            max_tokens=300,
        )

        assert provider.model == "gpt-4"
        assert provider.temperature == 0.5
        assert provider.max_tokens == 300


def test_openai_provider_generate(mock_openai_client: MagicMock) -> None:
    """Test text generation."""
    with patch("llm.openai_provider.OpenAI", return_value=mock_openai_client):
        provider = OpenAIProvider(api_key="test-key")
        result = provider.generate("Test prompt")

        assert result == "Generated response"
        mock_openai_client.chat.completions.create.assert_called_once()


def test_openai_provider_generate_with_overrides(mock_openai_client: MagicMock) -> None:
    """Test generation with parameter overrides."""
    with patch("llm.openai_provider.OpenAI", return_value=mock_openai_client):
        provider = OpenAIProvider(api_key="test-key", model="gpt-4")
        provider.generate("Test", model="gpt-3.5-turbo", temperature=0.9)

        call_args = mock_openai_client.chat.completions.create.call_args
        assert call_args.kwargs["model"] == "gpt-3.5-turbo"
        assert call_args.kwargs["temperature"] == 0.9


def test_openai_provider_empty_response(mock_openai_client: MagicMock) -> None:
    """Test handling of empty response."""
    mock_openai_client.chat.completions.create.return_value.choices[0].message.content = None

    with patch("llm.openai_provider.OpenAI", return_value=mock_openai_client):
        provider = OpenAIProvider(api_key="test-key")
        result = provider.generate("Test prompt")

        assert result == ""
