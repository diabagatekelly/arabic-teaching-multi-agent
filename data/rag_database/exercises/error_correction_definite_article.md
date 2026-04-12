---
exercise_type: error_correction
grammar_point: definite_article_spelling
difficulty: beginner
lesson_number: 1
target_skill: identifying_and_fixing_al_tanween_errors
reusable: true
reusable_for: [definite_article, verb_conjugation, pronoun_forms, adjective_agreement, plural_formation]
adaptation_params:
  - error_types: List of error patterns for this grammar point
  - correct_forms: Examples of correct usage
  - error_detection_rule: How to identify the error
---

# Error Correction Exercise: Definite Article Spelling

## Exercise Purpose

Test student's ability to:
1. Identify spelling errors in definite/indefinite nouns
2. Fix ال + tanween conflicts
3. Add missing tanween or ال
4. Apply definite/indefinite rules correctly

---

## Template Structure

**Question Format:**
```
Fix the spelling errors in these words:

1. {word_with_error_1}
2. {word_with_error_2}
3. {word_with_error_3}
...
```

**Answer Format:**
```json
{
  "corrections": [
    {
      "original": "الْكِتَابٌ",
      "corrected": "الْكِتَابُ",
      "explanation": "Remove tanween when word has ال"
    },
    ...
  ]
}
```

---

## Generation Rules

### Input Requirements
- `vocabulary_pool`: List of nouns with indefinite and definite forms
- `error_count`: Number of errors to present (default: 5)
- `error_types`: Mix of error patterns
- `difficulty`: beginner | intermediate | advanced

### Error Types

**Type 1: ال + tanween conflict (most common)**
- Error: الْكِتَابٌ (has both ال and tanween)
- Correct: الْكِتَابُ (has ال, no tanween)

**Type 2: Missing tanween on indefinite**
- Error: كِتَاب (indefinite but no tanween)
- Correct: كِتَابٌ (has tanween)

**Type 3: Missing ال on definite**
- Error: كِتَابُ (has damma but no ال)
- Correct: الْكِتَابُ (has ال)

**Type 4: Tanween on definite**
- Error: الْمَدْرَسَةٌ (definite but has tanween)
- Correct: الْمَدْرَسَةُ (no tanween)

### Question Generation Logic

**For each question set:**
1. Select 5 words from vocabulary_pool
2. Introduce 1-3 errors (mix of types)
3. Include 2-4 correct words as distractors
4. Student must identify and fix only the errors

---

## Example Generated Exercise Set

### Question 1 (Beginner - 5 words)
**Question:** Fix the spelling errors in these words. If a word is correct, write "correct".

1. الْكِتَابٌ (al-kitaabun) - "the book"
2. طَاوِلَةٌ (taawilatun) - "a table"
3. مَدْرَسَة (madrasa) - "a school"
4. الْبَيْتُ (al-baytu) - "the house"
5. قَلَم (qalam) - "a pen"

**Correct Answer:**
```json
{
  "corrections": [
    {
      "word_number": 1,
      "original": "الْكِتَابٌ",
      "corrected": "الْكِتَابُ",
      "error_type": "al_tanween_conflict",
      "explanation": "Remove tanween (ٌ) when word has ال. Change to single damma: الْكِتَابُ"
    },
    {
      "word_number": 2,
      "original": "طَاوِلَةٌ",
      "corrected": "correct",
      "error_type": "none",
      "explanation": "Indefinite feminine noun, correctly spelled with tanween"
    },
    {
      "word_number": 3,
      "original": "مَدْرَسَة",
      "corrected": "مَدْرَسَةٌ",
      "error_type": "missing_tanween",
      "explanation": "Indefinite noun must have tanween. Add ٌ: مَدْرَسَةٌ"
    },
    {
      "word_number": 4,
      "original": "الْبَيْتُ",
      "corrected": "correct",
      "error_type": "none",
      "explanation": "Definite noun, correctly spelled with ال and no tanween"
    },
    {
      "word_number": 5,
      "original": "قَلَم",
      "corrected": "قَلَمٌ",
      "error_type": "missing_tanween",
      "explanation": "Indefinite noun must have tanween. Add ٌ: قَلَمٌ"
    }
  ]
}
```

---

### Question 2 (Intermediate - focus on one error type)
**Question:** All of these words should be definite (with ال). Fix any spelling errors:

1. الطَّاوِلَةٌ (aT-Taawilatu) - "the table"
2. الْمَكْتَبُ (al-maktabu) - "the office"
3. الْكِتَابٌ (al-kitaabun) - "the book"
4. الْبَابُ (al-baabu) - "the door"
5. المَدْرَسَةٌ (al-madrasatu) - "the school"

**Correct Answer:**
All words with ال + tanween must have tanween removed:
- الطَّاوِلَةٌ → الطَّاوِلَةُ
- الْكِتَابٌ → الْكِتَابُ
- المَدْرَسَةٌ → الْمَدْرَسَةُ
- الْمَكْتَبُ ✓ correct
- الْبَابُ ✓ correct

---

### Question 3 (Challenge - mixed context)
**Question:** Fix the spelling errors. Context is given to help you:

1. "A book" in Arabic: كِتَابُ
2. "The school" in Arabic: مَدْرَسَةٌ
3. "A table" in Arabic: الطَّاوِلَةُ
4. "The pen" in Arabic: الْقَلَمُ
5. "A door" in Arabic: بَابٌ

**Correct Answer:**
- #1: كِتَابُ → كِتَابٌ (indefinite needs tanween)
- #2: مَدْرَسَةٌ → الْمَدْرَسَةُ (definite needs ال, no tanween)
- #3: الطَّاوِلَةُ → طَاوِلَةٌ (indefinite should not have ال)
- #4: الْقَلَمُ ✓ correct (definite with ال)
- #5: بَابٌ ✓ correct (indefinite with tanween)

---

## Grading Criteria

**Correct if:**
- Student correctly identifies all errors
- Student provides correct spelling fixes
- Student correctly marks correct words as "correct" (or leaves unchanged)

**Partial Credit:**
- Identify error but fix incorrectly: 50% for that item
- Miss an error: 0% for that item
- Mark correct word as error: 0% for that item

**Common Student Errors:**
- Only fixing tanween, not recognizing missing ال → Review full definite article rule
- Adding wrong vowel (kasra instead of damma) → Review harakaat placement
- Leaving all words marked as correct → May not understand what errors look like

---

## Adaptive Difficulty

**Beginner (Lesson 1):**
- 5 words, 2-3 errors
- Always show transliteration and English context
- One error type at a time (e.g., all ال + tanween conflicts)
- Clear instructions about what form is expected

**Intermediate (Lessons 2-3):**
- 6-8 words, 3-5 errors
- Show English context only
- Mix error types
- Include some correct words as distractors

**Advanced (Lessons 4+):**
- 8-10 words, 4-6 errors
- Arabic only, no context given
- All error types mixed
- Student must determine intended form from context

---

## Agent 3 Implementation Notes

**When generating this exercise type:**

1. **Parse this template** to understand error patterns
2. **Pull vocabulary** from cached lesson content
3. **Select words and introduce errors**:
   - 40% Type 1 (ال + tanween conflict)
   - 30% Type 2 (missing tanween)
   - 20% Type 4 (tanween on definite)
   - 10% Type 3 (missing ال)
4. **Add 2-3 correct distractors**
5. **Output JSON**:
```json
{
  "question": "Fix the spelling errors in these words. If a word is correct, write 'correct'.",
  "words": [
    {
      "number": 1,
      "arabic": "الْكِتَابٌ",
      "transliteration": "al-kitaabun",
      "english": "the book",
      "has_error": true
    },
    {
      "number": 2,
      "arabic": "طَاوِلَةٌ",
      "transliteration": "taawilatun",
      "english": "a table",
      "has_error": false
    },
    ...
  ],
  "corrections": [
    {
      "word_number": 1,
      "original": "الْكِتَابٌ",
      "corrected": "الْكِتَابُ",
      "error_type": "al_tanween_conflict",
      "explanation": "Remove tanween when word has ال. Change to single damma: الْكِتَابُ"
    },
    ...
  ]
}
```

**Quality checks:**
- [ ] All Arabic includes proper harakaat
- [ ] Mix of error types appropriate for difficulty level
- [ ] Include correct words as distractors (don't make all words errors)
- [ ] Clear context provided for intended form (definite vs indefinite)
- [ ] Explanations reference specific rules

---

## Pedagogical Notes

**Why this exercise works:**
- Active error detection (not passive recognition)
- Applies rules to fix problems (higher-order thinking)
- Builds editing/proofreading skills
- Mimics real writing scenarios

**Common misconceptions this reveals:**
1. Student thinks tanween and ال can coexist
2. Student doesn't recognize indefinite forms need tanween
3. Student confuses which harakaat to use (ُ vs ٌ)

**Follow-up teaching opportunities:**
- If student misses ال + tanween conflicts → Focus on "one or the other, never both"
- If student misses missing tanween → Focus on "indefinite always has tanween"
- If student marks correct words as errors → Review what correct forms look like
