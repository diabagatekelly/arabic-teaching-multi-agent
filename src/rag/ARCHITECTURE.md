# RAG Architecture: Dependency Inversion

## Overview

This module follows the **Dependency Inversion Principle (DIP)** to decouple application code from specific vector database implementations.

## Structure

```
src/rag/
├── vector_database.py   # Abstract interface (Protocol)
├── pinecone_client.py   # Concrete Pinecone implementation
└── __init__.py          # Public exports
```

## Key Principle: Depend on Abstractions

**Problem:** Directly depending on `PineconeClient` throughout the codebase creates tight coupling:
- Hard to test (requires mocking Pinecone API)
- Hard to switch providers (Qdrant, Weaviate, Chroma, etc.)
- Hard to experiment with different backends

**Solution:** Define `VectorDatabase` Protocol that both real and mock implementations satisfy.

## Usage Example

### ❌ Bad: Direct dependency on Pinecone

```python
from src.rag.pinecone_client import PineconeClient

class RAGOrchestrator:
    def __init__(self):
        # Tightly coupled to Pinecone
        self.vector_store = PineconeClient(api_key="...")
    
    def search(self, query_vector: list[float]) -> list:
        return self.vector_store.query(query_vector)
```

**Problems:**
- Can't test without Pinecone credentials
- Can't switch to Chroma/Qdrant without rewriting code
- Violates DIP: high-level module depends on low-level detail

### ✅ Good: Dependency injection with abstraction

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

## Testing Benefits

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
        return {"matches": []}  # Simple mock response

# Test without external dependencies
def test_orchestrator():
    mock_store = MockVectorDatabase()
    orchestrator = RAGOrchestrator(mock_store)
    
    # Test logic without hitting Pinecone API
    results = orchestrator.search([0.1] * 384)
    assert len(results) == 0
```

## Adding New Implementations

To add support for a new vector database:

1. **Create implementation class** (e.g., `qdrant_client.py`)
2. **Implement all VectorDatabase methods** (Protocol checks compatibility)
3. **No changes needed** in application code

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
    
    # ... implement other methods
```

Now application code works with both:
```python
# Works with Pinecone
orchestrator = RAGOrchestrator(PineconeClient())

# Works with Qdrant (no code changes needed!)
orchestrator = RAGOrchestrator(QdrantClient(url="..."))
```

## Protocol vs ABC

We use `Protocol` (structural typing) instead of `ABC` (nominal typing):

**Protocol advantages:**
- No explicit inheritance needed
- Duck typing: if it quacks like a VectorDatabase, it is a VectorDatabase
- Better for testing (mock classes don't need inheritance)
- More Pythonic and flexible

## References

- [SOLID Principles](https://en.wikipedia.org/wiki/SOLID)
- [Dependency Inversion Principle](https://en.wikipedia.org/wiki/Dependency_inversion_principle)
- [Python Protocols (PEP 544)](https://peps.python.org/pep-0544/)
