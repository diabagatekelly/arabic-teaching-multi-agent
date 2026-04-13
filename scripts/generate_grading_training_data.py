"""Generate grading mode training data for fine-tuning."""

from __future__ import annotations

from pathlib import Path

from training_data_builder import (
    create_grading_grammar_conversation,
    create_grading_multiple_errors_conversation,
    create_grading_vocab_conversation,
    load_examples,
    write_jsonl,
)


def main() -> None:
    """Generate all grading mode training data and save to JSONL."""
    output_dir = Path(__file__).parent.parent / "data" / "training"

    all_conversations: list[dict] = []

    vocab_correct = load_examples("vocab_correct_examples.json", "grading")
    for example in vocab_correct:
        all_conversations.append(create_grading_vocab_conversation(example, is_correct=True))

    vocab_incorrect = load_examples("vocab_incorrect_examples.json", "grading")
    for example in vocab_incorrect:
        all_conversations.append(create_grading_vocab_conversation(example, is_correct=False))

    grammar_correct = load_examples("grammar_correct_examples.json", "grading")
    for example in grammar_correct:
        all_conversations.append(create_grading_grammar_conversation(example, is_correct=True))

    grammar_incorrect = load_examples("grammar_incorrect_examples.json", "grading")
    for example in grammar_incorrect:
        all_conversations.append(create_grading_grammar_conversation(example, is_correct=False))

    grammar_multiple = load_examples("grammar_multiple_errors_examples.json", "grading")
    for example in grammar_multiple:
        all_conversations.append(create_grading_multiple_errors_conversation(example))

    output_file = output_dir / "grading_mode_training_data.jsonl"
    write_jsonl(all_conversations, output_file)

    print("\nBreakdown:")
    print("  - Grading vocab: 15 conversations (8 correct, 7 incorrect)")
    print("  - Grading grammar: 25 conversations")
    print("    - 10 correct (including flexible matches)")
    print("    - 10 incorrect (single errors)")
    print("    - 5 multiple errors (batch grading)")
    print(f"  - Total: {len(all_conversations)} conversations")


if __name__ == "__main__":
    main()
