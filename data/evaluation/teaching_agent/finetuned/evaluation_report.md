# Fine-Tuned Agent 1 - Evaluation Report

**Base Model:** Qwen/Qwen2.5-3B-Instruct
**LoRA Adapters:** /Users/kellydiabagate/Documents/LLMCourse/arabic-teaching-multi-agent/models/qwen-3b-arabic-teaching
**Evaluation Date:** 2026-04-13

## Comparison with Baseline

**Overall Performance:**
- Baseline: 12/35 (34.3%)
- Fine-tuned: 12/35 (34.3%)
- **Improvement: ➡️ +0.0%**

| Mode | Baseline | Fine-tuned | Δ |
|------|----------|------------|---|
| lesson_start ❌ | 0.0% | 0.0% | +0.0% |
| teaching_vocab ❌ | 0.0% | 0.0% | +0.0% |
| teaching_grammar ⚠️ | 40.0% | 60.0% | +20.0% |
| feedback_vocab ❌ | 40.0% | 30.0% | -10.0% |
| feedback_grammar ⚠️ | 60.0% | 60.0% | +0.0% |

---

## Lesson Start

**Passed:** 0/5

### Metrics Breakdown

**Has Navigation:**

- ✗ `lesson_start_01` (score: 0.00)
  - ✗ No clear navigation options provided
- ✗ `lesson_start_02` (score: 0.00)
  - ✗ No clear navigation options provided
- ✗ `lesson_start_03` (score: 0.00)
  - ✗ No clear navigation options provided
- ✗ `lesson_start_04` (score: 0.00)
  - ✗ No clear navigation options provided
- ✗ `lesson_start_05` (score: 0.00)
  - ✗ No clear navigation options provided

**Sentiment Teaching:**

- ✓ `lesson_start_01` (score: 0.75)
  - Sentiment score: 0.748 (✓ threshold: 0.6)
- ✓ `lesson_start_02` (score: 0.75)
  - Sentiment score: 0.748 (✓ threshold: 0.6)
- ✓ `lesson_start_03` (score: 0.75)
  - Sentiment score: 0.748 (✓ threshold: 0.6)
- ✓ `lesson_start_04` (score: 0.75)
  - Sentiment score: 0.748 (✓ threshold: 0.6)
- ✓ `lesson_start_05` (score: 0.75)
  - Sentiment score: 0.748 (✓ threshold: 0.6)

---

## Teaching Vocab

**Passed:** 0/5

### Metrics Breakdown

**Structure Valid:**

- ✗ `batch_intro_01` (score: 0.50)
  - ⚠ Word count mismatch: got 0, expected 3
- ✗ `batch_intro_02` (score: 0.50)
  - ⚠ Word count mismatch: got 0, expected 3
- ✗ `batch_intro_03` (score: 0.50)
  - ⚠ Word count mismatch: got 0, expected 2
- ✗ `batch_intro_04` (score: 0.50)
  - ⚠ Word count mismatch: got 0, expected 1
- ✗ `batch_intro_05` (score: 0.50)
  - ⚠ Word count mismatch: got 0, expected 3

**Has Navigation:**

- ✗ `batch_intro_01` (score: 0.00)
  - ✗ No clear navigation options provided
- ✗ `batch_intro_02` (score: 0.00)
  - ✗ No clear navigation options provided
- ✗ `batch_intro_03` (score: 0.00)
  - ✗ No clear navigation options provided
- ✗ `batch_intro_04` (score: 0.00)
  - ✗ No clear navigation options provided
- ✗ `batch_intro_05` (score: 0.00)
  - ✗ No clear navigation options provided

**Sentiment Teaching:**

- ✓ `batch_intro_01` (score: 0.75)
  - Sentiment score: 0.748 (✓ threshold: 0.6)
- ✓ `batch_intro_02` (score: 0.75)
  - Sentiment score: 0.748 (✓ threshold: 0.6)
- ✓ `batch_intro_03` (score: 0.75)
  - Sentiment score: 0.748 (✓ threshold: 0.6)
- ✓ `batch_intro_04` (score: 0.75)
  - Sentiment score: 0.748 (✓ threshold: 0.6)
- ✓ `batch_intro_05` (score: 0.75)
  - Sentiment score: 0.748 (✓ threshold: 0.6)

---

## Teaching Grammar

**Passed:** 3/5

### Metrics Breakdown

**Has Navigation:**

- ✓ `grammar_explain_01` (score: 1.00)
  - ✓ Has navigation guidance
- ✓ `grammar_explain_02` (score: 1.00)
  - ✓ Has navigation guidance
- ✗ `grammar_explain_03` (score: 0.00)
  - ✗ No clear navigation options provided
- ✓ `grammar_explain_04` (score: 1.00)
  - ✓ Has navigation guidance
- ✗ `grammar_explain_05` (score: 0.00)
  - ✗ No clear navigation options provided

**Sentiment Teaching:**

- ✓ `grammar_explain_01` (score: 1.00)
  - Sentiment score: 0.997 (✓ threshold: 0.6)
- ✓ `grammar_explain_02` (score: 1.00)
  - Sentiment score: 0.999 (✓ threshold: 0.6)
- ✓ `grammar_explain_03` (score: 0.98)
  - Sentiment score: 0.980 (✓ threshold: 0.6)
- ✓ `grammar_explain_04` (score: 0.97)
  - Sentiment score: 0.967 (✓ threshold: 0.6)
- ✓ `grammar_explain_05` (score: 0.98)
  - Sentiment score: 0.982 (✓ threshold: 0.6)

---

## Feedback Vocab

**Passed:** 3/10

### Metrics Breakdown

**Sentiment Feedback:**

- ✓ `feedback_vocab_correct_01` (score: 1.00)
  - Sentiment score: 0.995 (✓ threshold: 0.8)
- ✗ `feedback_vocab_correct_02` (score: 0.40)
  - Sentiment score: 0.396 (✗ threshold: 0.8)
- ✓ `feedback_vocab_correct_03` (score: 1.00)
  - Sentiment score: 1.000 (✓ threshold: 0.8)
- ✓ `feedback_vocab_correct_04` (score: 1.00)
  - Sentiment score: 0.999 (✓ threshold: 0.8)
- ✓ `feedback_vocab_correct_05` (score: 0.99)
  - Sentiment score: 0.992 (✓ threshold: 0.8)
- ✗ `feedback_vocab_incorrect_01` (score: 0.01)
  - Sentiment score: 0.005 (✗ threshold: 0.8)
- ✓ `feedback_vocab_incorrect_02` (score: 0.99)
  - Sentiment score: 0.990 (✓ threshold: 0.8)
- ✓ `feedback_vocab_incorrect_03` (score: 0.98)
  - Sentiment score: 0.983 (✓ threshold: 0.8)
- ✗ `feedback_vocab_incorrect_04` (score: 0.00)
  - Sentiment score: 0.002 (✗ threshold: 0.8)
- ✗ `feedback_vocab_incorrect_05` (score: 0.00)
  - Sentiment score: 0.003 (✗ threshold: 0.8)

**Feedback Appropriateness:**

- ✓ `feedback_vocab_correct_01` (score: 1.00)
  - ✓ Appropriate praise for correct answer
- ✓ `feedback_vocab_correct_02` (score: 1.00)
  - ✓ Appropriate praise for correct answer
- ✗ `feedback_vocab_correct_03` (score: 0.00)
  - ✗ Missing praise for correct answer
- ✓ `feedback_vocab_correct_04` (score: 1.00)
  - ✓ Appropriate praise for correct answer
- ✓ `feedback_vocab_correct_05` (score: 1.00)
  - ✓ Appropriate praise for correct answer
- ✗ `feedback_vocab_incorrect_01` (score: 0.00)
  - ✗ Gives false praise for incorrect answer
- ✗ `feedback_vocab_incorrect_02` (score: 0.00)
  - ✗ Gives false praise for incorrect answer
- ✗ `feedback_vocab_incorrect_03` (score: 0.00)
  - ✗ Gives false praise for incorrect answer
- ✗ `feedback_vocab_incorrect_04` (score: 0.00)
  - ✗ Gives false praise for incorrect answer
- ✗ `feedback_vocab_incorrect_05` (score: 0.00)
  - ✗ Gives false praise for incorrect answer

---

## Feedback Grammar

**Passed:** 6/10

### Metrics Breakdown

**Sentiment Feedback:**

- ✓ `feedback_grammar_correct_01` (score: 1.00)
  - Sentiment score: 1.000 (✓ threshold: 0.8)
- ✗ `feedback_grammar_correct_02` (score: 0.18)
  - Sentiment score: 0.181 (✗ threshold: 0.8)
- ✓ `feedback_grammar_correct_03` (score: 1.00)
  - Sentiment score: 1.000 (✓ threshold: 0.8)
- ✓ `feedback_grammar_correct_04` (score: 1.00)
  - Sentiment score: 1.000 (✓ threshold: 0.8)
- ✓ `feedback_grammar_correct_05` (score: 1.00)
  - Sentiment score: 1.000 (✓ threshold: 0.8)
- ✗ `feedback_grammar_incorrect_01` (score: 0.75)
  - Sentiment score: 0.748 (✗ threshold: 0.8)
- ✓ `feedback_grammar_incorrect_02` (score: 0.89)
  - Sentiment score: 0.886 (✓ threshold: 0.8)
- ✓ `feedback_grammar_incorrect_03` (score: 1.00)
  - Sentiment score: 0.996 (✓ threshold: 0.8)
- ✗ `feedback_grammar_incorrect_04` (score: 0.75)
  - Sentiment score: 0.748 (✗ threshold: 0.8)
- ✓ `feedback_grammar_incorrect_05` (score: 1.00)
  - Sentiment score: 0.996 (✓ threshold: 0.8)

**Feedback Appropriateness:**

- ✓ `feedback_grammar_correct_01` (score: 1.00)
  - ✓ Appropriate praise for correct answer
- ✗ `feedback_grammar_correct_02` (score: 0.00)
  - ✗ Missing praise for correct answer
- ✓ `feedback_grammar_correct_03` (score: 1.00)
  - ✓ Appropriate praise for correct answer
- ✓ `feedback_grammar_correct_04` (score: 1.00)
  - ✓ Appropriate praise for correct answer
- ✓ `feedback_grammar_correct_05` (score: 1.00)
  - ✓ Appropriate praise for correct answer
- ✗ `feedback_grammar_incorrect_01` (score: 0.00)
  - ✗ Doesn't show correct answer or provide correction
- ✗ `feedback_grammar_incorrect_02` (score: 0.00)
  - ✗ Doesn't show correct answer or provide correction
- ✓ `feedback_grammar_incorrect_03` (score: 0.70)
  - ⚠ Shows correction but could be more supportive
- ✗ `feedback_grammar_incorrect_04` (score: 0.00)
  - ✗ Doesn't show correct answer or provide correction
- ✓ `feedback_grammar_incorrect_05` (score: 0.70)
  - ⚠ Shows correction but could be more supportive

---
