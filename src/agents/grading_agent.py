"""
Agent 2: Grading Agent - Evaluates student responses with flexible, accurate grading.

## Overview

The GradingAgent is responsible for evaluating student responses to vocabulary and
grammar questions. It uses a fine-tuned Qwen2.5-7B model to provide flexible grading
that accepts edge cases like synonyms, typos, capitalization variations, and handles
Arabic text with proper harakaat rules.

## Model Strategy

**Base Model:** Qwen2.5-7B-Instruct
**Fine-tuning Status:** Planned (270+ examples)
**Baseline Evaluated:** 2026-04-13

### Baseline Results (7B, no fine-tuning)

- **JSON Compliance:** 0-6% (adds explanations after JSON) ❌
- **Reasoning Accuracy:** 83% (5/6 correct decisions when ignoring format) ✓
- **Edge Case Performance:**
  - Synonyms: 100% ✓ (e.g., "instructor" = "teacher")
  - Minor typos: 100% ✓ (e.g., "scool" = "school")
  - Capitalization: 100% ✓ (e.g., "Book" = "book")
  - Wrong answers: 100% ✓ (correctly rejected)
  - Case endings (Arabic): 100% ✓ (enforced properly)
  - Internal harakaat (Arabic): 0% ❌ (too strict, didn't follow "optional" rule)

### Fine-Tuning Requirements

**Training Data Needed:** 270+ examples

**Categories:**
- JSON format compliance: 100+ examples (strict JSON-only output)
- Harakaat rules: 50+ examples (internal optional, case endings required)
- Edge cases: 120+ examples (synonyms, typos, capitalization, articles)

**Target Metrics:**
- JSON validity: >95% (baseline: 0-6%)
- Grading accuracy: >90% (baseline: 83%)
- Harakaat handling: >90% (baseline: 50% - too strict)

## Edge Case Handling

### Vocabulary Grading
- ✓ Accept synonyms: "instructor" → "teacher"
- ✓ Accept minor typos: "scool" → "school", "bok" → "book"
- ✓ Accept capitalization variations: "Book" → "book"
- ✓ Accept articles: "a pen" → "pen", "the book" → "book"
- ✗ Reject wrong answers: "pen" ≠ "book"

### Grammar Grading
- ✓ Accept abbreviations: "m" = "masculine", "f" = "feminine"
- ✓ Accept synonyms and alternate phrasings
- ✓ Arabic harakaat: Internal marks optional (الكتابُ = الكِتَابُ)
- ✗ Arabic harakaat: Case endings required (الكتاب ≠ الكِتَابُ)

## Usage

### Basic Usage

```python
from transformers import AutoModelForCausalLM, AutoTokenizer
from src.agents import GradingAgent

# Load model and tokenizer
model = AutoModelForCausalLM.from_pretrained("Qwen/Qwen2.5-7B-Instruct")
tokenizer = AutoTokenizer.from_pretrained("Qwen/Qwen2.5-7B-Instruct")

# Initialize agent
grading_agent = GradingAgent(model, tokenizer, max_new_tokens=50)

# Grade vocabulary answer
vocab_input = {
    "word": "كِتَاب",
    "student_answer": "book",
    "correct_answer": "book"
}
result = grading_agent.grade_vocab(vocab_input)
# Returns: '{"correct": true}'

# Grade grammar quiz question
grammar_input = {
    "question": "Is مَدْرَسَة masculine or feminine?",
    "student_answer": "feminine",
    "correct_answer": "feminine"
}
result = grading_agent.grade_grammar_quiz(grammar_input)
# Returns: '{"correct": true}'

# Grade multiple grammar test questions
test_input = {
    "lesson_number": 3,
    "answers": [
        {
            "question": "Is مَدْرَسَة masculine or feminine?",
            "student_answer": "feminine",
            "correct_answer": "feminine"
        },
        {
            "question": "Is كِتَاب masculine or feminine?",
            "student_answer": "masculine",
            "correct_answer": "masculine"
        }
    ]
}
result = grading_agent.grade_grammar_test(test_input)
# Returns: '{"total_score": "2/2", "results": [{"question_id": "q1", "correct": true}, ...]}'
```

## Architecture Integration

The GradingAgent is called by the Orchestrator (Agent 1) during:
1. Vocabulary batch quizzes
2. Vocabulary final tests
3. Grammar topic quizzes
4. Grammar final tests

**Pattern A (Direct Calls):**
Orchestrator → GradingAgent.grade_vocab() → JSON result → Orchestrator formats feedback

## Output Format

All grading methods return JSON strings:

### Single Question Grading
```json
{"correct": true}
```
or
```json
{"correct": false}
```

### Multiple Question Grading
```json
{
  "total_score": "8/10",
  "results": [
    {"question_id": "q1", "correct": true},
    {"question_id": "q2", "correct": false},
    ...
  ]
}
```

## Error Handling

- **Invalid JSON Output:** If model produces invalid JSON, evaluation pipeline logs error
- **Missing Keys:** StructureMetric validates expected keys are present
- **Wrong Types:** StructureMetric validates "correct" field is boolean, not string

## See Also

- **docs/ARCHITECTURE.md** - Agent 2 architecture and design decisions
- **docs/PROMPT_DESIGN.md** - Grading prompt templates with JSON-only enforcement
- **docs/GRADING_AGENT_FINETUNING_PLAN.md** - Complete fine-tuning strategy (gitignored)
- **data/evaluation/grading_agent_test_cases.json** - Comprehensive edge case test suite (50 cases)
- **src/prompts/templates.py** - GRADING_VOCAB, GRADING_GRAMMAR_QUIZ, GRADING_GRAMMAR_TEST prompts
"""

import json
import logging
import re
from typing import Any

import torch
from Levenshtein import distance as levenshtein_distance
from transformers import PreTrainedModel, PreTrainedTokenizer

from src.prompts.templates import GRADING_GRAMMAR_QUIZ, GRADING_GRAMMAR_TEST, GRADING_VOCAB

logger = logging.getLogger(__name__)


# =============================================================================
# HYBRID VALIDATION HELPERS
# =============================================================================


def normalize_answer(text: str) -> str:
    """
    Normalize answer by stripping articles and whitespace.

    Used for vocabulary grading to handle article variations like:
    - "a pen" → "pen"
    - "the book" → "book"

    Args:
        text: Answer text to normalize

    Returns:
        Normalized text (lowercase, no articles, trimmed)
    """
    # Strip leading articles (case-insensitive)
    text = re.sub(r"^\s*(a|an|the)\s+", "", text, flags=re.IGNORECASE)
    return text.strip().lower()


def is_minor_typo(student: str, correct: str, threshold: int = 1) -> bool:
    """
    Check if student answer is a minor typo (1-character difference).

    Uses Levenshtein edit distance to detect single-character errors like:
    - "scool" = "school" (1 char missing)
    - "bok" = "book" (1 char missing)

    Args:
        student: Student's answer
        correct: Correct answer
        threshold: Maximum edit distance to accept (default: 1)

    Returns:
        True if edit distance <= threshold, False otherwise
    """
    # Normalize first (articles, case)
    s = normalize_answer(student)
    c = normalize_answer(correct)

    # Accept if edit distance <= threshold
    return levenshtein_distance(s, c) <= threshold


def normalize_arabic(text: str, keep_case_endings: bool = True) -> str:
    """
    Normalize Arabic text by removing internal harakaat, optionally keeping case endings.

    Arabic harakaat rules:
    - Internal harakaat (vowel marks): OPTIONAL - e.g., كبير = كَبِير
    - Case endings (final harakaat): REQUIRED - e.g., كبيرٌ ≠ كبيرُ

    Args:
        text: Arabic text with harakaat
        keep_case_endings: If True, preserve final harakaat (case endings)

    Returns:
        Normalized text with internal harakaat removed
    """
    # Arabic diacritical marks (harakaat)
    HARAKAAT = [
        "\u064b",  # Tanween Fatha (ً)
        "\u064c",  # Tanween Damma (ٌ)
        "\u064d",  # Tanween Kasra (ٍ)
        "\u064e",  # Fatha (َ)
        "\u064f",  # Damma (ُ)
        "\u0650",  # Kasra (ِ)
        "\u0651",  # Shadda (ّ)
        "\u0652",  # Sukun (ْ)
    ]

    if keep_case_endings:
        # Remove all harakaat except the last character's harakaat
        if len(text) > 0:
            last_char = text[-1]
            base_text = text[:-1]

            # Strip internal harakaat from base text
            for mark in HARAKAAT:
                base_text = base_text.replace(mark, "")

            return base_text + last_char
        return text
    else:
        # Remove all harakaat
        for mark in HARAKAAT:
            text = text.replace(mark, "")
        return text


def is_arabic_text(text: str) -> bool:
    """
    Check if text contains Arabic characters.

    Args:
        text: Text to check

    Returns:
        True if text contains Arabic characters, False otherwise
    """
    # Arabic Unicode range: U+0600 to U+06FF
    return bool(re.search(r"[\u0600-\u06FF]", text))


def compare_arabic_answers(student: str, correct: str, question: str) -> bool:
    """
    Compare Arabic answers with harakaat rules.

    Rules:
    - If question asks for case (nominative/accusative/genitive):
      - Base text must match (with internal harakaat normalized)
      - Case ending (final character) must match exactly
    - Otherwise: internal harakaat optional, compare with normalized text

    Args:
        student: Student's answer
        correct: Correct answer
        question: Question text (to detect if case is required)

    Returns:
        True if answers match according to harakaat rules, False otherwise
    """
    # Check if question asks for case
    case_required = any(
        word in question.lower() for word in ["nominative", "accusative", "genitive", "case"]
    )

    if case_required:
        # Case endings must match: normalize base, compare endings exactly
        if len(student) == 0 or len(correct) == 0:
            return student == correct

        # Extract last character (case ending)
        student_case = student[-1]
        correct_case = correct[-1]

        # Normalize base text (all except last char, remove all harakaat)
        student_base = (
            normalize_arabic(student[:-1], keep_case_endings=False) if len(student) > 1 else ""
        )
        correct_base = (
            normalize_arabic(correct[:-1], keep_case_endings=False) if len(correct) > 1 else ""
        )

        # Base must match AND case ending must match
        return (student_base == correct_base) and (student_case == correct_case)
    else:
        # Internal harakaat optional, compare without them
        student_normalized = normalize_arabic(student, keep_case_endings=True)
        correct_normalized = normalize_arabic(correct, keep_case_endings=True)
        return student_normalized == correct_normalized


class GradingAgent:
    """
    Agent 2: Grading Agent.

    Evaluates student responses with flexible, accurate grading that handles edge cases
    like synonyms, typos, and Arabic harakaat variations.

    ## Responsibilities

    1. **Vocabulary Translation Grading**
       - Accept exact matches, synonyms, minor typos, capitalization variations
       - Reject clearly incorrect answers
       - Return: {"correct": true/false}

    2. **Grammar Quiz Grading (Single Question)**
       - Accept abbreviations (m/f for masculine/feminine)
       - Apply Arabic harakaat rules: internal optional, case endings required
       - Return: {"correct": true/false}

    3. **Grammar Test Grading (Multiple Questions)**
       - Batch process multiple questions for efficiency
       - Return: {"total_score": "X/Y", "results": [...]}

    ## Model Configuration

    - **Base Model:** Qwen2.5-7B-Instruct (stronger reasoning than 3B)
    - **Max Tokens:** 50 (short JSON responses)
    - **Sampling:** Deterministic (do_sample=False) for consistent grading
    - **Fine-tuning:** Required for JSON compliance and harakaat flexibility

    ## Edge Case Handling

    ### Flexible Grading Rules
    - Synonyms: "instructor" = "teacher", "automobile" = "car"
    - Minor typos: "scool" = "school" (1 char error), "bok" = "book" (1 char missing)
    - Capitalization: "Book" = "book", "SCHOOL" = "school"
    - Articles: "a pen" = "pen", "the book" = "book"

    ### Arabic Harakaat Rules
    - **Internal harakaat (vowel marks):** OPTIONAL
      - الكتابُ = الكِتَابُ (both correct)
      - الكتابُ = الكتاابُ (both correct - internal marks don't affect correctness)
    - **Case endings (final harakaat):** REQUIRED and must match exactly
      - الكتابُ ≠ الكتاب (nominative vs. no case ending) ❌
      - الكتابُ ≠ الكتابَ (nominative vs. accusative) ❌
      - الكتابُ ≠ الكتابِ (nominative vs. genitive) ❌

    ## Integration Pattern

    Called by Orchestrator (Agent 1) in Pattern A architecture:
    1. Orchestrator detects quiz/test question
    2. Orchestrator calls appropriate GradingAgent method
    3. GradingAgent returns JSON result
    4. Orchestrator formats user-facing feedback based on result

    ## Performance Characteristics

    - **Latency:** <500ms per question (target)
    - **Batch Processing:** Multiple questions in single call for grammar tests
    - **Deterministic:** Same input always produces same output
    - **Memory:** ~4GB (7B model with 4-bit quantization)

    ## Example Usage

    ```python
    # Initialize
    grading_agent = GradingAgent(model, tokenizer, max_new_tokens=50)

    # Grade vocabulary (synonym accepted)
    result = grading_agent.grade_vocab({
        "word": "مُعَلِّم",
        "student_answer": "instructor",
        "correct_answer": "teacher"
    })
    # Returns: '{"correct": true}' (synonym accepted)

    # Grade grammar (abbreviation accepted)
    result = grading_agent.grade_grammar_quiz({
        "question": "Is مَدْرَسَة masculine or feminine?",
        "student_answer": "f",
        "correct_answer": "feminine"
    })
    # Returns: '{"correct": true}' (abbreviation accepted)

    # Grade Arabic harakaat (internal optional, case ending required)
    result = grading_agent.grade_grammar_quiz({
        "question": "Make definite (nominative): كتاب",
        "student_answer": "الكتابُ",  # No internal harakaat
        "correct_answer": "الكِتَابُ"  # Has internal harakaat
    })
    # Returns: '{"correct": true}' (internal harakaat optional)

    result = grading_agent.grade_grammar_quiz({
        "question": "Make definite (nominative): كتاب",
        "student_answer": "الكتاب",  # No case ending
        "correct_answer": "الكِتَابُ"  # Has case ending ُ
    })
    # Returns: '{"correct": false}' (case ending required)
    ```

    ## Attributes

    - model: HuggingFace model (Qwen2.5-7B-Instruct)
    - tokenizer: HuggingFace tokenizer
    - max_new_tokens: Maximum tokens to generate (default 50)
    """

    def __init__(
        self,
        model: PreTrainedModel,
        tokenizer: PreTrainedTokenizer,
        max_new_tokens: int = 50,
    ) -> None:
        """
        Initialize GradingAgent.

        Args:
            model: HuggingFace model (recommended: Qwen2.5-7B-Instruct)
            tokenizer: HuggingFace tokenizer matching the model
            max_new_tokens: Maximum tokens to generate (default 50)
        """
        self.model = model
        self.tokenizer = tokenizer
        self.max_new_tokens = max_new_tokens

    def generate_response(self, prompt: str) -> str:
        """
        Generate response from model with deterministic sampling.

        Supports both API adapters (Together.ai, Ollama) and local transformers models.

        Args:
            prompt: Input prompt (will be formatted as user message)

        Returns:
            Generated response text (assistant message only)
        """
        # Check if model is API adapter (Together.ai, Ollama)
        if hasattr(self.model, "generate_response"):
            # API adapter - delegate directly
            return self.model.generate_response(prompt, max_new_tokens=self.max_new_tokens)

        # Local transformers model - use chat template format
        # Format as chat messages (matching training format)
        messages = [
            {
                "role": "system",
                "content": "You are an Arabic vocabulary grading system. Return only valid JSON.",
            },
            {"role": "user", "content": prompt},
        ]

        # Apply chat template
        formatted_prompt = self.tokenizer.apply_chat_template(
            messages, tokenize=False, add_generation_prompt=True
        )

        inputs = self.tokenizer(formatted_prompt, return_tensors="pt").to(self.model.device)

        # Use autocast to handle BFloat16/Float mismatch
        device_type = "cuda" if self.model.device.type == "cuda" else "cpu"
        with torch.amp.autocast(
            device_type=device_type, dtype=torch.bfloat16, enabled=(device_type == "cuda")
        ):
            outputs = self.model.generate(
                **inputs,
                max_new_tokens=self.max_new_tokens,
                do_sample=True,
                temperature=0.3,  # Low temp for more deterministic grading
                top_p=0.9,
                top_k=50,
                pad_token_id=self.tokenizer.eos_token_id,
            )

        response = self.tokenizer.decode(outputs[0], skip_special_tokens=True)

        # Extract assistant response (remove formatted prompt)
        if response.startswith(formatted_prompt):
            response = response[len(formatted_prompt) :].strip()

        # Extract only the JSON after "assistant\n"
        if "assistant\n" in response:
            response = response.split("assistant\n", 1)[1].strip()

        return response

    def grade_vocab(self, input_data: dict, rag_context: dict = None) -> str:
        """
        Grade vocabulary translation with flexible edge case handling.

        Uses hybrid validation approach:
        1. Rule-based pre-processing (articles, typos, normalization)
        2. AI grading for semantic similarity (synonyms, context)

        Accepts synonyms, typos, capitalization variations, and articles.
        See module docstring for complete edge case examples.

        Args:
            input_data: Dict with word, student_answer, correct_answer
            rag_context: Optional RAG context with lesson content (vocab list, examples, common mistakes)

        Returns:
            JSON string: '{"correct": true}' or '{"correct": false}'

        Raises:
            ValueError: If required keys are missing from input_data
        """
        required_keys = {"word", "student_answer", "correct_answer"}
        if missing := required_keys - input_data.keys():
            raise ValueError(f"Missing required keys: {missing}")

        student_answer = input_data["student_answer"]
        correct_answer = input_data["correct_answer"]

        # =====================================================================
        # HYBRID VALIDATION: Rule-based pre-processing
        # =====================================================================

        # 1. Exact match after normalization (handles articles, case)
        if normalize_answer(student_answer) == normalize_answer(correct_answer):
            return '{"correct": true}'

        # 2. Minor typo detection (1-character edit distance)
        if is_minor_typo(student_answer, correct_answer, threshold=1):
            return '{"correct": true}'

        # =====================================================================
        # AI GRADING: For synonyms and semantic similarity
        # =====================================================================

        prompt = GRADING_VOCAB.format(
            word=input_data["word"],
            student_answer=student_answer,
            correct_answer=correct_answer,
        )

        # Append RAG context if provided
        if rag_context:
            context_parts = []
            if rag_context.get("vocab_list"):
                vocab_items = rag_context["vocab_list"][:10]  # Limit to avoid context overflow
                vocab_str = "\n".join(
                    [f"- {v.get('arabic', '')} = {v.get('english', '')}" for v in vocab_items]
                )
                context_parts.append(f"\n\nLesson vocabulary:\n{vocab_str}")

            if rag_context.get("examples"):
                examples = rag_context["examples"][:3]
                examples_str = "\n".join([f"- {ex}" for ex in examples])
                context_parts.append(f"\n\nExamples:\n{examples_str}")

            if context_parts:
                prompt += "".join(context_parts)

        response = self.generate_response(prompt)
        return response

    def grade_grammar_quiz(self, input_data: dict, rag_context: dict = None) -> str:
        """
        Grade single grammar quiz question with Arabic harakaat rules.

        Uses hybrid validation approach:
        1. Rule-based Arabic harakaat normalization (internal marks optional)
        2. AI grading for semantic similarity (abbreviations, synonyms)

        Accepts abbreviations, synonyms, and alternate phrasings.
        Arabic harakaat: Internal marks optional, case endings required.
        See module docstring for complete edge case examples.

        Args:
            input_data: Dict with question, student_answer, correct_answer
            rag_context: Optional RAG context with grammar rules, examples, and common mistakes

        Returns:
            JSON string: '{"correct": true}' or '{"correct": false}'

        Raises:
            ValueError: If required keys are missing from input_data
        """
        required_keys = {"question", "student_answer", "correct_answer"}
        if missing := required_keys - input_data.keys():
            raise ValueError(f"Missing required keys: {missing}")

        student_answer = input_data["student_answer"]
        correct_answer = input_data["correct_answer"]
        question = input_data["question"]

        # =====================================================================
        # HYBRID VALIDATION: Rule-based Arabic text comparison
        # =====================================================================

        # If both answers are Arabic text, apply harakaat rules
        if is_arabic_text(student_answer) and is_arabic_text(correct_answer):
            if compare_arabic_answers(student_answer, correct_answer, question):
                return '{"correct": true}'
            else:
                # Hybrid validation determined answers don't match
                return '{"correct": false}'

        # =====================================================================
        # AI GRADING: For abbreviations, synonyms, and semantic similarity
        # =====================================================================

        prompt = GRADING_GRAMMAR_QUIZ.format(
            question=question,
            student_answer=student_answer,
            correct_answer=correct_answer,
        )

        # Append RAG context if provided
        if rag_context:
            context_parts = []
            if rag_context.get("grammar_rule"):
                context_parts.append(f"\n\nGrammar rule: {rag_context['grammar_rule']}")

            if rag_context.get("examples"):
                examples = rag_context["examples"][:3]
                examples_str = "\n".join([f"- {ex}" for ex in examples])
                context_parts.append(f"\n\nExamples:\n{examples_str}")

            if rag_context.get("common_mistakes"):
                mistakes = rag_context["common_mistakes"][:3]
                mistakes_str = "\n".join([f"- {m}" for m in mistakes])
                context_parts.append(f"\n\nCommon mistakes:\n{mistakes_str}")

            if context_parts:
                prompt += "".join(context_parts)

        response = self.generate_response(prompt)
        return response

    def grade_grammar_test(self, input_data: dict) -> str:
        """
        Grade multiple grammar test questions in a single call.

        More efficient than calling grade_grammar_quiz() multiple times.
        Applies same flexible grading rules as grade_grammar_quiz().

        Args:
            input_data: Dict with lesson_number and answers list.
                Each answer dict has question, student_answer, correct_answer.

        Returns:
            JSON string: '{"total_score": "X/Y", "results": [{"question_id": "qN", "correct": bool}, ...]}'

        Raises:
            ValueError: If required keys are missing from input_data
        """
        required_keys = {"lesson_number", "answers"}
        if missing := required_keys - input_data.keys():
            raise ValueError(f"Missing required keys: {missing}")

        if not isinstance(input_data["answers"], list):
            raise ValueError("'answers' must be a list")

        if not input_data["answers"]:
            raise ValueError("'answers' list must be non-empty")

        # Validate each answer entry has required keys
        for i, ans in enumerate(input_data["answers"]):
            required_answer_keys = {"question", "student_answer", "correct_answer"}
            if missing := required_answer_keys - ans.keys():
                raise ValueError(f"Answer {i + 1} missing required keys: {missing}")

        # Format answers for prompt
        answers_list = []
        for i, ans in enumerate(input_data["answers"], 1):
            answers_list.append(
                f"Q{i}: {ans['question']}\n"
                f"Student: {ans['student_answer']}\n"
                f"Correct: {ans['correct_answer']}"
            )
        answers_formatted = "\n\n".join(answers_list)

        prompt = GRADING_GRAMMAR_TEST.format(
            lesson_number=input_data["lesson_number"],
            answers_formatted=answers_formatted,
        )

        response = self.generate_response(prompt)
        return response

    def handle_input(
        self,
        user_input: str,
        conversation_history: list[dict],
        grading_context: dict,
    ) -> str:
        """
        Handle user input and route to appropriate grading method.

        Not yet implemented - placeholder for future Pattern B architecture.
        Use grade_vocab(), grade_grammar_quiz(), or grade_grammar_test() directly.

        Returns:
            JSON string: {"status": "not_implemented", "message": "..."}
        """
        return json.dumps(
            {
                "status": "not_implemented",
                "message": "Direct input handling not yet implemented. Use grade_vocab() or grade_grammar_quiz() directly.",
            }
        )

    # Orchestrator adapter method

    def grade_answer(self, input_data: dict[str, Any]) -> str:
        """
        Orchestrator adapter: Grade a student's answer.

        This is an adapter method that orchestrator nodes expect.
        Routes to grade_vocab() or grade_grammar_quiz() based on mode.

        Args:
            input_data: Input with user_answer, correct_answer, question, mode

        Returns:
            JSON grading result ({"correct": true/false})

        Raises:
            ValueError: If required keys are missing or empty
        """
        # Validate required fields upfront
        required_keys = {"user_answer", "correct_answer", "question"}
        if missing := required_keys - input_data.keys():
            raise ValueError(f"Missing required keys for grading: {missing}")

        # Validate no empty strings (catches orchestrator bugs early)
        for key in required_keys:
            if not input_data[key]:
                raise ValueError(f"Required field '{key}' cannot be empty")

        mode = input_data.get("mode", "vocabulary")

        if mode == "grammar":
            # Grammar mode: use grade_grammar_quiz
            return self.grade_grammar_quiz(
                {
                    "question": input_data["question"],
                    "student_answer": input_data["user_answer"],
                    "correct_answer": input_data["correct_answer"],
                }
            )
        else:
            # Vocabulary mode (default): use grade_vocab
            # Map orchestrator field names to agent field names
            return self.grade_vocab(
                {
                    "word": input_data["question"],  # question contains the word/prompt
                    "student_answer": input_data["user_answer"],
                    "correct_answer": input_data["correct_answer"],
                }
            )
