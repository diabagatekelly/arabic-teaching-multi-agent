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
    vocab_correct_count = len(vocab_correct)

    vocab_incorrect = load_examples("vocab_incorrect_examples.json", "grading")
    for example in vocab_incorrect:
        all_conversations.append(create_grading_vocab_conversation(example, is_correct=False))
    vocab_incorrect_count = len(vocab_incorrect)

    grammar_correct = load_examples("grammar_correct_examples.json", "grading")
    for example in grammar_correct:
        all_conversations.append(create_grading_grammar_conversation(example, is_correct=True))
    grammar_correct_count = len(grammar_correct)

    grammar_incorrect = load_examples("grammar_incorrect_examples.json", "grading")
    for example in grammar_incorrect:
        all_conversations.append(create_grading_grammar_conversation(example, is_correct=False))
    grammar_incorrect_count = len(grammar_incorrect)

    grammar_multiple = load_examples("grammar_multiple_errors_examples.json", "grading")
    for example in grammar_multiple:
        all_conversations.append(create_grading_multiple_errors_conversation(example))
    grammar_multiple_count = len(grammar_multiple)

    output_file = output_dir / "grading_mode_training_data.jsonl"
    write_jsonl(all_conversations, output_file)

    vocab_total = vocab_correct_count + vocab_incorrect_count
    grammar_total = grammar_correct_count + grammar_incorrect_count + grammar_multiple_count

    print("\nBreakdown:")
    print(
        f"  - Grading vocab: {vocab_total} conversations ({vocab_correct_count} correct, {vocab_incorrect_count} incorrect)"
    )
    print(f"  - Grading grammar: {grammar_total} conversations")
    print(f"    - {grammar_correct_count} correct (including flexible matches)")
    print(f"    - {grammar_incorrect_count} incorrect (single errors)")
    print(f"    - {grammar_multiple_count} multiple errors (batch grading)")
    print(f"  - Total: {len(all_conversations)} conversations")


if __name__ == "__main__":
    main()
