---
exercise_type: sentence_level
grammar_point: contextual_application
difficulty: intermediate
lesson_number: 1
target_skill: applying_rules_in_sentence_context
---

# Sentence-Level Exercise: Contextual Application

## Exercise Purpose

Test student's ability to:
1. Apply gender and definiteness rules in sentence context
2. Fix errors in multi-word sentences
3. Recognize when context requires definite or indefinite forms
4. Integrate grammar rules with real language use

---

## Template Structure

**Question Format:**
```
Fix the errors in this sentence:

{sentence_with_errors}

Translation: {english_translation}
```

**Answer Format:**
```json
{
  "corrected_sentence": "{sentence_in_arabic}",
  "corrections": [
    {"word": "...", "error_type": "...", "fix": "..."}
  ],
  "explanation": "Brief explanation"
}
```

---

## Generation Rules

### Input Requirements
- `vocabulary_pool`: List of nouns with all forms
- `sentence_complexity`: "simple" | "compound"
- `error_count`: Number of errors per sentence (1-3)
- `difficulty`: intermediate | advanced

### Error Types in Context

**Type 1: Wrong definiteness for context**
```
Error: "I have كِتَابُ" (missing marker)
Correct: "I have كِتَابٌ" (indefinite - "a book")
Context clue: "a" in English = indefinite
```

**Type 2: Gender mismatch**
```
Error: "The big مَدْرَسَةٌ" (wrong form)
Correct: "The big مَدْرَسَةُ" or "The big الْمَدْرَسَةُ" 
Context clue: "the" requires definite form
```

**Type 3: Multiple errors in one sentence**
```
Error: "الْكِتَابٌ is on طَاوِلَة"
Correct: "الْكِتَابُ is on طَاوِلَةٌ"
Two errors: ال + tanween conflict, missing tanween
```

---

## Example Question 1 - Simple One Error
**Question:** Fix the error in this sentence:

The big كِتَابٌ is on the table.

**Correct Answer:**
```json
{
  "corrected_sentence": "The big الْكِتَابُ is on the table.",
  "corrections": [
    {
      "original": "كِتَابٌ",
      "corrected": "الْكِتَابُ",
      "error_type": "wrong_definiteness",
      "explanation": "'The book' is definite, needs ال and no tanween"
    }
  ]
}
```

**Explanation:** English "the" signals definite article needed. Change كِتَابٌ → الْكِتَابُ

---

## Example Question 2 - Two Words One Error Each
**Question:** Fix the errors in this sentence:

I see a كِتَاب on الطَّاوِلَةٌ.

**Correct Answer:**
```json
{
  "corrected_sentence": "I see a كِتَابٌ on الطَّاوِلَةُ.",
  "corrections": [
    {
      "original": "كِتَاب",
      "corrected": "كِتَابٌ",
      "error_type": "missing_tanween",
      "explanation": "'A book' is indefinite, needs tanween"
    },
    {
      "original": "الطَّاوِلَةٌ",
      "corrected": "الطَّاوِلَةُ",
      "error_type": "al_tanween_conflict",
      "explanation": "Definite word cannot have tanween, remove it"
    }
  ]
}
```

**Explanation:** "A" requires tanween (كِتَابٌ). "The" (ال) cannot have tanween (الطَّاوِلَةُ).

---

## Example Question 3 - Context Clues
**Question:** Fix the errors based on context:

There is a مَدْرَسَةُ near the بَيْتٌ.

**Correct Answer:**
```json
{
  "corrected_sentence": "There is a مَدْرَسَةٌ near the الْبَيْتُ.",
  "corrections": [
    {
      "original": "مَدْرَسَةُ",
      "corrected": "مَدْرَسَةٌ",
      "error_type": "missing_tanween",
      "explanation": "'A school' is indefinite (uses 'a'), needs tanween not just damma"
    },
    {
      "original": "بَيْتٌ",
      "corrected": "الْبَيْتُ",
      "error_type": "missing_al",
      "explanation": "'The house' is definite (uses 'the'), needs ال and no tanween"
    }
  ]
}
```

**Explanation:** Context words "a" and "the" signal which form to use. "A" = tanween, "the" = ال.

---

## Example Question 4 - All Arabic Sentence
**Question:** Fix the errors in this Arabic sentence:

**Arabic:** الْكِتَابٌ فِي غُرْفَة

**Translation:** The book is in a room.

**Correct Answer:**
```json
{
  "corrected_sentence": "الْكِتَابُ فِي غُرْفَةٌ",
  "corrections": [
    {
      "original": "الْكِتَابٌ",
      "corrected": "الْكِتَابُ",
      "error_type": "al_tanween_conflict",
      "explanation": "Remove tanween from definite noun"
    },
    {
      "original": "غُرْفَة",
      "corrected": "غُرْفَةٌ",
      "error_type": "missing_tanween",
      "explanation": "Indefinite noun (a room) needs tanween"
    }
  ]
}
```

**Explanation:** الْكِتَابُ is definite (the book), غُرْفَةٌ is indefinite (a room).

---

## Example Question 5 - Longer Sentence Advanced
**Question:** Fix all errors:

I see الْقَلَمٌ and كِتَاب and a طَاوِلَةُ.

**Correct Answer:**
```json
{
  "corrected_sentence": "I see الْقَلَمُ and كِتَابٌ and a طَاوِلَةٌ.",
  "corrections": [
    {
      "original": "الْقَلَمٌ",
      "corrected": "الْقَلَمُ",
      "error_type": "al_tanween_conflict",
      "explanation": "'The pen' has ال, remove tanween"
    },
    {
      "original": "كِتَاب",
      "corrected": "كِتَابٌ",
      "error_type": "missing_tanween",
      "explanation": "Indefinite 'a book' needs tanween"
    },
    {
      "original": "طَاوِلَةُ",
      "corrected": "طَاوِلَةٌ",
      "error_type": "wrong_vowel",
      "explanation": "'A table' is indefinite, needs tanween not just damma"
    }
  ]
}
```

**Explanation:** Three errors: ال+tanween conflict, missing tanween, wrong indefinite marking.

---

## Grading Criteria

**Correct if:**
- All errors identified
- All corrections are accurate
- Final sentence is grammatically correct
- No unnecessary changes to correct words

**Partial Credit:**
- Identify all errors but fix some incorrectly: 70%
- Miss one error but fix others correctly: 60-80% (depending on sentence length)
- Over-correct (change correct words): -10% per false positive

**Common Student Errors:**
- Fix obvious errors but miss subtle ones → Need more practice identifying all error types
- Change correct words → Overapplying rules, needs confidence building
- Correct one word type but not others → Focused on one rule, forgetting others

---

## Adaptive Difficulty

**Intermediate (Lesson 1):**
- 2-3 word sentences
- 1-2 errors per sentence
- Mix Arabic and English words
- Provide English translation

**Advanced (Lessons 2+):**
- 4-6 word sentences
- 2-3 errors per sentence
- All Arabic sentences
- English translation provided but test without it

**Expert:**
- Full paragraph (3-4 sentences)
- 4-6 errors across paragraph
- Arabic only
- No translation (infer from context)

---

## Agent 3 Implementation Notes

**When generating this exercise type:**

1. **Parse this template** to understand sentence patterns
2. **Pull vocabulary** from cached lesson content
3. **Construct sentence** with meaningful context
4. **Introduce errors** (1-3 per sentence)
5. **Ensure errors are fixable** (not ambiguous)
6. **Output JSON**:
```json
{
  "question": "Fix the errors in this sentence:",
  "sentence_with_errors": "The big كِتَابٌ is on the table.",
  "translation": "The big book is on the table.",
  "correct_sentence": "The big الْكِتَابُ is on the table.",
  "errors": [
    {
      "position": 2,
      "original": "كِتَابٌ",
      "corrected": "الْكِتَابُ",
      "error_type": "wrong_definiteness",
      "explanation": "'The book' is definite, needs ال"
    }
  ]
}
```

**Quality checks:**
- [ ] All Arabic includes proper harakaat
- [ ] Context clearly indicates correct form (definite/indefinite)
- [ ] Errors are realistic (common student mistakes)
- [ ] Not too many errors (overwhelming)
- [ ] Translation helps student understand context
- [ ] All vocabulary from current or previous lessons

---

## Pedagogical Notes

**Why this exercise works:**
- Tests application in context (not isolated rules)
- Builds reading skills (identifying errors while reading)
- Mimics real editing tasks
- Shows importance of context for definiteness

**What this reveals:**
- **Fixes ال errors but not tanween** → Prioritizing one rule over others
- **Doesn't use English context clues** → Not connecting translation to grammar
- **Changes correct words** → Lacks confidence, over-applies rules
- **Only fixes first error** → Not reading carefully enough

**Learning progression:**
1. **Mixed language sentences** (English + Arabic) - context obvious
2. **All Arabic with translation** - must connect translation to form
3. **All Arabic, no translation** - infer from sentence context
4. **Paragraph-level** - sustained attention, multiple sentences

**Real-world connection:**
- This mimics how students will use Arabic in writing
- Errors in context are harder to spot than isolated words
- Builds proofreading skills (checking own writing)
- Develops sensitivity to definiteness in natural language

**Common contexts to test:**

**Definite contexts (require ال):**
- "The X" (explicit article)
- "Look at X" (definite in context)
- "X is beautiful" (previously mentioned)

**Indefinite contexts (require tanween):**
- "A X" (explicit article)
- "I have X" (new information)
- "There is X" (introducing entity)

---

## Variations

**Error Type Focus:**
- Give all sentences with same error type (e.g., all ال + tanween conflicts)
- Builds pattern recognition for specific mistakes

**Progressive Reveal:**
- Show sentence word by word
- Student marks error as they see it
- Tests real-time reading comprehension

**Collaborative Editing:**
- Pair students
- Student A writes sentence, Student B finds errors
- Peer learning + writing practice

**Dictation + Correction:**
- Teacher says sentence with error
- Student writes what they hear
- Then identifies and corrects the error
- Tests listening, spelling, and error detection
