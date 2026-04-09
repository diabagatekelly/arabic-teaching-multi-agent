# Prompt Inventory - All LLM Generation Points

**Date:** 2026-04-09  
**Purpose:** Complete list of every point in the user flows where the LLM generates content

---

## Overview

This document traces through all interaction flows (INTERACTION_FLOWS.md) and identifies every prompt needed for the system to function.

**Total Prompts Needed:** 19

---

## Agent 1: Teaching/Presentation Agent (12 prompts)

### Vocabulary Teaching (6 prompts)

#### 1. Vocabulary Overview Introduction
**Flow:** 1A - Vocabulary Teaching - Batch Introduction  
**Function:** `present_vocab_intro()`  
**Mode:** `teaching_vocab`  
**Context:** User starts vocabulary section  
**Input:**
- `lesson_number`
- `total_words`
- `batches_count`

**Example Output:**
```
"Let's learn 10 words in 4 batches! Ready to start or skip to test?"
```

**Status:** ❌ Not yet implemented

---

#### 2. Vocabulary Batch Introduction
**Flow:** 1A - Vocabulary Teaching - Batch Introduction  
**Function:** `present_batch()`  
**Mode:** `teaching_vocab`  
**Context:** Show words in current batch  
**Input:**
- `lesson_number`
- `batch_number`
- `total_batches`
- `words` (list with arabic, transliteration, english)

**Example Output:**
```
"Let's learn Batch 1! Here are your first 3 words:

📝 كِتَاب (kitaab) - book
📝 مَدْرَسَة (madrasa) - school
📝 قَلَم (qalam) - pen

Take your time reviewing these. When you're ready, let's test your knowledge!"
```

**Status:** ✓ Implemented in baseline.py (lines 129-137)

---

#### 3. Vocabulary Quiz Question
**Flow:** 1B - Vocabulary Teaching - Batch Quiz  
**Function:** `ask_vocab_question()`  
**Mode:** `teaching_vocab`  
**Context:** Ask translation question during quiz  
**Input:**
- `word` (arabic)
- `transliteration`
- `question_type` ("arabic_to_english" or "english_to_arabic")

**Example Output:**
```
"What does كِتَاب mean?"
```

**Status:** ❌ Not yet implemented

---

#### 4. Vocabulary Quiz Feedback (Correct)
**Flow:** 1B - Vocabulary Teaching - Batch Quiz  
**Function:** `format_feedback(correct=True)`  
**Mode:** `feedback_vocab`  
**Context:** Student answered correctly  
**Input:**
- `word` (arabic)
- `transliteration`
- `english`
- `is_correct: True`

**Example Output:**
```
"Correct! ✓ كِتَاب = book. Great job!"
```

**Status:** ❌ Not yet implemented

---

#### 5. Vocabulary Quiz Feedback (Incorrect)
**Flow:** 1B - Vocabulary Teaching - Batch Quiz  
**Function:** `format_feedback(correct=False)`  
**Mode:** `feedback_vocab`  
**Context:** Student answered incorrectly  
**Input:**
- `word` (arabic)
- `transliteration`
- `english`
- `student_answer`
- `correct_answer`
- `is_correct: False`

**Example Output:**
```
"Not quite! The word مَدْرَسَة (madrasa) means 'school', not 'house'. Try to remember: madrasa = school."
```

**Status:** ❌ Not yet implemented

---

#### 6. Vocabulary Batch Quiz Summary
**Flow:** 1B - Vocabulary Teaching - Batch Quiz  
**Function:** `present_batch_quiz_results()`  
**Mode:** `teaching_vocab`  
**Context:** After completing batch quiz  
**Input:**
- `batch_number`
- `score` (e.g., "2/3")
- `words_correct` (list)
- `words_incorrect` (list with translations)

**Example Output:**
```
"That's it for the short quiz! You got 2/3 correct.

You missed: مَدْرَسَة (madrasa) = school

Ready for the next batch? You can also skip to the final test."
```

**Status:** ❌ Not yet implemented

---

### Grammar Teaching (6 prompts)

#### 7. Grammar Overview Introduction
**Flow:** 2A - Grammar Teaching - Topic Explanation  
**Function:** `present_grammar_intro()`  
**Mode:** `teaching_grammar`  
**Context:** User starts grammar section  
**Input:**
- `lesson_number`
- `topics` (list of topic names)
- `topics_count`

**Example Output:**
```
"I'll teach you 2 grammar topics:
1. Feminine Nouns
2. Definite Article

Each topic has a 5-question quiz. Ready to start?"
```

**Status:** ❌ Not yet implemented

---

#### 8. Grammar Topic Explanation
**Flow:** 2A - Grammar Teaching - Topic Explanation  
**Function:** `teach_grammar_topic()`  
**Mode:** `teaching_grammar`  
**Context:** Explain grammar rule with examples  
**Input:**
- `lesson_number`
- `topic_name`
- `grammar_rule` (description)
- `examples` (list with arabic, transliteration, english, correct/incorrect marker)
- `topics_remaining`

**Example Output:**
```
"Let's learn about Feminine Nouns! 🌟

**The Rule:**
In Arabic, most feminine nouns end with ة (taa marbuuta).

**Examples:**
- مَدْرَسَة (madrasa) - school ✓ (ends in ة)
- كِتَاب (kitaab) - book (masculine, no ة)

**Quick Check:** Look at the word بِنْت (bint - girl). Does it end in ة?"
```

**Status:** ❌ Not yet implemented

---

#### 9. Grammar Quiz Question
**Flow:** 2B - Grammar Teaching - Topic Quiz  
**Function:** `present_question()`  
**Mode:** `teaching_grammar`  
**Context:** Present grammar quiz question  
**Input:**
- `lesson_number`
- `topic_name`
- `question_number`
- `total_questions`
- `question` (text)

**Example Output:**
```
"Question 2 of 5: Is the word بَيْت (bayt - house) masculine or feminine?"
```

**Status:** ❌ Not yet implemented

---

#### 10. Grammar Quiz Feedback (Correct)
**Flow:** 2B - Grammar Teaching - Topic Quiz  
**Function:** `immediate_feedback(correct=True)`  
**Mode:** `feedback_grammar`  
**Context:** Student answered correctly  
**Input:**
- `question`
- `student_answer`
- `correct_answer`
- `explanation` (why it's correct)
- `is_correct: True`
- `current_score` (e.g., "2/2")

**Example Output:**
```
"Correct! ✓ بَيْت is masculine (no ة ending). You're doing great! (2/2 so far)"
```

**Status:** ❌ Not yet implemented

---

#### 11. Grammar Quiz Feedback (Incorrect)
**Flow:** 2B - Grammar Teaching - Topic Quiz  
**Function:** `immediate_feedback(correct=False)`  
**Mode:** `feedback_grammar`  
**Context:** Student answered incorrectly  
**Input:**
- `question`
- `student_answer`
- `correct_answer`
- `explanation` (why it's wrong)
- `is_correct: False`
- `current_score` (e.g., "1/2")

**Example Output:**
```
"Not quite. مَدْرَسَة is feminine because it ends in ة (taa marbuuta). The ة is the key indicator! (1/2 so far)"
```

**Status:** ❌ Not yet implemented

---

#### 12. Grammar Topic Quiz Summary
**Flow:** 2B - Grammar Teaching - Topic Quiz  
**Function:** `present_topic_quiz_results()`  
**Mode:** `teaching_grammar`  
**Context:** After completing topic quiz  
**Input:**
- `topic_name`
- `score` (e.g., "3/5")
- `weak_areas` (list of concepts to review)
- `pass_threshold: 4`

**Example Output (Score < 4/5):**
```
"You got 3 out of 5 correct.

You might want to review:
- Feminine noun markers (ة ending)
- Exceptions to the rule

Would you like to review and re-test, or move on to the next grammar topic?"
```

**Example Output (Score >= 4/5):**
```
"Great! 4/5 correct. You've got this! Ready for next topic?"
```

**Status:** ❌ Not yet implemented

---

## Agent 2: Grading Agent (4 prompts)

### Vocabulary Grading (2 prompts)

#### 13. Vocabulary Answer Grading
**Flow:** 1B - Vocabulary Teaching - Batch Quiz  
**Function:** `check_answer()`  
**Mode:** `grading_vocab`  
**Context:** Grade student's vocabulary translation  
**Input:**
- `word` (arabic)
- `student_answer`
- `correct_answer`

**Example Output:**
```json
{"correct": true}
```
or
```json
{"correct": false}
```

**Status:** ✓ Implemented in baseline.py (lines 179-189)

---

#### 14. Vocabulary Final Test Grading
**Flow:** 1C - Vocabulary Teaching - Final Test  
**Function:** `check_answer()`  
**Mode:** `grading_vocab`  
**Context:** Same as #13, but in final test context  
**Input:** Same as #13  
**Output:** Same as #13

**Status:** ✓ Same implementation as #13

---

### Grammar Grading (2 prompts)

#### 15. Grammar Quiz Answer Grading
**Flow:** 2B - Grammar Teaching - Topic Quiz  
**Function:** `check_answer()`  
**Mode:** `grading_grammar`  
**Context:** Grade student's grammar quiz answer  
**Input:**
- `lesson_number`
- `topic_name`
- `question`
- `student_answer`
- `correct_answer`
- `grammar_rules` (pre-loaded context)

**Example Output:**
```json
{"correct": true}
```
or
```json
{"correct": false}
```

**Status:** ❌ Not yet implemented

---

#### 16. Grammar Test Grading (Multiple Answers)
**Flow:** 4 - Test Mode  
**Function:** `grade_test()`  
**Mode:** `grading_grammar`  
**Context:** Grade full test with multiple grammar points  
**Input:**
- `lesson_number`
- `answers` (list of student answers with context)
- `grammar_rules` (all rules for lesson)

**Example Output:**
```json
{
  "total_score": "8/10",
  "results": [
    {"answer_id": "q1", "correct": true},
    {"answer_id": "q2", "correct": false, "expected": "..."},
    ...
  ],
  "weak_areas": ["definiteness_agreement"]
}
```

**Status:** ❌ Not yet implemented

---

## Agent 3: Content Retrieval & Generation (3 prompts)

### Exercise Generation (1 prompt)

#### 17. Exercise Generation
**Flow:** 3 - Exercise Mode  
**Function:** `generate_exercises()`  
**Mode:** `exercise_generation`  
**Context:** Generate practice exercises from template  
**Input:**
- `lesson_number`
- `exercise_type` (e.g., "fill_in_blank", "translation", "multiple_choice")
- `grammar_point` (focus area)
- `template` (structure)
- `primary_vocab` (current batch words)
- `all_vocab` (all lesson vocabulary)
- `count` (number of exercises, e.g., 5)

**Example Output:**
```json
[
  {
    "question": "Complete: كتاب ___",
    "answer": "كبير",
    "options": ["كبير", "كبيرة"],
    "explanation": "كتاب is masculine"
  },
  {
    "question": "Complete: مدرسة ___",
    "answer": "كبيرة",
    "options": ["كبير", "كبيرة"],
    "explanation": "مدرسة is feminine"
  },
  ...
]
```

**Status:** ❌ Not yet implemented

---

### Quiz Question Generation (2 prompts)

#### 18. Grammar Quiz Question Generation
**Flow:** 2B - Grammar Teaching - Topic Quiz  
**Function:** `generate_topic_quiz()`  
**Mode:** `exercise_generation` (or new mode `quiz_generation_grammar`?)  
**Context:** Generate 5 quiz questions for grammar topic  
**Input:**
- `lesson_number`
- `topic_name`
- `grammar_rule`
- `examples`
- `count: 5`

**Example Output:**
```json
[
  {
    "question": "Is 'مَدْرَسَة' masculine or feminine?",
    "answer": "feminine",
    "explanation": "مَدْرَسَة ends with ة so it's feminine"
  },
  {
    "question": "Is 'كِتَاب' masculine or feminine?",
    "answer": "masculine",
    "explanation": "كِتَاب has no ة ending"
  },
  ...
]
```

**Status:** ❌ Not yet implemented

---

#### 19. Test Composition (Mixed Grammar Points)
**Flow:** 4 - Test Mode  
**Function:** `compose_test()`  
**Mode:** `exercise_generation` (or new mode `test_generation`?)  
**Context:** Generate mixed test with multiple grammar points  
**Input:**
- `lesson_number`
- `grammar_points` (list of all topics in lesson)
- `question_count: 10`
- `question_types` (mix: fill-in-blank, correction, translation)

**Example Output:**
```json
{
  "test_id": "lesson_3_test",
  "total_questions": 10,
  "questions": [
    {
      "question_id": "q1",
      "type": "fill_in_blank",
      "question": "Complete: كتاب ___",
      "answer": "كبير",
      "grammar_point": "gender_agreement"
    },
    {
      "question_id": "q2",
      "type": "correction",
      "question": "Fix this: الكتاب كبيرة",
      "answer": "الكتاب الكبير",
      "grammar_point": "gender_agreement"
    },
    ...
  ]
}
```

**Status:** ❌ Not yet implemented

---

## Summary by Mode

| Mode | Prompts | Implemented | Missing |
|------|---------|-------------|---------|
| **teaching_vocab** | 4 | 1 | 3 |
| **teaching_grammar** | 4 | 0 | 4 |
| **feedback_vocab** | 2 | 0 | 2 |
| **feedback_grammar** | 2 | 0 | 2 |
| **grading_vocab** | 2 | 1 | 1 |
| **grading_grammar** | 2 | 0 | 2 |
| **exercise_generation** | 3 | 0 | 3 |
| **TOTAL** | **19** | **2** | **17** |

---

## Implementation Priority

### Phase 1: Core Teaching & Grading (Baseline Evaluation)
1. ✓ Vocabulary batch introduction (#2)
2. ✓ Vocabulary answer grading (#13)
3. Vocabulary quiz feedback - correct (#4)
4. Vocabulary quiz feedback - incorrect (#5)
5. Grammar topic explanation (#8)
6. Grammar quiz question (#9)
7. Grammar answer grading (#15)
8. Grammar quiz feedback - correct (#10)
9. Grammar quiz feedback - incorrect (#11)

**Purpose:** Enable baseline evaluation for teaching and grading modes

---

### Phase 2: Full User Flows
10. Vocabulary overview introduction (#1)
11. Vocabulary quiz question (#3)
12. Vocabulary batch quiz summary (#6)
13. Grammar overview introduction (#7)
14. Grammar topic quiz summary (#12)

**Purpose:** Complete vocabulary and grammar teaching flows

---

### Phase 3: Exercise Generation
15. Exercise generation (#17)
16. Grammar quiz question generation (#18)
17. Test composition (#19)
18. Grammar test grading (#16)

**Purpose:** Enable exercise mode and end-of-lesson tests

---

## Notes

- **Feedback prompts split:** User decided to split feedback into `feedback_vocab` and `feedback_grammar` because "the wording will be different"
- **Question generation:** Agent 3 generates quiz questions dynamically (not pre-stored), so we need generation prompts
- **Grading vs Teaching:** Agent 2 only returns JSON (`{"correct": bool}`), Agent 1 formats all user-facing text
- **Exercise generation:** Uses lightweight LLM (Agent 3) to generate variations from templates

---

## Next Steps

1. ✅ Create this inventory (complete)
2. ⏭️ Design each prompt template (PROMPT_DESIGN.md)
3. ⏭️ Validate test_cases.json covers all prompt types
4. ⏭️ Implement missing baseline methods
5. ⏭️ Create training data for fine-tuning

---

**See Also:**
- `PROMPT_DESIGN.md` - Detailed template design for each prompt
- `INTERACTION_FLOWS.md` - Visual diagrams of complete user flows
- `ARCHITECTURE.md` - Agent responsibilities and data flow
- `API_CONTRACT.md` - API endpoints and response formats
