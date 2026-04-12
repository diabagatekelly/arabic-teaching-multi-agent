---
exercise_type: multiple_choice
grammar_point: error_identification
difficulty: beginner
lesson_number: 1
target_skill: identifying_common_errors
---

# Multiple Choice Exercise: Error Identification

## Exercise Purpose

Test student's ability to:
1. Identify incorrect gender labels (feminine noun labeled as masculine)
2. Identify incorrect definite/indefinite spelling (ال + tanween conflict)
3. Recognize proper vs. improper Arabic spelling conventions

---

## Template Structure

**Question Format (Gender Label Error):**
```
Which word is incorrectly labeled?

Options:
a) {arabic_1} ({transliteration_1}) - {label_1}
b) {arabic_2} ({transliteration_2}) - {label_2}
c) {arabic_3} ({transliteration_3}) - {label_3}
```

**Question Format (Spelling Error):**
```
Which word is spelled incorrectly?

Options:
a) {arabic_1} ({transliteration_1}) - {description_1}
b) {arabic_2} ({transliteration_2}) - {description_2}
c) {arabic_3} ({transliteration_3}) - {description_3}
```

**Answer Format:**
```json
{
  "correct_answer": "b",
  "explanation": "Brief explanation of why this option is incorrect"
}
```

---

## Generation Rules

### Input Requirements
- `vocabulary_pool`: List of nouns with Arabic, transliteration, English, and gender
- `question_count`: Number of questions to generate (default: 5)
- `error_type`: "gender_label" | "spelling_definite" | "spelling_tanween" | "mixed"

### Question Generation Logic

**Error Type: gender_label**
- Show 3 words with gender labels
- ONE word has incorrect label (e.g., مَدْرَسَةٌ labeled "masculine" when it ends in ة)
- Two words have correct labels (distractors)
- Expected answer: Identify which label is wrong

**Error Type: spelling_definite**
- Show 3 words with definite article
- ONE word has spelling error (e.g., الْكِتَابٌ has both ال and tanween)
- Two words are spelled correctly
- Expected answer: Identify which spelling is wrong

**Error Type: spelling_tanween**
- Show 3 words (mix of indefinite and definite)
- ONE word missing tanween when indefinite OR has tanween when definite
- Two words are spelled correctly
- Expected answer: Identify which spelling is wrong

**Error Type: mixed**
- Randomly mix all three error types
- Aim for variety across question set

---

## Example Generated Exercise Set

### Question 1 (Gender Label Error)
**Question:** Which word is incorrectly labeled?

**Options:**
a) كِتَابٌ (kitaabun) - masculine  
b) مَدْرَسَةٌ (madrasatun) - masculine  
c) بَابٌ (baabun) - masculine

**Correct Answer:** b

**Explanation:** مَدْرَسَةٌ ends in ة (taa marbuuta), so it must be feminine, not masculine. Words ending in ة are always feminine in Lesson 1.

---

### Question 2 (Spelling Error - Definite Article)
**Question:** Which word is spelled incorrectly?

**Options:**
a) قَلَمٌ (qalamun) - indefinite  
b) الْكِتَابٌ (al-kitaabun) - definite  
c) الْبَيْتُ (al-baytu) - definite

**Correct Answer:** b

**Explanation:** الْكِتَابٌ has both ال (definite article) and tanween (ٌ). When a noun is definite, remove the tanween. Correct spelling: الْكِتَابُ with just damma (ُ).

---

### Question 3 (Gender Label Error)
**Question:** Which word is incorrectly labeled?

**Options:**
a) طَاوِلَةٌ (taawilatun) - feminine  
b) قَلَمٌ (qalamun) - masculine  
c) غُرْفَةٌ (ghurfatun) - masculine

**Correct Answer:** c

**Explanation:** غُرْفَةٌ ends in ة (taa marbuuta), which means it's feminine, not masculine. The label should be "feminine".

---

### Question 4 (Spelling Error - Missing Tanween)
**Question:** Which word is spelled incorrectly?

**Options:**
a) كِتَابٌ (kitaabun) - indefinite  
b) بَيْت (bayt) - indefinite  
c) طَاوِلَةٌ (taawilatun) - indefinite

**Correct Answer:** b

**Explanation:** بَيْت is missing tanween (ٌ). Indefinite nouns must have tanween at the end. Correct spelling: بَيْتٌ (baytun).

---

### Question 5 (Spelling Error - Tanween with Definite)
**Question:** Which word is spelled incorrectly?

**Options:**
a) الْمَكْتَبُ (al-maktabu) - definite  
b) الطَّاوِلَةٌ (at-taawilatu) - definite  
c) كُرْسِيٌّ (kursiyyun) - indefinite

**Correct Answer:** b

**Explanation:** الطَّاوِلَةٌ has both ال (definite article) and tanween (ٌ). When ال is added, remove the tanween. Correct spelling: الطَّاوِلَةُ with just damma (ُ).

---

## Grading Criteria

**Correct if:**
- Student selects the option with the error (a, b, or c)
- Answer matches the expected incorrect option

**Common Student Errors:**
- Selecting a correct option (distractor) → Need more practice identifying errors
- Not recognizing ة as feminine marker → Review gender rules
- Not recognizing ال + tanween conflict → Review definite article rules
- Not recognizing missing tanween → Review indefinite noun rules

---

## Adaptive Difficulty

**Beginner (Lesson 1):**
- Always show transliteration for all options
- Use only lesson vocabulary
- Errors are obvious (clear ة ending, clear ال + tanween conflict)
- 3 options per question

**Intermediate (Lessons 2-3):**
- Sometimes omit transliteration (test reading)
- Mix vocabulary from multiple lessons
- 4 options per question (more distractors)
- Include both masculine and feminine nouns in same question

**Advanced (Lessons 4+):**
- No transliteration (Arabic only)
- 5 options per question
- Combine multiple error types in one question set
- Include exception words (feminine without ة)

---

## Agent 3 Implementation Notes

**When generating this exercise type:**

1. **Parse this template** to understand structure
2. **Pull vocabulary** from cached lesson content
3. **Generate 5 questions** with variety:
   - 2 gender label errors
   - 2 spelling errors (definite/indefinite)
   - 1 mixed (either type)
4. **Ensure ONE wrong answer per question** and 2-3 correct distractors
5. **Output JSON**:
```json
[
  {
    "question": "Which word is incorrectly labeled?",
    "options": [
      "a) كِتَابٌ (kitaabun) - masculine",
      "b) مَدْرَسَةٌ (madrasatun) - masculine",
      "c) بَابٌ (baabun) - masculine"
    ],
    "correct_answer": "b",
    "explanation": "مَدْرَسَةٌ ends in ة (taa marbuuta), so it must be feminine, not masculine."
  },
  {
    "question": "Which word is spelled incorrectly?",
    "options": [
      "a) قَلَمٌ (qalamun) - indefinite",
      "b) الْكِتَابٌ (al-kitaabun) - definite",
      "c) الْبَيْتُ (al-baytu) - definite"
    ],
    "correct_answer": "b",
    "explanation": "الْكِتَابٌ has both ال and tanween. When definite, remove the tanween."
  }
  ...
]
```

**Quality checks:**
- [ ] All Arabic includes proper harakaat and tanween
- [ ] All options include transliteration (for beginner level)
- [ ] Exactly ONE incorrect option per question
- [ ] 2-3 correct distractors per question
- [ ] Mix of gender and spelling error types
- [ ] All vocabulary from current or previous lessons
- [ ] Explanations reference the specific rule violated

---

## Error Pattern Reference

### Gender Label Errors
```
❌ Wrong: مَدْرَسَةٌ (madrasatun) - masculine
✓ Correct: مَدْرَسَةٌ (madrasatun) - feminine

❌ Wrong: غُرْفَةٌ (ghurfatun) - masculine
✓ Correct: غُرْفَةٌ (ghurfatun) - feminine

Rule: If word ends in ة → FEMININE (not masculine)
```

### Spelling Errors - Definite Article + Tanween Conflict
```
❌ Wrong: الْكِتَابٌ (has ال + tanween)
✓ Correct: الْكِتَابُ (has ال, no tanween)

❌ Wrong: الطَّاوِلَةٌ (has ال + tanween)
✓ Correct: الطَّاوِلَةُ (has ال, no tanween)

Rule: Definite nouns (with ال) CANNOT have tanween
```

### Spelling Errors - Missing Tanween
```
❌ Wrong: كِتَاب (no tanween)
✓ Correct: كِتَابٌ (with tanween ٌ)

❌ Wrong: بَيْت (no tanween)
✓ Correct: بَيْتٌ (with tanween ٌ)

Rule: Indefinite nouns (without ال) MUST have tanween
```

---

## Success Criteria

Students should be able to:
1. ✓ Identify when a feminine noun (ending in ة) is mislabeled as masculine
2. ✓ Spot ال + tanween conflict (both markers present)
3. ✓ Recognize when indefinite nouns are missing tanween
4. ✓ Distinguish correct from incorrect spelling patterns
5. ✓ Explain WHY an option is incorrect using grammar rules
