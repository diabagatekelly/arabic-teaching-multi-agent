---
exercise_type: pattern_recognition
grammar_point: gender_identification
difficulty: beginner
lesson_number: 1
target_skill: quick_gender_pattern_spotting
---

# Pattern Recognition Exercise: Gender Identification

## Exercise Purpose

Test student's ability to:
1. Quickly identify feminine nouns among mixed lists
2. Recognize the ة (taa marbuuta) pattern at a glance
3. Build visual recognition speed for gender markers

---

## Template Structure

**Question Format:**
```
Circle/Select all the feminine nouns:

{word_list}
```

**Answer Format:**
```json
{
  "correct_selections": ["word1", "word2", ...],
  "explanation": "Brief explanation"
}
```

---

## Generation Rules

### Input Requirements
- `vocabulary_pool`: List of nouns with Arabic, transliteration, English, gender
- `total_words`: Number of words to show (default: 6-8)
- `feminine_count`: Number of feminine nouns (default: 2-4)
- `difficulty`: beginner | intermediate | advanced

### Question Generation Logic

**For each question:**
1. Select {feminine_count} feminine nouns from vocabulary_pool
2. Select remaining words as masculine nouns
3. Present all words in random order
4. Student selects only the feminine nouns

**Variation patterns:**
- Beginner: 6 words, 3 feminine (50%)
- Intermediate: 8 words, 3 feminine (37.5%)
- Advanced: 10 words, 2-3 feminine (20-30%, harder to spot)

---

## Example Generated Exercise Set

### Question 1 (Beginner)
**Question:** Select all the feminine nouns from this list:

- كِتَابٌ (kitaabun) - book
- مَدْرَسَةٌ (madrasatun) - school
- قَلَمٌ (qalamun) - pen
- طَاوِلَةٌ (taawilatun) - table
- بَابٌ (baabun) - door
- غُرْفَةٌ (ghurfatun) - room

**Correct Answer:**
```json
{
  "correct_selections": ["مَدْرَسَةٌ", "طَاوِلَةٌ", "غُرْفَةٌ"],
  "explanation": "Look for ة (taa marbuuta) at the end. Three words have it: مَدْرَسَةٌ (school), طَاوِلَةٌ (table), غُرْفَةٌ (room)."
}
```

---

### Question 2 (Intermediate - no transliteration)
**Question:** Select all the feminine nouns:

- بَيْتٌ (house)
- كُرْسِيٌّ (chair)
- نَافِذَةٌ (window)
- مَكْتَبٌ (office)
- مَدْرَسَةٌ (school)
- كِتَابٌ (book)
- بَابٌ (door)
- طَاوِلَةٌ (table)

**Correct Answer:**
```json
{
  "correct_selections": ["نَافِذَةٌ", "مَدْرَسَةٌ", "طَاوِلَةٌ"],
  "explanation": "Three words end in ة: نَافِذَةٌ, مَدْرَسَةٌ, طَاوِلَةٌ. These are all feminine."
}
```

---

### Question 3 (Challenge - mostly masculine)
**Question:** Select all the feminine nouns:

- كِتَابٌ (book)
- قَلَمٌ (pen)
- بَيْتٌ (house)
- طَاوِلَةٌ (table)
- بَابٌ (door)
- مَكْتَبٌ (office)
- كُرْسِيٌّ (chair)

**Correct Answer:**
```json
{
  "correct_selections": ["طَاوِلَةٌ"],
  "explanation": "Only one word ends in ة: طَاوِلَةٌ (table). The rest are masculine."
}
```

---

## Grading Criteria

**Correct if:**
- Student selects ALL feminine nouns
- Student selects ONLY feminine nouns (no false positives)
- Both precision and recall must be 100%

**Partial Credit:**
- If student misses 1 feminine noun: 80% credit
- If student incorrectly selects 1 masculine noun: 80% credit
- Calculate: (correct selections / total selections) × (correct selections / total feminine)

**Common Errors:**
- Missing some feminine nouns (recall issue) → "Did you check all words for ة?"
- Selecting masculine nouns (precision issue) → "Remember, only words ending in ة are feminine"
- Not selecting any / selecting all → Review basic ة rule

---

## Adaptive Difficulty

**Beginner (Lesson 1):**
- 6 words total
- 3 feminine (50% - easy to spot)
- Always show transliteration and English
- Use only lesson vocabulary

**Intermediate (Lessons 2-3):**
- 8 words total
- 2-3 feminine (25-37.5% - requires careful checking)
- Show English meaning, no transliteration
- Mix vocabulary from multiple lessons

**Advanced (Lessons 4+):**
- 10-12 words total
- 2-3 feminine (16-25% - needle in haystack)
- Arabic only, no translations
- Include exception words (if taught)
- Time pressure (speed challenge)

---

## Agent 3 Implementation Notes

**When generating this exercise type:**

1. **Parse this template** to understand structure
2. **Pull vocabulary** from cached lesson content
3. **Select feminine and masculine nouns**
4. **Randomize order** (don't cluster feminine together)
5. **Output JSON**:
```json
{
  "question": "Select all the feminine nouns from this list:",
  "words": [
    {"arabic": "كِتَابٌ", "transliteration": "kitaabun", "english": "book", "gender": "masculine"},
    {"arabic": "مَدْرَسَةٌ", "transliteration": "madrasatun", "english": "school", "gender": "feminine"},
    {"arabic": "قَلَمٌ", "transliteration": "qalamun", "english": "pen", "gender": "masculine"},
    {"arabic": "طَاوِلَةٌ", "transliteration": "taawilatun", "english": "table", "gender": "feminine"},
    {"arabic": "بَابٌ", "transliteration": "baabun", "english": "door", "gender": "masculine"},
    {"arabic": "غُرْفَةٌ", "transliteration": "ghurfatun", "english": "room", "gender": "feminine"}
  ],
  "correct_selections": ["مَدْرَسَةٌ", "طَاوِلَةٌ", "غُرْفَةٌ"],
  "explanation": "Look for ة at the end. Three words have it: مَدْرَسَةٌ, طَاوِلَةٌ, غُرْفَةٌ."
}
```

**Quality checks:**
- [ ] All Arabic includes proper harakaat and tanween
- [ ] Feminine nouns scattered throughout list (not grouped)
- [ ] Mix of masculine and feminine appropriate for difficulty level
- [ ] All vocabulary from current or previous lessons
- [ ] Explanation clearly identifies the ة pattern

---

## Pedagogical Notes

**Why this exercise works:**
- Builds pattern recognition speed
- Requires active searching (not passive multiple choice)
- Simulates real reading scenarios (scanning text for specific patterns)
- Can be gamified with speed challenges

**Learning progression:**
1. **First exposure**: 50% feminine (easy pattern recognition)
2. **Building skill**: 37% feminine (more careful checking)
3. **Mastery**: 20-25% feminine (rapid scanning of longer lists)

**Speed targets (optional):**
- Beginner: No time limit
- Intermediate: 30 seconds for 8 words
- Advanced: 45 seconds for 12 words
