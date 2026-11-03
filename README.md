# DocuChat

A document Q&A (RAG) application: upload a folder of documents (PDF/PPTX), ask questions in natural language, and get answers grounded strictly in the source material, with page-level citations.

## Why

Built for a use case where confidently-wrong answers are worse than no answer — the generation step is explicitly instructed to cite only what's actually in the retrieved chunks and say so when it isn't. Embeddings are also computed locally (no text leaves the machine during that step), which matters for confidentiality-sensitive documents.

## Architecture

```
documents (PDF/PPTX)
      │  chunking.py — splits into page-aware chunks
      ▼
embeddings.py — local sentence-transformers model (all-MiniLM-L6-v2), no external API call
      │
      ▼
db.py — stores chunks + vectors in Supabase (pgvector)
      │  (at query time: embed the question, vector-search for nearest chunks)
      ▼
generation.py — Groq LLM answers strictly from retrieved chunks, with page citations
      │
      ▼
main.py — FastAPI endpoint (/ask) wrapping the pipeline above
```

The `frontend/` is a Next.js app that calls the backend API.

## Running it

**Backend:**
```bash
cd backend
pip install -r requirements.txt
# set SUPABASE_URL, SUPABASE_SERVICE_KEY, GROQ_API_KEY in backend/.env
uvicorn app.main:app --reload
```
Visit `http://127.0.0.1:8000/docs` for the interactive API.

**Ingest documents:**
```bash
python backend/ingest_folder.py <path-to-folder>
```

**Frontend:**
```bash
cd frontend
npm install
npm run dev
```

## Tests

```bash
cd backend
pytest
```
Covers chunking, embeddings, retrieval, and answer generation.

## Stack

Python (FastAPI, sentence-transformers, Groq), Supabase (pgvector), Next.js frontend.
