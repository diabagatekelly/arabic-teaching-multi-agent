"""Vocabulary teaching agent."""

from __future__ import annotations

from agents.base import BaseAgent


class VocabularyAgent(BaseAgent):
    """Agent for teaching Arabic vocabulary."""

    def get_agent_name(self) -> str:
        """Return agent name."""
        return "VocabularyAgent"

    def introduce_words(self, lesson_number: int, vocabulary_list: str) -> str:
        """
        Introduce new vocabulary words.

        Args:
            lesson_number: Current lesson number
            vocabulary_list: Comma-separated list of words

        Returns:
            Introduction text with words and recall question
        """
        prompt = self._format_prompt(
            "vocab_introduction",
            lesson_number=lesson_number,
            vocabulary_list=vocabulary_list,
        )
        return self._generate(prompt)

    def assess_answer(self, student_answer: str, correct_answer: str) -> str:
        """
        Assess student's vocabulary answer.

        Args:
            student_answer: What the student provided
            correct_answer: Expected answer

        Returns:
            Feedback on correctness
        """
        prompt = self._format_prompt(
            "vocab_assessment",
            student_answer=student_answer,
            correct_answer=correct_answer,
        )
        return self._generate(prompt)

    def correct_error(self, student_answer: str, correct_answer: str) -> str:
        """
        Correct vocabulary mistake with explanation.

        Args:
            student_answer: Student's incorrect answer
            correct_answer: Correct form

        Returns:
            Explanation of error and correction
        """
        prompt = self._format_prompt(
            "vocab_error_correction",
            student_answer=student_answer,
            correct_answer=correct_answer,
        )
        return self._generate(prompt)

    def review_words(
        self,
        lesson_number: int,
        vocabulary_list: str,
        word_to_test: str,
    ) -> str:
        """
        Review vocabulary words.

        Args:
            lesson_number: Current lesson
            vocabulary_list: All words learned
            word_to_test: Specific word to quiz

        Returns:
            Review prompt with quiz question
        """
        prompt = self._format_prompt(
            "vocab_review",
            lesson_number=lesson_number,
            vocabulary_list=vocabulary_list,
            word_to_test=word_to_test,
        )
        return self._generate(prompt)

    def show_progress(self, words_learned: int, total_words: int) -> str:
        """
        Show progress and next step options.

        Args:
            words_learned: Number of words learned
            total_words: Total words in lesson

        Returns:
            Progress summary with options
        """
        prompt = self._format_prompt(
            "vocab_progress",
            words_learned=words_learned,
            total_words=total_words,
        )
        return self._generate(prompt)
