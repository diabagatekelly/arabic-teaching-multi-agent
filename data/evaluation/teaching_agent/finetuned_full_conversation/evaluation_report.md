# Agent 1 (Teaching) - End-to-End Conversation Evaluation

**Model:** Qwen2.5-7B Teaching (LoRA) from /Users/kellydiabagate/Documents/LLMCourse/arabic-teaching-multi-agent/models/qwen-7b-arabic-teaching
**Evaluation Date:** 2026-04-16

---

## Overall Results

- **Total Scenarios:** 12
- **Passed:** 0
- **Failed:** 12
- **Pass Rate:** 0.0%

---

## By Category

### ❌ Edge Case

- **Scenarios:** 4
- **Passed:** 0/4 (0.0%)
- **Tests:** e2e_off_topic_redirect, e2e_profanity_boundary, e2e_unstudied_content_question, e2e_boredom_distraction

### ❌ Error Recovery

- **Scenarios:** 2
- **Passed:** 0/2 (0.0%)
- **Tests:** e2e_error_recovery_flow, e2e_multiple_mistakes_encouragement

### ❌ Happy Path

- **Scenarios:** 2
- **Passed:** 0/2 (0.0%)
- **Tests:** e2e_vocab_learning_happy_path, e2e_grammar_learning_flow

### ❌ Navigation

- **Scenarios:** 4
- **Passed:** 0/4 (0.0%)
- **Tests:** e2e_navigation_back_forth, e2e_see_all_words_then_continue, e2e_lesson_progress_check, e2e_switch_modes_mid_lesson

---

## Detailed Results

### ❌ e2e_vocab_learning_happy_path

**Description:** Complete vocab learning flow: lesson start → batch intro → quiz with mixed results

**Category:** happy_path

**Pass Rate:** 75.0% (3/4 turns)

**Issues:**
- Turn 2: Missing mentions_flashcards
- Turn 4: Metric sentiment failed

### ❌ e2e_grammar_learning_flow

**Description:** Grammar learning: lesson start → grammar topic explanation → quiz with results

**Category:** happy_path

**Pass Rate:** 75.0% (3/4 turns)

**Issues:**
- Turn 4: Missing mentions_score
- Turn 4: Metric sentiment failed

### ❌ e2e_off_topic_redirect

**Description:** Edge case: student goes off-topic during vocab batch, model redirects and offers break

**Category:** edge_case

**Pass Rate:** 50.0% (1/2 turns)

**Issues:**
- Turn 2: Missing mentions_save_and_break_option

### ❌ e2e_profanity_boundary

**Description:** Edge case: student uses profanity, model sets professional boundary

**Category:** edge_case

**Pass Rate:** 50.0% (1/2 turns)

**Issues:**
- Turn 2: Missing offers_break_option
- Turn 2: Missing redirects_to_lesson_options

### ❌ e2e_unstudied_content_question

**Description:** Edge case: student asks about word not in current lesson

**Category:** edge_case

**Pass Rate:** 0.0% (0/2 turns)

**Issues:**
- Turn 1: Missing presents_lesson
- Turn 2: Missing answers_briefly_if_possible
- Turn 2: Missing redirects_to_lesson_1_content

### ❌ e2e_boredom_distraction

**Description:** Edge case: student expresses boredom, model offers break with encouragement

**Category:** edge_case

**Pass Rate:** 50.0% (1/2 turns)

**Issues:**
- Turn 2: Missing acknowledges_feeling
- Turn 2: Missing mentions_save_and_break

### ❌ e2e_error_recovery_flow

**Description:** Error recovery: incorrect answer → flashcard practice → retry → success

**Category:** error_recovery

**Pass Rate:** 50.0% (1/2 turns)

**Issues:**
- Turn 2: Missing acknowledges_improvement
- Turn 2: Metric sentiment failed

### ❌ e2e_multiple_mistakes_encouragement

**Description:** Multiple mistakes: model maintains encouragement and support

**Category:** error_recovery

**Pass Rate:** 100.0% (3/3 turns)

**Issues:**
- Turn 2: Metric sentiment failed
- Turn 3: Metric sentiment failed

### ❌ e2e_navigation_back_forth

**Description:** Navigation: batch 2 → back to batch 1 → quiz

**Category:** navigation

**Pass Rate:** 50.0% (1/2 turns)

**Issues:**
- Turn 1: Missing shows_batch_2
- Turn 1: Missing offers_choices

### ❌ e2e_see_all_words_then_continue

**Description:** Navigation: batch 1 → see all words → back to current batch

**Category:** navigation

**Pass Rate:** 50.0% (1/2 turns)

**Issues:**
- Turn 2: Missing indicates_current_position

### ❌ e2e_lesson_progress_check

**Description:** Navigation: lesson start → option 3 (progress) → see status → continue

**Category:** navigation

**Pass Rate:** 50.0% (1/2 turns)

**Issues:**
- Turn 2: Missing shows_progress_status

### ❌ e2e_switch_modes_mid_lesson

**Description:** Mode switching: vocab batch → student requests grammar instead

**Category:** navigation

**Pass Rate:** 50.0% (1/2 turns)

**Issues:**
- Turn 1: Missing shows_vocab_batch

