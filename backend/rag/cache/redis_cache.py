"""Response cache keyed by grade + subject + normalized query."""

from __future__ import annotations

import hashlib
import json
from typing import Any

from rag.config import get_rag_config
from rag.schemas import RagAnswer

_memory_cache: dict[str, tuple[RagAnswer, float]] = {}


def _normalize_query(query: str) -> str:
    return query.lower().strip()


def _cache_key(query: str, *, grade: int, subject: str) -> str:
    normalized = _normalize_query(query)
    digest = hashlib.sha256(f"{grade}:{subject}:{normalized}".encode("utf-8")).hexdigest()
    return f"rag:answer:{digest}"


def _redis_client():
    cfg = get_rag_config()
    if not cfg.redis_url:
        return None
    try:
        import redis

        return redis.from_url(cfg.redis_url, decode_responses=True)
    except Exception:
        return None


def get_cached_answer(query: str, *, grade: int, subject: str) -> RagAnswer | None:
    key = _cache_key(query, grade=grade, subject=subject)
    client = _redis_client()
    if client is not None:
        try:
            data = client.get(key)
            if data:
                return RagAnswer.model_validate(json.loads(data))
        except Exception:
            pass

    cached = _memory_cache.get(key)
    if cached:
        answer, _ts = cached
        return answer.model_copy(update={"cached": True})
    return None


def set_cached_answer(query: str, answer: RagAnswer, *, grade: int, subject: str) -> None:
    key = _cache_key(query, grade=grade, subject=subject)
    payload = answer.model_dump()
    payload["cached"] = False
    client = _redis_client()
    cfg = get_rag_config()
    if client is not None:
        try:
            client.setex(key, cfg.cache_ttl_seconds, json.dumps(payload))
            return
        except Exception:
            pass
    _memory_cache[key] = (RagAnswer.model_validate(payload), cfg.cache_ttl_seconds)


def cache_stats() -> dict[str, Any]:
    client = _redis_client()
    if client is not None:
        try:
            keys = client.keys("rag:answer:*")
            return {"backend": "redis", "entries": len(keys)}
        except Exception:
            pass
    return {"backend": "memory", "entries": len(_memory_cache)}
