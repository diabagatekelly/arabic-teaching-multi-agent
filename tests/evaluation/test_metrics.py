"""Tests for custom DeepEval metrics."""

import json

from deepeval.test_case import LLMTestCase

from src.evaluation.metrics import (
    AccuracyMetric,
    FaithfulnessMetric,
    JSONValidityMetric,
    SentimentMetric,
)


class TestSentimentMetric:
    """Tests for SentimentMetric."""

    def test_positive_sentiment_passes_threshold(self):
        """Test that highly positive text passes threshold."""
        metric = SentimentMetric(threshold=0.9, mode="teaching")
        test_case = LLMTestCase(
            input="test_input",
            actual_output="This is wonderful! I'm so excited to learn with you!",
            expected_output="positive",
        )

        score = metric.measure(test_case)

        assert score > 0.9
        assert metric.is_successful()
        assert metric.score == score

    def test_negative_sentiment_fails_threshold(self):
        """Test that negative text fails threshold."""
        metric = SentimentMetric(threshold=0.9, mode="teaching")
        test_case = LLMTestCase(
            input="test_input",
            actual_output="This is terrible and frustrating.",
            expected_output="negative",
        )

        score = metric.measure(test_case)

        assert score < 0.9
        assert not metric.is_successful()

    def test_different_thresholds(self):
        """Test that different thresholds work correctly."""
        test_case = LLMTestCase(
            input="test_input", actual_output="This is pretty good.", expected_output="neutral"
        )

        high_threshold_metric = SentimentMetric(threshold=0.95, mode="teaching")
        low_threshold_metric = SentimentMetric(threshold=0.7, mode="feedback")

        high_score = high_threshold_metric.measure(test_case)
        low_score = low_threshold_metric.measure(test_case)

        # Same score for both, but different success status
        assert high_score == low_score
        # May pass lower threshold but not higher
        if high_score < 0.95:
            assert not high_threshold_metric.is_successful()
        if low_score >= 0.7:
            assert low_threshold_metric.is_successful()

    def test_sentiment_pipeline_cached(self):
        """Test that sentiment pipeline is a class-level singleton."""
        # Create first instance - should load pipeline
        metric1 = SentimentMetric(threshold=0.9, mode="teaching")

        # Pipeline should be at class level
        assert SentimentMetric._shared_sentiment_pipeline is not None

        # Store reference to the pipeline
        pipeline_instance = SentimentMetric._shared_sentiment_pipeline

        # Create second instance - should NOT reload pipeline
        metric2 = SentimentMetric(threshold=0.8, mode="feedback")

        # Should still be the same pipeline instance (singleton)
        assert SentimentMetric._shared_sentiment_pipeline is pipeline_instance

        # Both metrics should use the same pipeline
        test_case = LLMTestCase(input="test", actual_output="Great!", expected_output="positive")
        metric1.measure(test_case)
        metric2.measure(test_case)

    def test_metric_name(self):
        """Test metric name property."""
        teaching_metric = SentimentMetric(threshold=0.9, mode="teaching")
        feedback_metric = SentimentMetric(threshold=0.8, mode="feedback")

        assert teaching_metric.__name__ == "Sentiment (teaching)"
        assert feedback_metric.__name__ == "Sentiment (feedback)"


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
        assert metric.parsed_json == {"correct": True}

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
        assert metric.parsed_json == {"correct": True}

    def test_json_in_generic_code_block(self):
        """Test that JSON in generic code blocks is extracted."""
        metric = JSONValidityMetric()
        test_case = LLMTestCase(
            input="test_input", actual_output='```\n{"correct": false}\n```', expected_output="{}"
        )

        score = metric.measure(test_case)

        assert score == 1.0
        assert metric.is_successful()
        assert metric.parsed_json == {"correct": False}

    def test_complex_json(self):
        """Test that complex JSON structures are parsed correctly."""
        metric = JSONValidityMetric()
        complex_json = json.dumps(
            {
                "correct": True,
                "score": 0.95,
                "feedback": "Great job!",
                "details": {"word": "hello", "translation": "مرحبا"},
            }
        )
        test_case = LLMTestCase(
            input="test_input", actual_output=complex_json, expected_output="{}"
        )

        score = metric.measure(test_case)

        assert score == 1.0
        assert metric.is_successful()
        assert metric.parsed_json["correct"] is True
        assert metric.parsed_json["score"] == 0.95

    def test_metric_name(self):
        """Test metric name property."""
        metric = JSONValidityMetric()
        assert metric.__name__ == "JSON Validity"


class TestAccuracyMetric:
    """Tests for AccuracyMetric."""

    def test_correct_classification_as_correct(self):
        """Test correct answer classified as correct."""
        metric = AccuracyMetric()
        test_case = LLMTestCase(
            input="test_input",
            actual_output='{"correct": true}',
            expected_output="true",  # DeepEval expects string
        )
        # Override expected_output for our metric logic
        test_case.expected_output = True

        score = metric.measure(test_case)

        assert score == 1.0
        assert metric.is_successful()
        assert "Correctly classified as correct" in metric.reason

    def test_correct_classification_as_incorrect(self):
        """Test incorrect answer classified as incorrect."""
        metric = AccuracyMetric()
        test_case = LLMTestCase(
            input="test_input", actual_output='{"correct": false}', expected_output="false"
        )
        test_case.expected_output = False

        score = metric.measure(test_case)

        assert score == 1.0
        assert metric.is_successful()
        assert "Correctly classified as incorrect" in metric.reason

    def test_wrong_classification_correct_as_incorrect(self):
        """Test misclassification: correct answer marked as incorrect."""
        metric = AccuracyMetric()
        test_case = LLMTestCase(
            input="test_input", actual_output='{"correct": false}', expected_output="true"
        )
        test_case.expected_output = True

        score = metric.measure(test_case)

        assert score == 0.0
        assert not metric.is_successful()
        assert "Expected correct, got False" in metric.reason

    def test_wrong_classification_incorrect_as_correct(self):
        """Test misclassification: incorrect answer marked as correct."""
        metric = AccuracyMetric()
        test_case = LLMTestCase(
            input="test_input", actual_output='{"correct": true}', expected_output="false"
        )
        test_case.expected_output = False

        score = metric.measure(test_case)

        assert score == 0.0
        assert not metric.is_successful()
        assert "Expected incorrect, got True" in metric.reason

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

    def test_non_dict_output(self):
        """Test that non-dict JSON output fails."""
        metric = AccuracyMetric()
        test_case = LLMTestCase(
            input="test_input",
            actual_output='["correct", "answer"]',  # Valid JSON but not a dict
            expected_output="true",
        )
        test_case.expected_output = True

        score = metric.measure(test_case)

        assert score == 0.0
        assert not metric.is_successful()
        assert "not a dict" in metric.reason

    def test_metric_name(self):
        """Test metric name property."""
        metric = AccuracyMetric()
        assert metric.__name__ == "Accuracy"


class TestFaithfulnessMetric:
    """Tests for FaithfulnessMetric."""

    def test_all_fields_present(self):
        """Test that exercises with all required fields pass."""
        metric = FaithfulnessMetric(threshold=0.9)
        test_case = LLMTestCase(
            input="test_input",
            actual_output=json.dumps(
                [{"question": "Q1", "answer": "A1"}, {"question": "Q2", "answer": "A2"}]
            ),
            expected_output='["question", "answer"]',  # DeepEval expects string
        )
        # Override for our metric logic
        test_case.expected_output = ["question", "answer"]

        score = metric.measure(test_case)

        assert score == 1.0
        assert metric.is_successful()
        assert "4/4 fields present" in metric.reason

    def test_some_fields_missing(self):
        """Test that exercises with missing fields have lower score."""
        metric = FaithfulnessMetric(threshold=0.9)
        test_case = LLMTestCase(
            input="test_input",
            actual_output=json.dumps(
                [
                    {"question": "Q1"},  # Missing "answer"
                    {"question": "Q2", "answer": "A2"},
                ]
            ),
            expected_output='["question", "answer"]',
        )
        test_case.expected_output = ["question", "answer"]

        score = metric.measure(test_case)

        assert score == 0.75  # 3/4 fields present
        assert not metric.is_successful()
        assert "3/4 fields present" in metric.reason

    def test_non_list_output(self):
        """Test that non-list output fails."""
        metric = FaithfulnessMetric(threshold=0.9)
        test_case = LLMTestCase(
            input="test_input",
            actual_output='{"question": "Q1", "answer": "A1"}',  # Dict, not list
            expected_output='["question", "answer"]',
        )
        test_case.expected_output = ["question", "answer"]

        score = metric.measure(test_case)

        assert score == 0.0
        assert not metric.is_successful()
        assert "not a list" in metric.reason

    def test_empty_list(self):
        """Test that empty list returns 0 score."""
        metric = FaithfulnessMetric(threshold=0.9)
        test_case = LLMTestCase(
            input="test_input", actual_output="[]", expected_output='["question", "answer"]'
        )
        test_case.expected_output = ["question", "answer"]

        score = metric.measure(test_case)

        assert score == 0.0
        assert not metric.is_successful()

    def test_invalid_json(self):
        """Test that invalid JSON fails."""
        metric = FaithfulnessMetric(threshold=0.9)
        test_case = LLMTestCase(
            input="test_input",
            actual_output='[{"question": "Q1"',  # Invalid JSON
            expected_output='["question", "answer"]',
        )
        test_case.expected_output = ["question", "answer"]

        score = metric.measure(test_case)

        assert score == 0.0
        assert not metric.is_successful()
        assert "Parsing error" in metric.reason

    def test_different_threshold(self):
        """Test that different thresholds work correctly."""
        test_case = LLMTestCase(
            input="test_input",
            actual_output=json.dumps(
                [
                    {"question": "Q1"}  # Missing "answer"
                ]
            ),
            expected_output='["question", "answer"]',
        )
        test_case.expected_output = ["question", "answer"]

        high_threshold_metric = FaithfulnessMetric(threshold=0.9)
        low_threshold_metric = FaithfulnessMetric(threshold=0.4)

        high_score = high_threshold_metric.measure(test_case)
        low_score = low_threshold_metric.measure(test_case)

        assert high_score == 0.5
        assert low_score == 0.5
        assert not high_threshold_metric.is_successful()  # 0.5 < 0.9
        assert low_threshold_metric.is_successful()  # 0.5 >= 0.4

    def test_metric_name(self):
        """Test metric name property."""
        metric = FaithfulnessMetric(threshold=0.9)
        assert metric.__name__ == "Faithfulness"
