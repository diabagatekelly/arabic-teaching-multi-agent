---
name: tests-audit
description: Audit test quality to ensure tests are necessary, not false positives, and provide real coverage without bloat
---

# Tests Audit Skill

Audit test quality to ensure tests are necessary, not false positives, and provide real coverage without bloat.

## Usage

```
/tests-audit <test_file_path>
```

Or audit all test files:
```
/tests-audit
```

## Audit Criteria

### 1. False Positive Detection
- **Test actually fails when it should**
- Run red/green verification: temporarily break the code, test should fail
- Check assertions are meaningful (not just `assert True`)
- Verify test exercises the actual code path

### 2. Redundant Test Detection
- **Implicit coverage** (testing return value already checks shape)
- **Duplicate assertions** (multiple tests checking the same thing)
- **Overly specific tests** (testing implementation details)
- **Unnecessary edge cases** (testing framework behavior, not your code)

### 3. Minimal Sufficient Coverage
- Each test should validate ONE behavior
- Avoid testing multiple concerns in one test
- Don't test what's already tested by dependency tests
- Don't test language/framework features

### 4. Test Clarity vs. Bloat
- Test name clearly states what's being tested
- Arrange/Act/Assert pattern is clear
- No redundant setup code
- No testing trivial getters/setters

## Instructions

When auditing tests:

1. **Identify False Positives**
   - Find assertions that would pass even if code is broken
   - Check for tests that don't actually exercise the code path
   - Look for missing assertions (test runs but doesn't verify)

2. **Find Redundant Tests**
   - Group tests by what they actually verify
   - Identify implicit coverage (e.g., testing `score == 1.0` already verifies it's a float)
   - Flag tests that duplicate coverage

3. **Check Minimal Coverage**
   - Every test should fail for exactly one reason
   - Tests should not overlap in what they verify
   - Tests should verify behavior, not implementation

4. **Perform Red/Green Audit** (Optional but Recommended)
   - Temporarily introduce a bug in the code
   - Verify the test fails with the expected error
   - Restore code, test should pass
   - Document which tests caught which bugs

5. **Assess Test Value**
   - Does this test prevent a real bug?
   - Would removing this test reduce confidence?
   - Is this testing our code or the framework?

## Output Format

Provide feedback in this structure:

```markdown
## Test Audit: <test_file_name>

### 📊 Coverage Analysis
- Total tests: X
- Useful tests: Y
- Redundant tests: Z
- False positive risks: W

### ✅ Good Tests (Keep)
- `test_name()` - Tests [specific behavior], good assertions
- `test_name()` - Catches [specific bug], minimal and clear

### ⚠️ Redundant Tests (Consolidate or Remove)

#### Test: `test_valid_json`
**Issue:** Implicitly covered by other tests
**Evidence:**
```python
# This test:
assert score == 1.0
assert metric.is_successful()

# Already checks JSON validity implicitly
# Every other test that checks score == 1.0 proves JSON is valid
```
**Recommendation:** Keep only if it's the canonical "happy path" test. Remove duplicate checks from other tests.

#### Tests: `test_dict_structure` + `test_has_correct_field` + `test_correct_is_bool`
**Issue:** Testing same thing in 3 tests
**Evidence:** All three fail if structure is wrong
**Recommendation:** Consolidate into one test:
```python
def test_valid_structure_with_required_types():
    """Test dict with 'correct' bool field."""
    # This one test covers all three concerns
```

### ❌ False Positive Risks

#### Test: `test_accuracy_metric`
**Issue:** Assertion would pass even if logic is broken
**Current:**
```python
def test_accuracy_metric():
    metric = AccuracyMetric()
    score = metric.measure(test_case)
    assert score >= 0  # ⚠️ Too weak - would pass even if broken
```
**Red/Green Check:** 
- Broke `measure()` to return `0.5` always
- Test still passed ❌
**Fix:**
```python
def test_accuracy_metric():
    metric = AccuracyMetric()
    score = metric.measure(test_case)
    assert score == 1.0  # Specific expectation
    assert metric.is_successful()  # Verify state
```

### 🔧 Consolidation Opportunities

#### Opportunity 1: Merge structure validation tests
**Current:** 7 separate tests for structure validation
**Proposed:** 3 tests covering:
1. Valid structure (all fields present, correct types)
2. Invalid structure (missing fields, wrong types) - parameterized
3. Edge cases (empty list, None values)

**Before (70 lines):**
```python
def test_has_correct_field(): ...
def test_correct_is_bool(): ...
def test_correct_not_string(): ...
def test_correct_not_int(): ...
def test_has_feedback_field(): ...
def test_feedback_is_string(): ...
def test_feedback_not_none(): ...
```

**After (25 lines):**
```python
def test_valid_structure():
    """Test complete valid structure with all fields and types."""
    result = {"correct": True, "feedback": "Good"}
    assert validate_structure(result)

@pytest.mark.parametrize("invalid_data,expected_error", [
    ({"correct": "true"}, "correct must be bool"),
    ({"feedback": "Good"}, "missing required field: correct"),
    ({"correct": True, "feedback": None}, "feedback cannot be None"),
])
def test_invalid_structure(invalid_data, expected_error):
    """Test various structure violations."""
    with pytest.raises(ValueError, match=expected_error):
        validate_structure(invalid_data)
```

### 🧪 Red/Green Audit Results

#### Mutation 1: Break AccuracyMetric.measure()
```python
# Changed: actual_correct = actual["correct"]
# To:      actual_correct = True  # Always return correct
```
**Tests that caught it:** ✅ `test_wrong_classification_incorrect_as_correct`
**Tests that missed it:** ❌ `test_correct_classification_as_correct` (false positive)

#### Mutation 2: Break StructureMetric required_keys check
```python
# Changed: if "correct" not in data:
# To:      if False:  # Never check
```
**Tests that caught it:** ✅ `test_missing_required_key`
**Tests that missed it:** ❌ None (good coverage)

### 📋 Recommendations

#### High Priority
1. **Remove:** `test_json_validity_for_each_case` - Redundant, covered by structure tests
2. **Fix:** `test_accuracy_passes` - False positive, assertion too weak
3. **Consolidate:** 7 structure tests → 3 parameterized tests

#### Medium Priority
4. **Strengthen:** Add specific assertions instead of `>= 0` checks
5. **Clarify:** Rename `test_metric_works` to describe specific behavior

#### Low Priority
6. **Consider:** Add negative test for unexpected JSON keys (defensive)

### 📊 Summary
- **Keep:** 15 tests (85%)
- **Remove:** 2 tests (redundant)
- **Consolidate:** 7 tests → 3 tests (reduce bloat)
- **Fix:** 1 test (false positive)
- **Net result:** 18 → 14 tests (-22%), better coverage

**Confidence before:** 75% (some false positives)
**Confidence after:** 95% (every test proves something unique)
```

## Red/Green Testing Procedure

To verify tests actually fail when they should:

```bash
# 1. Run original tests (should pass)
pytest tests/test_metrics.py -v

# 2. Introduce mutation in code
# Edit src/metrics.py - break one thing

# 3. Run tests again (should fail)
pytest tests/test_metrics.py -v

# 4. Document which tests failed
# Those are the tests that caught the bug

# 5. Restore code

# 6. Repeat for each critical code path
```

## Common Test Smells

### 🚩 Smell 1: Testing Implementation, Not Behavior
```python
# Bad: Testing internal state
def test_json_metric_sets_parsed_json():
    metric.measure(test_case)
    assert metric.parsed_json is not None  # Implementation detail

# Good: Testing behavior
def test_json_metric_validates_json():
    score = metric.measure(test_case)
    assert score == 1.0  # Behavior: valid JSON scores 1.0
```

### 🚩 Smell 2: Redundant Assertions
```python
# Bad: Second assertion is redundant
def test_valid_structure():
    result = {"correct": True}
    assert isinstance(result, dict)  # Redundant
    assert "correct" in result  # This is sufficient

# Good: Single sufficient assertion
def test_valid_structure():
    result = {"correct": True}
    assert result["correct"] is True  # Implicitly checks: is dict, has key, is bool
```

### 🚩 Smell 3: Testing the Framework
```python
# Bad: Testing pytest/Python behavior
def test_json_loads_returns_dict():
    result = json.loads('{"key": "value"}')
    assert isinstance(result, dict)  # Testing stdlib, not our code

# Good: Testing our code
def test_metric_handles_json_input():
    score = metric.measure('{"correct": true}')
    assert score == 1.0  # Testing our metric logic
```

### 🚩 Smell 4: False Precision
```python
# Bad: Over-specifying makes test brittle
def test_error_message():
    with pytest.raises(ValueError) as exc:
        validate({})
    assert str(exc.value) == "Missing required field: 'correct' in dict at line 42"
    # ^ Breaks if we change error format or line numbers

# Good: Check essential parts
def test_error_message():
    with pytest.raises(ValueError, match="Missing required field: 'correct'"):
        validate({})
    # ^ Tests the essential error info
```

### 🚩 Smell 5: Implicit Dependencies
```python
# Bad: Test passes only because previous test set state
def test_metric_state():
    assert metric.score == 1.0  # Depends on previous test running first

# Good: Test is independent
def test_metric_state():
    metric = AccuracyMetric()
    metric.measure(valid_test_case)
    assert metric.score == 1.0
```

## Examples

### Example 1: Implicit Coverage

**Before (Redundant):**
```python
def test_valid_json():
    """Test that valid JSON passes."""
    metric = JSONValidityMetric()
    score = metric.measure(test_case)
    assert score == 1.0

def test_parsed_json_is_dict():
    """Test that parsed JSON is a dict."""
    metric = JSONValidityMetric()
    metric.measure('{"correct": true}')
    assert isinstance(metric.parsed_json, dict)  # Redundant

def test_parsed_json_has_correct():
    """Test that parsed JSON has correct field."""
    metric = JSONValidityMetric()
    metric.measure('{"correct": true}')
    assert "correct" in metric.parsed_json  # Redundant
```

**After (Minimal):**
```python
def test_valid_json():
    """Test that valid JSON passes validation."""
    metric = JSONValidityMetric()
    score = metric.measure('{"correct": true}')
    assert score == 1.0
    # ✓ This single assertion proves:
    #   - JSON is valid (or it would be 0.0)
    #   - Parsing worked (or it would error)
    #   - Structure was checked (part of measure logic)
```

### Example 2: False Positive

**Before (False Positive):**
```python
def test_accuracy_correct_classification():
    """Test correct classification."""
    metric = AccuracyMetric()
    test_case = LLMTestCase(
        input="test",
        actual_output='{"correct": true}',
        expected_output="true"
    )
    test_case.expected_output = True
    
    score = metric.measure(test_case)
    assert score > 0  # ⚠️ Would pass even if logic returns 0.5
```

**Red/Green Check:**
```python
# Break the code:
# In AccuracyMetric.measure():
#   return 0.5  # Always return 0.5

# Run test:
pytest tests/test_metrics.py::test_accuracy_correct_classification
# Result: PASSED ❌ (should have failed!)
```

**After (Fixed):**
```python
def test_accuracy_correct_classification():
    """Test that correct answer is classified as correct."""
    metric = AccuracyMetric()
    test_case = LLMTestCase(
        input="test",
        actual_output='{"correct": true}',
        expected_output="true"
    )
    test_case.expected_output = True
    
    score = metric.measure(test_case)
    assert score == 1.0  # Specific expectation
    assert metric.is_successful()  # State verification
    assert "Correctly classified as correct" in metric.reason
```

**Red/Green Verification:**
```python
# Break the code same way
# Run test:
pytest tests/test_metrics.py::test_accuracy_correct_classification
# Result: FAILED ✅ (as expected!)
# Error: assert 0.5 == 1.0
```

## Integration with Coverage Tools

This skill complements coverage metrics:

```bash
# Run coverage
pytest --cov=src --cov-report=html tests/

# View coverage report
open htmlcov/index.html

# Then run test audit
# /tests-audit tests/test_metrics.py

# Coverage might be 100%, but:
# - Are tests useful?
# - Are tests redundant?
# - Are tests false positives?
```

**Coverage metrics tell you WHAT is tested**
**This skill tells you HOW WELL it's tested**

## Quick Checklist

For each test, ask:

- [ ] Does this test fail if I break the specific code it claims to test?
- [ ] Is this testing my code or the framework/language?
- [ ] Would removing this test reduce my confidence?
- [ ] Is this implicitly covered by another test?
- [ ] Does this test verify behavior (not implementation details)?
- [ ] Is the assertion specific enough to catch bugs?
- [ ] Can this be consolidated with similar tests?

**If any answer is "no" or "unsure", investigate further.**

## Notes

- **Prefer fewer, better tests over many weak tests**
- **100% coverage with false positives = 0% confidence**
- **Red/green testing is the ultimate validation**
- **When in doubt, break the code and see if tests catch it**
- **Good tests are insurance policies - each one should protect against a specific bug**
