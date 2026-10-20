"""Range engine (Ch III.2.1).

Deterministic range facts over **finalized** III.1 bars: high, low,
size, midpoint, direction, close location, consumed fraction,
range-left and the breakout/return state.

Discipline:

* only finalized bars contribute — a nonfinal bar is excluded by III.1's
  final-state selection, never blended;
* incomplete input yields ``DATA_QUALITY_BLOCKED`` (or the model-declared
  degraded state) — never a fabricated measurement;
* every price is a ``Decimal`` in asset-native units; the size is
  expressed as a ``NativeMagnitude`` (a count of the instrument's own
  native step), so an EUR pip count can never be added to a BTC dollar
  count;
* range-left is the *unconsumed remainder of the measured range*.  It is
  a measurement, not an expectation: any conditional-expansion range-left
  is a model concern and belongs to a later Bloc.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Sequence

from app.forge.market_data import (
    Bar,
    DataOutcome,
    Instrument,
    NativePrice,
    QualityFlag,
    QualityPolicy,
    final_state_input,
    missing_opens,
)

from .contracts import (
    Measurement,
    NativeMagnitude,
    Provenance,
    envelope,
    native_count,
    native_span,
    quantize_ratio,
    source_window_from_bars,
)
from .errors import (
    DataQualityBlockedError,
    RangeNotResolvableError,
)

__all__ = [
    "BreakoutReturnState",
    "RangeDirection",
    "RangeMeasurement",
    "measure_range",
]


class RangeDirection(str, Enum):
    """Direction of the measured range, as a fact from the input bars."""

    UP = "UP"
    DOWN = "DOWN"
    FLAT = "FLAT"


class BreakoutReturnState(str, Enum):
    """Where the path sits relative to the established range."""

    INSIDE_RANGE = "INSIDE_RANGE"
    BREAKOUT_ABOVE = "BREAKOUT_ABOVE"
    BREAKOUT_BELOW = "BREAKOUT_BELOW"
    RETURNED_INSIDE = "RETURNED_INSIDE"


@dataclass(frozen=True)
class RangeMeasurement(Measurement):
    """The measured range (Ch III.2.1) plus its provenance envelope."""

    high: NativePrice
    low: NativePrice
    size: NativeMagnitude
    midpoint: NativePrice
    direction: RangeDirection
    close_location: Decimal
    consumed_fraction: Decimal
    range_left: NativeMagnitude
    breakout_return_state: BreakoutReturnState

    def to_dict(self) -> dict:
        from .contracts import encode_value

        return encode_value(self)


def _clamp(value: Decimal, lower: Decimal, upper: Decimal) -> Decimal:
    if value < lower:
        return lower
    if value > upper:
        return upper
    return value


def _finalize(
    bars: Sequence[Bar],
    observation_cutoff: datetime,
    expected_opens: Sequence[datetime] | None,
) -> tuple[tuple[Bar, ...], DataOutcome, frozenset[QualityFlag]]:
    """Select the eligible finalized bars and their quality flags."""
    if not bars:
        raise RangeNotResolvableError("no bars supplied")
    selection = final_state_input(bars, observation_cutoff)
    if selection.outcome is DataOutcome.DATA_QUALITY_BLOCKED:
        raise DataQualityBlockedError(
            "no finalized bar is available for the observation cutoff"
        )
    flags: set[QualityFlag] = set()
    for bar in selection.final_bars:
        flags |= bar.quality_flags
    if expected_opens is not None:
        gaps = missing_opens(selection.final_bars, expected_opens)
        if gaps:
            flags.add(QualityFlag.GAP)
    return selection.final_bars, selection.outcome, frozenset(flags)


def _split_establishing(
    bars: Sequence[Bar], establish_until: datetime | None
) -> tuple[tuple[Bar, ...], tuple[Bar, ...]]:
    """Split bars into the establishing window and the post-window path."""
    if establish_until is None:
        return tuple(bars), ()
    establishing = tuple(
        bar for bar in bars if bar.close_time <= establish_until
    )
    following = tuple(bar for bar in bars if bar.close_time > establish_until)
    if not establishing:
        raise RangeNotResolvableError(
            "the establishing window contains no finalized bar"
        )
    return establishing, following


def _breakout_state(
    established_high: Decimal,
    established_low: Decimal,
    following: Sequence[Bar],
) -> BreakoutReturnState:
    """Classify the post-establishment path against the established range."""
    if not following:
        return BreakoutReturnState.INSIDE_RANGE
    last_close = following[-1].close
    if last_close > established_high:
        return BreakoutReturnState.BREAKOUT_ABOVE
    if last_close < established_low:
        return BreakoutReturnState.BREAKOUT_BELOW
    for bar in following:
        if bar.close > established_high or bar.close < established_low:
            return BreakoutReturnState.RETURNED_INSIDE
    return BreakoutReturnState.INSIDE_RANGE


def measure_range(
    bars: Sequence[Bar],
    *,
    instrument: Instrument,
    provenance: Provenance,
    observation_cutoff: datetime,
    quality_policy: QualityPolicy,
    expected_opens: Sequence[datetime] | None = None,
    establish_until: datetime | None = None,
    definition_version: str = "V1",
) -> RangeMeasurement:
    """Measure one range over finalized bars.

    ``establish_until`` splits the input: the range is established from
    the bars closing at or before it, and the breakout/return state is
    classified over the bars that follow.  With no split, the state is
    ``INSIDE_RANGE`` — a breakout cannot be measured without an
    established reference.
    """
    final_bars, outcome, flags = _finalize(
        bars, observation_cutoff, expected_opens
    )
    policy_outcome = quality_policy.evaluate(flags)
    if policy_outcome is DataOutcome.DATA_QUALITY_BLOCKED:
        raise DataQualityBlockedError(
            "declared quality policy blocks calculation: "
            + ", ".join(sorted(flag.value for flag in flags))
        )
    quality_state = (
        DataOutcome.DEGRADED
        if policy_outcome is DataOutcome.DEGRADED
        else outcome
    )

    establishing, following = _split_establishing(final_bars, establish_until)
    if not establishing:
        raise RangeNotResolvableError("no finalized bar in the measured window")

    high = max(bar.high for bar in establishing)
    low = min(bar.low for bar in establishing)
    if high < low:
        raise RangeNotResolvableError("range high is below range low")
    size = native_span(
        instrument.instrument_id,
        instrument.native_unit,
        instrument.native_step,
        low,
        high,
    )
    if size.value == 0:
        raise RangeNotResolvableError("range has zero size")

    unit = instrument.native_unit
    origin = establishing[0].open
    last_close = establishing[-1].close
    midpoint_value = (high + low) / Decimal(2)
    midpoint = NativePrice(instrument.instrument_id, unit, midpoint_value)

    span = high - low
    close_location = quantize_ratio((last_close - low) / span)

    if last_close > origin:
        direction = RangeDirection.UP
        consumed = _clamp(last_close - origin, Decimal(0), span)
    elif last_close < origin:
        direction = RangeDirection.DOWN
        consumed = _clamp(origin - last_close, Decimal(0), span)
    else:
        direction = RangeDirection.FLAT
        consumed = Decimal(0)

    consumed_fraction = quantize_ratio(consumed / span)
    range_left = native_count(
        instrument.instrument_id, unit, instrument.native_step, span - consumed
    )

    state = _breakout_state(high, low, following)

    window = source_window_from_bars(final_bars)
    context = provenance.context(window, quality_state)
    return RangeMeasurement(
        **envelope(
            context,
            "RANGE_MEASUREMENT",
            definition_version=definition_version,
            native_unit=unit,
        ),
        high=NativePrice(instrument.instrument_id, unit, high),
        low=NativePrice(instrument.instrument_id, unit, low),
        size=size,
        midpoint=midpoint,
        direction=direction,
        close_location=close_location,
        consumed_fraction=consumed_fraction,
        range_left=range_left,
        breakout_return_state=state,
    )
