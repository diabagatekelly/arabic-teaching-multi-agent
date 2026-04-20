"""Contextual prompt orchestrator - lets the model figure out flow."""

import logging

from src.agents.teaching_agent import TeachingAgent

logger = logging.getLogger(__name__)


class ContextualOrchestrator:
    """Simplified orchestrator using rich context instead of rigid templates."""

    def __init__(
        self,
        lesson_cache,
        sessions,
        teaching_model_getter,
        teaching_tokenizer,
        content_agent=None,
    ):
        """Initialize orchestrator.

        Args:
            lesson_cache: Dict of lesson_number -> lesson_data
            sessions: Dict of session_id -> session_state
            teaching_model_getter: Callable that returns the teaching model
            teaching_tokenizer: The tokenizer for the teaching model
            content_agent: ContentAgent instance (optional, for RAG)
        """
        self.lesson_cache = lesson_cache
        self.sessions = sessions
        self.teaching_model_getter = teaching_model_getter
        self.teaching_tokenizer = teaching_tokenizer
        self.content_agent = content_agent

    def start_lesson(self, session_id, lesson_number):
        """Start a lesson - initialize session and generate welcome.

        Args:
            session_id: User session identifier
            lesson_number: Lesson number to start

        Returns:
            str: Welcome message from teaching agent
        """
        if lesson_number not in self.lesson_cache:
            return f"Error: Lesson {lesson_number} not found in cache."

        lesson_data = self.lesson_cache[lesson_number]

        # Initialize session with minimal tracking
        if session_id not in self.sessions:
            self.sessions[session_id] = {}

        self.sessions[session_id].update(
            {
                "lesson_number": lesson_number,
                "lesson_name": lesson_data["lesson_name"],
                "vocabulary": lesson_data["vocabulary"],
                "grammar_points": lesson_data["grammar_points"],
                "status": "active",
                # Progress tracking
                "vocab_batch_1_taught": False,
                "vocab_batch_1_quiz": "not_started",  # not_started, in_progress, completed, skipped
                "vocab_batch_2_taught": False,
                "vocab_batch_2_quiz": "not_started",
                "grammar_taught": False,
                "grammar_quiz": "not_started",
                "final_exam": "not_started",
                # Quiz state (when active)
                "current_quiz": None,  # None or {type, words, current_q, answers, score}
            }
        )

        logger.info("[ContextualOrchestrator] Starting lesson with contextual prompt")

        # Build welcome prompt
        prompt = self._build_prompt(session_id, "Welcome to the lesson!")

        # Generate response
        teaching_agent = TeachingAgent(self.teaching_model_getter(), self.teaching_tokenizer)
        response = teaching_agent.respond(prompt, max_new_tokens=512, temperature=0.7)

        return response

    def handle_message(self, session_id, user_message):
        """Handle user message with contextual prompt.

        Args:
            session_id: User session identifier
            user_message: User's message text

        Returns:
            str: Response from teaching agent
        """
        session = self.sessions.get(session_id)
        if not session or session.get("status") != "active":
            return "No active lesson. Please start a lesson first."

        logger.info("=" * 80)
        logger.info(f"[ContextualOrchestrator] User message: {user_message}")
        logger.info(
            f"[ContextualOrchestrator] Current progress: {self._get_progress_summary(session)}"
        )
        logger.info("=" * 80)

        # Build contextual prompt
        prompt = self._build_prompt(session_id, user_message)

        logger.info("[ContextualOrchestrator] PROMPT TO MODEL:")
        logger.info(prompt)
        logger.info("=" * 80)

        # Generate response
        teaching_agent = TeachingAgent(self.teaching_model_getter(), self.teaching_tokenizer)
        response = teaching_agent.respond(prompt, max_new_tokens=512, temperature=0.7)

        logger.info("[ContextualOrchestrator] MODEL RESPONSE:")
        logger.info(response)
        logger.info("=" * 80)

        # Update progress based on keywords in conversation
        self._update_progress(session, user_message, response)

        return response

    def _build_prompt(self, session_id, user_message):
        """Build contextual prompt with full lesson context.

        Args:
            session_id: User session identifier
            user_message: User's message

        Returns:
            str: Full contextual prompt
        """
        session = self.sessions[session_id]
        lesson_number = session["lesson_number"]
        lesson_data = self.lesson_cache[lesson_number]

        # Get vocabulary batches
        all_vocab = session["vocabulary"]
        batch_1 = all_vocab[:3]
        batch_2 = all_vocab[3:6]

        # Format vocab
        batch_1_str = "\n".join(
            [f"- {w['arabic']} ({w['transliteration']}) - {w['english']}" for w in batch_1]
        )
        batch_2_str = "\n".join(
            [f"- {w['arabic']} ({w['transliteration']}) - {w['english']}" for w in batch_2]
        )

        # Get grammar info
        grammar_topic = session["grammar_points"][0] if session["grammar_points"] else "None"
        grammar_name = grammar_topic.replace("_", " ").title()

        # Get grammar content from RAG if available
        grammar_rule = ""
        grammar_examples = ""
        if self.content_agent and self.content_agent.rag_retriever:
            rag_results = self.content_agent.rag_retriever.retrieve_by_lesson(
                query=f"grammar {grammar_name} rule examples",
                lesson_number=lesson_number,
                top_k=3,
            )
            for result in rag_results:
                text = result.get("text", "")
                if "rule" in text.lower() or "Rule:" in text:
                    grammar_rule = text
                if "example" in text.lower() or "Examples:" in text:
                    grammar_examples = text

        # Build progress summary
        progress = self._get_progress_summary(session)

        # Check if in quiz mode
        quiz_context = ""
        current_quiz = session.get("current_quiz")
        if current_quiz:
            quiz_type = current_quiz["type"]
            current_q = current_quiz["current_q"]
            total_q = len(current_quiz["words"])
            current_word = current_quiz["words"][current_q]
            score = current_quiz["score"]

            quiz_context = f"""
**QUIZ MODE ACTIVE:**
- Type: {quiz_type}
- Question {current_q + 1} of {total_q}
- Current score: {score}/{current_q}
- Current word: {current_word['arabic']} ({current_word['transliteration']}) - {current_word['english']}

Quiz instructions:
1. Ask for translation (if arabic_to_english: "What does {current_word['arabic']} mean?", if english_to_arabic: "How do you say '{current_word['english']}' in Arabic?")
2. Student answers, you judge if correct (be flexible: accept typos like 'scool'='school', synonyms like 'instructor'='teacher')
3. Give brief feedback: "✓ Correct!" or "Not quite - it's [answer]"
4. Move to next word or end quiz if complete
"""

        # Build full contextual prompt
        prompt = f"""You are teaching Arabic to a student.

**LESSON {lesson_number}: {lesson_data['lesson_name']}**

**LESSON FLOW (5 tasks to complete):**
1. Teach Vocabulary Batch 1 (3 words) → Optional quiz
2. Teach Vocabulary Batch 2 (3 words) → Optional quiz
3. Teach Grammar topic → Quiz (required)
4. Final Exam (all vocab + grammar) → MANDATORY to complete lesson

**VOCABULARY:**

Batch 1:
{batch_1_str}

Batch 2:
{batch_2_str}

**GRAMMAR:**
Topic: {grammar_name}
{grammar_rule if grammar_rule else ""}
{grammar_examples if grammar_examples else ""}

**CURRENT PROGRESS:**
{progress}

**STUDENT BEHAVIOR:**
- If student says "vocab" or "vocabulary", teach next untaught batch
- If student says "quiz" or "test", start quiz on most recent taught content
- If student says "grammar", teach grammar topic
- If student goes off-topic, gently guide back or offer a break
- Always offer numbered options (1, 2) for navigation

**IMPORTANT REMINDERS:**
- Mention flashcards in left panel when teaching vocab batches
- Be encouraging and supportive
- Keep responses concise
- Use numbered options for navigation

{quiz_context}

**STUDENT JUST SAID:**
"{user_message}"

**YOUR RESPONSE:**
"""

        return prompt

    def _get_progress_summary(self, session):
        """Get human-readable progress summary.

        Args:
            session: Session dict

        Returns:
            str: Progress summary
        """
        lines = []
        lines.append(f"✓ Batch 1 taught: {session['vocab_batch_1_taught']}")
        lines.append(f"  - Batch 1 quiz: {session['vocab_batch_1_quiz']}")
        lines.append(f"✓ Batch 2 taught: {session['vocab_batch_2_taught']}")
        lines.append(f"  - Batch 2 quiz: {session['vocab_batch_2_quiz']}")
        lines.append(f"✓ Grammar taught: {session['grammar_taught']}")
        lines.append(f"  - Grammar quiz: {session['grammar_quiz']}")
        lines.append(f"✓ Final exam: {session['final_exam']}")

        return "\n".join(lines)

    def _update_progress(self, session, user_message, response):
        """Update progress flags based on conversation.

        Args:
            session: Session dict
            user_message: User's message
            response: Agent's response
        """
        user_lower = user_message.lower()
        response_lower = response.lower()

        # Check if teaching batch 1
        if not session["vocab_batch_1_taught"] and (
            "batch 1" in response_lower or "first batch" in response_lower
        ):
            session["vocab_batch_1_taught"] = True
            logger.info("[ContextualOrchestrator] Marked batch 1 as taught")

        # Check if teaching batch 2
        if not session["vocab_batch_2_taught"] and (
            "batch 2" in response_lower or "second batch" in response_lower
        ):
            session["vocab_batch_2_taught"] = True
            logger.info("[ContextualOrchestrator] Marked batch 2 as taught")

        # Check if starting quiz
        if ("quiz" in user_lower or "test" in user_lower) and session.get("current_quiz") is None:
            # Determine quiz type based on progress
            if session["vocab_batch_2_taught"] and session["vocab_batch_2_quiz"] == "not_started":
                self._start_quiz(session, "vocab_batch_2")
            elif session["vocab_batch_1_taught"] and session["vocab_batch_1_quiz"] == "not_started":
                self._start_quiz(session, "vocab_batch_1")
            elif session["grammar_taught"] and session["grammar_quiz"] == "not_started":
                self._start_quiz(session, "grammar")

        # Check if teaching grammar
        if not session["grammar_taught"] and (
            "grammar" in response_lower
            and ("masculine" in response_lower or "feminine" in response_lower)
        ):
            session["grammar_taught"] = True
            logger.info("[ContextualOrchestrator] Marked grammar as taught")

    def _start_quiz(self, session, quiz_type):
        """Start a quiz.

        Args:
            session: Session dict
            quiz_type: Type of quiz (vocab_batch_1, vocab_batch_2, grammar)
        """
        logger.info(f"[ContextualOrchestrator] Starting quiz: {quiz_type}")

        if quiz_type == "vocab_batch_1":
            words = session["vocabulary"][:3]
            session["vocab_batch_1_quiz"] = "in_progress"
        elif quiz_type == "vocab_batch_2":
            words = session["vocabulary"][3:6]
            session["vocab_batch_2_quiz"] = "in_progress"
        else:  # grammar
            words = []  # Grammar quiz doesn't use words
            session["grammar_quiz"] = "in_progress"

        session["current_quiz"] = {
            "type": quiz_type,
            "words": words,
            "current_q": 0,
            "answers": [],
            "score": 0,
        }
