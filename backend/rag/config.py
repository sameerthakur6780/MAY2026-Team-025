from __future__ import annotations

import os
from dataclasses import dataclass, field
from functools import lru_cache

from dotenv import load_dotenv

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
load_dotenv(os.path.join(BASE_DIR, ".env"))


def _env(name: str, default: str = "") -> str:
    return os.environ.get(name, default)


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


def _bool_env(name: str, default: bool = False) -> bool:
    raw = os.environ.get(name)
    if raw is None or not raw.strip():
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


@dataclass(frozen=True)
class RagConfig:
    pinecone_api_key: str = field(default_factory=lambda: _env("PINECONE_API_KEY"))
    pinecone_dense_index: str = field(
        default_factory=lambda: _env("PINECONE_DENSE_INDEX", "smartbatch-rag-dense")
    )
    pinecone_sparse_index: str = field(
        default_factory=lambda: _env("PINECONE_SPARSE_INDEX", "smartbatch-rag-sparse")
    )
    pinecone_cloud: str = field(default_factory=lambda: _env("PINECONE_CLOUD", "aws"))
    pinecone_region: str = field(default_factory=lambda: _env("PINECONE_REGION", "us-east-1"))
    pinecone_sparse_model: str = field(
        default_factory=lambda: _env("PINECONE_SPARSE_MODEL", "pinecone-sparse-english-v0")
    )
    gemini_api_key: str = field(default_factory=lambda: _env("GEMINI_API_KEY"))
    groq_api_key: str = field(default_factory=lambda: _env("GROQ_API_KEY"))
    openrouter_api_key: str = field(default_factory=lambda: _env("OPENROUTER_API_KEY"))
    redis_url: str = field(default_factory=lambda: _env("REDIS_URL"))
    upstash_redis_rest_url: str = field(default_factory=lambda: _env("UPSTASH_REDIS_REST_URL"))
    upstash_redis_rest_token: str = field(default_factory=lambda: _env("UPSTASH_REDIS_REST_TOKEN"))
    embedding_model: str = field(default_factory=lambda: _env("RAG_EMBEDDING_MODEL", "gemini/gemini-embedding-001"))
    embedding_dimensions: int = field(default_factory=lambda: _int_env("RAG_EMBEDDING_DIMENSIONS", 768))
    chunk_size_tokens: int = field(default_factory=lambda: _int_env("RAG_CHUNK_SIZE_TOKENS", 400))
    chunk_overlap_ratio: float = field(default_factory=lambda: _float_env("RAG_CHUNK_OVERLAP_RATIO", 0.12))
    retrieval_top_k: int = field(default_factory=lambda: _int_env("RAG_RETRIEVAL_TOP_K", 8))
    hybrid_rrf_k: int = field(default_factory=lambda: _int_env("RAG_HYBRID_RRF_K", 60))
    cache_ttl_seconds: int = field(default_factory=lambda: _int_env("RAG_CACHE_TTL_SECONDS", 3600))
    rewrite_enabled: bool = field(default_factory=lambda: _bool_env("RAG_REWRITE_ENABLED", False))
    generation_enabled: bool = field(default_factory=lambda: _bool_env("RAG_GENERATION_ENABLED", False))
    primary_model: str = field(
        default_factory=lambda: _env("RAG_PRIMARY_MODEL", "openrouter/liquid/lfm-2.5-2.6b:free")
    )
    secondary_model: str = field(default_factory=lambda: _env("RAG_SECONDARY_MODEL"))
    tertiary_model: str = field(default_factory=lambda: _env("RAG_TERTIARY_MODEL"))
    max_output_tokens: int = field(default_factory=lambda: _int_env("RAG_MAX_OUTPUT_TOKENS", 1024))
    rewrite_max_output_tokens: int = field(
        default_factory=lambda: _int_env("RAG_REWRITE_MAX_OUTPUT_TOKENS", 512)
    )
    llm_timeout_seconds: int = field(default_factory=lambda: _int_env("RAG_LLM_TIMEOUT_SECONDS", 30))


@lru_cache(maxsize=1)
def get_rag_config() -> RagConfig:
    return RagConfig()
