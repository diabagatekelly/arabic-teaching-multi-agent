"""Tests for prompt formatting helper functions."""

import pytest

from src.prompts.formatters import (
    flatten_nested_input,
    format_answers_list,
    format_examples_list,
    format_learned_items,
    format_topics_list,
    format_words_list,
)


@pytest.mark.parametrize(
    "formatter,empty_input,expected",
    [
        (format_words_list, [], ""),
        (format_examples_list, [], ""),
        (format_answers_list, [], ""),
        (format_topics_list, [], ""),
        (format_learned_items, [], ""),
        (flatten_nested_input, {}, {}),
    ],
)
def test_formatters_handle_empty_input(formatter, empty_input, expected) -> None:
    """All formatters return empty output for empty input."""
    result = formatter(empty_input)
    assert result == expected


def test_format_words_list() -> None:
    """Test formatting list of words into numbered list."""
    words = [
        {"arabic": "كِتَاب", "transliteration": "kitaab", "english": "book"},
        {"arabic": "قَلَم", "transliteration": "qalam", "english": "pen"},
    ]

    result = format_words_list(words)

    assert "1. كِتَاب (kitaab) - book" in result
    assert "2. قَلَم (qalam) - pen" in result
    assert result.count("\n") == 1  # Two lines, one newline


def test_format_examples_list() -> None:
    """Test formatting list of grammar examples."""
    examples = [
        {
            "arabic": "مَدْرَسَة",
            "transliteration": "madrasa",
            "english": "school",
            "note": "Ends with ة",
        },
        {
            "arabic": "كِتَاب",
            "transliteration": "kitaab",
            "english": "book",
            "note": "No ة ending",
        },
    ]

    result = format_examples_list(examples)

    assert "- مَدْرَسَة (madrasa) - school" in result
    assert "Note: Ends with ة" in result
    assert "- كِتَاب (kitaab) - book" in result
    assert "Note: No ة ending" in result


def test_format_answers_list() -> None:
    """Test formatting list of answers for grading."""
    answers = [
        {
            "question_id": "q1",
            "question": "Is مَدْرَسَة masculine or feminine?",
            "student_answer": "feminine",
            "correct_answer": "feminine",
        },
        {
            "question_id": "q2",
            "question": "Is كِتَاب masculine or feminine?",
            "student_answer": "feminine",
            "correct_answer": "masculine",
        },
    ]

    result = format_answers_list(answers)

    assert "Question 1 (ID: q1):" in result
    assert 'Student: "feminine"' in result
    assert "Question 2 (ID: q2):" in result
    assert 'Correct: "masculine"' in result


def test_format_topics_list() -> None:
    """Test formatting list of topics."""
    topics = ["Feminine Nouns", "Definite Article"]

    result = format_topics_list(topics)

    assert result == "- Feminine Nouns\n- Definite Article"


def test_format_learned_items() -> None:
    """Test formatting list of learned items."""
    items = ["مرحبا (marhaba) - hello", "شكرا (shukran) - thank you"]

    result = format_learned_items(items)

    assert result == "- مرحبا (marhaba) - hello\n- شكرا (shukran) - thank you"


def test_flatten_nested_input() -> None:
    """Test flattening nested input structure."""
    input_data = {
        "mode": "lesson_start",
        "lesson_number": 1,
        "vocab_summary": {
            "total_words": 10,
            "topics_preview": ["كِتَاب (book)", "قَلَم (pen)"],
        },
        "grammar_summary": {"topics": ["Feminine Nouns", "Definite Article"], "topics_count": 2},
    }

    result = flatten_nested_input(input_data)

    # Check flattened values
    assert result["lesson_number"] == 1
    assert result["total_words"] == 10
    assert result["topics_count"] == 2
    assert "كِتَاب (book)" in result["topics_preview"]
    assert "Feminine Nouns" in result["grammar_topics"]
    # Original nested structures should not be in flattened result
    assert "vocab_summary" not in result
    assert "grammar_summary" not in result


def test_flatten_nested_input_with_words() -> None:
    """Test flattening input with words list."""
    input_data = {
        "lesson_number": 1,
        "batch_number": 1,
        "total_batches": 3,
        "words": [
            {"arabic": "كِتَاب", "transliteration": "kitaab", "english": "book"},
            {"arabic": "قَلَم", "transliteration": "qalam", "english": "pen"},
        ],
    }

    result = flatten_nested_input(input_data)

    # Should have both original and formatted versions
    assert "words" in result
    assert "words_formatted" in result
    assert isinstance(result["words"], list)
    assert isinstance(result["words_formatted"], str)
    assert "1. كِتَاب (kitaab) - book" in result["words_formatted"]


def test_format_words_list_single() -> None:
    """Single word should be numbered as 1."""
    words = [{"arabic": "كِتَاب", "transliteration": "kitaab", "english": "book"}]
    result = format_words_list(words)
    assert result == "1. كِتَاب (kitaab) - book"
    assert "\n" not in result


def test_format_examples_list_without_note() -> None:
    """Examples without note field should work."""
    examples = [
        {"arabic": "كِتَاب", "transliteration": "kitaab", "english": "book"},
        {"arabic": "قَلَم", "transliteration": "qalam", "english": "pen"},
    ]
    result = format_examples_list(examples)
    assert "- كِتَاب (kitaab) - book" in result
    assert "- قَلَم (qalam) - pen" in result
    assert "Note:" not in result


def test_format_examples_list_mixed_notes() -> None:
    """Examples with some having notes and some not."""
    examples = [
        {
            "arabic": "مَدْرَسَة",
            "transliteration": "madrasa",
            "english": "school",
            "note": "Feminine",
        },
        {"arabic": "كِتَاب", "transliteration": "kitaab", "english": "book"},
    ]
    result = format_examples_list(examples)
    assert "Note: Feminine" in result
    lines = result.split("\n")
    assert len(lines) == 3


def test_format_answers_list_single() -> None:
    """Single answer should have no trailing blank line."""
    answers = [
        {
            "question_id": "q1",
            "question": "Is مَدْرَسَة masculine or feminine?",
            "student_answer": "feminine",
            "correct_answer": "feminine",
        }
    ]
    result = format_answers_list(answers)
    assert "Question 1 (ID: q1):" in result
    assert not result.endswith("\n\n")
    lines = result.split("\n")
    assert len(lines) == 4


def test_format_topics_list_single() -> None:
    """Single topic should format correctly."""
    topics = ["Feminine Nouns"]
    result = format_topics_list(topics)
    assert result == "- Feminine Nouns"


def test_flatten_nested_input_with_all_fields() -> None:
    """Test all supported list fields get formatted."""
    input_data = {
        "lesson_number": 1,
        "words": [{"arabic": "كِتَاب", "transliteration": "kitaab", "english": "book"}],
        "examples": [
            {"arabic": "مَدْرَسَة", "transliteration": "madrasa", "english": "school", "note": "Test"}
        ],
        "answers": [
            {
                "question_id": "q1",
                "question": "Test?",
                "student_answer": "answer",
                "correct_answer": "answer",
            }
        ],
        "learned_items": ["مرحبا (marhaba) - hello"],
        "grammar_topics": ["Feminine Nouns"],
    }

    result = flatten_nested_input(input_data)

    assert "words_formatted" in result
    assert "examples_formatted" in result
    assert "answers_formatted" in result
    assert "learned_items_formatted" in result
    assert "grammar_topics_formatted" in result
    assert "1. كِتَاب (kitaab) - book" in result["words_formatted"]
    assert "Question 1" in result["answers_formatted"]


def test_flatten_nested_input_missing_optional_keys() -> None:
    """vocab_summary and grammar_summary with missing optional keys."""
    input_data = {
        "vocab_summary": {"total_words": 5},
        "grammar_summary": {"topics_count": 2},
    }

    result = flatten_nested_input(input_data)

    assert result["total_words"] == 5
    assert result["topics_count"] == 2
    assert "topics_preview" not in result
    assert "grammar_topics" not in result


def test_flatten_nested_input_only_top_level() -> None:
    """Input with only top-level scalar values."""
    input_data = {"lesson_number": 1, "mode": "test", "student_name": "Ahmed"}

    result = flatten_nested_input(input_data)

    assert result["lesson_number"] == 1
    assert result["mode"] == "test"
    assert result["student_name"] == "Ahmed"
