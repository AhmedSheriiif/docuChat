"""
Generation step: given a question and the chunks we retrieved for it, ask
Groq to write a real answer - grounded ONLY in those chunks, with page
citations, and instructed to say so if the answer isn't actually in there.

That last instruction matters a lot for a client like Dana: an LLM's default
behavior is to be "helpful" by filling gaps with plausible-sounding made-up
content (hallucination). The system prompt below explicitly forbids that,
because a confident wrong answer is worse than no answer for a business
archive tool.
"""
import os
from pathlib import Path
from typing import List

from dotenv import load_dotenv
from groq import Groq

load_dotenv(Path(__file__).parent.parent / ".env")

GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")
GROQ_MODEL = os.environ.get("GROQ_MODEL", "llama-3.3-70b-versatile")

_client: Groq | None = None


def get_client() -> Groq:
    global _client
    if _client is None:
        if not GROQ_API_KEY:
            raise RuntimeError("GROQ_API_KEY missing from .env")
        _client = Groq(api_key=GROQ_API_KEY)
    return _client


SYSTEM_PROMPT = """You are a document Q&A assistant. You answer questions using ONLY the
excerpts provided below - never your general knowledge, never assumptions.

Rules:
1. Base your answer strictly on the provided excerpts.
2. Every claim you make must be traceable to one of the excerpts. Mention the
   page number(s) your answer relies on, like "(page 7)".
3. If the excerpts don't contain enough information to answer the question,
   say plainly: "I don't have enough information in the provided documents to
   answer that." Do NOT guess or fill gaps with outside knowledge.
4. Be concise. Answer in a few sentences unless the question calls for more.
"""


def build_context(chunks: List[dict]) -> str:
    """Format retrieved chunks into labeled excerpts for the prompt."""
    parts = []
    for i, chunk in enumerate(chunks, start=1):
        parts.append(f"[Excerpt {i} - page {chunk['page']}]\n{chunk['content']}")
    return "\n\n".join(parts)


def generate_answer(question: str, chunks: List[dict]) -> str:
    """
    chunks: the list of dicts returned by db.search_chunks() - each has
    'content', 'page', 'similarity'.
    """
    if not chunks:
        return "I don't have enough information in the provided documents to answer that."

    context = build_context(chunks)
    user_message = f"""Excerpts from the document archive:

{context}

Question: {question}

Answer using only the excerpts above, citing page numbers."""

    client = get_client()
    response = client.chat.completions.create(
        model=GROQ_MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_message},
        ],
        temperature=0.2,  # low temperature: favor grounded, consistent answers over creative ones
        max_tokens=500,
    )
    return response.choices[0].message.content