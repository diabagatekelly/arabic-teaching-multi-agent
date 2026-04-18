"""Show evaluation results in clean format."""

import json
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
EVAL_DIR = PROJECT_ROOT / "data" / "evaluation" / "grading_isagent" / "finetuned"

# Load results
with open(EVAL_DIR / "results.json") as f:
    results = json.load(f)

# Load test cases
with open(
    PROJECT_ROOT / "data" / "evaluation" / "grading_agent" / "grading_agent_test_cases.json"
) as f:
    test_cases = json.load(f)

# Load responses
with open(EVAL_DIR / "vocab_responses.json") as f:
    vocab_responses = json.load(f)

with open(EVAL_DIR / "grammar_responses.json") as f:
    grammar_responses = json.load(f)

print("=" * 80)
print("AGENT 2 (GRADING) - FULL EVALUATION RESULTS")
print("=" * 80)
print(f"\nModel: {results['metadata']['model']}")
print(f"Date: {results['metadata']['evaluation_date'][:10]}")
print()

# Overall summary
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

# Metrics
print("METRICS:")
for mode_name, mode_results in [("Vocabulary", vocab_results), ("Grammar", grammar_results)]:
    print(f"\n  {mode_name}:")
    for metric_name, metric_results in mode_results.get("metrics", {}).items():
        if not metric_results:
            continue
        passed = sum(1 for r in metric_results if r.get("passed", False))
        total = len(metric_results)
        rate = passed / total if total > 0 else 0
        print(f"    - {metric_name.replace('_', ' ').title()}: {passed}/{total} ({rate:.1%})")

# Failing tests with details
print("\n" + "=" * 80)
print("FAILING TESTS (DETAILED)")
print("=" * 80)


def find_test_case(test_id, mode):
    """Find test case by ID."""
    test_data = test_cases[f"grading_{mode}"]
    for category, cases in test_data.items():
        if isinstance(cases, list):
            for case in cases:
                if case["test_id"] == test_id:
                    return case
    return None


# Get all failing test IDs
failing_tests = []

for metric_name, metric_results in vocab_results.get("metrics", {}).items():
    for result in metric_results:
        if not result.get("passed", False):
            test_id = result.get("test_id")
            if test_id and test_id not in [t[0] for t in failing_tests]:
                failing_tests.append((test_id, "vocab"))

for metric_name, metric_results in grammar_results.get("metrics", {}).items():
    for result in metric_results:
        if not result.get("passed", False):
            test_id = result.get("test_id")
            if test_id and test_id not in [t[0] for t in failing_tests]:
                failing_tests.append((test_id, "grammar"))

# Show failing tests
vocab_fails = [t for t in failing_tests if t[1] == "vocab"]
grammar_fails = [t for t in failing_tests if t[1] == "grammar"]

print(f"\nVOCABULARY FAILURES ({len(vocab_fails)}):")
print("-" * 80)
for test_id, _ in vocab_fails:
    test_case = find_test_case(test_id, "vocab")
    if test_case:
        print(f"\n❌ {test_id}")
        print(f"   Word: {test_case['input'].get('word', 'N/A')}")
        print(f"   Student: \"{test_case['input']['student_answer']}\"")
        print(f"   Correct: \"{test_case['input']['correct_answer']}\"")
        print(f"   Expected: {test_case['expected_output']}")
        print(f"   Model:    {vocab_responses.get(test_id, 'N/A')}")

print(f"\n\nGRAMMAR FAILURES ({len(grammar_fails)}):")
print("-" * 80)
for test_id, _ in grammar_fails:
    test_case = find_test_case(test_id, "grammar")
    if test_case:
        print(f"\n❌ {test_id}")
        print(f"   Question: {test_case['input']['question']}")
        print(f"   Student:  \"{test_case['input']['student_answer']}\"")
        print(f"   Correct:  \"{test_case['input']['correct_answer']}\"")
        print(f"   Expected: {test_case['expected_output']}")
        print(f"   Model:    {grammar_responses.get(test_id, 'N/A')}")

print("\n" + "=" * 80)
print("END OF REPORT")
print("=" * 80)
