"""Pre-emission redaction and value minimization (Book II / Bloc II.6).

Redaction law (PLAN §6): redaction happens HERE, inside event construction,
before any sink sees a value. No sink, dashboard or log shipper is trusted to
hide fields downstream.

Three mechanisms, all deterministic:

1. **Secret scrubbing** — bearer tokens, `key=`/`token=`/`secret=`/
   `password=` pairs, `sk-` style keys and long opaque runs (>= 40 chars of
   base64url alphabet — which covers II.3 `token_urlsafe(32)` session tokens
   and SHA-256 hex digests) are replaced with a `[redacted]` marker.
2. **Bounded scalar attributes** — event attributes accept only scalars
   (str/int/float/bool/None); nested containers are refused at construction,
   so free-form dumps can never reach a sink.
3. **Content truncation** — any surviving string value is truncated to a
   bounded length with an explicit marker, so a protected corpus body or raw
   provider payload passed by mistake never reaches a sink in full.

This module is pure and imports no transport, provider or persistence code.
"""

from __future__ import annotations

import re
from typing import Any, Mapping

# Bounds (Ch II.6.2: bounded event payloads).
MAX_ATTRIBUTE_VALUE_LENGTH = 256
MAX_ATTRIBUTES = 16
MAX_KEY_LENGTH = 64

REDACTED = "[redacted]"
TRUNCATED = "[truncated]"

# Secret-shaped patterns. Order matters: specific patterns first.
_SECRET_PATTERNS: tuple[re.Pattern[str], ...] = (
    # Authorization headers / bearer tokens.
    re.compile(r"(?i)\bbearer\s+[A-Za-z0-9\-._~+/]+=*"),
    # key=..., token=..., secret=..., password=... assignments (any quoting).
    re.compile(
        r"(?i)\b(api[_-]?key|token|secret|password|authorization|credential)"
        r"\s*[=:]\s*\"?[A-Za-z0-9\-._~+/]{8,}\"?"
    ),
    # sk- style provider keys.
    re.compile(r"\bsk-[A-Za-z0-9\-_]{8,}"),
    # Long opaque runs: session tokens (token_urlsafe(32) = 43 chars) and
    # SHA-256 hex digests (64 chars) both exceed 40.
    re.compile(r"(?<![A-Za-z0-9\-_~+/])[A-Za-z0-9\-_~+/]{40,}(?![A-Za-z0-9\-_~+/])"),
)


def scrub_text(value: str) -> str:
    """Replace secret-shaped substrings with the redaction marker."""

    result = value
    for pattern in _SECRET_PATTERNS:
        result = pattern.sub(REDACTED, result)
    return result


def bounded_string(value: str, *, limit: int = MAX_ATTRIBUTE_VALUE_LENGTH) -> str:
    """Scrub then hard-bound a string value (pre-emission minimization)."""

    scrubbed = scrub_text(value)
    if len(scrubbed) <= limit:
        return scrubbed
    return scrubbed[:limit] + TRUNCATED


def safe_scalar(value: Any, *, limit: int = MAX_ATTRIBUTE_VALUE_LENGTH) -> Any:
    """Validate one attribute value: scalar in, bounded scalar out.

    Non-scalar values (dicts, lists, objects) are refused with ValueError —
    a free-form dump must fail at construction, never reach a sink.
    """

    if value is None or isinstance(value, (bool, int, float)):
        return value
    if isinstance(value, str):
        return bounded_string(value, limit=limit)
    raise ValueError(
        f"attribute value must be a scalar, got {type(value).__name__}"
    )


def safe_attributes(
    attributes: Mapping[str, Any] | None,
    *,
    max_attributes: int = MAX_ATTRIBUTES,
    limit: int = MAX_ATTRIBUTE_VALUE_LENGTH,
) -> dict[str, Any]:
    """Redact and bound a whole attribute mapping (deterministic order)."""

    if not attributes:
        return {}
    if len(attributes) > max_attributes:
        raise ValueError(
            f"at most {max_attributes} attributes are permitted, "
            f"got {len(attributes)}"
        )
    result: dict[str, Any] = {}
    for key in sorted(attributes):
        if not isinstance(key, str) or not key or len(key) > MAX_KEY_LENGTH:
            raise ValueError("attribute keys must be short non-empty strings")
        result[key] = safe_scalar(attributes[key], limit=limit)
    return result
