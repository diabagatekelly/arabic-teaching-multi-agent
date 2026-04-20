# Deployment Guide - Arabic Teaching Multi-Agent System

## Overview

This system is deployed on **HuggingFace Spaces** using **Zero-GPU** for serverless GPU inference. The deployment supports lazy model loading to comply with Zero-GPU memory constraints.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    HuggingFace Space                         │
│  ┌───────────────────────────────────────────────────────┐  │
│  │                   Gradio App (app.py)                  │  │
│  │  ┌─────────────────────────────────────────────────┐  │  │
│  │  │            Orchestrator                          │  │  │
│  │  │  - Session management                            │  │  │
│  │  │  - State machine (vocab/grammar/exam flows)      │  │  │
│  │  │  - Lazy model loading                            │  │  │
│  │  └─────────────────────────────────────────────────┘  │  │
│  │                                                          │  │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐             │  │
│  │  │Teaching  │  │ Grading  │  │ Content  │             │  │
│  │  │ Agent    │  │  Agent   │  │  System  │             │  │
│  │  │(7B LoRA) │  │(7B LoRA) │  │ (Cache)  │             │  │
│  │  └────┬─────┘  └────┬─────┘  └────┬─────┘             │  │
│  │       │             │             │                     │  │
│  │       └─────────────┴─────────────┘                     │  │
│  │                     │                                    │  │
│  │              @spaces.GPU decorator                       │  │
│  │              (Zero-GPU allocation)                       │  │
│  └──────────────────────────────────────────────────────────┘ │
│                                                                │
│  ┌────────────────────┐    ┌──────────────────────────┐      │
│  │  Lesson Cache      │    │  Session Storage         │      │
│  │  (lesson_cache.    │    │  (sessions.json)         │      │
│  │   json)            │    │  - User progress         │      │
│  │  - Pre-loaded      │    │  - Quiz states           │      │
│  │    vocabulary      │    │  - Scores                │      │
│  │  - Grammar rules   │    │                          │      │
│  └────────────────────┘    └──────────────────────────┘      │
└────────────────────────────────────────────────────────────────┘
```

## Deployment Process

### 1. Prerequisites

**Required Accounts:**
- GitHub account (code repository)
- HuggingFace account (Spaces deployment)

**Required Files:**
- `app.py` - Gradio interface
- `requirements.txt` - Python dependencies
- `lesson_cache.json` - Pre-built lesson content
- `content_loader.py` - Lesson content loading utilities
- `src/` - Agent implementations
- Fine-tuned models in `models/` directory

### 2. Local Development Setup

```bash
# Clone repository
git clone https://github.com/diabagatekelly/arabic-teaching-multi-agent.git
cd arabic-teaching-multi-agent

# Install dependencies with uv
uv pip install -r requirements.txt

# Build lesson cache (one-time)
python scripts/build_lesson_cache.py

# Run locally
python app.py
```

### 3. HuggingFace Space Configuration

**Create Space:**
1. Go to https://huggingface.co/new-space
2. Choose:
   - Owner: Your username/org
   - Space name: `arabic-teacher-v2`
   - License: Apache 2.0
   - SDK: Gradio
   - Hardware: ZeroGPU (free tier)

**Space Settings (README.md header):**
```yaml
---
title: Arabic Teaching System
emoji: 📚
colorFrom: green
colorTo: blue
sdk: gradio
sdk_version: "5.23.1"
app_file: app.py
pinned: false
---
```

### 4. Deployment Steps

**Method 1: Push to HuggingFace (Recommended)**

```bash
# Add HuggingFace remote
git remote add space-v2 https://huggingface.co/spaces/kdiabagate/arabic-teacher-v2

# Push to main branch (triggers automatic rebuild)
git push space-v2 main:main
```

**Method 2: GitHub Sync**
1. Enable GitHub sync in Space settings
2. Link to: `https://github.com/diabagatekelly/arabic-teaching-multi-agent`
3. Auto-deploy on push to main

### 5. Build Process

**On Space:**
1. Reads `requirements.txt` and installs dependencies
2. Loads `lesson_cache.json` into memory
3. Initializes Gradio app with lazy model loading
4. Models are NOT loaded until first inference call
5. ZeroGPU allocates GPU only when `@spaces.GPU` decorated functions are called

**Build Time:** ~2-3 minutes

**Cold Start:** First inference takes ~30s (model loading)

**Warm Inference:** 1-3s per response

## Inference Pipeline

### Model Loading Strategy

**Problem:** Zero-GPU has limited memory and requires lazy loading.

**Solution:** Models loaded on-demand via callable getters:

```python
# In app.py
def get_teaching_model():
    """Lazy load teaching model with LoRA adapter."""
    if teaching_model_cache['model'] is None:
        model, tokenizer = load_teaching_model()
        teaching_model_cache['model'] = model
        teaching_model_cache['tokenizer'] = tokenizer
    return teaching_model_cache['model'], teaching_model_cache['tokenizer']

# Orchestrator receives callable, not model
orchestrator = Orchestrator(
    lesson_cache=lesson_cache,
    sessions=sessions,
    teaching_model_getter=lambda: get_teaching_model()[0],
    teaching_tokenizer=get_teaching_model()[1]
)
```

### Inference Flow

**User sends message → Gradio → Orchestrator → Agent → GPU → Response**

```python
# 1. User input processed by Gradio
def chat(message, session_id, history):
    # 2. Orchestrator determines intent and stage
    response = orchestrator.handle_message(session_id, message)
    
    # 3. Orchestrator routes to appropriate agent
    #    - Teaching agent for presenting content
    #    - Grading agent for evaluating answers
    
    # 4. Agent applies @spaces.GPU decorator
    @spaces.GPU
    def generate_with_lora(model, tokenizer, prompt):
        inputs = tokenizer(prompt, return_tensors="pt")
        outputs = model.generate(**inputs, **generation_config)
        return tokenizer.decode(outputs[0])
    
    # 5. Response returned to user
    return response
```

### Generation Parameters

**Teaching Agent (Qwen2.5-7B + LoRA):**
```python
generation_config = {
    "max_new_tokens": 256,
    "do_sample": True,
    "temperature": 0.7,      # Moderate creativity
    "top_p": 0.92,           # Nucleus sampling
    "top_k": 60,             # Vocabulary limit
    "repetition_penalty": 1.05,
    "pad_token_id": tokenizer.eos_token_id
}
```

**Grading Agent (Qwen2.5-7B + LoRA):**
```python
generation_config = {
    "max_new_tokens": 50,    # Short JSON output
    "do_sample": True,
    "temperature": 0.1,      # Low for deterministic JSON
    "top_p": 0.95,
    "top_k": 40,
    "repetition_penalty": 1.0,  # JSON has repeated structure
    "pad_token_id": tokenizer.eos_token_id
}
```

**Content System:**
- No model used - content served from `lesson_cache.json`
- Pre-built via `scripts/build_lesson_cache.py`
- Instant retrieval (<100ms)

## Sampling Methods

### Nucleus Sampling (Top-P)

**All agents use nucleus sampling** for balanced quality and diversity.

**How it works:**
1. Rank tokens by probability
2. Select smallest set of tokens whose cumulative probability ≥ p
3. Sample from this set

**Parameters:**
- Teaching: `top_p=0.92` (high diversity for natural conversation)
- Grading: `top_p=0.95` (focused but allows minor variations)
- Content: `top_p=0.9` (balanced for exercise generation)

### Top-K Sampling

**Used in conjunction with top-p** to limit vocabulary.

**Parameters:**
- Teaching: `top_k=60` (broader vocabulary)
- Grading: `top_k=40` (focused vocabulary)
- Content: `top_k=40` (controlled generation)

### Temperature Scaling

**Controls randomness of probability distribution.**

**Parameters:**
- Teaching: `temperature=0.7` (moderate - natural but not random)
- Grading: `temperature=0.1` (very low - deterministic for JSON)
- Content: `temperature=0.3` (low-moderate - structured output)

**Effect:**
- `T < 1.0`: More confident, less random
- `T = 1.0`: Original distribution
- `T > 1.0`: More random, less confident

## Session Management

### Storage

**File-based persistence:**
```python
# sessions.json
{
    "session_123": {
        "lesson_number": 1,
        "lesson_name": "Gender and Definite Article",
        "vocabulary": {
            "words": [...],
            "current_batch": 1,
            "quizzed_words": []
        },
        "grammar": {
            "topics": {...},
            "sections": {...}
        },
        "current_progress": "vocab_batch_intro",
        "status": "active"
    }
}
```

**Session lifecycle:**
1. Created on lesson start
2. Updated after each interaction
3. Persists across page reloads
4. Manually cleared by "Reset Session" button

### State Machine

**Orchestrator manages lesson flow as state machine:**

```
lesson_start → vocab_batch_intro → vocab_quiz → vocab_feedback 
              → grammar_overview → grammar_explanation → grammar_quiz
              → final_exam → lesson_complete
```

## Monitoring & Debugging

### Logs

**Gradio provides real-time logs** in Space interface:
- Model loading events
- Inference timing
- Error messages
- User interactions

### Common Issues

**1. Out of Memory (OOM)**
- **Cause:** Models not lazy-loaded properly
- **Fix:** Ensure models loaded via callable getters
- **Check:** `teaching_model_getter()` called, not `teaching_model`

**2. Slow Cold Starts**
- **Cause:** Model loading on first request
- **Expected:** 20-30s for first inference
- **Normal:** Subsequent requests are fast

**3. Session Lost**
- **Cause:** Space rebuild or crash
- **Fix:** Sessions stored in `sessions.json` (persists across rebuilds)
- **Workaround:** Users can restart lesson

**4. GPU Timeout**
- **Cause:** Inference taking >60s
- **Fix:** Reduce `max_new_tokens` or optimize prompts
- **Current:** All agents complete in <5s

## Scaling Considerations

### Current Limits (Zero-GPU Free Tier)

- **Concurrent users:** ~5-10
- **GPU allocation:** 60s per inference
- **Memory:** 16GB GPU RAM
- **Storage:** 50GB persistent

### Optimization Strategies

**1. Model Quantization**
- Consider 4-bit quantization (BitsAndBytes)
- Reduces memory footprint 50-75%
- Slight quality trade-off

**2. Batch Processing**
- Group similar requests (not implemented)
- Would improve throughput for multiple users

**3. Caching**
- Lesson content cached in memory ✅
- Consider caching common responses

**4. Upgrade to Pro**
- **ZeroGPU A10G**: Dedicated GPU, faster
- **Persistent storage**: 100GB+
- **Better scaling**: 50+ concurrent users

## CI/CD Pipeline

### Current Setup

**Manual deployment:**
1. Develop locally on feature branch
2. Test with `python app.py`
3. Merge to main on GitHub
4. Push to HuggingFace: `git push space-v2 main:main`
5. Space auto-rebuilds

### Testing Before Deploy

```bash
# Run test suite
uv run pytest --cov=src

# Check code quality
uv run ruff check .
uv run ruff format .

# Test inference locally
python app.py  # Open http://localhost:7860
```

## Rollback Procedure

**If deployment breaks:**

```bash
# Check Space logs for error
# Identify last working commit
git log --oneline

# Rollback to working version
git push space-v2 <commit-hash>:main --force

# Or rollback on HuggingFace UI:
# Settings → Repository → Click commit → Revert
```

## Security Considerations

### API Keys

**Not required** - all models run locally on Space infrastructure.

### User Data

- Sessions stored ephemerally in `sessions.json`
- No PII collected
- No external API calls
- All processing on HuggingFace infrastructure

### Model Safety

- Base models (Qwen2.5) undergo safety filtering
- Fine-tuned on educational content only
- No harmful content in training data

## Cost Analysis

### Current Cost: $0/month

**Zero-GPU Free Tier:**
- Suitable for: Demo, portfolio, low traffic
- Limitations: Occasional cold starts, shared resources

### Upgrade Path

**Zero-GPU Pro ($9/month):**
- Dedicated GPU allocation
- Faster cold starts
- Better for production use

**A10G Space ($1/hour):**
- Always-on GPU
- Best performance
- Recommended for >100 daily active users

## References

- HuggingFace Spaces Docs: https://huggingface.co/docs/hub/spaces
- Zero-GPU Guide: https://huggingface.co/docs/hub/spaces-zerogpu
- Gradio Documentation: https://gradio.app/docs/
- Model Fine-tuning: See `training/README.md`
