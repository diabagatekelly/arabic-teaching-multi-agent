"""FastAPI + Gradio proof of concept with simple agent.

Demonstrates:
- FastAPI backend with agent endpoint
- Gradio UI mounted in FastAPI
- Works with HuggingFace Spaces @spaces.GPU
- GPU function isolated in engine.py for reliable ZeroGPU detection
"""

import json
import logging
import os
from pathlib import Path

import gradio as gr
import spaces
import torch
from peft import PeftModel
from transformers import AutoModelForCausalLM, AutoTokenizer

from src.agents.content_agent import ContentAgent
from src.orchestrator.orchestrator import Orchestrator
from src.rag.pinecone_client import PineconeClient
from src.rag.rag_retriever import RAGRetriever
from src.rag.sentence_transformer_client import SentenceTransformerClient

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Environment detection

ZEROGPU = os.getenv("SPACE_ID") is not None  # Running on HuggingFace Spaces
LOCAL_DEV = not ZEROGPU  # Running locally

# Model names
teaching_model_name = "Qwen/Qwen2.5-7B-Instruct"
teaching_adapter_name = "kdiabagate/qwen-7b-arabic-teaching-v2"
content_model_name = "Qwen/Qwen2.5-3B-Instruct"  # 3B for ContentAgent

# Load tokenizers globally (CPU-safe)
teaching_tokenizer = AutoTokenizer.from_pretrained(teaching_model_name)
content_tokenizer = AutoTokenizer.from_pretrained(content_model_name)

# Global model variables
teaching_model = None
content_model = None

# Load models at startup for local dev (no ZeroGPU restrictions)
if LOCAL_DEV:
    print("===== LOCAL_DEV: Loading models at startup =====")

    # Teaching model (7B + LoRA)
    print(f"===== Loading TeachingAgent model: {teaching_model_name} =====")
    base_model = AutoModelForCausalLM.from_pretrained(
        teaching_model_name,
        torch_dtype=torch.float16,
        device_map="auto",
    )
    print(f"===== Loading LoRA adapter: {teaching_adapter_name} =====")
    teaching_model = PeftModel.from_pretrained(base_model, teaching_adapter_name)
    print("===== Merging LoRA weights =====")
    teaching_model = teaching_model.merge_and_unload()
    print(f"===== TeachingAgent ready on device: {teaching_model.device} =====")

    # Content model (3B base)
    print(f"===== Loading ContentAgent model: {content_model_name} =====")
    content_model = AutoModelForCausalLM.from_pretrained(
        content_model_name,
        torch_dtype=torch.float16,
        device_map="auto",
    )
    print(f"===== ContentAgent ready on device: {content_model.device} =====")
else:
    print("===== ZEROGPU: Models will be lazy-loaded on first use =====")

# Initialize RAG retriever (CPU-bound, safe for all environments)
print("===== Initializing RAG retriever =====")
embedder = SentenceTransformerClient()
vector_db = PineconeClient()
rag_retriever = RAGRetriever(embedder, vector_db)
print("===== RAG retriever initialized =====")


# Define your GPU-enabled function with @spaces.GPU decorator
@spaces.GPU(duration=60)
def process_message(message, chat_history, session_id):
    """GPU-enabled message processing with Qwen model."""
    # Get model (lazy loads if needed)
    model = get_teaching_model()

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
    text = teaching_tokenizer.apply_chat_template(
        messages, tokenize=False, add_generation_prompt=True
    )
    model_inputs = teaching_tokenizer([text], return_tensors="pt").to(model.device)

    generated_ids = model.generate(
        **model_inputs,
        max_new_tokens=512,
        temperature=0.7,
    )
    generated_ids = [
        output_ids[len(input_ids) :]
        for input_ids, output_ids in zip(model_inputs.input_ids, generated_ids, strict=False)
    ]

    response = teaching_tokenizer.batch_decode(generated_ids, skip_special_tokens=True)[0]

    # Update chat history
    chat_history.append({"role": "user", "content": message})
    chat_history.append({"role": "assistant", "content": response})

    return "", chat_history


# Global lesson cache (loaded from JSON file)
lesson_cache = {}

# Per-user session store
sessions = {}

# Load lesson cache from pre-built JSON file
print("===== Loading lesson cache =====")
cache_file = Path(__file__).parent / "lesson_cache.json"
if cache_file.exists():
    with open(cache_file, encoding="utf-8") as f:
        cache_data = json.load(f)
        # Convert string keys back to integers
        lesson_cache = {int(k): v for k, v in cache_data.items()}
    print(f"===== Loaded {len(lesson_cache)} lessons from cache =====")
else:
    print("===== WARNING: lesson_cache.json not found, using empty cache =====")
    print("===== Run scripts/build_lesson_cache.py to generate it =====")


# Helper functions to get models (lazy loaded for ZeroGPU)
def get_teaching_model():
    """Get the teaching model, loading it if necessary."""
    global teaching_model
    if teaching_model is None:
        print(f"===== Loading TeachingAgent base: {teaching_model_name} =====")
        base_model = AutoModelForCausalLM.from_pretrained(
            teaching_model_name,
            torch_dtype=torch.float16,
            device_map="cuda",
        )
        print(f"===== Loading LoRA adapter: {teaching_adapter_name} =====")
        teaching_model = PeftModel.from_pretrained(base_model, teaching_adapter_name)
        print("===== Merging LoRA weights =====")
        teaching_model = teaching_model.merge_and_unload()
        print(f"===== TeachingAgent ready on: {teaching_model.device} =====")
    return teaching_model


def get_content_model():
    """Get the content model, loading it if necessary."""
    global content_model
    if content_model is None:
        print(f"===== Loading ContentAgent model: {content_model_name} =====")
        content_model = AutoModelForCausalLM.from_pretrained(
            content_model_name,
            torch_dtype=torch.float16,
            device_map="cuda",
        )
        print(f"===== ContentAgent ready on: {content_model.device} =====")
    return content_model


# Initialize ContentAgent with RAG
print("===== Initializing ContentAgent =====")
content_agent = ContentAgent(
    model=get_content_model() if LOCAL_DEV else None,  # Lazy load on ZeroGPU
    tokenizer=content_tokenizer,
    max_new_tokens=512,
)
content_agent.rag_retriever = rag_retriever  # Wire up RAG
print("===== ContentAgent initialized =====")

# Initialize orchestrator with all agents
orchestrator = Orchestrator(
    lesson_cache=lesson_cache,
    sessions=sessions,
    teaching_model_getter=get_teaching_model,
    teaching_tokenizer=teaching_tokenizer,
    content_agent=content_agent,
)
print("===== Orchestrator initialized =====")


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

    @spaces.GPU(duration=60)
    def start_lesson_ui(sid):
        """Start lesson and initialize session."""
        import uuid

        if not sid:
            sid = str(uuid.uuid4())[:8]

        # Get lesson from cache
        lesson_number = 1
        if lesson_number not in lesson_cache:
            return "**Status:** Error - Lesson not found", "**Learned:** 0 words", [], sid

        # Call orchestrator to start lesson (updates session, generates welcome)
        welcome_message = orchestrator.start_lesson(sid, lesson_number)

        lesson_data = lesson_cache[lesson_number]
        lesson_info = f"""**Status:** Active

**Lesson {lesson_number}:** {lesson_data['lesson_name']}

**Total Vocab:** {len(lesson_data['vocabulary'])} words
**Grammar:** {', '.join(lesson_data['grammar_points'])}
"""
        progress = "**Learned:** 0 words\n\n**Quizzes:** 0/0"

        # Initialize chat with welcome message
        chat_history = [{"role": "assistant", "content": welcome_message}]

        return lesson_info, progress, chat_history, sid

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
        start_lesson_ui, [session_id], [lesson_info, progress_display, chatbot, session_id]
    )
    end_lesson_btn.click(end_lesson_ui, [session_id], [lesson_info, progress_display])
    reset_lesson_btn.click(reset_lesson_ui, [session_id], [lesson_info, progress_display])


# Launch Gradio (standard for Spaces)
demo.launch()
