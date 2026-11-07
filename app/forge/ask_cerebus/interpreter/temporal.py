"""Temporal scope classification: five frozen values, no fallback."""

from __future__ import annotations

import re

from .enums import TimeScope

_AS_OF = re.compile(
    r"\b(as\s+of|yesterday|last\s+(monday|tuesday|wednesday|thursday|friday|week|month|year))\b"
    r"|\b\d{4}-\d{2}-\d{2}\b"
)
_VERSION = re.compile(r"\bv\d+\b|\bmodel\s+version\b|\bversion\b")
_HISTORICAL = re.compile(
    r"\b(historical|historically|original|backtest|old|older|earlier|legacy|lineage|"
    r"generation|p90|base80|markov)\b"
)
_CURRENT = re.compile(r"\b(doing|today|right\s+now|now|current|currently|live|production)\b")


def classify_time_scope(text: str) -> TimeScope:
    if _AS_OF.search(text):
        return TimeScope.AS_OF
    if _VERSION.search(text):
        return TimeScope.MODEL_VERSION
    if _HISTORICAL.search(text):
        return TimeScope.HISTORICAL_RESEARCH
    if _CURRENT.search(text):
        return TimeScope.CURRENT
    return TimeScope.GENERAL


__all__ = ["classify_time_scope"]
