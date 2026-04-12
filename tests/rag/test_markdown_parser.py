"""Tests for Markdown parser."""

from pathlib import Path
from unittest.mock import patch

import pytest

from src.rag.markdown_parser import MarkdownParser


class TestMarkdownParser:
    """Test suite for MarkdownParser."""

    @pytest.fixture
    def parser(self):
        """Fixture for MarkdownParser instance."""
        return MarkdownParser()

    @pytest.fixture
    def sample_lesson_content(self):
        """Sample lesson markdown content with frontmatter."""
        return """---
lesson_number: 1
lesson_name: "Gender and Definite Article"
grammar_points:
  - masculine_feminine_nouns
  - definite_article_al
difficulty: beginner
---

# Lesson 1: Gender and Definite Article

## Overview

This lesson introduces two fundamental concepts in Arabic.

## Grammar Point 1: Masculine Nouns

Arabic nouns are either masculine or feminine.

### Examples

- كِتَابٌ (kitaabun) - book
- بَيْتٌ (baytun) - house

## Grammar Point 2: Definite Article

The definite article ال (al-) makes nouns definite.
"""

    @pytest.fixture
    def sample_exercise_content(self):
        """Sample exercise markdown content with frontmatter."""
        return """---
exercise_type: fill_in_blank
grammar_point: gender_agreement
difficulty: beginner
lesson_number: 1
---

# Fill-in-Blank Exercise

## Exercise Purpose

Test student's ability to identify noun gender.

## Template Structure

Question format and rules.
"""

    @pytest.mark.parametrize(
        "content_fixture,expected_fields",
        [
            (
                "sample_lesson_content",
                {
                    "lesson_number": 1,
                    "lesson_name": "Gender and Definite Article",
                    "grammar_points": ["masculine_feminine_nouns", "definite_article_al"],
                    "difficulty": "beginner",
                },
            ),
            (
                "sample_exercise_content",
                {
                    "exercise_type": "fill_in_blank",
                    "grammar_point": "gender_agreement",
                    "difficulty": "beginner",
                    "lesson_number": 1,
                },
            ),
        ],
    )
    def test_parse_frontmatter(self, parser, content_fixture, expected_fields, request):
        """Test parsing YAML frontmatter with various field types."""
        content = request.getfixturevalue(content_fixture)
        metadata = parser.parse_frontmatter(content)

        for key, value in expected_fields.items():
            assert metadata[key] == value

    def test_parse_frontmatter_missing(self, parser):
        """Test parsing content without frontmatter returns empty dict."""
        content = "# Just a title\n\nSome content"
        metadata = parser.parse_frontmatter(content)

        assert metadata == {}

    def test_extract_sections(self, parser, sample_lesson_content):
        """Test extracting markdown sections by ## headers."""
        sections = parser.extract_sections(sample_lesson_content)

        assert len(sections) == 3

        assert sections[0]["title"] == "Overview"
        assert sections[0]["content"].startswith("This lesson introduces")
        assert "Grammar Point" not in sections[0]["content"]

        assert sections[1]["title"] == "Grammar Point 1: Masculine Nouns"
        assert "Arabic nouns are either masculine or feminine" in sections[1]["content"]
        assert sections[1]["content"].count("###") == 1

        assert sections[2]["title"] == "Grammar Point 2: Definite Article"
        assert "The definite article" in sections[2]["content"]
        assert "Overview" not in sections[2]["content"]

    def test_extract_sections_includes_subsections(self, parser, sample_lesson_content):
        """Test that subsections (###) are included in parent section."""
        sections = parser.extract_sections(sample_lesson_content)

        grammar_section = sections[1]
        assert "Examples" in grammar_section["content"]
        assert "كِتَابٌ" in grammar_section["content"]

    def test_extract_sections_no_sections(self, parser):
        """Test content without ## sections returns empty list."""
        content = "---\ntitle: test\n---\n\n# Title\n\nJust content"
        sections = parser.extract_sections(content)

        assert sections == []

    def test_parse_file_returns_chunks(self, parser, tmp_path):
        """Test parsing a file returns list of chunks with metadata."""
        lesson_file = tmp_path / "lesson_test.md"
        lesson_file.write_text("""---
lesson_number: 1
lesson_name: "Test Lesson"
grammar_points: [test_grammar]
difficulty: beginner
---

# Test Lesson

## Section 1

Content for section 1.

## Section 2

Content for section 2.
""")

        chunks = parser.parse_file(lesson_file)

        assert len(chunks) == 2

        assert chunks[0]["text"] == "Section 1\n\nContent for section 1."
        assert chunks[0]["metadata"]["lesson_number"] == 1
        assert chunks[0]["metadata"]["lesson_name"] == "Test Lesson"
        assert chunks[0]["metadata"]["grammar_points"] == ["test_grammar"]
        assert chunks[0]["metadata"]["section_title"] == "Section 1"
        assert chunks[0]["metadata"]["source_file"] == "lesson_test.md"
        assert chunks[0]["metadata"]["doc_type"] == "lesson"

        assert chunks[1]["text"] == "Section 2\n\nContent for section 2."
        assert chunks[1]["metadata"]["section_title"] == "Section 2"

    def test_parse_file_exercise_type(self, parser, tmp_path):
        """Test parsing exercise file has correct doc_type."""
        exercise_file = tmp_path / "exercise_test.md"
        exercise_file.write_text("""---
exercise_type: fill_in_blank
grammar_point: test
---

# Exercise

## Section 1

Content.
""")

        chunks = parser.parse_file(exercise_file)

        assert chunks[0]["metadata"]["doc_type"] == "exercise"
        assert chunks[0]["metadata"]["exercise_type"] == "fill_in_blank"

    def test_parse_file_not_found(self, parser):
        """Test parsing non-existent file raises FileNotFoundError."""
        with pytest.raises(FileNotFoundError):
            parser.parse_file(Path("nonexistent.md"))

    def test_parse_directory(self, parser, tmp_path):
        """Test parsing all markdown files in a directory."""
        (tmp_path / "lesson_01.md").write_text("""---
lesson_number: 1
---
# Lesson 1
## Section
Content.
""")
        (tmp_path / "lesson_02.md").write_text("""---
lesson_number: 2
---
# Lesson 2
## Section
Content.
""")
        (tmp_path / "README.md").write_text("# README")

        chunks = parser.parse_directory(tmp_path)

        assert len(chunks) == 2
        lesson_numbers = {c["metadata"]["lesson_number"] for c in chunks}
        assert lesson_numbers == {1, 2}

    def test_chunk_long_content(self, parser):
        """Test chunking long content splits at paragraph boundaries."""
        short_p1 = "Paragraph 1."
        oversized_p2 = "Word " * 200
        short_p3 = "Paragraph 2."
        long_content = f"{short_p1}\n\n{oversized_p2}\n\n{short_p3}"

        chunks = parser.chunk_content(long_content, max_chunk_size=500)

        assert len(chunks) == 4
        assert all(len(chunk) <= 500 for chunk in chunks)
        assert chunks[0] == short_p1
        assert chunks[-1] == short_p3

        combined = "\n\n".join(chunks)
        original_words = long_content.replace("\n\n", " ").split()
        combined_words = combined.replace("\n\n", " ").split()
        assert original_words == combined_words

    def test_chunk_short_content(self, parser):
        """Test chunking short content returns single chunk."""
        short_content = "This is short content."

        chunks = parser.chunk_content(short_content, max_chunk_size=500)

        assert len(chunks) == 1
        assert chunks[0] == short_content

    def test_chunk_multiple_paragraphs_within_limit(self, parser):
        """Test chunking multiple paragraphs that fit in one chunk."""
        content = "Paragraph 1 with some text.\n\nParagraph 2 with more text.\n\nParagraph 3."

        chunks = parser.chunk_content(content, max_chunk_size=500)

        assert len(chunks) == 1
        assert chunks[0] == content

    def test_chunk_splits_large_paragraphs(self, parser):
        """Test chunking splits paragraphs exceeding limit."""
        content = "A" * 300 + "\n\n" + "B" * 300

        chunks = parser.chunk_content(content, max_chunk_size=400)

        assert len(chunks) == 2
        assert all(len(c) <= 400 for c in chunks)
        assert chunks[0] == "A" * 300
        assert chunks[1] == "B" * 300

    def test_chunk_combines_small_paragraphs(self, parser):
        """Test chunking combines multiple small paragraphs."""
        content = "A" * 150 + "\n\n" + "B" * 150 + "\n\n" + "C" * 150 + "\n\n" + "D" * 150

        chunks = parser.chunk_content(content, max_chunk_size=350)

        assert len(chunks) == 2
        assert all(len(c) <= 350 for c in chunks)
        assert "A" * 150 in chunks[0] and "B" * 150 in chunks[0]
        assert "C" * 150 in chunks[1] and "D" * 150 in chunks[1]

    def test_chunk_massive_single_paragraph(self, parser):
        """Test chunking handles single paragraph exceeding max size."""
        massive_paragraph = "Word " * 500

        chunks = parser.chunk_content(massive_paragraph, max_chunk_size=500)

        assert len(chunks) > 1
        assert all(len(c) <= 500 for c in chunks)
        combined = "".join(chunks)
        assert combined == massive_paragraph

    def test_parse_frontmatter_invalid_yaml(self, parser):
        """Test parsing content with invalid YAML frontmatter returns empty dict."""
        content = """---
invalid: yaml: content: [
---

# Content"""

        metadata = parser.parse_frontmatter(content)

        assert metadata == {}

    def test_parse_directory_handles_expected_errors(self, tmp_path):
        """Test parsing directory continues when expected errors occur."""
        (tmp_path / "valid.md").write_text("""---
lesson_number: 1
---
# File 1
## Section
Content.""")

        parser = MarkdownParser()

        # Mock parse_file to raise OSError for one file
        original_parse_file = parser.parse_file

        def mock_parse_file(file_path: Path):
            if file_path.name == "error.md":
                raise OSError("Simulated I/O error")
            return original_parse_file(file_path)

        (tmp_path / "error.md").write_text("# Some content")

        with patch.object(parser, "parse_file", side_effect=mock_parse_file):
            chunks = parser.parse_directory(tmp_path)

        assert len(chunks) == 1
        assert chunks[0]["metadata"]["lesson_number"] == 1

    def test_parse_directory_unexpected_errors_propagate(self, tmp_path):
        """Test parsing directory does NOT catch unexpected errors."""
        (tmp_path / "file1.md").write_text("""---
lesson_number: 1
---
# File 1
## Section
Content.""")

        parser = MarkdownParser()

        # Mock parse_file to raise unexpected exception (ValueError)
        original_parse_file = parser.parse_file

        def mock_parse_file(file_path: Path):
            if file_path.name == "file1.md":
                raise ValueError("Unexpected error - should propagate!")
            return original_parse_file(file_path)

        with patch.object(parser, "parse_file", side_effect=mock_parse_file):
            # ValueError should propagate, not be caught
            with pytest.raises(ValueError, match="Unexpected error"):
                parser.parse_directory(tmp_path)

    def test_parse_file_no_frontmatter_no_sections(self, parser, tmp_path):
        """Test parsing file with no frontmatter and no sections returns empty list."""
        file = tmp_path / "plain.md"
        file.write_text("# Just a Title\n\nSome plain content without sections.")

        chunks = parser.parse_file(file)

        assert chunks == []

    def test_chunk_empty_content(self, parser):
        """Test chunking empty string returns single empty chunk."""
        chunks = parser.chunk_content("", max_chunk_size=500)

        assert len(chunks) == 1
        assert chunks[0] == ""

    def test_parse_frontmatter_windows_line_endings(self, parser):
        """Test parsing frontmatter with Windows line endings (CRLF)."""
        content = "---\r\nlesson_number: 1\r\nlesson_name: Test\r\n---\r\n\r\n# Content"

        metadata = parser.parse_frontmatter(content)

        assert metadata["lesson_number"] == 1
        assert metadata["lesson_name"] == "Test"

    def test_parse_frontmatter_at_eof(self, parser):
        """Test parsing frontmatter without trailing newline (EOF after ---)."""
        content = "---\nlesson_number: 1\nlesson_name: Test\n---"

        metadata = parser.parse_frontmatter(content)

        assert metadata["lesson_number"] == 1
        assert metadata["lesson_name"] == "Test"

    def test_extract_sections_windows_line_endings(self, parser):
        """Test extracting sections with Windows line endings."""
        content = "---\r\ntitle: test\r\n---\r\n\r\n## Section 1\r\n\r\nContent 1\r\n\r\n## Section 2\r\n\r\nContent 2"

        sections = parser.extract_sections(content)

        assert len(sections) == 2
        assert sections[0]["title"] == "Section 1"
        assert "Content 1" in sections[0]["content"]

    def test_parse_directory_handles_encoding_errors(self, parser, tmp_path):
        """Test parsing directory handles UnicodeDecodeError gracefully."""
        (tmp_path / "valid.md").write_text("""---
lesson_number: 1
---
# Valid
## Section
Content.""")

        invalid_file = tmp_path / "invalid.md"
        invalid_file.write_bytes(b"\xff\xfe Invalid UTF-8")

        chunks = parser.parse_directory(tmp_path)

        assert len(chunks) == 1
        assert chunks[0]["metadata"]["lesson_number"] == 1

    def test_parse_directory_handles_yaml_errors_gracefully(self, tmp_path):
        """Test parsing directory handles invalid YAML gracefully (empty metadata)."""
        (tmp_path / "bad_yaml.md").write_text("""---
invalid: yaml: [
---
## Section
Content.""")

        (tmp_path / "valid.md").write_text("""---
lesson_number: 2
---
# Valid
## Section
Content.""")

        parser = MarkdownParser()
        chunks = parser.parse_directory(tmp_path)

        assert len(chunks) == 2

        bad_yaml_chunk = next(c for c in chunks if c["metadata"]["source_file"] == "bad_yaml.md")
        valid_chunk = next(c for c in chunks if c["metadata"]["source_file"] == "valid.md")

        assert "lesson_number" not in bad_yaml_chunk["metadata"]
        assert bad_yaml_chunk["metadata"]["doc_type"] == "unknown"
        assert valid_chunk["metadata"]["lesson_number"] == 2
