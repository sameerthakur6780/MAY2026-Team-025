"""LiteLLM router with Gemini → Groq → OpenRouter fallback."""

from __future__ import annotations

import json
import os
from functools import lru_cache

import litellm
from litellm import Router

from rag.config import get_rag_config


def _set_env_keys() -> None:
    cfg = get_rag_config()
    if cfg.gemini_api_key:
        os.environ.setdefault("GEMINI_API_KEY", cfg.gemini_api_key)
    if cfg.groq_api_key:
        os.environ.setdefault("GROQ_API_KEY", cfg.groq_api_key)
    if cfg.openrouter_api_key:
        os.environ.setdefault("OPENROUTER_API_KEY", cfg.openrouter_api_key)


@lru_cache(maxsize=1)
def get_llm_router() -> Router:
    _set_env_keys()
    cfg = get_rag_config()
    model_list = [
        {
            "model_name": "primary",
            "litellm_params": {"model": cfg.primary_model, "api_key": cfg.gemini_api_key or None},
        },
        {
            "model_name": "secondary",
            "litellm_params": {"model": cfg.secondary_model, "api_key": cfg.groq_api_key or None},
        },
        {
            "model_name": "tertiary",
            "litellm_params": {"model": cfg.tertiary_model, "api_key": cfg.openrouter_api_key or None},
        },
    ]
    router_kwargs = {
        "model_list": model_list,
        "routing_strategy": "usage-based-routing-v2",
        "fallbacks": [{"primary": ["secondary", "tertiary"]}],
        "num_retries": 2,
        "cooldown_time": 30,
    }
    if cfg.redis_url:
        router_kwargs["redis_host"] = cfg.redis_url
    return Router(**router_kwargs)


def completion_with_fallback(messages: list[dict], *, temperature: float = 0.2) -> tuple[str, str]:
    router = get_llm_router()
    response = router.completion(model="primary", messages=messages, temperature=temperature)
    content = response.choices[0].message.content or ""
    model_used = getattr(response, "model", "primary")
    return content, model_used


def completion_json_with_fallback(messages: list[dict], *, temperature: float = 0.2) -> tuple[dict, str]:
    raw, model_used = completion_with_fallback(messages, temperature=temperature)
    cleaned = raw.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.split("\n", 1)[-1]
        if cleaned.endswith("```"):
            cleaned = cleaned.rsplit("```", 1)[0]
    return json.loads(cleaned), model_used
