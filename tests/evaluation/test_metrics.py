"""Tests for custom DeepEval metrics."""

import json
from unittest.mock import MagicMock, patch

import pytest
from deepeval.test_case import LLMTestCase

from src.evaluation.metrics import (
    AccuracyMetric,
    AlignmentMetric,
    JSONValidityMetric,
    SentimentMetric,
    StructureMetric,
)


@pytest.fixture(autouse=True)
def reset_sentiment_singleton():
    """Reset SentimentMetric singleton before each test."""
    SentimentMetric._shared_sentiment_pipeline = None
    yield
    # Cleanup after test
    SentimentMetric._shared_sentiment_pipeline = None


class TestSentimentMetric:
    """Tests for SentimentMetric."""

    @patch("src.evaluation.metrics.pipeline")
    def test_positive_sentiment_passes_threshold(self, mock_pipeline):
        """Test that highly positive text passes threshold."""
        # Mock the sentiment pipeline to return high positive score
        mock_pipeline_instance = MagicMock()
        mock_pipeline_instance.return_value = [{"label": "POSITIVE", "score": 0.95}]
        mock_pipeline.return_value = mock_pipeline_instance

        metric = SentimentMetric(threshold=0.9, mode="teaching")
        test_case = LLMTestCase(
            input="test_input",
            actual_output="This is wonderful! I'm so excited to learn with you!",
            expected_output="positive",
        )

        score = metric.measure(test_case)

        assert score >= 0.9  # Strengthened: >= instead of >
        assert metric.is_successful()
        assert metric.score == score

    @patch("src.evaluation.metrics.pipeline")
    def test_negative_sentiment_fails_threshold(self, mock_pipeline):
        """Test that negative text fails threshold."""
        # Mock the sentiment pipeline to return negative score
        mock_pipeline_instance = MagicMock()
        mock_pipeline_instance.return_value = [{"label": "NEGATIVE", "score": 0.85}]
        mock_pipeline.return_value = mock_pipeline_instance

        metric = SentimentMetric(threshold=0.9, mode="teaching")
        test_case = LLMTestCase(
            input="test_input",
            actual_output="This is terrible and frustrating.",
            expected_output="negative",
        )

        score = metric.measure(test_case)

        assert score < 0.9
        assert not metric.is_successful()

    @patch("src.evaluation.metrics.pipeline")
    def test_sentiment_pipeline_cached(self, mock_pipeline):
        """Test that sentiment pipeline is a class-level singleton."""
        # Mock the sentiment pipeline
        mock_pipeline_instance = MagicMock()
        mock_pipeline_instance.return_value = [{"label": "POSITIVE", "score": 0.95}]
        mock_pipeline.return_value = mock_pipeline_instance

        # Create first instance - should load pipeline
        metric1 = SentimentMetric(threshold=0.9, mode="teaching")

        # Pipeline should be loaded exactly once
        mock_pipeline.assert_called_once()

        # Pipeline should be at class level
        assert SentimentMetric._shared_sentiment_pipeline is not None

        # Store reference to the pipeline
        pipeline_instance = SentimentMetric._shared_sentiment_pipeline

        # Create second instance - should NOT reload pipeline
        metric2 = SentimentMetric(threshold=0.8, mode="feedback")

        # Still only called once (singleton behavior)
        mock_pipeline.assert_called_once()

        # Should still be the same pipeline instance (singleton)
        assert SentimentMetric._shared_sentiment_pipeline is pipeline_instance

        # Both metrics should use the same pipeline
        test_case = LLMTestCase(input="test", actual_output="Great!", expected_output="positive")
        metric1.measure(test_case)
        metric2.measure(test_case)


class TestJSONValidityMetric:
    """Tests for JSONValidityMetric."""

    def test_valid_json(self):
        """Test that valid JSON passes."""
        metric = JSONValidityMetric()
        test_case = LLMTestCase(
            input="test_input",
            actual_output='{"correct": true}',
            expected_output="{}",  # DeepEval expects string
        )

        score = metric.measure(test_case)

        assert score == 1.0
        assert metric.is_successful()

    def test_invalid_json(self):
        """Test that invalid JSON fails."""
        metric = JSONValidityMetric()
        test_case = LLMTestCase(
            input="test_input",
            actual_output='{"correct": true',  # Missing closing brace
            expected_output="{}",
        )

        score = metric.measure(test_case)

        assert score == 0.0
        assert not metric.is_successful()
        assert "Invalid JSON" in metric.reason

    def test_json_in_markdown_code_block(self):
        """Test that JSON in markdown code blocks is extracted."""
        metric = JSONValidityMetric()
        test_case = LLMTestCase(
            input="test_input",
            actual_output='```json\n{"correct": true}\n```',
            expected_output="{}",
        )

        score = metric.measure(test_case)

        assert score == 1.0
        assert metric.is_successful()


class TestStructureMetric:
    """Tests for StructureMetric."""

    def test_valid_dict_structure_with_all_required_keys(self):
        """Test that valid dict structure with all required keys passes."""
        metric = StructureMetric(
            expected_type=dict, required_keys=["correct"], expected_types={"correct": bool}
        )
        test_case = LLMTestCase(
            input="test_input", actual_output='{"correct": true}', expected_output="{}"
        )

        score = metric.measure(test_case)

        assert score == 1.0
        assert metric.is_successful()
        assert "Valid structure" in metric.reason

    def test_missing_required_key(self):
        """Test that missing required key fails."""
        metric = StructureMetric(expected_type=dict, required_keys=["correct"])
        test_case = LLMTestCase(
            input="test_input", actual_output='{"status": "done"}', expected_output="{}"
        )

        score = metric.measure(test_case)

        assert score == 0.0
        assert not metric.is_successful()
        assert "Missing required keys: ['correct']" in metric.reason

    def test_wrong_top_level_type(self):
        """Test that wrong top-level type fails."""
        metric = StructureMetric(expected_type=dict, required_keys=["correct"])
        test_case = LLMTestCase(
            input="test_input", actual_output='["correct"]', expected_output="{}"
        )

        score = metric.measure(test_case)

        assert score == 0.0
        assert not metric.is_successful()
        assert "Expected dict, got list" in metric.reason

    def test_wrong_value_type(self):
        """Test that wrong value type fails."""
        metric = StructureMetric(
            expected_type=dict, required_keys=["correct"], expected_types={"correct": bool}
        )
        test_case = LLMTestCase(
            input="test_input", actual_output='{"correct": "true"}', expected_output="{}"
        )

        score = metric.measure(test_case)

        assert score == 0.0
        assert not metric.is_successful()
        assert "Key 'correct': expected bool, got str" in metric.reason

    def test_valid_list_structure(self):
        """Test that valid list structure passes."""
        metric = StructureMetric(
            expected_type=list,
            required_keys=["question", "answer"],
            expected_types={"question": str, "answer": str},
        )
        test_case = LLMTestCase(
            input="test_input",
            actual_output='[{"question": "Q1", "answer": "A1"}]',
            expected_output="[]",
        )

        score = metric.measure(test_case)

        assert score == 1.0
        assert metric.is_successful()
        assert "Valid structure" in metric.reason

    def test_empty_list(self):
        """Test that empty list fails."""
        metric = StructureMetric(expected_type=list, required_keys=["question", "answer"])
        test_case = LLMTestCase(input="test_input", actual_output="[]", expected_output="[]")

        score = metric.measure(test_case)

        assert score == 0.0
        assert not metric.is_successful()
        assert "Expected non-empty list" in metric.reason


class TestAccuracyMetric:
    """Tests for AccuracyMetric."""

    @pytest.mark.parametrize(
        "actual,expected,should_pass,expected_reason",
        [
            (True, True, True, "Correctly classified as correct"),  # True Positive
            (False, False, True, "Correctly classified as incorrect"),  # True Negative
            (False, True, False, "Expected correct, got False"),  # False Negative
            (True, False, False, "Expected incorrect, got True"),  # False Positive
        ],
    )
    def test_accuracy_classification(self, actual, expected, should_pass, expected_reason):
        """Test all accuracy classification combinations."""
        metric = AccuracyMetric()
        test_case = LLMTestCase(
            input="test_input",
            actual_output=f'{{"correct": {str(actual).lower()}}}',
            expected_output=str(expected).lower(),
        )
        test_case.expected_output = expected

        score = metric.measure(test_case)

        assert (score == 1.0) == should_pass
        assert metric.is_successful() == should_pass
        assert expected_reason in metric.reason

    def test_invalid_json_format(self):
        """Test that invalid JSON returns 0 score."""
        metric = AccuracyMetric()
        test_case = LLMTestCase(
            input="test_input",
            actual_output='{"correct": true',  # Invalid JSON
            expected_output="true",
        )
        test_case.expected_output = True

        score = metric.measure(test_case)

        assert score == 0.0
        assert not metric.is_successful()
        assert "Parsing error" in metric.reason


class TestAlignmentMetric:
    """Tests for AlignmentMetric."""

    @patch("src.evaluation.metrics.AlignmentMetric._query_judge")
    def test_high_alignment_passes(self, mock_query_judge):
        """Test that high alignment score passes threshold."""
        mock_query_judge.return_value = "Overall: 0.9\nReasoning: Excellent alignment"

        metric = AlignmentMetric(threshold=0.8)
        test_case = LLMTestCase(
            input=json.dumps(
                {
                    "exercise_type": "fill_in_blank",
                    "learned_vocab": ["word1"],
                    "grammar_rule": "test rule",
                }
            ),
            actual_output=json.dumps({"question": "Test question", "answer": "Test answer"}),
            expected_output="{}",
        )

        score = metric.measure(test_case)

        assert score == 0.9
        assert metric.is_successful()
        assert "0.9" in metric.reason

    @patch("src.evaluation.metrics.AlignmentMetric._query_judge")
    def test_parsing_error_returns_zero(self, mock_query_judge):
        """Test that unparseable judge response returns 0."""
        mock_query_judge.return_value = "Some random text without score"

        metric = AlignmentMetric(threshold=0.8)
        test_case = LLMTestCase(
            input=json.dumps({"exercise_type": "test"}),
            actual_output=json.dumps({"question": "Q", "answer": "A"}),
            expected_output="{}",
        )

        score = metric.measure(test_case)

        assert score == 0.0
        assert not metric.is_successful()
