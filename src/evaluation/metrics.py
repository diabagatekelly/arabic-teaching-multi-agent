"""Custom evaluation metrics for Arabic Teaching Multi-Agent System v2."""

import json
import logging
import re

from deepeval.metrics import BaseMetric
from deepeval.test_case import LLMTestCase
from transformers import pipeline

logger = logging.getLogger(__name__)


class SentimentMetric(BaseMetric):
    """
    Evaluates sentiment score for Agent 1 (Teaching) responses.

    Target: >0.9 for teaching mode, >0.8 for feedback mode.
    """

    # Class-level singleton: shared sentiment pipeline across all instances
    _shared_sentiment_pipeline = None

    def __init__(self, threshold: float = 0.9, mode: str = "teaching") -> None:
        """
        Initialize sentiment metric.

        Args:
            threshold: Minimum sentiment score required
            mode: "teaching" (0.9) or "feedback" (0.8)
        """
        self.threshold = threshold
        self.mode = mode
        self.score = 0.0
        self.reason = ""
        self.success = False

        # Load sentiment pipeline once at class level (singleton pattern)
        if SentimentMetric._shared_sentiment_pipeline is None:
            logger.info("Loading sentiment analysis model (first time)...")
            SentimentMetric._shared_sentiment_pipeline = pipeline(
                "sentiment-analysis",
                model="distilbert-base-uncased-finetuned-sst-2-english",
            )
            logger.info("Sentiment model loaded and cached")

    def measure(self, test_case: LLMTestCase) -> float:
        """
        Measure sentiment score using transformers sentiment pipeline.

        Args:
            test_case: Test case with actual_output to analyze

        Returns:
            Sentiment score (0-1, where 1 is most positive)
        """
        try:
            # Use class-level shared sentiment pipeline (singleton)
            result = SentimentMetric._shared_sentiment_pipeline(test_case.actual_output)[0]

            # Convert to 0-1 scale (positive sentiment)
            if result["label"] == "POSITIVE":
                self.score = result["score"]
            else:
                self.score = 1.0 - result["score"]

            self.success = self.score >= self.threshold
            self.reason = f"Sentiment score: {self.score:.3f} ({'✓' if self.success else '✗'} threshold: {self.threshold})"

            return self.score

        except Exception as e:
            self.score = 0.0
            self.success = False
            self.reason = f"Sentiment analysis failed: {str(e)}"
            logger.error(f"Sentiment analysis error: {e}")
            return 0.0

    def is_successful(self) -> bool:
        """Check if metric passed threshold."""
        return self.success

    @property
    def __name__(self) -> str:
        """Metric name."""
        return f"Sentiment ({self.mode})"


class JSONValidityMetric(BaseMetric):
    """
    Evaluates JSON validity for Agent 2 (Grading) responses.

    Target: 100% valid JSON output.
    """

    def __init__(self) -> None:
        """Initialize JSON validity metric."""
        self.score = 0.0
        self.reason = ""
        self.success = False

    def _extract_json(self, text: str) -> str:
        """
        Extract JSON from text, handling markdown code blocks.

        Args:
            text: Text that may contain JSON with or without markdown blocks

        Returns:
            Extracted JSON string
        """
        text = text.strip()

        # Check for ```json code blocks
        # Match everything after ```json up to the next ``` or end of string
        if "```json" in text:
            match = re.search(r"```json\s*(.*?)(?:```|$)", text, re.DOTALL)
            if match:
                return match.group(1).strip()

        # Check for generic ``` code blocks
        # Match everything after ``` up to the next ``` or end of string
        if "```" in text:
            match = re.search(r"```\s*(.*?)(?:```|$)", text, re.DOTALL)
            if match:
                return match.group(1).strip()

        return text

    def measure(self, test_case: LLMTestCase) -> float:
        """
        Check if output is valid JSON.

        Args:
            test_case: Test case with actual_output to validate

        Returns:
            1.0 if valid JSON, 0.0 otherwise
        """
        try:
            # Extract JSON (handles markdown code blocks)
            json_str = self._extract_json(test_case.actual_output)
            json.loads(json_str)  # Just check if parseable

            self.score = 1.0
            self.success = True
            self.reason = "✓ Valid JSON output"
            return 1.0

        except json.JSONDecodeError as e:
            self.score = 0.0
            self.success = False
            self.reason = f"✗ Invalid JSON: {str(e)}"
            logger.error(f"JSON decode error: {e}")
            return 0.0

    def is_successful(self) -> bool:
        """Check if JSON is valid."""
        return self.success

    @property
    def __name__(self) -> str:
        """Metric name."""
        return "JSON Validity"


class StructureMetric(BaseMetric):
    """
    Validates JSON structure: correct type, required keys, expected value types.

    Configurable for different agent outputs.

    Examples:
        Agent 2 (Grading):
            StructureMetric(
                expected_type=dict,
                required_keys=["correct"],
                expected_types={"correct": bool}
            )

        Agent 3 (Exercise Generation):
            StructureMetric(
                expected_type=list,
                required_keys=["question", "answer"],
                expected_types={"question": str, "answer": str}
            )
    """

    def __init__(
        self,
        expected_type: type,  # dict, list, etc.
        required_keys: list[str] | None = None,  # Keys that must exist
        expected_types: dict[str, type] | None = None,  # Key: expected type
    ) -> None:
        """
        Initialize structure metric.

        Args:
            expected_type: Expected top-level type (dict, list, etc.)
            required_keys: List of keys that must exist
            expected_types: Dict mapping key names to expected types
        """
        # Required by DeepEval
        self.score = 0.0
        self.reason = ""
        self.success = False

        # Configuration
        self.expected_type = expected_type
        self.required_keys = required_keys or []
        self.expected_types = expected_types or {}

    def measure(self, test_case: LLMTestCase) -> float:
        """
        Check if JSON has correct structure.

        Args:
            test_case: Test case with actual_output to validate

        Returns:
            1.0 if structure is valid, 0.0 otherwise
        """
        try:
            # Parse JSON
            parsed = json.loads(test_case.actual_output)

            # Check 1: Top-level type
            if not isinstance(parsed, self.expected_type):
                self.score = 0.0
                self.success = False
                self.reason = (
                    f"✗ Expected {self.expected_type.__name__}, " f"got {type(parsed).__name__}"
                )
                return 0.0

            # Check 2: For dict - required keys
            if self.expected_type is dict:
                missing_keys = [k for k in self.required_keys if k not in parsed]
                if missing_keys:
                    self.score = 0.0
                    self.success = False
                    self.reason = f"✗ Missing required keys: {missing_keys}"
                    return 0.0

            # Check 3: For list - each item has required keys
            if self.expected_type is list:
                if not parsed:  # Empty list
                    self.score = 0.0
                    self.success = False
                    self.reason = "✗ Expected non-empty list"
                    return 0.0

                for i, item in enumerate(parsed):
                    if not isinstance(item, dict):
                        self.score = 0.0
                        self.success = False
                        self.reason = f"✗ Item {i} is not a dict"
                        return 0.0

                    missing = [k for k in self.required_keys if k not in item]
                    if missing:
                        self.score = 0.0
                        self.success = False
                        self.reason = f"✗ Item {i} missing keys: {missing}"
                        return 0.0

            # Check 4: Value types (if specified)
            if self.expected_types:
                for key, expected_type in self.expected_types.items():
                    if self.expected_type is dict:
                        value = parsed.get(key)
                        if value is not None and not isinstance(value, expected_type):
                            self.score = 0.0
                            self.success = False
                            self.reason = (
                                f"✗ Key '{key}': expected {expected_type.__name__}, "
                                f"got {type(value).__name__}"
                            )
                            return 0.0

                    elif self.expected_type is list:
                        for i, item in enumerate(parsed):
                            value = item.get(key)
                            if value is not None and not isinstance(value, expected_type):
                                self.score = 0.0
                                self.success = False
                                self.reason = (
                                    f"✗ Item {i}, key '{key}': "
                                    f"expected {expected_type.__name__}, "
                                    f"got {type(value).__name__}"
                                )
                                return 0.0

            # All checks passed
            self.score = 1.0
            self.success = True
            self.reason = "✓ Valid structure with required keys and types"
            return 1.0

        except json.JSONDecodeError as e:
            self.score = 0.0
            self.success = False
            self.reason = f"✗ Invalid JSON: {str(e)}"
            return 0.0

    def is_successful(self) -> bool:
        """Check if structure validation passed."""
        return self.success

    @property
    def __name__(self) -> str:
        """Metric name."""
        return "Structure"


class AccuracyMetric(BaseMetric):
    """
    Evaluates accuracy for Agent 2 (Grading) correct/incorrect classification.

    Returns 1.0 for correct classification, 0.0 for incorrect.
    Aggregate accuracy across multiple test cases should exceed 90%.
    """

    def __init__(self) -> None:
        """Initialize accuracy metric."""
        self.score = 0.0
        self.reason = ""
        self.success = False

    def measure(self, test_case: LLMTestCase) -> float:
        """
        Check if grading output matches expected correctness.

        Assumes structure is valid (StructureMetric already validated).

        Args:
            test_case: Test case with expected_output (bool) and actual_output (JSON)

        Returns:
            1.0 if correct classification, 0.0 otherwise
        """
        try:
            # Parse actual output JSON
            actual = json.loads(test_case.actual_output)
            expected_correct = test_case.expected_output

            # Structure is guaranteed valid by StructureMetric, safe to access
            actual_correct = actual["correct"]

            if actual_correct == expected_correct:
                self.score = 1.0
                self.success = True
                self.reason = (
                    f"✓ Correctly classified as {'correct' if expected_correct else 'incorrect'}"
                )
            else:
                self.score = 0.0
                self.success = False
                self.reason = f"✗ Expected {'correct' if expected_correct else 'incorrect'}, got {actual_correct}"

            return self.score

        except (json.JSONDecodeError, KeyError, TypeError) as e:
            # Should rarely happen if pipeline runs metrics in order
            self.score = 0.0
            self.success = False
            self.reason = f"✗ Parsing error: {str(e)}"
            logger.error(f"Accuracy metric parsing error: {e}")
            return 0.0

    def is_successful(self) -> bool:
        """Check if this test case was classified correctly."""
        return self.success

    @property
    def __name__(self) -> str:
        """Metric name."""
        return "Accuracy"


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
        # Lazy load judge model on first measure() call (singleton pattern)
        if AlignmentMetric._shared_judge_model is None:
            logger.info(f"Loading LLM judge model: {self.model_name} (first time)...")
            from transformers import AutoModelForCausalLM, AutoTokenizer

            AlignmentMetric._shared_judge_tokenizer = AutoTokenizer.from_pretrained(self.model_name)
            AlignmentMetric._shared_judge_model = AutoModelForCausalLM.from_pretrained(
                self.model_name,
                device_map="auto",
                torch_dtype="auto",
            )
            logger.info("LLM judge loaded and cached")

        try:
            # Parse input requirements and actual output
            input_data = json.loads(test_case.input)
            generated_exercises = json.loads(test_case.actual_output)

            # Build judge prompt
            judge_prompt = self._build_judge_prompt(input_data, generated_exercises)

            # Get LLM judge verdict
            judge_response = self._query_judge(judge_prompt)

            # Parse judge response for score
            alignment_score = self._parse_judge_response(judge_response)

            self.score = alignment_score
            self.success = alignment_score >= self.threshold
            self.reason = (
                f"{'✓' if self.success else '✗'} "
                f"Alignment score: {alignment_score:.2f} "
                f"(threshold: {self.threshold})\n{judge_response[:200]}"
            )

            return self.score

        except Exception as e:
            self.score = 0.0
            self.success = False
            self.reason = f"✗ Alignment check error: {str(e)}"
            logger.error(f"AlignmentMetric error: {e}")
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
- Exercise type: {input_data.get('exercise_type', 'N/A')}
- Learned vocabulary: {input_data.get('learned_vocab', [])}
- Grammar rule: {input_data.get('grammar_rule', 'N/A')}
- Question count: {input_data.get('question_count', 'N/A')}

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
