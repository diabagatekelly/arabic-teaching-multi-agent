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

        # Build lesson_start prompt using template
        vocab_preview = ", ".join([v["arabic"] for v in lesson_data["vocabulary"][:3]])
        if len(lesson_data["vocabulary"]) > 3:
            vocab_preview += f" ... ({len(lesson_data['vocabulary']) - 3} more)"

        prompt_text = LESSON_WELCOME.invoke(
            {
                "lesson_number": lesson_number,
                "total_words": len(lesson_data["vocabulary"]),
                "topics_preview": vocab_preview,
                "topics_count": len(lesson_data["grammar_points"]),
                "grammar_topics": ", ".join(lesson_data["grammar_points"]),
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

        # Build context from session state
        learned_words = session.get("vocabulary", {}).get("words", [])[:6]  # Current batch
        vocab_list = "\n".join(
            [
                f"{i+1}. {v['arabic']} ({v['transliteration']}) - {v['english']}"
                for i, v in enumerate(learned_words)
            ]
        )

        grammar_topics = ", ".join(lesson_data.get("grammar_points", []))

        # Build prompt with lesson context
        prompt = f"""You are teaching Lesson {lesson_number}: {lesson_data['lesson_name']}.

Current vocabulary being taught:
{vocab_list}

Grammar topics: {grammar_topics}

Student message: {user_message}

Respond as their Arabic teacher. Keep responses focused on the current lesson content."""

        # Store prompt for debugging
        self.sessions[session_id]["last_prompt"] = prompt

        logger.info(f"[Orchestrator] Handling message for lesson {lesson_number}")
        logger.debug(f"[Orchestrator] Prompt:\n{prompt}")

        # Generate response using teaching agent
        teaching_agent = TeachingAgent(self.teaching_model_getter(), self.teaching_tokenizer)
        response = teaching_agent.respond(prompt, max_new_tokens=256, temperature=0.7)

        logger.info(f"[Orchestrator] Response length: {len(response)} chars")

        return response
