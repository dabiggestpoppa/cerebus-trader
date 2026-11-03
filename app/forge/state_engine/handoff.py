"""Formal layer handoff (Ch III.4.6).

L3 destination context -> L2 path/opportunity -> L1 execution context.

Ownership is typed on each record, so a lower layer can never populate a
higher-layer field (``LAYER_OWNERSHIP_VIOLATION``).  There is no
probability field and no score field anywhere: agreement between layers
travels as facts, never as a monolithic confluence number, and a handoff
never creates entry eligibility.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from enum import Enum

from app.forge.model_runtime import Layer

from .errors import (
    LayerHandoffDirectionError,
    LayerOwnershipViolationError,
    StateContractError,
    TransitionAuthorityMismatchError,
)
from .snapshot import StateSnapshot

__all__ = [
    "HandoffAgreement",
    "LayerHandoff",
    "OwnershipScope",
    "build_handoff",
    "layer_conflict_facts",
]

_IDENT = re.compile(r"^[A-Za-z0-9_.:/\-]+$")


class OwnershipScope(str, Enum):
    """Who owns what after the handoff."""

    DESTINATION = "DESTINATION"  # L3
    PATH = "PATH"  # L2
    EXECUTION = "EXECUTION"  # L1


class HandoffAgreement(str, Enum):
    """Factual agreement between layers — never a score."""

    AGREE = "AGREE"
    CONFLICT = "CONFLICT"
    UNDECLARED = "UNDECLARED"


_ALLOWED_DIRECTIONS: frozenset[tuple[Layer, Layer]] = frozenset(
    {(Layer.L3, Layer.L2), (Layer.L2, Layer.L1)}
)

_UPWARD: frozenset[tuple[Layer, Layer]] = frozenset(
    {(Layer.L1, Layer.L2), (Layer.L1, Layer.L3), (Layer.L2, Layer.L3)}
)

_OWNERSHIP_BY_DESTINATION: dict[Layer, OwnershipScope] = {
    Layer.L2: OwnershipScope.PATH,
    Layer.L1: OwnershipScope.EXECUTION,
}


def layer_conflict_facts(
    *,
    source_layer: Layer,
    destination_layer: Layer,
    agreement: HandoffAgreement = HandoffAgreement.UNDECLARED,
) -> tuple[str, ...]:
    """The conflict facts a handoff may carry (facts, never a score)."""

    if agreement is HandoffAgreement.CONFLICT:
        return (
            f"MODEL_CONFLICT.{source_layer.value}_TO_{destination_layer.value}",
        )
    return ()


@dataclass(frozen=True)
class LayerHandoff:
    """One formal layer handoff with typed ownership."""

    handoff_id: str
    source_snapshot_id: str
    destination_snapshot_id: str
    source_layer: Layer
    destination_layer: Layer
    ownership: OwnershipScope
    destination_context_ref: str
    path_ref: str | None
    execution_context_ref: str | None
    agreement: HandoffAgreement
    conflict_facts: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not self.handoff_id or not _IDENT.match(self.handoff_id):
            raise StateContractError(
                f"handoff_id must be a bounded id: {self.handoff_id!r}"
            )
        if not self.source_snapshot_id or not self.destination_snapshot_id:
            raise StateContractError("a handoff names both snapshots")
        if not isinstance(self.ownership, OwnershipScope):
            raise StateContractError("a handoff carries a typed ownership scope")
        if not self.destination_context_ref:
            raise StateContractError(
                "a handoff carries its destination context reference"
            )
        if not isinstance(self.agreement, HandoffAgreement):
            raise StateContractError("agreement uses the bounded vocabulary")

    def to_payload(self) -> dict:
        return {
            "handoff_id": self.handoff_id,
            "source_snapshot_id": self.source_snapshot_id,
            "destination_snapshot_id": self.destination_snapshot_id,
            "source_layer": self.source_layer.value,
            "destination_layer": self.destination_layer.value,
            "ownership": self.ownership.value,
            "destination_context_ref": self.destination_context_ref,
            "path_ref": self.path_ref,
            "execution_context_ref": self.execution_context_ref,
            "agreement": self.agreement.value,
            "conflict_facts": list(self.conflict_facts),
        }


def build_handoff(
    *,
    source_snapshot: StateSnapshot,
    destination_snapshot: StateSnapshot,
    handoff_id: str,
    destination_context_ref: str,
    path_ref: str | None = None,
    execution_context_ref: str | None = None,
    agreement: HandoffAgreement = HandoffAgreement.UNDECLARED,
) -> LayerHandoff:
    """Build one downward handoff; upward or skipping handoffs refuse."""

    if not isinstance(source_snapshot, StateSnapshot) or not isinstance(
        destination_snapshot, StateSnapshot
    ):
        raise StateContractError("a handoff requires two snapshots")

    # A handoff crosses model *keys* by design (EUR L3 -> L2 -> L1 are distinct
    # registered models); it may never cross instruments, because asset
    # calibration stays local (invariant #2).
    if source_snapshot.instrument_id != destination_snapshot.instrument_id:
        raise TransitionAuthorityMismatchError(
            "a handoff cannot cross instruments: "
            f"{source_snapshot.instrument_id} -> {destination_snapshot.instrument_id}"
        )

    source_layer = source_snapshot.layer
    destination_layer = destination_snapshot.layer
    direction = (source_layer, destination_layer)

    if direction in _UPWARD:
        raise LayerOwnershipViolationError(
            f"{source_layer.value} cannot own or mutate {destination_layer.value}"
        )
    if direction not in _ALLOWED_DIRECTIONS:
        raise LayerHandoffDirectionError(
            f"{source_layer.value} -> {destination_layer.value} is not a formal "
            "handoff; only L3 -> L2 and L2 -> L1 are declared"
        )

    # Ownership is derived from the *destination* layer: L2 owns path, L1 owns
    # execution context.  An absent execution context stays explicitly absent
    # (never inherited), and no handoff creates entry eligibility either way.
    ownership = _OWNERSHIP_BY_DESTINATION[destination_layer]

    return LayerHandoff(
        handoff_id=handoff_id,
        source_snapshot_id=source_snapshot.snapshot_id,
        destination_snapshot_id=destination_snapshot.snapshot_id,
        source_layer=source_layer,
        destination_layer=destination_layer,
        ownership=ownership,
        destination_context_ref=destination_context_ref,
        path_ref=path_ref,
        execution_context_ref=execution_context_ref,
        agreement=agreement,
        conflict_facts=layer_conflict_facts(
            source_layer=source_layer,
            destination_layer=destination_layer,
            agreement=agreement,
        ),
    )
