"""Show evaluation results in clean format."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent.parent


def load_files(eval_dir: Path) -> tuple[dict, dict, dict, dict]:
    """Load all required files with error handling."""
    try:
        with open(eval_dir / "results.json") as f:
            results = json.load(f)
    except FileNotFoundError:
        print(f"Error: results.json not found in {eval_dir}", file=sys.stderr)
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON in results.json: {e}", file=sys.stderr)
        sys.exit(1)

    try:
        test_cases_path = (
            PROJECT_ROOT / "data" / "evaluation" / "grading_agent" / "grading_agent_test_cases.json"
        )
        with open(test_cases_path) as f:
            test_cases = json.load(f)
    except FileNotFoundError:
        print("Error: grading_agent_test_cases.json not found", file=sys.stderr)
        sys.exit(1)

    try:
        with open(eval_dir / "vocab_responses.json") as f:
            vocab_responses = json.load(f)
        with open(eval_dir / "grammar_responses.json") as f:
            grammar_responses = json.load(f)
    except FileNotFoundError as e:
        print(f"Error: Response file not found: {e}", file=sys.stderr)
        sys.exit(1)

    return results, test_cases, vocab_responses, grammar_responses


def find_test_case(test_id: str, mode: str, test_cases: dict) -> dict | None:
    """Find test case by ID."""
    test_data = test_cases[f"grading_{mode}"]
    for category, cases in test_data.items():
        if isinstance(cases, list):
            for case in cases:
                if case["test_id"] == test_id:
                    return case
    return None


def collect_failing_tests(results: dict, mode: str) -> list[tuple[str, str]]:
    """Collect all failing test IDs for a specific mode."""
    failing = []
    seen_ids = set()

    for metric_results in results.get("metrics", {}).values():
        for result in metric_results:
            if not result.get("passed", False):
                test_id = result.get("test_id")
                if test_id and test_id not in seen_ids:
                    failing.append((test_id, mode))
                    seen_ids.add(test_id)

    return failing


def print_failures(
    failures: list[tuple[str, str]],
    mode: str,
    test_cases: dict,
    responses: dict,
) -> None:
    """Print failure details for a specific mode."""
    print(f"\n{mode.upper()} FAILURES ({len(failures)}):")
    print("-" * 80)

    for test_id, _ in failures:
        test_case = find_test_case(test_id, mode, test_cases)
        if not test_case:
            continue

        print(f"\n❌ {test_id}")
        input_data = test_case["input"]

        if mode == "vocab":
            print(f"   Word: {input_data.get('word', 'N/A')}")
            print(f'   Student: "{input_data["student_answer"]}"')
            print(f'   Correct: "{input_data["correct_answer"]}"')
        else:
            print(f"   Question: {input_data['question']}")
            print(f'   Student:  "{input_data["student_answer"]}"')
            print(f'   Correct:  "{input_data["correct_answer"]}"')

        print(f"   Expected: {test_case['expected_output']}")
        print(f"   Model:    {responses.get(test_id, 'N/A')}")


def display_results(
    results: dict,
    test_cases: dict,
    vocab_responses: dict,
    grammar_responses: dict,
) -> None:
    """Display evaluation results in formatted output."""
    print("=" * 80)
    print("AGENT 2 (GRADING) - FULL EVALUATION RESULTS")
    print("=" * 80)
    print(f"\nModel: {results['metadata']['model']}")
    print(f"Date: {results['metadata']['evaluation_date'][:10]}")
    print()

    vocab_results = results["grading_vocab"]
    grammar_results = results["grading_grammar"]

    vocab_total = vocab_results["total"]
    vocab_passed = vocab_results["passed"]
    vocab_rate = vocab_passed / vocab_total if vocab_total > 0 else 0

    grammar_total = grammar_results["total"]
    grammar_passed = grammar_results["passed"]
    grammar_rate = grammar_passed / grammar_total if grammar_total > 0 else 0

    overall_total = vocab_total + grammar_total
    overall_passed = vocab_passed + grammar_passed
    overall_rate = overall_passed / overall_total if overall_total > 0 else 0

    print("=" * 80)
    print("OVERALL SUMMARY")
    print("=" * 80)
    print(f"Total Tests:     {overall_total}")
    print(f"Passed:          {overall_passed}")
    print(f"Failed:          {overall_total - overall_passed}")
    print(f"Pass Rate:       {overall_rate:.1%}")
    print()

    print("BY MODE:")
    print(f"  Vocabulary:    {vocab_passed}/{vocab_total} ({vocab_rate:.1%})")
    print(f"  Grammar:       {grammar_passed}/{grammar_total} ({grammar_rate:.1%})")
    print()

    print("METRICS:")
    for mode_name, mode_results in [
        ("Vocabulary", vocab_results),
        ("Grammar", grammar_results),
    ]:
        print(f"\n  {mode_name}:")
        for metric_name, metric_results in mode_results.get("metrics", {}).items():
            if not metric_results:
                continue
            passed = sum(1 for r in metric_results if r.get("passed", False))
            total = len(metric_results)
            rate = passed / total if total > 0 else 0
            print(
                f"    - {metric_name.replace('_', ' ').title()}: " f"{passed}/{total} ({rate:.1%})"
            )

    print("\n" + "=" * 80)
    print("FAILING TESTS (DETAILED)")
    print("=" * 80)

    vocab_fails = collect_failing_tests(vocab_results, "vocab")
    grammar_fails = collect_failing_tests(grammar_results, "grammar")

    print_failures(vocab_fails, "vocab", test_cases, vocab_responses)
    print_failures(grammar_fails, "grammar", test_cases, grammar_responses)

    print("\n" + "=" * 80)
    print("END OF REPORT")
    print("=" * 80)


def main() -> None:
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Display grading agent evaluation results")
    parser.add_argument(
        "--eval-dir",
        type=str,
        default="data/evaluation/grading_agent/finetuned",
        help="Path to evaluation directory (relative to project root)",
    )
    args = parser.parse_args()

    eval_dir = PROJECT_ROOT / args.eval_dir

    if not eval_dir.exists():
        print(f"Error: Evaluation directory not found: {eval_dir}", file=sys.stderr)
        sys.exit(1)

    results, test_cases, vocab_responses, grammar_responses = load_files(eval_dir)
    display_results(results, test_cases, vocab_responses, grammar_responses)


if __name__ == "__main__":
    main()
