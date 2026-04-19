"""Comprehensive integration test for complete lesson flow.

Tests the full user journey from lesson start through vocabulary learning.
This validates the orchestration between all agents and state management.
"""

import pytest

from src.orchestrator.state import Message, SystemState


@pytest.mark.integration
class TestCompleteLessonFlow:
    """Test complete lesson flow from start to vocabulary quiz generation."""

    def test_lesson_start_to_vocab_quiz_generation(self, real_orchestrator):
        """
        Test flow: lesson start → vocab choice → vocab batch → quiz request → quiz generated.

        This validates the core orchestration for the vocabulary learning path.
        """
        # ==================================================================
        # STEP 1: Lesson Start
        # ==================================================================
        state = SystemState(
            user_id="test_user",
            session_id="test_session_flow",
            current_lesson=1,
            conversation_history=[],
            next_agent="teaching",
            last_agent="",
        )

        result = real_orchestrator.invoke(state)

        # Verify lesson start response
        assert len(result["conversation_history"]) == 1, "Should have welcome message"
        welcome_msg = result["conversation_history"][0]
        assert welcome_msg.role == "agent1", "Welcome should be from teaching agent"

        # CRITICAL: Welcome should offer numbered navigation options
        content = welcome_msg.content
        print(f"\n=== LESSON START MESSAGE ===\n{content}\n")

        # Check for numbered options (1, 2, 3 or similar)
        has_numbers = any(str(i) in content for i in [1, 2, 3])
        assert has_numbers, f"Welcome should show numbered options, got: {content[:300]}"

        # Check for vocabulary option
        has_vocab_option = any(word in content.lower() for word in ["vocabulary", "vocab", "words"])
        assert has_vocab_option, f"Should offer vocabulary option, got: {content[:300]}"

        # Check for grammar option
        has_grammar_option = "grammar" in content.lower()
        assert has_grammar_option, f"Should offer grammar option, got: {content[:300]}"

        # Should be waiting for user input
        assert result["next_agent"] == "user", "Should wait for user choice after welcome"

        # Should NOT have a pending exercise
        assert result["pending_exercise"] is None, "No exercise should exist at lesson start"

        # ==================================================================
        # STEP 2: User Chooses Vocabulary ("1")
        # ==================================================================
        result["conversation_history"].append(Message(role="user", content="1"))
        result["next_agent"] = "teaching"
        result = real_orchestrator.invoke(result)

        # Verify mode switched to teaching_vocab
        assert (
            result["current_mode"] == "teaching_vocab"
        ), f"Mode should be teaching_vocab, got: {result.get('current_mode')}"

        # Should have teaching agent response
        assert result["last_agent"] == "agent1", "Teaching agent should respond to vocab choice"

        # Get the vocab batch message
        vocab_batch_msg = result["conversation_history"][-1]
        assert vocab_batch_msg.role == "agent1"
        batch_content = vocab_batch_msg.content
        print(f"\n=== VOCAB BATCH MESSAGE ===\n{batch_content}\n")

        # CRITICAL: Should show vocabulary words, NOT a quiz
        # Check for vocabulary indicators (Arabic text, transliteration)
        has_arabic = any("\u0600" <= char <= "\u06ff" for char in batch_content)
        assert has_arabic, f"Should show Arabic words in batch, got: {batch_content[:300]}"

        # Should mention transliteration (parentheses around romanization)
        has_transliteration = "(" in batch_content and ")" in batch_content
        assert has_transliteration, f"Should show transliteration (xxx), got: {batch_content[:300]}"

        # Should NOT be a quiz yet
        quiz_indicators = ["translate", "what does", "quiz time", "question"]
        is_quiz = any(indicator in batch_content.lower() for indicator in quiz_indicators)
        assert not is_quiz, f"Should NOT be a quiz yet, got: {batch_content[:300]}"

        # Should NOT have a pending exercise
        assert (
            result["pending_exercise"] is None
        ), "No exercise should be auto-generated after vocab batch"

        # Should be waiting for user input (not auto-triggering quiz)
        assert result["next_agent"] == "user", "Should wait for user to request quiz"

        # ==================================================================
        # STEP 3: User Requests Quiz
        # ==================================================================
        result["conversation_history"].append(Message(role="user", content="quiz me"))
        result["next_agent"] = "agent3"  # Route to content agent for exercise generation
        result = real_orchestrator.invoke(result)

        # CRITICAL: After agent3 generates exercise, should route BACK to agent1 to present it
        assert result["last_agent"] == "agent1", (
            f"After exercise generation, teaching agent should present question. "
            f"Got last_agent='{result['last_agent']}', expected 'agent1'"
        )

        # Should have generated an exercise
        assert (
            result["pending_exercise"] is not None
        ), "Exercise should be generated after explicit quiz request"

        # Should be awaiting user answer
        assert result["awaiting_user_answer"] is True, "Should be awaiting answer to quiz question"

        # Get the quiz message - should be from teaching agent (agent1)
        quiz_msg = result["conversation_history"][-1]
        assert (
            quiz_msg.role == "agent1"
        ), f"Quiz should be presented by teaching agent (agent1), got '{quiz_msg.role}'"
        quiz_content = quiz_msg.content
        print(f"\n=== QUIZ MESSAGE (from agent1) ===\n{quiz_content}\n")

        # Should be asking a question
        question_indicators = ["translate", "what does", "?"]
        is_question = any(indicator in quiz_content.lower() for indicator in question_indicators)
        assert is_question, f"Should ask a quiz question, got: {quiz_content[:200]}"

        # Should be waiting for user answer
        assert result["next_agent"] == "user", "Should wait for user's answer"

        # ==================================================================
        # STEP 4: User Answers → Grading → Feedback
        # ==================================================================
        # Get the correct answer from pending exercise
        exercise = result["pending_exercise"]
        correct_answer = exercise.answer

        print(f"\n[TEST] User will answer: '{correct_answer}'")

        # User submits answer
        result["conversation_history"].append(Message(role="user", content=correct_answer))
        result["next_agent"] = "agent2"  # Should route to grading agent
        result = real_orchestrator.invoke(result)

        # CRITICAL: After grading, should route BACK to agent1 for feedback
        assert result["last_agent"] == "agent1", (
            f"After grading, teaching agent should provide feedback. "
            f"Got last_agent='{result['last_agent']}', expected 'agent1'"
        )

        # Get the feedback message - should be from teaching agent
        feedback_msg = result["conversation_history"][-1]
        assert (
            feedback_msg.role == "agent1"
        ), f"Feedback should come from teaching agent (agent1), got '{feedback_msg.role}'"
        feedback_content = feedback_msg.content
        print(f"\n=== FEEDBACK MESSAGE (from agent1) ===\n{feedback_content}\n")

        # Feedback should acknowledge correctness
        feedback_indicators = ["correct", "great", "good", "right", "✓"]
        has_feedback = any(word in feedback_content.lower() for word in feedback_indicators)
        assert has_feedback, f"Should provide positive feedback, got: {feedback_content[:200]}"

        # Exercise should be completed or cleared
        assert result["pending_exercise"] is None or result["pending_exercise"].metadata.get(
            "completed"
        ), "Exercise should be marked as completed after answer"

        print("\n=== COMPLETE FLOW VALIDATED (Steps 1-4) ===")
        print("✓ Lesson start with navigation options")
        print("✓ User chose vocabulary → received vocab batch")
        print("✓ User requested quiz → agent3 generated → agent1 presented")
        print("✓ User answered → agent2 graded → agent1 provided feedback")
        print(f"Total messages: {len(result['conversation_history'])}")
        print("\nComplete agent flow:")
        print(
            "  teaching → user → teaching → user → content → teaching → user → grading → teaching"
        )
        print(
            f"\nStats: {result['total_exercises_completed']} exercises, "
            f"{result['total_correct_answers']} correct"
        )

    def test_lesson_start_awaits_user_doesnt_auto_teach(self, real_orchestrator):
        """
        Test that lesson start doesn't automatically jump into teaching.

        After welcome message, system should WAIT for user choice, not auto-teach.
        """
        state = SystemState(
            user_id="test_user",
            session_id="test_session_wait",
            current_lesson=1,
            conversation_history=[],
            next_agent="teaching",
            last_agent="",
        )

        result = real_orchestrator.invoke(state)

        # Should have exactly 1 message (the welcome)
        assert len(result["conversation_history"]) == 1, "Should only have welcome message"

        # Should be waiting for user input
        assert result["next_agent"] == "user", "Should wait for user, not auto-continue"

        # Should NOT have switched to any teaching mode yet
        assert (
            result.get("current_mode") is None or result.get("current_mode") == ""
        ), f"Should not be in teaching mode yet, got: {result.get('current_mode')}"

        # Should NOT have any exercises
        assert result["pending_exercise"] is None, "Should not have exercises at start"
