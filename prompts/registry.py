"""Central registry for all prompt templates."""

from __future__ import annotations

from typing import Any

from prompts.base import PromptTemplate
from prompts.templates import exercise_generator, grammar_teacher, vocabulary_teacher


class PromptRegistry:
    """Registry for managing and accessing prompt templates."""

    def __init__(self) -> None:
        """Initialize the registry."""
        self._templates: dict[str, PromptTemplate] = {}
        self._load_default_templates()

    def _load_default_templates(self) -> None:
        """Load all default prompt templates."""
        vocab_templates = [
            vocabulary_teacher.get_vocab_introduction_prompt(),
            vocabulary_teacher.get_vocab_assessment_prompt(),
            vocabulary_teacher.get_vocab_error_correction_prompt(),
            vocabulary_teacher.get_vocab_review_prompt(),
            vocabulary_teacher.get_vocab_progress_prompt(),
        ]

        grammar_templates = [
            grammar_teacher.get_grammar_introduction_prompt(),
            grammar_teacher.get_grammar_error_detection_prompt(),
            grammar_teacher.get_grammar_practice_prompt(),
            grammar_teacher.get_grammar_explanation_prompt(),
            grammar_teacher.get_grammar_correction_prompt(),
        ]

        exercise_templates = [
            exercise_generator.get_exercise_generation_prompt(),
            exercise_generator.get_exercise_adaptation_prompt(),
            exercise_generator.get_exercise_selection_prompt(),
            exercise_generator.get_exercise_feedback_prompt(),
            exercise_generator.get_exercise_hint_prompt(),
        ]

        all_templates = vocab_templates + grammar_templates + exercise_templates

        for template in all_templates:
            self.register(template)

    def register(self, template: PromptTemplate) -> None:
        """Register a template in the registry."""
        if template.name in self._templates:
            raise ValueError(f"Template '{template.name}' already registered")
        self._templates[template.name] = template

    def get(self, name: str) -> PromptTemplate:
        """Get a template by name."""
        if name not in self._templates:
            raise KeyError(f"Template '{name}' not found in registry")
        return self._templates[name]

    def get_by_category(self, category: str) -> list[PromptTemplate]:
        """Get all templates matching a category prefix."""
        return [t for name, t in self._templates.items() if name.startswith(category)]

    def list_templates(self) -> list[str]:
        """List all registered template names."""
        return sorted(self._templates.keys())

    def format_template(self, name: str, **kwargs: Any) -> str:
        """Get and format a template in one call."""
        template = self.get(name)
        return template.format(**kwargs)


_global_registry: PromptRegistry | None = None


def get_registry() -> PromptRegistry:
    """Get the global prompt registry singleton."""
    global _global_registry
    if _global_registry is None:
        _global_registry = PromptRegistry()
    return _global_registry
