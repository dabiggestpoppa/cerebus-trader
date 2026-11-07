"""Provider-neutral raw candle contract and adapter port (WP-3B).

A ``RawCandle`` is exactly what a provider gave us, quarantined: provider id,
source symbol, canonical instrument id, UTZ timestamps, native decimals,
source revision, finality hint, provenance and adapter version.  It is **not**
a canonical bar.  Canonicalization happens in ``canonical.py`` using the frozen
III.1 rules.

Laws enforced here:

* every timestamp is timezone-aware and normalized to UTC; a naive timestamp is
  refused rather than guessed;
* prices are ``Decimal`` and finite — no float conversion, no rounding;
* OHLC must be internally consistent;
* provider finality is a *hint* (``FINAL`` / ``NONFINAL`` / ``None``); it never
  becomes a canonical finality decision;
* provenance bounds mirror III.1: a synthetic candle can never cite evidence,
  and a source slice must cite one.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal
from typing import Iterator, Protocol, runtime_checkable

from app.forge.market_data.bars import TIMEFRAME_MINUTES, ProvenanceKind
from app.forge.market_data.errors import ConventionViolationError
from app.forge.providers.doctrine import ProviderHealth

ADAPTER_SCHEMA_VERSION = "MARKET_DATA_INGEST_V1"
FINALITY_HINTS: frozenset[str] = frozenset({"FINAL", "NONFINAL"})


def as_utc(value: datetime, field: str) -> datetime:
    """Normalize an aware timestamp to UTC; naive input is a convention error."""
    if not isinstance(value, datetime):
        raise ConventionViolationError(f"{field} must be a datetime")
    if value.tzinfo is None:
        raise ConventionViolationError(f"{field} must be timezone-aware")
    return value.astimezone(timezone.utc)


def _iso(value: datetime) -> str:
    return as_utc(value, "timestamp").isoformat().replace("+00:00", "Z")


@dataclass(frozen=True)
class ProviderCapabilities:
    """What an adapter truthfully supports — never a marketing claim."""

    provider_id: str
    instruments: frozenset[str]
    timeframes: frozenset[str]
    historical: bool
    streaming: bool
    revision_support: bool
    finality_signal: bool
    max_page_size: int
    notes: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not self.provider_id:
            raise ConventionViolationError("provider_id is required")
        if not self.instruments:
            raise ConventionViolationError("capabilities must declare instruments")
        unknown = set(self.timeframes) - set(TIMEFRAME_MINUTES)
        if unknown:
            raise ConventionViolationError(
                f"unknown timeframes {sorted(unknown)}"
            )
        if self.max_page_size < 1:
            raise ConventionViolationError("max_page_size must be >= 1")

    def supports(self, instrument_id: str, timeframe: str) -> bool:
        return (
            instrument_id in self.instruments
            and timeframe in self.timeframes
        )


@dataclass(frozen=True)
class CandleRequest:
    """One bounded historical or streaming window request."""

    instrument_id: str
    timeframe: str
    start: datetime
    end: datetime
    limit: int = 500

    def __post_init__(self) -> None:
        object.__setattr__(self, "start", as_utc(self.start, "start"))
        object.__setattr__(self, "end", as_utc(self.end, "end"))
        if self.timeframe not in TIMEFRAME_MINUTES:
            raise ConventionViolationError(f"unknown timeframe {self.timeframe}")
        if self.end <= self.start:
            raise ConventionViolationError("request end must be after start")
        if self.limit < 1:
            raise ConventionViolationError("limit must be >= 1")


@dataclass(frozen=True)
class RawCandle:
    """One provider observation, quarantined before canonicalization."""

    provider_id: str
    source_symbol: str
    instrument_id: str
    timeframe: str
    open_time: datetime
    close_time: datetime
    open: Decimal
    high: Decimal
    low: Decimal
    close: Decimal
    source_timestamp: datetime
    volume: Decimal | None = None
    source_revision: str | None = None
    finality_hint: str | None = None
    clock_id: str | None = None
    provenance: ProvenanceKind = ProvenanceKind.SYNTHETIC_FIXTURE
    source_ref: str | None = None
    adapter_version: str = ADAPTER_SCHEMA_VERSION

    def __post_init__(self) -> None:
        for field_name in ("open_time", "close_time", "source_timestamp"):
            object.__setattr__(
                self, field_name, as_utc(getattr(self, field_name), field_name)
            )
        if not self.provider_id or not self.source_symbol or not self.instrument_id:
            raise ConventionViolationError(
                "provider_id, source_symbol and instrument_id are required"
            )
        if self.timeframe not in TIMEFRAME_MINUTES:
            raise ConventionViolationError(f"unknown timeframe {self.timeframe}")
        if self.close_time <= self.open_time:
            raise ConventionViolationError("candle close must be after open")
        for name in ("open", "high", "low", "close"):
            value = getattr(self, name)
            if not isinstance(value, Decimal) or not value.is_finite():
                raise ConventionViolationError(f"{name} must be a finite Decimal")
        if self.volume is not None and (
            not isinstance(self.volume, Decimal) or not self.volume.is_finite()
        ):
            raise ConventionViolationError("volume must be a finite Decimal or None")
        if self.low > self.high:
            raise ConventionViolationError("low above high")
        if not (self.low <= self.open <= self.high):
            raise ConventionViolationError("open outside high/low")
        if not (self.low <= self.close <= self.high):
            raise ConventionViolationError("close outside high/low")
        if self.finality_hint is not None and self.finality_hint not in FINALITY_HINTS:
            raise ConventionViolationError("unknown finality hint")
        if self.provenance is ProvenanceKind.SYNTHETIC_FIXTURE and self.source_ref:
            raise ConventionViolationError(
                "SYNTHETIC_FIXTURE candle cannot carry an evidence reference"
            )
        if self.provenance is ProvenanceKind.SOURCE_SLICE and not self.source_ref:
            raise ConventionViolationError(
                "SOURCE_SLICE candle requires a source reference"
            )

    def canonical_fields(self) -> dict:
        """Provider-independent identity of this observation."""
        return {
            "instrument_id": self.instrument_id,
            "timeframe": self.timeframe,
            "open_time": _iso(self.open_time),
            "close_time": _iso(self.close_time),
            "open": format(self.open, "f"),
            "high": format(self.high, "f"),
            "low": format(self.low, "f"),
            "close": format(self.close, "f"),
            "volume": format(self.volume, "f") if self.volume is not None else None,
            "source_timestamp": _iso(self.source_timestamp),
            "source_revision": self.source_revision,
        }

    def digest(self) -> str:
        """Deterministic digest of canonical observation content."""
        payload = json.dumps(
            self.canonical_fields(), sort_keys=True, separators=(",", ":")
        )
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()

    @property
    def key(self) -> tuple[str, str, float]:
        return (
            self.instrument_id,
            self.timeframe,
            self.open_time.timestamp(),
        )


@dataclass(frozen=True)
class CandlePage:
    """One provider page; ``exhausted`` is the provider's own claim."""

    candles: tuple[RawCandle, ...]
    next_cursor: datetime | None = None
    exhausted: bool = True

    def __post_init__(self) -> None:
        if self.next_cursor is not None:
            object.__setattr__(
                self, "next_cursor", as_utc(self.next_cursor, "next_cursor")
            )
        if self.exhausted and self.next_cursor is not None:
            raise ConventionViolationError("exhausted page cannot carry a cursor")


@runtime_checkable
class MarketDataProvider(Protocol):
    """The WP-3B adapter port (mirrors II.5 doctrine)."""

    provider_id: str

    def capabilities(self) -> ProviderCapabilities:
        """Declare truthful coverage; never inferred from a filename."""
        ...

    def fetch(self, request: CandleRequest) -> CandlePage:
        """Fetch exactly one bounded page. Never loops, never retries."""
        ...

    def stream(self, request: CandleRequest) -> Iterator[RawCandle]:
        """Yield observations as they arrive; caller owns the loop and retries."""
        ...

    def health(self) -> ProviderHealth:
        """Pure health answer; performs no network call."""
        ...

    def close(self) -> None:
        """Release transport resources deterministically."""
        ...


__all__ = [
    "ADAPTER_SCHEMA_VERSION",
    "FINALITY_HINTS",
    "CandlePage",
    "CandleRequest",
    "MarketDataProvider",
    "ProviderCapabilities",
    "RawCandle",
    "as_utc",
]
