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
2. **Fine-tuned LLM** (Qwen 7B - teaching style) - Adds pedagogical style

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
3. **Fine-tuned LLM** (Qwen 7B - strict grading style) - Returns structured JSON

**Why Both Fine-Tuning AND Prompt?**

Fine-tuning teaches **behavior:**
- ✅ Output JSON format
- ✅ Strict grading style (no encouragement)
- ✅ How to identify error patterns WHEN GIVEN A RULE
- ✅ Error categorization

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

**Fine-tuned On:**
- Strict grading patterns (~40 conversations)
- JSON output format
- Error type identification
- **Generic** error patterns (not specific grammar rules - those come via prompt)

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
- **Option A:** Same fine-tuned Qwen 7B (reuse Agent 1/2 model)
- **Option B:** Smaller model like GPT-3.5-turbo or Qwen 1.5B (cheaper/faster for simple generation)
- **Option C:** Fine-tune separate small model just for exercise generation

**Recommendation:** Start with Option B (GPT-3.5-turbo) - simple generation doesn't need fine-tuning

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

**One Model, Three Modes:** Single combined dataset trains one Qwen2.5-3B model that can operate in three different modes based on system prompts.

### Combined Training Dataset

**Total Size:** 110-120 conversations

```
combined_training_data.jsonl
├─ Teaching Mode (~40 conversations)
│  ├─ Vocabulary batch introduction (~10)
│  ├─ Vocabulary quiz feedback (~10)
│  ├─ Grammar explanation (~15)
│  └─ Grammar quiz feedback (~5)
├─ Grading Mode (~40 conversations)
│  ├─ Vocabulary grading (~15)
│  └─ Grammar grading (~25)
└─ Exercise Generation Mode (~30 conversations)
```

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

### Mode 2: Grading Style (~40 conversations)

**Focus:** Strict JSON output, error identification, no encouragement

**System prompt pattern:**
```
Mode: Grading
Lesson: {lesson_number}
Grammar Rules: {rules_with_detection_patterns}
```

**Example conversation (correct answer):**
```json
{
  "messages": [
    {
      "role": "system",
      "content": "Mode: Grading\nLesson: 3\nRule: Adjectives must match noun gender\nPattern: If noun.gender ≠ adj.gender → error"
    },
    {
      "role": "user",
      "content": "{\"answers\": [{\"answer_id\": \"q1\", \"student_answer\": \"كتاب كبير\", \"expected_pattern\": \"كتاب كبير\", \"grammar_points\": [\"gender_agreement\"]}]}"
    },
    {
      "role": "assistant",
      "content": "{\"results\": [{\"answer_id\": \"q1\", \"correct\": true, \"errors\": [], \"total_errors\": 0}]}"
    }
  ]
}
```

**Example conversation (incorrect answer):**
```json
{
  "messages": [
    {
      "role": "system",
      "content": "Mode: Grading\nLesson: 3\nRule: Adjectives must match noun gender"
    },
    {
      "role": "user",
      "content": "{\"answers\": [{\"answer_id\": \"q1\", \"student_answer\": \"كتاب كبيرة\", \"expected_pattern\": \"كتاب كبير\", \"grammar_points\": [\"gender_agreement\"]}]}"
    },
    {
      "role": "assistant",
      "content": "{\"results\": [{\"answer_id\": \"q1\", \"correct\": false, \"errors\": [{\"error_type\": \"gender_mismatch\", \"grammar_point\": \"noun_adjective_agreement\", \"details\": \"كتاب (masculine) paired with كبيرة (feminine)\", \"correction\": \"Use كبير (masculine) to match كتاب\"}], \"total_errors\": 1, \"correct_form\": \"كتاب كبير\"}]}"
    }
  ]
}
```

**Mix includes:**
- Correct answers (output correct: true)
- Gender errors
- Definiteness errors
- Verb errors
- Multiple errors in one answer
- Generic error patterns (not specific grammar rules)

---

### Mode 3: Exercise Generation (~30 conversations)

**Focus:** Generate exercises from templates using provided vocabulary

**System prompt pattern:**
```
Mode: Exercise Generation
Lesson: {lesson_number}
Template: {exercise_template}
Primary Vocabulary: {student_vocab}
Additional Vocabulary: {optional_extra_words}
```

**Example conversation:**
```json
{
  "messages": [
    {
      "role": "system",
      "content": "Mode: Exercise Generation\nLesson: 3\nTemplate: Fill-in-blank with gender agreement\nPrimary Vocabulary: كبير, صغير, جميل\nGrammar Focus: Adjective must match noun gender"
    },
    {
      "role": "user",
      "content": "Generate 3 fill-in-blank exercises"
    },
    {
      "role": "assistant",
      "content": "[{\"question\": \"Complete: كِتَاب ___\", \"answer\": \"كَبِير\", \"options\": [\"كَبِير\", \"كَبِيرَة\"], \"explanation\": \"كتاب is masculine\"}, {\"question\": \"Complete: مَدْرَسَة ___\", \"answer\": \"كَبِيرَة\", \"options\": [\"كَبِير\", \"كَبِيرَة\"], \"explanation\": \"مدرسة is feminine\"}, {\"question\": \"Complete: بَيْت ___\", \"answer\": \"صَغِير\", \"options\": [\"صَغِير\", \"صَغِيرَة\"], \"explanation\": \"بيت is masculine\"}]"
    }
  ]
}
```

**Variety includes:**
- Fill-in-blank
- Translation
- Correction exercises
- Multiple choice
- Different grammar points

---

## Scalability: Alooks gooddding New Grammar

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

### Single Model for All Agents

**Model:** Qwen2.5-3B-Instruct (fine-tuned once)

**Why One Model:**
- ✅ Free (run locally)
- ✅ Small enough (2GB with 4-bit quantization)
- ✅ Sufficient for style learning (not memorizing grammar rules)
- ✅ One training run (~20 min)
- ✅ Load once, use for all three agents

**Training Strategy:**
```
One combined dataset (110-120 conversations):
├─ Teaching style (~40 conversations)
│  └─ System: "Mode: Teaching" → Encouraging, structured
├─ Grading style (~40 conversations)
│  └─ System: "Mode: Grading" → Strict JSON output
└─ Exercise generation (~30 conversations)
   └─ System: "Mode: Exercise Generation" → Template filling
```

**Behavior Control:**
Different system prompts at inference time control which "mode" the model uses.

```python
# Agent 1: Teaching mode
system_prompt = "Mode: Teaching\nBe encouraging and structured."

# Agent 2: Grading mode
system_prompt = "Mode: Grading\nOutput strict JSON with error analysis."

# Agent 3: Exercise generation mode
system_prompt = "Mode: Exercise Generation\nGenerate exercises from templates."
```

**Memory Requirements:**
- Model (4-bit): ~2GB
- Context (1536 tokens): ~1GB
- Total: ~3GB RAM

**Why 3B (not 1.5B or 7B):**
- 1.5B: Too small for reliable JSON output
- 3B: Sweet spot (v6/v7 showed good results)
- 7B: Unnecessary for style-only learning, uses more memory

---

## Technology Stack

| Component | Tool | Why |
|-----------|------|-----|
| Orchestration | LangGraph | State management, agent routing |
| **All Agents LLM** | **Qwen2.5-3B (fine-tuned once)** | **Teaching, grading, generation styles** |
| Agent 3 RAG | Pinecone | Cloud vector database, scalable retrieval |
| Prompt Assembly | LangChain PromptTemplate | Variable formatting for all agents |
| Vector Embeddings | `all-MiniLM-L6-v2` (sentence-transformers) | Free, 384-dim embeddings, used in assignment 8 |
| Evaluation | DeepEval | Automated quality testing with LLM-as-a-Judge |

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
4. **Create training data** - 110 conversations (teaching + grading + generation)
5. **Fine-tune Qwen2.5-3B** - Single model, three modes
6. **Build Agent 2** (Error Detection) - Test in isolation against evals
7. **Build Agent 3** (Content Retrieval + Generation) - Test in isolation
8. **Build Agent 1** (Teaching Presentation) - Test in isolation

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
