# Interface Contract v2.0

**Interface:** Gradio (gr.Blocks) | **Format:** Chat + UI controls | **State:** File-based sessions

**Note:** This document reflects the ACTUAL Gradio interface implementation. Original REST API design was not implemented.

## Core Interface Components

### Session Management
- **Session ID:** Auto-generated UUID stored in `gr.State`
- **Persistence:** File-based (`sessions.json`) for ZeroGPU compatibility
- **Lifecycle:** Created on lesson start, persists across page reloads, manually cleared

### Lesson Controls (UI Buttons)
- **Start Lesson:** `start_lesson_btn.click()` → Loads Lesson 1 from cache, initializes session
- **End Lesson:** `end_lesson_btn.click()` → Marks session as ended, preserves data
- **Reset Lesson:** `reset_lesson_btn.click()` → Wipes session completely

### Chat Interface
- **Input:** `gr.Textbox` (msg) - User types answers/commands
- **Output:** `gr.Chatbot` (chatbot) - Conversation history with agent
- **Processing:** `process_message(message, chat_history, session_id)` - @spaces.GPU decorated
- **Flow:** User message → Orchestrator routes → Teaching/Grading agent → Response

### Flashcard Display
- **Component:** `gr.HTML` (flashcard_display) - Shows Arabic word or translation
- **Controls:** Flip card, Next card buttons
- **Trigger:** Auto-updates when quiz state changes
- **State:** `gr.State` (flashcard_state) - Current card index, side shown

### Progress Display
- **Lesson Info:** Shows lesson name, status, session state
- **Progress:** Displays learned words count, quiz scores
- **Updates:** After each interaction via orchestrator

## Orchestrator Flow (Internal)

### 1. Start Lesson
```python
orchestrator.start_lesson(session_id, lesson_number=1)
→ Loads from lesson_cache[1]
→ Initializes session state with vocab/grammar structure
→ Returns welcome message via Teaching Agent
```

### 2. Handle Message
```python
orchestrator.handle_message(session_id, user_message)
→ Determines current stage (vocab/grammar/quiz)
→ Routes to Teaching Agent or Grading Agent
→ Updates session state
→ Returns response string
```

### 3. State Transitions
```
lesson_start → vocab_batch_intro → vocab_quiz → vocab_feedback
→ grammar_overview → grammar_explanation → grammar_quiz
→ grammar_feedback → lesson_complete
```

## Session State Schema

```python
{
    "lesson_number": 1,
    "lesson_name": "Gender and Definite Article",
    "vocabulary": {
        "words": [{"arabic": "...", "transliteration": "...", "english": "..."}],
        "current_batch": 1,
        "quizzed_words": [],
        "quiz_state": {
            "current_question": 0,
            "total_questions": 3,
            "words": [...],
            "answers": [],
            "score": 0,
            "feedback_shown": False
        }
    },
    "grammar": {
        "topics": {"topic_id": {"taught": False, "quiz_results": []}},
        "sections": {"rule": "...", "examples": "...", "practice": "..."}
    },
    "current_progress": "vocab_batch_intro",
    "status": "active"
}
```

## Agent Interactions

### Teaching Agent (User-Facing Content)
- **Triggered by:** Lesson welcome, vocab intro, feedback (correct/incorrect), grammar explanations
- **Input:** Prompt template + session variables (words, scores, progress)
- **Output:** Natural language text with encouraging tone
- **Config:** temperature=0.7, top_p=0.92, max_tokens=256

### Grading Agent (Answer Evaluation)
- **Triggered by:** User submits quiz answer (vocab or grammar)
- **Input:** GRADING_VOCAB or GRADING_GRAMMAR_QUIZ template + answer + correct answer
- **Output:** JSON `{"correct": true/false}`
- **Config:** temperature=0.1, top_p=0.95, max_tokens=50 (deterministic)
- **Implementation:** Same model as Teaching Agent, different prompt + config

## Error Handling

**Session Not Found:** Returns "Please start a lesson first" message
**Grading JSON Parse Error:** Falls back to "I couldn't evaluate that answer, please try again"
**GPU Timeout:** Gradio shows timeout message after 60s (@spaces.GPU duration limit)
**Model Loading Failure:** Logs error, returns "System error, please refresh" message

## Performance Characteristics

**Cold Start:** 15-20s (first inference, model loading)
**Warm Inference:** 1.5-2.5s per response (Teaching Agent), 0.8-1.2s (Grading Agent)
**Session Load:** <100ms (read from sessions.json)
**Flashcard Update:** <50ms (HTML render)

## Deployment

**Platform:** HuggingFace Spaces with ZeroGPU
**GPU Allocation:** On-demand via @spaces.GPU decorator (60s max per call)
**Share Link:** Enabled (`demo.launch(share=True)`) - generates 72hr public URL
**Persistence:** sessions.json stored in Space filesystem

---

**Status:** Production deployed  
**Last Updated:** 2026-04-20  
**See also:** `ARCHITECTURE.md`, `INFERENCE.md`, `DEPLOYMENT.md`
