"""Evaluation metrics for Agent 3 (Content/Exercise Generation Agent)."""

import json
import logging
import re

from deepeval.metrics import BaseMetric
from deepeval.test_case import LLMTestCase

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
        self, threshold: float = 0.8, model_name: str = "Qwen/Qwen2.5-7B-Instruct"
    ) -> None:
        """
        Initialize alignment metric.

        Args:
            threshold: Minimum alignment score required (default 0.8)
            model_name: HuggingFace model ID for LLM judge
        """
        self.threshold = threshold
        self.model_name = model_name
        self.score = 0.0
        self.reason = ""
        self.success = False

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
        """Lazy load judge model on first use (singleton pattern)."""
        if AlignmentMetric._shared_judge_model is not None:
            return

        logger.info(f"Loading LLM judge model: {self.model_name} (first time)...")
        from transformers import AutoModelForCausalLM, AutoTokenizer

        AlignmentMetric._shared_judge_tokenizer = AutoTokenizer.from_pretrained(self.model_name)
        AlignmentMetric._shared_judge_model = AutoModelForCausalLM.from_pretrained(
            self.model_name,
            device_map="auto",
            torch_dtype="auto",
        )
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
        inputs = AlignmentMetric._shared_judge_tokenizer(prompt, return_tensors="pt").to(
            AlignmentMetric._shared_judge_model.device
        )

        outputs = AlignmentMetric._shared_judge_model.generate(
            **inputs,
            max_new_tokens=256,
            do_sample=False,  # Deterministic
            pad_token_id=AlignmentMetric._shared_judge_tokenizer.eos_token_id,
        )

        response = AlignmentMetric._shared_judge_tokenizer.decode(
            outputs[0], skip_special_tokens=True
        )

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
