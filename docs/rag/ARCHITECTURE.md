# RAG Architecture & Implementation

**Last Updated:** 2026-04-18  
**Status:** Production - Integrated with orchestrator

---

## Overview

The RAG (Retrieval-Augmented Generation) system provides lesson content (vocabulary, grammar) to the teaching agents by querying a vector database. The architecture follows **Dependency Inversion Principle** for flexibility and testability.

---

## Architecture: Dependency Inversion

### Key Principle: Depend on Abstractions

**Problem:** Directly depending on `PineconeClient` creates tight coupling:
- Hard to test (requires mocking Pinecone API)
- Hard to switch providers (Qdrant, Weaviate, Chroma)
- Hard to experiment with different backends

**Solution:** Define `VectorDatabase` Protocol that both real and mock implementations satisfy.

### Structure

```
src/rag/
├── vector_database.py          # Abstract interface (Protocol)
├── pinecone_client.py           # Concrete Pinecone implementation
├── rag_retriever.py             # Query orchestration
├── sentence_transformer_client.py  # Embedding generation
├── lesson_content_loader.py     # High-level content loading
└── __init__.py                  # Public exports
```

### Usage Pattern

```python
from src.rag.vector_database import VectorDatabase
from src.rag.pinecone_client import PineconeClient

class RAGOrchestrator:
    def __init__(self, vector_store: VectorDatabase):
        # Depends on abstraction, not concrete implementation
        self.vector_store = vector_store
    
    def search(self, query_vector: list[float]) -> list:
        return self.vector_store.query(query_vector)

# Production: inject Pinecone
orchestrator = RAGOrchestrator(PineconeClient(api_key="..."))

# Testing: inject mock
orchestrator = RAGOrchestrator(MockVectorDatabase())

# Future: easily switch providers
orchestrator = RAGOrchestrator(QdrantClient())
```

**Benefits:**
- Easy to test with mocks
- Easy to swap implementations
- Follows SOLID principles
- Application code never imports Pinecone directly

---

## Production Implementation

### 1. Vector Database Stack

**Backend:** Pinecone Serverless (us-east-1)
- **Index:** `arabic-teaching`
- **Dimensions:** 384
- **Metric:** Cosine similarity
- **Content:** 40+ chunks from Lesson 1 (expandable to all lessons)

**Embedding Model:** `all-MiniLM-L6-v2` (SentenceTransformers)
- Lightweight (80MB)
- Fast inference
- Good for semantic search
- 384-dimensional embeddings

### 2. Component Layers

#### Layer 1: Vector Database (Pinecone)
```python
from src.rag.pinecone_client import PineconeClient

client = PineconeClient(
    index_name="arabic-teaching",
    dimension=384,
    api_key=os.environ["PINECONE_API_KEY"]
)

# Upsert vectors
client.upsert(vectors=[
    {"id": "lesson_1_vocab_1", "values": [0.1, 0.2, ...], "metadata": {...}}
])

# Query
results = client.query(query_vector=[0.1, 0.2, ...], top_k=5)
```

#### Layer 2: RAG Retriever (Query Orchestration)
```python
from src.rag.rag_retriever import RAGRetriever
from src.rag.sentence_transformer_client import SentenceTransformerClient

embedder = SentenceTransformerClient(model_name="all-MiniLM-L6-v2")
retriever = RAGRetriever(embedder, vector_db)

# Retrieve by lesson
chunks = retriever.retrieve_by_lesson(
    query="vocabulary words",
    lesson_number=1,
    top_k=10
)
```

#### Layer 3: Lesson Content Loader (High-Level Interface)
```python
from src.rag.lesson_content_loader import LessonContentLoader

loader = LessonContentLoader(retriever)

# Load structured vocabulary
vocab = loader.load_vocabulary(lesson_number=1)
# Returns: [{"arabic": "كِتَاب", "transliteration": "kitaab", "english": "book", "word_id": "w1"}, ...]

# Load structured grammar
grammar = loader.load_grammar(lesson_number=1)
# Returns: {"gender": {"rule": "...", "examples": [...]}, ...}
```

**Purpose:** Parse markdown tables and text from retrieved chunks into structured data for agents.

---

## Integration with Orchestrator

### Initialization Sequence

```
App Startup (app.py)
    ↓
1. Load models from HuggingFace Hub
    ↓
2. Initialize RAG system:
   - Create SentenceTransformerClient (embedder)
   - Connect to PineconeClient (vector DB)
   - Create RAGRetriever
   - Wrap in LessonContentLoader
    ↓
3. Pass content_loader to ContentAgent
    ↓
4. Create orchestrator with all agents
```

### ContentNode Integration

**File:** `src/orchestrator/nodes.py`

```python
class ContentNode:
    def initialize_lesson(self, state: SystemState) -> SystemState:
        """Load ALL lesson content upfront (one-time RAG query)."""
        try:
            # Check if RAG is available
            if self.agent.content_loader:
                logger.info("Loading lesson content from RAG...")
                state.cached_vocab_words = self.agent.content_loader.load_vocabulary(
                    state.current_lesson
                )
                state.cached_grammar_content = self.agent.content_loader.load_grammar(
                    state.current_lesson
                )
                logger.info(f"Loaded {len(state.cached_vocab_words)} words from RAG")
            else:
                # Fallback to placeholder data (for testing/development)
                logger.warning("No content loader available, using fallback data")
                state.cached_vocab_words = [...]  # Hardcoded fallback
                
            state.lesson_initialized = True
            return state
        except Exception as e:
            logger.error(f"Failed to initialize lesson: {e}")
            state.lesson_initialized = False
            return state
```

**Key Design:**
- ✅ **One-time retrieval:** Load ALL content at lesson start (per ARCHITECTURE.md guidance)
- ✅ **Cache in memory:** No repeated RAG queries during lesson
- ✅ **Graceful fallback:** Works with or without RAG (useful for testing)

### GradingNode Integration

**File:** `src/orchestrator/graph.py`

```python
def initialize_lesson_content(state, content_node, grading_node):
    """Initialize lesson content and pre-load grammar for grading."""
    # Load content from RAG
    state = content_node.initialize_lesson(state)
    
    # Pre-load grammar rules for grading agent
    grading_node.preload_grammar_rules(state)
    
    return state
```

**Benefit:** GradingAgent has full grammar context for better answer validation.

---

## Data Formats

### Vocabulary Format (from RAG)
```python
[
    {
        "arabic": "كِتَاب",
        "transliteration": "kitaab",
        "english": "book",
        "word_id": "w1"
    },
    {
        "arabic": "مَدْرَسَة",
        "transliteration": "madrasa",
        "english": "school",
        "word_id": "w2"
    }
]
```

**Source:** Parsed from markdown tables:
```markdown
| Arabic | Transliteration | English |
|--------|----------------|---------|
| كِتَاب | kitaab | book |
```

### Grammar Format (from RAG)
```python
{
    "gender": {
        "rule": "Nouns are either masculine or feminine",
        "examples": ["كِتَاب (masculine)", "مَدْرَسَة (feminine)"],
        "detection_pattern": "ة$",  # Regex for feminine marker
        "full_text": "# Gender\n\nArabic nouns are..."
    },
    "definite_article": {
        "rule": "Use ال (al-) for 'the'",
        "examples": ["الكِتَاب (the book)", "المَدْرَسَة (the school)"],
        "full_text": "..."
    }
}
```

**Source:** Parsed from markdown sections with H2 headers (`## Grammar: Gender`)

---

## Testing Strategy

### Testing with Mocks

```python
class MockVectorDatabase:
    """In-memory implementation for testing."""
    
    def __init__(self):
        self.vectors = {}
    
    def upsert(self, vectors: list[dict], batch_size: int = 100):
        for vec in vectors:
            self.vectors[vec["id"]] = vec
        return {"batches": 1, "total_vectors": len(vectors)}
    
    def query(self, vector: list[float], top_k: int = 5, **kwargs):
        # Return pre-defined test data
        return {"matches": [
            {"id": "lesson_1_vocab", "score": 0.95, "metadata": {...}}
        ]}

# Test without external dependencies
def test_orchestrator():
    mock_store = MockVectorDatabase()
    retriever = RAGRetriever(mock_embedder, mock_store)
    
    # Test logic without hitting Pinecone API
    results = retriever.retrieve_by_lesson("vocabulary", lesson_number=1)
    assert len(results) > 0
```

### Integration Tests

```python
@pytest.fixture
def mock_rag_retriever():
    """Mock RAG retriever with realistic lesson content."""
    retriever = MagicMock()
    
    def mock_retrieve(query, lesson, top_k):
        if "vocabulary" in query.lower():
            return [{
                "text": "| Arabic | Transliteration | English |\n|...",
                "metadata": {"section_title": "Vocabulary", "lesson_number": lesson}
            }]
        elif "grammar" in query.lower():
            return [{
                "text": "## Grammar: Gender\n\nNouns are...",
                "metadata": {"section_title": "Grammar: Gender"}
            }]
        return []
    
    retriever.retrieve_by_lesson.side_effect = mock_retrieve
    return retriever
```

---

## Adding New Vector Database Providers

To add support for a new vector database (e.g., Qdrant):

1. **Create implementation class:**
```python
# src/rag/qdrant_client.py
from qdrant_client import QdrantClient as QdrantSDK

class QdrantClient:
    """Qdrant implementation of VectorDatabase protocol."""
    
    def __init__(self, url: str):
        self.client = QdrantSDK(url=url)
        self.collection = "arabic-teaching"
    
    def upsert(self, vectors: list[dict], batch_size: int = 100):
        # Implement using Qdrant SDK
        ...
    
    def query(self, vector: list[float], top_k: int = 5, **kwargs):
        # Implement using Qdrant SDK
        ...
```

2. **No changes needed in application code** - just swap the injected dependency:
```python
# Works with Pinecone
orchestrator = RAGOrchestrator(PineconeClient())

# Works with Qdrant (no code changes!)
orchestrator = RAGOrchestrator(QdrantClient(url="..."))
```

---

## Protocol vs ABC

We use `Protocol` (structural typing) instead of `ABC` (nominal typing):

**Protocol advantages:**
- No explicit inheritance needed
- Duck typing: if it implements the methods, it's a VectorDatabase
- Better for testing (mock classes don't need inheritance)
- More Pythonic and flexible

**Example:**
```python
from typing import Protocol

class VectorDatabase(Protocol):
    """Protocol defining vector database interface."""
    
    def upsert(self, vectors: list[dict], batch_size: int = 100) -> dict:
        """Upload vectors to database."""
        ...
    
    def query(self, vector: list[float], top_k: int = 5, **kwargs) -> dict:
        """Query for similar vectors."""
        ...
```

Any class implementing these methods automatically satisfies the protocol - no inheritance required.

---

## Key Design Decisions

### 1. One-Time Retrieval at Lesson Start
**Rationale:** Per ARCHITECTURE.md, Agent 3 should retrieve ALL content upfront, not on-demand.

**Benefits:**
- Consistent content throughout lesson
- Faster during lesson (no API latency)
- Lower API costs
- Predictable behavior

**Implementation:** `ContentNode.initialize_lesson()` loads vocabulary and grammar, caches in `SystemState`.

### 2. Graceful Fallback to Placeholder Data
**Rationale:** System should work even if RAG initialization fails (network issues, missing credentials, etc.)

**Benefits:**
- Easier local development (no Pinecone required)
- Better error recovery
- Allows testing without external dependencies

**Implementation:** Check `if self.agent.content_loader` before calling RAG methods.

### 3. Markdown as Content Format
**Rationale:** Human-readable, easy to edit, supports structure (tables, headers).

**Benefits:**
- Non-technical contributors can edit lessons
- Version control friendly (git diffs work)
- Easy to validate with linters

**Implementation:** LessonContentLoader parses markdown tables/sections into structured data.

---

## Dependencies

- `pinecone-client` - Vector database client
- `sentence-transformers` - Embedding model
- `pyyaml` - Markdown frontmatter parsing (optional)

---

## References

- [SOLID Principles](https://en.wikipedia.org/wiki/SOLID)
- [Dependency Inversion Principle](https://en.wikipedia.org/wiki/Dependency_inversion_principle)
- [Python Protocols (PEP 544)](https://peps.python.org/pep-0544/)
- [Pinecone Documentation](https://docs.pinecone.io/)
- [SentenceTransformers](https://www.sbert.net/)

---

## Status: Production Ready

RAG integration is complete and deployed to HuggingFace Spaces.

**Monitoring:**
- Check Pinecone dashboard for query volume/latency
- Monitor RAG initialization errors in app logs
- Track fallback usage (should be minimal in production)
