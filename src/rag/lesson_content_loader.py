"""Lesson content loader using RAG retrieval.

This module provides a high-level interface for loading lesson content
from the RAG vector database. It handles vocabulary and grammar retrieval
and formats the data for use by the teaching agents.
"""

from __future__ import annotations

import logging
import re
from typing import Any

from src.rag.rag_retriever import RAGRetriever

logger = logging.getLogger(__name__)


class LessonContentLoader:
    """Loads lesson content from RAG database for teaching agents."""

    def __init__(self, retriever: RAGRetriever):
        """
        Initialize lesson content loader.

        Args:
            retriever: RAG retriever for querying vector database
        """
        self.retriever = retriever

    def load_vocabulary(self, lesson_number: int) -> list[dict[str, str]]:
        """
        Load all vocabulary words for a lesson.

        Args:
            lesson_number: Lesson number to load

        Returns:
            List of vocabulary items with arabic, transliteration, english, word_id
        """
        # Query for vocabulary sections in this lesson
        query = f"vocabulary words lesson {lesson_number}"
        results = self.retriever.retrieve_by_lesson(query, lesson_number, top_k=10)

        logger.info(f"Retrieved {len(results)} chunks for lesson {lesson_number} vocabulary")

        vocab_words = []
        word_id = 1

        for i, result in enumerate(results):
            text = result["text"]
            metadata = result.get("metadata", {})
            section_title = metadata.get("section_title", "unknown")

            # Log each chunk
            has_vocab_keyword = "vocabulary" in text.lower() or "vocab" in section_title.lower()
            logger.info(f"Chunk {i+1}: '{section_title}' - has_vocab_keyword={has_vocab_keyword}")

            # Check if this chunk contains vocabulary
            if has_vocab_keyword:
                # Extract words from tables or frontmatter
                words = self._extract_vocabulary_from_text(text)
                logger.info(f"Chunk {i+1}: Extracted {len(words)} words from '{section_title}'")
                for word in words:
                    word["word_id"] = f"w{word_id}"
                    word_id += 1
                    vocab_words.append(word)

        logger.info(
            f"Total vocabulary words extracted for lesson {lesson_number}: {len(vocab_words)}"
        )
        return vocab_words

    def load_grammar(self, lesson_number: int) -> dict[str, dict[str, Any]]:
        """
        Load all grammar content for a lesson.

        Args:
            lesson_number: Lesson number to load

        Returns:
            Dict mapping grammar topics to their content (rule, examples, etc.)
        """
        # Query for grammar sections in this lesson
        query = f"grammar rules lesson {lesson_number}"
        results = self.retriever.retrieve_by_lesson(query, lesson_number, top_k=20)

        grammar_content = {}

        for result in results:
            text = result["text"]
            metadata = result.get("metadata", {})
            section_title = metadata.get("section_title", "")

            # Check if this is a grammar section
            if "grammar" in section_title.lower() or "rule" in text.lower():
                topic_name = self._extract_topic_name(section_title, text)
                if topic_name:
                    grammar_content[topic_name] = {
                        "rule": self._extract_rule(text),
                        "examples": self._extract_examples(text),
                        "detection_pattern": self._extract_detection_pattern(text),
                        "full_text": text,
                    }

        return grammar_content

    def _extract_vocabulary_from_text(self, text: str) -> list[dict[str, str]]:
        """Extract vocabulary words from markdown text."""
        words = []

        # Pattern 1: Table format with Arabic | Transliteration | English
        table_pattern = r"\|\s*([^\|]+?)\s*\|\s*([^\|]+?)\s*\|\s*([^\|]+?)\s*\|"
        for match in re.finditer(table_pattern, text):
            arabic = match.group(1).strip()
            transliteration = match.group(2).strip()
            english = match.group(3).strip()

            # Skip table headers
            if arabic.lower() in ["arabic", "word"] or "-" in arabic:
                continue

            # Extract just the Arabic word (remove tanween markers if present)
            arabic_clean = re.sub(r"[ًٌٍ]", "", arabic)

            if arabic_clean and transliteration and english:
                words.append(
                    {
                        "arabic": arabic_clean,
                        "transliteration": transliteration,
                        "english": english,
                    }
                )

        # Pattern 2: Inline format like "كِتَابٌ (kitaabun) - book"
        inline_pattern = r"([ء-ي]+[ًٌٍَُِّْ]*)\s*\(([^)]+)\)\s*-\s*(.+?)(?:\n|$)"
        for match in re.finditer(inline_pattern, text):
            arabic = match.group(1).strip()
            transliteration = match.group(2).strip()
            english = match.group(3).strip()

            # Remove tanween
            arabic_clean = re.sub(r"[ًٌٍ]", "", arabic)

            if arabic_clean and transliteration and english:
                words.append(
                    {
                        "arabic": arabic_clean,
                        "transliteration": transliteration,
                        "english": english,
                    }
                )

        return words

    def _extract_rule(self, text: str) -> str:
        """Extract the main grammar rule from text."""
        # Look for "Rule" section or first paragraph
        rule_match = re.search(r"### Rule\s*\n+(.+?)(?:\n\n|\n###)", text, re.DOTALL)
        if rule_match:
            return rule_match.group(1).strip()

        # Fallback: first paragraph
        paragraphs = text.split("\n\n")
        for para in paragraphs:
            if len(para) > 20 and not para.startswith("#"):
                return para.strip()

        return text[:200]  # Truncate if nothing else works

    def _extract_examples(self, text: str) -> list[str]:
        """Extract example sentences from text."""
        examples = []

        # Look for bullet points or numbered lists with Arabic
        list_pattern = r"^[\-\*\d\.]\s*(.+[ء-ي].+)$"
        for match in re.finditer(list_pattern, text, re.MULTILINE):
            example = match.group(1).strip()
            if example:
                examples.append(example)

        # If no list examples, look for table rows with Arabic
        if not examples:
            table_pattern = r"\|\s*([^\|]*[ء-ي][^\|]*)\s*\|"
            for match in re.finditer(table_pattern, text):
                example = match.group(1).strip()
                if example and len(example) > 5:
                    examples.append(example)

        return examples[:5]  # Limit to 5 examples

    def _extract_detection_pattern(self, text: str) -> str:
        """Extract grading detection pattern if present."""
        pattern_match = re.search(r"Detection Pattern.*?\n+```\s*\n(.+?)\n```", text, re.DOTALL)
        if pattern_match:
            return pattern_match.group(1).strip()
        return ""

    def _extract_topic_name(self, section_title: str, text: str) -> str:
        """Extract grammar topic name from section title or text."""
        # Clean section title
        if section_title:
            # Remove "Grammar Point N:" prefix
            topic = re.sub(r"Grammar Point \d+:\s*", "", section_title, flags=re.IGNORECASE)
            if topic:
                return topic.strip().lower().replace(" ", "_")

        # Fallback: look for ## headers in text
        header_match = re.search(r"^##\s+(.+)$", text, re.MULTILINE)
        if header_match:
            topic = header_match.group(1).strip()
            return topic.lower().replace(" ", "_")

        return "unknown_topic"
