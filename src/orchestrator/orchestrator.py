"""Orchestrator for managing lesson flow and agent interactions."""

import logging

from src.agents.teaching_agent import TeachingAgent
from src.prompts.templates import LESSON_WELCOME

logger = logging.getLogger(__name__)


class Orchestrator:
    """Manages lesson cache, session state, and agent interactions."""

    def __init__(
        self,
        lesson_cache,
        sessions,
        teaching_model_getter,
        teaching_tokenizer,
        content_agent=None,
    ):
        """Initialize orchestrator with shared resources.

        Args:
            lesson_cache: Dict of lesson_number -> lesson_data
            sessions: Dict of session_id -> session_state
            teaching_model_getter: Callable that returns the teaching model (for lazy loading)
            teaching_tokenizer: The tokenizer for the teaching model
            content_agent: ContentAgent instance for RAG-based content retrieval
        """
        self.lesson_cache = lesson_cache
        self.sessions = sessions
        self.teaching_model_getter = teaching_model_getter
        self.teaching_tokenizer = teaching_tokenizer
        self.content_agent = content_agent

    def start_lesson(self, session_id, lesson_number):
        """Start a lesson - get content from cache, build prompt, generate welcome.

        Args:
            session_id: User session identifier
            lesson_number: Lesson number to start (1-10)

        Returns:
            str: Welcome message from teaching agent
        """
        # Check if lesson exists in cache
        if lesson_number not in self.lesson_cache:
            return f"Error: Lesson {lesson_number} not found in cache."

        # Get lesson data from cache
        lesson_data = self.lesson_cache[lesson_number]

        # Initialize session with structured vocabulary and grammar tracking
        if session_id not in self.sessions:
            self.sessions[session_id] = {}

        # Build grammar topics structure
        grammar_topics = {}
        for topic in lesson_data["grammar_points"]:
            grammar_topics[topic] = {"taught": False, "quiz_results": []}

        self.sessions[session_id].update(
            {
                "lesson_number": lesson_number,
                "lesson_name": lesson_data["lesson_name"],
                "vocabulary": {
                    "words": lesson_data["vocabulary"],
                    "current_batch": 1,
                    "quizzed_words": [],
                },
                "grammar": {
                    "topics": grammar_topics,
                    "sections": lesson_data["grammar_sections"],  # Keep raw content
                },
                "current_progress": "lesson_start",
                "status": "active",
            }
        )

        # Build full vocabulary list for prompt
        vocab_list = "\n".join(
            [
                f"{i+1}. {v['arabic']} ({v['transliteration']}) - {v['english']}"
                for i, v in enumerate(lesson_data["vocabulary"])
            ]
        )

        # Format grammar topics (replace underscores with spaces, title case)
        grammar_topics_formatted = ", ".join(
            [topic.replace("_", " ").title() for topic in lesson_data["grammar_points"]]
        )

        prompt_text = LESSON_WELCOME.invoke(
            {
                "lesson_number": lesson_number,
                "total_words": len(lesson_data["vocabulary"]),
                "vocabulary_list": vocab_list,
                "topics_count": len(lesson_data["grammar_points"]),
                "grammar_topics": grammar_topics_formatted,
            }
        ).text

        # Store prompt for debugging
        self.sessions[session_id]["last_prompt"] = prompt_text

        logger.info(
            f"[Orchestrator] Sending prompt to teaching agent (length: {len(prompt_text)} chars)"
        )
        logger.debug(f"[Orchestrator] Prompt:\n{prompt_text}")

        # Generate welcome message using teaching agent (lazy load model)
        teaching_agent = TeachingAgent(self.teaching_model_getter(), self.teaching_tokenizer)
        response = teaching_agent.respond(prompt_text, max_new_tokens=256, temperature=0.7)

        logger.info(
            f"[Orchestrator] Received response from teaching agent (length: {len(response)} chars)"
        )
        logger.debug(f"[Orchestrator] Response:\n{response}")

        return response

    def handle_message(self, session_id, user_message):
        """Handle user message during active lesson.

        Args:
            session_id: User session identifier
            user_message: User's message text

        Returns:
            str: Response from appropriate agent
        """
        # Get session state
        session = self.sessions.get(session_id)
        if not session or session.get("status") != "active":
            return "No active lesson. Please start a lesson first."

        # Get lesson data
        lesson_number = session.get("lesson_number")
        if lesson_number not in self.lesson_cache:
            return f"Error: Lesson {lesson_number} not found."

        lesson_data = self.lesson_cache[lesson_number]

        # Log session state
        logger.info("=" * 80)
        logger.info("[Orchestrator] SESSION STATE:")
        logger.info(f"  Lesson: {lesson_number} - {lesson_data['lesson_name']}")
        learned_words = session.get("vocabulary", {}).get("words", [])[:6]
        logger.info(f"  Learned words: {len(learned_words)}")
        logger.info(f"  Current progress: {session.get('current_progress')}")
        logger.info("=" * 80)
        logger.info("[Orchestrator] USER MESSAGE:")
        logger.info(f"  {user_message}")
        logger.info("=" * 80)

        # Build minimal context
        vocab_list = "\n".join(
            [
                f"{i+1}. {v['arabic']} ({v['transliteration']}) - {v['english']}"
                for i, v in enumerate(learned_words)
            ]
        )

        grammar_topics = ", ".join(lesson_data.get("grammar_points", []))

        # Minimal prompt - let model handle naturally
        prompt = f"""Lesson {lesson_number}: {lesson_data['lesson_name']}

Vocabulary:
{vocab_list}

Grammar: {grammar_topics}

Student: {user_message}

Teacher:"""

        # Store prompt for debugging
        self.sessions[session_id]["last_prompt"] = prompt

        logger.info("[Orchestrator] PROMPT TO MODEL:")
        logger.info(prompt)
        logger.info("=" * 80)

        # Generate response using teaching agent
        teaching_agent = TeachingAgent(self.teaching_model_getter(), self.teaching_tokenizer)
        response = teaching_agent.respond(prompt, max_new_tokens=512, temperature=0.7)

        logger.info("=" * 80)
        logger.info("[Orchestrator] MODEL RESPONSE:")
        logger.info(response)
        logger.info("=" * 80)

        # Detect if model needs other agents
        # For now, just return response - model handles everything
        # Future: detect [CONTENT:...] or [GRADE:...] signals

        return response
