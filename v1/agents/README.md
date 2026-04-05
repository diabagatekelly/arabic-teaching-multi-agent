# Teaching Agents

Core agents for Arabic language teaching system.

## Architecture

```
BaseAgent (abstract)
├── VocabularyAgent
├── GrammarAgent
└── ExerciseAgent (TODO)
```

## Components

### BaseAgent
Abstract base class providing:
- LLM provider interface (via Protocol)
- Prompt registry integration
- Common generation and formatting methods

### VocabularyAgent
Teaches Arabic vocabulary with 5 capabilities:
- `introduce_words()` - Introduce new vocabulary with examples
- `assess_answer()` - Check student answers with few-shot examples
- `correct_error()` - Provide detailed error correction with reasoning
- `review_words()` - Quiz student on learned vocabulary
- `show_progress()` - Display progress and offer next steps

### GrammarAgent
Teaches Arabic grammar with 5 capabilities:
- `introduce_concept()` - Explain grammar rules with examples
- `detect_error()` - Detect grammar errors with chain-of-thought reasoning
- `generate_practice()` - Create practice questions
- `explain_concept()` - Answer student questions about grammar
- `correct_mistake()` - Provide corrections for grammar errors

## Usage

```python
from agents import VocabularyAgent, GrammarAgent
from prompts.registry import get_registry

# Initialize with LLM provider
llm = YourLLMProvider()  # Must implement .generate(prompt) -> str
registry = get_registry()

# Create agents
vocab_agent = VocabularyAgent(llm, registry)
grammar_agent = GrammarAgent(llm, registry)

# Use vocabulary agent
response = vocab_agent.introduce_words(
    lesson_number=3,
    vocabulary_list="كِتَاب (book), مَدْرَسَة (school), بَيْت (house)"
)

# Use grammar agent
feedback = grammar_agent.detect_error(
    student_answer="كتاب كبيرة",
    grammar_rule="Gender agreement"
)
```

## Testing

All agents have comprehensive test coverage:
- `test_agents_base.py` - Base agent functionality (5 tests)
- `test_agents_vocabulary.py` - Vocabulary agent (8 tests)
- `test_agents_grammar.py` - Grammar agent (8 tests)

**Coverage:** 98%+ for agents module

Run tests:
```bash
uv run pytest tests/test_agents_*.py -v
```

## LLM Provider Interface

Agents use the `LLMProvider` Protocol, which requires:

```python
class LLMProvider(Protocol):
    def generate(self, prompt: str, **kwargs: Any) -> str:
        """Generate text from prompt."""
        ...
```

Example implementations:
- OpenAI API wrapper
- Local model (Transformers)
- Anthropic Claude API
- Mock LLM (for testing)

## Design Principles

1. **Single Responsibility:** Each agent focuses on one teaching area
2. **Dependency Injection:** LLM and registry passed in, not hardcoded
3. **Template-Based:** All prompts come from registry, not inline
4. **Testable:** Protocol-based LLM interface enables mocking
5. **Type-Safe:** Full type hints with mypy strict mode

## Next Steps

- [ ] Add ExerciseAgent with RAG integration
- [ ] Implement OpenAI and Transformers LLM providers
- [ ] Add conversation state management
- [ ] Integrate with LangGraph orchestration
