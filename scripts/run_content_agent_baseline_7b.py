#!/usr/bin/env python3
"""Run baseline evaluation for Agent 3 (Content Generation) with 7B model."""

import logging
import sys
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.evaluation.baseline import BaselineEvaluator  # noqa: E402
from src.evaluation.deepeval_pipeline import EvaluationPipeline  # noqa: E402

# Output paths (7B variant)
REPORT_OUTPUT_PATH = (
    PROJECT_ROOT / "data" / "evaluation" / "content_agent" / "baseline_report_7b.md"
)
OUTPUTS_OUTPUT_PATH = (
    PROJECT_ROOT / "data" / "evaluation" / "content_agent" / "baseline_outputs_7b.json"
)


def main() -> None:
    """Run Agent 3 (Content) baseline evaluation with 7B model."""
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    logger = logging.getLogger(__name__)
    logger.info("=== Agent 3 (Content) Baseline Evaluation (7B) ===")
    logger.info("Testing base Qwen2.5-7B (no fine-tuning) on content generation tasks")
    logger.info("Evaluating 4 modes: exercise_gen, quiz_gen, test_comp, content_retrieval\n")

    # Initialize evaluator
    evaluator = BaselineEvaluator()

    # Run content agent baseline with 7B model
    logger.info("Running content_agent baseline with 7B model...")

    # Modified version of run_content_agent_baseline that uses 7B
    if evaluator.content_pipeline is None:
        raise RuntimeError(
            "Agent 3 test cases not loaded. Cannot run content_agent baseline. "
            f"Ensure {evaluator.content_agent_test_cases_path} exists."
        )

    model_responses = {}
    sample_size = 5

    # Sample from all 4 modes
    all_test_cases = []

    # Mode 1: Exercise generation (has subgroups)
    if "exercise_generation" in evaluator.content_pipeline.test_cases:
        exercise_gen = evaluator.content_pipeline.test_cases["exercise_generation"]
        all_test_cases.extend(exercise_gen.get("comprehensive_types", [])[:sample_size])
        all_test_cases.extend(exercise_gen.get("smoke_tests", [])[:sample_size])

    # Mode 2-4: Quiz generation, test composition, content retrieval
    for mode_name in ["quiz_generation", "test_composition", "content_retrieval"]:
        if mode_name in evaluator.content_pipeline.test_cases:
            mode_cases = evaluator.content_pipeline.test_cases[mode_name].get("test_cases", [])
            all_test_cases.extend(mode_cases[:sample_size])

    # Generate responses for each test case using 7B model
    for test_case in all_test_cases:
        test_id = test_case["test_id"]
        input_data = test_case["input"]

        logger.info(f"Evaluating {test_id}...")

        # Build simple prompt for content generation
        prompt = evaluator._build_content_generation_prompt(input_data)
        response = evaluator.generate_response(prompt, max_new_tokens=512, use_7b=True)  # 7B!

        model_responses[test_id] = response

    # Run evaluation
    results = evaluator.content_pipeline.evaluate_content_agent(model_responses)

    # Calculate statistics
    passed_pct = EvaluationPipeline._safe_percentage(results["passed"], results["total"])
    logger.info(f"\n{'=' * 60}")
    logger.info(
        f"Content Agent Results (7B): {results['passed']}/{results['total']} passed ({passed_pct:.1f}%)"
    )
    logger.info(f"{'=' * 60}")

    # Save report
    REPORT_OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)

    report_lines = [
        "# Agent 3 (Content) Baseline Evaluation Report (7B)",
        "",
        "**Model:** Qwen2.5-7B-Instruct (base, no fine-tuning)",
        "**Date:** 2026-04-14",
        "**Sample Size:** 5 per mode",
        "",
        "## Purpose",
        "",
        "Compare 7B baseline performance vs 3B for content generation.",
        "**Hypothesis:** 7B should outperform 3B on structured JSON generation and complex reasoning.",
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

    logger.info(f"\n✓ Baseline report (7B) saved to: {REPORT_OUTPUT_PATH}")

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
    for test_id, response in model_responses.items():
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

    logger.info(f"✓ Detailed outputs (7B) saved to: {OUTPUTS_OUTPUT_PATH}")

    logger.info("\n=== Agent 3 Baseline Evaluation (7B) Complete ===")


if __name__ == "__main__":
    main()
