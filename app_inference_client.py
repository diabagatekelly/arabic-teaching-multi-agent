"""Streamlit UI using HuggingFace InferenceClient with automatic provider routing.

Uses InferenceClient to call your models via HF's inference API.
No local loading, no endpoints needed - just your model repo names!
"""

import logging
import os
import sys
from datetime import datetime
from pathlib import Path

import streamlit as st
import torch
from openai import OpenAI

# Add project root to path for src imports
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.orchestrator.graph import create_teaching_graph  # noqa: E402
from src.orchestrator.state import SystemState  # noqa: E402

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Page config
st.set_page_config(
    page_title="Arabic Teaching System",
    page_icon="🇸🇦",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS
st.markdown(
    """
<style>
    .stChatMessage {
        padding: 1rem;
        border-radius: 0.5rem;
        margin-bottom: 0.5rem;
    }
    .flashcard {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 2rem;
        border-radius: 1rem;
        text-align: center;
        margin: 1rem 0;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }
    .flashcard .arabic {
        font-size: 3rem;
        font-weight: bold;
        margin-bottom: 0.5rem;
    }
    .flashcard .transliteration {
        font-size: 1.5rem;
        opacity: 0.9;
        margin-bottom: 0.5rem;
    }
    .flashcard .english {
        font-size: 1.2rem;
        opacity: 0.8;
    }
    .progress-stat {
        background: #f7fafc;
        padding: 1rem;
        border-radius: 0.5rem;
        margin-bottom: 0.5rem;
        text-align: center;
    }
    .progress-stat .value {
        font-size: 2rem;
        font-weight: bold;
        color: #667eea;
    }
    .progress-stat .label {
        font-size: 0.9rem;
        color: #718096;
    }
</style>
""",
    unsafe_allow_html=True,
)

# HuggingFace Inference Endpoints (OpenAI-compatible API)
TEACHING_BASE_URL = "https://i8t2iza4o432viu2.us-east-1.aws.endpoints.huggingface.cloud/v1/"
TEACHING_MODEL = "kdiabagate/qwen-7b-arabic-teaching-merged"
GRADING_BASE_URL = "https://r80z32jw87buldc0.us-east-1.aws.endpoints.huggingface.cloud/v1/"
GRADING_MODEL = "kdiabagate/qwen-7b-arabic-grading-merged"
HF_TOKEN = os.getenv("HF_TOKEN", "")  # Use empty string if not set


class MockDevice:
    """Mock device object for API compatibility."""

    type = "api"


class InferenceClientWrapper:
    """Wrapper to make OpenAI client compatible with transformers model interface."""

    def __init__(
        self,
        base_url: str,
        model_name: str,
        api_key: str | None = None,
        max_new_tokens: int = 512,
    ):
        """Initialize OpenAI client for HF endpoint."""
        self.client = OpenAI(base_url=base_url, api_key=api_key)
        self.model_name = model_name
        self.max_new_tokens = max_new_tokens
        self.device = MockDevice()
        self._last_prompt = None  # Store last prompt from tokenizer

    def generate(self, input_ids=None, attention_mask=None, max_new_tokens=None, **kwargs):
        """
        Generate method matching transformers model.generate() interface.

        Returns a mock output that agents can decode via tokenizer.
        """
        # Use stored prompt if available (set by our TokenizerStub)
        if self._last_prompt:
            prompt = self._last_prompt
        else:
            logger.warning("No prompt stored - using empty string")
            prompt = ""

        max_tokens = max_new_tokens or self.max_new_tokens

        try:
            logger.info(f"Calling HF Endpoint (OpenAI API): {self.model_name}")
            logger.info(f"Prompt preview: {prompt[:200]}...")

            # Use OpenAI chat completions API
            chat_completion = self.client.chat.completions.create(
                model=self.model_name,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=max_tokens,
                temperature=0.7,
                top_p=0.9,
                stream=False,
            )

            response_text = chat_completion.choices[0].message.content

            logger.info(f"Got response from {self.model_name}: {response_text[:150]}...")

            # Store response so tokenizer can return it
            self._last_response = response_text

            # Return mock tensor (agents expect tensor output from generate())
            return torch.tensor([[0]])

        except Exception as e:
            logger.error(f"Endpoint error: {e}", exc_info=True)
            self._last_response = f"Error: {e}"
            return torch.tensor([[0]])

    def to(self, device: str):
        """No-op for API compatibility."""
        return self


class TokenizerStub:
    """Stub tokenizer for InferenceClient."""

    def __init__(self, model_wrapper=None):
        """Initialize with reference to model wrapper."""
        self.model_wrapper = model_wrapper
        self.pad_token_id = 0
        self.eos_token_id = 0

    def __call__(self, text, return_tensors=None, **kwargs):
        """Store prompt in model wrapper for later use."""
        if self.model_wrapper:
            self.model_wrapper._last_prompt = text

        # Return object with .to() method (agents expect this)
        class MockEncoding:
            def __init__(self):
                self.data = {
                    "input_ids": torch.tensor([[0]]),
                    "attention_mask": torch.tensor([[1]]),
                }

            def to(self, device):
                return self

            def get(self, key, default=None):
                return self.data.get(key, default)

            def __getitem__(self, key):
                return self.data[key]

        return MockEncoding()

    def apply_chat_template(self, messages, tokenize=False, add_generation_prompt=True, **kwargs):
        """Convert messages to prompt string."""
        if isinstance(messages, list):
            parts = []
            for msg in messages:
                if isinstance(msg, dict):
                    content = msg.get("content", "")
                    parts.append(content)
                else:
                    parts.append(str(msg))
            return "\n\n".join(parts)
        return str(messages)

    def decode(self, token_ids, skip_special_tokens=True, **kwargs):
        """Return the stored response from model wrapper."""
        if self.model_wrapper and hasattr(self.model_wrapper, "_last_response"):
            return self.model_wrapper._last_response
        return ""


@st.cache_resource
def initialize_orchestrator():
    """Initialize inference clients and orchestrator (cached)."""
    logger.info("Initializing InferenceClient connections...")

    try:
        # Create OpenAI clients for your HF endpoints
        teaching_client = InferenceClientWrapper(
            base_url=TEACHING_BASE_URL,
            model_name=TEACHING_MODEL,
            api_key=HF_TOKEN,
            max_new_tokens=512,
        )

        grading_client = InferenceClientWrapper(
            base_url=GRADING_BASE_URL,
            model_name=GRADING_MODEL,
            api_key=HF_TOKEN,
            max_new_tokens=50,
        )

        # Create tokenizer stubs linked to their model wrappers
        teaching_tokenizer = TokenizerStub(model_wrapper=teaching_client)
        grading_tokenizer = TokenizerStub(model_wrapper=grading_client)

        # Create agents
        from src.agents import ContentAgent, GradingAgent, TeachingAgent

        teaching_agent = TeachingAgent(
            model=teaching_client,
            tokenizer=teaching_tokenizer,
            max_new_tokens=512,
        )

        grading_agent = GradingAgent(
            model=grading_client,
            tokenizer=grading_tokenizer,
            max_new_tokens=50,
        )

        # Initialize RAG (embedder only, runs locally)
        from src.rag.lesson_content_loader import LessonContentLoader
        from src.rag.pinecone_client import PineconeClient
        from src.rag.rag_retriever import RAGRetriever
        from src.rag.sentence_transformer_client import SentenceTransformerClient

        embedder_model = SentenceTransformerClient()
        vector_db = PineconeClient()
        rag_retriever = RAGRetriever(embedder_model, vector_db)
        content_loader = LessonContentLoader(rag_retriever)

        content_agent = ContentAgent(
            model=teaching_client,
            tokenizer=teaching_tokenizer,  # Reuse teaching tokenizer
            max_new_tokens=512,
            content_loader=content_loader,
        )

        # Create orchestrator
        orchestrator = create_teaching_graph(
            teaching_agent=teaching_agent,
            grading_agent=grading_agent,
            content_agent=content_agent,
        )

        logger.info("✓ Orchestrator initialized with InferenceClient")
        return orchestrator

    except Exception as e:
        logger.error(f"Failed to initialize: {e}")
        st.error(f"❌ Initialization failed: {e}")
        st.stop()


def render_progress_sidebar():
    """Render progress tracking in sidebar."""
    st.sidebar.title("📊 Progress")

    if "system_state" in st.session_state and st.session_state.system_state:
        state = st.session_state.system_state
        exercises = state.get("total_exercises_completed", 0)
        correct = state.get("total_correct_answers", 0)
        accuracy = f"{(correct / exercises * 100):.1f}%" if exercises > 0 else "0%"

        st.sidebar.markdown(
            f"""
        <div class="progress-stat">
            <div class="value">{exercises}</div>
            <div class="label">Exercises Completed</div>
        </div>
        """,
            unsafe_allow_html=True,
        )

        st.sidebar.markdown(
            f"""
        <div class="progress-stat">
            <div class="value">{correct}</div>
            <div class="label">Correct Answers</div>
        </div>
        """,
            unsafe_allow_html=True,
        )

        st.sidebar.markdown(
            f"""
        <div class="progress-stat">
            <div class="value">{accuracy}</div>
            <div class="label">Accuracy</div>
        </div>
        """,
            unsafe_allow_html=True,
        )

        learned_items = list(state.get("learned_items", []))
        if learned_items:
            st.sidebar.markdown("### 📚 Learned Items")
            for item in learned_items[-5:]:
                st.sidebar.markdown(f"- {item}")


def extract_agent_response(conversation_history: list) -> str:
    """Extract last agent response."""
    for msg in reversed(conversation_history):
        msg_role = msg.role if hasattr(msg, "role") else msg.get("role")
        if msg_role in ["agent1", "agent2", "assistant"]:
            content = msg.content if hasattr(msg, "content") else msg.get("content", "")
            if content:
                return content
    return "I'm here to help!"


def start_lesson(lesson_number: int):
    """Start a new lesson."""
    logger.info(f"Starting lesson {lesson_number}...")

    try:
        orchestrator = initialize_orchestrator()

        initial_state = SystemState(
            user_id="user_1",
            session_id=f"session_{lesson_number}_{int(datetime.now().timestamp())}",
            current_lesson=lesson_number,
            conversation_history=[],
            next_agent="agent1",
            last_agent="",
        )

        result = orchestrator.invoke(initial_state)

        st.session_state.system_state = result
        st.session_state.messages = []

        conversation_history = result.get("conversation_history", [])
        welcome_msg = extract_agent_response(conversation_history)

        st.session_state.messages.append({"role": "assistant", "content": welcome_msg})

        st.success(f"✓ Lesson {lesson_number} started!")

    except Exception as e:
        logger.error(f"Failed to start lesson: {e}")
        st.error(f"❌ Error: {e}")


def send_message_stream(user_message: str):
    """Process user message and stream response."""
    if not st.session_state.get("system_state"):
        st.warning("⚠️ Please start a lesson first!")
        return

    logger.info(f"Processing: {user_message[:50]}...")

    try:
        orchestrator = initialize_orchestrator()
        current_state = SystemState.from_dict(st.session_state.system_state)
        current_state.add_message("user", user_message)

        if current_state.pending_exercise and current_state.awaiting_user_answer:
            current_state.next_agent = "agent2"
        else:
            current_state.next_agent = "agent1"

        result = orchestrator.invoke(current_state)
        st.session_state.system_state = result

        conversation_history = result.get("conversation_history", [])
        agent_response = extract_agent_response(conversation_history)

        # Stream word by word
        words = agent_response.split()
        for i, word in enumerate(words):
            yield word + " "
            if i < len(words) - 1:
                import time

                time.sleep(0.05)

    except Exception as e:
        logger.error(f"Error: {e}")
        yield f"❌ Error: {e}"


def main():
    st.title("🇸🇦 Arabic Teaching System")
    st.markdown("Powered by HuggingFace InferenceClient")

    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "system_state" not in st.session_state:
        st.session_state.system_state = None

    with st.sidebar:
        st.title("📚 Lesson Selection")

        lesson_number = st.selectbox("Choose a lesson", options=list(range(1, 11)), index=0)

        if st.button("Start New Lesson", type="primary", use_container_width=True):
            start_lesson(lesson_number)
            st.rerun()

        st.markdown("---")
        render_progress_sidebar()
        st.markdown("---")

        st.markdown("### ℹ️ System Info")
        st.markdown("**Teaching:** HF Endpoint (fine-tuned 7B)")
        st.markdown("**Grading:** HF Endpoint (fine-tuned 7B)")
        st.markdown("**Status:** Using your deployed models!")

    # Chat display
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # Chat input
    if prompt := st.chat_input("Type your answer here..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            full_response = st.write_stream(send_message_stream(prompt))
            if full_response:
                st.session_state.messages.append({"role": "assistant", "content": full_response})

        st.rerun()


if __name__ == "__main__":
    main()
