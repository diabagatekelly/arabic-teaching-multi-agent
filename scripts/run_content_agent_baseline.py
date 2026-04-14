#!/usr/bin/env python3
"""Run baseline evaluation for Agent 3 (Content Generation) only."""

import logging
import sys
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.evaluation.baseline import BaselineEvaluator  # noqa: E402
from src.evaluation.deepeval_pipeline import EvaluationPipeline  # noqa: E402

# Output paths
REPORT_OUTPUT_PATH = PROJECT_ROOT / "data" / "evaluation" / "content_agent" / "baseline_report.md"
OUTPUTS_OUTPUT_PATH = (
    PROJECT_ROOT / "data" / "evaluation" / "content_agent" / "baseline_outputs.json"
)


def main() -> None:
    """Run Agent 3 (Content) baseline evaluation only."""
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    logger = logging.getLogger(__name__)
    logger.info("=== Agent 3 (Content) Baseline Evaluation ===")
    logger.info("Testing base Qwen2.5-3B (no fine-tuning) on content generation tasks")
    logger.info("Evaluating 4 modes: exercise_gen, quiz_gen, test_comp, content_retrieval\n")

    # Initialize evaluator
    evaluator = BaselineEvaluator()

    # Run content agent baseline
    logger.info("Running content_agent baseline...")
    model_outputs, results = evaluator.run_content_agent_baseline(sample_size=5)

    # Calculate statistics
    passed_pct = EvaluationPipeline._safe_percentage(results["passed"], results["total"])
    logger.info(f"\n{'=' * 60}")
    logger.info(
        f"Content Agent Results: {results['passed']}/{results['total']} passed ({passed_pct:.1f}%)"
    )
    logger.info(f"{'=' * 60}")

    # Save report
    REPORT_OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)

    report_lines = [
        "# Agent 3 (Content) Baseline Evaluation Report",
        "",
        "**Model:** Qwen2.5-3B-Instruct (base, no fine-tuning)",
        "**Date:** 2026-04-14",
        "**Sample Size:** 5 per mode",
        "",
        "## Purpose",
        "",
        "Establish baseline performance for content generation before Agent 3 implementation.",
        "**Goal:** Agent 3 (when implemented) should significantly outperform these scores.",
        "",
        "---",
        "",
    ]

    # Generate mode report
    if evaluator.content_pipeline is not None:
        mode_report = evaluator.content_pipeline.generate_report(results, "content_agent")
        report_lines.append(mode_report)

    # Save markdown report
    with open(REPORT_OUTPUT_PATH, "w") as f:
        f.write("\n".join(report_lines))

    logger.info(f"\n✓ Baseline report saved to: {REPORT_OUTPUT_PATH}")

    # Save detailed outputs
    import json

    detailed_outputs = {}

    # Get all test cases for content_agent
    all_test_cases = []
    if "exercise_generation" in evaluator.content_pipeline.test_cases:
        exercise_gen = evaluator.content_pipeline.test_cases["exercise_generation"]
        all_test_cases.extend(exercise_gen.get("comprehensive_types", []))
        all_test_cases.extend(exercise_gen.get("smoke_tests", []))

    for mode_name in ["quiz_generation", "test_composition", "content_retrieval"]:
        if mode_name in evaluator.content_pipeline.test_cases:
            all_test_cases.extend(
                evaluator.content_pipeline.test_cases[mode_name].get("test_cases", [])
            )

    # Build dict mapping test_id -> test_case
    test_cases_by_id = {tc["test_id"]: tc for tc in all_test_cases}

    # Build output dict with test case details
    for test_id, response in model_outputs.items():
        test_case = test_cases_by_id.get(test_id)

        # Find scores from results
        scores = {}
        passed = False
        if "metrics" in results:
            for metric_name, metric_results_list in results["metrics"].items():
                for result in metric_results_list:
                    if result.get("test_id") == test_id:
                        scores[metric_name] = {
                            "score": result.get("score", 0.0),
                            "passed": result.get("passed", False),
                            "reason": result.get("reason", ""),
                        }
                        passed = passed or result.get("passed", False)

        detailed_outputs[test_id] = {
            "input": test_case["input"] if test_case else {},
            "expected_output": test_case.get("expected_output") if test_case else None,
            "model_output": response,
            "passed": passed,
            "scores": scores,
        }

    with open(OUTPUTS_OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(detailed_outputs, f, indent=2, ensure_ascii=False)

    logger.info(f"✓ Detailed outputs saved to: {OUTPUTS_OUTPUT_PATH}")

    logger.info("\n=== Agent 3 Baseline Evaluation Complete ===")


if __name__ == "__main__":
    main()
