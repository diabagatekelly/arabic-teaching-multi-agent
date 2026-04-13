"""Agent 3: Content Agent - Generates lesson content and exercises."""

from __future__ import annotations

from typing import Any

from src.rag.rag_retriever import RAGRetriever


class ContentAgent:
    """
    Agent 3: Content Agent

    Responsibilities:
    - Retrieves lesson content (vocab, grammar rules) via RAG
    - Generates exercises (fill-in-blank, multiple choice, translation)
    - Formats content for teaching agent presentation
    """

    def __init__(
        self,
        rag_retriever: RAGRetriever | None = None,
        rag_config: dict[str, Any] | None = None,
    ):
        """
        Initialize Content Agent.

        Args:
            rag_retriever: Optional RAGRetriever instance. If None, agent will work in mock mode
                          (useful for testing). In production, pass a configured RAGRetriever.
            rag_config: Optional RAG configuration (top_k, filters, etc.) used when retriever is provided.
                       If None, uses defaults.
        """
        self.rag_retriever = rag_retriever
        self.rag_config = rag_config or {}

    def get_lesson_content(
        self,
        lesson_number: int,
        topic: str,
        content_type: str = "all",
    ) -> dict[str, Any]:
        """
        Retrieve lesson content via RAG.

        Args:
            lesson_number: Lesson number (1-10)
            topic: Lesson topic (e.g., "gender", "definiteness", "plurals")
            content_type: Type of content to retrieve:
                - "vocab": vocabulary only
                - "grammar": grammar rules only
                - "all": both vocab and grammar (default)

        Returns:
            Dictionary with:
                - vocab: List of vocabulary items
                - grammar: Grammar rules/explanations
                - examples: Example sentences
                - metadata: Lesson metadata (number, topic, difficulty)

        Example:
            >>> agent = ContentAgent()
            >>> content = agent.get_lesson_content(lesson_number=1, topic="gender")
            >>> print(content["vocab"])
            [{"arabic": "كِتَابٌ", "transliteration": "kitaabun", "english": "book", ...}, ...]
        """
        # Build RAG query
        query = self._build_lesson_query(lesson_number, topic, content_type)

        # Retrieve content
        if self.rag_retriever:
            results = self.rag_retriever.retrieve(
                query=query,
                top_k=self.rag_config.get("top_k", 5),
                metadata_filter=self._build_rag_filters(lesson_number, topic, content_type),
            )
        else:
            # No retriever - return empty structure (for testing)
            results = []

        # Parse and structure results (pass known inputs for metadata fallback)
        return self._parse_lesson_content(
            results,
            content_type,
            known_metadata={"lesson_number": lesson_number, "topic": topic},
        )

    def generate_exercises(
        self,
        lesson_number: int,
        topic: str,
        exercise_type: str,
        difficulty: str = "beginner",
        count: int = 5,
    ) -> list[dict[str, Any]]:
        """
        Generate exercises for a lesson.

        Args:
            lesson_number: Lesson number (1-10)
            topic: Lesson topic
            exercise_type: Type of exercise:
                - "fill_in_blank": Fill in the blank exercises
                - "multiple_choice": Multiple choice questions
                - "translation": Translation exercises (English <-> Arabic)
                - "error_correction": Identify and correct errors
            difficulty: Exercise difficulty ("beginner", "intermediate", "advanced")
            count: Number of exercises to generate

        Returns:
            List of exercise dictionaries, each containing:
                - question: Exercise question/prompt
                - answer: Correct answer
                - options: For multiple choice (list of choices)
                - explanation: Why this is the answer
                - metadata: Exercise metadata

        Example:
            >>> agent = ContentAgent()
            >>> exercises = agent.generate_exercises(
            ...     lesson_number=1,
            ...     topic="gender",
            ...     exercise_type="multiple_choice",
            ...     count=3
            ... )
            >>> print(exercises[0])
            {
                "question": "What is the gender of كِتَابٌ (book)?",
                "options": ["masculine", "feminine"],
                "answer": "masculine",
                "explanation": "كِتَابٌ is masculine because...",
                ...
            }
        """
        # Get lesson content for exercise generation
        content = self.get_lesson_content(lesson_number, topic)

        # Generate exercises based on type
        if exercise_type == "fill_in_blank":
            return self._generate_fill_in_blank(content, count, difficulty)
        elif exercise_type == "multiple_choice":
            return self._generate_multiple_choice(content, count, difficulty)
        elif exercise_type == "translation":
            return self._generate_translation(content, count, difficulty)
        elif exercise_type == "error_correction":
            return self._generate_error_correction(content, count, difficulty)
        else:
            raise ValueError(f"Unknown exercise type: {exercise_type}")

    def format_for_teaching(
        self,
        content: dict[str, Any],
        format_type: str = "presentation",
    ) -> str:
        """
        Format content for teaching agent presentation.

        Args:
            content: Lesson content from get_lesson_content()
            format_type: How to format:
                - "presentation": Formatted for teaching/presentation
                - "reference": Formatted for student reference
                - "review": Formatted for review/practice

        Returns:
            Formatted string ready for teaching agent

        Example:
            >>> agent = ContentAgent()
            >>> content = agent.get_lesson_content(1, "gender")
            >>> formatted = agent.format_for_teaching(content, "presentation")
            >>> print(formatted)
            '''
            Lesson 1: Noun Gender

            Vocabulary:
            1. كِتَابٌ (kitaabun) - book [masculine]
            ...
            '''
        """
        if format_type == "presentation":
            return self._format_presentation(content)
        elif format_type == "reference":
            return self._format_reference(content)
        elif format_type == "review":
            return self._format_review(content)
        else:
            raise ValueError(f"Unknown format type: {format_type}")

    # ========== Private Helper Methods ==========

    def _build_lesson_query(self, lesson_number: int, topic: str, content_type: str) -> str:
        """Build RAG query string for lesson content."""
        base = f"Lesson {lesson_number}: {topic}"

        if content_type == "vocab":
            return f"{base} vocabulary words"
        elif content_type == "grammar":
            return f"{base} grammar rules and explanations"
        else:  # "all"
            return f"{base} vocabulary and grammar"

    def _build_rag_filters(
        self,
        lesson_number: int,
        topic: str,
        content_type: str,
    ) -> dict[str, Any]:
        """Build metadata filters for RAG retrieval."""
        filters = {
            "lesson_number": lesson_number,
            "topic": topic,
        }

        if content_type != "all":
            filters["content_type"] = content_type

        return filters

    def _parse_lesson_content(
        self,
        rag_results: list[dict[str, Any]],
        content_type: str,
        known_metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Parse RAG results into structured lesson content.

        Args:
            rag_results: Results from RAG retrieval
            content_type: Type of content requested ("vocab", "grammar", "all")
            known_metadata: Known metadata from input arguments (lesson_number, topic)
                           Used as fallback if RAG results don't provide metadata

        Returns:
            Structured lesson content with vocab, grammar, examples, and metadata
        """
        # Initialize with known metadata to ensure it's never empty
        known_metadata = known_metadata or {}
        parsed = {
            "vocab": [],
            "grammar": [],
            "examples": [],
            "metadata": {
                "lesson_number": known_metadata.get("lesson_number"),
                "topic": known_metadata.get("topic"),
                "difficulty": "beginner",  # Default
            },
        }

        for result in rag_results:
            metadata = result.get("metadata", {})
            text = result.get("text", "")

            # Categorize by content type (explicit comparisons to avoid substring matches)
            result_content_type = metadata.get("content_type", "")

            if result_content_type == "vocab" or content_type in ("vocab", "all"):
                parsed["vocab"].append(self._parse_vocab_item(text, metadata))

            if result_content_type == "grammar" or content_type in ("grammar", "all"):
                parsed["grammar"].append(self._parse_grammar_rule(text, metadata))

            # Extract examples
            if "example" in text.lower() or metadata.get("has_examples"):
                parsed["examples"].extend(self._extract_examples(text))

            # Enrich metadata from RAG results (only update if RAG provides better info)
            if metadata.get("difficulty") and metadata.get("difficulty") != "beginner":
                parsed["metadata"]["difficulty"] = metadata.get("difficulty")

        return parsed

    def _parse_vocab_item(self, text: str, metadata: dict[str, Any]) -> dict[str, Any]:
        """Parse vocabulary item from text."""
        # Placeholder: In production, this would parse structured vocab
        return {
            "arabic": metadata.get("arabic", ""),
            "transliteration": metadata.get("transliteration", ""),
            "english": metadata.get("english", ""),
            "part_of_speech": metadata.get("pos", "noun"),
            "gender": metadata.get("gender"),
            "root": metadata.get("root"),
        }

    def _parse_grammar_rule(self, text: str, metadata: dict[str, Any]) -> dict[str, Any]:
        """Parse grammar rule from text."""
        # Placeholder: In production, this would parse structured rules
        return {
            "rule": text,
            "category": metadata.get("category", ""),
            "examples": metadata.get("examples", []),
        }

    def _extract_examples(self, text: str) -> list[dict[str, str]]:
        """Extract example sentences from text."""
        # Placeholder: In production, this would parse examples
        return []

    def _generate_fill_in_blank(
        self,
        content: dict[str, Any],
        count: int,
        difficulty: str,
    ) -> list[dict[str, Any]]:
        """Generate fill-in-the-blank exercises."""
        # Placeholder implementation
        exercises = []
        vocab_items = content.get("vocab", [])[:count]

        for vocab in vocab_items:
            english_word = vocab.get("english", "word")
            arabic_word = vocab.get("arabic", "")
            transliteration = vocab.get("transliteration", "")

            exercises.append(
                {
                    "question": f"Complete: This is a _____ ({english_word} in Arabic)",
                    "answer": arabic_word,
                    "hint": transliteration,
                    "explanation": f"The Arabic word for {english_word} is {arabic_word}",
                    "metadata": {
                        "exercise_type": "fill_in_blank",
                        "difficulty": difficulty,
                        "vocab_item": vocab,
                    },
                }
            )

        return exercises

    def _generate_multiple_choice(
        self,
        content: dict[str, Any],
        count: int,
        difficulty: str,
    ) -> list[dict[str, Any]]:
        """Generate multiple choice exercises."""
        # Placeholder implementation
        exercises = []
        vocab_items = content.get("vocab", [])[:count]

        for vocab in vocab_items:
            # Create distractors (wrong answers)
            distractors = ["house", "teacher", "student"]  # Placeholder

            exercises.append(
                {
                    "question": f"What does {vocab.get('arabic', '')} mean?",
                    "options": [vocab.get("english", "")] + distractors[:2],
                    "answer": vocab.get("english", ""),
                    "explanation": f"{vocab.get('arabic')} means {vocab.get('english')}",
                    "metadata": {
                        "exercise_type": "multiple_choice",
                        "difficulty": difficulty,
                        "vocab_item": vocab,
                    },
                }
            )

        return exercises

    def _generate_translation(
        self,
        content: dict[str, Any],
        count: int,
        difficulty: str,
    ) -> list[dict[str, Any]]:
        """Generate translation exercises."""
        # Placeholder implementation
        exercises = []
        examples = content.get("examples", [])[:count]

        for example in examples:
            exercises.append(
                {
                    "question": f"Translate to Arabic: {example.get('english', '')}",
                    "answer": example.get("arabic", ""),
                    "explanation": f"Translation: {example.get('transliteration', '')}",
                    "metadata": {
                        "exercise_type": "translation",
                        "difficulty": difficulty,
                    },
                }
            )

        return exercises

    def _generate_error_correction(
        self,
        content: dict[str, Any],
        count: int,
        difficulty: str,
    ) -> list[dict[str, Any]]:
        """Generate error correction exercises."""
        # Placeholder implementation
        exercises = []
        grammar_rules = content.get("grammar", [])[:count]

        for rule in grammar_rules:
            exercises.append(
                {
                    "question": "Identify and correct the error: [placeholder sentence]",
                    "answer": "[corrected sentence]",
                    "error_type": rule.get("category", ""),
                    "explanation": rule.get("rule", ""),
                    "metadata": {
                        "exercise_type": "error_correction",
                        "difficulty": difficulty,
                    },
                }
            )

        return exercises

    def _format_presentation(self, content: dict[str, Any]) -> str:
        """Format content for teaching presentation."""
        metadata = content.get("metadata", {})
        vocab = content.get("vocab", [])
        grammar = content.get("grammar", [])

        output = []
        output.append(
            f"Lesson {metadata.get('lesson_number')}: {metadata.get('topic', '').title()}"
        )
        output.append("")

        if vocab:
            output.append("Vocabulary:")
            for i, item in enumerate(vocab, 1):
                output.append(
                    f"{i}. {item.get('arabic', '')} ({item.get('transliteration', '')}) - {item.get('english', '')}"
                )
            output.append("")

        if grammar:
            output.append("Grammar:")
            for rule in grammar:
                output.append(f"- {rule.get('rule', '')}")
            output.append("")

        return "\n".join(output)

    def _format_reference(self, content: dict[str, Any]) -> str:
        """Format content as reference material."""
        # Similar to presentation but more detailed
        return self._format_presentation(content)

    def _format_review(self, content: dict[str, Any]) -> str:
        """Format content for review/practice."""
        # Similar to presentation but focused on practice
        return self._format_presentation(content)
