---
exercise_type: fill_in_blank
grammar_point: gender_agreement
difficulty: beginner
lesson_number: 1
target_skill: identifying_noun_gender
---

# Fill-in-Blank Exercise: Gender Identification

## Exercise Purpose

Test student's ability to identify whether nouns are masculine or feminine by looking for the ة (taa marbuuta) ending.

---

## Template Structure

**Question Format:**
```
Is {noun} masculine or feminine?

Options:
a) masculine
b) feminine
```

**Answer Format:**
```json
{
  "correct_answer": "feminine" | "masculine",
  "explanation": "Brief explanation using the ة rule"
}
```

---

## Generation Rules

### Input Requirements
- `vocabulary_pool`: List of nouns (with Arabic, transliteration, English, gender)
- `question_count`: Number of questions to generate (default: 5)
- `difficulty`: beginner | intermediate | advanced

### Question Generation Logic

**For each question:**
1. Select a random noun from vocabulary_pool
2. Format question: "Is {noun_arabic} masculine or feminine?"
3. Provide options: a) masculine, b) feminine
4. Generate explanation based on gender rule

**Variation patterns:**
- Mix masculine and feminine nouns (aim for ~50/50 split)
- Include nouns with and without ة
- Vary presentation: sometimes show transliteration, sometimes just Arabic

---

## Example Generated Exercise Set

### Question 1
**Question:** Is مَدْرَسَةٌ (madrasatun) masculine or feminine?

**Options:**
a) masculine  
b) feminine

**Correct Answer:** b) feminine

**Explanation:** مَدْرَسَةٌ is feminine because it ends with ة (taa marbuuta). Words ending in ة are feminine nouns.

---

### Question 2
**Question:** Is كِتَابٌ (kitaabun) masculine or feminine?

**Options:**
a) masculine  
b) feminine

**Correct Answer:** a) masculine

**Explanation:** كِتَابٌ is masculine because it does not end with ة. Nouns without the ة ending are typically masculine.

---

### Question 3
**Question:** Is طَاوِلَةٌ masculine or feminine?

**Options:**
a) masculine  
b) feminine

**Correct Answer:** b) feminine

**Explanation:** طَاوِلَةٌ is feminine. Look for the ة (taa marbuuta) at the end - it's the key indicator of feminine gender.

---

## Grading Criteria

**Correct if:**
- Student selects the correct gender (masculine or feminine)
- Answer must match the grammatical gender of the noun

**Common Errors to Check:**
- Student confuses ة for a different letter
- Student identifies all nouns as masculine (not recognizing ة)
- Student identifies all nouns as feminine (over-applying the ة rule)

---

## Adaptive Difficulty

**Beginner (Lesson 1):**
- Use only lesson vocabulary (10 words)
- Always show transliteration
- Use clear, common nouns

**Intermediate (Lessons 2-3):**
- Mix lesson vocabulary with previous lessons
- Sometimes omit transliteration (test reading)
- Include nouns without ة (test masculine default rule)

**Advanced (Lessons 4+):**
- Include exception words (feminine without ة)
- Test in context of sentences
- Combine with other grammar points

---

## Agent 3 Implementation Notes

**When generating this exercise type:**

1. **Parse this template** to understand structure
2. **Pull vocabulary** from cached lesson content
3. **Generate 5 questions** following the format
4. **Ensure variety**: Mix masculine/feminine, vary transliteration visibility
5. **Output JSON**:
```json
[
  {
    "question": "Is مَدْرَسَةٌ (madrasatun) masculine or feminine?",
    "options": ["masculine", "feminine"],
    "correct_answer": "feminine",
    "explanation": "مَدْرَسَةٌ is feminine because it ends with ة (taa marbuuta)."
  },
  ...
]
```

**Quality checks:**
- [ ] All questions use vocabulary from current or previous lessons
- [ ] Mix of masculine and feminine nouns (~50/50)
- [ ] Explanations reference the ة rule
- [ ] All Arabic text includes proper harakaat and tanween
