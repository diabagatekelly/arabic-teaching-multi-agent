"""Build lesson cache from Pinecone and save to JSON."""

import json
import re

from src.rag.pinecone_client import PineconeClient
from src.rag.rag_retriever import RAGRetriever
from src.rag.sentence_transformer_client import SentenceTransformerClient

embedder = SentenceTransformerClient()
vector_db = PineconeClient()
rag_retriever = RAGRetriever(embedder, vector_db)

lesson_cache = {}

for lesson_num in range(1, 11):
    try:
        vocab_results = rag_retriever.retrieve_by_lesson(
            query="vocabulary words list table", lesson_number=lesson_num, top_k=10
        )
        grammar_results = rag_retriever.retrieve_by_lesson(
            query="grammar rules points topics", lesson_number=lesson_num, top_k=10
        )

        if not vocab_results and not grammar_results:
            print(f"✗ No results for Lesson {lesson_num}")
            continue

        metadata = (vocab_results[0] if vocab_results else grammar_results[0]).get("metadata", {})

        vocab_list = []
        for result in vocab_results:
            text = result.get("text", "")

            # Try numbered list format: "1. كِتَابٌ (kitaabun) - book"
            list_rows = re.findall(r"\d+\.\s+(\S+)\s+\(([^)]+)\)\s+-\s+(.+)", text)
            for row in list_rows:
                vocab_list.append(
                    {
                        "arabic": row[0].strip(),
                        "transliteration": row[1].strip(),
                        "english": row[2].strip(),
                    }
                )

            # Try table format: "| Arabic | transliteration | english |"
            table_rows = re.findall(r"\|\s*([^\|]+)\s*\|\s*([^\|]+)\s*\|\s*([^\|]+)\s*\|", text)
            for row in table_rows:
                if (
                    row[0].strip()
                    and not row[0].strip().startswith("--")
                    and row[0].strip() != "Arabic"
                ):
                    vocab_list.append(
                        {
                            "arabic": row[0].strip(),
                            "transliteration": row[1].strip(),
                            "english": row[2].strip(),
                        }
                    )

        grammar_points = metadata.get("grammar_points", [])
        if isinstance(grammar_points, str):
            import json

            try:
                grammar_points = json.loads(grammar_points)
            except (json.JSONDecodeError, TypeError):
                grammar_points = [grammar_points]

        lesson_cache[str(lesson_num)] = {
            "lesson_number": lesson_num,
            "lesson_name": metadata.get("lesson_name", f"Lesson {lesson_num}"),
            "vocabulary": vocab_list,
            "grammar_points": grammar_points,
            "grammar_sections": {},
            "difficulty": metadata.get("difficulty", "beginner"),
        }
        print(f"✓ Lesson {lesson_num}: {len(vocab_list)} words")
    except Exception as e:
        print(f"✗ Error: {e}")

with open("lesson_cache.json", "w", encoding="utf-8") as f:
    json.dump(lesson_cache, f, ensure_ascii=False, indent=2)

print(f"\n✓ Saved {len(lesson_cache)} lessons to lesson_cache.json")
