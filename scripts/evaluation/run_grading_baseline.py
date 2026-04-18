"""Run Agent 2 (Grading) baseline evaluations."""

from __future__ import annotations

import argparse
import logging
import sys
from datetime import datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from scripts.evaluation.eval_utils import (  # noqa: E402
    create_metadata,
    format_mode_section,
    format_summary,
    save_evaluation_results,
)
from src.evaluation.baseline import BaselineEvaluator  # noqa: E402

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

logger = logging.getLogger(__name__)

# Output directory
DEFAULT_OUTPUT_DIR = PROJECT_ROOT / "data" / "evaluation" / "grading_agent"
DEFAULT_SAMPLE_SIZE = 10


def save_results(
    output_dir: Path, vocab_results: dict, grammar_results: dict, model_size: str
) -> None:
    """Save evaluation results to files."""
    metadata = create_metadata(f"Qwen/Qwen2.5-{model_size}-Instruct", "Agent 2 (Grading)")
    metadata["model_size"] = model_size

    results_json = {
        "metadata": metadata,
        "grading_vocab": vocab_results,
        "grading_grammar": grammar_results,
    }

    report = generate_markdown_report(vocab_results, grammar_results, model_size)
    save_evaluation_results(output_dir, results_json, report)


def generate_markdown_report(vocab_results: dict, grammar_results: dict, model_size: str) -> str:
    """Generate markdown evaluation report."""
    return f"""# Agent 2 (Grading) - {model_size} Baseline Evaluation

**Model:** Qwen/Qwen2.5-{model_size}-Instruct
**Evaluation Date:** {datetime.now().strftime("%Y-%m-%d")}

## Summary

{format_mode_section("Grading Vocabulary", vocab_results)}

{format_mode_section("Grading Grammar", grammar_results)}

## Detailed Results

### Grading Vocabulary
{format_test_results(vocab_results)}

### Grading Grammar
{format_test_results(grammar_results)}
"""


def format_test_results(results: dict) -> str:
    """Format test results for markdown."""
    output = []
    metrics = results.get("metrics", {})

    if not metrics:
        return "No test results available"

    # Group test results by test_id
    test_status = {}  # test_id -> overall passed/failed

    # Process each metric
    for metric_name, metric_results in metrics.items():
        if not metric_results:
            continue

        output.append(f"\n#### {metric_name.replace('_', ' ').title()}")

        for metric_result in metric_results:
            test_id = metric_result.get("test_id", "unknown")
            passed = metric_result.get("passed", False)
            score = metric_result.get("score", 0)
            reason = metric_result.get("reason", "")

            # Track overall test status (test fails if any metric fails)
            if test_id not in test_status:
                test_status[test_id] = True
            if not passed:
                test_status[test_id] = False

            status = "✓" if passed else "✗"
            output.append(f"- {status} `{test_id}` (score: {score:.2f})")
            if not passed and reason:
                output.append(f"  - {reason}")

    # Add summary at the top
    summary_lines = ["\n#### Test Summary"]
    for test_id, passed in sorted(test_status.items()):
        status = "✓" if passed else "✗"
        summary_lines.append(f"- {status} `{test_id}`")

    return "\n".join(summary_lines + output)


def run_baseline_evaluation(
    evaluator: BaselineEvaluator, sample_size: int | None, model_size: str = "7B"
) -> tuple[dict, dict]:
    """Run baseline evaluation for both vocab and grammar."""
    logger.info("=" * 80)
    logger.info(f"AGENT 2 (GRADING) - {model_size} BASELINE")
    logger.info("=" * 80 + "\n")

    logger.info("Running grading_vocab with 7B model...")
    _, vocab_results = evaluator.run_grading_vocab_baseline(sample_size=sample_size, use_7b=True)
    logger.info("✓ Vocab grading (7B) complete")

    logger.info("Running grading_grammar with 7B model...")
    _, grammar_results = evaluator.run_grading_grammar_baseline(
        sample_size=sample_size, use_7b=True
    )
    logger.info("✓ Grammar grading (7B) complete")

    return vocab_results, grammar_results


def main() -> None:
    """Run grading baseline evaluation with 7B model."""
    parser = argparse.ArgumentParser(description="Run baseline grading evaluation")
    parser.add_argument(
        "--sample-size",
        type=int,
        default=DEFAULT_SAMPLE_SIZE,
        help="Number of test cases to evaluate per subgroup (None = all)",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default=str(DEFAULT_OUTPUT_DIR),
        help="Path to output directory",
    )
    args = parser.parse_args()

    logger.info("Initializing BaselineEvaluator...")
    evaluator = BaselineEvaluator()

    vocab_results, grammar_results = run_baseline_evaluation(evaluator, args.sample_size)

    save_results(Path(args.output_dir), vocab_results, grammar_results, "7B")

    logger.info("\n" + "=" * 80)
    logger.info("SUMMARY")
    logger.info("=" * 80 + "\n")

    logger.info(f"Vocabulary Grading: {format_summary(vocab_results)}")
    logger.info(f"Grammar Grading:    {format_summary(grammar_results)}")

    logger.info("\n✓ Evaluation complete!")


if __name__ == "__main__":
    main()
