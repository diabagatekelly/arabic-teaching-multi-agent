"""Generate teaching mode training data for fine-tuning."""

from __future__ import annotations

from pathlib import Path

from training_data_builder import (
    create_feedback_grammar_conversation,
    create_feedback_vocab_conversation,
    create_teaching_conversation,
    create_teaching_grammar_conversation,
    load_examples,
    write_jsonl,
)


def main() -> None:
    """Generate all teaching mode training data and save to JSONL."""
    output_dir = Path(__file__).parent.parent / "data" / "training"

    all_conversations: list[dict] = []

    lesson_start = load_examples("lesson_start_examples.json", "teaching")
    for example in lesson_start:
        all_conversations.append(create_teaching_conversation(example))
    lesson_start_count = len(lesson_start)

    teaching_vocab = load_examples("teaching_vocab_examples.json", "teaching")
    for example in teaching_vocab:
        all_conversations.append(create_teaching_conversation(example))
    teaching_vocab_count = len(teaching_vocab)

    teaching_grammar = load_examples("teaching_grammar_examples.json", "teaching")
    for example in teaching_grammar:
        all_conversations.append(create_teaching_grammar_conversation(example))
    teaching_grammar_count = len(teaching_grammar)

    feedback_vocab_correct = load_examples("feedback_vocab_correct_examples.json", "teaching")
    for example in feedback_vocab_correct:
        all_conversations.append(create_feedback_vocab_conversation(example, is_correct=True))
    feedback_vocab_correct_count = len(feedback_vocab_correct)

    feedback_vocab_incorrect = load_examples("feedback_vocab_incorrect_examples.json", "teaching")
    for example in feedback_vocab_incorrect:
        all_conversations.append(create_feedback_vocab_conversation(example, is_correct=False))
    feedback_vocab_incorrect_count = len(feedback_vocab_incorrect)

    feedback_grammar_correct = load_examples("feedback_grammar_correct_examples.json", "teaching")
    for example in feedback_grammar_correct:
        all_conversations.append(create_feedback_grammar_conversation(example, is_correct=True))
    feedback_grammar_correct_count = len(feedback_grammar_correct)

    feedback_grammar_incorrect = load_examples(
        "feedback_grammar_incorrect_examples.json", "teaching"
    )
    for example in feedback_grammar_incorrect:
        all_conversations.append(create_feedback_grammar_conversation(example, is_correct=False))
    feedback_grammar_incorrect_count = len(feedback_grammar_incorrect)

    output_file = output_dir / "teaching_mode_training_data.jsonl"
    write_jsonl(all_conversations, output_file)

    feedback_vocab_total = feedback_vocab_correct_count + feedback_vocab_incorrect_count
    feedback_grammar_total = feedback_grammar_correct_count + feedback_grammar_incorrect_count

    print("\nBreakdown:")
    print(f"  - Lesson start: {lesson_start_count} conversations")
    print(f"  - Teaching vocab: {teaching_vocab_count} conversations")
    print(f"  - Teaching grammar: {teaching_grammar_count} conversations")
    print(
        f"  - Feedback vocab: {feedback_vocab_total} conversations ({feedback_vocab_correct_count} correct, {feedback_vocab_incorrect_count} incorrect)"
    )
    print(
        f"  - Feedback grammar: {feedback_grammar_total} conversations ({feedback_grammar_correct_count} correct, {feedback_grammar_incorrect_count} incorrect)"
    )
    print(f"  - Total: {len(all_conversations)} conversations")


if __name__ == "__main__":
    main()
