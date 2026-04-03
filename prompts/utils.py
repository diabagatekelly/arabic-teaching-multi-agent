"""Utility functions for prompt formatting and validation."""

from __future__ import annotations

import re
from typing import Any


def truncate_text(text: str, max_length: int, suffix: str = "...") -> str:
    """
    Truncate text to maximum length.

    Args:
        text: Text to truncate
        max_length: Maximum length (including suffix)
        suffix: Suffix to add when truncated

    Returns:
        Truncated text
    """
    if len(text) <= max_length:
        return text

    return text[: max_length - len(suffix)] + suffix


def format_list(items: list[str], style: str = "bullets") -> str:
    """
    Format a list of items.

    Args:
        items: List of items to format
        style: "bullets", "numbers", or "comma"

    Returns:
        Formatted list string
    """
    if style == "bullets":
        return "\n".join(f"- {item}" for item in items)
    elif style == "numbers":
        return "\n".join(f"{i}. {item}" for i, item in enumerate(items, 1))
    elif style == "comma":
        return ", ".join(items)
    else:
        raise ValueError(f"Unknown style: {style}")


def format_examples(
    examples: list[dict[str, str]],
    include_index: bool = True,
    separator: str = "\n\n",
) -> str:
    """
    Format few-shot examples.

    Args:
        examples: List of example dicts
        include_index: Whether to number examples
        separator: Separator between examples

    Returns:
        Formatted examples string
    """
    formatted = []

    for i, example in enumerate(examples, 1):
        parts = []
        if include_index:
            parts.append(f"Example {i}:")

        for key, value in example.items():
            parts.append(f"{key}: {value}")

        formatted.append("\n".join(parts))

    return separator.join(formatted)


def clean_whitespace(text: str) -> str:
    """
    Clean excessive whitespace from text.

    Args:
        text: Text to clean

    Returns:
        Cleaned text
    """
    text = re.sub(r" +", " ", text)
    text = re.sub(r"\n\n+", "\n\n", text)
    text = text.strip()

    return text


def extract_variables(template: str) -> list[str]:
    """
    Extract variable names from template string.

    Args:
        template: Template with {variables}

    Returns:
        List of unique variable names
    """
    matches = re.findall(r"\{(\w+)\}", template)
    return list(set(matches))


def validate_template_variables(
    template: str,
    provided_vars: dict[str, Any],
) -> tuple[bool, list[str]]:
    """
    Validate that all template variables are provided.

    Args:
        template: Template string
        provided_vars: Dict of provided variables

    Returns:
        Tuple of (is_valid, missing_variables)
    """
    required = set(extract_variables(template))
    provided = set(provided_vars.keys())
    missing = required - provided

    return len(missing) == 0, list(missing)


def format_arabic_text(
    text: str,
    include_transliteration: bool = True,
    transliteration: str | None = None,
) -> str:
    """
    Format Arabic text with optional transliteration.

    Args:
        text: Arabic text
        include_transliteration: Whether to include transliteration
        transliteration: Transliteration string

    Returns:
        Formatted text
    """
    if include_transliteration and transliteration:
        return f"{text} ({transliteration})"
    return text


def create_multiple_choice(
    question: str,
    options: list[str],
    correct_index: int,
    labels: list[str] | None = None,
) -> str:
    """
    Create a formatted multiple choice question.

    Args:
        question: Question text
        options: List of option strings
        correct_index: Index of correct answer (0-based)
        labels: Custom labels (default: A, B, C, D)

    Returns:
        Formatted question string
    """
    if labels is None:
        labels = [chr(65 + i) for i in range(len(options))]

    if len(labels) != len(options):
        raise ValueError("Number of labels must match number of options")

    parts = [question, ""]

    for label, option in zip(labels, options, strict=True):
        parts.append(f"{label}) {option}")

    return "\n".join(parts)


def add_thinking_prompt(prompt: str, thinking_text: str = "Let's think step by step:") -> str:
    """
    Add chain-of-thought thinking prompt.

    Args:
        prompt: Original prompt
        thinking_text: Thinking prompt text

    Returns:
        Prompt with thinking trigger
    """
    return f"{prompt}\n\n{thinking_text}"
