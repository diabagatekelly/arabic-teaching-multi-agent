"""DeepEval pipeline for evaluating agent outputs against test cases."""

import json
import logging
from pathlib import Path
from typing import Any

from deepeval.metrics import BaseMetric
from deepeval.test_case import LLMTestCase

from src.evaluation.metrics import (
    AccuracyMetric,
    ExerciseQualityMetric,
    FeedbackAppropriatenessMetric,
    HasNavigationMetric,
    JSONValidityMetric,
    SentimentMetric,
    StructureMetric,
    StructureValidMetric,
)

__all__ = ["EvaluationPipeline"]

logger = logging.getLogger(__name__)

# Sentiment thresholds for different modes
TEACHING_MODE_THRESHOLD = 0.6  # Neutral/informative tone acceptable
FEEDBACK_MODE_THRESHOLD = 0.8  # Must be encouraging and positive


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

            # Validate structure - check for at least one mode key
            # (Allow partial test case files for specific agents)
            valid_mode_keys = [
                "lesson_start",
                "teaching_vocab",
                "teaching_grammar",
                "feedback_vocab",
                "feedback_grammar",
                "grading_vocab",
                "grading_grammar",
                "exercise_generation",
                "quiz_generation",
                "test_composition",
                "content_retrieval",
            ]
            found_modes = [key for key in valid_mode_keys if key in test_cases]
            if not found_modes:
                raise ValueError(
                    f"No valid mode keys found in test cases. Expected one of: {valid_mode_keys}"
                )

            return test_cases

        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in test cases file: {e}") from e

    def get_test_cases_for_mode(self, mode_name: str) -> list[dict]:
        """
        Extract test cases list for a given mode.

        Handles both simple structure (mode has 'test_cases' key) and
        complex structure (mode has subgroups with lists).

        Args:
            mode_name: Mode name (e.g., "lesson_start", "feedback_vocab")

        Returns:
            Flat list of test case dictionaries for the mode

        Raises:
            KeyError: If mode_name not found in test_cases
        """
        if mode_name not in self.test_cases:
            raise KeyError(f"Mode '{mode_name}' not found in test cases")

        mode_data = self.test_cases[mode_name]
        test_cases_list = []

        if "test_cases" in mode_data:
            # Simple structure: {"test_cases": [...]}
            test_cases_list = mode_data["test_cases"]
        else:
            # Complex structure: {"subgroup1": [...], "subgroup2": [...]}
            for subgroup_data in mode_data.values():
                if isinstance(subgroup_data, list):
                    test_cases_list.extend(subgroup_data)

        return test_cases_list

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

    def _create_metrics_from_test_case(self, test_case_data: dict) -> list[BaseMetric]:
        """
        Create metric instances based on test case's metrics field.

        Args:
            test_case_data: Test case data with 'metrics' and optional 'validation' fields

        Returns:
            List of instantiated metric objects
        """
        metrics_list = []
        # Require explicit metrics field - no default to avoid key mismatches
        metrics_requested = test_case_data.get("metrics", [])
        if not metrics_requested:
            logger.warning(
                f"Test case {test_case_data.get('test_id', 'unknown')} has no metrics specified"
            )
        validation = test_case_data.get("validation", {})
        input_data = test_case_data.get("input", {})

        for metric_name in metrics_requested:
            if metric_name == "sentiment_teaching":
                metrics_list.append(
                    SentimentMetric(threshold=TEACHING_MODE_THRESHOLD, mode="teaching")
                )
            elif metric_name == "sentiment_feedback":
                metrics_list.append(
                    SentimentMetric(threshold=FEEDBACK_MODE_THRESHOLD, mode="feedback")
                )
            elif metric_name == "feedback_appropriateness":
                # Extract parameters from input or validation
                is_correct = input_data.get("is_correct", True)
                correct_answer = validation.get("correct_answer")
                metrics_list.append(
                    FeedbackAppropriatenessMetric(
                        is_correct=is_correct, correct_answer=correct_answer
                    )
                )
            elif metric_name == "has_navigation":
                metrics_list.append(HasNavigationMetric())
            elif metric_name == "structure_valid":
                # Extract expected word count from input if available
                words = input_data.get("words", [])
                expected_count = len(words) if words else None
                metrics_list.append(StructureValidMetric(expected_word_count=expected_count))
            elif metric_name == "json_validity":
                metrics_list.append(JSONValidityMetric())
            elif metric_name == "structure":
                # This would need more configuration - placeholder for now
                metrics_list.append(
                    StructureMetric(
                        expected_type=dict,
                        required_keys=["correct"],
                        expected_types={"correct": bool},
                    )
                )
            elif metric_name == "accuracy":
                metrics_list.append(AccuracyMetric())
            elif metric_name == "exercise_quality":
                # Extract learned items from input (required for Agent 3)
                learned_items = input_data.get("learned_items", [])
                # For duplicate detection, would need batch_exercises context
                # For now, create metric with just learned_items
                metrics_list.append(
                    ExerciseQualityMetric(
                        learned_items=learned_items,
                        batch_exercises=[],  # TODO: Pass batch context for duplicate detection
                        use_llm_judge=False,  # Fast mode by default
                    )
                )
            else:
                logger.warning(f"Unknown metric requested: {metric_name}")

        return metrics_list

    def _evaluate_teaching_test_cases(
        self,
        test_cases: list[dict],
        model_responses: dict[str, str],
        results: dict[str, Any],
        threshold: float = None,
        mode: str = None,
        dynamic_threshold_fn=None,
    ) -> None:
        """
        Process a list of teaching test cases with dynamic metric creation.

        Args:
            test_cases: List of test case data dictionaries
            model_responses: Dict mapping test_id to model output
            results: Results dictionary to update (modified in place)
            threshold: Optional default sentiment threshold (deprecated - use test case metrics field)
            mode: Optional sentiment mode (deprecated - use test case metrics field)
            dynamic_threshold_fn: Optional function to compute threshold per test case (deprecated)
        """
        for test_case_data in test_cases:
            test_id = test_case_data["test_id"]
            if test_id not in model_responses:
                continue

            test_case = self._create_test_case(test_case_data, model_responses[test_id])

            # Create metrics dynamically from test case definition
            metrics = self._create_metrics_from_test_case(test_case_data)

            self._run_metrics(test_case, metrics, test_id, results)

    def evaluate_lesson_start(self, model_responses: dict[str, str]) -> dict[str, Any]:
        """
        Evaluate lesson_start mode responses (Prompt #1).

        Args:
            model_responses: Dict mapping test_id to model output

        Returns:
            Evaluation results with all metrics defined in test cases
        """
        lesson_start_cases = self.test_cases["lesson_start"]["test_cases"]

        # Collect all unique metric names from test cases
        metric_names = set()
        for tc in lesson_start_cases:
            for metric in tc.get("metrics", []):
                metric_names.add(self._normalize_metric_name(metric))

        results = self._init_results(list(metric_names))
        self._evaluate_teaching_test_cases(lesson_start_cases, model_responses, results)

        return results

    @staticmethod
    def _normalize_metric_name(metric_name: str) -> str:
        """Convert metric name to snake_case for results keys."""
        return metric_name.lower().replace(" ", "_").replace("(", "").replace(")", "")

    def evaluate_teaching_vocab(self, model_responses: dict[str, str]) -> dict[str, Any]:
        """
        Evaluate teaching_vocab mode responses (Prompts #2-6, #8).

        Args:
            model_responses: Dict mapping test_id to model output

        Returns:
            Evaluation results with all metrics defined in test cases
        """
        vocab_mode = self.test_cases["teaching_vocab"]

        # Collect all test cases from sub-groups
        all_test_cases = []
        for sub_group in [
            "vocab_overview",
            "batch_introduction",
            "list_view",
            "quiz_question",
            "batch_summary",
        ]:
            all_test_cases.extend(vocab_mode.get(sub_group, []))

        # Collect all unique metric names
        metric_names = set()
        for tc in all_test_cases:
            for metric in tc.get("metrics", []):
                metric_names.add(self._normalize_metric_name(metric))

        results = self._init_results(list(metric_names))

        # Evaluate all test cases
        for sub_group in [
            "vocab_overview",
            "batch_introduction",
            "list_view",
            "quiz_question",
            "batch_summary",
        ]:
            self._evaluate_teaching_test_cases(
                vocab_mode.get(sub_group, []),
                model_responses,
                results,
            )

        return results

    def evaluate_teaching_grammar(self, model_responses: dict[str, str]) -> dict[str, Any]:
        """
        Evaluate teaching_grammar mode responses (Prompts #9-12, #14).

        Args:
            model_responses: Dict mapping test_id to model output

        Returns:
            Evaluation results with all metrics defined in test cases
        """
        grammar_mode = self.test_cases["teaching_grammar"]

        # Collect all test cases from sub-groups
        all_test_cases = []
        for sub_group in [
            "grammar_overview",
            "topic_explanation",
            "quiz_question",
            "topic_summary",
        ]:
            all_test_cases.extend(grammar_mode.get(sub_group, []))

        # Collect all unique metric names
        metric_names = set()
        for tc in all_test_cases:
            for metric in tc.get("metrics", []):
                metric_names.add(self._normalize_metric_name(metric))

        results = self._init_results(list(metric_names))

        # Evaluate all test cases
        for sub_group in [
            "grammar_overview",
            "topic_explanation",
            "quiz_question",
            "topic_summary",
        ]:
            self._evaluate_teaching_test_cases(
                grammar_mode.get(sub_group, []),
                model_responses,
                results,
            )

        return results

    def evaluate_feedback_vocab(self, model_responses: dict[str, str]) -> dict[str, Any]:
        """
        Evaluate feedback_vocab mode responses (Prompts #6, #7).

        Args:
            model_responses: Dict mapping test_id to model output

        Returns:
            Evaluation results with all metrics defined in test cases
        """
        feedback_mode = self.test_cases["feedback_vocab"]

        # Collect all test cases from sub-groups
        all_test_cases = []
        for sub_group in ["correct_feedback", "incorrect_feedback"]:
            all_test_cases.extend(feedback_mode.get(sub_group, []))

        # Collect all unique metric names
        metric_names = set()
        for tc in all_test_cases:
            for metric in tc.get("metrics", []):
                metric_names.add(self._normalize_metric_name(metric))

        results = self._init_results(list(metric_names))

        # Evaluate all test cases
        for sub_group in ["correct_feedback", "incorrect_feedback"]:
            self._evaluate_teaching_test_cases(
                feedback_mode.get(sub_group, []),
                model_responses,
                results,
            )

        return results

    def evaluate_feedback_grammar(self, model_responses: dict[str, str]) -> dict[str, Any]:
        """
        Evaluate feedback_grammar mode responses (Prompts #12, #13).

        Args:
            model_responses: Dict mapping test_id to model output

        Returns:
            Evaluation results with all metrics defined in test cases
        """
        feedback_mode = self.test_cases["feedback_grammar"]

        # Collect all test cases from sub-groups
        all_test_cases = []
        for sub_group in ["correct_feedback", "incorrect_feedback"]:
            all_test_cases.extend(feedback_mode.get(sub_group, []))

        # Collect all unique metric names
        metric_names = set()
        for tc in all_test_cases:
            for metric in tc.get("metrics", []):
                metric_names.add(self._normalize_metric_name(metric))

        results = self._init_results(list(metric_names))

        # Evaluate all test cases
        for sub_group in ["correct_feedback", "incorrect_feedback"]:
            self._evaluate_teaching_test_cases(
                feedback_mode.get(sub_group, []),
                model_responses,
                results,
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

        # Iterate through all subgroups dynamically (supports any structure)
        for _sub_group_name, sub_group_cases in grading_mode.items():
            # Skip metadata fields
            if isinstance(sub_group_cases, list):
                self._evaluate_grading_test_cases(sub_group_cases, model_responses, results)

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

        # Iterate through all subgroups dynamically (supports any structure)
        for _sub_group_name, sub_group_cases in grading_mode.items():
            # Skip metadata fields
            if isinstance(sub_group_cases, list):
                self._evaluate_grading_test_cases(sub_group_cases, model_responses, results)

        return results

    def evaluate_content_agent(self, model_responses: dict[str, str]) -> dict[str, Any]:
        """
        Evaluate Agent 3 (Content Generation) responses across all test modes.

        Handles 4 test modes:
        1. exercise_generation - Individual exercise creation (12 types)
        2. quiz_generation - Quiz composition from multiple exercises
        3. test_composition - Full test creation with balanced content
        4. content_retrieval - RAG-based content retrieval

        Args:
            model_responses: Dict mapping test_id to model output

        Returns:
            Evaluation results with metrics: json_validity, structure, exercise_quality
        """
        # Collect all test cases from all 4 modes
        all_test_cases = []

        # Mode 1: Exercise generation (has subgroups)
        if "exercise_generation" in self.test_cases:
            exercise_gen = self.test_cases["exercise_generation"]
            all_test_cases.extend(exercise_gen.get("comprehensive_types", []))
            all_test_cases.extend(exercise_gen.get("smoke_tests", []))

        # Mode 2-4: Quiz generation, test composition, content retrieval (simple structure)
        for mode_name in ["quiz_generation", "test_composition", "content_retrieval"]:
            if mode_name in self.test_cases:
                all_test_cases.extend(self.test_cases[mode_name].get("test_cases", []))

        # Collect all unique metric names
        metric_names = set()
        for tc in all_test_cases:
            for metric in tc.get("metrics", []):
                metric_names.add(self._normalize_metric_name(metric))

        results = self._init_results(list(metric_names))

        # Evaluate all test cases using dynamic metric creation
        self._evaluate_teaching_test_cases(all_test_cases, model_responses, results)

        return results

    def generate_report(self, results: dict[str, Any], mode: str) -> str:
        """
        Generate markdown report from evaluation results.

        Args:
            results: Evaluation results
            mode: Agent mode ("teaching", "grading")

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
