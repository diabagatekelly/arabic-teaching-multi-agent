"""Evaluation metrics for Agent 1 (Teaching Agent)."""

import logging
import re

from deepeval.metrics import BaseMetric
from deepeval.test_case import LLMTestCase
from transformers import pipeline

logger = logging.getLogger(__name__)


class SentimentMetric(BaseMetric):
    """
    Evaluates sentiment score for Agent 1 (Teaching) responses.

    Target: >0.6 for teaching mode, >0.8 for feedback mode.
    """

    # Class-level singleton: shared sentiment pipeline across all instances
    _shared_sentiment_pipeline = None

    def __init__(self, threshold: float = 0.9, mode: str = "teaching") -> None:
        """
        Initialize sentiment metric.

        Args:
            threshold: Minimum sentiment score required
            mode: "teaching" (0.6) or "feedback" (0.8)
        """
        self.threshold = threshold
        self.mode = mode
        self.score = 0.0
        self.reason = ""
        self.success = False

        # Load sentiment pipeline once at class level (singleton pattern)
        if SentimentMetric._shared_sentiment_pipeline is None:
            logger.info("Loading sentiment analysis model (first time)...")
            SentimentMetric._shared_sentiment_pipeline = pipeline(
                "sentiment-analysis",
                model="distilbert-base-uncased-finetuned-sst-2-english",
            )
            logger.info("Sentiment model loaded and cached")

    def measure(self, test_case: LLMTestCase) -> float:
        """
        Measure sentiment score using transformers sentiment pipeline.

        Args:
            test_case: Test case with actual_output to analyze

        Returns:
            Sentiment score (0-1, where 1 is most positive)
        """
        try:
            # Use class-level shared sentiment pipeline (singleton)
            result = SentimentMetric._shared_sentiment_pipeline(test_case.actual_output)[0]

            # Convert to 0-1 scale (positive sentiment)
            if result["label"] == "POSITIVE":
                self.score = result["score"]
            else:
                self.score = 1.0 - result["score"]

            self.success = self.score >= self.threshold
            self.reason = f"Sentiment score: {self.score:.3f} ({'✓' if self.success else '✗'} threshold: {self.threshold})"

            return self.score

        except Exception as e:
            self.score = 0.0
            self.success = False
            self.reason = f"Sentiment analysis failed: {str(e)}"
            logger.error(f"Sentiment analysis error: {e}")
            return 0.0

    def is_successful(self) -> bool:
        """Check if metric passed threshold."""
        return self.success

    @property
    def __name__(self) -> str:
        """Metric name."""
        return f"Sentiment ({self.mode})"


class FeedbackAppropriatenessMetric(BaseMetric):
    """
    Validates that feedback matches correctness.

    For correct answers: Must contain praise and confirm correctness.
    For incorrect answers: Must be supportive with correction, NO false praise.

    Used by: feedback_vocab, feedback_grammar modes
    """

    # Praise keywords that indicate positive reinforcement
    PRAISE_KEYWORDS = [
        "perfect",
        "correct",
        "excellent",
        "great job",
        "well done",
        "good job",
        "nice work",
        "fantastic",
        "wonderful",
        "amazing",
    ]

    # Supportive keywords that indicate encouragement
    SUPPORTIVE_KEYWORDS = [
        "not quite",
        "almost",
        "close",
        "great effort",
        "keep trying",
        "keep practicing",
        "learning",
        "progress",
    ]

    def __init__(self, is_correct: bool, correct_answer: str | None = None) -> None:
        """
        Initialize feedback appropriateness metric.

        Args:
            is_correct: Whether the student's answer was correct
            correct_answer: The correct answer (for incorrect responses)
        """
        self.is_correct = is_correct
        self.correct_answer = correct_answer
        self.score = 0.0
        self.reason = ""
        self.success = False

    def measure(self, test_case: LLMTestCase) -> float:
        """
        Check if feedback is appropriate for correctness.

        Args:
            test_case: Test case with actual_output (feedback text)

        Returns:
            1.0 if appropriate, 0.0 otherwise
        """
        try:
            output = test_case.actual_output.lower()

            if self.is_correct:
                return self._validate_correct_feedback(output)
            else:
                return self._validate_incorrect_feedback(output)

        except Exception as e:
            return self._set_error(f"Feedback appropriateness check error: {str(e)}")

    def _validate_correct_feedback(self, output: str) -> float:
        """Validate feedback for correct answers (must have praise and confirmation)."""
        has_praise = any(keyword in output for keyword in self.PRAISE_KEYWORDS)
        confirms_correct = any(word in output for word in ["correct", "right", "yes", "✓"])

        if has_praise and confirms_correct:
            return self._set_success("Appropriate praise for correct answer")
        elif has_praise:
            return self._set_partial("Has praise but doesn't clearly confirm correctness")
        else:
            return self._set_failure("Missing praise for correct answer")

    def _validate_incorrect_feedback(self, output: str) -> float:
        """Validate feedback for incorrect answers (supportive with correction, no false praise)."""
        correction_phrases = ["correct answer is", "right answer is", "answer is"]
        has_correction_phrase = any(phrase in output for phrase in correction_phrases)

        has_false_praise = (
            any(keyword in output for keyword in self.PRAISE_KEYWORDS) and not has_correction_phrase
        )

        if has_false_praise:
            return self._set_failure("Gives false praise for incorrect answer")

        is_supportive = any(keyword in output for keyword in self.SUPPORTIVE_KEYWORDS)
        shows_correction = self.correct_answer and self.correct_answer.lower() in output

        if is_supportive and shows_correction:
            return self._set_success("Appropriate supportive correction")
        elif shows_correction:
            return self._set_partial("Shows correction but could be more supportive")
        else:
            return self._set_failure("Doesn't show correct answer or provide correction")

    def _set_success(self, reason: str) -> float:
        """Set success state."""
        self.score = 1.0
        self.success = True
        self.reason = f"✓ {reason}"
        return self.score

    def _set_partial(self, reason: str) -> float:
        """Set partial success state."""
        self.score = 0.5 if self.is_correct else 0.7
        self.success = False if self.is_correct else True
        self.reason = f"⚠ {reason}"
        return self.score

    def _set_failure(self, reason: str) -> float:
        """Set failure state."""
        self.score = 0.0
        self.success = False
        self.reason = f"✗ {reason}"
        return self.score

    def _set_error(self, reason: str) -> float:
        """Set error state."""
        logger.error(f"FeedbackAppropriatenessMetric error: {reason}")
        return self._set_failure(reason)

    def is_successful(self) -> bool:
        """Check if feedback is appropriate."""
        return self.success

    @property
    def __name__(self) -> str:
        """Metric name."""
        return "Feedback Appropriateness"


class HasNavigationMetric(BaseMetric):
    """
    Checks if response provides navigation options for the student.

    Looks for:
    - Numbered options (1., 2., 3., etc.)
    - Clear next steps ("What would you like to do?")
    - Action prompts

    Used by: lesson_start, teaching_vocab, teaching_grammar modes
    """

    def __init__(self) -> None:
        """Initialize navigation metric."""
        self.score = 0.0
        self.reason = ""
        self.success = False

    def measure(self, test_case: LLMTestCase) -> float:
        """
        Check if response has navigation options.

        Args:
            test_case: Test case with actual_output to check

        Returns:
            1.0 if has navigation, 0.0 otherwise
        """
        try:
            output = test_case.actual_output

            if self._has_numbered_list(output):
                return self._set_success("Has numbered navigation options")
            elif self._has_navigation_phrase(output):
                return self._set_success("Has navigation guidance")
            else:
                return self._set_failure("No clear navigation options provided")

        except Exception as e:
            return self._set_error(f"Navigation check error: {str(e)}")

    def _has_numbered_list(self, text: str) -> bool:
        """Check for numbered list (1., 2., 3. or 1), 2), 3))."""
        return bool(re.search(r"(?:^|\n)\s*[0-9]+[\.)]\s+", text, re.MULTILINE))

    def _has_navigation_phrase(self, text: str) -> bool:
        """Check for navigation phrase indicators."""
        navigation_phrases = [
            "what would you like",
            "would you like to",
            "you can",
            "choose",
            "select",
            "options",
            "next steps",
            "or tell me",
        ]
        return any(phrase in text.lower() for phrase in navigation_phrases)

    def _set_success(self, reason: str) -> float:
        """Set success state."""
        self.score = 1.0
        self.success = True
        self.reason = f"✓ {reason}"
        return self.score

    def _set_failure(self, reason: str) -> float:
        """Set failure state."""
        self.score = 0.0
        self.success = False
        self.reason = f"✗ {reason}"
        return self.score

    def _set_error(self, reason: str) -> float:
        """Set error state."""
        logger.error(f"HasNavigationMetric error: {reason}")
        return self._set_failure(reason)

    def is_successful(self) -> bool:
        """Check if navigation is present."""
        return self.success

    @property
    def __name__(self) -> str:
        """Metric name."""
        return "Has Navigation"


class StructureValidMetric(BaseMetric):
    """
    Validates structure for vocabulary teaching.

    Checks:
    - Batched vocabulary (3-4 words at a time for teaching modes)
    - No grammar leakage in vocab mode (shouldn't explain grammar rules)

    Used by: teaching_vocab mode (batch_introduction, batch_summary)
    """

    def __init__(self, expected_word_count: int | None = None) -> None:
        """
        Initialize structure validation metric.

        Args:
            expected_word_count: Expected number of words in batch (for batch teaching)
        """
        self.expected_word_count = expected_word_count
        self.score = 0.0
        self.reason = ""
        self.success = False

    def measure(self, test_case: LLMTestCase) -> float:
        """
        Check if vocabulary teaching structure is valid.

        Args:
            test_case: Test case with actual_output and input (word count)

        Returns:
            1.0 if structure is valid, 0.0 otherwise
        """
        try:
            output = test_case.actual_output.lower()

            if self._has_grammar_leakage(output):
                return self._set_failure("Grammar leakage detected in vocabulary mode")

            if self.expected_word_count:
                return self._validate_word_count(output)
            else:
                return self._set_success("No grammar leakage detected")

        except Exception as e:
            return self._set_error(f"Structure validation error: {str(e)}")

    def _has_grammar_leakage(self, output: str) -> bool:
        """Check for grammar-related keywords in vocabulary teaching."""
        grammar_keywords = [
            "feminine",
            "masculine",
            "gender",
            "definite article",
            "conjugation",
            "verb agreement",
            "noun-adjective",
            "case ending",
            "genitive",
            "nominative",
        ]
        return any(keyword in output for keyword in grammar_keywords)

    def _validate_word_count(self, output: str) -> float:
        """Validate word count matches expectation."""
        word_patterns = re.findall(r"[-•]\s*\S+\s*\(", output)
        actual_count = len(word_patterns)

        if actual_count == self.expected_word_count:
            return self._set_full_success(actual_count)
        elif 2 <= actual_count <= 5:
            return self._set_acceptable_range(actual_count)
        else:
            return self._set_word_count_mismatch(actual_count)

    def _set_full_success(self, count: int) -> float:
        """Set success for perfect word count match."""
        self.score = 1.0
        self.success = True
        self.reason = f"✓ Valid structure: {count} words, no grammar leakage"
        return self.score

    def _set_acceptable_range(self, count: int) -> float:
        """Set partial success for acceptable word count range."""
        self.score = 0.8
        self.success = True
        self.reason = (
            f"⚠ Word count {count} differs from expected {self.expected_word_count}, "
            f"but within acceptable range"
        )
        return self.score

    def _set_word_count_mismatch(self, count: int) -> float:
        """Set failure for word count outside acceptable range."""
        self.score = 0.5
        self.success = False
        self.reason = f"⚠ Word count mismatch: got {count}, expected {self.expected_word_count}"
        return self.score

    def _set_success(self, reason: str) -> float:
        """Set success state."""
        self.score = 1.0
        self.success = True
        self.reason = f"✓ {reason}"
        return self.score

    def _set_failure(self, reason: str) -> float:
        """Set failure state."""
        self.score = 0.0
        self.success = False
        self.reason = f"✗ {reason}"
        return self.score

    def _set_error(self, reason: str) -> float:
        """Set error state."""
        logger.error(f"StructureValidMetric error: {reason}")
        return self._set_failure(reason)

    def is_successful(self) -> bool:
        """Check if structure is valid."""
        return self.success

    @property
    def __name__(self) -> str:
        """Metric name."""
        return "Structure Valid"
