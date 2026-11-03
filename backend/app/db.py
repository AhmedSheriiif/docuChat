"""
Thin wrapper around the Supabase client. Every place in the app that needs to
read or write the database goes through these three functions - keeps DB
logic in one spot.
"""
import os
from pathlib import Path
from typing import List

from dotenv import load_dotenv
from supabase import create_client, Client

load_dotenv(Path(__file__).parent.parent / ".env")

SUPABASE_URL = os.environ.get("SUPABASE_URL", "")
SUPABASE_SERVICE_KEY = os.environ.get("SUPABASE_SERVICE_KEY", "")

_client: Client | None = None


def get_client() -> Client:
    global _client
    if _client is None:
        if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
            raise RuntimeError("SUPABASE_URL / SUPABASE_SERVICE_KEY missing from .env")
        _client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)
    return _client


def document_exists(filename: str) -> bool:
    """Check if a document with this filename was already ingested."""
    client = get_client()
    result = client.table("documents").select("id").eq("filename", filename).execute()
    return len(result.data) > 0


def delete_document(document_id: str) -> None:
    """Remove a document row (and any of its chunks, via cascade delete).
    Used to clean up after a failed ingest so the file can be retried."""
    client = get_client()
    client.table("documents").delete().eq("id", document_id).execute()


def insert_document(filename: str) -> str:
    """Create one row in `documents`, return its new id (a uuid string)."""
    client = get_client()
    result = client.table("documents").insert({"filename": filename}).execute()
    return result.data[0]["id"]


def insert_chunks(document_id: str, chunks: List[dict], embeddings: List[List[float]]) -> int:
    """
    Insert chunk rows in bulk.
    `chunks`: list of {"content": str, "page": int}
    `embeddings`: matching list of 384-number vectors, same order, same length.
    Returns how many rows were inserted.
    """
    assert len(chunks) == len(embeddings), "chunks and embeddings must be the same length and order"

    rows = [
        {
            "document_id": document_id,
            "content": chunk["content"],
            "page": chunk["page"],
            "embedding": embedding,
        }
        for chunk, embedding in zip(chunks, embeddings)
    ]

    client = get_client()
    batch_size = 100  # Supabase/PostgREST has a request size limit - batch large docs
    for i in range(0, len(rows), batch_size):
        client.table("chunks").insert(rows[i : i + batch_size]).execute()

    return len(rows)


def search_chunks(query_embedding: List[float], top_k: int = 5) -> List[dict]:
    """Call the match_chunks() Postgres function - returns the top_k closest chunks."""
    client = get_client()
    result = client.rpc(
        "match_chunks",
        {"query_embedding": query_embedding, "match_count": top_k},
    ).execute()
    return result.data