"""Normalized bar contract, finality gate and deterministic reconciliation
(Ch III.1.2 + finality mechanism of III.1.6).

A ``Bar`` carries exactly the frozen fields — instrument, timeframe,
open/close time, OHLC, volume when available, provider, finality, source
timestamp, quality flags — plus provenance and the market-data schema
version (M5).  Rules enforced here:

* no future or incomplete bar is ever treated as final (B2);
* duplicate rows reconcile to one deterministic, order-independent
  result (B3);
* revisions replace only by explicit later-source-timestamp and emit
  ``REVISED`` — silent overwrite is impossible (B4);
* missing bars stay visible as gaps; nothing is ever synthesized (B5);
* provenance is bounded: a ``SYNTHETIC_FIXTURE`` bar can never carry an
  evidence reference (N4).

All dataclasses are frozen: mutation raises (M4).
"""

from __future__ import annotations

import json
from dataclasses import dataclass, replace
from datetime import datetime, timezone
from decimal import Decimal
from enum import Enum
from typing import Iterable, Mapping, Sequence

from .errors import (
    ConventionViolationError,
    NonFinalError,
    RevisionViolationError,
    UnsupportedTimeframeError,
)
from .quality import (
    DataOutcome,
    QualityFlag,
    coerce_flags,
    normalize_flags,
)
from .versions import MARKET_DATA_SCHEMA_VERSION

__all__ = [
    "MARKET_DATA_SCHEMA_VERSION",
    "Bar",
    "Finality",
    "FinalStateSelection",
    "ProvenanceKind",
    "GapMarker",
    "assess_finality",
    "canonical_key",
    "content_digest",
    "dedupe",
    "finalize_for_cutoff",
    "final_state_input",
    "missing_opens",
    "reconcile",
]

TIMEFRAME_MINUTES: Mapping[str, int] = {
    "M1": 1,
    "M5": 5,
    "M15": 15,
    "M30": 30,
    "H1": 60,
    "H4": 240,
    "D1": 1440,
    "W1": 10080,
}


class Finality(str, Enum):
    FINAL = "FINAL"
    NONFINAL = "NONFINAL"


class ProvenanceKind(str, Enum):
    """Fixture provenance labels — synthetic is never evidence (N4)."""

    SYNTHETIC_FIXTURE = "SYNTHETIC_FIXTURE"
    SOURCE_SLICE = "SOURCE_SLICE"


def _as_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        raise ConventionViolationError("bar timestamps must be tz-aware")
    return value.astimezone(timezone.utc)


def _iso(value: datetime) -> str:
    return _as_utc(value).isoformat().replace("+00:00", "Z")


@dataclass(frozen=True)
class Bar:
    """The normalized bar contract (Ch III.1.2)."""

    instrument_id: str
    timeframe: str
    open_time: datetime
    close_time: datetime
    open: Decimal
    high: Decimal
    low: Decimal
    close: Decimal
    volume: Decimal | None
    provider: str
    finality: Finality
    source_timestamp: datetime
    quality_flags: frozenset[QualityFlag]
    provenance: ProvenanceKind
    source_ref: str | None
    market_data_schema_version: str = MARKET_DATA_SCHEMA_VERSION

    def __post_init__(self) -> None:
        object.__setattr__(self, "open_time", _as_utc(self.open_time))
        object.__setattr__(self, "close_time", _as_utc(self.close_time))
        object.__setattr__(self, "source_timestamp", _as_utc(self.source_timestamp))
        if self.market_data_schema_version != MARKET_DATA_SCHEMA_VERSION:
            raise ConventionViolationError("unknown market-data schema version")
        if not self.instrument_id or not self.provider:
            raise ConventionViolationError("instrument_id and provider are required")
        if self.timeframe not in TIMEFRAME_MINUTES:
            raise UnsupportedTimeframeError(f"unknown timeframe {self.timeframe}")
        if self.close_time <= self.open_time:
            raise ConventionViolationError("bar close must be after open")
        for name in ("open", "high", "low", "close"):
            value = getattr(self, name)
            if not isinstance(value, Decimal):
                raise ConventionViolationError(f"{name} must be Decimal")
        if not (self.low <= self.open <= self.high) or not (
            self.low <= self.close <= self.high
        ):
            raise ConventionViolationError("OHLC outside high/low bounds")
        if self.low > self.high:
            raise ConventionViolationError("low above high")
        if self.volume is not None and not isinstance(self.volume, Decimal):
            raise ConventionViolationError("volume must be Decimal or None")
        flags = coerce_flags(self.quality_flags)
        # finality and the NONFINAL flag can never disagree
        if self.finality is Finality.NONFINAL:
            flags = normalize_flags(flags | {QualityFlag.NONFINAL})
        elif QualityFlag.NONFINAL in flags:
            raise ConventionViolationError("FINAL bar cannot carry NONFINAL")
        object.__setattr__(self, "quality_flags", normalize_flags(flags))
        # provenance bounds (N4): synthetic bars can never cite evidence
        if self.provenance is ProvenanceKind.SYNTHETIC_FIXTURE and self.source_ref:
            raise ConventionViolationError(
                "SYNTHETIC_FIXTURE bar cannot carry an evidence reference"
            )
        if self.provenance is ProvenanceKind.SOURCE_SLICE and not self.source_ref:
            raise ConventionViolationError("SOURCE_SLICE bar requires a source ref")

    # -- derived views -------------------------------------------------
    @property
    def timeframe_minutes(self) -> int:
        return TIMEFRAME_MINUTES[self.timeframe]

    @property
    def is_final(self) -> bool:
        return self.finality is Finality.FINAL

    def to_dict(self) -> dict:
        """Deterministic, provider-quarantined serialization."""
        return {
            "instrument_id": self.instrument_id,
            "timeframe": self.timeframe,
            "open_time": _iso(self.open_time),
            "close_time": _iso(self.close_time),
            "open": str(self.open),
            "high": str(self.high),
            "low": str(self.low),
            "close": str(self.close),
            "volume": str(self.volume) if self.volume is not None else None,
            "provider": self.provider,
            "finality": self.finality.value,
            "source_timestamp": _iso(self.source_timestamp),
            "quality_flags": sorted(flag.value for flag in self.quality_flags),
            "provenance": self.provenance.value,
            "source_ref": self.source_ref,
            "market_data_schema_version": self.market_data_schema_version,
        }

    def dumps(self) -> str:
        return json.dumps(self.to_dict(), sort_keys=True, separators=(",", ":"))

    def with_flags(self, extra: Iterable[QualityFlag]) -> "Bar":
        return replace(self, quality_flags=normalize_flags(set(self.quality_flags) | set(extra)))


def canonical_key(bar: Bar) -> tuple[str, str, float]:
    """Identity of a bar for duplicate/revision grouping."""
    return (bar.instrument_id, bar.timeframe, bar.open_time.timestamp())


def assess_finality(close_time: datetime, observation_cutoff: datetime) -> Finality:
    """Final only when the bar has fully closed at the observation cutoff."""
    if _as_utc(close_time) <= _as_utc(observation_cutoff):
        return Finality.FINAL
    return Finality.NONFINAL


def finalize_for_cutoff(bar: Bar, observation_cutoff: datetime) -> Bar:
    """Project a bar onto the finality its close time earns at the cutoff.

    A bar whose close lies beyond the cutoff is (re)marked ``NONFINAL``;
    it can never be finalized by fiat.  A previously nonfinal bar becomes
    ``FINAL`` only once the cutoff passes its close — deterministic and
    repeatable.
    """
    target = assess_finality(bar.close_time, observation_cutoff)
    if target is bar.finality:
        return bar
    if target is Finality.NONFINAL:
        return replace(
            bar,
            finality=Finality.NONFINAL,
            quality_flags=normalize_flags(bar.quality_flags | {QualityFlag.NONFINAL}),
        )
    return replace(
        bar,
        finality=Finality.FINAL,
        quality_flags=normalize_flags(
            bar.quality_flags - {QualityFlag.NONFINAL}
        ),
    )


def _price_signature(bar: Bar) -> tuple:
    return (bar.open, bar.high, bar.low, bar.close, bar.volume)


def _sort_key(bar: Bar) -> tuple:
    return (bar.open_time.timestamp(), bar.source_timestamp.timestamp(), bar.dumps())


def reconcile(bars: Sequence[Bar]) -> tuple[Bar, ...]:
    """Deterministic duplicate resolution and explicit revisions (B3/B4).

    Grouping is by (instrument, timeframe, open_time).  Within a group:

    * identical price signatures -> one survivor carrying ``DUPLICATE``;
      the winner is the latest source timestamp with a stable
      serialization tie-break (order-independent);
    * differing price signatures -> the latest source timestamp wins and
      the survivor carries ``REVISED`` (an older row can never overwrite
      a newer one, regardless of arrival order).

    The result is sorted by open time, so input permutations produce
    byte-identical output.
    """
    groups: dict[tuple[str, str, float], list[Bar]] = {}
    for bar in bars:
        groups.setdefault(canonical_key(bar), []).append(bar)
    result: list[Bar] = []
    for _key, members in groups.items():
        if len(members) == 1:
            result.append(members[0])
            continue
        winner = max(members, key=_sort_key)
        signatures = {_price_signature(member) for member in members}
        if len(signatures) == 1:
            result.append(winner.with_flags([QualityFlag.DUPLICATE]))
        else:
            result.append(winner.with_flags([QualityFlag.REVISED]))
    result.sort(key=_sort_key)
    return tuple(result)


def dedupe(bars: Sequence[Bar]) -> tuple[Bar, ...]:
    """Deterministic duplicate resolution without revision semantics."""
    return reconcile(bars)


def missing_opens(
    present: Sequence[Bar] | Iterable[datetime],
    expected_opens: Sequence[datetime] | None = None,
    *,
    timeframe: str | None = None,
) -> tuple[datetime, ...]:
    """Visible gaps: expected opens with no bar present (B5).

    When ``expected_opens`` is not supplied the interior range is
    inferred from the present bars using the timeframe — the caller
    passes session-derived expectations to also see tail gaps.
    """
    present_opens: set[float] = set()
    stamps: list[float] = []
    for item in present:
        if isinstance(item, Bar):
            stamp = item.open_time.timestamp()
            present_opens.add(stamp)
            stamps.append(stamp)
        else:
            stamp = _as_utc(item).timestamp()
            present_opens.add(stamp)
            stamps.append(stamp)
    if expected_opens is None:
        if not stamps or timeframe is None or timeframe not in TIMEFRAME_MINUTES:
            return ()
        step = TIMEFRAME_MINUTES[timeframe] * 60
        expected = [min(stamps) + i * step for i in range(int((max(stamps) - min(stamps)) // step) + 1)]
    else:
        expected = [_as_utc(value).timestamp() for value in expected_opens]
    missing = sorted({stamp for stamp in expected if stamp not in present_opens})
    return tuple(datetime.fromtimestamp(stamp, tz=timezone.utc) for stamp in missing)


@dataclass(frozen=True)
class GapMarker:
    """A visible gap — a marker, never a synthesized bar."""

    missing_open_time: datetime
    timeframe: str
    quality_flags: frozenset[QualityFlag]

    def __post_init__(self) -> None:
        object.__setattr__(self, "missing_open_time", _as_utc(self.missing_open_time))
        if QualityFlag.GAP not in self.quality_flags:
            raise ConventionViolationError("gap marker must carry GAP")


def gap_markers(
    missing: Sequence[datetime], timeframe: str
) -> tuple[GapMarker, ...]:
    return tuple(
        GapMarker(
            missing_open_time=stamp,
            timeframe=timeframe,
            quality_flags=frozenset({QualityFlag.GAP}),
        )
        for stamp in missing
    )


@dataclass(frozen=True)
class FinalStateSelection:
    """Outcome of excluding nonfinal bars from a final-state calculation (F3/J-c)."""

    final_bars: tuple[Bar, ...]
    excluded_nonfinal: int
    outcome: DataOutcome

    def __post_init__(self) -> None:
        for bar in self.final_bars:
            if bar.finality is not Finality.FINAL or QualityFlag.NONFINAL in bar.quality_flags:
                raise NonFinalError("nonfinal bar reached a final-state selection")


def final_state_input(
    bars: Sequence[Bar], observation_cutoff: datetime
) -> FinalStateSelection:
    """Select final-state inputs: nonfinal bars are excluded, never blended.

    Outcome semantics: nothing final at all -> ``DATA_QUALITY_BLOCKED``;
    some bars excluded -> ``DEGRADED`` (disclosed); all final -> ``OK``.
    """
    final_bars: list[Bar] = []
    excluded = 0
    for bar in bars:
        if assess_finality(bar.close_time, observation_cutoff) is Finality.FINAL:
            final_bars.append(finalize_for_cutoff(bar, observation_cutoff))
        else:
            excluded += 1
    final_bars.sort(key=_sort_key)
    if not final_bars:
        outcome = DataOutcome.DATA_QUALITY_BLOCKED
    elif excluded:
        outcome = DataOutcome.DEGRADED
    else:
        outcome = DataOutcome.OK
    return FinalStateSelection(
        final_bars=tuple(final_bars),
        excluded_nonfinal=excluded,
        outcome=outcome,
    )


def content_digest(bars: Sequence[Bar]) -> str:
    """Digest of canonical bar content, provider metadata excluded (H4).

    Provider identity is feed provenance, not canonical content: two
    feeds of the same slice must digest identically.
    """
    import hashlib

    payload = []
    for bar in sorted(bars, key=_sort_key):
        data = bar.to_dict()
        data["provider"] = "<normalized>"
        payload.append(json.dumps(data, sort_keys=True, separators=(",", ":")))
    return hashlib.sha256("\n".join(payload).encode("utf-8")).hexdigest()
