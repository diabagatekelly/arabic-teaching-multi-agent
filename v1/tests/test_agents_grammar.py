"""Tests for grammar teaching agent."""

from __future__ import annotations

from prompts.registry import PromptRegistry

from agents.grammar_agent import GrammarAgent


class MockLLM:
    """Mock LLM for testing."""

    def __init__(self, response: str = "Mock response") -> None:
        self.response = response
        self.last_prompt: str | None = None
        self.call_count = 0

    def generate(self, prompt: str, **kwargs: dict[str, str]) -> str:
        """Store prompt and return mock response."""
        self.last_prompt = prompt
        self.call_count += 1
        return self.response


def test_grammar_agent_initialization() -> None:
    """Test grammar agent initialization."""
    llm = MockLLM()
    registry = PromptRegistry()

    agent = GrammarAgent(llm, registry)

    assert agent.get_agent_name() == "GrammarAgent"


def test_introduce_concept() -> None:
    """Test introducing grammar concept."""
    llm = MockLLM(response="Let me explain gender agreement...")
    registry = PromptRegistry()
    agent = GrammarAgent(llm, registry)

    result = agent.introduce_concept(
        lesson_number=3,
        grammar_topic="Noun-adjective gender agreement",
    )

    assert result == "Let me explain gender agreement..."
    assert llm.last_prompt is not None
    assert "Lesson 3" in llm.last_prompt
    assert "Noun-adjective gender agreement" in llm.last_prompt


def test_detect_error() -> None:
    """Test detecting grammar errors."""
    llm = MockLLM(response="No, that's incorrect! Gender mismatch...")
    registry = PromptRegistry()
    agent = GrammarAgent(llm, registry)

    result = agent.detect_error(
        student_answer="كتاب كبيرة",
        grammar_rule="Gender agreement",
    )

    assert result == "No, that's incorrect! Gender mismatch..."
    assert llm.last_prompt is not None
    assert "كتاب كبيرة" in llm.last_prompt
    assert "Gender agreement" in llm.last_prompt


def test_detect_error_correct_answer() -> None:
    """Test detecting no error when answer is correct."""
    llm = MockLLM(response="Perfect! ✓")
    registry = PromptRegistry()
    agent = GrammarAgent(llm, registry)

    result = agent.detect_error(
        student_answer="كتاب كبير",
        grammar_rule="Gender agreement",
    )

    assert result == "Perfect! ✓"
    assert "كتاب كبير" in llm.last_prompt


def test_generate_practice() -> None:
    """Test generating practice questions."""
    llm = MockLLM(response="Practice question: Is مَدْرَسَة masculine or feminine?")
    registry = PromptRegistry()
    agent = GrammarAgent(llm, registry)

    result = agent.generate_practice(
        grammar_rule="Noun gender",
        vocabulary="كِتَاب, مَدْرَسَة, بَيْت",
    )

    assert result == "Practice question: Is مَدْرَسَة masculine or feminine?"
    assert llm.last_prompt is not None
    assert "Noun gender" in llm.last_prompt
    assert "كِتَاب" in llm.last_prompt


def test_explain_concept() -> None:
    """Test explaining grammar concept."""
    llm = MockLLM(response="Great question! In Arabic, all nouns have gender...")
    registry = PromptRegistry()
    agent = GrammarAgent(llm, registry)

    result = agent.explain_concept(
        student_question="Why does Arabic have gender for objects?",
        grammar_topic="Noun gender",
    )

    assert result == "Great question! In Arabic, all nouns have gender..."
    assert llm.last_prompt is not None
    assert "Why does Arabic have gender for objects?" in llm.last_prompt
    assert "Noun gender" in llm.last_prompt


def test_correct_mistake() -> None:
    """Test correcting grammar mistake."""
    llm = MockLLM(response="Not quite! Gender mismatch...")
    registry = PromptRegistry()
    agent = GrammarAgent(llm, registry)

    result = agent.correct_mistake(
        error_description="Gender mismatch",
        student_answer="كتاب كبيرة",
        correct_answer="كتاب كبير",
    )

    assert result == "Not quite! Gender mismatch..."
    assert llm.last_prompt is not None
    assert "Gender mismatch" in llm.last_prompt
    assert "كتاب كبيرة" in llm.last_prompt
    assert "كتاب كبير" in llm.last_prompt


def test_multiple_calls_different_prompts() -> None:
    """Test that different methods use different prompts."""
    llm = MockLLM()
    registry = PromptRegistry()
    agent = GrammarAgent(llm, registry)

    agent.introduce_concept(1, "topic1")
    intro_prompt = llm.last_prompt

    agent.detect_error("answer", "rule")
    detect_prompt = llm.last_prompt

    agent.generate_practice("rule", "vocab")
    practice_prompt = llm.last_prompt

    assert intro_prompt != detect_prompt
    assert detect_prompt != practice_prompt
    assert llm.call_count == 3
