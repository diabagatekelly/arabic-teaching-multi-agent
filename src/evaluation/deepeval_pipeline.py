"""DeepEval pipeline for evaluating agent outputs against test cases."""

import json
import logging
from pathlib import Path
from typing import Any

from deepeval.metrics import BaseMetric
from deepeval.test_case import LLMTestCase

from src.evaluation.metrics import (
    AccuracyMetric,
    AlignmentMetric,
    JSONValidityMetric,
    SentimentMetric,
    StructureMetric,
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

            # Validate structure - check for all 8 mode keys
            required_keys = [
                "lesson_start",
                "teaching_vocab",
                "teaching_grammar",
                "feedback_vocab",
                "feedback_grammar",
                "grading_vocab",
                "grading_grammar",
                "exercise_generation",
            ]
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

    def _create_test_case(
        self,
        test_case_data: dict,
        actual_output: str,
        expected_output: Any | None = None,
    ) -> LLMTestCase:
        """
        Create LLMTestCase from test data and model response.

        Args:
            test_case_data: Test case data from JSON
            actual_output: Model's generated output
            expected_output: Optional override for expected output (will be set after creation)

        Returns:
            LLMTestCase ready for metric evaluation

        Note:
            DeepEval requires expected_output to be a string, but our metrics expect
            specific types (bool, list, etc.). We use empty string as placeholder,
            then immediately override expected_output with the actual value for our metrics.
        """
        if expected_output is None:
            expected_output = test_case_data["expected_output"]

        # Create test case with placeholder for DeepEval, then override for our metrics
        test_case = LLMTestCase(
            input=json.dumps(test_case_data["input"]),
            actual_output=actual_output,
            expected_output="",  # Placeholder for DeepEval
        )

        # Override with actual type for our metrics
        test_case.expected_output = expected_output

        return test_case

    @staticmethod
    def _get_metric_name(metric: BaseMetric) -> str:
        """
        Get metric name for results dictionary.

        Args:
            metric: Metric instance

        Returns:
            Metric name in snake_case (e.g., "json_validity", "sentiment")
        """
        # Use metric's __name__ property, convert to snake_case
        name = metric.__name__
        # Simple conversion: "JSON Validity" -> "json_validity"
        return name.lower().replace(" ", "_").replace("(", "").replace(")", "")

    def _run_metrics(
        self,
        test_case: LLMTestCase,
        metrics: list[BaseMetric],
        test_id: str,
        results: dict[str, Any],
    ) -> None:
        """
        Run multiple metrics on a test case and record results.

        Args:
            test_case: Test case to evaluate
            metrics: List of metrics to run
            test_id: Test case identifier
            results: Results dictionary to update (modified in place)
        """
        all_passed = True

        for metric in metrics:
            score = metric.measure(test_case)
            metric_name = self._get_metric_name(metric)

            # Ensure metric key exists in results
            if metric_name not in results["metrics"]:
                results["metrics"][metric_name] = []

            results["metrics"][metric_name].append(
                {
                    "test_id": test_id,
                    "score": score,
                    "passed": metric.is_successful(),
                    "reason": metric.reason,
                }
            )

            if not metric.is_successful():
                all_passed = False

        results["total"] += 1
        if all_passed:
            results["passed"] += 1
        else:
            results["failed"] += 1

    def _init_results(self, metric_names: list[str]) -> dict[str, Any]:
        """
        Initialize results dictionary with metric placeholders.

        Args:
            metric_names: List of metric names to track

        Returns:
            Results dictionary structure
        """
        return {
            "total": 0,
            "passed": 0,
            "failed": 0,
            "metrics": {name: [] for name in metric_names},
        }

    def _evaluate_teaching_test_cases(
        self,
        test_cases: list[dict],
        model_responses: dict[str, str],
        results: dict[str, Any],
        threshold: float,
        mode: str,
        dynamic_threshold_fn=None,
    ) -> None:
        """
        Process a list of teaching test cases.

        Args:
            test_cases: List of test case data dictionaries
            model_responses: Dict mapping test_id to model output
            results: Results dictionary to update (modified in place)
            threshold: Default sentiment threshold
            mode: Sentiment mode ("teaching" or "feedback")
            dynamic_threshold_fn: Optional function to compute threshold per test case
        """
        for test_case_data in test_cases:
            test_id = test_case_data["test_id"]
            if test_id not in model_responses:
                continue

            test_case = self._create_test_case(test_case_data, model_responses[test_id])

            # Use dynamic threshold if provided, otherwise use default
            if dynamic_threshold_fn:
                threshold = dynamic_threshold_fn(test_case_data)

            metrics = [SentimentMetric(threshold=threshold, mode=mode)]
            self._run_metrics(test_case, metrics, test_id, results)

    def evaluate_lesson_start(self, model_responses: dict[str, str]) -> dict[str, Any]:
        """
        Evaluate lesson_start mode responses (Prompt #1).

        Args:
            model_responses: Dict mapping test_id to model output

        Returns:
            Evaluation results with sentiment metric
        """
        results = self._init_results(["sentiment"])
        lesson_start_cases = self.test_cases["lesson_start"]["test_cases"]

        self._evaluate_teaching_test_cases(
            lesson_start_cases,
            model_responses,
            results,
            threshold=0.9,
            mode="teaching",
        )

        return results

    def evaluate_teaching_vocab(self, model_responses: dict[str, str]) -> dict[str, Any]:
        """
        Evaluate teaching_vocab mode responses (Prompts #2-6, #8).

        Args:
            model_responses: Dict mapping test_id to model output

        Returns:
            Evaluation results with sentiment metric
        """
        results = self._init_results(["sentiment"])
        vocab_mode = self.test_cases["teaching_vocab"]

        # Iterate through all sub-groups
        for sub_group in [
            "vocab_overview",
            "batch_introduction",
            "list_view",
            "quiz_question",
            "batch_summary",
        ]:
            self._evaluate_teaching_test_cases(
                vocab_mode[sub_group],
                model_responses,
                results,
                threshold=0.9,
                mode="teaching",
            )

        return results

    def evaluate_teaching_grammar(self, model_responses: dict[str, str]) -> dict[str, Any]:
        """
        Evaluate teaching_grammar mode responses (Prompts #9-12, #14).

        Args:
            model_responses: Dict mapping test_id to model output

        Returns:
            Evaluation results with sentiment metric
        """
        results = self._init_results(["sentiment"])
        grammar_mode = self.test_cases["teaching_grammar"]

        # Iterate through all sub-groups
        for sub_group in [
            "grammar_overview",
            "topic_explanation",
            "quiz_question",
            "topic_summary",
        ]:
            self._evaluate_teaching_test_cases(
                grammar_mode[sub_group],
                model_responses,
                results,
                threshold=0.9,
                mode="teaching",
            )

        return results

    def evaluate_feedback_vocab(self, model_responses: dict[str, str]) -> dict[str, Any]:
        """
        Evaluate feedback_vocab mode responses (Prompts #6, #7).

        Args:
            model_responses: Dict mapping test_id to model output

        Returns:
            Evaluation results with sentiment metric
        """
        results = self._init_results(["sentiment"])
        feedback_mode = self.test_cases["feedback_vocab"]

        # Iterate through correct and incorrect feedback
        for sub_group in ["correct_feedback", "incorrect_feedback"]:
            self._evaluate_teaching_test_cases(
                feedback_mode[sub_group],
                model_responses,
                results,
                threshold=0.8,
                mode="feedback",
            )

        return results

    def evaluate_feedback_grammar(self, model_responses: dict[str, str]) -> dict[str, Any]:
        """
        Evaluate feedback_grammar mode responses (Prompts #12, #13).

        Args:
            model_responses: Dict mapping test_id to model output

        Returns:
            Evaluation results with sentiment metric
        """
        results = self._init_results(["sentiment"])
        feedback_mode = self.test_cases["feedback_grammar"]

        # Iterate through correct and incorrect feedback
        for sub_group in ["correct_feedback", "incorrect_feedback"]:
            self._evaluate_teaching_test_cases(
                feedback_mode[sub_group],
                model_responses,
                results,
                threshold=0.8,
                mode="feedback",
            )

        return results

    def _evaluate_grading_test_cases(
        self,
        test_cases: list[dict],
        model_responses: dict[str, str],
        results: dict[str, Any],
    ) -> None:
        """
        Process a list of grading test cases (vocab or grammar).

        Handles two structures:
        1. Simple: {"correct": bool} - for single-question grading
        2. Complex: {"total_score": str, "results": [...]} - for multi-question test grading

        Args:
            test_cases: List of test case data dictionaries
            model_responses: Dict mapping test_id to model output
            results: Results dictionary to update (modified in place)
        """
        for test_case_data in test_cases:
            test_id = test_case_data["test_id"]
            if test_id not in model_responses:
                continue

            expected_output = test_case_data["expected_output"]

            # Determine structure type
            if "correct" in expected_output and "results" not in expected_output:
                # Simple case: {"correct": bool}
                test_case = self._create_test_case(
                    test_case_data,
                    model_responses[test_id],
                    expected_output=expected_output["correct"],
                )
                metrics = [
                    JSONValidityMetric(),
                    StructureMetric(
                        expected_type=dict,
                        required_keys=["correct"],
                        expected_types={"correct": bool},
                    ),
                    AccuracyMetric(),
                ]
            else:
                # Complex case: {"total_score": str, "results": [...]}
                test_case = self._create_test_case(
                    test_case_data, model_responses[test_id], expected_output=expected_output
                )
                metrics = [
                    JSONValidityMetric(),
                    StructureMetric(
                        expected_type=dict,
                        required_keys=["total_score", "results"],
                        expected_types={"total_score": str, "results": list},
                    ),
                    AccuracyMetric(),
                ]

            self._run_metrics(test_case, metrics, test_id, results)

    def evaluate_grading_vocab(self, model_responses: dict[str, str]) -> dict[str, Any]:
        """
        Evaluate grading_vocab mode responses (Prompt #15).

        Args:
            model_responses: Dict mapping test_id to model output

        Returns:
            Evaluation results with JSON, Structure, and Accuracy metrics
        """
        results = self._init_results(["json_validity", "structure", "accuracy"])
        grading_mode = self.test_cases["grading_vocab"]

        # Iterate through correct and incorrect translations
        for sub_group in ["correct_translations", "incorrect_translations"]:
            self._evaluate_grading_test_cases(grading_mode[sub_group], model_responses, results)

        return results

    def evaluate_grading_grammar(self, model_responses: dict[str, str]) -> dict[str, Any]:
        """
        Evaluate grading_grammar mode responses (Prompts #16, #17).

        Args:
            model_responses: Dict mapping test_id to model output

        Returns:
            Evaluation results with JSON, Structure, and Accuracy metrics
        """
        results = self._init_results(["json_validity", "structure", "accuracy"])
        grading_mode = self.test_cases["grading_grammar"]

        # Iterate through all sub-groups
        for sub_group in ["quiz_grading", "quiz_incorrect", "test_grading"]:
            self._evaluate_grading_test_cases(grading_mode[sub_group], model_responses, results)

        return results

    def evaluate_exercise_generation(self, model_responses: dict[str, str]) -> dict[str, Any]:
        """
        Evaluate exercise_generation mode responses (Prompts #19, #20, #21).

        Args:
            model_responses: Dict mapping test_id to model output

        Returns:
            Evaluation results with JSON, Structure, and Alignment metrics
        """
        results = self._init_results(["json_validity", "structure", "alignment"])
        exercise_mode = self.test_cases["exercise_generation"]

        # Iterate through all sub-groups
        for sub_group in ["exercise_gen", "quiz_question_gen", "test_composition"]:
            for test_case_data in exercise_mode[sub_group]:
                test_id = test_case_data["test_id"]
                if test_id not in model_responses:
                    continue

                test_case = self._create_test_case(test_case_data, model_responses[test_id])

                # Run JSON + Structure + Alignment metrics
                # Structure varies by sub-group, but all should be valid JSON with specific keys
                metrics = [
                    JSONValidityMetric(),
                    StructureMetric(
                        expected_type=dict,
                        required_keys=["question", "answer"],
                        expected_types={"question": str, "answer": str},
                    ),
                    AlignmentMetric(threshold=0.8),
                ]
                self._run_metrics(test_case, metrics, test_id, results)

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
