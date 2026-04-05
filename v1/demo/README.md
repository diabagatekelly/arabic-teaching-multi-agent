# Demo Scripts

Interactive demos for testing the multi-agent system.

## Simple CLI Demo

Test VocabularyAgent and GrammarAgent with real LLM responses.

### Setup

```bash
# Set OpenAI API key
export OPENAI_API_KEY='your-key-here'

# Run demo
uv run python demo/simple_cli.py
```

### Features

**VocabularyAgent test:**
- Introduce vocabulary words with examples
- Assess student answers with feedback

**GrammarAgent test:**
- Introduce grammar concepts
- Detect errors in student answers (correct and incorrect)

### Using Different Models

**With OpenAI (default):**
```python
from llm import OpenAIProvider
llm = OpenAIProvider(model="gpt-4o-mini")  # or gpt-4, gpt-3.5-turbo
```

**With fine-tuned local model:**
```python
from llm import TransformersProvider
llm = TransformersProvider(
    model_name="path/to/qwen-finetuned",
    load_in_4bit=True,
)
```

### Example Session

```
Arabic Teaching Multi-Agent System - Demo
==========================================================

✅ Agents initialized with GPT-4o-mini

Choose an agent:
  1) VocabularyAgent - Test vocabulary teaching
  2) GrammarAgent - Test grammar teaching
  3) Exit

Enter choice (1-3): 2

GRAMMAR AGENT TEST
==========================================================

1. Introducing grammar concept...
In Arabic, nouns and adjectives must match in gender...

2. Detecting error (incorrect)...
No, that's incorrect! كِتَاب (book) is masculine, but كَبِيرَة is feminine...

3. Detecting correct answer...
Perfect! كِتَابٌ كَبِيرٌ ✓ Both are masculine, so they agree!
```

## Future Demos

- [ ] Web UI with Streamlit
- [ ] Full conversation flow with orchestration
- [ ] RAG-powered exercise generation demo
- [ ] Fine-tuned model comparison (3B vs 7B)
