"""Shared test fixtures for agent tests."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from src.agents.content_agent import ContentAgent


@pytest.fixture
def content_agent():
    """Create a ContentAgent instance for testing."""
    # No retriever - will use mocks
    return ContentAgent(rag_retriever=None, rag_config={"namespace": "test-lessons", "top_k": 5})


@pytest.fixture
def mock_rag_results():
    """Mock RAG retrieval results."""
    return [
        {
            "id": "lesson_1_vocab_1",
            "score": 0.95,
            "text": "كِتَابٌ (kitaabun) means book in Arabic. It is a masculine noun.",
            "metadata": {
                "lesson_number": 1,
                "topic": "gender",
                "content_type": "vocab",
                "arabic": "كِتَابٌ",
                "transliteration": "kitaabun",
                "english": "book",
                "pos": "noun",
                "gender": "masculine",
            },
        },
        {
            "id": "lesson_1_vocab_2",
            "score": 0.93,
            "text": "مَدْرَسَةٌ (madrasatun) means school in Arabic. It is a feminine noun.",
            "metadata": {
                "lesson_number": 1,
                "topic": "gender",
                "content_type": "vocab",
                "arabic": "مَدْرَسَةٌ",
                "transliteration": "madrasatun",
                "english": "school",
                "pos": "noun",
                "gender": "feminine",
            },
        },
        {
            "id": "lesson_1_grammar_1",
            "score": 0.90,
            "text": "In Arabic, nouns have grammatical gender (masculine or feminine). The gender affects adjective agreement.",
            "metadata": {
                "lesson_number": 1,
                "topic": "gender",
                "content_type": "grammar",
                "category": "noun_gender",
            },
        },
    ]


@pytest.fixture
def sample_lesson_content():
    """Sample parsed lesson content."""
    return {
        "vocab": [
            {
                "arabic": "كِتَابٌ",
                "transliteration": "kitaabun",
                "english": "book",
                "part_of_speech": "noun",
                "gender": "masculine",
                "root": None,
            },
            {
                "arabic": "مَدْرَسَةٌ",
                "transliteration": "madrasatun",
                "english": "school",
                "part_of_speech": "noun",
                "gender": "feminine",
                "root": None,
            },
        ],
        "grammar": [
            {
                "rule": "In Arabic, nouns have grammatical gender (masculine or feminine). The gender affects adjective agreement.",
                "category": "noun_gender",
                "examples": [],
            }
        ],
        "examples": [],
        "metadata": {
            "lesson_number": 1,
            "topic": "gender",
            "difficulty": "beginner",
        },
    }


@pytest.fixture
def mock_retrieve(content_agent, mock_rag_results):
    """Mock the RAG retriever for testing."""
    mock_retriever = MagicMock()
    mock_retriever.retrieve.return_value = mock_rag_results
    content_agent.rag_retriever = mock_retriever
    return mock_retriever.retrieve
