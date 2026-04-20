"""Orchestrator for managing lesson flow and agent interactions."""

import logging
import threading

from src.agents.teaching_agent import TeachingAgent
from src.prompts.templates import (
    FEEDBACK_GRAMMAR_CORRECT,
    FEEDBACK_GRAMMAR_INCORRECT,
    FEEDBACK_VOCAB_CORRECT,
    FEEDBACK_VOCAB_INCORRECT,
    GRAMMAR_EXPLANATION,
    GRAMMAR_OVERVIEW,
    GRAMMAR_QUIZ_QUESTION,
    GRAMMAR_TOPIC_SUMMARY,
    LESSON_WELCOME,
    PROGRESS_REPORT,
    VOCAB_BATCH_INTRO,
    VOCAB_BATCH_SUMMARY,
    VOCAB_QUIZ_QUESTION,
)

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
        response = teaching_agent.respond(prompt_text, max_new_tokens=256, temperature=0.85)

        logger.info(
            f"[Orchestrator] Received response from teaching agent (length: {len(response)} chars)"
        )
        logger.debug(f"[Orchestrator] Response:\n{response}")

        # Start background generation of grammar quizzes
        if self.content_agent:
            threading.Thread(
                target=self._pregenerate_grammar_quizzes,
                args=(session_id, lesson_number, lesson_data),
                daemon=True,
            ).start()
            logger.info("[Orchestrator] Started background grammar quiz generation")

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
            return (
                "Oops, you haven't picked a lesson yet. Please start a lesson from the right panel."
            )

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

        # =====================================================================
        # STATE MACHINE: Detect user intent and transition to next state
        # =====================================================================

        # State transition map: (current_state, user_intent) -> next_state
        TRANSITIONS = {
            "lesson_start": {
                "vocab": "vocab_batch_intro",
                "grammar": "grammar_explanation",
            },
            "vocab_batch_intro": {
                "quiz": "vocab_quiz",
                "next_batch": "vocab_batch_intro",  # increment batch
                "grammar": "grammar_explanation",
            },
            "vocab_quiz": {
                "answer": "vocab_quiz",  # stay in quiz, process answer, show next question
                # No escape routes - must complete quiz
            },
            "vocab_quiz_complete": {
                "next_batch": "vocab_batch_intro",
                "grammar": "grammar_explanation",
                "vocab": "vocab_batch_intro",
                "review": "vocab_batch_intro",
            },
            "grammar_explanation": {
                "quiz": "grammar_quiz",
                "review": "grammar_explanation",
                "vocab": "vocab_batch_intro",
            },
            "grammar_quiz": {
                "answer": "grammar_quiz",  # stay in quiz, process answer, show next question
                "vocab": "vocab_batch_intro",
                "review": "grammar_explanation",
            },
            "grammar_quiz_complete": {
                "vocab": "vocab_batch_intro",
                "grammar": "grammar_explanation",
                "review": "grammar_explanation",
                "final_exam": "final_exam",
            },
            "final_exam": {
                "answer": "final_exam",  # stay in exam, process answer
            },
            "final_exam_complete": {
                "vocab": "vocab_batch_intro",
                "grammar": "grammar_explanation",
            },
        }

        user_lower = user_message.lower()
        logger.info("[Orchestrator] ===== STATE MACHINE =====")
        logger.info(f"[Orchestrator] Current state: {current_progress}")
        logger.info(f"[Orchestrator] User message: {user_message}")

        # Detect user intent from message
        detected_intent = None

        # Check for vocab intent
        if "vocab" in user_lower or "vocabulary" in user_lower:
            detected_intent = "vocab"
            logger.info("[Orchestrator] Detected intent: vocab")

        # Check for grammar intent
        elif "grammar" in user_lower:
            detected_intent = "grammar"
            logger.info("[Orchestrator] Detected intent: grammar")

        # Check for final exam intent
        elif "final" in user_lower or "exam" in user_lower:
            detected_intent = "final_exam"
            logger.info("[Orchestrator] Detected intent: final_exam")

        # Check for quiz intent
        elif "quiz" in user_lower or "test" in user_lower:
            detected_intent = "quiz"
            logger.info("[Orchestrator] Detected intent: quiz")

        # Check for review intent
        elif "review" in user_lower or "again" in user_lower:
            detected_intent = "review"
            logger.info("[Orchestrator] Detected intent: review")

        # Check for next batch intent
        elif "next" in user_lower or "batch" in user_lower:
            detected_intent = "next_batch"
            logger.info("[Orchestrator] Detected intent: next_batch")

        # Fallback: check for numbered options
        elif user_message.strip() == "1":
            # Option 1 is usually the primary action (quiz or first topic)
            if current_progress == "lesson_start":
                detected_intent = "vocab"
                logger.info("[Orchestrator] Detected intent from '1': vocab")
            elif current_progress in ["vocab_batch_intro", "grammar_explanation"]:
                detected_intent = "quiz"
                logger.info("[Orchestrator] Detected intent from '1': quiz")
            elif current_progress == "vocab_quiz_complete":
                detected_intent = "next_batch"
                logger.info("[Orchestrator] Detected intent from '1': next_batch")
            elif current_progress == "grammar_quiz_complete":
                detected_intent = "vocab"
                logger.info("[Orchestrator] Detected intent from '1': vocab")
        elif user_message.strip() == "2":
            # Option 2 is usually the secondary action
            if current_progress == "lesson_start":
                detected_intent = "grammar"
                logger.info("[Orchestrator] Detected intent from '2': grammar")
            elif current_progress == "vocab_batch_intro":
                detected_intent = "next_batch"
                logger.info("[Orchestrator] Detected intent from '2': next_batch")
            elif current_progress == "grammar_explanation":
                detected_intent = "review"
                logger.info("[Orchestrator] Detected intent from '2': review")
            elif current_progress == "vocab_quiz_complete":
                detected_intent = "review"
                logger.info("[Orchestrator] Detected intent from '2': review")
            elif current_progress == "grammar_quiz_complete":
                detected_intent = "grammar"
                logger.info("[Orchestrator] Detected intent from '2': grammar")
        elif user_message.strip() == "3":
            # Option 3 where applicable
            if current_progress == "vocab_quiz_complete":
                # Template says "Skip to final test" but final_exam not in TRANSITIONS
                # Map to grammar as best alternative
                detected_intent = "grammar"
                logger.info(
                    "[Orchestrator] Detected intent from '3': grammar (skip to grammar section)"
                )
            elif current_progress == "grammar_quiz_complete":
                # Template says "See lesson progress" - not a real transition
                # No good mapping, just log warning
                logger.warning("[Orchestrator] Option 3 'See lesson progress' not implemented")
                detected_intent = None

        # Default intent based on current state
        else:
            # In quiz/exam state, any message is an answer
            if current_progress in ["vocab_quiz", "grammar_quiz", "final_exam"]:
                detected_intent = "answer"
                logger.info(f"[Orchestrator] Default intent in {current_progress}: answer")
            # Check for affirmative (default to primary action)
            else:
                affirmative_keywords = [
                    "yes",
                    "yeah",
                    "yep",
                    "ok",
                    "okay",
                    "sure",
                    "let's",
                    "go",
                    "start",
                    "ready",
                ]
                is_affirmative = any(keyword in user_lower for keyword in affirmative_keywords)
                if is_affirmative:
                    # Default to primary action based on current state
                    if current_progress == "lesson_start":
                        detected_intent = "vocab"
                        logger.info(
                            "[Orchestrator] Detected intent from affirmative: vocab (default)"
                        )
                    elif current_progress in ["vocab_batch_intro", "grammar_explanation"]:
                        detected_intent = "quiz"
                        logger.info("[Orchestrator] Detected intent from affirmative: quiz")

        logger.info(f"[Orchestrator] Final detected intent: {detected_intent}")

        # Apply state transition if we have a valid intent
        if detected_intent and current_progress in TRANSITIONS:
            valid_intents = TRANSITIONS[current_progress]
            logger.info(
                f"[Orchestrator] Valid intents for state '{current_progress}': {list(valid_intents.keys())}"
            )

            if detected_intent in valid_intents:
                new_state = valid_intents[detected_intent]
                logger.info(f"[Orchestrator] Transitioning: {current_progress} -> {new_state}")

                # Handle special actions before transition
                if detected_intent == "next_batch":
                    current_batch = session.get("vocabulary", {}).get("current_batch", 1)
                    all_vocab = lesson_data.get("vocabulary", [])
                    total_batches = (len(all_vocab) + 2) // 3  # Ceiling division

                    if current_batch >= total_batches:
                        # Already at last batch - don't increment, redirect to grammar
                        logger.info(
                            f"[Orchestrator] Already at last batch ({current_batch}/{total_batches}), redirecting to grammar"
                        )
                        detected_intent = "grammar"
                        new_state = "grammar_explanation"
                    else:
                        # Increment to next batch
                        session["vocabulary"]["current_batch"] = current_batch + 1
                        logger.info(f"[Orchestrator] Incremented batch to {current_batch + 1}")

                # Handle answer intent in vocab_quiz
                elif detected_intent == "answer" and current_progress == "vocab_quiz":
                    import json

                    from src.agents.grading_agent import GradingAgent

                    logger.info("[Orchestrator] Processing vocab quiz answer")
                    quiz_state = session["vocabulary"]["quiz_state"]
                    current_q = quiz_state["current_question"]
                    current_word = quiz_state["words"][current_q]
                    logger.info(
                        f"[Orchestrator] Grading answer for question {current_q}: {current_word['arabic']} = {current_word['english']}"
                    )

                    # Grade the answer using grading agent
                    grading_agent = GradingAgent(
                        model=self.teaching_model_getter(),
                        tokenizer=self.teaching_tokenizer,
                        max_new_tokens=50,
                    )

                    # All questions are arabic_to_english for demo purposes
                    question_type = "arabic_to_english"
                    word_display = current_word["arabic"]
                    correct_answer = current_word["english"]

                    logger.info(f"[Orchestrator] Question type: {question_type}")

                    # Grade the answer (returns JSON string)
                    grading_result = grading_agent.grade_vocab(
                        {
                            "word": word_display,
                            "student_answer": user_message,
                            "correct_answer": correct_answer,
                        }
                    )

                    logger.info(f"[Orchestrator] Grading result (raw): {grading_result}")

                    # Parse JSON response - extract just the JSON part (model may add extra text)
                    import re

                    try:
                        # Try to find JSON object in response
                        json_match = re.search(
                            r'\{[^}]*"correct"\s*:\s*(true|false)[^}]*\}', grading_result
                        )
                        if json_match:
                            json_str = json_match.group(0)
                            result_dict = json.loads(json_str)
                            is_correct = result_dict.get("correct", False)
                        else:
                            logger.error(
                                f"[Orchestrator] No JSON found in grading result: {grading_result}"
                            )
                            is_correct = False
                    except json.JSONDecodeError:
                        logger.error(
                            f"[Orchestrator] Failed to parse grading result: {grading_result}"
                        )
                        is_correct = False

                    logger.info(f"[Orchestrator] Grading result (parsed): {is_correct}")

                    # Update quiz state
                    quiz_state["answers"].append(
                        {
                            "word": current_word,
                            "student_answer": user_message,
                            "correct": is_correct,
                        }
                    )

                    if is_correct:
                        quiz_state["score"] += 1

                    # Reset feedback_shown so feedback will be displayed
                    quiz_state["feedback_shown"] = False

                    # Move to next question or complete quiz
                    quiz_state["current_question"] += 1

                    if quiz_state["current_question"] >= quiz_state["total_questions"]:
                        # Quiz complete
                        logger.info(
                            "[Orchestrator] Quiz complete, transitioning to vocab_quiz_complete"
                        )
                        new_state = "vocab_quiz_complete"
                    else:
                        # Stay in quiz for next question
                        logger.info(
                            f"[Orchestrator] Moving to question {quiz_state['current_question'] + 1}"
                        )
                        new_state = "vocab_quiz"

                # Handle answer intent in grammar_quiz
                elif detected_intent == "answer" and current_progress == "grammar_quiz":
                    import json

                    from src.agents.grading_agent import GradingAgent

                    logger.info("[Orchestrator] Processing grammar quiz answer")
                    quiz_state = session["grammar"]["grammar_quiz_state"]
                    current_q = quiz_state["current_question"]
                    current_question = quiz_state["questions"][current_q]
                    logger.info(
                        f"[Orchestrator] Grading answer for question {current_q}: {current_question['question']}"
                    )
                    logger.info(f"[Orchestrator] Correct answer: {current_question['answer']}")

                    # Grade the answer using grading agent
                    grading_agent = GradingAgent(
                        model=self.teaching_model_getter(),
                        tokenizer=self.teaching_tokenizer,
                        max_new_tokens=50,
                    )

                    # Grade the answer (returns JSON string)
                    grading_result = grading_agent.grade_grammar_quiz(
                        {
                            "question": current_question["question"],
                            "student_answer": user_message,
                            "correct_answer": current_question["answer"],
                        }
                    )

                    logger.info(f"[Orchestrator] Grammar grading result (raw): {grading_result}")

                    # Parse JSON response - extract just the JSON part
                    import re

                    try:
                        json_match = re.search(
                            r'\{[^}]*"correct"\s*:\s*(true|false)[^}]*\}', grading_result
                        )
                        if json_match:
                            json_str = json_match.group(0)
                            result_dict = json.loads(json_str)
                            is_correct = result_dict.get("correct", False)
                        else:
                            logger.error(
                                f"[Orchestrator] No JSON found in grading result: {grading_result}"
                            )
                            is_correct = False
                    except json.JSONDecodeError:
                        logger.error(
                            f"[Orchestrator] Failed to parse grading result: {grading_result}"
                        )
                        is_correct = False

                    logger.info(f"[Orchestrator] Grammar grading result (parsed): {is_correct}")

                    # Update quiz state
                    quiz_state["answers"].append(
                        {
                            "question": current_question,
                            "student_answer": user_message,
                            "correct": is_correct,
                        }
                    )

                    if is_correct:
                        quiz_state["score"] += 1

                    # Reset feedback_shown so feedback will be displayed
                    quiz_state["feedback_shown"] = False

                    # Move to next question or complete quiz
                    quiz_state["current_question"] += 1

                    if quiz_state["current_question"] >= quiz_state["total_questions"]:
                        # Quiz complete
                        logger.info(
                            "[Orchestrator] Grammar quiz complete, transitioning to grammar_quiz_complete"
                        )
                        new_state = "grammar_quiz_complete"
                    else:
                        # Stay in quiz for next question
                        logger.info(
                            f"[Orchestrator] Moving to grammar question {quiz_state['current_question'] + 1}"
                        )
                        new_state = "grammar_quiz"

                # Update state
                session["current_progress"] = new_state
                current_progress = new_state
                logger.info(f"[Orchestrator] State updated to: {current_progress}")
            else:
                logger.warning(
                    f"[Orchestrator] Intent '{detected_intent}' not valid for state '{current_progress}'"
                )
        else:
            logger.warning(
                f"[Orchestrator] No valid transition - state: {current_progress}, intent: {detected_intent}"
            )

            # Handle off-topic/unrecognized input with progress report
            if detected_intent is None or (
                current_progress in TRANSITIONS
                and detected_intent not in TRANSITIONS[current_progress]
            ):
                logger.info(
                    "[Orchestrator] No clear intent detected - showing progress report with all options"
                )

                # Build progress summary
                vocab_progress_lines = []
                grammar_progress_lines = []

                # Vocabulary progress
                vocab_state = session.get("vocabulary", {})
                all_vocab = vocab_state.get("words", [])
                current_batch = vocab_state.get("current_batch", 1)
                total_batches = (len(all_vocab) + 2) // 3  # Ceiling division

                for batch_num in range(1, total_batches + 1):
                    batch_start = (batch_num - 1) * 3
                    batch_end = min(batch_start + 3, len(all_vocab))
                    batch_words = all_vocab[batch_start:batch_end]

                    if batch_num < current_batch:
                        # Completed batch
                        vocab_progress_lines.append(
                            f"✓ Batch {batch_num}: {len(batch_words)} words completed"
                        )
                    elif batch_num == current_batch:
                        # Current batch
                        vocab_progress_lines.append(
                            f"→ Batch {batch_num}: {len(batch_words)} words (in progress)"
                        )
                    else:
                        # Not started
                        vocab_progress_lines.append(
                            f"○ Batch {batch_num}: {len(batch_words)} words (not started)"
                        )

                vocab_progress = "\n".join(vocab_progress_lines)

                # Grammar progress
                grammar_topics = session.get("grammar", {}).get("topics", {})
                lesson_data = self.lesson_cache.get(session.get("lesson_number"))
                if lesson_data:
                    for topic_name in lesson_data.get("grammar_points", []):
                        topic_state = grammar_topics.get(topic_name, {})
                        if topic_state.get("taught", False):
                            score = topic_state.get("quiz_score", "N/A")
                            grammar_progress_lines.append(
                                f"✓ {topic_name}: Completed (Score: {score})"
                            )
                        else:
                            grammar_progress_lines.append(f"○ {topic_name}: Not started")

                grammar_progress = (
                    "\n".join(grammar_progress_lines)
                    if grammar_progress_lines
                    else "No grammar topics available"
                )

                # Generate progress report using template
                prompt_text = PROGRESS_REPORT.invoke(
                    {
                        "lesson_number": session.get("lesson_number", 1),
                        "vocab_progress": vocab_progress,
                        "grammar_progress": grammar_progress,
                    }
                ).text

                teaching_agent = TeachingAgent(
                    self.teaching_model_getter(), self.teaching_tokenizer
                )
                return teaching_agent.respond(prompt_text, max_new_tokens=300, temperature=0.75)

        logger.info("[Orchestrator] ===== END STATE MACHINE =====")

        # =====================================================================
        # OLD IF-ELSE LOGIC (COMMENTED OUT - REPLACED BY STATE MACHINE ABOVE)
        # =====================================================================
        # # Detect transitions from user message
        # user_lower = user_message.lower()
        #
        # # Helper: detect affirmative responses
        # affirmative_keywords = ["yes", "yeah", "yep", "ok", "okay", "sure", "let's", "go", "start"]
        # is_affirmative = any(keyword in user_lower for keyword in affirmative_keywords)
        #
        # # Check if transitioning to vocab or grammar
        # if current_progress == "lesson_start":
        #     if "vocab" in user_lower or "1" in user_lower:
        #         session["current_progress"] = "vocab_batch_intro"
        #         current_progress = "vocab_batch_intro"
        #         logger.info("[Orchestrator] Transitioning to vocab_batch_intro")
        #     elif "grammar" in user_lower or "2" in user_lower:
        #         session["current_progress"] = "grammar_explanation"
        #         current_progress = "grammar_explanation"
        #         logger.info("[Orchestrator] Transitioning to grammar_explanation")
        #
        # # Check if starting vocab quiz (user chooses quiz from vocab_batch_intro)
        # elif current_progress == "vocab_batch_intro":
        #     # Explicit quiz request or option 1 or affirmative for primary action
        #     if "quiz" in user_lower or "test" in user_lower or "1" in user_lower or (is_affirmative and "2" not in user_lower):
        #         session["current_progress"] = "vocab_quiz"
        #         current_progress = "vocab_quiz"
        #         logger.info("[Orchestrator] Transitioning to vocab_quiz")
        #     # Next batch request or option 2
        #     elif "next" in user_lower or "2" in user_lower or "batch" in user_lower:
        #         # Move to next batch
        #         current_batch = session.get("vocabulary", {}).get("current_batch", 1)
        #         session["vocabulary"]["current_batch"] = current_batch + 1
        #         logger.info(f"[Orchestrator] Moving to batch {current_batch + 1}")
        #
        # # Check if starting grammar quiz (from grammar_explanation)
        # elif current_progress == "grammar_explanation":
        #     # Explicit quiz request or option 1 or affirmative for primary action
        #     if "quiz" in user_lower or "test" in user_lower or "1" in user_lower or (is_affirmative and "2" not in user_lower):
        #         session["current_progress"] = "grammar_quiz"
        #         current_progress = "grammar_quiz"
        #         logger.info("[Orchestrator] Transitioning to grammar_quiz")
        #     # Review request or option 2
        #     elif "review" in user_lower or "2" in user_lower or "again" in user_lower:
        #         # Stay in grammar_explanation, will re-explain
        #         logger.info("[Orchestrator] User requested review, staying in grammar_explanation")

        # Build prompt based on current progress stage
        # Pass detected_intent to determine if user_message should be included
        prompt_result = self._build_stage_prompt(
            session_id, current_progress, user_message, detected_intent
        )

        # Check if result is a dict with skip_model flag (direct response)
        if isinstance(prompt_result, dict) and prompt_result.get("skip_model"):
            logger.info("[Orchestrator] Skipping model - returning direct response")
            response = prompt_result["response"]
        else:
            # Normal flow: use model to generate response
            prompt = (
                prompt_result if isinstance(prompt_result, str) else prompt_result.get("prompt", "")
            )

            # Store prompt for debugging
            session["last_prompt"] = prompt

            logger.info("[Orchestrator] PROMPT TO MODEL:")
            logger.info(prompt)
            logger.info("=" * 80)

            # Generate response using teaching agent
            teaching_agent = TeachingAgent(self.teaching_model_getter(), self.teaching_tokenizer)
            response = teaching_agent.respond(prompt, max_new_tokens=512, temperature=0.85)

        logger.info("=" * 80)
        logger.info("[Orchestrator] MODEL RESPONSE:")
        logger.info(response)
        logger.info("=" * 80)

        return response

    def _build_stage_prompt(self, session_id, stage, user_message, detected_intent=None):
        """Build prompt for current lesson stage using templates.

        Args:
            session_id: User session identifier
            stage: Current progress stage
            user_message: User's message
            detected_intent: Detected user intent (vocab, grammar, quiz, answer, etc.)

        Returns:
            str: Formatted prompt for the stage
        """

        session = self.sessions[session_id]
        lesson_number = session["lesson_number"]
        lesson_data = self.lesson_cache[lesson_number]

        # Determine if we should include user_message in prompt
        # Omit for navigation intents, include for answers or conversational messages
        navigation_intents = {"vocab", "grammar", "quiz", "next_batch", "review", "final_exam"}
        include_user_message = detected_intent not in navigation_intents or detected_intent is None

        # Route to appropriate template based on stage
        if stage == "vocab_batch_intro":
            logger.info("[Orchestrator] Using template: VOCAB_BATCH_INTRO")
            # Get current batch
            current_batch = session.get("vocabulary", {}).get("current_batch", 1)
            all_vocab = lesson_data["vocabulary"]

            # Get words for current batch (3 per batch)
            batch_size = 3
            start_idx = (current_batch - 1) * batch_size
            end_idx = min(start_idx + batch_size, len(all_vocab))
            batch_words = all_vocab[start_idx:end_idx]

            # Calculate total batches
            total_batches = (len(all_vocab) + 2) // 3  # Ceiling division

            # Format words for this batch
            words_formatted = "\n".join(
                [
                    f"{i+1}. {w['arabic']} ({w['transliteration']}) - {w['english']}"
                    for i, w in enumerate(batch_words)
                ]
            )

            # Build previous performance context
            previous_performance = ""
            if current_batch > 1:
                # Check if previous batch has quiz results
                vocab_state = session.get("vocabulary", {})
                if "previous_quiz_score" in vocab_state:
                    prev_score = vocab_state["previous_quiz_score"]
                    previous_performance = f"Previous Batch Score: {prev_score}"

            prompt_text = VOCAB_BATCH_INTRO.invoke(
                {
                    "lesson_number": lesson_number,
                    "batch_number": current_batch,
                    "total_batches": total_batches,
                    "words": words_formatted,
                    "previous_performance": previous_performance,
                }
            ).text

            if include_user_message:
                return f"{prompt_text}\n\nStudent: {user_message}\n\nTeacher:"
            else:
                return f"{prompt_text}\n\nTeacher:"

        elif stage == "vocab_quiz":
            logger.info("[Orchestrator] Using template: VOCAB_QUIZ_QUESTION or FEEDBACK")
            # Initialize quiz state if not exists
            if "quiz_state" not in session["vocabulary"]:
                current_batch = session.get("vocabulary", {}).get("current_batch", 1)
                all_vocab = lesson_data["vocabulary"]

                # Get words for current batch (3 per batch)
                batch_size = 3
                start_idx = (current_batch - 1) * batch_size
                end_idx = min(start_idx + batch_size, len(all_vocab))
                batch_words = all_vocab[start_idx:end_idx]

                session["vocabulary"]["quiz_state"] = {
                    "current_question": 0,
                    "total_questions": len(batch_words),
                    "words": batch_words,
                    "answers": [],
                    "score": 0,
                    "feedback_shown": False,
                    "batch_number": current_batch,  # Store which batch this quiz is for
                }
                logger.info(f"[Orchestrator] Initialized quiz_state with {len(batch_words)} words")

            quiz_state = session["vocabulary"]["quiz_state"]
            current_q = quiz_state["current_question"]

            logger.info(
                f"[Orchestrator] Vocab quiz state: current_q={current_q}, answers={len(quiz_state['answers'])}, total={quiz_state['total_questions']}"
            )

            # Check if we just graded an answer and haven't shown feedback yet
            if (
                quiz_state["answers"]
                and len(quiz_state["answers"]) == current_q
                and not quiz_state.get("feedback_shown", False)
            ):
                # Show feedback for the last answer
                last_answer = quiz_state["answers"][-1]
                word = last_answer["word"]
                is_correct = last_answer["correct"]

                logger.info(
                    f"[Orchestrator] Showing vocab feedback for question {current_q - 1} - correct: {is_correct}"
                )
                logger.info(f"[Orchestrator] Word was: {word['arabic']} = {word['english']}")
                logger.info(f"[Orchestrator] Student answered: {last_answer['student_answer']}")

                # Calculate current score for feedback (current_q is already the number of questions answered)
                current_score = f"{quiz_state['score']}/{len(quiz_state['answers'])}"

                if is_correct:
                    prompt_text = FEEDBACK_VOCAB_CORRECT.invoke(
                        {
                            "word_arabic": word["arabic"],
                            "word_transliteration": word["transliteration"],
                            "english": word["english"],
                            "current_score": current_score,
                        }
                    ).text
                else:
                    prompt_text = FEEDBACK_VOCAB_INCORRECT.invoke(
                        {
                            "word_arabic": word["arabic"],
                            "word_transliteration": word["transliteration"],
                            "english": word["english"],
                            "student_answer": last_answer["student_answer"],
                            "current_score": current_score,
                        }
                    ).text

                # Mark that we showed feedback
                quiz_state["feedback_shown"] = True

                # Generate feedback text using teaching model
                teaching_agent = TeachingAgent(
                    self.teaching_model_getter(), self.teaching_tokenizer
                )
                feedback_response = teaching_agent.respond(
                    f"{prompt_text}\n\nTeacher:", max_new_tokens=200, temperature=0.85
                )

                # Show feedback, then immediately show next question (don't wait for user)
                if current_q < quiz_state["total_questions"]:
                    # Ask next question immediately after feedback
                    next_word = quiz_state["words"][current_q]
                    question_type = "arabic_to_english"

                    next_question_prompt = VOCAB_QUIZ_QUESTION.invoke(
                        {
                            "question_type": question_type,
                            "word_arabic": next_word["arabic"],
                            "word_english": next_word["english"],
                            "question_number": current_q + 1,
                            "total_questions": quiz_state["total_questions"],
                        }
                    ).text

                    # Generate next question using teaching model
                    next_question_response = teaching_agent.respond(
                        f"{next_question_prompt}\n\nTeacher:", max_new_tokens=100, temperature=0.3
                    )

                    # Combine feedback + next question as direct response (bypass model)
                    combined_response = f"{feedback_response}\n\n{next_question_response}"
                    return {"skip_model": True, "response": combined_response}
                else:
                    # No more questions, just show feedback as direct response
                    return {"skip_model": True, "response": feedback_response}

            # Ask the current question (first question or continuing after feedback)
            word = quiz_state["words"][current_q]
            # Always use arabic_to_english for demo purposes
            question_type = "arabic_to_english"

            logger.info(
                f"[Orchestrator] Asking question {current_q + 1}/{quiz_state['total_questions']}"
            )

            prompt_text = VOCAB_QUIZ_QUESTION.invoke(
                {
                    "question_type": question_type,
                    "word_arabic": word["arabic"],
                    "word_english": word["english"],
                    "question_number": current_q + 1,
                    "total_questions": quiz_state["total_questions"],
                }
            ).text

            # Clear feedback flag since we're showing a question now
            quiz_state["feedback_shown"] = False

            # Don't include user_message in prompt for first question (it's just navigation like "1")
            return f"{prompt_text}\n\nTeacher:"

        elif stage == "vocab_quiz_complete":
            logger.info("[Orchestrator] Using template: VOCAB_BATCH_SUMMARY")

            # Check if quiz_state still exists (may have been deleted already)
            if "quiz_state" not in session.get("vocabulary", {}):
                logger.warning("[Orchestrator] quiz_state not found - quiz already completed")
                # Return a simple acknowledgment instead of crashing
                return "Great job on completing the quiz! What would you like to do next?"

            quiz_state = session["vocabulary"]["quiz_state"]

            # Calculate words correct and incorrect
            words_correct = [
                ans["word"]["english"] for ans in quiz_state["answers"] if ans["correct"]
            ]
            words_incorrect = [
                f"{ans['word']['english']} ({ans['word']['arabic']} - {ans['word']['transliteration']})"
                for ans in quiz_state["answers"]
                if not ans["correct"]
            ]

            # Get the batch number that was just quizzed (stored in quiz_state)
            batch_number = quiz_state.get(
                "batch_number", session.get("vocabulary", {}).get("current_batch", 1)
            )
            score = f"{quiz_state['score']}/{quiz_state['total_questions']}"

            words_correct_str = ", ".join(words_correct) if words_correct else "None"
            words_incorrect_str = "\n".join(words_incorrect) if words_incorrect else "None"

            # Calculate progress
            lesson_number = session.get("lesson_number", 1)
            lesson_data = self.lesson_cache.get(lesson_number, {})
            all_vocab = lesson_data.get("vocabulary", [])
            total_batches = (len(all_vocab) + 2) // 3  # Ceiling division
            batches_completed = batch_number  # This batch just finished

            # Store quiz score for next batch
            session["vocabulary"]["previous_quiz_score"] = score

            prompt_text = VOCAB_BATCH_SUMMARY.invoke(
                {
                    "batch_number": batch_number,
                    "score": score,
                    "words_correct": words_correct_str,
                    "words_incorrect": words_incorrect_str,
                    "total_batches": total_batches,
                    "batches_completed": batches_completed,
                }
            ).text

            # Clear quiz state for next batch
            if "quiz_state" in session["vocabulary"]:
                del session["vocabulary"]["quiz_state"]

            if include_user_message:
                return f"{prompt_text}\n\nStudent: {user_message}\n\nTeacher:"
            else:
                return f"{prompt_text}\n\nTeacher:"

        elif stage == "grammar_quiz_complete":
            logger.info("[Orchestrator] Using template: GRAMMAR_TOPIC_SUMMARY")

            # Check if quiz_state still exists
            if "grammar_quiz_state" not in session.get("grammar", {}):
                logger.warning(
                    "[Orchestrator] grammar_quiz_state not found - quiz already completed"
                )
                return "Great job on completing the grammar quiz! What would you like to do next?"

            quiz_state = session["grammar"]["grammar_quiz_state"]
            topic_name = quiz_state["topic"]
            score = f"{quiz_state['score']}/{quiz_state['total_questions']}"
            pass_threshold = "2/3"  # Simple threshold

            # Identify weak areas
            weak_areas_list = []
            for ans in quiz_state["answers"]:
                if not ans["correct"]:
                    weak_areas_list.append(f"- {ans['question']['question']}")

            weak_areas = (
                "\n".join(weak_areas_list)
                if weak_areas_list
                else "None! You got everything right! 🎉"
            )

            prompt_text = GRAMMAR_TOPIC_SUMMARY.invoke(
                {
                    "topic_name": topic_name,
                    "score": score,
                    "pass_threshold": pass_threshold,
                    "weak_areas": weak_areas,
                }
            ).text

            # Clear quiz state
            if "grammar_quiz_state" in session["grammar"]:
                del session["grammar"]["grammar_quiz_state"]

            if include_user_message:
                return f"{prompt_text}\n\nStudent: {user_message}\n\nTeacher:"
            else:
                return f"{prompt_text}\n\nTeacher:"

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

            if include_user_message:
                return f"{prompt_text}\n\nStudent: {user_message}\n\nTeacher:"
            else:
                return f"{prompt_text}\n\nTeacher:"

        elif stage == "grammar_explanation":
            logger.info("[Orchestrator] Using template: GRAMMAR_EXPLANATION")
            # Get first grammar topic (we only have 1)
            grammar_topic = lesson_data["grammar_points"][0]
            topic_name = grammar_topic.replace("_", " ").title()

            # Get grammar content from RAG
            if self.content_agent and self.content_agent.rag_retriever:
                rag_results = self.content_agent.rag_retriever.retrieve_by_lesson(
                    query=f"grammar {topic_name} rule examples",
                    lesson_number=lesson_number,
                    top_k=3,
                )

                # Extract rule and examples from RAG results
                grammar_rule = ""
                examples = []

                for result in rag_results:
                    text = result.get("text", "")
                    if "rule" in text.lower() or "Rule:" in text:
                        grammar_rule = text
                    if "example" in text.lower() or "Examples:" in text:
                        examples.append(text)

                # Fallback if RAG didn't return content
                if not grammar_rule:
                    grammar_rule = f"This lesson covers {topic_name}."
                if not examples:
                    examples = ["Check the lesson materials for examples."]

                examples_formatted = "\n\n".join(examples)
            else:
                # No RAG available
                grammar_rule = f"This lesson covers {topic_name}."
                examples_formatted = "Check the lesson materials for examples."

            prompt_text = GRAMMAR_EXPLANATION.invoke(
                {
                    "lesson_number": lesson_number,
                    "topic_name": topic_name,
                    "grammar_rule": grammar_rule,
                    "examples_formatted": examples_formatted,
                }
            ).text

            if include_user_message:
                return f"{prompt_text}\n\nStudent: {user_message}\n\nTeacher:"
            else:
                return f"{prompt_text}\n\nTeacher:"

        elif stage == "grammar_quiz":
            logger.info("[Orchestrator] Using template: GRAMMAR_QUIZ")

            # Generate quiz questions using pre-generated or ContentAgent if not already in quiz state
            if "grammar_quiz_state" not in session.get("grammar", {}):
                # Get the first grammar topic
                grammar_topic = lesson_data["grammar_points"][0]
                topic_name = grammar_topic.replace("_", " ").title()

                # First try to get pre-generated quiz from background thread
                pre_generated_quizzes = session.get("grammar", {}).get("quizzes", {})
                if grammar_topic in pre_generated_quizzes:
                    logger.info(
                        f"[Orchestrator] Using pre-generated quiz for topic: {grammar_topic}"
                    )
                    questions = pre_generated_quizzes[grammar_topic]
                else:
                    # Fallback: generate on-demand if pre-generation hasn't finished yet
                    logger.info(
                        "[Orchestrator] Pre-generated quiz not ready, generating on-demand via ContentAgent"
                    )

                    # Prepare learned vocabulary items for ContentAgent
                    learned_items = [
                        f"{v['arabic']} ({v['english']})" for v in lesson_data["vocabulary"]
                    ]

                    # Try to generate quiz via ContentAgent
                    if self.content_agent:
                        try:
                            logger.info("[Orchestrator] Calling ContentAgent.generate_quiz()")
                            quiz_json = self.content_agent.generate_quiz(
                                {
                                    "quiz_type": "grammar",
                                    "count": 3,
                                    "difficulty": "beginner",
                                    "learned_items": learned_items,
                                    "lesson_number": lesson_number,
                                }
                            )

                            # Parse the JSON response
                            import json

                            questions_raw = json.loads(quiz_json)

                            # Convert to our format
                            questions = []
                            for q in questions_raw[:3]:  # Take first 3
                                questions.append(
                                    {
                                        "question": q.get("question", ""),
                                        "answer": q.get("answer", q.get("correct", "")),
                                        "explanation": f"Grammar topic: {topic_name}",
                                    }
                                )

                            logger.info(
                                f"[Orchestrator] ContentAgent generated {len(questions)} questions"
                            )

                        except Exception as e:
                            logger.error(f"[Orchestrator] ContentAgent failed: {e}, using fallback")
                            questions = None
                    else:
                        logger.warning("[Orchestrator] No ContentAgent available, using fallback")
                        questions = None

                # Fallback: dynamic hardcoded questions using lesson vocabulary
                if not questions or len(questions) < 3:
                    import random

                    logger.info("[Orchestrator] Using fallback grammar questions")

                    # Separate vocab into masculine and feminine
                    masculine_words = [
                        v for v in lesson_data["vocabulary"] if not v["arabic"].endswith("ة")
                    ]
                    feminine_words = [
                        v for v in lesson_data["vocabulary"] if v["arabic"].endswith("ة")
                    ]

                    # Build 3 unique questions with randomization
                    fallback_questions = []
                    used_words = set()

                    # Generate 3 unique questions
                    attempts = 0
                    while len(fallback_questions) < 3 and attempts < 20:
                        attempts += 1
                        # Randomly pick masculine or feminine
                        if random.choice([True, False]) and masculine_words:
                            available = [
                                w for w in masculine_words if w["arabic"] not in used_words
                            ]
                            if available:
                                word = random.choice(available)
                                used_words.add(word["arabic"])
                                fallback_questions.append(
                                    {
                                        "question": f"Is {word['arabic']} ({word['english']}) masculine or feminine?",
                                        "answer": "masculine",
                                        "explanation": "It doesn't end with ة (taa marbuta), so it's masculine",
                                    }
                                )
                        else:
                            available = [w for w in feminine_words if w["arabic"] not in used_words]
                            if available:
                                word = random.choice(available)
                                used_words.add(word["arabic"])
                                fallback_questions.append(
                                    {
                                        "question": f"Is {word['arabic']} ({word['english']}) masculine or feminine?",
                                        "answer": "feminine",
                                        "explanation": "It ends with ة (taa marbuta), so it's feminine",
                                    }
                                )

                    questions = fallback_questions[:3]  # Ensure exactly 3 questions
                    logger.info(
                        f"[Orchestrator] Fallback generated {len(questions)} randomized questions"
                    )

                session["grammar"]["grammar_quiz_state"] = {
                    "current_question": 0,
                    "total_questions": len(questions),
                    "questions": questions,
                    "answers": [],
                    "score": 0,
                    "topic": topic_name,
                    "feedback_shown": False,
                }
                logger.info(f"[Orchestrator] Generated {len(questions)} grammar quiz questions")

            quiz_state = session["grammar"]["grammar_quiz_state"]
            current_q = quiz_state["current_question"]

            logger.info(
                f"[Orchestrator] Grammar quiz state: current_q={current_q}, answers={len(quiz_state['answers'])}, total={quiz_state['total_questions']}"
            )

            # Check if we just graded an answer and haven't shown feedback yet
            if (
                quiz_state["answers"]
                and len(quiz_state["answers"]) == current_q
                and not quiz_state.get("feedback_shown", False)
            ):
                # Show feedback for the last answer
                last_answer = quiz_state["answers"][-1]
                question_data = quiz_state["questions"][current_q - 1]
                is_correct = last_answer["correct"]

                logger.info(
                    f"[Orchestrator] Showing grammar feedback for question {current_q - 1} - correct: {is_correct}"
                )
                logger.info(f"[Orchestrator] Question was: {question_data['question']}")
                logger.info(f"[Orchestrator] Student answered: {last_answer['student_answer']}")

                # Calculate current score
                current_score = f"{quiz_state['score']}/{len(quiz_state['answers'])}"

                if is_correct:
                    prompt_text = FEEDBACK_GRAMMAR_CORRECT.invoke(
                        {
                            "question": question_data["question"],
                            "student_answer": last_answer["student_answer"],
                            "correct_answer": question_data["answer"],
                            "explanation": question_data["explanation"],
                            "current_score": current_score,
                        }
                    ).text
                else:
                    prompt_text = FEEDBACK_GRAMMAR_INCORRECT.invoke(
                        {
                            "question": question_data["question"],
                            "student_answer": last_answer["student_answer"],
                            "correct_answer": question_data["answer"],
                            "explanation": question_data["explanation"],
                            "current_score": current_score,
                        }
                    ).text

                # Mark that we showed feedback
                quiz_state["feedback_shown"] = True

                # Generate feedback text using teaching model
                teaching_agent = TeachingAgent(
                    self.teaching_model_getter(), self.teaching_tokenizer
                )
                feedback_response = teaching_agent.respond(
                    f"{prompt_text}\n\nTeacher:", max_new_tokens=200, temperature=0.85
                )

                # Show feedback, then immediately show next question (don't wait for user)
                if current_q < quiz_state["total_questions"]:
                    # Ask next question immediately after feedback
                    next_question = quiz_state["questions"][current_q]

                    next_question_prompt = GRAMMAR_QUIZ_QUESTION.invoke(
                        {
                            "topic_name": quiz_state["topic"],
                            "question_number": current_q + 1,
                            "total_questions": quiz_state["total_questions"],
                            "question": next_question["question"],
                        }
                    ).text

                    # Generate next question using teaching model
                    next_question_response = teaching_agent.respond(
                        f"{next_question_prompt}\n\nTeacher:", max_new_tokens=100, temperature=0.3
                    )

                    # Combine feedback + next question as direct response (bypass model)
                    combined_response = f"{feedback_response}\n\n{next_question_response}"
                    return {"skip_model": True, "response": combined_response}
                else:
                    # No more questions, just show feedback as direct response
                    return {"skip_model": True, "response": feedback_response}

            # Ask the current question (first question or continuing after feedback)
            question = quiz_state["questions"][current_q]

            logger.info(
                f"[Orchestrator] Asking grammar question {current_q + 1}/{quiz_state['total_questions']}"
            )

            prompt_text = GRAMMAR_QUIZ_QUESTION.invoke(
                {
                    "topic_name": quiz_state["topic"],
                    "question_number": current_q + 1,
                    "total_questions": quiz_state["total_questions"],
                    "question": question["question"],
                }
            ).text

            # Clear feedback flag since we're showing a question now
            quiz_state["feedback_shown"] = False

            # Don't include user_message in prompt for first question
            return f"{prompt_text}\n\nTeacher:"

        elif stage == "final_exam":
            logger.info("[Orchestrator] Using template: FINAL_EXAM (not implemented)")
            # TODO: Implement comprehensive final exam with mixed vocab + grammar questions
            return {
                "skip_model": True,
                "response": "The final exam feature is coming soon! For now, you can practice with vocab quizzes and grammar quizzes separately.",
            }

        elif stage == "final_exam_complete":
            logger.info("[Orchestrator] Final exam complete (not implemented)")
            return {
                "skip_model": True,
                "response": "Great work on completing the lesson! You can review vocabulary, try more grammar practice, or start a new lesson.",
            }

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

    def _pregenerate_grammar_quizzes(self, session_id, lesson_number, lesson_data):
        """
        Background thread: Pre-generate all grammar quizzes for this lesson.

        Args:
            session_id: Session identifier
            lesson_number: Lesson number
            lesson_data: Lesson data from cache
        """
        try:
            logger.info(
                f"[Orchestrator] [Background] Starting grammar quiz pre-generation for lesson {lesson_number}"
            )

            session = self.sessions.get(session_id)
            if not session:
                logger.warning("[Orchestrator] [Background] Session not found, aborting")
                return

            # Initialize quizzes storage
            if "quizzes" not in session["grammar"]:
                session["grammar"]["quizzes"] = {}

            # Generate quiz for each grammar topic
            for topic in lesson_data["grammar_points"]:
                try:
                    logger.info(f"[Orchestrator] [Background] Generating quiz for topic: {topic}")

                    # Use hardcoded gender identification questions for masculine_feminine_nouns
                    if topic == "masculine_feminine_nouns":
                        import random

                        # Separate vocab by gender (ة ending = feminine)
                        masculine_words = [
                            v for v in lesson_data["vocabulary"] if not v["arabic"].endswith("ة")
                        ]
                        feminine_words = [
                            v for v in lesson_data["vocabulary"] if v["arabic"].endswith("ة")
                        ]

                        questions = []
                        used_words = set()  # Track used words to avoid duplicates

                        # Generate 3 unique gender identification questions
                        attempts = 0
                        while len(questions) < 3 and attempts < 20:
                            attempts += 1
                            # Randomly pick masculine or feminine
                            if random.choice([True, False]) and masculine_words:
                                available = [
                                    w for w in masculine_words if w["arabic"] not in used_words
                                ]
                                if available:
                                    word = random.choice(available)
                                    used_words.add(word["arabic"])
                                    questions.append(
                                        {
                                            "question": f"Is {word['arabic']} ({word['english']}) masculine or feminine?",
                                            "answer": "masculine",
                                            "explanation": "It doesn't end with ة (taa marbuta), so it's masculine",
                                        }
                                    )
                            else:
                                available = [
                                    w for w in feminine_words if w["arabic"] not in used_words
                                ]
                                if available:
                                    word = random.choice(available)
                                    used_words.add(word["arabic"])
                                    questions.append(
                                        {
                                            "question": f"Is {word['arabic']} ({word['english']}) masculine or feminine?",
                                            "answer": "feminine",
                                            "explanation": "It ends with ة (taa marbuta), so it's feminine",
                                        }
                                    )

                        logger.info(
                            f"[Orchestrator] [Background] Generated {len(questions)} grammar-specific questions"
                        )
                    else:
                        # For other topics: try RAG-based generation (future enhancement)
                        logger.warning(
                            f"[Orchestrator] [Background] No quiz generator for topic: {topic}, skipping"
                        )
                        continue

                    session["grammar"]["quizzes"][topic] = questions
                    logger.info(
                        f"[Orchestrator] [Background] Stored {len(questions)} questions for {topic}"
                    )

                    # Save sessions after each quiz generation (for ZeroGPU persistence)
                    from app import save_sessions

                    save_sessions(self.sessions)
                    logger.info("[Orchestrator] [Background] Saved sessions to file")

                except Exception as e:
                    logger.error(
                        f"[Orchestrator] [Background] Failed to generate quiz for {topic}: {e}"
                    )
                    # Continue with other topics

            logger.info(
                f"[Orchestrator] [Background] Completed grammar quiz pre-generation for lesson {lesson_number}"
            )

        except Exception as e:
            logger.error(f"[Orchestrator] [Background] Pre-generation failed: {e}")
