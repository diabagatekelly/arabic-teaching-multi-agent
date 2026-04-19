"""FastAPI + Gradio proof of concept with simple agent.

Demonstrates:
- FastAPI backend with agent endpoint
- Gradio UI mounted in FastAPI
- Works with HuggingFace Spaces @spaces.GPU
- GPU function isolated in engine.py for reliable ZeroGPU detection
"""

import gradio as gr
import spaces
from fastapi import FastAPI
from gradio import mount_gradio_app

from content_loader import load_lesson
from engine import process_message as engine_process_message


# Define your GPU-enabled function with @spaces.GPU decorator
@spaces.GPU(duration=60)
def process_message(message, chat_history, session_id):
    """GPU-enabled message processing."""
    return engine_process_message(message, chat_history, session_id)


# Initialize FastAPI
app = FastAPI(title="Arabic Teaching API")

# Global lesson cache (loaded at startup, shared across all users)
lesson_cache = {}

# Per-user session store
sessions = {}


@app.on_event("startup")
def load_all_lessons():
    """Pre-load all lesson content at startup for fast access."""
    print("===== Loading lessons into cache =====")
    for lesson_num in range(1, 11):  # Lessons 1-10
        try:
            lesson_data = load_lesson(lesson_num)
            lesson_cache[lesson_num] = lesson_data
            print(f"✓ Loaded Lesson {lesson_num}: {lesson_data['lesson_name']}")
        except FileNotFoundError:
            print(f"✗ Lesson {lesson_num} not found, skipping")
    print(f"===== {len(lesson_cache)} lessons cached =====")


@app.get("/api/health")
def read_root():
    """Health check endpoint."""
    return {"status": "ok", "message": "Arabic Teaching API is running"}


@app.post("/api/chat")
def chat_endpoint(session_id: str, message: str):
    """
    Simple chat endpoint with basic agent logic.

    Args:
        session_id: Session identifier
        message: User message

    Returns:
        Agent response
    """
    # Initialize session if needed
    if session_id not in sessions:
        sessions[session_id] = {"history": [], "count": 0}

    session = sessions[session_id]
    session["count"] += 1

    # Simple agent logic (proof of concept)
    if "hello" in message.lower():
        response = f"مرحباً! Hello! This is message #{session['count']}"
    elif "vocab" in message.lower():
        response = "📚 Vocabulary mode activated!"
    elif "grammar" in message.lower():
        response = "📖 Grammar mode activated!"
    else:
        response = f"I heard: {message}. Message #{session['count']}"

    # Store in history
    session["history"].append({"user": message, "agent": response})

    return {"response": response, "session_id": session_id}


@app.get("/api/session/{session_id}")
def get_session(session_id: str):
    """Get session info."""
    if session_id not in sessions:
        return {"error": "Session not found"}
    return sessions[session_id]


@app.post("/api/start_lesson")
def start_lesson(session_id: str, lesson_number: int):
    """
    Start a lesson and load content from cache.

    Args:
        session_id: Session identifier
        lesson_number: Lesson number to start

    Returns:
        Lesson info and content
    """
    # Initialize session if needed
    if session_id not in sessions:
        sessions[session_id] = {"history": [], "count": 0}

    # Get lesson from cache
    if lesson_number not in lesson_cache:
        return {"error": f"Lesson {lesson_number} not found"}

    lesson_data = lesson_cache[lesson_number]

    # Store lesson data in session
    sessions[session_id]["lesson_number"] = lesson_number
    sessions[session_id]["lesson_name"] = lesson_data["lesson_name"]
    sessions[session_id]["vocabulary"] = lesson_data["vocabulary"]
    sessions[session_id]["grammar_sections"] = lesson_data["grammar_sections"]
    sessions[session_id]["mode"] = "vocab"

    return {
        "lesson_number": lesson_number,
        "lesson_name": lesson_data["lesson_name"],
        "vocab_count": len(lesson_data["vocabulary"]),
        "status": "started",
    }


# GPU function imported from engine.py for ZeroGPU detection


# Build Gradio interface with 3-column layout
with gr.Blocks(title="Arabic Teacher - FastAPI Demo") as demo:
    gr.Markdown("# 🌍 Arabic Teacher")

    with gr.Row():
        # Left panel - Flashcards (1/4 width)
        with gr.Column(scale=1):
            gr.Markdown("### 📚 Flashcards")
            flashcard_display = gr.Markdown("Click 'Next Card' to start")
            flashcard_progress = gr.Textbox(label="Progress", value="0/6", interactive=False)
            next_card_btn = gr.Button("Next Card")

        # Center panel - Chat (1/2 width)
        with gr.Column(scale=2):
            gr.Markdown("### 💬 Chat")
            # type="messages" only works in Gradio 5.x (Spaces), not local 6.12
            try:
                chatbot = gr.Chatbot(height=500, type="messages")
            except TypeError:
                chatbot = gr.Chatbot(height=500)
            msg = gr.Textbox(
                label="Your message",
                placeholder="Try: hello, vocab, grammar...",
            )
            with gr.Row():
                submit = gr.Button("Send", variant="primary")
                clear = gr.Button("Clear")

        # Right panel - Info/Controls (1/4 width)
        with gr.Column(scale=1):
            gr.Markdown("### ℹ️ Lesson Info")
            lesson_info = gr.Markdown("**Lesson:** Not started\n\n**Mode:** None")
            start_lesson_btn = gr.Button("Start Lesson 1", variant="primary")

    session_id = gr.State("")

    def start_lesson_ui(sid):
        """Start lesson and update UI."""
        import uuid

        import requests

        if not sid:
            sid = str(uuid.uuid4())[:8]

        response = requests.post(
            "http://localhost:7860/api/start_lesson", params={"session_id": sid, "lesson_number": 1}
        )
        data = response.json()

        info_text = f"**Lesson:** {data['lesson_name']}\n\n**Status:** {data['status']}"
        return info_text, sid

    # Wire up the GPU-accelerated function
    msg.submit(process_message, [msg, chatbot, session_id], [msg, chatbot])
    submit.click(process_message, [msg, chatbot, session_id], [msg, chatbot])
    clear.click(lambda: [], None, chatbot)
    start_lesson_btn.click(start_lesson_ui, [session_id], [lesson_info, session_id])


# Mount Gradio app inside FastAPI
mount_gradio_app(app, demo, path="/")

if __name__ == "__main__":
    import uvicorn

    # Port 7860 is required for HuggingFace Spaces
    uvicorn.run(app, host="0.0.0.0", port=7860)
