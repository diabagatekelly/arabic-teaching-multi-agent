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

    def __init__(self, agent: TeachingAgent):
        """Initialize teaching node with agent."""
        self.agent = agent

    def __call__(self, state: SystemState) -> SystemState:
        """
        Process user message or grading result through teaching agent.

        Args:
            state: Current system state

        Returns:
            Updated system state
        """
        try:
            # Get the most recent message
            if not state.conversation_history:
                # Start new session
                response = self._handle_lesson_start(state)
            elif state.last_agent == "agent2":
                # Coming from grading - provide feedback
                response = self._handle_feedback(state)
            else:
                # Handle user message
                response = self._handle_user_message(state)

            # Update state
            state.add_message("agent1", response)
            state.last_agent = "agent1"

            # Determine next step
            # TODO: Replace keyword detection with structured output
            # Current approach is fragile - fails on "No exercise needed" or "Question later"
            # Consider having agent return explicit flag: response.get("generate_exercise", False)
            if "exercise" in response.lower() or "question" in response.lower():
                # Agent wants to generate exercise
                state.next_agent = "agent3"
            else:
                # Wait for user response
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

    def _handle_lesson_start(self, state: SystemState) -> str:
        """Start a new lesson."""
        input_data = {
            "lesson_number": state.current_lesson,
            "mode": "vocabulary",  # Start with vocabulary
        }
        return self.agent.start_lesson(input_data)

    def _handle_user_message(self, state: SystemState) -> str:
        """Handle regular user message."""
        last_msg = state.conversation_history[-1]
        input_data = {
            "user_input": last_msg.content,
            "learned_items": state.learned_items,
            "mode": state.current_mode,
        }
        return self.agent.handle_user_message(input_data)

    def _handle_feedback(self, state: SystemState) -> str:
        """Provide feedback after grading."""
        grading_msg = state.conversation_history[-1]
        is_correct = grading_msg.metadata.get("is_correct", False)

        input_data = {
            "is_correct": is_correct,
            "user_answer": grading_msg.metadata.get("user_answer", ""),
            "correct_answer": grading_msg.metadata.get("correct_answer", ""),
            "mode": state.current_mode,
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

            # Update state
            state.add_message(
                "agent2",
                grading_result,
                metadata={
                    "user_answer": user_answer,
                    "correct_answer": state.pending_exercise.answer,
                    "is_correct": is_correct,
                },
            )
            state.record_exercise_result(is_correct)
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

        Checks for negative indicators first (incorrect, wrong, not correct, etc.),
        then checks for positive indicators (correct, checkmarks).
        """
        result_lower = grading_result.lower()

        # Check for negative indicators first (most specific patterns)
        negative_patterns = [
            "incorrect",
            "wrong",
            "not correct",
            "isn't correct",
            "wasn't correct",
            "not quite",
            "almost",
            "partially correct",
        ]
        if any(pattern in result_lower for pattern in negative_patterns):
            return False

        # Check for positive indicators
        positive_patterns = ["correct", "right", "✓", "✅", "yes"]
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
            state.next_agent = "user"  # Wait for user to answer exercise

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
        Initialize lesson by caching ALL content upfront.

        Per ARCHITECTURE.md, Agent 3 should:
        - Retrieve all vocabulary words for the lesson
        - Retrieve all grammar rules and examples
        - Cache in memory (no repeated RAG queries during lesson)

        Args:
            state: SystemState to update with cached content

        Returns:
            Updated SystemState with cached content
        """
        logger.info(f"Initializing lesson {state.current_lesson} - caching all content")

        try:
            # TODO: Integrate with actual RAG retriever when available
            # PLACEHOLDER DATA - Remove before production
            # In production, would call:
            # vocab_content = self.agent.rag_retriever.get_lesson_vocabulary(state.current_lesson)
            # grammar_content = self.agent.rag_retriever.get_lesson_grammar(state.current_lesson)

            # PLACEHOLDER: vocabulary (would come from RAG)
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

            # PLACEHOLDER: grammar (would come from RAG)
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
