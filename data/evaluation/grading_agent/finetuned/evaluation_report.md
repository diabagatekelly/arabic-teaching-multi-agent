# Agent 2 (Grading) - Fine-Tuned Evaluation

**Model:** Fine-tuned Qwen2.5-7B (LoRA) from /Users/kellydiabagate/Documents/LLMCourse/arabic-teaching-multi-agent/models/qwen-7b-arabic-grading
**Evaluation Date:** 2026-04-16

## Overall Summary

- **Total Test Cases:** 40
- **Passed:** 39
- **Failed:** 1
- **Pass Rate:** 97.5%

## By Mode

### Grading Vocabulary
- **Total Test Cases:** 22
- **Passed:** 21
- **Failed:** 1
- **Pass Rate:** 95.5%

### Grading Grammar
- **Total Test Cases:** 18
- **Passed:** 18
- **Failed:** 0
- **Pass Rate:** 100.0%

## Metrics Breakdown

### Vocabulary Grading
- **Accuracy:** 21/22 (95.5%), avg score: 0.955
- **JSON Validity:** 22/22 (100.0%), avg score: 1.000
- **Structure:** 22/22 (100.0%), avg score: 1.000

### Grammar Grading
- **Accuracy:** 18/18 (100.0%), avg score: 1.000
- **JSON Validity:** 18/18 (100.0%), avg score: 1.000
- **Structure:** 18/18 (100.0%), avg score: 1.000

## Detailed Test Results

### Vocabulary Grading

#### ✓ grade_vocab_article_01

- ✓ **JSON Validity:** 1.00
  - ✓ Valid JSON output
- ✓ **Structure:** 1.00
  - ✓ Valid structure with required keys and types
- ✓ **Accuracy:** 1.00
  - ✓ Correctly classified as correct

#### ✓ grade_vocab_article_02

- ✓ **JSON Validity:** 1.00
  - ✓ Valid JSON output
- ✓ **Structure:** 1.00
  - ✓ Valid structure with required keys and types
- ✓ **Accuracy:** 1.00
  - ✓ Correctly classified as correct

#### ✓ grade_vocab_caps_01

- ✓ **JSON Validity:** 1.00
  - ✓ Valid JSON output
- ✓ **Structure:** 1.00
  - ✓ Valid structure with required keys and types
- ✓ **Accuracy:** 1.00
  - ✓ Correctly classified as correct

#### ✓ grade_vocab_caps_02

- ✓ **JSON Validity:** 1.00
  - ✓ Valid JSON output
- ✓ **Structure:** 1.00
  - ✓ Valid structure with required keys and types
- ✓ **Accuracy:** 1.00
  - ✓ Correctly classified as correct

#### ✓ grade_vocab_exact_01

- ✓ **JSON Validity:** 1.00
  - ✓ Valid JSON output
- ✓ **Structure:** 1.00
  - ✓ Valid structure with required keys and types
- ✓ **Accuracy:** 1.00
  - ✓ Correctly classified as correct

#### ✓ grade_vocab_exact_02

- ✓ **JSON Validity:** 1.00
  - ✓ Valid JSON output
- ✓ **Structure:** 1.00
  - ✓ Valid structure with required keys and types
- ✓ **Accuracy:** 1.00
  - ✓ Correctly classified as correct

#### ✓ grade_vocab_exact_03

- ✓ **JSON Validity:** 1.00
  - ✓ Valid JSON output
- ✓ **Structure:** 1.00
  - ✓ Valid structure with required keys and types
- ✓ **Accuracy:** 1.00
  - ✓ Correctly classified as correct

#### ✓ grade_vocab_exact_04

- ✓ **JSON Validity:** 1.00
  - ✓ Valid JSON output
- ✓ **Structure:** 1.00
  - ✓ Valid structure with required keys and types
- ✓ **Accuracy:** 1.00
  - ✓ Correctly classified as correct

#### ✓ grade_vocab_exact_05

- ✓ **JSON Validity:** 1.00
  - ✓ Valid JSON output
- ✓ **Structure:** 1.00
  - ✓ Valid structure with required keys and types
- ✓ **Accuracy:** 1.00
  - ✓ Correctly classified as correct

#### ✓ grade_vocab_partial_01

- ✓ **JSON Validity:** 1.00
  - ✓ Valid JSON output
- ✓ **Structure:** 1.00
  - ✓ Valid structure with required keys and types
- ✓ **Accuracy:** 1.00
  - ✓ Correctly classified as incorrect

#### ✓ grade_vocab_partial_02

- ✓ **JSON Validity:** 1.00
  - ✓ Valid JSON output
- ✓ **Structure:** 1.00
  - ✓ Valid structure with required keys and types
- ✓ **Accuracy:** 1.00
  - ✓ Correctly classified as incorrect

#### ✓ grade_vocab_synonym_01

- ✓ **JSON Validity:** 1.00
  - ✓ Valid JSON output
- ✓ **Structure:** 1.00
  - ✓ Valid structure with required keys and types
- ✓ **Accuracy:** 1.00
  - ✓ Correctly classified as correct

#### ✓ grade_vocab_synonym_02

- ✓ **JSON Validity:** 1.00
  - ✓ Valid JSON output
- ✓ **Structure:** 1.00
  - ✓ Valid structure with required keys and types
- ✓ **Accuracy:** 1.00
  - ✓ Correctly classified as correct

#### ✓ grade_vocab_synonym_03

- ✓ **JSON Validity:** 1.00
  - ✓ Valid JSON output
- ✓ **Structure:** 1.00
  - ✓ Valid structure with required keys and types
- ✓ **Accuracy:** 1.00
  - ✓ Correctly classified as correct

#### ✓ grade_vocab_typo_01

- ✓ **JSON Validity:** 1.00
  - ✓ Valid JSON output
- ✓ **Structure:** 1.00
  - ✓ Valid structure with required keys and types
- ✓ **Accuracy:** 1.00
  - ✓ Correctly classified as correct

#### ✓ grade_vocab_typo_02

- ✓ **JSON Validity:** 1.00
  - ✓ Valid JSON output
- ✓ **Structure:** 1.00
  - ✓ Valid structure with required keys and types
- ✓ **Accuracy:** 1.00
  - ✓ Correctly classified as correct

#### ✗ grade_vocab_typo_03

- ✓ **JSON Validity:** 1.00
  - ✓ Valid JSON output
- ✓ **Structure:** 1.00
  - ✓ Valid structure with required keys and types
- ✗ **Accuracy:** 0.00
  - ✗ Expected incorrect, got True

#### ✓ grade_vocab_wrong_01

- ✓ **JSON Validity:** 1.00
  - ✓ Valid JSON output
- ✓ **Structure:** 1.00
  - ✓ Valid structure with required keys and types
- ✓ **Accuracy:** 1.00
  - ✓ Correctly classified as incorrect

#### ✓ grade_vocab_wrong_02

- ✓ **JSON Validity:** 1.00
  - ✓ Valid JSON output
- ✓ **Structure:** 1.00
  - ✓ Valid structure with required keys and types
- ✓ **Accuracy:** 1.00
  - ✓ Correctly classified as incorrect

#### ✓ grade_vocab_wrong_03

- ✓ **JSON Validity:** 1.00
  - ✓ Valid JSON output
- ✓ **Structure:** 1.00
  - ✓ Valid structure with required keys and types
- ✓ **Accuracy:** 1.00
  - ✓ Correctly classified as incorrect

#### ✓ grade_vocab_wrong_04

- ✓ **JSON Validity:** 1.00
  - ✓ Valid JSON output
- ✓ **Structure:** 1.00
  - ✓ Valid structure with required keys and types
- ✓ **Accuracy:** 1.00
  - ✓ Correctly classified as incorrect

#### ✓ grade_vocab_wrong_05

- ✓ **JSON Validity:** 1.00
  - ✓ Valid JSON output
- ✓ **Structure:** 1.00
  - ✓ Valid structure with required keys and types
- ✓ **Accuracy:** 1.00
  - ✓ Correctly classified as incorrect

### Grammar Grading

#### ✓ grade_grammar_abbrev_01

- ✓ **JSON Validity:** 1.00
  - ✓ Valid JSON output
- ✓ **Structure:** 1.00
  - ✓ Valid structure with required keys and types
- ✓ **Accuracy:** 1.00
  - ✓ Correctly classified as correct

#### ✓ grade_grammar_abbrev_02

- ✓ **JSON Validity:** 1.00
  - ✓ Valid JSON output
- ✓ **Structure:** 1.00
  - ✓ Valid structure with required keys and types
- ✓ **Accuracy:** 1.00
  - ✓ Correctly classified as correct

#### ✓ grade_grammar_case_required_01

- ✓ **JSON Validity:** 1.00
  - ✓ Valid JSON output
- ✓ **Structure:** 1.00
  - ✓ Valid structure with required keys and types
- ✓ **Accuracy:** 1.00
  - ✓ Correctly classified as incorrect

#### ✓ grade_grammar_case_required_02

- ✓ **JSON Validity:** 1.00
  - ✓ Valid JSON output
- ✓ **Structure:** 1.00
  - ✓ Valid structure with required keys and types
- ✓ **Accuracy:** 1.00
  - ✓ Correctly classified as incorrect

#### ✓ grade_grammar_case_required_03

- ✓ **JSON Validity:** 1.00
  - ✓ Valid JSON output
- ✓ **Structure:** 1.00
  - ✓ Valid structure with required keys and types
- ✓ **Accuracy:** 1.00
  - ✓ Correctly classified as incorrect

#### ✓ grade_grammar_exact_01

- ✓ **JSON Validity:** 1.00
  - ✓ Valid JSON output
- ✓ **Structure:** 1.00
  - ✓ Valid structure with required keys and types
- ✓ **Accuracy:** 1.00
  - ✓ Correctly classified as correct

#### ✓ grade_grammar_exact_02

- ✓ **JSON Validity:** 1.00
  - ✓ Valid JSON output
- ✓ **Structure:** 1.00
  - ✓ Valid structure with required keys and types
- ✓ **Accuracy:** 1.00
  - ✓ Correctly classified as correct

#### ✓ grade_grammar_exact_03

- ✓ **JSON Validity:** 1.00
  - ✓ Valid JSON output
- ✓ **Structure:** 1.00
  - ✓ Valid structure with required keys and types
- ✓ **Accuracy:** 1.00
  - ✓ Correctly classified as correct

#### ✓ grade_grammar_exact_04

- ✓ **JSON Validity:** 1.00
  - ✓ Valid JSON output
- ✓ **Structure:** 1.00
  - ✓ Valid structure with required keys and types
- ✓ **Accuracy:** 1.00
  - ✓ Correctly classified as correct

#### ✓ grade_grammar_exact_05

- ✓ **JSON Validity:** 1.00
  - ✓ Valid JSON output
- ✓ **Structure:** 1.00
  - ✓ Valid structure with required keys and types
- ✓ **Accuracy:** 1.00
  - ✓ Correctly classified as correct

#### ✓ grade_grammar_harakaat_internal_01

- ✓ **JSON Validity:** 1.00
  - ✓ Valid JSON output
- ✓ **Structure:** 1.00
  - ✓ Valid structure with required keys and types
- ✓ **Accuracy:** 1.00
  - ✓ Correctly classified as correct

#### ✓ grade_grammar_harakaat_internal_02

- ✓ **JSON Validity:** 1.00
  - ✓ Valid JSON output
- ✓ **Structure:** 1.00
  - ✓ Valid structure with required keys and types
- ✓ **Accuracy:** 1.00
  - ✓ Correctly classified as correct

#### ✓ grade_grammar_harakaat_internal_03

- ✓ **JSON Validity:** 1.00
  - ✓ Valid JSON output
- ✓ **Structure:** 1.00
  - ✓ Valid structure with required keys and types
- ✓ **Accuracy:** 1.00
  - ✓ Correctly classified as correct

#### ✓ grade_grammar_wrong_01

- ✓ **JSON Validity:** 1.00
  - ✓ Valid JSON output
- ✓ **Structure:** 1.00
  - ✓ Valid structure with required keys and types
- ✓ **Accuracy:** 1.00
  - ✓ Correctly classified as incorrect

#### ✓ grade_grammar_wrong_02

- ✓ **JSON Validity:** 1.00
  - ✓ Valid JSON output
- ✓ **Structure:** 1.00
  - ✓ Valid structure with required keys and types
- ✓ **Accuracy:** 1.00
  - ✓ Correctly classified as incorrect

#### ✓ grade_grammar_wrong_03

- ✓ **JSON Validity:** 1.00
  - ✓ Valid JSON output
- ✓ **Structure:** 1.00
  - ✓ Valid structure with required keys and types
- ✓ **Accuracy:** 1.00
  - ✓ Correctly classified as incorrect

#### ✓ grade_grammar_wrong_04

- ✓ **JSON Validity:** 1.00
  - ✓ Valid JSON output
- ✓ **Structure:** 1.00
  - ✓ Valid structure with required keys and types
- ✓ **Accuracy:** 1.00
  - ✓ Correctly classified as incorrect

#### ✓ grade_grammar_wrong_05

- ✓ **JSON Validity:** 1.00
  - ✓ Valid JSON output
- ✓ **Structure:** 1.00
  - ✓ Valid structure with required keys and types
- ✓ **Accuracy:** 1.00
  - ✓ Correctly classified as incorrect
