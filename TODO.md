# Arabic Teaching Multi-Agent System - TODO

**Last Updated:** 2026-04-03

---

## ✅ COMPLETED

### Foundation
- [x] Project setup with pyproject.toml
- [x] Pre-commit hooks (ruff, mypy, pytest with 95% coverage)
- [x] .gitignore configuration
- [x] Test infrastructure (pytest, coverage)

### Prompt Engineering System
- [x] Base template classes (Simple, FewShot, ChainOfThought)
- [x] Prompt registry with singleton pattern
- [x] Vocabulary teaching templates (5 templates)
- [x] Grammar teaching templates (5 templates)
- [x] Exercise generation templates (5 templates)
- [x] Utility functions for formatting
- [x] 41 tests for prompts module
- [x] 97%+ test coverage

### RAG Pipeline
- [x] ChromaDB vectorstore wrapper
- [x] Retrieval with semantic search
- [x] Metadata filtering (lesson, exercise_type, skill_focus)
- [x] Template ingestion from markdown files
- [x] 27 exercise templates in data/
- [x] 19 tests for RAG module
- [x] 97%+ test coverage

### Teaching Agents
- [x] BaseAgent abstract class with LLM provider protocol
- [x] VocabularyAgent (5 methods)
  - [x] introduce_words()
  - [x] assess_answer()
  - [x] correct_error()
  - [x] review_words()
  - [x] show_progress()
- [x] GrammarAgent (5 methods)
  - [x] introduce_concept()
  - [x] detect_error()
  - [x] generate_practice()
  - [x] explain_concept()
  - [x] correct_mistake()
- [x] 21 tests for agents
- [x] 98%+ test coverage

### LLM Providers
- [x] OpenAI API provider (optional)
- [x] HuggingFace Transformers provider
- [x] Protocol-based interface
- [x] 7 tests for LLM providers
- [x] 100% test coverage

### Demo & Documentation
- [x] Interactive CLI demo (simple_cli.py with OpenAI)
- [x] HuggingFace CLI demo (hf_cli.py with Qwen 1.5B)
- [x] STATUS.md - Project overview
- [x] agents/README.md
- [x] demo/README.md

---

## 🔄 IN PROGRESS

### Fine-tuned Model Training (SageMaker)
- [ ] Qwen2.5-7B training with v7 data
- [ ] Evaluate error correction capability
- [ ] Compare 7B vs 3B results
- [ ] Integrate fine-tuned model into TransformersProvider

---

## 📋 TODO - Core Features

### ExerciseAgent (Priority: Medium)
- [ ] Create ExerciseAgent class
- [ ] Implement generate_exercise() with RAG retrieval
- [ ] Implement provide_hint()
- [ ] Implement check_answer()
- [ ] Write 8+ tests for ExerciseAgent
- [ ] Achieve 95%+ coverage
- [ ] Update demo to include ExerciseAgent

**Estimated time:** 20-25 minutes  
**Blockers:** None - RAG pipeline already built

---

### LangGraph Orchestration (Priority: HIGH ⭐)
- [ ] Define conversation state schema (Pydantic model)
- [ ] Create StateGraph with agent nodes
- [ ] Implement intent detection logic
- [ ] Implement routing between agents
  - [ ] Route to VocabularyAgent
  - [ ] Route to GrammarAgent
  - [ ] Route to ExerciseAgent (when built)
- [ ] Add session state management
- [ ] Add conversation history tracking
- [ ] Write orchestration tests (10+ tests)
- [ ] Update CLI demo to use orchestrator
- [ ] Test multi-turn conversations

**Estimated time:** 30-40 minutes  
**Blockers:** None - agents are ready  
**Why priority:** Makes this a TRUE multi-agent system

---

## 📋 TODO - Production Features

### API Layer (Priority: Low - Can wait)
- [ ] FastAPI application setup
- [ ] POST /chat endpoint
- [ ] Session management
- [ ] Authentication (optional)
- [ ] WebSocket support for streaming
- [ ] API tests
- [ ] OpenAPI documentation

**Estimated time:** 1 hour  
**Blockers:** Should wait for orchestration to be complete

---

### Streamlit UI (Priority: Low - Can wait)
- [ ] Main chat interface
- [ ] Agent selection dropdown
- [ ] Conversation history display
- [ ] Input box with send button
- [ ] Progress tracking sidebar
- [ ] Exercise display formatting
- [ ] Arabic text rendering
- [ ] Session state management

**Estimated time:** 1-2 hours  
**Blockers:** Should wait for orchestration to be complete

---

## 📋 TODO - Enhancements (Future)

### Model Integration
- [ ] Test fine-tuned Qwen2.5-7B with agents
- [ ] Benchmark 7B vs 1.5B on error correction
- [ ] Add model switching in demo
- [ ] Document model performance differences

### Evaluation
- [ ] Create evaluation dataset
- [ ] Automated accuracy tests
- [ ] Response quality metrics
- [ ] Benchmark different models

### Advanced Features
- [ ] Multi-user support
- [ ] Progress persistence (database)
- [ ] Lesson progression tracking
- [ ] Spaced repetition for vocabulary
- [ ] Audio pronunciation (TTS)
- [ ] Student performance analytics

---

## 📊 Progress Summary

### Overall Completion: ~60%

**Completed (60%):**
- ✅ Prompts (100%)
- ✅ RAG (100%)
- ✅ Agents (67% - 2 of 3 agents)
- ✅ LLM Providers (100%)
- ✅ Demo CLI (100%)
- ✅ Tests & Coverage (100%)

**Remaining (40%):**
- 🔲 ExerciseAgent (0%)
- 🔲 Orchestration (0%) ⭐ **Most important**
- 🔲 API (0%)
- 🔲 UI (0%)

---

## 🎯 Recommended Next Steps

### Immediate (While Training Runs)
1. **Build LangGraph Orchestration** (30-40 min) ⭐
   - Makes agents work together
   - Shows architectural skills
   - Can demo immediately with CLI

### After Training Completes
2. **Test Fine-tuned 7B Model** (15 min)
   - Plug into TransformersProvider
   - Run error correction tests
   - Compare with 1.5B results

3. **Build ExerciseAgent** (20-25 min)
   - Completes the agent trio
   - Uses RAG pipeline

### Later (Optional)
4. **Build Streamlit UI** (1-2 hours)
   - Better UX than CLI
   - Good for demos

5. **Deploy API** (1 hour)
   - Production-ready
   - Multi-user support

---

## 📝 Notes

- All core functionality can work via CLI (no UI needed)
- Orchestration is the key missing piece for multi-agent collaboration
- Fine-tuned model will be plug-and-play when ready
- 98.49% test coverage maintained throughout

---

**Next action:** Build LangGraph orchestration to enable multi-agent conversations
