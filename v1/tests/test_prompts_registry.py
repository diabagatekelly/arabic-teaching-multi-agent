"""Tests for prompt registry."""

from __future__ import annotations

import pytest
from prompts.base import SimplePromptTemplate
from prompts.registry import PromptRegistry, get_registry


def test_registry_initialization() -> None:
    """Test registry initializes with default templates."""
    registry = PromptRegistry()

    templates = registry.list_templates()

    assert len(templates) > 0
    assert "vocab_introduction" in templates
    assert "grammar_introduction" in templates
    assert "exercise_generation" in templates


def test_registry_register_template() -> None:
    """Test registering a new template."""
    registry = PromptRegistry()

    template = SimplePromptTemplate(
        name="test_template",
        description="Test",
        template="Test {var}",
    )

    registry.register(template)

    assert "test_template" in registry.list_templates()


def test_registry_register_duplicate_raises_error() -> None:
    """Test registering duplicate template raises error."""
    registry = PromptRegistry()

    template1 = SimplePromptTemplate(
        name="duplicate",
        description="Test",
        template="Test 1",
    )
    template2 = SimplePromptTemplate(
        name="duplicate",
        description="Test",
        template="Test 2",
    )

    registry.register(template1)

    with pytest.raises(ValueError, match="already registered"):
        registry.register(template2)


def test_registry_get_template() -> None:
    """Test getting a template by name."""
    registry = PromptRegistry()

    template = registry.get("vocab_introduction")

    assert template.name == "vocab_introduction"
    assert template.description != ""


def test_registry_get_nonexistent_template_raises_error() -> None:
    """Test getting nonexistent template raises error."""
    registry = PromptRegistry()

    with pytest.raises(KeyError, match="not found"):
        registry.get("nonexistent_template")


def test_registry_get_by_category() -> None:
    """Test getting templates by category."""
    registry = PromptRegistry()

    vocab_templates = registry.get_by_category("vocab")

    assert len(vocab_templates) > 0
    assert all(t.name.startswith("vocab") for t in vocab_templates)


def test_registry_format_template() -> None:
    """Test formatting template through registry."""
    registry = PromptRegistry()

    template = SimplePromptTemplate(
        name="test_format",
        description="Test",
        template="Hello {user}",
    )
    registry.register(template)

    result = registry.format_template("test_format", user="World")

    assert result == "Hello World"


def test_get_registry_singleton() -> None:
    """Test global registry is a singleton."""
    registry1 = get_registry()
    registry2 = get_registry()

    assert registry1 is registry2


def test_list_templates_sorted() -> None:
    """Test template list is sorted."""
    registry = PromptRegistry()

    templates = registry.list_templates()

    assert templates == sorted(templates)
