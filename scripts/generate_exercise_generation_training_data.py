"""Generate exercise generation training data for fine-tuning."""

from __future__ import annotations

from pathlib import Path

from training_data_builder import (
    create_exercise_conversation,
    load_examples,
    write_jsonl,
)


def main() -> None:
    """Generate all exercise generation training data and save to JSONL."""
    output_dir = Path(__file__).parent.parent / "data" / "training"

    example_files = {
        "fill_in_blank_examples.json": "Fill-in-blank",
        "translation_examples.json": "Translation",
        "correction_examples.json": "Correction",
    }

    all_conversations: list[dict] = []
    counts_by_type: dict[str, int] = {}

    for example_file, exercise_type in example_files.items():
        examples = load_examples(example_file, "exercise_generation")
        conversations = [create_exercise_conversation(ex) for ex in examples]
        all_conversations.extend(conversations)
        counts_by_type[exercise_type] = len(conversations)
        print(f"✓ Loaded {len(conversations)} conversations from {example_file}")

    output_file = output_dir / "exercise_generation_training_data.jsonl"
    write_jsonl(all_conversations, output_file)

    print("\nBreakdown:")
    print(f"  - Fill-in-blank: {counts_by_type['Fill-in-blank']} conversations")
    print(f"  - Translation: {counts_by_type['Translation']} conversations")
    print(f"  - Correction: {counts_by_type['Correction']} conversations")
    print(f"  - Total: {len(all_conversations)} conversations")


if __name__ == "__main__":
    main()
