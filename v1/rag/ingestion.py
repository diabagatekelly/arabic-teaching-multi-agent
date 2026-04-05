"""
Parse and ingest exercise templates into vectorstore.
"""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any

import frontmatter


def parse_template(file_path: Path) -> dict[str, Any]:
    """
    Parse a markdown template with frontmatter.

    Args:
        file_path: Path to the template file

    Returns:
        Dictionary with content and metadata
    """
    with open(file_path, encoding="utf-8") as f:
        post = frontmatter.load(f)

    return {
        "content": post.content,
        "metadata": dict(post.metadata),
        "file_path": str(file_path),
    }


def generate_doc_id(file_path: Path) -> str:
    """
    Generate a stable document ID from file path.

    Args:
        file_path: Path to the template file

    Returns:
        MD5 hash of the file path
    """
    return hashlib.md5(str(file_path).encode()).hexdigest()


def load_templates(templates_dir: str = "rag/exercise_templates") -> list[dict[str, Any]]:
    """
    Load all templates from directory.

    Args:
        templates_dir: Directory containing template markdown files

    Returns:
        List of parsed templates
    """
    templates_path = Path(templates_dir)

    if not templates_path.exists():
        raise FileNotFoundError(f"Templates directory not found: {templates_dir}")

    templates = []
    for template_file in templates_path.glob("*.md"):
        try:
            template_data = parse_template(template_file)
            template_data["id"] = generate_doc_id(template_file)
            templates.append(template_data)
        except Exception as e:
            print(f"Error parsing {template_file}: {e}")
            continue

    return templates


def prepare_for_ingestion(
    templates: list[dict[str, Any]],
) -> tuple[list[str], list[dict[str, Any]], list[str]]:
    """
    Prepare templates for ChromaDB ingestion.

    Args:
        templates: List of parsed templates

    Returns:
        Tuple of (documents, metadatas, ids)
    """
    documents = []
    metadatas = []
    ids = []

    for template in templates:
        documents.append(template["content"])

        metadata = template["metadata"].copy()
        metadata["file_path"] = template["file_path"]

        if "tags" in metadata and isinstance(metadata["tags"], list):
            metadata["tags"] = ",".join(metadata["tags"])

        metadatas.append(metadata)
        ids.append(template["id"])

    return documents, metadatas, ids
