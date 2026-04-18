"""Model loading utilities for the Arabic teaching multi-agent system.

This module provides functions to load the fine-tuned and base models
with 4-bit quantization for memory efficiency.

Memory Requirements:
- Fine-tuned 3B (4-bit): ~2GB
- Base 7B (4-bit): ~4-5GB
- Total: ~7GB RAM
"""

import logging
import os
from pathlib import Path

import torch
from dotenv import load_dotenv
from peft import PeftModel
from transformers import AutoModelForCausalLM, AutoTokenizer

# Load environment variables (including HF_TOKEN)
load_dotenv()

logger = logging.getLogger(__name__)

# Model paths
# Local paths (fallback)
FINETUNED_7B_TEACHING_PATH_LOCAL = "models/qwen-7b-arabic-teaching"
FINETUNED_7B_GRADING_PATH_LOCAL = "models/qwen-7b-arabic-grading"

# HuggingFace Hub paths (primary)
FINETUNED_7B_TEACHING_PATH_HF = "kdiabagate/qwen-7b-arabic-teaching"
FINETUNED_7B_GRADING_PATH_HF = "kdiabagate/qwen-7b-arabic-grading"

BASE_7B_MODEL = "Qwen/Qwen2.5-7B-Instruct"


def load_teaching_model(use_hub: bool = True) -> tuple[AutoModelForCausalLM, AutoTokenizer]:
    """Load fine-tuned Qwen2.5-7B model for Agent 1 (Teaching).

    This model is fine-tuned on 153 multi-turn conversations for:
    - Teaching vocabulary with warm, encouraging tone
    - Providing personalized feedback
    - Clear navigation options

    Args:
        use_hub: If True, load from HuggingFace Hub. If False, load from local path.

    Returns:
        Tuple of (model, tokenizer)

    Raises:
        FileNotFoundError: If fine-tuned model not found
        RuntimeError: If model loading fails
    """
    # Determine model path
    if use_hub:
        model_path = FINETUNED_7B_TEACHING_PATH_HF
        logger.info(f"Loading fine-tuned 7B teaching model from HuggingFace Hub: {model_path}...")
    else:
        model_path_local = Path(FINETUNED_7B_TEACHING_PATH_LOCAL)
        if not model_path_local.exists():
            raise FileNotFoundError(
                f"Fine-tuned model not found at {model_path_local}. "
                "Please ensure the model is trained and saved, or use use_hub=True."
            )
        model_path = str(model_path_local)
        logger.info(f"Loading fine-tuned 7B teaching model from local path: {model_path}...")

    try:
        # Load tokenizer
        # Get HF token from environment
        hf_token = os.getenv("HF_TOKEN")

        tokenizer = AutoTokenizer.from_pretrained(
            model_path,
            trust_remote_code=True,
            token=hf_token,
        )

        # Read adapter config to get base model
        import json

        if use_hub:
            from huggingface_hub import hf_hub_download

            config_path = hf_hub_download(
                repo_id=model_path, filename="adapter_config.json", token=hf_token
            )
            with open(config_path) as f:
                adapter_config = json.load(f)
        else:
            with open(Path(model_path) / "adapter_config.json") as f:
                adapter_config = json.load(f)

        base_model_name = adapter_config["base_model_name_or_path"]
        logger.info(f"Base model: {base_model_name}")

        # Load base model (already 4-bit quantized)
        logger.info("Loading base model...")
        base_model = AutoModelForCausalLM.from_pretrained(
            base_model_name,
            device_map="auto",
            trust_remote_code=True,
            token=hf_token,
        )

        # Load LoRA adapter
        logger.info("Loading LoRA adapter...")
        model = PeftModel.from_pretrained(
            base_model,
            model_path,
            device_map="auto",
            token=hf_token,
        )

        # Log memory usage (CUDA-safe)
        memory_gb = torch.cuda.memory_allocated() / 1e9 if torch.cuda.is_available() else 0
        logger.info(
            f"✓ Fine-tuned 7B teaching model loaded successfully (memory: ~{memory_gb:.1f}GB)"
        )

        return model, tokenizer

    except Exception as e:
        raise RuntimeError(f"Failed to load teaching model: {e}") from e


def load_grading_model(use_hub: bool = True) -> tuple[AutoModelForCausalLM, AutoTokenizer]:
    """Load fine-tuned Qwen2.5-7B model for Agent 2 (Grading).

    This is the fine-tuned 7B model with improved:
    - Flexible grading (synonyms, typos, harakaat)
    - Edge case handling
    - Accurate correctness detection
    - JSON compliance

    Args:
        use_hub: If True, load from HuggingFace Hub. If False, load from local path.

    Returns:
        Tuple of (model, tokenizer)

    Raises:
        RuntimeError: If model loading fails
    """
    # Determine model path
    if use_hub:
        model_path = FINETUNED_7B_GRADING_PATH_HF
        logger.info(f"Loading fine-tuned 7B grading model from HuggingFace Hub: {model_path}...")
    else:
        model_path_local = Path(FINETUNED_7B_GRADING_PATH_LOCAL)
        if not model_path_local.exists():
            raise FileNotFoundError(
                f"Fine-tuned grading model not found at {model_path_local}. "
                "Please ensure the model is trained and saved, or use use_hub=True."
            )
        model_path = str(model_path_local)
        logger.info(f"Loading fine-tuned 7B grading model from local path: {model_path}...")

    try:
        # Load tokenizer
        # Get HF token from environment
        hf_token = os.getenv("HF_TOKEN")

        tokenizer = AutoTokenizer.from_pretrained(
            model_path,
            trust_remote_code=True,
            token=hf_token,
        )

        # Read adapter config to get base model
        import json

        if use_hub:
            from huggingface_hub import hf_hub_download

            config_path = hf_hub_download(
                repo_id=model_path, filename="adapter_config.json", token=hf_token
            )
            with open(config_path) as f:
                adapter_config = json.load(f)
        else:
            with open(Path(model_path) / "adapter_config.json") as f:
                adapter_config = json.load(f)

        base_model_name = adapter_config["base_model_name_or_path"]
        logger.info(f"Base model: {base_model_name}")

        # Load base model (already 4-bit quantized)
        logger.info("Loading base model...")
        base_model = AutoModelForCausalLM.from_pretrained(
            base_model_name,
            device_map="auto",
            trust_remote_code=True,
            token=hf_token,
        )

        # Load LoRA adapter
        logger.info("Loading LoRA adapter...")
        model = PeftModel.from_pretrained(
            base_model,
            model_path,
            device_map="auto",
            token=hf_token,
        )

        logger.info(
            f"✓ Fine-tuned 7B grading model loaded successfully "
            f"(memory: ~{torch.cuda.memory_allocated() / 1e9:.1f}GB)"
        )

        return model, tokenizer

    except Exception as e:
        raise RuntimeError(f"Failed to load grading model: {e}") from e


def load_all_models() -> dict:
    """Load all models for the multi-agent system.

    Loads both teaching (fine-tuned 7B) and grading (fine-tuned 7B) models
    with 4-bit quantization.

    Returns:
        dict with keys:
            - teaching_model: Fine-tuned 7B teaching model
            - teaching_tokenizer: 7B tokenizer
            - grading_model: Fine-tuned 7B grading model
            - grading_tokenizer: 7B tokenizer

    Raises:
        RuntimeError: If any model fails to load
    """
    logger.info("Loading all models for multi-agent system...")

    try:
        # Load teaching model (fine-tuned 7B)
        teaching_model, teaching_tokenizer = load_teaching_model()

        # Load grading model (fine-tuned 7B)
        grading_model, grading_tokenizer = load_grading_model()

        total_memory = torch.cuda.memory_allocated() / 1e9 if torch.cuda.is_available() else 0
        logger.info(f"✓ All models loaded successfully (total memory: ~{total_memory:.1f}GB)")

        return {
            "teaching_model": teaching_model,
            "teaching_tokenizer": teaching_tokenizer,
            "grading_model": grading_model,
            "grading_tokenizer": grading_tokenizer,
        }

    except Exception as e:
        raise RuntimeError(f"Failed to load models: {e}") from e
