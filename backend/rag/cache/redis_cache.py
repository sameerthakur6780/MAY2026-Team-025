"""Response cache keyed by grade + subject + chapter + normalized query."""

from __future__ import annotations

import hashlib
import json
import logging
from typing import Any
from urllib import request

from rag.config import get_rag_config
from rag.schemas import RagAnswer

logger = logging.getLogger(__name__)

_memory_cache: dict[str, tuple[RagAnswer, float]] = {}


def _normalize_query(query: str) -> str:
    return query.lower().strip()


def _cache_key(query: str, *, grade: int, subject: str, chapter: str | None = None) -> str:
    normalized = _normalize_query(query)
    chapter_key = (chapter or "").strip().lower()
    digest = hashlib.sha256(
        f"{grade}:{subject}:{chapter_key}:{normalized}".encode("utf-8")
    ).hexdigest()
    return f"rag:answer:{digest}"


def _redis_client():
    cfg = get_rag_config()
    if not cfg.redis_url:
        return None
    try:
        import redis

        return redis.from_url(cfg.redis_url, decode_responses=True)
    except Exception as exc:
        logger.debug("Redis client unavailable: %s", exc)
        return None


def _upstash_command(*command: str) -> Any:
    cfg = get_rag_config()
    if not cfg.upstash_redis_rest_url or not cfg.upstash_redis_rest_token:
        return None

    req = request.Request(
        cfg.upstash_redis_rest_url.rstrip("/"),
        data=json.dumps(command).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {cfg.upstash_redis_rest_token}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    with request.urlopen(req, timeout=5) as response:
        payload = json.loads(response.read().decode("utf-8"))
        return payload.get("result")


def get_cached_answer(
    query: str,
    *,
    grade: int,
    subject: str,
    chapter: str | None = None,
) -> RagAnswer | None:
    key = _cache_key(query, grade=grade, subject=subject, chapter=chapter)
    client = _redis_client()
    if client is not None:
        try:
            data = client.get(key)
            if data:
                return RagAnswer.model_validate(json.loads(data))
        except Exception as exc:
            logger.debug("Redis cache read failed: %s", exc)
    try:
        data = _upstash_command("GET", key)
        if data:
            return RagAnswer.model_validate(json.loads(data))
    except Exception as exc:
        logger.debug("Upstash cache read failed: %s", exc)

    cached = _memory_cache.get(key)
    if cached:
        answer, _ts = cached
        return answer.model_copy(update={"cached": True})
    return None


def set_cached_answer(
    query: str,
    answer: RagAnswer,
    *,
    grade: int,
    subject: str,
    chapter: str | None = None,
) -> None:
    key = _cache_key(query, grade=grade, subject=subject, chapter=chapter)
    payload = answer.model_dump()
    payload["cached"] = False
    client = _redis_client()
    cfg = get_rag_config()
    if client is not None:
        try:
            client.setex(key, cfg.cache_ttl_seconds, json.dumps(payload))
            return
        except Exception as exc:
            logger.debug("Redis cache write failed: %s", exc)
    try:
        result = _upstash_command("SETEX", key, str(cfg.cache_ttl_seconds), json.dumps(payload))
        if result is not None:
            return
    except Exception as exc:
        logger.debug("Upstash cache write failed: %s", exc)
    _memory_cache[key] = (RagAnswer.model_validate(payload), cfg.cache_ttl_seconds)


def cache_stats() -> dict[str, Any]:
    client = _redis_client()
    if client is not None:
        try:
            keys = client.keys("rag:answer:*")
            return {"backend": "redis", "entries": len(keys)}
        except Exception as exc:
            logger.debug("Redis cache stats failed: %s", exc)
    try:
        keys = _upstash_command("KEYS", "rag:answer:*")
        if keys is not None:
            return {"backend": "upstash-rest", "entries": len(keys)}
    except Exception as exc:
        logger.debug("Upstash cache stats failed: %s", exc)
    return {"backend": "memory", "entries": len(_memory_cache)}
