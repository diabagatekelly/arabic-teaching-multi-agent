"""Custom evaluation metrics for Arabic Teaching Multi-Agent System v2."""

import json
import logging
import re
from typing import Any

from deepeval.metrics import BaseMetric
from deepeval.test_case import LLMTestCase
from transformers import pipeline

logger = logging.getLogger(__name__)


class SentimentMetric(BaseMetric):
    """
    Evaluates sentiment score for Agent 1 (Teaching) responses.

    Target: >0.9 for teaching mode, >0.8 for feedback mode.
    """

    # Class-level singleton: shared sentiment pipeline across all instances
    _shared_sentiment_pipeline = None

    def __init__(self, threshold: float = 0.9, mode: str = "teaching") -> None:
        """
        Initialize sentiment metric.

        Args:
            threshold: Minimum sentiment score required
            mode: "teaching" (0.9) or "feedback" (0.8)
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


class JSONValidityMetric(BaseMetric):
    """
    Evaluates JSON validity for Agent 2 (Grading) responses.

    Target: 100% valid JSON output.
    """

    def __init__(self) -> None:
        """Initialize JSON validity metric."""
        self.score = 0.0
        self.reason = ""
        self.success = False
        self.parsed_json: Any = None

    def _extract_json(self, text: str) -> str:
        """
        Extract JSON from text, handling markdown code blocks.

        Args:
            text: Text that may contain JSON with or without markdown blocks

        Returns:
            Extracted JSON string
        """
        text = text.strip()

        # Check for ```json code blocks
        # Match everything after ```json up to the next ``` or end of string
        if "```json" in text:
            match = re.search(r"```json\s*(.*?)(?:```|$)", text, re.DOTALL)
            if match:
                return match.group(1).strip()

        # Check for generic ``` code blocks
        # Match everything after ``` up to the next ``` or end of string
        if "```" in text:
            match = re.search(r"```\s*(.*?)(?:```|$)", text, re.DOTALL)
            if match:
                return match.group(1).strip()

        return text

    def measure(self, test_case: LLMTestCase) -> float:
        """
        Check if output is valid JSON.

        Args:
            test_case: Test case with actual_output to validate

        Returns:
            1.0 if valid JSON, 0.0 otherwise
        """
        try:
            # Extract JSON (handles markdown code blocks)
            json_str = self._extract_json(test_case.actual_output)
            self.parsed_json = json.loads(json_str)
            self.score = 1.0
            self.success = True
            self.reason = "✓ Valid JSON output"
            return 1.0

        except json.JSONDecodeError as e:
            self.score = 0.0
            self.success = False
            self.reason = f"✗ Invalid JSON: {str(e)}"
            logger.error(f"JSON decode error: {e}")
            return 0.0

    def is_successful(self) -> bool:
        """Check if JSON is valid."""
        return self.success

    @property
    def __name__(self) -> str:
        """Metric name."""
        return "JSON Validity"


class AccuracyMetric(BaseMetric):
    """
    Evaluates accuracy for Agent 2 (Grading) correct/incorrect classification.

    Returns 1.0 for correct classification, 0.0 for incorrect.
    Aggregate accuracy across multiple test cases should exceed 90%.
    """

    def __init__(self) -> None:
        """Initialize accuracy metric."""
        self.score = 0.0
        self.reason = ""
        self.success = False

    def measure(self, test_case: LLMTestCase) -> float:
        """
        Check if grading output matches expected correctness.

        Args:
            test_case: Test case with expected_output (bool) and actual_output (JSON)

        Returns:
            1.0 if correct classification, 0.0 otherwise
        """
        try:
            # Parse actual output JSON
            actual = json.loads(test_case.actual_output)

            # Expected is a boolean: True = correct, False = incorrect
            expected_correct = test_case.expected_output

            # Check if grading matches
            if isinstance(actual, dict):
                actual_correct = actual.get("correct", False)
            else:
                self.score = 0.0
                self.success = False
                self.reason = "✗ Output is not a dict"
                return 0.0

            if actual_correct == expected_correct:
                self.score = 1.0
                self.success = True
                self.reason = (
                    f"✓ Correctly classified as {'correct' if expected_correct else 'incorrect'}"
                )
            else:
                self.score = 0.0
                self.success = False
                self.reason = f"✗ Expected {'correct' if expected_correct else 'incorrect'}, got {actual_correct}"

            return self.score

        except (json.JSONDecodeError, KeyError) as e:
            self.score = 0.0
            self.success = False
            self.reason = f"✗ Parsing error: {str(e)}"
            logger.error(f"Accuracy metric parsing error: {e}")
            return 0.0

    def is_successful(self) -> bool:
        """Check if this test case was classified correctly."""
        return self.success

    @property
    def __name__(self) -> str:
        """Metric name."""
        return "Accuracy"


class FaithfulnessMetric(BaseMetric):
    """
    Evaluates faithfulness to template for Agent 3 (Exercise Generation).

    Target: >90% faithfulness to template structure.
    """

    def __init__(self, threshold: float = 0.9) -> None:
        """
        Initialize faithfulness metric.

        Args:
            threshold: Minimum faithfulness score required
        """
        self.threshold = threshold
        self.score = 0.0
        self.reason = ""
        self.success = False

    def measure(self, test_case: LLMTestCase) -> float:
        """
        Check if generated exercises follow template structure.

        Args:
            test_case: Test case with expected template structure and actual output

        Returns:
            Faithfulness score (0-1)
        """
        try:
            # Parse actual output
            actual = json.loads(test_case.actual_output)

            # Expected contains required fields
            expected_fields = test_case.expected_output

            if not isinstance(actual, list):
                self.score = 0.0
                self.success = False
                self.reason = "✗ Output is not a list of exercises"
                return 0.0

            # Check each exercise has required fields
            total_fields = 0
            present_fields = 0

            for exercise in actual:
                for field in expected_fields:
                    total_fields += 1
                    if field in exercise:
                        present_fields += 1

            if total_fields > 0:
                self.score = present_fields / total_fields
            else:
                self.score = 0.0

            self.success = self.score >= self.threshold
            self.reason = (
                f"Faithfulness: {self.score:.2%} "
                f"({present_fields}/{total_fields} fields present) "
                f"({'✓' if self.success else '✗'} threshold: {self.threshold:.0%})"
            )

            return self.score

        except (json.JSONDecodeError, TypeError) as e:
            self.score = 0.0
            self.success = False
            self.reason = f"✗ Parsing error: {str(e)}"
            logger.error(f"Faithfulness metric parsing error: {e}")
            return 0.0

    def is_successful(self) -> bool:
        """Check if faithfulness meets threshold."""
        return self.success

    @property
    def __name__(self) -> str:
        """Metric name."""
        return "Faithfulness"
