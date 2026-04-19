"""Gradio UI for Arabic Teaching Multi-Agent System with Zero-GPU support.

HuggingFace Space entry point with GPU acceleration.
"""

import logging
import sys
from datetime import datetime
from pathlib import Path

import gradio as gr
import spaces
import torch

# Add project root to path for src imports
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.agents import ContentAgent, GradingAgent, TeachingAgent  # noqa: E402
from src.models.hf_model_loader import load_grading_model, load_teaching_model  # noqa: E402
from src.orchestrator.graph import create_teaching_graph  # noqa: E402
from src.orchestrator.state import Message, SystemState  # noqa: E402

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global components (loaded once)
orchestrator = None
current_state = None
teaching_model = None
grading_model = None
embedder_model = None

# Device detection
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
logger.info(f"Using device: {DEVICE}")


def initialize_models():
    """Initialize models and orchestrator (runs once at startup)."""
    global orchestrator, teaching_model, grading_model, embedder_model, current_state

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
            max_new_tokens=512,  # Increased for complete responses
        )

        grading_agent = GradingAgent(
            model=grading_model,
            tokenizer=grading_tokenizer,
            max_new_tokens=50,
        )

        # Initialize RAG retriever and content loader
        from src.rag.lesson_content_loader import LessonContentLoader
        from src.rag.pinecone_client import PineconeClient
        from src.rag.rag_retriever import RAGRetriever
        from src.rag.sentence_transformer_client import SentenceTransformerClient

        embedder_model = SentenceTransformerClient()
        vector_db = PineconeClient()
        rag_retriever = RAGRetriever(embedder_model, vector_db)
        content_loader = LessonContentLoader(rag_retriever)

        content_agent = ContentAgent(
            model=teaching_model,  # Reuse teaching model
            tokenizer=teaching_tokenizer,
            max_new_tokens=512,
            content_loader=content_loader,
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
    global current_state, teaching_model, grading_model, embedder_model

    # Move models to device (GPU on Spaces, CPU locally)
    logger.info(f"Moving models to {DEVICE}...")
    teaching_model.to(DEVICE)
    grading_model.to(DEVICE)
    embedder_model.model.to(DEVICE)

    logger.info(f"Starting lesson {lesson_number}...")

    try:
        # Create initial state - content will be loaded by TeachingNode
        initial_state = SystemState(
            user_id="user_1",
            session_id=f"session_{lesson_number}_{int(datetime.now().timestamp())}",
            current_lesson=lesson_number,
            conversation_history=[],
            next_agent="agent1",
            last_agent="",
        )

        # Run orchestrator (GPU-accelerated model inference)
        result = orchestrator.invoke(initial_state)

        # Update global state
        current_state = result

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

        # Update chat history (Gradio format: list of [user_msg, bot_msg] tuples)
        # For initial welcome, add empty user message
        chat_history.append([None, welcome_msg])

        exercises, correct, accuracy, learned = _format_progress_stats(result)

        status = f"✓ Lesson {lesson_number} started!"

        return chat_history, exercises, correct, accuracy, learned, status

    except Exception as e:
        logger.error(f"Failed to start lesson: {e}")
        return chat_history, 0, 0, "0%", "", f"❌ Error: {e}"


def _extract_agent_response(conversation_history: list) -> str:
    """Extract last agent response, skipping agent3 messages."""
    for msg in reversed(conversation_history):
        msg_role = msg.role if hasattr(msg, "role") else msg.get("role")
        if msg_role in ["agent1", "agent2", "assistant"]:
            content = msg.content if hasattr(msg, "content") else msg.get("content", "")
            # Preserve fallback for empty/None content
            if content:
                return content
    return "I'm here to help!"


def _format_progress_stats(result: dict) -> tuple:
    """Format progress statistics for UI display."""
    exercises = result.get("total_exercises_completed", 0)
    correct = result.get("total_correct_answers", 0)
    accuracy = f"{(correct / exercises * 100):.1f}%" if exercises > 0 else "0%"
    learned = ", ".join(list(result.get("learned_items", [])))[:100]
    return exercises, correct, accuracy, learned


@spaces.GPU(duration=120)
def send_message(user_message: str, chat_history: list):
    """
    Process user message (GPU-accelerated).

    Args:
        user_message: User's input
        chat_history: Current chat history

    Returns:
        Tuple of (updated_chat, exercises, correct, accuracy, learned_items, cleared_input)
    """
    global current_state, teaching_model, grading_model, embedder_model

    # Move models to device (GPU on Spaces, CPU locally)
    teaching_model.to(DEVICE)
    grading_model.to(DEVICE)
    embedder_model.model.to(DEVICE)

    if not current_state:
        chat_history.append([user_message, "⚠️ Please start a lesson first!"])
        return chat_history, 0, 0, "0%", "", ""

    if not user_message.strip():
        return chat_history, 0, 0, "0%", "", ""

    logger.info(f"Processing user message: {user_message[:50]}...")

    try:
        user_msg = Message(role="user", content=user_message)
        # Convert to dict for LangGraph compatibility
        current_state["conversation_history"].append(
            {
                "role": user_msg.role,
                "content": user_msg.content,
                "timestamp": user_msg.timestamp.isoformat(),
                "metadata": user_msg.metadata,
            }
        )

        if current_state.get("pending_exercise") and current_state.get("awaiting_user_answer"):
            current_state["next_agent"] = "agent2"  # Route to grading agent
        else:
            current_state["next_agent"] = "agent1"  # Route to teaching agent

        result = orchestrator.invoke(current_state)
        current_state = result

        conversation_history = result.get("conversation_history", [])
        agent_response = _extract_agent_response(conversation_history)

        chat_history.append([user_message, agent_response])

        exercises, correct, accuracy, learned = _format_progress_stats(result)

        return chat_history, exercises, correct, accuracy, learned, ""

    except Exception as e:
        logger.error(f"Error processing message: {e}")
        chat_history.append([user_message, f"❌ Error: {e}"])
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
    app.launch(server_name="0.0.0.0", server_port=7860)
