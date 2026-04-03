"""Prompt templates for grammar teaching agent."""

from __future__ import annotations

from prompts.base import ChainOfThoughtPromptTemplate, FewShotPromptTemplate, SimplePromptTemplate


def get_grammar_introduction_prompt() -> SimplePromptTemplate:
    """Prompt for introducing grammar concepts."""
    return SimplePromptTemplate(
        name="grammar_introduction",
        description="Introduce a grammar concept to student",
        template="""You are teaching Arabic grammar for Lesson {lesson_number}.

Grammar topic: {grammar_topic}

Introduce the concept by:
1. Stating the rule clearly
2. Showing 2-3 examples from the vocabulary
3. Highlighting the pattern

After explaining, ask a simple question to check understanding.

Keep explanations concise and use examples from words they already know.""",
    )


def get_grammar_error_detection_prompt() -> ChainOfThoughtPromptTemplate:
    """Prompt for detecting grammar errors with reasoning."""
    return ChainOfThoughtPromptTemplate(
        name="grammar_error_detection",
        description="Detect and explain grammar errors",
        instruction="Analyze if the student's answer has a grammar error.",
        thinking_prompt="Let me check this carefully:",
        input_template="Student wrote: {student_answer}\nGrammar rule: {grammar_rule}",
        include_examples=True,
        examples=[
            {
                "input": "Student wrote: كتاب كبيرة / Rule: Gender agreement (masculine noun + adjective)",
                "reasoning": "1. كِتَاب (book) is masculine (no ة)\n2. كَبِيرَة has ة, so it's feminine\n3. Gender mismatch - they don't agree",
                "answer": "No, that's incorrect! كِتَاب is masculine but كَبِيرَة is feminine. They must match: كِتَابٌ كَبِيرٌ ✓",
            },
            {
                "input": "Student wrote: المدرسة كبيرة / Rule: Definiteness agreement",
                "reasoning": "1. المَدْرَسَة has ال (definite)\n2. كَبِيرَة has no ال (indefinite)\n3. Definiteness mismatch",
                "answer": "Not quite! المَدْرَسَة is definite (has ال) but كَبِيرَة is indefinite. Both need ال: المَدْرَسَةُ الكَبِيرَةُ ✓",
            },
            {
                "input": "Student wrote: كتاب كبير / Rule: Gender agreement",
                "reasoning": "1. كِتَاب is masculine (no ة)\n2. كَبِير is masculine (no ة)\n3. Both match - correct!",
                "answer": "Perfect! كِتَابٌ كَبِيرٌ ✓ Both are masculine, so they agree!",
            },
        ],
    )


def get_grammar_practice_prompt() -> FewShotPromptTemplate:
    """Prompt for grammar practice exercises."""
    return FewShotPromptTemplate(
        name="grammar_practice",
        description="Generate grammar practice questions",
        instruction="Create a grammar practice question based on the rule.",
        examples=[
            {
                "Rule": "Noun gender - identifying masculine vs feminine",
                "Question": "Is مَدْرَسَة (school) masculine or feminine?\nA) Masculine\nB) Feminine",
                "Answer": "B) Feminine - it has the ة marker",
            },
            {
                "Rule": "Definite article ال",
                "Question": "Add ال to make this word definite: كِتَاب (book)",
                "Answer": "الكِتَاب (the book)",
            },
            {
                "Rule": "Adjective gender agreement",
                "Question": "Complete: مَدْرَسَة ___ (a big school)\nA) كَبِير\nB) كَبِيرَة",
                "Answer": "B) كَبِيرَة - matches feminine noun",
            },
        ],
        input_template="Rule: {grammar_rule}\nVocabulary: {vocabulary}\nQuestion:",
    )


def get_grammar_explanation_prompt() -> ChainOfThoughtPromptTemplate:
    """Prompt for explaining grammar concepts with examples."""
    return ChainOfThoughtPromptTemplate(
        name="grammar_explanation",
        description="Explain why a grammar rule works this way",
        instruction="Explain the grammar concept clearly and simply.",
        thinking_prompt="Here's how this works:",
        input_template="Student asked: {student_question}\nGrammar topic: {grammar_topic}",
        include_examples=True,
        examples=[
            {
                "input": "Why does Arabic have gender for objects? / Topic: Noun gender",
                "reasoning": "1. It's a feature of the language structure\n2. Helps with agreement throughout sentences\n3. Similar to French, Spanish, German",
                "answer": "Great question! In Arabic (like French or Spanish), all nouns have gender - even objects. This isn't about real-world gender, it's just how the language works. The gender helps other words (like adjectives) know how to match. Think of it as a matching game - the adjective wears the same 'outfit' as the noun!",
            },
        ],
    )


def get_grammar_correction_prompt() -> SimplePromptTemplate:
    """Prompt for correcting grammar mistakes."""
    return SimplePromptTemplate(
        name="grammar_correction",
        description="Provide correction for grammar error",
        template="""The student made a grammar error.

Error: {error_description}
Student's answer: {student_answer}
Correct answer: {correct_answer}

Provide:
1. Clear "No" or "Not quite"
2. Identify the specific error
3. Show the correct form
4. Brief explanation of the rule

Keep feedback supportive and educational.""",
    )
