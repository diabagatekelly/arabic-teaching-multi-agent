"""Evaluate fine-tuned Agent 2 (Grading) model vs baseline."""

from __future__ import annotations

import argparse
import json
import logging
import sys
from datetime import datetime
from pathlib import Path

import torch
from peft import AutoPeftModelForCausalLM
from transformers import AutoTokenizer

PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from scripts.evaluation.eval_utils import (  # noqa: E402
    create_metadata,
    format_summary,
    save_evaluation_results,
    save_json_responses,
)
from src.agents import ContentAgent, GradingAgent  # noqa: E402
from src.evaluation.deepeval_pipeline import EvaluationPipeline  # noqa: E402

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

logger = logging.getLogger(__name__)

TEST_CASES_PATH = (
    PROJECT_ROOT / "data" / "evaluation" / "grading_agent" / "grading_agent_test_cases.json"
)
FINETUNED_MODEL_PATH = PROJECT_ROOT / "models" / "qwen-7b-arabic-grading"
OUTPUT_DIR = PROJECT_ROOT / "data" / "evaluation" / "grading_agent" / "finetuned"


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


def retrieve_rag_context(
    test_case: dict,
    content_agent: ContentAgent,
    content_type: str,
) -> dict | None:
    """Retrieve RAG context for a test case."""
    lesson_num = test_case.get("lesson_number", 1)
    try:
        rag_context_raw = content_agent.retrieve_content(
            {"lesson_number": lesson_num, "content_type": content_type, "format": "practice"}
        )
        rag_context = json.loads(rag_context_raw)
        logger.info(f"  └─ RAG context retrieved for lesson {lesson_num}")
        return rag_context
    except Exception as e:
        logger.warning(f"  └─ No RAG context: {e}")
        return None


def evaluate_grading_mode(
    mode_name: str,
    test_cases: list[dict],
    grading_func: callable,
    content_agent: ContentAgent,
    content_type: str,
) -> dict[str, str]:
    """Evaluate a grading mode (vocab or grammar) with RAG context."""
    logger.info("=" * 80)
    logger.info(mode_name.upper())
    logger.info("=" * 80)

    responses = {}
    for i, test_case in enumerate(test_cases, 1):
        test_id = test_case["test_id"]
        logger.info(f"[{i}/{len(test_cases)}] Grading {content_type}: {test_id}")

        rag_context = retrieve_rag_context(test_case, content_agent, content_type)
        response = grading_func(test_case["input"], rag_context=rag_context)
        responses[test_id] = response

    logger.info(f"\n✓ {mode_name} complete")
    return responses


def collect_test_cases(
    mode_data: dict,
    sample_size: int | None,
) -> list[dict]:
    """Collect test cases from mode data with optional sampling."""
    test_cases = []
    for subgroup_name, subgroup_cases in mode_data.items():
        if isinstance(subgroup_cases, list):
            sampled = subgroup_cases[:sample_size] if sample_size else subgroup_cases
            test_cases.extend(sampled)
            logger.info(f"  {subgroup_name}: {len(sampled)} test cases")
    return test_cases


def calculate_pass_rate(results: dict) -> float:
    """Calculate pass rate from results."""
    total = results.get("total", 0)
    if total == 0:
        return 0.0
    return results.get("passed", 0) / total


def generate_markdown_report(
    vocab_results: dict,
    grammar_results: dict,
    model_name: str,
) -> str:
    """Generate markdown evaluation report."""
    vocab_total = vocab_results.get("total", 0)
    vocab_passed = vocab_results.get("passed", 0)
    vocab_pass_rate = calculate_pass_rate(vocab_results)

    grammar_total = grammar_results.get("total", 0)
    grammar_passed = grammar_results.get("passed", 0)
    grammar_pass_rate = calculate_pass_rate(grammar_results)

    overall_total = vocab_total + grammar_total
    overall_passed = vocab_passed + grammar_passed
    overall_pass_rate = overall_passed / overall_total if overall_total > 0 else 0

    report = f"""# Agent 2 (Grading) - Fine-Tuned Evaluation

**Model:** {model_name}
**Evaluation Date:** {datetime.now().strftime("%Y-%m-%d")}

## Overall Summary

- **Total Test Cases:** {overall_total}
- **Passed:** {overall_passed}
- **Failed:** {overall_total - overall_passed}
- **Pass Rate:** {overall_pass_rate:.1%}

## By Mode

### Grading Vocabulary
- **Total Test Cases:** {vocab_total}
- **Passed:** {vocab_passed}
- **Failed:** {vocab_results.get("failed", 0)}
- **Pass Rate:** {vocab_pass_rate:.1%}

### Grading Grammar
- **Total Test Cases:** {grammar_total}
- **Passed:** {grammar_passed}
- **Failed:** {grammar_results.get("failed", 0)}
- **Pass Rate:** {grammar_pass_rate:.1%}

## Metrics Breakdown

### Vocabulary Grading
{format_metrics(vocab_results.get("metrics", {}))}

### Grammar Grading
{format_metrics(grammar_results.get("metrics", {}))}

## Detailed Test Results

### Vocabulary Grading
{format_test_results(vocab_results)}

### Grammar Grading
{format_test_results(grammar_results)}
"""
    return report


def format_metrics(metrics: dict) -> str:
    """Format metrics summary."""
    if not metrics:
        return "No metrics available"

    output = []
    for metric_name, metric_results in sorted(metrics.items()):
        if not metric_results:
            continue

        passed = sum(1 for r in metric_results if r.get("passed", False))
        total = len(metric_results)
        pass_rate = passed / total if total > 0 else 0
        avg_score = sum(r.get("score", 0) for r in metric_results) / total if total > 0 else 0

        output.append(
            f"- **{metric_name.replace('_', ' ').title()}:** {passed}/{total} ({pass_rate:.1%}), avg score: {avg_score:.3f}"
        )

    return "\n".join(output) if output else "No metrics available"


def format_test_results(results: dict) -> str:
    """Format test results for markdown."""
    output = []
    metrics = results.get("metrics", {})

    if not metrics:
        return "No test results available"

    test_status = {}

    for metric_name, metric_results in metrics.items():
        if not metric_results:
            continue

        for metric_result in metric_results:
            test_id = metric_result.get("test_id", "unknown")
            passed = metric_result.get("passed", False)
            score = metric_result.get("score", 0)
            reason = metric_result.get("reason", "")

            if test_id not in test_status:
                test_status[test_id] = {}
            test_status[test_id][metric_name] = (passed, score, reason)

    for test_id in sorted(test_status.keys()):
        metrics_data = test_status[test_id]
        all_passed = all(passed for passed, _, _ in metrics_data.values())
        status = "✓" if all_passed else "✗"

        output.append(f"\n#### {status} {test_id}")
        output.append("")

        for metric_name, (passed, score, reason) in metrics_data.items():
            metric_status = "✓" if passed else "✗"
            output.append(
                f"- {metric_status} **{metric_name.replace('_', ' ').title()}:** {score:.2f}"
            )
            if reason:
                display_reason = reason if len(reason) <= 200 else reason[:197] + "..."
                output.append(f"  - {display_reason}")

    return "\n".join(output)


def run_vocab_grading(
    pipeline: EvaluationPipeline,
    grading_agent: GradingAgent,
    content_agent: ContentAgent,
    sample_size: int | None,
) -> tuple[dict[str, str], dict]:
    """Run vocabulary grading evaluation."""
    vocab_cases = collect_test_cases(pipeline.test_cases["grading_vocab"], sample_size)
    logger.info(f"\nTotal vocab test cases: {len(vocab_cases)}\n")

    vocab_responses = evaluate_grading_mode(
        "Vocabulary Grading",
        vocab_cases,
        grading_agent.grade_vocab,
        content_agent,
        "vocab",
    )

    logger.info("Running evaluation metrics...")
    vocab_results = pipeline.evaluate_grading_vocab(vocab_responses)
    return vocab_responses, vocab_results


def run_grammar_grading(
    pipeline: EvaluationPipeline,
    grading_agent: GradingAgent,
    content_agent: ContentAgent,
    sample_size: int | None,
) -> tuple[dict[str, str], dict]:
    """Run grammar grading evaluation."""
    grammar_cases = collect_test_cases(pipeline.test_cases["grading_grammar"], sample_size)
    logger.info(f"\nTotal grammar test cases: {len(grammar_cases)}\n")

    grammar_responses = evaluate_grading_mode(
        "Grammar Grading",
        grammar_cases,
        grading_agent.grade_grammar_quiz,
        content_agent,
        "grammar",
    )

    logger.info("Running evaluation metrics...")
    grammar_results = pipeline.evaluate_grading_grammar(grammar_responses)
    return grammar_responses, grammar_results


def save_results(
    output_dir: Path,
    vocab_results: dict,
    grammar_results: dict,
    model_name: str,
    vocab_responses: dict,
    grammar_responses: dict,
) -> None:
    """Save evaluation results to files."""
    save_json_responses(output_dir, vocab_responses, "vocab_responses.json")
    save_json_responses(output_dir, grammar_responses, "grammar_responses.json")

    results_data = {
        "metadata": create_metadata(model_name, "Agent 2 (Grading)"),
        "grading_vocab": vocab_results,
        "grading_grammar": grammar_results,
    }

    report = generate_markdown_report(vocab_results, grammar_results, model_name)
    save_evaluation_results(output_dir, results_data, report)


def main() -> None:
    """Run fine-tuned model evaluation."""
    parser = argparse.ArgumentParser(description="Evaluate fine-tuned Agent 2 (Grading) model")
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
    logger.info("AGENT 2 (GRADING) - FINE-TUNED MODEL EVALUATION")
    logger.info("=" * 80)
    logger.info("")

    model, tokenizer = load_finetuned_model(Path(args.model_path))

    logger.info("Initializing GradingAgent and ContentAgent (with RAG)...")
    grading_agent = GradingAgent(
        model=model,
        tokenizer=tokenizer,
        max_new_tokens=50,
    )
    content_agent = ContentAgent(
        model=model,
        tokenizer=tokenizer,
    )
    logger.info("✓ Agents initialized")
    logger.info(
        f"  RAG loaded: {len(content_agent.lessons)} lessons, {len(content_agent.exercise_templates)} templates"
    )

    logger.info(f"Loading test cases from {TEST_CASES_PATH}...")
    pipeline = EvaluationPipeline(TEST_CASES_PATH)
    logger.info("✓ Test cases loaded")

    sample_text = (
        f"(sampling {args.sample_size} per subgroup)" if args.sample_size else "(all test cases)"
    )
    logger.info(f"\nEvaluating {sample_text}\n")

    vocab_responses, vocab_results = run_vocab_grading(
        pipeline, grading_agent, content_agent, args.sample_size
    )

    logger.info("\n")
    grammar_responses, grammar_results = run_grammar_grading(
        pipeline, grading_agent, content_agent, args.sample_size
    )

    model_name = f"Fine-tuned Qwen2.5-7B (LoRA) from {args.model_path}"
    save_results(
        OUTPUT_DIR,
        vocab_results,
        grammar_results,
        model_name,
        vocab_responses,
        grammar_responses,
    )

    logger.info("\n" + "=" * 80)
    logger.info("SUMMARY")
    logger.info("=" * 80)

    logger.info(f"\nVocabulary Grading: {format_summary(vocab_results)}")
    logger.info(f"Grammar Grading:    {format_summary(grammar_results)}")

    overall_total = vocab_results.get("total", 0) + grammar_results.get("total", 0)
    overall_passed = vocab_results.get("passed", 0) + grammar_results.get("passed", 0)
    overall_rate = overall_passed / overall_total if overall_total > 0 else 0
    logger.info(
        f"\nOverall:            {overall_passed}/{overall_total} passed ({overall_rate:.1%})"
    )

    logger.info(f"\n✓ Evaluation complete! Results saved to {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
