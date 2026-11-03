"""
Ingest every .pdf and .pptx file in a folder - the real-world version of
test_ingest.py, for loading many documents at once (like Dana's ~40-file
pilot set, or here, stress-testing with your own thesis materials).

Skips any file whose filename is already in the `documents` table, so it's
safe to re-run if it gets interrupted partway through.

Run from the backend/ folder:
    python ingest_folder.py "../data"
"""
import sys
from pathlib import Path

from app.chunking import file_to_chunks
from app.embeddings import embed_texts
from app.db import document_exists, insert_document, insert_chunks, delete_document

SUPPORTED_EXTENSIONS = {".pdf", ".pptx"}


def ingest_one(path: Path) -> None:
    filename = path.name
    print(f"  Processing {filename}...")

    if document_exists(filename):
        print(f"  SKIP  {filename} (already ingested)")
        return

    file_bytes = path.read_bytes()

    try:
        chunks = file_to_chunks(filename, file_bytes)
    except ValueError as e:
        print(f"  SKIP  {filename} ({e})")
        return

    if not chunks:
        print(f"  WARN  {filename}: no extractable text found (possibly scanned/image-based)")
        return

    document_id = None
    try:
        texts = [c["content"] for c in chunks]
        vectors = embed_texts(texts)

        document_id = insert_document(filename)
        insert_chunks(document_id, chunks, vectors)

        print(f"  OK    {filename}: {len(chunks)} chunks ingested (document_id={document_id})")
    except Exception as e:
        print(f"  FAIL  {filename}: {e}")
        if document_id:
            # Clean up the orphaned document row so this file gets retried
            # (not silently skipped as "already ingested") next run.
            delete_document(document_id)
            print(f"        (cleaned up partial document row - safe to retry)")


def main():
    if len(sys.argv) < 2:
        print("Usage: python ingest_folder.py /path/to/folder")
        return

    folder = Path(sys.argv[1])
    if not folder.is_dir():
        print(f"Not a folder: {folder}")
        return

    files = sorted(
        p for p in folder.iterdir()
        if p.suffix.lower() in SUPPORTED_EXTENSIONS
    )

    if not files:
        print(f"No .pdf or .pptx files found in {folder}")
        return

    print(f"Found {len(files)} file(s) to process in {folder}\n")

    for path in files:
        ingest_one(path)

    print("\nDone. Run test_retrieval.py or the frontend to query across all ingested documents.")


if __name__ == "__main__":
    main()