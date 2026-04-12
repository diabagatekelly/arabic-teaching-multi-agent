"""Validate markdown files for RAG parser compatibility."""

import logging
import sys
from pathlib import Path
from typing import Any

# Add src to path (go up from scripts/ to project root, then into src/)
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from rag.markdown_parser import MarkdownParser

# Chunk size thresholds (in characters)
CHUNK_MIN_OPTIMAL = 400  # Below this is acceptable but not optimal
CHUNK_MAX_OPTIMAL = 2000  # Above this is acceptable but not optimal
CHUNK_MIN_WARN = 200  # Below this triggers warning (too small)
CHUNK_MAX_WARN = 2000  # Above this triggers warning (large, consider splitting)
CHUNK_MAX_FAIL = 3000  # Above this triggers failure (too large, must split)

# Token estimation (rough approximation: 1 token ≈ 4 chars)
CHARS_PER_TOKEN = 4

logger = logging.getLogger(__name__)


def validate_file(file_path: Path) -> dict[str, Any]:
    """
    Validate a single markdown file for RAG compatibility.

    Returns dict with validation results.
    """
    parser = MarkdownParser()

    result = {
        "file": file_path.name,
        "path": str(file_path),
        "status": "PASS",
        "frontmatter_valid": False,
        "sections": [],
        "chunks": [],
        "issues": [],
        "warnings": [],
    }

    try:
        # Read file
        content = file_path.read_text(encoding="utf-8")

        # Check frontmatter
        metadata = parser.parse_frontmatter(content)
        if metadata:
            result["frontmatter_valid"] = True
            result["metadata"] = metadata
        else:
            result["issues"].append("No valid frontmatter found")
            result["status"] = "FAIL"

        # Parse sections
        sections = parser.extract_sections(content)
        if not sections:
            result["warnings"].append("No ## sections found in file")

        # Parse full file to get chunks
        chunks = parser.parse_file(file_path)
        result["chunks"] = chunks

        # Analyze chunk sizes
        for chunk in chunks:
            text = chunk["text"]
            size = len(text)
            tokens_est = size // CHARS_PER_TOKEN
            section_title = chunk["metadata"].get("section_title", "Unknown")

            chunk_info = {
                "section": section_title,
                "chars": size,
                "tokens": tokens_est,
                "status": "OK",
            }

            # Check size against thresholds
            if size > CHUNK_MAX_FAIL:
                chunk_info["status"] = "TOO_LARGE"
                result["issues"].append(
                    f"Section '{section_title}' is too large: {size} chars (~{tokens_est} tokens)"
                )
                result["status"] = "FAIL"
            elif size > CHUNK_MAX_WARN:
                chunk_info["status"] = "LARGE"
                result["warnings"].append(
                    f"Section '{section_title}' is large: {size} chars (~{tokens_est} tokens). Consider splitting."
                )
                if result["status"] == "PASS":
                    result["status"] = "WARNING"
            elif size < CHUNK_MIN_WARN:
                chunk_info["status"] = "SMALL"
                result["warnings"].append(
                    f"Section '{section_title}' is small: {size} chars (~{tokens_est} tokens). Consider merging."
                )
                if result["status"] == "PASS":
                    result["status"] = "WARNING"

            result["sections"].append(chunk_info)

    except FileNotFoundError:
        result["status"] = "FAIL"
        result["issues"].append("File not found")
    except UnicodeDecodeError:
        result["status"] = "FAIL"
        result["issues"].append("File encoding error (not UTF-8)")
    except Exception:
        # Log full details so unexpected operational issues are not mistaken for parse errors
        logger.exception("Unexpected error while validating RAG content")
        result["status"] = "FAIL"
        result["issues"].append(
            "Unexpected internal error during validation (see logs for details)"
        )

    return result


def print_validation_result(result: dict[str, Any]) -> None:
    """Print validation result in a nice format."""

    status_icons = {
        "PASS": "✅",
        "WARNING": "⚠️",
        "FAIL": "❌",
    }

    icon = status_icons.get(result["status"], "❓")

    print(f"\n📋 Validating: {result['path']}")
    print("━" * 60)

    # Frontmatter
    if result["frontmatter_valid"]:
        print("✅ Frontmatter: Valid YAML")
        if "metadata" in result:
            for key, val in result["metadata"].items():
                if key not in ["source_file", "doc_type"]:
                    print(f"   • {key}: {val}")
        print(f"   • doc_type: {result['metadata'].get('doc_type', 'unknown')}")
    else:
        print("❌ Frontmatter: Missing or invalid")

    # Sections
    if result["sections"]:
        print(f"\n✅ Section Structure: {len(result['sections'])} sections found")
        for section in result["sections"]:
            status_icon = (
                "✅"
                if section["status"] == "OK"
                else "⚠️"
                if section["status"] in ["LARGE", "SMALL"]
                else "❌"
            )
            print(
                f"   {status_icon} {section['section']}: {section['chars']} chars (~{section['tokens']} tokens)"
            )

    # Chunk analysis summary
    if result["chunks"]:
        sizes = [len(c["text"]) for c in result["chunks"]]
        print("\n📊 Chunk Analysis:")
        print(f"   Total chunks: {len(sizes)}")
        print(
            f"   Size range: {min(sizes)} - {max(sizes)} chars "
            f"({min(sizes) // CHARS_PER_TOKEN} - {max(sizes) // CHARS_PER_TOKEN} tokens)"
        )

        # Distribution
        optimal = sum(1 for s in sizes if CHUNK_MIN_OPTIMAL <= s <= CHUNK_MAX_OPTIMAL)
        if optimal == len(sizes):
            print(
                f"   ✅ All chunks in optimal range ({CHUNK_MIN_OPTIMAL}-{CHUNK_MAX_OPTIMAL} chars)"
            )
        else:
            print(
                f"   {optimal}/{len(sizes)} chunks in optimal range "
                f"({CHUNK_MIN_OPTIMAL}-{CHUNK_MAX_OPTIMAL} chars)"
            )

    # Issues
    if result["issues"]:
        print("\n❌ Issues Found:")
        for issue in result["issues"]:
            print(f"   • {issue}")

    # Warnings
    if result["warnings"]:
        print("\n⚠️  Warnings:")
        for warning in result["warnings"]:
            print(f"   • {warning}")

    # Final status
    print(f"\n{icon} {result['status']}: ", end="")
    if result["status"] == "PASS":
        print("File is RAG-ready!")
    elif result["status"] == "WARNING":
        print("File is usable but could be improved")
    else:
        print("File needs fixes before use")

    print("━" * 60)


def validate_directory(directory: Path) -> None:
    """Validate all .md files in a directory."""

    md_files = list(directory.glob("*.md"))

    if not md_files:
        print(f"No .md files found in {directory}")
        return

    results = []
    for file_path in md_files:
        result = validate_file(file_path)
        results.append(result)
        print_validation_result(result)

    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)

    pass_count = sum(1 for r in results if r["status"] == "PASS")
    warning_count = sum(1 for r in results if r["status"] == "WARNING")
    fail_count = sum(1 for r in results if r["status"] == "FAIL")

    print(f"Total files: {len(results)}")
    print(f"✅ Pass: {pass_count}")
    print(f"⚠️  Warning: {warning_count}")
    print(f"❌ Fail: {fail_count}")
    print("=" * 60)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        # Default: validate all RAG content
        print("Validating all RAG database content...\n")
        lessons_dir = Path("data/rag_database/lessons")
        exercises_dir = Path("data/rag_database/exercises")

        if lessons_dir.exists():
            print("\n" + "=" * 60)
            print("LESSONS")
            print("=" * 60)
            validate_directory(lessons_dir)

        if exercises_dir.exists():
            print("\n" + "=" * 60)
            print("EXERCISES")
            print("=" * 60)
            validate_directory(exercises_dir)
    else:
        path = Path(sys.argv[1])

        if path.is_file():
            result = validate_file(path)
            print_validation_result(result)
        elif path.is_dir():
            validate_directory(path)
        else:
            print(f"Error: {path} is not a file or directory")
            sys.exit(1)
