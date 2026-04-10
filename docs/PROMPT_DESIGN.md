# Prompt Design Standards - Complete Templates

**Date:** 2026-04-09  
**Purpose:** Define all 20 prompt templates for fine-tuning and evaluation

---

## Overview

This document provides detailed templates for all 20 prompts needed for the Arabic Teaching Multi-Agent system.

**Total Prompts:** 21
- Agent 1 (Teaching): 14 prompts
- Agent 2 (Grading): 4 prompts  
- Agent 3 (Generation): 3 prompts

**Design Principle:** Prompts must be consistent across training, evaluation, and production.

---

## Mode Values

| Mode | Purpose | Agent | Count |
|------|---------|-------|-------|
| `lesson_start` | Welcome and lesson overview | Agent 1 | 1 |
| `teaching_vocab` | Introduce/present vocabulary | Agent 1 | 5 |
| `teaching_grammar` | Explain/present grammar | Agent 1 | 4 |
| `feedback_vocab` | Feedback on vocab answers | Agent 1 | 2 |
| `feedback_grammar` | Feedback on grammar answers | Agent 1 | 2 |
| `grading_vocab` | Grade vocabulary answers | Agent 2 | 2 |
| `grading_grammar` | Grade grammar answers | Agent 2 | 2 |
| `exercise_generation` | Generate exercises/quizzes | Agent 3 | 3 |

---

# Agent 1: Teaching/Presentation Agent (14 Prompts)

**Model:** Fine-tuned Qwen2.5-3B  
**Training Data:** These prompts will be used to create ~40 fine-tuning conversations  
**Purpose:** Learn encouraging, pedagogical presentation style

## Lesson Start (1 prompt)

### 1. Lesson Welcome/Greeting
**Priority:** Phase 2  
**Function:** `welcome_lesson()`  
**Mode:** `lesson_start`

**Purpose:** Greet student and present lesson overview with navigation options

**Required Input:**
- `mode`: "lesson_start"
- `lesson_number`: Integer
- `vocab_summary`: Object with:
  - `total_words`: Integer
  - `topics_preview`: List of strings (first few words to preview)
- `grammar_summary`: Object with:
  - `topics`: List of topic names
  - `topics_count`: Integer

**Prompt Template:**
```
Mode: lesson_start

Lesson {lesson_number} Overview

Vocabulary: {total_words} words
Preview: {word1}, {word2}, {word3}...

Grammar: {topics_count} topics
Topics: {topic1}, {topic2}...

Greet the student warmly and present the lesson structure. Offer navigation:
1. Start with vocabulary
2. Start with grammar
3. See lesson progress

Format with numbered options and mention they can request something else.
```

**Example:**
```
Mode: lesson_start

Lesson 3 Overview

Vocabulary: 10 words
Preview: كِتَاب (book), مَدْرَسَة (school), قَلَم (pen)...

Grammar: 2 topics
Topics: Feminine Nouns, Definite Article

Greet the student warmly and present the lesson structure. Offer navigation:
1. Start with vocabulary
2. Start with grammar
3. See lesson progress

Format with numbered options and mention they can request something else.
```

**Expected Output:**
```
"Welcome to Lesson 3! 🌟

Today you'll learn:
- **Vocabulary:** 10 new words (كِتَاب - book, مَدْرَسَة - school, قَلَم - pen, and more!)
- **Grammar:** 2 topics (Feminine Nouns and Definite Article)

Where would you like to start?
1. Start with vocabulary (10 words)
2. Start with grammar (2 topics)
3. See lesson progress

Or tell me what you'd like to do!"
```

**Evaluation:** SentimentMetric (threshold=0.9)

**Status:** ❌ Not implemented

---

## Vocabulary Teaching (7 prompts)

### 2. Vocabulary Overview Introduction
**Priority:** Phase 2  
**Function:** `present_vocab_intro()`  
**Mode:** `teaching_vocab`

**Purpose:** Welcome student to vocabulary section, show all words, explain options

**Required Input:**
- `mode`: "teaching_vocab"
- `lesson_number`: Integer
- `total_words`: Integer
- `batches_count`: Integer
- `words`: List of objects with:
  - `arabic`: String
  - `transliteration`: String
  - `english`: String

**Prompt Template:**
```
Mode: teaching_vocab

Lesson {lesson_number} - Vocabulary Overview

Words you'll learn:
1. {arabic} ({transliteration}) - {english}
2. {arabic} ({transliteration}) - {english}
...
{total_words}. {arabic} ({transliteration}) - {english}

These are divided into {batches_count} batches for easier learning.

Present all words and explain options:
1. Learn in batches (I'll teach each batch, then quiz you)
2. Skip to final test (test yourself on all {total_words} words now)

Format with numbered options and mention they can request something else.
```

**Example:**
```
Mode: teaching_vocab

Lesson 1 - Vocabulary Overview

Words you'll learn:
1. مرحبا (marhaba) - hello
2. شكرا (shukran) - thank you
3. وداعا (wada'an) - goodbye
4. نعم (naam) - yes
5. لا (laa) - no
6. كِتَاب (kitaab) - book
7. مَدْرَسَة (madrasa) - school
8. قَلَم (qalam) - pen
9. طَالِب (taalib) - student
10. مُعَلِّم (muallim) - teacher

These are divided into 4 batches for easier learning.

Present all words and explain options:
1. Learn in batches (I'll teach each batch, then quiz you)
2. Skip to final test (test yourself on all 10 words now)

Format with numbered options and mention they can request something else.
```

**Expected Output:**
```
"Welcome to Lesson 1 Vocabulary! Here are all 10 words you'll learn:

1. مرحبا (marhaba) - hello
2. شكرا (shukran) - thank you
3. وداعا (wada'an) - goodbye
4. نعم (naam) - yes
5. لا (laa) - no
6. كِتَاب (kitaab) - book
7. مَدْرَسَة (madrasa) - school
8. قَلَم (qalam) - pen
9. طَالِب (taalib) - student
10. مُعَلِّم (muallim) - teacher

I've divided these into 4 small batches to make learning easier.

What would you like to do?
1. Learn in batches (I'll teach each batch, then quiz you)
2. Skip to final test (test yourself on all 10 words now)

Or tell me what you'd like to do."
```

**Evaluation:** SentimentMetric (threshold=0.9)

**Status:** ❌ Not implemented

---

### 2. Vocabulary Batch Introduction
**Priority:** Phase 1 ✓  
**Function:** `present_batch()`  
**Mode:** `teaching_vocab`

**Purpose:** Present words in current batch to student

**Required Input:**
- `mode`: "teaching_vocab"
- `lesson_number`: Integer
- `batch_number`: Integer
- `total_batches`: Integer
- `words`: List of objects with:
  - `arabic`: String
  - `transliteration`: String
  - `english`: String

**Prompt Template:**
```
Mode: teaching_vocab

Lesson {lesson_number}, Batch {batch_number} of {total_batches}

Words to teach:
- {arabic} ({transliteration}) - {english}
- {arabic} ({transliteration}) - {english}
...

Present these words encouragingly. Remind them flashcards are available for learning. Then offer:
1. Take quiz on this batch
2. Go to next batch
3. See all words

Format with numbered options and mention they can request something else (like going to final test).
```

**Example:**
```
Mode: teaching_vocab

Lesson 1, Batch 1 of 3

Words to teach:
- مرحبا (marhaba) - hello
- شكرا (shukran) - thank you
- وداعا (wada'an) - goodbye

Present these words encouragingly. Remind them flashcards are available for learning. Then offer:
1. Take quiz on this batch
2. Go to next batch
3. See all words

Format with numbered options and mention they can request something else (like going to final test).
```

**Expected Output:**
```
"Let's learn Batch 1! Here are your first 3 words:

📝 مرحبا (marhaba) - hello
📝 شكرا (shukran) - thank you  
📝 وداعا (wada'an) - goodbye

Take your time learning with the flashcards!

What would you like to do next?
1. Take quiz on Batch 1
2. Go to Batch 2
3. See all 10 words

Or tell me what you'd like to do."
```

**Evaluation:** SentimentMetric (threshold=0.9)

**Status:** ✓ Implemented in `baseline.py` (lines 129-137) - **Needs update for flashcards mention and new navigation options**

---

### 4. Vocabulary List View
**Priority:** Phase 2  
**Function:** `show_all_vocab_words()`  
**Mode:** `teaching_vocab`

**Purpose:** Show all vocab words in current lesson with navigation back or to test

**Required Input:**
- `mode`: "teaching_vocab"
- `lesson_number`: Integer
- `words`: List of objects with:
  - `arabic`: String
  - `transliteration`: String
  - `english`: String
- `current_batch`: Integer
- `total_batches`: Integer

**Prompt Template:**
```
Mode: teaching_vocab

Lesson {lesson_number} - All Vocabulary Words

Words in this lesson:
1. {arabic} ({transliteration}) - {english}
2. {arabic} ({transliteration}) - {english}
...

Current progress: Batch {current_batch} of {total_batches}

Present all words and offer navigation:
1. Back to Batch {current_batch}
2. Skip to final test

Format with numbered options and mention they can request something else.
```

**Example:**
```
Mode: teaching_vocab

Lesson 1 - All Vocabulary Words

Words in this lesson:
1. مرحبا (marhaba) - hello
2. شكرا (shukran) - thank you
3. وداعا (wada'an) - goodbye
4. نعم (naam) - yes
5. لا (laa) - no
6. كِتَاب (kitaab) - book
7. مَدْرَسَة (madrasa) - school
8. قَلَم (qalam) - pen
9. طَالِب (taalib) - student
10. مُعَلِّم (muallim) - teacher

Current progress: Batch 2 of 4

Present all words and offer navigation:
1. Back to Batch 2
2. Skip to final test

Format with numbered options and mention they can request something else.
```

**Expected Output:**
```
"Here are all 10 vocabulary words for Lesson 1:

1. مرحبا (marhaba) - hello
2. شكرا (shukran) - thank you
3. وداعا (wada'an) - goodbye
4. نعم (naam) - yes
5. لا (laa) - no
6. كِتَاب (kitaab) - book
7. مَدْرَسَة (madrasa) - school
8. قَلَم (qalam) - pen
9. طَالِب (taalib) - student
10. مُعَلِّم (muallim) - teacher

You're currently on Batch 2 of 4.

What would you like to do?
1. Back to Batch 2
2. Skip to final test

Or tell me what you'd like to do."
```

**Evaluation:** SentimentMetric (threshold=0.8)

**Status:** ❌ Not implemented

---

### 5. Vocabulary Quiz Question
**Priority:** Phase 2  
**Function:** `ask_vocab_question()`  
**Mode:** `teaching_vocab`

**Purpose:** Ask translation question during quiz

**Required Input:**
- `mode`: "teaching_vocab"
- `word_arabic`: String
- `word_transliteration`: String
- `question_type`: "arabic_to_english" or "english_to_arabic"

**Prompt Template (Arabic → English):**
```
Mode: teaching_vocab

Quiz Question

Word: {word_arabic} ({word_transliteration})
Question type: Translate from Arabic to English

Ask the student what this word means:
```

**Prompt Template (English → Arabic):**
```
Mode: teaching_vocab

Quiz Question

English word: {english}
Question type: Translate from English to Arabic

Ask the student to provide the Arabic word:
```

**Example:**
```
Mode: teaching_vocab

Quiz Question

Word: كِتَاب (kitaab)
Question type: Translate from Arabic to English

Ask the student what this word means:
```

**Expected Output:**
```
"What does كِتَاب mean?"
```

**Evaluation:** Not directly evaluated (part of user flow)

**Status:** ❌ Not implemented

---

### 6. Vocabulary Quiz Feedback (Correct)
**Priority:** Phase 1 ✓  
**Function:** `format_feedback(correct=True)`  
**Mode:** `feedback_vocab`

**Purpose:** Provide encouraging feedback when student answers correctly

**Required Input:**
- `mode`: "feedback_vocab"
- `word_arabic`: String
- `word_transliteration`: String
- `word_english`: String
- `student_answer`: String
- `is_correct`: true

**Prompt Template:**
```
Mode: feedback_vocab

Question: What does "{word_arabic}" mean?
Student Answer: {student_answer}
Correct Answer: {word_english}
Result: Correct

Provide brief, encouraging feedback:
```

**Example:**
```
Mode: feedback_vocab

Question: What does "كِتَاب" mean?
Student Answer: book
Correct Answer: book
Result: Correct

Provide brief, encouraging feedback:
```

**Expected Output:**
```
"Correct! ✓ كِتَاب = book. Great job!"
```

**Evaluation:** SentimentMetric (threshold=0.8)

**Status:** ❌ Not implemented

---

### 7. Vocabulary Quiz Feedback (Incorrect)
**Priority:** Phase 1 ✓  
**Function:** `format_feedback(correct=False)`  
**Mode:** `feedback_vocab`

**Purpose:** Provide supportive correction when student answers incorrectly

**Required Input:**
- `mode`: "feedback_vocab"
- `word_arabic`: String
- `word_transliteration`: String
- `word_english`: String (correct answer)
- `student_answer`: String (what they said)
- `is_correct`: false

**Prompt Template:**
```
Mode: feedback_vocab

Question: What does "{word_arabic}" mean?
Student Answer: {student_answer}
Correct Answer: {word_english}
Result: Incorrect

Provide supportive feedback with the correction:
```

**Example:**
```
Mode: feedback_vocab

Question: What does "مَدْرَسَة" mean?
Student Answer: house
Correct Answer: school
Result: Incorrect

Provide supportive feedback with the correction:
```

**Expected Output:**
```
"Not quite! The word مَدْرَسَة (madrasa) means 'school', not 'house'. Try to remember: madrasa = school."
```

**Evaluation:** SentimentMetric (threshold=0.7)

**Status:** ❌ Not implemented

---

### 8. Vocabulary Batch Quiz Summary
**Priority:** Phase 2  
**Function:** `present_batch_quiz_results()`  
**Mode:** `teaching_vocab`

**Purpose:** Summarize batch quiz results and guide next steps

**Required Input:**
- `mode`: "teaching_vocab"
- `batch_number`: Integer
- `score`: String (e.g., "2/3")
- `total_questions`: Integer
- `correct_count`: Integer
- `words_missed`: List of objects with:
  - `arabic`: String
  - `transliteration`: String
  - `english`: String

**Prompt Template:**
```
Mode: teaching_vocab

Batch {batch_number} Quiz Complete

Score: {score}
Correct: {correct_count} out of {total_questions}

Words you missed:
- {arabic} ({transliteration}) = {english}
...

Summarize results and suggest next steps with numbered options. Mention they can request something else.
```

**Example:**
```
Mode: teaching_vocab

Batch 1 Quiz Complete

Score: 2/3
Correct: 2 out of 3

Words you missed:
- مَدْرَسَة (madrasa) = school

Summarize results and suggest next steps with numbered options. Mention they can request something else.
```

**Expected Output:**
```
"Nice work! You got 2 out of 3 correct on Batch 1.

You missed: مَدْرَسَة (madrasa) = school

What would you like to do?
1. Move to Batch 2
2. Skip to final vocabulary test
3. See all 10 words

Or tell me what you'd like to do."
```

**Evaluation:** SentimentMetric (threshold=0.8)

**Status:** ❌ Not implemented

---

## Grammar Teaching (6 prompts)

### 9. Grammar Overview Introduction
**Priority:** Phase 2  
**Function:** `present_grammar_intro()`  
**Mode:** `teaching_grammar`

**Purpose:** Welcome student to grammar section and preview topics

**Required Input:**
- `mode`: "teaching_grammar"
- `lesson_number`: Integer
- `topics`: List of topic names (strings)
- `topics_count`: Integer

**Prompt Template:**
```
Mode: teaching_grammar

Lesson {lesson_number} - Grammar Overview

Topics to cover: {topics_count}
1. {topic_1}
2. {topic_2}
...

Welcome the student to the grammar section with numbered options:
1. Start with first topic
2. Skip to grammar test (if available)

Mention they can request something else.
```

**Example:**
```
Mode: teaching_grammar

Lesson 3 - Grammar Overview

Topics to cover: 2
1. Feminine Nouns
2. Definite Article

Welcome the student to the grammar section with numbered options:
1. Start with first topic
2. Skip to grammar test (if available)

Mention they can request something else.
```

**Expected Output:**
```
"Let's learn some grammar for Lesson 3! I'll teach you 2 important topics:
1. Feminine Nouns
2. Definite Article

Each topic includes an explanation with examples, followed by a 5-question quiz.

What would you like to do?
1. Start with Feminine Nouns
2. Skip to grammar test (after learning all topics)

Or tell me what you'd like to do."
```

**Evaluation:** SentimentMetric (threshold=0.9)

**Status:** ❌ Not implemented

---

### 10. Grammar Topic Explanation
**Priority:** Phase 1 ✓  
**Function:** `teach_grammar_topic()`  
**Mode:** `teaching_grammar`

**Purpose:** Explain grammar rule with examples

**Required Input:**
- `mode`: "teaching_grammar"
- `lesson_number`: Integer
- `topic_name`: String
- `grammar_rule`: String (rule description)
- `examples`: List of objects with:
  - `arabic`: String
  - `transliteration`: String
  - `english`: String
  - `note`: String (why this example demonstrates the rule)

**Prompt Template:**
```
Mode: teaching_grammar

Lesson {lesson_number}

Topic: {topic_name}

Rule: {grammar_rule}

Examples:
- {arabic} ({transliteration}) - {english}
  Note: {note}
- {arabic} ({transliteration}) - {english}
  Note: {note}
...

Explain this grammar topic to the student in an encouraging way. End by mentioning the quiz is next.
```

**Example:**
```
Mode: teaching_grammar

Lesson 3

Topic: Feminine Nouns

Rule: In Arabic, most feminine nouns end with ة (taa marbuuta)

Examples:
- مَدْرَسَة (madrasa) - school
  Note: Ends with ة so it's feminine
- طَاوِلَة (taawila) - table
  Note: Ends with ة so it's feminine
- كِتَاب (kitaab) - book
  Note: No ة ending, so it's masculine (not feminine)

Explain this grammar topic to the student in an encouraging way. End by mentioning the quiz is next.
```

**Expected Output:**
```
"Let's learn about Feminine Nouns! 🌟

**The Rule:**
In Arabic, most feminine nouns end with ة (taa marbuuta).

**Examples:**
- مَدْرَسَة (madrasa) - school ✓ (ends in ة)
- طَاوِلَة (taawila) - table ✓ (ends in ة)
- كِتَاب (kitaab) - book (masculine, no ة)

**Quick Check:** Look at the word بِنْت (bint - girl). Does it end in ة?

Now let's test your understanding with a 5-question quiz!"
```

**Evaluation:** SentimentMetric (threshold=0.9)

**Status:** ❌ Not implemented

---

### 11. Grammar Quiz Question
**Priority:** Phase 1 ✓  
**Function:** `present_question()`  
**Mode:** `teaching_grammar`

**Purpose:** Present grammar quiz question to student

**Required Input:**
- `mode`: "teaching_grammar"
- `lesson_number`: Integer
- `topic_name`: String
- `question_number`: Integer
- `total_questions`: Integer (typically 5)
- `question`: String (the actual question text)

**Prompt Template:**
```
Mode: teaching_grammar

Lesson {lesson_number} - {topic_name} Quiz

Question {question_number} of {total_questions}:
{question}

Present this question to the student:
```

**Example:**
```
Mode: teaching_grammar

Lesson 3 - Feminine Nouns Quiz

Question 2 of 5:
Is the word بَيْت (bayt - house) masculine or feminine?

Present this question to the student:
```

**Expected Output:**
```
"Question 2 of 5: Is the word بَيْت (bayt - house) masculine or feminine?"
```

**Evaluation:** Not directly evaluated (part of user flow)

**Status:** ❌ Not implemented

---

### 12. Grammar Quiz Feedback (Correct)
**Priority:** Phase 1 ✓  
**Function:** `immediate_feedback(correct=True)`  
**Mode:** `feedback_grammar`

**Purpose:** Provide encouraging feedback with explanation when correct

**Required Input:**
- `mode`: "feedback_grammar"
- `question`: String
- `student_answer`: String
- `correct_answer`: String
- `explanation`: String (why this answer is correct)
- `is_correct`: true
- `current_score`: String (e.g., "2/2")

**Prompt Template:**
```
Mode: feedback_grammar

Question: {question}
Student Answer: {student_answer}
Correct Answer: {correct_answer}
Explanation: {explanation}
Result: Correct
Current score: {current_score}

Provide brief, encouraging feedback with the explanation:
```

**Example:**
```
Mode: feedback_grammar

Question: Is the word بَيْت (bayt - house) masculine or feminine?
Student Answer: masculine
Correct Answer: masculine
Explanation: بَيْت has no ة ending, so it's masculine
Result: Correct
Current score: 2/2

Provide brief, encouraging feedback with the explanation:
```

**Expected Output:**
```
"Correct! ✓ بَيْت is masculine (no ة ending). You're doing great! (2/2 so far)"
```

**Evaluation:** SentimentMetric (threshold=0.8)

**Status:** ❌ Not implemented

---

### 13. Grammar Quiz Feedback (Incorrect)
**Priority:** Phase 1 ✓  
**Function:** `immediate_feedback(correct=False)`  
**Mode:** `feedback_grammar`

**Purpose:** Provide supportive correction with explanation

**Required Input:**
- `mode`: "feedback_grammar"
- `question`: String
- `student_answer`: String
- `correct_answer`: String
- `explanation`: String (why student's answer was wrong)
- `is_correct`: false
- `current_score`: String (e.g., "1/2")

**Prompt Template:**
```
Mode: feedback_grammar

Question: {question}
Student Answer: {student_answer}
Correct Answer: {correct_answer}
Explanation: {explanation}
Result: Incorrect
Current score: {current_score}

Provide supportive feedback with the explanation:
```

**Example:**
```
Mode: feedback_grammar

Question: Is the word مَدْرَسَة (madrasa - school) masculine or feminine?
Student Answer: masculine
Correct Answer: feminine
Explanation: مَدْرَسَة ends with ة (taa marbuuta), which makes it feminine
Result: Incorrect
Current score: 1/2

Provide supportive feedback with the explanation:
```

**Expected Output:**
```
"Not quite. مَدْرَسَة is feminine because it ends in ة (taa marbuuta). The ة is the key indicator! (1/2 so far)"
```

**Evaluation:** SentimentMetric (threshold=0.7)

**Status:** ❌ Not implemented

---

### 14. Grammar Topic Quiz Summary
**Priority:** Phase 2  
**Function:** `present_topic_quiz_results()`  
**Mode:** `teaching_grammar`

**Purpose:** Summarize topic quiz results and suggest review if needed

**Required Input:**
- `mode`: "teaching_grammar"
- `topic_name`: String
- `score`: String (e.g., "3/5")
- `correct_count`: Integer
- `total_questions`: Integer
- `pass_threshold`: Integer (typically 4)
- `weak_areas`: List of strings (concepts needing review)

**Prompt Template:**
```
Mode: teaching_grammar

{topic_name} Quiz Complete

Score: {score}
Correct: {correct_count} out of {total_questions}
Pass threshold: {pass_threshold}

Weak areas identified:
- {weak_area_1}
- {weak_area_2}
...

Summarize results and suggest next steps with numbered options. Mention they can request something else.
```

**Example (Below threshold):**
```
Mode: teaching_grammar

Feminine Nouns Quiz Complete

Score: 3/5
Correct: 3 out of 5
Pass threshold: 4

Weak areas identified:
- Feminine noun markers (ة ending)
- Exceptions to the rule

Summarize results and suggest next steps with numbered options. Mention they can request something else.
```

**Expected Output (Below threshold):**
```
"You got 3 out of 5 correct.

You might want to review:
- Feminine noun markers (ة ending)
- Exceptions to the rule

What would you like to do?
1. Review and re-test this topic
2. Move to next grammar topic
3. Skip to grammar test

Or tell me what you'd like to do."
```

**Example (Passed):**
```
Mode: teaching_grammar

Feminine Nouns Quiz Complete

Score: 4/5
Correct: 4 out of 5
Pass threshold: 4

Weak areas identified: None

Summarize results and suggest next steps with numbered options. Mention they can request something else.
```

**Expected Output (Passed):**
```
"Great work! You got 4 out of 5 correct. You've mastered Feminine Nouns!

What would you like to do?
1. Move to next grammar topic (Definite Article)
2. Skip to grammar test

Or tell me what you'd like to do."
```

**Evaluation:** SentimentMetric (threshold=0.8)

**Status:** ❌ Not implemented

---

# Agent 2: Grading Agent (4 Prompts)

**Model:** Base Qwen2.5-7B (not fine-tuned initially)  
**Strategy:** Use detailed prompts with flexibility instructions  
**Rationale:** Better reasoning for semantic comparison (typos, synonyms, abbreviations)  
**Note:** Will fine-tune only if baseline evaluation shows accuracy <90%

These prompts are designed to be self-contained - all grading instructions included in the prompt itself.

## Vocabulary Grading (2 prompts)

### 15. Vocabulary Answer Grading (Quiz)
**Priority:** Phase 1 ✓  
**Function:** `check_answer()`  
**Mode:** `grading_vocab`

**Purpose:** Grade student's vocabulary translation answer

**Required Input:**
- `mode`: "grading_vocab"
- `word`: String (Arabic word)
- `student_answer`: String
- `correct_answer`: String

**Prompt Template:**
```
Mode: grading_vocab

Question: What does "{word}" mean?
Student Answer: "{student_answer}"
Correct Answer: "{correct_answer}"

Evaluate if the student's answer is correct. Be flexible:
- Accept minor typos (e.g., "scool" for "school")
- Accept synonyms (e.g., "instructor" for "teacher")
- Accept alternate phrasings that convey the same meaning

Return JSON:
{"correct": true} or {"correct": false}

Response:
```

**Example:**
```
Mode: grading_vocab

Question: What does "كِتَاب" mean?
Student Answer: "book"
Correct Answer: "book"

Evaluate if the student's answer is correct. Be flexible:
- Accept minor typos (e.g., "scool" for "school")
- Accept synonyms (e.g., "instructor" for "teacher")
- Accept alternate phrasings that convey the same meaning

Return JSON:
{"correct": true} or {"correct": false}

Response:
```

**Expected Output:**
```json
{"correct": true}
```

**Evaluation:** JSONValidityMetric → StructureMetric → AccuracyMetric

**Status:** ✓ Implemented in `baseline.py` (lines 179-189)

---

### 16. Vocabulary Answer Grading (Final Test)
**Priority:** Phase 1 ✓  
**Function:** `check_answer()` (same as #15)  
**Mode:** `grading_vocab`

**Purpose:** Grade vocabulary answer in final test context

**Note:** Uses identical prompt template as #15. The only difference is context (batch quiz vs final test), but the grading logic is the same.

**Status:** ✓ Same implementation as #15

---

## Grammar Grading (2 prompts)

### 17. Grammar Quiz Answer Grading
**Priority:** Phase 1 ✓  
**Function:** `check_answer()`  
**Mode:** `grading_grammar`

**Purpose:** Grade student's grammar quiz answer

**Required Input:**
- `mode`: "grading_grammar"
- `question`: String
- `student_answer`: String
- `correct_answer`: String

**Prompt Template:**
```
Mode: grading_grammar

Question: {question}
Student Answer: "{student_answer}"
Correct Answer: "{correct_answer}"

Evaluate if the student's answer is correct. Be flexible:
- Accept minor typos
- Accept synonyms or alternate phrasings that convey the same meaning
- For identification questions (masculine/feminine), accept abbreviated forms (m/f, masc/fem)

Return JSON:
{"correct": true} or {"correct": false}

Response:
```

**Example:**
```
Mode: grading_grammar

Question: Is the word مَدْرَسَة masculine or feminine?
Student Answer: "feminine"
Correct Answer: "feminine"

Evaluate if the student's answer is correct. Be flexible:
- Accept minor typos
- Accept synonyms or alternate phrasings that convey the same meaning
- For identification questions (masculine/feminine), accept abbreviated forms (m/f, masc/fem)

Return JSON:
{"correct": true} or {"correct": false}

Response:
```

**Expected Output:**
```json
{"correct": true}
```

**Evaluation:** JSONValidityMetric → StructureMetric → AccuracyMetric

**Status:** ❌ Not implemented

---

### 18. Grammar Test Grading (Multiple Answers)
**Priority:** Phase 3  
**Function:** `grade_test()`  
**Mode:** `grading_grammar`

**Purpose:** Grade full test with multiple questions at once

**Required Input:**
- `mode`: "grading_grammar"
- `lesson_number`: Integer
- `answers`: List of objects with:
  - `question_id`: String
  - `question`: String
  - `student_answer`: String
  - `correct_answer`: String

**Prompt Template:**
```
Mode: grading_grammar

Lesson {lesson_number} - Final Test Grading

Grade the following answers:

Question 1 (ID: {question_id}):
Q: {question}
Student: "{student_answer}"
Correct: "{correct_answer}"

Question 2 (ID: {question_id}):
Q: {question}
Student: "{student_answer}"
Correct: "{correct_answer}"

...

Return JSON with results for each question:
{
  "total_score": "X/Y",
  "results": [
    {"question_id": "...", "correct": true/false},
    ...
  ]
}

Response:
```

**Example:**
```
Mode: grading_grammar

Lesson 3 - Final Test Grading

Grade the following answers:

Question 1 (ID: q1):
Q: Is مَدْرَسَة masculine or feminine?
Student: "feminine"
Correct: "feminine"

Question 2 (ID: q2):
Q: Is كِتَاب masculine or feminine?
Student: "feminine"
Correct: "masculine"

Return JSON with results for each question:
{
  "total_score": "X/Y",
  "results": [
    {"question_id": "...", "correct": true/false},
    ...
  ]
}

Response:
```

**Expected Output:**
```json
{
  "total_score": "1/2",
  "results": [
    {"question_id": "q1", "correct": true},
    {"question_id": "q2", "correct": false}
  ]
}
```

**Evaluation:** JSONValidityMetric → StructureMetric (custom for test results)

**Status:** ❌ Not implemented

---

# Agent 3: Content Retrieval & Generation (3 Prompts)

**Model:** Base Qwen2.5-3B (not fine-tuned initially)  
**Strategy:** Use prompts with templates and cached vocabulary  
**Rationale:** Exercise generation is straightforward, prompting should be sufficient  
**Note:** Will fine-tune only if exercise quality needs improvement

### 19. Exercise Generation
**Priority:** Phase 3  
**Function:** `generate_exercises()`  
**Mode:** `exercise_generation`

**Purpose:** Generate practice exercises from learned content

**Required Input:**
- `mode`: "exercise_generation"
- `lesson_number`: Integer
- `exercise_type`: String ("fill_in_blank", "translation", "multiple_choice")
- `content_type`: String ("vocabulary" or "grammar")
- `count`: Integer (number of exercises to generate)
- `learned_items`: List of strings (words or concepts)

**Prompt Template:**
```
Mode: exercise_generation

Lesson {lesson_number}
Type: {exercise_type}
Content: {content_type}
Count: {count}

Learned items:
- {item_1}
- {item_2}
...

Generate {count} practice exercises. Return JSON list:
[
  {
    "question": "question text here",
    "answer": "correct answer here"
  },
  ...
]

Response:
```

**Example:**
```
Mode: exercise_generation

Lesson 1
Type: translation
Content: vocabulary
Count: 5

Learned items:
- مرحبا (marhaba) - hello
- شكرا (shukran) - thank you
- وداعا (wada'an) - goodbye

Generate 5 practice exercises. Return JSON list:
[
  {
    "question": "question text here",
    "answer": "correct answer here"
  },
  ...
]

Response:
```

**Expected Output:**
```json
[
  {
    "question": "What does 'مرحبا' mean?",
    "answer": "hello"
  },
  {
    "question": "How do you say 'thank you' in Arabic?",
    "answer": "شكرا"
  },
  {
    "question": "Translate: goodbye",
    "answer": "وداعا"
  },
  {
    "question": "What does 'شكرا' mean?",
    "answer": "thank you"
  },
  {
    "question": "How do you say 'hello' in Arabic?",
    "answer": "مرحبا"
  }
]
```

**Evaluation:** JSONValidityMetric → StructureMetric

**Status:** ❌ Not implemented

---

### 20. Grammar Quiz Question Generation
**Priority:** Phase 3  
**Function:** `generate_topic_quiz()`  
**Mode:** `exercise_generation`

**Purpose:** Generate 5 quiz questions for a grammar topic

**Required Input:**
- `mode`: "exercise_generation"
- `lesson_number`: Integer
- `topic_name`: String
- `grammar_rule`: String
- `examples`: List of objects with arabic, transliteration, english
- `count`: Integer (always 5 for topic quizzes)

**Prompt Template:**
```
Mode: exercise_generation

Lesson {lesson_number} - {topic_name} Quiz Generation

Grammar Rule: {grammar_rule}

Examples:
- {arabic} ({transliteration}) - {english}
- {arabic} ({transliteration}) - {english}
...

Generate {count} quiz questions to test understanding of this rule. Return JSON list:
[
  {
    "question": "question text",
    "answer": "correct answer",
    "explanation": "why this is the answer"
  },
  ...
]

Response:
```

**Example:**
```
Mode: exercise_generation

Lesson 3 - Feminine Nouns Quiz Generation

Grammar Rule: In Arabic, most feminine nouns end with ة (taa marbuuta)

Examples:
- مَدْرَسَة (madrasa) - school
- طَاوِلَة (taawila) - table
- كِتَاب (kitaab) - book

Generate 5 quiz questions to test understanding of this rule. Return JSON list:
[
  {
    "question": "question text",
    "answer": "correct answer",
    "explanation": "why this is the answer"
  },
  ...
]

Response:
```

**Expected Output:**
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
  {
    "question": "Is 'طَاوِلَة' masculine or feminine?",
    "answer": "feminine",
    "explanation": "طَاوِلَة ends with ة so it's feminine"
  },
  {
    "question": "Does the word 'بَيْت' look masculine or feminine?",
    "answer": "masculine",
    "explanation": "No ة ending indicates masculine"
  },
  {
    "question": "What marker indicates a feminine noun in Arabic?",
    "answer": "ة (taa marbuuta)",
    "explanation": "The ة ending is the primary feminine marker"
  }
]
```

**Evaluation:** JSONValidityMetric → StructureMetric

**Status:** ❌ Not implemented

---

### 21. Test Composition (Mixed Grammar Points)
**Priority:** Phase 3  
**Function:** `compose_test()`  
**Mode:** `exercise_generation`

**Purpose:** Generate comprehensive test with multiple grammar topics

**Required Input:**
- `mode`: "exercise_generation"
- `lesson_number`: Integer
- `grammar_topics`: List of topic names
- `question_count`: Integer (typically 10)
- `question_types`: List of types ("fill_in_blank", "correction", "translation")

**Prompt Template:**
```
Mode: exercise_generation

Lesson {lesson_number} - Final Test Composition

Grammar topics to cover:
- {topic_1}
- {topic_2}
...

Question count: {question_count}
Question types: {question_types}

Generate a mixed test covering all topics. Return JSON:
{
  "test_id": "lesson_{lesson_number}_test",
  "total_questions": {question_count},
  "questions": [
    {
      "question_id": "q1",
      "type": "...",
      "question": "...",
      "answer": "...",
      "grammar_topic": "..."
    },
    ...
  ]
}

Response:
```

**Example:**
```
Mode: exercise_generation

Lesson 3 - Final Test Composition

Grammar topics to cover:
- Feminine Nouns
- Definite Article

Question count: 10
Question types: ["fill_in_blank", "identification", "translation"]

Generate a mixed test covering all topics. Return JSON:
{
  "test_id": "lesson_3_test",
  "total_questions": 10,
  "questions": [
    {
      "question_id": "q1",
      "type": "...",
      "question": "...",
      "answer": "...",
      "grammar_topic": "..."
    },
    ...
  ]
}

Response:
```

**Expected Output:**
```json
{
  "test_id": "lesson_3_test",
  "total_questions": 10,
  "questions": [
    {
      "question_id": "q1",
      "type": "identification",
      "question": "Is مَدْرَسَة masculine or feminine?",
      "answer": "feminine",
      "grammar_topic": "Feminine Nouns"
    },
    {
      "question_id": "q2",
      "type": "translation",
      "question": "Translate: the big school",
      "answer": "المَدْرَسَة الكَبِيرَة",
      "grammar_topic": "Definite Article"
    }
  ]
}
```

**Evaluation:** JSONValidityMetric → StructureMetric (custom for test structure)

**Status:** ❌ Not implemented

---

# Design Principles

### 1. Mode Field Always First
Every prompt starts with `Mode: {mode_value}` to clearly identify the agent's role.

### 2. Structured Input Section
Present all input data in a clear, structured format before the instruction.

### 3. Explicit Instruction
End with a clear, imperative instruction:
- Teaching: "Present these words..." / "Explain this concept..."
- Feedback: "Provide encouraging feedback..." / "Provide supportive feedback..."
- Grading: "Evaluate if..." / "Return JSON..."
- Generation: "Generate X exercises..." / "Return JSON list..."

### 4. JSON Output Format Specification
For grading and generation, explicitly show the expected JSON structure in the prompt.

### 5. Consistent Field Naming
- `lesson_number` (not `lesson_id` or `lesson`)
- `student_answer` (not `answer` or `response`)
- `correct_answer` (not `expected` or `solution`)
- `question_id` (not `id` or `q_id`)

### 6. Encouraging Language for Teaching
Teaching/feedback prompts end with "in an encouraging way" to prime the model for positive sentiment.

### 7. Arabic Text with Transliteration in Teaching Mode
**Always** provide Arabic alongside transliteration in all teaching modes (`lesson_start`, `teaching_vocab`, `teaching_grammar`, `feedback_vocab`, `feedback_grammar`). This applies to:
- Word presentations
- Examples in grammar explanations
- Feedback on student answers
- Any time Arabic text appears in teaching context

Format: `{arabic} ({transliteration})` or `{arabic} ({transliteration}) - {english}`

Exception: Grading modes may not need transliteration (just Arabic and English for comparison).

### 8. Feedback Tone Guidance
- Correct feedback: "brief, encouraging"
- Incorrect feedback: "supportive feedback with the correction"

### 9. Flexible Navigation
When offering numbered options, always end with: "Or tell me what you'd like to do." This allows users to request actions not explicitly listed (e.g., "skip to final test" from batch view, "see progress", etc.).

---

# Implementation Priority

## Phase 1: Core Teaching & Grading (Enable Baseline Evaluation)
1. ✓ Vocabulary batch introduction (#3) - **needs update for navigation**
2. ✓ Vocabulary answer grading (#15, #16)
3. ❌ Vocabulary quiz feedback - correct (#6)
4. ❌ Vocabulary quiz feedback - incorrect (#7)
5. ❌ Grammar topic explanation (#10)
6. ❌ Grammar quiz question (#11)
7. ❌ Grammar answer grading (#17)
8. ❌ Grammar quiz feedback - correct (#12)
9. ❌ Grammar quiz feedback - incorrect (#13)

**Goal:** Enable baseline evaluation for teaching and grading modes

---

## Phase 2: Complete User Flows
10. ❌ Lesson welcome/greeting (#1)
11. ❌ Vocabulary overview introduction (#2)
12. ❌ Vocabulary list view (#4)
13. ❌ Vocabulary quiz question (#5)
14. ❌ Vocabulary batch quiz summary (#8)
15. ❌ Grammar overview introduction (#9)
16. ❌ Grammar topic quiz summary (#14)

**Goal:** Complete vocabulary and grammar teaching flows

---

## Phase 3: Exercise Generation & Testing
17. ❌ Exercise generation (#19)
18. ❌ Grammar quiz question generation (#20)
19. ❌ Test composition (#21)
20. ❌ Grammar test grading (#18)

**Goal:** Enable exercise mode and end-of-lesson tests

---

# Quick Reference

## Prompt Count by Mode

| Mode | Prompt Count | Phase 1 | Phase 2 | Phase 3 |
|------|-------------|---------|---------|---------|
| lesson_start | 1 | 0 | 1 | 0 |
| teaching_vocab | 5 | 1 | 4 | 0 |
| teaching_grammar | 4 | 2 | 2 | 0 |
| feedback_vocab | 2 | 2 | 0 | 0 |
| feedback_grammar | 2 | 2 | 0 | 0 |
| grading_vocab | 2 | 2 | 0 | 0 |
| grading_grammar | 2 | 1 | 0 | 1 |
| exercise_generation | 3 | 0 | 0 | 3 |
| **TOTAL** | **21** | **10** | **7** | **4** |

## Implementation Status

- ✅ 2 prompts implemented (1 needs navigation update)
- ❌ 19 prompts need implementation
- Phase 1 focus: 10 prompts (8 remaining + 1 update)

---

# Next Steps

1. ✅ Design all 21 prompt templates (this document)
2. ⏭️ Validate test_cases.json against these templates
3. ⏭️ Implement Phase 1 prompts in baseline.py
4. ⏭️ Update evaluation pipeline for all modes
5. ⏭️ Run baseline evaluation
6. ⏭️ Create training data for fine-tuning

---

**Last Updated:** 2026-04-09
