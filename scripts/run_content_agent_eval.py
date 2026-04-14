"""Run Agent 3 (Content/Exercise Generation) evaluations with 3B and 7B models."""

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
OUTPUT_DIR = PROJECT_ROOT / "data" / "evaluation" / "content_agent"


def save_results(output_dir: Path, results: dict, model_size: str, model_responses: dict):
    """Save evaluation results to files."""
    output_dir.mkdir(parents=True, exist_ok=True)

    # Save model responses (for manual inspection)
    responses_file = output_dir / f"evaluation_outputs_{model_size.lower()}.json"
    with open(responses_file, "w", encoding="utf-8") as f:
        json.dump(model_responses, f, indent=2, ensure_ascii=False)
    logger.info(f"✓ Responses saved to {responses_file}")

    # Save detailed results as JSON
    results_json = {
        "metadata": {
            "model_size": model_size,
            "evaluation_date": datetime.now().isoformat(),
            "agent": "Agent 3 (Content/Exercise Generation)",
        },
        "exercise_generation": results,
    }

    results_file = output_dir / f"results_{model_size.lower()}.json"
    with open(results_file, "w", encoding="utf-8") as f:
        json.dump(results_json, f, indent=2, ensure_ascii=False)
    logger.info(f"✓ Results saved to {results_file}")

    # Generate markdown report
    report = generate_markdown_report(results, model_size)
    report_file = output_dir / f"evaluation_report_{model_size.lower()}.md"
    with open(report_file, "w", encoding="utf-8") as f:
        f.write(report)
    logger.info(f"✓ Report saved to {report_file}")


def generate_markdown_report(results: dict, model_size: str) -> str:
    """Generate markdown evaluation report."""
    # Calculate pass rates
    total = results.get("total", 0)
    passed = results.get("passed", 0)
    failed = results.get("failed", 0)
    pass_rate = passed / total if total > 0 else 0

    report = [
        f"# Agent 3 (Content Generation) - {model_size} Evaluation",
        "",
        f"**Model:** Qwen/Qwen2.5-{model_size}-Instruct",
        f"**Evaluation Date:** {datetime.now().strftime('%Y-%m-%d')}",
        "",
        "## Summary",
        "",
        f"- **Total Test Cases:** {total}",
        f"- **Passed:** {passed}",
        f"- **Failed:** {failed}",
        f"- **Pass Rate:** {pass_rate:.1%}",
        "",
        "## Metrics Summary",
        "",
    ]

    # Add per-metric breakdown
    metrics = results.get("metrics", {})
    for metric_name, metric_results in sorted(metrics.items()):
        if not metric_results:
            continue

        metric_passed = sum(1 for r in metric_results if r.get("passed", False))
        metric_total = len(metric_results)
        metric_pass_rate = metric_passed / metric_total if metric_total > 0 else 0
        avg_score = (
            sum(r.get("score", 0) for r in metric_results) / metric_total if metric_total > 0 else 0
        )

        report.append(f"### {metric_name.replace('_', ' ').title()}")
        report.append(f"- **Pass Rate:** {metric_passed}/{metric_total} ({metric_pass_rate:.1%})")
        report.append(f"- **Average Score:** {avg_score:.3f}")
        report.append("")

    # Add detailed test case results
    report.append("## Detailed Results")
    report.append("")
    report.append(format_test_results(results))

    return "\n".join(report)


def format_test_results(results: dict) -> str:
    """Format test results for markdown."""
    output = []
    metrics = results.get("metrics", {})

    if not metrics:
        return "No test results available"

    # Group test results by test_id
    test_status = {}  # test_id -> {metric_name: (passed, reason)}

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

        output.append(f"### {status} {test_id}")
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
        output.append("")

    return "\n".join(output)


def main():
    """Run content agent evaluation with 3B and 7B models."""
    logger.info("Initializing BaselineEvaluator...")

    # Use content_agent_test_cases.json instead of test_cases.json
    test_cases_path = PROJECT_ROOT / "data" / "evaluation" / "content_agent_test_cases.json"
    evaluator = BaselineEvaluator(test_cases_path=test_cases_path)

    # Full evaluation (all test cases in exercise_gen)
    sample_size = None  # None = all test cases

    # ========================================================================
    # 3B Evaluation
    # ========================================================================
    logger.info("\n" + "=" * 80)
    logger.info("AGENT 3 (CONTENT GENERATION) - 3B EVALUATION")
    logger.info("=" * 80 + "\n")

    logger.info("Running exercise_generation with 3B model...")
    responses_3b, results_3b = evaluator.run_exercise_generation_baseline(
        sample_size=sample_size, use_7b=False
    )
    logger.info("✓ Exercise generation (3B) complete")

    # Save 3B results
    save_results(OUTPUT_DIR, results_3b, "3B", responses_3b)

    # ========================================================================
    # 7B Evaluation
    # ========================================================================
    logger.info("\n" + "=" * 80)
    logger.info("AGENT 3 (CONTENT GENERATION) - 7B EVALUATION")
    logger.info("=" * 80 + "\n")

    logger.info("Running exercise_generation with 7B model...")
    responses_7b, results_7b = evaluator.run_exercise_generation_baseline(
        sample_size=sample_size, use_7b=True
    )
    logger.info("✓ Exercise generation (7B) complete")

    # Save 7B results
    save_results(OUTPUT_DIR, results_7b, "7B", responses_7b)

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

    logger.info("Exercise Generation:")
    logger.info(f"  3B: {format_summary(results_3b)}")
    logger.info(f"  7B: {format_summary(results_7b)}")

    # Metric-level comparison
    logger.info("\nMetric-Level Comparison:")
    for metric_name in results_3b.get("metrics", {}).keys():
        metric_3b = results_3b["metrics"][metric_name]
        metric_7b = results_7b["metrics"][metric_name]

        passed_3b = sum(1 for r in metric_3b if r.get("passed", False))
        total_3b = len(metric_3b)
        rate_3b = passed_3b / total_3b if total_3b > 0 else 0

        passed_7b = sum(1 for r in metric_7b if r.get("passed", False))
        total_7b = len(metric_7b)
        rate_7b = passed_7b / total_7b if total_7b > 0 else 0

        logger.info(f"  {metric_name}:")
        logger.info(f"    3B: {passed_3b}/{total_3b} ({rate_3b:.1%})")
        logger.info(f"    7B: {passed_7b}/{total_7b} ({rate_7b:.1%})")

    logger.info("\n✓ Evaluation complete!")


if __name__ == "__main__":
    main()
