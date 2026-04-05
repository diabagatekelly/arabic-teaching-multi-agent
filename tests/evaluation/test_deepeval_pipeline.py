"""Tests for DeepEval evaluation pipeline."""

import json
from unittest.mock import MagicMock, patch

import pytest

from src.evaluation.deepeval_pipeline import EvaluationPipeline


@pytest.fixture
def mock_test_cases_file(tmp_path):
    """Create a mock test cases JSON file."""
    test_cases = {
        "teaching_mode": {
            "vocabulary_batch_introduction": [
                {
                    "test_id": "teach_vocab_01",
                    "input": {
                        "mode": "teaching",
                        "lesson_number": 1,
                        "batch_number": 1,
                        "words": [
                            {"arabic": "مرحبا", "transliteration": "marhaba", "english": "hello"}
                        ],
                    },
                    "expected_output": "positive",
                }
            ],
            "grammar_topic_explanation": [],
            "quiz_feedback": [],
        },
        "grading_mode": {
            "vocabulary_grading": {
                "correct_translations": [
                    {
                        "test_id": "grade_vocab_01",
                        "input": {
                            "mode": "grading",
                            "word": "مرحبا",
                            "student_answer": "hello",
                            "correct_answer": "hello",
                        },
                        "expected_output": {"correct": True},
                    }
                ],
                "incorrect_translations": [],
            },
            "grammar_grading": {"correct_answers": [], "incorrect_answers": []},
        },
        "exercise_generation": {
            "test_cases": [
                {
                    "test_id": "exercise_01",
                    "input": {"mode": "exercise_generation", "type": "fill_in_blank"},
                }
            ]
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
        assert "teaching_mode" in pipeline.test_cases
        assert "grading_mode" in pipeline.test_cases
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
            json.dump({"teaching_mode": {}}, f)  # Missing grading_mode, exercise_generation

        with pytest.raises(ValueError, match="Missing required key"):
            EvaluationPipeline(incomplete_file)

    def test_safe_percentage_normal(self):
        """Test safe percentage calculation."""
        assert EvaluationPipeline._safe_percentage(5, 10) == 50.0
        assert EvaluationPipeline._safe_percentage(10, 10) == 100.0
        assert EvaluationPipeline._safe_percentage(0, 10) == 0.0

    def test_safe_percentage_division_by_zero(self):
        """Test safe percentage handles division by zero."""
        assert EvaluationPipeline._safe_percentage(5, 0) == 0.0
        assert EvaluationPipeline._safe_percentage(0, 0) == 0.0

    @patch("src.evaluation.deepeval_pipeline.SentimentMetric")
    def test_evaluate_teaching_mode(self, mock_sentiment_metric, mock_test_cases_file):
        """Test teaching mode evaluation."""
        # Mock sentiment metric
        mock_metric_instance = MagicMock()
        mock_metric_instance.measure.return_value = 0.95
        mock_metric_instance.is_successful.return_value = True
        mock_metric_instance.reason = "Sentiment score: 0.950 (✓ threshold: 0.9)"
        mock_sentiment_metric.return_value = mock_metric_instance

        pipeline = EvaluationPipeline(mock_test_cases_file)

        model_responses = {"teach_vocab_01": "Great! Let's learn these wonderful words together!"}

        results = pipeline.evaluate_teaching_mode(model_responses)

        assert results["total"] == 1
        assert results["passed"] == 1
        assert results["failed"] == 0
        assert len(results["metrics"]["sentiment"]) == 1
        assert results["metrics"]["sentiment"][0]["score"] == 0.95
        assert results["metrics"]["sentiment"][0]["passed"] is True

    @patch("src.evaluation.deepeval_pipeline.JSONValidityMetric")
    @patch("src.evaluation.deepeval_pipeline.AccuracyMetric")
    def test_evaluate_grading_mode(
        self, mock_accuracy_metric, mock_json_metric, mock_test_cases_file
    ):
        """Test grading mode evaluation."""
        # Mock JSON validity metric
        mock_json_instance = MagicMock()
        mock_json_instance.measure.return_value = 1.0
        mock_json_instance.is_successful.return_value = True
        mock_json_instance.reason = "✓ Valid JSON output"
        mock_json_metric.return_value = mock_json_instance

        # Mock accuracy metric
        mock_accuracy_instance = MagicMock()
        mock_accuracy_instance.measure.return_value = 1.0
        mock_accuracy_instance.is_successful.return_value = True
        mock_accuracy_instance.reason = "✓ Correctly classified as correct"
        mock_accuracy_metric.return_value = mock_accuracy_instance

        pipeline = EvaluationPipeline(mock_test_cases_file)

        model_responses = {"grade_vocab_01": '{"correct": true}'}

        results = pipeline.evaluate_grading_mode(model_responses)

        assert results["total"] == 1
        assert results["passed"] == 1
        assert results["failed"] == 0
        assert len(results["metrics"]["json_validity"]) == 1
        assert len(results["metrics"]["accuracy"]) == 1

    @patch("src.evaluation.deepeval_pipeline.JSONValidityMetric")
    @patch("src.evaluation.deepeval_pipeline.FaithfulnessMetric")
    def test_evaluate_exercise_generation(
        self, mock_faithfulness_metric, mock_json_metric, mock_test_cases_file
    ):
        """Test exercise generation evaluation."""
        # Mock JSON validity metric
        mock_json_instance = MagicMock()
        mock_json_instance.measure.return_value = 1.0
        mock_json_instance.is_successful.return_value = True
        mock_json_instance.reason = "✓ Valid JSON output"
        mock_json_metric.return_value = mock_json_instance

        # Mock faithfulness metric
        mock_faithfulness_instance = MagicMock()
        mock_faithfulness_instance.measure.return_value = 1.0
        mock_faithfulness_instance.is_successful.return_value = True
        mock_faithfulness_instance.reason = "Faithfulness: 100% (2/2 fields present)"
        mock_faithfulness_metric.return_value = mock_faithfulness_instance

        pipeline = EvaluationPipeline(mock_test_cases_file)

        model_responses = {"exercise_01": '[{"question": "Q1", "answer": "A1"}]'}

        results = pipeline.evaluate_exercise_generation(model_responses)

        assert results["total"] == 1
        assert results["passed"] == 1
        assert results["failed"] == 0

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

    def test_evaluate_teaching_mode_missing_response(self, mock_test_cases_file):
        """Test teaching mode evaluation skips missing responses."""
        pipeline = EvaluationPipeline(mock_test_cases_file)

        # Empty model_responses - test case should be skipped
        model_responses = {}

        results = pipeline.evaluate_teaching_mode(model_responses)

        assert results["total"] == 0
        assert results["passed"] == 0
        assert results["failed"] == 0
