"""Agent 1: Teaching Agent for Arabic language instruction."""

import logging
from typing import Any

from transformers import PreTrainedModel, PreTrainedTokenizer

from src.prompts.formatters import flatten_nested_input
from src.prompts.templates import (
    FEEDBACK_GRAMMAR_CORRECT,
    FEEDBACK_GRAMMAR_INCORRECT,
    FEEDBACK_VOCAB_CORRECT,
    FEEDBACK_VOCAB_INCORRECT,
    GRAMMAR_EXPLANATION,
    LESSON_WELCOME,
    VOCAB_BATCH_INTRO,
)

logger = logging.getLogger(__name__)


class TeachingAgent:
    """
    Agent 1: Teaching Agent (Pattern A - Orchestrates other agents).

    Responsibilities:
    - Welcome students and introduce lessons
    - Teach vocabulary in batches (3-4 words)
    - Explain grammar concepts
    - Provide warm, supportive feedback
    - Control teaching flow and call other agents as needed

    Model: Fine-tuned Qwen2.5-3B-Instruct (base 3B for baseline)

    Dependencies (Pattern A):
    - content_agent (Agent 3): Get lesson content, exercises
    - grading_agent (Agent 2): Grade student answers

    State Management:
    - Agent is STATELESS (backend manages session state)
    - Takes conversation_history and student context as input
    - Returns teaching response only
    """

    def __init__(
        self,
        model: PreTrainedModel,
        tokenizer: PreTrainedTokenizer,
        content_agent: Any | None = None,  # Agent 3 (future)
        grading_agent: Any | None = None,  # Agent 2 (future)
        max_new_tokens: int = 256,
    ) -> None:
        """
        Initialize teaching agent.

        Args:
            model: Fine-tuned teaching model (Qwen2.5-3B-Instruct)
            tokenizer: Model tokenizer
            content_agent: Agent 3 for content generation (optional, for Pattern A)
            grading_agent: Agent 2 for answer grading (optional, for Pattern A)
            max_new_tokens: Maximum tokens to generate in response
        """
        self.model = model
        self.tokenizer = tokenizer
        self.content_agent = content_agent
        self.grading_agent = grading_agent
        self.max_new_tokens = max_new_tokens

    def generate_response(self, prompt: str) -> str:
        """
        Generate response from teaching model.

        Args:
            prompt: Input prompt

        Returns:
            Generated teaching response
        """
        inputs = self.tokenizer(prompt, return_tensors="pt").to(self.model.device)

        outputs = self.model.generate(
            **inputs,
            max_new_tokens=self.max_new_tokens,
            do_sample=False,  # Deterministic for evaluation
            pad_token_id=self.tokenizer.eos_token_id,
        )

        response = self.tokenizer.decode(outputs[0], skip_special_tokens=True)

        if response.startswith(prompt):
            response = response[len(prompt) :].strip()

        return response

    def handle_lesson_start(self, input_data: dict[str, Any]) -> str:
        """
        Handle lesson start scenario (welcome message).

        Args:
            input_data: Input with mode, student_name, lesson_number, etc.

        Returns:
            Welcoming teaching response with navigation options
        """
        flattened = flatten_nested_input(input_data)
        prompt = LESSON_WELCOME.format(**flattened)
        return self.generate_response(prompt)

    def handle_teaching_vocab(self, input_data: dict[str, Any]) -> str:
        """
        Handle vocabulary teaching scenario (batch introduction).

        Args:
            input_data: Input with mode, sub_mode, words list, etc.

        Returns:
            Teaching response with vocabulary introduction
        """
        flattened = flatten_nested_input(input_data)

        # Use batch_introduction template (primary vocab teaching mode)
        prompt = VOCAB_BATCH_INTRO.format(**flattened)
        return self.generate_response(prompt)

    def handle_teaching_grammar(self, input_data: dict[str, Any]) -> str:
        """
        Handle grammar teaching scenario (topic explanation).

        Args:
            input_data: Input with mode, sub_mode, grammar_topic, examples, etc.

        Returns:
            Teaching response with grammar explanation
        """
        flattened = flatten_nested_input(input_data)

        # Use topic_explanation template (primary grammar teaching mode)
        prompt = GRAMMAR_EXPLANATION.format(**flattened)
        return self.generate_response(prompt)

    def handle_feedback_vocab(self, input_data: dict[str, Any]) -> str:
        """
        Handle vocabulary feedback scenario.

        Args:
            input_data: Input with mode, word_arabic, student_answer, is_correct, english

        Returns:
            Feedback response (praise if correct, supportive correction if incorrect)
        """
        is_correct = input_data.get("is_correct", False)

        if is_correct:
            prompt = FEEDBACK_VOCAB_CORRECT.format(**input_data)
        else:
            prompt = FEEDBACK_VOCAB_INCORRECT.format(**input_data)

        return self.generate_response(prompt)

    def handle_feedback_grammar(self, input_data: dict[str, Any]) -> str:
        """
        Handle grammar feedback scenario.

        Args:
            input_data: Input with mode, question, student_answer, is_correct, correct_answer

        Returns:
            Feedback response (praise if correct, supportive correction if incorrect)
        """
        is_correct = input_data.get("is_correct", False)

        if is_correct:
            prompt = FEEDBACK_GRAMMAR_CORRECT.format(**input_data)
        else:
            prompt = FEEDBACK_GRAMMAR_INCORRECT.format(**input_data)

        return self.generate_response(prompt)

    def handle_input(
        self,
        user_input: str,
        conversation_history: list[dict[str, str]] | None = None,
        student_context: dict[str, Any] | None = None,
    ) -> str:
        """
        Handle arbitrary user input (placeholder - not yet implemented).

        Use specific handle_* methods instead for evaluation.

        Args:
            user_input: User's message
            conversation_history: Previous conversation turns
            student_context: Student profile and progress

        Returns:
            Placeholder message
        """
        logger.warning("handle_input() not implemented - use specific handle_* methods")
        return "I'm still learning how to have conversations! Please use the specific teaching modes for now."

    # Orchestrator adapter methods

    def start_lesson(self, input_data: dict[str, Any]) -> str:
        """
        Orchestrator adapter: Start a new lesson.

        This is an adapter method that orchestrator nodes expect.
        Delegates to handle_lesson_start().

        Args:
            input_data: Input with lesson_number, mode, etc.

        Returns:
            Lesson introduction response
        """
        return self.handle_lesson_start(input_data)

    def handle_user_message(self, input_data: dict[str, Any]) -> str:
        """
        Orchestrator adapter: Handle general user messages (placeholder).

        Delegates to handle_input(). Use specific handle_* methods instead.

        Args:
            input_data: Input with user_input, mode, learned_items, etc.

        Returns:
            Placeholder message
        """
        return self.handle_input(
            user_input=input_data.get("user_input", ""),
            conversation_history=None,
            student_context=input_data,
        )

    def provide_feedback(self, input_data: dict[str, Any]) -> str:
        """
        Orchestrator adapter: Provide feedback after grading.

        This is an adapter method that orchestrator nodes expect.
        Routes to handle_feedback_vocab() or handle_feedback_grammar()
        based on the mode.

        Args:
            input_data: Input with is_correct, user_answer, correct_answer, mode

        Returns:
            Feedback response (vocabulary or grammar)

        Raises:
            ValueError: If mode is not one of the supported values
        """
        mode = input_data.get("mode", "vocabulary")

        # Validate mode against explicit allowed set
        allowed_modes = {"vocabulary", "grammar"}
        if mode not in allowed_modes:
            raise ValueError(
                f"Unsupported mode '{mode}' for feedback. Must be one of: {allowed_modes}"
            )

        if mode == "grammar":
            return self.handle_feedback_grammar(input_data)
        else:
            # Vocabulary mode (explicitly checked above)
            return self.handle_feedback_vocab(input_data)
