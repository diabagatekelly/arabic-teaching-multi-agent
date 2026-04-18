"""Test for teaching agent lesson start with RAG content."""


def test_teaching_agent_lesson_start_with_vocab_and_grammar():
    """Test that lesson start handles vocab and grammar without KeyError.

    Replicates HuggingFace Spaces bug: KeyError: 'total_words'
    """
    from unittest.mock import MagicMock

    from src.agents import TeachingAgent

    # Arrange: Mock model and tokenizer
    mock_model = MagicMock()
    mock_model.generate.return_value = MagicMock(sequences=[[1, 2, 3]])

    mock_tokenizer = MagicMock()
    mock_tokenizer.apply_chat_template.return_value = "formatted_prompt"
    mock_tokenizer.return_value = {"input_ids": MagicMock(), "attention_mask": MagicMock()}
    mock_tokenizer.decode.return_value = "Welcome to Lesson 1! We have 3 words to learn."

    agent = TeachingAgent(model=mock_model, tokenizer=mock_tokenizer, max_new_tokens=256)

    # Mock generate_response to return a string
    agent.generate_response = MagicMock(
        return_value="Welcome to Lesson 1! We have 3 words to learn."
    )

    # Input data formatted like TeachingNode._handle_lesson_start sends it
    input_data = {
        "lesson_number": 1,
        "mode": "lesson_start",
        "total_words": 3,
        "topics_preview": "1. كِتَاب (kitaabun) - book\n\n2. بَيْت (baytun) - house\n\n3. قَلَم (qalamun) - pen",
        "topics_count": 2,
        "grammar_topics": "Gender, Definite Article",
    }

    # Act: Should not raise KeyError
    response = agent.start_lesson(input_data)

    # Assert: Response generated without error
    assert response is not None
    assert isinstance(response, str)
