"""Mock agent responses for orchestrator testing.

These responses simulate what the teaching agent would return after being trained
with keyword-based routing. Each response contains a keyword that the orchestrator
should detect to route to the correct next agent.
"""

# ===== Lesson Start =====
LESSON_START_WELCOME = """Welcome to Lesson 1! 🌟

Today you'll learn:
- **Vocabulary:** 6 words (2 batches)
- **Grammar:** Masculine and Feminine Nouns

Where would you like to start?
1. Learn vocabulary
2. Learn grammar
3. See my progress"""


# ===== Request Quiz =====
REQUEST_QUIZ_RESPONSE_1 = "Great! Let me prepare your quiz."

REQUEST_QUIZ_RESPONSE_2 = "Perfect! Starting your quiz now."

REQUEST_QUIZ_RESPONSE_3 = "Love the energy! Starting your quiz."


# ===== Mid-Quiz Feedback (Correct) =====
MID_QUIZ_CORRECT_1 = "Correct! ✓ كِتَاب = book. Next word."

MID_QUIZ_CORRECT_2 = "Perfect! ✓ بَيْت = house. Next word."

MID_QUIZ_CORRECT_3 = "Excellent! ✓ طَاوِلَة = table. Next word."


# ===== Mid-Quiz Feedback (Incorrect) =====
MID_QUIZ_INCORRECT_1 = "Not quite! كِتَاب means 'book'. Next word."

MID_QUIZ_INCORRECT_2 = "Close! مَدْرَسَة means 'school'. Next word."


# ===== Batch Complete =====
BATCH_COMPLETE_RESPONSE = """Perfect! ✓ قَلَم = pen.

Batch 1 complete! 🎉 Score: 3/3

Ready for Batch 2?"""


# ===== Request Next Batch =====
REQUEST_NEXT_BATCH_1 = "Great! Here's Batch 2."

REQUEST_NEXT_BATCH_2 = "Perfect! Loading Batch 2."

REQUEST_NEXT_BATCH_3 = "Let's go! Here's Batch 2."


# ===== Request Grammar =====
REQUEST_GRAMMAR_1 = "Perfect! Switching to grammar."

REQUEST_GRAMMAR_2 = "Great! Let's dive into grammar."

REQUEST_GRAMMAR_3 = "Of course! Moving to grammar."


# ===== Request Vocabulary =====
REQUEST_VOCABULARY_1 = "Perfect! Here's your vocabulary:\n\nBatch 1:\n📚 كِتَاب (kitaabun) - book"

REQUEST_VOCABULARY_2 = "Great! Let's start with vocabulary.\n\nBatch 1:\n📚 كِتَاب (kitaabun) - book"


# ===== Request Final Test =====
REQUEST_FINAL_TEST_1 = "Excellent! Preparing your final exam."

REQUEST_FINAL_TEST_2 = "Perfect! Starting your final test."

REQUEST_FINAL_TEST_3 = "Love it! Setting up your final exam."


# ===== Request Break =====
REQUEST_BREAK_1 = "No problem! Take a break. Progress saved."

REQUEST_BREAK_2 = "Of course! Take a break. Everything is saved."

REQUEST_BREAK_3 = "That's fine! Let's take a break. Progress saved."


# ===== Request Progress =====
REQUEST_PROGRESS_1 = """Let me show your progress:

📊 Batch 1: ✓ Complete (3/3)
📊 Batch 2: In progress

You're doing great!"""

REQUEST_PROGRESS_2 = """Here's your progress:

📊 Lesson 1:
- Batch 1: ✓ Complete
- Batch 2: Ready to start

Keep going!"""


# ===== Off-Topic =====
OFF_TOPIC_1 = "Haha, that's off topic! Let's focus on Arabic or take a break."

OFF_TOPIC_2 = "That's off topic! Want to continue Arabic or take a break?"

OFF_TOPIC_3 = "A bit off topic! Let's focus on Arabic or take a break."


# ===== Bored/Frustrated =====
BORED_RESPONSE_1 = "I understand! You can take a break anytime. Or try grammar instead?"

BORED_RESPONSE_2 = "I hear you! Take a break or switch to grammar?"


# ===== Profanity =====
PROFANITY_RESPONSE_1 = "Let's keep it respectful! Want to take a break?"

PROFANITY_RESPONSE_2 = "Please keep language respectful. Need a break?"


# ===== Inappropriate =====
INAPPROPRIATE_RESPONSE_1 = "That's off topic! Want to continue Arabic or take a break?"

INAPPROPRIATE_RESPONSE_2 = (
    "That's inappropriate. Let's keep this professional. Want to take a break?"
)


# ===== Clarification =====
CLARIFICATION_RESPONSE = """No problem! Here's the key:

Feminine nouns end with ة (taa marbuuta). That's your clue!

Example: مَدْرَسَة (school) - has ة = feminine"""


# ===== All Vocabulary Complete =====
ALL_VOCAB_COMPLETE = """Perfect! ✓ نَافِذَة = window.

Batch 2 complete! 🎉 Score: 3/3

All vocabulary done! Ready for grammar or final test?"""


# ===== Final Test Complete =====
FINAL_TEST_COMPLETE = """Correct! ✓

Final test complete! 🎉 Score: 5/5 - Perfect!

You've mastered Lesson 1!"""
