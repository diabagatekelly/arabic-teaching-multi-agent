# Training Data V3 - Vocabulary Phase Grammar Leakage Fix

**Created:** 2026-03-28
**Purpose:** Fix grammar leakage in vocabulary-only phase identified during Capability #1 evaluation

---

## Problem Identified

**Evaluation Results (Training Iteration #2):**
- Pass rate: 1/4 tests (25%)
- Critical issue: Grammar terminology appearing during vocabulary-only phase
- Model was trained with examples like:
  ```
  "كِتَاب (kitaab) - book [masculine]"
  "This is a masculine noun - no special ending."
  ```

**Root Cause:**
- All 12 conversations in `lesson_1_conversations.jsonl` violated the vocab-only boundary
- Vocabulary phase included [masculine]/[feminine] labels
- Vocabulary phase explained gender patterns and ة (taa marbuta) marker
- This contradicts the pedagogical design: Vocabulary → Grammar (separate phases)

---

## Solution Applied

### Removed:
- `lesson_1_conversations.jsonl` (12 conversations with grammar leakage)

### Added:
- `vocab_only_complete.jsonl` (20 clean conversations)
  - 10 original conversations (vocab_only_conversations.jsonl)
  - 10 expanded conversations (vocab_only_expanded.jsonl)

### Clean Vocabulary Format:
```
✓ كِتَاب (kitaab) - book
✓ مَدْرَسَة (madrasa) - school
✓ بَيْت (bayt) - house

✗ NO [masculine]/[feminine] labels
✗ NO ة (taa marbuta) explanations
✗ NO grammar terminology
```

---

## V3 Composition

**Total Conversations:** 98 (up from 90 in v2)

**Files Included:**
1. `common_errors_conversations.jsonl` - 10 conversations
2. `edge_cases_conversations.jsonl` - [~10 conversations]
3. `exercise_variety_conversations.jsonl` - [~15 conversations]
4. `full_flow_conversations.jsonl` - [~15 conversations]
5. `lesson_2_conversations.jsonl` - [~12 conversations]
6. `lesson_8_conversations.jsonl` - [~11 conversations]
7. `error_validation_conversations.jsonl` - 15 conversations
8. `vocab_only_complete.jsonl` - 20 conversations (NEW!)

**Error-Related Content:**
- 25 conversations (common_errors + error_validation)
- 25.5% of total (target: 25-30%) ✓

**File Size:** 176KB (up from 161KB)

---

## Changes vs V2

| Metric | V2 | V3 | Change |
|--------|----|----|--------|
| **Total Conversations** | 90 | 98 | +8 |
| **Vocab-only Examples** | 0 clean | 20 clean | +20 |
| **Grammar Leakage** | Yes (lesson_1) | No (replaced) | Fixed |
| **Error Content %** | 27.8% | 25.5% | -2.3% |
| **File Size** | 161KB | 176KB | +15KB |

---

## Patterns in New Vocab-Only Conversations

The 20 new conversations cover:

1. **Happy paths** (2 conversations) - ideal flow, student answers correctly
2. **Review requests** (2 conversations) - student asks to repeat/review
3. **Grammar questions deferred** (1 conversation) - "Why ة ending?" → "We'll learn in grammar!"
4. **Student struggles** (3 conversations) - doesn't remember, needs help with transliteration
5. **Word confusion** (1 conversation) - mixes up similar words, model clarifies
6. **Fast learner** (1 conversation) - moves quickly through all 10 words
7. **Practical questions** (1 conversation) - "How do I write this?" → defer to writing lesson
8. **Wrong answers** (1 conversation) - model corrects gently, tests again
9. **Progress tracking** (1 conversation) - explicit "6 of 10 learned"
10. **Varied pacing** (7 conversations) - different batch sizes, question patterns

---

## Expected Impact

### What Should Improve:
1. ✅ No grammar leakage in vocabulary phase (target: 0% → measured in re-evaluation)
2. ✅ Clean vocabulary presentation (Arabic + transliteration + English only)
3. ✅ Proper phase separation (vocabulary first, grammar second)
4. ✅ Model-led conversations with comprehension questions
5. ✅ Student agency (Continue / Review / Ask choices)

### What Might Not Change Yet:
- Factual errors (if any remain, will need targeted fixes)
- Model leading behavior (new examples should help, but may need more)
- Progress tracking consistency (some examples added, should improve)

### Known Limitations:
- `lesson_2_conversations.jsonl` and `lesson_8_conversations.jsonl` contain "masculine/feminine" terms
  - Need to verify if these appear in vocabulary phase or only in grammar phase
  - If vocab phase, will need similar fix in future iteration
  - For now: focus on Lesson 1 (most critical, most evaluated)

---

## Next Steps

**Immediate:**
1. ✅ Created training_data_v3.jsonl
2. ⏳ Upload to Kaggle notebook
3. ⏳ Re-train at 15 epochs (~26 min)
4. ⏳ Re-run Capability #1 evaluation (16 tests)
5. ⏳ Document results

**If Evaluation Passes (≥80%):**
- Move to Capability #2 (Grammar Teaching) evaluation
- Build Capability #3 (Error Correction) tests

**If Evaluation Fails (<80%):**
- Analyze patterns in remaining failures
- Check if lesson_2/lesson_8 need similar vocab-only fixes
- Add more targeted training examples
- Iterate again

---

## Training Parameters (Unchanged)

- **Model:** Qwen2.5-3B-Instruct
- **Method:** LoRA fine-tuning (rank=16, alpha=16)
- **Epochs:** 15
- **Hardware:** Kaggle T4 GPU x2
- **Training Time:** ~26 minutes
- **Chat Template:** ChatML format

---

*Created as part of Training Iteration #3*
*Targeting: Grammar leakage elimination in vocabulary phase*
*Evaluated against: Capability #1 - Vocabulary Introduction (16 tests)*
