# Implementation Plan - Arabic Teaching Multi-Agent System

**Last Updated:** 2026-04-14

---

## Current Status Summary

### ✅ Completed (Phase 1 - Evaluation Infrastructure)

1. **Evaluation Framework** 
   - DeepEval integration with custom metrics
   - Agent 1 (Teaching) evaluation suite - 50 test cases
   - Agent 2 (Grading) evaluation suite - 40 test cases
   - Agent 3 (Content) evaluation suite - 25 test cases
   - Baseline performance established for 3B and 7B models

2. **Agent Implementations (Base)**
   - Agent 1 (TeachingAgent): Teaching style and user interaction
   - Agent 2 (GradingAgent): Answer validation with flexible grading
   - Agent 3 (ContentAgent): Exercise generation with RAG

3. **RAG Database v1**
   - 12 exercise types with templates
   - Lesson content with vocabulary and grammar
   - Initial template-based approach

### 📊 Baseline Performance (Before Fine-tuning)

| Agent | Model | Pass Rate | Notes |
|-------|-------|-----------|-------|
| Agent 1 | 3B | 52% | Good teaching style baseline |
| Agent 1 | 7B | 58% | Better but not worth 2x size |
| Agent 2 | 3B | 47.5% | Struggles with flexible grading |
| Agent 2 | 7B | 55% | Better reasoning for edge cases |
| Agent 3 | 3B/7B | 20% | RAG schema mismatch issue |

---

## 🎯 Tomorrow (2026-04-15): Agent Improvement Day

### Priority 1: Fine-tune Agents 1 & 2

#### Agent 1 (Teaching) - Fine-tuning Pipeline
**Goal:** Improve teaching style, personalization, and user interaction from 52% → 70%+

**Tasks:**
- [ ] Create fine-tuning dataset from evaluation test cases
  - Extract successful teaching interactions
  - Add more conversational examples
  - Include proper Arabic harakaat usage
  - Add vocabulary introduction patterns
- [ ] Set up fine-tuning pipeline for Qwen2.5-3B
  - Configure LoRA/QLoRA parameters
  - Set training hyperparameters
  - Monitor for overfitting
- [ ] Run fine-tuning job (~2-3 hours)
- [ ] Evaluate fine-tuned model on test set
- [ ] Compare: baseline 3B vs fine-tuned 3B vs baseline 7B
- [ ] Document: Does fine-tuned 3B beat baseline 7B?

**Success Metric:** Fine-tuned 3B reaches 65%+ pass rate

#### Agent 2 (Grading) - Fine-tuning Pipeline
**Goal:** Improve flexible grading with edge cases from 47.5% → 70%+

**Tasks:**
- [ ] Create fine-tuning dataset for grading
  - Focus on synonym handling
  - Include harakaat variations
  - Add typo tolerance examples
  - Cover partial credit scenarios
- [ ] Fine-tune Qwen2.5-7B for grading
  - Use reasoning-heavy examples
  - Emphasize explanation quality
- [ ] Evaluate on grading test suite
- [ ] Compare: 3B vs fine-tuned 7B

**Success Metric:** Fine-tuned 7B reaches 70%+ pass rate with better edge case handling

---

### Priority 2: Fix Agent 3 RAG Schema Issues

#### Root Cause Analysis (Completed)
**Problem Identified:** Schema mismatch between RAG examples and test expectations
- RAG examples show: `"correct": "الكِتَاب"` (answer string)
- Test schema expects: `"correct": true` (boolean) or `"correct": "a"` (option)
- Result: 0% structure pass rate despite valid JSON

#### RAG Improvement Tasks
- [ ] **Fix schema consistency**
  - Audit all 12 exercise type templates
  - Standardize "correct" field format per type:
    - Translation: Use "answer" field only
    - Multiple choice: Use "correct": "a/b/c/d"
    - Fill-in-blank: Use "correct": "answer text"
  - Remove "correct" field where not needed
  
- [ ] **Improve example quality**
  - Ensure all examples use learned vocabulary
  - Add more variety per difficulty level
  - Fix harakaat consistency
  
- [ ] **Test retrieval filtering**
  - Verify difficulty-based filtering works
  - Confirm 2-3 examples per request is optimal
  
- [ ] **Re-evaluate**
  - Run evaluation with fixed schema
  - Target: 60%+ pass rate without fine-tuning
  - Compare: Do we need to fine-tune Agent 3 or is RAG sufficient?

**Success Metric:** 60%+ pass rate with corrected schema

---

### Priority 3: Orchestration Layer (Critical Path)

#### Build LangGraph Orchestrator
**Goal:** Complete multi-agent coordination system

**Tasks:**
- [ ] **Define system state**
  ```python
  class SystemState:
      user_id: str
      session_id: str
      current_lesson: int
      learned_items: List[str]
      conversation_history: List[Message]
      pending_exercise: Optional[Exercise]
      last_agent: str
  ```

- [ ] **Implement routing logic**
  - User message → Agent 1 (Teaching)
  - Agent 1 generates exercise → Agent 3 (Content)
  - User submits answer → Agent 2 (Grading)
  - Grading result → Agent 1 (Feedback)
  
- [ ] **State management**
  - Session persistence
  - Learned vocabulary tracking
  - Progress checkpointing
  
- [ ] **Agent communication**
  - Define message formats between agents
  - Handle agent failures gracefully
  - Implement retry logic

**Files to Create:**
- `src/orchestrator/graph.py` - LangGraph definition
- `src/orchestrator/state.py` - State schema
- `src/orchestrator/nodes.py` - Agent node wrappers
- `src/orchestrator/routing.py` - Conditional routing logic

---

### Priority 4: Integration Tests

#### End-to-End Test Scenarios
**Goal:** Validate full system with all agents working together

**Test Cases:**
- [ ] **Happy path**: Complete lesson flow
  1. User starts lesson 1
  2. Agent 1 introduces vocabulary
  3. Agent 3 generates translation exercise
  4. User answers correctly
  5. Agent 2 grades as correct
  6. Agent 1 provides positive feedback
  7. Move to next word
  
- [ ] **Error handling**: Wrong answer flow
  1. User submits incorrect answer
  2. Agent 2 identifies mistake
  3. Agent 1 provides corrective feedback
  4. System retries with simpler exercise
  
- [ ] **Edge cases**:
  - Harakaat variations (with/without vowel marks)
  - Synonym acceptance
  - Typo tolerance
  - Partial credit scenarios
  
- [ ] **Performance tests**:
  - Response time < 3 seconds per agent
  - Memory usage with 10 concurrent sessions
  - Token usage optimization

**Files to Create:**
- `tests/integration/test_full_lesson.py`
- `tests/integration/test_error_flows.py`
- `tests/integration/test_edge_cases.py`

---

## 📋 Definition of Done (Tomorrow EOD)

### Must Have:
- [x] Agent 1 fine-tuning job running or complete
- [x] Agent 2 fine-tuning job running or complete
- [x] Agent 3 RAG schema fixed and re-evaluated
- [x] Orchestration layer skeleton implemented
- [x] At least 1 end-to-end integration test passing

### Nice to Have:
- [ ] All fine-tuning evaluations complete
- [ ] Full integration test suite passing
- [ ] Performance benchmarks documented

---

## 🐛 Known Issues

### Agent 3 (Content Generation)
**Issue:** Schema mismatch between RAG examples and test expectations
- **Impact:** 0% structure pass rate
- **Root Cause:** Inconsistent "correct" field format across exercise types
- **Fix:** Update all 12 exercise templates with correct schema
- **Status:** Documented, fix planned for tomorrow

### Agent 1 (Teaching)
**Issue:** Test mode not exiting properly
- **Impact:** Test sessions persist after completion
- **Root Cause:** Missing state cleanup in test completion logic
- **Fix:** Add proper session termination
- **Status:** Low priority, workaround exists

### Agent 2 (Grading)
**Issue:** Overly strict on harakaat variations
- **Impact:** Rejects valid answers missing vowel marks
- **Root Cause:** Base model too literal, needs fine-tuning examples
- **Fix:** Include harakaat flexibility in training data
- **Status:** Will be addressed in fine-tuning

---

## 📈 Success Metrics

### Phase 2 Goals (Fine-tuning & Integration)
- **Agent 1 (3B fine-tuned):** 65%+ pass rate
- **Agent 2 (7B fine-tuned):** 70%+ pass rate  
- **Agent 3 (RAG improved):** 60%+ pass rate
- **Orchestration:** All agents communicate successfully
- **Integration tests:** 80%+ pass rate

### Phase 3 Goals (Production)
- **User experience:** < 3s response time
- **Accuracy:** 85%+ correct grading
- **Engagement:** Users complete 5+ lessons
- **Scalability:** Support 100+ concurrent sessions

---

## 🔄 Next Steps After Tomorrow

1. **UI/UX Layer**
   - Streamlit interface for web demo
   - CLI interface for testing
   - Session management UI

2. **Deployment**
   - Containerize with Docker
   - Set up model serving (TGI/vLLM)
   - Deploy orchestrator to cloud

3. **Monitoring**
   - Agent performance metrics
   - User analytics
   - Error tracking and alerting

4. **Content Expansion**
   - Add lessons 2-10
   - Expand vocabulary database
   - Create more exercise types
