"""Evaluation metrics for Agent 3 (Content/Exercise Generation Agent)."""

import json
import logging
import re

from deepeval.metrics import BaseMetric
from deepeval.test_case import LLMTestCase
from transformers import pipeline

from .shared_metrics import extract_json

logger = logging.getLogger(__name__)


class ExerciseQualityMetric(BaseMetric):
    """
    Evaluates exercise quality for Agent 3 (Content) using hybrid strategy.

    Tier 1 (Fast, Always Run): Rule-based checks for universal properties
    Tier 2 (Slow, Sample): LLM-as-judge for semantic quality

    Universal Properties (all exercises must have):
    1. Question field (not empty, >10 chars, <500 chars)
    2. Answer field (not empty)
    3. Uses >=1 learned vocab/grammar item
    4. No exact duplicates in batch
    5. Target difficulty level specified
    6. Cultural appropriateness (no offensive content)
    7. Harakaat consistency
    8. Instructions clarity
    9. Answer format specification

    Type-Specific Checks (based on exercise_type):
    - multiple_choice: has options field (2-6 options)
    - paradigm_table: has table structure (rows/cols)
    - transformation_chain: has steps list (2+ transformations)
    """

    # Class-level singleton for LLM judge (7B model)
    _shared_llm_judge = None

    # Offensive content patterns (basic check)
    OFFENSIVE_PATTERNS = [
        r"\b(kill|murder|death|hate|violence)\b",
        r"\b(stupid|dumb|idiot)\b",
    ]

    # Exercise types that require type-specific checks
    TYPE_SPECIFIC_FIELDS = {
        "multiple_choice": {"field": "options", "validator": "_validate_options"},
        "paradigm_table": {"field": "table", "validator": "_validate_table"},
        "transformation_chain": {"field": "steps", "validator": "_validate_steps"},
    }

    def __init__(
        self,
        learned_items: list[str] | None = None,
        batch_exercises: list[dict] | None = None,
        use_llm_judge: bool = False,
        llm_judge_threshold: float = 0.7,
    ) -> None:
        """
        Initialize exercise quality metric.

        Args:
            learned_items: List of learned vocab/grammar items to check usage
            batch_exercises: Full batch of exercises for duplicate detection
            use_llm_judge: Whether to use Tier 2 LLM judge (slow, for sampling)
            llm_judge_threshold: Minimum score required from LLM judge (0-1)
        """
        # Required by DeepEval
        self.score = 0.0
        self.reason = ""
        self.success = False

        # Configuration
        self.learned_items = learned_items or []
        self.batch_exercises = batch_exercises or []
        self.use_llm_judge = use_llm_judge
        self.llm_judge_threshold = llm_judge_threshold

        # Load LLM judge once at class level (singleton pattern)
        if use_llm_judge and ExerciseQualityMetric._shared_llm_judge is None:
            logger.info("Loading LLM judge model (first time)...")
            ExerciseQualityMetric._shared_llm_judge = pipeline(
                "text-generation",
                model="distilgpt2",  # Using lightweight model for judge
                max_length=200,
            )
            logger.info("LLM judge model loaded and cached")

    def measure(self, test_case: LLMTestCase) -> float:
        """
        Measure exercise quality using Tier 1 (rule-based) checks.

        Args:
            test_case: Test case with actual_output (exercise JSON)

        Returns:
            Quality score (0-1)
        """
        try:
            # Parse exercise JSON
            exercise = self._parse_exercise(test_case.actual_output)

            # Tier 1: Rule-based checks (fast, always run)
            tier1_score, tier1_reasons = self._tier1_checks(exercise)

            # Tier 2: LLM judge (slow, optional)
            if self.use_llm_judge and tier1_score >= 0.7:
                tier2_score, tier2_reason = self._check_with_llm_judge(exercise)
                final_score = (tier1_score * 0.6) + (tier2_score * 0.4)
                reasons = tier1_reasons + [tier2_reason]
            else:
                final_score = tier1_score
                reasons = tier1_reasons

            # Set final state
            self.score = final_score
            self.success = final_score >= 0.8
            self.reason = " | ".join(reasons)

            return self.score

        except (json.JSONDecodeError, KeyError, ValueError) as e:
            return self._set_failure(f"Parsing error: {str(e)}")

    def _parse_exercise(self, output: str) -> dict:
        """Extract and parse exercise JSON."""
        json_str = extract_json(output)
        return json.loads(json_str)

    def _tier1_checks(self, exercise: dict) -> tuple[float, list[str]]:
        """
        Tier 1: Fast rule-based checks for universal properties.

        Returns:
            Tuple of (score, list of reason strings)
        """
        checks = []
        reasons = []

        # 1. Question field validation
        question_score, question_reason = self._check_question_field(exercise)
        checks.append(question_score)
        reasons.append(question_reason)

        # 2. Answer field validation
        answer_score, answer_reason = self._check_answer_field(exercise)
        checks.append(answer_score)
        reasons.append(answer_reason)

        # 3. Learned items usage
        if self.learned_items:
            learned_score, learned_reason = self._check_learned_items(exercise)
            checks.append(learned_score)
            reasons.append(learned_reason)

        # 4. Duplicate detection
        if self.batch_exercises:
            dup_score, dup_reason = self._check_duplicates(exercise)
            checks.append(dup_score)
            reasons.append(dup_reason)

        # 5. Difficulty level
        diff_score, diff_reason = self._check_difficulty_level(exercise)
        checks.append(diff_score)
        reasons.append(diff_reason)

        # 6. Cultural appropriateness
        cultural_score, cultural_reason = self._check_cultural_appropriateness(exercise)
        checks.append(cultural_score)
        reasons.append(cultural_reason)

        # 7. Harakaat consistency
        harakaat_score, harakaat_reason = self._check_harakaat_consistency(exercise)
        checks.append(harakaat_score)
        reasons.append(harakaat_reason)

        # 8. Instructions clarity
        instr_score, instr_reason = self._check_instructions_clarity(exercise)
        checks.append(instr_score)
        reasons.append(instr_reason)

        # 9. Answer format specification
        format_score, format_reason = self._check_answer_format(exercise)
        checks.append(format_score)
        reasons.append(format_reason)

        # 10. Type-specific checks
        type_score, type_reason = self._check_type_specific(exercise)
        if type_score is not None:
            checks.append(type_score)
            reasons.append(type_reason)

        # Calculate average score
        avg_score = sum(checks) / len(checks) if checks else 0.0

        return avg_score, reasons

    def _check_question_field(self, exercise: dict) -> tuple[float, str]:
        """Check question field: not empty, >10 chars, <500 chars."""
        question = exercise.get("question", "").strip()

        if not question:
            return 0.0, "✗ Question: empty"
        if len(question) < 10:
            return 0.5, f"⚠ Question: too short ({len(question)} chars)"
        if len(question) > 500:
            return 0.5, f"⚠ Question: too long ({len(question)} chars)"

        return 1.0, f"✓ Question: valid ({len(question)} chars)"

    def _check_answer_field(self, exercise: dict) -> tuple[float, str]:
        """Check answer field: not empty."""
        answer = exercise.get("answer")

        if answer is None or (isinstance(answer, str) and not answer.strip()):
            return 0.0, "✗ Answer: empty"

        return 1.0, "✓ Answer: present"

    def _check_learned_items(self, exercise: dict) -> tuple[float, str]:
        """Check if exercise uses >=1 learned vocab/grammar item."""
        question = exercise.get("question", "").lower()
        answer = str(exercise.get("answer", "")).lower()
        combined = f"{question} {answer}"

        used_items = [item for item in self.learned_items if item.lower() in combined]

        if not used_items:
            return 0.0, "✗ Learned items: none used"

        return 1.0, f"✓ Learned items: {len(used_items)} used"

    def _check_duplicates(self, exercise: dict) -> tuple[float, str]:
        """Check for exact duplicates in batch."""
        current_question = exercise.get("question", "").strip().lower()

        for other in self.batch_exercises:
            if other.get("question", "").strip().lower() == current_question:
                return 0.0, "✗ Duplicate: exact match found"

        return 1.0, "✓ Duplicate: none found"

    def _check_difficulty_level(self, exercise: dict) -> tuple[float, str]:
        """Check if difficulty level is specified."""
        valid_levels = ["beginner", "intermediate", "advanced"]
        difficulty = exercise.get("difficulty", "").lower()

        if difficulty not in valid_levels:
            return 0.0, f"✗ Difficulty: invalid ({difficulty})"

        return 1.0, f"✓ Difficulty: {difficulty}"

    def _check_cultural_appropriateness(self, exercise: dict) -> tuple[float, str]:
        """Check for offensive content (basic pattern matching)."""
        question = exercise.get("question", "").lower()
        answer = str(exercise.get("answer", "")).lower()
        combined = f"{question} {answer}"

        for pattern in self.OFFENSIVE_PATTERNS:
            if re.search(pattern, combined, re.IGNORECASE):
                return 0.0, "✗ Cultural: offensive content detected"

        return 1.0, "✓ Cultural: appropriate"

    def _check_harakaat_consistency(self, exercise: dict) -> tuple[float, str]:
        """Check if Arabic text uses vowel marks consistently."""
        question = exercise.get("question", "")
        answer = str(exercise.get("answer", ""))

        # Arabic vowel marks (harakaat)
        harakaat_pattern = r"[\u064B-\u065F]"

        question_has_harakaat = bool(re.search(harakaat_pattern, question))
        answer_has_harakaat = bool(re.search(harakaat_pattern, answer))

        # Check if Arabic text exists
        has_arabic = bool(re.search(r"[\u0600-\u06FF]", f"{question} {answer}"))

        if not has_arabic:
            return 1.0, "✓ Harakaat: N/A (no Arabic)"

        # If one has harakaat, both should have it
        if question_has_harakaat != answer_has_harakaat:
            return 0.5, "⚠ Harakaat: inconsistent usage"

        return 1.0, "✓ Harakaat: consistent"

    def _check_instructions_clarity(self, exercise: dict) -> tuple[float, str]:
        """Check if question has clear instruction."""
        question = exercise.get("question", "").lower()
        instruction_keywords = [
            "translate:",
            "fill in:",
            "sort:",
            "choose:",
            "select:",
            "complete:",
            "transform:",
            "correct:",
            "match:",
            "identify:",
        ]

        has_instruction = any(keyword in question for keyword in instruction_keywords)

        if not has_instruction:
            return 0.5, "⚠ Instructions: unclear"

        return 1.0, "✓ Instructions: clear"

    def _check_answer_format(self, exercise: dict) -> tuple[float, str]:
        """Check if exercise specifies expected answer format."""
        question = exercise.get("question", "").lower()
        exercise_type = exercise.get("type", "").lower()

        # Format indicators
        format_indicators = [
            "in arabic",
            "in english",
            "true or false",
            "yes or no",
            "a, b, c",
            "1, 2, 3",
            "select",
            "choose",
        ]

        # Some types implicitly specify format
        implicit_format_types = ["multiple_choice", "sorting", "true_false"]

        has_format_spec = any(indicator in question for indicator in format_indicators)
        has_implicit_format = exercise_type in implicit_format_types

        if not (has_format_spec or has_implicit_format):
            return 0.5, "⚠ Answer format: not specified"

        return 1.0, "✓ Answer format: specified"

    def _check_type_specific(self, exercise: dict) -> tuple[float | None, str]:
        """Check type-specific requirements."""
        exercise_type = exercise.get("type", "").lower()

        if exercise_type not in self.TYPE_SPECIFIC_FIELDS:
            return None, ""

        config = self.TYPE_SPECIFIC_FIELDS[exercise_type]
        validator_method = getattr(self, config["validator"])

        return validator_method(exercise, config["field"])

    def _validate_options(self, exercise: dict, field: str) -> tuple[float, str]:
        """Validate multiple choice options (2-6 options)."""
        options = exercise.get(field, [])

        if not isinstance(options, list):
            return 0.0, "✗ Options: not a list"

        if len(options) < 2:
            return 0.0, f"✗ Options: too few ({len(options)})"

        if len(options) > 6:
            return 0.5, f"⚠ Options: too many ({len(options)})"

        return 1.0, f"✓ Options: {len(options)} choices"

    def _validate_table(self, exercise: dict, field: str) -> tuple[float, str]:
        """Validate paradigm table structure (has rows/cols)."""
        table = exercise.get(field, {})

        if not isinstance(table, dict):
            return 0.0, "✗ Table: not a dict"

        has_rows = "rows" in table or "headers" in table
        has_cols = "cols" in table or "columns" in table

        if not (has_rows or has_cols):
            return 0.0, "✗ Table: missing structure"

        return 1.0, "✓ Table: valid structure"

    def _validate_steps(self, exercise: dict, field: str) -> tuple[float, str]:
        """Validate transformation chain steps (2+ transformations)."""
        steps = exercise.get(field, [])

        if not isinstance(steps, list):
            return 0.0, "✗ Steps: not a list"

        if len(steps) < 2:
            return 0.0, f"✗ Steps: too few ({len(steps)})"

        return 1.0, f"✓ Steps: {len(steps)} transformations"

    def _check_with_llm_judge(self, exercise: dict) -> tuple[float, str]:
        """
        Tier 2: Use LLM judge for semantic quality evaluation.

        Evaluates:
        1. Clarity: Is the question clear and unambiguous?
        2. Difficulty: Appropriate for difficulty level?
        3. Pedagogy: Does it effectively test the concept?
        4. Cultural: Culturally appropriate content?

        Returns:
            Tuple of (score, reason string)
        """
        try:
            prompt = self._build_llm_judge_prompt(exercise)

            # Use class-level shared LLM judge
            result = ExerciseQualityMetric._shared_llm_judge(
                prompt, max_length=150, num_return_sequences=1
            )[0]["generated_text"]

            # Parse score from result (expects "Score: 0.85\nReason: ...")
            score_match = re.search(r"Score:\s*(0\.\d+|1\.0)", result)
            if score_match:
                llm_score = float(score_match.group(1))
                reason = f"✓ LLM Judge: {llm_score:.2f}"
                return llm_score, reason
            else:
                return 0.5, "⚠ LLM Judge: could not parse score"

        except Exception as e:
            logger.error(f"LLM judge error: {e}")
            return 0.5, f"⚠ LLM Judge: error ({str(e)[:30]})"

    def _build_llm_judge_prompt(self, exercise: dict) -> str:
        """Build prompt for LLM judge evaluation."""
        difficulty = exercise.get("difficulty", "unknown")
        exercise_type = exercise.get("type", "unknown")
        question = exercise.get("question", "")
        answer = exercise.get("answer", "")

        return f"""You are evaluating Arabic teaching exercises. Rate the quality (0.0-1.0) based on:
1. Clarity: Is the question clear and unambiguous?
2. Difficulty: Appropriate for {difficulty} level?
3. Pedagogy: Does it effectively test the concept?
4. Cultural: Culturally appropriate content?

Exercise Type: {exercise_type}
Question: {question}
Answer: {answer}
Learned Items: {', '.join(self.learned_items)}

Return format: "Score: 0.85\\nReason: Clear question, appropriate difficulty..."
"""

    def _set_failure(self, reason: str) -> float:
        """Set failure state."""
        self.score = 0.0
        self.success = False
        self.reason = f"✗ {reason}"
        logger.error(f"ExerciseQualityMetric: {reason}")
        return 0.0

    def is_successful(self) -> bool:
        """Check if exercise quality meets threshold."""
        return self.success

    @property
    def __name__(self) -> str:
        """Metric name."""
        return "Exercise Quality"
