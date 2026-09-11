"""Best-effort redaction for user-safe errors and operational logs."""

from collections.abc import Mapping, Sequence
from pathlib import Path
import re
from typing import Any

from pydantic import SecretStr

REDACTED = "[REDACTED]"
_SENSITIVE_KEY = re.compile(
    r"(?:api[_-]?key|authorization|bearer|credential|password|secret|token)",
    re.IGNORECASE,
)
_BEARER_VALUE = re.compile(r"\bBearer\s+[A-Za-z0-9._~+/=-]+", re.IGNORECASE)
_KEY_VALUE = re.compile(
    r"(?i)(api[_-]?key|password|secret|token)\s*[=:]\s*[^\s,;]+"
)


def redact_text(value: str) -> str:
    """Remove common credential patterns without logging the original value."""

    value = _BEARER_VALUE.sub(f"Bearer {REDACTED}", value)
    return _KEY_VALUE.sub(lambda match: f"{match.group(1)}={REDACTED}", value)


def redact_value(value: Any) -> Any:
    """Return a JSON-compatible, recursively redacted value."""

    if isinstance(value, SecretStr):
        return REDACTED
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, Mapping):
        return {
            str(key): REDACTED if _SENSITIVE_KEY.search(str(key)) else redact_value(item)
            for key, item in value.items()
        }
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        return [redact_value(item) for item in value]
    if isinstance(value, str):
        return redact_text(value)
    if value is None or isinstance(value, (bool, int, float)):
        return value
    return redact_text(str(value))
