"""
Helper functions to format structured data for prompt templates.

These functions transform structured data (from agents, evaluation, or any source) into
formatted strings that LangChain PromptTemplate can use. This bridges the gap between
natural data structures (lists, nested objects) and simple string substitution.

Used by:
- Production agents (formatting lesson content, user responses)
- Evaluation pipeline (preparing test cases)
- Baseline evaluator (generating outputs for comparison)
"""

from collections.abc import Callable
from typing import Any


def format_words_list(words: list[dict[str, str]]) -> str:
    """
    Format list of word objects into numbered list with Arabic, transliteration, and English.

    Args:
        words: List of dicts with 'arabic', 'transliteration', 'english' keys

    Returns:
        Formatted string like:
        "1. كِتَاب (kitaab) - book
         2. قَلَم (qalam) - pen"

    Example:
        >>> words = [
        ...     {"arabic": "كِتَاب", "transliteration": "kitaab", "english": "book"},
        ...     {"arabic": "قَلَم", "transliteration": "qalam", "english": "pen"}
        ... ]
        >>> print(format_words_list(words))
        1. كِتَاب (kitaab) - book
        2. قَلَم (qalam) - pen
    """
    return "\n".join(
        f"{i}. {w['arabic']} ({w['transliteration']}) - {w['english']}"
        for i, w in enumerate(words, 1)
    )


def format_examples_list(examples: list[dict[str, str]]) -> str:
    """
    Format list of grammar example objects into bulleted list with notes.

    Args:
        examples: List of dicts with 'arabic', 'transliteration', 'english', 'note' keys

    Returns:
        Formatted string like:
        "- مَدْرَسَة (madrasa) - school
           Note: Ends with ة so it's feminine
         - كِتَاب (kitaab) - book
           Note: No ة ending, so it's masculine"

    Example:
        >>> examples = [
        ...     {
        ...         "arabic": "مَدْرَسَة",
        ...         "transliteration": "madrasa",
        ...         "english": "school",
        ...         "note": "Ends with ة so it's feminine"
        ...     }
        ... ]
        >>> print(format_examples_list(examples))
        - مَدْرَسَة (madrasa) - school
          Note: Ends with ة so it's feminine
    """
    lines = []
    for example in examples:
        line = f"- {example['arabic']} ({example['transliteration']}) - {example['english']}"
        lines.append(line)
        if "note" in example:
            lines.append(f"  Note: {example['note']}")
    return "\n".join(lines)


def format_answers_list(answers: list[dict[str, str]]) -> str:
    """
    Format list of answer objects for grammar test grading.

    Args:
        answers: List of dicts with 'question_id', 'question', 'student_answer', 'correct_answer'

    Returns:
        Formatted string like:
        "Question 1 (ID: q1):
         Q: Is مَدْرَسَة masculine or feminine?
         Student: 'feminine'
         Correct: 'feminine'

         Question 2 (ID: q2):
         Q: Is كِتَاب masculine or feminine?
         Student: 'feminine'
         Correct: 'masculine'"

    Example:
        >>> answers = [
        ...     {
        ...         "question_id": "q1",
        ...         "question": "Is مَدْرَسَة masculine or feminine?",
        ...         "student_answer": "feminine",
        ...         "correct_answer": "feminine"
        ...     }
        ... ]
        >>> print(format_answers_list(answers))
        Question 1 (ID: q1):
        Q: Is مَدْرَسَة masculine or feminine?
        Student: "feminine"
        Correct: "feminine"
    """
    blocks = []
    for i, answer in enumerate(answers, 1):
        block = [
            f"Question {i} (ID: {answer['question_id']}):",
            f"Q: {answer['question']}",
            f'Student: "{answer["student_answer"]}"',
            f'Correct: "{answer["correct_answer"]}"',
        ]
        blocks.append("\n".join(block))
    return "\n\n".join(blocks)


def _format_bulleted_list(items: list[str]) -> str:
    """Format list of strings into bulleted list."""
    return "\n".join(f"- {item}" for item in items)


def format_topics_list(topics: list[str]) -> str:
    """
    Format list of topic names into bulleted list.

    Args:
        topics: List of topic name strings

    Returns:
        Formatted string like:
        "- Feminine Nouns
         - Definite Article"

    Example:
        >>> topics = ["Feminine Nouns", "Definite Article"]
        >>> print(format_topics_list(topics))
        - Feminine Nouns
        - Definite Article
    """
    return _format_bulleted_list(topics)


def format_learned_items(items: list[str]) -> str:
    """
    Format list of learned items (words or phrases) into bulleted list.

    Args:
        items: List of learned item strings (can include transliteration and translation)

    Returns:
        Formatted string like:
        "- مرحبا (marhaba) - hello
         - شكرا (shukran) - thank you"

    Example:
        >>> items = ["مرحبا (marhaba) - hello", "شكرا (shukran) - thank you"]
        >>> print(format_learned_items(items))
        - مرحبا (marhaba) - hello
        - شكرا (shukran) - thank you
    """
    return _format_bulleted_list(items)


def _flatten_vocab_summary(input_data: dict[str, Any], flattened: dict[str, Any]) -> None:
    """Extract and flatten vocab_summary fields."""
    if vocab := input_data.get("vocab_summary"):
        if "total_words" in vocab:
            flattened["total_words"] = vocab["total_words"]
        if "topics_preview" in vocab:
            flattened["topics_preview"] = ", ".join(vocab["topics_preview"])


def _flatten_grammar_summary(input_data: dict[str, Any], flattened: dict[str, Any]) -> None:
    """Extract and flatten grammar_summary fields."""
    if grammar := input_data.get("grammar_summary"):
        if "topics_count" in grammar:
            flattened["topics_count"] = grammar["topics_count"]
        if "topics" in grammar:
            flattened["grammar_topics"] = ", ".join(grammar["topics"])


def _format_list_fields(input_data: dict[str, Any], flattened: dict[str, Any]) -> None:
    """Format list fields using their corresponding formatters."""
    list_formatters: dict[str, Callable[[list], str]] = {
        "words": format_words_list,
        "examples": format_examples_list,
        "answers": format_answers_list,
        "learned_items": format_learned_items,
        "grammar_topics": format_topics_list,
    }

    for field, formatter in list_formatters.items():
        if (value := input_data.get(field)) and isinstance(value, list):
            # Special case: words needs both original and formatted
            if field == "words":
                flattened["words"] = value
            flattened[f"{field}_formatted"] = formatter(value)


def flatten_nested_input(input_data: dict[str, Any]) -> dict[str, Any]:
    """
    Flatten nested input data into template-ready variables.

    Handles common nesting patterns like vocab_summary and grammar_summary.
    Converts structured data (lists, nested dicts) into flat key-value pairs
    with formatted string values ready for LangChain PromptTemplate.format().

    Args:
        input_data: Nested input dictionary (from agents, evaluation, or any source)

    Returns:
        Flattened dictionary with formatted string variables

    Example:
        >>> input_data = {
        ...     "lesson_number": 1,
        ...     "vocab_summary": {
        ...         "total_words": 10,
        ...         "topics_preview": ["word1", "word2"]
        ...     },
        ...     "grammar_summary": {
        ...         "topics": ["Topic 1", "Topic 2"],
        ...         "topics_count": 2
        ...     }
        ... }
        >>> result = flatten_nested_input(input_data)
        >>> result["lesson_number"]
        1
        >>> result["total_words"]
        10
        >>> result["topics_count"]
        2
    """
    flattened = {}

    # Copy top-level scalars (non-dict values)
    for key, value in input_data.items():
        if not isinstance(value, dict):
            flattened[key] = value

    # Flatten vocab_summary
    _flatten_vocab_summary(input_data, flattened)

    # Flatten grammar_summary
    _flatten_grammar_summary(input_data, flattened)

    # Format lists with data-driven approach
    _format_list_fields(input_data, flattened)

    return flattened
