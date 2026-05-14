"""Payload sanitization helpers for trace logging."""

from __future__ import annotations

import re
from typing import Any


SENSITIVE_KEYWORDS = ("api_key", "token", "password", "authorization", "secret")
TOKEN_USAGE_KEYS = {"prompt_tokens", "completion_tokens", "total_tokens"}
MASK = "***"


def sanitize_payload(payload: Any) -> Any:
    """Return a sanitized copy of a trace payload."""
    return _sanitize_value(payload, key=None)


def _sanitize_value(value: Any, key: str | None) -> Any:
    if key and _is_sensitive_key(key):
        return MASK

    if isinstance(value, dict):
        return {
            item_key: _sanitize_value(item_value, key=str(item_key))
            for item_key, item_value in value.items()
        }

    if isinstance(value, list):
        return [_sanitize_value(item, key=None) for item in value]

    if isinstance(value, tuple):
        return tuple(_sanitize_value(item, key=None) for item in value)

    if isinstance(value, str):
        return _sanitize_string(value)

    return value


def _is_sensitive_key(key: str) -> bool:
    normalized = key.lower()
    if normalized in TOKEN_USAGE_KEYS:
        return False
    return any(keyword in normalized for keyword in SENSITIVE_KEYWORDS)


def _sanitize_string(value: str) -> str:
    value = re.sub(r"sk-[A-Za-z0-9_\-]{6,}", "sk-***", value)
    return re.sub(
        r"Bearer\s+[A-Za-z0-9._~+/\-=]+",
        "Bearer ***",
        value,
        flags=re.IGNORECASE,
    )
