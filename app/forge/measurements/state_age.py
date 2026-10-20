"""Clock / state-age measurements (Ch III.2.5).

Time **weights** state; it never manufactures it (invariant #5).  Every
function here measures an elapsed fact against an *injected* instant
pair — there is no wall clock, no scheduling and no price semantics
anywhere in this module.

The vocabulary is the frozen Book III failure behaviour:

* a clock or session that cannot be resolved -> ``NO_CALCULATION``
  (never an empty success);
* time-to-delivery is the distance to a **scheduled** canonical
  boundary — a schedule distance, not a forecast of price or delivery;
* session and calendar-period phase derive from the III.1 session and
  research-day contracts, never from an invented schedule.

Durations are exact ``Decimal`` seconds, so a value is reproducible
byte-for-byte across platforms.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal
from enum import Enum
from typing import Sequence

from app.forge.market_data import (
    ResearchDayRegistry,
    SessionDefinition,
    SessionKind,
    SessionRegistry,
    assign_research_day,
    close_matches_checkpoint,
    local_open_in_session,
    local_wall,
)

from .contracts import (
    Measurement,
    Provenance,
    envelope,
    source_window_from_instants,
)
from .errors import (
    MeasurementContractError,
    NoCalculationError,
)

__all__ = [
    "AcceptanceDuration",
    "CheckpointReached",
    "CheckpointState",
    "ElapsedSinceEvent",
    "FailureAge",
    "PeriodKind",
    "PeriodPhase",
    "ScheduleState",
    "SessionPhase",
    "SessionPhaseState",
    "TimeToDelivery",
    "checkpoint_reached",
    "duration_seconds",
    "elapsed_since",
    "failure_age",
    "measure_acceptance_duration",
    "measure_period_phase",
    "measure_session_phase",
    "time_to_delivery",
]


def _require_aware(value: datetime, label: str) -> datetime:
    if not isinstance(value, datetime):
        raise MeasurementContractError(f"{label} must be a datetime")
    if value.tzinfo is None:
        raise MeasurementContractError(f"{label} must be tz-aware")
    return value.astimezone(timezone.utc)


def duration_seconds(start: datetime, end: datetime) -> Decimal:
    """Exact elapsed seconds between two aware instants.

    The result is a ``Decimal`` number of seconds; a negative span
    (end before start) is refused rather than signed silently, because
    an elapsed duration is never negative.
    """
    start = _require_aware(start, "start instant")
    end = _require_aware(end, "end instant")
    delta = end - start
    if delta.total_seconds() < 0:
        raise MeasurementContractError("an elapsed duration must not be negative")
    return Decimal(str(delta.total_seconds()))


class CheckpointState(str, Enum):
    """Whether a scheduled checkpoint instant has been reached."""

    REACHED = "REACHED"
    NOT_REACHED = "NOT_REACHED"


class ScheduleState(str, Enum):
    """Whether a scheduled boundary is still ahead of the observation."""

    PENDING = "PENDING"
    ELAPSED = "ELAPSED"


class SessionPhaseState(str, Enum):
    """Factual membership of an instant in a canonical session."""

    INSIDE_WINDOW = "INSIDE_WINDOW"
    OUTSIDE_WINDOW = "OUTSIDE_WINDOW"
    CHECKPOINT_MATCHED = "CHECKPOINT_MATCHED"
    CHECKPOINT_NOT_MATCHED = "CHECKPOINT_NOT_MATCHED"


class PeriodKind(str, Enum):
    """The calendar period a phase is measured over."""

    WEEK = "WEEK"
    MONTH = "MONTH"


@dataclass(frozen=True)
class ElapsedSinceEvent(Measurement):
    """Elapsed time since a declared event instant."""

    event_instant: datetime
    observed_instant: datetime
    elapsed_seconds: Decimal

    def to_dict(self) -> dict:
        from .contracts import encode_value

        return encode_value(self)


@dataclass(frozen=True)
class CheckpointReached(Measurement):
    """Whether a scheduled checkpoint instant has been reached."""

    scheduled_instant: datetime
    observed_instant: datetime
    state: CheckpointState

    def to_dict(self) -> dict:
        from .contracts import encode_value

        return encode_value(self)


@dataclass(frozen=True)
class AcceptanceDuration(Measurement):
    """Elapsed duration of a declared acceptance."""

    acceptance_start: datetime
    acceptance_end: datetime
    duration_seconds: Decimal

    def to_dict(self) -> dict:
        from .contracts import encode_value

        return encode_value(self)


@dataclass(frozen=True)
class FailureAge(Measurement):
    """Age of a declared failure."""

    failure_instant: datetime
    observed_instant: datetime
    age_seconds: Decimal

    def to_dict(self) -> dict:
        from .contracts import encode_value

        return encode_value(self)


@dataclass(frozen=True)
class TimeToDelivery(Measurement):
    """Distance to a *scheduled* canonical boundary.

    A schedule distance only: it carries no price, no direction and no
    delivery forecast.
    """

    scheduled_boundary: datetime
    observed_instant: datetime
    remaining_seconds: Decimal
    state: ScheduleState

    def to_dict(self) -> dict:
        from .contracts import encode_value

        return encode_value(self)


@dataclass(frozen=True)
class SessionPhase(Measurement):
    """Membership of an instant in a canonical session."""

    session_id: str
    model_id: str
    model_version: str
    observed_instant: datetime
    state: SessionPhaseState

    def to_dict(self) -> dict:
        from .contracts import encode_value

        return encode_value(self)


@dataclass(frozen=True)
class PeriodPhase(Measurement):
    """The calendar period containing the III.1-resolved research day."""

    lineage_id: str
    period_kind: PeriodKind
    research_day: str
    period_label: str
    period_index: int

    def to_dict(self) -> dict:
        from .contracts import encode_value

        return encode_value(self)


def _temporal_context(
    provenance: Provenance, instants: Sequence[datetime]
):
    window = source_window_from_instants(instants)
    return provenance.context(window)


def elapsed_since(
    event_instant: datetime,
    observed_instant: datetime,
    *,
    provenance: Provenance,
    definition_version: str = "V1",
) -> ElapsedSinceEvent:
    """Measure the elapsed time since a declared event."""
    event_instant = _require_aware(event_instant, "event instant")
    observed_instant = _require_aware(observed_instant, "observed instant")
    elapsed = duration_seconds(event_instant, observed_instant)
    context = _temporal_context(provenance, (event_instant, observed_instant))
    return ElapsedSinceEvent(
        **envelope(context, "ELAPSED_SINCE_EVENT", definition_version=definition_version),
        event_instant=event_instant,
        observed_instant=observed_instant,
        elapsed_seconds=elapsed,
    )


def checkpoint_reached(
    scheduled_instant: datetime,
    observed_instant: datetime,
    *,
    provenance: Provenance,
    definition_version: str = "V1",
) -> CheckpointReached:
    """Measure whether a scheduled checkpoint has been reached."""
    scheduled_instant = _require_aware(scheduled_instant, "scheduled instant")
    observed_instant = _require_aware(observed_instant, "observed instant")
    state = (
        CheckpointState.REACHED
        if observed_instant >= scheduled_instant
        else CheckpointState.NOT_REACHED
    )
    context = _temporal_context(provenance, (scheduled_instant, observed_instant))
    return CheckpointReached(
        **envelope(context, "CHECKPOINT_REACHED", definition_version=definition_version),
        scheduled_instant=scheduled_instant,
        observed_instant=observed_instant,
        state=state,
    )


def measure_acceptance_duration(
    acceptance_start: datetime,
    acceptance_end: datetime,
    *,
    provenance: Provenance,
    definition_version: str = "V1",
) -> AcceptanceDuration:
    """Measure the duration of a declared acceptance."""
    acceptance_start = _require_aware(acceptance_start, "acceptance start")
    acceptance_end = _require_aware(acceptance_end, "acceptance end")
    duration = duration_seconds(acceptance_start, acceptance_end)
    context = _temporal_context(provenance, (acceptance_start, acceptance_end))
    return AcceptanceDuration(
        **envelope(
            context, "ACCEPTANCE_DURATION", definition_version=definition_version
        ),
        acceptance_start=acceptance_start,
        acceptance_end=acceptance_end,
        duration_seconds=duration,
    )


def failure_age(
    failure_instant: datetime,
    observed_instant: datetime,
    *,
    provenance: Provenance,
    definition_version: str = "V1",
) -> FailureAge:
    """Measure the age of a declared failure."""
    failure_instant = _require_aware(failure_instant, "failure instant")
    observed_instant = _require_aware(observed_instant, "observed instant")
    age = duration_seconds(failure_instant, observed_instant)
    context = _temporal_context(provenance, (failure_instant, observed_instant))
    return FailureAge(
        **envelope(context, "FAILURE_AGE", definition_version=definition_version),
        failure_instant=failure_instant,
        observed_instant=observed_instant,
        age_seconds=age,
    )


def time_to_delivery(
    scheduled_boundary: datetime,
    observed_instant: datetime,
    *,
    provenance: Provenance,
    definition_version: str = "V1",
) -> TimeToDelivery:
    """Measure the distance to a *scheduled* canonical boundary.

    The boundary is a schedule fact (a session edge, a declared
    checkpoint).  The measurement is the remaining schedule distance; it
    says nothing about price, direction or delivery.
    """
    scheduled_boundary = _require_aware(scheduled_boundary, "scheduled boundary")
    observed_instant = _require_aware(observed_instant, "observed instant")
    if scheduled_boundary >= observed_instant:
        remaining = duration_seconds(observed_instant, scheduled_boundary)
        state = ScheduleState.PENDING
    else:
        remaining = duration_seconds(scheduled_boundary, observed_instant)
        state = ScheduleState.ELAPSED
    context = _temporal_context(
        provenance, (scheduled_boundary, observed_instant)
    )
    return TimeToDelivery(
        **envelope(context, "TIME_TO_DELIVERY", definition_version=definition_version),
        scheduled_boundary=scheduled_boundary,
        observed_instant=observed_instant,
        remaining_seconds=remaining,
        state=state,
    )


def _phase_state(
    definition: SessionDefinition, instant: datetime
) -> SessionPhaseState:
    wall = local_wall(instant, definition.clock)
    if definition.kind is SessionKind.WINDOW:
        inside = local_open_in_session(definition, wall)
        return (
            SessionPhaseState.INSIDE_WINDOW
            if inside
            else SessionPhaseState.OUTSIDE_WINDOW
        )
    matched = close_matches_checkpoint(definition, wall)
    return (
        SessionPhaseState.CHECKPOINT_MATCHED
        if matched
        else SessionPhaseState.CHECKPOINT_NOT_MATCHED
    )


def measure_session_phase(
    registry: SessionRegistry,
    model_id: str,
    model_version: str,
    session_id: str,
    instant: datetime,
    *,
    provenance: Provenance,
    definition_version: str = "V1",
) -> SessionPhase:
    """Measure the phase of an instant inside a canonical session.

    An unresolvable session refuses with ``NO_CALCULATION`` — it never
    returns an empty success, and it never invents a window.
    """
    instant = _require_aware(instant, "observed instant")
    resolution = registry.resolve(model_id, model_version, session_id)
    if not resolution.resolved or resolution.definition is None:
        raise NoCalculationError(
            f"session {model_id}/{model_version}/{session_id} unresolved: "
            f"{resolution.reason_code}"
        )
    definition = resolution.definition
    state = _phase_state(definition, instant)
    context = _temporal_context(provenance, (instant,))
    payload = envelope(
        context, "SESSION_PHASE", definition_version=definition_version
    )
    # The measured session identity overrides the envelope's provenance
    # session: this record reports the phase *of that session*.
    payload["session_id"] = session_id
    return SessionPhase(
        **payload,
        model_id=model_id,
        model_version=model_version,
        observed_instant=instant,
        state=state,
    )


def measure_period_phase(
    research_days: ResearchDayRegistry,
    lineage_id: str,
    instrument_id: str,
    close_time_utc: datetime,
    period_kind: PeriodKind,
    *,
    provenance: Provenance,
    definition_version: str = "V1",
) -> PeriodPhase:
    """Measure the calendar period containing the resolved research day.

    The research day comes from the III.1 lineage rule (never a
    calendar-date guess); the week/month that contains it is a
    structural period label.  A lineage that cannot be resolved refuses
    with ``NO_CALCULATION``.

    Note: weekly *seed window* timing has no canonical definition
    (III.1 GAP-2) — this measurement therefore labels the period, and
    never invents seed-session bounds.
    """
    close_time_utc = _require_aware(close_time_utc, "close time")
    assignment = assign_research_day(
        research_days, lineage_id, instrument_id, close_time_utc
    )
    if not assignment.resolved or assignment.research_day is None:
        raise NoCalculationError(
            f"research day unresolved for lineage {lineage_id!r}"
        )
    day = assignment.research_day
    if period_kind is PeriodKind.WEEK:
        iso_year, iso_week, _ = day.isocalendar()
        label = f"{iso_year}-W{iso_week:02d}"
        index = iso_week
    else:
        label = f"{day.year}-{day.month:02d}"
        index = day.month
    context = _temporal_context(provenance, (close_time_utc,))
    return PeriodPhase(
        **envelope(context, "PERIOD_PHASE", definition_version=definition_version),
        lineage_id=lineage_id,
        period_kind=period_kind,
        research_day=day.isoformat(),
        period_label=label,
        period_index=index,
    )
