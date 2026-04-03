"""Prompt templates for exercise generation agent."""

from __future__ import annotations

from prompts.base import FewShotPromptTemplate, SimplePromptTemplate


def get_exercise_generation_prompt() -> SimplePromptTemplate:
    """Prompt for generating exercises from templates."""
    return SimplePromptTemplate(
        name="exercise_generation",
        description="Generate exercise from template and context",
        template="""Generate an Arabic learning exercise based on this template and student context.

**Template:**
{exercise_template}

**Student Context:**
- Lesson: {lesson_number}
- Skill focus: {skill_focus}
- Vocabulary: {vocabulary_list}
- Difficulty: {difficulty}

Generate a complete exercise following the template's pattern and guidelines.
Use vocabulary from the student's current lesson.
Match the difficulty level to their progress.""",
    )


def get_exercise_adaptation_prompt() -> FewShotPromptTemplate:
    """Prompt for adapting exercises to student level."""
    return FewShotPromptTemplate(
        name="exercise_adaptation",
        description="Adapt exercise difficulty for student",
        instruction="Modify the exercise to match the student's level.",
        examples=[
            {
                "Original": "Translate: 'the big beautiful new school'",
                "Student level": "Beginner (Lesson 1, day 1)",
                "Adapted": "Translate: 'book' → كِتَاب",
                "Reasoning": "Too complex for day 1, simplified to single word",
            },
            {
                "Original": "What does كتاب mean?",
                "Student level": "Advanced (completed Lesson 3)",
                "Adapted": "Build a sentence using: كِتَاب، كَبِير، جَدِيد (with proper agreement)",
                "Reasoning": "Too simple, increased complexity to sentence building",
            },
        ],
        input_template="Original exercise: {exercise}\nStudent level: {student_level}\nAdapted exercise:",
    )


def get_exercise_selection_prompt() -> SimplePromptTemplate:
    """Prompt for selecting appropriate exercise type."""
    return SimplePromptTemplate(
        name="exercise_selection",
        description="Choose the best exercise type for student goals",
        template="""Select the most appropriate exercise type for this student.

**Student Profile:**
- Current lesson: {lesson_number}
- Weak areas: {weak_areas}
- Strong areas: {strong_areas}
- Recent performance: {recent_performance}
- Learning goal: {learning_goal}

**Available exercise types:**
- Fill-in-blank (vocabulary recall)
- Multiple choice (recognition)
- Translation (production)
- Error correction (grammar application)
- Sentence formation (synthesis)

Choose the exercise type that will:
1. Address weak areas
2. Build on strong areas
3. Match the learning goal
4. Provide appropriate challenge

Recommended exercise type and why:""",
    )


def get_exercise_feedback_prompt() -> FewShotPromptTemplate:
    """Prompt for providing feedback on exercise attempts."""
    return FewShotPromptTemplate(
        name="exercise_feedback",
        description="Provide feedback on student's exercise attempt",
        instruction="Evaluate the student's answer and provide helpful feedback.",
        examples=[
            {
                "Exercise": "Fill in blank: ___ كَبِير (a big book)",
                "Student answer": "كتاب",
                "Evaluation": "Correct! كِتَابٌ كَبِيرٌ ✓",
                "Feedback": "Perfect! You matched the masculine noun with masculine adjective.",
            },
            {
                "Exercise": "Is 'كتاب كبيرة' correct?",
                "Student answer": "Yes",
                "Evaluation": "Incorrect - gender mismatch",
                "Feedback": "No, there's a gender mismatch. كِتَاب (masculine) + كَبِيرَة (feminine) don't agree. Should be: كِتَابٌ كَبِيرٌ ✓",
            },
        ],
        input_template="Exercise: {exercise_text}\nStudent answer: {student_answer}\nFeedback:",
    )


def get_exercise_hint_prompt() -> SimplePromptTemplate:
    """Prompt for generating helpful hints."""
    return SimplePromptTemplate(
        name="exercise_hint",
        description="Generate a helpful hint without giving away the answer",
        template="""The student is stuck on this exercise and asked for a hint.

**Exercise:** {exercise_text}
**Correct answer:** {correct_answer}
**Student's current understanding:** {student_context}

Provide a hint that:
1. Points them in the right direction
2. Doesn't give away the full answer
3. Builds on what they already know
4. Encourages them to think through it

Hint:""",
    )
