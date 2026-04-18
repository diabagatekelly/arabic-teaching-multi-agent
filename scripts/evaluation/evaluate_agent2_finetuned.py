"""Evaluate fine-tuned Agent 2 (Grading) model vs baseline."""

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

from src.agents import ContentAgent, GradingAgent
from src.evaluation.deepeval_pipeline import EvaluationPipeline

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

logger = logging.getLogger(__name__)

# Paths
TEST_CASES_PATH = (
    PROJECT_ROOT / "data" / "evaluation" / "grading_agent" / "grading_agent_test_cases.json"
)
FINETUNED_MODEL_PATH = PROJECT_ROOT / "models" / "qwen-7b-arabic-grading"
OUTPUT_DIR = PROJECT_ROOT / "data" / "evaluation" / "grading_agent" / "finetuned"


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
    vocab_results: dict,
    grammar_results: dict,
    model_name: str,
    vocab_responses: dict = None,
    grammar_responses: dict = None,
):
    """Save evaluation results to files."""
    output_dir.mkdir(parents=True, exist_ok=True)

    # Save responses (for inspection)
    if vocab_responses:
        with open(output_dir / "vocab_responses.json", "w", encoding="utf-8") as f:
            json.dump(vocab_responses, f, indent=2, ensure_ascii=False)

    if grammar_responses:
        with open(output_dir / "grammar_responses.json", "w", encoding="utf-8") as f:
            json.dump(grammar_responses, f, indent=2, ensure_ascii=False)

    # Save detailed results as JSON
    results_json = {
        "metadata": {
            "model": model_name,
            "evaluation_date": datetime.now().isoformat(),
            "agent": "Agent 2 (Grading)",
        },
        "grading_vocab": vocab_results,
        "grading_grammar": grammar_results,
    }

    with open(output_dir / "results.json", "w") as f:
        json.dump(results_json, f, indent=2)

    # Generate markdown report
    report = generate_markdown_report(vocab_results, grammar_results, model_name)
    with open(output_dir / "evaluation_report.md", "w") as f:
        f.write(report)

    logger.info(f"✓ Results saved to {output_dir}")


def generate_markdown_report(vocab_results: dict, grammar_results: dict, model_name: str) -> str:
    """Generate markdown evaluation report."""
    # Calculate pass rates
    vocab_total = vocab_results.get("total", 0)
    vocab_passed = vocab_results.get("passed", 0)
    vocab_pass_rate = vocab_passed / vocab_total if vocab_total > 0 else 0

    grammar_total = grammar_results.get("total", 0)
    grammar_passed = grammar_results.get("passed", 0)
    grammar_pass_rate = grammar_passed / grammar_total if grammar_total > 0 else 0

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

    # Group test results by test_id
    test_status = {}  # test_id -> {metric_name: (passed, score, reason)}

    # Process each metric
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

    # Format by test case
    for test_id in sorted(test_status.keys()):
        metrics_data = test_status[test_id]
        # Test passes if all metrics pass
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
                # Truncate long reasons
                display_reason = reason if len(reason) <= 200 else reason[:197] + "..."
                output.append(f"  - {display_reason}")

    return "\n".join(output)


def main():
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

    # Load fine-tuned model
    model, tokenizer = load_finetuned_model(Path(args.model_path))

    # Create agents with fine-tuned model
    logger.info("Initializing GradingAgent and ContentAgent (with RAG)...")
    grading_agent = GradingAgent(
        model=model,
        tokenizer=tokenizer,
        max_new_tokens=50,  # Grading should be short
    )
    content_agent = ContentAgent(
        model=model,
        tokenizer=tokenizer,
    )
    logger.info("✓ Agents initialized")
    logger.info(
        f"  RAG loaded: {len(content_agent.lessons)} lessons, {len(content_agent.exercise_templates)} templates"
    )

    # Load test cases
    logger.info(f"Loading test cases from {TEST_CASES_PATH}...")
    pipeline = EvaluationPipeline(TEST_CASES_PATH)
    logger.info("✓ Test cases loaded")

    sample_size = args.sample_size
    sample_text = f"(sampling {sample_size} per subgroup)" if sample_size else "(all test cases)"
    logger.info(f"\nEvaluating {sample_text}\n")

    # ========================================================================
    # Vocabulary Grading
    # ========================================================================
    logger.info("=" * 80)
    logger.info("VOCABULARY GRADING")
    logger.info("=" * 80)

    vocab_responses = {}
    grading_mode = pipeline.test_cases["grading_vocab"]

    # Sample from all subgroups
    vocab_cases = []
    for subgroup_name, subgroup_cases in grading_mode.items():
        if isinstance(subgroup_cases, list):
            sampled = subgroup_cases[:sample_size] if sample_size else subgroup_cases
            vocab_cases.extend(sampled)
            logger.info(f"  {subgroup_name}: {len(sampled)} test cases")

    logger.info(f"\nTotal vocab test cases: {len(vocab_cases)}\n")

    for i, test_case in enumerate(vocab_cases, 1):
        test_id = test_case["test_id"]
        logger.info(f"[{i}/{len(vocab_cases)}] Grading vocab: {test_id}")

        # Get RAG context for this test (simulating production flow)
        lesson_num = test_case.get("lesson_number", 1)
        try:
            rag_context_raw = content_agent.retrieve_content(
                {"lesson_number": lesson_num, "content_type": "vocab", "format": "practice"}
            )
            rag_context = json.loads(rag_context_raw)
            logger.info(f"  └─ RAG context retrieved for lesson {lesson_num}")
        except Exception as e:
            logger.warning(f"  └─ No RAG context: {e}")
            rag_context = None

        # Grade with RAG context (production flow)
        response = grading_agent.grade_vocab(test_case["input"], rag_context=rag_context)
        vocab_responses[test_id] = response

    logger.info("\n✓ Vocabulary grading complete")
    logger.info("Running evaluation metrics...")
    vocab_results = pipeline.evaluate_grading_vocab(vocab_responses)

    # ========================================================================
    # Grammar Grading
    # ========================================================================
    logger.info("\n" + "=" * 80)
    logger.info("GRAMMAR GRADING")
    logger.info("=" * 80)

    grammar_responses = {}
    grading_mode = pipeline.test_cases["grading_grammar"]

    # Sample from all subgroups
    grammar_cases = []
    for subgroup_name, subgroup_cases in grading_mode.items():
        if isinstance(subgroup_cases, list):
            sampled = subgroup_cases[:sample_size] if sample_size else subgroup_cases
            grammar_cases.extend(sampled)
            logger.info(f"  {subgroup_name}: {len(sampled)} test cases")

    logger.info(f"\nTotal grammar test cases: {len(grammar_cases)}\n")

    for i, test_case in enumerate(grammar_cases, 1):
        test_id = test_case["test_id"]
        logger.info(f"[{i}/{len(grammar_cases)}] Grading grammar: {test_id}")

        # Get RAG context for this test (simulating production flow)
        lesson_num = test_case.get("lesson_number", 1)
        try:
            rag_context_raw = content_agent.retrieve_content(
                {"lesson_number": lesson_num, "content_type": "grammar", "format": "practice"}
            )
            rag_context = json.loads(rag_context_raw)
            logger.info(f"  └─ RAG context retrieved for lesson {lesson_num}")
        except Exception as e:
            logger.warning(f"  └─ No RAG context: {e}")
            rag_context = None

        # Grade with RAG context (production flow)
        response = grading_agent.grade_grammar_quiz(test_case["input"], rag_context=rag_context)
        grammar_responses[test_id] = response

    logger.info("\n✓ Grammar grading complete")
    logger.info("Running evaluation metrics...")
    grammar_results = pipeline.evaluate_grading_grammar(grammar_responses)

    # ========================================================================
    # Save Results
    # ========================================================================
    model_name = f"Fine-tuned Qwen2.5-7B (LoRA) from {args.model_path}"
    save_results(
        OUTPUT_DIR,
        vocab_results,
        grammar_results,
        model_name,
        vocab_responses,
        grammar_responses,
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
