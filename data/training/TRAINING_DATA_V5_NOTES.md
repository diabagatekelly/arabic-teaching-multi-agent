# Training Data V5 - Nuclear Option (Clean Only)

**Created:** 2026-03-29
**Purpose:** Eliminate ALL grammar leakage by removing problematic files entirely

---

## Problem (from v4 evaluation)

**v4 Results with do_sample=False:**
- Test 2, 3: ✅ Clean (generic prompts)
- Test 4: ❌ Grammar leakage (when user says "Lesson 1")
- Multi-turn: ❌ Grammar leakage throughout
- **Pass rate: 2/4 = 50%**

**Root Cause:**
- 48 clean vocab examples vs 38 with grammar leakage
- 1.26x ratio NOT enough to override contextual associations
- Model learned: "Lesson X" phrase → grammar-leaky pattern
- Model learned: Generic "teach vocab" → clean pattern
- **Conclusion:** Can't override with volume alone when patterns are contextually triggered

---

## Solution: Nuclear Option

### Remove ALL Files with Grammar Leakage

**REMOVED:**
- `lesson_2_conversations.jsonl` (11 conversations, 10 grammar leakage instances)
- `lesson_8_conversations.jsonl` (12 conversations, 10 grammar leakage instances)
- `full_flow_conversations.jsonl` (12 conversations, 17 grammar leakage instances)
- `lesson_1_conversations.jsonl` (already removed in v3)

**Total removed:** 35 conversations with ~37 grammar leakage instances

**KEPT (Clean files only):**
- `common_errors_conversations.jsonl` (10 conversations)
- `edge_cases_conversations.jsonl` (8 conversations)
- `exercise_variety_conversations.jsonl` (10 conversations)
- `error_validation_conversations.jsonl` (15 conversations)
- `vocab_only_final.jsonl` (48 conversations) ✓

**Total kept:** 91 conversations, 0 grammar leakage instances

---

## V5 Composition

**Total Conversations:** 91

**Breakdown:**
1. **Vocabulary Teaching (Clean):** 48 conversations (52.7%)
   - All 48 from vocab_only_final.jsonl
   - Zero grammar terminology in vocab phase
   - Diverse patterns: 28 different teaching styles, student behaviors, interaction formats

2. **Error Correction:** 25 conversations (27.5%)
   - 10 common_errors (teaching corrections during practice)
   - 15 error_validation (direct "Is X correct?" → "No, that's wrong!" patterns)

3. **Exercise Variety:** 10 conversations (11.0%)
   - Fill-in-blank, error correction, conjugation drills, sentence building
   - Various exercise types without vocab phase content

4. **Edge Cases:** 8 conversations (8.8%)
   - Low score handling, hints, "why" questions, locked content, breaks, streaks
   - General interaction patterns

**Grammar Leakage:** 0 instances (verified via grep)

**File Size:** 155KB (down from 224KB in v4)

---

## Changes vs V4

| Metric | V4 | V5 | Change |
|--------|----|----|--------|
| **Total Conversations** | 126 | 91 | -35 |
| **Clean Vocab Examples** | 48 | 48 | Same |
| **Grammar Leakage Instances** | ~38 | 0 | **-38 ✓** |
| **Clean : Bad Ratio** | 1.26 | ∞ | **Pure!** ✓ |
| **Error Content %** | 19.8% | 27.5% | +7.7% |
| **Vocab Content %** | 38.1% | 52.7% | +14.6% |
| **File Size** | 224KB | 155KB | -69KB |

---

## What We Lost (Trade-offs)

### Lost: Grammar Teaching Conversations (23 total)

**From lesson_2 (~5-6 conversations):**
- Subject pronouns teaching
- Nominal sentence structure explanations

**From lesson_8 (~5-6 conversations):**
- Possessive pronouns teaching
- Idaafah construct explanations

**From full_flow (~11-12 conversations):**
- Full lesson flow examples (vocab → grammar → practice)
- Grammar teaching for Lesson 3+ topics

**Impact:**
- ⚠️ Model may not learn to teach grammar phase as well
- ⚠️ May struggle with grammar explanations when asked
- ⚠️ Might not transition smoothly from vocab → grammar → exercises

### Retained: Core Capabilities

**What we kept:**
- ✅ Vocabulary teaching (48 examples - strong!)
- ✅ Error correction (25 examples - balanced!)
- ✅ Exercise variety (10 examples)
- ✅ Edge case handling (8 examples)
- ✅ Session management patterns (embedded in various convos)

---

## Expected Impact

### What SHOULD Improve (High Confidence):
1. ✅ **100% no grammar leakage in vocab phase** (0 bad examples)
2. ✅ Clean vocabulary format every time
3. ✅ No contextual triggers ("Lesson 1" won't cause issues)
4. ✅ Consistent behavior (do_sample=False should always be clean)
5. ✅ Capability #1 evaluation: Target 4/4 or 3/4 pass rate

### What MIGHT Suffer (Medium Risk):
1. ⚠️ **Grammar teaching quality** - lost 23 examples
2. ⚠️ Full lesson flow transitions (vocab → grammar → exercises)
3. ⚠️ Subject pronouns, possessive pronouns, idaafah explanations
4. ⚠️ Advanced grammar topics (Lessons 2, 3, 8)

### Mitigation Strategy:
- If vocab phase passes but grammar phase fails → confirmed it's the trade-off
- Can create "grammar_only_conversations.jsonl" with clean grammar teaching
- Add back 20-30 grammar examples WITHOUT vocab phase content
- Create v6 = v5 + clean grammar examples

---

## Training Parameters

- **Model:** Qwen2.5-3B-Instruct
- **Method:** LoRA fine-tuning (rank=16, alpha=16)
- **Epochs:** 15
- **Training steps:** ~113 steps (91 conversations × 15 epochs ÷ effective batch size)
- **Hardware:** Kaggle T4 GPU x2
- **Training Time:** ~23 minutes (estimate, down from ~28 min due to less data)
- **Chat Template:** ChatML format

---

## Validation Plan

### Phase 1: Capability #1 - Vocabulary Introduction (Immediate)
**Tests:** Run all 16 tests (4 critical single-turn + multi-turn)
**Expected:** ≥3/4 critical tests pass (target: 4/4)
**Metric:** NO `[masculine]`/`[feminine]` labels in vocab phase

**Success Criteria:**
- Test 2: ✅ No grammar leakage
- Test 3: ✅ No language confusion
- Test 4: ✅ No grammar leakage (this was failing in v4)
- Multi-turn: ✅ Stays clean throughout entire conversation

### Phase 2: Grammar Teaching Assessment (Secondary)
**Create new test:** Evaluate if model can still teach grammar properly
**System prompt:** Phase: Grammar Teaching
**Expected:** Model explains masculine/feminine/ة/ال concepts clearly

**Success Criteria:**
- Model can explain gender in grammar phase
- Model can explain ة (taa marbuta) marker
- Model can explain ال (definite article)
- Explanations are clear and accurate

**If Grammar Teaching Fails:**
- Confirmed trade-off (lost 23 grammar examples)
- Solution: Create grammar_only_conversations.jsonl (20-30 examples)
- Train v6 = v5 + clean grammar examples

### Phase 3: Capability #3 - Error Correction (Validation)
**Tests:** "Is X correct?" → "No, that's incorrect!"
**Expected:** Still works (25 error examples retained)

---

## Next Steps

**Immediate:**
1. ✅ Created training_data_v5.jsonl (91 conversations, 155KB)
2. ⏳ Upload to Kaggle
3. ⏳ Update Cell 3: `DATASET_PATH = "training_data_v5.jsonl"`
4. ⏳ Train at 15 epochs (~23 min)
5. ⏳ Run Capability #1 evaluation (16 tests)

**If Vocab Phase Passes (≥3/4):**
- ✅ Primary goal achieved!
- Test grammar teaching capability separately
- Document results

**If Grammar Phase Struggles:**
- Create grammar_only_conversations.jsonl with clean examples
- Train v6 = v5 + grammar_only
- Final iteration

**If Vocab Phase Still Fails (<3/4):**
- ❌ Unlikely! Zero grammar leakage in training data
- Debug: Check if system prompts match training data format
- Last resort: RAG/constraints at inference time

---

## Risk Assessment

### Low Risk (95% confident will work):
- ✅ Vocabulary phase will be clean
- ✅ No grammar leakage in vocab teaching
- ✅ Consistent behavior across all test prompts

### Medium Risk (60% confident):
- ⚠️ Grammar teaching quality maintained
- ⚠️ Model can transition vocab → grammar smoothly
- ⚠️ Full lesson flow works as expected

### Mitigation:
- If grammar suffers: Add back clean grammar examples (v6)
- If transitions break: Add full-flow examples without vocab leakage
- If specific topics missing: Target those with new conversations

---

## Files Created

```
data/training/
├── training_data_v5.jsonl              (91 conversations, 155KB) ✓
└── TRAINING_DATA_V5_NOTES.md           (this file) ✓
```

**Removed from v4:**
```
❌ lesson_2_conversations.jsonl         (11 conversations, grammar leakage)
❌ lesson_8_conversations.jsonl         (12 conversations, grammar leakage)
❌ full_flow_conversations.jsonl        (12 conversations, grammar leakage)
```

---

*Created as part of Training Iteration #3*
*Strategy: Nuclear option - eliminate ALL grammar leakage*
*Trade-off: Lost 23 grammar teaching examples (can add back if needed)*
*Target: 100% clean vocabulary teaching, assess grammar teaching separately*
*Expected: Capability #1 pass rate ≥75% (3/4 or 4/4)*
