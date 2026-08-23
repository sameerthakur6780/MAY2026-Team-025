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


def _salvage_truncated_json(text: str) -> str | None:
    """Close off unterminated strings/objects/arrays in output that was cut
    off mid-value because the model hit its output token limit. Returns a
    best-effort repaired string, or None if there's nothing to close."""
    stack: list[str] = []
    in_string = False
    escape = False
    for ch in text:
        if in_string:
            if escape:
                escape = False
            elif ch == "\\":
                escape = True
            elif ch == '"':
                in_string = False
            continue
        if ch == '"':
            in_string = True
        elif ch in "{[":
            stack.append(ch)
        elif ch in "}]" and stack:
            stack.pop()

    if not stack and not in_string:
        return None

    closers = {"{": "}", "[": "]"}
    repaired = text + ('"' if in_string else "")
    # A dangling trailing comma (output cut off right after one) would make
    # the repaired JSON invalid even once brackets are closed.
    repaired = repaired.rstrip()
    if repaired.endswith(","):
        repaired = repaired[:-1]
    repaired += "".join(closers[opener] for opener in reversed(stack))
    return repaired


def extract_json_object(raw: str, *, salvage_truncated: bool = False) -> dict | None:
    """Parse a JSON object from raw LLM output, tolerating fences and leading
    prose. With salvage_truncated=True, also attempts to close off strings/
    objects/arrays left open by output that was cut off at the token limit --
    opt-in since callers may intentionally treat truncation as unrecoverable
    (e.g. to trigger an extractive fallback)."""
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

    if salvage_truncated:
        start = stripped.find("{")
        if start != -1:
            salvaged = _salvage_truncated_json(stripped[start:])
            if salvaged is not None:
                parsed = _try_parse_json(salvaged)
                if parsed is not None:
                    return parsed
    return None
