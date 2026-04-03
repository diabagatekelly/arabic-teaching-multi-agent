# Training Data V6 - Grammar Restoration

**Created:** 2026-03-30
**Purpose:** Restore grammar teaching capability while maintaining clean vocabulary teaching

---

## Strategy

v5 achieved 75% pass rate on vocabulary teaching (3/4 tests) by removing ALL grammar leakage (nuclear option). However, this broke error correction capability because error correction REQUIRES grammar knowledge.

**v6 Solution:** Add back 22 clean grammar teaching conversations that are **structurally distinct** from vocabulary teaching.

---

## V6 Composition

**Total Conversations:** 113

**Sources:**
1. **From v5:** 91 conversations
   - 48 vocab teaching (clean)
   - 25 error correction
   - 10 exercise variety
   - 8 edge cases

2. **NEW - Grammar Teaching:** 22 conversations
   - 12 Lesson 1 grammar (gender, ة marker, ال article)
   - 10 Lesson 2 grammar (pronouns, nominal sentences)

**Breakdown by Type:**
- Vocabulary Teaching: 48 (42.5%)
- Grammar Teaching: 22 (19.5%) ← NEW!
- Error Correction: 25 (22.1%)
- Exercise Variety: 10 (8.8%)
- Edge Cases: 8 (7.1%)

**File Size:** 184KB (up from 155KB in v5)

---

## Grammar Teaching Design (NEW)

### Key Distinctions from Vocabulary Phase

**Structural Separation:**
- System Prompt: `"Phase: Grammar Teaching"` (vs `"Phase: Vocabulary Learning"`)
- Content Label: `"Grammar Lesson: [Topic]"` (vs `"Here are 3 words..."`)
- Entry Point: Student says "I finished vocabulary" or "Ready for grammar"

**Teaching Approach:**
- Grammar: State rule → Show examples → Test understanding
- Vocab: Introduce words → Test recall → Continue or review

**Content Scope:**
- Grammar: Uses lesson vocab + NEW words (shows generalization, demonstrates rule applies universally)
- Vocab: ONLY teaches lesson words (no grammar explanation)

**Question Style:**
- Both use closed questions only (A/B, true/false, which one)
- No open-ended questions (prevents unpredictable student responses)

### Lesson 1 Grammar Topics (12 conversations)

**Noun Gender (4 conversations):**
1. Introduction to masculine/feminine concept
2. Generalization with new words (وَلَد, بِنْت, شَجَرَة)
3. Error correction when student misidentifies
4. Clarifying question: "Why is مَدْرَسَة feminine?"

**ة Marker (4 conversations):**
1. Introduction to taa marbuuta (ة) as feminine marker
2. Practice examples identifying ة
3. Error correction when student says كِتَاب is feminine
4. Clarifying question: "What is ة exactly?"

**ال Article (4 conversations):**
1. Introduction to definite article (الكِتَاب = the book)
2. Error correction when student forgets ال
3. Clarifying question: "When do I use ال?"
4. Generalization with new words (رَجُل, وَلَد)

### Lesson 2 Grammar Topics (10 conversations)

**Subject Pronouns (4 conversations):**
1. Introduction to all 8 pronouns (أَنَا، أَنْتَ، أَنْتِ، هُوَ، هِيَ، نَحْنُ، أَنْتُمْ، هُمْ)
2. Practice identifying pronouns
3. Error correction when confusing أَنْتَ/أَنْتِ
4. Clarifying question: "Why are there two words for 'you'?"

**Nominal Sentences (6 conversations):**
1. Introduction to structure (Subject + Predicate, no verb)
2. Structure practice building sentences
3. Error correction for wrong word order (صَغِير أَنَا ✗)
4. Generalization with new words (ذَكِيّ, جَمِيل)
5. Clarifying question: "Why is there no 'is' in the sentence?"
6. Combined: pronouns + gender agreement (أَنَا طَالِب vs أَنَا طَالِبَة)

### Example Conversation Format

```json
{
  "messages": [
    {
      "role": "system",
      "content": "Mode: Learning Pathway\nLesson: 1 - Gender & Definite Article\nPhase: Grammar Teaching\nVocabulary: كِتَاب (kitaab) - book, مَدْرَسَة (madrasa) - school, قَلَم (qalam) - pen\nGrammar Focus: Noun Gender\nObjective: Teach that Arabic nouns have gender"
    },
    {
      "role": "user",
      "content": "I finished vocabulary. Ready for grammar!"
    },
    {
      "role": "assistant",
      "content": "Excellent! Now let's discover the PATTERN.\n\n**Grammar Lesson: Noun Gender**\n\nIn Arabic, every noun is either masculine or feminine..."
    }
  ]
}
```

---

## Changes vs V5

| Metric | V5 | V6 | Change |
|--------|----|----|--------|
| **Total Conversations** | 91 | 113 | +22 |
| **Vocab Examples** | 48 | 48 | Same |
| **Grammar Examples** | 0 | 22 | **+22** ✓ |
| **Error Correction** | 25 | 25 | Same |
| **Grammar Leakage in Vocab** | 0 | 0 | Still 0 ✓ |
| **File Size** | 155KB | 184KB | +29KB |

---

## Expected Impact

### What SHOULD Maintain (High Confidence):
1. ✅ **Clean vocabulary teaching** (still 0 grammar leakage in vocab phase)
2. ✅ **Structural distinction** clear (Phase labels, content framing different)
3. ✅ **Capability #1 pass rate ≥75%** (same 48 clean vocab examples)

### What SHOULD Improve (Medium-High Confidence):
1. ✅ **Grammar teaching quality** (restored with 22 clean examples)
2. ✅ **Error correction capability** (model now knows gender, ة, ال to identify errors)
3. ✅ **Capability #2 pass rate target: 70%+** (grammar teaching evaluation)
4. ✅ **Capability #3 pass rate target: 70%+** (error correction, was 0-25% in v5)

### Risk (Low):
- ⚠️ Could grammar examples re-introduce leakage? **Unlikely** - explicit phase separation and distinct framing should prevent this
- ⚠️ Model might confuse phases? **Unlikely** - system prompts and content labels are very different

---

## Training Parameters

- **Model:** Qwen2.5-3B-Instruct
- **Method:** LoRA fine-tuning (rank=16, alpha=16)
- **Epochs:** 15
- **Training steps:** ~140 steps (113 conversations × 15 epochs ÷ effective batch size)
- **Hardware:** Kaggle T4 GPU x2
- **Training Time:** ~28 minutes (estimate, up from ~23 min due to more data)
- **Chat Template:** ChatML format

---

## Validation Plan

### Phase 1: Capability #1 - Vocabulary Teaching
**Tests:** 16 tests (4 critical single-turn + multi-turn)
**Expected:** ≥3/4 critical tests pass (maintain 75% from v5)
**Metric:** NO `[masculine]`/`[feminine]` labels in vocab phase

**Success Criteria:**
- Grammar leakage should remain at 0%
- Structural distinction should prevent contamination

### Phase 2: Capability #2 - Grammar Teaching (NEW)
**Tests:** Create evaluation for grammar teaching
**Topics to test:**
- Can explain noun gender (masculine/feminine)
- Can explain ة marker
- Can explain ال article
- Can teach pronouns
- Can teach nominal sentence structure

**Expected:** ≥70% pass rate (14/20 tests or 3/4 major topics)

### Phase 3: Capability #3 - Error Correction (RESTORATION)
**Tests:** 4 critical tests + multi-turn
**Expected:** ≥70% pass rate (was 0-25% in v5, should restore)

**Success Criteria:**
- Test 1: Says "No" to كتاب كبيرة (gender mismatch)
- Test 2: Doesn't invent errors when answer is correct
- Test 3: Clearly identifies actual errors
- Test 4: Says "No" to missing ال when needed
- Multi-turn: Maintains correct grammar understanding throughout

---

## Next Steps

**Immediate:**
1. ✅ Created grammar_only_conversations.jsonl (22 conversations, 29KB)
2. ✅ Created training_data_v6.jsonl (113 conversations, 184KB)
3. ⏳ Upload to Kaggle
4. ⏳ Update notebook Cell 3: `DATASET_PATH = "training_data_v6.jsonl"`
5. ⏳ Train at 15 epochs (~28 min)
6. ⏳ Run all three capability evaluations

**If V6 Results are Good (all capabilities ≥70%):**
- ✅ All three capabilities working!
- Create final demo
- Document results
- Project complete

**If Vocab Phase Degrades (<75%):**
- Investigate: Did grammar examples cause leakage?
- Option A: Increase vocab examples (48 → 60-70) to strengthen pattern
- Option B: Make phase separation even more explicit
- Train v7

**If Grammar/Error Correction Still Struggling (<70%):**
- Add more grammar examples (22 → 30-35)
- Add more error correction examples (25 → 35-40)
- Train v7

---

## Risk Assessment

### Low Risk (90% confident):
- ✅ Vocabulary phase stays clean (structural separation strong)
- ✅ Grammar teaching works (22 examples should be sufficient)
- ✅ Error correction improves (now has grammar knowledge)

### Medium Risk (70% confident):
- ⚠️ All three capabilities hit 70%+ on first try
- ⚠️ No unexpected interactions between phases
- ⚠️ Model generalizes well beyond training examples

### Mitigation:
- If one capability weak: Add more examples for that specific capability
- If phase confusion: Strengthen system prompt distinctions
- If generalization poor: Add more variety within each conversation type

---

## Files Created

```
data/training/
├── grammar_only_conversations.jsonl       (22 conversations, 29KB) ✓
├── training_data_v6.jsonl                 (113 conversations, 184KB) ✓
└── TRAINING_DATA_V6_NOTES.md              (this file) ✓
```

**Kept from v5:**
```
├── training_data_v5.jsonl                 (91 conversations, 155KB)
├── vocab_only_final.jsonl                 (48 conversations)
└── TRAINING_DATA_V5_NOTES.md
```

---

## Curriculum Coverage

**v6 covers Lessons 1 and 2 ONLY** (scoped for MVP demo):

✅ **Lesson 1: Gender & Definite Article**
- Noun gender (masculine/feminine) ✓
- ة marker recognition ✓
- Definite article ال ✓

✅ **Lesson 2: Subject Pronouns & Nominal Sentences**
- Subject pronouns (all 8) ✓
- Nominal sentence structure ✓
- Gender agreement in sentences ✓

❌ **Not included:**
- Lesson 3: Noun-adjective agreement, adjective order (beyond demo scope)
- Lesson 4+: Verbs, tenses, questions, etc.

---

*Created as part of Training Iteration #4*
*Strategy: Restore grammar teaching with structural distinction from vocab*
*Trade-off: None! Adding capability back without sacrificing vocab cleanliness*
*Target: Vocab ≥75%, Grammar ≥70%, Error Correction ≥70%*
*Expected: All three capabilities working by leveraging phase separation*
