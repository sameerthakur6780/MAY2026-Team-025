"""Shared helpers for extracting JSON objects from LLM responses."""

from __future__ import annotations

import json
import re


def _strip_code_fences(text: str) -> str:
    cleaned = text.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.split("\n", 1)[-1]
        if cleaned.endswith("```"):
            cleaned = cleaned.rsplit("```", 1)[0]
        return cleaned.strip()

    fence_match = re.search(r"```(?:json)?\s*\n(.*?)```", cleaned, flags=re.DOTALL | re.IGNORECASE)
    if fence_match:
        return fence_match.group(1).strip()
    return cleaned


def _try_parse_json(text: str) -> dict | None:
    try:
        payload = json.loads(text)
    except json.JSONDecodeError:
        return None
    return payload if isinstance(payload, dict) else None


def extract_json_object(raw: str) -> dict | None:
    """Parse a JSON object from raw LLM output, tolerating fences and leading prose."""
    if not raw or not raw.strip():
        return None

    stripped = _strip_code_fences(raw)
    parsed = _try_parse_json(stripped)
    if parsed is not None:
        return parsed

    for match in re.finditer(r"\{.*\}", stripped, flags=re.DOTALL):
        parsed = _try_parse_json(match.group(0))
        if parsed is not None:
            return parsed
    return None
