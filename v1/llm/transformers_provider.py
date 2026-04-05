"""Local Transformers model LLM provider."""

from __future__ import annotations

from typing import Any

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer


class TransformersProvider:
    """LLM provider using local Transformers models."""

    def __init__(
        self,
        model_name: str,
        device: str = "auto",
        max_new_tokens: int = 500,
        temperature: float = 0.7,
        load_in_4bit: bool = False,
    ) -> None:
        """
        Initialize Transformers provider.

        Args:
            model_name: HuggingFace model name or path
            device: Device to use (auto/cuda/cpu)
            max_new_tokens: Maximum tokens to generate
            temperature: Sampling temperature
            load_in_4bit: Whether to use 4-bit quantization
        """
        self.model_name = model_name
        self.max_new_tokens = max_new_tokens
        self.temperature = temperature

        kwargs: dict[str, Any] = {"device_map": device}
        if load_in_4bit:
            kwargs["load_in_4bit"] = True

        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.model = AutoModelForCausalLM.from_pretrained(model_name, **kwargs)

    def generate(self, prompt: str, **kwargs: Any) -> str:
        """
        Generate text using local model.

        Args:
            prompt: Input prompt
            **kwargs: Override default parameters

        Returns:
            Generated text
        """
        inputs = self.tokenizer(prompt, return_tensors="pt").to(self.model.device)

        with torch.no_grad():
            outputs = self.model.generate(
                **inputs,
                max_new_tokens=kwargs.get("max_new_tokens", self.max_new_tokens),
                temperature=kwargs.get("temperature", self.temperature),
                do_sample=True,
                pad_token_id=self.tokenizer.pad_token_id,
            )

        generated = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
        return generated[len(prompt) :].strip()
