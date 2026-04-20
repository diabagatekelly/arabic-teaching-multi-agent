"""Agent 1: Teaching Agent - handles lesson presentation and feedback."""


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
        # Build messages for model
        messages = [{"role": "user", "content": prompt}]

        # Apply chat template
        text = self.tokenizer.apply_chat_template(
            messages, tokenize=False, add_generation_prompt=True
        )
        model_inputs = self.tokenizer([text], return_tensors="pt").to(self.model.device)

        # Generate response
        generated_ids = self.model.generate(
            **model_inputs,
            max_new_tokens=max_new_tokens,
            temperature=temperature,
        )
        generated_ids = [
            output_ids[len(input_ids) :]
            for input_ids, output_ids in zip(model_inputs.input_ids, generated_ids, strict=False)
        ]

        response = self.tokenizer.batch_decode(generated_ids, skip_special_tokens=True)[0]

        return response
