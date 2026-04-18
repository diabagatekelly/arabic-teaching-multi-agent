"""Gradio UI for Arabic Teaching Multi-Agent System with Zero-GPU support.

HuggingFace Space entry point with GPU acceleration.
"""

import logging
from datetime import datetime

import gradio as gr
import spaces

from src.agents import ContentAgent, GradingAgent, TeachingAgent
from src.models.hf_model_loader import load_grading_model, load_teaching_model
from src.orchestrator.graph import create_teaching_graph
from src.orchestrator.state import Message, SystemState

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global components (loaded once)
orchestrator = None
current_state = None


def initialize_models():
    """Initialize models and orchestrator (runs once at startup)."""
    global orchestrator

    logger.info("Loading fine-tuned models...")

    try:
        # Load teaching model (7B fine-tuned)
        teaching_model, teaching_tokenizer = load_teaching_model()

        # Load grading model (7B fine-tuned)
        grading_model, grading_tokenizer = load_grading_model()

        # Create agents
        teaching_agent = TeachingAgent(
            model=teaching_model,
            tokenizer=teaching_tokenizer,
            max_new_tokens=256,
        )

        grading_agent = GradingAgent(
            model=grading_model,
            tokenizer=grading_tokenizer,
            max_new_tokens=50,
        )

        content_agent = ContentAgent(
            model=teaching_model,  # Reuse teaching model
            tokenizer=teaching_tokenizer,
            max_new_tokens=512,
        )

        # Create orchestrator
        orchestrator = create_teaching_graph(
            teaching_agent=teaching_agent,
            grading_agent=grading_agent,
            content_agent=content_agent,
        )

        logger.info("✓ All components initialized")
        return "✓ Models loaded successfully!"

    except Exception as e:
        logger.error(f"Failed to initialize: {e}")
        return f"❌ Initialization failed: {e}"


@spaces.GPU(duration=120)  # Reserve GPU for 120 seconds per call
def start_lesson(lesson_number: int, chat_history: list) -> tuple:
    """
    Start a new lesson (GPU-accelerated).

    Args:
        lesson_number: Lesson to start (1-10)
        chat_history: Current chat history

    Returns:
        Tuple of (updated_chat, exercises, correct, accuracy, learned_items, status)
    """
    global current_state

    logger.info(f"Starting lesson {lesson_number}...")

    try:
        # Create initial state
        initial_state = SystemState(
            user_id="user_1",
            session_id=f"session_{lesson_number}_{int(datetime.now().timestamp())}",
            current_lesson=lesson_number,
            conversation_history=[],
            next_agent="teaching",
            last_agent="",
        )

        # Run orchestrator (GPU-accelerated model inference)
        result = orchestrator.invoke(initial_state)

        # Update global state
        current_state = result

        # Extract welcome message
        conversation_history = result.get("conversation_history", [])
        if conversation_history:
            last_message = conversation_history[-1]
            if hasattr(last_message, "role") and last_message.role == "agent1":
                welcome_msg = last_message.content
            elif isinstance(last_message, dict) and last_message.get("role") == "agent1":
                welcome_msg = last_message.get("content", "")
            else:
                welcome_msg = "Welcome to the lesson!"
        else:
            welcome_msg = "Welcome to the lesson!"

        # Update chat history
        chat_history.append((None, welcome_msg))

        # Update progress stats
        exercises = result.get("total_exercises_completed", 0)
        correct = result.get("total_correct_answers", 0)
        accuracy = f"{(correct / exercises * 100):.1f}%" if exercises > 0 else "0%"
        learned = ", ".join(list(result.get("learned_items", [])))[:100]

        status = f"✓ Lesson {lesson_number} started!"

        return chat_history, exercises, correct, accuracy, learned, status

    except Exception as e:
        logger.error(f"Failed to start lesson: {e}")
        return chat_history, 0, 0, "0%", "", f"❌ Error: {e}"


@spaces.GPU(duration=120)  # Reserve GPU for inference
def send_message(user_message: str, chat_history: list) -> tuple:
    """
    Process user message (GPU-accelerated).

    Args:
        user_message: User's input
        chat_history: Current chat history

    Returns:
        Tuple of (updated_chat, exercises, correct, accuracy, learned_items, cleared_input)
    """
    global current_state

    if not current_state:
        chat_history.append((user_message, "⚠️ Please start a lesson first!"))
        return chat_history, 0, 0, "0%", "", ""

    if not user_message.strip():
        return chat_history, 0, 0, "0%", "", ""

    logger.info(f"Processing user message: {user_message[:50]}...")

    try:
        # Add user message to state
        user_msg = Message(role="user", content=user_message)
        current_state["conversation_history"].append(user_msg)

        # Set next agent (grading if pending exercise AND awaiting answer, teaching otherwise)
        # FIX: Check both pending_exercise AND awaiting_user_answer
        # This prevents auto-grading of non-answer messages like "quiz time!"
        if current_state.get("pending_exercise") and current_state.get("awaiting_user_answer"):
            current_state["next_agent"] = "grading"
        else:
            current_state["next_agent"] = "teaching"

        # Run orchestrator (GPU-accelerated)
        result = orchestrator.invoke(current_state)

        # Update global state
        current_state = result

        # Extract agent response - skip agent3 messages (exercises), find last agent1/agent2
        conversation_history = result.get("conversation_history", [])
        agent_response = None
        if conversation_history:
            # Loop through messages in reverse, skip agent3
            for msg in reversed(conversation_history):
                msg_role = msg.role if hasattr(msg, "role") else msg.get("role")

                if msg_role in ["agent1", "agent2", "assistant"]:
                    agent_response = (
                        msg.content if hasattr(msg, "content") else msg.get("content", "")
                    )
                    break

        # Fallback if no agent message found
        if not agent_response:
            agent_response = "I'm here to help!"

        # Update chat history
        chat_history.append((user_message, agent_response))

        # Update progress stats
        exercises = result.get("total_exercises_completed", 0)
        correct = result.get("total_correct_answers", 0)
        accuracy = f"{(correct / exercises * 100):.1f}%" if exercises > 0 else "0%"
        learned = ", ".join(list(result.get("learned_items", [])))[:100]

        return chat_history, exercises, correct, accuracy, learned, ""  # Clear input

    except Exception as e:
        logger.error(f"Error processing message: {e}")
        chat_history.append((user_message, f"❌ Error: {e}"))
        return chat_history, 0, 0, "0%", "", ""


# Build Gradio interface
with gr.Blocks(title="Arabic Teaching System", theme=gr.themes.Soft()) as app:
    gr.Markdown("# 🇸🇦 Arabic Teaching System")
    gr.Markdown("Learn Arabic through interactive lessons powered by fine-tuned AI agents")

    with gr.Row():
        # Left column: Chat
        with gr.Column(scale=3):
            chatbot = gr.Chatbot(
                label="Chat with your Arabic teacher",
                height=500,
                show_label=True,
            )

            with gr.Row():
                msg = gr.Textbox(
                    label="Your response",
                    placeholder="Type your answer here...",
                    scale=4,
                )
                send_btn = gr.Button("Send", variant="primary", scale=1)

        # Right column: Controls & Progress
        with gr.Column(scale=1):
            gr.Markdown("### 📚 Lesson Selection")
            lesson_dropdown = gr.Dropdown(
                choices=list(range(1, 11)),
                value=1,
                label="Choose a lesson",
            )
            start_btn = gr.Button("Start New Lesson", variant="primary", size="lg")
            status_box = gr.Textbox(label="Status", interactive=False)

            gr.Markdown("---")
            gr.Markdown("### 📊 Progress")

            exercises_count = gr.Number(label="Exercises Completed", value=0, interactive=False)
            correct_count = gr.Number(label="Correct Answers", value=0, interactive=False)
            accuracy_display = gr.Textbox(label="Accuracy", value="0%", interactive=False)
            learned_items = gr.Textbox(
                label="Learned Items",
                value="",
                interactive=False,
                lines=3,
            )

            gr.Markdown("---")
            gr.Markdown("### ℹ️ System Info")
            gr.Markdown("**Teaching:** Fine-tuned Qwen2.5-7B")
            gr.Markdown("**Grading:** Fine-tuned Qwen2.5-7B")
            gr.Markdown("**GPU:** Zero-GPU (HuggingFace)")

    # Event handlers
    start_btn.click(
        fn=start_lesson,
        inputs=[lesson_dropdown, chatbot],
        outputs=[
            chatbot,
            exercises_count,
            correct_count,
            accuracy_display,
            learned_items,
            status_box,
        ],
    )

    send_btn.click(
        fn=send_message,
        inputs=[msg, chatbot],
        outputs=[chatbot, exercises_count, correct_count, accuracy_display, learned_items, msg],
    )

    msg.submit(
        fn=send_message,
        inputs=[msg, chatbot],
        outputs=[chatbot, exercises_count, correct_count, accuracy_display, learned_items, msg],
    )

    # Initialize on load
    app.load(fn=initialize_models, outputs=[status_box])


if __name__ == "__main__":
    app.launch()
