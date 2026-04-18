# Training Examples

This directory contains **sample training examples** extracted from the actual training data uploaded to SageMaker.

## Purpose

These files serve as **reference documentation** to show the format and variety of training data, NOT as source files for generating training data.

## Structure

Each `*_sample.json` file contains one representative example of that training type.

### Agent 2 (Grading)
- `grading/vocab_correct_sample.json` - Vocabulary grading (correct answer)
- `grading/vocab_incorrect_sample.json` - Vocabulary grading (incorrect answer)
- `grading/grammar_correct_sample.json` - Grammar grading (correct answer)
- `grading/grammar_incorrect_sample.json` - Grammar grading (incorrect answer)

### Agent 1 (Teaching)
- `teaching/lesson_start_sample.json` - Lesson welcome/introduction
- `teaching/teaching_vocab_sample.json` - Vocabulary batch introduction
- `teaching/teaching_grammar_sample.json` - Grammar topic explanation
- `teaching/feedback_vocab_correct_sample.json` - Vocabulary feedback (correct)
- `teaching/feedback_vocab_incorrect_sample.json` - Vocabulary feedback (incorrect)

## Format

### Agent 1 (Teaching) - V2 Multi-Turn Format
Each teaching example contains 3-8 messages showing complete conversational flow:
- **System message:** Structured with Mode/Lesson/Phase/Objective/Available Content
- **Multi-turn dialogue:** Model leads, handles boundaries, offers navigation
- **RAG content:** Summarized in system message (not user message)

### Agent 2 (Grading) - Structured Format
Each grading example shows correct/incorrect answer validation with explanations.

## Actual Training Data

The **actual training data** used for fine-tuning is in:
- `../agent1_teaching_training_data.jsonl` (153 multi-turn conversations)
- `../agent2_grading_training_data.jsonl` (346 examples)

These JSONL files were uploaded to SageMaker for model training.

## Last Updated

2026-04-18 - Updated to V2 multi-turn format for teaching agent
