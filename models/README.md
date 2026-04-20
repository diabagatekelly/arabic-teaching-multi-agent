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
**Purpose:** Agent 2 (Grading Agent) - DEPRECATED

**Status:** This model was developed but not deployed. Production system uses the same `qwen-7b-arabic-teaching` model for both teaching and grading, with role differentiation via prompts and inference configs.

**Original Intent:** Separate fine-tuned Qwen2.5-7B model for validating student answers:
- Vocabulary answer grading (handles typos, synonyms)
- Grammar answer grading (validates rules and case endings)
- JSON-only output enforcement
- Hybrid validation (rule-based + semantic AI grading)

**Training:** 346 grading examples  
**Performance:** 97.5% accuracy (39/40 test cases)

**Why Not Deployed:** Single-model architecture simplified deployment and reduced GPU memory requirements for ZeroGPU. The teaching model proved capable of grading when prompted correctly with low temperature (0.1).

See `docs/evaluation/grading_agent/FINAL_EVALUATION.md` for detailed evaluation results.

---

## Note

These directories are excluded from version control (see `.gitignore`) due to large file sizes (~40MB per model).
