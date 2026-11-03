"""
The web API. Step 1: a single endpoint, /ask, that wraps the exact pipeline
we already proved works in test_answer.py - nothing new happens here logically,
we're just putting an HTTP door in front of it.

Run from the backend/ folder:
    uvicorn app.main:app --reload

Then open http://127.0.0.1:8000/docs in a browser - FastAPI auto-generates
an interactive test page from the code below, no separate test script needed.
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from app.embeddings import embed_query
from app.db import search_chunks
from app.generation import generate_answer

app = FastAPI(title="DocuChat API")

# Allows a browser-based frontend (running on a different port, e.g. 3000)
# to call this API. Without this, browsers block the request by default.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class AskRequest(BaseModel):
    question: str


class Source(BaseModel):
    page: int
    similarity: float
    excerpt: str


class AskResponse(BaseModel):
    answer: str
    sources: list[Source]


@app.get("/")
def health_check():
    """Quick way to confirm the server is up at all."""
    return {"status": "ok", "service": "DocuChat API"}


@app.post("/ask", response_model=AskResponse)
def ask(request: AskRequest):
    if not request.question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty.")

    query_vector = embed_query(request.question)
    chunks = search_chunks(query_vector, top_k=5)
    answer = generate_answer(request.question, chunks)

    sources = [
        Source(
            page=c["page"],
            similarity=round(c["similarity"], 3),
            excerpt=c["content"][:200] + ("..." if len(c["content"]) > 200 else ""),
        )
        for c in chunks
    ]

    return AskResponse(answer=answer, sources=sources)