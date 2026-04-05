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
   │ Teaching │      │  Error   │      │   Content    │
   │  (Face)  │      │Detection │      │  Retrieval   │
   └──────────┘      └──────────┘      └──────────────┘
        │                 │                    │
   Fine-tuned        Fine-tuned          RAG Pipeline
   Qwen2.5-3B       Qwen2.5-3B          + Pinecone
   (Teaching         (Strict JSON        + Embeddings
    style)            grading)           + LLM for
                                          generation
```

**Design Philosophy:**
- **Agent 1:** All user-facing text (teaching, feedback)
- **Agent 2:** Strict grading (JSON in → JSON out)
- **Agent 3:** Content retrieval + holds in memory (no repeated RAG queries)
- **One Model:** Single Qwen2.5-3B fine-tuned for all three agent modes

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

### **Single Fine-Tuned Model**
- **Qwen2.5-3B-Instruct** fine-tuned once (~110-120 conversations)
- Three modes controlled by system prompts (Teaching, Grading, Exercise Generation)
- 4-bit quantization (~2GB memory)
- LoRA rank=32 for efficient fine-tuning

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

### v2 Architecture (Current)
- **[ARCHITECTURE.md](docs/v2/ARCHITECTURE.md)** - Agent specs, model strategy, design decisions
- **[IMPLEMENTATION_PLAN.md](docs/v2/IMPLEMENTATION_PLAN.md)** - TDD checklist with phases
- **[INTERACTION_FLOWS.md](docs/v2/INTERACTION_FLOWS.md)** - Visual flows with mermaid diagrams
- **[API_CONTRACT.md](docs/v2/API_CONTRACT.md)** - Complete API specification

### v1 (Archived)
- See `v1/` folder and `docs/v1/` for previous implementation

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

**Current Phase:** Phase 1 - Foundation (Define Success First)

**Architecture:** ✅ Complete
- [x] Agent specifications documented
- [x] Interaction flows defined
- [x] API contract established
- [x] Evaluation test cases created (75 total)

**Implementation Progress:**
- [x] Task 1.1: Create evaluation dataset (75 test cases)
- [ ] Task 1.2: Set up DeepEval pipeline
- [ ] Task 1.3: Build RAG database schema
- [ ] Task 1.4: Set up Pinecone + embeddings

**Roadmap:**
- **Phase 1:** Foundation (eval-first, RAG setup) - *In Progress*
- **Phase 2:** Core Components (training data, fine-tuning, agents with TDD)
- **Phase 3:** Integration (orchestrator, LangGraph)
- **Phase 4:** Scale Testing (add Lessons 4-5 without retraining)

See [IMPLEMENTATION_PLAN.md](docs/v2/IMPLEMENTATION_PLAN.md) for detailed checklist.

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

### Agent 2 (Error Detection)
- Accuracy: >90% correct/incorrect classification
- Error type identification: >80% accuracy
- Valid JSON output: 100%

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
│   ├── v1/                    # Archived v1 documentation
│   └── v2/                    # Current v2 architecture
│       ├── ARCHITECTURE.md
│       ├── IMPLEMENTATION_PLAN.md
│       ├── INTERACTION_FLOWS.md
│       └── API_CONTRACT.md
├── v1/                        # Archived v1 code
│   ├── agents/
│   ├── prompts/
│   ├── rag/
│   └── tests/
├── src/                       # v2 development (gitignored until ready)
│   ├── agents/
│   ├── orchestration/
│   ├── rag/
│   └── evaluation/
├── data/
│   └── evaluation/
│       └── test_cases.json    # 75 eval test cases
├── tests/                     # v2 tests
├── pyproject.toml
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

*Last updated: April 5, 2026*
