"""FastAPI + Gradio proof of concept with simple agent.

Demonstrates:
- FastAPI backend with agent endpoint
- Gradio UI mounted in FastAPI
- Works with HuggingFace Spaces @spaces.GPU
- GPU function isolated in engine.py for reliable ZeroGPU detection
"""

import logging
import re

import gradio as gr
import spaces
import torch
from peft import PeftModel
from transformers import AutoModelForCausalLM, AutoTokenizer

from src.orchestrator.orchestrator import Orchestrator
from src.rag.pinecone_client import PineconeClient
from src.rag.rag_retriever import RAGRetriever
from src.rag.sentence_transformer_client import SentenceTransformerClient

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load teaching model at module level (required for ZeroGPU)
print("===== Loading Base Qwen 7B Model =====")
base_model_name = "Qwen/Qwen2.5-7B-Instruct"
adapter_model_name = "kdiabagate/qwen-7b-arabic-teaching-v2"

tokenizer = AutoTokenizer.from_pretrained(base_model_name)
base_model = AutoModelForCausalLM.from_pretrained(
    base_model_name,
    torch_dtype=torch.float16,
    device_map="auto",
)
print("===== Base model loaded, loading LoRA adapter =====")

# Load LoRA adapter
teaching_model = PeftModel.from_pretrained(base_model, adapter_model_name)
print("===== LoRA adapter merged =====")

# Only move to cuda if available (for HuggingFace Spaces)
if torch.cuda.is_available():
    teaching_model.to("cuda")
print("===== Fine-tuned model ready =====")

# TODO: Load LoRA adapter for teaching model when available
# from peft import PeftModel
# teaching_model = PeftModel.from_pretrained(teaching_model, "path/to/adapter")

# Initialize RAG retriever
print("===== Initializing RAG retriever =====")
embedder = SentenceTransformerClient()
vector_db = PineconeClient()
rag_retriever = RAGRetriever(embedder, vector_db)
print("===== RAG retriever initialized =====")


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


# Global lesson cache (populated from RAG retrieval)
lesson_cache = {}

# Per-user session store
sessions = {}

# Build lesson cache by retrieving from Pinecone
print("===== Building lesson cache from RAG =====")
for lesson_num in range(1, 11):  # Lessons 1-10
    try:
        # Retrieve vocabulary section from Pinecone
        vocab_results = rag_retriever.retrieve_by_lesson(
            query="vocabulary words list table", lesson_number=lesson_num, top_k=10
        )

        # Retrieve grammar sections from Pinecone
        grammar_results = rag_retriever.retrieve_by_lesson(
            query="grammar rules points topics", lesson_number=lesson_num, top_k=10
        )

        if not vocab_results and not grammar_results:
            print(f"✗ No results found in Pinecone for Lesson {lesson_num}")
            continue

        # Extract metadata from first result
        metadata = (vocab_results[0] if vocab_results else grammar_results[0]).get("metadata", {})

        # Parse vocabulary from retrieved markdown table
        vocab_list = []
        for result in vocab_results:
            text = result.get("text", "")
            # Extract vocabulary entries from markdown table
            # Looking for lines like: | كِتَابٌ | kitaabun | book |
            table_rows = re.findall(r"\|\s*([^\|]+)\s*\|\s*([^\|]+)\s*\|\s*([^\|]+)\s*\|", text)
            for row in table_rows:
                if (
                    row[0].strip()
                    and not row[0].strip().startswith("--")
                    and row[0].strip() != "Arabic"
                ):
                    vocab_list.append(
                        {
                            "arabic": row[0].strip(),
                            "transliteration": row[1].strip(),
                            "english": row[2].strip(),
                        }
                    )

        # Get grammar points from metadata
        grammar_points = metadata.get("grammar_points", [])
        if isinstance(grammar_points, str):
            # Parse JSON string if needed
            import json

            try:
                grammar_points = json.loads(grammar_points)
            except (json.JSONDecodeError, TypeError):
                grammar_points = [grammar_points]

        lesson_data = {
            "lesson_number": lesson_num,
            "lesson_name": metadata.get("lesson_name", f"Lesson {lesson_num}"),
            "vocabulary": vocab_list,
            "grammar_points": grammar_points,
            "grammar_sections": {},  # Could extract from grammar_results if needed
            "difficulty": metadata.get("difficulty", "beginner"),
        }

        lesson_cache[lesson_num] = lesson_data
        print(
            f"✓ Cached Lesson {lesson_num}: {lesson_data['lesson_name']} ({len(vocab_list)} words)"
        )

    except Exception as e:
        print(f"✗ Error caching lesson {lesson_num}: {e}")
        import traceback

        traceback.print_exc()

print(f"===== {len(lesson_cache)} lessons cached =====")

# Initialize orchestrator
orchestrator = Orchestrator(lesson_cache, sessions, teaching_model, tokenizer)
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
