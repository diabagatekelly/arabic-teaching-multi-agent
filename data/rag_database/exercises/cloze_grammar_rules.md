---
exercise_type: cloze
grammar_point: grammar_rule_completion
difficulty: beginner
lesson_number: 1
target_skill: articulating_grammar_rules
reusable: true
reusable_for: [ALL_GRAMMAR_POINTS]
adaptation_params:
  - rule_text: The grammar rule statement
  - key_terms: Terms to blank out
  - acceptable_answers: List of synonyms/variations accepted
  - word_bank: Optional list of choices (for beginner level)
---

# Cloze Exercise: Grammar Rule Completion

## Exercise Purpose

Test student's ability to:
1. Articulate grammar rules in their own words
2. Recall key terminology (tanween, ة, ال)
3. Explain transformation processes
4. Demonstrate conceptual understanding (not just application)

---

## Template Structure

**Question Format:**
```
Complete the following grammar rule by filling in the blanks:

{rule_with_blanks}
```

**Answer Format:**
```json
{
  "blank_1": "answer text",
  "blank_2": "answer text",
  ...
}
```

---

## Generation Rules

### Input Requirements
- `grammar_topic`: "gender" | "definite_article" | "tanween"
- `difficulty`: beginner | intermediate | advanced
- `blank_count`: Number of blanks per rule (1-4)

### Question Types by Topic

**Gender Rules:**
1. "Words ending in _____ are feminine"
2. "The _____ (taa marbuuta) is the marker of feminine gender"
3. "If a noun does not end in ة, it is usually _____"

**Definite Article Rules:**
1. "To make a noun definite, add _____ at the beginning"
2. "When you add ال, the tanween _____"
3. "Definite nouns have _____ and no tanween"
4. "Indefinite nouns have _____ and no ال"

**Tanween Rules:**
1. "Tanween is the _____ vowel mark that indicates indefinite"
2. "When ال is added, tanween _____ and becomes a single vowel"
3. "The most common tanween for beginners is _____ (dammatan)"

---

## Example Generated Exercise Set

### Question 1 (Single Blank - Gender)
**Question:** Complete the grammar rule:

Words ending in _____ (taa marbuuta) are feminine nouns.

**Correct Answer:**
```json
{
  "blank_1": "ة"
}
```

**Acceptable Alternatives:**
- "ة" (exact)
- "ta marbuta" (transliteration)
- "taa marbuuta"
- "the letter ة"

---

### Question 2 (Single Blank - Definite Article)
**Question:** Complete the grammar rule:

To make a noun definite, add _____ at the beginning and remove the tanween.

**Correct Answer:**
```json
{
  "blank_1": "ال"
}
```

**Acceptable Alternatives:**
- "ال" (exact)
- "al" (transliteration)
- "al-" (with hyphen)
- "the definite article"
- "the article ال"

---

### Question 3 (Two Blanks - Transformation)
**Question:** Complete the grammar rule:

When you add _____ to a noun, the tanween (ٌ) _____ and becomes a single damma (ُ).

**Correct Answer:**
```json
{
  "blank_1": "ال",
  "blank_2": "disappears"
}
```

**Acceptable Alternatives for blank_2:**
- "disappears"
- "is removed"
- "goes away"
- "is dropped"
- "becomes a single vowel"

---

### Question 4 (Three Blanks - Complete Rule)
**Question:** Complete the grammar rule:

Indefinite nouns end with _____ (double vowel). Definite nouns have _____ at the beginning and _____ tanween.

**Correct Answer:**
```json
{
  "blank_1": "tanween",
  "blank_2": "ال",
  "blank_3": "no"
}
```

**Acceptable Alternatives:**
- blank_1: "tanween" | "ٌ" | "double vowel" | "dammatan"
- blank_2: "ال" | "al" | "the definite article"
- blank_3: "no" | "without" | "0" | "not"

---

### Question 5 (Multiple Choice Cloze - Intermediate)
**Question:** Complete the grammar rule by selecting the correct word:

When ال is added to كِتَابٌ, the tanween _____ and the word becomes الْكِتَابُ.

Options:
a) remains
b) disappears
c) doubles
d) moves

**Correct Answer:**
```json
{
  "answer": "b",
  "explanation": "Tanween disappears when ال is added because definite nouns cannot have tanween"
}
```

---

### Question 6 (Complex Rule - Advanced)
**Question:** Complete the complex grammar rule:

To transform an indefinite noun to definite: (1) add _____ to the _____, (2) remove the _____, and (3) replace it with a single _____.

**Correct Answer:**
```json
{
  "blank_1": "ال",
  "blank_2": "beginning",
  "blank_3": "tanween",
  "blank_4": "damma"
}
```

---

## Grading Criteria

**Correct if:**
- Meaning is accurate (accepts synonyms)
- Arabic text is exact (if Arabic required)
- Technical terms are correct (tanween, ال, ة)
- Answer fits grammatically in the blank

**Flexible Grading:**
- Accept transliteration for Arabic terms (ال = "al")
- Accept synonyms ("disappears" = "is removed" = "goes away")
- Accept descriptive answers ("the taa marbuuta letter" = "ة")
- Accept abbreviations if standard ("def." = "definite")

**Common Student Errors:**
- Wrong terminology (calling ة "feminine marker" instead of "taa marbuuta") → Partially correct, provide correct term
- Reversed logic ("add tanween" instead of "remove tanween") → Incorrect, review rule
- Vague answers ("changes" instead of "disappears") → Partially correct, request specificity

---

## Adaptive Difficulty

**Beginner (Lesson 1):**
- 1-2 blanks per rule
- Provide word bank with options
- Simple sentence structure
- Focus on key terms only (ة, ال, tanween)

**Intermediate (Lessons 2-3):**
- 2-3 blanks per rule
- No word bank (free recall)
- More complex sentences
- Combine multiple concepts in one rule

**Advanced (Lessons 4+):**
- 3-4 blanks per rule
- Multi-sentence rules
- Require technical terminology
- Test edge cases and exceptions

---

## Agent 3 Implementation Notes

**When generating this exercise type:**

1. **Parse this template** to understand cloze patterns
2. **Select grammar rule** from lesson content
3. **Determine key terms to blank out** (aim for meaningful blanks)
4. **Generate question** with blanks marked as _____
5. **Output JSON**:
```json
{
  "question": "Complete the grammar rule by filling in the blanks:",
  "rule_text": "To make a noun definite, add _____ at the beginning and remove the _____.",
  "blanks": [
    {
      "blank_id": "blank_1",
      "position": 1,
      "correct_answers": ["ال", "al", "al-", "the definite article"],
      "primary_answer": "ال"
    },
    {
      "blank_id": "blank_2",
      "position": 2,
      "correct_answers": ["tanween", "ٌ", "double vowel", "dammatan"],
      "primary_answer": "tanween"
    }
  ],
  "explanation": "The rule is: add ال and remove tanween to make a noun definite"
}
```

**Quality checks:**
- [ ] Blanks are meaningful (not trivial words like "a", "the")
- [ ] Multiple acceptable answers listed for flexibility
- [ ] Rule is grammatically correct when completed
- [ ] Explanation provided for learning
- [ ] Difficulty appropriate for lesson level

---

## Pedagogical Notes

**Why this exercise works:**
- Tests conceptual understanding (not just application)
- Requires active recall of terminology
- Builds metalinguistic awareness (ability to talk about language)
- Prepares students to explain rules to others

**What this reveals:**
- **Can apply but can't explain** → Rote memorization, needs deeper understanding
- **Uses wrong terminology** → Needs vocabulary review
- **Reverses logic** → Fundamental misconception about the rule
- **Too vague** → Understands concept but lacks precision

**Best practices:**
- Start with simple 1-blank rules (build confidence)
- Progress to multi-blank rules (increase challenge)
- Provide immediate feedback with correct terminology
- Link back to examples when student struggles with abstract rule

**Word bank strategy:**
- **Beginner**: Always provide word bank (recognition easier than recall)
- **Intermediate**: Optional word bank (student can request if needed)
- **Advanced**: No word bank (pure recall)

**Example word banks:**

**For Gender:**
```
Word Bank: ة, masculine, feminine, taa marbuuta, ending
```

**For Definite Article:**
```
Word Bank: ال, tanween, definite, indefinite, beginning, disappears, damma
```

---

## UI/Implementation Notes

**For web interface:**
- Inline blanks with text boxes
- Auto-complete suggestions for common answers
- Highlight incorrect blanks (show which need correction)
- Show correct answer after 2-3 attempts

**For text interface:**
- Number blanks: (1) _____ , (2) _____
- Student responds: "1: ال, 2: tanween"
- Accept natural language: "The answer to blank 1 is ال"
