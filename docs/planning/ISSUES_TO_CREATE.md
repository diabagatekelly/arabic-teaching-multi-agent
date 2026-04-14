# GitHub Issues to Create for Tomorrow (2026-04-15)

## 🔥 Priority 1: Fine-tuning

### Issue 1: Fine-tune Agent 1 (Teaching) - Qwen2.5-3B
**Title:** Fine-tune Agent 1 (TeachingAgent) for improved teaching style

**Labels:** `enhancement`, `agent-1`, `fine-tuning`, `priority-high`

**Description:**
Fine-tune Qwen2.5-3B model for Agent 1 (Teaching) to improve teaching style and user interaction.

**Current Performance:**
- Baseline 3B: 52% pass rate
- Baseline 7B: 58% pass rate

**Goal:** Achieve 65%+ pass rate with fine-tuned 3B (competitive with baseline 7B)

**Tasks:**
- [ ] Create fine-tuning dataset from evaluation test cases
  - Extract successful teaching interactions (26/50 passing cases)
  - Add conversational examples with proper tone
  - Include proper Arabic harakaat usage patterns
  - Add vocabulary introduction patterns
- [ ] Set up fine-tuning pipeline
  - Configure LoRA/QLoRA for efficient training
  - Set hyperparameters (lr, batch size, epochs)
  - Add validation split for monitoring
- [ ] Run fine-tuning job (~2-3 hours)
- [ ] Evaluate on test suite (50 test cases)
- [ ] Compare: baseline 3B vs fine-tuned 3B vs baseline 7B
- [ ] Document results and recommendations

**Success Criteria:**
- Fine-tuned 3B reaches 65%+ pass rate
- Teaching style improvements visible in qualitative review
- Model maintains proper Arabic formatting

**Files:**
- `scripts/finetune_agent1.py` - Training script
- `data/finetuning/agent1_training_data.jsonl` - Training dataset
- `data/evaluation/teaching_agent/finetuned_report.md` - Results

---

### Issue 2: Fine-tune Agent 2 (Grading) - Qwen2.5-7B
**Title:** Fine-tune Agent 2 (GradingAgent) for flexible grading with edge cases

**Labels:** `enhancement`, `agent-2`, `fine-tuning`, `priority-high`

**Description:**
Fine-tune Qwen2.5-7B model for Agent 2 (Grading) to handle edge cases: synonyms, typos, harakaat variations, partial credit.

**Current Performance:**
- Baseline 3B: 47.5% pass rate
- Baseline 7B: 55% pass rate

**Goal:** Achieve 70%+ pass rate with fine-tuned 7B

**Edge Cases to Address:**
1. Synonym handling (e.g., "the book" vs "a book")
2. Harakaat variations (e.g., الكِتَاب vs الكتاب)
3. Typo tolerance (e.g., "kitab" vs "kitaab")
4. Partial credit (e.g., correct root but wrong form)

**Tasks:**
- [ ] Create fine-tuning dataset
  - Focus on edge case examples from evaluation failures
  - Include reasoning-heavy examples (why answer is correct/incorrect)
  - Add explanation quality examples
  - Cover all grading scenarios (correct, incorrect, partial)
- [ ] Fine-tune Qwen2.5-7B
  - Use 7B for better reasoning capacity
  - Emphasize explanation generation
- [ ] Evaluate on grading test suite (40 test cases)
- [ ] Qualitative review of edge case handling
- [ ] Compare: baseline 3B vs baseline 7B vs fine-tuned 7B

**Success Criteria:**
- Fine-tuned 7B reaches 70%+ pass rate
- Edge cases handled correctly (synonym: 80%+, harakaat: 90%+, typo: 70%+)
- Explanations are clear and educational

**Files:**
- `scripts/finetune_agent2.py` - Training script
- `data/finetuning/agent2_training_data.jsonl` - Training dataset
- `data/evaluation/grading_agent/finetuned_report.md` - Results

---

## 🛠️ Priority 2: RAG Improvement

### Issue 3: Fix Agent 3 RAG Schema Mismatch
**Title:** Fix RAG template schema inconsistency causing 0% structure pass rate

**Labels:** `bug`, `agent-3`, `rag`, `priority-high`

**Description:**
Agent 3 (ContentAgent) RAG templates have schema mismatch with test expectations, causing 0% structure validation pass rate despite generating valid JSON.

**Root Cause:**
RAG examples show: `"correct": "الكِتَاب"` (answer string)
Test schema expects: `"correct": true` (boolean) or `"correct": "a"` (multiple choice option)

**Current Performance:**
- 3B: 20% pass rate (10% JSON validity, 0% structure)
- 7B: 20% pass rate (55% JSON validity, 0% structure)

**Goal:** Fix schema → 60%+ pass rate

**Tasks:**
- [ ] Audit all 12 exercise type templates
  - translation.md
  - multiple_choice.md
  - fill_in_blank.md
  - cloze.md
  - dictation.md
  - error_correction.md
  - noun_adjective_agreement.md
  - pattern_recognition.md
  - sentence_level.md
  - sorting.md
  - paradigm_table.md
  - transformation_chain.md
- [ ] Standardize "correct" field per type:
  - Translation: Remove "correct", use "answer" only
  - Multiple choice: "correct": "a/b/c/d"
  - Fill-in-blank: "correct": "answer text"
- [ ] Update all examples (3 per difficulty × 12 types = 36 examples)
- [ ] Ensure examples use learned vocabulary
- [ ] Verify harakaat consistency
- [ ] Re-run evaluation
- [ ] Compare: old schema vs new schema

**Success Criteria:**
- Structure validation: 0% → 80%+ pass rate
- Overall pass rate: 20% → 60%+
- All exercise types use correct schema

**Files:**
- `data/rag_database/exercises/*.md` - All 12 template files
- `data/evaluation/content_agent/schema_fix_report.md` - Before/after comparison

---

## 🎯 Priority 3: Orchestration

### Issue 4: Implement LangGraph Orchestration Layer
**Title:** Build multi-agent orchestration with LangGraph for agent coordination

**Labels:** `feature`, `orchestration`, `langgraph`, `priority-high`

**Description:**
Build the orchestration layer that coordinates all 3 agents using LangGraph for state management and routing.

**Architecture:**
```
User Input → Agent 1 (Teaching) → Agent 3 (Content) → User Exercise
User Answer → Agent 2 (Grading) → Agent 1 (Feedback) → Next Step
```

**Tasks:**
- [ ] Define system state schema
  - User context (user_id, session_id, current_lesson)
  - Learning progress (learned_items, lesson_history)
  - Conversation state (history, pending_exercise, last_agent)
- [ ] Implement LangGraph nodes
  - `teaching_node` - Wraps Agent 1
  - `grading_node` - Wraps Agent 2
  - `content_node` - Wraps Agent 3
- [ ] Implement routing logic
  - User message → teaching_node
  - Exercise request → content_node
  - Answer submission → grading_node
  - Grading result → teaching_node (feedback)
- [ ] Add state persistence
  - Session checkpointing
  - Progress saving
  - Conversation history
- [ ] Error handling
  - Agent failures → graceful fallback
  - Retry logic for transient errors
  - Timeout handling
- [ ] Write unit tests for routing

**Success Criteria:**
- All agents communicate successfully through orchestrator
- State persists across conversation turns
- Routing logic handles all message types correctly
- Error handling prevents system crashes

**Files:**
- `src/orchestrator/graph.py` - LangGraph definition
- `src/orchestrator/state.py` - State schema
- `src/orchestrator/nodes.py` - Agent node wrappers
- `src/orchestrator/routing.py` - Conditional routing
- `tests/orchestrator/test_routing.py` - Unit tests

---

## ✅ Priority 4: Integration Tests

### Issue 5: Create End-to-End Integration Tests
**Title:** Build integration test suite for full multi-agent system

**Labels:** `testing`, `integration`, `priority-medium`

**Description:**
Create comprehensive integration tests that validate the full system with all agents working together.

**Test Scenarios:**

**1. Happy Path - Complete Lesson Flow**
```python
def test_complete_lesson_flow():
    # User starts lesson 1
    # Agent 1 introduces first vocab word
    # Agent 3 generates exercise
    # User answers correctly
    # Agent 2 grades as correct
    # Agent 1 provides positive feedback
    # System moves to next word
    assert lesson_completed
```

**2. Error Handling - Wrong Answer Flow**
```python
def test_wrong_answer_flow():
    # User submits incorrect answer
    # Agent 2 identifies specific mistake
    # Agent 1 provides corrective feedback
    # System retries with simpler exercise
    assert feedback_helpful
    assert retry_offered
```

**3. Edge Cases**
- Harakaat variations acceptance
- Synonym handling
- Typo tolerance (1-2 chars off)
- Partial credit scenarios

**4. Performance Tests**
- Response time < 3s per agent
- Memory usage with 10 concurrent sessions
- Token usage optimization

**Tasks:**
- [ ] Set up integration test infrastructure
- [ ] Implement happy path test
- [ ] Implement error flow test
- [ ] Implement edge case tests
- [ ] Implement performance benchmarks
- [ ] Add test fixtures for sessions
- [ ] Mock external dependencies (if needed)
- [ ] CI integration

**Success Criteria:**
- 80%+ integration tests passing
- All critical paths covered
- Performance benchmarks documented
- Tests run in < 5 minutes

**Files:**
- `tests/integration/test_full_lesson.py`
- `tests/integration/test_error_flows.py`
- `tests/integration/test_edge_cases.py`
- `tests/integration/test_performance.py`
- `tests/integration/fixtures.py`

---

## 📝 Documentation Tasks

### Issue 6: Document Evaluation Results and Findings
**Title:** Document baseline vs fine-tuned performance and key findings

**Labels:** `documentation`, `priority-low`

**Description:**
Create comprehensive documentation of all evaluation results, findings, and recommendations.

**Tasks:**
- [ ] Create evaluation summary report
  - Baseline performance (all agents, all models)
  - Fine-tuned performance (Agent 1, Agent 2)
  - RAG improvement impact (Agent 3)
- [ ] Document key findings
  - When to use 3B vs 7B
  - RAG vs fine-tuning trade-offs
  - Schema design lessons learned
- [ ] Create recommendations guide
  - Model selection criteria
  - Fine-tuning best practices
  - RAG template design guidelines
- [ ] Update README with final architecture
- [ ] Add performance benchmarks to docs

**Files:**
- `docs/evaluation_summary.md`
- `docs/findings.md`
- `docs/recommendations.md`
- `README.md` (update)

---

## 🎯 Sprint Goals Summary

**Tomorrow (2026-04-15) - Agent Improvement Day:**

**Must Complete:**
1. ✅ Agent 1 fine-tuning running
2. ✅ Agent 2 fine-tuning running
3. ✅ Agent 3 RAG schema fixed
4. ✅ Orchestration skeleton implemented
5. ✅ 1+ integration test passing

**Nice to Have:**
- All fine-tuning evaluations complete
- Full integration test suite
- Performance benchmarks documented

**Definition of Done:**
- All agents improved from baseline
- Full system can run end-to-end
- Tests validate system behavior
- Findings documented for future work
