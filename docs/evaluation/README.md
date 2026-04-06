# Evaluation Module

**Purpose:** Automated evaluation pipeline for testing agent outputs against defined success criteria.

## Overview

This module implements **Eval-Driven Development** (TDD for AI) using DeepEval framework with custom metrics for the Arabic Teaching Multi-Agent System v2.

## Custom Metrics

### 1. SentimentMetric
**For:** Agent 1 (Teaching/Presentation)

**Purpose:** Measures sentiment/tone of teaching content and feedback

**Thresholds:**
- Teaching mode: >0.9 (highly positive)
- Feedback mode: >0.8 (encouraging)

**Implementation:** Uses `transformers` sentiment analysis pipeline

### 2. JSONValidityMetric
**For:** Agent 2 (Error Detection/Grading)

**Purpose:** Validates that grading outputs are valid JSON

**Target:** 100% valid JSON

### 3. AccuracyMetric
**For:** Agent 2 (Error Detection/Grading)

**Purpose:** Checks correct/incorrect classification accuracy

**Target:** >90% accuracy

### 4. FaithfulnessMetric
**For:** Agent 3 (Content Retrieval + Exercise Generation)

**Purpose:** Ensures generated exercises follow template structure

**Target:** >90% faithfulness to template

## Files

- `__init__.py` - Module exports
- `metrics.py` - Custom DeepEval metrics
- `deepeval_pipeline.py` - Main evaluation runner
- `baseline.py` - Baseline evaluation using base Qwen2.5-3B

## Usage

### Running Baseline Evaluation

Establishes baseline scores for base model (no fine-tuning):

```bash
python -m src.evaluation.baseline
```

This will:
1. Load base Qwen2.5-3B model
2. Run sample test cases (5 per category for speed)
3. Generate `data/evaluation/baseline_report.md`

**Note:** Baseline scores show what base model achieves WITHOUT fine-tuning. Fine-tuned model should significantly outperform these scores.

### Using Evaluation Pipeline

```python
from src.evaluation.deepeval_pipeline import EvaluationPipeline

# Initialize pipeline
pipeline = EvaluationPipeline("data/evaluation/test_cases.json")

# Evaluate teaching mode outputs
model_responses = {
    "teach_vocab_01": "Let's learn Batch 1! Here are your first 3 words...",
    # ... more responses
}

results = pipeline.evaluate_teaching_mode(model_responses)

# Generate report
report = pipeline.generate_report(results, "teaching")
print(report)
```

### Evaluating Fine-Tuned Model

After fine-tuning (Phase 2):

```python
from src.evaluation.deepeval_pipeline import EvaluationPipeline
from transformers import AutoModelForCausalLM, AutoTokenizer

# Load fine-tuned model
model = AutoModelForCausalLM.from_pretrained("models/qwen-3b-arabic-teaching")
tokenizer = AutoTokenizer.from_pretrained("Qwen/Qwen2.5-3B-Instruct")

# Generate responses for test cases
# ... (similar to baseline.py)

# Run evaluation
pipeline = EvaluationPipeline("data/evaluation/test_cases.json")
results = pipeline.evaluate_teaching_mode(responses)

# Compare with baseline
# Fine-tuned should beat baseline scores
```

## Test Cases

**Total:** 75 test cases in `data/evaluation/test_cases.json`

**Breakdown:**
- Teaching Mode: 30 cases
  - 10 vocabulary batch introductions
  - 10 grammar explanations
  - 10 quiz feedback (correct/incorrect)
- Grading Mode: 35 cases
  - 15 vocabulary grading (8 correct, 7 incorrect)
  - 20 grammar grading (10 correct, 10 incorrect)
- Exercise Generation: 10 cases
  - Various types (fill-in-blank, translation, correction, etc.)

## Success Criteria

**Phase 1 Complete When:**
- [x] DeepEval pipeline implemented
- [x] Custom metrics created
- [ ] Baseline evaluation run and documented
- [ ] Baseline report shows clear room for improvement via fine-tuning

**Fine-Tuning Success (Phase 2):**
- Fine-tuned model scores >baseline + 20% on all metrics
- Teaching sentiment: >0.9 (vs baseline ~0.6-0.7)
- Grading accuracy: >90% (vs baseline ~60-70%)
- JSON validity: 100% (vs baseline ~50-70%)

## Next Steps

1. Run baseline evaluation: `python -m src.evaluation.baseline`
2. Review baseline report
3. Proceed to Phase 2: Create training data and fine-tune
4. Re-run evaluation with fine-tuned model
5. Compare: fine-tuned vs baseline
