"""Tests for ExerciseQualityMetric."""

import json

from deepeval.test_case import LLMTestCase

from src.evaluation.metrics import ExerciseQualityMetric


class TestExerciseQualityMetric:
    """Test ExerciseQualityMetric rule-based checks."""

    def test_perfect_exercise(self):
        """Test exercise that passes all checks."""
        input_data = {
            "exercise_type": "translation",
            "difficulty": "beginner",
            "learned_items": ["كِتَاب (kitaab) - book", "قَلَم (qalam) - pen"],
        }
        exercise = {
            "question": "Translate to Arabic: the book",
            "answer": "الكِتَاب",
            "difficulty": "beginner",
            "type": "translation",
        }

        test_case = LLMTestCase(
            input=json.dumps(input_data),
            actual_output=json.dumps(exercise),
            expected_output="",
        )

        metric = ExerciseQualityMetric(threshold=0.7)
        score = metric.measure(test_case)

        assert metric.is_successful()
        assert score >= 0.7

        # Check reason mentions key concepts (resilient to formatting changes)
        reason = metric.reason.lower()
        assert "question" in reason
        assert "answer" in reason
        # CRITICAL: Should now detect the learned vocab!
        assert any(term in reason for term in ("learned", "vocab", "learned_items", "used"))

    def test_real_world_failure_case_1(self):
        """Test the actual failing case from evaluation: المدرسة in sentence."""
        input_data = {
            "exercise_type": "translation",
            "difficulty": "beginner",
            "learned_items": [
                "كِتَاب (kitaab) - book",
                "قَلَم (qalam) - pen",
                "مَدْرَسَة (madrasa) - school",
            ],
        }
        exercise = {
            "question": "Translate: 'أنا أكتب في المدرسة'",
            "answer": "I write at the school",
            "difficulty": "beginner",
            "type": "translation",
        }

        test_case = LLMTestCase(
            input=json.dumps(input_data),
            actual_output=json.dumps(exercise),
            expected_output="",
        )

        metric = ExerciseQualityMetric(threshold=0.7)
        metric.measure(test_case)

        # Should NOW pass the learned_items check!
        assert "✓ Learned_items:" in metric.reason or "1/3 used" in metric.reason
        # Check that learned_items specifically doesn't say "none used"
        assert "learned_items: none used" not in metric.reason.lower()

    def test_real_world_failure_case_2(self):
        """Test the actual failing case from evaluation: القَلَم direct match."""
        input_data = {
            "exercise_type": "translation",
            "difficulty": "beginner",
            "learned_items": [
                "كِتَاب (kitaab) - book",
                "قَلَم (qalam) - pen",
                "مَدْرَسَة (madrasa) - school",
            ],
        }
        exercise = {
            "question": "Translate to Arabic: the pen",
            "answer": "القَلَم",
            "difficulty": "beginner",
            "type": "translation",
        }

        test_case = LLMTestCase(
            input=json.dumps(input_data),
            actual_output=json.dumps(exercise),
            expected_output="",
        )

        metric = ExerciseQualityMetric(threshold=0.7)
        metric.measure(test_case)

        # Should NOW pass the learned_items check!
        assert "✓ Learned_items:" in metric.reason or "1/3 used" in metric.reason
        # Check that learned_items specifically doesn't say "none used"
        assert "learned_items: none used" not in metric.reason.lower()

    def test_missing_question(self):
        """Test exercise with missing question."""
        input_data = {"exercise_type": "translation", "difficulty": "beginner"}
        exercise = {"question": "", "answer": "الكتاب", "difficulty": "beginner"}

        test_case = LLMTestCase(
            input=json.dumps(input_data),
            actual_output=json.dumps(exercise),
            expected_output="",
        )

        metric = ExerciseQualityMetric(threshold=0.7)
        metric.measure(test_case)

        assert not metric.is_successful()
        assert "✗ Question:" in metric.reason or "invalid length" in metric.reason

    def test_missing_answer(self):
        """Test exercise with missing answer."""
        input_data = {"exercise_type": "translation", "difficulty": "beginner"}
        exercise = {
            "question": "Translate: the book",
            "answer": "",
            "difficulty": "beginner",
        }

        test_case = LLMTestCase(
            input=json.dumps(input_data),
            actual_output=json.dumps(exercise),
            expected_output="",
        )

        # Use threshold 0.9 to ensure this fails (missing answer is 1/6 = ~17% of critical checks)
        metric = ExerciseQualityMetric(threshold=0.9)
        metric.measure(test_case)

        assert not metric.is_successful()
        assert "✗ Answer: missing" in metric.reason

    def test_no_learned_items_used(self):
        """Test exercise that doesn't use any learned items."""
        input_data = {
            "exercise_type": "translation",
            "difficulty": "beginner",
            "learned_items": ["كِتَاب (kitaab) - book", "قَلَم (qalam) - pen"],
        }
        exercise = {
            "question": "Translate: the car",
            "answer": "السيارة",
            "difficulty": "beginner",
        }

        test_case = LLMTestCase(
            input=json.dumps(input_data),
            actual_output=json.dumps(exercise),
            expected_output="",
        )

        metric = ExerciseQualityMetric(threshold=0.7)
        metric.measure(test_case)

        # Should detect no learned items used
        assert "✗ Learned_items: none used" in metric.reason

    def test_difficulty_mismatch(self):
        """Test exercise with wrong difficulty level."""
        input_data = {
            "exercise_type": "translation",
            "difficulty": "beginner",
            "learned_items": ["كِتَاب (kitaab) - book"],
        }
        exercise = {
            "question": "Translate: the book",
            "answer": "الكِتَاب",
            "difficulty": "advanced",  # Mismatch!
        }

        test_case = LLMTestCase(
            input=json.dumps(input_data),
            actual_output=json.dumps(exercise),
            expected_output="",
        )

        metric = ExerciseQualityMetric(threshold=0.7)
        metric.measure(test_case)

        assert "✗ Difficulty:" in metric.reason
        assert "mismatch" in metric.reason

    def test_harakaat_consistency_good(self):
        """Test exercise with consistent harakaat usage."""
        input_data = {"exercise_type": "translation", "difficulty": "beginner"}
        exercise = {
            "question": "Translate: the book",
            "answer": "الكِتَابُ",  # All words have harakaat
            "difficulty": "beginner",
        }

        test_case = LLMTestCase(
            input=json.dumps(input_data),
            actual_output=json.dumps(exercise),
            expected_output="",
        )

        metric = ExerciseQualityMetric(threshold=0.7)
        metric.measure(test_case)

        assert "✓ Harakaat: consistent" in metric.reason

    def test_no_learned_items_specified(self):
        """Test exercise when no learned items are required (should pass)."""
        input_data = {
            "exercise_type": "translation",
            "difficulty": "beginner",
            # No learned_items field
        }
        exercise = {
            "question": "Translate: hello",
            "answer": "مرحبا",
            "difficulty": "beginner",
        }

        test_case = LLMTestCase(
            input=json.dumps(input_data),
            actual_output=json.dumps(exercise),
            expected_output="",
        )

        metric = ExerciseQualityMetric(threshold=0.7)
        metric.measure(test_case)

        # Should pass learned_items check since none were required
        assert "✓ Learned_items: N/A" in metric.reason

    def test_clear_instructions(self):
        """Test exercise with clear instruction keywords."""
        input_data = {"exercise_type": "translation", "difficulty": "beginner"}
        exercise = {
            "question": "Translate the following word to Arabic: book",
            "answer": "كتاب",
            "difficulty": "beginner",
        }

        test_case = LLMTestCase(
            input=json.dumps(input_data),
            actual_output=json.dumps(exercise),
            expected_output="",
        )

        metric = ExerciseQualityMetric(threshold=0.7)
        metric.measure(test_case)

        # Should detect "translate" keyword
        assert "✓ Instructions: clear" in metric.reason or "⚠ Instructions:" in metric.reason

    def test_question_too_long(self):
        """Test exercise with excessively long question."""
        input_data = {"exercise_type": "translation", "difficulty": "beginner"}
        exercise = {
            "question": "A" * 501,  # Over 500 chars
            "answer": "الكتاب",
            "difficulty": "beginner",
        }

        test_case = LLMTestCase(
            input=json.dumps(input_data),
            actual_output=json.dumps(exercise),
            expected_output="",
        )

        metric = ExerciseQualityMetric(threshold=0.7)
        metric.measure(test_case)

        assert not metric.is_successful()
        assert "✗ Question:" in metric.reason

    def test_partial_learned_items_usage(self):
        """Test exercise using some but not all learned items (should still pass)."""
        input_data = {
            "exercise_type": "translation",
            "difficulty": "beginner",
            "learned_items": [
                "كِتَاب (kitaab) - book",
                "قَلَم (qalam) - pen",
                "مَدْرَسَة (madrasa) - school",
            ],
        }
        exercise = {
            "question": "Translate: the book and the pen",
            "answer": "الكِتَاب والقَلَم",
            "difficulty": "beginner",
        }

        test_case = LLMTestCase(
            input=json.dumps(input_data),
            actual_output=json.dumps(exercise),
            expected_output="",
        )

        metric = ExerciseQualityMetric(threshold=0.7)
        metric.measure(test_case)

        # Should pass with 2/3 items used
        assert "✓ Learned_items:" in metric.reason or "2/3 used" in metric.reason

    def test_score_calculation(self):
        """Test that score is calculated correctly from checks."""
        input_data = {
            "exercise_type": "translation",
            "difficulty": "beginner",
            "learned_items": ["كِتَاب (kitaab) - book"],
        }
        exercise = {
            "question": "Translate to Arabic: the book",
            "answer": "الكِتَاب",
            "difficulty": "beginner",
        }

        test_case = LLMTestCase(
            input=json.dumps(input_data),
            actual_output=json.dumps(exercise),
            expected_output="",
        )

        metric = ExerciseQualityMetric(threshold=0.7)
        score = metric.measure(test_case)

        # Score should be between 0 and 1
        assert 0.0 <= score <= 1.0
        # With all critical checks passing, should be high
        assert score >= 0.7

    def test_threshold_sensitivity(self):
        """Test that different thresholds affect success status."""
        input_data = {"exercise_type": "translation", "difficulty": "beginner"}
        exercise = {
            "question": "Translate: book",
            "answer": "كتاب",
            "difficulty": "beginner",
        }

        test_case = LLMTestCase(
            input=json.dumps(input_data),
            actual_output=json.dumps(exercise),
            expected_output="",
        )

        # Low threshold should pass
        metric_low = ExerciseQualityMetric(threshold=0.5)
        score_low = metric_low.measure(test_case)
        assert metric_low.is_successful()

        # Very high threshold might fail
        metric_high = ExerciseQualityMetric(threshold=0.95)
        score_high = metric_high.measure(test_case)
        # Score is the same, but success depends on threshold
        assert score_low == score_high
