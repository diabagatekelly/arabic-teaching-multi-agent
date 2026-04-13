"""Integration tests for Content Agent with real RAG."""

from __future__ import annotations

import pytest

from src.agents.content_agent import ContentAgent


@pytest.mark.integration
@pytest.mark.skipif(
    True,  # Skip by default - requires Pinecone setup
    reason="Requires Pinecone RAG database (set PINECONE_API_KEY to run)",
)
def test_get_lesson_content_with_real_rag():
    """
    Integration test: get_lesson_content with real Pinecone RAG.

    Prerequisites:
    - Pinecone index created and populated with lesson data
    - Environment variable PINECONE_API_KEY set
    - RAG embeddings generated (see src/rag/load_data.py)

    To run:
        pytest tests/agents/test_content_agent_integration.py -m integration
    """
    agent = ContentAgent(
        rag_config={
            "namespace": "arabic-lessons",
            "top_k": 10,
        }
    )

    # Get Lesson 1 content
    content = agent.get_lesson_content(
        lesson_number=1,
        topic="gender",
        content_type="all",
    )

    # Verify we got real content
    assert len(content["vocab"]) > 0, "Should retrieve vocabulary from RAG"
    assert len(content["grammar"]) > 0, "Should retrieve grammar from RAG"
    assert content["metadata"]["lesson_number"] == 1
    assert content["metadata"]["topic"] == "gender"

    # Check vocab structure
    vocab_item = content["vocab"][0]
    assert vocab_item["arabic"], "Vocab should have Arabic text"
    assert vocab_item["english"], "Vocab should have English translation"
    assert vocab_item["transliteration"], "Vocab should have transliteration"


@pytest.mark.integration
@pytest.mark.skipif(
    True,
    reason="Requires Pinecone RAG database",
)
def test_generate_exercises_with_real_content():
    """
    Integration test: generate exercises from real RAG content.

    Prerequisites: Same as test_get_lesson_content_with_real_rag
    """
    agent = ContentAgent()

    # Generate exercises for Lesson 1
    exercises = agent.generate_exercises(
        lesson_number=1,
        topic="gender",
        exercise_type="multiple_choice",
        difficulty="beginner",
        count=5,
    )

    # Verify exercises generated
    assert len(exercises) > 0, "Should generate exercises"
    assert len(exercises) <= 5, "Should respect count parameter"

    # Check exercise quality
    for exercise in exercises:
        assert exercise["question"], "Exercise should have question"
        assert exercise["answer"], "Exercise should have answer"
        assert len(exercise["options"]) >= 2, "Multiple choice needs options"
        assert exercise["answer"] in exercise["options"], "Answer should be in options"


@pytest.mark.integration
@pytest.mark.skipif(
    True,
    reason="Requires Pinecone RAG database",
)
def test_full_teaching_workflow_real_rag():
    """
    Integration test: Complete teaching workflow with real RAG.

    Simulates:
    1. Agent retrieves lesson content
    2. Formats for teaching presentation
    3. Generates practice exercises

    Prerequisites: Same as test_get_lesson_content_with_real_rag
    """
    agent = ContentAgent()

    # Step 1: Get lesson content
    content = agent.get_lesson_content(lesson_number=1, topic="gender")
    assert len(content["vocab"]) > 0

    # Step 2: Format for teaching
    presentation = agent.format_for_teaching(content, format_type="presentation")
    assert "Lesson 1" in presentation
    assert len(presentation) > 100  # Should be substantial

    # Step 3: Generate exercises
    exercises = agent.generate_exercises(
        lesson_number=1,
        topic="gender",
        exercise_type="fill_in_blank",
        count=3,
    )
    assert len(exercises) > 0

    # Workflow complete - ready for Teaching Agent (Agent 1)
    assert True, "Full workflow successful"
