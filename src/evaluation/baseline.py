"""Baseline evaluation using base Qwen2.5-3B (no fine-tuning)."""

import logging
from pathlib import Path

from transformers import AutoModelForCausalLM, AutoTokenizer

from src.evaluation.deepeval_pipeline import EvaluationPipeline

# Constants
PROJECT_ROOT = Path(__file__).parent.parent.parent
DEFAULT_TEST_CASES_PATH = PROJECT_ROOT / "data" / "evaluation" / "test_cases.json"
DEFAULT_BASELINE_REPORT_PATH = PROJECT_ROOT / "data" / "evaluation" / "baseline_report.md"
DEFAULT_MAX_TOKENS = 256
GRADING_MAX_TOKENS = 50
DEFAULT_SAMPLE_SIZE = 5

logger = logging.getLogger(__name__)


class BaselineEvaluator:
    """
    Evaluates base Qwen2.5-3B model (no fine-tuning) against test cases.

    Goal: Establish baseline scores that fine-tuned model should beat.
    """

    def __init__(
        self,
        model_name: str = "Qwen/Qwen2.5-3B-Instruct",
        test_cases_path: str | Path | None = None,
    ) -> None:
        """
        Initialize baseline evaluator.

        Args:
            model_name: HuggingFace model ID
            test_cases_path: Path to test cases JSON (defaults to PROJECT_ROOT/data/evaluation/test_cases.json)

        Raises:
            RuntimeError: If model loading fails
            FileNotFoundError: If test cases file not found
        """
        self.model_name = model_name
        self.test_cases_path = Path(test_cases_path) if test_cases_path else DEFAULT_TEST_CASES_PATH

        try:
            logger.info(f"Loading base model: {model_name}...")
            self.tokenizer = AutoTokenizer.from_pretrained(model_name)
            self.model = AutoModelForCausalLM.from_pretrained(
                model_name,
                device_map="auto",
                torch_dtype="auto",
            )
            logger.info("✓ Model loaded successfully")

        except Exception as e:
            error_msg = f"Failed to load model {model_name}: {e}"
            logger.error(error_msg)
            raise RuntimeError(error_msg) from e

        try:
            self.pipeline = EvaluationPipeline(self.test_cases_path)
        except FileNotFoundError:
            logger.error(f"Test cases file not found: {self.test_cases_path}")
            raise

    def generate_response(self, prompt: str, max_new_tokens: int = DEFAULT_MAX_TOKENS) -> str:
        """
        Generate response from base model.

        Args:
            prompt: Input prompt
            max_new_tokens: Maximum tokens to generate

        Returns:
            Generated text
        """
        inputs = self.tokenizer(prompt, return_tensors="pt").to(self.model.device)

        outputs = self.model.generate(
            **inputs,
            max_new_tokens=max_new_tokens,
            do_sample=False,  # Deterministic for evaluation
            pad_token_id=self.tokenizer.eos_token_id,
        )

        response = self.tokenizer.decode(outputs[0], skip_special_tokens=True)

        # Remove the prompt from response
        if response.startswith(prompt):
            response = response[len(prompt) :].strip()

        return response

    def run_teaching_mode_baseline(
        self, sample_size: int = DEFAULT_SAMPLE_SIZE
    ) -> tuple[dict[str, str], dict]:
        """
        Run baseline evaluation on teaching mode test cases.

        Args:
            sample_size: Number of test cases to evaluate per category (for speed)

        Returns:
            Tuple of (model_responses, evaluation_results)
        """
        logger.info("\n=== Running Teaching Mode Baseline ===\n")

        model_responses = {}
        teaching_cases = self.pipeline.test_cases["teaching_mode"]

        # Sample vocab batch introduction cases
        for test_case in teaching_cases["vocabulary_batch_introduction"][:sample_size]:
            test_id = test_case["test_id"]
            input_data = test_case["input"]

            # Create prompt using list join for efficiency
            word_lines = [
                f"- {word['arabic']} ({word['transliteration']}) - {word['english']}"
                for word in input_data["words"]
            ]
            words_section = "\n".join(word_lines)

            prompt = f"""Mode: {input_data['mode']}

Lesson {input_data['lesson_number']}, Batch {input_data['batch_number']}

Words to teach:
{words_section}

Present these words to the student in an encouraging way:
"""

            logger.info(f"Evaluating {test_id}...")
            response = self.generate_response(prompt)
            model_responses[test_id] = response

        # Run evaluation
        results = self.pipeline.evaluate_teaching_mode(model_responses)
        return model_responses, results

    def run_grading_mode_baseline(
        self, sample_size: int = DEFAULT_SAMPLE_SIZE
    ) -> tuple[dict[str, str], dict]:
        """
        Run baseline evaluation on grading mode test cases.

        Args:
            sample_size: Number of test cases to evaluate per category

        Returns:
            Tuple of (model_responses, evaluation_results)
        """
        logger.info("\n=== Running Grading Mode Baseline ===\n")

        model_responses = {}
        grading_cases = self.pipeline.test_cases["grading_mode"]

        # Sample vocabulary grading cases
        vocab_cases = (
            grading_cases["vocabulary_grading"]["correct_translations"][:sample_size]
            + grading_cases["vocabulary_grading"]["incorrect_translations"][:sample_size]
        )

        for test_case in vocab_cases:
            test_id = test_case["test_id"]
            input_data = test_case["input"]

            # Create prompt
            prompt = f"""Mode: {input_data['mode']}

Question: What does "{input_data['word']}" mean?
Student Answer: "{input_data['student_answer']}"
Correct Answer: "{input_data['correct_answer']}"

Evaluate if the student's answer is correct. Return JSON:
{{"correct": true}} or {{"correct": false}}

Response:
"""

            logger.info(f"Evaluating {test_id}...")
            response = self.generate_response(prompt, max_new_tokens=GRADING_MAX_TOKENS)
            model_responses[test_id] = response

        # Run evaluation
        results = self.pipeline.evaluate_grading_mode(model_responses)
        return model_responses, results

    def save_baseline_report(
        self,
        teaching_results: dict,
        grading_results: dict,
        output_path: str | Path | None = None,
    ) -> None:
        """
        Save baseline evaluation report.

        Args:
            teaching_results: Teaching mode evaluation results
            grading_results: Grading mode evaluation results
            output_path: Output file path (defaults to PROJECT_ROOT/data/evaluation/baseline_report.md)
        """
        output_file = Path(output_path) if output_path else DEFAULT_BASELINE_REPORT_PATH

        report = [
            "# Baseline Evaluation Report",
            "",
            f"**Model:** {self.model_name}",
            "**Fine-tuning:** None (base model)",
            "",
            "## Purpose",
            "",
            "Establish baseline scores for base Qwen2.5-3B model (no fine-tuning).",
            "**Goal:** Fine-tuned model should significantly outperform these scores.",
            "",
            "---",
            "",
        ]

        # Teaching mode report
        teaching_report = self.pipeline.generate_report(teaching_results, "teaching")
        report.append(teaching_report)
        report.append("")
        report.append("---")
        report.append("")

        # Grading mode report
        grading_report = self.pipeline.generate_report(grading_results, "grading")
        report.append(grading_report)

        # Save report
        output_file.parent.mkdir(parents=True, exist_ok=True)

        with open(output_file, "w") as f:
            f.write("\n".join(report))

        logger.info(f"\n✓ Baseline report saved to: {output_file}")


def main() -> None:
    """Run baseline evaluation."""
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    logger.info("=== Baseline Evaluation ===")
    logger.info("Testing base Qwen2.5-3B (no fine-tuning) against evaluation dataset\n")

    evaluator = BaselineEvaluator()

    # Run teaching mode baseline (uses DEFAULT_SAMPLE_SIZE)
    teaching_responses, teaching_results = evaluator.run_teaching_mode_baseline()

    teaching_pct = EvaluationPipeline._safe_percentage(
        teaching_results["passed"], teaching_results["total"]
    )
    logger.info("\nTeaching Mode Results:")
    logger.info(
        f"  Passed: {teaching_results['passed']}/{teaching_results['total']} "
        f"({teaching_pct:.1f}%)"
    )

    # Run grading mode baseline
    grading_responses, grading_results = evaluator.run_grading_mode_baseline()

    grading_pct = EvaluationPipeline._safe_percentage(
        grading_results["passed"], grading_results["total"]
    )
    logger.info("\nGrading Mode Results:")
    logger.info(
        f"  Passed: {grading_results['passed']}/{grading_results['total']} " f"({grading_pct:.1f}%)"
    )

    # Save report
    evaluator.save_baseline_report(teaching_results, grading_results)

    logger.info("\n=== Baseline Evaluation Complete ===")


if __name__ == "__main__":
    main()
