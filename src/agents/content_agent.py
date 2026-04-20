"""Agent 3: Content Agent for exercise generation and RAG-based content retrieval."""

import json
import logging
import re
from pathlib import Path
from typing import Any

import yaml
from transformers import PreTrainedModel, PreTrainedTokenizer

logger = logging.getLogger(__name__)

# RAG database paths
PROJECT_ROOT = Path(__file__).parent.parent.parent
RAG_EXERCISES_PATH = PROJECT_ROOT / "data" / "rag_database" / "exercises"
RAG_LESSONS_PATH = PROJECT_ROOT / "data" / "rag_database" / "lessons"


class ContentAgent:
    """
    Agent 3: Content Agent (Pattern B - Provides content to other agents).

    Responsibilities:
    - Generate exercises using RAG templates
    - Compose quizzes from multiple exercises
    - Create balanced tests (vocab + grammar)
    - Retrieve lesson content and vocabulary

    Model: Fine-tuned Qwen2.5-3B-Instruct (base 3B for baseline)

    RAG Strategy:
    - Load exercise templates from data/rag_database/exercises/
    - Load lesson content from data/rag_database/lessons/
    - Use templates to guide model generation
    - Ensure consistency with curriculum

    State Management:
    - Agent is STATELESS
    - RAG database loaded at initialization
    - No session state maintained
    """

    def __init__(
        self,
        model: PreTrainedModel | None,
        tokenizer: PreTrainedTokenizer,
        max_new_tokens: int = 512,
    ) -> None:
        """
        Initialize content agent.

        Args:
            model: Fine-tuned content generation model (Qwen2.5-3B-Instruct), optional for lazy loading
            tokenizer: Model tokenizer
            max_new_tokens: Maximum tokens to generate in response
        """
        self.model = model
        self.tokenizer = tokenizer
        self.max_new_tokens = max_new_tokens
        self.rag_retriever = None  # Set externally after initialization

        # Load RAG database at initialization
        self.exercise_templates = self._load_exercise_templates()
        self.lessons = self._load_lessons()

        logger.info(
            f"ContentAgent initialized with {len(self.exercise_templates)} templates "
            f"and {len(self.lessons)} lessons"
        )

    def _load_exercise_templates(self) -> dict[str, dict]:
        """
        Load all exercise templates from RAG database.

        Templates now contain concrete JSON examples organized by difficulty.

        Returns:
            Dict mapping exercise_type to template data with parsed examples
        """
        templates = {}

        if not RAG_EXERCISES_PATH.exists():
            logger.warning(f"RAG exercises path not found: {RAG_EXERCISES_PATH}")
            return templates

        for template_file in RAG_EXERCISES_PATH.glob("*.md"):
            try:
                content = template_file.read_text(encoding="utf-8")

                # Extract YAML frontmatter
                match = re.match(r"^---\n(.*?)\n---\n(.*)$", content, re.DOTALL)
                if match:
                    frontmatter = yaml.safe_load(match.group(1))
                    markdown_content = match.group(2)

                    exercise_type = frontmatter.get("exercise_type")
                    if exercise_type:
                        # Parse examples by difficulty
                        examples_by_difficulty = self._parse_examples_from_template(
                            markdown_content
                        )

                        templates[exercise_type] = {
                            "metadata": frontmatter,
                            "content": markdown_content,
                            "examples": examples_by_difficulty,
                            "file": template_file.name,
                        }
                        logger.debug(
                            f"Loaded template: {exercise_type} with {sum(len(v) for v in examples_by_difficulty.values())} examples"
                        )

            except Exception as e:
                logger.error(f"Error loading template {template_file.name}: {e}")

        return templates

    def _parse_examples_from_template(self, content: str) -> dict[str, list[str]]:
        """
        Parse JSON examples from template markdown organized by difficulty.

        Args:
            content: Template markdown content

        Returns:
            Dict mapping difficulty level to list of example JSON strings
        """
        examples = {"beginner": [], "intermediate": [], "advanced": []}

        # Split by difficulty sections
        sections = {
            "beginner": re.search(
                r"## Beginner Examples(.*?)(?=## Intermediate|$)", content, re.DOTALL
            ),
            "intermediate": re.search(
                r"## Intermediate Examples(.*?)(?=## Advanced|$)", content, re.DOTALL
            ),
            "advanced": re.search(r"## Advanced Examples(.*?)(?=$)", content, re.DOTALL),
        }

        for difficulty, match in sections.items():
            if match:
                section_content = match.group(1)
                # Extract JSON code blocks
                json_blocks = re.findall(r"```json\n(.*?)\n```", section_content, re.DOTALL)
                examples[difficulty] = [block.strip() for block in json_blocks]

        return examples

    def _load_lessons(self) -> dict[int, dict]:
        """
        Load all lesson content from RAG database.

        Returns:
            Dict mapping lesson_number to lesson data
        """
        lessons = {}

        if not RAG_LESSONS_PATH.exists():
            logger.warning(f"RAG lessons path not found: {RAG_LESSONS_PATH}")
            return lessons

        for lesson_file in RAG_LESSONS_PATH.glob("*.md"):
            try:
                content = lesson_file.read_text(encoding="utf-8")

                # Extract YAML frontmatter
                match = re.match(r"^---\n(.*?)\n---\n(.*)$", content, re.DOTALL)
                if match:
                    frontmatter = yaml.safe_load(match.group(1))
                    markdown_content = match.group(2)

                    lesson_number = frontmatter.get("lesson_number")
                    if lesson_number:
                        lessons[lesson_number] = {
                            "metadata": frontmatter,
                            "content": markdown_content,
                            "file": lesson_file.name,
                        }
                        logger.debug(f"Loaded lesson: {lesson_number}")

            except Exception as e:
                logger.error(f"Error loading lesson {lesson_file.name}: {e}")

        return lessons

    def generate_response(self, prompt: str) -> str:
        """
        Generate response from content model.

        Args:
            prompt: Input prompt

        Returns:
            Generated content response
        """
        inputs = self.tokenizer(prompt, return_tensors="pt").to(self.model.device)

        outputs = self.model.generate(
            **inputs,
            max_new_tokens=self.max_new_tokens,
            do_sample=True,
            temperature=0.3,  # Low temperature for focused reasoning
            top_p=0.9,  # Nucleus sampling for quality
            top_k=40,  # Limit vocabulary for coherence
            repetition_penalty=1.1,  # Slight penalty to avoid repetition
            pad_token_id=self.tokenizer.eos_token_id,
        )

        response = self.tokenizer.decode(outputs[0], skip_special_tokens=True)

        # Remove the prompt from response
        if response.startswith(prompt):
            response = response[len(prompt) :].strip()

        return response

    def generate_exercise(self, input_data: dict[str, Any]) -> str:
        """
        Generate single exercise using RAG examples (few-shot learning).

        Args:
            input_data: Input with keys:
                - exercise_type: Type of exercise (translation, multiple_choice, etc.)
                - difficulty: beginner/intermediate/advanced
                - learned_items: List of vocab/grammar items to use
                - count: Number of exercises to generate (default: 1)
                - lesson_number: Optional lesson number for context

        Returns:
            JSON string with exercise data
        """
        exercise_type = input_data.get("exercise_type", "translation")
        difficulty = input_data.get("difficulty", "beginner")
        learned_items = input_data.get("learned_items", [])
        lesson_number = input_data.get("lesson_number")

        # Get RAG examples for this exercise type and difficulty
        template = self.exercise_templates.get(exercise_type)
        examples = []
        if template and "examples" in template:
            examples = template["examples"].get(difficulty, [])[:2]  # Use 2 examples

        # Get lesson vocabulary if available
        lesson_vocab = []
        if lesson_number and lesson_number in self.lessons:
            lesson_vocab = self.lessons[lesson_number]["metadata"].get("vocabulary", [])

        # Build few-shot prompt with concrete examples
        examples_text = ""
        if examples:
            examples_text = "\n\nHere are examples of the correct format:\n\n"
            for i, example in enumerate(examples, 1):
                examples_text += f"Example {i}:\n{example}\n\n"

        # Build prompt
        prompt = f"""You are an Arabic language exercise generator. Generate a single exercise following the exact format shown in the examples.

Exercise Type: {exercise_type}
Difficulty: {difficulty}
Learned Items: {", ".join(learned_items[:5])}
Lesson Vocabulary: {", ".join(lesson_vocab[:10])}
{examples_text}
CRITICAL REQUIREMENTS:
1. Output ONLY valid JSON matching the example format EXACTLY
2. Use the learned items provided above in your question
3. Include ALL fields shown in the examples: "question", "answer", "correct", "type", "difficulty"
4. The "correct" field must contain the expected answer
5. Use proper Arabic with harakaat (vowel marks) where shown in examples
6. Make the question clear and self-contained
7. NO explanations, NO markdown, NO commentary - ONLY the JSON object

Generate ONE exercise now:
"""

        response = self.generate_response(prompt)

        # Extract JSON from response (handles markdown code blocks)
        json_match = re.search(r"```json\n(.*?)\n```", response, re.DOTALL)
        if json_match:
            return json_match.group(1).strip()

        # Try to find JSON object
        json_match = re.search(r"\{.*\}", response, re.DOTALL)
        if json_match:
            return json_match.group(0).strip()

        # Return as-is if no JSON found
        return response.strip()

    def generate_quiz(self, input_data: dict[str, Any]) -> str:
        """
        Generate quiz (multiple exercises) using few-shot examples.

        Args:
            input_data: Input with keys:
                - quiz_type: vocabulary/grammar/mixed
                - count: Number of questions
                - difficulty: beginner/intermediate/advanced
                - learned_items: List of items to test
                - lesson_number: Optional lesson number

        Returns:
            JSON array of exercises
        """
        quiz_type = input_data.get("quiz_type", "mixed")
        count = input_data.get("count", 5)
        difficulty = input_data.get("difficulty", "beginner")
        learned_items = input_data.get("learned_items", [])
        lesson_number = input_data.get("lesson_number")

        # Get lesson vocabulary
        lesson_vocab = []
        if lesson_number and lesson_number in self.lessons:
            lesson_vocab = self.lessons[lesson_number]["metadata"].get("vocabulary", [])

        # Get examples from translation and multiple_choice templates
        examples_text = ""
        for ex_type in ["translation", "multiple_choice"]:
            if ex_type in self.exercise_templates:
                template = self.exercise_templates[ex_type]
                if "examples" in template:
                    type_examples = template["examples"].get(difficulty, [])[:1]
                    if type_examples:
                        examples_text += f"\n{ex_type} example:\n{type_examples[0]}\n"

        prompt = f"""You are an Arabic language quiz generator. Generate {count} questions in a JSON array.

Quiz Type: {quiz_type}
Difficulty: {difficulty}
Learned Items: {", ".join(learned_items[:10])}
Lesson Vocabulary: {", ".join(lesson_vocab[:10])}
{examples_text}

REQUIREMENTS:
1. Output ONLY a JSON array: [{{"question": "...", "answer": "...", "correct": "...", "type": "...", "difficulty": "..."}}]
2. Include ALL fields in each question: "question", "answer", "correct", "type", "difficulty"
3. Use variety (translation, multiple_choice, fill_in_blank)
4. Each question uses learned items
5. No duplicates

Generate the JSON array now:
"""

        response = self.generate_response(prompt)

        # Extract JSON array
        json_match = re.search(r"```json\n(.*?)\n```", response, re.DOTALL)
        if json_match:
            return json_match.group(1).strip()

        json_match = re.search(r"\[.*\]", response, re.DOTALL)
        if json_match:
            return json_match.group(0).strip()

        return response.strip()

    def generate_test(self, input_data: dict[str, Any]) -> str:
        """
        Generate full test (balanced vocab + grammar) using few-shot examples.

        Args:
            input_data: Input with keys:
                - question_count: Total number of questions
                - vocab_ratio: Ratio of vocabulary questions (0-1)
                - difficulty: beginner/intermediate/advanced
                - learned_items: List of items to test
                - lesson_number: Optional lesson number

        Returns:
            JSON object with test structure
        """
        question_count = input_data.get("question_count", 20)
        vocab_ratio = input_data.get("vocab_ratio", 0.5)
        difficulty = input_data.get("difficulty", "beginner")
        learned_items = input_data.get("learned_items", [])
        lesson_number = input_data.get("lesson_number")

        vocab_count = int(question_count * vocab_ratio)
        grammar_count = question_count - vocab_count

        # Get lesson info
        lesson_vocab = []
        grammar_points = []
        if lesson_number and lesson_number in self.lessons:
            lesson_meta = self.lessons[lesson_number]["metadata"]
            lesson_vocab = lesson_meta.get("vocabulary", [])
            grammar_points = lesson_meta.get("grammar_points", [])

        # Get example questions
        examples_text = ""
        for ex_type in ["translation", "fill_in_blank"]:
            if ex_type in self.exercise_templates:
                template = self.exercise_templates[ex_type]
                if "examples" in template:
                    type_examples = template["examples"].get(difficulty, [])[:1]
                    if type_examples:
                        examples_text += f"\n{ex_type} example:\n{type_examples[0]}\n"

        prompt = f"""You are an Arabic test generator. Generate a test with {question_count} questions.

Test Specifications:
- Total Questions: {question_count} (Vocab: {vocab_count}, Grammar: {grammar_count})
- Difficulty: {difficulty}
- Learned Items: {", ".join(learned_items[:10])}
- Lesson Vocabulary: {", ".join(lesson_vocab[:10])}
- Grammar Points: {", ".join(grammar_points)}
{examples_text}

REQUIREMENTS:
1. Output structure: {{"test": [...]}}
2. Each question has: "question", "answer", "correct", "type", "section" (vocab/grammar), "difficulty"
3. Mix question types
4. Balance vocab and grammar sections

Generate the test JSON now:
"""

        response = self.generate_response(prompt)

        # Extract JSON
        json_match = re.search(r"```json\n(.*?)\n```", response, re.DOTALL)
        if json_match:
            return json_match.group(1).strip()

        json_match = re.search(r"\{.*\}", response, re.DOTALL)
        if json_match:
            return json_match.group(0).strip()

        return response.strip()

    def retrieve_content(self, input_data: dict[str, Any]) -> str:
        """
        Retrieve lesson content from RAG database.

        Args:
            input_data: Input with keys:
                - lesson_number: Lesson to retrieve
                - content_type: all/vocab/grammar/exercises
                - format: presentation/practice

        Returns:
            JSON object with lesson content
        """
        lesson_number = input_data.get("lesson_number")
        content_type = input_data.get("content_type", "all")

        if lesson_number not in self.lessons:
            return json.dumps(
                {
                    "error": f"Lesson {lesson_number} not found",
                    "available_lessons": list(self.lessons.keys()),
                }
            )

        lesson = self.lessons[lesson_number]
        metadata = lesson["metadata"]
        content = lesson["content"]

        # Build response based on content_type
        response_data = {
            "lesson": lesson_number,
            "lesson_name": metadata.get("lesson_name", ""),
            "difficulty": metadata.get("difficulty", "beginner"),
        }

        if content_type in ["all", "vocab"]:
            response_data["vocabulary"] = metadata.get("vocabulary", [])

        if content_type in ["all", "grammar"]:
            response_data["grammar_points"] = metadata.get("grammar_points", [])
            # Extract grammar rules from content
            grammar_sections = re.findall(
                r"## Grammar Point.*?\n\n(.*?)(?=\n##|\Z)", content, re.DOTALL
            )
            if grammar_sections:
                response_data["grammar_rules"] = grammar_sections

        if content_type == "all":
            response_data["full_content"] = content[:1000]  # Truncate for brevity

        return json.dumps(response_data, ensure_ascii=False, indent=2)
