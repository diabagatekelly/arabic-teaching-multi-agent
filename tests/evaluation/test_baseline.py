"""Tests for baseline evaluation."""

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from src.evaluation.baseline import (
    DEFAULT_BASELINE_REPORT_PATH,
    DEFAULT_MAX_TOKENS,
    DEFAULT_SAMPLE_SIZE,
    DEFAULT_TEST_CASES_PATH,
    GRADING_MAX_TOKENS,
    BaselineEvaluator,
)


@pytest.fixture
def mock_test_cases_file(tmp_path):
    """Create a mock test cases JSON file."""
    test_cases = {
        "teaching_mode": {
            "vocabulary_batch_introduction": [
                {
                    "test_id": f"teach_vocab_{i:02d}",
                    "input": {
                        "mode": "teaching",
                        "lesson_number": 1,
                        "batch_number": 1,
                        "words": [
                            {"arabic": "مرحبا", "transliteration": "marhaba", "english": "hello"},
                            {
                                "arabic": "شكرا",
                                "transliteration": "shukran",
                                "english": "thank you",
                            },
                        ],
                    },
                    "expected_output": "positive",
                }
                for i in range(10)  # Create 10 unique test cases
            ]
        },
        "grading_mode": {
            "vocabulary_grading": {
                "correct_translations": [
                    {
                        "test_id": f"grade_vocab_{i:02d}",
                        "input": {
                            "mode": "grading",
                            "word": "مرحبا",
                            "student_answer": "hello",
                            "correct_answer": "hello",
                        },
                        "expected_output": {"correct": True},
                    }
                    for i in range(10)
                ],
                "incorrect_translations": [],
            },
            "grammar_grading": {"correct_answers": [], "incorrect_answers": []},
        },
        "exercise_generation": {"test_cases": []},
    }

    test_file = tmp_path / "test_cases.json"
    with open(test_file, "w") as f:
        json.dump(test_cases, f)

    return test_file


class TestBaselineEvaluator:
    """Tests for BaselineEvaluator."""

    @patch("src.evaluation.baseline.AutoModelForCausalLM")
    @patch("src.evaluation.baseline.AutoTokenizer")
    @patch("src.evaluation.baseline.EvaluationPipeline")
    def test_initialization(self, mock_pipeline, mock_tokenizer, mock_model, mock_test_cases_file):
        """Test evaluator initialization."""
        evaluator = BaselineEvaluator(model_name="test-model", test_cases_path=mock_test_cases_file)

        assert evaluator.model_name == "test-model"
        assert evaluator.test_cases_path == Path(mock_test_cases_file)
        mock_tokenizer.from_pretrained.assert_called_once_with("test-model")
        mock_model.from_pretrained.assert_called_once()
        mock_pipeline.assert_called_once_with(mock_test_cases_file)

    @patch("src.evaluation.baseline.AutoModelForCausalLM")
    @patch("src.evaluation.baseline.AutoTokenizer")
    def test_initialization_model_load_failure(self, mock_tokenizer, mock_model):
        """Test that RuntimeError is raised when model loading fails."""
        mock_model.from_pretrained.side_effect = Exception("Model not found")

        with pytest.raises(RuntimeError, match="Failed to load model"):
            BaselineEvaluator(model_name="invalid-model")

    @patch("src.evaluation.baseline.AutoModelForCausalLM")
    @patch("src.evaluation.baseline.AutoTokenizer")
    def test_initialization_test_cases_not_found(self, mock_tokenizer, mock_model):
        """Test that FileNotFoundError is raised when test cases file doesn't exist."""
        with pytest.raises(FileNotFoundError):
            BaselineEvaluator(test_cases_path="/nonexistent/path/test_cases.json")

    @patch("src.evaluation.baseline.AutoModelForCausalLM")
    @patch("src.evaluation.baseline.AutoTokenizer")
    @patch("src.evaluation.baseline.EvaluationPipeline")
    def test_initialization_uses_defaults(self, mock_pipeline, mock_tokenizer, mock_model):
        """Test that initialization uses default paths when not provided."""
        # We need to mock the pipeline to avoid FileNotFoundError
        mock_pipeline.return_value = MagicMock()

        evaluator = BaselineEvaluator()

        assert evaluator.model_name == "Qwen/Qwen2.5-3B-Instruct"
        assert evaluator.test_cases_path == DEFAULT_TEST_CASES_PATH

    @patch("src.evaluation.baseline.AutoModelForCausalLM")
    @patch("src.evaluation.baseline.AutoTokenizer")
    @patch("src.evaluation.baseline.EvaluationPipeline")
    def test_generate_response(
        self, mock_pipeline, mock_tokenizer, mock_model, mock_test_cases_file
    ):
        """Test response generation."""
        # Mock tokenizer and model
        mock_tokenizer_instance = MagicMock()
        mock_tokenizer.from_pretrained.return_value = mock_tokenizer_instance

        # Mock tokenizer return value with .to() method
        mock_tokenized_input = MagicMock()
        mock_tokenized_input.to.return_value = mock_tokenized_input
        mock_tokenizer_instance.return_value = mock_tokenized_input

        mock_model_instance = MagicMock()
        mock_model.from_pretrained.return_value = mock_model_instance
        mock_model_instance.device = "cpu"
        mock_model_instance.generate.return_value = [[1, 2, 3, 4, 5]]

        mock_tokenizer_instance.decode.return_value = "Test promptGenerated response"
        mock_tokenizer_instance.eos_token_id = 2

        evaluator = BaselineEvaluator(model_name="test-model", test_cases_path=mock_test_cases_file)

        response = evaluator.generate_response("Test prompt", max_new_tokens=50)

        assert response == "Generated response"
        mock_model_instance.generate.assert_called_once()

    @patch("src.evaluation.baseline.AutoModelForCausalLM")
    @patch("src.evaluation.baseline.AutoTokenizer")
    @patch("src.evaluation.baseline.EvaluationPipeline")
    def test_generate_response_uses_default_max_tokens(
        self, mock_pipeline, mock_tokenizer, mock_model, mock_test_cases_file
    ):
        """Test that generate_response uses default max tokens."""
        mock_tokenizer_instance = MagicMock()
        mock_tokenizer.from_pretrained.return_value = mock_tokenizer_instance

        # Mock tokenizer return value with .to() method
        mock_tokenized_input = MagicMock()
        mock_tokenized_input.to.return_value = mock_tokenized_input
        mock_tokenizer_instance.return_value = mock_tokenized_input

        mock_model_instance = MagicMock()
        mock_model.from_pretrained.return_value = mock_model_instance
        mock_model_instance.device = "cpu"
        mock_model_instance.generate.return_value = [[1, 2, 3]]

        mock_tokenizer_instance.decode.return_value = "PromptResponse"
        mock_tokenizer_instance.eos_token_id = 2

        evaluator = BaselineEvaluator(model_name="test-model", test_cases_path=mock_test_cases_file)

        evaluator.generate_response("Prompt")  # No max_new_tokens specified

        # Check that generate was called with DEFAULT_MAX_TOKENS
        call_kwargs = mock_model_instance.generate.call_args[1]
        assert call_kwargs["max_new_tokens"] == DEFAULT_MAX_TOKENS

    @patch("src.evaluation.baseline.AutoModelForCausalLM")
    @patch("src.evaluation.baseline.AutoTokenizer")
    @patch("src.evaluation.baseline.EvaluationPipeline")
    def test_run_teaching_mode_baseline(
        self, mock_pipeline_class, mock_tokenizer, mock_model, mock_test_cases_file
    ):
        """Test running teaching mode baseline."""
        # Setup mocks
        mock_tokenizer_instance = MagicMock()
        mock_tokenizer.from_pretrained.return_value = mock_tokenizer_instance

        mock_model_instance = MagicMock()
        mock_model.from_pretrained.return_value = mock_model_instance
        mock_model_instance.device = "cpu"

        mock_pipeline_instance = MagicMock()
        mock_pipeline_class.return_value = mock_pipeline_instance

        # Mock test cases
        with open(mock_test_cases_file) as f:
            test_cases = json.load(f)
        mock_pipeline_instance.test_cases = test_cases

        # Mock evaluation results
        mock_pipeline_instance.evaluate_teaching_mode.return_value = {
            "total": 5,
            "passed": 4,
            "failed": 1,
        }

        evaluator = BaselineEvaluator(model_name="test-model", test_cases_path=mock_test_cases_file)

        # Mock generate_response
        evaluator.generate_response = MagicMock(return_value="Great response!")

        responses, results = evaluator.run_teaching_mode_baseline(sample_size=5)

        assert len(responses) == 5
        assert results["total"] == 5
        assert results["passed"] == 4
        assert evaluator.generate_response.call_count == 5

    @patch("src.evaluation.baseline.AutoModelForCausalLM")
    @patch("src.evaluation.baseline.AutoTokenizer")
    @patch("src.evaluation.baseline.EvaluationPipeline")
    def test_run_teaching_mode_baseline_uses_default_sample_size(
        self, mock_pipeline_class, mock_tokenizer, mock_model, mock_test_cases_file
    ):
        """Test that run_teaching_mode_baseline uses DEFAULT_SAMPLE_SIZE."""
        mock_tokenizer_instance = MagicMock()
        mock_tokenizer.from_pretrained.return_value = mock_tokenizer_instance

        mock_model_instance = MagicMock()
        mock_model.from_pretrained.return_value = mock_model_instance

        mock_pipeline_instance = MagicMock()
        mock_pipeline_class.return_value = mock_pipeline_instance

        with open(mock_test_cases_file) as f:
            test_cases = json.load(f)
        mock_pipeline_instance.test_cases = test_cases

        mock_pipeline_instance.evaluate_teaching_mode.return_value = {
            "total": DEFAULT_SAMPLE_SIZE,
            "passed": DEFAULT_SAMPLE_SIZE,
            "failed": 0,
        }

        evaluator = BaselineEvaluator(model_name="test-model", test_cases_path=mock_test_cases_file)
        evaluator.generate_response = MagicMock(return_value="Response")

        responses, results = evaluator.run_teaching_mode_baseline()  # No sample_size

        assert len(responses) == DEFAULT_SAMPLE_SIZE

    @patch("src.evaluation.baseline.AutoModelForCausalLM")
    @patch("src.evaluation.baseline.AutoTokenizer")
    @patch("src.evaluation.baseline.EvaluationPipeline")
    def test_run_grading_mode_baseline(
        self, mock_pipeline_class, mock_tokenizer, mock_model, mock_test_cases_file
    ):
        """Test running grading mode baseline."""
        mock_tokenizer_instance = MagicMock()
        mock_tokenizer.from_pretrained.return_value = mock_tokenizer_instance

        mock_model_instance = MagicMock()
        mock_model.from_pretrained.return_value = mock_model_instance
        mock_model_instance.device = "cpu"

        mock_pipeline_instance = MagicMock()
        mock_pipeline_class.return_value = mock_pipeline_instance

        with open(mock_test_cases_file) as f:
            test_cases = json.load(f)
        mock_pipeline_instance.test_cases = test_cases

        mock_pipeline_instance.evaluate_grading_mode.return_value = {
            "total": 5,
            "passed": 5,
            "failed": 0,
        }

        evaluator = BaselineEvaluator(model_name="test-model", test_cases_path=mock_test_cases_file)
        evaluator.generate_response = MagicMock(return_value='{"correct": true}')

        responses, results = evaluator.run_grading_mode_baseline(sample_size=5)

        assert len(responses) == 5
        assert results["total"] == 5

        # Check that generate_response was called with GRADING_MAX_TOKENS
        for call in evaluator.generate_response.call_args_list:
            assert call[1]["max_new_tokens"] == GRADING_MAX_TOKENS

    @patch("src.evaluation.baseline.AutoModelForCausalLM")
    @patch("src.evaluation.baseline.AutoTokenizer")
    @patch("src.evaluation.baseline.EvaluationPipeline")
    def test_save_baseline_report(
        self, mock_pipeline_class, mock_tokenizer, mock_model, mock_test_cases_file, tmp_path
    ):
        """Test saving baseline report."""
        mock_pipeline_instance = MagicMock()
        mock_pipeline_class.return_value = mock_pipeline_instance
        mock_pipeline_instance.generate_report.return_value = "# Mock Report"

        evaluator = BaselineEvaluator(model_name="test-model", test_cases_path=mock_test_cases_file)

        teaching_results = {"total": 5, "passed": 4, "failed": 1}
        grading_results = {"total": 10, "passed": 9, "failed": 1}

        output_path = tmp_path / "baseline_report.md"
        evaluator.save_baseline_report(teaching_results, grading_results, output_path=output_path)

        assert output_path.exists()
        content = output_path.read_text()
        assert "# Baseline Evaluation Report" in content
        assert "test-model" in content
        assert "# Mock Report" in content

    @patch("src.evaluation.baseline.AutoModelForCausalLM")
    @patch("src.evaluation.baseline.AutoTokenizer")
    @patch("src.evaluation.baseline.EvaluationPipeline")
    def test_save_baseline_report_uses_default_path(
        self, mock_pipeline_class, mock_tokenizer, mock_model, mock_test_cases_file
    ):
        """Test that save_baseline_report uses default path when not provided."""
        mock_pipeline_instance = MagicMock()
        mock_pipeline_class.return_value = mock_pipeline_instance
        mock_pipeline_instance.generate_report.return_value = "# Mock Report"

        evaluator = BaselineEvaluator(model_name="test-model", test_cases_path=mock_test_cases_file)

        teaching_results = {"total": 5, "passed": 4, "failed": 1}
        grading_results = {"total": 10, "passed": 9, "failed": 1}

        with patch("builtins.open", create=True) as mock_open:
            evaluator.save_baseline_report(teaching_results, grading_results)

            # Check that open was called with the default path
            assert any(
                str(DEFAULT_BASELINE_REPORT_PATH) in str(call) for call in mock_open.call_args_list
            )
