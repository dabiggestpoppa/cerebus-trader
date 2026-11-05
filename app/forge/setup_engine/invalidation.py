"""Price / structural / temporal invalidation (Ch III.5.4).

Three independent typed records.  Absence is explicit (``None`` means
``UNRESOLVED`` for that kind), never empty-success, and no kind is ever
substituted for another: a price level cannot stand in for a session
bound and a session bound cannot stand in for a price level.

An invalidation that fires dominates a satisfied trigger — the setup is
``BLOCKED`` even when its confirmation completed.
"""

from __future__ import annotations

from dataclasses import dataclass

from .contracts import (
    InvalidationKind,
    PriceInvalidation,
    StructuralInvalidation,
    TemporalInvalidation,
)
from .errors import SetupContractError

__all__ = [
    "InvalidationEvents",
    "InvalidationSet",
    "active_kinds",
    "resolve_invalidations",
]


@dataclass(frozen=True)
class InvalidationEvents:
    """Which observed facts fired, by kind (supplied, never inferred)."""

    price_fired: bool = False
    structural_fired: bool = False
    temporal_fired: bool = False

    def fired(self, kind: InvalidationKind) -> bool:
        if kind is InvalidationKind.PRICE:
            return self.price_fired
        if kind is InvalidationKind.STRUCTURAL:
            return self.structural_fired
        if kind is InvalidationKind.TEMPORAL:
            return self.temporal_fired
        raise SetupContractError("unknown invalidation kind")


@dataclass(frozen=True)
class InvalidationSet:
    """The trichotomy as three separate fields, each typed or explicitly absent."""

    price: PriceInvalidation | None = None
    structural: StructuralInvalidation | None = None
    temporal: TemporalInvalidation | None = None

    def __post_init__(self) -> None:
        if self.price is not None and not isinstance(self.price, PriceInvalidation):
            raise SetupContractError("the price slot carries a price invalidation")
        if self.structural is not None and not isinstance(
            self.structural, StructuralInvalidation
        ):
            raise SetupContractError("the structural slot carries a structural invalidation")
        if self.temporal is not None and not isinstance(
            self.temporal, TemporalInvalidation
        ):
            raise SetupContractError("the temporal slot carries a temporal invalidation")

    def kind(self, kind: InvalidationKind) -> object | None:
        if kind is InvalidationKind.PRICE:
            return self.price
        if kind is InvalidationKind.STRUCTURAL:
            return self.structural
        if kind is InvalidationKind.TEMPORAL:
            return self.temporal
        raise SetupContractError("unknown invalidation kind")

    def unresolved_kinds(self) -> tuple[str, ...]:
        """Kinds carried as the explicit absent form, never silently fine."""

        missing: list[str] = []
        if self.price is None:
            missing.append(InvalidationKind.PRICE.value)
        if self.structural is None:
            missing.append(InvalidationKind.STRUCTURAL.value)
        if self.temporal is None:
            missing.append(InvalidationKind.TEMPORAL.value)
        return tuple(missing)

    def active_kinds(self) -> tuple[str, ...]:
        fired: list[str] = []
        if self.price is not None and self.price.active:
            fired.append(InvalidationKind.PRICE.value)
        if self.structural is not None and self.structural.active:
            fired.append(InvalidationKind.STRUCTURAL.value)
        if self.temporal is not None and self.temporal.active:
            fired.append(InvalidationKind.TEMPORAL.value)
        return tuple(fired)

    @property
    def any_active(self) -> bool:
        return bool(self.active_kinds())

    def declared_kinds(self) -> tuple[str, ...]:
        return tuple(
            kind.value
            for kind in (
                InvalidationKind.PRICE,
                InvalidationKind.STRUCTURAL,
                InvalidationKind.TEMPORAL,
            )
            if self.kind(kind) is not None
        )


def resolve_invalidations(
    *,
    price: PriceInvalidation | None,
    structural: StructuralInvalidation | None,
    temporal: TemporalInvalidation | None,
    events: InvalidationEvents,
) -> InvalidationSet:
    """Apply observed firing flags to the supplied typed invalidations.

    The returned records carry the fired flag; absence is preserved as
    absence (reported by :meth:`InvalidationSet.unresolved_kinds`).
    """

    if not isinstance(events, InvalidationEvents):
        raise SetupContractError("invalidation events are typed")
    return InvalidationSet(
        price=(
            None
            if price is None
            else PriceInvalidation(
                value=price.value,
                magnitude_unit=price.magnitude_unit,
                materialization=price.materialization,
                source_ref=price.source_ref,
                active=events.price_fired,
            )
        ),
        structural=(
            None
            if structural is None
            else StructuralInvalidation(
                condition_id=structural.condition_id,
                state_ref=structural.state_ref,
                source_ref=structural.source_ref,
                active=events.structural_fired,
            )
        ),
        temporal=(
            None
            if temporal is None
            else TemporalInvalidation(
                bound_id=temporal.bound_id,
                checkpoint=temporal.checkpoint,
                source_ref=temporal.source_ref,
                active=events.temporal_fired,
            )
        ),
    )


def active_kinds(invalidations: InvalidationSet) -> tuple[str, ...]:
    return invalidations.active_kinds()
