"""Run Agent 2 (Grading) baseline evaluations."""

import json
import logging
import sys
from datetime import datetime
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.evaluation.baseline import BaselineEvaluator  # noqa: E402

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

logger = logging.getLogger(__name__)

# Output directory
OUTPUT_DIR = PROJECT_ROOT / "data" / "evaluation" / "grading_agent"


def save_results(output_dir: Path, vocab_results: dict, grammar_results: dict, model_size: str):
    """Save evaluation results to files."""
    output_dir.mkdir(parents=True, exist_ok=True)

    # Save detailed results as JSON
    results_json = {
        "metadata": {
            "model_size": model_size,
            "evaluation_date": datetime.now().isoformat(),
            "agent": "Agent 2 (Grading)",
        },
        "grading_vocab": vocab_results,
        "grading_grammar": grammar_results,
    }

    with open(output_dir / "results.json", "w") as f:
        json.dump(results_json, f, indent=2)

    # Generate markdown report
    report = generate_markdown_report(vocab_results, grammar_results, model_size)
    with open(output_dir / "evaluation_report.md", "w") as f:
        f.write(report)

    logger.info(f"✓ Results saved to {output_dir}")


def generate_markdown_report(vocab_results: dict, grammar_results: dict, model_size: str) -> str:
    """Generate markdown evaluation report."""
    # Calculate pass rates
    vocab_total = vocab_results.get("total", 0)
    vocab_passed = vocab_results.get("passed", 0)
    vocab_pass_rate = vocab_passed / vocab_total if vocab_total > 0 else 0

    grammar_total = grammar_results.get("total", 0)
    grammar_passed = grammar_results.get("passed", 0)
    grammar_pass_rate = grammar_passed / grammar_total if grammar_total > 0 else 0

    report = f"""# Agent 2 (Grading) - {model_size} Baseline Evaluation

**Model:** Qwen/Qwen2.5-{model_size}-Instruct
**Evaluation Date:** {datetime.now().strftime("%Y-%m-%d")}

## Summary

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

## Detailed Results

### Grading Vocabulary
{format_test_results(vocab_results)}

### Grading Grammar
{format_test_results(grammar_results)}
"""
    return report


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


def main():
    """Run grading baseline evaluation with 7B model."""
    logger.info("Initializing BaselineEvaluator...")
    evaluator = BaselineEvaluator()

    # Test sample size (use smaller number for quick testing, or None for all)
    sample_size = 10

    # ========================================================================
    # 7B Baseline
    # ========================================================================
    logger.info("\n" + "=" * 80)
    logger.info("AGENT 2 (GRADING) - 7B BASELINE")
    logger.info("=" * 80 + "\n")

    # Vocab grading - 7B
    logger.info("Running grading_vocab with 7B model...")
    vocab_responses_7b, vocab_results_7b = evaluator.run_grading_vocab_baseline(
        sample_size=sample_size, use_7b=True
    )
    logger.info("✓ Vocab grading (7B) complete")

    # Grammar grading - 7B
    logger.info("Running grading_grammar with 7B model...")
    grammar_responses_7b, grammar_results_7b = evaluator.run_grading_grammar_baseline(
        sample_size=sample_size, use_7b=True
    )
    logger.info("✓ Grammar grading (7B) complete")

    # Save results
    save_results(OUTPUT_DIR, vocab_results_7b, grammar_results_7b, "7B")

    # ========================================================================
    # Summary
    # ========================================================================
    logger.info("\n" + "=" * 80)
    logger.info("SUMMARY")
    logger.info("=" * 80 + "\n")

    def format_summary(results: dict) -> str:
        total = results.get("total", 0)
        passed = results.get("passed", 0)
        pass_rate = passed / total if total > 0 else 0
        return f"{passed}/{total} passed ({pass_rate:.1%})"

    logger.info("Vocabulary Grading:")
    logger.info(f"  7B: {format_summary(vocab_results_7b)}")

    logger.info("\nGrammar Grading:")
    logger.info(f"  7B: {format_summary(grammar_results_7b)}")

    logger.info("\n✓ Evaluation complete!")


if __name__ == "__main__":
    main()
