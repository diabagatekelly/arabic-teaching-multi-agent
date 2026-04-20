"""Orchestrator for managing lesson flow and agent interactions."""

import logging

from src.agents.teaching_agent import TeachingAgent
from src.prompts.templates import LESSON_WELCOME

logger = logging.getLogger(__name__)


class Orchestrator:
    """Manages lesson cache, session state, and agent interactions."""

    def __init__(self, lesson_cache, sessions, model_getter, tokenizer):
        """Initialize orchestrator with shared resources.

        Args:
            lesson_cache: Dict of lesson_number -> lesson_data
            sessions: Dict of session_id -> session_state
            model_getter: Callable that returns the teaching model (for lazy loading)
            tokenizer: The tokenizer for the teaching model
        """
        self.lesson_cache = lesson_cache
        self.sessions = sessions
        self.model_getter = model_getter
        self.tokenizer = tokenizer

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
        teaching_agent = TeachingAgent(self.model_getter(), self.tokenizer)
        response = teaching_agent.respond(prompt_text, max_new_tokens=256, temperature=0.7)

        logger.info(
            f"[Orchestrator] Received response from teaching agent (length: {len(response)} chars)"
        )
        logger.debug(f"[Orchestrator] Response:\n{response}")

        return response
