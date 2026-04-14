"""Tests for baseline evaluation."""

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from src.evaluation.baseline import (
    DEFAULT_BASELINE_REPORT_PATH,
    GRADING_MAX_TOKENS,
    BaselineEvaluator,
)


@pytest.fixture
def mock_test_cases_file(tmp_path):
    """Create a mock test cases JSON file with v2.0 structure."""
    test_cases = {
        "lesson_start": {"test_cases": []},
        "teaching_vocab": {
            "vocab_overview": [],
            "batch_introduction": [
                {
                    "test_id": f"teach_vocab_{i:02d}",
                    "input": {
                        "mode": "teaching_vocab",
                        "lesson_number": 1,
                        "batch_number": 1,
                        "total_batches": 3,
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
            ],
            "list_view": [],
            "quiz_question": [],
            "batch_summary": [],
        },
        "teaching_grammar": {
            "grammar_overview": [],
            "topic_explanation": [],
            "quiz_question": [],
            "topic_summary": [],
        },
        "feedback_vocab": {"correct_feedback": [], "incorrect_feedback": []},
        "feedback_grammar": {"correct_feedback": [], "incorrect_feedback": []},
        "grading_vocab": {
            "correct_translations": [
                {
                    "test_id": f"grade_vocab_{i:02d}",
                    "input": {
                        "mode": "grading_vocab",
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
        "grading_grammar": {"quiz_grading": [], "quiz_incorrect": [], "test_grading": []},
        "exercise_generation": {
            "exercise_gen": [],
            "quiz_question_gen": [],
            "test_composition": [],
        },
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
        """Test evaluator initialization with lazy loading."""
        evaluator = BaselineEvaluator(
            model_3b_name="test-3b", model_7b_name="test-7b", test_cases_path=mock_test_cases_file
        )

        assert evaluator.model_3b_name == "test-3b"
        assert evaluator.model_7b_name == "test-7b"
        assert evaluator.test_cases_path == Path(mock_test_cases_file)
        # Models should NOT be loaded yet (lazy loading)
        mock_tokenizer.from_pretrained.assert_not_called()
        mock_model.from_pretrained.assert_not_called()
        mock_pipeline.assert_called_once_with(mock_test_cases_file)

    @patch("src.evaluation.baseline.AutoModelForCausalLM")
    @patch("src.evaluation.baseline.AutoTokenizer")
    @patch("src.evaluation.baseline.EvaluationPipeline")
    def test_initialization_model_load_failure(self, mock_pipeline, mock_tokenizer, mock_model):
        """Test that RuntimeError is raised when model loading fails (lazy load)."""
        mock_model.from_pretrained.side_effect = Exception("Model not found")

        evaluator = BaselineEvaluator(model_3b_name="invalid-model")

        # Model loading fails on first access (lazy loading)
        with pytest.raises(RuntimeError, match="Failed to load 3B model"):
            _ = evaluator.model_3b

    @patch("src.evaluation.baseline.AutoModelForCausalLM")
    @patch("src.evaluation.baseline.AutoTokenizer")
    def test_initialization_test_cases_not_found(self, mock_tokenizer, mock_model):
        """Test that FileNotFoundError is raised when test cases file doesn't exist."""
        with pytest.raises(FileNotFoundError):
            BaselineEvaluator(test_cases_path="/nonexistent/path/test_cases.json")

    @patch("src.evaluation.baseline.AutoModelForCausalLM")
    @patch("src.evaluation.baseline.AutoTokenizer")
    @patch("src.evaluation.baseline.EvaluationPipeline")
    def test_generate_response(
        self, mock_pipeline, mock_tokenizer, mock_model, mock_test_cases_file
    ):
        """Test response generation with 3B model (default)."""
        # Mock tokenizer and model instances
        mock_tokenizer_instance = MagicMock()
        mock_tokenized_input = MagicMock()
        mock_tokenized_input.to.return_value = mock_tokenized_input
        mock_tokenizer_instance.return_value = mock_tokenized_input

        mock_model_instance = MagicMock()
        mock_model_instance.device = "cpu"
        mock_model_instance.generate.return_value = [[1, 2, 3, 4, 5]]

        mock_tokenizer_instance.decode.return_value = "Test promptGenerated response"
        mock_tokenizer_instance.eos_token_id = 2

        evaluator = BaselineEvaluator(test_cases_path=mock_test_cases_file)

        # Bypass lazy loading by setting mocks directly
        evaluator._tokenizer_3b = mock_tokenizer_instance
        evaluator._model_3b = mock_model_instance

        response = evaluator.generate_response("Test prompt", max_new_tokens=50, use_7b=False)

        assert response == "Generated response"
        mock_model_instance.generate.assert_called_once()

    @patch("src.evaluation.baseline.AutoModelForCausalLM")
    @patch("src.evaluation.baseline.AutoTokenizer")
    @patch("src.evaluation.baseline.EvaluationPipeline")
    def test_run_teaching_vocab_baseline(
        self, mock_pipeline_class, mock_tokenizer, mock_model, mock_test_cases_file
    ):
        """Test running teaching vocab baseline."""
        mock_pipeline_instance = MagicMock()
        mock_pipeline_class.return_value = mock_pipeline_instance

        # Mock test cases
        with open(mock_test_cases_file) as f:
            test_cases = json.load(f)
        mock_pipeline_instance.test_cases = test_cases

        # Mock evaluation results
        mock_pipeline_instance.evaluate_teaching_vocab.return_value = {
            "total": 5,
            "passed": 4,
            "failed": 1,
        }

        evaluator = BaselineEvaluator(test_cases_path=mock_test_cases_file)

        # Mock teaching_agent (property) by setting _teaching_agent directly
        mock_teaching_agent = MagicMock()
        mock_teaching_agent.handle_teaching_vocab = MagicMock(return_value="Great response!")
        evaluator._teaching_agent = mock_teaching_agent

        responses, results = evaluator.run_teaching_vocab_baseline(sample_size=5)

        assert len(responses) == 5
        assert results["total"] == 5
        assert results["passed"] == 4
        assert mock_teaching_agent.handle_teaching_vocab.call_count == 5

    @patch("src.evaluation.baseline.AutoModelForCausalLM")
    @patch("src.evaluation.baseline.AutoTokenizer")
    @patch("src.evaluation.baseline.EvaluationPipeline")
    def test_run_grading_vocab_baseline(
        self, mock_pipeline_class, mock_tokenizer, mock_model, mock_test_cases_file
    ):
        """Test running grading vocab baseline with 7B model."""
        mock_pipeline_instance = MagicMock()
        mock_pipeline_class.return_value = mock_pipeline_instance

        with open(mock_test_cases_file) as f:
            test_cases = json.load(f)
        mock_pipeline_instance.test_cases = test_cases

        mock_pipeline_instance.evaluate_grading_vocab.return_value = {
            "total": 5,
            "passed": 5,
            "failed": 0,
        }

        evaluator = BaselineEvaluator(test_cases_path=mock_test_cases_file)
        evaluator.generate_response = MagicMock(return_value='{"correct": true}')

        responses, results = evaluator.run_grading_vocab_baseline(sample_size=5)

        assert len(responses) == 5
        assert results["total"] == 5

        # Check that generate_response was called with GRADING_MAX_TOKENS and use_7b=True
        for call in evaluator.generate_response.call_args_list:
            assert call[1]["max_new_tokens"] == GRADING_MAX_TOKENS
            assert call[1]["use_7b"] is True

    @patch("src.evaluation.baseline.AutoModelForCausalLM")
    @patch("src.evaluation.baseline.AutoTokenizer")
    @patch("src.evaluation.baseline.EvaluationPipeline")
    def test_save_baseline_report(
        self, mock_pipeline_class, mock_tokenizer, mock_model, mock_test_cases_file, tmp_path
    ):
        """Test saving baseline report with new signature."""
        mock_pipeline_instance = MagicMock()
        mock_pipeline_class.return_value = mock_pipeline_instance
        mock_pipeline_instance.generate_report.return_value = "# Mock Report"

        evaluator = BaselineEvaluator(test_cases_path=mock_test_cases_file)

        results_by_mode = {
            "teaching_vocab": {"total": 5, "passed": 4, "failed": 1},
            "grading_vocab": {"total": 10, "passed": 9, "failed": 1},
        }

        outputs_by_mode = {
            "teaching_vocab": {"teach_vocab_01": "مرحبا means hello"},
            "grading_vocab": {"grade_vocab_01": '{"correct": true}'},
        }

        output_path = tmp_path / "baseline_report.md"
        evaluator.save_baseline_report(results_by_mode, outputs_by_mode, output_path=output_path)

        assert output_path.exists()
        content = output_path.read_text()
        assert "# Baseline Evaluation Report" in content
        assert "Qwen/Qwen2.5-3B-Instruct" in content
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

        evaluator = BaselineEvaluator(test_cases_path=mock_test_cases_file)

        results_by_mode = {
            "teaching_vocab": {"total": 5, "passed": 4, "failed": 1},
            "grading_vocab": {"total": 10, "passed": 9, "failed": 1},
        }

        outputs_by_mode = {
            "teaching_vocab": {"teach_vocab_01": "مرحبا means hello"},
            "grading_vocab": {"grade_vocab_01": '{"correct": true}'},
        }

        with patch("builtins.open", create=True) as mock_open:
            evaluator.save_baseline_report(results_by_mode, outputs_by_mode)

            # Check that open was called with the default path
            assert any(
                str(DEFAULT_BASELINE_REPORT_PATH) in str(call) for call in mock_open.call_args_list
            )
