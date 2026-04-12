---
exercise_type: translation
grammar_point: definite_article_al
difficulty: beginner
lesson_number: 1
target_skill: adding_removing_definite_article
---

# Translation Exercise: Definite Article

## Exercise Purpose

Test student's ability to:
1. Add the definite article ال to nouns (making indefinite → definite)
2. Remove the definite article (making definite → indefinite)
3. Understand that tanween (ٌ) disappears when ال is added

---

## Template Structure

**Question Format (Add ال):**
```
Translate to Arabic: "the {noun}"

Given the indefinite form: {noun_indefinite}
```

**Question Format (Remove ال):**
```
Translate to Arabic: "a {noun}"

Given the definite form: {noun_definite}
```

**Answer Format:**
```json
{
  "correct_answer": "{arabic_with_harakaat}",
  "explanation": "Brief explanation about ال and tanween"
}
```

---

## Generation Rules

### Input Requirements
- `vocabulary_pool`: List of nouns with both indefinite and definite forms
- `question_count`: Number of questions to generate (default: 5)
- `direction`: "add_al" | "remove_al" | "mixed"

### Question Generation Logic

**Direction: add_al (indefinite → definite)**
1. Select noun from vocabulary_pool
2. Show indefinite form: {noun}ٌ
3. Ask: "Translate: the {english}"
4. Expected: ال{noun}ُ (with ال prefix, no tanween)

**Direction: remove_al (definite → indefinite)**
1. Select noun from vocabulary_pool
2. Show definite form: ال{noun}ُ
3. Ask: "Translate: a {english}"
4. Expected: {noun}ٌ (no ال, with tanween)

**Direction: mixed**
- Randomly mix add_al and remove_al questions
- Aim for ~50/50 split

---

## Example Generated Exercise Set

### Question 1 (Add ال)
**Question:** Translate to Arabic: "the book"

**Given:** كِتَابٌ (kitaabun - a book)

**Correct Answer:** الْكِتَابُ

**Explanation:** To make a noun definite, add ال at the beginning and remove the tanween (ٌ). Result: كِتَابٌ → الْكِتَابُ

---

### Question 2 (Remove ال)
**Question:** Translate to Arabic: "a school"

**Given:** الْمَدْرَسَةُ (al-madrasatu - the school)

**Correct Answer:** مَدْرَسَةٌ

**Explanation:** To make a noun indefinite, remove ال and add tanween (ٌ) at the end. Result: الْمَدْرَسَةُ → مَدْرَسَةٌ

---

### Question 3 (Add ال)
**Question:** Translate to Arabic: "the pen"

**Given:** قَلَمٌ (qalamun - a pen)

**Correct Answer:** الْقَلَمُ

**Explanation:** Add ال at the beginning and change tanween (ٌ) to single damma (ُ). Result: قَلَمٌ → الْقَلَمُ

---

### Question 4 (Mixed - identify)
**Question:** Which one means "the house"?

**Options:**
a) بَيْتٌ  
b) الْبَيْتُ  
c) بَيْتُ

**Correct Answer:** b) الْبَيْتُ

**Explanation:** الْبَيْتُ means "the house" because it has ال (definite article). Option (a) بَيْتٌ means "a house" (indefinite). Option (c) is missing proper harakaat.

---

### Question 5 (Remove ال)
**Question:** Translate to Arabic: "a table"

**Given:** الطَّاوِلَةُ (aT-Taawilatu - the table)

**Correct Answer:** طَاوِلَةٌ

**Explanation:** Remove ال and add tanween. For feminine nouns ending in ة, add ٌ after the ة: الطَّاوِلَةُ → طَاوِلَةٌ

---

## Grading Criteria

**Correct if:**
- Arabic text matches expected form exactly
- Includes proper harakaat (vowel marks)
- Has tanween (ٌ) for indefinite
- Has ال prefix for definite (no tanween)

**Common Errors to Accept (with feedback):**
- Wrong tanween type (ً or ٍ instead of ٌ) → Accept but note "use ٌ for nominative"
- Missing tanween → Accept but note "add tanween for indefinite"
- Extra space between ال and noun → Mark wrong, note "attach ال directly"

**Common Errors to Reject:**
- Missing ال when definite required
- Including ال when indefinite required
- Has both ال and tanween (conflicting markers)
- Missing all harakaat

---

## Adaptive Difficulty

**Beginner (Lesson 1):**
- Always show the starting form (indefinite or definite)
- Use only lesson vocabulary
- Focus on simple transformations (add or remove ال)

**Intermediate (Lessons 2-3):**
- Sometimes ask without showing starting form
- Mix vocabulary from multiple lessons
- Include both masculine and feminine nouns

**Advanced (Lessons 4+):**
- Use in context: "The big house" → الْبَيْتُ الْكَبِيرُ
- Test sun letters (ال + ش → الشَّمْس)
- Combine with other grammar points (pronouns, adjectives)

---

## Agent 3 Implementation Notes

**When generating this exercise type:**

1. **Parse this template** to understand structure
2. **Pull vocabulary** from cached lesson content (need both indefinite and definite forms)
3. **Generate 5 questions** with variety:
   - 2-3 "add ال" questions
   - 2-3 "remove ال" questions
   - Mix masculine and feminine nouns
4. **Output JSON**:
```json
[
  {
    "question": "Translate to Arabic: 'the book'",
    "given": "كِتَابٌ (kitaabun - a book)",
    "correct_answer": "الْكِتَابُ",
    "explanation": "To make a noun definite, add ال at the beginning and remove the tanween (ٌ)."
  },
  {
    "question": "Translate to Arabic: 'a school'",
    "given": "الْمَدْرَسَةُ (al-madrasatu - the school)",
    "correct_answer": "مَدْرَسَةٌ",
    "explanation": "To make a noun indefinite, remove ال and add tanween (ٌ) at the end."
  }
  ...
]
```

**Quality checks:**
- [ ] All Arabic includes proper harakaat and tanween
- [ ] Indefinite forms have tanween (ٌ)
- [ ] Definite forms have ال prefix (no tanween)
- [ ] Mix of add/remove ال questions (~50/50)
- [ ] Mix of masculine and feminine nouns
- [ ] All vocabulary from current or previous lessons
