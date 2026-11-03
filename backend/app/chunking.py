"""
Turn a document into overlapping text chunks ready for embedding.

Supports PDF and PowerPoint (.pptx). Word support can be added the same way
later if Dana's archive needs it.

The chunker is deliberately simple: fixed-size character windows with overlap.
Overlap exists so a sentence that gets cut off at the end of one chunk still
appears in full at the start of the next one - otherwise a fact that spans a
chunk boundary could get lost entirely.
"""
from io import BytesIO
from typing import List

from pypdf import PdfReader
from pptx import Presentation

CHUNK_SIZE = 900     # characters per chunk
CHUNK_OVERLAP = 150  # characters repeated between consecutive chunks


def extract_pages(pdf_bytes: bytes) -> List[str]:
    """PDF -> list of per-page text. Page 1 is index 0."""
    reader = PdfReader(BytesIO(pdf_bytes))
    return [(page.extract_text() or "").strip() for page in reader.pages]


def extract_slides(pptx_bytes: bytes) -> List[str]:
    """PowerPoint -> list of per-slide text. Slide 1 is index 0."""
    prs = Presentation(BytesIO(pptx_bytes))
    slides_text = []
    for slide in prs.slides:
        parts = [
            shape.text_frame.text
            for shape in slide.shapes
            if shape.has_text_frame and shape.text_frame.text.strip()
        ]
        slides_text.append("\n".join(parts))
    return slides_text


def chunk_text(text: str, page: int) -> List[dict]:
    """Slice one page/slide's text into overlapping windows."""
    # Some PDFs embed null bytes and other control characters as artifacts of
    # how their internal fonts/encoding work. Postgres text columns reject
    # \u0000 outright, so strip it (and other non-printable control chars)
    # before this text goes anywhere near the database.
    text = "".join(ch for ch in text if ch == "\n" or ch == "\t" or ord(ch) >= 32)
    text = " ".join(text.split())  # collapse newlines/extra whitespace
    step = max(CHUNK_SIZE - CHUNK_OVERLAP, 1)

    chunks: List[dict] = []
    start = 0
    while start < len(text):
        window = text[start : start + CHUNK_SIZE].strip()
        if window:
            chunks.append({"content": window, "page": page})
        start += step
    return chunks


def pdf_to_chunks(pdf_bytes: bytes) -> List[dict]:
    """Full path: raw PDF bytes -> list of {content, page} chunk dicts."""
    all_chunks: List[dict] = []
    for page_number, page_text in enumerate(extract_pages(pdf_bytes), start=1):
        if page_text:
            all_chunks.extend(chunk_text(page_text, page_number))
    return all_chunks


def pptx_to_chunks(pptx_bytes: bytes) -> List[dict]:
    """Full path: raw PPTX bytes -> list of {content, page} chunk dicts.
    Here 'page' actually means slide number - kept the same key so the rest
    of the app (db, generation, frontend) doesn't need to know the difference.
    """
    all_chunks: List[dict] = []
    for slide_number, slide_text in enumerate(extract_slides(pptx_bytes), start=1):
        if slide_text:
            all_chunks.extend(chunk_text(slide_text, slide_number))
    return all_chunks


def file_to_chunks(filename: str, file_bytes: bytes) -> List[dict]:
    """
    Dispatch by file extension so ingest scripts don't need their own
    if/else - just call this with any supported file and get chunks back.
    """
    ext = filename.lower().rsplit(".", 1)[-1] if "." in filename else ""
    if ext == "pdf":
        return pdf_to_chunks(file_bytes)
    elif ext == "pptx":
        return pptx_to_chunks(file_bytes)
    else:
        raise ValueError(
            f"Unsupported file type '.{ext}' for '{filename}'. "
            f"Supported: .pdf, .pptx"
        )