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

        logger.info("[Orchestrator] Using template: LESSON_WELCOME")
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

        Routes to appropriate template based on session state.

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
        current_progress = session.get("current_progress", "lesson_start")

        # Log session state
        logger.info("=" * 80)
        logger.info("[Orchestrator] SESSION STATE:")
        logger.info(f"  Lesson: {lesson_number} - {lesson_data['lesson_name']}")
        logger.info(f"  Current progress: {current_progress}")
        logger.info("=" * 80)
        logger.info("[Orchestrator] USER MESSAGE:")
        logger.info(f"  {user_message}")
        logger.info("=" * 80)

        # Detect transitions from user message
        user_lower = user_message.lower()

        # Check if transitioning to vocab or grammar
        if current_progress == "lesson_start":
            if "vocab" in user_lower or "1" in user_lower:
                session["current_progress"] = "vocab_overview"
                current_progress = "vocab_overview"
                logger.info("[Orchestrator] Transitioning to vocab_overview")
            elif "grammar" in user_lower or "2" in user_lower:
                session["current_progress"] = "grammar_overview"
                current_progress = "grammar_overview"
                logger.info("[Orchestrator] Transitioning to grammar_overview")

        # Check if starting vocab quiz (user chooses quiz from vocab_overview)
        elif current_progress == "vocab_overview":
            if "quiz" in user_lower or "1" in user_lower:
                session["current_progress"] = "vocab_quiz"
                current_progress = "vocab_quiz"
                logger.info("[Orchestrator] Transitioning to vocab_quiz")

        # Check if starting grammar quiz
        elif current_progress == "grammar_overview":
            if "quiz" in user_lower or "1" in user_lower:
                session["current_progress"] = "grammar_quiz"
                current_progress = "grammar_quiz"
                logger.info("[Orchestrator] Transitioning to grammar_quiz")

        # Build prompt based on current progress stage
        prompt = self._build_stage_prompt(session_id, current_progress, user_message)

        # Store prompt for debugging
        session["last_prompt"] = prompt

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

        return response

    def _build_stage_prompt(self, session_id, stage, user_message):
        """Build prompt for current lesson stage using templates.

        Args:
            session_id: User session identifier
            stage: Current progress stage
            user_message: User's message

        Returns:
            str: Formatted prompt for the stage
        """
        from src.prompts.templates import GRAMMAR_OVERVIEW, VOCAB_OVERVIEW

        session = self.sessions[session_id]
        lesson_number = session["lesson_number"]
        lesson_data = self.lesson_cache[lesson_number]

        # Route to appropriate template based on stage
        if stage == "vocab_overview":
            logger.info("[Orchestrator] Using template: VOCAB_OVERVIEW")
            # Build vocab overview prompt
            words_formatted = "\n".join(
                [
                    f"{i+1}. {v['arabic']} ({v['transliteration']}) - {v['english']}"
                    for i, v in enumerate(lesson_data["vocabulary"])
                ]
            )
            # Calculate batches (3 words per batch)
            total_words = len(lesson_data["vocabulary"])
            batches_count = (total_words + 2) // 3  # Ceiling division

            prompt_text = VOCAB_OVERVIEW.invoke(
                {
                    "lesson_number": lesson_number,
                    "words_formatted": words_formatted,
                    "batches_count": batches_count,
                    "total_words": total_words,
                }
            ).text
            return f"{prompt_text}\n\nStudent: {user_message}\n\nTeacher:"

        elif stage == "grammar_overview":
            logger.info("[Orchestrator] Using template: GRAMMAR_OVERVIEW")
            # Build grammar overview prompt
            topics_list = "\n".join(
                [
                    f"{i+1}. {topic.replace('_', ' ').title()}"
                    for i, topic in enumerate(lesson_data["grammar_points"])
                ]
            )
            prompt_text = GRAMMAR_OVERVIEW.invoke(
                {
                    "lesson_number": lesson_number,
                    "topics_count": len(lesson_data["grammar_points"]),
                    "topics_list": topics_list,
                }
            ).text
            return f"{prompt_text}\n\nStudent: {user_message}\n\nTeacher:"

        else:
            logger.info(f"[Orchestrator] Using default minimal prompt for stage: {stage}")
            # Default: minimal context for free conversation
            vocab_list = "\n".join(
                [
                    f"{i+1}. {v['arabic']} ({v['transliteration']}) - {v['english']}"
                    for i, v in enumerate(lesson_data["vocabulary"])
                ]
            )
            grammar_topics = ", ".join(
                [topic.replace("_", " ").title() for topic in lesson_data["grammar_points"]]
            )

            return f"""Lesson {lesson_number}: {lesson_data['lesson_name']}

Vocabulary:
{vocab_list}

Grammar: {grammar_topics}

Student: {user_message}

Teacher:"""

    def _generate_vocab_batch_quiz(self, session_id, batch_number):
        """Pre-generate quiz for a vocabulary batch.

        Args:
            session_id: User session identifier
            batch_number: Batch number (1-indexed)
        """
        session = self.sessions[session_id]
        lesson_number = session["lesson_number"]

        # Get words for this batch (batches of 3)
        all_vocab = session["vocabulary"]["words"]
        batch_size = 3
        start_idx = (batch_number - 1) * batch_size
        end_idx = min(start_idx + batch_size, len(all_vocab))
        batch_words = all_vocab[start_idx:end_idx]

        if not batch_words:
            return

        # Prepare learned items for ContentAgent
        learned_items = [
            f"{v['arabic']} ({v['transliteration']}) - {v['english']}" for v in batch_words
        ]

        # Generate quiz via ContentAgent
        quiz_input = {
            "quiz_type": "vocabulary",
            "count": len(batch_words),  # One question per word
            "difficulty": "beginner",
            "learned_items": learned_items,
            "lesson_number": lesson_number,
        }

        logger.info(
            f"[Orchestrator] Generating vocab quiz for batch {batch_number} with {len(batch_words)} words"
        )
        quiz_json = self.content_agent.generate_quiz(quiz_input)

        # Store in session
        if "quizzes" not in session["vocabulary"]:
            session["vocabulary"]["quizzes"] = {}
        session["vocabulary"]["quizzes"][f"batch_{batch_number}"] = quiz_json

        logger.info(f"[Orchestrator] Stored vocab batch {batch_number} quiz in session")

    def _generate_grammar_quizzes(self, session_id):
        """Pre-generate quizzes for all grammar topics.

        Args:
            session_id: User session identifier
        """
        session = self.sessions[session_id]
        lesson_number = session["lesson_number"]
        lesson_data = self.lesson_cache[lesson_number]

        # Get all grammar topics
        grammar_topics = lesson_data["grammar_points"]

        for topic in grammar_topics:
            # Generate quiz for this topic
            quiz_input = {
                "quiz_type": "grammar",
                "count": 5,  # 5 questions per topic
                "difficulty": "beginner",
                "learned_items": [topic.replace("_", " ")],
                "lesson_number": lesson_number,
            }

            logger.info(f"[Orchestrator] Generating grammar quiz for topic: {topic}")
            quiz_json = self.content_agent.generate_quiz(quiz_input)

            # Store in session
            if "quizzes" not in session["grammar"]:
                session["grammar"]["quizzes"] = {}
            session["grammar"]["quizzes"][topic] = quiz_json

            logger.info(f"[Orchestrator] Stored grammar quiz for {topic} in session")

    def get_vocab_batch_quiz(self, session_id, batch_number):
        """Get pre-generated vocabulary batch quiz.

        Args:
            session_id: User session identifier
            batch_number: Batch number (1-indexed)

        Returns:
            str: Quiz JSON or None if not found
        """
        session = self.sessions.get(session_id)
        if not session:
            return None

        quizzes = session.get("vocabulary", {}).get("quizzes", {})
        quiz = quizzes.get(f"batch_{batch_number}")

        if not quiz:
            # Generate on demand if not pre-generated
            logger.info(
                f"[Orchestrator] Quiz not pre-generated, generating now for batch {batch_number}"
            )
            self._generate_vocab_batch_quiz(session_id, batch_number)
            quiz = session.get("vocabulary", {}).get("quizzes", {}).get(f"batch_{batch_number}")

        return quiz

    def get_grammar_quiz(self, session_id, topic):
        """Get pre-generated grammar topic quiz.

        Args:
            session_id: User session identifier
            topic: Grammar topic name

        Returns:
            str: Quiz JSON or None if not found
        """
        session = self.sessions.get(session_id)
        if not session:
            return None

        quizzes = session.get("grammar", {}).get("quizzes", {})
        quiz = quizzes.get(topic)

        if not quiz:
            # Generate on demand if not pre-generated
            logger.info(f"[Orchestrator] Quiz not pre-generated, generating now for topic {topic}")
            lesson_number = session["lesson_number"]
            quiz_input = {
                "quiz_type": "grammar",
                "count": 5,
                "difficulty": "beginner",
                "learned_items": [topic.replace("_", " ")],
                "lesson_number": lesson_number,
            }
            quiz = self.content_agent.generate_quiz(quiz_input)
            if "quizzes" not in session["grammar"]:
                session["grammar"]["quizzes"] = {}
            session["grammar"]["quizzes"][topic] = quiz

        return quiz
