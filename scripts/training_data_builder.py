"""Shared utilities for building training data conversations."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any


def load_examples(filename: str, examples_subdir: str = "") -> list[dict[str, Any]]:
    """Load examples from JSON file.

    Args:
        filename: Name of the JSON file to load
        examples_subdir: Subdirectory under data/training/examples/

    Returns:
        List of example dictionaries

    Raises:
        FileNotFoundError: If the file doesn't exist
        json.JSONDecodeError: If the file contains invalid JSON
    """
    examples_dir = Path(__file__).parent.parent / "data" / "training" / "examples"

    if examples_subdir:
        examples_dir = examples_dir / examples_subdir

    file_path = examples_dir / filename

    try:
        with open(file_path, encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"❌ Error: {file_path} not found")
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"❌ Error parsing {file_path}: {e}")
        sys.exit(1)


def create_exercise_conversation(
    example: dict[str, Any],
    system_content: str = "You are an Arabic exercise generation system. Return only valid JSON.",
) -> dict[str, Any]:
    """Create an exercise generation training conversation.

    Args:
        example: Dictionary with lesson_number, exercise_type, content_type,
                count, learned_items, and exercises
        system_content: System message for the conversation

    Returns:
        Training conversation dictionary
    """
    learned_items_formatted = "\n".join([f"- {item}" for item in example["learned_items"]])

    return {
        "messages": [
            {"role": "system", "content": system_content},
            {
                "role": "user",
                "content": f"""Mode: exercise_generation

Lesson {example['lesson_number']}
Type: {example['exercise_type']}
Content: {example['content_type']}
Count: {example['count']}

Learned items:
{learned_items_formatted}

Generate {example['count']} practice exercises. Return JSON list:
[
  {{
    "question": "question text here",
    "answer": "correct answer here"
  }},
  ...
]

Response:""",
            },
            {"role": "assistant", "content": json.dumps(example["exercises"], ensure_ascii=False)},
        ]
    }


def create_grading_vocab_conversation(
    example: dict[str, Any],
    is_correct: bool,
    system_content: str = "You are an Arabic vocabulary grading system. Return only valid JSON.",
) -> dict[str, Any]:
    """Create a grading vocabulary training conversation.

    Args:
        example: Dictionary with word, student_answer, correct_answer
        is_correct: Whether the student answer is correct
        system_content: System message for the conversation

    Returns:
        Training conversation dictionary
    """
    return {
        "messages": [
            {"role": "system", "content": system_content},
            {
                "role": "user",
                "content": f"""Mode: grading_vocab

Question: What does "{example['word']}" mean?
Student Answer: "{example['student_answer']}"
Correct Answer: "{example['correct_answer']}"

Evaluate if the student's answer is correct. Be flexible:
- Accept minor typos (e.g., "scool" for "school")
- Accept synonyms (e.g., "instructor" for "teacher")
- Accept alternate phrasings that convey the same meaning

Return JSON:
{{"correct": true}} or {{"correct": false}}

Response:""",
            },
            {
                "role": "assistant",
                "content": json.dumps({"correct": is_correct}, ensure_ascii=False),
            },
        ]
    }


def create_grading_grammar_conversation(
    example: dict[str, Any],
    is_correct: bool,
    system_content: str = "You are an Arabic grammar grading system. Return only valid JSON.",
) -> dict[str, Any]:
    """Create a grading grammar training conversation.

    Args:
        example: Dictionary with question, student_answer, correct_answer
        is_correct: Whether the student answer is correct
        system_content: System message for the conversation

    Returns:
        Training conversation dictionary
    """
    return {
        "messages": [
            {"role": "system", "content": system_content},
            {
                "role": "user",
                "content": f"""Mode: grading_grammar

Question: {example['question']}
Student Answer: "{example['student_answer']}"
Correct Answer: "{example['correct_answer']}"

Evaluate if the student's answer is correct. Be flexible:
- Accept minor typos
- Accept synonyms or alternate phrasings that convey the same meaning
- For identification questions (masculine/feminine), accept abbreviated forms (m/f, masc/fem)

Return JSON:
{{"correct": true}} or {{"correct": false}}

Response:""",
            },
            {
                "role": "assistant",
                "content": json.dumps({"correct": is_correct}, ensure_ascii=False),
            },
        ]
    }


def create_grading_multiple_errors_conversation(
    example: dict[str, Any],
    system_content: str = "You are an Arabic grammar test grading system. Return only valid JSON.",
) -> dict[str, Any]:
    """Create a batch grading conversation with multiple questions.

    Args:
        example: Dictionary with lesson_number and answers list
        system_content: System message for the conversation

    Returns:
        Training conversation dictionary
    """
    answers_formatted = "\n\n".join(
        [
            f"Question {i+1} (ID: {ans['question_id']}):\nQ: {ans['question']}\nStudent: \"{ans['student']}\"\nCorrect: \"{ans['correct']}\""
            for i, ans in enumerate(example["answers"])
        ]
    )

    results = []
    for ans in example["answers"]:
        is_correct = ans["student"].lower().strip() in [
            ans["correct"].lower(),
            ans["correct"].split("(")[0].strip().lower(),
        ]

        if not is_correct and "masculine or feminine" in ans["question"].lower():
            if ans["student"].lower() in ["m", "masc"] and "masculine" in ans["correct"].lower():
                is_correct = True
            elif ans["student"].lower() in ["f", "fem"] and "feminine" in ans["correct"].lower():
                is_correct = True

        results.append({"question_id": ans["question_id"], "correct": is_correct})

    correct_count = sum(1 for r in results if r["correct"])
    total_score = f"{correct_count}/{len(results)}"

    response_json = {"total_score": total_score, "results": results}

    return {
        "messages": [
            {"role": "system", "content": system_content},
            {
                "role": "user",
                "content": f"""Mode: grading_grammar

Lesson {example['lesson_number']} - Final Test Grading

Grade the following answers:

{answers_formatted}

For each answer, evaluate correctness with flexibility (accept typos, synonyms, abbreviations).

Return JSON with results for each question. The "correct" field should be true or false (boolean values):
{{{{
  "total_score": "X/Y",
  "results": [
    {{{{"question_id": "q1", "correct": true}}}},
    {{{{"question_id": "q2", "correct": false}}}},
    ...
  ]
}}}}

Response:""",
            },
            {"role": "assistant", "content": json.dumps(response_json, ensure_ascii=False)},
        ]
    }


def create_teaching_conversation(
    example: dict[str, Any],
    system_content: str = "You are a supportive Arabic language teacher. Use an encouraging, warm tone.",
) -> dict[str, Any]:
    """Create a teaching mode training conversation.

    Args:
        example: Dictionary with user_prompt and assistant_response
        system_content: System message for the conversation

    Returns:
        Training conversation dictionary
    """
    return {
        "messages": [
            {"role": "system", "content": system_content},
            {"role": "user", "content": example["user_prompt"]},
            {"role": "assistant", "content": example["assistant_response"]},
        ]
    }


def create_teaching_grammar_conversation(
    example: dict[str, Any],
    system_content: str = "You are a supportive Arabic language teacher. Use an encouraging, warm tone.",
) -> dict[str, Any]:
    """Create a grammar teaching conversation.

    Args:
        example: Dictionary with topic, rule, and examples
        system_content: System message for the conversation

    Returns:
        Training conversation dictionary
    """
    user_prompt = f"""Mode: teaching_grammar

Lesson {{{{lesson_number}}}}

Topic: {example['topic']}

Rule: {example['rule']}

Examples:
{example['examples']}

Explain this grammar topic to the student in an encouraging way. End by mentioning the quiz is next and offering to proceed."""

    assistant_response = f"""Let's explore {example['topic']}! 🌟

**The Rule:**
{example['rule']}

**Let's See It In Action:**
{example['examples']}

Notice how the rule works in these examples? This pattern will become second nature with practice!

Understanding {example['topic']} opens up so many possibilities in Arabic. You're building a strong foundation!

Ready to test your understanding with the quiz? Or would you like me to review anything first?"""

    return {
        "messages": [
            {"role": "system", "content": system_content},
            {"role": "user", "content": user_prompt},
            {"role": "assistant", "content": assistant_response},
        ]
    }


def create_feedback_vocab_conversation(
    example: dict[str, Any],
    is_correct: bool,
    system_content: str = "You are a supportive Arabic language teacher. Use an encouraging, warm tone.",
) -> dict[str, Any]:
    """Create a vocabulary feedback conversation.

    Args:
        example: Dictionary with arabic, trans, english, and optionally student_answer
        is_correct: Whether the student answer was correct
        system_content: System message for the conversation

    Returns:
        Training conversation dictionary
    """
    if is_correct:
        user_prompt = f"""Mode: feedback_vocab

Word: {example['arabic']} ({example['trans']})
Translation: {example['english']}
Student was correct.

Provide brief, encouraging feedback. Confirm correctness with checkmark."""

        assistant_response = f"""✅ Perfect! That's correct!

{example['arabic']} ({example['trans']}) means {example['english']}. Well done!"""
    else:
        user_prompt = f"""Mode: feedback_vocab

Word: {example['arabic']} ({example['trans']})
Correct Translation: {example['english']}
Student Answer: {example['student_answer']}
Student was incorrect.

Provide supportive correction. Show correct answer with transliteration. Give memory tip."""

        assistant_response = f"""Not quite, but great effort! Let's clarify:

{example['arabic']} ({example['trans']}) means **{example['english']}**, not {example['student_answer']}.

💡 Memory tip: Try connecting the sound "{example['trans']}" with "{example['english']}" in your mind. The more you practice, the more natural it becomes!

You're learning - that's what matters! ✨"""

    return {
        "messages": [
            {"role": "system", "content": system_content},
            {"role": "user", "content": user_prompt},
            {"role": "assistant", "content": assistant_response},
        ]
    }


def create_feedback_grammar_conversation(
    example: dict[str, Any],
    is_correct: bool,
    system_content: str = "You are a supportive Arabic language teacher. Use an encouraging, warm tone.",
) -> dict[str, Any]:
    """Create a grammar feedback conversation.

    Args:
        example: Dictionary with question, student_answer, correct_answer,
                explanation, and score
        is_correct: Whether the student answer was correct
        system_content: System message for the conversation

    Returns:
        Training conversation dictionary
    """
    if is_correct:
        user_prompt = f"""Mode: feedback_grammar

Question: {example['question']}
Student Answer: {example['student_answer']}
Correct Answer: {example['correct_answer']}
Explanation: {example['explanation']}
Current Score: {example['score']}
Student was correct.

Provide brief, encouraging feedback. Mention current score."""

        assistant_response = f"""✅ Excellent! You're absolutely right!

{example['explanation']}

Your current score: {example['score']} - keep up the great work! 🌟"""
    else:
        user_prompt = f"""Mode: feedback_grammar

Question: {example['question']}
Student Answer: {example['student_answer']}
Correct Answer: {example['correct_answer']}
Explanation: {example['explanation']}
Current Score: {example['score']}
Student was incorrect.

Provide supportive correction. Explain why with reference to grammar rule. Mention current score."""

        assistant_response = f"""Not quite, but you're learning! Let's work through this together:

**Your answer:** {example['student_answer']}
**Correct answer:** {example['correct_answer']}

**Why:** {example['explanation']}

Your current score: {example['score']}

Don't be discouraged - understanding grammar rules takes practice, and you're making progress with every attempt! Keep going! 💪"""

    return {
        "messages": [
            {"role": "system", "content": system_content},
            {"role": "user", "content": user_prompt},
            {"role": "assistant", "content": assistant_response},
        ]
    }


def write_jsonl(conversations: list[dict[str, Any]], output_file: Path) -> None:
    """Write conversations to a JSONL file.

    Args:
        conversations: List of conversation dictionaries
        output_file: Path to output JSONL file
    """
    output_file.parent.mkdir(parents=True, exist_ok=True)

    with open(output_file, "w", encoding="utf-8") as f:
        for conversation in conversations:
            f.write(json.dumps(conversation, ensure_ascii=False) + "\n")

    print(f"✅ Generated {len(conversations)} training conversations")
    print(f"📁 Saved to: {output_file}")
