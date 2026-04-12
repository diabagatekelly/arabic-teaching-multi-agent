"""Markdown parser for extracting content and metadata from RAG database files."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import yaml

# Constants
DEFAULT_CHUNK_SIZE = 1000
PARAGRAPH_SEPARATOR = "\n\n"
PARAGRAPH_SEPARATOR_LENGTH = len(PARAGRAPH_SEPARATOR)


class MarkdownParser:
    """Parser for markdown files with YAML frontmatter."""

    def parse_frontmatter(self, content: str) -> dict[str, Any]:
        """
        Extract YAML frontmatter from markdown content.

        Args:
            content: Markdown file content

        Returns:
            Dictionary of metadata from frontmatter, or empty dict if none
        """
        # Match content between --- delimiters at start of file
        match = re.match(r"^---\s*\n(.*?)\n---\s*\n", content, re.DOTALL)
        if not match:
            return {}

        frontmatter_text = match.group(1)
        try:
            return yaml.safe_load(frontmatter_text) or {}
        except yaml.YAMLError:
            return {}

    def extract_sections(self, content: str) -> list[dict[str, str]]:
        """
        Extract markdown sections by ## headers.

        Args:
            content: Markdown file content

        Returns:
            List of dicts with {title, content} for each ## section
        """
        # Remove frontmatter first
        content = re.sub(r"^---\s*\n.*?\n---\s*\n", "", content, flags=re.DOTALL)

        # Split by ## headers (but not # or ###)
        sections = []
        pattern = r"^## (.+)$"

        # Find all ## headers and their positions
        matches = list(re.finditer(pattern, content, re.MULTILINE))

        for i, match in enumerate(matches):
            title = match.group(1).strip()
            start = match.end()

            # Content ends at next ## header or end of file
            if i + 1 < len(matches):
                end = matches[i + 1].start()
            else:
                end = len(content)

            section_content = content[start:end].strip()

            sections.append({"title": title, "content": section_content})

        return sections

    def _determine_doc_type(self, metadata: dict[str, Any]) -> str:
        """
        Determine document type from metadata fields.

        Args:
            metadata: Parsed frontmatter metadata

        Returns:
            Document type: "lesson", "exercise", or "unknown"
        """
        if "lesson_number" in metadata and "lesson_name" in metadata:
            return "lesson"
        if "exercise_type" in metadata:
            return "exercise"
        return "unknown"

    def chunk_content(self, content: str, max_chunk_size: int = DEFAULT_CHUNK_SIZE) -> list[str]:
        """
        Split long content into chunks at paragraph boundaries.

        Args:
            content: Text content to chunk
            max_chunk_size: Maximum characters per chunk

        Returns:
            List of content chunks
        """
        if len(content) <= max_chunk_size:
            return [content]

        paragraphs = content.split(PARAGRAPH_SEPARATOR)
        return self._build_chunks_from_paragraphs(paragraphs, max_chunk_size)

    def _build_chunks_from_paragraphs(
        self, paragraphs: list[str], max_chunk_size: int
    ) -> list[str]:
        """Build chunks from paragraphs respecting max size."""
        chunks = []
        current_chunk = ""

        for paragraph in paragraphs:
            if len(paragraph) > max_chunk_size:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                    current_chunk = ""
                chunks.extend(self._split_large_paragraph(paragraph, max_chunk_size))
                continue

            if len(current_chunk) + len(paragraph) + PARAGRAPH_SEPARATOR_LENGTH > max_chunk_size:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                current_chunk = paragraph
            else:
                current_chunk = (
                    paragraph
                    if not current_chunk
                    else f"{current_chunk}{PARAGRAPH_SEPARATOR}{paragraph}"
                )

        if current_chunk:
            chunks.append(current_chunk.strip())

        return chunks

    def _split_large_paragraph(self, paragraph: str, max_chunk_size: int) -> list[str]:
        """Split a single large paragraph into fixed-size chunks."""
        return [paragraph[i : i + max_chunk_size] for i in range(0, len(paragraph), max_chunk_size)]

    def parse_file(self, file_path: Path) -> list[dict[str, Any]]:
        """
        Parse a markdown file into chunks with metadata.

        Args:
            file_path: Path to markdown file

        Returns:
            List of dicts with {text, metadata}

        Raises:
            FileNotFoundError: If file doesn't exist
        """
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        content = file_path.read_text(encoding="utf-8")

        # Extract metadata from frontmatter
        metadata = self.parse_frontmatter(content)

        # Add source file and document type to metadata
        metadata["source_file"] = file_path.name
        metadata["doc_type"] = self._determine_doc_type(metadata)

        # Extract sections
        sections = self.extract_sections(content)

        # Create chunks from sections
        chunks = []
        for section in sections:
            section_text = f"{section['title']}\n\n{section['content']}"

            # Add section-specific metadata
            section_metadata = metadata.copy()
            section_metadata["section_title"] = section["title"]

            chunks.append({"text": section_text, "metadata": section_metadata})

        return chunks

    def parse_directory(self, directory: Path) -> list[dict[str, Any]]:
        """
        Parse all markdown files in a directory.

        Args:
            directory: Path to directory containing markdown files

        Returns:
            List of all chunks from all files
        """
        all_chunks = []

        for file_path in directory.glob("*.md"):
            try:
                chunks = self.parse_file(file_path)
                all_chunks.extend(chunks)
            except Exception:
                # Skip files that fail to parse
                # TODO: Add logging to track parse failures for debugging
                # logger.warning(f"Failed to parse {file_path}: {e}")
                continue

        return all_chunks
