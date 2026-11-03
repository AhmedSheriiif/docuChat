"""
Step 6 test: the full RAG pipeline, end to end.
Question -> embed -> retrieve chunks from Supabase -> Groq writes a grounded
answer citing pages. This is the complete Milestone 2 proof.

Run from the backend/ folder:
    python test_answer.py "your question here"
"""
import sys

from app.embeddings import embed_query
from app.db import search_chunks
from app.generation import generate_answer


def main():
    if len(sys.argv) < 2:
        print('Usage: python test_answer.py "your question"')
        return

    question = " ".join(sys.argv[1:])
    print(f"Question: {question}\n")

    print("1. Retrieving relevant chunks...")
    query_vector = embed_query(question)
    chunks = search_chunks(query_vector, top_k=5)
    print(f"   OK. Retrieved {len(chunks)} chunk(s) "
          f"(top similarity: {chunks[0]['similarity']:.3f})" if chunks else "   No chunks found.")

    print("\n2. Asking Groq to write a grounded answer...")
    answer = generate_answer(question, chunks)

    print("\n" + "=" * 70)
    print("ANSWER:")
    print("=" * 70)
    print(answer)
    print("=" * 70)

    print("\nSources used (for you to verify against the real document):")
    for c in chunks:
        print(f"  - page {c['page']}, similarity {c['similarity']:.3f}")


if __name__ == "__main__":
    main()