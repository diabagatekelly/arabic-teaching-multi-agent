"""
LangChain Prompt Templates for Arabic Teaching Multi-Agent System

All prompts follow the design specifications in docs/PROMPT_DESIGN.md
Total: 20 prompts across 3 agents
"""

from langchain_core.prompts import PromptTemplate

# =============================================================================
# MODE CONSTANTS
# =============================================================================

MODE_LESSON_START = "lesson_start"
MODE_TEACHING_VOCAB = "teaching_vocab"
MODE_TEACHING_GRAMMAR = "teaching_grammar"
MODE_FEEDBACK_VOCAB = "feedback_vocab"
MODE_FEEDBACK_GRAMMAR = "feedback_grammar"
MODE_GRADING_VOCAB = "grading_vocab"
MODE_GRADING_GRAMMAR = "grading_grammar"
MODE_EXERCISE_GENERATION = "exercise_generation"


# =============================================================================
# AGENT 1: TEACHING/PRESENTATION AGENT (13 prompts)
# Model: Fine-tuned Qwen2.5-3B
# =============================================================================

# -----------------------------------------------------------------------------
# Lesson Start (1 prompt)
# -----------------------------------------------------------------------------

LESSON_WELCOME = PromptTemplate(
    template="""Mode: lesson_start

Lesson {lesson_number} Overview

Vocabulary ({total_words} words):
{vocabulary_list}

Grammar ({topics_count} topics):
{grammar_topics}

Example response format:

"Welcome to Lesson 1! 🌟 I'm excited to guide you through Arabic basics today.

Here's what we'll cover:

**Vocabulary:** 6 essential words
- كِتَاب (kitāb) - book
- مَدْرَسَة (madrasa) - school
- قَلَم (qalam) - pen
- بَيْت (bayt) - house
- طَالِب (ṭālib) - student
- مُعَلِّم (muʿallim) - teacher

**Grammar:** Noun Gender - learning masculine and feminine nouns

Which would you like to start with?
1. Start with vocabulary
2. Start with grammar"

Now welcome the student in your own warm, natural style. List all vocabulary words (Arabic + English) and grammar topics.

End with EXACTLY these numbered options:
1. Start with vocabulary
2. Start with grammar""",
    input_variables=[
        "lesson_number",
        "total_words",
        "vocabulary_list",
        "topics_count",
        "grammar_topics",
    ],
)


# -----------------------------------------------------------------------------
# Progress Report (1 prompt)
# -----------------------------------------------------------------------------

PROGRESS_REPORT = PromptTemplate(
    template="""Mode: lesson_start

Lesson {lesson_number} Progress Report

Vocabulary Progress:
{vocab_progress}

Grammar Progress:
{grammar_progress}

Example response:

"Here's where you are in Lesson 1! 📊

**Vocabulary:**
✓ Batch 1: 3/3 words mastered
✓ Batch 2: 2/3 words learned
○ Batch 3: Not started

**Grammar:**
✓ Noun Gender: Passed (4/5)
○ Definite Article: Not started

What would you like to do?
1. Review Batch 1 vocabulary
2. Continue Batch 2 vocabulary
3. Review Noun Gender
4. Start Definite Article
5. Continue where I left off"

Now show their progress in your own encouraging style. List what they've completed with scores and what's still available.

End with numbered options that let them:
- Review/retake any completed vocab batch
- Continue or start vocab batches
- Review/retake any grammar topic
- Continue where they left off""",
    input_variables=["lesson_number", "vocab_progress", "grammar_progress"],
)


# -----------------------------------------------------------------------------
# Vocabulary Teaching (3 prompts)
# -----------------------------------------------------------------------------

VOCAB_BATCH_INTRO = PromptTemplate(
    template="""Mode: teaching_vocab

Lesson {lesson_number}, Batch {batch_number} of {total_batches}

Words (3 per batch):
{words}

{previous_performance}

Example response format:

"Great! Let's learn Batch 1 of 2. Here are your words:

1. كِتَاب (kitāb) - book
2. مَدْرَسَة (madrasa) - school
3. قَلَم (qalam) - pen

Use the flashcards in the left panel to practice these words!

What would you like to do?
1. Take quick quiz on these words
2. Move on to next batch"

Now introduce this batch in your own warm, engaging style. Present the words clearly with Arabic, transliteration, and English. Remind students about the flashcards.

End with EXACTLY these numbered options:
1. Take quick quiz on these words
2. Move on to next batch""",
    input_variables=[
        "lesson_number",
        "batch_number",
        "total_batches",
        "words",
        "previous_performance",
    ],
)

VOCAB_QUIZ_QUESTION = PromptTemplate(
    template="""Mode: teaching_vocab

Question {question_number} of {total_questions}

Example response format:

"Question 1 of 3

What does {word_arabic} mean?"

Now ask your question simply and clearly. Use EXACTLY this format: "Question {question_number} of {total_questions}\n\nWhat does {word_arabic} mean?"

IMPORTANT: DO NOT include the transliteration or English translation in your question. Keep it simple and wait for the student's answer.""",
    input_variables=[
        "question_type",
        "word_arabic",
        "word_english",
        "question_number",
        "total_questions",
    ],
)

VOCAB_BATCH_SUMMARY = PromptTemplate(
    template="""Mode: teaching_vocab

Batch {batch_number} of {total_batches} - Quiz Results

Score: {score}
Correct: {words_correct}
Missed: {words_incorrect}

Progress: You've completed {batches_completed} of {total_batches} batches.

IMPORTANT: Check if all batches are done ({batches_completed} == {total_batches}).

Example responses:

If batches remaining:
"Excellent work! You scored 2/3 on Batch 1. 🎉

✓ Got right: book, school
✗ Missed: pen (قَلَم - qalam)

You've completed 1 of 2 batches - great progress!

What would you like to do?
1. Continue to next batch
2. Review these words"

If all batches complete:
"Amazing! You scored 2/3 on Batch 2 - that's the final vocabulary batch! 🎉

✓ Got right: book, school
✗ Missed: pen (قَلَم - qalam)

You've completed all vocabulary! Ready for grammar?
1. Move on to grammar
2. Review vocabulary"

Now summarize their performance in your own warm, encouraging style. Show which words they got right and which they missed (with translations).

End with EXACTLY these numbered options based on progress:
- If batches remaining: "1. Continue to next batch" and "2. Review these words"
- If all batches complete: "1. Move on to grammar" and "2. Review vocabulary" """,
    input_variables=[
        "batch_number",
        "score",
        "words_correct",
        "words_incorrect",
        "total_batches",
        "batches_completed",
    ],
)


# -----------------------------------------------------------------------------
# Grammar Teaching (4 prompts)
# -----------------------------------------------------------------------------

GRAMMAR_OVERVIEW = PromptTemplate(
    template="""Mode: teaching_grammar

Lesson {lesson_number} - Grammar Section

Topics ({topics_count}):
{topics_list}

Present grammar section overview. Explain each topic has a quiz. Offer options:
1. Start first topic
2. See lesson progress

Or tell me what you'd like to do.""",
    input_variables=["lesson_number", "topics_count", "topics_list"],
)

GRAMMAR_EXPLANATION = PromptTemplate(
    template="""Mode: teaching_grammar

Lesson {lesson_number}

Topic: {topic_name}

Rule: {grammar_rule}

Examples:
{examples_formatted}

Example response format:

"Let's learn about Noun Gender! 📚

In Arabic, every noun is either masculine or feminine. Here's the key rule:

**Feminine nouns** usually end in ة (tā' marbūṭa), while **masculine nouns** don't.

Examples:
- كِتَابٌ (kitābun) - book [masculine]
- مَدْرَسَةٌ (madrasatun) - school [feminine]

What would you like to do next?
1. Take quiz on this topic
2. Review the lesson"

Now teach this grammar topic in your own clear, engaging style. Explain the rule and provide the examples to help them understand.

End with EXACTLY these numbered options:
1. Take quiz on this topic
2. Review the lesson""",
    input_variables=["lesson_number", "topic_name", "grammar_rule", "examples_formatted"],
)

GRAMMAR_QUIZ_QUESTION = PromptTemplate(
    template="""Mode: teaching_grammar

{topic_name} - Question {question_number} of {total_questions}

Question: {question}

Present the question clearly.

IMPORTANT: If the question expects an Arabic answer, make sure to include case endings (final harakaat) in the question text, as these are grammatically significant and students must learn them.""",
    input_variables=["topic_name", "question_number", "total_questions", "question"],
)

GRAMMAR_TOPIC_SUMMARY = PromptTemplate(
    template="""Mode: teaching_grammar

{topic_name} Quiz Results

Score: {score}
Pass Threshold: {pass_threshold}

{weak_areas}

Summarize performance. If score < threshold, suggest reviewing weak areas and offer retry. If passed, congratulate. Offer options:
1. Continue to next topic (if available)
2. Review and retry (if failed)
3. See lesson progress

Or tell me what you'd like to do.""",
    input_variables=["topic_name", "score", "pass_threshold", "weak_areas"],
)


# -----------------------------------------------------------------------------
# Feedback (4 prompts - 2 vocab, 2 grammar)
# -----------------------------------------------------------------------------

FEEDBACK_VOCAB_CORRECT = PromptTemplate(
    template="""Mode: feedback_vocab

Word: {word_arabic} ({word_transliteration})
Translation: {english}
Student was correct.
Current Score: {current_score}

Example response:

"✓ Correct! كِتَاب (kitāb) means book. You're doing great - that's 2/3 correct!"

IMPORTANT: The student got this RIGHT. Start with a positive affirmation like "Correct!", "Yes!", "Perfect!", or "Exactly!".
Now provide brief, encouraging feedback in your own style. Confirm correctness and mention their score. Be warm and personable!""",
    input_variables=["word_arabic", "word_transliteration", "english", "current_score"],
)

FEEDBACK_VOCAB_INCORRECT = PromptTemplate(
    template="""Mode: feedback_vocab

Word: {word_arabic} ({word_transliteration})
Correct Translation: {english}
Student Answer: {student_answer}
Student was incorrect.
Current Score: {current_score}

Example response:

"Not quite! كِتَاب (kitāb) means book, not pen. Think of 'kitāb' like 'book' - they both have that 'k' sound! You're at 1/2 so far - keep going!"

IMPORTANT: The student got this WRONG. Start with a gentle correction like "Not quite!", "Almost!", "Close, but...", or "Actually,".
Now provide supportive correction in your own style. Show the correct answer clearly, optionally give a memory tip, and mention their score. Be encouraging and helpful!""",
    input_variables=[
        "word_arabic",
        "word_transliteration",
        "english",
        "student_answer",
        "current_score",
    ],
)

FEEDBACK_GRAMMAR_CORRECT = PromptTemplate(
    template="""Mode: feedback_grammar

Question: {question}
Student Answer: {student_answer}
Correct Answer: {correct_answer}
Explanation: {explanation}
Current Score: {current_score}
Student was correct.

IMPORTANT: The student got this RIGHT. Start with a positive affirmation like "Correct!", "Yes!", "Exactly!", or "Perfect!".
Provide brief, encouraging feedback in your own style. Mention current score. Be warm and personable!""",
    input_variables=[
        "question",
        "student_answer",
        "correct_answer",
        "explanation",
        "current_score",
    ],
)

FEEDBACK_GRAMMAR_INCORRECT = PromptTemplate(
    template="""Mode: feedback_grammar

Question: {question}
Student Answer: {student_answer}
Correct Answer: {correct_answer}
Explanation: {explanation}
Current Score: {current_score}
Student was incorrect.

IMPORTANT: The student got this WRONG. Start with a gentle correction like "Not quite!", "Almost!", "Actually,", or "Close, but...".
Provide supportive correction in your own style. Explain why with reference to grammar rule. Mention current score. Be encouraging and helpful!""",
    input_variables=[
        "question",
        "student_answer",
        "correct_answer",
        "explanation",
        "current_score",
    ],
)


# =============================================================================
# AGENT 2: GRADING AGENT (4 prompts)
# Model: Fine-tuned Qwen2.5-7B
# Baseline evaluated: 2026-04-13 (83% reasoning accuracy, 0-6% JSON compliance)
# Fine-tuning planned: 270+ examples for JSON-only output + harakaat rules
# =============================================================================

GRADING_VOCAB = PromptTemplate(
    template="""Mode: grading_vocab

Question: What does "{word}" mean?
Student Answer: "{student_answer}"
Correct Answer: "{correct_answer}"

Evaluate if the student's answer is correct. Be flexible:
- Accept minor typos (e.g., "scool" for "school")
- Accept synonyms (e.g., "instructor" for "teacher")
- Accept alternate phrasings that convey the same meaning

IMPORTANT: Output ONLY a JSON object. Do NOT add explanations, reasoning, or any text before or after the JSON.

Correct output examples:
{{"correct": true}}
{{"correct": false}}

Incorrect output examples (DO NOT DO THIS):
{{"correct": true}} because the answer matches
The answer is correct: {{"correct": true}}

Your response must be ONLY the JSON object with no additional text.

Response:""",
    input_variables=["word", "student_answer", "correct_answer"],
)

GRADING_GRAMMAR_QUIZ = PromptTemplate(
    template="""Mode: grading_grammar

Question: {question}
Student Answer: "{student_answer}"
Correct Answer: "{correct_answer}"

Evaluate if the student's answer is correct. Be flexible:
- Accept minor typos
- Accept synonyms or alternate phrasings that convey the same meaning
- For identification questions (masculine/feminine), accept abbreviated forms (m/f, masc/fem)
- For Arabic text answers: Internal harakaat (vowel marks) are OPTIONAL, but case endings (final harakaat like ُ َ ِ ٌ ً ٍ) are REQUIRED and must match exactly

IMPORTANT: Output ONLY a JSON object. Do NOT add explanations, reasoning, or any text before or after the JSON.

Correct output examples:
{{"correct": true}}
{{"correct": false}}

Incorrect output examples (DO NOT DO THIS):
{{"correct": true}} The student correctly identified the gender
Explanation: {{"correct": false}}

Your response must be ONLY the JSON object with no additional text.

Response:""",
    input_variables=["question", "student_answer", "correct_answer"],
)

GRADING_GRAMMAR_TEST = PromptTemplate(
    template="""Mode: grading_grammar

Lesson {lesson_number} - Final Test Grading

Grade the following answers:

{answers_formatted}

For each answer, evaluate correctness with flexibility:
- Accept minor typos, synonyms, abbreviations
- For Arabic text answers: Internal harakaat (vowel marks) are OPTIONAL, but case endings (final harakaat like ُ َ ِ ٌ ً ٍ) are REQUIRED and must match exactly

IMPORTANT: Output ONLY a JSON object. Do NOT add explanations, reasoning, or any text before or after the JSON.

Required JSON format:
{{
  "total_score": "X/Y",
  "results": [
    {{"question_id": "q1", "correct": true}},
    {{"question_id": "q2", "correct": false}},
    ...
  ]
}}

The "correct" field must be a boolean (true or false, not strings).

Your response must be ONLY the JSON object with no additional text.

Response:""",
    input_variables=["lesson_number", "answers_formatted"],
)


# =============================================================================
# AGENT 3: CONTENT GENERATION AGENT (3 prompts)
# Model: Base Qwen2.5-3B (not fine-tuned initially)
# =============================================================================

EXERCISE_GENERATION = PromptTemplate(
    template="""Mode: exercise_generation

Lesson {lesson_number}
Type: {exercise_type}
Difficulty: {difficulty}
Count: {count}

Learned items:
{learned_items_formatted}

Generate {count} practice exercises using the learned items above.

CRITICAL REQUIREMENTS:
1. ALL Arabic text MUST include harakaat (diacritical marks), especially final case endings (ُ َ ِ ٌ ً ٍ)
2. NEVER use transliteration alone (e.g., "kabiir") - always include Arabic script: "كَبِيرٌ"
3. Each question must be clear: "Translate:", "What does X mean?", "Fill in:", "Complete:", etc.
4. Use the learned vocabulary in your exercises

Correct Arabic examples:
- "كِتَابٌ" (with harakaat ٌ)
- "الكِتَابُ" (with case ending ُ)
- "المَدْرَسَةَ" (with case ending َ)

IMPORTANT: Output ONLY valid JSON. Do NOT add explanations, commentary, or text before/after the JSON.

Required JSON format:
[
  {{
    "question": "...",
    "answer": "...",
    "difficulty": "{difficulty}"
  }},
  ...
]

Response:""",
    input_variables=[
        "lesson_number",
        "exercise_type",
        "difficulty",
        "count",
        "learned_items_formatted",
    ],
)

QUIZ_QUESTION_GENERATION = PromptTemplate(
    template="""Mode: exercise_generation

Lesson {lesson_number} - {topic_name} Quiz Generation

Grammar Rule: {grammar_rule}

Examples:
{examples_formatted}

Generate {count} quiz questions to test understanding of this rule.

IMPORTANT: For questions expecting Arabic answers, always include case endings (final harakaat like ُ َ ِ ٌ ً ٍ) in both the question text and the correct answer. Case endings are grammatically significant and must be tested.

Return JSON list:
[
  {{
    "question": "question text",
    "answer": "correct answer",
    "explanation": "why this is the answer"
  }},
  ...
]

Response:""",
    input_variables=["lesson_number", "topic_name", "grammar_rule", "count", "examples_formatted"],
)

TEST_COMPOSITION = PromptTemplate(
    template="""Mode: exercise_generation

Lesson {lesson_number} - Final Test Composition

Grammar topics to cover:
{grammar_topics_formatted}

Question count: {question_count}
Question types: {question_types}

Generate a mixed test covering all topics.

IMPORTANT: For questions expecting Arabic answers, always include case endings (final harakaat like ُ َ ِ ٌ ً ٍ) in both the question text and the correct answer. Case endings are grammatically significant and must be tested.

Return JSON:
{{
  "test_id": "lesson_{lesson_number}_test",
  "total_questions": {question_count},
  "questions": [
    {{
      "question_id": "q1",
      "type": "...",
      "question": "...",
      "answer": "...",
      "grammar_topic": "..."
    }},
    ...
  ]
}}

Response:""",
    input_variables=[
        "lesson_number",
        "grammar_topics_formatted",
        "question_count",
        "question_types",
    ],
)
