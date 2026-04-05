"""Grammar teaching agent."""

from __future__ import annotations

from agents.base import BaseAgent


class GrammarAgent(BaseAgent):
    """Agent for teaching Arabic grammar."""

    def get_agent_name(self) -> str:
        """Return agent name."""
        return "GrammarAgent"

    def introduce_concept(self, lesson_number: int, grammar_topic: str) -> str:
        """
        Introduce a grammar concept.

        Args:
            lesson_number: Current lesson
            grammar_topic: Grammar rule to teach

        Returns:
            Explanation with examples and check question
        """
        prompt = self._format_prompt(
            "grammar_introduction",
            lesson_number=lesson_number,
            grammar_topic=grammar_topic,
        )
        return self._generate(prompt)

    def detect_error(self, student_answer: str, grammar_rule: str) -> str:
        """
        Detect if student's answer has grammar error.

        Args:
            student_answer: Student's response
            grammar_rule: Applicable grammar rule

        Returns:
            Error detection with reasoning
        """
        prompt = self._format_prompt(
            "grammar_error_detection",
            student_answer=student_answer,
            grammar_rule=grammar_rule,
        )
        return self._generate(prompt)

    def generate_practice(self, grammar_rule: str, vocabulary: str) -> str:
        """
        Generate practice question.

        Args:
            grammar_rule: Rule to practice
            vocabulary: Available vocabulary

        Returns:
            Practice question
        """
        prompt = self._format_prompt(
            "grammar_practice",
            grammar_rule=grammar_rule,
            vocabulary=vocabulary,
        )
        return self._generate(prompt)

    def explain_concept(self, student_question: str, grammar_topic: str) -> str:
        """
        Explain grammar concept in response to question.

        Args:
            student_question: What student asked
            grammar_topic: Related grammar topic

        Returns:
            Clear explanation with reasoning
        """
        prompt = self._format_prompt(
            "grammar_explanation",
            student_question=student_question,
            grammar_topic=grammar_topic,
        )
        return self._generate(prompt)

    def correct_mistake(
        self,
        error_description: str,
        student_answer: str,
        correct_answer: str,
    ) -> str:
        """
        Provide correction for grammar mistake.

        Args:
            error_description: Type of error
            student_answer: Student's incorrect answer
            correct_answer: Correct form

        Returns:
            Corrective feedback
        """
        prompt = self._format_prompt(
            "grammar_correction",
            error_description=error_description,
            student_answer=student_answer,
            correct_answer=correct_answer,
        )
        return self._generate(prompt)
