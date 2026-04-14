# Arabic Teaching Multi-Agent System v2

**Production-grade multi-agent RAG system for Arabic language teaching with eval-driven development**

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![LangGraph](https://img.shields.io/badge/LangGraph-latest-green.svg)](https://github.com/langchain-ai/langgraph)

---

## 🎯 Project Overview

An intelligent Arabic language teaching system built with **multi-agent orchestration**, **RAG (Retrieval-Augmented Generation)**, and **fine-tuned LLMs**. The system coordinates three specialized agents to deliver personalized Arabic lessons with vocabulary teaching, grammar instruction, error detection, and dynamic exercise generation.

**Key Innovation:** Separates **content** (RAG) from **style** (fine-tuning) for true scalability—add new grammar lessons without retraining models.

### Architecture v2

```
┌─────────────────────────────────────────────────────────┐
│          ORCHESTRATOR (LangGraph)                        │
│     State management, agent routing, session tracking    │
└─────────────────────────────────────────────────────────┘
                          │
        ┌─────────────────┼────────────────────┐
        ▼                 ▼                    ▼
   ┌──────────┐      ┌──────────┐      ┌──────────────┐
   │ AGENT 1  │      │ AGENT 2  │      │   AGENT 3    │
   │ Teaching │      │ Grading  │      │   Content    │
   │  (Face)  │      │  Agent   │      │  Retrieval   │
   └──────────┘      └──────────┘      └──────────────┘
        │                 │                    │
   Fine-tuned        Fine-tuned          RAG Pipeline
   Qwen2.5-3B       Qwen2.5-7B          + Pinecone
   (Teaching         (Flexible,          + Embeddings
    style)            accurate           + LLM for
                      grading)            generation
```

**Design Philosophy:**
- **Agent 1:** All user-facing text (teaching, feedback) - 3B fine-tuned
- **Agent 2:** Flexible grading with edge case handling (synonyms, typos, harakaat) - 7B fine-tuned
- **Agent 3:** Content retrieval + holds in memory (no repeated RAG queries)
- **Dual-Model Strategy:** 3B for teaching style, 7B for grading reasoning

---

## 🚀 Key Features

### **Eval-Driven Development**
- **75 test cases** defined BEFORE building agents
- **DeepEval pipeline** with automated metrics (sentiment, accuracy, JSON validity)
- **Baseline testing** to prove fine-tuning effectiveness
- Test-Driven Development (TDD) approach for AI systems

### **True Scalability**
- Add new grammar lessons by uploading markdown (< 5 min, **no retraining**)
- Grammar rules stored in RAG, not model weights
- Supports 100+ lessons without model degradation
- Content lives in Pinecone vector database

### **Multi-Agent Orchestration**
- **3 specialized agents** with clear separation of concerns
- LangGraph state machine for complex conversation flows
- Session management with vocabulary/grammar progress tracking
- Pre-loading strategy for fast quiz responses

### **Vocabulary + Grammar Teaching**
- **Vocabulary:** 10 words in batches (3-3-3-1), user-paced quizzes, flashcard integration
- **Grammar:** Multiple topics per lesson, 5-question quizzes, review suggestions if ≥2 wrong
- Immediate per-question feedback with encouraging tone
- Running score tracking

### **Dual Fine-Tuned Models**
- **Agent 1/3: Qwen2.5-3B-Instruct** fine-tuned (~110-120 conversations)
  - Teaching, feedback, exercise generation modes
  - 4-bit quantization (~2GB memory)
  - LoRA rank=32 for efficient fine-tuning
- **Agent 2: Qwen2.5-7B-Instruct** fine-tuned (~270+ grading examples)
  - Flexible grading with edge case handling
  - JSON-only output enforcement
  - Arabic harakaat rules (internal optional, case endings required)

---

## 🛠️ Technology Stack

**Core Framework:**
- [LangGraph](https://github.com/langchain-ai/langgraph) - Multi-agent orchestration
- [LangChain](https://github.com/langchain-ai/langchain) - Prompt assembly
- [Pinecone](https://www.pinecone.io/) - Vector database (cloud)
- [DeepEval](https://github.com/confident-ai/deepeval) - LLM evaluation framework

**Models:**
- [Qwen2.5-3B-Instruct](https://huggingface.co/Qwen/Qwen2.5-3B-Instruct) - Base model
- [all-MiniLM-L6-v2](https://huggingface.co/sentence-transformers/all-MiniLM-L6-v2) - Embeddings (384-dim)
- [PEFT](https://github.com/huggingface/peft) - LoRA fine-tuning
- [Transformers](https://github.com/huggingface/transformers) - Model inference

**API & UI:**
- [FastAPI](https://fastapi.tiangolo.com/) - High-performance API
- [Streamlit](https://streamlit.io/) - Interactive web interface (optional)
- [Pydantic](https://docs.pydantic.dev/) - Data validation

**Development:**
- Python 3.10+
- pytest for testing (95%+ coverage target)
- ruff for linting
- pre-commit hooks

---

## 📖 Documentation

- **[ARCHITECTURE.md](docs/ARCHITECTURE.md)** - Agent specs, model strategy, design decisions
- **[API_CONTRACT.md](docs/API_CONTRACT.md)** - Complete API specification
- **[WORKFLOW.md](docs/WORKFLOW.md)** - Git workflow and development process
- **[TOOLING.md](docs/TOOLING.md)** - Development tooling (uv, ruff, mypy, pytest)

---

## 🚀 Quick Start

### Prerequisites
- Python 3.10+
- Pinecone API key (free tier)
- Git

### Installation

1. **Clone the repository:**
```bash
git clone https://github.com/diabagatekelly/arabic-teaching-multi-agent.git
cd arabic-teaching-multi-agent
```

2. **Create virtual environment:**
```bash
python -m venv .venv
source .venv/bin/activate  # On Mac/Linux
# .venv\Scripts\activate   # On Windows
```

3. **Install dependencies:**
```bash
pip install -r requirements.txt
# OR use uv for faster installation
uv pip install -r requirements.txt
```

4. **Set up environment variables:**
```bash
cp .env.example .env
# Edit .env and add:
# - PINECONE_API_KEY
# - PINECONE_ENVIRONMENT
# - (Optional) OPENAI_API_KEY for embeddings
```

5. **Run tests:**
```bash
pytest tests/
```

---

## 🗓️ Development Status

**Current Phase:** Phase 2 - Multi-Agent Orchestration (Integration Complete)

**Architecture:** ✅ Complete
- [x] Agent specifications documented
- [x] Interaction flows defined
- [x] API contract established
- [x] Evaluation test cases created (94 total)

**Implementation Progress:**

**Phase 1 - Foundation:** ✅ COMPLETE
- [x] Evaluation dataset (94 test cases - 44 teaching/feedback, 50 grading)
- [x] DeepEval pipeline with custom metrics
- [x] Baseline evaluation (Agent 1: 3B, Agent 2: 7B)
- [x] RAG database setup with Pinecone
- [x] Model fine-tuning (Qwen2.5-3B for Agent 1/3)

**Phase 2 - Multi-Agent System:** ✅ COMPLETE
- [x] Agent 1 (TeachingAgent) implementation - 26 tests passing
- [x] Agent 2 (GradingAgent) implementation - 15 tests passing
- [x] Agent 3 (ContentAgent) implementation - 21 tests passing
- [x] LangGraph orchestrator - 124 tests passing
  - [x] Core state machine and routing
  - [x] Agent node wrappers
  - [x] End-to-end integration tests (11 tests)
  - [x] Lesson initialization caching
  - [x] Grammar rules pre-loading
  - [x] Grading correctness logic (39 tests)
- [x] Agent orchestrator adapters - 35 agent tests passing
  - [x] TeachingAgent: start_lesson(), provide_feedback(), handle_user_message()
  - [x] GradingAgent: grade_answer()
  - [x] Input validation (required fields, mode validation, empty strings)

**Phase 3 - API Layer & Integration:** 🔄 IN PROGRESS
- [ ] FastAPI wrapper with session management - **NEXT**
- [ ] Real model integration (load fine-tuned models) - **NEXT**
- [ ] CLI or Streamlit UI
- [ ] Performance testing and optimization

**Roadmap:**
- **Phase 1:** Foundation (eval-first, RAG setup) - ✅ COMPLETE
- **Phase 2:** Multi-Agent System - ✅ COMPLETE
- **Phase 3:** API Layer & UI - 🔄 IN PROGRESS (FastAPI wrapper, real models)
- **Phase 4:** Production Readiness (performance, monitoring, deployment)

---

## 💼 Portfolio Highlights

**This project demonstrates:**

✅ **Eval-Driven Development** - 75 test cases defined before building agents  
✅ **Multi-agent systems** - LangGraph orchestration with clear separation of concerns  
✅ **Scalable RAG** - Add content without retraining models  
✅ **Fine-tuning strategy** - Content vs. style separation  
✅ **Production API design** - Complete API contract with error handling  
✅ **TDD for AI** - Test cases, metrics, baseline comparisons  
✅ **Clean architecture** - Well-documented design decisions  
✅ **State management** - Complex conversation flows with vocabulary/grammar tracking  

---

## 📊 Metrics & Goals

### Agent 1 (Teaching)
- Sentiment score: >0.9 for teaching, >0.8 for feedback
- Includes all required elements (Arabic, transliteration, English)
- Asks comprehension questions

### Agent 2 (Grading)
- Accuracy: >90% correct/incorrect classification
- Edge case handling: synonyms, typos, capitalization, articles
- Arabic harakaat: internal marks optional, case endings required
- Valid JSON output: 100%
- JSON structure compliance: 100%

### Agent 3 (Content Retrieval + Generation)
- Retrieval relevance: >90%
- Retrieval latency: <500ms
- Exercise faithfulness to template: >90%

### Scalability
- Add new lesson in <10 minutes (no retraining)
- Support 100+ grammar points without degradation

---

## 📁 Project Structure

```
arabic-teaching-multi-agent/
├── docs/
│   ├── ARCHITECTURE.md        # Agent specifications & design
│   ├── API_CONTRACT.md        # API specification
│   ├── WORKFLOW.md            # Git workflow
│   ├── TOOLING.md             # Development tools
│   └── evaluation/
│       └── README.md          # Evaluation framework docs
├── src/
│   └── evaluation/            # DeepEval pipeline & custom metrics
│       ├── metrics.py
│       ├── deepeval_pipeline.py
│       └── baseline.py
├── data/
│   └── evaluation/
│       └── test_cases.json    # 75 eval test cases
├── tests/
│   └── evaluation/            # Tests for evaluation module
├── pyproject.toml
├── uv.lock
└── README.md
```

---

## 🔄 Development Workflow

**Branch Strategy:**
- `main` - Stable, reviewed code only
- `dev` - Integration branch
- `phase-N/*` - Feature branches for each phase/task

**Process:**
1. Create feature branch from `dev`
2. Implement with TDD (tests first)
3. Create PR to `dev` (triggers Sourcery + /review skill)
4. Merge to `dev` after approval
5. Periodically merge `dev` → `main`

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

**Note:** This is an educational/portfolio project demonstrating GenAI engineering capabilities and production-ready multi-agent system design.

---

## 👤 Author

**Kelly Diabagate**

- GitHub: [@diabagatekelly](https://github.com/diabagatekelly)
- Portfolio: [Link to your portfolio]

---

## 🙏 Acknowledgments

- **LangChain/LangGraph** for multi-agent framework
- **Qwen Team** for Qwen2.5 base model
- **DeepEval** for LLM evaluation tools
- **Pinecone** for vector database

---

⭐ **If you find this project useful, please give it a star!**

---

*Last updated: April 14, 2026*
