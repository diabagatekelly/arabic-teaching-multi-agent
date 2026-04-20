# Inference Pipeline Documentation

## Overview

The Arabic Teaching System uses a **multi-agent inference pipeline** where three specialized models collaborate to deliver personalized Arabic lessons. Each agent has distinct responsibilities and inference configurations optimized for its role.

## Pipeline Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         Inference Flow                           │
└─────────────────────────────────────────────────────────────────┘

User Input: "كتاب"
     │
     ↓
┌────────────────────────┐
│   Orchestrator         │  ← Determines context: quiz answer
│   (State Machine)      │
└───────┬────────────────┘
        │
        ↓ (Route to Grading Agent)
┌────────────────────────────────────────────────────────────┐
│  Grading Agent (Qwen2.5-7B + LoRA)                         │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ 1. Build prompt with GRADING_VOCAB template          │  │
│  │    Input: word="كِتَاب", answer="book", correct="book"│  │
│  │                                                        │  │
│  │ 2. Apply chat template                                │  │
│  │    messages = [{"role": "user", "content": prompt}]   │  │
│  │                                                        │  │
│  │ 3. Tokenize                                           │  │
│  │    tokens = tokenizer(messages, return_tensors="pt")  │  │
│  │                                                        │  │
│  │ 4. Generate with LoRA adapter (@spaces.GPU)          │  │
│  │    outputs = model.generate(                          │  │
│  │        **tokens,                                      │  │
│  │        max_new_tokens=50,                             │  │
│  │        temperature=0.1,                               │  │
│  │        do_sample=True                                 │  │
│  │    )                                                  │  │
│  │                                                        │  │
│  │ 5. Decode output                                      │  │
│  │    response = tokenizer.decode(outputs)               │  │
│  └──────────────────────────────────────────────────────┘  │
│  Output: '{"correct": true}'                              │
└────────────────────────────────────────────────────────────┘
        │
        ↓ (Parse JSON result)
┌────────────────────────┐
│   Orchestrator         │  ← Updates session state: score += 1
│   (Score: 1/3)         │
└───────┬────────────────┘
        │
        ↓ (Route to Teaching Agent for feedback)
┌────────────────────────────────────────────────────────────┐
│  Teaching Agent (Qwen2.5-7B + LoRA)                        │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ 1. Build prompt with FEEDBACK_VOCAB_CORRECT template │  │
│  │    Input: word_arabic, translation, score="1/3"      │  │
│  │                                                        │  │
│  │ 2-5. Same generation pipeline as Grading Agent       │  │
│  │      but with temperature=0.7 (more creative)        │  │
│  └──────────────────────────────────────────────────────┘  │
│  Output: "✓ Correct! كِتَاب means book. Great work!"     │
└────────────────────────────────────────────────────────────┘
        │
        ↓
    User sees feedback in Gradio chat
```

## Agent-Specific Configurations

### Agent 1: Teaching Agent

**Model:** `kdiabagate/qwen-7b-arabic-teaching`
- Base: Qwen/Qwen2.5-7B-Instruct
- Fine-tuning: LoRA (rank=32, alpha=64)
- Training data: 153 multi-turn teaching conversations

**Purpose:** Generate user-facing educational content with warm, encouraging tone

**Inference Config:**
```python
{
    "max_new_tokens": 256,        # Longer responses for explanations
    "do_sample": True,            # Enable sampling for natural language
    "temperature": 0.7,           # Moderate creativity
    "top_p": 0.92,                # Nucleus sampling (92% probability mass)
    "top_k": 60,                  # Top 60 tokens considered
    "repetition_penalty": 1.05,   # Slight penalty to avoid repetition
    "num_beams": 1,               # Greedy decoding (no beam search)
    "use_cache": True,            # KV cache for efficiency
    "pad_token_id": tokenizer.eos_token_id
}
```

**Rationale:**
- **Higher temperature (0.7):** Natural, varied teaching style
- **Higher top_k (60):** Rich vocabulary for explanations
- **Moderate top_p (0.92):** Balance between quality and diversity
- **Repetition penalty (1.05):** Avoid monotonous phrasing

**Typical Latency:** 1.5-2.5s per response

**Prompts Used:**
- `LESSON_WELCOME`: Introduce lesson with vocab/grammar overview
- `VOCAB_BATCH_INTRO`: Present 3-word batch with flashcards
- `VOCAB_QUIZ_QUESTION`: Ask "What does X mean?"
- `VOCAB_BATCH_SUMMARY`: Summarize quiz performance
- `GRAMMAR_EXPLANATION`: Teach grammar rule with examples
- `FEEDBACK_VOCAB_CORRECT/INCORRECT`: Provide quiz feedback
- `FEEDBACK_GRAMMAR_CORRECT/INCORRECT`: Provide grammar feedback
- `PROGRESS_REPORT`: Show lesson progress and next options

---

### Agent 2: Grading Agent

**Model:** Same as Agent 1 - `kdiabagate/qwen-7b-arabic-teaching`
- Base: Qwen/Qwen2.5-7B-Instruct
- Fine-tuning: LoRA (rank=32, alpha=64)
- Training data: Same 153 conversations as Agent 1 (includes grading patterns)

**Purpose:** Evaluate answers accurately with flexible matching, return JSON

**Inference Config:**
```python
{
    "max_new_tokens": 50,         # Short JSON output only
    "do_sample": True,            # Still use sampling (not greedy)
    "temperature": 0.1,           # Very low for deterministic JSON
    "top_p": 0.95,                # High probability mass for consistency
    "top_k": 40,                  # Focused vocabulary
    "repetition_penalty": 1.0,    # No penalty (JSON has repeated structure)
    "num_beams": 1,
    "use_cache": True,
    "pad_token_id": tokenizer.eos_token_id
}
```

**Rationale:**
- **Low temperature (0.1):** Deterministic, consistent JSON output
- **High top_p (0.95):** Focus on most likely tokens
- **Lower top_k (40):** Limited to JSON-relevant vocabulary
- **No repetition penalty:** JSON keys naturally repeat (`"correct": true`)
- **Short max_tokens (50):** Only need `{"correct": true/false}`

**Typical Latency:** 0.8-1.2s per response

**Prompts Used:**
- `GRADING_VOCAB`: Grade vocabulary translation
- `GRADING_GRAMMAR_QUIZ`: Grade grammar quiz answer
- `GRADING_GRAMMAR_TEST`: Grade multiple final exam questions

**Edge Case Handling:**

*Vocabulary Grading:*
```python
# Accepts:
- Synonyms: "instructor" = "teacher"
- Typos: "scool" = "school"
- Case variations: "BOOK" = "book"
- Articles: "the book" = "book"

# Rejects:
- Wrong meaning: "pen" ≠ "book"
```

*Grammar Grading (Arabic text):*
```python
# Internal harakaat (diacritics) OPTIONAL:
"الكتاب" = "الكِتَاب"  ✓ (internal َ ِ ُ optional)

# Case endings REQUIRED:
"الكتاب" ≠ "الكِتَابُ"  ✗ (missing final ُ)
```

---

### Content System (No Model)

**Implementation:** Pre-built `lesson_cache.json` (RAG deprecated)

**Purpose:** Serve lesson content (vocabulary, grammar, quizzes)

**Data Structure:**
```python
{
    "lesson_number": 1,
    "lesson_name": "Gender and Definite Article",
    "vocabulary": [{"arabic": "...", "transliteration": "...", "english": "..."}],
    "grammar_points": ["masculine_feminine_nouns"],
    "grammar_sections": {"rule": "...", "examples": "...", "practice": "..."},
    "difficulty": "beginner"
}
```

**Rationale:**
- **No inference latency:** Instant JSON lookup (<100ms)
- **100% reliability:** No model failures or hallucinations
- **No GPU needed:** Reduces ZeroGPU allocation overhead
- **Consistent quality:** Human-curated content

**Typical Latency:** <100ms per lookup (file read)

**Current Status:** All production lessons use lesson_cache.json. RAG infrastructure preserved in codebase but not active. Content Agent class exists for potential future dynamic exercise generation.

---

## Model Loading Strategy

### Problem: ZeroGPU Memory Constraints

HuggingFace ZeroGPU allocates GPU memory **on-demand** only when `@spaces.GPU` decorated functions are called. Loading all models at startup would exceed memory limits.

### Solution: Lazy Loading with Callable Getters

**Instead of:**
```python
# ❌ This loads models immediately (OOM on Zero-GPU)
teaching_model = load_teaching_model()
grading_model = load_grading_model()

orchestrator = Orchestrator(teaching_model, ...)
```

**We use:**
```python
# ✅ Models loaded only when first needed
teaching_model_cache = {'model': None, 'tokenizer': None}

def get_teaching_model():
    if teaching_model_cache['model'] is None:
        model, tokenizer = load_teaching_model()
        teaching_model_cache['model'] = model
        teaching_model_cache['tokenizer'] = tokenizer
    return teaching_model_cache['model'], teaching_model_cache['tokenizer']

# Orchestrator receives CALLABLE, not model
orchestrator = Orchestrator(
    teaching_model_getter=lambda: get_teaching_model()[0],
    teaching_tokenizer=get_teaching_model()[1]
)
```

**Benefits:**
- Models loaded only when first inference occurs
- GPU memory allocated just-in-time
- Complies with ZeroGPU constraints
- Cached after first load (subsequent calls are fast)

### Loading Timeline

```
App Start (t=0s)
├─ Load lesson_cache.json (0.5s)
├─ Initialize orchestrator (0.1s)
└─ Gradio interface ready ✓

First User Message (t=30s)
├─ Orchestrator determines need for Teaching Agent
├─ Call teaching_model_getter() 
├─ Load base model (15s)
├─ Load LoRA adapter (2s)
├─ Cache in memory ✓
├─ Run inference (2s)
└─ Response delivered (total: ~19s first time)

Subsequent Messages (t=60s, 90s, ...)
├─ Model already cached
├─ Run inference (2s)
└─ Response delivered (total: ~2s)
```

## Prompt Engineering

### Template Structure

All prompts follow a consistent format with mode declarations:

```python
template = """Mode: {mode_name}

{Context variables...}

Example response format:
{example}

Instructions for model behavior...

Output format requirements:
{format_spec}
"""
```

**Mode Declaration Benefits:**
- Helps model understand task type
- Signals different behavior patterns
- Assists with prompt routing

### Chat Template Application

**All agents use chat templates** (not raw text):

```python
# 1. Build prompt from template
prompt_text = VOCAB_QUIZ_QUESTION.format(
    question_type="translation",
    word_arabic="كِتَاب",
    word_english="book",
    question_number=1,
    total_questions=3
)

# 2. Wrap in messages format
messages = [{"role": "user", "content": prompt_text}]

# 3. Apply model's chat template
text = tokenizer.apply_chat_template(
    messages,
    tokenize=False,
    add_generation_prompt=True
)

# 4. Tokenize and generate
inputs = tokenizer([text], return_tensors="pt")
outputs = model.generate(**inputs, **generation_config)
```

**Why chat templates?**
- Models fine-tuned on chat format (Qwen2.5-Instruct)
- Adds special tokens (`<|im_start|>`, `<|im_end|>`)
- Improves instruction-following
- Consistent with training format

### Example: Full Inference Pipeline

**Input:** User answers quiz question with "book"

**Step 1: Grading Agent**
```python
# Orchestrator builds grading prompt
prompt = GRADING_VOCAB.format(
    word="كِتَاب",
    student_answer="book",
    correct_answer="book"
)

# Grading Agent processes
@spaces.GPU
def grade(prompt):
    messages = [{"role": "user", "content": prompt}]
    text = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
    inputs = tokenizer([text], return_tensors="pt").to(model.device)
    
    outputs = model.generate(
        **inputs,
        max_new_tokens=50,
        temperature=0.1,
        top_p=0.95,
        top_k=40,
        do_sample=True,
        pad_token_id=tokenizer.eos_token_id
    )
    
    # Strip input tokens
    generated_ids = [output[len(input_ids):] for input_ids, output in zip(inputs.input_ids, outputs)]
    response = tokenizer.batch_decode(generated_ids, skip_special_tokens=True)[0]
    return response

result = grade(prompt)  # '{"correct": true}'
```

**Step 2: Teaching Agent**
```python
# Orchestrator parses grading result and builds feedback prompt
prompt = FEEDBACK_VOCAB_CORRECT.format(
    word_arabic="كِتَاب",
    word_transliteration="kitaab",
    english="book",
    current_score="1/3"
)

# Teaching Agent processes (same pipeline, different config)
@spaces.GPU
def teach(prompt):
    # ... same chat template logic ...
    outputs = model.generate(
        **inputs,
        max_new_tokens=256,       # Longer for feedback
        temperature=0.7,          # More creative
        top_p=0.92,
        top_k=60,
        do_sample=True
    )
    # ... decode ...

feedback = teach(prompt)  # "✓ Correct! كِتَاب means book. Great job! You're at 1/3 so far."
```

**Step 3: Return to User**
```python
return feedback  # Displayed in Gradio chat
```

## Performance Optimization

### 1. KV Cache

**Enabled by default (`use_cache=True`)**

Caches key-value tensors from previous tokens during generation, avoiding recomputation.

**Benefit:** ~40% speedup on longer generations

### 2. Token Stripping

**Remove prompt tokens from output:**
```python
generated_ids = [
    output_ids[len(input_ids):]
    for input_ids, output_ids in zip(model_inputs.input_ids, generated_ids)
]
```

**Why:** Saves decoding time and memory

### 3. Batch Decoding

**Use `batch_decode` instead of individual decode calls:**
```python
# ✓ Fast
response = tokenizer.batch_decode(generated_ids, skip_special_tokens=True)[0]

# ✗ Slower
response = tokenizer.decode(generated_ids[0], skip_special_tokens=True)
```

**Benefit:** ~20% faster for single responses, scales better for batches

### 4. Lesson Content Caching

**Pre-build lesson cache to avoid RAG queries:**
```bash
# Build once, deploy everywhere
python scripts/build_lesson_cache.py

# Generates lesson_cache.json with all vocab/grammar
```

**Benefit:**
- Eliminates RAG retrieval latency (200-500ms per query)
- Reduces dependencies (no Pinecone/embedding model needed at runtime)
- Faster lesson initialization

## Monitoring & Debugging

### Inference Logging

**Enable verbose logging in agents:**
```python
logger.info(f"[TeachingAgent] Starting generation (max_tokens={max_new_tokens}, temp={temperature})")
logger.info(f"[TeachingAgent] Tokenized input: {model_inputs.input_ids.shape[1]} tokens")
logger.info(f"[TeachingAgent] Generated {len(generated_ids[0])} new tokens")
logger.info(f"[TeachingAgent] Decoded response length: {len(response)} chars")
```

**Check logs in Space UI → Logs tab**

### Common Issues

**1. JSON Parsing Errors**
- **Cause:** Grading agent output isn't valid JSON
- **Diagnosis:** Check logs for raw output
- **Fix:** Adjust temperature (lower = more consistent)

**2. Slow Inference**
- **Cause:** Large `max_new_tokens` or high `temperature`
- **Diagnosis:** Check generation time in logs
- **Fix:** Reduce `max_new_tokens` or use lower temperature

**3. Repetitive Output**
- **Cause:** Too low `repetition_penalty` or `temperature`
- **Fix:** Increase `repetition_penalty` to 1.05-1.1

**4. Off-topic Responses**
- **Cause:** Temperature too high or prompt too vague
- **Fix:** Lower temperature or add more specific prompt instructions

## Testing Inference Locally

```python
# Test teaching agent directly
from src.agents.teaching_agent import TeachingAgent
from transformers import AutoModelForCausalLM, AutoTokenizer
from peft import PeftModel

# Load base model
base_model = AutoModelForCausalLM.from_pretrained("Qwen/Qwen2.5-7B-Instruct", torch_dtype=torch.float16)

# Load and merge LoRA adapter
model = PeftModel.from_pretrained(base_model, "kdiabagate/qwen-7b-arabic-teaching")
model = model.merge_and_unload()

tokenizer = AutoTokenizer.from_pretrained("Qwen/Qwen2.5-7B-Instruct")

agent = TeachingAgent(model, tokenizer)
prompt = "Mode: feedback_vocab\n\nWord: كِتَاب\nStudent was correct."
response = agent.respond(prompt)
print(response)
```

## References

- Qwen2.5 Model Card: https://huggingface.co/Qwen/Qwen2.5-7B-Instruct
- LoRA Paper: https://arxiv.org/abs/2106.09685
- Nucleus Sampling: https://arxiv.org/abs/1904.09751
- Fine-tuning Guide: `training/README.md`
- Prompt Design: `docs/PROMPT_DESIGN.md`
