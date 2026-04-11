# Arabic Teaching Multi-Agent System - Architecture v2

**Design Philosophy:** Separate content from style. Fine-tune for teaching behavior, use RAG for scalable grammar content.

---

## Core Problem We're Solving

**Old approach (v1):** Fine-tune model on specific grammar rules
- ❌ Adding new grammar = retrain entire model
- ❌ Doesn't scale past 5-10 grammar points
- ❌ Model memorizes examples, doesn't generalize

**New approach (v2):** Fine-tune for style, RAG for content
- ✅ Adding new grammar = upload markdown file (no retrain)
- ✅ Scales to 100+ grammar points
- ✅ Model learns teaching patterns, not specific rules

---

## Agent Architecture

### 🎭 Agent 1: Teaching/Presentation Agent (The "Face")

**Role:** Format content into pedagogical style

**Single Job:** Take structured variables and present them in an encouraging, learner-friendly way

**Responsibilities:**
- Format lessons in structured, learner-friendly way
- Maintain encouraging, supportive tone
- Ask comprehension questions
- Provide progress feedback

**Does NOT:**
- ❌ Access RAG directly
- ❌ Retrieve content
- ❌ Assemble prompts from scratch

**Input Variables** (passed from Agent 3 or orchestrator):

*Vocabulary modes:*
```python
# Mode: vocab_batch_introduction
{
    "lesson_number": 3,
    "batch_number": 1,
    "words": [
        {"arabic": "كِتَاب", "transliteration": "kitaab", "english": "book"},
        {"arabic": "مَدْرَسَة", "transliteration": "madrasa", "english": "school"},
        {"arabic": "قَلَم", "transliteration": "qalam", "english": "pen"}
    ]
}

# Mode: vocab_batch_quiz (per word)
{
    "word": {"arabic": "كِتَاب", "transliteration": "kitaab"},
    "question_type": "arabic_to_english"  # or "english_to_arabic"
}

# Mode: vocab_final_test (per word)
{
    "word": {"arabic": "مَدْرَسَة", "transliteration": "madrasa"},
    "question_number": 3,
    "total_questions": 10
}
```

*Grammar modes:*
```python
# Mode: grammar_explanation
{
    "lesson_number": 3,
    "topic_name": "Feminine Nouns",
    "grammar_rule": "Feminine nouns usually end in ة (taa marbuuta)",
    "examples": ["مَدْرَسَة (school) ✓", "كِتَاب (book - masculine) ✗"],
    "topics_remaining": 1  # "After this, 1 more topic"
}

# Mode: grammar_quiz (per question)
{
    "lesson_number": 3,
    "topic_name": "Feminine Nouns",
    "question_number": 2,
    "total_questions": 5,
    "question": "Is بَيْت masculine or feminine?",
    "correct_answer": "masculine"
}
```

**Tools:**
1. **LangChain PromptTemplate** - Formats variables into structured prompt
2. **Fine-tuned LLM** (Qwen2.5-3B - teaching style) - Adds pedagogical style

**Process:**
```python
from langchain.prompts import PromptTemplate

# 1. LangChain template formats the structure
template = PromptTemplate(
    template="""You are teaching Lesson {lesson_number}.

Grammar Rule: {grammar_rule}

Examples:
{examples}

Vocabulary: {vocabulary}

Present this in an encouraging, structured way with a comprehension question.""",
    input_variables=["lesson_number", "grammar_rule", "examples", "vocabulary"]
)

# 2. Format with input variables
prompt = template.format(**input_variables)

# 3. Fine-tuned model adds pedagogical style
response = teaching_llm.generate(prompt)
```

**Output Examples:**

*Vocabulary Batch Introduction:*
```
"Let's learn Batch 1! Here are your first 3 words:

📝 كِتَاب (kitaab) - book
📝 مَدْرَسَة (madrasa) - school  
📝 قَلَم (qalam) - pen

Take your time reviewing these. When you're ready, let's test your knowledge!"
```

*Vocabulary Batch Quiz Feedback (correct):*
```
"Correct! ✓ كِتَاب = book. Great job!"
```

*Vocabulary Batch Quiz Feedback (incorrect):*
```
"Not quite! The word مَدْرَسَة (madrasa) means 'school', not 'house'. Try to remember: madrasa = school."
```

*Grammar Explanation:*
```
"Let's learn about Feminine Nouns! 🌟

**The Rule:** In Arabic, most feminine nouns end with ة (taa marbuuta).

**Examples:**
- مَدْرَسَة (madrasa) - school ✓ (ends in ة)
- كِتَاب (kitaab) - book (masculine, no ة)

**Quick Check:** Look at the word بِنْت (bint - girl). Does it end in ة?"
```

*Grammar Quiz Question:*
```
"Question 2 of 5: Is the word بَيْت (bayt - house) masculine or feminine?"
```

*Grammar Quiz Feedback (correct):*
```
"Correct! ✓ بَيْت is masculine (no ة ending). You're doing great! (2/2 so far)"
```

*Grammar Quiz Feedback (incorrect):*
```
"Not quite. مَدْرَسَة is feminine because it ends in ة (taa marbuuta). The ة is the key indicator! (1/2 so far)"
```

**Fine-tuned On:**
- Vocabulary teaching patterns (~15 conversations)
  - Batch introductions with Arabic + transliteration + English
  - Per-word quiz feedback (correct/incorrect)
  - Final test feedback
- Grammar teaching patterns (~25 conversations)
  - Structured explanations with rule + examples
  - Comprehension questions
  - Quiz feedback with running score
  - Review suggestions
- Encouraging, supportive tone throughout
- **NOT** specific vocabulary words or grammar rules (content comes via variables)

---

### ✅ Agent 2: Error Detection Agent (The "Grader")

**Role:** Strict grading - receives JSON, returns JSON

**Single Job:** Evaluate student answers against grammar rules and return structured results

**Pre-Loading Strategy:**
```
User enters Lesson 3
    ↓
Agent 3 retrieves content
    ├─→ Agent 1: Gets teaching prompt → teaches
    └─→ Agent 2: Gets grammar rules → waits in background (rules loaded)

When student answers:
    ↓
Agent 2 already has: All Lesson 3 rules, detection patterns, expected formats
Agent 2 just needs: Student answer(s)
```

**Responsibilities:**
- Determine if answer is correct/incorrect
- Identify specific error types (in order of occurrence)
- Provide structured error analysis
- Grade single answers or multiple exercises

**Does NOT:**
- ❌ Access RAG during grading (rules pre-loaded at lesson start)
- ❌ Be encouraging (just factual analysis)
- ❌ Format for user (Agent 1 handles presentation)

**Input JSON:**

Single answer (rapid quiz):
```json
{
  "lesson": 3,
  "answers": [
    {
      "answer_id": "q1",
      "question_type": "grammar_check",
      "student_answer": "الكتاب كبيرة",
      "expected_pattern": "الكتاب الكبير",
      "grammar_points": ["gender_agreement", "definiteness_agreement"]
    }
  ]
}
```

Multiple answers (exercise set):
```json
{
  "lesson": 3,
  "answers": [
    {
      "answer_id": "q1",
      "student_answer": "كتاب كبيرة",
      "expected_pattern": "كتاب كبير",
      "grammar_points": ["gender_agreement"]
    },
    {
      "answer_id": "q2",
      "student_answer": "مدرسة كبيرة",
      "expected_pattern": "مدرسة كبيرة",
      "grammar_points": ["gender_agreement"]
    }
  ]
}
```

**Output JSON:**

Errors ordered by: (1) question order, (2) occurrence in answer
```json
{
  "lesson": 3,
  "total_score": "1/2",
  "results": [
    {
      "answer_id": "q1",
      "correct": false,
      "errors": [
        {
          "error_type": "gender_mismatch",
          "grammar_point": "noun_adjective_agreement",
          "details": "كتاب (masculine) paired with كبيرة (feminine)",
          "correction": "Use كبير (masculine) to match كتاب"
        },
        {
          "error_type": "definiteness_mismatch",
          "grammar_point": "noun_adjective_agreement",
          "details": "الكتاب (definite) paired with كبيرة (indefinite)",
          "correction": "Add ال to adjective: الكبيرة"
        }
      ],
      "total_errors": 2,
      "correct_form": "الكتاب الكبير"
    },
    {
      "answer_id": "q2",
      "correct": true,
      "errors": [],
      "total_errors": 0
    }
  ]
}
```

**Tools:**
1. **Pre-loaded grammar rules** - Received from Agent 3 at lesson start
2. **LangChain PromptTemplate** - Formats grading instructions + rules + answers
3. **Base LLM** (Qwen2.5-7B - better reasoning) - Returns structured JSON

**Why 7B Base Model (Not Fine-Tuned)?**

The base Qwen2.5-7B provides:
- ✅ Strong reasoning for semantic comparison (typos, synonyms, abbreviations)
- ✅ Good Arabic comprehension
- ✅ Reliable JSON output with proper prompting
- ✅ No fine-tuning needed initially (prompting is sufficient)
- ⚠️ May fine-tune later if grading accuracy needs improvement

**Flexible Grading:**
Prompt instructs model to accept:
- Minor typos (e.g., "scool" for "school")
- Synonyms (e.g., "instructor" for "teacher")
- Alternate phrasings with same meaning
- Abbreviated forms for grammar (e.g., "m" for "masculine")

Prompt provides **content:**
- ✅ Specific grammar rules for this lesson
- ✅ Student's actual answers
- ✅ Which grammar points to check

**Example: LangChain Template**
```python
grading_template = PromptTemplate(
    template="""You are grading student answers.

GRAMMAR RULES FOR LESSON {lesson}:
{grammar_rules}

STUDENT ANSWERS:
{student_answers}

For each answer, output JSON with:
- correct: true/false
- errors: list of all errors (ordered by occurrence)
- correct_form: the right answer

Be strict and factual.""",
    input_variables=["lesson", "grammar_rules", "student_answers"]
)
```

**Note:** Using base model with good prompting initially. Will fine-tune only if baseline evaluation shows grading accuracy needs improvement.

---

### 📚 Agent 3: Content Retrieval Agent (The "Librarian")

**Role:** Retrieve content from RAG and prepare data for other agents

**Single Job:** Fetch lesson content and assemble it into formats that Agent 1 and Agent 2 can use

**When Lesson Starts:**
```
Backend: "User starting Lesson 3"
  ↓ (provides structure)
Backend → Orchestrator: {
    lesson: 3,
    vocab: {total: 10, batches: [3,3,3,1]},
    grammar: {topics: ["feminine_nouns", "definite_article"]}
}
  ↓
Orchestrator → Agent 3: "Prepare lesson 3"
  ↓
Agent 3:
  1. Retrieves ALL Lesson 3 content from RAG (vocabulary + grammar)
  2. Splits vocabulary into batches per backend structure
  3. Holds everything in memory (no more RAG queries during lesson)
  4. Sends grammar rules to Agent 2 for pre-loading
  ↓
Agent 3 → Orchestrator: "Ready. Content cached."
```

**Responsibilities:**
- **At lesson start:** Retrieve ALL content (vocabulary + grammar) and hold in memory
- Split vocabulary into batches per backend-provided structure
- Serve vocabulary words on-demand (from memory, not RAG)
- Serve grammar content on-demand (from memory, not RAG)
- Assemble prompt variables for Agent 1
- Pre-load grammar rules for Agent 2
- Generate exercises using lightweight LLM + cached content

**Does NOT:**
- ❌ Generate student-facing content (Agent 1 does that)
- ❌ Grade answers (Agent 2 does that)

**Inputs:**

*From Backend (lesson structure):*
- Lesson number
- Vocabulary batch structure (e.g., [3, 3, 3, 1])
- Grammar topics list (e.g., ["feminine_nouns", "definite_article"])

*Retrieval queries (to RAG):*
- Lesson number → retrieve all vocabulary and grammar content
- Grammar point name (optional - for specific queries)
- Exercise type (fill-in-blank, translation, etc.)

**Note on Content Flow:**
- Backend provides STRUCTURE (how many batches, which topics)
- Agent 3 retrieves CONTENT (actual words, rules, examples) from RAG
- Agent 3 holds content in memory throughout lesson (no repeated RAG queries)

**Outputs:**

*For Agent 1 (vocabulary teaching):*
```python
# Batch introduction
{
    "lesson_number": 3,
    "batch_number": 1,
    "words": [
        {"arabic": "كِتَاب", "transliteration": "kitaab", "english": "book"},
        {"arabic": "مَدْرَسَة", "transliteration": "madrasa", "english": "school"},
        {"arabic": "قَلَم", "transliteration": "qalam", "english": "pen"}
    ]
}

# Batch quiz (per word)
{
    "word": {"arabic": "كِتَاب", "transliteration": "kitaab"},
    "question_type": "arabic_to_english"
}
```

*For Agent 1 (grammar teaching):*
```python
# Topic explanation
{
    "lesson_number": 3,
    "topic_name": "Feminine Nouns",
    "grammar_rule": "Feminine nouns usually end in ة (taa marbuuta)",
    "examples": ["مَدْرَسَة (school) ✓", "كِتَاب (book - masculine) ✗"],
    "topics_remaining": 1
}

# Topic quiz (per question)
{
    "lesson_number": 3,
    "topic_name": "Feminine Nouns",
    "question_number": 2,
    "total_questions": 5,
    "question": "Is بَيْت masculine or feminine?"
}
```

For Agent 2 (grading):
```python
{
    "lesson": 3,
    "grammar_rules": {
        "gender_agreement": {
            "rule": "Adjectives must match noun gender",
            "detection_pattern": "If noun.gender ≠ adj.gender → error",
            "error_types": ["gender_mismatch"]
        },
        "definiteness_agreement": {
            "rule": "Adjectives must match noun definiteness",
            "detection_pattern": "If noun has ال but adj doesn't → error",
            "error_types": ["definiteness_mismatch"]
        }
    }
}
```

**Tools:**
1. **Vector Database** (ChromaDB/Pinecone) - Stores lesson content and exercise templates
2. **Semantic Search** - Finds relevant content by meaning
3. **Metadata Filtering** - Filters by lesson number, grammar point, difficulty
4. **Lightweight LLM** - Generates exercises from templates + vocabulary
5. **LangChain PromptTemplate** - Assembles prompts for Agent 1 and Agent 2

**RAG Database Structure:**
```
data/rag_database/
├── lessons/
│   ├── lesson_01_gender_definiteness.md
│   ├── lesson_02_pronouns_nominal.md
│   ├── lesson_03_adjective_agreement.md
│   ├── lesson_04_present_tense.md
│   ├── lesson_05_past_tense.md
│   ├── lesson_06_negation.md
│   ├── lesson_07_questions.md
│   ├── lesson_08_possessive_idaafah.md
│   └── ... (expand to 25+ lessons)
│
└── exercises/
    ├── gender_agreement_fill_blank.md
    ├── definiteness_translation.md
    ├── verb_conjugation_practice.md
    └── ...
```

**Example Lesson File Metadata:**
```markdown
---
lesson_number: 3
grammar_points: 
  - noun_adjective_agreement
  - gender_agreement
  - definiteness_agreement
prerequisites: [1, 2]
difficulty: intermediate
vocabulary: [كبير, صغير, جميل, جديد, قديم]
---

# Lesson 3: Noun-Adjective Agreement

## Grammar Rules
...
```

**Process Flow:**

**Lesson Initialization (happens once):**
```python
# 1. Receive lesson structure from backend
lesson_structure = backend.get_lesson_structure(3)
# {
#     "lesson": 3,
#     "vocab": {"total": 10, "batches": [3, 3, 3, 1]},
#     "grammar": {"topics": ["feminine_nouns", "definite_article"]}
# }

# 2. Retrieve ALL content from RAG (one-time query)
vocab_content = vectorstore.query(
    filter={"lesson_number": 3, "content_type": "vocabulary"}
)
# Returns all 10 words with metadata

grammar_content = vectorstore.query(
    filter={"lesson_number": 3, "content_type": "grammar"}
)
# Returns all grammar rules, examples, patterns

# 3. Cache everything in memory
self.cached_vocab = vocab_content.words  # All 10 words
self.vocab_batches = split_into_batches(
    self.cached_vocab, 
    lesson_structure["vocab"]["batches"]
)  # [[3 words], [3 words], [3 words], [1 word]]

self.cached_grammar = {
    topic: grammar_content[topic]
    for topic in lesson_structure["grammar"]["topics"]
}

# 4. Pre-load Agent 2 with grammar rules
agent2.preload_rules(grammar_content.rules)

# → Ready! No more RAG queries during this lesson
```

**Serving Content (from memory):**
```python
# Vocabulary batch introduction
def get_batch_content(batch_number):
    # No RAG query - serve from memory
    return self.vocab_batches[batch_number - 1]

# Grammar topic explanation
def get_topic_content(topic_name):
    # No RAG query - serve from memory
    return self.cached_grammar[topic_name]

# Format for Agent 1
agent1_variables = {
    "lesson_number": 3,
    "batch_number": 1,
    "words": self.vocab_batches[0]
}
# → Agent 1 uses these with LangChain template
```

**For Agent 2 Pre-loading (happens at lesson start):**
```python
# Format rules for Agent 2's pre-loading
agent2_rules = {
    "lesson": 3,
    "grammar_rules": {
        rule.name: {
            "rule": rule.description,
            "detection_pattern": rule.pattern,
            "error_types": rule.error_types
        }
        for rule in self.cached_grammar.values()
    }
}
# → Agent 2 pre-loads these rules and keeps them ready for grading
```

**For Exercise Generation:**
```python
# 1. Retrieve template (could also be cached at lesson start)
template = vectorstore.query(
    filter={"type": "exercise", "grammar_point": "gender_agreement"}
)

# 2. Use cached vocabulary (already in memory from lesson initialization)
primary_vocab = self.cached_vocab[:3]  # Current batch words
all_vocab = self.cached_vocab  # All lesson vocabulary

# 3. Generate new exercises using LLM + cached content
generation_prompt = f"""Generate 5 fill-in-blank exercises.

Template: {template.structure}
Primary vocabulary (current batch): {primary_vocab}
All lesson vocabulary: {all_vocab}
Grammar focus: Gender agreement

Focus on primary vocabulary, use others for variety.

Output JSON array of exercises."""

exercises = lightweight_llm.generate(generation_prompt)
# Returns: [
#   {"question": "Complete: كتاب ___", "answer": "كبير", "options": ["كبير", "كبيرة"]},
#   ...
# ]
```

**For Test Composition:**
```python
# 6. Generate mixed test with multiple grammar points
test_content = {
    "lesson": 3,
    "num_questions": 10,
    "grammar_points": ["gender_agreement", "definiteness_agreement"]
}

# Agent 3 generates variety of questions
test = lightweight_llm.generate_test(test_content)
```

**LLM Choice for Agent 3:**
- **Option A:** Fine-tuned Qwen2.5-3B (same as Agent 1, optimized for exercise generation patterns)
- **Option B:** Base Qwen2.5-3B with prompting (no fine-tuning, simpler approach)
- **Option C:** Base Qwen2.5-7B (same as Agent 2, better reasoning for complex generation)

**Recommendation:** Start with Option B (base 3B with prompting). Fine-tune later if exercise quality needs improvement.

---

## State Management

### Lesson Structure Provided by Backend

**Backend Responsibilities:**
- Provide lesson structure (vocabulary batches, grammar topics list)
- Track student progress (which batches/topics completed)
- Determine when to move to next section

**Agent 3 Responsibilities:**
- Retrieve ALL content for lesson upfront (vocabulary + grammar)
- Hold content in memory (no repeated RAG queries)
- Serve content on-demand as lesson progresses

**Example Lesson Structure from Backend:**
```python
{
    "lesson_number": 3,
    "vocabulary": {
        "total_words": 10,
        "batch_structure": [3, 3, 3, 1],  # 4 batches
        "words": [...]  # Backend provides list
    },
    "grammar": {
        "topics": ["feminine_nouns", "definite_article"],
        "quiz_per_topic": 5  # 5 questions each
    }
}
```

### Conversation State Schema

**Tracked by Orchestrator:**
```python
class ConversationState(TypedDict):
    lesson_number: int
    
    # Vocabulary progress
    vocab_mode: str  # "batch_intro" | "batch_quiz" | "final_test" | "complete"
    vocab_batches_completed: List[int]  # [1, 2]
    current_vocab_batch: int  # 3
    vocab_batch_scores: Dict[int, str]  # {1: "2/3", 2: "3/3"}
    vocab_words_missed: List[str]  # ["مَدْرَسَة", "بَيْت"]
    vocab_final_test_score: Optional[str]  # "8/10"
    
    # Grammar progress
    grammar_mode: str  # "explanation" | "quiz" | "review" | "complete"
    grammar_topics_completed: List[str]  # ["feminine_nouns"]
    current_grammar_topic: str  # "definite_article"
    topic_quiz_scores: Dict[str, str]  # {"feminine_nouns": "3/5"}
    grammar_topics_needing_review: List[str]  # ["feminine_nouns"]
    
    # Agent 3 cache (loaded once per lesson)
    cached_vocab_words: List[Dict]  # All 10 words
    cached_grammar_content: Dict[str, Dict]  # All grammar rules + examples
    
    # Agent 2 pre-load (loaded once per lesson)
    preloaded_grammar_rules: Dict  # All rules for grading
    
    conversation_history: List[dict]
```

**State Flow Example:**

*Lesson Start:*
```python
state = {
    "lesson_number": 3,
    "vocab_mode": "batch_intro",
    "current_vocab_batch": 1,
    "vocab_batches_completed": [],
    # Agent 3 retrieves everything upfront:
    "cached_vocab_words": [...],  # All 10 words
    "cached_grammar_content": {...},  # All topics
    # Agent 2 pre-loads all rules:
    "preloaded_grammar_rules": {...}
}
```

*After Batch 1 Quiz:*
```python
state = {
    ...
    "vocab_batches_completed": [1],
    "vocab_batch_scores": {1: "2/3"},
    "vocab_words_missed": ["مَدْرَسَة"],
    "current_vocab_batch": 2
}
```

*Vocabulary Complete, Starting Grammar:*
```python
state = {
    ...
    "vocab_mode": "complete",
    "vocab_final_test_score": "8/10",
    "grammar_mode": "explanation",
    "current_grammar_topic": "feminine_nouns",
    "grammar_topics_completed": []
}
```

*After Grammar Topic 1 Quiz (Score < 4/5):*
```python
state = {
    ...
    "grammar_topics_completed": ["feminine_nouns"],
    "topic_quiz_scores": {"feminine_nouns": "3/5"},
    "grammar_topics_needing_review": ["feminine_nouns"],
    # Orchestrator asks: "Review or continue?"
}
```

---

## Agent Interaction Flows

**Note:** Detailed interaction flows with mermaid diagrams are documented in `INTERACTION_FLOWS.md`

---

## Key Design Decisions

### 1. Agent 1 is Always the "Face"

**Why:** Consistency in tone and presentation
- All user-facing text goes through Agent 1
- Other agents provide structured data
- Agent 1 wraps data in pedagogical style

### 2. Agent 2 Outputs Structured Data (JSON)

**Why:** Clear separation of evaluation vs. presentation
- Agent 2 focuses purely on correctness
- No need to be "nice" - just accurate
- Agent 1 handles making it encouraging

### 3. Agent 3 Retrieves + Generates Content

**Why:** Scalability without memorization
- Grammar rules stored in RAG (data, not model weights)
- Exercise templates stored in RAG
- Lightweight LLM generates exercise variations from templates
- Add new lesson = upload markdown file (no retraining)
- Add new exercise type = upload new template (no retraining)

### 4. Fine-Tuning for Behavior, Not Facts

**Why:** Efficient scaling
- Train once on ~110 style examples
- Model learns "how to teach" not "what to teach"
- Content lives in RAG (easily updatable)

---

## Training Data Strategy

**Initial Approach:** Fine-tune only Agent 1 (Teaching). Use base models with prompting for Agent 2 (Grading) and Agent 3 (Generation).

### Teaching Agent Training Dataset

**Total Size:** ~40 conversations

```
teaching_training_data.jsonl
├─ Vocabulary batch introduction (~10 conversations)
├─ Vocabulary quiz feedback (~10 conversations)
├─ Grammar explanation (~15 conversations)
└─ Grammar quiz feedback (~5 conversations)
```

**Optional Future Fine-Tuning:**
- Agent 2 (Grading): If baseline evaluation shows accuracy issues (~40 grading conversations)
- Agent 3 (Generation): If exercise quality needs improvement (~30 generation conversations)

---

### Mode 1: Teaching Style (~40 conversations)

**Focus:** Encouraging pedagogy, structured presentations, comprehension questions

**Sub-modes:**
- Vocabulary batch introduction (~10 conversations)
- Vocabulary quiz feedback (~10 conversations)
- Grammar explanation (~15 conversations)
- Grammar quiz feedback (~5 conversations)

**System prompt patterns:**

*Vocabulary batch introduction:*
```
Mode: vocab_batch_introduction
Lesson: {lesson_number}
Batch: {batch_number}
Words: {word_list_with_transliteration}
```

**Example conversation:**
```json
{
  "messages": [
    {
      "role": "system",
      "content": "Mode: vocab_batch_introduction\nLesson: 3\nBatch: 1\nWords: [{\"arabic\": \"كِتَاب\", \"transliteration\": \"kitaab\", \"english\": \"book\"}, {\"arabic\": \"مَدْرَسَة\", \"transliteration\": \"madrasa\", \"english\": \"school\"}, {\"arabic\": \"قَلَم\", \"transliteration\": \"qalam\", \"english\": \"pen\"}]"
    },
    {"role": "user", "content": "Show me batch 1"},
    {
      "role": "assistant",
      "content": "Let's learn Batch 1! Here are your first 3 words:\n\n📝 كِتَاب (kitaab) - book\n📝 مَدْرَسَة (madrasa) - school\n📝 قَلَم (qalam) - pen\n\nTake your time reviewing these. When you're ready, let's test your knowledge!"
    }
  ]
}
```

*Grammar explanation:*
```
Mode: grammar_explanation
Lesson: {lesson_number}
Topic: {topic_name}
Grammar Rule: {rule_description}
Examples: {examples}
```

**Example conversation:**
```json
{
  "messages": [
    {
      "role": "system", 
      "content": "Mode: grammar_explanation\nLesson: 3\nTopic: Feminine Nouns\nGrammar Rule: Feminine nouns usually end in ة (taa marbuuta)\nExamples: مَدْرَسَة (school) ✓, كِتَاب (book - masculine) ✗"
    },
    {"role": "user", "content": "Teach me this topic"},
    {
      "role": "assistant", 
      "content": "Let's learn about Feminine Nouns! 🌟\n\n**The Rule:**\nIn Arabic, most feminine nouns end with ة (taa marbuuta).\n\n**Examples:**\n- مَدْرَسَة (madrasa) - school ✓ (ends in ة)\n- كِتَاب (kitaab) - book (masculine, no ة)\n\n**Quick Check:** Look at the word بِنْت (bint - girl). Does it end in ة?"
    }
  ]
}
```

**Key:** Uses placeholders in system prompt - actual content inserted at inference from Agent 3's cache

---

### Agent 2 & 3: Base Models with Prompting (Not Fine-Tuned Initially)

**Agent 2 (Grading) - Qwen2.5-7B Base:**
- Uses detailed prompts with grammar rules and flexible matching instructions
- Accepts typos, synonyms, abbreviations through prompt guidance
- Returns JSON with grading results
- Will fine-tune only if baseline evaluation shows accuracy issues

**Agent 3 (Generation) - Qwen2.5-3B Base:**
- Uses prompts with exercise templates and cached vocabulary
- Generates varied exercises from templates
- Returns JSON array of exercises
- Will fine-tune only if exercise quality needs improvement

**Note:** Both agents rely on good prompting initially. Fine-tuning is optional based on baseline evaluation results.

---

## Scalability: Adding New Grammar

**Old approach (v1):**
1. Write 20-30 new training examples
2. Retrain model (20-30 min)
3. Test and validate
4. Repeat for each new grammar point

**New approach (v2):**
1. Write `lesson_XX_new_grammar.md` (5 min):
```markdown
---
lesson: 5
grammar_point: negation_particles
---

# Negation in Arabic

## Rule
Use لا for present/future, ما for past

## Examples
- لا أكتب (I don't write) ✓
- ما كتبت (I didn't write) ✓

## Detection Pattern
If negation particle doesn't match tense → ERROR
```

2. Upload to RAG database (1 min)
3. Test immediately (no retrain needed!)
4. **Total time: 6 minutes vs. 30+ minutes**

---

## Model Strategy

### Two-Model Architecture

**Agent 1 (Teaching):** Qwen2.5-3B-Instruct (fine-tuned)
- Fine-tuned on ~40 teaching conversations
- Optimized for encouraging tone and pedagogical structure
- Lightweight (2GB with 4-bit quantization)
- Fast inference for real-time teaching interactions

**Agent 2 (Grading):** Qwen2.5-7B-Instruct (base, not fine-tuned)
- Better reasoning for semantic comparison
- Strong Arabic comprehension
- Handles flexible grading (typos, synonyms, abbreviations)
- Base model sufficient with good prompting
- May fine-tune later if accuracy needs improvement

**Agent 3 (Generation):** Qwen2.5-3B-Instruct (base with prompting)
- Uses base 3B model initially (no fine-tuning needed)
- Can fine-tune later for exercise generation patterns if needed
- Generates exercises from templates using cached vocabulary

**Why Two Different Models:**
- **Teaching needs fine-tuning:** Specific tone/style requirements for user-facing content
- **Grading needs reasoning:** 7B provides better semantic understanding for flexible matching
- **Separation of concerns:** Teaching optimized for friendliness, grading optimized for accuracy

**Training Strategy (Agent 1 Only):**
```
Fine-tune Qwen2.5-3B on teaching conversations (~40 total):
├─ Vocabulary batch introduction (~10 conversations)
├─ Vocabulary quiz feedback (~10 conversations)
├─ Grammar explanation (~15 conversations)
└─ Grammar quiz feedback (~5 conversations)
```

**Memory Requirements:**
- 3B Model (4-bit): ~2GB
- 7B Model (4-bit): ~4GB
- Context (1536 tokens): ~1GB per model
- Total: ~7GB RAM (both models loaded)

**Why 3B for Teaching:**
- Sufficient for style learning (not memorizing content)
- Fast inference for interactive teaching
- Small training dataset (40 conversations)

**Why 7B for Grading:**
- Better reasoning for semantic comparison
- Stronger Arabic language understanding
- More reliable for critical grading decisions
- Reduces false negatives/positives

---

## Technology Stack

| Component | Tool | Why |
|-----------|------|-----|
| Orchestration | LangGraph | State management, agent routing |
| **Agent 1 LLM** | **Qwen2.5-3B (fine-tuned)** | **Teaching style - encouraging, structured** |
| **Agent 2 LLM** | **Qwen2.5-7B (base)** | **Grading - better reasoning, Arabic comprehension** |
| **Agent 3 LLM** | **Qwen2.5-3B (base)** | **Exercise generation - prompting sufficient** |
| Agent 3 RAG | Pinecone | Cloud vector database, scalable retrieval |
| Prompt Assembly | LangChain PromptTemplate | Variable formatting for all agents |
| Vector Embeddings | `all-MiniLM-L6-v2` (sentence-transformers) | Free, 384-dim embeddings, used in assignment 8 |
| Evaluation | DeepEval + Qwen2.5-7B | Automated testing with LLM-as-a-Judge for alignment |

---

## Success Metrics

### Agent 1 (Teaching)
- ✅ Maintains encouraging tone (95%+ positive sentiment)
- ✅ Structures explanations clearly
- ✅ Asks comprehension questions proactively

### Agent 2 (Error Detection)
- ✅ 90%+ accuracy on correct/incorrect classification
- ✅ Identifies error type correctly
- ✅ Generalizes to unseen grammar points

### Agent 3 (Content Retrieval)
- ✅ Retrieves relevant rules (90%+ relevance score)
- ✅ Fast retrieval (<500ms)
- ✅ Handles 100+ grammar points without degradation

### Overall System
- ✅ Can add new grammar in <10 minutes
- ✅ No retraining needed for content expansion
- ✅ Student satisfaction: encouraging + accurate feedback

---

## Next Steps

Following modern **Eval-Driven Development** approach (2026 best practices):

### Phase 1: Foundation (Define Success First)
1. **Create evaluation dataset** - Test cases with expected outputs
2. **Set up DeepEval pipeline** - Automated testing, baseline scores
3. **Build RAG database** - Lessons 1-8 grammar rules and templates

### Phase 2: Core Components (Build & Measure)
4. **Create training data** - 40 teaching conversations for Agent 1
5. **Fine-tune Qwen2.5-3B** - Agent 1 teaching style only
6. **Build Agent 2** (Grading) - Use base Qwen2.5-7B with prompting, test against evals
7. **Build Agent 3** (Content Retrieval + Generation) - Use base Qwen2.5-3B with prompting, test in isolation
8. **Build Agent 1** (Teaching Presentation) - Use fine-tuned 3B, test in isolation
9. **Evaluate grading accuracy** - If <90%, create grading training data and fine-tune 7B

### Phase 3: Integration (Orchestrate)
9. **Build simple orchestrator** - Basic routing between agents
10. **Test end-to-end flows** - Full lesson and quiz flows
11. **Add LangGraph** - State management, complex routing

### Phase 4: Scale Testing (Validate Architecture)
12. **Add Lessons 9-10** - Verify no retraining needed
13. **Run full eval suite** - Confirm all metrics still pass

**Detailed implementation plan with TDD approach:** See `IMPLEMENTATION_PLAN.md`

---

**Status:** Architecture defined, ready for implementation
**Created:** 2026-04-03
