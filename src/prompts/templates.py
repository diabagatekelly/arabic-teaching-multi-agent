"""
LangChain Prompt Templates for Arabic Teaching Multi-Agent System

All prompts follow the design specifications in docs/PROMPT_DESIGN.md
Total: 21 prompts across 3 agents
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
# AGENT 1: TEACHING/PRESENTATION AGENT (14 prompts)
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

Now generate your response following this format exactly. Greet warmly, list ALL vocabulary words with Arabic and English, present grammar topics, and end with those exact numbered options.""",
    input_variables=[
        "lesson_number",
        "total_words",
        "vocabulary_list",
        "topics_count",
        "grammar_topics",
    ],
)


# -----------------------------------------------------------------------------
# Vocabulary Teaching (5 prompts)
# -----------------------------------------------------------------------------

VOCAB_OVERVIEW = PromptTemplate(
    template="""Mode: teaching_vocab

Lesson {lesson_number} - Vocabulary Overview

Words you'll learn:
{words_formatted}

These are divided into {batches_count} batches for easier learning.

Present all words and explain options:
1. Learn in batches (I'll teach each batch, then quiz you)
2. Skip to final test (test yourself on all {total_words} words now)

Format with numbered options and mention they can request something else.""",
    input_variables=["lesson_number", "words_formatted", "batches_count", "total_words"],
)

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

Now generate your response following this exact format. Present the words clearly, remind them about flashcards, and end with those exact numbered options.""",
    input_variables=[
        "lesson_number",
        "batch_number",
        "total_batches",
        "words",
        "previous_performance",
    ],
)

VOCAB_LIST_VIEW = PromptTemplate(
    template="""Mode: teaching_vocab

Lesson {lesson_number} - All Vocabulary Words

All Words:
{all_words}

Show all vocabulary words with Arabic, transliteration, and English. Mention current batch ({current_batch}) and offer navigation:
1. Go back to current batch (Batch {current_batch})
2. Skip to final test

Or tell me what you'd like to do.""",
    input_variables=["lesson_number", "all_words", "current_batch"],
)

VOCAB_QUIZ_QUESTION = PromptTemplate(
    template="""Mode: teaching_vocab

Question {question_number} of {total_questions}
Question Type: {question_type}

Example for arabic_to_english:
"Question 1 of 3

What does كِتَاب mean?"

Example for english_to_arabic:
"Question 2 of 3

How do you say 'school' in Arabic?"

Now generate your question following this format:
- If arabic_to_english: Ask "What does {word_arabic} mean?" (DO NOT include transliteration or English)
- If english_to_arabic: Ask "How do you say '{word_english}' in Arabic?" (DO NOT include the Arabic answer)

Keep it simple and clear. Wait for the student's answer.""",
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

Example response:

"Excellent work! You scored 2/3 on Batch 1. 🎉

✓ Got right: book, school
✗ Missed: pen (قَلَم - qalam)

You've completed 1 of 2 batches - great progress!

What would you like to do?
1. Continue to next batch
2. Review these words
3. Skip to final test"

Now generate your response following this format. Summarize performance encouragingly, show missed words with translations, and end with those exact numbered options.""",
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

Now generate your response following this exact format. Explain clearly with examples and end with those exact numbered options.""",
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

Now provide brief, encouraging feedback following this style. Confirm correctness and mention their score.""",
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

Now provide supportive correction following this style. Show the correct answer, give a memory tip, and mention their score.""",
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

Provide brief, encouraging feedback. Mention current score.""",
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

Provide supportive correction. Explain why with reference to grammar rule. Mention current score.""",
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
