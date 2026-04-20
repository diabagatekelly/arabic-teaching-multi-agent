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
from typing import Any

from transformers import PreTrainedModel, PreTrainedTokenizer

from src.prompts.templates import GRADING_GRAMMAR_QUIZ, GRADING_GRAMMAR_TEST, GRADING_VOCAB

logger = logging.getLogger(__name__)


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

        Args:
            prompt: Input prompt

        Returns:
            Generated response text (with prompt stripped)
        """
        # Build messages for model (use chat template like teaching agent)
        messages = [{"role": "user", "content": prompt}]

        # Apply chat template
        text = self.tokenizer.apply_chat_template(
            messages, tokenize=False, add_generation_prompt=True
        )

        # Tokenize
        model_inputs = self.tokenizer([text], return_tensors="pt").to(self.model.device)

        # Generate with tight constraints for JSON output
        generated_ids = self.model.generate(
            **model_inputs,
            max_new_tokens=self.max_new_tokens,
            do_sample=True,
            temperature=0.1,  # Very low for focused, deterministic JSON
            top_p=0.95,
            top_k=40,
            repetition_penalty=1.0,  # No penalty - JSON has repeated structure
            num_beams=1,
            use_cache=True,
            pad_token_id=self.tokenizer.pad_token_id,
        )

        # Strip input tokens from output
        generated_ids = [
            output_ids[len(input_ids) :]
            for input_ids, output_ids in zip(model_inputs.input_ids, generated_ids, strict=False)
        ]

        # Decode
        response = self.tokenizer.batch_decode(generated_ids, skip_special_tokens=True)[0]

        return response

    def grade_vocab(self, input_data: dict) -> str:
        """
        Grade vocabulary translation with flexible edge case handling.

        Accepts synonyms, typos, capitalization variations, and articles.
        See module docstring for complete edge case examples.

        Args:
            input_data: Dict with word, student_answer, correct_answer

        Returns:
            JSON string: '{"correct": true}' or '{"correct": false}'

        Raises:
            ValueError: If required keys are missing from input_data
        """
        required_keys = {"word", "student_answer", "correct_answer"}
        if missing := required_keys - input_data.keys():
            raise ValueError(f"Missing required keys: {missing}")

        logger.info(f"[GradingAgent] Grading vocab - word: {input_data['word']}")
        logger.info(f"[GradingAgent] Student answer: {input_data['student_answer']}")
        logger.info(f"[GradingAgent] Correct answer: {input_data['correct_answer']}")

        prompt = GRADING_VOCAB.format(
            word=input_data["word"],
            student_answer=input_data["student_answer"],
            correct_answer=input_data["correct_answer"],
        )

        response = self.generate_response(prompt)
        logger.info(f"[GradingAgent] Vocab grading result: {response}")
        return response

    def grade_grammar_quiz(self, input_data: dict) -> str:
        """
        Grade single grammar quiz question with Arabic harakaat rules.

        Accepts abbreviations, synonyms, and alternate phrasings.
        Arabic harakaat: Internal marks optional, case endings required.
        See module docstring for complete edge case examples.

        Args:
            input_data: Dict with question, student_answer, correct_answer

        Returns:
            JSON string: '{"correct": true}' or '{"correct": false}'

        Raises:
            ValueError: If required keys are missing from input_data
        """
        required_keys = {"question", "student_answer", "correct_answer"}
        if missing := required_keys - input_data.keys():
            raise ValueError(f"Missing required keys: {missing}")

        logger.info(f"[GradingAgent] Grading grammar - question: {input_data['question']}")
        logger.info(f"[GradingAgent] Student answer: {input_data['student_answer']}")
        logger.info(f"[GradingAgent] Correct answer: {input_data['correct_answer']}")

        prompt = GRADING_GRAMMAR_QUIZ.format(
            question=input_data["question"],
            student_answer=input_data["student_answer"],
            correct_answer=input_data["correct_answer"],
        )

        response = self.generate_response(prompt)
        logger.info(f"[GradingAgent] Grammar grading result: {response}")
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
