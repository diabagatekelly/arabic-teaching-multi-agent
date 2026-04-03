"""Tests for RAG ingestion functionality."""

from __future__ import annotations

import tempfile
from pathlib import Path

import pytest

from rag.ingestion import (
    generate_doc_id,
    load_templates,
    parse_template,
    prepare_for_ingestion,
)


@pytest.fixture
def sample_template_file() -> Path:
    """Create a sample template file for testing."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
        f.write("""---
exercise_type: fill_in_blank
skill_focus: vocabulary
lesson: 1
tags: [vocab, test]
---

# Test Template

This is a test template content.
""")
        return Path(f.name)


def test_parse_template(sample_template_file: Path) -> None:
    """Test parsing a template with frontmatter."""
    result = parse_template(sample_template_file)

    assert "content" in result
    assert "metadata" in result
    assert result["metadata"]["exercise_type"] == "fill_in_blank"
    assert result["metadata"]["lesson"] == 1
    assert "Test Template" in result["content"]

    sample_template_file.unlink()


def test_generate_doc_id() -> None:
    """Test document ID generation."""
    path1 = Path("test/path/file.md")
    path2 = Path("test/path/file.md")
    path3 = Path("different/path/file.md")

    id1 = generate_doc_id(path1)
    id2 = generate_doc_id(path2)
    id3 = generate_doc_id(path3)

    assert id1 == id2
    assert id1 != id3
    assert len(id1) == 32


def test_prepare_for_ingestion() -> None:
    """Test preparing templates for ChromaDB ingestion."""
    templates = [
        {
            "content": "Template 1 content",
            "metadata": {
                "exercise_type": "fill_in_blank",
                "lesson": 1,
                "tags": ["vocab", "test"],
            },
            "file_path": "/path/to/template1.md",
            "id": "id1",
        },
        {
            "content": "Template 2 content",
            "metadata": {
                "exercise_type": "multiple_choice",
                "lesson": 2,
                "tags": ["grammar"],
            },
            "file_path": "/path/to/template2.md",
            "id": "id2",
        },
    ]

    documents, metadatas, ids = prepare_for_ingestion(templates)

    assert len(documents) == 2
    assert len(metadatas) == 2
    assert len(ids) == 2
    assert documents[0] == "Template 1 content"
    assert metadatas[0]["exercise_type"] == "fill_in_blank"
    assert metadatas[0]["tags"] == "vocab,test"
    assert ids[0] == "id1"


def test_load_templates() -> None:
    """Test loading templates from directory."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)

        template1 = tmpdir_path / "template1.md"
        template1.write_text("""---
exercise_type: test
lesson: 1
---
Content 1
""")

        template2 = tmpdir_path / "template2.md"
        template2.write_text("""---
exercise_type: test
lesson: 2
---
Content 2
""")

        templates = load_templates(str(tmpdir_path))

        assert len(templates) == 2
        assert all("content" in t for t in templates)
        assert all("metadata" in t for t in templates)
        assert all("id" in t for t in templates)


def test_load_templates_nonexistent_dir() -> None:
    """Test loading templates from nonexistent directory."""
    with pytest.raises(FileNotFoundError):
        load_templates("/nonexistent/directory")
