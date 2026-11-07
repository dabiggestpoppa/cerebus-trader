"""Offline provider normalization (Ch III.1.8).

Raw provider feeds are quarantined observations: each scripted provider
declares its own field names, symbol spelling, timestamp convention and
clock field.  Normalization maps them into the frozen contract; raw key
names, raw symbol spellings and raw timestamp conventions never appear
in the normalized output, and downstream objects carry only canonical
ids (H2).

No network, no provider SDK, no credentials: only scripted fixture
feeds exist in this bloc.  Refusals are explicit ``NormalizeStatus``
states with bounded reasons — unknown symbol, unsupported timeframe,
unsupported clock (never remapped, G4), incomplete record (no invented
OHLC, J-e) and precision violations.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from decimal import Decimal, InvalidOperation
from enum import Enum
from types import MappingProxyType
from typing import Any, Mapping, Sequence

from .bars import (
    Bar,
    ProvenanceKind,
    assess_finality,
    finalize_for_cutoff,
    missing_opens,
    reconcile,
    TIMEFRAME_MINUTES,
)
from .errors import (
    MarketDataError,
    PrecisionViolationError,
    UnknownAliasError,
    UnsupportedTimeframeError,
    UnsupportedProviderError,
)
from .instruments import InstrumentRegistry
from .quality import DataOutcome, QualityFlag, QualityPolicy, normalize_flags


class NormalizeStatus(str, Enum):
    OK = "OK"
    REFUSED = "REFUSED"


class RefusalReason(str, Enum):
    """Bounded refusal vocabulary — factual, no free text."""

    UNKNOWN_SYMBOL = "UNKNOWN_SYMBOL"
    UNSUPPORTED_TIMEFRAME = "UNSUPPORTED_TIMEFRAME"
    UNSUPPORTED_CLOCK = "UNSUPPORTED_CLOCK"
    INCOMPLETE_RECORD = "INCOMPLETE_RECORD"
    PRECISION_VIOLATION = "PRECISION_VIOLATION"


class TimestampStyle(str, Enum):
    EPOCH_SECONDS = "EPOCH_SECONDS"
    EPOCH_MILLISECONDS = "EPOCH_MILLISECONDS"
    ISO_OFFSET = "ISO_OFFSET"


class CloseTimeRule(str, Enum):
    """How a provider's bar close time is obtained.

    ``SOURCE`` requires a provider-supplied close field.  ``OPEN_PLUS_TIMEFRAME``
    derives the close from the bar's open time and declared timeframe with UTC
    arithmetic — deterministic, DST-independent, and never written back into
    the source timestamp.
    """

    SOURCE = "SOURCE"
    OPEN_PLUS_TIMEFRAME = "OPEN_PLUS_TIMEFRAME"


@dataclass(frozen=True)
class ProviderFieldMap:
    """Provider-specific raw field conventions (quarantined here).

    ``close_time`` and ``clock`` are optional: some vendors publish neither.
    A missing close time is only ever *derived* when ``close_time_rule``
    explicitly says so; a missing clock means the provider made no clock
    claim, never that a clock may be assumed.
    """

    provider: str
    symbol: str
    timeframe: str
    open_time: str
    close_time: str | None
    open_price: str
    high: str
    low: str
    close_price: str
    volume: str
    source_timestamp: str
    timestamp_style: TimestampStyle
    clock: str | None = None
    close_time_rule: CloseTimeRule = CloseTimeRule.SOURCE

    @property
    def required_keys(self) -> tuple[str, ...]:
        keys = [self.symbol, self.timeframe, self.open_time]
        if self.close_time is not None:
            keys.append(self.close_time)
        keys.extend(
            (
                self.open_price,
                self.high,
                self.low,
                self.close_price,
                self.source_timestamp,
            )
        )
        if self.clock is not None:
            keys.append(self.clock)
        return tuple(keys)

    @property
    def raw_keys(self) -> tuple[str, ...]:
        return self.required_keys + (self.volume,)


PROVIDER_SCHEMA_REGISTRY_VERSION = "PROVIDER_SCHEMAS_V2"

# Epoch milliseconds before 2001-09-09 are indistinguishable from a seconds
# value passed in the wrong unit; such input is refused, never rescaled.
PROVIDER_SCHEMAS: Mapping[str, ProviderFieldMap] = MappingProxyType({
    "fake_alpha": ProviderFieldMap(
        provider="fake_alpha",
        symbol="pair",
        timeframe="tf",
        open_time="epoch_open",
        close_time="epoch_close",
        open_price="o",
        high="h",
        low="l",
        close_price="c",
        volume="vol",
        source_timestamp="feed_ts",
        clock="zone",
        timestamp_style=TimestampStyle.EPOCH_SECONDS,
    ),
    "fake_beta": ProviderFieldMap(
        provider="fake_beta",
        symbol="sym",
        timeframe="int",
        open_time="t0",
        close_time="t1",
        open_price="px_o",
        high="px_h",
        low="px_l",
        close_price="px_c",
        volume="qty",
        source_timestamp="src_t",
        clock="tz",
        timestamp_style=TimestampStyle.ISO_OFFSET,
    ),
    # Vendors below publish no close-time field and no clock column: the
    # adapter supplies request context (symbol/timeframe) and the kernel
    # derives the interval boundary from the canonical open time.
    "twelvedata": ProviderFieldMap(
        provider="twelvedata",
        symbol="symbol",
        timeframe="interval",
        open_time="datetime",
        close_time=None,
        open_price="open",
        high="high",
        low="low",
        close_price="close",
        volume="volume",
        source_timestamp="datetime",
        timestamp_style=TimestampStyle.ISO_OFFSET,
        clock=None,
        close_time_rule=CloseTimeRule.OPEN_PLUS_TIMEFRAME,
    ),
    "polygon": ProviderFieldMap(
        provider="polygon",
        symbol="symbol",
        timeframe="timeframe",
        open_time="t",
        close_time=None,
        open_price="o",
        high="h",
        low="l",
        close_price="c",
        volume="v",
        source_timestamp="t",
        timestamp_style=TimestampStyle.EPOCH_MILLISECONDS,
        clock=None,
        close_time_rule=CloseTimeRule.OPEN_PLUS_TIMEFRAME,
    ),
    "kraken": ProviderFieldMap(
        provider="kraken",
        symbol="symbol",
        timeframe="timeframe",
        open_time="t",
        close_time=None,
        open_price="o",
        high="h",
        low="l",
        close_price="c",
        volume="v",
        source_timestamp="t",
        timestamp_style=TimestampStyle.EPOCH_SECONDS,
        clock=None,
        close_time_rule=CloseTimeRule.OPEN_PLUS_TIMEFRAME,
    ),
})


def provider_schema(provider: str) -> ProviderFieldMap:
    schema = PROVIDER_SCHEMAS.get(provider)
    if schema is None:
        raise UnsupportedProviderError(
            f"no scripted normalization schema for provider {provider!r}"
        )
    return schema


def _integer_timestamp(value: Any) -> int | None:
    """Integer epoch value as int or digit string; floats are refused."""
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, str):
        text = value.strip()
        if text.lstrip("-").isdigit():
            return int(text)
    return None


def _parse_timestamp(value: Any, style: TimestampStyle) -> datetime | None:
    try:
        if style is TimestampStyle.EPOCH_SECONDS:
            seconds = _integer_timestamp(value)
            if seconds is None:
                return None
            return datetime.fromtimestamp(seconds, tz=timezone.utc)
        if style is TimestampStyle.EPOCH_MILLISECONDS:
            milliseconds = _integer_timestamp(value)
            if milliseconds is None or milliseconds < 10**12:
                return None  # seconds value under a ms style is refused
            seconds, remainder = divmod(milliseconds, 1000)
            return datetime.fromtimestamp(seconds, tz=timezone.utc) + timedelta(
                milliseconds=remainder
            )
        if style is not TimestampStyle.ISO_OFFSET:
            return None  # unknown unit is never guessed
        parsed = datetime.fromisoformat(str(value))
    except (ValueError, TypeError, OverflowError, OSError):
        return None
    if parsed.tzinfo is None:
        return None  # naive provider timestamps are refused, never guessed
    return parsed.astimezone(timezone.utc)


def _parse_decimal(value: Any) -> Decimal | None:
    if isinstance(value, bool) or value is None:
        return None
    try:
        return Decimal(str(value))
    except (InvalidOperation, ValueError):
        return None


@dataclass(frozen=True)
class NormalizedRecord:
    """Result of normalizing exactly one raw record."""

    status: NormalizeStatus
    bar: Bar | None
    reason: RefusalReason | None
    flags: frozenset[QualityFlag]

    @property
    def refused(self) -> bool:
        return self.status is NormalizeStatus.REFUSED


def _refused(reason: RefusalReason, flags: Sequence[QualityFlag] = ()) -> NormalizedRecord:
    return NormalizedRecord(
        status=NormalizeStatus.REFUSED,
        bar=None,
        reason=reason,
        flags=frozenset(flags),
    )


def normalize_record(
    payload: Mapping[str, Any],
    provider: str,
    registry: InstrumentRegistry,
    *,
    observation_cutoff: datetime,
    provenance: ProvenanceKind,
    source_ref: str | None = None,
) -> NormalizedRecord:
    """Map one raw provider record into the normalized contract.

    Every failure mode is an explicit refusal carrying a bounded reason
    and, where data state is involved, a bounded quality flag — never an
    invented bar and never a remapped clock.
    """
    schema = provider_schema(provider)

    missing_keys = [key for key in schema.required_keys if key not in payload]
    if missing_keys:
        return _refused(RefusalReason.INCOMPLETE_RECORD, [QualityFlag.GAP])

    try:
        instrument = registry.resolve_provider(provider, str(payload[schema.symbol]))
    except UnknownAliasError:
        return _refused(RefusalReason.UNKNOWN_SYMBOL)

    timeframe = str(payload[schema.timeframe])
    try:
        instrument.require_timeframe(timeframe)
    except UnsupportedTimeframeError:
        return _refused(RefusalReason.UNSUPPORTED_TIMEFRAME)

    if schema.clock is not None:
        clock_id = str(payload[schema.clock])
        if not instrument.supports_clock(clock_id):
            # G4: fail closed with the flag — never silently remapped.
            return _refused(
                RefusalReason.UNSUPPORTED_CLOCK, [QualityFlag.UNSUPPORTED_CLOCK]
            )

    open_time = _parse_timestamp(payload[schema.open_time], schema.timestamp_style)
    if open_time is None:
        return _refused(RefusalReason.INCOMPLETE_RECORD, [QualityFlag.GAP])
    if schema.close_time is not None:
        close_time = _parse_timestamp(
            payload[schema.close_time], schema.timestamp_style
        )
    elif schema.close_time_rule is CloseTimeRule.OPEN_PLUS_TIMEFRAME:
        close_time = open_time + timedelta(minutes=TIMEFRAME_MINUTES[timeframe])
    else:  # SOURCE rule without a source close field: nothing is invented
        close_time = None
    source_timestamp = _parse_timestamp(
        payload[schema.source_timestamp], schema.timestamp_style
    )
    if close_time is None or source_timestamp is None:
        return _refused(RefusalReason.INCOMPLETE_RECORD, [QualityFlag.GAP])
    if close_time <= open_time:
        return _refused(RefusalReason.INCOMPLETE_RECORD, [QualityFlag.GAP])

    open_price = _parse_decimal(payload[schema.open_price])
    high = _parse_decimal(payload[schema.high])
    low = _parse_decimal(payload[schema.low])
    close_price = _parse_decimal(payload[schema.close_price])
    if None in (open_price, high, low, close_price):
        return _refused(RefusalReason.INCOMPLETE_RECORD, [QualityFlag.GAP])
    for price in (open_price, high, low, close_price):
        try:
            instrument.validate_price(price)
        except PrecisionViolationError:
            return _refused(RefusalReason.PRECISION_VIOLATION)

    volume: Decimal | None = None
    if schema.volume in payload:
        volume = _parse_decimal(payload[schema.volume])

    finality = assess_finality(close_time, observation_cutoff)
    flags: set[QualityFlag] = {QualityFlag.COMPLETE}
    try:
        bar = Bar(
            instrument_id=instrument.instrument_id,
            timeframe=timeframe,
            open_time=open_time,
            close_time=close_time,
            open=open_price,
            high=high,
            low=low,
            close=close_price,
            volume=volume,
            provider=provider,
            finality=finality,
            source_timestamp=source_timestamp,
            quality_flags=frozenset(flags),
            provenance=provenance,
            source_ref=source_ref,
        )
    except MarketDataError:
        return _refused(RefusalReason.INCOMPLETE_RECORD, [QualityFlag.GAP])
    return NormalizedRecord(
        status=NormalizeStatus.OK,
        bar=bar,
        reason=None,
        flags=bar.quality_flags,
    )


@dataclass(frozen=True)
class FeedResult:
    """Outcome of normalizing a scripted feed slice."""

    bars: tuple[Bar, ...]
    refused: tuple[NormalizedRecord, ...]
    missing: tuple[datetime, ...]
    quality_flags: frozenset[QualityFlag]
    timeframe: str | None

    @property
    def ok_count(self) -> int:
        return len(self.bars)

    @property
    def refusal_count(self) -> int:
        return len(self.refused)

    def evaluate(self, policy: QualityPolicy) -> DataOutcome:
        return policy.evaluate(self.quality_flags)

    def to_dict(self) -> dict:
        return {
            "bars": [bar.to_dict() for bar in self.bars],
            "refusals": [
                {"reason": record.reason.value if record.reason else None}
                for record in self.refused
            ],
            "missing": [
                stamp.isoformat().replace("+00:00", "Z") for stamp in self.missing
            ],
            "quality_flags": sorted(flag.value for flag in self.quality_flags),
            "timeframe": self.timeframe,
        }


def normalize_feed(
    records: Sequence[Mapping[str, Any]],
    provider: str,
    registry: InstrumentRegistry,
    *,
    observation_cutoff: datetime,
    provenance: ProvenanceKind,
    source_ref: str | None = None,
    expected_opens: Sequence[datetime] | None = None,
) -> FeedResult:
    """Normalize, reconcile and gap-check a scripted feed slice.

    The result is deterministic for a given record set regardless of
    arrival order: reconciliation inside ``bars.reconcile`` is
    order-independent and missing-bar detection only reports absence —
    it never synthesizes OHLC.
    """
    schema = provider_schema(provider)
    normalized = [
        normalize_record(
            payload,
            provider,
            registry,
            observation_cutoff=observation_cutoff,
            provenance=provenance,
            source_ref=source_ref,
        )
        for payload in records
    ]
    ok_bars = [record.bar for record in normalized if record.bar is not None]
    refused = tuple(record for record in normalized if record.refused)
    reconciled = reconcile(ok_bars)
    bars = tuple(finalize_for_cutoff(bar, observation_cutoff) for bar in reconciled)

    timeframe: str | None = bars[0].timeframe if bars else None
    if timeframe is None and records:
        candidate = str(records[0].get(schema.timeframe, ""))
        timeframe = candidate if candidate in TIMEFRAME_MINUTES else None
    missing = missing_opens(bars, expected_opens, timeframe=timeframe)

    quality: set[QualityFlag] = set()
    for bar in bars:
        quality |= set(bar.quality_flags)
    for record in refused:
        quality |= set(record.flags)
    if missing:
        quality.add(QualityFlag.GAP)
    quality_flags = normalize_flags(quality)

    return FeedResult(
        bars=bars,
        refused=refused,
        missing=tuple(missing),
        quality_flags=quality_flags,
        timeframe=timeframe,
    )
