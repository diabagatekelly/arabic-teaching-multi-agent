"""OpenAI API LLM provider."""

from __future__ import annotations

from typing import Any

from openai import OpenAI


class OpenAIProvider:
    """LLM provider using OpenAI API."""

    def __init__(
        self,
        api_key: str | None = None,
        model: str = "gpt-4",
        temperature: float = 0.7,
        max_tokens: int = 500,
    ) -> None:
        """
        Initialize OpenAI provider.

        Args:
            api_key: OpenAI API key (uses env var if None)
            model: Model name to use
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
        """
        self.client = OpenAI(api_key=api_key)
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens

    def generate(self, prompt: str, **kwargs: Any) -> str:
        """
        Generate text using OpenAI API.

        Args:
            prompt: Input prompt
            **kwargs: Override default parameters

        Returns:
            Generated text
        """
        response = self.client.chat.completions.create(
            model=kwargs.get("model", self.model),
            messages=[{"role": "user", "content": prompt}],
            temperature=kwargs.get("temperature", self.temperature),
            max_tokens=kwargs.get("max_tokens", self.max_tokens),
        )
        return response.choices[0].message.content or ""
