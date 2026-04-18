"""Evaluate fine-tuned Agent 1 (Teaching/Presentation) model."""

import argparse
import json
import logging
import sys
from datetime import datetime
from pathlib import Path

import torch
from peft import AutoPeftModelForCausalLM
from transformers import AutoTokenizer

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.agents import TeachingAgent
from src.evaluation.deepeval_pipeline import EvaluationPipeline

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

logger = logging.getLogger(__name__)

# Paths
TEST_CASES_PATH = (
    PROJECT_ROOT / "data" / "evaluation" / "teaching_agent" / "teaching_agent_test_cases.json"
)
FINETUNED_MODEL_PATH = PROJECT_ROOT / "models" / "qwen-7b-arabic-teaching"
OUTPUT_DIR = PROJECT_ROOT / "data" / "evaluation" / "teaching_agent" / "finetuned"


def load_finetuned_model(model_path: Path):
    """Load fine-tuned LoRA model with base model."""
    logger.info(f"Loading fine-tuned model from {model_path}...")

    # Load LoRA model (automatically loads base model + adapters)
    model = AutoPeftModelForCausalLM.from_pretrained(
        str(model_path),
        device_map="auto",
        torch_dtype=torch.float16,
    )

    tokenizer = AutoTokenizer.from_pretrained(str(model_path))

    logger.info("✓ Fine-tuned model loaded")
    return model, tokenizer


def save_results(
    output_dir: Path,
    lesson_start_results: dict,
    teaching_vocab_results: dict,
    teaching_grammar_results: dict,
    feedback_vocab_results: dict,
    feedback_grammar_results: dict,
    model_name: str,
    responses: dict,
):
    """Save evaluation results to files."""
    output_dir.mkdir(parents=True, exist_ok=True)

    # Save all responses (for inspection)
    with open(output_dir / "all_responses.json", "w", encoding="utf-8") as f:
        json.dump(responses, f, indent=2, ensure_ascii=False)

    # Save detailed results as JSON
    results_json = {
        "metadata": {
            "model": model_name,
            "evaluation_date": datetime.now().isoformat(),
            "agent": "Agent 1 (Teaching/Presentation)",
        },
        "lesson_start": lesson_start_results,
        "teaching_vocab": teaching_vocab_results,
        "teaching_grammar": teaching_grammar_results,
        "feedback_vocab": feedback_vocab_results,
        "feedback_grammar": feedback_grammar_results,
    }

    with open(output_dir / "results.json", "w") as f:
        json.dump(results_json, f, indent=2)

    # Generate markdown report
    report = generate_markdown_report(
        lesson_start_results,
        teaching_vocab_results,
        teaching_grammar_results,
        feedback_vocab_results,
        feedback_grammar_results,
        model_name,
    )
    with open(output_dir / "evaluation_report.md", "w") as f:
        f.write(report)

    logger.info(f"✓ Results saved to {output_dir}")


def generate_markdown_report(
    lesson_start_results: dict,
    teaching_vocab_results: dict,
    teaching_grammar_results: dict,
    feedback_vocab_results: dict,
    feedback_grammar_results: dict,
    model_name: str,
) -> str:
    """Generate markdown evaluation report."""

    # Calculate overall metrics
    all_results = [
        lesson_start_results,
        teaching_vocab_results,
        teaching_grammar_results,
        feedback_vocab_results,
        feedback_grammar_results,
    ]

    overall_total = sum(r.get("total", 0) for r in all_results)
    overall_passed = sum(r.get("passed", 0) for r in all_results)
    overall_pass_rate = overall_passed / overall_total if overall_total > 0 else 0

    report = f"""# Agent 1 (Teaching/Presentation) - Fine-Tuned Evaluation

**Model:** {model_name}
**Evaluation Date:** {datetime.now().strftime("%Y-%m-%d")}

## Overall Summary

- **Total Test Cases:** {overall_total}
- **Passed:** {overall_passed}
- **Failed:** {overall_total - overall_passed}
- **Pass Rate:** {overall_pass_rate:.1%}

## By Mode

### Lesson Start
- **Total Test Cases:** {lesson_start_results.get("total", 0)}
- **Passed:** {lesson_start_results.get("passed", 0)}
- **Failed:** {lesson_start_results.get("failed", 0)}
- **Pass Rate:** {lesson_start_results.get("passed", 0) / lesson_start_results.get("total", 1):.1%}

### Teaching Vocabulary
- **Total Test Cases:** {teaching_vocab_results.get("total", 0)}
- **Passed:** {teaching_vocab_results.get("passed", 0)}
- **Failed:** {teaching_vocab_results.get("failed", 0)}
- **Pass Rate:** {teaching_vocab_results.get("passed", 0) / teaching_vocab_results.get("total", 1):.1%}

### Teaching Grammar
- **Total Test Cases:** {teaching_grammar_results.get("total", 0)}
- **Passed:** {teaching_grammar_results.get("passed", 0)}
- **Failed:** {teaching_grammar_results.get("failed", 0)}
- **Pass Rate:** {teaching_grammar_results.get("passed", 0) / teaching_grammar_results.get("total", 1):.1%}

### Feedback Vocabulary
- **Total Test Cases:** {feedback_vocab_results.get("total", 0)}
- **Passed:** {feedback_vocab_results.get("passed", 0)}
- **Failed:** {feedback_vocab_results.get("failed", 0)}
- **Pass Rate:** {feedback_vocab_results.get("passed", 0) / feedback_vocab_results.get("total", 1):.1%}

### Feedback Grammar
- **Total Test Cases:** {feedback_grammar_results.get("total", 0)}
- **Passed:** {feedback_grammar_results.get("passed", 0)}
- **Failed:** {feedback_grammar_results.get("failed", 0)}
- **Pass Rate:** {feedback_grammar_results.get("passed", 0) / feedback_grammar_results.get("total", 1):.1%}

## Metrics Details

Detailed metrics for each mode are available in `results.json`.
"""
    return report


def main():
    """Run fine-tuned model evaluation."""
    parser = argparse.ArgumentParser(description="Evaluate fine-tuned Agent 1 (Teaching) model")
    parser.add_argument(
        "--sample-size",
        type=int,
        default=None,
        help="Number of test cases to evaluate per subgroup (None = all)",
    )
    parser.add_argument(
        "--model-path",
        type=str,
        default=str(FINETUNED_MODEL_PATH),
        help="Path to fine-tuned model directory",
    )
    args = parser.parse_args()

    logger.info("=" * 80)
    logger.info("AGENT 1 (TEACHING/PRESENTATION) - FINE-TUNED MODEL EVALUATION")
    logger.info("=" * 80)
    logger.info("")

    # Load fine-tuned model
    model, tokenizer = load_finetuned_model(Path(args.model_path))

    # Create teaching agent
    logger.info("Initializing TeachingAgent...")
    teaching_agent = TeachingAgent(
        model=model,
        tokenizer=tokenizer,
        max_new_tokens=256,  # Teaching responses can be longer
    )
    logger.info("✓ TeachingAgent initialized")

    # Load test cases
    logger.info(f"Loading test cases from {TEST_CASES_PATH}...")
    pipeline = EvaluationPipeline(TEST_CASES_PATH)
    logger.info("✓ Test cases loaded")

    sample_size = args.sample_size
    sample_text = f"(sampling {sample_size} per subgroup)" if sample_size else "(all test cases)"
    logger.info(f"\nEvaluating {sample_text}\n")

    all_responses = {}

    # ========================================================================
    # Lesson Start
    # ========================================================================
    logger.info("=" * 80)
    logger.info("LESSON START")
    logger.info("=" * 80)

    lesson_start_responses = {}
    test_cases = pipeline.test_cases["lesson_start"]["test_cases"]
    if sample_size:
        test_cases = test_cases[:sample_size]

    logger.info(f"Total test cases: {len(test_cases)}\n")

    for i, test_case in enumerate(test_cases, 1):
        test_id = test_case["test_id"]
        logger.info(f"[{i}/{len(test_cases)}] {test_id}")

        response = teaching_agent.handle_lesson_start(test_case["input"])
        lesson_start_responses[test_id] = response

    logger.info("\n✓ Lesson start evaluation complete")
    logger.info("Running evaluation metrics...")
    lesson_start_results = pipeline.evaluate_lesson_start(lesson_start_responses)
    all_responses.update(lesson_start_responses)

    # ========================================================================
    # Teaching Vocabulary
    # ========================================================================
    logger.info("\n" + "=" * 80)
    logger.info("TEACHING VOCABULARY")
    logger.info("=" * 80)

    teaching_vocab_responses = {}
    vocab_mode = pipeline.test_cases["teaching_vocab"]

    # TeachingAgent only handles batch_introduction (primary teaching scenario)
    # Other subgroups would need different routing or additional agent methods
    subgroup_name = "batch_introduction"
    if subgroup_name in vocab_mode and isinstance(vocab_mode[subgroup_name], list):
        vocab_cases = vocab_mode[subgroup_name]
        sampled = vocab_cases[:sample_size] if sample_size else vocab_cases
        logger.info(f"  {subgroup_name}: {len(sampled)} test cases")
        logger.info(f"\nTotal vocab test cases: {len(sampled)}\n")

        for i, test_case in enumerate(sampled, 1):
            test_id = test_case["test_id"]
            logger.info(f"[{i}/{len(sampled)}] {test_id}")

            response = teaching_agent.handle_teaching_vocab(test_case["input"])
            teaching_vocab_responses[test_id] = response

    logger.info("\n✓ Teaching vocabulary evaluation complete")
    logger.info("Running evaluation metrics...")
    teaching_vocab_results = pipeline.evaluate_teaching_vocab(teaching_vocab_responses)
    all_responses.update(teaching_vocab_responses)

    # ========================================================================
    # Teaching Grammar
    # ========================================================================
    logger.info("\n" + "=" * 80)
    logger.info("TEACHING GRAMMAR")
    logger.info("=" * 80)

    teaching_grammar_responses = {}
    grammar_mode = pipeline.test_cases["teaching_grammar"]

    # TeachingAgent only handles topic_explanation (primary teaching scenario)
    # Other subgroups would need different routing or additional agent methods
    subgroup_name = "topic_explanation"
    if subgroup_name in grammar_mode and isinstance(grammar_mode[subgroup_name], list):
        grammar_cases = grammar_mode[subgroup_name]
        sampled = grammar_cases[:sample_size] if sample_size else grammar_cases
        logger.info(f"  {subgroup_name}: {len(sampled)} test cases")
        logger.info(f"\nTotal grammar test cases: {len(sampled)}\n")

        for i, test_case in enumerate(sampled, 1):
            test_id = test_case["test_id"]
            logger.info(f"[{i}/{len(sampled)}] {test_id}")

            response = teaching_agent.handle_teaching_grammar(test_case["input"])
            teaching_grammar_responses[test_id] = response

    logger.info("\n✓ Teaching grammar evaluation complete")
    logger.info("Running evaluation metrics...")
    teaching_grammar_results = pipeline.evaluate_teaching_grammar(teaching_grammar_responses)
    all_responses.update(teaching_grammar_responses)

    # ========================================================================
    # Feedback Vocabulary
    # ========================================================================
    logger.info("\n" + "=" * 80)
    logger.info("FEEDBACK VOCABULARY")
    logger.info("=" * 80)

    feedback_vocab_responses = {}
    feedback_mode = pipeline.test_cases["feedback_vocab"]

    # Collect from both correct and incorrect feedback
    feedback_cases = []
    for subgroup_name in ["correct_feedback", "incorrect_feedback"]:
        if subgroup_name in feedback_mode and isinstance(feedback_mode[subgroup_name], list):
            subgroup_cases = feedback_mode[subgroup_name]
            sampled = subgroup_cases[:sample_size] if sample_size else subgroup_cases
            feedback_cases.extend(sampled)
            logger.info(f"  {subgroup_name}: {len(sampled)} test cases")

    logger.info(f"\nTotal feedback vocab test cases: {len(feedback_cases)}\n")

    for i, test_case in enumerate(feedback_cases, 1):
        test_id = test_case["test_id"]
        logger.info(f"[{i}/{len(feedback_cases)}] {test_id}")

        response = teaching_agent.handle_feedback_vocab(test_case["input"])
        feedback_vocab_responses[test_id] = response

    logger.info("\n✓ Feedback vocabulary evaluation complete")
    logger.info("Running evaluation metrics...")
    feedback_vocab_results = pipeline.evaluate_feedback_vocab(feedback_vocab_responses)
    all_responses.update(feedback_vocab_responses)

    # ========================================================================
    # Feedback Grammar
    # ========================================================================
    logger.info("\n" + "=" * 80)
    logger.info("FEEDBACK GRAMMAR")
    logger.info("=" * 80)

    feedback_grammar_responses = {}
    feedback_mode = pipeline.test_cases["feedback_grammar"]

    # Collect from both correct and incorrect feedback
    feedback_cases = []
    for subgroup_name in ["correct_feedback", "incorrect_feedback"]:
        if subgroup_name in feedback_mode and isinstance(feedback_mode[subgroup_name], list):
            subgroup_cases = feedback_mode[subgroup_name]
            sampled = subgroup_cases[:sample_size] if sample_size else subgroup_cases
            feedback_cases.extend(sampled)
            logger.info(f"  {subgroup_name}: {len(sampled)} test cases")

    logger.info(f"\nTotal feedback grammar test cases: {len(feedback_cases)}\n")

    for i, test_case in enumerate(feedback_cases, 1):
        test_id = test_case["test_id"]
        logger.info(f"[{i}/{len(feedback_cases)}] {test_id}")

        response = teaching_agent.handle_feedback_grammar(test_case["input"])
        feedback_grammar_responses[test_id] = response

    logger.info("\n✓ Feedback grammar evaluation complete")
    logger.info("Running evaluation metrics...")
    feedback_grammar_results = pipeline.evaluate_feedback_grammar(feedback_grammar_responses)
    all_responses.update(feedback_grammar_responses)

    # ========================================================================
    # Save Results
    # ========================================================================
    model_name = f"Fine-tuned Qwen2.5-3B (LoRA) from {args.model_path}"
    save_results(
        OUTPUT_DIR,
        lesson_start_results,
        teaching_vocab_results,
        teaching_grammar_results,
        feedback_vocab_results,
        feedback_grammar_results,
        model_name,
        all_responses,
    )

    # ========================================================================
    # Summary
    # ========================================================================
    logger.info("\n" + "=" * 80)
    logger.info("SUMMARY")
    logger.info("=" * 80)

    def format_summary(results: dict) -> str:
        total = results.get("total", 0)
        passed = results.get("passed", 0)
        pass_rate = passed / total if total > 0 else 0
        return f"{passed}/{total} passed ({pass_rate:.1%})"

    logger.info(f"\nLesson Start:        {format_summary(lesson_start_results)}")
    logger.info(f"Teaching Vocabulary: {format_summary(teaching_vocab_results)}")
    logger.info(f"Teaching Grammar:    {format_summary(teaching_grammar_results)}")
    logger.info(f"Feedback Vocabulary: {format_summary(feedback_vocab_results)}")
    logger.info(f"Feedback Grammar:    {format_summary(feedback_grammar_results)}")

    overall_total = sum(
        [
            lesson_start_results.get("total", 0),
            teaching_vocab_results.get("total", 0),
            teaching_grammar_results.get("total", 0),
            feedback_vocab_results.get("total", 0),
            feedback_grammar_results.get("total", 0),
        ]
    )
    overall_passed = sum(
        [
            lesson_start_results.get("passed", 0),
            teaching_vocab_results.get("passed", 0),
            teaching_grammar_results.get("passed", 0),
            feedback_vocab_results.get("passed", 0),
            feedback_grammar_results.get("passed", 0),
        ]
    )
    overall_rate = overall_passed / overall_total if overall_total > 0 else 0
    logger.info(
        f"\nOverall:             {overall_passed}/{overall_total} passed ({overall_rate:.1%})"
    )

    logger.info(f"\n✓ Evaluation complete! Results saved to {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
