"""LiteLLM router with Gemini → Groq → OpenRouter fallback."""

from __future__ import annotations

import os
from functools import lru_cache

import litellm
from litellm import Router

from rag.config import get_rag_config
from rag.generation.json_utils import extract_json_object


def _set_env_keys() -> None:
    cfg = get_rag_config()
    if cfg.gemini_api_key:
        os.environ.setdefault("GEMINI_API_KEY", cfg.gemini_api_key)
    if cfg.groq_api_key:
        os.environ.setdefault("GROQ_API_KEY", cfg.groq_api_key)
    if cfg.openrouter_api_key:
        os.environ.setdefault("OPENROUTER_API_KEY", cfg.openrouter_api_key)


def _api_key_for_model(model: str) -> str | None:
    cfg = get_rag_config()
    if model.startswith("gemini/"):
        return cfg.gemini_api_key or None
    if model.startswith("groq/"):
        return cfg.groq_api_key or None
    if model.startswith("openrouter/"):
        return cfg.openrouter_api_key or None
    return None


@lru_cache(maxsize=1)
def get_llm_router() -> Router:
    _set_env_keys()
    cfg = get_rag_config()
    model_list = []
    primary_params = {"model": cfg.primary_model, "api_key": _api_key_for_model(cfg.primary_model)}
    model_list.append({"model_name": "primary", "litellm_params": primary_params})

    if cfg.secondary_model:
        model_list.append(
            {
                "model_name": "secondary",
                "litellm_params": {"model": cfg.secondary_model, "api_key": _api_key_for_model(cfg.secondary_model)},
            }
        )
    if cfg.tertiary_model:
        model_list.append(
            {
                "model_name": "tertiary",
                "litellm_params": {"model": cfg.tertiary_model, "api_key": _api_key_for_model(cfg.tertiary_model)},
            }
        )

    fallback_targets = [model["model_name"] for model in model_list if model["model_name"] != "primary"]
    router_kwargs = {
        "model_list": model_list,
        "routing_strategy": "usage-based-routing-v2",
        "num_retries": 1,
        "cooldown_time": 30,
    }
    if fallback_targets:
        router_kwargs["fallbacks"] = [{"primary": fallback_targets}]
    if cfg.redis_url:
        router_kwargs["redis_host"] = cfg.redis_url
    return Router(**router_kwargs)


def completion_with_fallback(
    messages: list[dict],
    *,
    temperature: float = 0.2,
    max_tokens: int | None = None,
) -> tuple[str, str]:
    cfg = get_rag_config()
    router = get_llm_router()
    token_limit = max_tokens if max_tokens is not None else cfg.max_output_tokens
    response = router.completion(
        model="primary",
        messages=messages,
        temperature=temperature,
        max_tokens=token_limit,
        timeout=cfg.llm_timeout_seconds,
    )
    content = response.choices[0].message.content or ""
    model_used = getattr(response, "model", "primary")
    return content, model_used


def completion_json_with_fallback(
    messages: list[dict],
    *,
    temperature: float = 0.2,
    max_tokens: int | None = None,
) -> tuple[dict, str]:
    cfg = get_rag_config()
    token_limit = max_tokens if max_tokens is not None else cfg.rewrite_max_output_tokens
    raw, model_used = completion_with_fallback(messages, temperature=temperature, max_tokens=token_limit)
    payload = extract_json_object(raw)
    if payload is None:
        raise ValueError("LLM response did not contain valid JSON")
    return payload, model_used
