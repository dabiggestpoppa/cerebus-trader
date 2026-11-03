"""First-delivery ordering (Ch III.4.3).

The engine records the *ordered* delivery of declared targets.  A
terminal both-side reach is retained together with the sequence that
produced it: the same terminal outcome reached in the opposite order is
a different path, and the record must say so.

Intrabar ordering is never inferred from OHLC.  When the supplied
evidence cannot resolve which target was realized first, the engine
refuses with ``AMBIGUOUS_PATH`` — an explicit unresolved result, not a
guess.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime
from enum import Enum

from .errors import (
    AmbiguousPathError,
    NoCalculationError,
    StateContractError,
    TargetNotDeclaredError,
)

__all__ = [
    "DeclaredTarget",
    "DeliveryObservation",
    "DeliveryPath",
    "DeliveryRecord",
    "DeliverySide",
    "FirstDelivery",
    "TerminalReach",
    "build_path",
    "path_hash",
    "target_order",
]

_IDENT = re.compile(r"^[A-Za-z0-9_.:/\-]+$")


class DeliverySide(str, Enum):
    """Which side of the reference price a target sits on."""

    ABOVE = "ABOVE"
    BELOW = "BELOW"


class TerminalReach(str, Enum):
    """The factual terminal reach of the recorded path."""

    NONE = "NONE"
    ONE_SIDE = "ONE_SIDE"
    BOTH_SIDES_REACHED = "BOTH_SIDES_REACHED"


@dataclass(frozen=True)
class DeclaredTarget:
    """A target declared before the path is observed."""

    target_id: str
    side: DeliverySide
    declared_order_index: int

    def __post_init__(self) -> None:
        if not self.target_id or not _IDENT.match(self.target_id):
            raise StateContractError(
                f"target_id must be a bounded id: {self.target_id!r}"
            )
        if not isinstance(self.side, DeliverySide):
            raise StateContractError("a target carries a bounded side")
        if self.declared_order_index < 0:
            raise StateContractError("declared_order_index must not be negative")


@dataclass(frozen=True)
class DeliveryObservation:
    """One hit supplied by the caller, with its realizing bar reference."""

    target_id: str
    realized_event_time: datetime
    realizing_bar_ref: str

    def __post_init__(self) -> None:
        if not self.target_id or not _IDENT.match(self.target_id):
            raise StateContractError("an observation carries a bounded target id")
        if not isinstance(self.realized_event_time, datetime):
            raise StateContractError("an observation carries its event time")
        if self.realized_event_time.tzinfo is None:
            raise StateContractError(
                "observation event times must be timezone-aware (injected)"
            )
        if not self.realizing_bar_ref or not _IDENT.match(self.realizing_bar_ref):
            raise StateContractError(
                "an observation names its realizing bar reference"
            )


@dataclass(frozen=True)
class DeliveryRecord:
    """One ordered delivery in the path."""

    target_id: str
    side: DeliverySide
    order_index: int
    realized_event_time: datetime
    realizing_bar_ref: str

    def to_payload(self) -> dict:
        return {
            "target_id": self.target_id,
            "side": self.side.value,
            "order_index": self.order_index,
            "realized_event_time": self.realized_event_time,
            "realizing_bar_ref": self.realizing_bar_ref,
        }


@dataclass(frozen=True)
class FirstDelivery:
    """The first hit: which target, which side, and when."""

    target_id: str
    side: DeliverySide
    realized_event_time: datetime
    order_index: int
    realizing_bar_ref: str

    def to_payload(self) -> dict:
        return {
            "target_id": self.target_id,
            "side": self.side.value,
            "realized_event_time": self.realized_event_time,
            "order_index": self.order_index,
            "realizing_bar_ref": self.realizing_bar_ref,
        }


@dataclass(frozen=True)
class DeliveryPath:
    """The ordered delivery path, retained in full."""

    clock_id: str
    targets: tuple[DeclaredTarget, ...]
    deliveries: tuple[DeliveryRecord, ...]
    first_delivery: FirstDelivery | None
    terminal_reach: TerminalReach
    ambiguous: bool = False

    def __post_init__(self) -> None:
        if not self.clock_id:
            raise StateContractError("a delivery path carries its clock identity")
        if not isinstance(self.terminal_reach, TerminalReach):
            raise StateContractError("a delivery path carries its terminal reach")

    @property
    def delivery_order(self) -> tuple[str, ...]:
        return tuple(record.target_id for record in self.deliveries)

    def reached_sides(self) -> frozenset[DeliverySide]:
        return frozenset(record.side for record in self.deliveries)

    @property
    def terminal_result(self) -> str:
        """The terminal result only — deliberately *not* the whole path."""

        return self.terminal_reach.value

    def to_payload(self) -> dict:
        return {
            "clock_id": self.clock_id,
            "targets": [
                {
                    "target_id": target.target_id,
                    "side": target.side.value,
                    "declared_order_index": target.declared_order_index,
                }
                for target in self.targets
            ],
            "deliveries": [record.to_payload() for record in self.deliveries],
            "first_delivery": (
                self.first_delivery.to_payload() if self.first_delivery else None
            ),
            "terminal_reach": self.terminal_reach.value,
            "ambiguous": self.ambiguous,
        }


def target_order(targets: tuple[DeclaredTarget, ...]) -> tuple[str, ...]:
    """The stable declared order of target ids."""

    return tuple(
        target.target_id
        for target in sorted(targets, key=lambda item: item.declared_order_index)
    )


def build_path(
    *,
    clock_id: str | None,
    targets: tuple[DeclaredTarget, ...],
    observations: tuple[DeliveryObservation, ...],
    intrabar_order_resolvable: bool = True,
    requires_first_delivery: bool = False,
) -> DeliveryPath:
    """Record an ordered delivery path from supplied observations.

    Ordering comes from ``(realized_event_time, supplied order)``.  When
    two observations fall inside the same bar and the caller cannot
    certify intrabar ordering, the path is refused rather than invented.
    """

    if not clock_id:
        raise NoCalculationError(
            "a delivery path requires its clock identity (no wall clock here)"
        )
    if not targets:
        raise StateContractError("a delivery path requires declared targets")
    if not isinstance(intrabar_order_resolvable, bool):
        raise StateContractError("intrabar_order_resolvable must be a bool")

    ids = [target.target_id for target in targets]
    if len(set(ids)) != len(ids):
        raise StateContractError("declared target ids must be unique")
    by_id = {target.target_id: target for target in targets}

    # Stable order first, then chronological within the supplied order.
    declared = tuple(sorted(targets, key=lambda item: item.declared_order_index))
    indexed: list[tuple[DeliveryObservation, DeclaredTarget, int]] = []
    for position, observation in enumerate(observations):
        target = by_id.get(observation.target_id)
        if target is None:
            raise TargetNotDeclaredError(
                f"observation for undeclared target {observation.target_id!r}"
            )
        indexed.append((observation, target, position))

    # Same-bar ambiguity: unresolvable intrabar ordering refuses.
    if not intrabar_order_resolvable:
        bars = [observation.realizing_bar_ref for observation, _, _ in indexed]
        if len(set(bars)) != len(bars):
            raise AmbiguousPathError(
                "two deliveries share one bar and intrabar ordering is not "
                "resolvable from the supplied evidence"
            )

    ordered = sorted(
        indexed,
        key=lambda item: (item[0].realized_event_time, item[2]),
    )

    records: list[DeliveryRecord] = []
    for order_index, (observation, target, _position) in enumerate(ordered):
        records.append(
            DeliveryRecord(
                target_id=target.target_id,
                side=target.side,
                order_index=order_index,
                realized_event_time=observation.realized_event_time,
                realizing_bar_ref=observation.realizing_bar_ref,
            )
        )

    sides = {record.side for record in records}
    if not records:
        reach = TerminalReach.NONE
    elif len(sides) == 2:
        reach = TerminalReach.BOTH_SIDES_REACHED
    else:
        reach = TerminalReach.ONE_SIDE

    ambiguous = False
    if requires_first_delivery and reach is TerminalReach.BOTH_SIDES_REACHED:
        # Both sides reached: the sequence is the only evidence of order.
        if not intrabar_order_resolvable:
            ambiguous = True
            raise AmbiguousPathError(
                "both sides reached with unresolved intrabar ordering; "
                "first delivery cannot be established"
            )

    first = records[0] if records else None
    return DeliveryPath(
        clock_id=clock_id,
        targets=declared,
        deliveries=tuple(records),
        first_delivery=(
            FirstDelivery(
                target_id=first.target_id,
                side=first.side,
                realized_event_time=first.realized_event_time,
                order_index=first.order_index,
                realizing_bar_ref=first.realizing_bar_ref,
            )
            if first is not None
            else None
        ),
        terminal_reach=reach,
        ambiguous=ambiguous,
    )


def path_hash(path: DeliveryPath, compute_hash) -> str:
    """Deterministic hash of the whole ordered path (never the summary)."""

    return compute_hash(path.to_payload())
