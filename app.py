"""FastAPI + Gradio proof of concept with simple agent.

Demonstrates:
- FastAPI backend with agent endpoint
- Gradio UI mounted in FastAPI
- Works with HuggingFace Spaces @spaces.GPU
"""

import gradio as gr
import spaces
from fastapi import FastAPI

# Initialize FastAPI
app = FastAPI(title="Arabic Teaching API")

# Simple in-memory session store
sessions = {}


@app.get("/")
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


# GPU-accelerated agent function (must be at module level for Spaces detection)
@spaces.GPU(duration=60)
def process_message(message, chat_history, session_id):
    """Process user message with agent (GPU-accelerated)."""
    import uuid

    # Generate session ID if not provided
    if not session_id:
        session_id = str(uuid.uuid4())[:8]

    # Simple agent logic
    if "hello" in message.lower():
        response = "مرحباً! Hello!"
    elif "vocab" in message.lower():
        response = "📚 Vocabulary mode activated!"
    elif "grammar" in message.lower():
        response = "📖 Grammar mode activated!"
    else:
        response = f"Echo: {message}"

    # Use messages format
    chat_history.append({"role": "user", "content": message})
    chat_history.append({"role": "assistant", "content": response})
    return "", chat_history


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
            chatbot = gr.Chatbot(height=500, type="messages")
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

    # Wire up the GPU-accelerated function
    msg.submit(process_message, [msg, chatbot, session_id], [msg, chatbot])
    submit.click(process_message, [msg, chatbot, session_id], [msg, chatbot])
    clear.click(lambda: [], None, chatbot)


# Mount Gradio in FastAPI
app = gr.mount_gradio_app(app, demo, path="/")

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=7860)
