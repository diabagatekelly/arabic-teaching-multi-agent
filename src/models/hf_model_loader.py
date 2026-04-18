"""Model loading utilities for the Arabic teaching multi-agent system."""

import json
import logging
import os
from pathlib import Path

import torch
from dotenv import load_dotenv
from huggingface_hub import hf_hub_download
from peft import PeftModel
from transformers import AutoModelForCausalLM, AutoTokenizer

load_dotenv()

logger = logging.getLogger(__name__)

FINETUNED_7B_TEACHING_PATH_LOCAL = "models/qwen-7b-arabic-teaching"
FINETUNED_7B_GRADING_PATH_LOCAL = "models/qwen-7b-arabic-grading"

FINETUNED_7B_TEACHING_PATH_HF = "kdiabagate/qwen-7b-arabic-teaching"
FINETUNED_7B_GRADING_PATH_HF = "kdiabagate/qwen-7b-arabic-grading"

BASE_7B_MODEL = "Qwen/Qwen2.5-7B-Instruct"


def _load_adapter_config(model_path: str, use_hub: bool, token: str) -> dict:
    """Load adapter_config.json from Hub or local path."""
    if use_hub:
        config_path = hf_hub_download(
            repo_id=model_path, filename="adapter_config.json", token=token
        )
    else:
        config_path = Path(model_path) / "adapter_config.json"

    with open(config_path) as f:
        return json.load(f)


def _load_finetuned_model(
    model_type: str,
    hf_path: str,
    local_path: str,
    use_hub: bool = True,
) -> tuple[AutoModelForCausalLM, AutoTokenizer]:
    """Load fine-tuned model (teaching or grading).

    Args:
        model_type: Model type for logging ("teaching" or "grading")
        hf_path: HuggingFace Hub path
        local_path: Local filesystem path
        use_hub: If True, load from Hub; else local

    Returns:
        Tuple of (model, tokenizer)

    Raises:
        FileNotFoundError: If local model not found
        RuntimeError: If model loading fails
    """
    if use_hub:
        model_path = hf_path
        logger.info(f"Loading {model_type} model from HuggingFace Hub: {model_path}...")
    else:
        model_path_obj = Path(local_path)
        if not model_path_obj.exists():
            raise FileNotFoundError(
                f"{model_type.title()} model not found at {local_path}. "
                "Use use_hub=True or train the model first."
            )
        model_path = str(model_path_obj)
        logger.info(f"Loading {model_type} model from local path: {model_path}...")

    try:
        hf_token = os.getenv("HF_TOKEN")

        tokenizer = AutoTokenizer.from_pretrained(
            model_path, trust_remote_code=True, token=hf_token
        )

        adapter_config = _load_adapter_config(model_path, use_hub, hf_token)
        base_model_name = adapter_config["base_model_name_or_path"]
        logger.info(f"Base model: {base_model_name}")

        logger.info("Loading base model...")
        base_model = AutoModelForCausalLM.from_pretrained(
            base_model_name,
            device_map="auto",
            trust_remote_code=True,
            token=hf_token,
        )

        logger.info("Loading LoRA adapter...")
        model = PeftModel.from_pretrained(base_model, model_path, device_map="auto", token=hf_token)

        memory_gb = torch.cuda.memory_allocated() / 1e9 if torch.cuda.is_available() else 0
        logger.info(
            f"✓ {model_type.title()} model loaded successfully (memory: ~{memory_gb:.1f}GB)"
        )

        return model, tokenizer

    except Exception as e:
        raise RuntimeError(f"Failed to load {model_type} model: {e}") from e


def load_teaching_model(use_hub: bool = True) -> tuple[AutoModelForCausalLM, AutoTokenizer]:
    """Load fine-tuned Qwen2.5-7B teaching model.

    Fine-tuned on 153 multi-turn conversations for warm teaching tone.
    """
    return _load_finetuned_model(
        model_type="teaching",
        hf_path=FINETUNED_7B_TEACHING_PATH_HF,
        local_path=FINETUNED_7B_TEACHING_PATH_LOCAL,
        use_hub=use_hub,
    )


def load_grading_model(use_hub: bool = True) -> tuple[AutoModelForCausalLM, AutoTokenizer]:
    """Load fine-tuned Qwen2.5-7B grading model.

    Fine-tuned for flexible grading with synonym/typo handling.
    """
    return _load_finetuned_model(
        model_type="grading",
        hf_path=FINETUNED_7B_GRADING_PATH_HF,
        local_path=FINETUNED_7B_GRADING_PATH_LOCAL,
        use_hub=use_hub,
    )


def load_all_models() -> dict:
    """Load all models for the multi-agent system."""
    logger.info("Loading all models for multi-agent system...")

    try:
        teaching_model, teaching_tokenizer = load_teaching_model()
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
