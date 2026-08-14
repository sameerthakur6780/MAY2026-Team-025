from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache

from dotenv import load_dotenv

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
load_dotenv(os.path.join(BASE_DIR, ".env"))


def _int_env(name: str, default: int) -> int:
    raw = os.environ.get(name)
    if raw is None or not raw.strip():
        return default
    return int(raw)


def _float_env(name: str, default: float) -> float:
    raw = os.environ.get(name)
    if raw is None or not raw.strip():
        return default
    return float(raw)


@dataclass(frozen=True)
class RagConfig:
    database_url: str = os.environ.get("RAG_DATABASE_URL", "")
    gemini_api_key: str = os.environ.get("GEMINI_API_KEY", "")
    groq_api_key: str = os.environ.get("GROQ_API_KEY", "")
    openrouter_api_key: str = os.environ.get("OPENROUTER_API_KEY", "")
    redis_url: str = os.environ.get("REDIS_URL", "")
    embedding_model: str = os.environ.get("RAG_EMBEDDING_MODEL", "gemini/text-embedding-004")
    embedding_dimensions: int = _int_env("RAG_EMBEDDING_DIMENSIONS", 768)
    chunk_size_tokens: int = _int_env("RAG_CHUNK_SIZE_TOKENS", 400)
    chunk_overlap_ratio: float = _float_env("RAG_CHUNK_OVERLAP_RATIO", 0.12)
    retrieval_top_k: int = _int_env("RAG_RETRIEVAL_TOP_K", 8)
    hybrid_rrf_k: int = _int_env("RAG_HYBRID_RRF_K", 60)
    cache_ttl_seconds: int = _int_env("RAG_CACHE_TTL_SECONDS", 3600)
    primary_model: str = os.environ.get("RAG_PRIMARY_MODEL", "gemini/gemini-2.0-flash")
    secondary_model: str = os.environ.get("RAG_SECONDARY_MODEL", "groq/llama-3.3-70b-versatile")
    tertiary_model: str = os.environ.get(
        "RAG_TERTIARY_MODEL", "openrouter/meta-llama/llama-3.2-3b-instruct:free"
    )


@lru_cache(maxsize=1)
def get_rag_config() -> RagConfig:
    return RagConfig()
