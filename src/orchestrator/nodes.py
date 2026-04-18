"""Agent node wrappers for LangGraph.

Each node wraps an agent and provides a standard interface for the orchestrator.
Nodes handle:
- Agent invocation
- State updates
- Error handling
- Response formatting
"""

import logging
from typing import Any

from src.agents import ContentAgent, GradingAgent, TeachingAgent

from .state import Exercise, SystemState

logger = logging.getLogger(__name__)


class TeachingNode:
    """
    Node wrapping Agent 1 (Teaching).

    Responsibilities:
    - Lesson introductions
    - Vocabulary teaching
    - Grammar explanations
    - User feedback after grading
    - Progress guidance
    """

    def __init__(self, agent: TeachingAgent, content_agent: ContentAgent | None = None):
        """Initialize teaching node with agent and optional content agent for RAG."""
        self.agent = agent
        self.content_agent = content_agent

    def __call__(self, state: SystemState) -> SystemState:
        """
        Process user message or grading result through teaching agent.

        Args:
            state: Current system state

        Returns:
            Updated system state
        """
        logger.info(f"TeachingNode called - conversation length: {len(state.conversation_history)}")
        try:
            # Get the most recent message
            if not state.conversation_history:
                # Start new session - initialize lesson content first
                logger.info("Handling lesson start...")
                # Initialize lesson content from RAG before starting
                if not state.lesson_initialized and self.content_agent:
                    state = self._initialize_lesson_content(state)
                response = self._handle_lesson_start(state)
                logger.info(f"Lesson start response generated: {len(response)} chars")
            elif state.last_agent == "agent3" and state.pending_exercise:
                # Coming from content agent - present the exercise to user
                logger.info("Presenting exercise from content agent...")
                response = self._present_exercise(state)
            elif state.last_agent == "agent2":
                # Coming from grading - provide feedback
                response = self._handle_feedback(state)
            else:
                # Handle user message
                response = self._handle_user_message(state)

            # Update state
            state.add_message("agent1", response)
            state.last_agent = "agent1"

            logger.info(f"TeachingNode response being returned: {response[:200]}...")

            # Determine next step
            # If we just presented an exercise, wait for user to answer
            if state.pending_exercise and state.awaiting_user_answer:
                logger.info("Exercise presented, waiting for user answer")
                state.next_agent = "user"
            # Look for explicit exercise generation markers
            elif "[GENERATE_EXERCISE]" in response:
                # Agent wants to generate exercise - strip marker from response
                response = response.replace("[GENERATE_EXERCISE]", "").strip()
                state.next_agent = "agent3"
            else:
                # Wait for user response
                # Note: Removed keyword detection ("exercise"/"quiz") - too prone to false positives
                # (e.g., lesson welcome mentioning "practice exercises" shouldn't trigger generation)
                state.next_agent = "user"

            return state

        except Exception as e:
            logger.error(
                f"TeachingNode error: {e}",
                extra={
                    "last_agent": state.last_agent,
                    "conversation_length": len(state.conversation_history),
                    "current_lesson": state.current_lesson,
                    "has_pending_exercise": state.pending_exercise is not None,
                },
                exc_info=True,
            )
            state.add_message("system", f"Error in teaching agent: {str(e)}")
            state.next_agent = "user"  # Fallback to user
            return state

    def _initialize_lesson_content(self, state: SystemState) -> SystemState:
        """Initialize lesson content from RAG."""
        logger.info(f"Initializing lesson {state.current_lesson} content from RAG")

        try:
            # Check if content agent has content_loader (RAG-based)
            if hasattr(self.content_agent, "content_loader") and self.content_agent.content_loader:
                logger.info("Loading vocabulary and grammar from RAG...")

                # Load vocabulary from RAG
                vocab_words = self.content_agent.content_loader.load_vocabulary(
                    state.current_lesson
                )
                state.cached_vocab_words = vocab_words

                # Load grammar from RAG
                grammar_content = self.content_agent.content_loader.load_grammar(
                    state.current_lesson
                )
                state.cached_grammar_content = grammar_content

                state.lesson_initialized = True
                logger.info(
                    f"Lesson {state.current_lesson} initialized: "
                    f"{len(vocab_words)} words, {len(grammar_content)} grammar topics"
                )
            else:
                logger.warning("Content agent has no content_loader - skipping RAG initialization")

        except Exception as e:
            logger.error(f"Failed to initialize lesson content: {e}", exc_info=True)
            # Don't fail - teaching can continue with empty content
            state.lesson_initialized = False

        return state

    def _handle_lesson_start(self, state: SystemState) -> str:
        """Start a new lesson."""
        # Use cached content from initialize_lesson_content
        vocab_words = state.cached_vocab_words if state.cached_vocab_words else []
        grammar_topics = (
            list(state.cached_grammar_content.keys()) if state.cached_grammar_content else []
        )

        # Format vocabulary preview (first 10 words) with double newlines for Gradio markdown
        vocab_preview_list = []
        for i, word in enumerate(vocab_words[:10], 1):
            vocab_preview_list.append(
                f"{i}. {word['arabic']} ({word['transliteration']}) - {word['english']}"
            )
        topics_preview = "\n\n".join(vocab_preview_list)

        # Format grammar topics
        grammar_topics_formatted = ", ".join(
            [topic.replace("_", " ").title() for topic in grammar_topics]
        )

        input_data = {
            "lesson_number": state.current_lesson,
            "mode": "lesson_start",
            "total_words": len(vocab_words),
            "topics_preview": topics_preview,
            "topics_count": len(grammar_topics),
            "grammar_topics": grammar_topics_formatted,
        }
        # Call the actual fine-tuned model
        logger.info(
            f"Calling teaching agent start_lesson with {len(vocab_words)} vocab words, {len(grammar_topics)} grammar topics"
        )
        response = self.agent.start_lesson(input_data)
        logger.info(f"Teaching agent returned: {len(response)} chars")
        return response

    def _handle_user_message(self, state: SystemState) -> str:
        """Handle regular user message."""
        last_msg = state.conversation_history[-1]
        user_input = last_msg.content.lower().strip()

        # Detect mode changes from user input and initiate teaching
        if user_input in ["1", "vocab", "vocabulary"]:
            state.current_mode = "teaching_vocab"
            logger.info("Mode changed to teaching_vocab - initiating vocabulary teaching")

            # Prepare vocabulary batch from cached content
            vocab_words = state.cached_vocab_words[:3] if state.cached_vocab_words else []
            words_formatted = "\n".join(
                [
                    f"{i + 1}. {w['arabic']} ({w['transliteration']}) - {w['english']}"
                    for i, w in enumerate(vocab_words)
                ]
            )

            input_data = {
                "lesson_number": state.current_lesson,
                "batch_number": 1,
                "total_batches": (len(state.cached_vocab_words) + 2) // 3
                if state.cached_vocab_words
                else 1,
                "words": words_formatted,
                "mode": "teaching_vocab",
            }
            return self.agent.handle_teaching_vocab(input_data)

        elif user_input in ["2", "grammar"]:
            state.current_mode = "teaching_grammar"
            logger.info("Mode changed to teaching_grammar - initiating grammar teaching")

            # Prepare grammar overview from cached content
            grammar_topics = (
                list(state.cached_grammar_content.keys()) if state.cached_grammar_content else []
            )
            topics_list = "\n".join(
                [f"- {topic.replace('_', ' ').title()}" for topic in grammar_topics]
            )

            input_data = {
                "lesson_number": state.current_lesson,
                "topics_count": len(grammar_topics),
                "topics_list": topics_list,
                "mode": "teaching_grammar",
            }
            return self.agent.handle_teaching_grammar(input_data)

        # General user message (not mode change)
        input_data = {
            "user_input": last_msg.content,
            "learned_items": state.learned_items,
            "mode": state.current_mode,
        }
        return self.agent.handle_user_message(input_data)

    def _present_exercise(self, state: SystemState) -> str:
        """Present an exercise that was just generated by ContentAgent.

        This is called after agent3 generates an exercise and routes to agent1.
        The teaching agent should present the exercise question to the user in a
        friendly way, then the system waits for the user's answer.
        """
        if not state.pending_exercise:
            logger.warning("_present_exercise called but no pending exercise")
            return "Let's continue learning!"

        exercise = state.pending_exercise

        # Format the exercise question nicely
        if state.current_mode == "teaching_vocab":
            presentation = f"**Quiz Time!** 📝\n\n{exercise.question}\n\nType your answer below:"
        elif state.current_mode == "teaching_grammar":
            presentation = f"**Grammar Quiz!** 📖\n\n{exercise.question}\n\nWhat's your answer?"
        else:
            presentation = f"{exercise.question}"

        logger.info(f"Presenting exercise to user: {presentation[:100]}...")
        return presentation

    def _handle_feedback(self, state: SystemState) -> str:
        """Provide feedback after grading."""
        grading_msg = state.conversation_history[-1]
        is_correct = grading_msg.metadata.get("is_correct", False)

        # Map internal mode names to agent-expected modes
        mode_map = {
            "teaching_vocab": "vocabulary",
            "teaching_grammar": "grammar",
        }
        agent_mode = mode_map.get(state.current_mode, state.current_mode)

        input_data = {
            "is_correct": is_correct,
            "user_answer": grading_msg.metadata.get("user_answer", ""),
            "correct_answer": grading_msg.metadata.get("correct_answer", ""),
            "mode": agent_mode,
        }
        return self.agent.provide_feedback(input_data)


class GradingNode:
    """
    Node wrapping Agent 2 (Grading).

    Responsibilities:
    - Validate user answers
    - Handle edge cases (synonyms, typos, harakaat)
    - Use pre-loaded grammar rules for context
    - Provide grading explanations
    - Detect partial credit scenarios
    """

    def __init__(self, agent: GradingAgent):
        """Initialize grading node with agent."""
        self.agent = agent

    def preload_grammar_rules(self, state: SystemState) -> None:
        """
        Pre-load grammar rules at lesson start for grading context.

        Per ARCHITECTURE.md, Agent 2 should have grammar rules pre-loaded
        so it can make accurate grading decisions.

        Args:
            state: SystemState with cached_grammar_content from Agent 3
        """
        if not state.cached_grammar_content:
            logger.warning("No cached grammar content to pre-load for grading")
            return

        logger.info(f"Pre-loading {len(state.cached_grammar_content)} grammar rules for grading")

        # Extract grading-relevant rules from cached grammar
        state.preloaded_grammar_rules = {
            topic: {
                "rule": content.get("rule", ""),
                "examples": content.get("examples", []),
                "detection_pattern": content.get("detection_pattern", ""),
            }
            for topic, content in state.cached_grammar_content.items()
        }

        logger.info("Grammar rules pre-loaded for Agent 2")

    def __call__(self, state: SystemState) -> SystemState:
        """
        Grade user's answer to pending exercise.

        Args:
            state: Current system state

        Returns:
            Updated system state with grading result
        """
        try:
            if not state.pending_exercise:
                logger.warning("GradingNode called but no pending exercise")
                state.next_agent = "agent1"
                return state

            # Get user's answer from last message
            user_answer = state.conversation_history[-1].content

            # Prepare grading input
            input_data = {
                "user_answer": user_answer,
                "correct_answer": state.pending_exercise.answer,
                "question": state.pending_exercise.question,
                "mode": state.current_mode,
            }

            # Grade the answer
            grading_result = self.agent.grade_answer(input_data)

            # Parse result
            is_correct = self._is_answer_correct(grading_result)

            # Update state - include all exercise metadata for feedback template
            metadata = {
                "user_answer": user_answer,
                "correct_answer": state.pending_exercise.answer,
                "is_correct": is_correct,
            }
            # Add exercise metadata (word_arabic, word_english, etc.)
            if state.pending_exercise.metadata:
                metadata.update(state.pending_exercise.metadata)

            state.add_message(
                "agent2",
                grading_result,
                metadata=metadata,
            )
            state.record_exercise_result(is_correct)

            # Add to learned items if correct
            if is_correct:
                # Extract word/concept from exercise metadata
                item_to_add = state.pending_exercise.metadata.get(
                    "word_arabic", state.pending_exercise.question
                )
                state.add_learned_item(item_to_add)

            state.clear_pending_exercise()

            state.last_agent = "agent2"
            state.next_agent = "agent1"  # Go back to teaching for feedback

            return state

        except Exception as e:
            logger.error(
                f"GradingNode error: {e}",
                extra={
                    "last_agent": state.last_agent,
                    "has_pending_exercise": state.pending_exercise is not None,
                    "exercise_type": state.pending_exercise.exercise_type
                    if state.pending_exercise
                    else None,
                    "conversation_length": len(state.conversation_history),
                },
                exc_info=True,
            )
            state.add_message("system", f"Error in grading: {str(e)}")
            state.next_agent = "agent1"
            return state

    def _is_answer_correct(self, grading_result: str) -> bool:
        """
        Parse grading result to determine if answer is correct.

        Checks for negation overrides first (e.g., "not incorrect"),
        then negative indicators, then positive indicators.
        Ambiguous cases default to False.
        """
        result_lower = grading_result.lower()

        # Handle explicit negated-negative phrases first
        # so we don't misclassify cases like "not incorrect" or "not wrong"
        negation_overrides = [
            "not incorrect",
            "not wrong",
        ]
        if any(pattern in result_lower for pattern in negation_overrides):
            return True

        # Check for negative indicators (most specific patterns first)
        negative_patterns = [
            # More specific phrasings first
            " is incorrect",
            " was incorrect",
            " is wrong",
            " was wrong",
            "not entirely correct",  # e.g., "Not entirely correct"
            "not fully correct",  # e.g., "not fully correct"
            "not correct",
            "isn't correct",
            "wasn't correct",
            "not quite",
            "almost",
            "partially correct",
            # Generic catch-alls (checked after the specific phrases)
            "incorrect",
            "wrong",
        ]
        if any(pattern in result_lower for pattern in negative_patterns):
            return False

        # Check for positive indicators
        positive_patterns = ["correct", "right", "✓", "✔", "✅", "yes"]
        if any(pattern in result_lower for pattern in positive_patterns):
            return True

        # Default to False if unclear
        return False


class ContentNode:
    """
    Node wrapping Agent 3 (Content).

    Responsibilities:
    - Initialize lesson (cache ALL content upfront)
    - Generate exercises using RAG
    - Serve cached content during lesson
    - Compose quizzes and tests
    """

    def __init__(self, agent: ContentAgent):
        """Initialize content node with agent."""
        self.agent = agent

    def __call__(self, state: SystemState) -> SystemState:
        """
        Generate exercise based on teaching agent's request.

        Args:
            state: Current system state

        Returns:
            Updated system state with generated exercise
        """
        try:
            # Initialize lesson content if not already cached
            if not state.lesson_initialized:
                state = self.initialize_lesson(state)

            exercise_request = self._parse_exercise_request(state)

            # Generate exercise using cached content
            response = self.agent.generate_exercise(exercise_request)

            # Parse exercise from response
            exercise = self._parse_exercise_response(response, exercise_request, state)

            # Update state
            state.set_pending_exercise(exercise)
            state.add_message("agent3", response)
            state.last_agent = "agent3"

            # FIX: Route to teaching agent to PRESENT the exercise to user
            # Previously set to "user" which caused orchestrator to stop,
            # leading to auto-grading bug where next user message would be graded
            state.next_agent = "agent1"  # Teaching agent presents exercise

            return state

        except Exception as e:
            logger.error(
                f"ContentNode error: {e}",
                extra={
                    "last_agent": state.last_agent,
                    "lesson_initialized": state.lesson_initialized,
                    "current_lesson": state.current_lesson,
                    "cached_vocab_count": len(state.cached_vocab_words),
                },
                exc_info=True,
            )
            state.add_message("system", f"Error generating exercise: {str(e)}")
            state.next_agent = "agent1"  # Return to teaching
            return state

    def initialize_lesson(self, state: SystemState) -> SystemState:
        """
        Initialize lesson by caching ALL content upfront using RAG retrieval.

        Per ARCHITECTURE.md, Agent 3 should:
        - Retrieve all vocabulary words for the lesson
        - Retrieve all grammar rules and examples
        - Cache in memory (no repeated RAG queries during lesson)

        Args:
            state: SystemState to update with cached content

        Returns:
            Updated SystemState with cached content
        """
        logger.info(f"Initializing lesson {state.current_lesson} - caching all content from RAG")

        try:
            # Check if agent has content_loader (RAG-based) or use fallback
            if hasattr(self.agent, "content_loader") and self.agent.content_loader is not None:
                logger.info("Using RAG retrieval for lesson content")

                # Load vocabulary from RAG
                vocab_words = self.agent.content_loader.load_vocabulary(state.current_lesson)
                state.cached_vocab_words = vocab_words

                # Load grammar from RAG
                grammar_content = self.agent.content_loader.load_grammar(state.current_lesson)
                state.cached_grammar_content = grammar_content

            else:
                logger.warning("No content_loader found, using fallback placeholder data")
                # FALLBACK: Use placeholder data if RAG not initialized
                state.cached_vocab_words = [
                    {
                        "arabic": "كِتَاب",
                        "transliteration": "kitaab",
                        "english": "book",
                        "word_id": "w1",
                    },
                    {
                        "arabic": "مَدْرَسَة",
                        "transliteration": "madrasa",
                        "english": "school",
                        "word_id": "w2",
                    },
                    {
                        "arabic": "قَلَم",
                        "transliteration": "qalam",
                        "english": "pen",
                        "word_id": "w3",
                    },
                ]

                state.cached_grammar_content = {
                    "gender": {
                        "rule": "Nouns are either masculine or feminine",
                        "examples": ["كِتَاب (masculine)", "مَدْرَسَة (feminine)"],
                    },
                    "definite_article": {
                        "rule": "Use ال for 'the'",
                        "examples": ["الكِتَاب (the book)", "المَدْرَسَة (the school)"],
                    },
                }

            state.lesson_initialized = True
            logger.info(
                f"Lesson {state.current_lesson} initialized: "
                f"{len(state.cached_vocab_words)} words, "
                f"{len(state.cached_grammar_content)} grammar topics cached"
            )

        except Exception as e:
            logger.error(f"Failed to initialize lesson {state.current_lesson}: {e}", exc_info=True)
            # Don't fail - will retry on next content request
            state.lesson_initialized = False

        return state

    def _parse_exercise_request(self, state: SystemState) -> dict[str, Any]:
        """Extract exercise requirements from current state."""
        return {
            "exercise_type": "translation",  # Default type
            "difficulty": "beginner",
            "learned_items": state.learned_items[-3:] if state.learned_items else [],
            "lesson_number": state.current_lesson,
            "mode": "exercise_generation",
        }

    def _parse_exercise_response(
        self, response: str, request: dict[str, Any], state: SystemState
    ) -> Exercise:
        """
        Parse generated exercise from agent response.

        Extracts JSON from markdown code blocks or raw JSON objects,
        validates required fields, and returns an Exercise object.
        """
        import json
        import re

        # Try markdown code block first (non-greedy)
        json_match = re.search(r"```(?:json)?\s*\n(.*?)\n```", response, re.DOTALL)
        if json_match:
            json_str = json_match.group(1)
        else:
            # Try to find JSON object (non-greedy, limit scope)
            json_match = re.search(r"\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}", response)
            if json_match:
                json_str = json_match.group(0)
            else:
                raise ValueError("Could not find JSON in exercise response")

        # Parse JSON
        try:
            exercise_data = json.loads(json_str)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in exercise response: {e}") from e

        # Validate required fields
        required_fields = ["question", "answer"]
        missing = [f for f in required_fields if not exercise_data.get(f)]
        if missing:
            raise ValueError(f"Missing required fields in exercise: {missing}")

        # Create Exercise object
        return Exercise(
            exercise_id=f"ex_{state.total_exercises_completed + 1}",
            exercise_type=request["exercise_type"],
            question=exercise_data["question"],
            answer=exercise_data["answer"],
            difficulty=exercise_data.get("difficulty", request["difficulty"]),
            metadata=exercise_data,
        )
