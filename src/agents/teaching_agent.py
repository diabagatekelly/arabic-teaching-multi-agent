"""Agent 1: Teaching Agent - handles lesson presentation and feedback."""

import logging

logger = logging.getLogger(__name__)


class TeachingAgent:
    """Teaching Agent wraps the LLM model for teaching tasks."""

    def __init__(self, model, tokenizer):
        """Initialize TeachingAgent with model and tokenizer.

        Args:
            model: The loaded teaching model (e.g., Qwen 7B)
            tokenizer: The tokenizer for the model
        """
        self.model = model
        self.tokenizer = tokenizer

    def respond(self, prompt, max_new_tokens=256, temperature=0.7):
        """Generate a response from the teaching model.

        Args:
            prompt: The prompt text (already formatted with template)
            max_new_tokens: Maximum tokens to generate
            temperature: Sampling temperature

        Returns:
            str: The model's response
        """
        logger.info("=" * 80)
        logger.info(f"[TeachingAgent] USING FINE-TUNED MODEL: {type(self.model).__name__}")
        logger.info(f"[TeachingAgent] Model device: {self.model.device}")
        logger.info(
            f"[TeachingAgent] Starting generation (max_tokens={max_new_tokens}, temp={temperature})"
        )

        # Build messages for model
        messages = [{"role": "user", "content": prompt}]

        # Apply chat template
        text = self.tokenizer.apply_chat_template(
            messages, tokenize=False, add_generation_prompt=True
        )
        logger.debug(f"[TeachingAgent] Chat template applied (length: {len(text)} chars)")

        model_inputs = self.tokenizer([text], return_tensors="pt").to(self.model.device)
        logger.info(f"[TeachingAgent] Tokenized input: {model_inputs.input_ids.shape[1]} tokens")

        # Generate response
        logger.info("[TeachingAgent] Generating...")
        generated_ids = self.model.generate(
            **model_inputs,
            max_new_tokens=max_new_tokens,
            do_sample=True,
            temperature=temperature,
            top_p=0.9,
            top_k=50,
            repetition_penalty=1.1,
            num_beams=1,
            use_cache=True,
            pad_token_id=self.tokenizer.pad_token_id,
        )

        # Strip input tokens from output
        generated_ids = [
            output_ids[len(input_ids) :]
            for input_ids, output_ids in zip(model_inputs.input_ids, generated_ids, strict=False)
        ]
        logger.info(f"[TeachingAgent] Generated {len(generated_ids[0])} new tokens")

        response = self.tokenizer.batch_decode(generated_ids, skip_special_tokens=True)[0]
        logger.info(f"[TeachingAgent] Decoded response length: {len(response)} chars")
        logger.info("=" * 80)
        logger.info("[TeachingAgent] MODEL OUTPUT:")
        logger.info(response)
        logger.info("=" * 80)

        return response
