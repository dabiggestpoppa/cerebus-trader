"""Canonical serialisation: sorted keys, exact decimals, no floats, no clock."""

from __future__ import annotations

import hashlib
import json
from dataclasses import fields, is_dataclass
from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from typing import Any, Mapping

from app.forge.intelligence_api.errors import RefusalError

CONTENT_TYPE = "application/json; charset=utf-8"
MAX_RESPONSE_BYTES = 2_000_000


def _decimal_text(value: Decimal) -> str:
    if not value.is_finite():
        raise RefusalError("MALFORMED_REQUEST", detail="nonfinite_decimal")
    return format(value, "f")


def to_primitive(value: Any) -> Any:
    """Convert a value to canonical JSON primitives, refusing floats."""

    if value is None or isinstance(value, (bool, int, str)):
        return value
    if isinstance(value, float):
        raise RefusalError("MALFORMED_REQUEST", detail="float_not_permitted")
    if isinstance(value, Decimal):
        return _decimal_text(value)
    if isinstance(value, Enum):
        return to_primitive(value.value)
    if isinstance(value, datetime):
        return value.isoformat().replace("+00:00", "Z")
    if isinstance(value, date):
        return value.isoformat()
    if isinstance(value, Mapping):
        out: dict[str, Any] = {}
        for key, item in value.items():
            if not isinstance(key, str):
                raise RefusalError("MALFORMED_REQUEST", detail="nonstring_key")
            out[key] = to_primitive(item)
        return out
    if isinstance(value, (list, tuple)):
        return [to_primitive(item) for item in value]
    if isinstance(value, (set, frozenset)):
        return [to_primitive(item) for item in sorted(value, key=repr)]
    if is_dataclass(value) and not isinstance(value, type):
        return {field.name: to_primitive(getattr(value, field.name)) for field in fields(value)}
    raise RefusalError("MALFORMED_REQUEST", detail="unsupported_value")


def canonical_json(value: Any) -> str:
    return json.dumps(
        to_primitive(value),
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    )


def content_hash(value: Any) -> str:
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


def schema_hash(descriptor: Mapping[str, Any] | tuple[Any, ...] | list[Any]) -> str:
    return content_hash(descriptor)


def bounded_json(value: Any) -> str:
    """Serialise canonically, refusing payloads above the bounded size."""

    text = canonical_json(value)
    if len(text.encode("utf-8")) > MAX_RESPONSE_BYTES:
        raise RefusalError("MALFORMED_REQUEST", detail="response_too_large")
    return text


__all__ = [
    "CONTENT_TYPE",
    "MAX_RESPONSE_BYTES",
    "to_primitive",
    "canonical_json",
    "content_hash",
    "schema_hash",
    "bounded_json",
]
