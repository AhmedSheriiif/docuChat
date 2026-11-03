"""
Step 3 test: prove we can pull text out of a real PDF and chunk it sensibly.
No embeddings, no database yet - just: does extraction + chunking work.

Run from the backend/ folder, pointing at any real PDF you have handy
(ideally one of the actual pilot documents):
    python test_chunking.py "/path/to/some_document.pdf"
"""
import sys

from app.chunking import extract_pages, pdf_to_chunks


def main():
    if len(sys.argv) < 2:
        print("Usage: python test_chunking.py /path/to/file.pdf")
        return

    path = sys.argv[1]

    print(f"1. Reading PDF: {path}")
    with open(path, "rb") as f:
        pdf_bytes = f.read()
    print(f"   OK. File is {len(pdf_bytes) / 1024:.1f} KB.")

    print("\n2. Extracting text per page...")
    pages = extract_pages(pdf_bytes)
    print(f"   OK. Found {len(pages)} page(s).")
    non_empty = [p for p in pages if p.strip()]
    if not non_empty:
        print("   WARNING: no extractable text found on any page.")
        print("   -> This PDF might be a scanned image (no selectable text).")
        print("      Those need an OCR step we haven't built yet - flag it, don't ingest it as-is.")
        return
    print(f"   {len(non_empty)} of {len(pages)} page(s) have extractable text.")

    print("\n3. Chunking the document...")
    chunks = pdf_to_chunks(pdf_bytes)
    print(f"   OK. Produced {len(chunks)} chunk(s).")

    lengths = [len(c["content"]) for c in chunks]
    print(f"   Avg chunk length: {sum(lengths) / len(lengths):.0f} chars")
    print(f"   Min/Max chunk length: {min(lengths)} / {max(lengths)} chars")

    print("\n4. Sample - first chunk:")
    print("   ---")
    print("   " + chunks[0]["content"][:300] + ("..." if len(chunks[0]["content"]) > 300 else ""))
    print("   ---")
    print(f"   (from page {chunks[0]['page']})")

    if len(chunks) > 1:
        print("\n5. Sample - second chunk (check the overlap with the end of chunk 1):")
        print("   ---")
        print("   " + chunks[1]["content"][:300] + ("..." if len(chunks[1]["content"]) > 300 else ""))
        print("   ---")

    print("\nALL CHECKS PASSED. Chunking works on a real document.")
    print("Ready for Step 4: writing chunks + embeddings into Supabase.")


if __name__ == "__main__":
    main()