"""Canonicalization of raw provider observations through public III.1 APIs.

Why this module exists instead of calling ``normalize.normalize_feed``: that
function resolves providers through a module-level ``PROVIDER_SCHEMAS`` table
inside the frozen ``market_data/normalize.py``.  Registering real providers
therefore requires a frozen amendment, which WP-3B is not authorized to make.

This module instead composes the *public* frozen contracts:

``InstrumentRegistry`` → ``Instrument.validate_price`` → ``Bar`` →
``assess_finality`` → ``reconcile`` → ``finalize_for_cutoff`` →
``missing_opens`` → ``QualityPolicy.evaluate`` → ``content_digest``.

Every rule is still III.1's.  What lives here is only the provider-field
quarantine (already done by the adapter) and the refusal mapping.  If the
schema-table amendment is later approved, this module can delegate to
``normalize_feed`` without changing callers.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Iterable, Sequence

from app.forge.market_data.bars import (
    Bar,
    assess_finality,
    content_digest,
    finalize_for_cutoff,
    missing_opens,
    reconcile,
)
from app.forge.market_data.errors import (
    MarketDataError,
    UnsupportedTimeframeError,
    UnknownAliasError,
)
from app.forge.market_data.instruments import InstrumentRegistry
from app.forge.market_data.normalize import RefusalReason
from app.forge.market_data.quality import (
    DataOutcome,
    QualityFlag,
    QualityPolicy,
    normalize_flags,
)

from .capture import source_window_digest
from .contract import RawCandle, as_utc


@dataclass(frozen=True)
class IngestRefusal:
    """One bounded refusal; no free-text payload."""

    instrument_id: str
    reason: RefusalReason
    flags: frozenset[QualityFlag] = frozenset()
    open_time: datetime | None = None


@dataclass(frozen=True)
class CanonicalOutcome:
    """Result of canonicalizing one provider window."""

    bars: tuple[Bar, ...]
    refused: tuple[IngestRefusal, ...]
    missing: tuple[datetime, ...]
    quality_flags: frozenset[QualityFlag]
    outcome: DataOutcome
    source_window_digest: str

    @property
    def refusal_count(self) -> int:
        return len(self.refused)

    @property
    def digest(self) -> str:
        """Canonical content digest (provider identity excluded)."""
        return content_digest(self.bars)

    def to_dict(self) -> dict:
        return {
            "bar_count": len(self.bars),
            "refusals": [
                {
                    "instrument_id": item.instrument_id,
                    "reason": item.reason.value,
                    "flags": sorted(flag.value for flag in item.flags),
                }
                for item in self.refused
            ],
            "missing": [
                stamp.isoformat().replace("+00:00", "Z") for stamp in self.missing
            ],
            "quality_flags": sorted(flag.value for flag in self.quality_flags),
            "outcome": self.outcome.value,
            "source_window_digest": self.source_window_digest,
            "content_digest": self.digest,
        }


def _refuse(
    candle: RawCandle,
    reason: RefusalReason,
    flags: Iterable[QualityFlag] = (),
) -> IngestRefusal:
    return IngestRefusal(
        instrument_id=candle.instrument_id,
        reason=reason,
        flags=frozenset(flags),
        open_time=candle.open_time,
    )


def canonicalize(
    candles: Sequence[RawCandle],
    registry: InstrumentRegistry,
    policy: QualityPolicy,
    *,
    observation_cutoff: datetime,
    expected_opens: Sequence[datetime] | None = None,
) -> CanonicalOutcome:
    """Map raw observations to canonical bars without inventing anything."""
    cutoff = as_utc(observation_cutoff, "observation_cutoff")
    bars: list[Bar] = []
    refused: list[IngestRefusal] = []
    for candle in candles:
        try:
            instrument = registry.get(candle.instrument_id)
        except UnknownAliasError:
            refused.append(_refuse(candle, RefusalReason.UNKNOWN_SYMBOL))
            continue
        try:
            instrument.require_timeframe(candle.timeframe)
        except UnsupportedTimeframeError:
            refused.append(_refuse(candle, RefusalReason.UNSUPPORTED_TIMEFRAME))
            continue
        if candle.clock_id is not None and not instrument.supports_clock(
            candle.clock_id
        ):
            refused.append(
                _refuse(
                    candle,
                    RefusalReason.UNSUPPORTED_CLOCK,
                    [QualityFlag.UNSUPPORTED_CLOCK],
                )
            )
            continue
        try:
            for name in ("open", "high", "low", "close"):
                instrument.validate_price(getattr(candle, name))
        except MarketDataError:
            refused.append(_refuse(candle, RefusalReason.PRECISION_VIOLATION))
            continue
        try:
            bar = Bar(
                instrument_id=instrument.instrument_id,
                timeframe=candle.timeframe,
                open_time=candle.open_time,
                close_time=candle.close_time,
                open=candle.open,
                high=candle.high,
                low=candle.low,
                close=candle.close,
                volume=candle.volume,
                provider=candle.provider_id,
                finality=assess_finality(candle.close_time, cutoff),
                source_timestamp=candle.source_timestamp,
                quality_flags=frozenset({QualityFlag.COMPLETE}),
                provenance=candle.provenance,
                source_ref=candle.source_ref,
            )
        except MarketDataError:
            refused.append(
                _refuse(candle, RefusalReason.INCOMPLETE_RECORD, [QualityFlag.GAP])
            )
            continue
        bars.append(bar)

    reconciled = tuple(
        finalize_for_cutoff(bar, cutoff) for bar in reconcile(bars)
    )
    timeframe = reconciled[0].timeframe if reconciled else None
    if timeframe is None and candles:
        candidate = candles[0].timeframe
        timeframe = candidate
    missing = missing_opens(reconciled, expected_opens, timeframe=timeframe)

    quality: set[QualityFlag] = set()
    for bar in reconciled:
        quality |= set(bar.quality_flags)
    for refusal in refused:
        quality |= set(refusal.flags)
    if missing:
        quality.add(QualityFlag.GAP)
    flags = normalize_flags(quality)
    return CanonicalOutcome(
        bars=reconciled,
        refused=tuple(refused),
        missing=tuple(missing),
        quality_flags=flags,
        outcome=policy.evaluate(flags),
        source_window_digest=source_window_digest(candles),
    )


__all__ = ["CanonicalOutcome", "IngestRefusal", "canonicalize"]
