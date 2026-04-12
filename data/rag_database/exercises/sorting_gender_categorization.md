---
exercise_type: sorting
grammar_point: gender_categorization
difficulty: beginner
lesson_number: 1
target_skill: categorizing_nouns_by_gender
reusable: true
reusable_for: [gender, verb_tense, noun_number, adjective_type, sentence_type, pronoun_person]
adaptation_params:
  - category_names: Names of categories to sort into
  - category_count: Number of categories (2-3)
  - identification_rule: How to determine category membership
---

# Sorting Exercise: Gender Categorization

## Exercise Purpose

Test student's ability to:
1. Identify multiple nouns as masculine or feminine
2. Recognize the ة (taa marbuuta) pattern across multiple words
3. Sort and categorize vocabulary by gender

---

## Template Structure

**Question Format:**
```
Sort these {count} words into masculine and feminine columns:

Words: {words_list}

Masculine: [drag/type here]
Feminine: [drag/type here]
```

**Answer Format:**
```json
{
  "masculine": ["word1", "word2", ...],
  "feminine": ["word3", "word4", ...]
}
```

---

## Generation Rules

### Input Requirements
- `vocabulary_pool`: List of nouns with Arabic, transliteration, English, gender
- `word_count`: Number of words to sort (default: 6)
- `difficulty`: beginner | intermediate | advanced

### Question Generation Logic

**For each question:**
1. Select {word_count} nouns from vocabulary_pool
2. Aim for ~50/50 masculine/feminine split
3. Present words in random order (mixed gender)
4. Student must sort into two categories

**Variation patterns:**
- Beginner: Show transliteration with Arabic
- Intermediate: Arabic only, no transliteration
- Advanced: Mix in exception words (if taught)

---

## Example Generated Exercise Set

### Question 1 (Beginner - 6 words)
**Question:** Sort these 6 words into masculine and feminine columns:

**Words:**
- كِتَابٌ (kitaabun) - book
- مَدْرَسَةٌ (madrasatun) - school
- قَلَمٌ (qalamun) - pen
- طَاوِلَةٌ (taawilatun) - table
- بَابٌ (baabun) - door
- غُرْفَةٌ (ghurfatun) - room

**Correct Answer:**
```json
{
  "masculine": ["كِتَابٌ", "قَلَمٌ", "بَابٌ"],
  "feminine": ["مَدْرَسَةٌ", "طَاوِلَةٌ", "غُرْفَةٌ"]
}
```

**Explanation:** Feminine nouns end in ة (taa marbuuta): مَدْرَسَةٌ, طَاوِلَةٌ, غُرْفَةٌ. Masculine nouns do not have this ending: كِتَابٌ, قَلَمٌ, بَابٌ.

---

### Question 2 (Intermediate - 8 words, no transliteration)
**Question:** Sort these 8 words into masculine and feminine columns:

**Words:**
- بَيْتٌ (house)
- نَافِذَةٌ (window)
- مَكْتَبٌ (office)
- كُرْسِيٌّ (chair)
- مَدْرَسَةٌ (school)
- كِتَابٌ (book)
- طَاوِلَةٌ (table)
- قَلَمٌ (pen)

**Correct Answer:**
```json
{
  "masculine": ["بَيْتٌ", "مَكْتَبٌ", "كُرْسِيٌّ", "كِتَابٌ", "قَلَمٌ"],
  "feminine": ["نَافِذَةٌ", "مَدْرَسَةٌ", "طَاوِلَةٌ"]
}
```

**Explanation:** Look for ة at the end of words. Three words have ة (feminine), five do not (masculine).

---

## Grading Criteria

**Correct if:**
- All masculine nouns are in masculine category
- All feminine nouns are in feminine category
- No words are missing or duplicated
- Accept either Arabic or English word as identifier

**Partial Credit:**
- If 75%+ correct, give partial credit with feedback on mistakes
- Identify specific words that were miscategorized

**Common Errors:**
- Student puts all words in one category → Review gender rules
- Student confuses specific words → Practice those words individually
- Student categorizes by meaning rather than grammar → Re-explain ة rule

---

## Adaptive Difficulty

**Beginner (Lesson 1):**
- 6 words total
- Always show transliteration and English
- Clear 50/50 split (3 masculine, 3 feminine)
- Use only lesson vocabulary

**Intermediate (Lessons 2-3):**
- 8 words total
- Show English meaning, no transliteration
- Uneven split (e.g., 5 masculine, 3 feminine)
- Mix vocabulary from multiple lessons

**Advanced (Lessons 4+):**
- 10 words total
- Arabic only, no translations
- Include exception words (feminine without ة)
- Time limit challenge

---

## Agent 3 Implementation Notes

**When generating this exercise type:**

1. **Parse this template** to understand structure
2. **Pull vocabulary** from cached lesson content
3. **Generate question** with mixed gender words
4. **Randomize order** so masculine/feminine aren't grouped
5. **Output JSON**:
```json
{
  "question": "Sort these 6 words into masculine and feminine columns:",
  "words": [
    {"arabic": "كِتَابٌ", "transliteration": "kitaabun", "english": "book"},
    {"arabic": "مَدْرَسَةٌ", "transliteration": "madrasatun", "english": "school"},
    {"arabic": "قَلَمٌ", "transliteration": "qalamun", "english": "pen"},
    {"arabic": "طَاوِلَةٌ", "transliteration": "taawilatun", "english": "table"},
    {"arabic": "بَابٌ", "transliteration": "baabun", "english": "door"},
    {"arabic": "غُرْفَةٌ", "transliteration": "ghurfatun", "english": "room"}
  ],
  "correct_answer": {
    "masculine": ["كِتَابٌ", "قَلَمٌ", "بَابٌ"],
    "feminine": ["مَدْرَسَةٌ", "طَاوِلَةٌ", "غُرْفَةٌ"]
  },
  "explanation": "Feminine nouns end in ة: مَدْرَسَةٌ, طَاوِلَةٌ, غُرْفَةٌ. Masculine nouns do not: كِتَابٌ, قَلَمٌ, بَابٌ."
}
```

**Quality checks:**
- [ ] All Arabic includes proper harakaat and tanween
- [ ] Words are presented in random order (not pre-sorted)
- [ ] Approximately balanced masculine/feminine split
- [ ] All vocabulary from current or previous lessons
- [ ] Explanation references the ة rule

---

## UI/Implementation Notes

**For web interface:**
- Drag-and-drop interface works well for this exercise
- Two drop zones: "Masculine" and "Feminine"
- Show checkmark/X after each word is sorted
- Allow re-sorting before final submission

**For text interface:**
- Student can list words: "Masculine: كِتَابٌ, قَلَمٌ, بَابٌ"
- Accept comma-separated lists
- Accept English or Arabic as identifiers
