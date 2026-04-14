"""Evaluation metrics for Agent 3 (Content/Exercise Generation Agent)."""

import json
import logging
import re

from deepeval.metrics import BaseMetric
from deepeval.test_case import LLMTestCase

from src.evaluation.utils import check_learned_items_usage, extract_arabic_words

from .shared_metrics import extract_json

logger = logging.getLogger(__name__)


class AlignmentMetric(BaseMetric):
    """
    Evaluates semantic alignment for Agent 3 (Exercise Generation).

    Uses base Qwen2.5-7B as LLM judge to evaluate:
    - Matches requested exercise_type
    - Uses learned_vocab appropriately
    - Tests specified grammar_rule
    - Has variety in question formats

    Threshold: >0.8 for alignment score
    """

    # Class-level singleton: shared LLM judge across all instances
    _shared_judge_model = None
    _shared_judge_tokenizer = None

    def __init__(
        self,
        threshold: float = 0.8,
        model_name: str = "Qwen/Qwen2.5-7B-Instruct",
        judge_model=None,
        judge_tokenizer=None,
    ) -> None:
        """
        Initialize alignment metric.

        Args:
            threshold: Minimum alignment score required (default 0.8)
            model_name: HuggingFace model ID for LLM judge (fallback if judge not provided)
            judge_model: Optional pre-loaded judge model (for dependency injection)
            judge_tokenizer: Optional pre-loaded judge tokenizer (for dependency injection)
        """
        self.threshold = threshold
        self.model_name = model_name
        self.score = 0.0
        self.reason = ""
        self.success = False

        # Support dependency injection of judge model/tokenizer
        self.judge_model = judge_model
        self.judge_tokenizer = judge_tokenizer

    def measure(self, test_case: LLMTestCase) -> float:
        """
        Measure alignment score using LLM judge.

        Args:
            test_case: Test case with input (requirements) and actual_output (generated exercises)

        Returns:
            Alignment score (0.0-1.0)
        """
        self._ensure_judge_loaded()

        try:
            input_data, generated_exercises = self._parse_test_case(test_case)
            judge_prompt = self._build_judge_prompt(input_data, generated_exercises)
            judge_response = self._query_judge(judge_prompt)
            alignment_score = self._parse_judge_response(judge_response)

            return self._set_result(alignment_score, judge_response)

        except Exception as e:
            return self._set_error(f"Alignment check error: {str(e)}")

    def _ensure_judge_loaded(self) -> None:
        """
        Ensure a judge model/tokenizer are available.

        Preference order:
        1. Explicitly injected judge on the instance (self.judge_model/self.judge_tokenizer)
        2. Class-level shared judge (singleton)
        3. Lazily load a new judge from `self.model_name` as a fallback
        """
        # 1) Instance-level injection: if caller provided model/tokenizer, use them
        if self.judge_model is not None and self.judge_tokenizer is not None:
            return

        # 2) Reuse class-level singleton if already initialized
        if (
            AlignmentMetric._shared_judge_model is not None
            and AlignmentMetric._shared_judge_tokenizer is not None
        ):
            # Mirror shared judge onto the instance for convenience
            self.judge_model = AlignmentMetric._shared_judge_model
            self.judge_tokenizer = AlignmentMetric._shared_judge_tokenizer
            return

        # 3) Fallback: lazily load from `self.model_name` once per process
        logger.info(f"Loading LLM judge model: {self.model_name} (first time)...")
        from transformers import AutoModelForCausalLM, AutoTokenizer

        tokenizer = AutoTokenizer.from_pretrained(self.model_name)
        model = AutoModelForCausalLM.from_pretrained(
            self.model_name,
            device_map="auto",
            torch_dtype="auto",
        )

        # Cache at class level (singleton)
        AlignmentMetric._shared_judge_tokenizer = tokenizer
        AlignmentMetric._shared_judge_model = model

        # Also attach to the instance
        self.judge_model = model
        self.judge_tokenizer = tokenizer

        logger.info("LLM judge loaded and cached")

    def _parse_test_case(self, test_case: LLMTestCase) -> tuple[dict, dict]:
        """Extract and parse input requirements and generated output."""
        input_json = extract_json(test_case.input)
        output_json = extract_json(test_case.actual_output)
        input_data = json.loads(input_json)
        generated_exercises = json.loads(output_json)
        return input_data, generated_exercises

    def _set_result(self, score: float, response: str) -> float:
        """Set metric result with score and reason."""
        self.score = score
        self.success = score >= self.threshold
        self.reason = (
            f"{'✓' if self.success else '✗'} "
            f"Alignment score: {score:.2f} (threshold: {self.threshold})\n"
            f"{response[:200]}"
        )
        return self.score

    def _set_error(self, reason: str) -> float:
        """Set error state."""
        self.score = 0.0
        self.success = False
        self.reason = f"✗ {reason}"
        logger.error(f"AlignmentMetric error: {reason}")
        return 0.0

    def _build_judge_prompt(self, input_data: dict, generated_exercises: dict) -> str:
        """
        Build prompt for LLM judge to evaluate alignment.

        Args:
            input_data: Exercise generation requirements
            generated_exercises: Model's generated output

        Returns:
            Judge prompt string
        """
        prompt = f"""You are an expert judge evaluating the alignment between exercise requirements and generated exercises.

Requirements:
- Exercise type: {input_data.get("exercise_type", "N/A")}
- Learned vocabulary: {input_data.get("learned_vocab", [])}
- Grammar rule: {input_data.get("grammar_rule", "N/A")}
- Question count: {input_data.get("question_count", "N/A")}

Generated Exercises:
{json.dumps(generated_exercises, indent=2, ensure_ascii=False)}

Evaluate alignment on these criteria (each 0-1 score):
1. Matches exercise type
2. Uses learned vocabulary appropriately
3. Tests the specified grammar rule
4. Has variety in question formats

Provide scores as: "1: 0.9, 2: 0.8, 3: 1.0, 4: 0.7"
Then provide overall score (0.0-1.0) and brief reasoning.

Response format:
Scores: 1: X, 2: Y, 3: Z, 4: W
Overall: X.XX
Reasoning: [brief explanation]
"""
        return prompt

    def _query_judge(self, prompt: str) -> str:
        """
        Query LLM judge with prompt.

        Args:
            prompt: Judge prompt

        Returns:
            Judge response text
        """
        # Use instance attributes (respects dependency injection)
        inputs = self.judge_tokenizer(prompt, return_tensors="pt").to(self.judge_model.device)

        outputs = self.judge_model.generate(
            **inputs,
            max_new_tokens=256,
            do_sample=False,  # Deterministic
            pad_token_id=self.judge_tokenizer.eos_token_id,
        )

        response = self.judge_tokenizer.decode(outputs[0], skip_special_tokens=True)

        # Remove prompt from response
        if response.startswith(prompt):
            response = response[len(prompt) :].strip()

        return response

    def _parse_judge_response(self, response: str) -> float:
        """
        Parse overall score from judge response.

        Args:
            response: Judge response text

        Returns:
            Alignment score (0.0-1.0)
        """
        # Look for "Overall: X.XX" pattern
        match = re.search(r"Overall:\s*([0-9]*\.?[0-9]+)", response)
        if match:
            return float(match.group(1))

        # Fallback: look for any decimal number 0.0-1.0
        match = re.search(r"\b(0\.[0-9]+|1\.0+)\b", response)
        if match:
            return float(match.group(1))

        # Default: assume poor alignment if can't parse
        logger.warning(f"Could not parse alignment score from response: {response[:100]}")
        return 0.0

    def is_successful(self) -> bool:
        """Check if alignment score meets threshold."""
        return self.success

    @property
    def __name__(self) -> str:
        """Metric name."""
        return "Alignment"


class ExerciseQualityMetric(BaseMetric):
    """
    Rule-based quality evaluation for generated exercises.

    Checks:
    1. Question validity (has text, reasonable length 10-500 chars)
    2. Answer presence (not empty)
    3. Learned items usage (using Arabic text matching with harakaat handling)
    4. Difficulty appropriateness (matches requested difficulty)
    5. Cultural appropriateness (no offensive content)
    6. Harakaat consistency (if present, used consistently)
    7. Instructions clarity (has clear prompt)
    8. Answer format specification (specifies expected format)

    This is a RULE-BASED metric (not LLM-judged) for fast, deterministic evaluation.
    """

    def __init__(self, threshold: float = 0.7) -> None:
        """
        Initialize exercise quality metric.

        Args:
            threshold: Minimum quality score required (default 0.7)
        """
        self.threshold = threshold
        self.score = 0.0
        self.reason = ""
        self.success = False

    def measure(self, test_case: LLMTestCase) -> float:
        """
        Measure exercise quality using rule-based checks.

        Args:
            test_case: Test case with input (requirements) and actual_output (generated exercise or list)

        Returns:
            Quality score (0.0-1.0)
        """
        try:
            input_data, generated_output = self._parse_test_case(test_case)

            # Handle both single exercise (dict) and multiple exercises (list)
            if isinstance(generated_output, list):
                # Multiple exercises: check first exercise only (representative)
                if not generated_output:
                    return self._set_error("Empty list of exercises")
                exercise = generated_output[0]
                checks = self._run_quality_checks(input_data, exercise)
                score = self._calculate_score(checks)
                return self._set_result(score, checks)
            else:
                # Single exercise: check directly
                checks = self._run_quality_checks(input_data, generated_output)
                score = self._calculate_score(checks)
                return self._set_result(score, checks)

        except Exception as e:
            return self._set_error(f"Quality check error: {str(e)}")

    def _parse_test_case(self, test_case: LLMTestCase) -> tuple[dict, dict | list]:
        """Extract and parse input requirements and generated output."""
        input_json = extract_json(test_case.input)
        output_json = extract_json(test_case.actual_output)
        input_data = json.loads(input_json)
        generated_output = json.loads(output_json)
        return input_data, generated_output

    def _run_quality_checks(self, input_data: dict, exercise: dict) -> dict:
        """
        Run all quality checks on generated exercise.

        Args:
            input_data: Exercise generation requirements (learned_items, difficulty, etc.)
            exercise: Generated exercise JSON

        Returns:
            Dictionary of check results with passed/failed status and reasons
        """
        checks = {}

        # 1. Question validity
        question = exercise.get("question", "")
        question_len = len(question)
        checks["question"] = {
            "passed": 10 <= question_len <= 500,
            "reason": f"valid ({question_len} chars)"
            if 10 <= question_len <= 500
            else f"invalid length ({question_len} chars)",
        }

        # 2. Answer presence
        answer = exercise.get("answer", "")
        checks["answer"] = {
            "passed": bool(answer.strip()),
            "reason": "present" if answer.strip() else "missing",
        }

        # 3. Learned items usage (FIXED with Arabic text matching!)
        learned_items = input_data.get("learned_items", [])
        if learned_items:
            # Extract Arabic text from question and answer
            text_to_check = question + " " + answer
            passed, used_items, unused_items = check_learned_items_usage(
                text_to_check, learned_items, require_all=False, min_usage_count=1
            )
            checks["learned_items"] = {
                "passed": passed,
                "reason": (
                    f"{len(used_items)}/{len(learned_items)} used" if passed else "none used"
                ),
            }
        else:
            # No learned items specified, so pass by default
            checks["learned_items"] = {"passed": True, "reason": "N/A"}

        # 4. Difficulty appropriateness
        expected_difficulty = input_data.get("difficulty", "beginner")
        actual_difficulty = exercise.get("difficulty", "")
        checks["difficulty"] = {
            "passed": actual_difficulty == expected_difficulty,
            "reason": actual_difficulty
            if actual_difficulty == expected_difficulty
            else f"mismatch (expected {expected_difficulty}, got {actual_difficulty})",
        }

        # 5. Cultural appropriateness (basic check for offensive keywords)
        offensive_keywords = ["offensive", "inappropriate", "taboo"]  # Extend as needed
        text = (question + " " + answer).lower()
        has_offensive = any(keyword in text for keyword in offensive_keywords)
        checks["cultural"] = {
            "passed": not has_offensive,
            "reason": "appropriate" if not has_offensive else "contains offensive content",
        }

        # 6. Harakaat consistency (if Arabic text has harakaat, should be used consistently)
        arabic_text = " ".join(extract_arabic_words(question + " " + answer))
        harakaat_pattern = r"[\u064B-\u0652\u0670]"
        has_harakaat = bool(re.search(harakaat_pattern, arabic_text))
        if has_harakaat:
            # Count words with and without harakaat
            words = arabic_text.split()
            words_with_harakaat = sum(1 for w in words if re.search(harakaat_pattern, w))
            consistency = words_with_harakaat / len(words) if words else 0
            checks["harakaat"] = {
                "passed": consistency > 0.8,
                "reason": f"consistent ({consistency:.0%})"
                if consistency > 0.8
                else f"inconsistent ({consistency:.0%})",
            }
        else:
            checks["harakaat"] = {"passed": True, "reason": "consistent (none used)"}

        # 7. Instructions clarity (question should have clear prompt)
        instruction_keywords = [
            "translate",
            "fill",
            "choose",
            "write",
            "complete",
            "match",
            "اكتب",
            "املأ",
            "اختر",
            "ترجم",
        ]
        has_instruction = any(keyword in text.lower() for keyword in instruction_keywords)
        checks["instructions"] = {
            "passed": has_instruction,
            "reason": "clear" if has_instruction else "unclear",
            "warning": not has_instruction,  # Mark as warning, not failure
        }

        # 8. Answer format specification (for complex exercises)
        format_keywords = ["format", "example", "e.g.", "like", "as follows", "مثال", "بالشكل"]
        has_format_spec = any(keyword in text.lower() for keyword in format_keywords)
        # This is a soft check - nice to have but not critical for simple exercises
        checks["answer_format"] = {
            "passed": has_format_spec,
            "reason": "specified" if has_format_spec else "not specified",
            "warning": not has_format_spec,  # Mark as warning, not failure
        }

        return checks

    def _calculate_score(self, checks: dict) -> float:
        """
        Calculate overall quality score from individual checks.

        Critical checks (must pass): question, answer, learned_items, difficulty, cultural, harakaat
        Warning checks (nice to have): instructions, answer_format

        Args:
            checks: Dictionary of check results

        Returns:
            Quality score (0.0-1.0)
        """
        critical_checks = [
            "question",
            "answer",
            "learned_items",
            "difficulty",
            "cultural",
            "harakaat",
        ]
        warning_checks = ["instructions", "answer_format"]

        critical_passed = sum(
            1 for key in critical_checks if checks.get(key, {}).get("passed", False)
        )
        warnings_passed = sum(
            1 for key in warning_checks if checks.get(key, {}).get("passed", False)
        )

        # Critical checks are worth 0.8 of the score, warnings are worth 0.2
        critical_score = (critical_passed / len(critical_checks)) * 0.8
        warning_score = (warnings_passed / len(warning_checks)) * 0.2

        return critical_score + warning_score

    def _set_result(self, score: float, checks: dict) -> float:
        """Set metric result with score and detailed reason."""
        self.score = score
        self.success = score >= self.threshold

        # Format reason with all check results
        check_symbols = []
        for check_name, check_result in checks.items():
            symbol = (
                "✓" if check_result["passed"] else ("⚠" if check_result.get("warning") else "✗")
            )
            reason_text = check_result["reason"]
            check_symbols.append(f"{symbol} {check_name.capitalize()}: {reason_text}")

        self.reason = " | ".join(check_symbols)
        return self.score

    def _set_error(self, reason: str) -> float:
        """Set error state."""
        self.score = 0.0
        self.success = False
        self.reason = f"✗ {reason}"
        logger.error(f"ExerciseQualityMetric error: {reason}")
        return 0.0

    def is_successful(self) -> bool:
        """Check if quality score meets threshold."""
        return self.success

    @property
    def __name__(self) -> str:
        """Metric name."""
        return "Exercise Quality"
