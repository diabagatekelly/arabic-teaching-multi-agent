"""Base prompt template classes and utilities."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from pydantic import BaseModel, Field


class PromptTemplate(BaseModel, ABC):
    """Base class for all prompt templates."""

    name: str = Field(description="Template name")
    description: str = Field(description="What this template does")
    version: str = Field(default="1.0", description="Template version")

    @abstractmethod
    def format(self, **kwargs: Any) -> str:
        """Format the template with provided variables."""
        pass

    @abstractmethod
    def get_required_variables(self) -> list[str]:
        """Return list of required variable names."""
        pass

    def validate_variables(self, **kwargs: Any) -> None:
        """Validate that all required variables are provided."""
        required = set(self.get_required_variables())
        provided = set(kwargs.keys())
        missing = required - provided

        if missing:
            raise ValueError(f"Missing required variables: {missing}")


class SimplePromptTemplate(PromptTemplate):
    """Simple template with variable substitution."""

    template: str = Field(description="Template string with {variables}")

    def format(self, **kwargs: Any) -> str:
        """Format template by substituting variables."""
        self.validate_variables(**kwargs)
        return self.template.format(**kwargs)

    def get_required_variables(self) -> list[str]:
        """Extract variable names from template string."""
        import re

        matches = re.findall(r"\{(\w+)\}", self.template)
        return list(set(matches))


class FewShotPromptTemplate(PromptTemplate):
    """Template with few-shot examples."""

    instruction: str = Field(description="Task instruction")
    examples: list[dict[str, str]] = Field(description="Few-shot examples")
    input_template: str = Field(description="Template for new input")
    example_separator: str = Field(default="\n\n", description="Separator between examples")

    def format(self, **kwargs: Any) -> str:
        """Format with instruction, examples, and new input."""
        self.validate_variables(**kwargs)

        parts = [self.instruction, ""]

        for i, example in enumerate(self.examples, 1):
            parts.append(f"Example {i}:")
            for key, value in example.items():
                parts.append(f"{key}: {value}")
            parts.append("")

        parts.append("Now your turn:")
        parts.append(self.input_template.format(**kwargs))

        return "\n".join(parts)

    def get_required_variables(self) -> list[str]:
        """Extract variables from input template."""
        import re

        matches = re.findall(r"\{(\w+)\}", self.input_template)
        return list(set(matches))


class ChainOfThoughtPromptTemplate(PromptTemplate):
    """Template for chain-of-thought reasoning."""

    instruction: str = Field(description="Task instruction")
    thinking_prompt: str = Field(
        default="Let's think step by step:",
        description="Prompt to trigger reasoning",
    )
    input_template: str = Field(description="Template for input")
    include_examples: bool = Field(default=True, description="Include reasoning examples")
    examples: list[dict[str, Any]] = Field(
        default_factory=list,
        description="Examples with reasoning steps",
    )

    def format(self, **kwargs: Any) -> str:
        """Format with reasoning prompt."""
        self.validate_variables(**kwargs)

        parts = [self.instruction, ""]

        if self.include_examples and self.examples:
            for i, example in enumerate(self.examples, 1):
                parts.append(f"Example {i}:")
                parts.append(f"Input: {example['input']}")
                parts.append(f"Reasoning: {example['reasoning']}")
                parts.append(f"Answer: {example['answer']}")
                parts.append("")

        parts.append(self.input_template.format(**kwargs))
        parts.append("")
        parts.append(self.thinking_prompt)

        return "\n".join(parts)

    def get_required_variables(self) -> list[str]:
        """Extract variables from input template."""
        import re

        matches = re.findall(r"\{(\w+)\}", self.input_template)
        return list(set(matches))
