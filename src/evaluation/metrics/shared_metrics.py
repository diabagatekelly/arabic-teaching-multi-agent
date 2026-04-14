"""Shared evaluation metrics used by multiple agents."""

import json
import logging
import re

from deepeval.metrics import BaseMetric
from deepeval.test_case import LLMTestCase

logger = logging.getLogger(__name__)


def extract_json(text: str) -> str:
    """
    Extract JSON from text, handling markdown code blocks.

    This is a shared helper used by all metrics to ensure consistent
    JSON extraction, especially for models that may return JSON wrapped
    in markdown fences (```json ... ```).

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


class JSONValidityMetric(BaseMetric):
    """
    Evaluates JSON validity for agent responses.

    Used by: Agent 2 (Grading), Agent 3 (Exercise Generation)
    Target: 100% valid JSON output.
    """

    def __init__(self) -> None:
        """Initialize JSON validity metric."""
        self.score = 0.0
        self.reason = ""
        self.success = False

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
            json_str = extract_json(test_case.actual_output)
            json.loads(json_str)  # Just check if parseable

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


class StructureMetric(BaseMetric):
    """
    Validates JSON structure: correct type, required keys, expected value types.

    Used by: Agent 2 (Grading), Agent 3 (Exercise Generation)
    Configurable for different agent outputs.

    Examples:
        Agent 2 (Grading):
            StructureMetric(
                expected_type=dict,
                required_keys=["correct"],
                expected_types={"correct": bool}
            )

        Agent 3 (Exercise Generation):
            StructureMetric(
                expected_type=list,
                required_keys=["question", "answer"],
                expected_types={"question": str, "answer": str}
            )
    """

    def __init__(
        self,
        expected_type: type,  # dict, list, etc.
        required_keys: list[str] | None = None,  # Keys that must exist
        expected_types: dict[str, type] | None = None,  # Key: expected type
    ) -> None:
        """
        Initialize structure metric.

        Args:
            expected_type: Expected top-level type (dict, list, etc.)
            required_keys: List of keys that must exist
            expected_types: Dict mapping key names to expected types
        """
        # Required by DeepEval
        self.score = 0.0
        self.reason = ""
        self.success = False

        # Configuration
        self.expected_type = expected_type
        self.required_keys = required_keys or []
        self.expected_types = expected_types or {}

    def measure(self, test_case: LLMTestCase) -> float:
        """
        Check if JSON has correct structure.

        Args:
            test_case: Test case with actual_output to validate

        Returns:
            1.0 if structure is valid, 0.0 otherwise
        """
        try:
            parsed = self._parse_json(test_case.actual_output)
            self._validate_top_level_type(parsed)
            self._validate_required_keys(parsed)
            self._validate_value_types(parsed)
            return self._set_success()
        except (json.JSONDecodeError, ValueError) as e:
            return self._set_failure(str(e))

    def _parse_json(self, output: str) -> dict | list:
        """Extract and parse JSON from output."""
        json_str = extract_json(output)
        return json.loads(json_str)

    def _validate_top_level_type(self, parsed: dict | list) -> None:
        """Validate top-level type matches expected."""
        if not isinstance(parsed, self.expected_type):
            raise ValueError(f"Expected {self.expected_type.__name__}, got {type(parsed).__name__}")

    def _validate_required_keys(self, parsed: dict | list) -> None:
        """Validate required keys exist."""
        if self.expected_type is dict:
            self._validate_dict_keys(parsed)
        elif self.expected_type is list:
            self._validate_list_items(parsed)

    def _validate_dict_keys(self, parsed: dict) -> None:
        """Validate dict has all required keys."""
        missing_keys = [k for k in self.required_keys if k not in parsed]
        if missing_keys:
            raise ValueError(f"Missing required keys: {missing_keys}")

    def _validate_list_items(self, parsed: list) -> None:
        """Validate list items have required keys."""
        if not parsed:
            raise ValueError("Expected non-empty list")

        for i, item in enumerate(parsed):
            if not isinstance(item, dict):
                raise ValueError(f"Item {i} is not a dict")

            missing = [k for k in self.required_keys if k not in item]
            if missing:
                raise ValueError(f"Item {i} missing keys: {missing}")

    def _validate_value_types(self, parsed: dict | list) -> None:
        """Validate value types match expected types."""
        if not self.expected_types:
            return

        if self.expected_type is dict:
            self._validate_dict_value_types(parsed)
        elif self.expected_type is list:
            self._validate_list_value_types(parsed)

    def _validate_dict_value_types(self, parsed: dict) -> None:
        """Validate dict value types."""
        for key, expected_type in self.expected_types.items():
            value = parsed.get(key)
            if value is not None and not isinstance(value, expected_type):
                raise ValueError(
                    f"Key '{key}': expected {expected_type.__name__}, "
                    f"got {type(value).__name__}"
                )

    def _validate_list_value_types(self, parsed: list) -> None:
        """Validate list item value types."""
        for i, item in enumerate(parsed):
            for key, expected_type in self.expected_types.items():
                value = item.get(key)
                if value is not None and not isinstance(value, expected_type):
                    raise ValueError(
                        f"Item {i}, key '{key}': expected {expected_type.__name__}, "
                        f"got {type(value).__name__}"
                    )

    def _set_success(self) -> float:
        """Set success state and return score."""
        self.score = 1.0
        self.success = True
        self.reason = "✓ Valid structure with required keys and types"
        return 1.0

    def _set_failure(self, reason: str) -> float:
        """Set failure state and return score."""
        self.score = 0.0
        self.success = False
        self.reason = f"✗ {reason}"
        return 0.0

    def is_successful(self) -> bool:
        """Check if structure validation passed."""
        return self.success

    @property
    def __name__(self) -> str:
        """Metric name."""
        return "Structure"
