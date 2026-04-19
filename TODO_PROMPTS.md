# Prompt Templates Alignment with PROMPT_DESIGN.md

## Templates Needing Updates

### ✅ LESSON_WELCOME (lines 32-62)
- Status: **CORRECT** - matches PROMPT_DESIGN spec
- Already shows complete word list, numbered options

### ✅ VOCAB_BATCH_INTRO (lines 87-104)
- Status: **CORRECT** - just updated to match spec
- Shows flashcards reminder, 3 numbered options

### ❌ VOCAB_QUIZ_QUESTION (lines 122-130)
- Current: Generic "Ask the translation question clearly"
- Should: Separate templates for arabic_to_english vs english_to_arabic
- Spec: docs/PROMPT_DESIGN.md lines 393-453
- Fix needed: Create two separate prompt paths based on question_type

### ❌ FEEDBACK_VOCAB_CORRECT (lines 231-246)
- Current: Generic feedback prompt
- Should: Follow spec format with specific instructions
- Spec: docs/PROMPT_DESIGN.md lines 453-503
- Issues:
  - Missing specific output format
  - Should mention continuing or generating next question

### ❌ FEEDBACK_VOCAB_INCORRECT (lines 248-261)
- Current: Generic correction prompt
- Should: Follow spec with flashcard practice direction
- Spec: docs/PROMPT_DESIGN.md lines 503-553
- Issues:
  - Should explicitly mention flashcard practice
  - Should show correct answer format

### ❌ FEEDBACK_GRAMMAR_CORRECT (lines 263-284)
- Current: Has explanation field
- Should: Match spec format exactly
- Spec: docs/PROMPT_DESIGN.md lines 825-880

### ❌ FEEDBACK_GRAMMAR_INCORRECT (lines 286-307)
- Current: Has explanation field  
- Should: Match spec format with rule reference
- Spec: docs/PROMPT_DESIGN.md lines 880-935

### ❌ GRADING_VOCAB (lines 316-335)
- Current: Has detailed comparison logic in prompt
- Should: Match spec exactly
- Spec: docs/PROMPT_DESIGN.md lines 1048-1123
- Issues:
  - Prompt has too much logic explanation
  - Should be simpler, focused on comparison

### ❌ GRADING_GRAMMAR_QUIZ (lines 337-356)
- Current: Complex harakaat rules in prompt
- Should: Match spec format
- Spec: docs/PROMPT_DESIGN.md lines 1138-1214
- Issues:
  - Over-complicated with inline explanations
  - Should separate case ending logic

### ❌ GRADING_GRAMMAR_TEST (lines 358-392)
- Current: Bulk grading with detailed instructions
- Should: Match spec exactly
- Spec: docs/PROMPT_DESIGN.md lines 1214-1317

### ❌ EXERCISE_GENERATION (lines 400-444)
- Current: Has critical requirements section
- Should: Match spec format
- Spec: docs/PROMPT_DESIGN.md lines 1317-1416
- Issues:
  - Too verbose with requirements
  - Should trust model training

### ❌ QUIZ_QUESTION_GENERATION (lines 446-472)
- Current: Grammar quiz generation
- Should: Match spec format
- Spec: docs/PROMPT_DESIGN.md lines 1416-end

## Priority Order

1. **HIGH**: VOCAB_QUIZ_QUESTION - breaks quiz flow
2. **HIGH**: FEEDBACK templates - user sees these constantly  
3. **MEDIUM**: GRADING templates - affects correctness
4. **LOW**: EXERCISE_GENERATION - works but could be cleaner

## Strategy

- Fix HIGH priority first (quiz + feedback)
- Test each change in isolation
- Deploy incrementally to avoid breaking everything at once
