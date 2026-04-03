# Training Data V4 - Clean Vocabulary Dominance Strategy

**Created:** 2026-03-29
**Purpose:** Override grammar leakage with 48 clean vocab-only examples (vs 38 with leakage)

---

## Problem (from v3 evaluation)

**v3 Results:**
- Training with 20 clean vocab vs 38 with grammar leakage
- **20 < 38** → Model learned the bad pattern (grammar terms in vocab phase)
- Evaluation: Still showing `[masculine]`/`[feminine]` labels in vocab phase
- Pass rate: Still low (model learned dominant pattern)

**Root Cause:**
- lesson_2, lesson_8, full_flow all have grammar leakage in vocabulary phases
- ~38 total conversations teaching vocab with `[masculine]`/`[feminine]` labels
- 20 clean examples not enough to override

---

## Solution: Dominance Strategy

### Create 48 Clean Examples (28 new + 20 existing)

**New Patterns Added (28 conversations):**
1. Different word orderings (household first, school first, people first)
2. Mixed Arabic/English question formats
3. Grammar questions deferred ("Why two student words?" → defer)
4. Batch size variations (2-3-5, all 10 at once, etc.)
5. Pronunciation help provided
6. Multiple review cycles (patient repetition)
7. Word confusion clarification (similar words)
8. Very concise/efficient style
9. Very encouraging/enthusiastic tone
10. Grouped by theme (school, home, tools)
11. Student gets tired mid-lesson (break offered)
12. Both Arabic typing + English answer tests
13. Multiple wrong answers (patient correction)
14. Adaptive pacing (2→3→5 words)
15. Preview expectations at start
16. Present all, then test random order
17. Anxious student (lots of encouragement)
18. Numbered progress explicitly shown
19. Mnemonic hints when struggling
20. Multiple review cycles requested
21. Summary at checkpoints
22. Sounds/letters question (defer to alphabet lesson)
23. Different question formats (multiple choice, fill blank)
24. Very concise, no extra text
25. Preview lesson structure
26. Student wants to see all first
27. Compare/contrast similar words
28. Explicit transition to grammar

**Total Clean Vocab Examples:** 48 (20 original + 28 new)

---

## V4 Composition

**Total Conversations:** 126

**Files Included:**
1. `common_errors_conversations.jsonl` - 10 conversations
2. `edge_cases_conversations.jsonl` - ~10 conversations
3. `exercise_variety_conversations.jsonl` - ~15 conversations
4. `full_flow_conversations.jsonl` - ~12 conversations (has 17 grammar leakage instances)
5. `lesson_2_conversations.jsonl` - ~11 conversations (has 10 grammar leakage instances)
6. `lesson_8_conversations.jsonl` - ~12 conversations (has 10 grammar leakage instances)
7. `error_validation_conversations.jsonl` - 15 conversations
8. `vocab_only_final.jsonl` - 48 conversations ✓ (NEW!)

**Critical Ratio:**
- **48 clean vocab examples** (good pattern)
- **~38 vocab with grammar leakage** (bad pattern)
- **48 > 38** → Clean pattern dominates! ✓

**Error-Related Content:**
- 25 conversations (common_errors + error_validation)
- 19.8% of total (still balanced ✓)

**File Size:** 224KB (up from 176KB)

---

## Changes vs V3

| Metric | V3 | V4 | Change |
|--------|----|----|--------|
| **Total Conversations** | 98 | 126 | +28 |
| **Clean Vocab Examples** | 20 | 48 | +28 ✓ |
| **Grammar Leakage** | ~38 | ~38 | Same |
| **Clean : Bad Ratio** | 0.53 | 1.26 | **Dominance!** ✓ |
| **Error Content %** | 25.5% | 19.8% | -5.7% |
| **File Size** | 176KB | 224KB | +48KB |

---

## Why This Should Work

### Pattern Learning Theory

**Model sees during training:**
- 48 examples: "Vocab phase = NO grammar terms, clean format only"
- 38 examples: "Vocab phase = grammar labels, explanations"

**Model learns:**
- Dominant pattern (48 > 38) becomes the default behavior
- Clean vocab-only format is the "correct" way to teach vocabulary
- Grammar terminology appears ONLY in grammar phase (from grammar teaching conversations)

### Supporting Evidence

**What model has for grammar teaching:**
- 23 grammar teaching conversations (from lesson_2, lesson_8, full_flow)
- These show: Grammar phase = YES, explain masculine/feminine/ة/ال
- Model learns phase separation: Vocab (clean) → Grammar (terms introduced)

**Result:**
- Vocab phase: Model outputs clean format (48 examples say so)
- Grammar phase: Model outputs grammar explanations (23 examples say so)
- Phase boundary respected ✓

---

## Diverse Patterns in 48 Clean Examples

### Teaching Styles (10 variations):
1. Standard 3-3-4 batching
2. 2-3-5 adaptive pacing
3. All 10 shown, then tested
4. Grouped by theme (school, home, people)
5. Pairs and contrasts (similar words)
6. Rapid-fire minimal text
7. Very detailed with summaries
8. Preview expectations first
9. Multiple choice / fill blank formats
10. Random order testing

### Student Behaviors (12 variations):
1. Happy path (answers all correct)
2. Forgets/struggles (needs repetition)
3. Asks pronunciation help
4. Confuses similar words
5. Multiple wrong answers
6. Gets tired mid-lesson
7. Requests multiple reviews
8. Very fast learner
9. Anxious/nervous
10. Asks about grammar (deferred)
11. Asks about writing (deferred)
12. Wants to see all words first

### Interaction Patterns (6 variations):
1. Arabic typing tests
2. English meaning tests
3. Mixed Arabic + English
4. Multiple choice
5. Fill in blank
6. Match/identify format

---

## Expected Impact

### What Should Improve:
1. ✅ **No grammar leakage in vocab phase** (48 > 38, clean dominates)
2. ✅ Clean vocabulary format: "كِتَاب (kitaab) - book" only
3. ✅ Proper phase separation maintained
4. ✅ Model leads with comprehension questions
5. ✅ Student agency (Continue/Review/Ask)

### What Should Stay Good:
- ✅ Grammar teaching ability (23 conversations preserved)
- ✅ Error correction (25 conversations, 19.8%)
- ✅ Exercise variety
- ✅ Edge case handling

### Risks:
- ⚠️ If 48:38 ratio not enough, may need to remove bad files entirely
- ⚠️ Model might average behaviors (sometimes clean, sometimes leaky)
- ⚠️ Grammar teaching quality might dilute slightly (but 23 examples should hold)

---

## Next Steps

**Immediate:**
1. ✅ Created training_data_v4.jsonl (126 conversations, 224KB)
2. ⏳ Upload to Kaggle
3. ⏳ Train at 15 epochs (~28 min, slightly longer due to +28 conversations)
4. ⏳ Re-run Capability #1 evaluation (16 tests)
5. ⏳ Target: ≥80% pass rate (≥13/16 tests)

**If V4 Passes:**
- Move to Capability #2 (Grammar Teaching) evaluation
- Build Capability #3 (Error Correction) tests
- Create final demo

**If V4 Still Fails (grammar leakage persists):**
- Option E: Remove lesson_2, lesson_8, full_flow entirely → v5
- Result: 78 conversations, 48 clean vocab, 0 grammar leakage
- Trade-off: Lose some grammar teaching examples, but keep core capability

---

## Training Parameters (Unchanged)

- **Model:** Qwen2.5-3B-Instruct
- **Method:** LoRA fine-tuning (rank=16, alpha=16)
- **Epochs:** 15
- **Training steps:** ~157 steps (126 conversations × 15 epochs ÷ effective batch size)
- **Hardware:** Kaggle T4 GPU x2
- **Training Time:** ~28 minutes (estimate, up from 26 due to more data)
- **Chat Template:** ChatML format

---

## Files Created

```
data/training/
├── vocab_only_conversations.jsonl      (10 original)
├── vocab_only_expanded.jsonl           (10 more)
├── vocab_only_batch2.jsonl             (28 new!) ✓
├── vocab_only_complete.jsonl           (20 merged)
├── vocab_only_final.jsonl              (48 total) ✓
├── training_data_v3.jsonl              (98 conversations)
├── training_data_v4.jsonl              (126 conversations) ✓
├── TRAINING_DATA_V3_NOTES.md
└── TRAINING_DATA_V4_NOTES.md           (this file) ✓
```

---

*Created as part of Training Iteration #3*
*Strategy: Dominance through volume (48 clean > 38 bad)*
*Hypothesis: Model learns dominant pattern, outputs clean vocab format*
*Evaluated against: Capability #1 - Vocabulary Introduction (16 tests)*
*Target: ≥80% pass rate with NO grammar leakage in vocab phase*
