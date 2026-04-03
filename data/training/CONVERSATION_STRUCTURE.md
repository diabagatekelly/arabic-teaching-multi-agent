# Training Conversation Structure Documentation

## Overview

Training conversations teach the LLM **HOW to teach** Arabic - the pedagogy, flow management, and conversational patterns. Each conversation is in chat format with system prompts providing context.

---

## Conversation Format

```json
{
  "messages": [
    {
      "role": "system",
      "content": "Context about mode, lesson, phase, student history, objectives"
    },
    {
      "role": "user",
      "content": "Student input"
    },
    {
      "role": "assistant",
      "content": "Model response - teaching, feedback, guidance"
    },
    // ... more turns
  ]
}
```

Each line in the JSONL file is one complete conversation.

---

## System Prompt Structure

System prompts provide crucial context the model needs to respond appropriately:

```
Mode: [Learning Pathway | Quick Review | Session Start]
Lesson: [Number] - [Name]
Phase: [Vocabulary Learning | Vocab Practice | Grammar Lesson | Grammar Exercises | etc.]
Grammar focus: [Specific topic]
Vocabulary (10 words): [List of words with review/new designation]
Student Progress: [Lessons completed, overall accuracy]
Recent Sessions: [What happened last time, when]
Weak Areas: [Specific struggles with percentages]
Current: [Current position in multi-step process]
Objective: [What this conversation should accomplish]
```

Not all fields appear in every system prompt - only what's relevant to that conversation.

---

## Conversation Categories

### **Category 1: Session Management (3 conversations)**

**1.1 Session Start & Navigation**
- **Conversation ID:** Conv 1
- **Purpose:** Greeting, mode selection, lesson structure explanation
- **Key Patterns:**
  - Welcome back with progress recap
  - Present available vs locked options
  - Explain lesson structure before starting
  - Guide user to their choice
- **System Prompt Focus:** Available options, last session date, unlocked content

**1.2 Lesson Completion & Scoring**
- **Conversation ID:** Conv 6
- **Purpose:** Celebrate completion, show comprehensive results, present next steps
- **Key Patterns:**
  - Detailed score breakdown (vocab + grammar)
  - Spaced repetition status update
  - Unlocking notification
  - Multiple next-step options
- **System Prompt Focus:** All scores, SR intervals, next available content

**1.3 Locked Content Explanation**
- **Conversation ID:** Conv 10
- **Purpose:** Explain why content is locked, offer constructive alternatives
- **Key Patterns:**
  - Clear explanation of threshold requirement
  - Show which component needs work
  - Offer review/retake options
  - Positive framing (not punitive)
- **System Prompt Focus:** Specific scores that fell short, threshold requirement

---

### **Category 2: Vocabulary Learning (4 conversations)**

**2.1 Word-by-Word Presentation**
- **Conversation ID:** Conv 2
- **Purpose:** Present 10 words one at a time with pacing control
- **Key Patterns:**
  - "Word X of 10" progress tracking
  - Distinguish review vs new words
  - Wait for student confirmation
  - Encouragement at milestones (halfway, etc.)
  - Transition to practice after word 10
- **System Prompt Focus:** Current word number, full vocab list with review/new tags

**2.2 Vocabulary Practice Exercises**
- **Conversation ID:** Conv 3
- **Purpose:** Test vocabulary retention through exercises
- **Key Patterns:**
  - Exercise type announcement (matching, fill-blank, translation)
  - Question numbering (1 of 5)
  - Immediate feedback: ✓ correct, ✗ with correction
  - Running score display
  - Exercise completion summary
  - Transition to next exercise
- **System Prompt Focus:** Exercise type, which exercise number (1 of 3), current score

**2.3 Mid-Lesson Breaks**
- **Conversation ID:** Conv 7
- **Purpose:** Handle student-initiated breaks and resumption
- **Key Patterns:**
  - Acknowledge break request positively
  - Save progress explicitly
  - Welcome back warmly
  - Resume exactly where left off
- **System Prompt Focus:** Current position in sequence, what's remaining

**2.4 Quick Review - Flashcards**
- **Conversation ID:** Conv 12
- **Purpose:** Fast-paced vocabulary review
- **Key Patterns:**
  - Rapid fire (no explanations between)
  - Bidirectional (Arabic→English, English→Arabic)
  - Running score commentary ("5/5 so far!")
  - Perfect score celebration
  - SR interval update
- **System Prompt Focus:** Category selected, words due for review

---

### **Category 3: Grammar Teaching (2 conversations)**

**3.1 Grammar Lesson Introduction**
- **Conversation ID:** Conv 4 (second half)
- **Purpose:** Teach new grammar concept clearly
- **Key Patterns:**
  - Clear rule statement (numbered when multiple)
  - Multiple examples with structure breakdown
  - Visual formatting (bold, indentation)
  - Compare/contrast patterns
  - Check comprehension before exercises
- **System Prompt Focus:** Grammar concept, relevant vocabulary from lesson

**3.2 Grammar Exercises**
- **Conversation ID:** Conv 5
- **Purpose:** Apply grammar rules in practice
- **Key Patterns:**
  - Task description clear ("Build phrases", "Translate")
  - Question structure with hints
  - Feedback explains WHY answer is right/wrong
  - Corrections show proper form
  - Progressive difficulty
  - Option to continue or move on
- **System Prompt Focus:** Grammar concept being practiced, lesson vocabulary

---

### **Category 4: Error Handling & Support (3 conversations)**

**4.1 Repeated Error Pattern Recognition**
- **Conversation ID:** Conv 9
- **Purpose:** Identify recurring mistake, provide targeted help
- **Key Patterns:**
  - Acknowledge pattern: "I notice you've missed X a few times"
  - Provide memory trick or mnemonic
  - Extra focused practice on that specific point
  - Build confidence with successes
  - Re-explain concept differently
- **System Prompt Focus:** Student error pattern, accuracy percentage on that skill

**4.2 Struggling Student Support**
- **Conversation ID:** Conv 11
- **Purpose:** Recognize frustration, slow down, rebuild confidence
- **Key Patterns:**
  - Validate feelings: "It's totally okay"
  - Normalize struggle: "Many students find this hard"
  - Offer multiple support options
  - Break concept into smaller pieces
  - Go at student's pace explicitly
  - Celebrate small wins
- **System Prompt Focus:** Low scores, student frustration cues

**4.3 Near-Miss Corrections**
- **Conversation ID:** Conv 3, 5, 9 (embedded in exercises)
- **Purpose:** Correct errors gently but clearly
- **Key Patterns:**
  - "Almost!" when close
  - Identify what was right first
  - Show specific error
  - Provide correct form
  - Brief explanation of fix
  - Immediate retry opportunity
- **System Prompt Focus:** Student's error type, related weak areas

---

### **Category 5: Transitions & Flow Management (3 conversations)**

**5.1 Phase Transitions**
- **Conversation ID:** Conv 4 (first half)
- **Purpose:** Move from vocab practice → grammar lesson
- **Key Patterns:**
  - Summarize completed phase with all scores
  - Celebrate improvement across exercises
  - Preview what comes next
  - Motivational framing ("Now let's USE these words")
  - Check readiness
- **System Prompt Focus:** Results from all previous exercises, next phase description

**5.2 Quick Review Mode Selection**
- **Conversation ID:** Conv 8
- **Purpose:** Guide user through Quick Review options
- **Key Patterns:**
  - Show review status (X words due)
  - Highlight weak areas
  - Present clear option menu (numbered)
  - Explain what each option does
  - Adapt to user choice
- **System Prompt Focus:** Words due for SR, weak areas with percentages, available categories

**5.3 Mid-Conversation Redirects**
- **Conversation ID:** Conv 10 (attempting locked content)
- **Purpose:** Handle invalid actions, offer alternatives
- **Key Patterns:**
  - Acknowledge intent positively
  - Explain constraint clearly
  - Show specific requirement
  - Offer constructive alternatives
  - Keep momentum positive
- **System Prompt Focus:** Why action is blocked, what's needed to unblock

---

## Key Teaching Patterns Across All Conversations

### **1. Feedback Types**

**Correct Answer:**
- "Perfect! ✓"
- "Excellent!"
- "Correct!"
- Brief confirmation, move on quickly

**Incorrect Answer:**
- "Almost!" (near miss)
- "Not quite" (clear error)
- Identify what was RIGHT first
- Show correct form
- Brief explanation
- Immediate retry or move forward

**Repeated Error:**
- Acknowledge pattern
- Provide memory trick
- Extra practice
- Rebuild confidence

### **2. Progress Communication**

**During Activity:**
- "Word 5 of 10"
- "Question 3 of 5"
- "You're halfway through!"
- "Exercise 1 Complete: 4/5 (80%)"

**End of Activity:**
- Detailed breakdown
- Overall percentage
- What this means for progression
- Next available options

### **3. Encouragement Timing**

**Small Wins:**
- "Great!" after correct answer
- "You're getting it!" after correction applied

**Milestones:**
- "You're halfway through!"
- "7 down, 3 to go!"

**Completion:**
- "🎉 Lesson Complete! 🎉"
- "Fantastic improvement!"
- "You've mastered..."

**Struggle Support:**
- "It's totally okay"
- "No worries"
- "We go at your pace"

### **4. Choice Presentation**

**Numbered Options:**
```
What would you like to do?

1. **Option Name** (context/status)
2. **Option Name** (context/status)
3. **Option Name** (context/status)

Which sounds good?
```

**Binary Choices:**
"Ready to continue or take a break?"

**Open Ended:**
"What sounds most helpful right now?"

### **5. Context Reminders**

**During Exercises:**
- "Remember كِتَاب from Lesson 1?"
- "Remember: feminine = ـَتْ"
- Brief refreshers without full re-teaching

**In Hints:**
- "Hint: 'he wrote' = كَتَبَ"
- "Hint: feminine adjectives add ة"

### **6. Spaced Repetition Integration**

**Words Due Mention:**
- "12 words due for review today"
- "This word is due tomorrow"

**Interval Updates:**
- "These 10 words now move to 7-day interval"
- "Next review: 1 week from today"

**Mastery Status:**
- "8/10 words mastered"
- "2 words need review tomorrow"

---

## System Prompt Field Reference

### **Always Include:**
- `Mode:` [Learning Pathway | Quick Review | Session Start]
- `Objective:` What this conversation should accomplish

### **Lesson Context (Learning Pathway):**
- `Lesson:` Number and name
- `Phase:` Current phase in lesson
- `Grammar focus:` Specific topic
- `Vocabulary:` The 10 words with review/new tags

### **Student History:**
- `Student Progress:` Lessons completed, overall accuracy
- `Recent Sessions:` What happened, when
- `Weak Areas:` Specific struggles with percentages
- `Last Session:` How long ago

### **Current State (when mid-process):**
- `Current:` Word 5 of 10, Exercise 2 of 3, etc.
- `Results:` Scores from completed phases
- `Spaced Repetition:` Words due, intervals

### **Available Actions:**
- `Available Options:` What's unlocked vs locked
- `Next Available:` What unlocks next

### **Exercise Context:**
- `Exercise Type:` Matching, translation, fill-blank
- `Exercise:` Which number (1 of 3)
- `Words to practice:` Subset for this exercise

---

## Coverage Matrix

| Category | Conversations | Lessons Covered | Modes Covered |
|----------|--------------|-----------------|---------------|
| Session Management | 3 | All | Learning + Quick |
| Vocabulary Learning | 4 | 1, 3 | Learning + Quick |
| Grammar Teaching | 2 | 3, 4, 5, 6, 7 | Learning |
| Error Handling | 3 | 3, 4, 5 | Both |
| Transitions | 3 | All | Both |
| **TOTAL** | **12** | **1-7** | **Both** |

---

## What's NOT Yet Covered

### **Missing Lesson Coverage:**
- ❌ Lesson 1 full flow (only referenced)
- ❌ Lesson 2 full flow (only referenced)
- ❌ Lesson 8 (Possessive Pronouns & Idaafah)

### **Missing Interaction Types:**
- ❌ Different exercise types (fill-in-blank, error correction, conjugation drills)
- ❌ Multiple correct answers scenario
- ❌ Student asking "why?" questions
- ❌ Student asking for examples
- ❌ Student expressing confusion before attempting
- ❌ Perfect score celebration patterns
- ❌ Low score recovery conversations
- ❌ Retaking a lesson scenario
- ❌ First-time user onboarding

### **Missing Error Patterns:**
- ❌ Gender agreement errors (noun-adj mismatch)
- ❌ Definiteness errors (missing ال on one but not other)
- ❌ Wrong prefix on present tense
- ❌ Missing pronouns in sentences
- ❌ Word order errors
- ❌ Spelling/diacritic errors
- ❌ Using wrong negation particle
- ❌ Question formation errors

### **Missing Quick Review Variations:**
- ❌ Mixed practice (vocab + grammar)
- ❌ Grammar-only drills (without context)
- ❌ Error correction exercises
- ❌ Conjugation drills
- ❌ Sentence building exercises

---

## Conversation Length Distribution

| Length (turns) | Count | Examples |
|----------------|-------|----------|
| Short (3-5 turns) | 2 | Conv 1, 10 |
| Medium (6-12 turns) | 6 | Conv 3, 6, 7, 8, 9, 12 |
| Long (13+ turns) | 4 | Conv 2, 4, 5, 11 |

**Average turns per conversation:** ~10
**Total turns across 12 conversations:** ~120

---

## Training Data Quality Notes

### **Strengths:**
✅ Demonstrates full app flow from start to finish
✅ Shows adaptive pacing (fast learner vs struggling student)
✅ Includes error patterns and recovery
✅ Demonstrates encouragement and support
✅ Shows spaced repetition integration
✅ Covers both modes (Learning Pathway + Quick Review)
✅ Includes phase transitions
✅ Shows progress tracking and scoring

### **Areas to Expand:**
⚠️ Need more exercise type variety
⚠️ Need more specific error correction patterns for each grammar point
⚠️ Need first-time user experience
⚠️ Need more Quick Review variations
⚠️ Need Lesson 8 coverage
⚠️ Need more student-initiated questions ("Why?" "Can you explain again?")

---

## Recommended Next Steps

1. **Complete Lesson Coverage (Priority 1)**
   - Create full Lesson 1 flow (15-20 conversations)
   - Create full Lesson 2 flow (15-20 conversations)
   - Create full Lesson 8 flow (15-20 conversations)

2. **Error Type Expansion (Priority 2)**
   - 5-10 conversations per grammar point showing specific errors
   - Each lesson's common mistakes

3. **Exercise Variety (Priority 3)**
   - Fill-in-blank exercises (10 conversations)
   - Error correction exercises (10 conversations)
   - Conjugation drills (10 conversations)
   - Sentence building (10 conversations)

4. **Quick Review Expansion (Priority 4)**
   - Mixed practice flows (10 conversations)
   - Category-specific drills (10 conversations)

5. **Student Question Handling (Priority 5)**
   - "Why does this work?" questions (10 conversations)
   - "Can you give more examples?" (5 conversations)
   - "I'm confused about X" (5 conversations)

**Total Recommended: 200-300 additional conversations**

---

*Document Created: 2026-03-13*
*Current Total: 12 training conversations*
*Target Total: 200-400 training conversations*
