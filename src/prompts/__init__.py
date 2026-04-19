"""Prompt templates for the Arabic Teaching Multi-Agent system."""

from .formatters import (
    flatten_nested_input,
    format_answers_list,
    format_examples_list,
    format_learned_items,
    format_topics_list,
    format_words_list,
)
from .templates import (
    # Agent 3: Generation prompts
    EXERCISE_GENERATION,
    FEEDBACK_GRAMMAR_CORRECT,
    FEEDBACK_GRAMMAR_INCORRECT,
    FEEDBACK_VOCAB_CORRECT,
    FEEDBACK_VOCAB_INCORRECT,
    GRADING_GRAMMAR_QUIZ,
    GRADING_GRAMMAR_TEST,
    # Agent 2: Grading prompts
    GRADING_VOCAB,
    GRAMMAR_EXPLANATION,
    GRAMMAR_OVERVIEW,
    GRAMMAR_QUIZ_QUESTION,
    GRAMMAR_TOPIC_SUMMARY,
    # Agent 1: Teaching prompts
    LESSON_WELCOME,
    MODE_EXERCISE_GENERATION,
    MODE_FEEDBACK_GRAMMAR,
    MODE_FEEDBACK_VOCAB,
    MODE_GRADING_GRAMMAR,
    MODE_GRADING_VOCAB,
    # Mode constants
    MODE_LESSON_START,
    MODE_TEACHING_GRAMMAR,
    MODE_TEACHING_VOCAB,
    QUIZ_QUESTION_GENERATION,
    TEST_COMPOSITION,
    VOCAB_BATCH_INTRO,
    VOCAB_BATCH_SUMMARY,
    VOCAB_LIST_VIEW,
    VOCAB_OVERVIEW,
    VOCAB_QUIZ_QUESTION_ARABIC_TO_ENGLISH,
    VOCAB_QUIZ_QUESTION_ENGLISH_TO_ARABIC,
)

__all__ = [
    # Mode constants
    "MODE_LESSON_START",
    "MODE_TEACHING_VOCAB",
    "MODE_TEACHING_GRAMMAR",
    "MODE_FEEDBACK_VOCAB",
    "MODE_FEEDBACK_GRAMMAR",
    "MODE_GRADING_VOCAB",
    "MODE_GRADING_GRAMMAR",
    "MODE_EXERCISE_GENERATION",
    # Formatters
    "flatten_nested_input",
    "format_answers_list",
    "format_examples_list",
    "format_learned_items",
    "format_topics_list",
    "format_words_list",
    # Agent 1
    "LESSON_WELCOME",
    "VOCAB_OVERVIEW",
    "VOCAB_BATCH_INTRO",
    "VOCAB_LIST_VIEW",
    "VOCAB_QUIZ_QUESTION_ARABIC_TO_ENGLISH",
    "VOCAB_QUIZ_QUESTION_ENGLISH_TO_ARABIC",
    "VOCAB_BATCH_SUMMARY",
    "GRAMMAR_OVERVIEW",
    "GRAMMAR_EXPLANATION",
    "GRAMMAR_QUIZ_QUESTION",
    "GRAMMAR_TOPIC_SUMMARY",
    "FEEDBACK_VOCAB_CORRECT",
    "FEEDBACK_VOCAB_INCORRECT",
    "FEEDBACK_GRAMMAR_CORRECT",
    "FEEDBACK_GRAMMAR_INCORRECT",
    # Agent 2
    "GRADING_VOCAB",
    "GRADING_GRAMMAR_QUIZ",
    "GRADING_GRAMMAR_TEST",
    # Agent 3
    "EXERCISE_GENERATION",
    "QUIZ_QUESTION_GENERATION",
    "TEST_COMPOSITION",
]
