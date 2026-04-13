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

    example_files = [
        "fill_in_blank_examples.json",
        "translation_examples.json",
        "correction_examples.json",
    ]

    all_conversations: list[dict] = []

    for example_file in example_files:
        examples = load_examples(example_file, "exercise_generation")
        conversations = [create_exercise_conversation(ex) for ex in examples]
        all_conversations.extend(conversations)
        print(f"✓ Loaded {len(conversations)} conversations from {example_file}")

    output_file = output_dir / "exercise_generation_training_data.jsonl"
    write_jsonl(all_conversations, output_file)

    print("\nBreakdown:")
    print("  - Fill-in-blank: 15 conversations")
    print("  - Translation: 10 conversations")
    print("  - Correction: 5 conversations")
    print(f"  - Total: {len(all_conversations)} conversations")


if __name__ == "__main__":
    main()
