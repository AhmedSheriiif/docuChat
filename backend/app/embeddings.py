"""
Local embedding model.

This runs entirely on your own machine, downloading the model weights once
(~90MB) the first time you use it. No text ever leaves your computer for this
step — which is exactly the confidentiality promise we made Dana.

all-MiniLM-L6-v2 turns any text into a list of 384 numbers ("a spot on the
meaning map"). Texts with similar meaning end up with similar numbers.
"""
from functools import lru_cache
from typing import List

from sentence_transformers import SentenceTransformer

MODEL_NAME = "all-MiniLM-L6-v2"
EMBEDDING_DIM = 384  # must match the vector(384) column in Supabase


@lru_cache(maxsize=1)
def _model() -> SentenceTransformer:
    # Cached so the ~90MB model only loads into memory once per process,
    # not on every call.
    return SentenceTransformer(MODEL_NAME)


def embed_texts(texts: List[str]) -> List[List[float]]:
    """Embed a batch of chunks (used when ingesting a document)."""
    vectors = _model().encode(texts, normalize_embeddings=True, show_progress_bar=False)
    return [v.tolist() for v in vectors]


def embed_query(text: str) -> List[float]:
    """Embed a single question (used at search time)."""
    return embed_texts([text])[0]