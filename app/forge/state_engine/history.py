"""Append-only ordered transition history (Ch III.4.9).

The ledger is append-only, ordered and gapless.  Every event names its
source snapshot, its event time, its rule identity, its resulting state
and the hash of the previous event, so any reorder, deletion, insertion
or silent rewrite breaks the chain.

Replaying the ledger from its genesis snapshot reproduces the recorded
current state; a divergence refuses with
``REPLAY_RECONSTRUCTION_MISMATCH``.  Explanations are ordered structured
facts — never generated prose.

Durable storage is **not** implemented here (III.4-GAP-10): the contract
is logical and storage-agnostic, and this module opens no database, no
file and no socket.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime
from types import MappingProxyType
from typing import Mapping

from app.forge.model_runtime import ExplanationFact, compute_hash, make_fact

from .errors import (
    HistoryChainMismatchError,
    HistorySequenceGapError,
    ReplayReconstructionMismatchError,
    StateContractError,
    TransitionAuthorityMismatchError,
)
from .snapshot import StateSnapshot
from .versions import STATE_ENGINE_VERSION
from .vocabulary import TransitionDecision, TransitionKind

__all__ = [
    "TransitionEvent",
    "TransitionLedger",
    "append_event",
    "explain",
    "history_hash",
    "open_ledger",
    "reconstruct_state",
    "replay_events",
    "state_at",
    "verify_history",
]

_HASH = re.compile(r"^[0-9a-f]{64}$")
_IDENT = re.compile(r"^[A-Za-z0-9_.:/\-]+$")

#: The ledger's own vocabulary of retained negative evidence.
NEGATIVE_KINDS: frozenset[TransitionKind] = frozenset(
    {
        TransitionKind.REJECT,
        TransitionKind.FAIL,
        TransitionKind.INVALIDATE,
        TransitionKind.STAND_DOWN,
    }
)


@dataclass(frozen=True)
class TransitionEvent:
    """One appended transition event (frozen III.4.9 field set)."""

    event_id: str
    sequence: int
    kind: TransitionKind
    model_id: str
    model_version: str
    engine_version: str
    source_snapshot_ref: str
    source_snapshot_hash: str
    source_output_hash: str
    event_time: datetime
    rule_id: str
    rule_version: str
    rule_source_ref: str
    prior_state: str
    resulting_state: str
    resulting_state_id: str
    conditions: tuple[str, ...]
    evidence_refs: tuple[str, ...]
    payload: tuple[tuple[str, str], ...]
    prev_event_hash: str
    event_hash: str

    def __post_init__(self) -> None:
        if not self.event_id or not _IDENT.match(self.event_id):
            raise StateContractError(
                f"event_id must be a bounded id: {self.event_id!r}"
            )
        if self.sequence < 0:
            raise StateContractError("sequence must not be negative")
        if not isinstance(self.kind, TransitionKind):
            raise StateContractError("an event carries a vocabulary kind")
        if not self.source_snapshot_ref or not self.source_output_hash:
            raise StateContractError("an event names its source lineage")
        if self.event_time.tzinfo is None:
            raise StateContractError("event times are timezone-aware")
        if self.engine_version != STATE_ENGINE_VERSION:
            raise StateContractError(
                f"events are stamped by {STATE_ENGINE_VERSION}, got "
                f"{self.engine_version!r}"
            )
        if not self.rule_id or not self.rule_version:
            raise StateContractError("an event names its rule identity")
        if not self.prior_state or not self.resulting_state:
            raise StateContractError("an event names both states")
        if not self.resulting_state_id:
            raise StateContractError("an event names its resulting state id")
        for name in ("prev_event_hash", "event_hash"):
            value = getattr(self, name)
            if not _HASH.match(value):
                raise StateContractError(f"{name} is a sha256 hex digest")

    def to_payload(self) -> dict:
        """The hashed payload (the self-referential hash is excluded)."""

        return {
            "event_id": self.event_id,
            "sequence": self.sequence,
            "kind": self.kind.value,
            "model_id": self.model_id,
            "model_version": self.model_version,
            "engine_version": self.engine_version,
            "source_snapshot_ref": self.source_snapshot_ref,
            "source_snapshot_hash": self.source_snapshot_hash,
            "source_output_hash": self.source_output_hash,
            "event_time": self.event_time,
            "rule_id": self.rule_id,
            "rule_version": self.rule_version,
            "rule_source_ref": self.rule_source_ref,
            "prior_state": self.prior_state,
            "resulting_state": self.resulting_state,
            "resulting_state_id": self.resulting_state_id,
            "conditions": list(self.conditions),
            "evidence_refs": list(self.evidence_refs),
            "payload": [list(item) for item in self.payload],
            "prev_event_hash": self.prev_event_hash,
        }


@dataclass(frozen=True)
class TransitionLedger:
    """An append-only ordered transition ledger for one model key."""

    model_id: str
    model_version: str
    genesis_snapshot_id: str
    genesis_snapshot_hash: str
    genesis_state: str
    events: tuple[TransitionEvent, ...]
    history_hash: str

    def __post_init__(self) -> None:
        if not self.model_id or not self.model_version:
            raise StateContractError("a ledger declares its model key")
        if not _HASH.match(self.genesis_snapshot_hash):
            raise StateContractError("a ledger carries its genesis snapshot hash")
        if not _HASH.match(self.history_hash):
            raise StateContractError("a ledger carries its history hash")

    # -- queries -----------------------------------------------------------

    @property
    def current_state(self) -> str:
        return self.events[-1].resulting_state if self.events else self.genesis_state

    @property
    def current_state_id(self) -> str:
        return (
            self.events[-1].resulting_state_id
            if self.events
            else self.genesis_snapshot_id
        )

    @property
    def event_hashes(self) -> tuple[str, ...]:
        return tuple(event.event_hash for event in self.events)

    def negative_events(self) -> tuple[TransitionEvent, ...]:
        """Retained negative evidence stays queryable (invariant #15)."""

        return tuple(event for event in self.events if event.kind in NEGATIVE_KINDS)

    def events_of(self, kind: TransitionKind) -> tuple[TransitionEvent, ...]:
        return tuple(event for event in self.events if event.kind is kind)


def history_hash(
    *, genesis_snapshot_hash: str, events: tuple[TransitionEvent, ...]
) -> str:
    """Deterministic history hash over the ordered event hashes."""

    return compute_hash(
        {
            "genesis_snapshot_hash": genesis_snapshot_hash,
            "event_hashes": [event.event_hash for event in events],
        }
    )


def open_ledger(genesis: StateSnapshot) -> TransitionLedger:
    """Open an empty ledger at a finalized genesis snapshot."""

    if not isinstance(genesis, StateSnapshot):
        raise StateContractError("a ledger opens at a StateSnapshot")
    if not _HASH.match(genesis.snapshot_hash):
        raise StateContractError("the genesis snapshot must be finalized")
    events: tuple[TransitionEvent, ...] = ()
    return TransitionLedger(
        model_id=genesis.model_id,
        model_version=genesis.model_version,
        genesis_snapshot_id=genesis.snapshot_id,
        genesis_snapshot_hash=genesis.snapshot_hash,
        genesis_state=genesis.active_state,
        events=events,
        history_hash=history_hash(
            genesis_snapshot_hash=genesis.snapshot_hash, events=events
        ),
    )


def append_event(
    ledger: TransitionLedger,
    decision: TransitionDecision,
    *,
    resulting_snapshot: StateSnapshot,
    event_id: str,
) -> TransitionLedger:
    """Append one earned decision; append-only, ordered, gapless."""

    if not isinstance(ledger, TransitionLedger):
        raise StateContractError("append_event requires a TransitionLedger")
    if not isinstance(decision, TransitionDecision):
        raise StateContractError("append_event requires earned decisions")
    if not isinstance(resulting_snapshot, StateSnapshot):
        raise StateContractError("append_event requires the resulting snapshot")

    if (
        decision.model_id != ledger.model_id
        or decision.model_version != ledger.model_version
    ):
        raise TransitionAuthorityMismatchError(
            f"decision {decision.model_id}@{decision.model_version} does not "
            f"belong to ledger {ledger.model_id}@{ledger.model_version}"
        )
    if resulting_snapshot.model_id != ledger.model_id:
        raise TransitionAuthorityMismatchError(
            "the resulting snapshot belongs to another model key"
        )

    # The decision must read the ledger's current state.
    if decision.prior_snapshot_id != ledger.current_state_id:
        raise HistoryChainMismatchError(
            f"decision reads {decision.prior_snapshot_id}, ledger is at "
            f"{ledger.current_state_id}"
        )
    if decision.prior_state != ledger.current_state:
        raise HistoryChainMismatchError(
            f"decision prior state {decision.prior_state} drifted from ledger "
            f"state {ledger.current_state}"
        )
    if resulting_snapshot.active_state != decision.resulting_state:
        raise StateContractError(
            f"resulting snapshot state {resulting_snapshot.active_state} does not "
            f"match the decision {decision.resulting_state}"
        )
    if resulting_snapshot.snapshot_id != decision.resulting_state_id:
        raise StateContractError(
            "resulting snapshot id must be the decision's resulting state id"
        )

    for existing in ledger.events:
        if existing.event_id == event_id:
            raise StateContractError(f"duplicate event id {event_id!r}")

    sequence = len(ledger.events)
    prev_hash = (
        ledger.events[-1].event_hash
        if ledger.events
        else ledger.genesis_snapshot_hash
    )

    draft = TransitionEvent(
        event_id=event_id,
        sequence=sequence,
        kind=decision.kind,
        model_id=decision.model_id,
        model_version=decision.model_version,
        engine_version=STATE_ENGINE_VERSION,
        source_snapshot_ref=decision.prior_snapshot_id,
        source_snapshot_hash=decision.prior_snapshot_hash,
        source_output_hash=decision.source_output_hash,
        event_time=decision.event_time,
        rule_id=decision.rule_id,
        rule_version=decision.rule_version,
        rule_source_ref=decision.rule_source_ref,
        prior_state=decision.prior_state,
        resulting_state=decision.resulting_state,
        resulting_state_id=decision.resulting_state_id,
        conditions=decision.conditions,
        evidence_refs=decision.evidence_refs,
        payload=decision.payload,
        prev_event_hash=prev_hash,
        event_hash="0" * 64,
    )
    event = TransitionEvent(
        **{
            **{
                name: getattr(draft, name)
                for name in draft.__dataclass_fields__
                if name != "event_hash"
            },
            "event_hash": compute_hash(draft.to_payload()),
        }
    )

    events = ledger.events + (event,)
    return TransitionLedger(
        model_id=ledger.model_id,
        model_version=ledger.model_version,
        genesis_snapshot_id=ledger.genesis_snapshot_id,
        genesis_snapshot_hash=ledger.genesis_snapshot_hash,
        genesis_state=ledger.genesis_state,
        events=events,
        history_hash=history_hash(
            genesis_snapshot_hash=ledger.genesis_snapshot_hash, events=events
        ),
    )


def verify_history(ledger: TransitionLedger) -> None:
    """Re-derive the chain; any reorder/insert/rewrite refuses."""

    if not isinstance(ledger, TransitionLedger):
        raise StateContractError("verify_history requires a TransitionLedger")

    previous = ledger.genesis_snapshot_hash
    for index, event in enumerate(ledger.events):
        # Link first, then ordering, then content: a reorder is a chain break,
        # a resequenced event is a gap, a rewritten event is a hash break.
        if event.prev_event_hash != previous:
            raise HistoryChainMismatchError(
                f"event {event.event_id} does not chain to its predecessor"
            )
        if event.sequence != index:
            raise HistorySequenceGapError(
                f"event {event.event_id} carries sequence {event.sequence}, "
                f"expected {index}"
            )
        recomputed = compute_hash(event.to_payload())
        if recomputed != event.event_hash:
            raise HistoryChainMismatchError(
                f"event {event.event_id} hash does not reproduce"
            )
        previous = event.event_hash

    expected = history_hash(
        genesis_snapshot_hash=ledger.genesis_snapshot_hash, events=ledger.events
    )
    if expected != ledger.history_hash:
        raise HistoryChainMismatchError("ledger history hash does not reproduce")


def replay_events(ledger: TransitionLedger) -> tuple[TransitionEvent, ...]:
    """Replay order: the ledger as recorded, after verification."""

    verify_history(ledger)
    return ledger.events


def reconstruct_state(
    ledger: TransitionLedger,
    snapshots: Mapping[str, StateSnapshot],
) -> StateSnapshot:
    """Replay the ledger and return the reconstructed current snapshot."""

    verify_history(ledger)
    if not ledger.events:
        raise ReplayReconstructionMismatchError(
            "the ledger carries no events to reconstruct"
        )

    previous_state = ledger.genesis_state
    previous_id = ledger.genesis_snapshot_id
    for event in ledger.events:
        if event.prior_state != previous_state or event.source_snapshot_ref != previous_id:
            raise ReplayReconstructionMismatchError(
                f"event {event.event_id} does not continue the replayed state"
            )
        snapshot = snapshots.get(event.resulting_state_id)
        if snapshot is None:
            raise ReplayReconstructionMismatchError(
                f"no snapshot recorded for {event.resulting_state_id}"
            )
        if snapshot.active_state != event.resulting_state:
            raise ReplayReconstructionMismatchError(
                f"snapshot {snapshot.snapshot_id} state {snapshot.active_state} "
                f"contradicts event {event.event_id}"
            )
        if snapshot.prior_snapshot_id != event.source_snapshot_ref:
            raise ReplayReconstructionMismatchError(
                f"snapshot {snapshot.snapshot_id} does not chain to "
                f"{event.source_snapshot_ref}"
            )
        previous_state = event.resulting_state
        previous_id = event.resulting_state_id

    return snapshots[ledger.current_state_id]


def state_at(
    ledger: TransitionLedger,
    sequence: int,
    *,
    genesis: StateSnapshot,
    snapshots: Mapping[str, StateSnapshot],
) -> StateSnapshot:
    """Return the historical state after ``sequence`` events (0 = genesis)."""

    verify_history(ledger)
    if not isinstance(sequence, int) or sequence < 0:
        raise StateContractError("sequence must be a non-negative int")
    if sequence == 0:
        return genesis
    if sequence > len(ledger.events):
        raise StateContractError(
            f"sequence {sequence} is beyond the ledger ({len(ledger.events)} events)"
        )
    event = ledger.events[sequence - 1]
    try:
        return snapshots[event.resulting_state_id]
    except KeyError:
        raise ReplayReconstructionMismatchError(
            f"no snapshot recorded for {event.resulting_state_id}"
        ) from None


def explain(ledger: TransitionLedger) -> tuple[ExplanationFact, ...]:
    """Ordered structured explanation facts (never generated prose)."""

    verify_history(ledger)
    facts: list[ExplanationFact] = []
    for event in ledger.events:
        facts.append(
            make_fact(
                f"TRANSITION.{event.sequence}.{event.kind.value}",
                event.rule_id,
                event.rule_source_ref,
                (
                    ("prior_state", event.prior_state),
                    ("resulting_state", event.resulting_state),
                    ("source_snapshot", event.source_snapshot_ref),
                    ("event_time", event.event_time.isoformat()),
                    ("resulting_state_id", event.resulting_state_id),
                ),
                rule_version=event.rule_version,
            )
        )
    return tuple(facts)
