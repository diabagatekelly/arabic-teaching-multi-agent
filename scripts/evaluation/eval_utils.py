"""Shared evaluation utilities to reduce code duplication."""

from __future__ import annotations

import json
import logging
from collections.abc import Callable
from datetime import datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


def calculate_pass_rate(results: dict) -> float:
    """Calculate pass rate from results dictionary."""
    total = results.get("total", 0)
    if total == 0:
        return 0.0
    return results.get("passed", 0) / total


def format_summary(results: dict) -> str:
    """Format results as summary string."""
    total = results.get("total", 0)
    passed = results.get("passed", 0)
    pass_rate = calculate_pass_rate(results)
    return f"{passed}/{total} passed ({pass_rate:.1%})"


def collect_test_cases(
    mode_data: dict, subgroups: list[str] | None = None, sample_size: int | None = None
) -> list[dict]:
    """Collect test cases from mode data, optionally sampling from subgroups."""
    test_cases = []

    if subgroups:
        for subgroup_name in subgroups:
            if subgroup_name in mode_data and isinstance(mode_data[subgroup_name], list):
                subgroup_cases = mode_data[subgroup_name]
                sampled = subgroup_cases[:sample_size] if sample_size else subgroup_cases
                test_cases.extend(sampled)
                logger.info(f"  {subgroup_name}: {len(sampled)} test cases")
    else:
        for subgroup_name, subgroup_cases in mode_data.items():
            if isinstance(subgroup_cases, list):
                sampled = subgroup_cases[:sample_size] if sample_size else subgroup_cases
                test_cases.extend(sampled)
                logger.info(f"  {subgroup_name}: {len(sampled)} test cases")

    return test_cases


def run_evaluation_mode(
    mode_name: str,
    test_cases: list[dict],
    handler_func: Callable[[dict], str],
) -> dict[str, str]:
    """Run evaluation for a specific mode."""
    logger.info("=" * 80)
    logger.info(mode_name.upper())
    logger.info("=" * 80)
    logger.info(f"\nTotal test cases: {len(test_cases)}\n")

    responses = {}
    for i, test_case in enumerate(test_cases, 1):
        test_id = test_case["test_id"]
        logger.info(f"[{i}/{len(test_cases)}] {test_id}")
        responses[test_id] = handler_func(test_case["input"])

    logger.info(f"\n✓ {mode_name} evaluation complete")
    return responses


def save_json_responses(output_dir: Path, responses: dict[str, Any], filename: str) -> None:
    """Save responses to JSON file."""
    output_dir.mkdir(parents=True, exist_ok=True)
    with open(output_dir / filename, "w", encoding="utf-8") as f:
        json.dump(responses, f, indent=2, ensure_ascii=False)


def save_evaluation_results(
    output_dir: Path,
    results_data: dict[str, Any],
    markdown_report: str,
) -> None:
    """Save evaluation results and markdown report."""
    output_dir.mkdir(parents=True, exist_ok=True)

    with open(output_dir / "results.json", "w") as f:
        json.dump(results_data, f, indent=2)

    with open(output_dir / "evaluation_report.md", "w") as f:
        f.write(markdown_report)

    logger.info(f"✓ Results saved to {output_dir}")


def format_mode_section(mode_name: str, results: dict) -> str:
    """Format a single mode section for markdown report."""
    total = results.get("total", 0)
    passed = results.get("passed", 0)
    failed = results.get("failed", 0)
    pass_rate = calculate_pass_rate(results)

    return f"""### {mode_name}
- **Total Test Cases:** {total}
- **Passed:** {passed}
- **Failed:** {failed}
- **Pass Rate:** {pass_rate:.1%}"""


def generate_overall_summary(all_results: list[dict]) -> tuple[int, int, float]:
    """Calculate overall metrics from list of results."""
    overall_total = sum(r.get("total", 0) for r in all_results)
    overall_passed = sum(r.get("passed", 0) for r in all_results)
    overall_pass_rate = overall_passed / overall_total if overall_total > 0 else 0.0
    return overall_total, overall_passed, overall_pass_rate


def create_metadata(model_name: str, agent_name: str) -> dict[str, str]:
    """Create metadata dictionary for results."""
    return {
        "model": model_name,
        "evaluation_date": datetime.now().isoformat(),
        "agent": agent_name,
    }
