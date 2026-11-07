"""Numerical-claim detection and the deterministic-measurement distinction."""

from __future__ import annotations

import re

_STATISTIC = re.compile(
    r"(win\s*rate|winrate|\bwr\b|probabilit|\bodss?\b|chance|expectanc|correlation|"
    r"sample\s*size|\bn\s*=|median|hit\s*rate|how\s+often|\d+(?:\.\d+)?\s*%|percent|"
    r"backtest|statistic|tier\b|timing\s*distribution|results?\b|target\s*rate)"
)
_MEASUREMENT = re.compile(r"\b(price|spread|atr|quote|tick|range)\b")
_CURRENT = re.compile(r"\b(current|currently|now|today|live|right\s+now)\b")


def requires_evidence(text: str) -> bool:
    return bool(_STATISTIC.search(text))


def is_deterministic_measurement(text: str) -> bool:
    return bool(_MEASUREMENT.search(text) and _CURRENT.search(text))


def statistical_text(text: str) -> bool:
    return requires_evidence(text)


__all__ = ["requires_evidence", "is_deterministic_measurement", "statistical_text"]
