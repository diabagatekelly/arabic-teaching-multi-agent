# Test Status After Scope Simplification

## Current Situation

After simplifying the lesson (10 words → 6 words, 2 grammar topics → 1), integration tests are failing because:

1. **RAG database not re-embedded** - still has old lesson content
2. **Mock responses outdated** - welcome message says "10 words and 2 grammar topics"
3. **Model responses need retraining** - using mock model that returns generic responses

## Test Results (as of now)

### ✅ Passing Tests
- `test_lesson_start_awaits_user_doesnt_auto_teach` - Basic orchestration logic works

### ❌ Failing Tests
- `test_lesson_start_to_vocab_quiz_generation` - Expects structured vocab batch response

**Failure details:**
```
Welcome message: "Welcome to Lesson 1! 🌟 Today we'll learn 10 words and 2 grammar topics."
                  Should say: "6 words and 1 grammar topic"

Vocab batch response: "I'm here to help you learn Arabic!"
                      Should show: Arabic words with transliteration
```

## What Needs To Be Done

### 1. Re-embed RAG Database (REQUIRED)
```bash
cd /Users/kellydiabagate/Documents/LLMCourse/arabic-teaching-multi-agent
# Run your embedding script to update Pinecone with new lesson content
python scripts/embed_lessons.py  # or whatever your script is
```

**Why:** The lesson file `lesson_01_gender_definite_article.md` was updated with 6 words, but the vector database still has 10 words indexed.

### 2. Retrain Teaching Agent (REQUIRED)
The model needs retraining with:
- Updated training data (207 examples with conversational + intent variations)
- New lesson scope (6 words, 1 grammar concept)
- Control markers (`[GENERATE_EXERCISE]`)

**After retraining:** Tests will use the new model and should return properly structured responses.

### 3. Update Test Expectations (OPTIONAL - Can wait)
Some tests might have hard-coded expectations that need updating after retraining:

```python
# In test_complete_lesson_flow.py - Step 2 expectations
# Currently checks: has Arabic words, transliteration
# May need to add: checks for 3 words per batch, masculine words in batch 1

# New checks to add after Step 4 (feedback):
assert "Ready for the next word?" in feedback_content.lower()
assert result["next_agent"] == "agent3"  # Auto-generate next quiz
assert len(result["batch_quizzed_words"]) == 1  # Track quizzed words

# New test needed: Batch completion
# After 3rd word in batch:
assert "✅ Batch 1 Complete!" in result["conversation_history"][-1].content
assert result["batch_correct_count"] == 0  # Reset after summary
assert result["batch_quizzed_words"] == []  # Reset after summary
```

## Action Plan

### Immediate (Before Retraining)
1. ✅ Updated lesson RAG document (done)
2. ✅ Updated training data with 207 examples (done)
3. ✅ Updated orchestrator to strip `[GENERATE_EXERCISE]` marker (done)
4. ✅ Added batch tracking to state (done)
5. ⏳ Re-embed RAG database (TODO - run embedding script)

### After Retraining
6. Deploy new model
7. Run integration tests
8. Update test assertions if needed (based on actual model responses)
9. Add new tests for:
   - Auto-quiz generation after feedback
   - Batch completion summary
   - Batch progression

## Test Strategy

### Current Approach
Tests use **real agents** with **mocked LLM responses**. This tests orchestration logic but not actual model quality.

### After Retraining
You can choose:

**Option A: Keep mocked LLMs** (fast, tests orchestration)
- Update mocks to return expected format
- Good for CI/CD

**Option B: Use real fine-tuned model** (slow, tests everything)
- Tests actual model responses
- Better for validation
- Can use for smoke tests, not every CI run

**Recommendation:** 
- Keep mocked tests for fast feedback
- Add a separate "smoke test" suite that uses the real model
- Run smoke tests manually before deployments

## Expected Test Outcomes After Re-embedding + Retraining

### Should Pass
- ✅ Lesson start with 6 words
- ✅ Vocab batch shows 3 words with Arabic + transliteration
- ✅ Quiz generation after user request
- ✅ Grading and feedback flow
- ✅ Auto-generation after feedback (NEW)
- ✅ Batch completion summary (NEW)

### May Need Adjustment
- Format of auto-generated summary text
- Exact wording of "Ready for next word?" prompt
- Batch progression messages

## Summary

**Current blocker:** RAG database has old content (10 words), model not retrained yet.

**Next steps:**
1. Re-embed RAG → fixes lesson content
2. Retrain model → fixes responses  
3. Run tests → see what needs tweaking
4. Update test assertions → match actual model behavior

**Estimated time:**
- Re-embedding: 5-10 minutes
- Retraining: 30-60 minutes (depending on GPU)
- Test updates: 15-30 minutes
