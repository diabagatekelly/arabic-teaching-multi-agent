"""Debug test to inspect the actual prompt sent to ContentAgent."""

from unittest.mock import MagicMock

from src.agents.content_agent import ContentAgent
from src.orchestrator.nodes import ContentNode
from src.orchestrator.state import create_initial_state


def test_inspect_prompt_with_batch_quizzed_words():
    """Capture and print the actual prompt to see if filtering is working."""

    # Setup
    mock_model = MagicMock()
    mock_tokenizer = MagicMock()
    agent = ContentAgent(model=mock_model, tokenizer=mock_tokenizer, max_new_tokens=512)

    # Spy on generate_response
    prompts_captured = []

    def spy_generate(prompt: str) -> str:
        prompts_captured.append(prompt)
        # Return valid JSON
        return """```json
{
    "exercise_id": "ex_001",
    "exercise_type": "translation",
    "question": "What does test mean?",
    "answer": "test",
    "correct": "test",
    "type": "translation",
    "difficulty": "beginner",
    "metadata": {
        "word_arabic": "test",
        "word_transliteration": "test",
        "english": "test"
    }
}
```"""

    agent.generate_response = spy_generate

    # Create state with quizzed words
    state = create_initial_state(lesson_number=1, user_id="test_user")
    state.current_vocab_batch = 1
    state.lesson_initialized = True
    state.cached_vocab_words = [
        {"arabic": "كِتَاب", "transliteration": "kitaabun", "english": "book", "word_id": "w1"},
        {"arabic": "بَيْت", "transliteration": "baytun", "english": "house", "word_id": "w2"},
        {"arabic": "قَلَم", "transliteration": "qalamun", "english": "pen", "word_id": "w3"},
    ]
    state.batch_quizzed_words = ["كِتَاب"]  # Book already quizzed

    # Generate exercise
    content_node = ContentNode(agent=agent)
    state.add_message("user", "quiz me")
    state = content_node(state)

    # Print captured prompt
    assert len(prompts_captured) == 1, "Should have called generate_response once"
    prompt = prompts_captured[0]

    print("\n" + "=" * 80)
    print("CAPTURED PROMPT:")
    print("=" * 80)
    print(prompt)
    print("=" * 80)

    # Check critical lines
    for line in prompt.split("\n"):
        if "Available Items (NOT already quizzed):" in line:
            print(f"\n✓ Available Items line: {line}")
            assert "كِتَاب" not in line, "ERROR: 'كِتَاب' should NOT be in Available Items!"
            assert "بَيْت" in line or "قَلَم" in line, "Should have house or pen available"

        if "Words Already Quizzed (DO NOT USE):" in line:
            print(f"✓ Already Quizzed line: {line}")
            assert "كِتَاب" in line, "ERROR: 'كِتَاب' should be in Already Quizzed list!"


if __name__ == "__main__":
    test_inspect_prompt_with_batch_quizzed_words()
    print("\n✅ Prompt inspection complete!")
