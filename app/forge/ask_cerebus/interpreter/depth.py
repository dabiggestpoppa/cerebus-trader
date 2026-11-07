"""Depth selection: explicit request, intent recommendation, authorized cap."""

from __future__ import annotations

import re

from .enums import Depth, Intent, TimeScope, clamp_depth

_OPERATOR_INTENTS = frozenset(
    {
        Intent.CURRENT_STATE,
        Intent.SETUP_CONTEXT,
        Intent.LEVEL_COORDINATE,
        Intent.COMPARISON,
        Intent.TROUBLESHOOTING,
        Intent.INDICATOR_NAVIGATION,
    }
)


def explicit_depth(text: str) -> Depth | None:
    found = [
        depth
        for depth in (Depth.BEGINNER, Depth.OPERATOR, Depth.RESEARCHER)
        if re.search(rf"\b{depth.value.lower()}\b", text)
    ]
    return max(found, key=lambda depth: depth.rank) if found else None


def recommended_depth(text: str, intent: Intent, scope: TimeScope) -> Depth:
    if scope is TimeScope.HISTORICAL_RESEARCH:
        return Depth.RESEARCHER
    if scope is TimeScope.AS_OF:
        return Depth.OPERATOR
    if intent in (Intent.STATISTIC_EVIDENCE, Intent.HISTORICAL_LINEAGE):
        return Depth.RESEARCHER
    if intent in _OPERATOR_INTENTS:
        return Depth.OPERATOR
    return Depth.BEGINNER


def requested_depth(
    text: str, intent: Intent, scope: TimeScope, maximum: Depth
) -> tuple[Depth, Depth]:
    requested = explicit_depth(text) or recommended_depth(text, intent, scope)
    return requested, clamp_depth(requested, maximum)


__all__ = ["explicit_depth", "recommended_depth", "requested_depth"]
