# Training Notebooks

This directory contains Jupyter notebooks for fine-tuning models on AWS SageMaker.

## Notebooks

### `sagemaker_finetune_qwen7b_teaching.ipynb`
**Purpose:** Fine-tune Qwen2.5-7B for Agent 1 (Teaching Agent)

**Training Data:** `data/training/agent1_teaching_training_data.jsonl` (153 multi-turn conversations)

**Instance Type:** ml.g5.xlarge or larger (A10G GPU, 24GB VRAM recommended)

**Output:** LoRA adapter (`qwen-7b-arabic-teaching/`)

**Includes:** End-to-end evaluation cells at the end of the notebook for immediate testing after training.

---

### `sagemaker_finetune_qwen7b_grading.ipynb`
**Purpose:** Fine-tune Qwen2.5-7B for Agent 2 (Grading Agent)

**Training Data:** `data/training/agent2_grading_training_data.jsonl` (346 examples)

**Instance Type:** ml.g5.xlarge or larger (A10G GPU, 24GB VRAM recommended)

**Output:** LoRA adapter (`qwen-7b-arabic-grading/`)

---

## Prerequisites

1. **AWS Account** with SageMaker access
2. **SageMaker Studio** or Notebook instance
3. **EFS Storage** attached (user-default-efs for model/data persistence)
4. **HuggingFace Token** set as environment variable (`HF_TOKEN`)

---

## Training Data Location

Training data should be uploaded to EFS before running notebooks:

```bash
# Upload to EFS
cp data/training/agent1_teaching_training_data.jsonl /home/sagemaker-user/user-default-efs/
cp data/training/agent2_grading_training_data.jsonl /home/sagemaker-user/user-default-efs/
```

Or reference the data path in the notebook if running from the repo directory.

---

## Model Output

Trained models are saved to EFS and can be uploaded to HuggingFace Hub directly from the notebooks.

**Current models on Hub:**
- `kdiabagate/qwen-7b-arabic-teaching` (Teaching Agent) - **PRODUCTION MODEL**
- `kdiabagate/qwen-7b-arabic-grading` (Grading Agent) - Trained but not deployed (see models/README.md)

---

## Training Configuration

**LoRA Settings:**
- Rank: 16-32
- Alpha: 32-64
- Dropout: 0.1
- Target modules: Attention layers (q_proj, k_proj, v_proj, o_proj)

**Training:**
- Epochs: 4-6
- Learning rate: 2e-4
- Batch size: 4
- Gradient accumulation: 4
- Max sequence length: 2048

**Framework:** Unsloth + PEFT for 2x faster training with memory efficiency.
