"""Evaluation metrics for Agent 2 (Grading Agent)."""

import json
import logging

from deepeval.metrics import BaseMetric
from deepeval.test_case import LLMTestCase

from .shared_metrics import extract_json

logger = logging.getLogger(__name__)


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

        Assumes structure is valid (StructureMetric already validated).

        Args:
            test_case: Test case with expected_output (bool) and actual_output (JSON)

        Returns:
            1.0 if correct classification, 0.0 otherwise
        """
        try:
            # Extract and parse actual output JSON (handles markdown code blocks)
            json_str = extract_json(test_case.actual_output)
            actual = json.loads(json_str)
            expected_correct = test_case.expected_output

            # Structure is guaranteed valid by StructureMetric, safe to access
            actual_correct = actual["correct"]

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

        except (json.JSONDecodeError, KeyError, TypeError) as e:
            # Should rarely happen if pipeline runs metrics in order
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
