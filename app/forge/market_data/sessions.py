"""Versioned session registry and final-bar semantics (Ch III.1.5 + III.1.6).

``SessionDefinition`` values are bound to (model_id, model_version,
session_id): session definitions belong to model/calibration versions
and cross-version reuse fails closed to ``NO_CALCULATION``.  Definitions
are built only from canonical source records — the registry never
invents timing for a model whose canonical source does not define it,
and coverage of a family without a canonical definition is returned as a
disclosed gap (PLAN §10 G2).

Boundary semantics are exact: windows are half-open ``[start, end)``
unless ``end_inclusive`` is declared; checkpoint sessions match an exact
close instant (no invented duration).  The canonical M5 ``02:55`` final
bar of the 19:00-03:00 construction is computed from the session's UTC
end instant minus the timeframe, so DST days resolve correctly instead
of assuming a local 02:55 exists.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import date, datetime, time, timedelta
from enum import Enum
from typing import Iterable, Mapping, Sequence

from .clocks import ClockIdentity, session_bounds_utc
from .errors import (
    ConventionViolationError,
    DuplicateRegistrationError,
)
from .quality import DataOutcome  # noqa: F401  (outcome vocabulary shared)
from .versions import MARKET_DATA_SCHEMA_VERSION

SESSION_REGISTRY_VERSION = "SESSION_REGISTRY_V1"


class SessionFamily(str, Enum):
    """The frozen session-family list (E1)."""

    ASIAN_RANGE = "ASIAN_RANGE"
    LONDON_MLR = "LONDON_MLR"
    DAILY_CHECKPOINT = "DAILY_CHECKPOINT"
    WEEKLY_SEED = "WEEKLY_SEED"
    DT_WINDOW = "DT_WINDOW"
    MONTH_BOUNDARY = "MONTH_BOUNDARY"
    QUARTER_BOUNDARY = "QUARTER_BOUNDARY"


class SessionKind(str, Enum):
    WINDOW = "WINDOW"        # half-open window; end inclusive only when declared
    CHECKPOINT = "CHECKPOINT"  # exact close instant, no invented duration


class SessionStatus(str, Enum):
    RESOLVED = "RESOLVED"
    NO_CALCULATION = "NO_CALCULATION"


@dataclass(frozen=True)
class SessionDefinition:
    """One versioned session definition bound to a model/calibration version."""

    session_id: str
    family: SessionFamily
    model_id: str
    model_version: str
    kind: SessionKind
    clock: ClockIdentity
    source_ref: str
    start_local: time | None = None
    end_local: time | None = None
    end_inclusive: bool = False
    instant_local: time | None = None

    def __post_init__(self) -> None:
        if not self.session_id or not self.model_id or not self.model_version:
            raise ConventionViolationError("session key fields are required")
        if not self.source_ref:
            raise ConventionViolationError("canonical source_ref required")
        if self.kind is SessionKind.WINDOW:
            if self.start_local is None or self.end_local is None:
                raise ConventionViolationError("window requires start and end")
            if self.instant_local is not None:
                raise ConventionViolationError("window must not carry an instant")
        else:
            if self.instant_local is None:
                raise ConventionViolationError("checkpoint requires an instant")
            if self.start_local is not None or self.end_local is not None:
                raise ConventionViolationError("checkpoint must not carry a window")

    @property
    def registry_key(self) -> tuple[str, str, str]:
        return (self.model_id, self.model_version, self.session_id)

    def to_dict(self) -> dict:
        data = asdict(self)
        data["family"] = self.family.value
        data["kind"] = self.kind.value
        data["start_local"] = self.start_local.isoformat() if self.start_local else None
        data["end_local"] = self.end_local.isoformat() if self.end_local else None
        data["instant_local"] = (
            self.instant_local.isoformat() if self.instant_local else None
        )
        data["clock"] = self.clock.to_dict()
        data["market_data_schema_version"] = MARKET_DATA_SCHEMA_VERSION
        data["session_registry_version"] = SESSION_REGISTRY_VERSION
        return data


@dataclass(frozen=True)
class SessionResolution:
    """Explicit resolution result — unknown stays ``NO_CALCULATION``."""

    status: SessionStatus
    definition: SessionDefinition | None
    reason_code: str  # RESOLVED | UNKNOWN_SESSION | VERSION_MISMATCH | AMBIGUOUS
    session_registry_version: str = SESSION_REGISTRY_VERSION
    market_data_schema_version: str = MARKET_DATA_SCHEMA_VERSION

    @property
    def resolved(self) -> bool:
        return self.status is SessionStatus.RESOLVED

    @property
    def outcome(self) -> DataOutcome:
        """Resolution as a failure-behavior outcome (L2/E4)."""
        return DataOutcome.OK if self.resolved else DataOutcome.NO_CALCULATION

    def to_dict(self) -> dict:
        return {
            "status": self.status.value,
            "reason_code": self.reason_code,
            "definition": self.definition.to_dict() if self.definition else None,
            "session_registry_version": self.session_registry_version,
            "market_data_schema_version": self.market_data_schema_version,
        }


class SessionRegistry:
    """Versioned (model_id, model_version, session_id) -> definition."""

    def __init__(self, registry_version: str = SESSION_REGISTRY_VERSION) -> None:
        self.registry_version = registry_version
        self._definitions: dict[tuple[str, str, str], SessionDefinition] = {}

    def add(self, definition: SessionDefinition) -> None:
        if definition.registry_key in self._definitions:
            raise DuplicateRegistrationError(
                f"duplicate session {definition.registry_key}"
            )
        self._definitions[definition.registry_key] = definition

    def add_all(self, definitions: Iterable[SessionDefinition]) -> None:
        for definition in definitions:
            self.add(definition)

    def resolve(
        self, model_id: str, model_version: str, session_id: str
    ) -> SessionResolution:
        key = (model_id, model_version, session_id)
        definition = self._definitions.get(key)
        if definition is not None:
            return SessionResolution(
                status=SessionStatus.RESOLVED,
                definition=definition,
                reason_code="RESOLVED",
                session_registry_version=self.registry_version,
            )
        reason = "UNKNOWN_SESSION"
        for (m_id, _m_version, s_id), _defn in self._definitions.items():
            if m_id == model_id and s_id == session_id:
                reason = "VERSION_MISMATCH"
                break
        return SessionResolution(
            status=SessionStatus.NO_CALCULATION,
            definition=None,
            reason_code=reason,
            session_registry_version=self.registry_version,
        )

    def definitions_for(self, model_id: str, model_version: str) -> tuple[SessionDefinition, ...]:
        return tuple(
            sorted(
                (
                    defn
                    for (m_id, m_version, _s_id), defn in self._definitions.items()
                    if m_id == model_id and m_version == model_version
                ),
                key=lambda defn: defn.session_id,
            )
        )

    def coverage(self, documented_gaps: Mapping[SessionFamily, str] | None = None) -> dict[str, str]:
        """Status of every frozen family: DEFINED, or the disclosed gap.

        Families without a canonical definition never come back as
        defined — PLAN §10 gap G2 stays visible in the output itself.
        """
        defined = {defn.family for defn in self._definitions.values()}
        gaps = documented_gaps or {}
        result: dict[str, str] = {}
        for family in SessionFamily:
            if family in defined:
                result[family.value] = "DEFINED"
            elif family in gaps:
                result[family.value] = f"GAP: {gaps[family]}"
            else:
                result[family.value] = "GAP: no canonical definition recorded"
        return result


# ------------------------------------------------------------------
# Boundary helpers (III.1.6)
# ------------------------------------------------------------------


def local_open_in_session(definition: SessionDefinition, local_open: datetime) -> bool:
    """Membership of a bar's local *open* time in a window session.

    Half-open ``[start, end)`` by default; ``end_inclusive`` makes the
    end edge a member.  Windows crossing midnight match either segment.
    """
    if definition.kind is not SessionKind.WINDOW:
        raise ConventionViolationError("checkpoint membership uses close time")
    wall = local_open.time()
    start = definition.start_local
    end = definition.end_local
    assert start is not None and end is not None
    if end > start:
        if start <= wall < end:
            return True
        return definition.end_inclusive and wall == end
    # crosses midnight: [start, 24:00) or [00:00, end)
    if wall >= start:
        return True
    if wall < end:
        return True
    return definition.end_inclusive and wall == end


def close_matches_checkpoint(definition: SessionDefinition, local_close: datetime) -> bool:
    """A checkpoint matches exactly one wall time — no invented duration."""
    if definition.kind is not SessionKind.CHECKPOINT:
        raise ConventionViolationError("window sessions use open membership")
    assert definition.instant_local is not None
    return local_close.time() == definition.instant_local


def final_bar_open_utc(
    definition: SessionDefinition,
    timeframe: timedelta,
    on_day: date,
    *,
    fold: int = 0,
) -> datetime:
    """UTC open instant of the final bar of a window session on ``on_day``.

    Computed as session end instant minus the timeframe, i.e. the last
    bar that *opens* before the session closes.  For the canonical
    19:00-03:00 M5 construction this is local ``02:55`` on ordinary days;
    on a DST spring-forward day the local ``02:55`` wall label does not
    exist and the instant still resolves correctly (III.1.6, K1).
    """
    if definition.kind is not SessionKind.WINDOW:
        raise ConventionViolationError("checkpoints have no final bar")
    assert definition.start_local is not None and definition.end_local is not None
    _start_u, end_u = session_bounds_utc(
        on_day, definition.start_local, definition.end_local, definition.clock, fold=fold
    )
    return end_u - timeframe


def definitions_from_records(
    records: Sequence[Mapping[str, object]],
    clocks: Mapping[str, ClockIdentity],
) -> tuple[SessionDefinition, ...]:
    """Build definitions from canonical-source fixture records.

    Each record must name its clock by id (looked up, never defaulted)
    and carry a canonical ``source_ref``.
    """
    definitions: list[SessionDefinition] = []
    for record in records:
        clock_id = str(record["clock"])
        if clock_id not in clocks:
            raise ConventionViolationError(f"session record names unknown clock {clock_id}")
        start = record.get("start_local")
        end = record.get("end_local")
        instant = record.get("instant_local")
        definitions.append(
            SessionDefinition(
                session_id=str(record["session_id"]),
                family=SessionFamily(str(record["family"])),
                model_id=str(record["model_id"]),
                model_version=str(record["model_version"]),
                kind=SessionKind(str(record["kind"])),
                clock=clocks[clock_id],
                source_ref=str(record["source_ref"]),
                start_local=time.fromisoformat(str(start)) if start else None,
                end_local=time.fromisoformat(str(end)) if end else None,
                end_inclusive=bool(record.get("end_inclusive", False)),
                instant_local=time.fromisoformat(str(instant)) if instant else None,
            )
        )
    return tuple(definitions)
