"""Tests for base prompt template classes."""

from __future__ import annotations

import pytest
from prompts.base import (
    ChainOfThoughtPromptTemplate,
    FewShotPromptTemplate,
    SimplePromptTemplate,
)


def test_simple_prompt_template_format() -> None:
    """Test simple template formatting."""
    template = SimplePromptTemplate(
        name="test",
        description="Test template",
        template="Hello {name}, you are {age} years old.",
    )

    result = template.format(name="Alice", age="25")
    assert result == "Hello Alice, you are 25 years old."


def test_simple_prompt_template_get_variables() -> None:
    """Test extracting variables from template."""
    template = SimplePromptTemplate(
        name="test",
        description="Test template",
        template="Hello {name}, you are {age} years old.",
    )

    variables = template.get_required_variables()
    assert set(variables) == {"name", "age"}


def test_simple_prompt_template_validation_success() -> None:
    """Test validation passes with all variables."""
    template = SimplePromptTemplate(
        name="test",
        description="Test template",
        template="Hello {name}",
    )

    template.validate_variables(name="Alice")


def test_simple_prompt_template_validation_failure() -> None:
    """Test validation fails with missing variables."""
    template = SimplePromptTemplate(
        name="test",
        description="Test template",
        template="Hello {name}, you are {age} years old.",
    )

    with pytest.raises(ValueError, match="Missing required variables"):
        template.validate_variables(name="Alice")


def test_few_shot_prompt_template_format() -> None:
    """Test few-shot template formatting."""
    template = FewShotPromptTemplate(
        name="test",
        description="Test template",
        instruction="Translate to French:",
        examples=[
            {"Input": "hello", "Output": "bonjour"},
            {"Input": "goodbye", "Output": "au revoir"},
        ],
        input_template="Input: {word}",
    )

    result = template.format(word="cat")

    assert "Translate to French:" in result
    assert "Example 1:" in result
    assert "Input: hello" in result
    assert "Output: bonjour" in result
    assert "Example 2:" in result
    assert "Now your turn:" in result
    assert "Input: cat" in result


def test_few_shot_prompt_template_get_variables() -> None:
    """Test extracting variables from few-shot template."""
    template = FewShotPromptTemplate(
        name="test",
        description="Test template",
        instruction="Test",
        examples=[],
        input_template="Translate {word} from {source} to {target}",
    )

    variables = template.get_required_variables()
    assert set(variables) == {"word", "source", "target"}


def test_chain_of_thought_prompt_template_format() -> None:
    """Test chain-of-thought template formatting."""
    template = ChainOfThoughtPromptTemplate(
        name="test",
        description="Test template",
        instruction="Solve this math problem:",
        thinking_prompt="Let's solve step by step:",
        input_template="What is {a} + {b}?",
        include_examples=False,
    )

    result = template.format(a="5", b="3")

    assert "Solve this math problem:" in result
    assert "What is 5 + 3?" in result
    assert "Let's solve step by step:" in result


def test_chain_of_thought_prompt_template_with_examples() -> None:
    """Test chain-of-thought with examples."""
    template = ChainOfThoughtPromptTemplate(
        name="test",
        description="Test template",
        instruction="Solve math:",
        thinking_prompt="Think:",
        input_template="Problem: {problem}",
        include_examples=True,
        examples=[
            {
                "input": "2 + 2",
                "reasoning": "2 + 2 = 4",
                "answer": "4",
            },
        ],
    )

    result = template.format(problem="5 + 3")

    assert "Example 1:" in result
    assert "Input: 2 + 2" in result
    assert "Reasoning: 2 + 2 = 4" in result
    assert "Answer: 4" in result
    assert "Problem: 5 + 3" in result


def test_chain_of_thought_prompt_template_without_examples() -> None:
    """Test chain-of-thought skips examples when disabled."""
    template = ChainOfThoughtPromptTemplate(
        name="test",
        description="Test template",
        instruction="Solve math:",
        thinking_prompt="Think:",
        input_template="Problem: {problem}",
        include_examples=False,
        examples=[{"input": "2 + 2", "reasoning": "test", "answer": "4"}],
    )

    result = template.format(problem="5 + 3")

    assert "Example 1:" not in result
    assert "2 + 2" not in result
