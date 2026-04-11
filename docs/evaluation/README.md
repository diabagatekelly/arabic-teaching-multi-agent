# Evaluation Module

**Purpose:** Automated evaluation pipeline for testing agent outputs against defined success criteria.

## Overview

This module implements **Eval-Driven Development** (TDD for AI) using DeepEval framework with custom metrics for the Arabic Teaching Multi-Agent System v2.

## Custom Metrics

### 1. SentimentMetric
**For:** Teaching and Feedback modes (lesson_start, teaching_vocab, teaching_grammar, feedback_vocab, feedback_grammar)

**Purpose:** Measures sentiment/tone of teaching content and feedback

**Thresholds:**
- Teaching mode: >0.9 (highly positive)
- Feedback mode: >0.8 (encouraging)

**Implementation:** Uses `transformers` sentiment analysis pipeline (DistilBERT)

### 2. JSONValidityMetric
**For:** Grading modes (grading_vocab, grading_grammar)

**Purpose:** Validates that grading outputs are valid JSON (handles markdown code blocks)

**Target:** 100% valid JSON

### 3. StructureMetric
**For:** Grading and Exercise Generation modes

**Purpose:** Validates JSON structure - correct type, required keys, expected value types

**Target:** 100% valid structure

**Configurable for different output schemas:**
- Grading: expects `dict` with `"correct"` key (bool)
- Exercise Generation: expects `list` with `"question"` and `"answer"` keys (str)

### 4. AccuracyMetric
**For:** Grading modes (grading_vocab, grading_grammar)

**Purpose:** Checks correct/incorrect classification accuracy

**Target:** >90% aggregate accuracy across test cases

### 5. AlignmentMetric
**For:** Exercise Generation mode

**Purpose:** Evaluates semantic alignment using LLM-as-judge (Qwen2.5-7B)

**Criteria:**
- Matches requested exercise type
- Uses learned vocabulary appropriately
- Tests specified grammar rule
- Has variety in question formats

**Target:** >0.8 alignment score

## Files

- `__init__.py` - Module exports
- `metrics.py` - Custom DeepEval metrics (5 metrics + shared `extract_json` helper)
- `deepeval_pipeline.py` - Main evaluation runner (8 mode-specific evaluators)
- `baseline.py` - Baseline evaluation using base Qwen2.5-3B/7B (dual-model strategy)

**Documentation:**
- `.notes/deepeval-baseline-evaluator.md` - Detailed baseline implementation
- `.notes/deepeval-pipeline-refactored.md` - Pipeline architecture and flow
- `.notes/deepeval-custom-metrics-alignment.md` - AlignmentMetric deep dive

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

The pipeline provides 8 mode-specific evaluation methods:

```python
from src.evaluation.deepeval_pipeline import EvaluationPipeline

# Initialize pipeline
pipeline = EvaluationPipeline("data/evaluation/test_cases.json")

# Example 1: Evaluate teaching vocabulary mode
model_responses = {
    "teach_vocab_01": "Let's learn Batch 1! Here are your first 3 words...",
    "teach_vocab_02": "Great! Now let's learn Batch 2...",
    # ... more responses
}

results = pipeline.evaluate_teaching_vocab(model_responses)
print(f"Average sentiment: {results['avg_sentiment']:.3f}")

# Example 2: Evaluate grading mode
grading_responses = {
    "grade_vocab_01": '{"correct": true}',
    "grade_vocab_02": '{"correct": false}',
    # ... more responses
}

results = pipeline.evaluate_grading_vocab(grading_responses)
print(f"Accuracy: {results['accuracy']:.1%}")
print(f"JSON validity: {results['json_validity']:.1%}")

# Example 3: Evaluate exercise generation
exercise_responses = {
    "exercise_gen_01": '[{"question": "...", "answer": "..."}]',
    # ... more responses
}

results = pipeline.evaluate_exercise_generation(exercise_responses)
print(f"Alignment score: {results['avg_alignment']:.3f}")
```

**Available evaluation methods:**
- `evaluate_lesson_start(responses)` - SentimentMetric (0.9 threshold)
- `evaluate_teaching_vocab(responses)` - SentimentMetric (0.9 threshold)
- `evaluate_teaching_grammar(responses)` - SentimentMetric (0.9 threshold)
- `evaluate_feedback_vocab(responses)` - SentimentMetric (0.8 threshold)
- `evaluate_feedback_grammar(responses)` - SentimentMetric (0.8 threshold)
- `evaluate_grading_vocab(responses)` - JSONValidityMetric, StructureMetric, AccuracyMetric
- `evaluate_grading_grammar(responses)` - JSONValidityMetric, StructureMetric, AccuracyMetric
- `evaluate_exercise_generation(responses)` - JSONValidityMetric, StructureMetric, AlignmentMetric

### Evaluating Fine-Tuned Model

After fine-tuning (Phase 2), the workflow is similar to baseline but with your fine-tuned model:

```python
from src.evaluation.deepeval_pipeline import EvaluationPipeline
from transformers import AutoModelForCausalLM, AutoTokenizer

# Load fine-tuned model(s)
# Note: System uses dual-model strategy
#   - Qwen2.5-3B: teaching, feedback, exercise generation
#   - Qwen2.5-7B: grading (requires better reasoning)
model_3b = AutoModelForCausalLM.from_pretrained("models/qwen-3b-arabic-teaching")
tokenizer = AutoTokenizer.from_pretrained("Qwen/Qwen2.5-3B-Instruct")

# Generate responses for each mode
# ... (see baseline.py for full implementation)

# Run mode-specific evaluations
pipeline = EvaluationPipeline("data/evaluation/test_cases.json")

teaching_results = pipeline.evaluate_teaching_vocab(teaching_responses)
grading_results = pipeline.evaluate_grading_vocab(grading_responses)

# Compare with baseline scores from baseline_report.md
# Fine-tuned model should significantly outperform baseline
```

## Test Cases

**Total:** 94 test cases in `data/evaluation/test_cases.json`

**Breakdown by Mode:**
1. **lesson_start**: 5 cases - Initial lesson introduction
2. **teaching_vocab**: 16 cases - Vocabulary batch teaching
3. **teaching_grammar**: 15 cases - Grammar rule explanations
4. **feedback_vocab**: 20 cases (10 correct, 10 incorrect) - Vocabulary quiz feedback
5. **feedback_grammar**: 20 cases (10 correct, 10 incorrect) - Grammar quiz feedback
6. **grading_vocab**: 8 cases - Vocabulary answer grading
7. **grading_grammar**: 5 cases - Grammar answer grading
8. **exercise_generation**: 5 cases - Exercise generation requests

## Success Criteria

**Phase 1 Complete When:**
- [x] DeepEval pipeline implemented (8 mode-specific evaluators)
- [x] Custom metrics created (5 metrics: Sentiment, JSONValidity, Structure, Accuracy, Alignment)
- [x] Baseline evaluation fully implemented (dual-model, 8 baseline methods)
- [ ] Baseline evaluation run and documented (generates `data/evaluation/baseline_report.md`)
- [ ] Baseline report shows clear room for improvement via fine-tuning

**Fine-Tuning Success (Phase 2):**
Fine-tuned model should significantly outperform baseline:
- **Teaching/Feedback sentiment:** >0.9/0.8 (vs baseline expected ~0.6-0.7)
- **Grading accuracy:** >90% aggregate (vs baseline expected ~60-70%)
- **Grading JSON validity:** 100% (vs baseline expected ~50-70%)
- **Grading structure:** 100% (vs baseline expected ~50-70%)
- **Exercise alignment:** >0.8 (vs baseline expected ~0.4-0.6)

## Next Steps

1. Run baseline evaluation: `python -m src.evaluation.baseline`
2. Review baseline report
3. Proceed to Phase 2: Create training data and fine-tune
4. Re-run evaluation with fine-tuned model
5. Compare: fine-tuned vs baseline
