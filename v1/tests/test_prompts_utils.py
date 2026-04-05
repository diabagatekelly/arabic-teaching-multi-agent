"""Tests for prompt utility functions."""

from __future__ import annotations

import pytest
from prompts.utils import (
    add_thinking_prompt,
    clean_whitespace,
    create_multiple_choice,
    extract_variables,
    format_arabic_text,
    format_examples,
    format_list,
    truncate_text,
    validate_template_variables,
)


def test_truncate_text_no_truncation() -> None:
    """Test text shorter than max length is not truncated."""
    text = "Short text"
    result = truncate_text(text, max_length=20)
    assert result == "Short text"


def test_truncate_text_with_truncation() -> None:
    """Test long text is truncated."""
    text = "This is a very long text that needs to be truncated"
    result = truncate_text(text, max_length=20)
    assert len(result) == 20
    assert result.endswith("...")


def test_truncate_text_custom_suffix() -> None:
    """Test truncation with custom suffix."""
    text = "This is a very long text"
    result = truncate_text(text, max_length=15, suffix=" [...]")
    assert len(result) == 15
    assert result.endswith(" [...]")


def test_format_list_bullets() -> None:
    """Test formatting list as bullets."""
    items = ["apple", "banana", "cherry"]
    result = format_list(items, style="bullets")
    assert result == "- apple\n- banana\n- cherry"


def test_format_list_numbers() -> None:
    """Test formatting list as numbered."""
    items = ["first", "second", "third"]
    result = format_list(items, style="numbers")
    assert result == "1. first\n2. second\n3. third"


def test_format_list_comma() -> None:
    """Test formatting list as comma-separated."""
    items = ["apple", "banana", "cherry"]
    result = format_list(items, style="comma")
    assert result == "apple, banana, cherry"


def test_format_list_invalid_style() -> None:
    """Test invalid style raises error."""
    with pytest.raises(ValueError, match="Unknown style"):
        format_list(["a", "b"], style="invalid")


def test_format_examples_with_index() -> None:
    """Test formatting examples with index."""
    examples = [
        {"Input": "hello", "Output": "bonjour"},
        {"Input": "goodbye", "Output": "au revoir"},
    ]
    result = format_examples(examples, include_index=True)

    assert "Example 1:" in result
    assert "Input: hello" in result
    assert "Example 2:" in result


def test_format_examples_without_index() -> None:
    """Test formatting examples without index."""
    examples = [{"Input": "hello", "Output": "bonjour"}]
    result = format_examples(examples, include_index=False)

    assert "Example 1:" not in result
    assert "Input: hello" in result
    assert "Output: bonjour" in result


def test_format_examples_custom_separator() -> None:
    """Test formatting examples with custom separator."""
    examples = [
        {"Input": "a"},
        {"Input": "b"},
    ]
    result = format_examples(examples, separator="\n---\n")

    assert "\n---\n" in result


def test_clean_whitespace() -> None:
    """Test cleaning excessive whitespace."""
    text = "This  has   multiple    spaces\n\n\nand\n\n\nnewlines  "
    result = clean_whitespace(text)

    assert "  " not in result
    assert "\n\n\n" not in result
    assert result == "This has multiple spaces\n\nand\n\nnewlines"


def test_extract_variables() -> None:
    """Test extracting variables from template."""
    template = "Hello {name}, you are {age} years old. Welcome {name}!"
    result = extract_variables(template)

    assert set(result) == {"name", "age"}


def test_extract_variables_no_variables() -> None:
    """Test extracting from template with no variables."""
    template = "No variables here"
    result = extract_variables(template)

    assert result == []


def test_validate_template_variables_valid() -> None:
    """Test validation passes with all variables provided."""
    template = "Hello {name}"
    is_valid, missing = validate_template_variables(template, {"name": "Alice"})

    assert is_valid is True
    assert missing == []


def test_validate_template_variables_missing() -> None:
    """Test validation fails with missing variables."""
    template = "Hello {name}, age {age}"
    is_valid, missing = validate_template_variables(template, {"name": "Alice"})

    assert is_valid is False
    assert "age" in missing


def test_format_arabic_text_with_transliteration() -> None:
    """Test formatting Arabic with transliteration."""
    result = format_arabic_text(
        "كِتَاب",
        include_transliteration=True,
        transliteration="kitaab",
    )

    assert result == "كِتَاب (kitaab)"


def test_format_arabic_text_without_transliteration() -> None:
    """Test formatting Arabic without transliteration."""
    result = format_arabic_text("كِتَاب", include_transliteration=False)

    assert result == "كِتَاب"


def test_format_arabic_text_no_transliteration_provided() -> None:
    """Test formatting with no transliteration provided."""
    result = format_arabic_text(
        "كِتَاب",
        include_transliteration=True,
        transliteration=None,
    )

    assert result == "كِتَاب"


def test_create_multiple_choice() -> None:
    """Test creating multiple choice question."""
    result = create_multiple_choice(
        question="What is 2+2?",
        options=["3", "4", "5"],
        correct_index=1,
    )

    assert "What is 2+2?" in result
    assert "A) 3" in result
    assert "B) 4" in result
    assert "C) 5" in result


def test_create_multiple_choice_custom_labels() -> None:
    """Test multiple choice with custom labels."""
    result = create_multiple_choice(
        question="Pick one:",
        options=["opt1", "opt2"],
        correct_index=0,
        labels=["1", "2"],
    )

    assert "1) opt1" in result
    assert "2) opt2" in result


def test_create_multiple_choice_mismatched_labels() -> None:
    """Test multiple choice with mismatched labels raises error."""
    with pytest.raises(ValueError, match="Number of labels"):
        create_multiple_choice(
            question="Pick:",
            options=["a", "b", "c"],
            correct_index=0,
            labels=["1", "2"],
        )


def test_add_thinking_prompt() -> None:
    """Test adding thinking prompt."""
    prompt = "Solve this problem"
    result = add_thinking_prompt(prompt)

    assert "Solve this problem" in result
    assert "Let's think step by step:" in result


def test_add_thinking_prompt_custom() -> None:
    """Test adding custom thinking prompt."""
    prompt = "Calculate"
    result = add_thinking_prompt(prompt, thinking_text="Step-by-step:")

    assert "Step-by-step:" in result
