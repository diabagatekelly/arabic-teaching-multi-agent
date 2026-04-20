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

# 🇸🇦 Arabic Teaching System

An interactive Arabic language learning system powered by fine-tuned AI agents running on HuggingFace Zero-GPU.

**🚀 Try it live:** [https://huggingface.co/spaces/kdiabagate/arabic-teacher-v2](https://huggingface.co/spaces/kdiabagate/arabic-teacher-v2)

**📖 Documentation:** See [`docs/`](docs/) directory for comprehensive technical documentation

## Features

- **Interactive Chat Interface**: Learn Arabic through conversational lessons
- **Multi-Agent System**: 
  - Teaching Agent (Fine-tuned Qwen2.5-7B + LoRA) - Presents lessons with encouraging feedback
  - Grading Agent (Same model, different prompts) - Evaluates answers with flexible matching
  - Content System - Pre-built lesson cache for fast, reliable content delivery
- **Batched Vocabulary Learning**: Learn 3-4 words at a time
- **Grammar Lessons**: Master Arabic grammar concepts
- **Real-time Progress Tracking**: See your accuracy and learned items
- **GPU Acceleration**: Fast inference with HuggingFace Zero-GPU

## How to Use

1. Select a lesson (1-10) from the sidebar
2. Click "Start New Lesson"
3. Follow the teacher's instructions
4. Answer vocabulary and grammar questions
5. Receive instant feedback and track your progress

## Model Details

**Base Models**: Qwen/Qwen2.5-7B-Instruct (Apache 2.0)

**Fine-tuning**:
- Single Model: `kdiabagate/qwen-7b-arabic-teaching` on HuggingFace Hub
- Training: 153 multi-turn conversational examples
- Method: LoRA (rank=32, alpha=64) merged at deployment
- Framework: Unsloth + PEFT
- Differentiation: Teaching vs Grading via prompts and inference configs (temp 0.7 vs 0.1)

**Training Data**: Multi-turn Arabic teaching conversations covering:
- Vocabulary introduction and quizzing
- Grammar explanations
- Personalized feedback
- Flexible grading with synonym/typo tolerance

## Architecture

```
User Input → Orchestrator → Teaching/Grading Agent (Qwen 7B + LoRA) → Response
                ↓
         lesson_cache.json (pre-built content)
```

Built with:
- **Orchestrator**: Custom state machine for lesson flow
- **Transformers + PEFT**: Model inference with LoRA adapters
- **Gradio**: Interactive chat UI with flashcards
- **HuggingFace Spaces**: Zero-GPU hosting with lazy model loading

## Documentation

- **[ARCHITECTURE.md](docs/ARCHITECTURE.md)** - System design and agent details
- **[INFERENCE.md](docs/INFERENCE.md)** - Inference pipeline and generation configs
- **[DEPLOYMENT.md](docs/DEPLOYMENT.md)** - HuggingFace Spaces deployment guide
- **[API_CONTRACT.md](docs/API_CONTRACT.md)** - Gradio interface contract
- **[PROMPTS_INVENTORY.md](docs/PROMPTS_INVENTORY.md)** - All 19 prompts documented

## Credits

- Base model: [Qwen/Qwen2.5-7B-Instruct](https://huggingface.co/Qwen/Qwen2.5-7B-Instruct)
- Fine-tuning framework: [Unsloth](https://github.com/unslothai/unsloth)
- Developed as part of LLM course winter cohort 2026

## License

Apache 2.0 (same as base Qwen model)
