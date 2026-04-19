"""FastAPI + Gradio proof of concept with simple agent.

Demonstrates:
- FastAPI backend with agent endpoint
- Gradio UI mounted in FastAPI
- Works with HuggingFace Spaces @spaces.GPU
- GPU function isolated in engine.py for reliable ZeroGPU detection
"""

import gradio as gr
import spaces
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

from content_loader import load_lesson

# Load teaching model at module level (required for ZeroGPU)
print("===== Loading Qwen 7B Teaching Model =====")
model_name = "Qwen/Qwen2.5-7B-Instruct"
tokenizer = AutoTokenizer.from_pretrained(model_name)
teaching_model = AutoModelForCausalLM.from_pretrained(
    model_name,
    torch_dtype=torch.float16,
    device_map="auto",
)
teaching_model.to("cuda")
print("===== Model loaded =====")

# TODO: Load LoRA adapter for teaching model when available
# from peft import PeftModel
# teaching_model = PeftModel.from_pretrained(teaching_model, "path/to/adapter")


# Define your GPU-enabled function with @spaces.GPU decorator
@spaces.GPU(duration=60)
def process_message(message, chat_history, session_id):
    """GPU-enabled message processing with Qwen model."""
    # Build chat history for model
    messages = []
    for msg in chat_history:
        if msg["role"] == "user":
            messages.append({"role": "user", "content": msg["content"]})
        elif msg["role"] == "assistant":
            messages.append({"role": "assistant", "content": msg["content"]})

    # Add current message
    messages.append({"role": "user", "content": message})

    # Generate response using Qwen model
    text = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
    model_inputs = tokenizer([text], return_tensors="pt").to(teaching_model.device)

    generated_ids = teaching_model.generate(
        **model_inputs,
        max_new_tokens=512,
        temperature=0.7,
    )
    generated_ids = [
        output_ids[len(input_ids) :]
        for input_ids, output_ids in zip(model_inputs.input_ids, generated_ids, strict=False)
    ]

    response = tokenizer.batch_decode(generated_ids, skip_special_tokens=True)[0]

    # Update chat history
    chat_history.append({"role": "user", "content": message})
    chat_history.append({"role": "assistant", "content": response})

    return "", chat_history


# Global lesson cache (loaded at startup, shared across all users)
lesson_cache = {}

# Per-user session store
sessions = {}

# Load all lessons at module level
print("===== Loading lessons into cache =====")
for lesson_num in range(1, 11):  # Lessons 1-10
    try:
        lesson_data = load_lesson(lesson_num)
        lesson_cache[lesson_num] = lesson_data
        print(f"✓ Loaded Lesson {lesson_num}: {lesson_data['lesson_name']}")
    except FileNotFoundError:
        print(f"✗ Lesson {lesson_num} not found, skipping")
print(f"===== {len(lesson_cache)} lessons cached =====")


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

        # Right panel - Controls & Progress (1/4 width)
        with gr.Column(scale=1):
            gr.Markdown("### 🎮 Lesson Controls")
            start_lesson_btn = gr.Button("Start Lesson", variant="primary")
            with gr.Row():
                end_lesson_btn = gr.Button("⏹️ End Lesson", variant="secondary", scale=1)
                reset_lesson_btn = gr.Button("🔄 Reset", variant="stop", scale=1)

            gr.Markdown("### 📊 Progress")
            lesson_info = gr.Markdown("**Status:** Not started")
            progress_display = gr.Markdown("**Learned:** 0 words\n\n**Quizzes:** 0/0")

    session_id = gr.State("")

    def start_lesson_ui(sid):
        """Start lesson and initialize session."""
        import uuid

        if not sid:
            sid = str(uuid.uuid4())[:8]

        # Get lesson from cache
        lesson_number = 1
        if lesson_number not in lesson_cache:
            return "**Status:** Error - Lesson not found", "**Learned:** 0 words", sid

        lesson_data = lesson_cache[lesson_number]

        # Initialize session with lesson data
        if sid not in sessions:
            sessions[sid] = {}

        sessions[sid].update(
            {
                "lesson_number": lesson_number,
                "lesson_name": lesson_data["lesson_name"],
                "vocabulary": lesson_data["vocabulary"],
                "grammar_sections": lesson_data["grammar_sections"],
                "learned_words": [],
                "quiz_scores": [],
                "status": "active",
            }
        )

        lesson_info = f"""**Status:** Active

**Lesson {lesson_number}:** {lesson_data['lesson_name']}

**Total Vocab:** {len(lesson_data['vocabulary'])} words
**Grammar:** {', '.join(lesson_data['grammar_points'])}
"""
        progress = "**Learned:** 0 words\n\n**Quizzes:** 0/0"
        return lesson_info, progress, sid

    def end_lesson_ui(sid):
        """End lesson - session saved but marked inactive."""
        if sid in sessions and "status" in sessions[sid]:
            sessions[sid]["status"] = "ended"
            learned = len(sessions[sid].get("learned_words", []))
            quizzes = len(sessions[sid].get("quiz_scores", []))

            lesson_info = f"""**Status:** Ended

**Lesson:** {sessions[sid].get('lesson_name', 'Unknown')}
**Session saved** ✓
"""
            progress = f"**Learned:** {learned} words\n\n**Quizzes:** {quizzes} completed"
        else:
            lesson_info = "**Status:** No active lesson"
            progress = "**Learned:** 0 words\n\n**Quizzes:** 0/0"

        return lesson_info, progress

    def reset_lesson_ui(sid):
        """Reset lesson - wipes session cache and progress."""
        if sid in sessions:
            # Clear all lesson data from session
            del sessions[sid]

        lesson_info = "**Status:** Reset complete\n\n*Session data cleared*"
        progress = "**Learned:** 0 words\n\n**Quizzes:** 0/0"
        return lesson_info, progress

    # Wire up chat functions
    msg.submit(process_message, [msg, chatbot, session_id], [msg, chatbot])
    submit.click(process_message, [msg, chatbot, session_id], [msg, chatbot])
    clear.click(lambda: [], None, chatbot)

    # Wire up lesson control functions
    start_lesson_btn.click(
        start_lesson_ui, [session_id], [lesson_info, progress_display, session_id]
    )
    end_lesson_btn.click(end_lesson_ui, [session_id], [lesson_info, progress_display])
    reset_lesson_btn.click(reset_lesson_ui, [session_id], [lesson_info, progress_display])


# Launch Gradio (standard for Spaces)
demo.launch()
