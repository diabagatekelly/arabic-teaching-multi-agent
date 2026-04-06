# API Contract

**Version:** 1.0  
**Base URL:** `/api/v1`  
**Format:** JSON  
**Authentication:** Session-based (session_id in headers or cookies)

---

## Table of Contents

1. [Session Management](#session-management)
2. [Lesson Initialization](#lesson-initialization)
3. [Vocabulary Endpoints](#vocabulary-endpoints)
4. [Grammar Endpoints](#grammar-endpoints)
5. [Exercise Endpoints](#exercise-endpoints)
6. [Test Endpoints](#test-endpoints)
7. [Error Responses](#error-responses)
8. [State Queries](#state-queries)

---

## Session Management

### Start New Session

**Endpoint:** `POST /session/start`

**Request:**
```json
{
  "user_id": "user_123",
  "lesson_number": 3
}
```

**Response:**
```json
{
  "session_id": "sess_abc123",
  "user_id": "user_123",
  "lesson_number": 3,
  "created_at": "2026-04-04T10:30:00Z",
  "state": {
    "vocab_mode": "not_started",
    "grammar_mode": "not_started",
    "vocab_batches_completed": [],
    "grammar_topics_completed": []
  }
}
```

### Get Session State

**Endpoint:** `GET /session/{session_id}`

**Response:**
```json
{
  "session_id": "sess_abc123",
  "user_id": "user_123",
  "lesson_number": 3,
  "state": {
    "vocab_mode": "batch_quiz",
    "current_vocab_batch": 2,
    "vocab_batches_completed": [1],
    "vocab_batch_scores": {"1": "2/3"},
    "vocab_words_missed": ["مَدْرَسَة"],
    
    "grammar_mode": "not_started",
    "grammar_topics_completed": [],
    "current_grammar_topic": null
  }
}
```

---

## Lesson Initialization

### Initialize Lesson

**Endpoint:** `POST /lesson/initialize`

**Description:** Loads all content into memory (Agent 3 caches vocabulary + grammar, Agent 2 pre-loads rules)

**Request:**
```json
{
  "session_id": "sess_abc123",
  "lesson_number": 3
}
```

**Response:**
```json
{
  "success": true,
  "lesson_number": 3,
  "lesson_structure": {
    "vocabulary": {
      "total_words": 10,
      "batch_structure": [3, 3, 3, 1],
      "batches_count": 4
    },
    "grammar": {
      "topics": ["feminine_nouns", "definite_article"],
      "topics_count": 2,
      "quiz_questions_per_topic": 5
    }
  },
  "message": "Lesson 3 ready! Start with vocabulary or grammar?",
  "next_actions": [
    {"action": "start_vocab", "label": "Start Vocabulary (10 words)"},
    {"action": "start_grammar", "label": "Start Grammar (2 topics)"},
    {"action": "vocab_final_test", "label": "Skip to Vocabulary Test"}
  ]
}
```

**Orchestrator Mapping:**
```python
orchestrator.initialize_lesson(lesson_number=3)
```

---

## Vocabulary Endpoints

### Start Vocabulary Section

**Endpoint:** `POST /vocab/start`

**Request:**
```json
{
  "session_id": "sess_abc123"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Let's learn 10 new words in 4 batches! Ready to start?",
  "total_words": 10,
  "batches_count": 4,
  "next_action": {
    "action": "get_batch",
    "batch_number": 1
  }
}
```

---

### Get Vocabulary Batch

**Endpoint:** `GET /vocab/batch/{batch_number}`

**Request:** (batch_number in URL)

**Response:**
```json
{
  "success": true,
  "lesson_number": 3,
  "batch_number": 1,
  "total_batches": 4,
  "words": [
    {
      "word_id": "w1",
      "arabic": "كِتَاب",
      "transliteration": "kitaab",
      "english": "book"
    },
    {
      "word_id": "w2",
      "arabic": "مَدْرَسَة",
      "transliteration": "madrasa",
      "english": "school"
    },
    {
      "word_id": "w3",
      "arabic": "قَلَم",
      "transliteration": "qalam",
      "english": "pen"
    }
  ],
  "message": "Let's learn Batch 1! Here are your first 3 words:\n\n📝 كِتَاب (kitaab) - book\n📝 مَدْرَسَة (madrasa) - school\n📝 قَلَم (qalam) - pen\n\nTake your time reviewing these. When you're ready, let's test your knowledge!",
  "next_action": {
    "action": "start_batch_quiz",
    "batch_number": 1
  }
}
```

**Orchestrator Mapping:**
```python
orchestrator.get_vocab_batch(batch_number=1)
```

---

### Start Batch Quiz

**Endpoint:** `POST /vocab/batch/{batch_number}/quiz/start`

**Request:**
```json
{
  "session_id": "sess_abc123"
}
```

**Response:**
```json
{
  "success": true,
  "batch_number": 1,
  "total_questions": 3,
  "question_number": 1,
  "question": {
    "question_id": "q1",
    "word_id": "w1",
    "type": "arabic_to_english",
    "prompt": "What does كِتَاب mean?",
    "arabic": "كِتَاب",
    "transliteration": "kitaab"
  }
}
```

---

### Submit Vocabulary Answer

**Endpoint:** `POST /vocab/batch/{batch_number}/quiz/answer`

**Request:**
```json
{
  "session_id": "sess_abc123",
  "question_id": "q1",
  "word_id": "w1",
  "student_answer": "book"
}
```

**Response (Correct):**
```json
{
  "success": true,
  "correct": true,
  "feedback": "Correct! ✓ كِتَاب = book. Great job!",
  "score": {
    "current": "1/1",
    "progress": "Question 1 of 3 complete"
  },
  "next_action": {
    "action": "next_question",
    "question_number": 2
  }
}
```

**Response (Incorrect):**
```json
{
  "success": true,
  "correct": false,
  "student_answer": "school",
  "correct_answer": "book",
  "feedback": "Not quite! The word كِتَاب (kitaab) means 'book', not 'school'. Try to remember: kitaab = book.",
  "score": {
    "current": "0/1",
    "progress": "Question 1 of 3 complete"
  },
  "next_action": {
    "action": "next_question",
    "question_number": 2
  }
}
```

**Orchestrator Mapping:**
```python
orchestrator.handle_vocab_quiz_answer(
    batch_number=1,
    question_id="q1",
    word_id="w1",
    student_answer="book"
)
```

---

### Get Batch Quiz Summary

**Endpoint:** `GET /vocab/batch/{batch_number}/quiz/summary`

**Response:**
```json
{
  "success": true,
  "batch_number": 1,
  "score": "2/3",
  "words_correct": ["كِتَاب", "قَلَم"],
  "words_incorrect": [
    {
      "arabic": "مَدْرَسَة",
      "transliteration": "madrasa",
      "correct_answer": "school",
      "student_answer": "house"
    }
  ],
  "message": "Good effort! You got 2 out of 3 correct.\n\nYou missed:\n• مَدْرَسَة (madrasa) = school",
  "next_action": {
    "action": "get_batch",
    "batch_number": 2,
    "label": "Continue to Batch 2"
  }
}
```

---

### Start Vocabulary Final Test

**Endpoint:** `POST /vocab/final-test/start`

**Request:**
```json
{
  "session_id": "sess_abc123"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Final vocabulary test! All 10 words, randomized order.",
  "total_questions": 10,
  "test_type": "vocabulary_final",
  "next_action": {
    "action": "get_question",
    "question_number": 1
  }
}
```

---

### Submit Final Test Answer

**Endpoint:** `POST /vocab/final-test/answer`

**Request:**
```json
{
  "session_id": "sess_abc123",
  "question_number": 3,
  "word_id": "w5",
  "student_answer": "house"
}
```

**Response:**
```json
{
  "success": true,
  "correct": true,
  "feedback": "Correct! ✓",
  "score": {
    "current": "3/3",
    "total": 10,
    "progress": "Question 3 of 10 complete"
  },
  "next_action": {
    "action": "next_question",
    "question_number": 4
  }
}
```

---

### Get Final Test Results

**Endpoint:** `GET /vocab/final-test/results`

**Response:**
```json
{
  "success": true,
  "score": "8/10",
  "percentage": 80,
  "words_correct": 8,
  "words_incorrect": [
    {
      "arabic": "مَدْرَسَة",
      "correct_answer": "school",
      "student_answer": "house"
    },
    {
      "arabic": "بَيْت",
      "correct_answer": "house",
      "student_answer": "door"
    }
  ],
  "message": "Great job! You scored 8 out of 10! 🎉\n\nWords to review:\n• مَدْرَسَة (madrasa) = school\n• بَيْت (bayt) = house",
  "next_action": {
    "action": "start_grammar",
    "label": "Start Grammar Section"
  }
}
```

---

## Grammar Endpoints

### Start Grammar Section

**Endpoint:** `POST /grammar/start`

**Request:**
```json
{
  "session_id": "sess_abc123"
}
```

**Response:**
```json
{
  "success": true,
  "lesson_number": 3,
  "topics": [
    {
      "topic_id": "feminine_nouns",
      "topic_name": "Feminine Nouns",
      "order": 1
    },
    {
      "topic_id": "definite_article",
      "topic_name": "Definite Article",
      "order": 2
    }
  ],
  "message": "I'll teach you 2 grammar topics:\n1. Feminine Nouns\n2. Definite Article\n\nEach topic has a 5-question quiz. Ready to start?",
  "next_action": {
    "action": "get_topic",
    "topic_id": "feminine_nouns"
  }
}
```

---

### Get Grammar Topic Explanation

**Endpoint:** `GET /grammar/topic/{topic_id}`

**Response:**
```json
{
  "success": true,
  "lesson_number": 3,
  "topic_id": "feminine_nouns",
  "topic_name": "Feminine Nouns",
  "explanation": "Let's learn about Feminine Nouns! 🌟\n\n**The Rule:**\nIn Arabic, most feminine nouns end with ة (taa marbuuta).\n\n**Examples:**\n- مَدْرَسَة (madrasa) - school ✓ (ends in ة)\n- كِتَاب (kitaab) - book (masculine, no ة)\n\n**Quick Check:** Look at the word بِنْت (bint - girl). Does it end in ة?",
  "grammar_rule": "Feminine nouns usually end in ة (taa marbuuta)",
  "examples": [
    {
      "arabic": "مَدْرَسَة",
      "transliteration": "madrasa",
      "english": "school",
      "is_feminine": true,
      "explanation": "ends in ة"
    },
    {
      "arabic": "كِتَاب",
      "transliteration": "kitaab",
      "english": "book",
      "is_feminine": false,
      "explanation": "no ة - masculine"
    }
  ],
  "topics_remaining": 1,
  "next_action": {
    "action": "start_topic_quiz",
    "topic_id": "feminine_nouns"
  }
}
```

**Orchestrator Mapping:**
```python
orchestrator.get_grammar_topic_explanation(topic_id="feminine_nouns")
```

---

### Start Topic Quiz

**Endpoint:** `POST /grammar/topic/{topic_id}/quiz/start`

**Request:**
```json
{
  "session_id": "sess_abc123"
}
```

**Response:**
```json
{
  "success": true,
  "topic_id": "feminine_nouns",
  "topic_name": "Feminine Nouns",
  "total_questions": 5,
  "message": "Now let's test your understanding with 5 questions!",
  "next_action": {
    "action": "get_question",
    "question_number": 1
  }
}
```

---

### Get Topic Quiz Question

**Endpoint:** `GET /grammar/topic/{topic_id}/quiz/question/{question_number}`

**Response:**
```json
{
  "success": true,
  "topic_id": "feminine_nouns",
  "question_number": 1,
  "total_questions": 5,
  "question": {
    "question_id": "gq1",
    "type": "identification",
    "prompt": "Is 'مَدْرَسَة' masculine or feminine?",
    "arabic": "مَدْرَسَة",
    "transliteration": "madrasa",
    "options": ["masculine", "feminine"]
  }
}
```

---

### Submit Topic Quiz Answer

**Endpoint:** `POST /grammar/topic/{topic_id}/quiz/answer`

**Request:**
```json
{
  "session_id": "sess_abc123",
  "question_id": "gq1",
  "question_number": 1,
  "student_answer": "feminine"
}
```

**Response (Correct):**
```json
{
  "success": true,
  "correct": true,
  "feedback": "Correct! ✓ مَدْرَسَة is feminine because it ends in ة (taa marbuuta). You're doing great! (1/1 so far)",
  "explanation": "The ة ending is the key indicator of feminine nouns.",
  "score": {
    "current_topic": "1/1",
    "questions_remaining": 4
  },
  "next_action": {
    "action": "next_question",
    "question_number": 2
  }
}
```

**Response (Incorrect):**
```json
{
  "success": true,
  "correct": false,
  "student_answer": "masculine",
  "correct_answer": "feminine",
  "feedback": "Not quite. مَدْرَسَة is feminine because it ends in ة (taa marbuuta). The ة is the key indicator! (0/1 so far)",
  "errors": [
    {
      "error_type": "gender_identification",
      "details": "مَدْرَسَة ends in ة, which indicates feminine",
      "correction": "Look for the ة (taa marbuuta) ending"
    }
  ],
  "score": {
    "current_topic": "0/1",
    "questions_remaining": 4
  },
  "next_action": {
    "action": "next_question",
    "question_number": 2
  }
}
```

**Orchestrator Mapping:**
```python
orchestrator.handle_grammar_quiz_answer(
    topic_id="feminine_nouns",
    question_id="gq1",
    question_number=1,
    student_answer="feminine"
)
```

---

### Get Topic Quiz Results

**Endpoint:** `GET /grammar/topic/{topic_id}/quiz/results`

**Response (Score >= 4/5):**
```json
{
  "success": true,
  "topic_id": "feminine_nouns",
  "topic_name": "Feminine Nouns",
  "score": "4/5",
  "percentage": 80,
  "passed": true,
  "message": "Great job! You got 4 out of 5 correct! ✓\n\nYou've mastered feminine nouns. Ready for the next topic?",
  "questions_correct": 4,
  "questions_incorrect": 1,
  "next_action": {
    "action": "get_topic",
    "topic_id": "definite_article",
    "label": "Continue to Next Topic"
  }
}
```

**Response (Score < 4/5 - Suggest Review):**
```json
{
  "success": true,
  "topic_id": "feminine_nouns",
  "topic_name": "Feminine Nouns",
  "score": "3/5",
  "percentage": 60,
  "passed": false,
  "message": "You got 3 out of 5. You might want to review feminine nouns.\n\nWeak areas:\n- Identifying ة endings\n- Exceptions to the rule\n\nReview and re-test, or move on?",
  "questions_correct": 3,
  "questions_incorrect": 2,
  "weak_areas": [
    "Identifying ة endings",
    "Exceptions to the rule"
  ],
  "next_actions": [
    {
      "action": "review_topic",
      "topic_id": "feminine_nouns",
      "label": "Review and Re-test"
    },
    {
      "action": "get_topic",
      "topic_id": "definite_article",
      "label": "Move to Next Topic"
    }
  ]
}
```

**Orchestrator Mapping:**
```python
orchestrator.get_topic_quiz_results(topic_id="feminine_nouns")
```

---

## Exercise Endpoints

### Generate Exercises

**Endpoint:** `POST /exercises/generate`

**Request:**
```json
{
  "session_id": "sess_abc123",
  "lesson_number": 3,
  "exercise_type": "fill_in_blank",
  "grammar_point": "gender_agreement",
  "count": 5
}
```

**Response:**
```json
{
  "success": true,
  "exercise_set_id": "exset_123",
  "lesson_number": 3,
  "exercise_type": "fill_in_blank",
  "count": 5,
  "exercises": [
    {
      "exercise_id": "ex1",
      "question": "Complete: كِتَاب ___",
      "options": ["كَبِير", "كَبِيرَة"],
      "hint": "كتاب is masculine"
    },
    {
      "exercise_id": "ex2",
      "question": "Complete: مَدْرَسَة ___",
      "options": ["صَغِير", "صَغِيرَة"],
      "hint": "مدرسة is feminine"
    },
    {
      "exercise_id": "ex3",
      "question": "Complete: قَلَم ___",
      "options": ["جَدِيد", "جَدِيدَة"],
      "hint": "قلم is masculine"
    },
    {
      "exercise_id": "ex4",
      "question": "Complete: سَيَّارَة ___",
      "options": ["كَبِير", "كَبِيرَة"],
      "hint": "سيارة is feminine"
    },
    {
      "exercise_id": "ex5",
      "question": "Complete: بَيْت ___",
      "options": ["جَمِيل", "جَمِيلَة"],
      "hint": "بيت is masculine"
    }
  ],
  "message": "Here are 5 fill-in-blank exercises to practice gender agreement!"
}
```

**Orchestrator Mapping:**
```python
orchestrator.generate_exercises(
    lesson_number=3,
    exercise_type="fill_in_blank",
    grammar_point="gender_agreement",
    count=5
)
```

---

### Submit Exercise Answers

**Endpoint:** `POST /exercises/{exercise_set_id}/submit`

**Request:**
```json
{
  "session_id": "sess_abc123",
  "answers": [
    {"exercise_id": "ex1", "answer": "كَبِير"},
    {"exercise_id": "ex2", "answer": "صَغِيرَة"},
    {"exercise_id": "ex3", "answer": "جَدِيد"},
    {"exercise_id": "ex4", "answer": "كَبِيرَة"},
    {"exercise_id": "ex5", "answer": "جَمِيلَة"}
  ]
}
```

**Response:**
```json
{
  "success": true,
  "exercise_set_id": "exset_123",
  "total_score": "4/5",
  "percentage": 80,
  "results": [
    {
      "exercise_id": "ex1",
      "correct": true,
      "student_answer": "كَبِير"
    },
    {
      "exercise_id": "ex2",
      "correct": true,
      "student_answer": "صَغِيرَة"
    },
    {
      "exercise_id": "ex3",
      "correct": true,
      "student_answer": "جَدِيد"
    },
    {
      "exercise_id": "ex4",
      "correct": true,
      "student_answer": "كَبِيرَة"
    },
    {
      "exercise_id": "ex5",
      "correct": false,
      "student_answer": "جَمِيلَة",
      "correct_answer": "جَمِيل",
      "explanation": "بَيْت is masculine, so use جَمِيل (masculine)"
    }
  ],
  "message": "Great work! You got 4 out of 5 correct! 🌟\n\nReview:\n• Exercise 5: بَيْت is masculine, use جَمِيل"
}
```

**Orchestrator Mapping:**
```python
orchestrator.grade_exercises(
    exercise_set_id="exset_123",
    answers=[...]
)
```

---

## Test Endpoints

### Generate Lesson Test

**Endpoint:** `POST /test/generate`

**Request:**
```json
{
  "session_id": "sess_abc123",
  "lesson_number": 3,
  "question_count": 10
}
```

**Response:**
```json
{
  "success": true,
  "test_id": "test_456",
  "lesson_number": 3,
  "question_count": 10,
  "grammar_points": ["feminine_nouns", "definite_article"],
  "message": "Lesson 3 Test - 10 questions covering all topics",
  "questions": [
    {
      "question_id": "t1",
      "type": "fill_in_blank",
      "prompt": "Complete: الكتاب ___",
      "options": ["الكبير", "كبير"]
    },
    {
      "question_id": "t2",
      "type": "identification",
      "prompt": "Is 'بِنْت' masculine or feminine?",
      "options": ["masculine", "feminine"]
    }
    // ... 8 more questions
  ]
}
```

---

### Submit Test Answers

**Endpoint:** `POST /test/{test_id}/submit`

**Request:**
```json
{
  "session_id": "sess_abc123",
  "answers": [
    {"question_id": "t1", "answer": "الكبير"},
    {"question_id": "t2", "answer": "feminine"}
    // ... all 10 answers
  ]
}
```

**Response:**
```json
{
  "success": true,
  "test_id": "test_456",
  "total_score": "8/10",
  "percentage": 80,
  "passed": true,
  "results_by_topic": {
    "feminine_nouns": {
      "score": "5/5",
      "status": "excellent"
    },
    "definite_article": {
      "score": "3/5",
      "status": "needs_review"
    }
  },
  "message": "Well done! You scored 8 out of 10! 🎉\n\nStrengths:\n- Excellent at feminine nouns (5/5 correct)\n\nAreas to review:\n- Definite article agreement (3/5 correct)\n\nSuggestion: Review when to use ال with adjectives.\n\nReady to move to Lesson 4?",
  "next_actions": [
    {
      "action": "review_topic",
      "topic_id": "definite_article",
      "label": "Review Definite Article"
    },
    {
      "action": "next_lesson",
      "lesson_number": 4,
      "label": "Start Lesson 4"
    }
  ]
}
```

---

## Error Responses

### Standard Error Format

All errors follow this structure:

```json
{
  "success": false,
  "error": {
    "code": "ERROR_CODE",
    "message": "Human-readable error message",
    "details": {}
  }
}
```

### Error Codes

**Authentication/Session:**
- `INVALID_SESSION` (401) - Session ID not found or expired
- `SESSION_EXPIRED` (401) - Session timed out
- `UNAUTHORIZED` (401) - User not authorized for this resource

**Validation:**
- `INVALID_REQUEST` (400) - Malformed JSON or missing required fields
- `INVALID_LESSON` (400) - Lesson number doesn't exist
- `INVALID_BATCH` (400) - Batch number out of range
- `INVALID_TOPIC` (400) - Topic ID not found in lesson

**State:**
- `LESSON_NOT_INITIALIZED` (400) - Must call `/lesson/initialize` first
- `WRONG_MODE` (400) - Action not allowed in current mode (e.g., trying to quiz before teaching)
- `QUIZ_NOT_STARTED` (400) - Must start quiz before submitting answers

**RAG/Content:**
- `CONTENT_NOT_FOUND` (404) - Requested content not in RAG database
- `RAG_TIMEOUT` (504) - RAG query timed out

**Agent:**
- `AGENT_ERROR` (500) - Agent returned invalid response
- `GENERATION_TIMEOUT` (504) - Exercise/question generation timed out
- `GRADING_ERROR` (500) - Agent 2 failed to grade

### Error Examples

**Invalid Session:**
```json
{
  "success": false,
  "error": {
    "code": "INVALID_SESSION",
    "message": "Session not found or expired",
    "details": {
      "session_id": "sess_invalid"
    }
  }
}
```

**Lesson Not Initialized:**
```json
{
  "success": false,
  "error": {
    "code": "LESSON_NOT_INITIALIZED",
    "message": "Lesson must be initialized before starting vocabulary",
    "details": {
      "required_action": "POST /lesson/initialize"
    }
  }
}
```

**Content Not Found:**
```json
{
  "success": false,
  "error": {
    "code": "CONTENT_NOT_FOUND",
    "message": "Lesson 99 not found in database",
    "details": {
      "lesson_number": 99,
      "available_lessons": [1, 2, 3, 4, 5, 6, 7, 8]
    }
  }
}
```

---

## State Queries

### Get Current Progress

**Endpoint:** `GET /progress/{session_id}`

**Response:**
```json
{
  "success": true,
  "lesson_number": 3,
  "overall_progress": {
    "vocabulary": {
      "status": "in_progress",
      "batches_completed": 2,
      "batches_total": 4,
      "scores": {"1": "2/3", "2": "3/3"},
      "words_mastered": 5,
      "words_total": 10
    },
    "grammar": {
      "status": "not_started",
      "topics_completed": 0,
      "topics_total": 2,
      "scores": {}
    }
  }
}
```

---

## Implementation Notes

### Session Management

**Storage:** Redis or in-memory cache (for demo)

**Session Object:**
```python
{
    "session_id": "sess_abc123",
    "user_id": "user_123",
    "lesson_number": 3,
    "created_at": "2026-04-04T10:30:00Z",
    "last_activity": "2026-04-04T11:00:00Z",
    "expires_at": "2026-04-04T18:30:00Z",  # 8 hours
    
    # Full conversation state (from ARCHITECTURE.md)
    "state": {
        "vocab_mode": "batch_quiz",
        "vocab_batches_completed": [1],
        "current_vocab_batch": 2,
        # ... full state schema
    }
}
```

### Rate Limiting

- 100 requests per minute per session
- 10 concurrent sessions per user

### Response Times

Target latencies:
- Vocabulary/Grammar content: < 200ms (from cache)
- Single answer grading: < 500ms (Agent 2 pre-loaded)
- Exercise generation: < 2s (Agent 3 LLM generation)
- Lesson initialization: < 3s (RAG query + caching)

---

**Next Steps for Implementation:**

1. Build orchestrator with these exact return formats
2. Wrap orchestrator in FastAPI with these endpoints
3. Frontend consumes these contracts exactly

**Contract is versioned:** If we need changes, create `/api/v2`
