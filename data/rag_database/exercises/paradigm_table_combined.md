---
exercise_type: paradigm_table
grammar_point: full_noun_paradigm
difficulty: beginner
lesson_number: 1
target_skill: systematic_form_generation
reusable: true
reusable_for: [noun_forms, verb_conjugation, pronoun_tables, adjective_declension, noun_cases]
adaptation_params:
  - table_headers: Column names for the paradigm
  - row_categories: Row categories (e.g., person, number, gender)
  - form_count: Number of forms in paradigm
  - systematic_pattern: Pattern that connects forms
---

# Paradigm Table Exercise: Complete Noun Forms

## Exercise Purpose

Test student's ability to:
1. Generate all forms of a noun systematically
2. Apply both gender and definiteness rules comprehensively
3. See relationships between all forms of one word
4. Build complete mental model of noun declension

---

## Template Structure

**Question Format:**
```
Complete this table for the word "{english}":

| Gender | Indefinite | Definite |
|--------|-----------|----------|
| ?      | ?         | ?        |
```

**Answer Format:**
```json
{
  "gender": "masculine" | "feminine",
  "indefinite": "{arabic_indefinite}",
  "definite": "{arabic_definite}"
}
```

---

## Generation Rules

### Input Requirements
- `vocabulary_pool`: List of nouns with all forms
- `question_count`: Number of tables to complete (default: 3-5)
- `blanks_pattern`: "all" | "partial" | "mixed"
- `difficulty`: beginner | intermediate | advanced

### Blank Patterns

**Pattern 1: All blanks (hardest)**
```
| Gender | Indefinite | Definite |
|--------|-----------|----------|
| ?      | ?         | ?        |
```
Given: "book" → Student fills all 3 cells

**Pattern 2: Given one form (medium)**
```
| Gender | Indefinite     | Definite |
|--------|----------------|----------|
| ?      | كِتَابٌ        | ?        |
```
Given indefinite → Student identifies gender and produces definite

**Pattern 3: Given gender only (easier)**
```
| Gender     | Indefinite | Definite |
|------------|-----------|----------|
| masculine  | ?         | ?        |
```
Given gender → Student produces both forms

**Pattern 4: Mixed (one blank each)**
```
| Gender | Indefinite | Definite      |
|--------|-----------|---------------|
| ?      | طَاوِلَةٌ | ?             |

| Gender     | Indefinite | Definite |
|------------|-----------|----------|
| masculine  | ?         | الْقَلَمُ |
```

---

## Example Generated Exercise Set

### Question 1 (All Blanks)
**Question:** Complete this table for the word "book":

| Gender | Indefinite | Definite |
|--------|-----------|----------|
| ?      | ?         | ?        |

**Correct Answer:**

| Gender     | Indefinite | Definite    |
|------------|-----------|-------------|
| masculine  | كِتَابٌ    | الْكِتَابُ |

**Explanation:**
- Gender: masculine (no ة ending)
- Indefinite: كِتَابٌ (kitaabun) - has tanween
- Definite: الْكِتَابُ (al-kitaabu) - has ال, no tanween

---

### Question 2 (Given Indefinite)
**Question:** Complete this table:

| Gender | Indefinite     | Definite |
|--------|----------------|----------|
| ?      | مَدْرَسَةٌ      | ?        |

**Correct Answer:**

| Gender     | Indefinite     | Definite       |
|------------|----------------|----------------|
| feminine   | مَدْرَسَةٌ      | الْمَدْرَسَةُ   |

**Explanation:**
- Gender: feminine (ends in ة)
- Indefinite: مَدْرَسَةٌ (given) - has ة and tanween
- Definite: الْمَدْرَسَةُ (al-madrasatu) - add ال, remove tanween

---

### Question 3 (Given Definite)
**Question:** Complete this table:

| Gender | Indefinite | Definite      |
|--------|-----------|---------------|
| ?      | ?         | الطَّاوِلَةُ   |

**Correct Answer:**

| Gender     | Indefinite   | Definite      |
|------------|-------------|---------------|
| feminine   | طَاوِلَةٌ    | الطَّاوِلَةُ   |

**Explanation:**
- Gender: feminine (has ة in definite form)
- Indefinite: طَاوِلَةٌ (taawilatun) - remove ال, add tanween
- Definite: الطَّاوِلَةُ (given) - has ال, no tanween

---

### Question 4 (Given Gender - Masculine)
**Question:** Complete this table for "pen":

| Gender     | Indefinite | Definite |
|------------|-----------|----------|
| masculine  | ?         | ?        |

**Correct Answer:**

| Gender     | Indefinite | Definite   |
|------------|-----------|------------|
| masculine  | قَلَمٌ     | الْقَلَمُ  |

**Explanation:**
- Gender: masculine (given) - no ة ending
- Indefinite: قَلَمٌ (qalamun) - has tanween
- Definite: الْقَلَمُ (al-qalamu) - has ال, no tanween

---

### Question 5 (Multiple Tables - Challenge)
**Question:** Complete both tables:

**Table A: "door"**
| Gender | Indefinite | Definite |
|--------|-----------|----------|
| ?      | ?         | ?        |

**Table B: "window"**
| Gender | Indefinite | Definite |
|--------|-----------|----------|
| ?      | ?         | ?        |

**Correct Answer:**

**Table A:**
| Gender     | Indefinite | Definite  |
|------------|-----------|-----------|
| masculine  | بَابٌ      | الْبَابُ  |

**Table B:**
| Gender     | Indefinite  | Definite      |
|------------|-------------|---------------|
| feminine   | نَافِذَةٌ   | النَّافِذَةُ  |

**Explanation:**
- Door (بَابٌ): masculine (no ة), indefinite بَابٌ, definite الْبَابُ
- Window (نَافِذَةٌ): feminine (has ة), indefinite نَافِذَةٌ, definite النَّافِذَةُ

---

## Grading Criteria

**Correct if:**
- Gender identification is correct
- Indefinite form has tanween (ٌ), no ال
- Definite form has ال, no tanween
- All harakaat present
- Feminine forms have ة, masculine forms do not

**Partial Credit per cell:**
- Gender: 20% of total
- Indefinite: 40% of total
- Definite: 40% of total

**Common Errors:**
- Gender wrong but forms consistent → 50% (applied rules correctly to wrong gender)
- Indefinite has ال or missing tanween → 0% for that cell
- Definite missing ال or has tanween → 0% for that cell
- Missing harakaat → 80% for that cell

---

## Adaptive Difficulty

**Beginner (Lesson 1):**
- One table per question
- Given 1-2 cells (only fill 1-2 blanks)
- Always provide English word as hint
- Use only lesson vocabulary

**Intermediate (Lessons 2-3):**
- One table per question
- Given 0-1 cells (fill 2-3 blanks)
- Sometimes no English hint (work from given Arabic form)
- Mix vocabulary from multiple lessons

**Advanced (Lessons 4+):**
- Multiple tables per question (2-3 words)
- All blanks (fill entire table)
- No English hints
- Include exception words

---

## Agent 3 Implementation Notes

**When generating this exercise type:**

1. **Parse this template** to understand table structure
2. **Pull vocabulary** from cached lesson content
3. **Select blank pattern** based on difficulty
4. **Generate table** with appropriate blanks
5. **Output JSON**:
```json
{
  "question": "Complete this table for the word 'book':",
  "english_word": "book",
  "table": {
    "given_cells": {
      "gender": null,
      "indefinite": null,
      "definite": null
    },
    "correct_answers": {
      "gender": "masculine",
      "indefinite": "كِتَابٌ",
      "definite": "الْكِتَابُ"
    }
  },
  "explanation": "masculine (no ة), indefinite كِتَابٌ (has tanween), definite الْكِتَابُ (has ال, no tanween)"
}
```

**Quality checks:**
- [ ] All Arabic includes proper harakaat and tanween
- [ ] Indefinite forms have tanween (ٌ)
- [ ] Definite forms have ال prefix (no tanween)
- [ ] Gender matches ة presence
- [ ] All vocabulary from current or previous lessons
- [ ] Blank pattern appropriate for difficulty level

---

## Pedagogical Notes

**Why this exercise works:**
- Shows systematic relationships (not isolated forms)
- Builds paradigm thinking (all forms of one word)
- Reinforces mutual exclusivity of ال and tanween
- Visual format aids memory

**What this reveals:**
- **Can't identify gender from forms** → Doesn't recognize ة pattern
- **Produces both forms but wrong gender** → Understands mechanics but not gender identification
- **Confuses which form is indefinite/definite** → Doesn't understand marker meanings
- **Mixes ال and tanween** → Fundamental misunderstanding of definiteness

**Learning progression:**
1. **Given 2 cells** → Fill 1 (easiest)
2. **Given 1 cell** → Fill 2 (medium)
3. **Given 0 cells** → Fill 3 (hardest)
4. **Multiple tables** → Systematic practice

**Comparison to linguistic paradigms:**
```
Traditional noun paradigm:
        Singular  | Plural
Nom.    كِتَابٌ   | كُتُبٌ
Acc.    كِتَابًا  | كُتُبًا
Gen.    كِتَابٍ   | كُتُبٍ

Our beginner paradigm:
         Indefinite | Definite
Gender   masculine  |
Form     كِتَابٌ     | الْكِتَابُ
```

We simplify to essential contrasts for beginners.

---

## UI/Implementation Notes

**For web interface:**
- Interactive table with editable cells
- Color-code given cells (gray) vs. blank cells (white)
- Show checkmark/X per cell as student fills
- Allow submit after all blanks filled

**For text interface:**
- Label cells: "Gender:", "Indefinite:", "Definite:"
- Student responds: "Gender: masculine, Indefinite: كِتَابٌ, Definite: الْكِتَابُ"
- Accept abbreviated format: "m, كِتَابٌ, الْكِتَابُ"

**Accessibility:**
- Screen reader support for table navigation
- Keyboard shortcuts to move between cells
- Option to see table as list format
