"""Cross-source disagreement and clock-drift detection (WP-3B).

Two vendors describing the same interval should agree within one native tick.
Disagreement is never resolved by silently preferring one feed: it is reported
and mapped onto the frozen ``OUTLIER_SOURCE`` flag, which a blocking policy
turns into ``DATA_QUALITY_BLOCKED``.

No new quality flag or refusal code is introduced.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Mapping, Sequence

from app.forge.market_data.quality import QualityFlag

from .contract import RawCandle


@dataclass(frozen=True)
class DisagreementReport:
    """Comparison of two sources over the same canonical keys."""

    agreement: bool
    compared: int
    missing_in_candidate: int
    max_close_delta: Decimal | None
    tolerance: Decimal
    flags: frozenset[QualityFlag]

    def to_dict(self) -> dict:
        return {
            "agreement": self.agreement,
            "compared": self.compared,
            "missing_in_candidate": self.missing_in_candidate,
            "max_close_delta": (
                format(self.max_close_delta, "f")
                if self.max_close_delta is not None
                else None
            ),
            "tolerance": format(self.tolerance, "f"),
            "flags": sorted(flag.value for flag in self.flags),
        }


def compare_sources(
    reference: Sequence[RawCandle],
    candidate: Sequence[RawCandle],
    *,
    tolerance: Decimal,
) -> DisagreementReport:
    """Compare closes on shared keys; absence is reported, never filled."""
    if tolerance < 0:
        raise ValueError("tolerance must be >= 0")
    reference_by_key = {candle.key: candle for candle in reference}
    candidate_by_key = {candle.key: candle for candle in candidate}
    shared = sorted(set(reference_by_key) & set(candidate_by_key))
    max_delta: Decimal | None = None
    for key in shared:
        delta = abs(reference_by_key[key].close - candidate_by_key[key].close)
        if max_delta is None or delta > max_delta:
            max_delta = delta
    missing = len(set(reference_by_key) - set(candidate_by_key))
    agreement = (
        bool(shared)
        and missing == 0
        and max_delta is not None
        and max_delta <= tolerance
    )
    flags: frozenset[QualityFlag] = (
        frozenset() if agreement else frozenset({QualityFlag.OUTLIER_SOURCE})
    )
    return DisagreementReport(
        agreement=agreement,
        compared=len(shared),
        missing_in_candidate=missing,
        max_close_delta=max_delta,
        tolerance=tolerance,
        flags=flags,
    )


def clock_drift_seconds(candles: Sequence[RawCandle]) -> float:
    """Largest gap between a bar's open and the provider's source timestamp."""
    return max(
        (
            abs((candle.source_timestamp - candle.open_time).total_seconds())
            for candle in candles
        ),
        default=0.0,
    )


def detect_clock_drift(
    candles: Sequence[RawCandle], *, max_skew_seconds: float
) -> bool:
    """True when any observation exceeds the declared source clock skew."""
    if max_skew_seconds < 0:
        raise ValueError("max_skew_seconds must be >= 0")
    return clock_drift_seconds(candles) > max_skew_seconds


__all__ = [
    "DisagreementReport",
    "clock_drift_seconds",
    "compare_sources",
    "detect_clock_drift",
]
