# Prompt Inventory

**Total:** 19 prompts implemented across 2 agents (+ 3 for content generation)

**Implementation:** All prompts defined in `src/prompts/templates.py` using LangChain PromptTemplate

## Agent 1: Teaching Agent (13 prompts)

**Model:** Qwen2.5-7B-Instruct + LoRA (kdiabagate/qwen-7b-arabic-teaching)

### Lesson Management (2)
1. ✅ **LESSON_WELCOME** - Introduce lesson with vocab/grammar overview
2. ✅ **PROGRESS_REPORT** - Show lesson progress and next options

### Vocabulary (6)
3. ✅ **VOCAB_BATCH_INTRO** - Present 3-word batch with flashcards
4. ✅ **VOCAB_QUIZ_QUESTION** - Ask "What does X mean?"
5. ✅ **VOCAB_BATCH_SUMMARY** - Summarize batch quiz performance
6. ✅ **FEEDBACK_VOCAB_CORRECT** - Provide correct answer feedback
7. ✅ **FEEDBACK_VOCAB_INCORRECT** - Provide incorrect answer feedback with correction

### Grammar (5)
8. ✅ **GRAMMAR_OVERVIEW** - Introduce grammar section with topics list
9. ✅ **GRAMMAR_EXPLANATION** - Teach grammar rule with examples
10. ✅ **GRAMMAR_QUIZ_QUESTION** - Ask grammar question (translation or fill-in-blank)
11. ✅ **GRAMMAR_TOPIC_SUMMARY** - Summarize grammar quiz results
12. ✅ **FEEDBACK_GRAMMAR_CORRECT** - Provide correct grammar feedback
13. ✅ **FEEDBACK_GRAMMAR_INCORRECT** - Provide incorrect grammar feedback with explanation

**Inference Config:**
- temperature=0.7 (moderate creativity)
- top_p=0.92, top_k=60 (rich vocabulary)
- max_new_tokens=256 (full explanations)

## Agent 2: Grading Agent (3 prompts)

**Model:** Same Qwen2.5-7B + LoRA as Agent 1 (differentiated by prompt + config)

14. ✅ **GRADING_VOCAB** - Grade vocabulary translation (JSON output: `{"correct": true/false}`)
15. ✅ **GRADING_GRAMMAR_QUIZ** - Grade grammar quiz answer (JSON output)
16. ✅ **GRADING_GRAMMAR_TEST** - Grade multiple final exam questions (batch JSON)

**Edge Cases Handled:**
- Synonyms: "instructor" = "teacher" ✓
- Typos: "scool" = "school" ✓
- Case: "BOOK" = "book" ✓
- Articles: "the book" = "book" ✓
- Arabic harakaat: internal diacritics optional, case endings required

**Inference Config:**
- temperature=0.1 (deterministic JSON)
- top_p=0.95, top_k=40 (focused)
- max_new_tokens=50 (short JSON only)

## Content Generation (3 prompts - NOT USED IN PRODUCTION)

**Status:** Implemented but deprecated in favor of lesson_cache.json

17. ✅ **EXERCISE_GENERATION** - Generate practice exercises from templates
18. ✅ **QUIZ_QUESTION_GENERATION** - Generate quiz questions
19. ✅ **TEST_COMPOSITION** - Generate mixed grammar tests

**Note:** Content now pre-built via `scripts/build_lesson_cache.py` instead of runtime generation

---

## Implementation Status

- ✅ **19/19 prompts implemented** (100% coverage)
- ✅ All prompts in production use (16 teaching/grading, 3 content deprecated)
- ✅ Comprehensive mode declarations for task type identification
- ✅ Consistent format with examples and instructions

## Prompt Usage Patterns

**Teaching Flow:**
```
LESSON_WELCOME → VOCAB_BATCH_INTRO → VOCAB_QUIZ_QUESTION
→ [GRADING_VOCAB] → FEEDBACK_VOCAB_CORRECT/INCORRECT
→ VOCAB_BATCH_SUMMARY → GRAMMAR_OVERVIEW → GRAMMAR_EXPLANATION
→ GRAMMAR_QUIZ_QUESTION → [GRADING_GRAMMAR_QUIZ]
→ FEEDBACK_GRAMMAR_CORRECT/INCORRECT → PROGRESS_REPORT
```

**Orchestrator Routes:**
- User input → Orchestrator determines stage → Selects prompt
- Teaching prompts: `.format()` with session variables
- Grading prompts: `.format()` with answer data → parse JSON response
- Chat template applied to all prompts before inference

---

**Last Updated:** 2026-04-20  
**See:** `PROMPT_DESIGN.md` for template design principles, `INFERENCE.md` for generation configs
