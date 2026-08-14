"""Gemini embeddings via LiteLLM with batching."""

from __future__ import annotations

import os
from typing import Sequence

import litellm

from rag.config import get_rag_config

BATCH_SIZE = 64


def _ensure_api_key() -> None:
    cfg = get_rag_config()
    if not cfg.gemini_api_key:
        raise RuntimeError("GEMINI_API_KEY is not configured")
    os.environ.setdefault("GEMINI_API_KEY", cfg.gemini_api_key)


def embed_texts(texts: Sequence[str]) -> list[list[float]]:
    if not texts:
        return []
    _ensure_api_key()
    cfg = get_rag_config()
    vectors: list[list[float]] = []
    for start in range(0, len(texts), BATCH_SIZE):
        batch = list(texts[start : start + BATCH_SIZE])
        response = litellm.embedding(model=cfg.embedding_model, input=batch)
        batch_vectors = [item["embedding"] for item in response.data]
        vectors.extend(batch_vectors)
    return vectors


def embed_query(text: str) -> list[float]:
    return embed_texts([text])[0]
