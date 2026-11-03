"""
Step 4 test: the full ingest pipeline for ONE document.
PDF file -> extract text -> chunk -> embed locally -> store in Supabase.

Run from the backend/ folder:
    python test_ingest.py "../data/your_file.pdf"

Note: running this twice on the same file will insert it TWICE (we haven't
added "skip if already ingested" logic yet - that's a fine next improvement,
but for proving the pipeline works, simple is better).
"""
import sys

from app.chunking import pdf_to_chunks
from app.embeddings import embed_texts
from app.db import insert_document, insert_chunks


def main():
    if len(sys.argv) < 2:
        print("Usage: python test_ingest.py /path/to/file.pdf")
        return

    path = sys.argv[1]
    filename = path.split("/")[-1].split("\\")[-1]

    print(f"1. Reading and chunking: {filename}")
    with open(path, "rb") as f:
        pdf_bytes = f.read()
    chunks = pdf_to_chunks(pdf_bytes)
    print(f"   OK. {len(chunks)} chunks produced.")

    print(f"\n2. Embedding {len(chunks)} chunks locally (this may take a bit)...")
    texts = [c["content"] for c in chunks]
    vectors = embed_texts(texts)
    print(f"   OK. {len(vectors)} vectors produced, dimension {len(vectors[0])}.")

    print(f"\n3. Creating a 'documents' row in Supabase...")
    document_id = insert_document(filename)
    print(f"   OK. document_id = {document_id}")

    print(f"\n4. Inserting {len(chunks)} chunk rows into Supabase (batched)...")
    inserted = insert_chunks(document_id, chunks, vectors)
    print(f"   OK. {inserted} rows inserted.")

    print("\nALL DONE. This document is now searchable.")
    print(f"document_id: {document_id}")
    print("Ready for Step 5: asking a real question and seeing retrieval work.")


if __name__ == "__main__":
    main()