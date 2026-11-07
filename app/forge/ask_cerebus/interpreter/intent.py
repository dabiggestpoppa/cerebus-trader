"""Deterministic intent classification for the twelve frozen intents."""

from __future__ import annotations

import re

from .enums import Intent
from .entities import _MODEL_PATTERNS, _pattern

_COMPARISON = re.compile(
    r"\b(same\s+as|vs\.?|versus|compare|comparison|difference\s+between|different\s+from)\b"
)
_STATISTIC = re.compile(
    r"(win\s*rate|winrate|\bwr\b|probabilit|\bodss?\b|chance|expectanc|correlation|"
    r"sample\s*size|\bn\s*=|median|hit\s*rate|how\s+often|\d+(?:\.\d+)?\s*%|percent|"
    r"backtest|statistic|results?\b|tier\s*boundary|timing\s*distribution|target\s*rate)"
)
_TROUBLESHOOTING = re.compile(
    r"\b(not\s+working|doesn'?t\s+work|broken|error|fix|troubleshoot|wrong|failing)\b"
)
_INDICATOR = re.compile(r"\b(vault|indicator|indicators|library|download)\b")
_METHODOLOGY = re.compile(
    r"\b(explain|how\s+(does|do|is)|methodology|framework|doctrine|confirmation|confirm|"
    r"why\s+(does|do))\b"
)
_HISTORICAL = re.compile(
    r"\b(historical|historically|original|backtest|old|older|earlier|legacy|lineage|"
    r"generation|p90|base80|markov)\b"
    r"|last\s+(monday|tuesday|wednesday|thursday|friday|week|month)"
)
_SETUP = re.compile(
    r"\b(setup|should\s+i|enter|entry|buy|sell|short|long|position|invalidation|"
    r"trade|execute|play)\b"
)
_CURRENT = re.compile(
    r"\b(doing|today|right\s+now|now|current|currently|live|production)\b"
)
_LEVEL = re.compile(r"\b(level|levels|coordinate|anchor|range\s+birth)\b|\b(132|168|120)\b|\bfib\b")
_MODEL_DESCRIPTION = re.compile(r"\b(mean|means|model|game|tracker|family)\b")
_DEFINITION = re.compile(r"\b(what\s+is|what's|define|definition|meaning|term)\b")


def _model_family_present(text: str) -> bool:
    return any(pattern.search(text) for pattern, _ in _MODEL_PATTERNS)


def classify_intent(text: str) -> Intent:
    """Ordered, deterministic classification. First matching rule wins."""

    if _COMPARISON.search(text):
        return Intent.COMPARISON
    if _STATISTIC.search(text):
        return Intent.STATISTIC_EVIDENCE
    if _TROUBLESHOOTING.search(text):
        return Intent.TROUBLESHOOTING
    if _INDICATOR.search(text):
        return Intent.INDICATOR_NAVIGATION
    if _METHODOLOGY.search(text):
        return Intent.METHODOLOGY_RESEARCH
    if _HISTORICAL.search(text):
        return Intent.HISTORICAL_LINEAGE
    if _SETUP.search(text):
        return Intent.SETUP_CONTEXT
    if _LEVEL.search(text):
        return Intent.LEVEL_COORDINATE
    if _CURRENT.search(text):
        return Intent.CURRENT_STATE
    if _MODEL_DESCRIPTION.search(text) and _model_family_present(text):
        return Intent.MODEL_DESCRIPTION
    if _DEFINITION.search(text):
        return Intent.DEFINITION
    return Intent.GENERAL_MARKET_KNOWLEDGE


__all__ = ["classify_intent"]
