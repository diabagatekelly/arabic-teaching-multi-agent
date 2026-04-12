---
exercise_type: agreement_matching
grammar_point: noun_adjective_agreement
difficulty: beginner
lesson_number: 1
target_skill: matching_gender_and_definiteness
reusable: true
reusable_for: [adjective_agreement, verb_subject_agreement, pronoun_agreement]
---

# Noun-Adjective Agreement Exercise

## Exercise Purpose

Test student's ability to:
1. Match adjective gender to noun gender (masculine/feminine)
2. Match adjective definiteness to noun definiteness (ال or tanween)
3. Apply correct word order (noun before adjective in Arabic)
4. Produce correct noun-adjective phrases with full agreement

---

## Template Structure

**Question Format (Type 1 - Complete the phrase):**
```
Complete the phrase with the correct form of the adjective:

{noun} + {adjective_base} (big/small/etc.)

Example: كِتَابٌ + كَبِير → ?
```

**Question Format (Type 2 - Identify error):**
```
Which phrase has correct agreement?

a) كِتَابٌ كَبِيرَةٌ
b) كِتَابٌ كَبِيرٌ
c) كَبِيرٌ كِتَابٌ
```

**Question Format (Type 3 - Fix the phrase):**
```
Fix the agreement error:

الْكِتَابُ كَبِيرٌ
```

**Answer Format:**
```json
{
  "correct_phrase": "{noun} {adjective}",
  "explanation": "Brief explanation of agreement"
}
```

---

## Generation Rules

### Input Requirements
- `vocabulary_pool`: List of nouns with gender
- `adjective_pool`: List of adjectives with masculine/feminine forms
- `question_count`: Number of questions to generate (default: 5)
- `question_type`: "complete" | "identify" | "fix" | "mixed"
- `difficulty`: beginner | intermediate | advanced

### Agreement Rules to Test

**Rule 1: Gender Agreement**
- Masculine noun → masculine adjective: كِتَابٌ كَبِيرٌ ✓
- Feminine noun → feminine adjective: طَاوِلَةٌ كَبِيرَةٌ ✓
- Mismatch: كِتَابٌ كَبِيرَةٌ ❌

**Rule 2: Definiteness Agreement**
- Indefinite noun → indefinite adjective: كِتَابٌ كَبِيرٌ ✓
- Definite noun → definite adjective: الْكِتَابُ الْكَبِيرُ ✓
- Mismatch: الْكِتَابُ كَبِيرٌ ❌

**Rule 3: Word Order**
- Noun first, adjective second: كِتَابٌ كَبِيرٌ ✓
- Adjective before noun: كَبِيرٌ كِتَابٌ ❌ (English order)

---

## Example Generated Exercise Set

### Question 1 (Complete - Gender Agreement)
**Question:** Complete the phrase with the correct form of "big":

كِتَابٌ (kitaabun - book, masculine) + كَبِير/كَبِيرَة → ?

**Correct Answer:** كِتَابٌ كَبِيرٌ

**Explanation:** كِتَابٌ is masculine, so use the masculine adjective كَبِيرٌ (not كَبِيرَةٌ). Both are indefinite (with tanween).

---

### Question 2 (Complete - Gender + Definiteness)
**Question:** Complete the phrase with the correct form of "big":

الطَّاوِلَةُ (aT-Taawilatu - the table, feminine, definite) + كَبِير/كَبِيرَة → ?

**Correct Answer:** الطَّاوِلَةُ الْكَبِيرَةُ

**Explanation:** الطَّاوِلَةُ is feminine and definite, so use الْكَبِيرَةُ (feminine form with ال, no tanween). Both gender and definiteness must match.

---

### Question 3 (Identify Correct Phrase)
**Question:** Which phrase has correct agreement?

a) مَدْرَسَةٌ كَبِيرٌ (school, feminine + big, masculine)  
b) مَدْرَسَةٌ كَبِيرَةٌ (school, feminine + big, feminine)  
c) كَبِيرَةٌ مَدْرَسَةٌ (adjective before noun)

**Correct Answer:** b) مَدْرَسَةٌ كَبِيرَةٌ

**Explanation:** 
- (a) has gender mismatch (feminine noun + masculine adjective)
- (b) is correct (both feminine, both indefinite with tanween, correct order)
- (c) has wrong word order (adjective before noun)

---

### Question 4 (Fix Agreement Error - Definiteness)
**Question:** Fix the agreement error in this phrase:

الْكِتَابُ كَبِيرٌ (al-kitaabu kabiir**un**)

**Correct Answer:** الْكِتَابُ الْكَبِيرُ

**Explanation:** الْكِتَابُ is definite (has ال), so the adjective must also be definite. Change كَبِيرٌ → الْكَبِيرُ (add ال, remove tanween).

---

### Question 5 (Fix Agreement Error - Gender)
**Question:** Fix the agreement error in this phrase:

بَيْتٌ جَمِيلَةٌ (baytun jamiilat**un**)

**Correct Answer:** بَيْتٌ جَمِيلٌ

**Explanation:** بَيْتٌ (house) is masculine, so use masculine adjective جَمِيلٌ (not feminine جَمِيلَةٌ). Remove the ة from the adjective.

---

### Question 6 (Fix Word Order)
**Question:** Fix the word order in this phrase:

كَبِيرٌ كِتَابٌ

**Correct Answer:** كِتَابٌ كَبِيرٌ

**Explanation:** In Arabic, the noun comes first, then the adjective. The phrase should be "book big" (كِتَابٌ كَبِيرٌ), not "big book" (English order).

---

## Grading Criteria

**Correct if:**
- Adjective gender matches noun gender
- Adjective definiteness matches noun definiteness (both have ال or both have tanween)
- Word order is correct (noun before adjective)
- All harakaat present

**Partial Credit:**
- Gender correct but definiteness wrong: 50%
- Definiteness correct but gender wrong: 50%
- Both correct but word order wrong: 80%
- Missing harakaat only: 80%

**Common Student Errors:**
- Gender mismatch → Review: "Adjectives must match noun gender"
- Definiteness mismatch → Review: "If noun has ال, adjective needs ال too"
- English word order → Review: "Arabic is noun-adjective, not adjective-noun"
- Both ال and tanween on adjective → Review: "ال and tanween are mutually exclusive"

---

## Adaptive Difficulty

**Beginner (Lesson 1):**
- Always show gender and definiteness in parentheses
- One agreement rule per question (either gender OR definiteness)
- Always provide transliteration
- Use only lesson vocabulary

**Intermediate (Lessons 2-3):**
- Test both gender AND definiteness in same question
- Sometimes omit hints (must identify noun gender from ة)
- Mix vocabulary from multiple lessons
- Include 2-adjective phrases: كِتَابٌ كَبِيرٌ جَدِيدٌ

**Advanced (Lessons 4+):**
- Test all three rules simultaneously (gender + definiteness + order)
- No transliteration or hints
- Include exception words (feminine without ة)
- Sentence context: "I see ___" (must determine definiteness from context)

---

## Agent 3 Implementation Notes

**When generating this exercise type:**

1. **Parse this template** to understand agreement rules
2. **Pull vocabulary** from cached lesson content (nouns + adjectives)
3. **Select noun and adjective**
4. **Determine error type** (gender, definiteness, or word order)
5. **Generate question** with appropriate format
6. **Output JSON**:
```json
{
  "question": "Complete the phrase with the correct form of 'big':",
  "noun": {
    "arabic": "كِتَابٌ",
    "transliteration": "kitaabun",
    "english": "book",
    "gender": "masculine",
    "definiteness": "indefinite"
  },
  "adjective": {
    "english": "big",
    "masculine_indefinite": "كَبِيرٌ",
    "masculine_definite": "الْكَبِيرُ",
    "feminine_indefinite": "كَبِيرَةٌ",
    "feminine_definite": "الْكَبِيرَةُ"
  },
  "correct_answer": "كِتَابٌ كَبِيرٌ",
  "explanation": "كِتَابٌ is masculine and indefinite, so use masculine indefinite adjective كَبِيرٌ"
}
```

**Quality checks:**
- [ ] All Arabic includes proper harakaat and tanween
- [ ] Noun and adjective genders are clear
- [ ] Definiteness markers are correct (ال or tanween, never both)
- [ ] Word order is Arabic (noun-adjective)
- [ ] All vocabulary from current or previous lessons
- [ ] Explanation clearly states which agreement rule(s) apply

---

## Reusability for Other Grammar Points

This template is designed to be **reusable** for other agreement contexts:

### Verb-Subject Agreement (Future Lessons)
- Replace adjective with verb
- Test gender/number agreement: هُوَ يَكْتُبُ (he writes) vs هِيَ تَكْتُبُ (she writes)

### Pronoun Agreement
- Replace adjective with pronoun
- Test gender match: كِتَابٌ → هُوَ (book → it/he) vs طَاوِلَةٌ → هِيَ (table → it/she)

### Demonstrative Agreement
- هَذَا كِتَابٌ (this book, m) vs هَذِهِ طَاوِلَةٌ (this table, f)

**To adapt this template:**
1. Change `adjective_pool` to `verb_pool`, `pronoun_pool`, etc.
2. Update agreement rules (e.g., verb prefixes instead of ة suffix)
3. Keep same question types (complete, identify, fix)

---

## Pedagogical Notes

**Why this exercise works:**
- Tests two rules simultaneously (gender + definiteness)
- Builds awareness that agreement is multi-dimensional
- Common real-world pattern (noun-adjective phrases)
- Foundation for more complex sentences

**What this reveals:**
- **Gender correct, definiteness wrong** → Understands gender but not definiteness rules
- **Definiteness correct, gender wrong** → Doesn't recognize ة as feminine marker
- **English word order** → Translating literally from English
- **Both ال and tanween** → Doesn't understand they're mutually exclusive

**Common patterns:**
1. Students often get gender right first (ة is visual)
2. Definiteness harder (requires understanding ال vs tanween)
3. Word order mistakes persist (L1 interference from English)

**Teaching sequence:**
1. Gender agreement only (definite forms to avoid tanween complexity)
2. Definiteness agreement only (same gender to isolate the rule)
3. Both together (full agreement system)
4. In sentences (realistic usage)

---

## Example Full Exercise Set (5 questions)

```json
[
  {
    "type": "complete",
    "question": "كِتَابٌ + كَبِير/كَبِيرَة → ?",
    "answer": "كِتَابٌ كَبِيرٌ"
  },
  {
    "type": "identify",
    "question": "Which is correct: (a) الطَّاوِلَةُ الْكَبِيرُ (b) الطَّاوِلَةُ الْكَبِيرَةُ (c) الطَّاوِلَةُ كَبِيرَةٌ",
    "answer": "b"
  },
  {
    "type": "fix",
    "question": "Fix: مَدْرَسَةٌ جَدِيدٌ",
    "answer": "مَدْرَسَةٌ جَدِيدَةٌ"
  },
  {
    "type": "fix",
    "question": "Fix: الْبَيْتُ قَدِيمٌ",
    "answer": "الْبَيْتُ الْقَدِيمُ"
  },
  {
    "type": "complete",
    "question": "الْمَكْتَبُ + صَغِير/صَغِيرَة → ?",
    "answer": "الْمَكْتَبُ الصَّغِيرُ"
  }
]
```
