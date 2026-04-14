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
            if "exercise" in response.lower() or "question" in response.lower():
                # Agent wants to generate exercise
                state.next_agent = "agent3"
            else:
                # Wait for user response
                state.next_agent = "user"

            return state

        except Exception as e:
            logger.error(f"TeachingNode error: {e}")
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
        # Get grading result from last message
        grading_msg = state.conversation_history[-1]
        is_correct = "correct" in grading_msg.content.lower()

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
    - Provide grading explanations
    - Detect partial credit scenarios
    """

    def __init__(self, agent: GradingAgent):
        """Initialize grading node with agent."""
        self.agent = agent

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
            logger.error(f"GradingNode error: {e}")
            state.add_message("system", f"Error in grading: {str(e)}")
            state.next_agent = "agent1"
            return state

    def _is_answer_correct(self, grading_result: str) -> bool:
        """Parse grading result to determine if answer is correct."""
        # Simple heuristic - can be improved
        result_lower = grading_result.lower()
        if "correct" in result_lower and "incorrect" not in result_lower:
            return True
        if "✓" in grading_result or "✅" in grading_result:
            return True
        return False


class ContentNode:
    """
    Node wrapping Agent 3 (Content).

    Responsibilities:
    - Generate exercises using RAG
    - Compose quizzes
    - Create balanced tests
    - Retrieve lesson content
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
            # Extract exercise requirements from teaching agent's last message
            last_msg = state.conversation_history[-1]
            exercise_request = self._parse_exercise_request(last_msg.content, state)

            # Generate exercise
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
            logger.error(f"ContentNode error: {e}")
            state.add_message("system", f"Error generating exercise: {str(e)}")
            state.next_agent = "agent1"  # Return to teaching
            return state

    def _parse_exercise_request(self, message: str, state: SystemState) -> dict[str, Any]:
        """Extract exercise requirements from teaching agent message."""
        # Default exercise request
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
        """Parse generated exercise from agent response."""
        import json
        import re

        # Extract JSON from response
        json_match = re.search(r"```json\n(.*?)\n```", response, re.DOTALL)
        if json_match:
            exercise_data = json.loads(json_match.group(1))
        else:
            # Try to find JSON object
            json_match = re.search(r"\{.*\}", response, re.DOTALL)
            if json_match:
                exercise_data = json.loads(json_match.group(0))
            else:
                raise ValueError("Could not parse exercise JSON from response")

        # Create Exercise object
        return Exercise(
            exercise_id=f"ex_{state.total_exercises_completed + 1}",
            exercise_type=request["exercise_type"],
            question=exercise_data.get("question", ""),
            answer=exercise_data.get("answer", ""),
            difficulty=exercise_data.get("difficulty", request["difficulty"]),
            metadata=exercise_data,
        )
