"""Tests for base agent functionality."""

from __future__ import annotations

import pytest
from prompts.registry import PromptRegistry

from agents.base import BaseAgent


class MockLLM:
    """Mock LLM for testing."""

    def __init__(self, response: str = "Mock response") -> None:
        self.response = response
        self.last_prompt: str | None = None

    def generate(self, prompt: str, **kwargs: dict[str, str]) -> str:
        """Store prompt and return mock response."""
        self.last_prompt = prompt
        return self.response


class ConcreteAgent(BaseAgent):
    """Concrete implementation for testing."""

    def get_agent_name(self) -> str:
        return "TestAgent"


def test_base_agent_initialization() -> None:
    """Test base agent can be initialized."""
    llm = MockLLM()
    registry = PromptRegistry()

    agent = ConcreteAgent(llm, registry)

    assert agent.llm is llm
    assert agent.registry is registry


def test_base_agent_get_name() -> None:
    """Test agent name retrieval."""
    llm = MockLLM()
    registry = PromptRegistry()
    agent = ConcreteAgent(llm, registry)

    assert agent.get_agent_name() == "TestAgent"


def test_base_agent_generate() -> None:
    """Test LLM generation."""
    llm = MockLLM(response="Generated text")
    registry = PromptRegistry()
    agent = ConcreteAgent(llm, registry)

    result = agent._generate("Test prompt")

    assert result == "Generated text"
    assert llm.last_prompt == "Test prompt"


def test_base_agent_format_prompt() -> None:
    """Test prompt formatting through registry."""
    llm = MockLLM()
    registry = PromptRegistry()
    agent = ConcreteAgent(llm, registry)

    result = agent._format_prompt(
        "vocab_introduction",
        lesson_number=3,
        vocabulary_list="كِتَاب, مَدْرَسَة",
    )

    assert "Lesson 3" in result
    assert "كِتَاب, مَدْرَسَة" in result


def test_base_agent_format_nonexistent_template() -> None:
    """Test formatting nonexistent template raises error."""
    llm = MockLLM()
    registry = PromptRegistry()
    agent = ConcreteAgent(llm, registry)

    with pytest.raises(KeyError, match="not found"):
        agent._format_prompt("nonexistent_template")
