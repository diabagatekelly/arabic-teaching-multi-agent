"""Content loader for pre-loading lesson data into sessions.

This module parses lesson markdown files and extracts structured data
for vocabulary, grammar rules, and examples to cache in sessions.
"""

import re
from pathlib import Path
from typing import Any

import yaml


def parse_vocabulary(vocab_list: list[str]) -> list[dict[str, str]]:
    """Parse vocabulary from YAML frontmatter.

    Args:
        vocab_list: List of vocab entries with comments like:
                   "كِتَابٌ  # kitaabun - book (m)"

    Returns:
        List of dicts with 'arabic', 'transliteration', 'english', 'gender'
    """
    vocab = []
    for entry in vocab_list:
        # Split on # to separate Arabic from comment
        if "#" not in entry:
            continue

        arabic = entry.split("#")[0].strip()
        comment = entry.split("#")[1].strip()

        # Parse comment: "kitaabun - book (m)"
        # Updated pattern to handle any word characters including non-ASCII
        match = re.match(r"([\w\u0600-\u06FF]+)\s*-\s*(.+?)\s*\(([mf])\)", comment)
        if match:
            vocab.append(
                {
                    "arabic": arabic,
                    "transliteration": match.group(1),
                    "english": match.group(2),
                    "gender": "masculine" if match.group(3) == "m" else "feminine",
                }
            )
        else:
            # Debug: print entries that don't match
            print(f"DEBUG: Failed to parse: '{comment}'")

    return vocab


def extract_grammar_sections(content: str) -> dict[str, str]:
    """Extract grammar sections from markdown content.

    Args:
        content: Markdown content after frontmatter

    Returns:
        Dict with section names as keys and content as values
    """
    sections = {}

    # Extract "Rule" section
    rule_match = re.search(r"### Rule\s*\n\n(.*?)(?=\n### |\n## |\Z)", content, re.DOTALL)
    if rule_match:
        sections["rule"] = rule_match.group(1).strip()

    # Extract "Agreement Rule" section
    agreement_match = re.search(
        r"### Agreement Rule.*?\n\n(.*?)(?=\n### |\n## |\Z)", content, re.DOTALL
    )
    if agreement_match:
        sections["agreement"] = agreement_match.group(1).strip()

    # Extract masculine examples table
    masc_match = re.search(
        r"### Examples - Masculine Nouns.*?\n\n.*?\n\n(.*?)(?=\n### |\n## |\Z)",
        content,
        re.DOTALL,
    )
    if masc_match:
        sections["masculine_examples"] = masc_match.group(1).strip()

    # Extract feminine examples table
    fem_match = re.search(
        r"### Examples - Feminine Nouns.*?\n\n.*?\n\n(.*?)(?=\n### |\n## |\Z)",
        content,
        re.DOTALL,
    )
    if fem_match:
        sections["feminine_examples"] = fem_match.group(1).strip()

    return sections


def load_lesson(lesson_number: int) -> dict[str, Any]:
    """Load and parse lesson content for caching.

    Args:
        lesson_number: Lesson number (1-10)

    Returns:
        Dict with structured lesson data:
        {
            "lesson_number": int,
            "lesson_name": str,
            "vocabulary": list[dict],
            "grammar_points": list[str],
            "grammar_sections": dict[str, str],
        }
    """
    # Locate lesson file
    lesson_dir = Path(__file__).parent / "data" / "rag_database" / "lessons"
    lesson_files = list(lesson_dir.glob(f"lesson_{lesson_number:02d}_*.md"))

    if not lesson_files:
        raise FileNotFoundError(f"No lesson file found for lesson {lesson_number}")

    lesson_path = lesson_files[0]

    # Parse frontmatter and content manually
    with open(lesson_path, encoding="utf-8") as f:
        content = f.read()

    # Split frontmatter and body
    if content.startswith("---"):
        parts = content.split("---", 2)
        frontmatter_text = parts[1]
        body = parts[2]
    else:
        raise ValueError("No frontmatter found in lesson file")

    # Parse YAML frontmatter (for non-vocab fields)
    metadata = yaml.safe_load(frontmatter_text)

    # Extract vocabulary manually from raw YAML (YAML strips # comments)
    vocab_raw = []
    in_vocab = False
    for line in frontmatter_text.split("\n"):
        if line.strip().startswith("vocabulary:"):
            in_vocab = True
            continue
        if in_vocab:
            if line.startswith("  - "):
                # This is a vocab line, keep the full line with comment
                vocab_raw.append(line.strip()[2:])  # Remove "  - " prefix
            elif not line.startswith(" "):
                # End of vocabulary section
                break

    # Parse vocabulary from raw lines (already extracted above)
    vocabulary = parse_vocabulary(vocab_raw)

    # Extract grammar sections
    grammar_sections = extract_grammar_sections(body)

    return {
        "lesson_number": metadata.get("lesson_number"),
        "lesson_name": metadata.get("lesson_name"),
        "vocabulary": vocabulary,
        "grammar_points": metadata.get("grammar_points", []),
        "grammar_sections": grammar_sections,
        "difficulty": metadata.get("difficulty"),
    }


if __name__ == "__main__":
    # Test the loader
    lesson_data = load_lesson(1)
    print(f"Lesson: {lesson_data['lesson_name']}")
    print(f"Vocabulary count: {len(lesson_data['vocabulary'])}")
    print(f"Grammar points: {lesson_data['grammar_points']}")
    print("\nFirst vocab word:")
    print(lesson_data["vocabulary"][0])
    print(f"\nGrammar sections: {list(lesson_data['grammar_sections'].keys())}")
