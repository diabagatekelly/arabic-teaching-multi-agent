# Fine-Tuned Models

This directory contains LoRA adapters for the fine-tuned agents.

## Models

### `qwen-7b-arabic-teaching/`
**Purpose:** Agent 1 (Teaching Agent)

Fine-tuned Qwen2.5-7B model for Arabic language teaching tasks:
- Lesson introductions and welcomes
- Vocabulary batch presentation (3-4 words at a time)
- Grammar topic explanations
- Feedback on student answers (correct/incorrect)
- Navigation guidance and boundary setting

**Training:** 153 multi-turn conversation examples (V2 format)  
**Performance:** 57.1% on targeted evaluations, 100% on lesson start and grammar teaching

See `docs/evaluation/teaching_agent/FINAL_EVALUATION.md` for detailed evaluation results.

---

### `qwen-7b-arabic-grading/`
**Purpose:** Agent 2 (Grading Agent)

Fine-tuned Qwen2.5-7B model for validating student answers:
- Vocabulary answer grading (handles typos, synonyms)
- Grammar answer grading (validates rules and case endings)
- Explanation generation for incorrect answers
- Hybrid validation (rule-based + semantic AI grading)

**Training:** 346 grading examples  
**Performance:** 97.5% accuracy (39/40 test cases)

See `docs/evaluation/grading_agent/FINAL_EVALUATION.md` for detailed evaluation results.

---

## Note

These directories are excluded from version control (see `.gitignore`) due to large file sizes (~40MB per model).
