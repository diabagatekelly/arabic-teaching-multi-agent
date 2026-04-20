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
content_model_name = "Qwen/Qwen2.5-7B-Instruct"  # 7B base for ContentAgent

# Load tokenizers globally (CPU-safe)
teaching_tokenizer = AutoTokenizer.from_pretrained(teaching_model_name)
content_tokenizer = AutoTokenizer.from_pretrained(content_model_name)

# Global model variables
teaching_model = None
content_model = None

# Load models at startup (both local and ZeroGPU)
print("===== Loading models at startup =====")

# Teaching model (7B + LoRA)
print(f"===== Loading TeachingAgent base: {teaching_model_name} =====")
base_model = AutoModelForCausalLM.from_pretrained(
    teaching_model_name,
    torch_dtype=torch.float16,
    device_map="cpu" if ZEROGPU else "auto",  # CPU for ZeroGPU, auto for local
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
    device_map="cpu" if ZEROGPU else "auto",  # CPU for ZeroGPU, auto for local
)
print(f"===== ContentAgent ready on device: {content_model.device} =====")

if ZEROGPU:
    print("===== ZEROGPU: Models loaded on CPU, will move to GPU inside @spaces.GPU calls =====")

# Initialize RAG retriever (CPU-bound, safe for all environments)
print("===== Initializing RAG retriever =====")
embedder = SentenceTransformerClient()
vector_db = PineconeClient()
rag_retriever = RAGRetriever(embedder, vector_db)
print("===== RAG retriever initialized =====")


# Define your GPU-enabled function with @spaces.GPU decorator
@spaces.GPU(duration=60)
def process_message(message, chat_history, session_id):
    """GPU-enabled message processing through orchestrator."""
    # Reload sessions from file (ZeroGPU isolation) - update in-place
    sessions.clear()
    sessions.update(load_sessions())

    logger.info("=" * 80)
    logger.info("[App] USER INPUT CAPTURED")
    logger.info(f"  Message: {message}")
    logger.info(f"  Session ID: {session_id}")
    logger.info(f"  Session ID type: {type(session_id)}")
    logger.info(f"  Chat history length: {len(chat_history)}")
    logger.info(f"  Sessions dict keys: {list(sessions.keys())}")
    logger.info(f"  Session exists: {session_id in sessions}")

    if session_id in sessions:
        logger.info(f"  Session status: {sessions[session_id].get('status')}")
        logger.info(f"  Session data: {list(sessions[session_id].keys())}")

    # Check if lesson is active
    if session_id not in sessions or sessions[session_id].get("status") != "active":
        logger.warning("[App] No active lesson - returning error message")
        logger.warning(f"  Condition 1 - session_id not in sessions: {session_id not in sessions}")
        if session_id in sessions:
            logger.warning(
                f"  Condition 2 - status not active: {sessions[session_id].get('status') != 'active'}"
            )
            logger.warning(f"  Actual status: {sessions[session_id].get('status')}")
        error_msg = "Please start a lesson first using the 'Start Lesson' button."
        chat_history.append({"role": "user", "content": message})
        chat_history.append({"role": "assistant", "content": error_msg})
        return "", chat_history

    logger.info("[App] Routing to orchestrator.handle_message()")

    # Route through orchestrator
    response = orchestrator.handle_message(session_id, message)

    # Save sessions after orchestrator updates state
    save_sessions(sessions)

    logger.info("[App] Received response from orchestrator")
    logger.info(f"  Response length: {len(response)} chars")
    logger.info(f"  Response preview: {response[:100]}...")

    # Update chat history
    chat_history.append({"role": "user", "content": message})
    chat_history.append({"role": "assistant", "content": response})

    logger.info(f"[App] Updated chat history, new length: {len(chat_history)}")
    logger.info("=" * 80)

    # Check if we need to update flashcards (user chose vocab)
    session = sessions.get(session_id, {})
    current_progress = session.get("current_progress", "")
    flashcard_update = ""

    if current_progress == "vocab_batch_intro":
        # Trigger flashcard update by changing the trigger value
        import time

        flashcard_update = str(time.time())

    # Update progress display
    progress_text = _build_progress_display(session)

    return "", chat_history, flashcard_update, progress_text


def _build_progress_display(session):
    """Build progress display from session state - matches orchestrator progress report."""
    if not session:
        return "**Vocabulary:**\n○ No progress yet\n\n**Grammar:**\n○ No progress yet"

    progress_lines = []

    # Vocabulary progress
    progress_lines.append("**Vocabulary:**")
    vocab_state = session.get("vocabulary", {})
    all_vocab = vocab_state.get("words", [])
    current_batch = vocab_state.get("current_batch", 1)
    total_batches = (len(all_vocab) + 2) // 3  # Ceiling division

    for batch_num in range(1, total_batches + 1):
        batch_start = (batch_num - 1) * 3
        batch_end = min(batch_start + 3, len(all_vocab))
        batch_words = all_vocab[batch_start:batch_end]

        if batch_num < current_batch:
            # Completed batch
            progress_lines.append(f"  ✓ Batch {batch_num}")
            progress_lines.append(f"     {len(batch_words)} words")
        elif batch_num == current_batch:
            # Current batch
            progress_lines.append(f"  → Batch {batch_num}")
            progress_lines.append(f"     {len(batch_words)} words")
        else:
            # Not started
            progress_lines.append(f"  ○ Batch {batch_num}")
            progress_lines.append(f"     {len(batch_words)} words")

    # Grammar progress
    progress_lines.append("\n**Grammar:**")
    grammar_topics = session.get("grammar", {}).get("topics", {})
    lesson_number = session.get("lesson_number")

    if lesson_number and lesson_number in lesson_cache:
        lesson_data = lesson_cache[lesson_number]
        for topic_name in lesson_data.get("grammar_points", []):
            # Convert underscore keys to display names
            topic_display = topic_name.replace("_", " ").title()
            topic_state = grammar_topics.get(topic_name, {})
            if topic_state.get("taught", False):
                score = topic_state.get("quiz_score", "N/A")
                progress_lines.append(f"  ✓ {topic_display}")
                progress_lines.append(f"     Score: {score}")
            else:
                progress_lines.append(f"  ○ {topic_display}")
    else:
        progress_lines.append("  ○ No topics available")

    return "\n".join(progress_lines)


# Global lesson cache (loaded from JSON file)
lesson_cache = {}

# Per-user session store (file-based for ZeroGPU persistence)
SESSION_FILE = Path(__file__).parent / "sessions.json"


def load_sessions():
    """Load sessions from file."""
    if SESSION_FILE.exists():
        with open(SESSION_FILE, encoding="utf-8") as f:
            return json.load(f)
    return {}


def save_sessions(sessions_dict):
    """Save sessions to file."""
    with open(SESSION_FILE, "w", encoding="utf-8") as f:
        json.dump(sessions_dict, f, ensure_ascii=False, indent=2)


sessions = load_sessions()
logger.info(f"===== Loaded {len(sessions)} sessions from file =====")

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


# Helper functions to get models (move to GPU if on ZeroGPU)
def get_teaching_model():
    """Get the teaching model, moving to GPU if necessary."""
    global teaching_model
    if ZEROGPU and str(teaching_model.device) == "cpu":
        print("===== Moving TeachingAgent to GPU =====")
        teaching_model = teaching_model.to("cuda")
    return teaching_model


def get_content_model():
    """Get the content model, moving to GPU if necessary."""
    global content_model
    if ZEROGPU and str(content_model.device) == "cpu":
        print("===== Moving ContentAgent to GPU =====")
        content_model = content_model.to("cuda")
    return content_model


# Initialize ContentAgent with RAG
print("===== Initializing ContentAgent =====")
content_agent = ContentAgent(
    model=content_model,  # Model already loaded at startup
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
with gr.Blocks(
    title="Arabic Learning Companion",
    css="""
    .flashcard {
        padding: 60px 20px;
        min-height: 250px;
        display: flex;
        align-items: center;
        justify-content: center;
        text-align: center;
        background-color: #f9f9f9;
        font-size: 2em;
        font-weight: 500;
        margin-top: 0;
    }
    .main-title {
        text-align: center;
        font-size: 2em;
        margin-bottom: 0.5em;
        margin-top: 0;
    }
    /* Fix double scrollbar in chatbot */
    .chatbot {
        overflow: hidden !important;
    }
    /* Remove top margin from section headers */
    h3 {
        margin-top: 0 !important;
    }
    """,
) as demo:
    with gr.Row():
        # Left panel - Flashcards (1/4 width)
        with gr.Column(scale=1):
            gr.Markdown("### 📚 Flashcards", elem_classes=["section-header"])
            flashcard_display = gr.Markdown(
                "*Start a lesson to see flashcards*", visible=True, elem_classes=["flashcard"]
            )
            flashcard_progress = gr.Textbox(
                label="Progress", value="0/0", interactive=False, visible=True
            )
            with gr.Row():
                flip_card_btn = gr.Button("Flip Card", size="sm", visible=True)
                next_card_btn = gr.Button("Next Card", size="sm", visible=True)

        # Center panel - Chat (1/2 width)
        with gr.Column(scale=2):
            gr.Markdown("# 🌟 Arabic Learning Companion", elem_classes=["main-title"])
            # type="messages" only works in Gradio 5.x (Spaces), not local 6.12
            try:
                chatbot = gr.Chatbot(height=600, type="messages", elem_classes=["chatbot"])
            except TypeError:
                chatbot = gr.Chatbot(height=600, elem_classes=["chatbot"])
            msg = gr.Textbox(
                label="Your message",
                placeholder="Try: hello, vocab, grammar...",
            )
            with gr.Row():
                submit = gr.Button("Send", variant="primary")
                stop = gr.Button("Stop", variant="stop")
                clear = gr.Button("Clear")

        # Right panel - Controls & Progress (1/4 width)
        with gr.Column(scale=1):
            gr.Markdown("### 🎮 Lesson Controls")
            start_lesson_btn = gr.Button("Start Lesson", variant="primary")
            with gr.Row():
                end_lesson_btn = gr.Button("⏹️ End Lesson", variant="secondary", scale=1)
                reset_lesson_btn = gr.Button("🔄 Reset", variant="stop", scale=1)

            gr.Markdown("### 📖 About")
            lesson_info = gr.Markdown("**Status:** Not started")

            gr.Markdown("### 📊 Progress")
            progress_display = gr.Markdown(
                "**Vocabulary:**\n○ No progress yet\n\n**Grammar:**\n○ No progress yet"
            )

    session_id = gr.State("")  # String type for session ID
    flashcard_state = gr.State(
        {"current_index": 0, "flipped": False, "cards": [], "visible": False}
    )
    flashcard_trigger = gr.Textbox(visible=False)  # Hidden trigger for flashcard updates

    def flip_flashcard(state):
        """Flip the current flashcard."""
        if not state["cards"]:
            return state, "*No flashcards available*"

        state["flipped"] = not state["flipped"]
        card = state["cards"][state["current_index"]]

        if state["flipped"]:
            # Show Arabic + transliteration
            display = f"### {card['arabic']}\n\n*{card['transliteration']}*"
        else:
            # Show English
            display = f"### {card['english']}"

        return state, display

    def next_flashcard(state):
        """Move to next flashcard."""
        if not state["cards"]:
            return state, "*No flashcards available*", "0/0"

        state["current_index"] = (state["current_index"] + 1) % len(state["cards"])
        state["flipped"] = False

        card = state["cards"][state["current_index"]]
        display = f"### {card['english']}"
        progress = f"{state['current_index'] + 1}/{len(state['cards'])}"

        return state, display, progress

    def update_flashcards(sid, state):
        """Update flashcards - shows all learned vocab except during quizzes/tests."""
        sessions.clear()
        sessions.update(load_sessions())

        if sid not in sessions:
            return (
                state,
                "*Start a lesson to see flashcards*",
                "0/0",
                gr.update(visible=False),
                gr.update(visible=False),
                gr.update(visible=False),
            )

        session = sessions[sid]
        current_progress = session.get("current_progress", "")

        # Hide flashcards only during quizzes and tests
        hide_flashcards = current_progress in [
            "vocab_quiz",
            "grammar_quiz",
            "final_test",
        ]

        if hide_flashcards:
            # Hide flashcards during assessment
            return (
                state,
                "*Flashcards hidden during quiz*",
                "0/0",
                gr.update(visible=False),
                gr.update(visible=False),
                gr.update(visible=False),
            )

        # Show all vocabulary learned so far (all batches up to current)
        current_batch = session.get("vocabulary", {}).get("current_batch", 1)
        all_vocab = session.get("vocabulary", {}).get("words", [])

        # Get all words from completed and current batches
        batch_size = 3
        total_words_learned = min(current_batch * batch_size, len(all_vocab))
        learned_words = all_vocab[:total_words_learned]

        if not learned_words:
            return (
                state,
                "*No vocabulary learned yet*",
                "0/0",
                gr.update(visible=True),
                gr.update(visible=True),
                gr.update(visible=True),
            )

        # Update flashcard state with all learned words
        state["cards"] = learned_words
        state["current_index"] = 0
        state["flipped"] = False

        # Show first card (English side)
        display = f"### {learned_words[0]['english']}"
        progress = f"1/{len(learned_words)}"

        return (
            state,
            display,
            progress,
            gr.update(visible=True),
            gr.update(visible=True),
            gr.update(visible=True),
        )

    @spaces.GPU(duration=60)
    def start_lesson_ui(sid):
        """Start lesson and initialize session."""
        import uuid

        # Reload sessions from file (ZeroGPU isolation) - update in-place
        sessions.clear()
        sessions.update(load_sessions())

        if not sid:
            sid = str(uuid.uuid4())[:8]

        logger.info("=" * 80)
        logger.info("[App] START LESSON UI CALLED")
        logger.info(f"  Session ID: {sid}")
        logger.info(f"  Session ID type: {type(sid)}")
        logger.info(f"  Sessions before: {list(sessions.keys())}")

        # Get lesson from cache
        lesson_number = 1
        if lesson_number not in lesson_cache:
            return "**Status:** Error - Lesson not found", "**Learned:** 0 words", [], sid

        # Call orchestrator to start lesson (updates session, generates welcome)
        welcome_message = orchestrator.start_lesson(sid, lesson_number)

        # Save sessions to file for ZeroGPU persistence
        save_sessions(sessions)

        logger.info(f"  Sessions after: {list(sessions.keys())}")
        logger.info(f"  Session created: {sid in sessions}")
        if sid in sessions:
            logger.info(f"  Session status: {sessions[sid].get('status')}")
        logger.info("=" * 80)

        lesson_data = lesson_cache[lesson_number]
        # Convert grammar point keys to display names
        grammar_display = [gp.replace("_", " ").title() for gp in lesson_data["grammar_points"]]

        lesson_info = f"""**Status:** Active

**Lesson {lesson_number}:** {lesson_data['lesson_name']}

**Total Vocab:** {len(lesson_data['vocabulary'])} words

**Grammar:** {', '.join(grammar_display)}
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

    # Wire up flashcard functions
    flip_card_btn.click(flip_flashcard, [flashcard_state], [flashcard_state, flashcard_display])
    next_card_btn.click(
        next_flashcard, [flashcard_state], [flashcard_state, flashcard_display, flashcard_progress]
    )

    # Auto-update flashcards when trigger changes (includes visibility)
    flashcard_trigger.change(
        update_flashcards,
        [session_id, flashcard_state],
        [
            flashcard_state,
            flashcard_display,
            flashcard_progress,
            flashcard_display,
            flip_card_btn,
            next_card_btn,
        ],
    )

    # Wire up chat functions
    submit_event = msg.submit(
        process_message,
        [msg, chatbot, session_id],
        [msg, chatbot, flashcard_trigger, progress_display],
    )
    click_event = submit.click(
        process_message,
        [msg, chatbot, session_id],
        [msg, chatbot, flashcard_trigger, progress_display],
    )

    # Stop button cancels ongoing inference
    stop.click(None, None, None, cancels=[submit_event, click_event])

    clear.click(lambda: [], None, chatbot)

    # Wire up lesson control functions
    start_lesson_btn.click(
        start_lesson_ui, [session_id], [lesson_info, progress_display, chatbot, session_id]
    )
    end_lesson_btn.click(end_lesson_ui, [session_id], [lesson_info, progress_display])
    reset_lesson_btn.click(reset_lesson_ui, [session_id], [lesson_info, progress_display])


# Launch Gradio (standard for Spaces)
demo.launch()
