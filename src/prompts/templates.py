"""
LangChain Prompt Templates for Arabic Teaching Multi-Agent System

All prompts follow the design specifications in docs/PROMPT_DESIGN.md
Total: 21 prompts across 3 agents
"""

from langchain.prompts import PromptTemplate

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

Vocabulary: {total_words} words
Preview: {topics_preview}

Grammar: {topics_count} topics
Topics: {grammar_topics}

Greet the student warmly and present the lesson structure. Offer navigation:
1. Start with vocabulary
2. Start with grammar
3. See lesson progress

Or tell me what you'd like to do.""",
    input_variables=[
        "lesson_number",
        "total_words",
        "topics_preview",
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

Words:
{words}

Present these words with Arabic, transliteration, and English translation. Remind them flashcards are available for learning. Offer options:
1. Take quiz on these words
2. Go to next batch
3. See all words

Or tell me what you'd like to do.""",
    input_variables=["lesson_number", "batch_number", "total_batches", "words"],
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

Question Type: {question_type}
Word: {word_arabic} ({word_transliteration})

Ask the translation question clearly. If arabic_to_english, ask "What does {word_arabic} mean?" If english_to_arabic, provide the English word and ask for Arabic translation.""",
    input_variables=["question_type", "word_arabic", "word_transliteration"],
)

VOCAB_BATCH_SUMMARY = PromptTemplate(
    template="""Mode: teaching_vocab

Batch {batch_number} Quiz Results

Score: {score}
Correct: {words_correct}
Missed: {words_incorrect}

Summarize performance encouragingly. Show words missed with translations. Offer options:
1. Continue to next batch
2. Review these words
3. Skip to final test

Or tell me what you'd like to do.""",
    input_variables=["batch_number", "score", "words_correct", "words_incorrect"],
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

Explain this grammar topic to the student in an encouraging way. End by mentioning the quiz is next.""",
    input_variables=["lesson_number", "topic_name", "grammar_rule", "examples_formatted"],
)

GRAMMAR_QUIZ_QUESTION = PromptTemplate(
    template="""Mode: teaching_grammar

{topic_name} - Question {question_number} of {total_questions}

Question: {question}

Present the question clearly.""",
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

Provide brief, encouraging feedback. Confirm correctness with checkmark.""",
    input_variables=["word_arabic", "word_transliteration", "english"],
)

FEEDBACK_VOCAB_INCORRECT = PromptTemplate(
    template="""Mode: feedback_vocab

Word: {word_arabic} ({word_transliteration})
Correct Translation: {english}
Student Answer: {student_answer}
Student was incorrect.

Provide supportive correction. Show correct answer with transliteration. Give memory tip.""",
    input_variables=["word_arabic", "word_transliteration", "english", "student_answer"],
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
# Model: Base Qwen2.5-7B (not fine-tuned initially)
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

Return JSON:
{{"correct": true}} or {{"correct": false}}

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

Return JSON:
{{"correct": true}} or {{"correct": false}}

Response:""",
    input_variables=["question", "student_answer", "correct_answer"],
)

GRADING_GRAMMAR_TEST = PromptTemplate(
    template="""Mode: grading_grammar

Lesson {lesson_number} - Final Test Grading

Grade the following answers:

{answers_formatted}

For each answer, evaluate correctness with flexibility (accept typos, synonyms, abbreviations).

Return JSON with results for each question. The "correct" field should be true or false (boolean values):
{{
  "total_score": "X/Y",
  "results": [
    {{"question_id": "q1", "correct": true}},
    {{"question_id": "q2", "correct": false}},
    ...
  ]
}}

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
Content: {content_type}
Count: {count}

Learned items:
{learned_items_formatted}

Generate {count} practice exercises. Return JSON list:
[
  {{
    "question": "question text here",
    "answer": "correct answer here"
  }},
  ...
]

Response:""",
    input_variables=[
        "lesson_number",
        "exercise_type",
        "content_type",
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

Generate {count} quiz questions to test understanding of this rule. Return JSON list:
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

Generate a mixed test covering all topics. Return JSON:
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
