#!/usr/bin/env python3
"""Run evaluation for Agent 3 (Content Generation) WITH RAG - proper implementation."""

import logging
import sys
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.evaluation.baseline import BaselineEvaluator  # noqa: E402
from src.evaluation.deepeval_pipeline import EvaluationPipeline  # noqa: E402

# Output paths
REPORT_OUTPUT_PATH_3B = (
    PROJECT_ROOT / "data" / "evaluation" / "content_agent" / "evaluation_report.md"
)
OUTPUTS_OUTPUT_PATH_3B = (
    PROJECT_ROOT / "data" / "evaluation" / "content_agent" / "evaluation_outputs.json"
)

REPORT_OUTPUT_PATH_7B = (
    PROJECT_ROOT / "data" / "evaluation" / "content_agent" / "evaluation_report_7b.md"
)
OUTPUTS_OUTPUT_PATH_7B = (
    PROJECT_ROOT / "data" / "evaluation" / "content_agent" / "evaluation_outputs_7b.json"
)


def save_report(
    evaluator: BaselineEvaluator, results: dict, model_outputs: dict, use_7b: bool
) -> None:
    """Save evaluation report and outputs."""
    import json

    model_size = "7B" if use_7b else "3B"
    report_path = REPORT_OUTPUT_PATH_7B if use_7b else REPORT_OUTPUT_PATH_3B
    outputs_path = OUTPUTS_OUTPUT_PATH_7B if use_7b else OUTPUTS_OUTPUT_PATH_3B

    logger = logging.getLogger(__name__)

    # Calculate statistics
    passed_pct = EvaluationPipeline._safe_percentage(results["passed"], results["total"])

    # Build report
    report_lines = [
        f"# Agent 3 (Content) Evaluation Report ({model_size})",
        "",
        f"**Model:** Qwen2.5-{model_size}-Instruct (base, no fine-tuning)",
        "**Agent:** ContentAgent with RAG templates",
        "**Date:** 2026-04-14",
        "**Sample Size:** 5 per mode",
        "",
        "## Purpose",
        "",
        "Evaluate Agent 3 (ContentAgent) with proper RAG implementation.",
        "**Difference from baseline:** Uses RAG templates and lesson content instead of raw prompts.",
        "",
        "---",
        "",
    ]

    # Generate mode report
    if evaluator.content_pipeline is not None:
        mode_report = evaluator.content_pipeline.generate_report(results, "content_agent")
        report_lines.append(mode_report)

    # Save markdown report
    report_path.parent.mkdir(parents=True, exist_ok=True)
    with open(report_path, "w") as f:
        f.write("\n".join(report_lines))

    logger.info(f"\n✓ Evaluation report ({model_size}) saved to: {report_path}")

    # Save detailed outputs
    detailed_outputs = {}

    # Get all test cases
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

    # Build output dict
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

    with open(outputs_path, "w", encoding="utf-8") as f:
        json.dump(detailed_outputs, f, indent=2, ensure_ascii=False)

    logger.info(f"✓ Detailed outputs ({model_size}) saved to: {outputs_path}")

    logger.info(f"\n{'=' * 60}")
    logger.info(
        f"Content Agent Results ({model_size}): {results['passed']}/{results['total']} passed ({passed_pct:.1f}%)"
    )
    logger.info(f"{'=' * 60}")


def main() -> None:
    """Run Agent 3 (Content) evaluation with RAG for both 3B and 7B."""
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    logger = logging.getLogger(__name__)
    logger.info("=== Agent 3 (Content) Evaluation with RAG ===")
    logger.info("Testing ContentAgent with RAG templates on content generation tasks\n")

    # Initialize evaluator
    evaluator = BaselineEvaluator()

    # Run 3B evaluation
    logger.info("=" * 60)
    logger.info("EVALUATING 3B MODEL")
    logger.info("=" * 60)
    model_outputs_3b, results_3b = evaluator.run_content_agent_evaluation(
        sample_size=5, use_7b=False
    )
    save_report(evaluator, results_3b, model_outputs_3b, use_7b=False)

    # Run 7B evaluation
    logger.info("\n" + "=" * 60)
    logger.info("EVALUATING 7B MODEL")
    logger.info("=" * 60)
    model_outputs_7b, results_7b = evaluator.run_content_agent_evaluation(
        sample_size=5, use_7b=True
    )
    save_report(evaluator, results_7b, model_outputs_7b, use_7b=True)

    # Compare results
    logger.info("\n" + "=" * 60)
    logger.info("COMPARISON SUMMARY")
    logger.info("=" * 60)

    pct_3b = EvaluationPipeline._safe_percentage(results_3b["passed"], results_3b["total"])
    pct_7b = EvaluationPipeline._safe_percentage(results_7b["passed"], results_7b["total"])

    logger.info(f"3B Model: {results_3b['passed']}/{results_3b['total']} passed ({pct_3b:.1f}%)")
    logger.info(f"7B Model: {results_7b['passed']}/{results_7b['total']} passed ({pct_7b:.1f}%)")

    if pct_7b > pct_3b:
        logger.info(f"✓ 7B outperformed 3B by {pct_7b - pct_3b:.1f} percentage points")
    elif pct_3b > pct_7b:
        logger.info(f"✓ 3B outperformed 7B by {pct_3b - pct_7b:.1f} percentage points")
    else:
        logger.info("= Both models tied")

    logger.info("\n=== Agent 3 Evaluation Complete ===")


if __name__ == "__main__":
    main()
