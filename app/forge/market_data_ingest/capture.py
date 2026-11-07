"""Source-slice capture, provenance and deterministic window digests.

A captured slice is evidence only when it carries a licence and a source
reference.  The digest deliberately excludes provider identity so the same
market slice from two vendors can be compared without conflating provenance.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime
from typing import Iterable

from app.forge.market_data.bars import ProvenanceKind
from app.forge.market_data.errors import ConventionViolationError

from .contract import RawCandle, as_utc


def source_window_digest(candles: Iterable[RawCandle]) -> str:
    """Stable digest over canonical observation content, provider excluded."""
    payload = [
        candle.canonical_fields()
        for candle in sorted(
            candles,
            key=lambda item: (
                item.open_time.timestamp(),
                item.source_timestamp.timestamp(),
                item.source_revision or "",
            ),
        )
    ]
    text = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class CaptureMetadata:
    """Provenance record for a real (licensed) source slice."""

    provider_id: str
    instrument_id: str
    timeframe: str
    window_start: datetime
    window_end: datetime
    digest: str
    licence_ref: str
    captured_at: datetime
    source_ref: str
    provenance: ProvenanceKind = ProvenanceKind.SOURCE_SLICE

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "window_start", as_utc(self.window_start, "window_start")
        )
        object.__setattr__(self, "window_end", as_utc(self.window_end, "window_end"))
        object.__setattr__(self, "captured_at", as_utc(self.captured_at, "captured_at"))
        if self.provenance is not ProvenanceKind.SOURCE_SLICE:
            raise ConventionViolationError(
                "capture metadata describes a SOURCE_SLICE only"
            )
        if not self.licence_ref or not self.source_ref or not self.digest:
            raise ConventionViolationError(
                "capture requires licence_ref, source_ref and digest"
            )
        if self.window_end <= self.window_start:
            raise ConventionViolationError("capture window must be positive")

    def to_dict(self) -> dict:
        return {
            "provider_id": self.provider_id,
            "instrument_id": self.instrument_id,
            "timeframe": self.timeframe,
            "window_start": self.window_start.isoformat().replace("+00:00", "Z"),
            "window_end": self.window_end.isoformat().replace("+00:00", "Z"),
            "digest": self.digest,
            "licence_ref": self.licence_ref,
            "captured_at": self.captured_at.isoformat().replace("+00:00", "Z"),
            "source_ref": self.source_ref,
            "provenance": self.provenance.value,
        }


def capture_slice(
    candles: Iterable[RawCandle],
    *,
    instrument_id: str,
    timeframe: str,
    licence_ref: str,
    captured_at: datetime,
    source_ref: str,
) -> tuple[tuple[RawCandle, ...], CaptureMetadata]:
    """Label a slice as licensed evidence or refuse.

    Callers must not describe synthetic fixtures as captured market data; the
    provenance label on every candle is checked, not trusted.
    """
    ordered = tuple(sorted(candles, key=lambda item: item.open_time.timestamp()))
    if not ordered:
        raise ConventionViolationError("cannot capture an empty slice")
    for candle in ordered:
        if candle.provenance is ProvenanceKind.SYNTHETIC_FIXTURE:
            raise ConventionViolationError(
                "synthetic candles cannot be captured as licensed evidence"
            )
    labelled = tuple(
        RawCandle(
            provider_id=candle.provider_id,
            source_symbol=candle.source_symbol,
            instrument_id=candle.instrument_id,
            timeframe=candle.timeframe,
            open_time=candle.open_time,
            close_time=candle.close_time,
            open=candle.open,
            high=candle.high,
            low=candle.low,
            close=candle.close,
            source_timestamp=candle.source_timestamp,
            volume=candle.volume,
            source_revision=candle.source_revision,
            finality_hint=candle.finality_hint,
            clock_id=candle.clock_id,
            provenance=ProvenanceKind.SOURCE_SLICE,
            source_ref=source_ref,
            adapter_version=candle.adapter_version,
        )
        for candle in ordered
    )
    metadata = CaptureMetadata(
        provider_id=labelled[0].provider_id,
        instrument_id=instrument_id,
        timeframe=timeframe,
        window_start=labelled[0].open_time,
        window_end=labelled[-1].close_time,
        digest=source_window_digest(labelled),
        licence_ref=licence_ref,
        captured_at=captured_at,
        source_ref=source_ref,
    )
    return labelled, metadata


__all__ = ["CaptureMetadata", "capture_slice", "source_window_digest"]
