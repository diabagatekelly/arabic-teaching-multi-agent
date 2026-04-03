"""Prompt templates for vocabulary teaching agent."""

from __future__ import annotations

from prompts.base import ChainOfThoughtPromptTemplate, FewShotPromptTemplate, SimplePromptTemplate


def get_vocab_introduction_prompt() -> SimplePromptTemplate:
    """Prompt for introducing new vocabulary words."""
    return SimplePromptTemplate(
        name="vocab_introduction",
        description="Introduce vocabulary words to student",
        template="""You are teaching Arabic vocabulary for Lesson {lesson_number}.

Vocabulary to introduce: {vocabulary_list}

Introduce 3-4 words at a time. For each word, provide:
- Arabic script with diacritics
- Transliteration (in parentheses)
- English translation

After introducing the words, ask a simple recall question about one of them.

Keep the tone encouraging and supportive.""",
    )


def get_vocab_assessment_prompt() -> FewShotPromptTemplate:
    """Prompt for assessing vocabulary knowledge with few-shot examples."""
    return FewShotPromptTemplate(
        name="vocab_assessment",
        description="Assess student's vocabulary knowledge",
        instruction="Check if the student's answer is correct and provide feedback.",
        examples=[
            {
                "Student answer": "كتاب",
                "Correct answer": "كِتَاب (book)",
                "Feedback": "Perfect! كِتَاب ✓",
            },
            {
                "Student answer": "house",
                "Correct answer": "بَيْت (house)",
                "Feedback": "Correct meaning! The Arabic word is بَيْت (bayt).",
            },
            {
                "Student answer": "school",
                "Correct answer": "كِتَاب (book)",
                "Feedback": "Not quite. كِتَاب means 'book', not 'school'. School is مَدْرَسَة (madrasa).",
            },
        ],
        input_template="Student answer: {student_answer}\nCorrect answer: {correct_answer}\nFeedback:",
    )


def get_vocab_error_correction_prompt() -> ChainOfThoughtPromptTemplate:
    """Prompt for correcting vocabulary mistakes with reasoning."""
    return ChainOfThoughtPromptTemplate(
        name="vocab_error_correction",
        description="Analyze and correct vocabulary mistakes",
        instruction="Identify if there's an error and explain how to fix it.",
        thinking_prompt="Let me analyze this step by step:",
        input_template="Student wrote: {student_answer}\nExpected: {correct_answer}",
        include_examples=True,
        examples=[
            {
                "input": "Student wrote: كتب / Expected: كِتَاب (book)",
                "reasoning": "1. Student wrote كتب without diacritics\n2. This could be confused with 'books' or 'he wrote'\n3. Need to emphasize the correct form with diacritics",
                "answer": "Close! You're missing the vowel marks. كِتَاب (with kasra on ك) means 'book'. The diacritics matter!",
            },
            {
                "input": "Student wrote: bait / Expected: بَيْت (house)",
                "reasoning": "1. Student used transliteration instead of Arabic script\n2. Spelling is close (bait vs bayt)\n3. Need to guide them to use Arabic script",
                "answer": "Good try with the transliteration! Now let's write it in Arabic: بَيْت (bayt). Can you type the Arabic script?",
            },
        ],
    )


def get_vocab_review_prompt() -> SimplePromptTemplate:
    """Prompt for reviewing vocabulary words."""
    return SimplePromptTemplate(
        name="vocab_review",
        description="Review vocabulary with student",
        template="""Let's review the vocabulary from Lesson {lesson_number}.

Words we've learned: {vocabulary_list}

I'll ask you about a few words to check your memory.

Word to recall: {word_to_test}

What does this word mean in English?""",
    )


def get_vocab_progress_prompt() -> SimplePromptTemplate:
    """Prompt for checking student progress and offering next steps."""
    return SimplePromptTemplate(
        name="vocab_progress",
        description="Check progress and offer options",
        template="""Great work! You've learned {words_learned} out of {total_words} vocabulary words.

Your options:
A) Continue learning new words
B) Review words you've learned
C) Take a quick vocabulary test
D) Move to grammar lesson

What would you like to do?""",
    )
