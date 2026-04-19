"""Fixtures for integration tests.

Integration tests use REAL agents with MOCKED LLMs and RAG.
This tests the actual orchestration logic, state management, and agent coordination.
"""

from unittest.mock import MagicMock, Mock

import pytest


# Keep old mock agents for backwards compatibility with existing tests
class MockTeachingAgent:
    """Mock teaching agent for testing orchestrator wiring."""

    def start_lesson(self, input_data):
        """Mock lesson start."""
        lesson_number = input_data.get("lesson_number", 1)
        return f"Welcome to Lesson {lesson_number}! Let's start learning Arabic."

    def handle_teaching_vocab(self, input_data):
        """Mock vocabulary teaching."""
        words = input_data.get("words", [])
        if words:
            word = words[0]
            return f"Let's learn: {word.get('arabic', 'كِتَاب')} ({word.get('transliteration', 'kitaab')}) - {word.get('english', 'book')}"
        return "Let's learn some vocabulary!"

    def handle_teaching_grammar(self, input_data):
        """Mock grammar teaching."""
        topic = input_data.get("grammar_topic", "Feminine Nouns")
        return f"Let's learn about {topic} in Arabic."

    def provide_feedback(self, input_data):
        """Mock feedback."""
        is_correct = input_data.get("is_correct", False)
        if is_correct:
            return "Great job! That's correct."
        else:
            correct_answer = input_data.get("correct_answer", "the correct answer")
            return f"Not quite. The correct answer is: {correct_answer}. Try again!"

    def handle_user_message(self, input_data):
        """Mock general message handling - returns vocab/grammar based on mode."""
        user_input = input_data.get("user_input", "").lower().strip()
        mode = input_data.get("mode", "vocabulary")

        # If user chose vocab or grammar, present content
        if user_input in ["1", "vocab", "vocabulary"] or mode == "teaching_vocab":
            return "Let's learn vocabulary: كِتَاب (kitaab) - book, قَلَم (qalam) - pen"
        elif user_input in ["2", "grammar"] or mode == "teaching_grammar":
            return "Let's learn grammar: Feminine nouns end in ة (taa marbuta)"
        else:
            return f"I heard you say: {user_input}. What would you like to do next?"


class MockGradingAgent:
    """Mock grading agent for testing orchestrator wiring."""

    def grade_answer(self, input_data):
        """Mock grading - returns string like LLM output."""
        user_answer = input_data.get("user_answer", "")
        correct_answer = input_data.get("correct_answer", "")

        # Simple equality check for mock
        is_correct = user_answer.lower().strip() == correct_answer.lower().strip()

        if is_correct:
            return "Correct! Your answer is right."
        else:
            return f"Incorrect. The correct answer is: {correct_answer}"


class MockContentAgent:
    """Mock content agent for testing orchestrator wiring."""

    def get_lesson_content(self, lesson_number, content_type="vocabulary"):
        """Mock content retrieval."""
        if content_type == "vocabulary":
            return {
                "lesson_number": lesson_number,
                "vocabulary": [
                    {"arabic": "كِتَاب", "transliteration": "kitaab", "english": "book"},
                    {"arabic": "قَلَم", "transliteration": "qalam", "english": "pen"},
                    {"arabic": "بَيْت", "transliteration": "bayt", "english": "house"},
                ],
            }
        else:  # grammar
            return {
                "lesson_number": lesson_number,
                "grammar_topics": [
                    {
                        "topic": "Feminine Nouns",
                        "rules": "Nouns ending in ة (taa marbuta) are usually feminine.",
                        "examples": ["مَدْرَسَة (school)", "جَامِعَة (university)"],
                    }
                ],
            }

    def generate_exercise(self, exercise_request):
        """Mock exercise generation - returns string like LLM output."""
        exercise_type = exercise_request.get("exercise_type", "translation")

        if "vocab" in exercise_type or exercise_type == "translation":
            return """```json
{
    "question": "What does كِتَاب mean?",
    "answer": "book",
    "word_arabic": "كِتَاب",
    "exercise_type": "translation"
}
```"""
        else:  # grammar
            return """```json
{
    "question": "Is مَدْرَسَة masculine or feminine?",
    "answer": "feminine",
    "exercise_type": "grammar_quiz"
}
```"""


@pytest.fixture
def mock_teaching_agent():
    """Provide mock teaching agent for testing."""
    return MockTeachingAgent()


@pytest.fixture
def mock_grading_agent():
    """Provide mock grading agent for testing."""
    return MockGradingAgent()


@pytest.fixture
def mock_content_agent():
    """Provide mock content agent for testing."""
    return MockContentAgent()


@pytest.fixture
def orchestrator(mock_teaching_agent, mock_grading_agent, mock_content_agent):
    """Create orchestrator with mock agents (legacy for old tests)."""
    from src.orchestrator.graph import create_teaching_graph

    return create_teaching_graph(
        teaching_agent=mock_teaching_agent,
        grading_agent=mock_grading_agent,
        content_agent=mock_content_agent,
    )


# === NEW: Real agents with mocked LLMs for proper integration testing ===


@pytest.fixture
def mock_llm():
    """Mock LLM that returns realistic teaching responses based on prompt content."""
    mock = MagicMock()

    def smart_response(prompt, **kwargs):
        """Return different responses based on prompt content."""
        prompt_lower = prompt.lower() if isinstance(prompt, str) else ""

        # Debug: Uncomment to see prompts
        # print(f"\n[MOCK LLM CALLED] Prompt preview: {prompt_lower[:400]}...")

        # Check mode header FIRST (most reliable)
        # Lesson start
        if "mode: lesson_start" in prompt_lower or "mode: lesson start" in prompt_lower:
            # print("[MOCK] → Returning LESSON START welcome")
            return "Welcome to Lesson 1! 🌟\n\nToday we'll learn 10 words and 2 grammar topics.\n\nWhat would you like to start with?\n1. Vocabulary (10 words)\n2. Grammar (2 topics)"

        # Vocabulary batch teaching
        elif "mode: teaching vocabulary" in prompt_lower:
            # print("[MOCK] → Returning VOCAB BATCH")
            return "Let's learn Batch 1! Here are your first 3 words:\n\n📝 مَرْحَبا (marhaba) - hello\n📝 كَيْفَ حَالُكَ (kayfa haaluk) - how are you\n📝 اِسْمِي (ismi) - my name is\n\nWhat would you like to do?\n1. Take quiz on this batch\n2. Continue learning"

        # Grammar teaching
        elif "mode: teaching grammar" in prompt_lower:
            # print("[MOCK] → Returning GRAMMAR content")
            return "Let's learn about Gender! In Arabic, nouns are masculine or feminine.\nFeminine nouns typically end in ة (taa marbuuta).\n\nExamples:\n- مَدْرَسَة (madrasa) - school (feminine)\n- كِتَاب (kitaab) - book (masculine)"

        # Exercise generation (ContentAgent) - check for mode header
        elif "mode: exercise_generation" in prompt_lower or (
            "generate" in prompt_lower
            and "exercise" in prompt_lower
            and ("translation" in prompt_lower or "quiz" in prompt_lower)
            and "mode:" not in prompt_lower[:100]
        ):
            # print("[MOCK] → Returning EXERCISE JSON")
            return """```json
{
    "question": "What does مَرْحَبا mean?",
    "answer": "hello",
    "word_arabic": "مَرْحَبا",
    "exercise_type": "translation"
}
```"""

        # Grammar teaching
        elif "teaching grammar" in prompt_lower or (
            "grammar" in prompt_lower and ("rule" in prompt_lower or "topic" in prompt_lower)
        ):
            return "Let's learn about Gender! In Arabic, nouns are masculine or feminine.\nFeminine nouns typically end in ة (taa marbuuta).\n\nExamples:\n- مَدْرَسَة (madrasa) - school (feminine)\n- كِتَاب (kitaab) - book (masculine)"

        # Grading (must return JSON)
        elif (
            "mode: grading" in prompt_lower
            or "grading" in prompt_lower
            or "evaluate" in prompt_lower
        ):
            # print("[MOCK] → Returning GRADING JSON")
            return '{"correct": true}'

        # Feedback (correct)
        elif "mode: feedback" in prompt_lower or (
            "correct" in prompt_lower and "feedback" in prompt_lower
        ):
            # print("[MOCK] → Returning FEEDBACK (correct)")
            return "Correct! ✓ Great job!"

        # Feedback (incorrect)
        elif "incorrect" in prompt_lower or ("feedback" in prompt_lower and "not" in prompt_lower):
            # print("[MOCK] → Returning FEEDBACK (incorrect)")
            return "Not quite. Keep trying!"

        # Default fallback
        else:
            return "I'm here to help you learn Arabic!"

    # Mock both possible method names
    mock.generate.side_effect = smart_response
    mock.generate_response.side_effect = smart_response

    return mock


@pytest.fixture
def mock_tokenizer():
    """Mock tokenizer for testing."""
    tokenizer = MagicMock()
    tokenizer.pad_token_id = 0
    tokenizer.eos_token_id = 1
    tokenizer.apply_chat_template.return_value = "formatted_prompt"
    tokenizer.return_value = {"input_ids": Mock(), "attention_mask": Mock()}
    tokenizer.decode.return_value = "Generated response"
    return tokenizer


@pytest.fixture
def mock_rag_retriever():
    """Mock RAG retriever that returns realistic lesson content."""
    retriever = MagicMock()

    # Mock returns different data based on query type
    def mock_retrieve(query, lesson, top_k):
        if "vocabulary" in query.lower() or "vocab" in query.lower():
            # Return vocabulary data
            # Return ONE document with vocabulary table
            return [
                {
                    "text": """
# Lesson 1 Vocabulary

| Arabic | Transliteration | English |
|--------|----------------|---------|
| مَرْحَبا | marhaba | hello |
| كَيْفَ حَالُكَ | kayfa haaluk | how are you |
| اِسْمِي | ismi | my name is |
| شُكْرًا | shukran | thank you |
| مِنْ فَضْلِكَ | min fadlik | please |
| نَعَمْ | naam | yes |
| لَا | laa | no |
| مَعَ السَّلَامَة | ma'a salama | goodbye |
| صَبَاح الْخَيْر | sabah alkhair | good morning |
| مَسَاء الْخَيْر | masa alkhair | good evening |
            """,
                    "metadata": {"section_title": "Vocabulary", "lesson_number": lesson},
                }
            ]
        elif "grammar" in query.lower():
            # Return grammar data only
            return [
                {
                    "text": """
# Grammar: Gender

Arabic nouns are either masculine or feminine.
Feminine nouns typically end in ة (taa marbuuta).

Examples:
- مَدْرَسَة (madrasa) - school (feminine)
- كِتَاب (kitaab) - book (masculine)
            """,
                    "metadata": {"section_title": "Grammar: Gender", "lesson_number": lesson},
                },
                {
                    "text": """
# Grammar: Definite Article

The definite article in Arabic is ال (al-).
It's attached to the beginning of the noun.

Examples:
- الكِتَاب (al-kitaab) - the book
- المَدْرَسَة (al-madrasa) - the school
            """,
                    "metadata": {
                        "section_title": "Grammar: Definite Article",
                        "lesson_number": lesson,
                    },
                },
            ]
        else:
            return []

    retriever.retrieve_by_lesson.side_effect = mock_retrieve

    return retriever


@pytest.fixture
def mock_content_loader(mock_rag_retriever):
    """Mock content loader with realistic data."""
    from src.rag.lesson_content_loader import LessonContentLoader

    loader = LessonContentLoader(mock_rag_retriever)
    return loader


@pytest.fixture
def real_teaching_agent(mock_llm, mock_tokenizer):
    """Real TeachingAgent with mocked LLM."""
    from src.agents import TeachingAgent

    agent = TeachingAgent(model=mock_llm, tokenizer=mock_tokenizer, max_new_tokens=256)
    return agent


@pytest.fixture
def real_grading_agent(mock_llm, mock_tokenizer):
    """Real GradingAgent with mocked LLM."""
    from src.agents import GradingAgent

    agent = GradingAgent(model=mock_llm, tokenizer=mock_tokenizer, max_new_tokens=50)
    return agent


@pytest.fixture
def real_content_agent(mock_llm, mock_tokenizer, mock_content_loader):
    """Real ContentAgent with mocked LLM and RAG."""
    from src.agents import ContentAgent

    agent = ContentAgent(
        model=mock_llm,
        tokenizer=mock_tokenizer,
        max_new_tokens=512,
        content_loader=mock_content_loader,
    )
    return agent


@pytest.fixture
def real_orchestrator(real_teaching_agent, real_grading_agent, real_content_agent):
    """Orchestrator with REAL agents (mocked LLMs only).

    This is what integration tests should use - tests real orchestration logic.
    """
    from src.orchestrator.graph import create_teaching_graph

    return create_teaching_graph(
        teaching_agent=real_teaching_agent,
        grading_agent=real_grading_agent,
        content_agent=real_content_agent,
    )
