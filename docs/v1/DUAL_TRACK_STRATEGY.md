# Dual-Track Strategy: Final Project vs. Job Portfolio

**Purpose:** Maintain two versions - safe fallback for class, ambitious version for job

---

## 📚 **TRACK 1: Original Repo (Final Project - Safe)**

**Location:** `llm-class-2026-winter-cohort/final_project_planning/`
**Purpose:** Course deliverable - working demo, passes requirements
**Status:** KEEP AS-IS (fallback)

### **What It Has:**
- ✅ Fine-tuned Qwen2.5-3B model (v6, or v7 when ready)
- ✅ Training data (113 conversations)
- ✅ Evaluation framework (16 tests for Capability #1)
- ✅ Simple Streamlit demo
- ✅ Documentation

### **Architecture:**
```
Single Fine-Tuned Model
  ├── Vocabulary Teaching
  ├── Grammar Teaching
  └── Error Correction
```

### **What It Demonstrates:**
- Fine-tuning with LoRA ✅
- Instruction tuning ✅
- Evaluation methodology ✅
- Pedagogical AI ✅

### **Timeline:**
- Can complete in 1 week if needed
- Already 90% done (just need v7 error fixes)

### **Risk Level:** LOW
- Known working approach
- Minimal external dependencies
- Proven with v6 results

---

## 💼 **TRACK 2: New Repo (Job Portfolio - Ambitious)**

**Location:** `arabic-teaching-multi-agent/`
**Purpose:** Job applications - shows advanced skills
**Status:** BUILD NOW (3 weeks)

### **What It Has:**
- ✅ Multi-agent system (5 agents)
- ✅ LangGraph orchestration
- ✅ RAG pipeline (ChromaDB + exercise templates)
- ✅ Fine-tuned model integration (reuses v7)
- ✅ Prompt engineering library
- ✅ Self-correction loops
- ✅ 25-test evaluation framework
- ✅ FastAPI backend
- ✅ Advanced Streamlit UI
- ✅ Production-quality documentation

### **Architecture:**
```
LangGraph Orchestrator
  ├── Coordinator (state management)
  ├── Vocabulary Teacher (fine-tuned model)
  ├── Grammar Teacher (fine-tuned model)
  ├── Exercise Generator (RAG + ChromaDB)
  └── Evaluator (validation + feedback)
```

### **What It Demonstrates:**
- Multi-agent orchestration ✅ (LangGraph)
- RAG implementation ✅ (ChromaDB)
- Vector search ✅ (semantic + hybrid)
- Prompt engineering ✅ (library + patterns)
- Self-correction ✅ (retry with feedback)
- Evaluation frameworks ✅ (25 tests)
- API development ✅ (FastAPI)
- Production UI ✅ (Streamlit)
- Documentation ✅ (architecture, API specs, model card)
- **PLUS** Fine-tuning expertise ✅

### **Timeline:**
- 3 weeks for complete implementation
- Week 1: RAG + agents
- Week 2: Orchestration + evaluation
- Week 3: API + UI + docs

### **Risk Level:** MEDIUM
- New technologies (LangGraph, ChromaDB)
- More complex integration
- Longer timeline
- BUT: Has fallback (Track 1)

---

## 🔄 **How They Relate**

### **Shared Components:**
Both repos share:
- Training data (copy from Track 1 → Track 2)
- Fine-tuned model (trained once, used in both)
- Vocabulary files
- Curriculum sequence
- Core evaluation tests

### **Track 2 EXTENDS Track 1:**
```
Track 1: Fine-tuned model that works ✓
         ↓
Track 2: Wrap model in agent interface
         + Add orchestration layer
         + Add RAG for exercises
         + Add API layer
         + Enhance docs
```

### **Strategy:**
1. **Weeks 1-3:** Build Track 2 (job portfolio)
2. **If Track 2 succeeds:** Use for BOTH job AND final project
3. **If Track 2 delayed:** Fall back to Track 1 for final project

---

## 📊 **Feature Comparison**

| Feature | Track 1 (Final Project) | Track 2 (Job Portfolio) |
|---------|------------------------|------------------------|
| **Model** | Fine-tuned Qwen2.5-3B ✅ | Same + agent wrappers ✅ |
| **Architecture** | Single model | Multi-agent (5 agents) |
| **Orchestration** | None | LangGraph ✅ |
| **RAG** | None | ChromaDB + templates ✅ |
| **Prompt Engineering** | In training data | Structured library ✅ |
| **Self-Correction** | None | Retry loops ✅ |
| **Evaluation** | 16 tests | 25 tests ✅ |
| **API** | None | FastAPI ✅ |
| **UI** | Basic Streamlit | Enhanced Streamlit ✅ |
| **Documentation** | Basic | Production-grade ✅ |
| **Time to Complete** | 1 week | 3 weeks |
| **Risk** | LOW | MEDIUM |

---

## 🎯 **Use Cases**

### **When to use Track 1:**
- ✅ Final project demo (if Track 2 not ready)
- ✅ Quick working prototype
- ✅ Testing fine-tuning iterations
- ✅ Class presentation fallback

### **When to use Track 2:**
- ✅ Job applications (primary)
- ✅ Portfolio website showcase
- ✅ Technical interviews
- ✅ Demonstrating architecture skills
- ✅ Final project (if ready in time)

---

## ⚠️ **Important Rules**

### **DO:**
- ✅ Keep Track 1 repo working at all times (safety net)
- ✅ Copy training data from Track 1 → Track 2
- ✅ Reuse fine-tuned model in both repos
- ✅ Test Track 2 components independently
- ✅ Document both repos clearly

### **DON'T:**
- ❌ Delete or break Track 1 while building Track 2
- ❌ Mix the two repos (keep separate)
- ❌ Assume Track 2 will finish on time
- ❌ Abandon Track 1 until Track 2 is proven

---

## 📅 **Timeline Management**

### **Parallel Work:**
```
Week 1 (Track 2):
  - Build RAG pipeline
  - Implement agents
  - Keep Track 1 as is

Week 2 (Track 2):
  - Build orchestration
  - Enhance evaluation
  - Track 1 still available

Week 3 (Track 2):
  - Build API + UI
  - Complete docs
  - Decide: Use Track 2 or Track 1 for final project

Decision Point (End of Week 3):
  IF Track 2 ready & tested → Use for job + final project
  IF Track 2 incomplete → Use Track 1 for final project, continue Track 2 for job
```

---

## 🎓 **Final Project Submission Decision Tree**

```
Is Track 2 ready by final project deadline?
│
├─ YES → Submit Track 2
│   ├─ Show multi-agent architecture
│   ├─ Demo RAG pipeline
│   ├─ Highlight evaluation framework
│   └─ Explain: "Went beyond requirements"
│
└─ NO → Submit Track 1
    ├─ Show fine-tuning results
    ├─ Demo simple UI
    ├─ Highlight evaluation tests
    └─ Explain: "Focused on core ML skills"
```

**Both are valid submissions for the course.**

---

## 💼 **Job Application Strategy**

**Primary portfolio:** Track 2 (multi-agent RAG system)

**Resume bullet:**
> "ARABIC TEACHER LLM: Multi-Agent RAG Orchestrator
> Python | LangGraph | ChromaDB | FastAPI | Streamlit
> 
> Architected 5-agent system with LangGraph orchestration; implemented 
> production RAG pipeline with ChromaDB for dynamic exercise generation; 
> integrated fine-tuned Qwen2.5-3B for specialized grammar teaching; 
> built comprehensive evaluation framework with self-correction loops; 
> deployed FastAPI backend with Streamlit UI."

**GitHub repos to share:**
- Primary: `arabic-teaching-multi-agent` (Track 2)
- Secondary: Mention fine-tuning work from Track 1

---

## ✅ **Success Criteria**

### **Track 1 Success:**
- [ ] Fine-tuned model works (v7 fixes error correction)
- [ ] 16 tests pass at >70%
- [ ] Simple demo runs
- [ ] Can present in 10 minutes

### **Track 2 Success:**
- [ ] 5 agents implemented
- [ ] LangGraph orchestration working
- [ ] RAG retrieves relevant exercises
- [ ] 25 tests pass at >70%
- [ ] API + UI functional
- [ ] Documentation complete
- [ ] Can demo in 10 minutes

---

## 🚀 **Current Status**

**Track 1 (Final Project):**
- Status: 90% complete
- Blockers: v7 error correction fixes needed
- Timeline: 1 week to finish
- Risk: LOW

**Track 2 (Job Portfolio):**
- Status: 0% complete (starting now)
- Blockers: None (greenfield)
- Timeline: 3 weeks
- Risk: MEDIUM

**Strategy:** Build Track 2 over next 3 weeks, keep Track 1 as safety net.

---

*Created: 2026-03-30*
*Status: Dual-track strategy committed*
*Primary focus: Track 2 (job portfolio)*
*Fallback: Track 1 (final project)*
