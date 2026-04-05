"""Tests for vocabulary teaching agent."""

from __future__ import annotations

from prompts.registry import PromptRegistry

from agents.vocabulary_agent import VocabularyAgent


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


def test_vocabulary_agent_initialization() -> None:
    """Test vocabulary agent initialization."""
    llm = MockLLM()
    registry = PromptRegistry()

    agent = VocabularyAgent(llm, registry)

    assert agent.get_agent_name() == "VocabularyAgent"


def test_introduce_words() -> None:
    """Test introducing vocabulary words."""
    llm = MockLLM(response="Let me introduce these words...")
    registry = PromptRegistry()
    agent = VocabularyAgent(llm, registry)

    result = agent.introduce_words(
        lesson_number=3,
        vocabulary_list="كِتَاب (book), مَدْرَسَة (school)",
    )

    assert result == "Let me introduce these words..."
    assert llm.last_prompt is not None
    assert "Lesson 3" in llm.last_prompt
    assert "كِتَاب (book), مَدْرَسَة (school)" in llm.last_prompt


def test_assess_answer() -> None:
    """Test assessing student answer."""
    llm = MockLLM(response="Perfect! ✓")
    registry = PromptRegistry()
    agent = VocabularyAgent(llm, registry)

    result = agent.assess_answer(
        student_answer="كِتَاب",
        correct_answer="كِتَاب (book)",
    )

    assert result == "Perfect! ✓"
    assert llm.last_prompt is not None
    assert "كِتَاب" in llm.last_prompt


def test_correct_error() -> None:
    """Test correcting vocabulary error."""
    llm = MockLLM(response="Close! You're missing the vowel marks...")
    registry = PromptRegistry()
    agent = VocabularyAgent(llm, registry)

    result = agent.correct_error(
        student_answer="كتاب",
        correct_answer="كِتَاب (book)",
    )

    assert result == "Close! You're missing the vowel marks..."
    assert llm.last_prompt is not None
    assert "كتاب" in llm.last_prompt
    assert "كِتَاب" in llm.last_prompt


def test_review_words() -> None:
    """Test reviewing vocabulary."""
    llm = MockLLM(response="Let's review...")
    registry = PromptRegistry()
    agent = VocabularyAgent(llm, registry)

    result = agent.review_words(
        lesson_number=3,
        vocabulary_list="كِتَاب, مَدْرَسَة, بَيْت",
        word_to_test="كِتَاب",
    )

    assert result == "Let's review..."
    assert llm.last_prompt is not None
    assert "Lesson 3" in llm.last_prompt
    assert "كِتَاب" in llm.last_prompt


def test_show_progress() -> None:
    """Test showing progress."""
    llm = MockLLM(response="Great work! You've learned 8 out of 12...")
    registry = PromptRegistry()
    agent = VocabularyAgent(llm, registry)

    result = agent.show_progress(words_learned=8, total_words=12)

    assert result == "Great work! You've learned 8 out of 12..."
    assert llm.last_prompt is not None
    assert "8" in llm.last_prompt
    assert "12" in llm.last_prompt


def test_multiple_calls_different_prompts() -> None:
    """Test that different methods use different prompts."""
    llm = MockLLM()
    registry = PromptRegistry()
    agent = VocabularyAgent(llm, registry)

    agent.introduce_words(1, "word1")
    intro_prompt = llm.last_prompt

    agent.assess_answer("answer", "correct")
    assess_prompt = llm.last_prompt

    assert intro_prompt != assess_prompt
    assert llm.call_count == 2
