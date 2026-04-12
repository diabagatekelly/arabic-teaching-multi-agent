---
title: Exercise Template Reusability Guide
purpose: Explain how to adapt exercise templates for different grammar points
---

# Exercise Template Reusability Guide

## Overview

Most exercise templates in this directory are **reusable** across multiple grammar points. This guide explains how Agent 3 should adapt each template for different lessons.

---

## Reusability Classification

### ✅ Fully Reusable (Works for ANY grammar point)

These templates work with minimal adaptation:

1. **sorting_gender_categorization.md**
   - **Reusable for**: verb tense, noun number (singular/plural), adjective agreement, sentence types
   - **How to adapt**: Change category names (masculine/feminine → past/present → singular/plural)
   - **Example**: "Sort these verbs: past tense | present tense"

2. **pattern_recognition_gender.md**
   - **Reusable for**: any binary or ternary classification
   - **How to adapt**: Change the target pattern to identify
   - **Example**: "Select all past tense verbs", "Select all plural nouns"

3. **error_correction_definite_article.md**
   - **Reusable for**: any spelling/form errors
   - **How to adapt**: Change error types (ال errors → verb conjugation errors → pronoun errors)
   - **Example**: "Fix the verb conjugation: أنا يكتب → أنا أكتب"

4. **transformation_chain_definite_article.md**
   - **Reusable for**: any A → B transformation
   - **How to adapt**: Change transformation rule
   - **Examples**:
     - Singular → Plural: كِتَابٌ → كُتُبٌ → كِتَابٌ
     - Present → Past: يَكْتُبُ → كَتَبَ → يَكْتُبُ
     - Verb conjugation: أَكْتُبُ → تَكْتُبُ → يَكْتُبُ

5. **cloze_grammar_rules.md**
   - **Reusable for**: ANY grammar rule explanation
   - **How to adapt**: Change the rule text, keep the fill-in-blank format
   - **Example**: "Verbs in past tense end with _____"

6. **paradigm_table_combined.md**
   - **Reusable for**: ANY systematic forms (verb conjugations, noun declensions)
   - **How to adapt**: Change table headers and fill patterns
   - **Examples**:
     - Verb conjugation table: I/you/he/she × singular/plural
     - Noun case table: nominative/accusative/genitive × singular/plural

7. **sentence_level_combined.md**
   - **Reusable for**: ANY grammar in context
   - **How to adapt**: Change error types to match target grammar
   - **Example**: "Fix the verb agreement: أنا يكتب في الكتاب"

8. **multiple_choice_error_identification.md**
   - **Reusable for**: ANY error types
   - **How to adapt**: Change error patterns
   - **Example**: "Which verb is conjugated incorrectly?"

9. **noun_adjective_agreement.md** (NEW)
   - **Reusable for**: verb-subject agreement, pronoun agreement, demonstrative agreement
   - **How to adapt**: Change what must agree (adjective → verb → pronoun)
   - **Example**: "Complete: أنا _____ (to write)" → أنا أَكْتُبُ

---

### ⚠️ Partially Reusable (Needs significant adaptation)

10. **dictation_combined_gender_definite.md**
    - **Current**: Tests gender + definiteness simultaneously
    - **Reusable for**: Any two combined grammar points
    - **How to adapt**: Change the two dimensions being tested
    - **Example**: "Write: 'I wrote' (past tense, first person)" → كَتَبْتُ

---

### ❌ Lesson-Specific (Not easily reusable)

11. **fill_in_blank_gender.md**
    - Highly specific to gender identification (is this masculine or feminine?)
    - Could be adapted for other binary choices but structure is very specialized

12. **translation_definite_article.md**
    - Very specific to adding/removing ال
    - Hard to generalize beyond this transformation

**Note**: Even "non-reusable" templates can inspire similar templates for other grammar points.

---

## How Agent 3 Should Use This Guide

### Step 1: Identify Grammar Point
```
Input: lesson_number=2, grammar_point="verb_conjugation_present"
```

### Step 2: Select Compatible Templates
```
Compatible templates:
- sorting → "Sort by person (I/you/he)"
- pattern_recognition → "Select all first-person verbs"
- error_correction → "Fix conjugation errors"
- transformation_chain → "أَكْتُبُ → تَكْتُبُ → ___"
- cloze → "First person singular verbs start with _____"
- paradigm_table → "Complete verb conjugation table"
- sentence_level → "Fix: أنا يكتب"
```

### Step 3: Adapt Template Parameters
```python
# Example: Adapting sorting template for verb tense
template = "sorting_gender_categorization.md"
adaptations = {
    "category_1": "past_tense",
    "category_2": "present_tense",
    "vocabulary_pool": verb_vocabulary,
    "question_prompt": "Sort these verbs into past and present tense:"
}
```

### Step 4: Generate Exercise
Use adapted parameters to fill template and generate questions.

---

## Template Adaptation Parameters

### For Sorting Templates
```yaml
parameters:
  - category_names: [list of categories to sort into]
  - category_count: 2 or 3
  - vocabulary_pool: items to sort
  - identification_rule: how to determine category (e.g., "ends in ة" → "ends in ت")
```

### For Transformation Templates
```yaml
parameters:
  - transformation_rule: description of A → B
  - forward_example: كِتَابٌ → الْكِتَابُ
  - backward_example: الْكِتَابُ → كِتَابٌ
  - rule_name: "add ال" | "conjugate for first person" | etc.
```

### For Agreement Templates
```yaml
parameters:
  - element_1: noun | verb | pronoun
  - element_2: adjective | subject | verb
  - agreement_dimensions: [gender, definiteness] | [person, number] | etc.
  - rules: list of what must match
```

### For Error Correction Templates
```yaml
parameters:
  - error_types: [list of common errors for this grammar point]
  - correct_forms: examples of correct usage
  - error_patterns: regex or description of errors to introduce
```

---

## Reusability Matrix

| Template | Gender | Def/Indef | Verb Tense | Verb Conj | Noun Plural | Adjective | Pronouns |
|----------|--------|-----------|------------|-----------|-------------|-----------|----------|
| Sorting | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| Pattern Recognition | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| Error Correction | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| Transformation Chain | ✗ | ✓ | ✓ | ✓ | ✓ | ✗ | ✗ |
| Cloze Rules | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| Paradigm Table | ✗ | ✓ | ✗ | ✓ | ✓ | ✗ | ✓ |
| Sentence Level | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| Multiple Choice Error | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| Agreement | ✓ | ✓ | ✗ | ✓ | ✓ | ✓ | ✓ |
| Dictation Combined | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |

**Legend:**
- ✓ = Easily reusable for this grammar point
- ✗ = Not applicable or requires major restructuring

---

## Future Grammar Points & Templates

### Lesson 2: Subject Pronouns & Nominal Sentences
**Reusable templates:**
- Sorting → "Sort pronouns by person (1st/2nd/3rd)"
- Pattern Recognition → "Select all second-person pronouns"
- Agreement → "Match pronoun to noun gender"
- Sentence Level → "Fix: هُوَ طَالِبَةٌ (wrong gender)"

### Lesson 3: Adjective Agreement
**Reusable templates:**
- noun_adjective_agreement.md (already designed for this!)
- Error Correction → Fix gender/definiteness mismatches
- Paradigm Table → Complete all forms (m/f × def/indef)

### Lesson 4: Present Tense Verbs
**Reusable templates:**
- Transformation Chain → I write → you write → he writes
- Paradigm Table → Verb conjugation chart
- Error Correction → Fix conjugation errors
- Cloze → "First person verbs start with _____"

### Lesson 5: Past Tense Verbs
**Reusable templates:**
- Sorting → Sort verbs by tense (past/present)
- Transformation Chain → Present → Past
- Sentence Level → Fix tense in context

---

## Agent 3 Implementation Strategy

### When generating exercises:

1. **Load grammar point** from lesson metadata
2. **Check reusability guide** to find compatible templates
3. **Load template** with parameter adaptations
4. **Parse template rules** (replace gender with tense, etc.)
5. **Generate questions** using adapted vocabulary and rules
6. **Output exercises** with grammar-point-specific content

### Example code structure:
```python
def adapt_template(template_name, grammar_point, vocabulary):
    """Adapt a reusable template for a specific grammar point."""
    
    template = load_template(template_name)
    adaptations = ADAPTATION_RULES[grammar_point]
    
    # Replace category names
    template = template.replace(adaptations["old_category"], adaptations["new_category"])
    
    # Replace vocabulary pool
    template.vocabulary_pool = vocabulary
    
    # Generate questions using adapted template
    questions = generate_questions(template, count=5)
    
    return questions
```

---

## Benefits of Reusable Templates

1. **Consistency**: Same exercise structure across lessons
2. **Efficiency**: Don't reinvent the wheel for each grammar point
3. **Proven patterns**: Templates that work well for gender will work for tense
4. **Easier maintenance**: Fix a bug once, applies to all lessons
5. **Faster development**: Create new lessons without creating new exercise types

---

## When to Create NEW Templates

Create a new template only when:
- Existing templates can't be adapted (e.g., dual vs. plural specific exercise)
- Grammar point has unique structure (e.g., idafa construction)
- Exercise type is fundamentally different (e.g., audio comprehension)

Otherwise, prefer adapting existing templates using this guide.
