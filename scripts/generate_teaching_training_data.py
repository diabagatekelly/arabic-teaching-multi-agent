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

    teaching_vocab = load_examples("teaching_vocab_examples.json", "teaching")
    for example in teaching_vocab:
        all_conversations.append(create_teaching_conversation(example))

    teaching_grammar = load_examples("teaching_grammar_examples.json", "teaching")
    for example in teaching_grammar:
        all_conversations.append(create_teaching_grammar_conversation(example))

    feedback_vocab_correct = load_examples("feedback_vocab_correct_examples.json", "teaching")
    for example in feedback_vocab_correct:
        all_conversations.append(create_feedback_vocab_conversation(example, is_correct=True))

    feedback_vocab_incorrect = load_examples("feedback_vocab_incorrect_examples.json", "teaching")
    for example in feedback_vocab_incorrect:
        all_conversations.append(create_feedback_vocab_conversation(example, is_correct=False))

    feedback_grammar_correct = load_examples("feedback_grammar_correct_examples.json", "teaching")
    for example in feedback_grammar_correct:
        all_conversations.append(create_feedback_grammar_conversation(example, is_correct=True))

    feedback_grammar_incorrect = load_examples(
        "feedback_grammar_incorrect_examples.json", "teaching"
    )
    for example in feedback_grammar_incorrect:
        all_conversations.append(create_feedback_grammar_conversation(example, is_correct=False))

    output_file = output_dir / "teaching_mode_training_data.jsonl"
    write_jsonl(all_conversations, output_file)

    print("\nBreakdown:")
    print("  - Lesson start: 5 conversations")
    print("  - Teaching vocab: 6 conversations")
    print("  - Teaching grammar: 10 conversations")
    print("  - Feedback vocab: 10 conversations (5 correct, 5 incorrect)")
    print("  - Feedback grammar: 10 conversations (6 correct, 4 incorrect)")
    print(f"  - Total: {len(all_conversations)} conversations")


if __name__ == "__main__":
    main()
