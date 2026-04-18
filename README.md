---
title: Arabic Teaching System
emoji: 📚
colorFrom: green
colorTo: blue
sdk: gradio
sdk_version: "5.0.0"
app_file: app.py
pinned: false
---

# 🇸🇦 Arabic Teaching System

An interactive Arabic language learning system powered by fine-tuned AI agents running on HuggingFace Zero-GPU.

## Features

- **Interactive Chat Interface**: Learn Arabic through conversational lessons
- **Multi-Agent System**: 
  - Teaching Agent (Fine-tuned Qwen2.5-7B) - Presents lessons and feedback
  - Grading Agent (Fine-tuned Qwen2.5-7B) - Evaluates your answers
  - Content Agent - Retrieves lesson content and generates exercises
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
- Teaching Agent: Trained on 153 multi-turn conversational examples
- Grading Agent: Trained on 346 grading examples with edge case handling
- Method: LoRA (rank=32, alpha=64)
- Framework: Unsloth + PEFT

**Training Data**: Multi-turn Arabic teaching conversations covering:
- Vocabulary introduction and quizzing
- Grammar explanations
- Personalized feedback
- Flexible grading with synonym/typo tolerance

## Architecture

```
User Input → Teaching Agent → Content Agent → Grading Agent → Feedback
                ↑                                                  ↓
                └──────────────────────────────────────────────────┘
```

Built with:
- **LangGraph**: Multi-agent orchestration
- **Transformers**: Model inference
- **PEFT**: LoRA adapters
- **Gradio**: Interactive UI
- **HuggingFace Spaces**: Zero-GPU hosting

## Credits

- Base model: [Qwen/Qwen2.5-7B-Instruct](https://huggingface.co/Qwen/Qwen2.5-7B-Instruct)
- Fine-tuning framework: [Unsloth](https://github.com/unslothai/unsloth)
- Developed as part of LLM course winter cohort 2026

## License

Apache 2.0 (same as base Qwen model)
