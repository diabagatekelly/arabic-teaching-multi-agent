"""CLI demo using HuggingFace model instead of OpenAI."""

from __future__ import annotations

import sys

from llm import TransformersProvider
from prompts.registry import get_registry

from agents import GrammarAgent, VocabularyAgent


def main() -> None:
    """Run interactive CLI demo with HuggingFace model."""
    print("=" * 60)
    print("Arabic Teaching Multi-Agent System - HuggingFace Demo")
    print("=" * 60)
    print()

    print("Loading Qwen2.5-1.5B-Instruct model...")
    print("(This will download ~1GB on first run)")
    print()

    try:
        llm = TransformersProvider(
            model_name="Qwen/Qwen2.5-1.5B-Instruct",
            device="auto",
            max_new_tokens=300,
            temperature=0.7,
        )
    except Exception as e:
        print(f"ERROR loading model: {e}")
        print("\nTip: Model will auto-download from HuggingFace")
        sys.exit(1)

    registry = get_registry()
    vocab_agent = VocabularyAgent(llm, registry)
    grammar_agent = GrammarAgent(llm, registry)

    print("✅ Agents initialized with Qwen2.5-1.5B-Instruct")
    print()

    while True:
        print("-" * 60)
        print("Choose an agent:")
        print("  1) VocabularyAgent - Test vocabulary teaching")
        print("  2) GrammarAgent - Test grammar teaching")
        print("  3) Exit")
        print()

        choice = input("Enter choice (1-3): ").strip()

        if choice == "1":
            test_vocabulary_agent(vocab_agent)
        elif choice == "2":
            test_grammar_agent(grammar_agent)
        elif choice == "3":
            print("\nGoodbye!")
            break
        else:
            print("Invalid choice")


def test_vocabulary_agent(agent: VocabularyAgent) -> None:
    """Test vocabulary agent interactively."""
    print("\n" + "=" * 60)
    print("VOCABULARY AGENT TEST")
    print("=" * 60)
    print()

    print("1. Introducing vocabulary words...")
    print("(Generating response...)")
    response = agent.introduce_words(
        lesson_number=3,
        vocabulary_list="كِتَاب (book), مَدْرَسَة (school), بَيْت (house)",
    )
    print(response)
    print()

    input("Press Enter to continue...")

    print("\n2. Assessing student answer...")
    print("(Generating response...)")
    response = agent.assess_answer(
        student_answer="كِتَاب",
        correct_answer="كِتَاب (book)",
    )
    print(response)
    print()


def test_grammar_agent(agent: GrammarAgent) -> None:
    """Test grammar agent interactively."""
    print("\n" + "=" * 60)
    print("GRAMMAR AGENT TEST")
    print("=" * 60)
    print()

    print("1. Introducing grammar concept...")
    print("(Generating response...)")
    response = agent.introduce_concept(
        lesson_number=3,
        grammar_topic="Noun-adjective gender agreement",
    )
    print(response)
    print()

    input("Press Enter to continue...")

    print("\n2. Detecting error (incorrect answer)...")
    print("(Generating response...)")
    response = agent.detect_error(
        student_answer="كتاب كبيرة",
        grammar_rule="Gender agreement",
    )
    print(response)
    print()

    input("Press Enter to continue...")

    print("\n3. Detecting correct answer...")
    print("(Generating response...)")
    response = agent.detect_error(
        student_answer="كتاب كبير",
        grammar_rule="Gender agreement",
    )
    print(response)
    print()


if __name__ == "__main__":
    main()
