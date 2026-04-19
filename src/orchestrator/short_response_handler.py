"""Short response handler for orchestrator.

Transforms short user responses (numbers, yes/no, ok/sure) into clear intents
based on conversation context, without needing LLM interpretation.
"""

import re

from src.orchestrator.state import Message


def transform_short_response(user_input: str, conversation_history: list[Message]) -> str:
    """
    Transform short responses into clear intents based on conversation context.

    Args:
        user_input: User's short response (e.g., "yes", "1", "ok")
        conversation_history: Full conversation history

    Returns:
        Transformed input (clear intent) or original if not a short response

    Examples:
        >>> # After "Ready for Batch 2?"
        >>> transform_short_response("yes", history)
        "give me batch 2"

        >>> # After "Want 1. vocabulary or 2. grammar?"
        >>> transform_short_response("1", history)
        "vocabulary"

        >>> # After "Want to take a quiz?"
        >>> transform_short_response("ok", history)
        "start quiz"
    """
    # Normalize input
    normalized_input = user_input.strip().lower()

    # Define short response patterns
    affirmative_responses = ["yes", "yeah", "yep", "yup", "ok", "sure", "alright"]
    negative_responses = ["no", "nope", "nah"]
    numeric_responses = ["1", "2", "3", "4", "5"]

    # Check if it's a short response
    is_short_response = (
        normalized_input in affirmative_responses + negative_responses + numeric_responses
    )

    if not is_short_response:
        return user_input  # Not a short response, return original

    # Get last assistant message
    if not conversation_history:
        return user_input  # No context, return original

    last_message = None
    for msg in reversed(conversation_history):
        if msg.role == "assistant":
            last_message = msg.content
            break

    if not last_message:
        return user_input  # No assistant message found

    last_message_lower = last_message.lower()

    # Handle numbered responses (e.g., "1", "2")
    if normalized_input in numeric_responses:
        # Look for numbered options like "1. vocabulary or 2. grammar"
        numbered_pattern = r"(\d+)\.\s*([a-z]+)"
        matches = re.findall(numbered_pattern, last_message_lower)

        if matches:
            # Find the option corresponding to the user's number
            for num, option in matches:
                if num == normalized_input:
                    return option

        # No numbered options found, return original
        return user_input

    # Handle negative responses
    if normalized_input in negative_responses:
        return "not yet"

    # Handle affirmative responses - detect intent from last message
    if normalized_input in affirmative_responses:
        # Check for keywords in last message
        if "batch" in last_message_lower:
            # Extract batch number if present
            batch_match = re.search(r"batch\s+(\d+)", last_message_lower)
            if batch_match:
                batch_num = batch_match.group(1)
                return f"give me batch {batch_num}"
            return "give me next batch"

        if "quiz" in last_message_lower or "test" in last_message_lower:
            return "start quiz"

        if "vocab" in last_message_lower:
            return "teach me vocabulary"

        if "grammar" in last_message_lower:
            return "teach me grammar"

        # Generic affirmative with no clear context
        return "continue"

    # Fallback
    return user_input
