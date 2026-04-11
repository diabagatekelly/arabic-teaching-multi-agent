"""Tests for DeepEval evaluation pipeline."""

import json
from unittest.mock import MagicMock, patch

import pytest
from deepeval.test_case import LLMTestCase

from src.evaluation.deepeval_pipeline import EvaluationPipeline
from src.evaluation.metrics import (
    AccuracyMetric,
    JSONValidityMetric,
    SentimentMetric,
    StructureMetric,
)


@pytest.fixture
def mock_test_cases_file(tmp_path):
    """Create a mock test cases JSON file with v2.0 structure."""
    test_cases = {
        "metadata": {
            "version": "2.0",
            "total_test_cases": 8,
        },
        "lesson_start": {
            "total_cases": 1,
            "test_cases": [
                {
                    "test_id": "lesson_start_01",
                    "input": {
                        "mode": "lesson_start",
                        "lesson_number": 1,
                        "vocab_summary": {"total_words": 10, "topics_preview": ["word1", "word2"]},
                        "grammar_summary": {"topics": ["Topic 1"], "topics_count": 1},
                    },
                    "expected_output": "positive",
                    "metrics": ["sentiment"],
                }
            ],
        },
        "teaching_vocab": {
            "total_cases": 1,
            "vocab_overview": [],
            "batch_introduction": [
                {
                    "test_id": "teach_vocab_01",
                    "input": {
                        "mode": "teaching_vocab",
                        "lesson_number": 1,
                        "batch_number": 1,
                        "words": [
                            {"arabic": "مرحبا", "transliteration": "marhaba", "english": "hello"}
                        ],
                    },
                    "expected_output": "positive",
                    "metrics": ["sentiment"],
                }
            ],
            "list_view": [],
            "quiz_question": [],
            "batch_summary": [],
        },
        "teaching_grammar": {
            "total_cases": 1,
            "grammar_overview": [],
            "topic_explanation": [
                {
                    "test_id": "teach_grammar_01",
                    "input": {
                        "mode": "teaching_grammar",
                        "lesson_number": 1,
                        "topic_name": "Feminine Nouns",
                        "grammar_rule": "Nouns ending in ة are feminine",
                        "learned_items": [],
                    },
                    "expected_output": "positive",
                    "metrics": ["sentiment"],
                }
            ],
            "quiz_question": [],
            "topic_summary": [],
        },
        "feedback_vocab": {
            "total_cases": 1,
            "correct_feedback": [
                {
                    "test_id": "feedback_vocab_01",
                    "input": {
                        "mode": "feedback_vocab",
                        "word": "مرحبا",
                        "is_correct": True,
                    },
                    "expected_output": "positive",
                    "metrics": ["sentiment"],
                }
            ],
            "incorrect_feedback": [],
        },
        "feedback_grammar": {
            "total_cases": 1,
            "correct_feedback": [
                {
                    "test_id": "feedback_grammar_01",
                    "input": {
                        "mode": "feedback_grammar",
                        "is_correct": True,
                    },
                    "expected_output": "positive",
                    "metrics": ["sentiment"],
                }
            ],
            "incorrect_feedback": [],
        },
        "grading_vocab": {
            "total_cases": 1,
            "correct_translations": [
                {
                    "test_id": "grade_vocab_01",
                    "input": {
                        "mode": "grading_vocab",
                        "word": "مرحبا",
                        "student_answer": "hello",
                        "correct_answer": "hello",
                    },
                    "expected_output": {"correct": True},
                    "metrics": ["json_validity", "structure", "accuracy"],
                }
            ],
            "incorrect_translations": [],
        },
        "grading_grammar": {
            "total_cases": 1,
            "quiz_grading": [
                {
                    "test_id": "grade_grammar_01",
                    "input": {
                        "mode": "grading_grammar",
                        "question": "Test question",
                        "student_answer": "correct",
                        "correct_answer": "correct",
                    },
                    "expected_output": {"correct": True},
                    "metrics": ["json_validity", "structure", "accuracy"],
                }
            ],
            "quiz_incorrect": [],
            "test_grading": [],
        },
        "exercise_generation": {
            "total_cases": 1,
            "exercise_gen": [
                {
                    "test_id": "exercise_01",
                    "input": {
                        "mode": "exercise_generation",
                        "exercise_type": "fill_in_blank",
                        "learned_vocab": ["word1"],
                        "grammar_rule": "test rule",
                    },
                    "expected_output": {"question": "test", "answer": "test"},
                    "metrics": ["json_validity", "structure", "alignment"],
                }
            ],
            "quiz_question_gen": [],
            "test_composition": [],
        },
    }

    test_file = tmp_path / "test_cases.json"
    with open(test_file, "w") as f:
        json.dump(test_cases, f)

    return test_file


class TestEvaluationPipeline:
    """Tests for EvaluationPipeline."""

    def test_initialization(self, mock_test_cases_file):
        """Test pipeline initialization."""
        pipeline = EvaluationPipeline(mock_test_cases_file)

        assert pipeline.test_cases_path == mock_test_cases_file
        # Check for all 8 mode keys
        assert "lesson_start" in pipeline.test_cases
        assert "teaching_vocab" in pipeline.test_cases
        assert "teaching_grammar" in pipeline.test_cases
        assert "feedback_vocab" in pipeline.test_cases
        assert "feedback_grammar" in pipeline.test_cases
        assert "grading_vocab" in pipeline.test_cases
        assert "grading_grammar" in pipeline.test_cases
        assert "exercise_generation" in pipeline.test_cases

    def test_initialization_file_not_found(self):
        """Test that FileNotFoundError is raised if test cases file doesn't exist."""
        with pytest.raises(FileNotFoundError):
            EvaluationPipeline("/nonexistent/path/test_cases.json")

    def test_load_test_cases_invalid_json(self, tmp_path):
        """Test that ValueError is raised for invalid JSON."""
        invalid_file = tmp_path / "invalid.json"
        with open(invalid_file, "w") as f:
            f.write("{invalid json")

        with pytest.raises(ValueError, match="Invalid JSON"):
            EvaluationPipeline(invalid_file)

    def test_load_test_cases_missing_keys(self, tmp_path):
        """Test that ValueError is raised for missing required keys."""
        incomplete_file = tmp_path / "incomplete.json"
        with open(incomplete_file, "w") as f:
            json.dump({"lesson_start": {}}, f)  # Missing other 7 modes

        with pytest.raises(ValueError, match="Missing required key"):
            EvaluationPipeline(incomplete_file)

    def test_safe_percentage_division_by_zero(self):
        """Test safe percentage handles division by zero."""
        assert EvaluationPipeline._safe_percentage(5, 0) == 0.0
        assert EvaluationPipeline._safe_percentage(0, 0) == 0.0

    @patch("src.evaluation.deepeval_pipeline.SentimentMetric")
    def test_evaluate_teaching_vocab(self, mock_sentiment_metric, mock_test_cases_file):
        """Test teaching_vocab mode evaluation."""
        # Mock sentiment metric
        mock_metric_instance = MagicMock()
        mock_metric_instance.measure.return_value = 0.95
        mock_metric_instance.is_successful.return_value = True
        mock_metric_instance.reason = "Sentiment score: 0.950 (✓ threshold: 0.9)"
        mock_metric_instance.__name__ = "Sentiment"  # Converts to "sentiment"
        mock_sentiment_metric.return_value = mock_metric_instance

        pipeline = EvaluationPipeline(mock_test_cases_file)

        model_responses = {"teach_vocab_01": "Great! Let's learn these wonderful words together!"}

        results = pipeline.evaluate_teaching_vocab(model_responses)

        assert results["total"] == 1
        assert results["passed"] == 1
        assert results["failed"] == 0
        assert len(results["metrics"]["sentiment"]) == 1
        assert results["metrics"]["sentiment"][0]["score"] == 0.95
        assert results["metrics"]["sentiment"][0]["passed"] is True
        # Verify mock was actually called
        mock_metric_instance.measure.assert_called_once()

    @patch("src.evaluation.deepeval_pipeline.JSONValidityMetric")
    @patch("src.evaluation.deepeval_pipeline.StructureMetric")
    @patch("src.evaluation.deepeval_pipeline.AccuracyMetric")
    def test_evaluate_grading_vocab(
        self, mock_accuracy_metric, mock_structure_metric, mock_json_metric, mock_test_cases_file
    ):
        """Test grading_vocab mode evaluation."""
        # Mock JSON validity metric
        mock_json_instance = MagicMock()
        mock_json_instance.measure.return_value = 1.0
        mock_json_instance.is_successful.return_value = True
        mock_json_instance.reason = "✓ Valid JSON output"
        mock_json_instance.__name__ = "JSON Validity"
        mock_json_metric.return_value = mock_json_instance

        # Mock structure metric
        mock_structure_instance = MagicMock()
        mock_structure_instance.measure.return_value = 1.0
        mock_structure_instance.is_successful.return_value = True
        mock_structure_instance.reason = "✓ Valid structure"
        mock_structure_instance.__name__ = "Structure"
        mock_structure_metric.return_value = mock_structure_instance

        # Mock accuracy metric
        mock_accuracy_instance = MagicMock()
        mock_accuracy_instance.measure.return_value = 1.0
        mock_accuracy_instance.is_successful.return_value = True
        mock_accuracy_instance.reason = "✓ Correctly classified as correct"
        mock_accuracy_instance.__name__ = "Accuracy"
        mock_accuracy_metric.return_value = mock_accuracy_instance

        pipeline = EvaluationPipeline(mock_test_cases_file)

        model_responses = {"grade_vocab_01": '{"correct": true}'}

        results = pipeline.evaluate_grading_vocab(model_responses)

        assert results["total"] == 1
        assert results["passed"] == 1
        assert results["failed"] == 0
        assert len(results["metrics"]["json_validity"]) == 1
        assert len(results["metrics"]["structure"]) == 1
        assert len(results["metrics"]["accuracy"]) == 1
        # Verify all metrics were actually called
        mock_json_instance.measure.assert_called_once()
        mock_structure_instance.measure.assert_called_once()
        mock_accuracy_instance.measure.assert_called_once()

    @patch("src.evaluation.deepeval_pipeline.JSONValidityMetric")
    @patch("src.evaluation.deepeval_pipeline.StructureMetric")
    @patch("src.evaluation.deepeval_pipeline.AlignmentMetric")
    def test_evaluate_exercise_generation(
        self, mock_alignment_metric, mock_structure_metric, mock_json_metric, mock_test_cases_file
    ):
        """Test exercise generation evaluation with alignment metric."""
        # Mock JSON validity metric
        mock_json_instance = MagicMock()
        mock_json_instance.measure.return_value = 1.0
        mock_json_instance.is_successful.return_value = True
        mock_json_instance.reason = "✓ Valid JSON output"
        mock_json_instance.__name__ = "JSON Validity"
        mock_json_metric.return_value = mock_json_instance

        # Mock structure metric
        mock_structure_instance = MagicMock()
        mock_structure_instance.measure.return_value = 1.0
        mock_structure_instance.is_successful.return_value = True
        mock_structure_instance.reason = "✓ Valid structure with required keys and types"
        mock_structure_instance.__name__ = "Structure"
        mock_structure_metric.return_value = mock_structure_instance

        # Mock alignment metric
        mock_alignment_instance = MagicMock()
        mock_alignment_instance.measure.return_value = 0.85
        mock_alignment_instance.is_successful.return_value = True
        mock_alignment_instance.reason = "✓ Alignment score: 0.85 (threshold: 0.8)"
        mock_alignment_instance.__name__ = "Alignment"
        mock_alignment_metric.return_value = mock_alignment_instance

        pipeline = EvaluationPipeline(mock_test_cases_file)

        model_responses = {"exercise_01": '{"question": "Q1", "answer": "A1"}'}

        results = pipeline.evaluate_exercise_generation(model_responses)

        assert results["total"] == 1
        assert results["passed"] == 1
        assert results["failed"] == 0
        assert len(results["metrics"]["json_validity"]) == 1
        assert len(results["metrics"]["structure"]) == 1
        assert len(results["metrics"]["alignment"]) == 1

    def test_generate_report(self, mock_test_cases_file):
        """Test report generation."""
        pipeline = EvaluationPipeline(mock_test_cases_file)

        results = {
            "total": 10,
            "passed": 8,
            "failed": 2,
            "metrics": {
                "sentiment": [
                    {"test_id": "test1", "score": 0.95, "passed": True, "reason": "Good"},
                    {"test_id": "test2", "score": 0.85, "passed": False, "reason": "Low"},
                ]
            },
        }

        report = pipeline.generate_report(results, "teaching")

        assert "# Evaluation Report: Teaching Mode" in report
        assert "**Total Test Cases:** 10" in report
        assert "**Passed:** 8 (80.0%)" in report
        assert "**Failed:** 2" in report
        assert "### Sentiment" in report
        assert "**Pass Rate:** 1/2 (50.0%)" in report
        assert "**Average Score:** 0.900" in report

    def test_generate_report_empty_results(self, mock_test_cases_file):
        """Test report generation with empty results."""
        pipeline = EvaluationPipeline(mock_test_cases_file)

        results = {"total": 0, "passed": 0, "failed": 0, "metrics": {}}

        report = pipeline.generate_report(results, "grading")

        assert "# Evaluation Report: Grading Mode" in report
        assert "**Total Test Cases:** 0" in report
        assert "**Passed:** 0 (0.0%)" in report

    def test_evaluate_teaching_vocab_missing_response(self, mock_test_cases_file):
        """Test teaching_vocab evaluation skips missing responses."""
        pipeline = EvaluationPipeline(mock_test_cases_file)

        # Empty model_responses - test case should be skipped
        model_responses = {}

        results = pipeline.evaluate_teaching_vocab(model_responses)

        assert results["total"] == 0
        assert results["passed"] == 0
        assert results["failed"] == 0


class TestEvaluationPipelineHelpers:
    """Test helper methods introduced in refactoring."""

    def test_create_test_case_default_expected(self, mock_test_cases_file):
        """Test creating test case with default expected output."""
        pipeline = EvaluationPipeline(mock_test_cases_file)

        test_case_data = {
            "test_id": "test1",
            "input": {"word": "كتاب", "student_answer": "book"},
            "expected_output": {"correct": True},
        }

        test_case = pipeline._create_test_case(test_case_data, '{"correct": true}')

        assert isinstance(test_case, LLMTestCase)
        assert test_case.actual_output == '{"correct": true}'
        assert test_case.expected_output == {"correct": True}
        assert json.loads(test_case.input) == test_case_data["input"]

    def test_create_test_case_override_expected(self, mock_test_cases_file):
        """Test creating test case with overridden expected output."""
        pipeline = EvaluationPipeline(mock_test_cases_file)

        test_case_data = {
            "test_id": "test1",
            "input": {"word": "كتاب"},
            "expected_output": {"correct": True},
        }

        # Override with boolean
        test_case = pipeline._create_test_case(
            test_case_data, '{"correct": true}', expected_output=True
        )

        assert test_case.expected_output is True  # Overridden to boolean

    @pytest.mark.parametrize(
        "metric,expected_name",
        [
            (SentimentMetric(threshold=0.9, mode="teaching"), "sentiment_teaching"),
            (JSONValidityMetric(), "json_validity"),
            (StructureMetric(expected_type=dict, required_keys=["correct"]), "structure"),
            (AccuracyMetric(), "accuracy"),
        ],
    )
    def test_get_metric_name(self, metric, expected_name):
        """Test metric name extraction for all metric types."""
        name = EvaluationPipeline._get_metric_name(metric)
        assert name == expected_name

    def test_run_metrics_all_pass(self, mock_test_cases_file):
        """Test running metrics when all pass."""
        pipeline = EvaluationPipeline(mock_test_cases_file)

        # Create test case with JSON string, then override for metrics
        test_case = LLMTestCase(
            input='{"word": "كتاب", "student_answer": "book", "correct_answer": "book"}',
            actual_output='{"correct": true}',
            expected_output="true",  # JSON string for DeepEval
        )
        test_case.expected_output = True  # Override for our metrics

        metrics = [
            JSONValidityMetric(),
            StructureMetric(
                expected_type=dict, required_keys=["correct"], expected_types={"correct": bool}
            ),
            AccuracyMetric(),
        ]

        results = pipeline._init_results(["json_validity", "structure", "accuracy"])

        pipeline._run_metrics(test_case, metrics, "test1", results)

        assert results["total"] == 1
        assert results["passed"] == 1
        assert results["failed"] == 0

        # Check all metrics recorded
        assert len(results["metrics"]["json_validity"]) == 1
        assert len(results["metrics"]["structure"]) == 1
        assert len(results["metrics"]["accuracy"]) == 1

        # Check all passed
        assert results["metrics"]["json_validity"][0]["passed"] is True
        assert results["metrics"]["structure"][0]["passed"] is True
        assert results["metrics"]["accuracy"][0]["passed"] is True

    def test_run_metrics_structure_fails(self, mock_test_cases_file):
        """Test running metrics when structure fails."""
        pipeline = EvaluationPipeline(mock_test_cases_file)

        # Create test case with JSON string, then override for metrics
        test_case = LLMTestCase(
            input='{"word": "كتاب"}',
            actual_output='{"status": "ok"}',  # Missing "correct" key
            expected_output="true",  # JSON string for DeepEval
        )
        test_case.expected_output = True  # Override for our metrics

        metrics = [
            JSONValidityMetric(),
            StructureMetric(
                expected_type=dict, required_keys=["correct"], expected_types={"correct": bool}
            ),
            AccuracyMetric(),
        ]

        results = pipeline._init_results(["json_validity", "structure", "accuracy"])

        pipeline._run_metrics(test_case, metrics, "test1", results)

        assert results["total"] == 1
        assert results["passed"] == 0
        assert results["failed"] == 1

        # JSON passes, structure fails
        assert results["metrics"]["json_validity"][0]["passed"] is True
        assert results["metrics"]["structure"][0]["passed"] is False
        assert "Missing required keys" in results["metrics"]["structure"][0]["reason"]

        # Accuracy also fails (KeyError due to missing key)
        assert results["metrics"]["accuracy"][0]["passed"] is False

    def test_run_metrics_creates_missing_keys(self, mock_test_cases_file):
        """Test that _run_metrics creates metric keys if missing."""
        pipeline = EvaluationPipeline(mock_test_cases_file)

        # Create test case with JSON string, then override for metrics
        test_case = LLMTestCase(
            input='{"word": "كتاب"}',
            actual_output='{"correct": true}',
            expected_output="true",  # JSON string for DeepEval
        )
        test_case.expected_output = True  # Override for our metrics

        metrics = [JSONValidityMetric()]

        # Results without "json_validity" key
        results = {"total": 0, "passed": 0, "failed": 0, "metrics": {}}

        pipeline._run_metrics(test_case, metrics, "test1", results)

        # Should create the key
        assert "json_validity" in results["metrics"]
        assert len(results["metrics"]["json_validity"]) == 1

    @pytest.mark.parametrize(
        "metric_names,expected_keys",
        [
            (
                ["json_validity", "structure", "accuracy"],
                ["json_validity", "structure", "accuracy"],
            ),
            ([], []),
        ],
    )
    def test_init_results(self, mock_test_cases_file, metric_names, expected_keys):
        """Test result initialization with various metric configurations."""
        pipeline = EvaluationPipeline(mock_test_cases_file)

        results = pipeline._init_results(metric_names)

        assert results["total"] == 0
        assert results["passed"] == 0
        assert results["failed"] == 0
        for key in expected_keys:
            assert key in results["metrics"]
            assert results["metrics"][key] == []
        assert len(results["metrics"]) == len(expected_keys)
