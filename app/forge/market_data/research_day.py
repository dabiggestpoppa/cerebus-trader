"""Explicit research-day ownership (Ch III.1.4).

A research day is never a calendar-date derivation.  It is a pure
function of (lineage, bar close time) evaluated through the lineage's
clock identity, where the lineage itself declares — from its canonical
source — whether evening bars belong to the following research day.

Known EUR/BTC lineage: bars *closing after* the 19:00 NY boundary of a
calendar date belong to the *following* research day (the 19:00-03:00
construction is one research day labelled by its morning date), because
the canonical sources establish that rule (EUR daily Phase1 calibration
evidence; BTC tracker model card).  A bar closing exactly at 19:00:00
has content entirely before the boundary and stays on its calendar
date.

Any lineage not registered — or registered without a boundary — is
reported as ``UNRESOLVED`` with no day value: no default calendar guess
is ever substituted (D5).
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, time, timedelta
from enum import Enum

from .clocks import ClockIdentity, local_wall
from .errors import DuplicateRegistrationError
from .versions import MARKET_DATA_SCHEMA_VERSION


class ResearchDayStatus(str, Enum):
    """Explicit ownership states — resolved or fail-closed unresolved."""

    RESOLVED = "RESOLVED"
    UNRESOLVED = "UNRESOLVED"


@dataclass(frozen=True)
class ResearchDayLineage:
    """A lineage's research-day rule, bound to its model/calibration version.

    ``evening_shift_boundary`` is the local wall time after which a bar
    close belongs to the following research day; ``None`` means the
    canonical source states same-day ownership with no shift.
    """

    lineage_id: str
    model_id: str
    model_version: str
    clock: ClockIdentity
    evening_shift_boundary: time | None
    source_ref: str


@dataclass(frozen=True)
class ResearchDayAssignment:
    """Outcome of an explicit assignment — never an inferred date."""

    status: ResearchDayStatus
    lineage_id: str
    instrument_id: str
    research_day: date | None
    clock_identity: ClockIdentity | None
    source_ref: str | None
    market_data_schema_version: str = MARKET_DATA_SCHEMA_VERSION

    @property
    def resolved(self) -> bool:
        return self.status is ResearchDayStatus.RESOLVED


class ResearchDayRegistry:
    """Registry of lineage-declared research-day rules."""

    def __init__(self) -> None:
        self._lineages: dict[str, ResearchDayLineage] = {}

    def register(self, lineage: ResearchDayLineage) -> None:
        if lineage.lineage_id in self._lineages:
            raise DuplicateRegistrationError(
                f"duplicate research-day lineage {lineage.lineage_id}"
            )
        self._lineages[lineage.lineage_id] = lineage

    def get(self, lineage_id: str) -> ResearchDayLineage | None:
        return self._lineages.get(lineage_id)

    @property
    def lineage_ids(self) -> tuple[str, ...]:
        return tuple(sorted(self._lineages))


def assign_research_day(
    registry: ResearchDayRegistry,
    lineage_id: str,
    instrument_id: str,
    close_time_utc: datetime,
) -> ResearchDayAssignment:
    """Explicit (lineage, bar close time) -> research-day assignment.

    Pure and deterministic: identical inputs yield the identical day.
    Unknown lineage, or a close time that is not tz-aware, yields the
    explicit ``UNRESOLVED`` state — never a calendar-date guess.
    """
    lineage = registry.get(lineage_id)
    if lineage is None:
        return ResearchDayAssignment(
            status=ResearchDayStatus.UNRESOLVED,
            lineage_id=lineage_id,
            instrument_id=instrument_id,
            research_day=None,
            clock_identity=None,
            source_ref=None,
        )
    local_close = local_wall(close_time_utc, lineage.clock)
    day = local_close.date()
    if (
        lineage.evening_shift_boundary is not None
        and local_close.time() > lineage.evening_shift_boundary
    ):
        day = day + timedelta(days=1)
    return ResearchDayAssignment(
        status=ResearchDayStatus.RESOLVED,
        lineage_id=lineage.lineage_id,
        instrument_id=instrument_id,
        research_day=day,
        clock_identity=lineage.clock,
        source_ref=lineage.source_ref,
    )
