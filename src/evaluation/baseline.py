"""Baseline evaluation using base Qwen2.5-3B (no fine-tuning)."""

import logging
from pathlib import Path

from transformers import AutoModelForCausalLM, AutoTokenizer

from src.agents import TeachingAgent
from src.evaluation.deepeval_pipeline import EvaluationPipeline
from src.prompts.formatters import flatten_nested_input
from src.prompts.templates import (
    EXERCISE_GENERATION,
    GRADING_GRAMMAR_QUIZ,
    GRADING_VOCAB,
)

# Constants
PROJECT_ROOT = Path(__file__).parent.parent.parent
DEFAULT_TEST_CASES_PATH = PROJECT_ROOT / "data" / "evaluation" / "test_cases.json"
TEACHING_AGENT_TEST_CASES_PATH = (
    PROJECT_ROOT / "data" / "evaluation" / "teaching_agent_test_cases.json"
)
DEFAULT_BASELINE_REPORT_PATH = PROJECT_ROOT / "data" / "evaluation" / "baseline_report.md"
DEFAULT_MAX_TOKENS = 256
GRADING_MAX_TOKENS = 50
DEFAULT_SAMPLE_SIZE = 5

logger = logging.getLogger(__name__)


class BaselineEvaluator:
    """
    Evaluates base models (no fine-tuning) against test cases.

    Model Strategy (matches production architecture):
    - Agent 1 (Teaching/Feedback): Base Qwen2.5-3B → Fine-tuned 3B
    - Agent 2 (Grading): Base Qwen2.5-7B (not fine-tuned initially)
    - Agent 3 (Generation): Base Qwen2.5-3B (not fine-tuned initially)

    Available baseline methods (8/8 modes - COMPLETE COVERAGE):
    1. run_lesson_start_baseline() - Agent 1 (3B)
    2. run_teaching_vocab_baseline() - Agent 1 (3B, batch_introduction only)
    3. run_teaching_grammar_baseline() - Agent 1 (3B, topic_explanation only)
    4. run_feedback_vocab_baseline() - Agent 1 (3B)
    5. run_feedback_grammar_baseline() - Agent 1 (3B)
    6. run_grading_vocab_baseline() - Direct model (7B)
    7. run_grading_grammar_baseline() - Direct model (7B, quiz_grading only)
    8. run_exercise_generation_baseline() - Direct model (3B, exercise_gen only)

    Note: Some modes only evaluate primary sub-groups for speed (marked above).
    To evaluate all sub-groups, extend the relevant method to sample from more sub-groups.

    Pattern for Agent 1 methods (1-5):
    1. Sample test cases from self.pipeline.test_cases[mode_name]
    2. Call teaching_agent.handle_*() with input_data
    3. Collect responses and run evaluation
    4. Return (model_responses, results) tuple

    Pattern for direct model methods (6-8):
    1. Sample test cases from self.pipeline.test_cases[mode_name]
    2. Use flatten_nested_input() to prepare data
    3. Use prompt templates to generate prompts
    4. Call self.generate_response() with appropriate model
    5. Return (model_responses, results) tuple
    """

    def __init__(
        self,
        model_3b_name: str = "Qwen/Qwen2.5-3B-Instruct",
        model_7b_name: str = "Qwen/Qwen2.5-7B-Instruct",
        test_cases_path: str | Path | None = None,
        teaching_agent_test_cases_path: str | Path | None = None,
    ) -> None:
        """
        Initialize baseline evaluator with both 3B and 7B models.

        Args:
            model_3b_name: HuggingFace model ID for 3B model (teaching, feedback, generation)
            model_7b_name: HuggingFace model ID for 7B model (grading)
            test_cases_path: Path to test cases JSON for Agent 2/3 (defaults to test_cases.json)
            teaching_agent_test_cases_path: Path to Agent 1 test cases (defaults to teaching_agent_test_cases.json)

        Raises:
            RuntimeError: If model loading fails
            FileNotFoundError: If test cases file not found
        """
        self.model_3b_name = model_3b_name
        self.model_7b_name = model_7b_name
        self.test_cases_path = Path(test_cases_path) if test_cases_path else DEFAULT_TEST_CASES_PATH
        self.teaching_agent_test_cases_path = (
            Path(teaching_agent_test_cases_path)
            if teaching_agent_test_cases_path
            else TEACHING_AGENT_TEST_CASES_PATH
        )

        # Lazy loading - models loaded on first access
        self._model_3b = None
        self._tokenizer_3b = None
        self._model_7b = None
        self._tokenizer_7b = None
        self._teaching_agent = None

        # Load both pipelines: one for Agent 1, one for Agent 2/3
        try:
            self.teaching_pipeline = EvaluationPipeline(self.teaching_agent_test_cases_path)
            logger.info(f"Loaded Agent 1 test cases from {self.teaching_agent_test_cases_path}")
        except FileNotFoundError:
            logger.error(
                f"Agent 1 test cases file not found: {self.teaching_agent_test_cases_path}"
            )
            raise

        try:
            self.pipeline = EvaluationPipeline(self.test_cases_path)
            logger.info(f"Loaded Agent 2/3 test cases from {self.test_cases_path}")
        except FileNotFoundError:
            logger.warning(f"Agent 2/3 test cases file not found: {self.test_cases_path}")
            self.pipeline = None  # Optional for now

    @property
    def model_3b(self):
        """Lazy load 3B model on first access."""
        if self._model_3b is None:
            try:
                logger.info(f"Loading 3B model: {self.model_3b_name}...")
                self._model_3b = AutoModelForCausalLM.from_pretrained(
                    self.model_3b_name,
                    device_map="auto",
                    torch_dtype="auto",
                )
                logger.info("✓ 3B model loaded successfully")
            except Exception as e:
                error_msg = f"Failed to load 3B model {self.model_3b_name}: {e}"
                logger.error(error_msg)
                raise RuntimeError(error_msg) from e
        return self._model_3b

    @property
    def tokenizer_3b(self):
        """Lazy load 3B tokenizer on first access."""
        if self._tokenizer_3b is None:
            self._tokenizer_3b = AutoTokenizer.from_pretrained(self.model_3b_name)
        return self._tokenizer_3b

    @property
    def model_7b(self):
        """Lazy load 7B model on first access."""
        if self._model_7b is None:
            try:
                logger.info(f"Loading 7B model: {self.model_7b_name}...")
                self._model_7b = AutoModelForCausalLM.from_pretrained(
                    self.model_7b_name,
                    device_map="auto",
                    torch_dtype="auto",
                )
                logger.info("✓ 7B model loaded successfully")
            except Exception as e:
                error_msg = f"Failed to load 7B model {self.model_7b_name}: {e}"
                logger.error(error_msg)
                raise RuntimeError(error_msg) from e
        return self._model_7b

    @property
    def tokenizer_7b(self):
        """Lazy load 7B tokenizer on first access."""
        if self._tokenizer_7b is None:
            self._tokenizer_7b = AutoTokenizer.from_pretrained(self.model_7b_name)
        return self._tokenizer_7b

    @property
    def teaching_agent(self):
        """Lazy load TeachingAgent on first access."""
        if self._teaching_agent is None:
            logger.info("Initializing TeachingAgent with 3B model...")
            self._teaching_agent = TeachingAgent(
                model=self.model_3b,
                tokenizer=self.tokenizer_3b,
                max_new_tokens=DEFAULT_MAX_TOKENS,
            )
            logger.info("✓ TeachingAgent initialized")
        return self._teaching_agent

    def generate_response(
        self, prompt: str, max_new_tokens: int = DEFAULT_MAX_TOKENS, use_7b: bool = False
    ) -> str:
        """
        Generate response from base model (3B or 7B).

        Args:
            prompt: Input prompt
            max_new_tokens: Maximum tokens to generate
            use_7b: If True, use 7B model; if False, use 3B model (default)

        Returns:
            Generated text
        """
        # Select model and tokenizer
        if use_7b:
            model = self.model_7b
            tokenizer = self.tokenizer_7b
        else:
            model = self.model_3b
            tokenizer = self.tokenizer_3b

        inputs = tokenizer(prompt, return_tensors="pt").to(model.device)

        outputs = model.generate(
            **inputs,
            max_new_tokens=max_new_tokens,
            do_sample=False,  # Deterministic for evaluation
            pad_token_id=tokenizer.eos_token_id,
        )

        response = tokenizer.decode(outputs[0], skip_special_tokens=True)

        # Remove the prompt from response
        if response.startswith(prompt):
            response = response[len(prompt) :].strip()

        return response

    def run_lesson_start_baseline(
        self, sample_size: int = DEFAULT_SAMPLE_SIZE
    ) -> tuple[dict[str, str], dict]:
        """
        Run baseline evaluation on lesson_start mode (Prompt #1).

        Args:
            sample_size: Number of test cases to evaluate

        Returns:
            Tuple of (model_responses, evaluation_results)
        """
        logger.info("\n=== Running Lesson Start Baseline ===\n")

        model_responses = {}
        lesson_start_cases = self.teaching_pipeline.get_test_cases_for_mode("lesson_start")[
            :sample_size
        ]

        for test_case in lesson_start_cases:
            test_id = test_case["test_id"]
            input_data = test_case["input"]

            logger.info(f"Evaluating {test_id}...")
            response = self.teaching_agent.handle_lesson_start(input_data)
            model_responses[test_id] = response

        # Run evaluation
        results = self.teaching_pipeline.evaluate_lesson_start(model_responses)
        return model_responses, results

    def run_teaching_vocab_baseline(
        self, sample_size: int = DEFAULT_SAMPLE_SIZE
    ) -> tuple[dict[str, str], dict]:
        """
        Run baseline evaluation on teaching_vocab mode (batch_introduction only).

        Note: Only evaluates batch_introduction for speed.
        Extend to other sub-groups (vocab_overview, list_view, etc.) if needed.

        Args:
            sample_size: Number of test cases to evaluate

        Returns:
            Tuple of (model_responses, evaluation_results)
        """
        logger.info("\n=== Running Teaching Vocab Baseline ===\n")

        model_responses = {}
        # Only use batch_introduction subgroup (other subgroups have different templates)
        vocab_cases = self.teaching_pipeline.test_cases["teaching_vocab"]["batch_introduction"][
            :sample_size
        ]

        for test_case in vocab_cases:
            test_id = test_case["test_id"]
            input_data = test_case["input"]

            logger.info(f"Evaluating {test_id}...")
            response = self.teaching_agent.handle_teaching_vocab(input_data)
            model_responses[test_id] = response

        # Run evaluation
        results = self.teaching_pipeline.evaluate_teaching_vocab(model_responses)
        return model_responses, results

    def run_grading_vocab_baseline(
        self, sample_size: int = DEFAULT_SAMPLE_SIZE
    ) -> tuple[dict[str, str], dict]:
        """
        Run baseline evaluation on grading_vocab mode (Prompt #15).

        Uses 7B model (Agent 2 - Grading).

        Args:
            sample_size: Number of test cases to evaluate per sub-group

        Returns:
            Tuple of (model_responses, evaluation_results)

        Raises:
            RuntimeError: If Agent 2/3 test cases not loaded
        """
        if self.pipeline is None:
            raise RuntimeError(
                "Agent 2/3 test cases not loaded. Cannot run grading_vocab baseline. "
                f"Ensure {self.test_cases_path} exists."
            )

        logger.info("\n=== Running Grading Vocab Baseline ===\n")

        model_responses = {}
        grading_mode = self.pipeline.test_cases["grading_vocab"]

        # Sample from both correct and incorrect translations
        vocab_cases = (
            grading_mode["correct_translations"][:sample_size]
            + grading_mode["incorrect_translations"][:sample_size]
        )

        for test_case in vocab_cases:
            test_id = test_case["test_id"]
            input_data = test_case["input"]

            # Use template to generate prompt
            prompt = GRADING_VOCAB.format(**input_data)

            logger.info(f"Evaluating {test_id}...")
            # Use 7B model for grading (Agent 2)
            response = self.generate_response(
                prompt, max_new_tokens=GRADING_MAX_TOKENS, use_7b=True
            )
            model_responses[test_id] = response

        # Run evaluation
        results = self.pipeline.evaluate_grading_vocab(model_responses)
        return model_responses, results

    def run_teaching_grammar_baseline(
        self, sample_size: int = DEFAULT_SAMPLE_SIZE
    ) -> tuple[dict[str, str], dict]:
        """
        Run baseline evaluation on teaching_grammar mode (topic_explanation only).

        Note: Only evaluates topic_explanation for speed.
        Extend to other sub-groups (grammar_overview, quiz_question, topic_summary) if needed.

        Args:
            sample_size: Number of test cases to evaluate

        Returns:
            Tuple of (model_responses, evaluation_results)
        """
        logger.info("\n=== Running Teaching Grammar Baseline ===\n")

        model_responses = {}
        # Only use topic_explanation subgroup (other subgroups have different templates)
        grammar_cases = self.teaching_pipeline.test_cases["teaching_grammar"]["topic_explanation"][
            :sample_size
        ]

        for test_case in grammar_cases:
            test_id = test_case["test_id"]
            input_data = test_case["input"]

            logger.info(f"Evaluating {test_id}...")
            response = self.teaching_agent.handle_teaching_grammar(input_data)
            model_responses[test_id] = response

        # Run evaluation
        results = self.teaching_pipeline.evaluate_teaching_grammar(model_responses)
        return model_responses, results

    def run_feedback_vocab_baseline(
        self, sample_size: int = DEFAULT_SAMPLE_SIZE
    ) -> tuple[dict[str, str], dict]:
        """
        Run baseline evaluation on feedback_vocab mode.

        Args:
            sample_size: Number of test cases to evaluate per sub-group

        Returns:
            Tuple of (model_responses, evaluation_results)
        """
        logger.info("\n=== Running Feedback Vocab Baseline ===\n")

        model_responses = {}
        feedback_cases = self.teaching_pipeline.get_test_cases_for_mode("feedback_vocab")[
            : sample_size * 2
        ]

        for test_case in feedback_cases:
            test_id = test_case["test_id"]
            input_data = test_case["input"]

            logger.info(f"Evaluating {test_id}...")
            response = self.teaching_agent.handle_feedback_vocab(input_data)
            model_responses[test_id] = response

        # Run evaluation
        results = self.teaching_pipeline.evaluate_feedback_vocab(model_responses)
        return model_responses, results

    def run_feedback_grammar_baseline(
        self, sample_size: int = DEFAULT_SAMPLE_SIZE
    ) -> tuple[dict[str, str], dict]:
        """
        Run baseline evaluation on feedback_grammar mode.

        Args:
            sample_size: Number of test cases to evaluate per sub-group

        Returns:
            Tuple of (model_responses, evaluation_results)
        """
        logger.info("\n=== Running Feedback Grammar Baseline ===\n")

        model_responses = {}
        feedback_cases = self.teaching_pipeline.get_test_cases_for_mode("feedback_grammar")[
            : sample_size * 2
        ]

        for test_case in feedback_cases:
            test_id = test_case["test_id"]
            input_data = test_case["input"]

            logger.info(f"Evaluating {test_id}...")
            response = self.teaching_agent.handle_feedback_grammar(input_data)
            model_responses[test_id] = response

        # Run evaluation
        results = self.teaching_pipeline.evaluate_feedback_grammar(model_responses)
        return model_responses, results

    def run_grading_grammar_baseline(
        self, sample_size: int = DEFAULT_SAMPLE_SIZE
    ) -> tuple[dict[str, str], dict]:
        """
        Run baseline evaluation on grading_grammar mode (quiz_grading only).

        Uses 7B model (Agent 2 - Grading).

        Note: Only evaluates quiz_grading for speed.
        Extend to test_grading if needed (which uses different template).

        Args:
            sample_size: Number of test cases to evaluate

        Returns:
            Tuple of (model_responses, evaluation_results)

        Raises:
            RuntimeError: If Agent 2/3 test cases not loaded
        """
        if self.pipeline is None:
            raise RuntimeError(
                "Agent 2/3 test cases not loaded. Cannot run grading_grammar baseline. "
                f"Ensure {self.test_cases_path} exists."
            )

        logger.info("\n=== Running Grading Grammar Baseline ===\n")

        model_responses = {}
        grading_mode = self.pipeline.test_cases["grading_grammar"]

        # Sample quiz_grading cases
        grammar_cases = grading_mode["quiz_grading"][:sample_size]

        for test_case in grammar_cases:
            test_id = test_case["test_id"]
            input_data = test_case["input"]

            # Use template to generate prompt
            prompt = GRADING_GRAMMAR_QUIZ.format(**input_data)

            logger.info(f"Evaluating {test_id}...")
            # Use 7B model for grading (Agent 2)
            response = self.generate_response(
                prompt, max_new_tokens=GRADING_MAX_TOKENS, use_7b=True
            )
            model_responses[test_id] = response

        # Run evaluation
        results = self.pipeline.evaluate_grading_grammar(model_responses)
        return model_responses, results

    def run_exercise_generation_baseline(
        self, sample_size: int = DEFAULT_SAMPLE_SIZE
    ) -> tuple[dict[str, str], dict]:
        """
        Run baseline evaluation on exercise_generation mode (exercise_gen only).

        Note: Only evaluates exercise_gen sub-group for speed.
        AlignmentMetric will use Qwen2.5-7B as judge.

        Args:
            sample_size: Number of test cases to evaluate

        Returns:
            Tuple of (model_responses, evaluation_results)

        Raises:
            RuntimeError: If Agent 2/3 test cases not loaded
        """
        if self.pipeline is None:
            raise RuntimeError(
                "Agent 2/3 test cases not loaded. Cannot run exercise_generation baseline. "
                f"Ensure {self.test_cases_path} exists."
            )

        logger.info("\n=== Running Exercise Generation Baseline ===\n")

        model_responses = {}
        exercise_mode = self.pipeline.test_cases["exercise_generation"]

        # Sample exercise_gen cases
        exercise_cases = exercise_mode["exercise_gen"][:sample_size]

        for test_case in exercise_cases:
            test_id = test_case["test_id"]
            input_data = test_case["input"]

            # Use formatter to flatten input
            flattened = flatten_nested_input(input_data)

            # Use template to generate prompt
            prompt = EXERCISE_GENERATION.format(**flattened)

            logger.info(f"Evaluating {test_id}...")
            response = self.generate_response(prompt, max_new_tokens=DEFAULT_MAX_TOKENS)
            model_responses[test_id] = response

        # Run evaluation (includes AlignmentMetric with 7B judge)
        results = self.pipeline.evaluate_exercise_generation(model_responses)
        return model_responses, results

    def save_baseline_report(
        self,
        results_by_mode: dict[str, dict],
        outputs_by_mode: dict[str, dict[str, str]],
        output_path: str | Path | None = None,
    ) -> None:
        """
        Save baseline evaluation report and detailed outputs for all evaluated modes.

        Args:
            results_by_mode: Dict mapping mode names to their evaluation results
                Example: {"lesson_start": {...}, "teaching_vocab": {...}, "grading_vocab": {...}}
            outputs_by_mode: Dict mapping mode names to model outputs (test_id -> response)
            output_path: Output file path (defaults to PROJECT_ROOT/data/evaluation/baseline_report.md)
        """
        output_file = Path(output_path) if output_path else DEFAULT_BASELINE_REPORT_PATH

        report = [
            "# Baseline Evaluation Report",
            "",
            "**Models:**",
            f"- Teaching/Feedback/Generation: {self.model_3b_name} (3B)",
            f"- Grading: {self.model_7b_name} (7B)",
            "**Fine-tuning:** None (base models)",
            "",
            "## Purpose",
            "",
            "Establish baseline scores for base Qwen2.5-3B model (no fine-tuning).",
            "**Goal:** Fine-tuned model should significantly outperform these scores.",
            "",
            "---",
            "",
        ]

        # Add report for each mode
        for mode_name, mode_results in results_by_mode.items():
            mode_report = self.pipeline.generate_report(mode_results, mode_name)
            report.append(mode_report)
            report.append("")
            report.append("---")
            report.append("")

        # Save markdown report
        output_file.parent.mkdir(parents=True, exist_ok=True)

        with open(output_file, "w") as f:
            f.write("\n".join(report))

        logger.info(f"\n✓ Baseline report saved to: {output_file}")

        # Save detailed outputs JSON
        outputs_file = output_file.parent / "baseline_outputs.json"
        self._save_detailed_outputs(outputs_by_mode, results_by_mode, outputs_file)

    def _save_detailed_outputs(
        self,
        outputs_by_mode: dict[str, dict[str, str]],
        results_by_mode: dict[str, dict],
        output_file: Path,
    ) -> None:
        """
        Save detailed model outputs with inputs and scores for manual review.

        Args:
            outputs_by_mode: Model outputs by mode (test_id -> response)
            results_by_mode: Evaluation results by mode
            output_file: Path to save JSON
        """
        import json

        detailed_outputs = {}

        for mode_name, model_responses in outputs_by_mode.items():
            mode_results = results_by_mode[mode_name]
            detailed_outputs[mode_name] = {}

            # Get test cases for this mode using centralized helper
            test_cases_list = self.pipeline.get_test_cases_for_mode(mode_name)

            # Build dict mapping test_id -> test_case for O(1) lookup
            test_cases_by_id = {tc["test_id"]: tc for tc in test_cases_list}

            # Build output dict with test case details
            for test_id, response in model_responses.items():
                # O(1) lookup instead of O(n) scan
                test_case = test_cases_by_id.get(test_id)

                # Find scores from results
                scores = {}
                passed = False
                if "metrics" in mode_results:
                    for metric_name, metric_results_list in mode_results["metrics"].items():
                        for result in metric_results_list:
                            if result.get("test_id") == test_id:
                                scores[metric_name] = {
                                    "score": result.get("score", 0.0),
                                    "passed": result.get("passed", False),
                                    "reason": result.get("reason", ""),
                                }
                                passed = passed or result.get("passed", False)

                detailed_outputs[mode_name][test_id] = {
                    "input": test_case["input"] if test_case else {},
                    "expected_output": test_case.get("expected_output") if test_case else None,
                    "model_output": response,
                    "passed": passed,
                    "scores": scores,
                }

        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(detailed_outputs, f, indent=2, ensure_ascii=False)

        logger.info(f"✓ Detailed outputs saved to: {output_file}")


def main() -> None:
    """Run baseline evaluation across all 8 modes."""
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    logger.info("=== Baseline Evaluation ===")
    logger.info("Testing base Qwen2.5-3B (no fine-tuning) against evaluation dataset")
    logger.info("Evaluating all 8 modes with sample_size=5 per mode\n")

    evaluator = BaselineEvaluator()
    results_by_mode = {}
    outputs_by_mode = {}

    # Define all baseline methods to run
    baseline_methods = [
        ("lesson_start", evaluator.run_lesson_start_baseline),
        ("teaching_vocab", evaluator.run_teaching_vocab_baseline),
        ("teaching_grammar", evaluator.run_teaching_grammar_baseline),
        ("feedback_vocab", evaluator.run_feedback_vocab_baseline),
        ("feedback_grammar", evaluator.run_feedback_grammar_baseline),
        ("grading_vocab", evaluator.run_grading_vocab_baseline),
        ("grading_grammar", evaluator.run_grading_grammar_baseline),
        ("exercise_generation", evaluator.run_exercise_generation_baseline),
    ]

    # Run all baselines and collect results + outputs
    for mode_name, baseline_method in baseline_methods:
        model_outputs, mode_results = baseline_method()
        results_by_mode[mode_name] = mode_results
        outputs_by_mode[mode_name] = model_outputs

        mode_pct = EvaluationPipeline._safe_percentage(
            mode_results["passed"], mode_results["total"]
        )
        logger.info(f"\n{mode_name.replace('_', ' ').title()} Results:")
        logger.info(f"  Passed: {mode_results['passed']}/{mode_results['total']} ({mode_pct:.1f}%)")

    # Calculate overall statistics
    total_cases = sum(r["total"] for r in results_by_mode.values())
    total_passed = sum(r["passed"] for r in results_by_mode.values())
    overall_pct = EvaluationPipeline._safe_percentage(total_passed, total_cases)

    logger.info("\n" + "=" * 60)
    logger.info(f"Overall: {total_passed}/{total_cases} passed ({overall_pct:.1f}%)")
    logger.info("=" * 60)

    # Save comprehensive report and detailed outputs
    evaluator.save_baseline_report(results_by_mode, outputs_by_mode)

    logger.info("\n=== Baseline Evaluation Complete ===")


if __name__ == "__main__":
    main()
