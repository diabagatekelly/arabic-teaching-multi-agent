"""Fine-tune Qwen2.5-3B-Instruct on Arabic teaching training data using LoRA + Unsloth.

This script fine-tunes Qwen2.5-3B for multi-mode Arabic teaching:
- Teaching mode (lesson_start, teaching_vocab, teaching_grammar, feedback)
- Grading mode (grading_vocab, grading_grammar)
- Exercise generation mode (fill-in-blank, translation, correction)

Training: ~111 conversations
Method: LoRA (rank=32, alpha=32) with Unsloth for 2x faster training
Epochs: 10
Output: 4-bit quantized model (~200MB)

Installation (for SageMaker/Kaggle/local GPU):
    pip install "unsloth[colab-new] @ git+https://github.com/unslothai/unsloth.git"
    pip install --no-deps trl peft accelerate bitsandbytes

Note: Uses Unsloth approach validated on SageMaker. Matches sagemaker_finetune_qwen3b.ipynb.
"""

from __future__ import annotations

import gc
import json
import os
from pathlib import Path

import torch
from datasets import Dataset
from transformers import TrainingArguments

# IMPORTANT: Disable Unsloth statistics BEFORE importing Unsloth
os.environ["UNSLOTH_DISABLE_LOG_STATS"] = "1"

from trl import SFTTrainer
from unsloth import FastLanguageModel


def load_training_data(file_path: Path) -> list[dict]:
    """Load training data from JSONL file."""
    with open(file_path, encoding="utf-8") as f:
        conversations = [json.loads(line) for line in f]
    return conversations


# Note: format_conversation_for_training removed - done inline in main()


def main():
    """Fine-tune Qwen2.5-3B on Arabic teaching data using Unsloth."""

    # ========== Configuration ==========
    MODEL_NAME = "Qwen/Qwen2.5-3B-Instruct"  # Non-Unsloth version (Unsloth patches it)
    OUTPUT_DIR = Path(__file__).parent.parent / "models" / "qwen-3b-arabic-teaching"
    TRAINING_DATA = (
        Path(__file__).parent.parent / "data" / "training" / "combined_training_data.jsonl"
    )

    # LoRA config (matches SageMaker notebook)
    LORA_RANK = 32
    LORA_ALPHA = 32
    LORA_DROPOUT = 0  # No dropout for faster training

    # Training config (matches SageMaker notebook)
    EPOCHS = 10
    BATCH_SIZE = 2
    GRADIENT_ACCUMULATION_STEPS = 4
    LEARNING_RATE = 2e-4
    MAX_SEQ_LENGTH = 1536  # Changed from 2048 to match SageMaker (avoids OOM)
    WARMUP_RATIO = 0.03

    print("=" * 60)
    print("🚀 Fine-Tuning Qwen2.5-3B for Arabic Teaching (Unsloth)")
    print("=" * 60)
    print(f"Model: {MODEL_NAME}")
    print(f"LoRA: rank={LORA_RANK}, alpha={LORA_ALPHA}, dropout={LORA_DROPOUT}")
    print(f"Epochs: {EPOCHS}")
    print(f"Batch size: {BATCH_SIZE} (effective: {BATCH_SIZE * GRADIENT_ACCUMULATION_STEPS})")
    print(f"Max seq length: {MAX_SEQ_LENGTH}")
    print("=" * 60)

    # ========== Load Training Data ==========
    print("\n📂 Loading training data...")
    conversations = load_training_data(TRAINING_DATA)
    print(f"✓ Loaded {len(conversations)} conversations")

    # ========== Load Model & Tokenizer with Unsloth ==========
    print(f"\n🤖 Loading model with Unsloth: {MODEL_NAME}")

    model, tokenizer = FastLanguageModel.from_pretrained(
        model_name=MODEL_NAME,
        max_seq_length=MAX_SEQ_LENGTH,
        dtype=None,  # Auto-detect
        load_in_4bit=True,
    )

    print(f"✓ Model loaded: {model.num_parameters() / 1e9:.2f}B params")

    # ========== Add LoRA Adapters with Unsloth ==========
    print("\n🔧 Adding LoRA adapters...")

    model = FastLanguageModel.get_peft_model(
        model,
        r=LORA_RANK,
        lora_alpha=LORA_ALPHA,
        lora_dropout=LORA_DROPOUT,
        target_modules=[
            "q_proj",
            "k_proj",
            "v_proj",
            "o_proj",
            "gate_proj",
            "up_proj",
            "down_proj",
        ],
        bias="none",
        use_gradient_checkpointing="unsloth",
        random_state=42,
    )

    trainable = sum(p.numel() for p in model.parameters() if p.requires_grad)
    total = sum(p.numel() for p in model.parameters())
    print(f"✓ LoRA: {trainable:,} trainable ({100 * trainable / total:.2f}%)")

    # ========== Format Dataset ==========
    print("\n📝 Formatting dataset...")

    # Apply chat template to each conversation
    formatted_data = [
        {
            "text": tokenizer.apply_chat_template(
                conv["messages"], tokenize=False, add_generation_prompt=False
            )
        }
        for conv in conversations
    ]

    dataset = Dataset.from_list(formatted_data)
    print(f"✓ Dataset formatted: {len(dataset)} examples")

    # ========== Setup Trainer ==========
    print("\n🔧 Setting up trainer...")

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    torch.cuda.empty_cache()
    gc.collect()

    training_args = TrainingArguments(
        output_dir=str(OUTPUT_DIR),
        per_device_train_batch_size=BATCH_SIZE,
        gradient_accumulation_steps=GRADIENT_ACCUMULATION_STEPS,
        gradient_checkpointing=True,
        num_train_epochs=EPOCHS,
        learning_rate=LEARNING_RATE,
        warmup_ratio=WARMUP_RATIO,
        fp16=not torch.cuda.is_bf16_supported(),
        bf16=torch.cuda.is_bf16_supported(),
        logging_steps=1,
        optim="adamw_8bit",
        weight_decay=0.01,
        lr_scheduler_type="linear",
        seed=42,
        report_to="none",
        average_tokens_across_devices=False,
    )

    trainer = SFTTrainer(
        model=model,
        tokenizer=tokenizer,
        train_dataset=dataset,
        dataset_text_field="text",
        max_seq_length=MAX_SEQ_LENGTH,
        args=training_args,
        packing=False,
    )

    print("✓ Trainer ready")

    # ========== Train ==========
    print("\n🏋️ Starting training...")
    print(f"Steps/epoch: {len(conversations) // (BATCH_SIZE * GRADIENT_ACCUMULATION_STEPS)}")
    print(
        f"Total steps: {(len(conversations) // (BATCH_SIZE * GRADIENT_ACCUMULATION_STEPS)) * EPOCHS}"
    )

    stats = trainer.train()

    print("\n" + "=" * 60)
    print("✅ TRAINING COMPLETE!")
    print("=" * 60)
    print(f"Loss: {stats.training_loss:.4f}")
    print(f"Time: {stats.metrics['train_runtime'] / 60:.1f} min")

    # ========== Save Model ==========
    print(f"\n💾 Saving fine-tuned model to {OUTPUT_DIR}...")

    # Save LoRA adapters
    model.save_pretrained(OUTPUT_DIR)
    tokenizer.save_pretrained(OUTPUT_DIR)

    print(f"✓ Model saved to {OUTPUT_DIR}")

    # ========== Test Generation ==========
    print("\n🧪 Testing model generation...")

    # Prepare for inference
    FastLanguageModel.for_inference(model)

    test_messages = [
        {
            "role": "system",
            "content": "You are a supportive Arabic language teacher. Use an encouraging, warm tone.",
        },
        {
            "role": "user",
            "content": """Mode: teaching_vocab

Batch 1 of 3

Words:
- كِتَابٌ (kitaabun) - book
- مَدْرَسَةٌ (madrasatun) - school

Introduce these words with Arabic, transliteration, and English. Remind them flashcards are available. Offer options:
1. Take quiz on this batch
2. Go to next batch
3. See all words

Format with numbered options and mention they can request something else. Be encouraging and clear.""",
        },
    ]

    prompt = tokenizer.apply_chat_template(
        test_messages, tokenize=False, add_generation_prompt=True
    )

    inputs = tokenizer([prompt], return_tensors="pt").to("cuda")

    outputs = model.generate(
        **inputs,
        max_new_tokens=300,
        temperature=0.7,
        top_p=0.9,
        do_sample=True,
    )

    full_output = tokenizer.batch_decode(outputs)[0]

    # Extract assistant response
    if "<|im_start|>assistant" in full_output:
        response = full_output.split("<|im_start|>assistant")[-1]
        response = response.replace("<|im_end|>", "").strip()
    elif "assistant" in full_output:
        response = full_output.split("assistant")[-1].strip()
    else:
        response = full_output

    print("\n" + "=" * 60)
    print("📝 Test Generation:")
    print("=" * 60)
    print(response)
    print("=" * 60)

    # Test grading mode
    print("\n\n🧪 Testing grading mode...")

    grading_test = [
        {
            "role": "system",
            "content": "You are a precise Arabic grading assistant. Return only JSON.",
        },
        {
            "role": "user",
            "content": """Mode: grading_vocab

Grade this answer:
Word: مَدْرَسَةٌ
Student answer: school
Correct answer: school

Return JSON: {"correct": true/false}""",
        },
    ]

    grading_prompt = tokenizer.apply_chat_template(
        grading_test, tokenize=False, add_generation_prompt=True
    )

    grading_inputs = tokenizer([grading_prompt], return_tensors="pt").to("cuda")
    grading_outputs = model.generate(
        **grading_inputs, max_new_tokens=50, temperature=0.3, do_sample=False
    )

    grading_full = tokenizer.batch_decode(grading_outputs)[0]
    if "<|im_start|>assistant" in grading_full:
        grading_response = grading_full.split("<|im_start|>assistant")[-1]
        grading_response = grading_response.replace("<|im_end|>", "").strip()
    else:
        grading_response = (
            grading_full.split("assistant")[-1].strip()
            if "assistant" in grading_full
            else grading_full
        )

    print("\n" + "=" * 60)
    print("📝 Grading Test:")
    print("=" * 60)
    print(grading_response)
    print("=" * 60)

    print("\n" + "=" * 60)
    print("✅ FINE-TUNING COMPLETE!")
    print("=" * 60)
    print(f"📁 Model saved to: {OUTPUT_DIR}")
    print("\n📊 Summary:")
    print(f"  - Training examples: {len(conversations)}")
    print(f"  - Epochs: {EPOCHS}")
    print(f"  - LoRA rank: {LORA_RANK}")
    print(f"  - Max seq length: {MAX_SEQ_LENGTH}")
    print("  - Model size: ~2GB (4-bit quantized)")
    print("\n🎯 Validated approach from SageMaker notebook")


if __name__ == "__main__":
    main()
