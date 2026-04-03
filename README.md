# Arabic Teaching Multi-Agent System

**Production-grade multi-agent RAG system for Arabic language teaching**

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![LangChain](https://img.shields.io/badge/LangChain-v0.1+-green.svg)](https://github.com/langchain-ai/langchain)

---

## 🎯 Project Overview

An intelligent Arabic language teaching system built with **multi-agent orchestration**, **RAG (Retrieval-Augmented Generation)**, and **fine-tuned LLMs**. The system coordinates specialized agents to deliver personalized, adaptive Arabic lessons with real-time error correction and dynamic exercise generation.

### Architecture

```
┌─────────────────────────────────────────────────────────┐
│          LESSON COORDINATOR (LangGraph)                  │
│     Orchestrates workflow, manages conversation state    │
└─────────────────────────────────────────────────────────┘
                          │
        ┌─────────────────┼────────────────┬────────────┐
        ▼                 ▼                ▼            ▼
   ┌─────────┐      ┌──────────┐     ┌──────────┐  ┌───────────┐
   │  VOCAB  │      │ GRAMMAR  │     │EXERCISE  │  │ EVALUATOR │
   │ TEACHER │      │ TEACHER  │     │GENERATOR │  │   AGENT   │
   └─────────┘      └──────────┘     └──────────┘  └───────────┘
        │                │                 │             │
   Fine-tuned       Fine-tuned      RAG Pipeline    Rule-based
   Qwen2.5-3B       Qwen2.5-3B      + ChromaDB     + LLM
   (LoRA)           (LoRA)          + Embeddings   Validation
```

---

## 🚀 Key Features

### **Multi-Agent Orchestration**
- **5 specialized agents** coordinated via LangGraph state machine
- Autonomous task delegation with human-in-the-loop checkpoints
- Conversation state management across agents
- Intent routing based on lesson phase and student performance

### **Intelligent RAG Pipeline**
- **ChromaDB** vector store with 50+ exercise templates
- Semantic search using OpenAI embeddings
- Hybrid retrieval (keyword + semantic)
- Dynamic exercise generation adapted to lesson vocabulary
- Metadata filtering by grammar focus, difficulty, and lesson number

### **Fine-Tuned Language Models**
- **Qwen2.5-3B** fine-tuned with LoRA (16-bit quantization)
- 113 training conversations across vocabulary and grammar teaching
- Specialized for pedagogical interactions in Arabic
- Deterministic evaluation mode (do_sample=False)

### **Self-Correction & Validation**
- Retry loops with evaluator feedback
- Multi-metric evaluation (accuracy, consistency, safety)
- 25+ automated tests across 4 capability areas
- Real-time error detection and correction

### **Production API & UI**
- **FastAPI** backend with RESTful endpoints
- **Streamlit** interactive frontend with real-time chat
- Agent activity visualization
- Lesson progress tracking
- Evaluation dashboard

---

## 🛠️ Technology Stack

**Core Framework:**
- [LangChain](https://github.com/langchain-ai/langchain) - LLM application framework
- [LangGraph](https://github.com/langchain-ai/langgraph) - Multi-agent orchestration
- [ChromaDB](https://www.trychroma.com/) - Vector database
- [OpenAI API](https://platform.openai.com/) - Embeddings

**Models:**
- [Qwen2.5-3B-Instruct](https://huggingface.co/Qwen/Qwen2.5-3B-Instruct) - Base model
- [PEFT](https://github.com/huggingface/peft) - LoRA fine-tuning
- [Transformers](https://github.com/huggingface/transformers) - Model inference

**API & UI:**
- [FastAPI](https://fastapi.tiangolo.com/) - High-performance API
- [Streamlit](https://streamlit.io/) - Interactive web interface
- [Pydantic](https://docs.pydantic.dev/) - Data validation

**Development:**
- Python 3.10+
- Poetry / pip for dependency management
- pytest for testing

---

## 🚀 Quick Start

### Prerequisites
- Python 3.10+
- OpenAI API key
- Git

### Installation

1. **Clone the repository:**
```bash
git clone https://github.com/diabagatekelly/arabic-teaching-multi-agent.git
cd arabic-teaching-multi-agent
```

2. **Create virtual environment:**
```bash
python -m venv venv
source venv/bin/activate  # On Mac/Linux
# venv\Scripts\activate   # On Windows
```

3. **Install dependencies:**
```bash
pip install -r requirements.txt
```

4. **Set up environment variables:**
```bash
cp .env.example .env
# Edit .env and add your OpenAI API key
```

5. **Initialize vector store:**
```bash
python scripts/setup_vectorstore.py
```

6. **Run the application:**
```bash
# Start FastAPI backend
uvicorn api.main:app --reload --port 8000

# In another terminal, start Streamlit UI
streamlit run ui/app.py --server.port 8501
```

7. **Access the application:**
- UI: http://localhost:8501
- API docs: http://localhost:8000/docs

---

## 💼 Portfolio Highlights

**This project demonstrates:**

✅ **Multi-agent systems** - LangGraph orchestration with 5 specialized agents  
✅ **RAG implementation** - Production ChromaDB pipeline with semantic search  
✅ **Fine-tuning** - LoRA fine-tuning on specialized teaching dataset  
✅ **Prompt engineering** - Systematic prompt library with few-shot & CoT patterns  
✅ **Evaluation frameworks** - 25+ automated tests with multi-metric assessment  
✅ **Self-correction** - Retry loops with evaluator feedback  
✅ **API development** - FastAPI with RESTful endpoints  
✅ **Production UI** - Interactive Streamlit interface  
✅ **Documentation** - Architecture diagrams, API specs, model cards  

---

## 📖 Documentation

- **[Architecture](docs/ARCHITECTURE.md)** - System design and agent interactions
- **[RAG Pipeline](docs/RAG_PIPELINE.md)** - Retrieval implementation details
- **[Agent Design](docs/AGENT_DESIGN.md)** - Agent responsibilities and interfaces
- **[Prompt Engineering](docs/PROMPT_ENGINEERING.md)** - Prompt strategy and patterns
- **[Evaluation](docs/EVALUATION.md)** - Testing methodology and metrics
- **[API Specification](docs/API_SPECS.md)** - Complete API reference
- **[Model Card](docs/MODEL_CARD.md)** - Responsible AI documentation
- **[Deployment](docs/DEPLOYMENT.md)** - Production deployment guide

---

## 🗓️ Development Status

**Current Phase:** Week 1 - RAG Pipeline & Agent Implementation

**Timeline:**
- ✅ Week 0: Project setup & planning
- 🔄 Week 1: RAG pipeline + agent implementations (in progress)
- ⏳ Week 2: LangGraph orchestration + evaluation framework
- ⏳ Week 3: API, UI, and documentation

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

**Note:** This is an educational/portfolio project demonstrating GenAI engineering capabilities.

---

## 👤 Author

**Kelly Diabagate**

- GitHub: [@diabagatekelly](https://github.com/diabagatekelly)
- LinkedIn: [Add your LinkedIn]
- Email: [Add your email]

---

## 🙏 Acknowledgments

- **LangChain/LangGraph** for multi-agent framework
- **Qwen Team** for Qwen2.5 base model
- **Tatoeba Project** for Arabic example sentences
- **OpenAI** for embeddings API

---

⭐ **If you find this project useful, please give it a star!**

---

*Last updated: April 3, 2026*
