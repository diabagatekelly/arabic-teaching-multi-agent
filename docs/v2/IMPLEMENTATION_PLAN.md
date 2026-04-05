# Implementation Plan - Eval-Driven Development

**Project:** Arabic Teaching Multi-Agent System v2  
**Approach:** Test/Eval-Driven Development (TDD for AI)  
**Serves:** School final project + Work portfolio

---

## Project Goals

### School Requirements
- ✅ Demonstrates fine-tuning (Qwen2.5-3B)
- ✅ Demonstrates RAG (Pinecone + semantic search)
- ✅ Demonstrates multi-agent orchestration (LangGraph)
- ✅ Shows scalability (add lessons without retraining)
- ✅ Includes evaluation pipeline (DeepEval)

### Work Portfolio Requirements
- ✅ Production-ready architecture (follows 2026 best practices)
- ✅ Clean separation of concerns (agents have clear responsibilities)
- ✅ Scalable design (supports 100+ grammar points)
- ✅ Well-documented (architecture, flows, decisions)
- ✅ Measurable results (automated evals, metrics)

---

## Phase 1: Foundation (Define Success First)

**Timeline:** 1-2 days  
**Goal:** Know what "good" looks like before building

### Task 1.1: Create Evaluation Dataset

**Purpose:** Test cases to measure agent quality

- [ ] **Teaching Mode Test Cases** (30 test cases)
  - [ ] Vocabulary batch introduction (10 test cases)
    - [ ] Input: Batch of 3 words with Arabic + transliteration + English
    - [ ] Expected: Formatted presentation with emoji, clear structure
    - [ ] Metrics: Sentiment (>0.9), Includes all 3 words, Readable format
  - [ ] Grammar topic explanation (10 test cases)
    - [ ] Input: Grammar rule + examples
    - [ ] Expected: Encouraging explanation with comprehension question
    - [ ] Metrics: Sentiment (>0.9), Contains question, Structured format
  - [ ] Quiz feedback (10 test cases)
    - [ ] Input: Correct/incorrect answers
    - [ ] Expected: Encouraging feedback with running score
    - [ ] Metrics: Sentiment (>0.8), Includes score, Appropriate tone
  
- [ ] **Grading Mode Test Cases** (35 test cases)
  - [ ] Vocabulary grading (15 test cases)
    - [ ] 8 correct translations → Expected: `{"correct": true}`
    - [ ] 7 incorrect translations → Expected: `{"correct": false}`
    - [ ] Metrics: Accuracy (>90%), Valid JSON, Simple true/false
  - [ ] Grammar grading (20 test cases)
    - [ ] 10 correct answers → Expected: `{"correct": true}`
    - [ ] 10 incorrect answers → Expected: `{"correct": false, "errors": [...]}`
    - [ ] Metrics: Accuracy (>90%), Valid JSON, Correct error type identification
  
- [ ] **Exercise Generation Test Cases** (10 test cases)
  - [ ] Input: Template + vocabulary + grammar point
  - [ ] Expected: Valid exercises with answer keys
  - [ ] Metrics: Faithfulness to template, Uses vocabulary correctly

**Deliverable:** `data/evaluation/test_cases.json`

---

### Task 1.2: Set Up DeepEval Pipeline

**Purpose:** Automate evaluation against test cases

- [ ] **Install and configure DeepEval**
  ```bash
  pip install deepeval
  ```

- [ ] **Create eval metrics**
  - [ ] Sentiment analyzer (for Agent 1)
  - [ ] JSON validator (for Agent 2)
  - [ ] Accuracy calculator (for Agent 2)
  - [ ] Faithfulness checker (for Agent 3)

- [ ] **Create baseline test**
  - [ ] Test base Qwen2.5-3B (no fine-tuning) against test cases
  - [ ] Record baseline scores
  - [ ] Goal: Fine-tuning should beat baseline

**Deliverable:** `evaluation/deepeval_pipeline.py` + baseline scores

---

### Task 1.3: Build RAG Database Schema

**Purpose:** Define how grammar content is structured

- [ ] **Create markdown schema for lessons**
  ```markdown
  ---
  lesson_number: 3
  grammar_points: [noun_adjective_agreement, gender_agreement]
  prerequisites: [1, 2]
  difficulty: intermediate
  vocabulary: [كبير, صغير, جميل]
  ---
  
  # Lesson 3: Noun-Adjective Agreement
  
  ## Grammar Rule
  ...
  
  ## Examples - Correct
  ...
  
  ## Examples - Incorrect
  ...
  
  ## Detection Pattern
  ...
  ```

- [ ] **Create exercise template schema**
  ```markdown
  ---
  type: fill_in_blank
  grammar_point: gender_agreement
  difficulty: beginner
  ---
  
  # Fill-in-Blank: Gender Agreement
  
  ## Template Structure
  Complete: {noun} ___
  
  ## Answer Key Pattern
  Use adjective matching {noun} gender
  ```

- [ ] **Write Lessons 1-3 content** (test with small set first)
  - [ ] Lesson 1: Gender & Definite Article
  - [ ] Lesson 2: Subject Pronouns & Nominal Sentences
  - [ ] Lesson 3: Noun-Adjective Agreement

**Deliverable:** `data/rag_database/lessons/` + schema documentation

---

### Task 1.4: Set Up Pinecone + Embeddings

**Purpose:** RAG infrastructure ready for content

- [ ] **Create Pinecone account** (free tier)

- [ ] **Set up index**
  ```python
  # 384 dimensions for all-MiniLM-L6-v2
  pinecone.create_index(name="arabic-teaching", dimension=384)
  ```

- [ ] **Install sentence-transformers**
  ```bash
  pip install sentence-transformers
  ```

- [ ] **Create ingestion script**
  - [ ] Load lesson markdown files
  - [ ] Generate embeddings with `all-MiniLM-L6-v2`
  - [ ] Upload to Pinecone with metadata

- [ ] **Test retrieval**
  - [ ] Query: "gender agreement"
  - [ ] Should return Lesson 3 content
  - [ ] Verify metadata filtering works

**Deliverable:** `rag/pinecone_setup.py` + `rag/ingest_lessons.py`

**Test:**
```python
def test_rag_retrieval():
    results = retriever.query("gender agreement", lesson=3)
    assert len(results) > 0
    assert "Adjectives must match noun gender" in results[0].content
```

---

## Phase 2: Core Components (Build & Measure)

**Timeline:** 2-3 days  
**Goal:** Build agents that beat baseline on evals

### Task 2.1: Create Training Data

**Purpose:** Fine-tuning dataset for one model, three modes

- [ ] **Teaching Mode Data** (~40 conversations)
  - [ ] 10 conversations: Vocabulary batch introductions
    - [ ] Format: Arabic + transliteration + English
    - [ ] Different batch sizes (1-3 words)
  - [ ] 10 conversations: Vocabulary quiz feedback
    - [ ] 5 correct answers
    - [ ] 5 incorrect answers
  - [ ] 15 conversations: Grammar topic explanations
    - [ ] Different grammar types (nouns, verbs, agreement)
    - [ ] Structured: rule + examples + comprehension question
  - [ ] 5 conversations: Grammar quiz feedback
    - [ ] Per-question feedback with running score
    - [ ] Review suggestions for low scores
  - [ ] Use `{{PLACEHOLDERS}}` for dynamic content
  
- [ ] **Grading Mode Data** (~40 conversations)
  - [ ] 15 conversations: Vocabulary grading
    - [ ] 8 correct translations
    - [ ] 7 incorrect translations
    - [ ] Simple JSON: `{"correct": true/false}`
  - [ ] 25 conversations: Grammar grading
    - [ ] 10 correct answers
    - [ ] 10 incorrect answers (various error types)
    - [ ] 5 multiple errors in one answer
    - [ ] Complex JSON with error details
  - [ ] Output strict JSON format (no encouragement)
  
- [ ] **Exercise Generation Mode Data** (~30 conversations)
  - [ ] 15 conversations: Fill-in-blank generation
  - [ ] 10 conversations: Translation exercises
  - [ ] 5 conversations: Correction exercises
  - [ ] Follow template faithfully

**Deliverable:** `data/training/combined_training_data.jsonl` (110 conversations)

**Validation:**
```python
def test_training_data_format():
    data = load_jsonl("combined_training_data.jsonl")
    assert len(data) >= 110
    
    # Check mode distribution
    teaching = [d for d in data if "Mode: Teaching" in d["messages"][0]["content"] 
                or "Mode: vocab_" in d["messages"][0]["content"]
                or "Mode: grammar_" in d["messages"][0]["content"]]
    assert len(teaching) >= 35  # ~40 target
    
    # Check vocabulary vs grammar split in teaching
    vocab_teaching = [d for d in teaching if "vocab_" in d["messages"][0]["content"]]
    grammar_teaching = [d for d in teaching if "grammar_" in d["messages"][0]["content"]]
    assert len(vocab_teaching) >= 18  # ~20 target (batch intro + quiz feedback)
    assert len(grammar_teaching) >= 17  # ~20 target (explanation + quiz feedback)
    
    grading = [d for d in data if "Mode: Grading" in d["messages"][0]["content"]]
    assert len(grading) >= 35  # ~40 target
```

---

### Task 2.2: Fine-Tune Qwen2.5-3B

**Purpose:** Single model that handles all three modes

- [ ] **Set up SageMaker training** (or local with Unsloth)
  - [ ] Model: `Qwen/Qwen2.5-3B-Instruct`
  - [ ] LoRA config: rank=32, alpha=32
  - [ ] Epochs: 10 (based on 7B testing)
  - [ ] Batch size: 2, grad_accum: 4

- [ ] **Run training** (~20-30 min)

- [ ] **Save model**
  - [ ] Export to `models/qwen-3b-arabic-teaching/`
  - [ ] Save in 4-bit quantized format

**Deliverable:** Fine-tuned model file

**Test:**
```python
def test_model_loads():
    model = load_finetuned_model("models/qwen-3b-arabic-teaching")
    assert model is not None
    
    # Quick sanity check
    response = model.generate("Mode: Teaching\nTeach me a rule")
    assert len(response) > 0
```

---

### Task 2.3: Build Agent 2 (Error Detection)

**Purpose:** Grading agent - simplest, most critical

- [ ] **Create agent class**
  ```python
  class ErrorDetectionAgent:
      def __init__(self, model, prompt_template):
          ...
      
      def grade_answers(self, answers_json, grammar_rules):
          # Returns JSON with errors
          ...
  ```

- [ ] **Create LangChain prompt template**

- [ ] **Pre-load grammar rules** (from Agent 3)

**Test (TDD - write BEFORE implementing):**
```python
def test_agent2_correct_answer():
    agent = ErrorDetectionAgent(model, template)
    
    input_json = {
        "answers": [{
            "answer_id": "q1",
            "student_answer": "كتاب كبير",
            "grammar_points": ["gender_agreement"]
        }]
    }
    
    result = agent.grade_answers(input_json, grammar_rules)
    
    assert result["results"][0]["correct"] == True
    assert len(result["results"][0]["errors"]) == 0

def test_agent2_gender_error():
    agent = ErrorDetectionAgent(model, template)
    
    input_json = {
        "answers": [{
            "answer_id": "q1",
            "student_answer": "كتاب كبيرة",
            "grammar_points": ["gender_agreement"]
        }]
    }
    
    result = agent.grade_answers(input_json, grammar_rules)
    
    assert result["results"][0]["correct"] == False
    assert len(result["results"][0]["errors"]) == 1
    assert result["results"][0]["errors"][0]["error_type"] == "gender_mismatch"
```

- [ ] **Run against eval dataset**
  - [ ] Target: >90% accuracy on correct/incorrect classification
  - [ ] Target: >80% accuracy on error type identification

**Deliverable:** `agents/error_detection_agent.py` + passing tests

---

### Task 2.4: Build Agent 3 (Content Retrieval + Generation)

**Purpose:** Fetch from RAG and generate exercises

- [ ] **Create agent class**
  ```python
  class ContentRetrievalAgent:
      def __init__(self, rag_retriever, generation_model):
          ...
      
      def get_lesson_content(self, lesson_number, vocab_list):
          # Retrieves from Pinecone, formats for Agent 1
          ...
      
      def get_grammar_rules(self, lesson_number):
          # Pre-loads for Agent 2
          ...
      
      def generate_exercises(self, template, vocab, count=5):
          # Generates exercise set
          ...
  ```

**Test (TDD):**
```python
def test_agent3_retrieves_lesson():
    agent = ContentRetrievalAgent(rag, model)
    
    content = agent.get_lesson_content(lesson_number=3, vocab_list=["كبير"])
    
    assert content["lesson_number"] == 3
    assert "gender" in content["grammar_rule"].lower()
    assert len(content["examples"]) > 0

def test_agent3_generates_valid_exercises():
    agent = ContentRetrievalAgent(rag, model)
    
    exercises = agent.generate_exercises(
        template="fill_in_blank",
        vocab=["كبير", "صغير"],
        count=3
    )
    
    assert len(exercises) == 3
    assert all("question" in ex for ex in exercises)
    assert all("answer" in ex for ex in exercises)
    # Check vocabulary is used
    assert any("كبير" in ex["question"] or "كبير" in ex["answer"] for ex in exercises)
```

- [ ] **Run against eval dataset**
  - [ ] Target: >90% relevance on retrievals
  - [ ] Target: 100% valid exercise format

**Deliverable:** `agents/content_retrieval_agent.py` + passing tests

---

### Task 2.5: Build Agent 1 (Teaching Presentation)

**Purpose:** Format content in pedagogical style

- [ ] **Create agent class**
  ```python
  class TeachingAgent:
      def __init__(self, model, prompt_template):
          ...
      
      def present_lesson(self, content_dict):
          # Takes variables from Agent 3, adds pedagogy
          ...
      
      def format_feedback(self, grading_result):
          # Takes JSON from Agent 2, makes encouraging
          ...
  ```

**Test (TDD):**
```python
def test_agent1_vocab_batch_introduction():
    agent = TeachingAgent(model, template)
    
    content = {
        "lesson_number": 3,
        "batch_number": 1,
        "words": [
            {"arabic": "كِتَاب", "transliteration": "kitaab", "english": "book"},
            {"arabic": "مَدْرَسَة", "transliteration": "madrasa", "english": "school"}
        ]
    }
    
    result = agent.present_vocab_batch(content)
    
    # Check encouraging tone
    sentiment = analyze_sentiment(result)
    assert sentiment > 0.8
    
    # Check all words included
    assert "كِتَاب" in result
    assert "kitaab" in result
    assert "book" in result

def test_agent1_grammar_explanation():
    agent = TeachingAgent(model, template)
    
    content = {
        "lesson_number": 3,
        "topic_name": "Feminine Nouns",
        "grammar_rule": "Feminine nouns usually end in ة",
        "examples": ["مَدْرَسَة ✓"]
    }
    
    result = agent.present_grammar_topic(content)
    
    # Check encouraging tone
    sentiment = analyze_sentiment(result)
    assert sentiment > 0.8
    
    # Check structure
    assert "rule" in result.lower() or "feminine" in result.lower()
    assert "?" in result  # Should ask comprehension question

def test_agent1_vocab_quiz_feedback():
    agent = TeachingAgent(model, template)
    
    grading = {
        "correct": False,
        "expected": "book",
        "student_answer": "school"
    }
    
    result = agent.format_vocab_feedback(grading)
    
    # Should be encouraging despite error
    assert not any(word in result.lower() for word in ["wrong", "bad", "fail"])
    assert "book" in result.lower()  # Shows correct answer

def test_agent1_grammar_quiz_feedback():
    agent = TeachingAgent(model, template)
    
    grading = {
        "correct": False,
        "question_number": 2,
        "total_questions": 5,
        "errors": [{
            "error_type": "gender_mismatch",
            "details": "كتاب is masculine but كبيرة is feminine"
        }]
    }
    
    result = agent.format_grammar_feedback(grading)
    
    # Should be encouraging despite error
    assert not any(word in result.lower() for word in ["wrong", "bad", "fail"])
    assert any(word in result.lower() for word in ["not quite", "almost", "try"])
    # Should show running score
    assert "2" in result or "5" in result
```

- [ ] **Run against eval dataset**
  - [ ] Target: >0.9 sentiment score
  - [ ] Target: 100% include comprehension question

**Deliverable:** `agents/teaching_agent.py` + passing tests

---

## Phase 3: Integration (Orchestrate)

**Timeline:** 1-2 days  
**Goal:** Agents work together seamlessly

### Task 3.1: Build Simple Orchestrator

**Purpose:** Route between agents without full LangGraph yet

- [ ] **Create orchestrator class**
  ```python
  class SimpleOrchestrator:
      def __init__(self, agent1, agent2, agent3):
          ...
      
      def handle_teaching_request(self, lesson_number, vocab_list):
          # Agent 3 → Agent 1
          ...
      
      def handle_quiz_request(self, student_answer, lesson):
          # Agent 3 → Agent 2 → Agent 1
          ...
  ```

**Test (TDD):**
```python
def test_orchestrator_vocab_batch_flow():
    orch = SimpleOrchestrator(agent1, agent2, agent3)
    
    # Initialize lesson (Agent 3 caches all content)
    orch.initialize_lesson(lesson_number=3)
    
    # Get batch 1 introduction
    response = orch.handle_vocab_batch_request(batch_number=1)
    
    # Should be encouraging vocabulary presentation
    assert len(response) > 50
    assert "كِتَاب" in response or "kitaab" in response

def test_orchestrator_vocab_quiz_flow():
    orch = SimpleOrchestrator(agent1, agent2, agent3)
    
    # Quiz single word
    response = orch.handle_vocab_quiz(
        word="كِتَاب",
        student_answer="book"
    )
    
    # Should grade and present encouragingly
    assert "correct" in response.lower() or "✓" in response

def test_orchestrator_grammar_teaching_flow():
    orch = SimpleOrchestrator(agent1, agent2, agent3)
    
    response = orch.handle_grammar_topic_request(
        lesson_number=3,
        topic="feminine_nouns"
    )
    
    # Should be encouraging teaching content
    assert len(response) > 100
    assert "?" in response  # Has comprehension question

def test_orchestrator_grammar_quiz_flow():
    orch = SimpleOrchestrator(agent1, agent2, agent3)
    
    response = orch.handle_grammar_quiz_answer(
        lesson=3,
        topic="feminine_nouns",
        student_answer="كتاب كبيرة",
        question_number=2
    )
    
    # Should identify error (Agent 2) and present encouragingly (Agent 1)
    assert "gender" in response.lower() or "match" in response.lower()
    # Should be encouraging
    sentiment = analyze_sentiment(response)
    assert sentiment > 0.7
    # Should show progress
    assert "2" in response or "5" in response
```

**Deliverable:** `orchestration/simple_orchestrator.py` + passing tests

---

### Task 3.2: Test End-to-End Flows

**Purpose:** Full lesson/quiz flows work correctly

- [ ] **Vocabulary Flow Test**
  ```python
  def test_full_vocab_flow():
      # User starts lesson 3
      orchestrator.initialize_lesson(3)
      
      # User gets batch 1 introduction
      intro = orchestrator.get_vocab_batch(1)
      assert len(intro) > 50
      assert "كِتَاب" in intro
      
      # User takes batch quiz (3 words)
      feedback1 = orchestrator.quiz_vocab_word("كِتَاب", "book")
      assert "correct" in feedback1.lower()
      
      feedback2 = orchestrator.quiz_vocab_word("مَدْرَسَة", "house")
      assert "not quite" in feedback2.lower()
      assert "school" in feedback2.lower()
      
      # User completes all batches and takes final test
      final = orchestrator.start_vocab_final_test()
      assert "10" in final  # Shows total words
  ```

- [ ] **Grammar Flow Test**
  ```python
  def test_full_grammar_flow():
      # User starts grammar section
      topics = orchestrator.get_grammar_topics(lesson=3)
      assert len(topics) >= 1
      
      # User learns topic 1
      explanation = orchestrator.teach_grammar_topic("feminine_nouns")
      assert "ة" in explanation
      assert "?" in explanation
      
      # User takes 5-question quiz
      for i in range(5):
          question = orchestrator.get_grammar_quiz_question(i+1)
          # User answers (mix of correct/incorrect)
          feedback = orchestrator.grade_grammar_answer(
              question_id=i+1,
              answer="test_answer"
          )
          assert len(feedback) > 20
      
      # Check final score and review suggestion
      summary = orchestrator.get_quiz_summary()
      if "3/5" in summary or "2/5" in summary:
          assert "review" in summary.lower()
  ```

- [ ] **Run full eval suite**
  - [ ] All Agent 1 tests pass
  - [ ] All Agent 2 tests pass
  - [ ] All Agent 3 tests pass
  - [ ] Integration tests pass

**Deliverable:** Passing integration tests

---

### Task 3.3: Add LangGraph Orchestration

**Purpose:** State management, complex routing, conversation history

- [ ] **Define state schema**
  ```python
  class ConversationState(TypedDict):
      lesson_number: int
      
      # Vocabulary state
      vocab_mode: str  # "batch_intro" | "batch_quiz" | "final_test" | "complete"
      vocab_batches_completed: List[int]
      current_vocab_batch: int
      vocab_batch_scores: Dict[int, str]
      vocab_words_missed: List[str]
      
      # Grammar state
      grammar_mode: str  # "explanation" | "quiz" | "review" | "complete"
      grammar_topics_completed: List[str]
      current_grammar_topic: str
      topic_quiz_scores: Dict[str, str]
      grammar_topics_needing_review: List[str]
      
      # Agent 3 cache (loaded once)
      cached_vocab_words: List[Dict]
      cached_grammar_content: Dict[str, Dict]
      
      # Agent 2 pre-load
      preloaded_grammar_rules: Dict
      
      conversation_history: List[dict]
  ```

- [ ] **Build LangGraph state machine**
  - [ ] Node: Lesson initialization (Agent 3 caches all content)
  - [ ] Node: Intent detection (vocab vs grammar, teaching vs quiz)
  - [ ] Node: Vocabulary batch serving (Agent 3 → Agent 1)
  - [ ] Node: Vocabulary grading (Agent 2 → Agent 1)
  - [ ] Node: Grammar topic serving (Agent 3 → Agent 1)
  - [ ] Node: Grammar grading (Agent 2 → Agent 1)
  - [ ] Edges: Routing logic
    - [ ] Route to vocab or grammar based on lesson progress
    - [ ] Route to teaching or quiz based on user action
    - [ ] Route to review if quiz score < 4/5

- [ ] **Test state persistence**
  ```python
  def test_langgraph_vocab_state():
      graph = build_graph()
      
      # Lesson starts - Agent 3 caches all content
      state1 = graph.invoke({"action": "start_lesson", "lesson": 3})
      assert "cached_vocab_words" in state1
      assert len(state1["cached_vocab_words"]) == 10
      assert state1["vocab_mode"] == "batch_intro"
      
      # Get batch 1
      state2 = graph.invoke({
          "action": "vocab_batch",
          "batch_number": 1,
          "previous_state": state1
      })
      assert state2["current_vocab_batch"] == 1
      
      # Complete batch quiz
      state3 = graph.invoke({
          "action": "vocab_quiz_complete",
          "score": "2/3",
          "previous_state": state2
      })
      assert 1 in state3["vocab_batches_completed"]
      assert state3["vocab_batch_scores"][1] == "2/3"
  
  def test_langgraph_grammar_state():
      graph = build_graph()
      
      # Start grammar (after vocab complete)
      state1 = graph.invoke({
          "action": "start_grammar",
          "lesson": 3
      })
      assert "cached_grammar_content" in state1
      assert "preloaded_grammar_rules" in state1
      assert state1["grammar_mode"] == "explanation"
      
      # Complete topic quiz with low score
      state2 = graph.invoke({
          "action": "grammar_quiz_complete",
          "topic": "feminine_nouns",
          "score": "3/5",
          "previous_state": state1
      })
      assert "feminine_nouns" in state2["grammar_topics_needing_review"]
      assert state2["topic_quiz_scores"]["feminine_nouns"] == "3/5"
  ```

**Deliverable:** `orchestration/langgraph_orchestrator.py` + passing tests

---

## Phase 4: Scale Testing (Validate Architecture)

**Timeline:** 1 day  
**Goal:** Prove scalability without retraining

### Task 4.1: Add New Lessons

**Purpose:** Test "no retrain needed" claim

- [ ] **Write Lessons 4-5 content**
  - [ ] Lesson 4: Present Tense Verbs
  - [ ] Lesson 5: Past Tense Verbs

- [ ] **Ingest to Pinecone** (no code changes)

- [ ] **Test retrieval** (should work immediately)
  ```python
  def test_new_lesson_retrieval():
      # No model retraining done
      content = agent3.get_lesson_content(lesson_number=4, vocab=[])
      assert "verb" in content["grammar_rule"].lower()
      assert "present" in content["grammar_rule"].lower()
  ```

- [ ] **Run full system with new lessons**
  - [ ] Teaching flow for Lesson 4
  - [ ] Quiz flow for Lesson 4
  - [ ] Should work without any model changes

**Deliverable:** Working Lessons 4-5 (no retrain performed)

---

### Task 4.2: Run Full Eval Suite

**Purpose:** Confirm all metrics still pass at scale

- [ ] **Run DeepEval on all test cases**
  - [ ] Teaching mode: Sentiment >0.9
  - [ ] Grading mode: Accuracy >90%
  - [ ] Exercise generation: Faithfulness >90%

- [ ] **Performance testing**
  - [ ] Retrieval latency <500ms
  - [ ] End-to-end response time <3s

- [ ] **Scalability validation**
  - [ ] Add 10 more lessons
  - [ ] Performance doesn't degrade
  - [ ] Accuracy maintained

**Deliverable:** Passing eval report

---

## Final Deliverables

### For School
- [ ] **Codebase** (`final_project_multi_v2/`)
- [ ] **Documentation**
  - [ ] ARCHITECTURE.md
  - [ ] IMPLEMENTATION_PLAN.md (this doc)
  - [ ] INTERACTION_FLOWS.md
- [ ] **Demo video** (5-10 min showing teaching, quiz, scalability)
- [ ] **Eval results** (DeepEval report showing metrics)

### For Work Portfolio
- [ ] **GitHub repo** (clean, well-documented)
- [ ] **README.md** (problem, solution, architecture, results)
- [ ] **Blog post / case study** (design decisions, lessons learned)
- [ ] **Live demo** (optional - Streamlit app)

---

## Success Criteria

**School:**
- ✅ Fine-tuning works (model performs better than baseline)
- ✅ RAG enables scalability (add lessons without retrain)
- ✅ Multi-agent orchestration (agents work together)
- ✅ Evaluation demonstrates quality (>90% accuracy)

**Work:**
- ✅ Production-ready code (tests, documentation, clean architecture)
- ✅ Follows 2026 best practices (eval-driven, RAG, orchestration)
- ✅ Demonstrates scalability (empirically validated)
- ✅ Shows engineering maturity (TDD, metrics, trade-offs documented)

---

**Timeline:** ~5-7 days total (assuming part-time work)

**Next Step:** Start with Phase 1, Task 1.1 (Create Evaluation Dataset)
