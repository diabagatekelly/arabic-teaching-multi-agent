"""
Initialize and populate the ChromaDB vectorstore with exercise templates.
"""

from __future__ import annotations

import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from rag.ingestion import load_templates, prepare_for_ingestion  # noqa: E402
from rag.vectorstore import VectorStore  # noqa: E402


def main() -> None:
    """Load templates and populate vectorstore."""
    print("Loading exercise templates...")
    templates = load_templates()
    print(f"Found {len(templates)} templates")

    print("\nPreparing templates for ingestion...")
    documents, metadatas, ids = prepare_for_ingestion(templates)

    print("\nInitializing vectorstore...")
    vectorstore = VectorStore()

    existing_count = vectorstore.get_count()
    if existing_count > 0:
        print(f"Vectorstore already contains {existing_count} documents")
        response = input("Reset and rebuild? (y/n): ")
        if response.lower() == "y":
            print("Resetting vectorstore...")
            vectorstore.reset()
        else:
            print("Keeping existing vectorstore")
            return

    print("\nIngesting documents...")
    vectorstore.add_documents(documents=documents, metadatas=metadatas, ids=ids)

    final_count = vectorstore.get_count()
    print(f"\n✓ Vectorstore initialized with {final_count} documents")

    print("\nSample templates by type:")
    for ex_type in ["fill_in_blank", "multiple_choice", "error_correction"]:
        count = sum(1 for m in metadatas if m.get("exercise_type") == ex_type)
        print(f"  - {ex_type}: {count}")

    print("\nSample templates by skill:")
    for skill in ["vocabulary", "grammar", "mixed"]:
        count = sum(1 for m in metadatas if m.get("skill_focus") == skill)
        print(f"  - {skill}: {count}")

    print("\nSample templates by lesson:")
    for lesson in [1, 2]:
        count = sum(1 for m in metadatas if m.get("lesson") == lesson)
        print(f"  - Lesson {lesson}: {count}")


if __name__ == "__main__":
    main()
