"""DeepEval pipeline for evaluating agent outputs against test cases."""

import json
import logging
from pathlib import Path
from typing import Any

from deepeval.test_case import LLMTestCase

from src.evaluation.metrics import (
    AccuracyMetric,
    FaithfulnessMetric,
    JSONValidityMetric,
    SentimentMetric,
)

__all__ = ["EvaluationPipeline"]

logger = logging.getLogger(__name__)


class EvaluationPipeline:
    """Pipeline for running DeepEval evaluations on agent outputs."""

    def __init__(self, test_cases_path: str | Path) -> None:
        """
        Initialize evaluation pipeline.

        Args:
            test_cases_path: Path to test_cases.json file
        """
        self.test_cases_path = Path(test_cases_path)
        if not self.test_cases_path.exists():
            raise FileNotFoundError(f"Test cases file not found: {test_cases_path}")
        self.test_cases = self._load_test_cases()
        logger.info(f"Loaded test cases from {test_cases_path}")

    def _load_test_cases(self) -> dict[str, Any]:
        """
        Load and validate test cases from JSON file.

        Returns:
            Validated test cases dictionary

        Raises:
            ValueError: If test cases structure is invalid
        """
        try:
            with open(self.test_cases_path) as f:
                test_cases = json.load(f)

            # Validate structure
            required_keys = ["teaching_mode", "grading_mode", "exercise_generation"]
            for key in required_keys:
                if key not in test_cases:
                    raise ValueError(f"Missing required key in test cases: {key}")

            return test_cases

        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in test cases file: {e}") from e

    @staticmethod
    def _safe_percentage(numerator: int, denominator: int) -> float:
        """
        Calculate percentage safely, avoiding division by zero.

        Args:
            numerator: Numerator value
            denominator: Denominator value

        Returns:
            Percentage (0-100), or 0.0 if denominator is 0
        """
        return (numerator / denominator * 100) if denominator > 0 else 0.0

    def evaluate_teaching_mode(self, model_responses: dict[str, str]) -> dict[str, Any]:
        """
        Evaluate teaching mode responses.

        Args:
            model_responses: Dict mapping test_id to model output

        Returns:
            Evaluation results with metrics
        """
        results = {
            "total": 0,
            "passed": 0,
            "failed": 0,
            "metrics": {
                "sentiment": [],
                "completeness": [],
                "format": [],
            },
        }

        # Get teaching mode test cases
        teaching_cases = self.test_cases["teaching_mode"]

        # Vocab batch introduction
        for test_case_data in teaching_cases["vocabulary_batch_introduction"]:
            test_id = test_case_data["test_id"]

            if test_id not in model_responses:
                continue

            # Create LLMTestCase
            test_case = LLMTestCase(
                input=json.dumps(test_case_data["input"]),
                actual_output=model_responses[test_id],
                expected_output=test_case_data["expected_output"],
            )

            # Run sentiment metric
            sentiment_metric = SentimentMetric(threshold=0.9, mode="teaching")
            sentiment_score = sentiment_metric.measure(test_case)

            results["total"] += 1
            if sentiment_metric.is_successful():
                results["passed"] += 1
            else:
                results["failed"] += 1

            results["metrics"]["sentiment"].append(
                {
                    "test_id": test_id,
                    "score": sentiment_score,
                    "passed": sentiment_metric.is_successful(),
                    "reason": sentiment_metric.reason,
                }
            )

        # Grammar topic explanation
        for test_case_data in teaching_cases["grammar_topic_explanation"]:
            test_id = test_case_data["test_id"]

            if test_id not in model_responses:
                continue

            test_case = LLMTestCase(
                input=json.dumps(test_case_data["input"]),
                actual_output=model_responses[test_id],
                expected_output=test_case_data["expected_output"],
            )

            sentiment_metric = SentimentMetric(threshold=0.9, mode="teaching")
            sentiment_score = sentiment_metric.measure(test_case)

            results["total"] += 1
            if sentiment_metric.is_successful():
                results["passed"] += 1
            else:
                results["failed"] += 1

            results["metrics"]["sentiment"].append(
                {
                    "test_id": test_id,
                    "score": sentiment_score,
                    "passed": sentiment_metric.is_successful(),
                    "reason": sentiment_metric.reason,
                }
            )

        # Quiz feedback
        for test_case_data in teaching_cases["quiz_feedback"]:
            test_id = test_case_data["test_id"]

            if test_id not in model_responses:
                continue

            test_case = LLMTestCase(
                input=json.dumps(test_case_data["input"]),
                actual_output=model_responses[test_id],
                expected_output=test_case_data["expected_output"],
            )

            # Feedback has lower threshold (0.7-0.8)
            threshold = 0.8 if test_case_data["input"].get("is_correct") else 0.7
            sentiment_metric = SentimentMetric(threshold=threshold, mode="feedback")
            sentiment_score = sentiment_metric.measure(test_case)

            results["total"] += 1
            if sentiment_metric.is_successful():
                results["passed"] += 1
            else:
                results["failed"] += 1

            results["metrics"]["sentiment"].append(
                {
                    "test_id": test_id,
                    "score": sentiment_score,
                    "passed": sentiment_metric.is_successful(),
                    "reason": sentiment_metric.reason,
                }
            )

        return results

    def evaluate_grading_mode(self, model_responses: dict[str, str]) -> dict[str, Any]:
        """
        Evaluate grading mode responses.

        Args:
            model_responses: Dict mapping test_id to model output

        Returns:
            Evaluation results with metrics
        """
        results = {
            "total": 0,
            "passed": 0,
            "failed": 0,
            "metrics": {
                "json_validity": [],
                "accuracy": [],
            },
        }

        grading_cases = self.test_cases["grading_mode"]

        # Vocabulary grading
        vocab_grading = grading_cases["vocabulary_grading"]

        for test_case_data in (
            vocab_grading["correct_translations"] + vocab_grading["incorrect_translations"]
        ):
            test_id = test_case_data["test_id"]

            if test_id not in model_responses:
                continue

            # Store expected boolean for accuracy check
            expected_correct = test_case_data["expected_output"]["correct"]

            test_case = LLMTestCase(
                input=json.dumps(test_case_data["input"]),
                actual_output=model_responses[test_id],
                expected_output=json.dumps(expected_correct),  # Convert to JSON string for DeepEval
            )
            # Override for our metric logic which expects bool
            test_case.expected_output = expected_correct

            # Check JSON validity
            json_metric = JSONValidityMetric()
            json_score = json_metric.measure(test_case)

            # Check accuracy
            accuracy_metric = AccuracyMetric()
            accuracy_score = accuracy_metric.measure(test_case)

            results["total"] += 1
            if json_metric.is_successful() and accuracy_metric.is_successful():
                results["passed"] += 1
            else:
                results["failed"] += 1

            results["metrics"]["json_validity"].append(
                {
                    "test_id": test_id,
                    "score": json_score,
                    "passed": json_metric.is_successful(),
                    "reason": json_metric.reason,
                }
            )

            results["metrics"]["accuracy"].append(
                {
                    "test_id": test_id,
                    "score": accuracy_score,
                    "passed": accuracy_metric.is_successful(),
                    "reason": accuracy_metric.reason,
                }
            )

        # Grammar grading
        grammar_grading = grading_cases["grammar_grading"]

        for test_case_data in (
            grammar_grading["correct_answers"] + grammar_grading["incorrect_answers"]
        ):
            test_id = test_case_data["test_id"]

            if test_id not in model_responses:
                continue

            # Store expected boolean for accuracy check
            expected_correct = test_case_data["expected_output"]["correct"]

            test_case = LLMTestCase(
                input=json.dumps(test_case_data["input"]),
                actual_output=model_responses[test_id],
                expected_output=json.dumps(expected_correct),  # Convert to JSON string for DeepEval
            )
            # Override for our metric logic which expects bool
            test_case.expected_output = expected_correct

            # Check JSON validity
            json_metric = JSONValidityMetric()
            json_score = json_metric.measure(test_case)

            # Check accuracy
            accuracy_metric = AccuracyMetric()
            accuracy_score = accuracy_metric.measure(test_case)

            results["total"] += 1
            if json_metric.is_successful() and accuracy_metric.is_successful():
                results["passed"] += 1
            else:
                results["failed"] += 1

            results["metrics"]["json_validity"].append(
                {
                    "test_id": test_id,
                    "score": json_score,
                    "passed": json_metric.is_successful(),
                    "reason": json_metric.reason,
                }
            )

            results["metrics"]["accuracy"].append(
                {
                    "test_id": test_id,
                    "score": accuracy_score,
                    "passed": accuracy_metric.is_successful(),
                    "reason": accuracy_metric.reason,
                }
            )

        return results

    def evaluate_exercise_generation(self, model_responses: dict[str, str]) -> dict[str, Any]:
        """
        Evaluate exercise generation responses.

        Args:
            model_responses: Dict mapping test_id to model output

        Returns:
            Evaluation results with metrics
        """
        results = {
            "total": 0,
            "passed": 0,
            "failed": 0,
            "metrics": {
                "json_validity": [],
                "faithfulness": [],
            },
        }

        exercise_cases = self.test_cases["exercise_generation"]["test_cases"]

        for test_case_data in exercise_cases:
            test_id = test_case_data["test_id"]

            if test_id not in model_responses:
                continue

            # Expected fields for exercises
            expected_fields = ["question", "answer"]

            test_case = LLMTestCase(
                input=json.dumps(test_case_data["input"]),
                actual_output=model_responses[test_id],
                expected_output=json.dumps(expected_fields),  # Convert to JSON string for DeepEval
            )
            # Override for our metric logic which expects list
            test_case.expected_output = expected_fields

            # Check JSON validity
            json_metric = JSONValidityMetric()
            json_score = json_metric.measure(test_case)

            # Check faithfulness to template
            faithfulness_metric = FaithfulnessMetric(threshold=0.9)
            faithfulness_score = faithfulness_metric.measure(test_case)

            results["total"] += 1
            if json_metric.is_successful() and faithfulness_metric.is_successful():
                results["passed"] += 1
            else:
                results["failed"] += 1

            results["metrics"]["json_validity"].append(
                {
                    "test_id": test_id,
                    "score": json_score,
                    "passed": json_metric.is_successful(),
                    "reason": json_metric.reason,
                }
            )

            results["metrics"]["faithfulness"].append(
                {
                    "test_id": test_id,
                    "score": faithfulness_score,
                    "passed": faithfulness_metric.is_successful(),
                    "reason": faithfulness_metric.reason,
                }
            )

        return results

    def generate_report(self, results: dict[str, Any], mode: str) -> str:
        """
        Generate markdown report from evaluation results.

        Args:
            results: Evaluation results
            mode: Agent mode ("teaching", "grading", "exercise_generation")

        Returns:
            Markdown formatted report
        """
        passed_pct = self._safe_percentage(results["passed"], results["total"])

        report = [
            f"# Evaluation Report: {mode.replace('_', ' ').title()} Mode",
            "",
            f"**Total Test Cases:** {results['total']}",
            f"**Passed:** {results['passed']} ({passed_pct:.1f}%)",
            f"**Failed:** {results['failed']}",
            "",
            "## Metrics Summary",
            "",
        ]

        for metric_name, metric_results in results["metrics"].items():
            if not metric_results:
                continue

            passed = sum(1 for r in metric_results if r["passed"])
            total = len(metric_results)
            pass_rate = self._safe_percentage(passed, total)
            avg_score = sum(r["score"] for r in metric_results) / total if total > 0 else 0

            report.append(f"### {metric_name.replace('_', ' ').title()}")
            report.append(f"- **Pass Rate:** {passed}/{total} ({pass_rate:.1f}%)")
            report.append(f"- **Average Score:** {avg_score:.3f}")
            report.append("")

        logger.info(f"Generated report for {mode} mode: {passed_pct:.1f}% passed")
        return "\n".join(report)


def main() -> None:
    """Run evaluation pipeline (example usage)."""
    logging.basicConfig(level=logging.INFO)

    # Initialize pipeline
    pipeline = EvaluationPipeline("data/evaluation/test_cases.json")

    logger.info("✓ Evaluation pipeline initialized")
    logger.info(f"✓ Loaded {len(pipeline.test_cases)} test case categories")


if __name__ == "__main__":
    main()
