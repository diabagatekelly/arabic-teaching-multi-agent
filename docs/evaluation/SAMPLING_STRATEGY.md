# Sampling Strategy

**Purpose:** Document sampling parameters for model inference across different modes and explain rationale for each configuration.

---

## Overview

Different modes in the Arabic Teaching Multi-Agent System require different sampling strategies. Teaching and generation benefit from creativity, while grading requires determinism for reproducibility.

---

## Sampling Parameters by Mode

### Teaching Modes (Agent 1)

**Modes:** `lesson_start`, `teaching_vocab`, `teaching_grammar`, `feedback_vocab`, `feedback_grammar`

**Parameters:**
```python
{
    "temperature": 0.7,
    "top_p": 0.9,
    "top_k": 40,
    "max_new_tokens": 256,
    "do_sample": True
}
```

**Rationale:**
- **Creativity needed:** Teaching benefits from varied phrasing and natural language
- **Temperature 0.7:** Balanced - not too random, not too rigid
- **Top-p 0.9:** Nucleus sampling keeps responses coherent while allowing variety
- **Top-k 40:** Limits to reasonable token choices
- **Goal:** Engaging, human-like teaching interactions that don't feel robotic

**Example output variation:**
```
Response 1: "Great work! You're really getting the hang of this. ✓"
Response 2: "Excellent! That's exactly right. ✓"
Response 3: "Perfect! You nailed it. ✓"
```

---

### Grading Modes (Agent 2)

**Modes:** `grading_vocab`, `grading_grammar`

**Parameters:**
```python
{
    "do_sample": False,  # Deterministic
    "max_new_tokens": 512,
    "temperature": None,  # Not used when do_sample=False
    "top_p": None,
    "top_k": None
}
```

**Rationale:**
- **Consistency required:** Same input should produce same grading result
- **Reproducibility:** Critical for evaluation and debugging
- **Deterministic mode:** Uses greedy decoding (always picks highest probability token)
- **Longer output:** May need more tokens for detailed error analysis
- **Goal:** Reliable, repeatable grading that can be audited

**Example (deterministic):**
```json
// Always produces identical output for same input
{
  "correct": false,
  "errors": [{
    "error_type": "gender_mismatch",
    "details": "كتاب (masculine) paired with كبيرة (feminine)"
  }]
}
```

---

### Exercise Generation Mode (Agent 3)

**Mode:** `exercise_generation`

**Parameters:**
```python
{
    "temperature": 0.8,
    "top_p": 0.9,
    "top_k": 50,
    "max_new_tokens": 512,
    "do_sample": True
}
```

**Rationale:**
- **Creativity essential:** Need varied exercise questions to avoid repetition
- **Temperature 0.8:** Higher than teaching (more creative) but not chaotic
- **Top-k 50:** Broader token selection for diverse question generation
- **Longer output:** Exercises are JSON arrays with multiple items
- **Goal:** Diverse, interesting exercises that don't feel copy-pasted

**Example variety:**
```json
[
  {"question": "Complete: كتاب ___", "answer": "كبير"},
  {"question": "The book is big: ___ كبير", "answer": "كتاب"},
  {"question": "Add adjective: الكتاب ___", "answer": "الكبير"}
]
```

---

## Baseline Evaluation Configuration

For baseline evaluation (comparing base model vs. fine-tuned), **all modes use deterministic sampling** to ensure reproducibility:

```python
# baseline.py configuration
{
    "do_sample": False,
    "max_new_tokens": 256,  # (512 for grading/generation)
}
```

**Rationale:**
- Baseline runs need to be reproducible
- Comparison requires identical conditions
- Single baseline score can be trusted across multiple runs
- Once baseline established, can test with creative sampling

---

## Impact on Evaluation Metrics

### SentimentMetric (Teaching/Feedback Modes)
**Current:** Evaluated with deterministic sampling in baseline
**Production:** Will use creative sampling (temp=0.7)
**Impact:** Creative sampling may produce slightly varied sentiment scores, but should average around deterministic score

### JSONValidityMetric (Grading Modes)
**Always:** Deterministic sampling
**Impact:** 100% validity easier to achieve with determinism (no creative JSON formatting risks)

### StructureMetric (Grading/Generation Modes)
**Grading:** Deterministic - consistent structure
**Generation:** Creative - may need validation to ensure JSON structure maintained at temp=0.8

### AccuracyMetric (Grading Modes)
**Always:** Deterministic
**Impact:** Critical for reproducible accuracy measurements

### AlignmentMetric (Generation Mode)
**Baseline:** Deterministic
**Production:** Creative (temp=0.8)
**Impact:** Creative sampling should produce better alignment scores (more variety = better match to requirements)

---

## Configuration Management

### Code Location

**Baseline Evaluator:** `src/evaluation/baseline.py`
```python
# Lines 247-252 (teaching/feedback modes)
outputs = self.model_3b.generate(
    **inputs,
    max_new_tokens=256,
    do_sample=False,  # Deterministic for baseline
    pad_token_id=self.tokenizer.eos_token_id,
)

# Lines 299-304 (grading modes - 7B model)
outputs = self.model_7b.generate(
    **inputs,
    max_new_tokens=512,
    do_sample=False,
    pad_token_id=self.tokenizer.eos_token_id,
)
```

### Production Configuration (Future)

When deploying agents, use mode-specific configurations:

```python
# agents/teaching_agent.py
TEACHING_SAMPLING_CONFIG = {
    "temperature": 0.7,
    "top_p": 0.9,
    "top_k": 40,
    "max_new_tokens": 256,
    "do_sample": True,
}

# agents/error_detection_agent.py
GRADING_SAMPLING_CONFIG = {
    "do_sample": False,
    "max_new_tokens": 512,
}

# agents/content_retrieval_agent.py
GENERATION_SAMPLING_CONFIG = {
    "temperature": 0.8,
    "top_p": 0.9,
    "top_k": 50,
    "max_new_tokens": 512,
    "do_sample": True,
}
```

---

## Testing Different Configurations

### Ablation Study (Future Work)

Test impact of different temperatures on teaching quality:

| Temperature | Sentiment Score | Variety | Coherence |
|-------------|----------------|---------|-----------|
| 0.0 (greedy) | ? | Low | High |
| 0.5 | ? | Medium | High |
| 0.7 | ? | High | High |
| 1.0 | ? | Very High | Medium |

---

## References

- **Baseline Implementation:** `src/evaluation/baseline.py`
- **Evaluation Metrics:** `src/evaluation/metrics.py`
- **Evaluation Pipeline:** `src/evaluation/deepeval_pipeline.py`

---

**Last Updated:** 2026-04-11  
**Status:** Baseline uses deterministic sampling; production sampling configs documented for future implementation
