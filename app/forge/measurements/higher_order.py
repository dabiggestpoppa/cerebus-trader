"""Higher-order measurements (Ch III.2.8).

The canonical higher-order hierarchy is::

    Quarter seed -> M1 range seed -> M2 shaping -> M3 resolution
                 -> Weekly local path -> Daily execution

This module measures the *structure* of that hierarchy and nothing
more.  Two laws apply throughout:

* **Evidence-bound definitions (III.2-GAP-6).**  The exact
  definitions of the D3 prior, the unfinished side and the M3
  completion state "must travel with evidence" (EUR Higher Order
  model card).  Those statistical parameters are therefore *referenced
  by evidence id* and never hardcoded as engine constants: this module
  emits no percentage, no correlation coefficient and no prior.
* **No confluence score (invariant / M6).**  When layers disagree the
  output is a *conflict fact* — which layers disagree and how.  The
  record has no score, no weight, no confidence and no aggregate
  number, and it is structurally incapable of emitting one.

Where a canonical definition is missing, the container says so
explicitly (``UNRESOLVED``) instead of substituting a default.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
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

from .calibration import CalibrationStatus
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
)

__all__ = [
    "D1D3State",
    "HigherOrderCheckpoint",
    "HigherOrderLayer",
    "HigherOrderState",
    "LayerConflict",
    "LayerConflictFact",
    "LayerConflictKind",
    "M1Scale",
    "M2Shaping",
    "SeedRange",
    "SeedRangeKind",
    "UnfinishedSide",
    "UnfinishedSideState",
    "WeeklyNode",
    "WeeklyOuterNode",
    "WeeklyPath",
    "measure_d1d3_state",
    "measure_higher_order_checkpoint",
    "measure_layer_conflict",
    "measure_m1_scale",
    "measure_m2_shaping",
    "measure_seed_range",
    "measure_unfinished_side",
    "measure_weekly_path",
]


class SeedRangeKind(str, Enum):
    """The seed window a seed range was measured over."""

    MONTH = "MONTH"
    QUARTER = "QUARTER"
    WEEK = "WEEK"
    QUARTER_DAY = "QUARTER_DAY"


class HigherOrderState(str, Enum):
    """Availability of a higher-order measurement.

    ``MEASURED`` — the declared inputs were measured.
    ``UNRESOLVED`` — the canonical definition is not materialized, so
    only the explicit absence is reported.
    """

    MEASURED = "MEASURED"
    UNRESOLVED = "UNRESOLVED"


class UnfinishedSideState(str, Enum):
    """Which side of the higher-order hierarchy is unfinished."""

    UNRESOLVED = "UNRESOLVED"
    UPPER = "UPPER"
    LOWER = "LOWER"


class HigherOrderLayer(str, Enum):
    """The bounded layer vocabulary used by conflict facts."""

    QUARTER = "QUARTER"
    MONTH_1 = "MONTH_1"
    MONTH_2 = "MONTH_2"
    MONTH_3 = "MONTH_3"
    WEEK = "WEEK"
    DAY = "DAY"


class LayerConflictKind(str, Enum):
    """The bounded kinds of layer disagreement."""

    DIRECTION_DISAGREEMENT = "DIRECTION_DISAGREEMENT"
    MAGNITUDE_DISAGREEMENT = "MAGNITUDE_DISAGREEMENT"
    TIMING_DISAGREEMENT = "TIMING_DISAGREEMENT"
    COMPLETION_DISAGREEMENT = "COMPLETION_DISAGREEMENT"


@dataclass(frozen=True)
class SeedRange(Measurement):
    """The measured high/low/size of one seed window."""

    seed_kind: SeedRangeKind
    high: NativePrice
    low: NativePrice
    size: NativeMagnitude
    bar_count: int

    def to_dict(self) -> dict:
        from .contracts import encode_value

        return encode_value(self)


@dataclass(frozen=True)
class D1D3State(Measurement):
    """The D1-D3 quarter-day seed structure.

    The *directional prior* the scientific review recovered for D3 is a
    model-level interpretation carried by an evidence card; it is
    deliberately absent here — this record holds the measured quarter
    seed and the measured first three day seeds, nothing statistical.
    """

    quarter_seed: SeedRange | None
    d1: SeedRange | None
    d2: SeedRange | None
    d3: SeedRange | None
    state: HigherOrderState

    def to_dict(self) -> dict:
        from .contracts import encode_value

        return encode_value(self)


@dataclass(frozen=True)
class M1Scale(Measurement):
    """The Month-1 seed range used as the higher-order scale feature.

    The recovered correlation (r) is a statistical parameter of an
    evidence card; it is referenced by evidence id and never hardcoded
    as an engine constant.
    """

    m1_seed: SeedRange | None
    scale: NativeMagnitude | None
    state: HigherOrderState

    def to_dict(self) -> dict:
        from .contracts import encode_value

        return encode_value(self)


@dataclass(frozen=True)
class M2Shaping(Measurement):
    """The Month-2 shaping state.

    The M2 shaping *definition* is evidence-bound and not materialized
    in the corpus, so the record reports the measured Month-2 seed and
    an explicit availability state — never an invented shaping rule.
    """

    m2_seed: SeedRange | None
    state: HigherOrderState

    def to_dict(self) -> dict:
        from .contracts import encode_value

        return encode_value(self)


@dataclass(frozen=True)
class UnfinishedSide(Measurement):
    """The unfinished side of the higher-order hierarchy.

    The side is a declared structural fact; the completion association
    (historical / forward-OOS) lives in its evidence card and is never
    attached here.
    """

    side: UnfinishedSideState
    state: HigherOrderState

    def to_dict(self) -> dict:
        from .contracts import encode_value

        return encode_value(self)


@dataclass(frozen=True)
class WeeklyOuterNode:
    """One weekly outer node, carrying its research standing."""

    node_id: str
    order_index: int
    magnitude: NativeMagnitude
    sample_n: int
    source_ref: str
    calibration_status: CalibrationStatus

    def to_dict(self) -> dict:
        from .contracts import encode_value

        return encode_value(self)


@dataclass(frozen=True)
class WeeklyPath(Measurement):
    """The measured weekly seed and its ordered outer nodes."""

    weekly_seed: SeedRange | None
    nodes: tuple[WeeklyOuterNode, ...]
    calibration_status: CalibrationStatus | None
    state: HigherOrderState

    def to_dict(self) -> dict:
        from .contracts import encode_value

        return encode_value(self)


@dataclass(frozen=True)
class HigherOrderCheckpoint(Measurement):
    """Whether a declared higher-order checkpoint instant was reached."""

    checkpoint_id: str
    scheduled_instant: datetime
    observed_instant: datetime
    reached: bool
    source_ref: str

    def to_dict(self) -> dict:
        from .contracts import encode_value

        return encode_value(self)


@dataclass(frozen=True)
class LayerConflictFact:
    """One bounded disagreement between two layers."""

    layer_a: HigherOrderLayer
    layer_b: HigherOrderLayer
    kind: LayerConflictKind

    def to_dict(self) -> dict:
        from .contracts import encode_value

        return encode_value(self)


@dataclass(frozen=True)
class LayerConflict(Measurement):
    """The conflict facts between layers.

    The record has no score, no weight and no confidence field: a
    higher/lower layer disagreement is reported as a fact, never
    collapsed into an invented confluence number.
    """

    conflicts: tuple[LayerConflictFact, ...]
    state: HigherOrderState

    def to_dict(self) -> dict:
        from .contracts import encode_value

        return encode_value(self)


def _finalize(
    bars: Sequence[Bar],
    observation_cutoff: datetime,
    expected_opens: Sequence[datetime] | None,
) -> tuple[tuple[Bar, ...], DataOutcome]:
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
    return selection.final_bars, selection.outcome


def measure_seed_range(
    bars: Sequence[Bar],
    *,
    seed_kind: SeedRangeKind,
    instrument: Instrument,
    provenance: Provenance,
    observation_cutoff: datetime,
    quality_policy: QualityPolicy,
    expected_opens: Sequence[datetime] | None = None,
    definition_version: str = "V1",
) -> SeedRange:
    """Measure one seed window's range over finalized bars."""
    if not bars:
        raise MeasurementContractError("a seed range needs at least one bar")
    final_bars, outcome = _finalize(bars, observation_cutoff, expected_opens)
    policy_outcome = quality_policy.evaluate(
        flag for bar in final_bars for flag in bar.quality_flags
    )
    if policy_outcome is DataOutcome.DATA_QUALITY_BLOCKED:
        raise DataQualityBlockedError(
            "declared quality policy blocks calculation"
        )
    quality_state = (
        DataOutcome.DEGRADED
        if policy_outcome is DataOutcome.DEGRADED
        else outcome
    )

    high = max(bar.high for bar in final_bars)
    low = min(bar.low for bar in final_bars)
    if high < low:
        raise MeasurementContractError("seed range high is below seed range low")
    size = native_span(
        instrument.instrument_id,
        instrument.native_unit,
        instrument.native_step,
        low,
        high,
    )
    definition_id = (
        "HO_WEEKLY_SEED" if seed_kind is SeedRangeKind.WEEK else "HO_SEED_RANGE"
    )
    window = source_window_from_bars(final_bars)
    context = provenance.context(window, quality_state)
    return SeedRange(
        **envelope(
            context,
            definition_id,
            definition_version=definition_version,
            native_unit=instrument.native_unit,
        ),
        seed_kind=seed_kind,
        high=NativePrice(instrument.instrument_id, instrument.native_unit, high),
        low=NativePrice(instrument.instrument_id, instrument.native_unit, low),
        size=size,
        bar_count=len(final_bars),
    )


def measure_d1d3_state(
    *,
    quarter_seed: SeedRange | None,
    d1: SeedRange | None,
    d2: SeedRange | None,
    d3: SeedRange | None,
    provenance: Provenance,
    source_window,
    definition_version: str = "V1",
) -> D1D3State:
    """Container for the D1-D3 quarter-day seed structure."""
    state = (
        HigherOrderState.MEASURED
        if any(seed is not None for seed in (quarter_seed, d1, d2, d3))
        else HigherOrderState.UNRESOLVED
    )
    context = provenance.context(source_window)
    return D1D3State(
        **envelope(context, "HO_D1D3_STATE", definition_version=definition_version),
        quarter_seed=quarter_seed,
        d1=d1,
        d2=d2,
        d3=d3,
        state=state,
    )


def measure_m1_scale(
    *,
    m1_seed: SeedRange | None,
    provenance: Provenance,
    source_window,
    definition_version: str = "V1",
) -> M1Scale:
    """Container for the Month-1 scale feature."""
    state = (
        HigherOrderState.MEASURED
        if m1_seed is not None
        else HigherOrderState.UNRESOLVED
    )
    context = provenance.context(source_window)
    return M1Scale(
        **envelope(context, "HO_M1_SCALE", definition_version=definition_version),
        m1_seed=m1_seed,
        scale=m1_seed.size if m1_seed is not None else None,
        state=state,
    )


def measure_m2_shaping(
    *,
    m2_seed: SeedRange | None,
    provenance: Provenance,
    source_window,
    definition_version: str = "V1",
) -> M2Shaping:
    """Container for the Month-2 shaping state."""
    state = (
        HigherOrderState.MEASURED
        if m2_seed is not None
        else HigherOrderState.UNRESOLVED
    )
    context = provenance.context(source_window)
    return M2Shaping(
        **envelope(context, "HO_M2_SHAPING", definition_version=definition_version),
        m2_seed=m2_seed,
        state=state,
    )


def measure_unfinished_side(
    *,
    side: UnfinishedSideState,
    provenance: Provenance,
    source_window,
    definition_version: str = "V1",
) -> UnfinishedSide:
    """Container for the unfinished side of the hierarchy."""
    state = (
        HigherOrderState.MEASURED
        if side is not UnfinishedSideState.UNRESOLVED
        else HigherOrderState.UNRESOLVED
    )
    context = provenance.context(source_window)
    return UnfinishedSide(
        **envelope(
            context, "HO_UNFINISHED_SIDE", definition_version=definition_version
        ),
        side=side,
        state=state,
    )


def measure_weekly_path(
    *,
    weekly_seed: SeedRange | None,
    nodes: Sequence[WeeklyOuterNode] = (),
    provenance: Provenance,
    source_window,
    definition_version: str = "V1",
) -> WeeklyPath:
    """Container for the weekly seed and its ordered outer nodes."""
    ordered = tuple(sorted(nodes, key=lambda node: node.order_index))
    status: CalibrationStatus | None = None
    if ordered:
        statuses = {node.calibration_status for node in ordered}
        if len(statuses) > 1:
            raise MeasurementContractError(
                "weekly outer nodes must carry one calibration status"
            )
        status = statuses.pop()
    state = (
        HigherOrderState.MEASURED
        if weekly_seed is not None or ordered
        else HigherOrderState.UNRESOLVED
    )
    context = provenance.context(source_window)
    return WeeklyPath(
        **envelope(context, "HO_WEEKLY_PATH", definition_version=definition_version),
        weekly_seed=weekly_seed,
        nodes=ordered,
        calibration_status=status,
        state=state,
    )


def measure_higher_order_checkpoint(
    *,
    checkpoint_id: str,
    scheduled_instant: datetime,
    observed_instant: datetime,
    source_ref: str,
    provenance: Provenance,
    definition_version: str = "V1",
) -> HigherOrderCheckpoint:
    """Measure whether a declared higher-order checkpoint was reached."""
    from .contracts import source_window_from_instants

    if not checkpoint_id:
        raise MeasurementContractError("a checkpoint requires an id")
    if not source_ref:
        raise MeasurementContractError("a checkpoint requires a source ref")
    window = source_window_from_instants((scheduled_instant, observed_instant))
    context = provenance.context(window)
    return HigherOrderCheckpoint(
        **envelope(context, "HO_CHECKPOINT", definition_version=definition_version),
        checkpoint_id=checkpoint_id,
        scheduled_instant=scheduled_instant,
        observed_instant=observed_instant,
        reached=observed_instant >= scheduled_instant,
        source_ref=source_ref,
    )


def measure_layer_conflict(
    *,
    conflicts: Sequence[LayerConflictFact],
    provenance: Provenance,
    source_window,
    definition_version: str = "V1",
) -> LayerConflict:
    """Container for the conflict facts between layers.

    Deliberately carries no score: the record states *that* layers
    disagree and *how*, never a combined number.
    """
    context = provenance.context(source_window)
    return LayerConflict(
        **envelope(context, "HO_LAYER_CONFLICT", definition_version=definition_version),
        conflicts=tuple(conflicts),
        state=(
            HigherOrderState.MEASURED
            if conflicts
            else HigherOrderState.UNRESOLVED
        ),
    )
