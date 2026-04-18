"""Evaluate fine-tuned Agent 1 (Teaching/Presentation) model."""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

import torch
from peft import AutoPeftModelForCausalLM
from transformers import AutoTokenizer

PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from scripts.evaluation.eval_utils import (
    collect_test_cases,
    create_metadata,
    format_mode_section,
    format_summary,
    generate_overall_summary,
    save_evaluation_results,
    save_json_responses,
)
from src.agents import TeachingAgent
from src.evaluation.deepeval_pipeline import EvaluationPipeline

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

logger = logging.getLogger(__name__)

TEST_CASES_PATH = (
    PROJECT_ROOT / "data" / "evaluation" / "teaching_agent" / "teaching_agent_test_cases.json"
)
FINETUNED_MODEL_PATH = PROJECT_ROOT / "models" / "qwen-7b-arabic-teaching"
OUTPUT_DIR = PROJECT_ROOT / "data" / "evaluation" / "teaching_agent" / "finetuned"


def load_finetuned_model(model_path: Path) -> tuple:
    """Load fine-tuned LoRA model with base model."""
    logger.info(f"Loading fine-tuned model from {model_path}...")

    model = AutoPeftModelForCausalLM.from_pretrained(
        str(model_path),
        device_map="auto",
        torch_dtype=torch.float16,
    )

    tokenizer = AutoTokenizer.from_pretrained(str(model_path))

    logger.info("✓ Fine-tuned model loaded")
    return model, tokenizer


def run_lesson_start_evaluation(
    agent: TeachingAgent, pipeline: EvaluationPipeline, sample_size: int | None
) -> tuple[dict, dict]:
    """Run lesson start evaluation."""
    logger.info("=" * 80)
    logger.info("LESSON START")
    logger.info("=" * 80)

    test_cases = pipeline.test_cases["lesson_start"]["test_cases"]
    if sample_size:
        test_cases = test_cases[:sample_size]

    logger.info(f"Total test cases: {len(test_cases)}\n")

    responses = {}
    for i, test_case in enumerate(test_cases, 1):
        test_id = test_case["test_id"]
        logger.info(f"[{i}/{len(test_cases)}] {test_id}")
        responses[test_id] = agent.handle_lesson_start(test_case["input"])

    logger.info("\n✓ Lesson start evaluation complete")
    logger.info("Running evaluation metrics...")
    results = pipeline.evaluate_lesson_start(responses)
    return responses, results


def run_teaching_vocab_evaluation(
    agent: TeachingAgent, pipeline: EvaluationPipeline, sample_size: int | None
) -> tuple[dict, dict]:
    """Run teaching vocabulary evaluation."""
    logger.info("\n" + "=" * 80)
    logger.info("TEACHING VOCABULARY")
    logger.info("=" * 80)

    vocab_mode = pipeline.test_cases["teaching_vocab"]
    test_cases = collect_test_cases(
        vocab_mode, subgroups=["batch_introduction"], sample_size=sample_size
    )

    logger.info(f"\nTotal vocab test cases: {len(test_cases)}\n")

    responses = {}
    for i, test_case in enumerate(test_cases, 1):
        test_id = test_case["test_id"]
        logger.info(f"[{i}/{len(test_cases)}] {test_id}")
        responses[test_id] = agent.handle_teaching_vocab(test_case["input"])

    logger.info("\n✓ Teaching vocabulary evaluation complete")
    logger.info("Running evaluation metrics...")
    results = pipeline.evaluate_teaching_vocab(responses)
    return responses, results


def run_teaching_grammar_evaluation(
    agent: TeachingAgent, pipeline: EvaluationPipeline, sample_size: int | None
) -> tuple[dict, dict]:
    """Run teaching grammar evaluation."""
    logger.info("\n" + "=" * 80)
    logger.info("TEACHING GRAMMAR")
    logger.info("=" * 80)

    grammar_mode = pipeline.test_cases["teaching_grammar"]
    test_cases = collect_test_cases(
        grammar_mode, subgroups=["topic_explanation"], sample_size=sample_size
    )

    logger.info(f"\nTotal grammar test cases: {len(test_cases)}\n")

    responses = {}
    for i, test_case in enumerate(test_cases, 1):
        test_id = test_case["test_id"]
        logger.info(f"[{i}/{len(test_cases)}] {test_id}")
        responses[test_id] = agent.handle_teaching_grammar(test_case["input"])

    logger.info("\n✓ Teaching grammar evaluation complete")
    logger.info("Running evaluation metrics...")
    results = pipeline.evaluate_teaching_grammar(responses)
    return responses, results


def run_feedback_vocab_evaluation(
    agent: TeachingAgent, pipeline: EvaluationPipeline, sample_size: int | None
) -> tuple[dict, dict]:
    """Run feedback vocabulary evaluation."""
    logger.info("\n" + "=" * 80)
    logger.info("FEEDBACK VOCABULARY")
    logger.info("=" * 80)

    feedback_mode = pipeline.test_cases["feedback_vocab"]
    test_cases = collect_test_cases(
        feedback_mode,
        subgroups=["correct_feedback", "incorrect_feedback"],
        sample_size=sample_size,
    )

    logger.info(f"\nTotal feedback vocab test cases: {len(test_cases)}\n")

    responses = {}
    for i, test_case in enumerate(test_cases, 1):
        test_id = test_case["test_id"]
        logger.info(f"[{i}/{len(test_cases)}] {test_id}")
        responses[test_id] = agent.handle_feedback_vocab(test_case["input"])

    logger.info("\n✓ Feedback vocabulary evaluation complete")
    logger.info("Running evaluation metrics...")
    results = pipeline.evaluate_feedback_vocab(responses)
    return responses, results


def run_feedback_grammar_evaluation(
    agent: TeachingAgent, pipeline: EvaluationPipeline, sample_size: int | None
) -> tuple[dict, dict]:
    """Run feedback grammar evaluation."""
    logger.info("\n" + "=" * 80)
    logger.info("FEEDBACK GRAMMAR")
    logger.info("=" * 80)

    feedback_mode = pipeline.test_cases["feedback_grammar"]
    test_cases = collect_test_cases(
        feedback_mode,
        subgroups=["correct_feedback", "incorrect_feedback"],
        sample_size=sample_size,
    )

    logger.info(f"\nTotal feedback grammar test cases: {len(test_cases)}\n")

    responses = {}
    for i, test_case in enumerate(test_cases, 1):
        test_id = test_case["test_id"]
        logger.info(f"[{i}/{len(test_cases)}] {test_id}")
        responses[test_id] = agent.handle_feedback_grammar(test_case["input"])

    logger.info("\n✓ Feedback grammar evaluation complete")
    logger.info("Running evaluation metrics...")
    results = pipeline.evaluate_feedback_grammar(responses)
    return responses, results


def collect_all_results(
    agent: TeachingAgent, pipeline: EvaluationPipeline, sample_size: int | None
) -> tuple[dict[str, str], dict[str, dict]]:
    """Collect all evaluation results across all modes."""
    lesson_start_responses, lesson_start_results = run_lesson_start_evaluation(
        agent, pipeline, sample_size
    )

    teaching_vocab_responses, teaching_vocab_results = run_teaching_vocab_evaluation(
        agent, pipeline, sample_size
    )

    (
        teaching_grammar_responses,
        teaching_grammar_results,
    ) = run_teaching_grammar_evaluation(agent, pipeline, sample_size)

    feedback_vocab_responses, feedback_vocab_results = run_feedback_vocab_evaluation(
        agent, pipeline, sample_size
    )

    (
        feedback_grammar_responses,
        feedback_grammar_results,
    ) = run_feedback_grammar_evaluation(agent, pipeline, sample_size)

    all_responses = {
        **lesson_start_responses,
        **teaching_vocab_responses,
        **teaching_grammar_responses,
        **feedback_vocab_responses,
        **feedback_grammar_responses,
    }

    results_by_mode = {
        "lesson_start": lesson_start_results,
        "teaching_vocab": teaching_vocab_results,
        "teaching_grammar": teaching_grammar_results,
        "feedback_vocab": feedback_vocab_results,
        "feedback_grammar": feedback_grammar_results,
    }

    return all_responses, results_by_mode


def generate_markdown_report(results_by_mode: dict[str, dict], model_name: str) -> str:
    """Generate markdown evaluation report."""
    from datetime import datetime

    all_results = list(results_by_mode.values())

    overall_total, overall_passed, overall_pass_rate = generate_overall_summary(all_results)

    report = f"""# Agent 1 (Teaching/Presentation) - Fine-Tuned Evaluation

**Model:** {model_name}
**Evaluation Date:** {datetime.now().strftime("%Y-%m-%d")}

## Overall Summary

- **Total Test Cases:** {overall_total}
- **Passed:** {overall_passed}
- **Failed:** {overall_total - overall_passed}
- **Pass Rate:** {overall_pass_rate:.1%}

## By Mode

{format_mode_section("Lesson Start", results_by_mode["lesson_start"])}

{format_mode_section("Teaching Vocabulary", results_by_mode["teaching_vocab"])}

{format_mode_section("Teaching Grammar", results_by_mode["teaching_grammar"])}

{format_mode_section("Feedback Vocabulary", results_by_mode["feedback_vocab"])}

{format_mode_section("Feedback Grammar", results_by_mode["feedback_grammar"])}

## Metrics Details

Detailed metrics for each mode are available in `results.json`.
"""
    return report


def log_summary(results_by_mode: dict[str, dict]) -> None:
    """Log evaluation summary."""
    logger.info("\n" + "=" * 80)
    logger.info("SUMMARY")
    logger.info("=" * 80)

    logger.info(f"\nLesson Start:        {format_summary(results_by_mode['lesson_start'])}")
    logger.info(f"Teaching Vocabulary: {format_summary(results_by_mode['teaching_vocab'])}")
    logger.info(f"Teaching Grammar:    {format_summary(results_by_mode['teaching_grammar'])}")
    logger.info(f"Feedback Vocabulary: {format_summary(results_by_mode['feedback_vocab'])}")
    logger.info(f"Feedback Grammar:    {format_summary(results_by_mode['feedback_grammar'])}")

    all_results = list(results_by_mode.values())
    overall_total, overall_passed, overall_rate = generate_overall_summary(all_results)
    logger.info(
        f"\nOverall:             {overall_passed}/{overall_total} passed ({overall_rate:.1%})"
    )


def main() -> None:
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

    model, tokenizer = load_finetuned_model(Path(args.model_path))

    logger.info("Initializing TeachingAgent...")
    teaching_agent = TeachingAgent(
        model=model,
        tokenizer=tokenizer,
        max_new_tokens=256,
    )
    logger.info("✓ TeachingAgent initialized")

    logger.info(f"Loading test cases from {TEST_CASES_PATH}...")
    pipeline = EvaluationPipeline(TEST_CASES_PATH)
    logger.info("✓ Test cases loaded")

    sample_size = args.sample_size
    sample_text = f"(sampling {sample_size} per subgroup)" if sample_size else "(all test cases)"
    logger.info(f"\nEvaluating {sample_text}\n")

    all_responses, results_by_mode = collect_all_results(teaching_agent, pipeline, sample_size)

    model_name = f"Fine-tuned Qwen2.5-3B (LoRA) from {args.model_path}"

    save_json_responses(OUTPUT_DIR, all_responses, "all_responses.json")

    results_data = {
        "metadata": create_metadata(model_name, "Agent 1 (Teaching/Presentation)"),
        **results_by_mode,
    }

    markdown_report = generate_markdown_report(results_by_mode, model_name)

    save_evaluation_results(OUTPUT_DIR, results_data, markdown_report)

    log_summary(results_by_mode)

    logger.info(f"\n✓ Evaluation complete! Results saved to {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
