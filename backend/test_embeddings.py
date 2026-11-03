"""
Step 2 test: prove the embedding model works and actually captures meaning
(not just producing random numbers). No database, no documents yet.

Run from the backend/ folder:
    python test_embeddings.py

First run will download the model (~90MB) - that's normal and only happens once.
"""
import numpy as np

from app.embeddings import embed_texts, EMBEDDING_DIM


def cosine_similarity(a, b):
    a, b = np.array(a), np.array(b)
    return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)))


def main():
    print("1. Loading model and embedding 3 test sentences...")
    sentences = [
        "We advised the client on their retail supply chain strategy in 2022.",
        "In 2022 we gave supply-chain recommendations to a retail customer.",
        "The office coffee machine broke down last Tuesday.",
    ]
    vectors = embed_texts(sentences)
    print(f"   OK. Got {len(vectors)} vectors.")

    print(f"\n2. Checking vector dimension matches Supabase column (384)...")
    dim = len(vectors[0])
    if dim == EMBEDDING_DIM == 384:
        print(f"   OK. Dimension = {dim}. Matches vector(384) in Supabase.")
    else:
        print(f"   MISMATCH: got {dim}, expected 384. Do not proceed to ingest yet.")
        return

    print("\n3. Checking the model actually understands meaning, not just words...")
    sim_related = cosine_similarity(vectors[0], vectors[1])
    sim_unrelated = cosine_similarity(vectors[0], vectors[2])
    print(f"   Similarity between the two supply-chain sentences (different wording): {sim_related:.3f}")
    print(f"   Similarity between supply-chain sentence and coffee-machine sentence:   {sim_unrelated:.3f}")

    if sim_related > sim_unrelated:
        print("   OK. Related-meaning sentences scored higher than unrelated ones.")
        print("   This is the core mechanic RAG relies on.")
    else:
        print("   UNEXPECTED: unrelated sentence scored higher. Something's off.")
        return

    print("\nALL CHECKS PASSED. Embeddings are working and dimension-compatible.")
    print("Ready for Step 3: chunking a real document.")


if __name__ == "__main__":
    main()