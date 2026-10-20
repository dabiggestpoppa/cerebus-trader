"""Event / news features (Ch III.2.7).

A *normalized event* is a record of one official event: its family, the
currencies and assets it is relevant to, its scheduled and (optional)
actual instants, and — where a canonical source provides them — its
historical band and size.

Discipline:

* **Absence is disclosed, never defaulted.**  A missing historical
  band or size is ``None`` with an explicit ``*_declared`` flag; it is
  never a zero and never a silently substituted number;
* **The budget is subtractive.**  Canonical EUR event doctrine: already
  consumed movement changes what remains available.  The residual
  budget is ``total - consumed``, clamped at zero, and the consumed
  amount is supplied by the measured path — the event never invents it;
* **News conditions geometry; it never replaces it** (invariant #17).
  Nothing in this module emits a level, a range, a coordinate or a
  direction.  There is no event history in the repository (III.2-GAP-4),
  so events are supplied by the caller over synthetic, labeled data.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import Sequence

from .contracts import (
    Measurement,
    NativeMagnitude,
    Provenance,
    envelope,
    subtract_magnitude,
)
from .errors import (
    EventBudgetError,
    MeasurementContractError,
)

__all__ = [
    "EVENT_BUDGET_SOURCE",
    "EventBudget",
    "EventFamily",
    "EventFeatures",
    "NormalizedEvent",
    "measure_event_features",
    "measure_event_budget",
]


#: The canonical source of the subtractive residual-budget doctrine.
EVENT_BUDGET_SOURCE = (
    "corpus/canonical/models/EUR_DAILY_NEWS_REKEY_MODEL_CARD_V1.md"
)


class EventFamily(str, Enum):
    """The declared event-family vocabulary.

    The frozen corpus does **not** publish a canonical event-family
    taxonomy: the EUR Daily model card requires an "official EUR event
    family" as an *input*.  This bounded vocabulary is therefore the
    measurement contract's declared set of family labels.  A caller
    states the family of a normalized event.  It asserts no canonical
    CEREBUS classification, and no member carries an impact,
    expectancy or direction meaning.
    """

    MACRO_RELEASE = "MACRO_RELEASE"
    CENTRAL_BANK = "CENTRAL_BANK"
    INFLATION_RELEASE = "INFLATION_RELEASE"
    EMPLOYMENT_RELEASE = "EMPLOYMENT_RELEASE"
    GROWTH_RELEASE = "GROWTH_RELEASE"
    OTHER_OFFICIAL = "OTHER_OFFICIAL"
    UNCLASSIFIED = "UNCLASSIFIED"


def _require_aware(value: datetime, label: str) -> datetime:
    if not isinstance(value, datetime):
        raise MeasurementContractError(f"{label} must be a datetime")
    if value.tzinfo is None:
        raise MeasurementContractError(f"{label} must be tz-aware")
    return value.astimezone(timezone.utc)


@dataclass(frozen=True)
class NormalizedEvent:
    """One normalized event record.

    ``historical_band_lower`` / ``historical_band_upper`` /
    ``historical_size`` are optional but **explicit**: ``None`` means
    "not declared by the source", never "zero".
    """

    event_id: str
    family: EventFamily
    relevance_currencies: frozenset[str]
    relevance_assets: frozenset[str]
    scheduled_time: datetime
    actual_time: datetime | None
    source_ref: str
    provenance_label: str
    historical_band_lower: NativeMagnitude | None = None
    historical_band_upper: NativeMagnitude | None = None
    historical_size: NativeMagnitude | None = None

    def __post_init__(self) -> None:
        if not self.event_id:
            raise MeasurementContractError("event requires an id")
        if not self.source_ref:
            raise MeasurementContractError("event requires a source ref")
        if not self.provenance_label:
            raise MeasurementContractError("event requires a provenance label")
        object.__setattr__(
            self,
            "relevance_currencies",
            frozenset(self.relevance_currencies),
        )
        object.__setattr__(
            self, "relevance_assets", frozenset(self.relevance_assets)
        )
        object.__setattr__(
            self, "scheduled_time", _require_aware(self.scheduled_time, "scheduled time")
        )
        if self.actual_time is not None:
            object.__setattr__(
                self, "actual_time", _require_aware(self.actual_time, "actual time")
            )
        lower = self.historical_band_lower
        upper = self.historical_band_upper
        if (lower is None) != (upper is None):
            raise MeasurementContractError(
                "a historical band needs both a lower and an upper bound"
            )
        if lower is not None and upper is not None:
            if lower.instrument_id != upper.instrument_id or lower.unit is not upper.unit:
                raise MeasurementContractError(
                    "a historical band must live in one asset-native domain"
                )
            if upper.value < lower.value:
                raise MeasurementContractError(
                    "a historical band's upper bound is below its lower bound"
                )
        size = self.historical_size
        if size is not None and lower is not None:
            if size.instrument_id != lower.instrument_id or size.unit is not lower.unit:
                raise MeasurementContractError(
                    "a historical size must live in the band's asset-native domain"
                )

    # -- explicit absence --------------------------------------------
    @property
    def band_declared(self) -> bool:
        return self.historical_band_lower is not None

    @property
    def size_declared(self) -> bool:
        return self.historical_size is not None

    @property
    def actual_declared(self) -> bool:
        return self.actual_time is not None

    def to_dict(self) -> dict:
        from .contracts import encode_value

        return encode_value(self)


@dataclass(frozen=True)
class EventFeatures(Measurement):
    """The normalized event features as a measurement."""

    event_id: str
    family: EventFamily
    relevance_currencies: tuple[str, ...]
    relevance_assets: tuple[str, ...]
    scheduled_time: datetime
    actual_time: datetime | None
    actual_declared: bool
    band_declared: bool
    size_declared: bool
    source_ref: str
    provenance_label: str

    def to_dict(self) -> dict:
        from .contracts import encode_value

        return encode_value(self)


@dataclass(frozen=True)
class EventBudget(Measurement):
    """The subtractive residual event budget."""

    event_id: str
    total_size: NativeMagnitude
    consumed: NativeMagnitude
    residual: NativeMagnitude
    source_ref: str

    def to_dict(self) -> dict:
        from .contracts import encode_value

        return encode_value(self)


def measure_event_features(
    event: NormalizedEvent,
    *,
    provenance: Provenance,
    source_window,
    definition_version: str = "V1",
) -> EventFeatures:
    """Report the normalized features of one event.

    The output carries no geometry, no level and no direction: news
    conditions state, it never replaces geometry (invariant #17).
    """
    from .contracts import source_window_from_instants

    if source_window is None:
        instants = [event.scheduled_time]
        if event.actual_time is not None:
            instants.append(event.actual_time)
        source_window = source_window_from_instants(instants)
    context = provenance.context(source_window)
    return EventFeatures(
        **envelope(
            context, "EVENT_RELEVANCE", definition_version=definition_version
        ),
        event_id=event.event_id,
        family=event.family,
        relevance_currencies=tuple(sorted(event.relevance_currencies)),
        relevance_assets=tuple(sorted(event.relevance_assets)),
        scheduled_time=event.scheduled_time,
        actual_time=event.actual_time,
        actual_declared=event.actual_declared,
        band_declared=event.band_declared,
        size_declared=event.size_declared,
        source_ref=event.source_ref,
        provenance_label=event.provenance_label,
    )


def measure_event_budget(
    event: NormalizedEvent,
    consumed: NativeMagnitude,
    *,
    provenance: Provenance,
    source_window=None,
    definition_version: str = "V1",
) -> EventBudget:
    """Measure the residual event budget (subtractive).

    The total is the declared historical size, or the width of the
    declared historical band.  When neither is declared the budget
    refuses (``EVENT_BUDGET``): a missing historical input is an
    explicit refusal, never a zero.
    """
    total: NativeMagnitude | None = event.historical_size
    if total is None and event.historical_band_lower is not None:
        assert event.historical_band_upper is not None
        total = subtract_magnitude(
            event.historical_band_upper, event.historical_band_lower
        )
    if total is None:
        raise EventBudgetError(
            f"event {event.event_id!r} declares neither a historical size "
            "nor a historical band; the budget cannot be computed"
        )
    if (
        consumed.instrument_id != total.instrument_id
        or consumed.unit is not total.unit
    ):
        raise EventBudgetError(
            "the consumed movement must live in the event's asset-native domain"
        )
    if consumed.value > total.value:
        residual = NativeMagnitude(total.instrument_id, total.unit, total.value * 0)
    else:
        residual = subtract_magnitude(total, consumed)

    from .contracts import source_window_from_instants

    if source_window is None:
        source_window = source_window_from_instants([event.scheduled_time])
    context = provenance.context(source_window)
    return EventBudget(
        **envelope(context, "EVENT_BUDGET", definition_version=definition_version),
        event_id=event.event_id,
        total_size=total,
        consumed=consumed,
        residual=residual,
        source_ref=EVENT_BUDGET_SOURCE,
    )
