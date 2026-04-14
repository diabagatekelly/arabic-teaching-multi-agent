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

# Output directories
GRADING_EVAL_DIR = PROJECT_ROOT / "data" / "evaluation" / "grading_agent"
BASELINE_3B_DIR = GRADING_EVAL_DIR / "3b_baseline"
BASELINE_7B_DIR = GRADING_EVAL_DIR / "7b_baseline"


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
    report = f"""# Agent 2 (Grading) - {model_size} Baseline Evaluation

**Model:** Qwen/Qwen2.5-{model_size}-Instruct
**Evaluation Date:** {datetime.now().strftime("%Y-%m-%d")}

## Summary

### Grading Vocabulary
- **Total Test Cases:** {vocab_results.get("total_test_cases", 0)}
- **Passed:** {vocab_results.get("passed", 0)}
- **Failed:** {vocab_results.get("failed", 0)}
- **Pass Rate:** {vocab_results.get("pass_rate", 0):.1%}

### Grading Grammar
- **Total Test Cases:** {grammar_results.get("total_test_cases", 0)}
- **Passed:** {grammar_results.get("passed", 0)}
- **Failed:** {grammar_results.get("failed", 0)}
- **Pass Rate:** {grammar_results.get("pass_rate", 0):.1%}

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

    for test_id, test_result in results.get("test_results", {}).items():
        status = "✓" if test_result.get("passed", False) else "✗"
        output.append(f"- {status} `{test_id}`")

        # Show metric details
        for metric_name, metric_result in test_result.get("metrics", {}).items():
            if not metric_result.get("success", False):
                reason = metric_result.get("reason", "No reason provided")
                output.append(f"  - {metric_name}: {reason}")

    return "\n".join(output) if output else "No test results available"


def main():
    """Run grading baseline evaluations for both 3B and 7B models."""
    logger.info("Initializing BaselineEvaluator...")
    evaluator = BaselineEvaluator()

    # Test sample size (use smaller number for quick testing, or None for all)
    sample_size = 10

    # ========================================================================
    # 3B Baseline
    # ========================================================================
    logger.info("\n" + "=" * 80)
    logger.info("AGENT 2 (GRADING) - 3B BASELINE")
    logger.info("=" * 80 + "\n")

    # Vocab grading - 3B
    logger.info("Running grading_vocab with 3B model...")
    vocab_responses_3b, vocab_results_3b = evaluator.run_grading_vocab_baseline(
        sample_size=sample_size, use_7b=False
    )
    logger.info("✓ Vocab grading (3B) complete")

    # Grammar grading - 3B
    logger.info("Running grading_grammar with 3B model...")
    grammar_responses_3b, grammar_results_3b = evaluator.run_grading_grammar_baseline(
        sample_size=sample_size, use_7b=False
    )
    logger.info("✓ Grammar grading (3B) complete")

    # Save 3B results
    save_results(BASELINE_3B_DIR, vocab_results_3b, grammar_results_3b, "3B")

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

    # Save 7B results
    save_results(BASELINE_7B_DIR, vocab_results_7b, grammar_results_7b, "7B")

    # ========================================================================
    # Summary
    # ========================================================================
    logger.info("\n" + "=" * 80)
    logger.info("COMPARISON SUMMARY")
    logger.info("=" * 80 + "\n")

    logger.info("Vocabulary Grading:")
    logger.info(f"  3B: {vocab_results_3b.get('summary', {})}")
    logger.info(f"  7B: {vocab_results_7b.get('summary', {})}")

    logger.info("\nGrammar Grading:")
    logger.info(f"  3B: {grammar_results_3b.get('summary', {})}")
    logger.info(f"  7B: {grammar_results_7b.get('summary', {})}")

    logger.info("\n✓ All evaluations complete!")


if __name__ == "__main__":
    main()
