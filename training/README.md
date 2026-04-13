# Training

This directory contains fine-tuning code and notebooks for training the Qwen2.5-3B model on Arabic teaching data using **Unsloth** for 2x faster training.

## Files

- **`finetune.py`** - Python script for local fine-tuning (uses Unsloth, matches SageMaker approach)
- **`sagemaker_finetune_qwen3b.ipynb`** - Jupyter notebook for AWS SageMaker GPU training

## Quick Start

### AWS SageMaker (Recommended)

1. Upload `combined_training_data.jsonl` to EFS at `/home/sagemaker-user/user-default-efs/combined_training_data.jsonl`
2. Open `sagemaker_finetune_qwen3b.ipynb` in SageMaker Studio/Notebook
3. Use ml.g4dn.xlarge or ml.g5.xlarge instance (T4/A10G GPU)
4. Set HF_TOKEN environment variable
5. Run all cells (~20-30 minutes)
6. Model saved to EFS (persists across sessions)

### Local Training (If you have GPU)

If you have local CUDA GPU (8GB+ VRAM):

```bash
python training/finetune.py
```

**Requirements:**
- CUDA-capable GPU (8GB+ VRAM)
- unsloth, transformers, trl, datasets, peft, accelerate, bitsandbytes

**Note:** `finetune.py` uses the same validated approach as the SageMaker notebook (Unsloth + SFTTrainer).

---

## SageMaker Setup Guide

### Prerequisites

1. AWS account with SageMaker access
2. SageMaker Studio or Notebook instance configured
3. EFS storage attached (user-default-efs)
4. HuggingFace account and token

### Step 1: Prepare EFS Storage

Upload training data to EFS:

```bash
# Create directory structure on EFS
mkdir -p /home/sagemaker-user/user-default-efs/arabic-teaching/data
mkdir -p /home/sagemaker-user/user-default-efs/arabic-teaching/models

# Upload training data
# Option A: From local machine via SageMaker terminal
cp combined_training_data.jsonl /home/sagemaker-user/user-default-efs/arabic-teaching/data/

# Option B: Download from S3 if you uploaded it there
aws s3 cp s3://your-bucket/combined_training_data.jsonl \
  /home/sagemaker-user/user-default-efs/arabic-teaching/data/
```

**Why EFS?** EFS storage persists across notebook sessions, so your trained model remains available even if you stop/restart your instance.

### Step 2: Set HuggingFace Token

**Option A: Environment Variable (Recommended)**

Set as lifecycle configuration or in terminal before starting notebook:

```bash
export HF_TOKEN="hf_your_token_here"
```

**Option B: In Notebook Cell**

Uncomment and paste your token in Cell 2 of the notebook:

```python
hf_token = "hf_your_token_here"
```

⚠️ **Warning:** Don't commit notebooks with hardcoded tokens!

### Step 3: Choose Instance Type

Recommended GPU instances:

| Instance Type | GPU | Memory | Cost/hr | Notes |
|--------------|-----|--------|---------|-------|
| **ml.g4dn.xlarge** | T4 (16GB) | 16 GB | ~$0.70 | ✅ Recommended, good balance |
| **ml.g5.xlarge** | A10G (24GB) | 16 GB | ~$1.00 | Faster, more memory |
| ml.p3.2xlarge | V100 (16GB) | 61 GB | ~$3.00 | Overkill for this task |

**Training time:** ~20-30 minutes on ml.g4dn.xlarge

### Step 4: Upload and Open Notebook

1. Upload `sagemaker_finetune_qwen3b.ipynb` to SageMaker
2. Open in JupyterLab or SageMaker Studio
3. Select kernel: **Python 3 (PyTorch 2.x)**
4. Ensure instance type has GPU

### Step 5: Run Training

#### First Time Setup

1. **Cell 1:** Install dependencies (~2-3 minutes)
   ```
   !pip install --upgrade torchvision
   !pip install unsloth trl transformers datasets peft accelerate bitsandbytes
   ```
   **Important:** Uses SageMaker's default PyTorch (don't upgrade!)

2. **⚠️ RESTART KERNEL** after Cell 1

3. **Cell 2:** Clear local cache + setup EFS caching + authenticate
   - Automatically clears `~/.cache` to free space
   - Redirects all HuggingFace caching to EFS
   - Shows disk space and cache paths

4. **Cell 3:** Verify GPU detected
   ```
   GPU: Tesla T4 (or A10G)
   Memory: 15-24 GB
   ```

5. **Cell 4:** Configure paths (check DATA_PATH exists)

#### Training

6. **Cells 5-10:** Load data, model, and train (~20-30 min)

7. **Cell 11:** Save model to EFS
   - Output: `/home/sagemaker-user/user-default-efs/arabic-teaching/models/qwen-3b-arabic-teaching/lora_adapters/`

8. **Cell 12:** Test generation

### Step 6: Verify Output

Check model files on EFS:

```bash
ls -lh /home/sagemaker-user/user-default-efs/arabic-teaching/models/qwen-3b-arabic-teaching/lora_adapters/
```

Expected files:
- `adapter_config.json` (~1 KB)
- `adapter_model.safetensors` (~200 MB)
- `tokenizer.json` (~2 MB)
- `tokenizer_config.json` (~1 KB)
- `special_tokens_map.json` (~1 KB)

Total size: ~200-220 MB

---

## Troubleshooting

### "Unsloth: HuggingFace seems to be down after trying for 120 seconds"

This is Unsloth's telemetry check timing out, not the actual model download.

**Already fixed in Cell 3** with:
```python
os.environ["UNSLOTH_DISABLE_LOG_STATS"] = "1"
```

If you still see this error, HuggingFace might be experiencing issues. Check https://status.huggingface.co/

### "HF_TOKEN not found"

Set environment variable or paste token in Cell 2.

### "Training data not found"

Verify path in Cell 4 matches your EFS structure:
```python
DATA_PATH = "/home/sagemaker-user/user-default-efs/arabic-teaching/data/combined_training_data.jsonl"
```

Check file exists:
```bash
ls -l /home/sagemaker-user/user-default-efs/arabic-teaching/data/
```

### "No GPU detected"

- Check instance type has GPU (g4dn, g5, p3)
- Verify PyTorch CUDA is installed: `torch.cuda.is_available()`
- Restart kernel after dependency installation

### "No space left on device"

This means model downloads are going to the small instance storage instead of EFS.

**Cell 2 already handles this automatically:**
- Clears local cache with `rm -rf ~/.cache/*`
- Redirects all caching to EFS via environment variables
- Shows disk space usage

If you still get this error:
1. Verify EFS is mounted: `ls -la /home/sagemaker-user/user-default-efs`
2. Re-run Cell 2 to ensure environment variables are set
3. Check disk usage: `df -h /home/sagemaker-user`

### Out of Memory (OOM)

If training crashes with OOM error:
1. Reduce `BATCH_SIZE` from 2 to 1
2. Increase `GRAD_ACCUM` from 4 to 8 (keeps effective batch size)
3. Or upgrade to ml.g5.xlarge (24GB GPU)

### Model loading stuck at 23%

- Verify `MAX_SEQ_LENGTH = 1536` (not 2048)
- Ensure using T4 GPU instance
- Try restarting kernel and re-running cells

---

## Training Configuration

- **Base Model:** Qwen/Qwen2.5-3B-Instruct
- **Method:** LoRA fine-tuning (rank=32, alpha=32, dropout=0)
- **Framework:** Unsloth (2x faster training)
- **Training Data:** 111 conversations
  - 41 teaching mode (lesson_start, teaching_vocab, teaching_grammar, feedback)
  - 40 grading mode (vocab, grammar)
  - 30 exercise generation (fill-in-blank, translation, correction)
- **Epochs:** 10
- **Batch Size:** 2 (effective 8 with gradient accumulation)
- **Max Seq Length:** 1536 tokens (optimized for memory)
- **Output:** 4-bit quantized model with LoRA adapters (~200MB)

## Output Structure

After training, the model will be saved to `models/qwen-3b-arabic-teaching/`:

```
qwen-3b-arabic-teaching/
├── adapter_config.json         # LoRA configuration
├── adapter_model.safetensors   # LoRA weights (~228MB)
├── tokenizer.json              # Tokenizer
├── tokenizer_config.json       # Tokenizer config
├── special_tokens_map.json     # Token mappings
├── chat_template.jinja         # Chat template
└── README.md                   # Model card
```

## Validated Configuration

✅ **Current setup validated on SageMaker:**
- No PyTorch upgrades (uses SageMaker default)
- EFS caching for large downloads
- Unsloth statistics disabled
- MAX_SEQ_LENGTH=1536 (avoids OOM)
- Clean JSON output for grading mode

## Training Results

**Current production model:**
- ✅ Clean JSON for grading: `{"correct": true/false}`
- ✅ Proper exercise generation JSON array
- ✅ Warm teaching tone without grammar leakage
- ✅ Clear navigation options

Saved at: `models/qwen-3b-arabic-teaching/`

## Cost Optimization

**Training cost:** ~$0.35-0.50 per run on ml.g4dn.xlarge

**Tips:**
1. **Stop instance** when not using (EFS persists)
2. **Use ml.g4dn.xlarge** (not larger instances)
3. **Run overnight** if you have free credits
4. **Delete checkpoints** after training completes (only need `lora_adapters/`)

## Next Steps

After training completes:

1. Model is saved to EFS - **no download needed**
2. EFS path persists across notebook sessions
3. Update agent code to load from EFS:
   ```python
   model_path = "/home/sagemaker-user/user-default-efs/arabic-teaching/models/qwen-3b-arabic-teaching/lora_adapters"
   ```
4. Test with multi-agent system
