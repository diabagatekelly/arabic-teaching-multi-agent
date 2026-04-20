# Arabic Teaching Multi-Agent System - Architecture v2

**Design Philosophy:** Separate content from style. Fine-tune for teaching behavior, use lesson cache for scalable content.

## Core Problem

**v1 approach:** Fine-tune model on specific grammar rules
- Adding new grammar = retrain entire model
- Doesn't scale past 5-10 grammar points

**v2 approach:** Fine-tune for style, cache content from JSON
- Adding new grammar = update lesson_cache.json
- Scales to 100+ grammar points

## Why Multi-Agent?

Original plan had separate models for conflicting objectives (encouraging tone vs. accurate correction). Current implementation uses shared 7B teaching model for both presentation and grading, with orchestrator managing behavioral differences through prompts.

**Agent 1 (Teaching):** Qwen2.5-7B + LoRA - Pedagogical style, user-facing
**Agent 2 (Grading):** Same Qwen2.5-7B + LoRA - Evaluation with flexible matching
**Agent 3 (Content):** lesson_cache.json - Pre-built content (RAG deprecated)

**Trade-offs:** Single model simplifies deployment; orchestrator handles role-switching via prompts.

---

## Agent 1: Teaching Agent

**Model:** Qwen2.5-7B-Instruct + LoRA (kdiabagate/qwen-7b-arabic-teaching)

**Responsibility:** Present content with encouraging pedagogical style

**Input:** Structured variables (words, rules, scores) from lesson cache/orchestrator

**Output:** User-facing text with supportive tone

**Examples:**
- Batch intro: "Let's learn Batch 1! Here are your first 3 words..."
- Feedback (correct): "Correct! ✓ كِتَاب = book. Great job!"
- Feedback (incorrect): "Not quite! مَدْرَسَة (madrasa) means 'school', not 'house'."

**Training:** 153 multi-turn conversations on teaching patterns (not specific content)

**Deployment:** HuggingFace model hub, loaded with LoRA adapter merged at startup

---

## Agent 2: Grading Agent

**Model:** Same as Agent 1 - Qwen2.5-7B-Instruct + LoRA (kdiabagate/qwen-7b-arabic-teaching)

**Responsibility:** Evaluate answers with flexible matching, return JSON

**Edge Cases:** Accepts synonyms, typos, capitalization; for Arabic: internal harakaat optional, case endings required

**Input/Output:**
```python
{"word": "كِتَاب", "student_answer": "book", "correct_answer": "book"}
→ {"correct": true}
```

**Implementation:** Lazy-loaded on first grading call via orchestrator. Uses same teaching model but with different prompts (GRADING_VOCAB, GRADING_GRAMMAR_QUIZ templates) and lower temperature (0.1) for deterministic JSON output.

**Status:** Active and deployed (uses teaching model, differentiated by inference config)

---

## Agent 3: Content Agent

**Model:** None (deprecated in production)

**Responsibility:** Serve pre-built lesson content from lesson_cache.json

**Flow:**
1. Lesson starts → load ALL vocab + grammar from lesson_cache.json
2. Cache content in orchestrator session state
3. Serve content on-demand to Agents 1 & 2
4. No dynamic exercise generation (uses fixed quizzes from cache)

**Data Structure:** lesson_cache.json with pre-built lessons (vocabulary, grammar sections, difficulty)

**RAG Status:** RAG infrastructure exists (Pinecone, embeddings) but not used in production. Content is pre-built via `scripts/build_lesson_cache.py` instead.

**Trade-off:** Faster, more reliable (no vector DB latency), but less dynamic content generation.

## State Management

**Tracked by Orchestrator:**
- Lesson progress (vocab/grammar modes, scores, quiz state, current batch)
- Session state (lesson_number, lesson_name, vocabulary/grammar sections)
- Lesson content cache (loaded from lesson_cache.json at lesson start)
- File-based persistence (sessions.json for cross-request state in ZeroGPU)

**Session Schema:**
```python
{
    "lesson_number": 1,
    "lesson_name": "Gender and Definite Article",
    "vocabulary": {
        "words": [...],
        "current_batch": 1,
        "quizzed_words": [],
        "quiz_state": {...}
    },
    "grammar": {
        "topics": {...},
        "sections": {...}
    },
    "current_progress": "vocab_batch_intro",
    "status": "active"
}
```

See `orchestrator.py:start_lesson()` for full implementation.

## Training Data

**Agent 1 (Teaching):** 153 multi-turn conversations on teaching patterns (vocab intro, feedback, grammar explanations)
**Agent 2 (Grading):** Uses same teaching model as Agent 1, differentiated by prompts + inference config
**Agent 3 (Content):** No model - uses pre-built lesson_cache.json generated from data/lessons/

## Scalability

Adding new grammar: Update lesson_cache.json via build script (~2 min) vs. retrain model (30+ min)

## Technology Stack

- **Orchestration:** Custom state machine in `orchestrator.py` (LangGraph removed)
- **Models:** Qwen2.5-7B-Instruct + LoRA (single model for both teaching and grading)
- **UI:** Gradio (gr.Blocks) with chat interface and flashcards
- **Deployment:** HuggingFace Spaces with ZeroGPU (@spaces.GPU decorator)
- **Content:** Pre-built lesson_cache.json (RAG deprecated)
- **Evaluation:** DeepEval with LLM-as-a-Judge

## Success Metrics

- Agent 1 (Teaching): 95%+ positive sentiment, natural conversation flow
- Agent 2 (Grading): 90%+ grading accuracy with flexible matching
- Agent 3 (Content): <100ms cache lookup, 100% availability
- System: Add grammar in <10 min without retraining

---

**Status:** Production deployed on HuggingFace Spaces  
**Created:** 2026-04-03  
**Last Updated:** 2026-04-20 (aligned with actual implementation)  
**See also:** `INFERENCE.md`, `DEPLOYMENT.md`, `PROMPTS_INVENTORY.md`

**Note:** This architecture document now reflects the ACTUAL implementation, not the original design plan. Key changes from v2 design:
- Single 7B model instead of separate 3B/7B models
- lesson_cache.json instead of RAG
- Gradio-only interface (no REST API)
- Shared model for teaching and grading (different prompts/configs)
