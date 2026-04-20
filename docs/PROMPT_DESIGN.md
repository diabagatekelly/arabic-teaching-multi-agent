# Prompt Design Standards

**Purpose:** Template design for all teaching and grading prompts  
**Implementation:** `src/prompts/templates.py` (LangChain PromptTemplate)  
**Updated:** 2026-04-20

## Overview

**19 prompts total:**
- Agent 1 (Teaching): 13 prompts
- Agent 2 (Grading): 3 prompts  
- Content Generation: 3 prompts (deprecated, not used in production)

**All prompts implemented in production** - see `PROMPTS_INVENTORY.md` for complete list.

## Design Principles

### 1. Mode-Based Structure
Every prompt starts with clear mode declaration:
```
Mode: teaching_vocab
Lesson: {lesson_number}
Phase: {current_phase}
...
```

### 2. Variable Formatting
- Use LangChain `PromptTemplate.format()` for structured input
- Variables from lesson cache or session state
- Consistent naming: `lesson_number`, `student_answer`, `correct_answer`

### 3. Chat Template Wrapping
All prompts wrapped with model's chat template before inference:
```python
messages = [{"role": "system", "content": formatted_prompt}]
final_prompt = tokenizer.apply_chat_template(messages, tokenize=False)
```

### 4. Agent-Specific Configurations

**Teaching Agent (temperature=0.7):**
- Encouraging language: "Provide feedback in an encouraging way"
- Arabic with transliteration: `{arabic} ({transliteration})`
- Flexible navigation: "Or tell me what you'd like to do"
- Numbered options for user choices

**Grading Agent (temperature=0.1):**
- JSON-only output: "Output ONLY JSON, no explanations"
- Explicit format: `{"correct": true}` or `{"correct": false}`
- Edge case handling: synonyms, typos, capitalization
- Arabic rules: Internal harakaat optional, case endings required

### 5. Feedback Tone
- **Correct:** "Brief, encouraging" (e.g., "Correct! ✓ Great job!")
- **Incorrect:** "Supportive with correction" (e.g., "Not quite! X means Y, not Z")

## Example Templates

### Teaching: Vocab Batch Intro
```python
VOCAB_BATCH_INTRO = PromptTemplate(
    template="""
Mode: teaching_vocab
Lesson: {lesson_number}
Batch: {batch_number} of {total_batches}

Words to teach:
{words_formatted}

Present encouragingly with flashcard reminder. Offer:
1. Take quiz
2. Next batch
3. See all words
""",
    input_variables=["lesson_number", "batch_number", "total_batches", "words_formatted"]
)
```

### Grading: Vocab Answer
```python
GRADING_VOCAB = PromptTemplate(
    template="""
Mode: grading_vocab

Question: What does "{word}" mean?
Student: "{student_answer}"
Correct: "{correct_answer}"

Evaluate with flexibility (synonyms, typos, case).
Output ONLY JSON: {{"correct": true}} or {{"correct": false}}

Response:
""",
    input_variables=["word", "student_answer", "correct_answer"]
)
```

### Teaching: Grammar Feedback (Correct)
```python
FEEDBACK_GRAMMAR_CORRECT = PromptTemplate(
    template="""
Mode: feedback_grammar

Question: {question}
Student: "{student_answer}"
Correct: "{correct_answer}"
Explanation: {explanation}
Score: {current_score}

Provide brief encouraging feedback.
""",
    input_variables=["question", "student_answer", "correct_answer", "explanation", "current_score"]
)
```

## Prompt Categories

### Lesson Management (2)
- LESSON_WELCOME - Intro with vocab/grammar overview
- PROGRESS_REPORT - Show progress and next options

### Vocabulary Teaching (6)
- VOCAB_BATCH_INTRO - Present 3-word batch
- VOCAB_QUIZ_QUESTION - "What does X mean?"
- VOCAB_BATCH_SUMMARY - Batch performance summary
- FEEDBACK_VOCAB_CORRECT - Correct answer praise
- FEEDBACK_VOCAB_INCORRECT - Incorrect with correction

### Grammar Teaching (5)
- GRAMMAR_OVERVIEW - Topic list intro
- GRAMMAR_EXPLANATION - Rule with examples
- GRAMMAR_QUIZ_QUESTION - Translation or fill-blank
- FEEDBACK_GRAMMAR_CORRECT - Correct with explanation
- FEEDBACK_GRAMMAR_INCORRECT - Incorrect with correction

### Grading (3)
- GRADING_VOCAB - JSON output for vocab answers
- GRADING_GRAMMAR_QUIZ - JSON output for grammar
- GRADING_GRAMMAR_TEST - Batch JSON for multiple questions

### Content Generation (3 - Deprecated)
- EXERCISE_GENERATION - Practice exercise templates
- QUIZ_QUESTION_GENERATION - Quiz question creation
- TEST_COMPOSITION - Mixed grammar tests

**Note:** Content generation prompts exist but not used; lesson_cache.json provides pre-built content.

## Implementation Notes

**Location:** All templates defined in `src/prompts/templates.py`

**Usage Pattern:**
```python
from src.prompts.templates import VOCAB_BATCH_INTRO

# 1. Format with session variables
prompt = VOCAB_BATCH_INTRO.format(
    lesson_number=1,
    batch_number=1,
    total_batches=3,
    words_formatted="..."
)

# 2. Wrap with chat template
messages = [{"role": "system", "content": prompt}]
formatted = tokenizer.apply_chat_template(messages, tokenize=False)

# 3. Generate
output = model.generate(formatted, temperature=0.7, max_new_tokens=256)
```

**Testing:** See `tests/test_prompts.py` for validation

**Evaluation:** DeepEval metrics in `scripts/evaluation/`

---

**See also:**
- `PROMPTS_INVENTORY.md` - Complete prompt list with status
- `INFERENCE.md` - Generation configs and pipeline
- `src/prompts/templates.py` - Actual implementations
