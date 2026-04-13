"""Combine all training data into a single JSONL file for fine-tuning."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


def load_training_file(file_path: Path) -> list[dict[str, Any]] | None:
    """Load conversations from a JSONL file.

    Args:
        file_path: Path to the JSONL file

    Returns:
        List of conversation dictionaries, or None if error occurred

    Note:
        Skips blank lines to avoid JSONDecodeError.
    """
    try:
        with open(file_path, encoding="utf-8") as f:
            return [json.loads(line) for line in f if line.strip()]
    except FileNotFoundError:
        print(f"❌ Error: {file_path.name} not found")
        return None
    except json.JSONDecodeError as e:
        print(f"❌ Error parsing {file_path.name}: {e}")
        return None


def validate_conversations(conversations: list[dict[str, Any]]) -> bool:
    """Validate conversation format.

    Args:
        conversations: List of conversation dictionaries

    Returns:
        True if all conversations are valid, False otherwise
    """
    if not all("messages" in c for c in conversations):
        return False
    return all(all("role" in m and "content" in m for m in c["messages"]) for c in conversations)


def main(
    input_files: list[str] | None = None,
    output_name: str = "combined_training_data.jsonl",
    validate: bool = True,
) -> None:
    """Combine all training data files.

    Args:
        input_files: List of input filenames (defaults to standard files)
        output_name: Name of the output file
        validate: Whether to validate conversation format
    """
    data_dir = Path(__file__).parent.parent / "data" / "training"

    if input_files is None:
        input_files = [
            "teaching_mode_training_data.jsonl",
            "grading_mode_training_data.jsonl",
            "exercise_generation_training_data.jsonl",
        ]

    all_conversations: list[dict[str, Any]] = []

    for filename in input_files:
        file_path = data_dir / filename
        conversations = load_training_file(file_path)

        if conversations is None:
            sys.exit(1)

        all_conversations.extend(conversations)
        print(f"✓ Loaded {len(conversations)} conversations from {filename}")

    if not all_conversations:
        print("❌ Error: No conversations loaded")
        sys.exit(1)

    output_file = data_dir / output_name
    with open(output_file, "w", encoding="utf-8") as f:
        for conversation in all_conversations:
            f.write(json.dumps(conversation, ensure_ascii=False) + "\n")

    print(f"\n✅ Combined {len(all_conversations)} total conversations")
    print(f"📁 Saved to: {output_file}")

    if validate:
        print("\n📊 Validation:")
        print(f"  - Total conversations: {len(all_conversations)}")
        print(f"  - All have 'messages' field: {all('messages' in c for c in all_conversations)}")
        print(
            f"  - All messages have roles: {all(all('role' in m for m in c['messages']) for c in all_conversations)}"
        )

        if not validate_conversations(all_conversations):
            print("\n⚠️  Warning: Some conversations have invalid format")
            sys.exit(1)

        print("\n✅ Format validation passed!")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Combine training data JSONL files into a single file"
    )
    parser.add_argument(
        "--input",
        "-i",
        nargs="+",
        help="Input JSONL files to combine (default: all standard files)",
    )
    parser.add_argument(
        "--output",
        "-o",
        default="combined_training_data.jsonl",
        help="Output filename (default: combined_training_data.jsonl)",
    )
    parser.add_argument("--no-validate", action="store_true", help="Skip format validation")

    args = parser.parse_args()

    main(input_files=args.input, output_name=args.output, validate=not args.no_validate)
