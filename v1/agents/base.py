"""Base agent class for all teaching agents."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Protocol

from prompts.registry import PromptRegistry


class LLMProvider(Protocol):
    """Protocol for LLM providers (OpenAI, local model, etc)."""

    def generate(self, prompt: str, **kwargs: Any) -> str:
        """Generate text from prompt."""
        ...


class BaseAgent(ABC):
    """Base class for all teaching agents."""

    def __init__(self, llm: LLMProvider, prompt_registry: PromptRegistry) -> None:
        """
        Initialize agent.

        Args:
            llm: LLM provider for text generation
            prompt_registry: Registry of prompt templates
        """
        self.llm = llm
        self.registry = prompt_registry

    @abstractmethod
    def get_agent_name(self) -> str:
        """Return the agent's name."""
        pass

    def _generate(self, prompt: str, **kwargs: Any) -> str:
        """
        Generate response using LLM.

        Args:
            prompt: Formatted prompt string
            **kwargs: Additional generation parameters

        Returns:
            Generated text response
        """
        return self.llm.generate(prompt, **kwargs)

    def _format_prompt(self, template_name: str, **variables: Any) -> str:
        """
        Format a prompt template.

        Args:
            template_name: Name of template in registry
            **variables: Variables to fill template

        Returns:
            Formatted prompt string
        """
        return self.registry.format_template(template_name, **variables)
