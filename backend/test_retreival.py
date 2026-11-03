"""
Step 5 test: ask a real question about the ingested document and see if
retrieval pulls back the right passages. This is the actual "proof" you'd
show a client for Milestone 1 - no LLM involved yet, just: does the database
find the right chunks for a question.

Run from the backend/ folder:
    python test_retrieval.py "your question here"

Example (for the tracking paper we ingested):
    python test_retrieval.py "what is dense temporal token learning?"
"""
import sys

from app.embeddings import embed_query
from app.db import search_chunks


def main():
    if len(sys.argv) < 2:
        print('Usage: python test_retrieval.py "your question"')
        return

    question = " ".join(sys.argv[1:])

    print(f"Question: {question}\n")

    print("1. Embedding the question...")
    query_vector = embed_query(question)
    print(f"   OK. {len(query_vector)}-dim vector produced.")

    print("\n2. Searching for the closest chunks in Supabase...")
    results = search_chunks(query_vector, top_k=5)
    print(f"   OK. Got {len(results)} result(s).\n")

    if not results:
        print("   No results. Did test_ingest.py run successfully first?")
        return

    print("=" * 70)
    for i, r in enumerate(results, start=1):
        print(f"Result {i}  |  similarity = {r['similarity']:.3f}  |  page {r['page']}")
        print("-" * 70)
        print(r["content"][:400] + ("..." if len(r["content"]) > 400 else ""))
        print("=" * 70)

    print("\nLook at the top result: does it actually answer the question?")
    print("If yes - retrieval is working. This is your Milestone 1 proof.")


if __name__ == "__main__":
    main()