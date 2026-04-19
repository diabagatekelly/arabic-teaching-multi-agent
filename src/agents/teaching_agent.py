"""Agent 1: Teaching Agent for Arabic language instruction."""

import logging
import re
from typing import Any

import torch
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


def remove_chinese_text(text: str) -> str:
    """
    Remove Chinese characters from text output.

    Qwen models sometimes generate Chinese text due to multilingual training.
    This post-processing filter removes Chinese characters while preserving
    Arabic, English, and common symbols.

    Args:
        text: Generated text that may contain Chinese characters

    Returns:
        Text with Chinese characters removed
    """
    # Chinese Unicode ranges:
    # CJK Unified Ideographs: 4E00-9FFF
    # CJK Extension A: 3400-4DBF
    # CJK Compatibility: F900-FAFF
    chinese_pattern = r"[\u4e00-\u9fff\u3400-\u4dbf\uf900-\ufaff]+"

    # Remove Chinese characters
    cleaned = re.sub(chinese_pattern, "", text)

    # Remove common weird formatting patterns that appear with Chinese
    # Matches: _Office_, _Office Building_, _Building Center_, etc.
    cleaned = re.sub(r"_[A-Z][a-zA-Z\s]+_\s*", "", cleaned)

    # Remove standalone underscored patterns
    cleaned = re.sub(r"_[A-Z][a-z]+_", "", cleaned)

    # Clean up extra spaces
    cleaned = re.sub(r"\s+", " ", cleaned).strip()

    return cleaned


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

        Supports both Ollama adapter and transformers models.

        IMPORTANT: For fine-tuned models, uses chat template format to match training.

        Args:
            prompt: Input prompt (raw text or system message content)

        Returns:
            Generated teaching response
        """
        # Check if model is Ollama adapter or Together.ai adapter
        if hasattr(self.model, "generate_response"):
            # Ollama or Together.ai adapter
            return self.model.generate_response(prompt, max_new_tokens=self.max_new_tokens)
        else:
            # Local transformers model - use chat template format (matches training!)
            # Convert raw prompt to chat format that model was trained on
            messages = [{"role": "system", "content": prompt}]
            logger.info(f"Messages for generation: {messages} ")

            # Apply chat template (Qwen format: <|im_start|>...<|im_end|>)
            formatted_prompt = self.tokenizer.apply_chat_template(
                messages,
                tokenize=False,
                add_generation_prompt=True,  # Adds <|im_start|>assistant
            )

            # Use current device and handle BFloat16/Float dtype mismatch
            inputs = self.tokenizer(formatted_prompt, return_tensors="pt").to(self.model.device)

            logger.info(
                f"Inputs shape: {inputs['input_ids'].shape}, device: {inputs['input_ids'].device}"
            )
            logger.info(f"About to call model.generate() with max_new_tokens={self.max_new_tokens}")

            # Use autocast to handle BFloat16/Float mismatch automatically
            device_type = "cuda" if self.model.device.type == "cuda" else "cpu"
            with torch.amp.autocast(
                device_type=device_type, dtype=torch.bfloat16, enabled=(device_type == "cuda")
            ):
                outputs = self.model.generate(
                    input_ids=inputs["input_ids"],
                    attention_mask=inputs.get("attention_mask"),
                    max_new_tokens=self.max_new_tokens,
                    pad_token_id=self.tokenizer.pad_token_id
                    if self.tokenizer.pad_token_id
                    else self.tokenizer.eos_token_id,
                    eos_token_id=self.tokenizer.eos_token_id,
                    do_sample=True,  # Enable sampling for faster generation
                    temperature=0.7,  # Lower = more focused
                    top_p=0.9,  # Nucleus sampling
                    top_k=50,  # Limit vocabulary per step
                )

            logger.info(f"Generation complete! Output shape: {outputs.shape}")

            response = self.tokenizer.decode(outputs[0], skip_special_tokens=True)

            # Extract only the assistant's response (after the prompt)
            # Handle both special tokens and literal text
            if "<|im_start|>assistant" in response:
                # Has special tokens
                response = response.split("<|im_start|>assistant")[-1]
                response = response.replace("<|im_end|>", "").strip()
            elif "\nassistant\n" in response:
                # Special tokens decoded as literal text
                response = response.split("\nassistant\n")[-1].strip()
            elif "assistant\n" in response:
                # Variant without leading newline
                response = response.split("assistant\n")[-1].strip()
            elif response.startswith(formatted_prompt):
                # Fallback: remove the full prompt
                response = response[len(formatted_prompt) :].strip()

            # Remove Chinese text contamination (post-processing filter)
            response = remove_chinese_text(response)

            logger.info(f"Generated response (post-processed): {response}")

            return response

    def handle_lesson_start(self, input_data: dict[str, Any]) -> str:
        """
        Handle lesson start scenario (welcome message).

        Args:
            input_data: Input with mode, student_name, lesson_number, etc.

        Returns:
            Welcoming teaching response with navigation options
        """
        logger.info("handle_lesson_start called")
        flattened = flatten_nested_input(input_data)
        prompt = LESSON_WELCOME.format(**flattened)
        logger.info(f"Calling generate_response with prompt length: {len(prompt)}")
        response = self.generate_response(prompt)
        logger.info(f"generate_response returned: {len(response)} chars")
        return response

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
        Handle grammar teaching scenario (overview or topic explanation).

        Args:
            input_data: Input with mode, topics_list (for overview) or topic_name (for explanation)

        Returns:
            Teaching response with grammar overview or explanation
        """
        flattened = flatten_nested_input(input_data)

        # Check if this is overview (topics_list) or topic explanation (topic_name)
        if "topics_list" in flattened and "topic_name" not in flattened:
            # Grammar overview - show all topics
            from src.prompts.templates import GRAMMAR_OVERVIEW

            prompt = GRAMMAR_OVERVIEW.format(**flattened)
        else:
            # Topic explanation with examples
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
        Handle arbitrary user input using the fine-tuned model.

        Args:
            user_input: User's message
            conversation_history: Previous conversation turns
            student_context: Student profile and progress

        Returns:
            Model-generated response
        """
        # Build a conversational prompt for the fine-tuned model
        context = student_context or {}
        mode = context.get("mode", "vocabulary")
        learned_items = context.get("learned_items", [])

        # Create a simple prompt for general conversation
        prompt = f"""You are an Arabic language teacher. The student said: "{user_input}"

Current mode: {mode}
Learned items: {len(learned_items)} items

Respond naturally and helpfully. Guide them through the lesson, answer their questions, and keep them motivated.

Your response:"""

        return self.generate_response(prompt)

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
