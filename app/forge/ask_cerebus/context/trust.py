"""Exposure and untrusted-data guards for IV.3."""

from __future__ import annotations

import hashlib
import re
from typing import Iterable

from app.forge.ask_cerebus.context.enums import ContextSectionId
from app.forge.ask_cerebus.context.versions import MAX_EXCERPT_CHARS

ALLOWED_EXPOSURES = frozenset(
    {"PUBLIC_TEACHING", "SUBSCRIBER_MODEL", "OPERATOR_ONLY", "RESEARCH_LAB"}
)
FORBIDDEN_EXPOSURES = frozenset({"INTERNAL_METHOD", "INTERNAL_CODE"})
ALLOWED_FACT_KEYS = frozenset(
    {
        "identity",
        "version",
        "status",
        "layer",
        "market_scope",
        "generation",
        "support_classification",
        "join_status",
        "identity_key",
        "result_value",
        "metric",
        "event_identity",
        "conditioning_population",
        "sample_size",
        "research_period",
        "oos_status",
        "quality",
        "no_go",
        "setup_id",
        "setup_version",
        "setup_class",
        "eligibility",
        "surface",
        "snapshot_id",
        "snapshot_hash",
        "view",
        "state",
        "levels",
        "path",
        "setup",
        "cutoff",
        "refusal",
        "intent",
        "time_scope",
        "depth",
        "actionable",
        "ambiguity",
        "general_knowledge_allowed",
    }
)
_ALLOWED_INTELLIGENCE_PATHS = frozenset(
    {"state", "levels", "path", "setup", "quality", "no_go", "version", "cutoff"}
)


def exposure_allowed(exposure: str) -> bool:
    return exposure not in FORBIDDEN_EXPOSURES


def fact_key_allowed(key: str) -> bool:
    return key in ALLOWED_FACT_KEYS


def intelligence_path_allowed(path: str) -> bool:
    return path in _ALLOWED_INTELLIGENCE_PATHS


def normalise_excerpt(text: str, *, max_chars: int = MAX_EXCERPT_CHARS) -> str:
    value = (text or "").replace("\r\n", "\n").replace("\r", "\n").strip()
    if len(value) > max_chars:
        value = value[:max_chars]
    return value


def text_digest(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def contains_forbidden_words(value: str) -> bool:
    lowered = value.lower()
    return any(
        token in lowered
        for token in ("secret", "api_key", "private_key", "password", "sk-")
    )


def safe_source_id(value: str, authorized: Iterable[str]) -> str:
    """Return an id only when it is already in the authorized set."""

    return value if value and value in set(authorized) else ""


__all__ = [
    "ALLOWED_EXPOSURES",
    "FORBIDDEN_EXPOSURES",
    "ALLOWED_FACT_KEYS",
    "exposure_allowed",
    "fact_key_allowed",
    "intelligence_path_allowed",
    "normalise_excerpt",
    "text_digest",
    "contains_forbidden_words",
    "safe_source_id",
]
