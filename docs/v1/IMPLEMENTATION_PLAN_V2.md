# Arabic Teaching LLM - Multi-Agent RAG Implementation Plan

**Purpose:** Job portfolio demonstrating multi-agent orchestration + RAG + evaluation
**Timeline:** 3 weeks
**Status:** Committed - Ready to implement

---

## 🎯 Project Overview

### Committed Architecture
**5-Agent System with LangGraph Orchestration:**

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
   (v7 model)       (v7 model)      + Templates    Validation
```

### Key Deliverables
- ✅ Multi-agent orchestration (LangGraph)
- ✅ RAG pipeline implementation (ChromaDB + embeddings)
- ✅ Fine-tuned model integration
- ✅ Prompt engineering library
- ✅ Self-correction loops
- ✅ Evaluation framework (20-25 tests)
- ✅ FastAPI backend
- ✅ Streamlit frontend
- ✅ Technical documentation

---

## 📂 New Repository Structure

```
arabic-teaching-multi-agent/
├── README.md                          # Project overview + architecture
├── requirements.txt                   # Python dependencies
├── .env.example                       # Environment variables template
├── pyproject.toml                     # Poetry/project config
│
├── agents/                            # Agent implementations
│   ├── __init__.py
│   ├── coordinator.py                 # LangGraph orchestrator
│   ├── vocabulary_teacher.py          # Fine-tuned model wrapper
│   ├── grammar_teacher.py             # Fine-tuned model wrapper
│   ├── exercise_generator.py          # RAG-based generator
│   ├── evaluator.py                   # Validation agent
│   └── base_agent.py                  # Shared agent interface
│
├── orchestration/                     # LangGraph workflow
│   ├── __init__.py
│   ├── state.py                       # Conversation state schema
│   ├── workflow.py                    # LangGraph state machine
│   ├── router.py                      # Intent routing logic
│   └── nodes.py                       # Agent node definitions
│
├── rag/                               # RAG pipeline
│   ├── __init__.py
│   ├── vectorstore.py                 # ChromaDB setup
│   ├── embeddings.py                  # Embedding utilities
│   ├── retriever.py                   # Retrieval logic
│   ├── exercise_templates/            # Exercise template documents
│   │   ├── fill_in_blank.md
│   │   ├── error_detection.md
│   │   ├── sentence_building.md
│   │   └── metadata.json
│   └── ingestion.py                   # Document processing pipeline
│
├── prompts/                           # Prompt engineering library
│   ├── __init__.py
│   ├── prompt_library.py              # Centralized prompts
│   ├── few_shot_examples.py           # Few-shot learning examples
│   ├── chain_of_thought.py            # CoT templates
│   └── templates/
│       ├── vocabulary_teaching.txt
│       ├── grammar_teaching.txt
│       ├── exercise_generation.txt
│       └── evaluation.txt
│
├── models/                            # Fine-tuned model integration
│   ├── __init__.py
│   ├── model_loader.py                # Load Qwen2.5-3B v7
│   ├── inference.py                   # Generation utilities
│   └── config.py                      # Model configuration
│
├── evaluation/                        # Evaluation framework
│   ├── __init__.py
│   ├── evaluation_framework.py        # Main evaluation system
│   ├── metrics.py                     # Accuracy, consistency, safety metrics
│   ├── self_correction.py             # Retry logic with feedback
│   ├── test_suites/
│   │   ├── capability_1_vocab.py      # 16 existing tests
│   │   ├── capability_2_grammar.py    # Grammar teaching tests
│   │   ├── capability_3_error.py      # Error correction tests
│   │   └── capability_4_exercises.py  # NEW: Exercise quality tests
│   └── reports/                       # Evaluation results
│
├── api/                               # FastAPI backend
│   ├── __init__.py
│   ├── main.py                        # FastAPI app
│   ├── routes/
│   │   ├── chat.py                    # /api/chat endpoint
│   │   ├── lessons.py                 # /api/lessons endpoints
│   │   ├── evaluation.py              # /api/evaluate endpoint
│   │   └── health.py                  # Health checks
│   ├── schemas.py                     # Pydantic models
│   ├── dependencies.py                # DI for agents
│   └── middleware.py                  # Auth, logging, CORS
│
├── ui/                                # Streamlit frontend
│   ├── app.py                         # Main Streamlit app
│   ├── components/
│   │   ├── chat_interface.py
│   │   ├── lesson_progress.py
│   │   ├── agent_visualizer.py        # Show which agent is active
│   │   └── evaluation_dashboard.py
│   └── utils.py
│
├── data/                              # Training data & datasets
│   ├── training/
│   │   ├── training_data_v7.jsonl     # Final training data
│   │   ├── vocab_only_final.jsonl
│   │   ├── grammar_only_conversations.jsonl
│   │   └── error_correction_v2.jsonl  # Enhanced error examples
│   ├── raw/
│   │   ├── tatoeba_arabic.txt         # (from final_project_planning)
│   │   └── vocab_master.txt
│   └── vocab_conversational.txt
│
├── docs/                              # Documentation
│   ├── ARCHITECTURE.md                # System architecture
│   ├── API_SPECS.md                   # OpenAPI/Swagger docs
│   ├── AGENT_DESIGN.md                # Agent responsibilities
│   ├── RAG_PIPELINE.md                # RAG implementation details
│   ├── PROMPT_ENGINEERING.md          # Prompt strategy
│   ├── EVALUATION.md                  # Testing methodology
│   ├── MODEL_CARD.md                  # Responsible AI doc
│   └── DEPLOYMENT.md                  # How to run/deploy
│
├── tests/                             # Unit & integration tests
│   ├── test_agents.py
│   ├── test_orchestration.py
│   ├── test_rag.py
│   ├── test_api.py
│   └── test_evaluation.py
│
├── scripts/                           # Utility scripts
│   ├── setup_vectorstore.py           # Initialize ChromaDB
│   ├── ingest_exercises.py            # Load exercise templates
│   ├── train_model.py                 # Fine-tuning script (from Kaggle)
│   └── run_evaluation.py              # Run full test suite
│
└── notebooks/                         # Jupyter notebooks
    ├── 01_rag_exploration.ipynb       # RAG pipeline development
    ├── 02_agent_testing.ipynb         # Agent testing
    ├── 03_evaluation_analysis.ipynb   # Results analysis
    └── kd-arabic-training-t4-x2.ipynb # (copied from final_project)
```

---

## 📅 3-Week Implementation Timeline

### **WEEK 1: Core Infrastructure**

#### **Day 1-2: Project Setup & RAG Foundation**
- [ ] Create new private GitHub repo: `arabic-teaching-multi-agent`
- [ ] Copy relevant files from `final_project_planning/`:
  - Training data (v6 + plan for v7)
  - Tatoeba dataset
  - Vocabulary files
  - Curriculum docs
- [ ] Set up project structure (directories above)
- [ ] Install dependencies: LangChain, LangGraph, ChromaDB, FastAPI, Streamlit
- [ ] Create exercise template documents (50+ templates)
- [ ] **RAG Pipeline Implementation:**
  - Document chunking strategy
  - Embed exercise templates with OpenAI
  - Initialize ChromaDB vector store
  - Test retrieval (keyword + semantic search)

**Deliverable:** Working RAG pipeline that retrieves exercise templates

---

#### **Day 3-4: Agent Implementations**
- [ ] **Vocabulary Teacher Agent:**
  - Wrapper for fine-tuned Qwen2.5-3B v7
  - Load model (use existing v6, or wait for v7)
  - Simple interface: `teach_vocabulary(lesson_num, vocab_list)`
  - Test with sample prompts
  
- [ ] **Grammar Teacher Agent:**
  - Wrapper for same fine-tuned model
  - Interface: `teach_grammar(topic, vocab_list, grammar_rule)`
  - Test with Lesson 1-2 grammar
  
- [ ] **Exercise Generator Agent (RAG):**
  - Integrate ChromaDB retriever
  - Template adaptation logic
  - Interface: `generate_exercise(grammar_focus, vocab, difficulty, type)`
  - Test: Generate 10 diverse exercises
  
- [ ] **Evaluator Agent:**
  - Rule-based validation (gender agreement, definiteness, etc.)
  - LLM fallback for nuanced feedback
  - Interface: `evaluate(question, student_answer, expected, grammar_rule)`

**Deliverable:** 4 working agents (coordinator comes next week)

---

#### **Day 5-7: Prompt Engineering Library**
- [ ] Create `prompts/prompt_library.py`:
  - Vocabulary teaching template
  - Grammar teaching template
  - Exercise generation template (few-shot)
  - Evaluator template (chain-of-thought)
- [ ] Document prompt engineering strategy
- [ ] Create versioned prompt templates
- [ ] Test prompts with each agent
- [ ] Write `PROMPT_ENGINEERING.md` documentation

**Deliverable:** Structured prompt library with documentation

---

### **WEEK 2: Orchestration & Integration**

#### **Day 8-9: LangGraph Coordinator**
- [ ] Define conversation state schema:
  ```python
  class ConversationState(TypedDict):
      lesson_number: int
      current_phase: str  # "vocab" | "grammar" | "exercises"
      vocabulary_learned: List[str]
      grammar_topics_covered: List[str]
      student_performance: Dict[str, float]
      conversation_history: List[Message]
  ```
- [ ] Build LangGraph state machine:
  - Intent routing (vocab → grammar → exercises)
  - Agent nodes (call appropriate agent)
  - Decision nodes (pass/fail → next step)
  - Human-in-the-loop checkpoints
- [ ] Implement coordinator logic:
  - Route to vocab teacher
  - After teaching, route to evaluator
  - Based on score, route to grammar or review
- [ ] Test end-to-end flow (mock student responses)

**Deliverable:** Working LangGraph orchestrator coordinating all 5 agents

---

#### **Day 10-11: Self-Correction Implementation**
- [ ] Create `SelfCorrectingAgent` wrapper:
  - Retry logic (max 3 attempts)
  - Feedback injection into prompts
  - Failure tracking
- [ ] Integrate with Exercise Generator:
  - If generated exercise is invalid → retry with feedback
- [ ] Integrate with Evaluator:
  - If evaluation is inconsistent → retry with explanation request
- [ ] Test self-correction loops
- [ ] Document in `EVALUATION.md`

**Deliverable:** Agents with retry + feedback loops

---

#### **Day 12-14: Evaluation Framework Expansion**
- [ ] Expand test suite from 16 → 25 tests:
  - **Capability #1 (Vocab):** Keep existing 16 tests
  - **Capability #2 (Grammar):** Add 5 tests for grammar teaching
  - **Capability #3 (Error Correction):** Keep existing 4 tests
  - **NEW Capability #4 (Exercise Quality):** Add 5 tests
    - Exercise variety
    - Appropriate difficulty
    - Grammar focus alignment
    - Vocabulary usage
    - Answer correctness
- [ ] Implement multi-metric evaluation:
  - Accuracy metric
  - Consistency metric
  - Safety metric
  - Helpfulness metric
- [ ] Run full evaluation suite on integrated system
- [ ] Generate evaluation reports
- [ ] Document methodology in `EVALUATION.md`

**Deliverable:** 25-test evaluation framework with reports

---

### **WEEK 3: API, UI & Documentation**

#### **Day 15-16: FastAPI Backend**
- [ ] Create API endpoints:
  - `POST /api/chat` - Main conversation endpoint
  - `GET /api/lessons/{lesson_id}` - Lesson info
  - `GET /api/lessons/{lesson_id}/progress` - Student progress
  - `POST /api/evaluate` - Run evaluation tests
  - `GET /api/health` - Health check
- [ ] Integrate agents with API:
  - Dependency injection for agent instances
  - Session management (conversation state)
  - Error handling
- [ ] Add middleware:
  - CORS
  - Request logging
  - Rate limiting (optional)
- [ ] Write OpenAPI/Swagger docs
- [ ] Test all endpoints with curl/Postman

**Deliverable:** Working FastAPI backend with documented endpoints

---

#### **Day 17-18: Streamlit Frontend**
- [ ] Create main Streamlit app:
  - Chat interface (send message → display response)
  - Lesson progress tracker (current lesson, words learned)
  - Agent visualizer (show which agent is responding)
  - Evaluation dashboard (test results, pass rates)
- [ ] Integrate with FastAPI backend
- [ ] Add visual elements:
  - Arabic text display (RTL support)
  - Transliteration toggle
  - Agent activity indicator
  - Progress bars
- [ ] Polish UX:
  - Loading states
  - Error messages
  - Success feedback
- [ ] Test full user flow

**Deliverable:** Interactive Streamlit UI connected to backend

---

#### **Day 19-21: Documentation & Polish**
- [ ] Write comprehensive documentation:
  - `ARCHITECTURE.md` - System design with diagrams
  - `AGENT_DESIGN.md` - Agent responsibilities & interfaces
  - `RAG_PIPELINE.md` - How RAG works, retrieval strategy
  - `MODEL_CARD.md` - Responsible AI documentation
  - `DEPLOYMENT.md` - How to run locally
  - `API_SPECS.md` - Complete API reference
- [ ] Create architecture diagrams:
  - Overall system diagram
  - Agent collaboration flow
  - RAG pipeline diagram
  - State machine visualization
- [ ] Update README with:
  - Project overview
  - Quick start guide
  - Technology stack
  - Demo screenshots/GIFs
  - Link to documentation
- [ ] Add code comments and docstrings
- [ ] Final testing:
  - Run full evaluation suite
  - Test all API endpoints
  - Test UI flows
  - Check error handling
- [ ] Create demo recording (5-10 min video)

**Deliverable:** Production-quality documentation + polished demo

---

## 🔧 Technical Specifications

### **Dependencies**
```txt
# Core
python>=3.10
langchain>=0.1.0
langgraph>=0.1.0
langchain-openai>=0.1.0

# RAG
chromadb>=0.4.0
openai>=1.0.0
tiktoken>=0.5.0

# Model
torch>=2.0.0
transformers>=4.30.0
peft>=0.5.0

# API
fastapi>=0.110.0
uvicorn>=0.27.0
pydantic>=2.0.0

# UI
streamlit>=1.31.0

# Evaluation
pytest>=7.4.0
langsmith>=0.1.0  # Optional

# Utilities
python-dotenv>=1.0.0
requests>=2.31.0
```

### **Environment Variables**
```bash
# .env
OPENAI_API_KEY=sk-...
LANGSMITH_API_KEY=...  # Optional
MODEL_PATH=/path/to/qwen2.5-3b-v7
CHROMADB_PATH=./data/vectorstore
```

---

## 🎯 Success Criteria

### **Technical Deliverables:**
- [ ] 5 agents implemented and tested independently
- [ ] LangGraph orchestrator coordinating all agents
- [ ] RAG pipeline retrieving exercise templates with >80% relevance
- [ ] Self-correction loops reducing errors by >30%
- [ ] 25-test evaluation suite with >70% pass rate overall
- [ ] FastAPI with 5+ documented endpoints
- [ ] Streamlit UI with chat, progress tracking, evaluation dashboard
- [ ] Complete documentation (architecture, API, deployment)

### **Demo Requirements:**
- [ ] Show multi-agent orchestration (visualize which agent responds)
- [ ] Show RAG retrieval (display retrieved templates)
- [ ] Show self-correction (demonstrate retry with feedback)
- [ ] Show evaluation results (pass rates across capabilities)
- [ ] Show end-to-end lesson flow (vocab → grammar → exercises)

### **Job Portfolio Requirements:**
- [ ] GitHub repo with clean code + documentation
- [ ] README with architecture diagram + quick start
- [ ] API documentation (OpenAPI/Swagger)
- [ ] Responsible AI documentation (model card)
- [ ] Demo video (5-10 minutes)
- [ ] Evaluation report showing test results

---

## ⚠️ Risk Management

### **High Risk Items:**
1. **LangGraph learning curve** - Mitigation: Start Day 8, allocate 2 full days
2. **RAG retrieval quality** - Mitigation: Test early (Day 1-2), iterate on chunking
3. **Agent integration bugs** - Mitigation: Test each agent independently first
4. **Time pressure** - Mitigation: MVP first, polish later

### **Critical Path:**
```
Day 1-2 (RAG) → Day 3-4 (Agents) → Day 8-9 (Orchestrator) → Day 15-16 (API)
```
If any of these slip, entire timeline slips.

### **Fallback Options:**
- **If LangGraph too complex:** Use simple router instead of state machine
- **If RAG underperforms:** Fall back to hardcoded exercise templates
- **If fine-tuned model not ready:** Use GPT-4 for vocab/grammar agents
- **If time runs out:** Cut Streamlit UI, demo via API only

---

## 📊 Progress Tracking

### **Week 1 Checklist:**
- [ ] RAG pipeline working
- [ ] 4 agents implemented
- [ ] Prompt library created
- [ ] Documentation started

### **Week 2 Checklist:**
- [ ] LangGraph orchestrator working
- [ ] Self-correction implemented
- [ ] 25-test suite complete
- [ ] End-to-end flow tested

### **Week 3 Checklist:**
- [ ] FastAPI deployed
- [ ] Streamlit UI working
- [ ] All documentation complete
- [ ] Demo recorded

---

## 🚀 Post-Implementation

### **After Week 3:**
- [ ] Optional: Add LangSmith observability
- [ ] Optional: Deploy to cloud (AWS/Azure)
- [ ] Optional: Add v7 training data fixes
- [ ] Share portfolio with job applications
- [ ] Adapt simple version for final project if needed

---

## 📝 Notes

**What stays from final_project_planning:**
- Training data (will enhance error correction in Week 2)
- Curriculum sequence (Lessons 1-2 focus)
- Evaluation framework (expand from 16 → 25 tests)
- Fine-tuned model (v6, or v7 if ready)

**What's new for job portfolio:**
- Multi-agent architecture (LangGraph)
- RAG pipeline (ChromaDB)
- FastAPI backend
- Advanced documentation
- Professional polish

**Dual-track strategy:**
- Job portfolio (new repo): Full 5-agent system
- Final project (original repo): Simple fine-tuned model as fallback

---

*Created: 2026-03-30*
*Status: Ready to implement*
*Estimated completion: 2026-04-20 (3 weeks)*
