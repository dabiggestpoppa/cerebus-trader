"""Path measurements (Ch III.2.6).

A *path* is the ordered sequence of finalized bars after a reference
price.  This module measures it.  The distinctions it preserves are the
whole point of the chapter:

* **touch ≠ acceptance** (invariant #6) — an intrabar contact is a
  touch; acceptance requires a *close* at or beyond the level on the
  level's side.  The two are separate typed fields and never coerce
  into one another;
* **reach ≠ target-before-stop** (invariant #7) — the measurement
  retains the *ordered* sequence of realized deliveries.  It has no
  aggregate "won/lost", no expectancy and no risk-reward field: a path
  that reached a level and then went the other way is reported as
  exactly that, and nothing more;
* **terminal outcome ≠ ordered path** (invariant #8) — the first
  delivery is retained independently of the last close;
* **remaining distribution is never synthesized** (F7) — without a
  measured range the remaining distribution is explicitly
  ``UNRESOLVED``, never a zero and never a guess.

All distances are exact ``Decimal`` magnitudes in the instrument's own
native units.
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
    native_span,
    source_window_from_bars,
)
from .errors import (
    DataQualityBlockedError,
    MeasurementContractError,
    PathNotResolvableError,
)
from .ranges import RangeMeasurement

__all__ = [
    "AcceptanceState",
    "CloseBeyondState",
    "DeliveryObservation",
    "LevelOutcome",
    "LevelSide",
    "PathLevel",
    "PathMeasurement",
    "ReEntryState",
    "RejectionState",
    "RemainingState",
    "TouchState",
    "measure_path",
]


class TouchState(str, Enum):
    """Whether the path *touched* a declared level (intrabar contact)."""

    TOUCHED = "TOUCHED"
    NOT_TOUCHED = "NOT_TOUCHED"


class AcceptanceState(str, Enum):
    """Whether the path *accepted* a declared level (a close beyond it)."""

    ACCEPTED = "ACCEPTED"
    NOT_ACCEPTED = "NOT_ACCEPTED"


class CloseBeyondState(str, Enum):
    """Whether the terminal close of the path is beyond the level."""

    BEYOND = "BEYOND"
    NOT_BEYOND = "NOT_BEYOND"


class ReEntryState(str, Enum):
    """Whether the path returned to the origin side after closing beyond."""

    REENTERED = "REENTERED"
    NOT_REENTERED = "NOT_REENTERED"


class RejectionState(str, Enum):
    """Whether a touched level was later closed back on the origin side."""

    REJECTED = "REJECTED"
    NOT_REJECTED = "NOT_REJECTED"


class RemainingState(str, Enum):
    """Whether the remaining distribution is measured or unresolved."""

    MEASURED = "MEASURED"
    UNRESOLVED = "UNRESOLVED"


class LevelSide(str, Enum):
    """Which side of the reference price a level lies on."""

    ABOVE = "ABOVE"
    BELOW = "BELOW"


@dataclass(frozen=True)
class PathLevel:
    """One declared level the path is measured against."""

    level_id: str
    price: NativePrice
    side: LevelSide

    def __post_init__(self) -> None:
        if not self.level_id:
            raise MeasurementContractError("path level requires an id")

    def to_dict(self) -> dict:
        from .contracts import encode_value

        return encode_value(self)


@dataclass(frozen=True)
class DeliveryObservation:
    """One realized delivery, with the bar it was realized on and its order."""

    level_id: str
    bar_index: int
    realized_at: datetime
    order_index: int

    def to_dict(self) -> dict:
        from .contracts import encode_value

        return encode_value(self)


@dataclass(frozen=True)
class LevelOutcome:
    """The typed facts about one declared level over the path."""

    level_id: str
    touch_state: TouchState
    acceptance_state: AcceptanceState
    close_beyond_state: CloseBeyondState
    re_entry_state: ReEntryState
    rejection_state: RejectionState
    max_excursion: NativeMagnitude
    first_delivery: DeliveryObservation | None

    def to_dict(self) -> dict:
        from .contracts import encode_value

        return encode_value(self)


@dataclass(frozen=True)
class PathMeasurement(Measurement):
    """The measured path.

    The record carries no win, expectancy or risk-reward field: reach
    is not a trade result (invariant #7).
    """

    reference_price: NativePrice
    mae: NativeMagnitude
    mfe: NativeMagnitude
    levels: tuple[LevelOutcome, ...]
    first_delivery: DeliveryObservation | None
    delivery_order: tuple[DeliveryObservation, ...]
    remaining_state: RemainingState
    remaining_distribution: NativeMagnitude | None
    bar_count: int

    def to_dict(self) -> dict:
        from .contracts import encode_value

        return encode_value(self)


def _magnitude(
    instrument: Instrument, distance: Decimal
) -> NativeMagnitude:
    return native_span(
        instrument.instrument_id,
        instrument.native_unit,
        instrument.native_step,
        Decimal("0"),
        distance,
    )


def _beyond(level: PathLevel, value: Decimal) -> bool:
    if level.side is LevelSide.ABOVE:
        return value >= level.price.value
    return value <= level.price.value


def _origin_side(level: PathLevel, value: Decimal) -> bool:
    """Strictly back on the origin side of the level."""
    if level.side is LevelSide.ABOVE:
        return value < level.price.value
    return value > level.price.value


def measure_path(
    bars: Sequence[Bar],
    *,
    instrument: Instrument,
    provenance: Provenance,
    observation_cutoff: datetime,
    quality_policy: QualityPolicy,
    levels: Sequence[PathLevel] = (),
    reference_price: NativePrice | None = None,
    measured_range: RangeMeasurement | None = None,
    expected_opens: Sequence[datetime] | None = None,
    definition_version: str = "V1",
) -> PathMeasurement:
    """Measure a path over finalized bars.

    Only finalized bars contribute.  Incomplete input raises
    ``DATA_QUALITY_BLOCKED``; a path that cannot be resolved raises
    ``PATH_NOT_RESOLVABLE``.  Nothing is fabricated.
    """
    if not bars:
        raise PathNotResolvableError("no bars supplied")
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
    policy_outcome = quality_policy.evaluate(flags)
    if policy_outcome is DataOutcome.DATA_QUALITY_BLOCKED:
        raise DataQualityBlockedError(
            "declared quality policy blocks calculation: "
            + ", ".join(sorted(flag.value for flag in flags))
        )
    quality_state = (
        DataOutcome.DEGRADED
        if policy_outcome is DataOutcome.DEGRADED
        else selection.outcome
    )

    final_bars = selection.final_bars
    if not final_bars:
        raise PathNotResolvableError("no finalized bar in the measured path")

    reference = reference_price or NativePrice(
        instrument.instrument_id, instrument.native_unit, final_bars[0].open
    )

    highest = max(bar.high for bar in final_bars)
    lowest = min(bar.low for bar in final_bars)
    mae_distance = reference.value - lowest
    mfe_distance = highest - reference.value
    mae = _magnitude(instrument, mae_distance if mae_distance > 0 else Decimal("0"))
    mfe = _magnitude(instrument, mfe_distance if mfe_distance > 0 else Decimal("0"))

    outcomes: list[LevelOutcome] = []
    pending_deliveries: list[tuple[int, str, datetime]] = []
    for level in levels:
        touched = False
        accepted_at: int | None = None
        beyond_at: int | None = None
        reentered = False
        rejected = False
        for index, bar in enumerate(final_bars):
            if bar.low <= level.price.value <= bar.high:
                touched = True
            if _beyond(level, bar.close):
                if accepted_at is None:
                    accepted_at = index
                beyond_at = index
            elif accepted_at is not None and _origin_side(level, bar.close):
                reentered = True
            if touched and _origin_side(level, bar.close):
                rejected = True
        if level.side is LevelSide.ABOVE:
            excursion = highest - level.price.value
        else:
            excursion = level.price.value - lowest
        if excursion < 0:
            excursion = Decimal("0")
        if accepted_at is not None:
            pending_deliveries.append(
                (accepted_at, level.level_id, final_bars[accepted_at].close_time)
            )
        outcomes.append(
            LevelOutcome(
                level_id=level.level_id,
                touch_state=(
                    TouchState.TOUCHED if touched else TouchState.NOT_TOUCHED
                ),
                acceptance_state=(
                    AcceptanceState.ACCEPTED
                    if accepted_at is not None
                    else AcceptanceState.NOT_ACCEPTED
                ),
                close_beyond_state=(
                    CloseBeyondState.BEYOND
                    if beyond_at is not None
                    else CloseBeyondState.NOT_BEYOND
                ),
                re_entry_state=(
                    ReEntryState.REENTERED
                    if reentered
                    else ReEntryState.NOT_REENTERED
                ),
                rejection_state=(
                    RejectionState.REJECTED
                    if rejected
                    else RejectionState.NOT_REJECTED
                ),
                max_excursion=_magnitude(instrument, excursion),
                first_delivery=None,
            )
        )

    pending_deliveries.sort(key=lambda item: (item[0], item[1]))
    delivery_order: list[DeliveryObservation] = []
    for order_index, (bar_index, level_id, realized_at) in enumerate(pending_deliveries):
        delivery_order.append(
            DeliveryObservation(
                level_id=level_id,
                bar_index=bar_index,
                realized_at=realized_at,
                order_index=order_index,
            )
        )
    by_level = {item.level_id: item for item in delivery_order}
    outcomes = [
        LevelOutcome(
            level_id=outcome.level_id,
            touch_state=outcome.touch_state,
            acceptance_state=outcome.acceptance_state,
            close_beyond_state=outcome.close_beyond_state,
            re_entry_state=outcome.re_entry_state,
            rejection_state=outcome.rejection_state,
            max_excursion=outcome.max_excursion,
            first_delivery=by_level.get(outcome.level_id),
        )
        for outcome in outcomes
    ]
    first_delivery = delivery_order[0] if delivery_order else None

    if measured_range is not None:
        remaining_state = RemainingState.MEASURED
        remaining = measured_range.range_left
    else:
        remaining_state = RemainingState.UNRESOLVED
        remaining = None

    window = source_window_from_bars(final_bars)
    context = provenance.context(window, quality_state)
    return PathMeasurement(
        **envelope(
            context,
            "PATH_MEASUREMENT",
            definition_version=definition_version,
            native_unit=instrument.native_unit,
        ),
        reference_price=reference,
        mae=mae,
        mfe=mfe,
        levels=tuple(outcomes),
        first_delivery=first_delivery,
        delivery_order=tuple(delivery_order),
        remaining_state=remaining_state,
        remaining_distribution=remaining,
        bar_count=len(final_bars),
    )
