"""Structural rekey (Ch III.4.5).

Rekey is a **structural remapping transition**, never "price touched a
number".  The record preserves the prior range reference, the qualifying
structural event, the canonical rule, the new active mapping, the
eligibility change and the prior-state lineage.

The prior mapping is *closed/replaced*, not deleted: history stays
reconstructable.  A bare touch or threshold crossing refuses with
``REKEY_NOT_STRUCTURAL``.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime, timezone

from app.forge.measurements import AnchorStatus
from app.forge.model_runtime import Layer

from .errors import (
    RekeyFromUnresolvedAnchorError,
    RekeyNotStructuralError,
    StateContractError,
    TransitionNotEarnedError,
)
from .snapshot import StateSnapshot
from .vocabulary import (
    Condition,
    TransitionDecision,
    TransitionKind,
    TransitionRequest,
    TransitionRule,
    authority_for,
    evaluate_transition,
)

__all__ = [
    "EUR_DAILY_LADDER",
    "RekeyRecord",
    "plan_rekey",
]

_IDENT = re.compile(r"^[A-Za-z0-9_.:/\-]+$")

#: The canonical EUR Daily rekey/extension ladder (distinct states).
EUR_DAILY_LADDER: tuple[str, ...] = (
    "REKEY_100",
    "REKEY_125",
    "REKEY_132",
    "REKEY_168",
    "REKEY_185",
)

#: Anchor states that cannot authorize a structural rekey.
_NON_STRUCTURAL_ANCHOR_STATES: frozenset[AnchorStatus] = frozenset(
    {AnchorStatus.UNRESOLVED, AnchorStatus.INVALIDATED}
)


@dataclass(frozen=True)
class RekeyRecord:
    """The structural remapping record (prior -> rekey -> new mapping)."""

    rekey_id: str
    decision: TransitionDecision
    prior_range_ref: str
    qualifying_event_ref: str
    new_mapping_ref: str
    new_state: str
    eligibility_change: str
    replaces: str
    closed: bool
    prior_lineage: tuple[str, ...]

    def __post_init__(self) -> None:
        if not self.rekey_id or not _IDENT.match(self.rekey_id):
            raise StateContractError(f"rekey_id must be a bounded id: {self.rekey_id!r}")
        if not isinstance(self.decision, TransitionDecision):
            raise StateContractError("a rekey carries its earned decision")
        if self.decision.kind is not TransitionKind.REKEY:
            raise StateContractError("a rekey record wraps a REKEY decision")
        if not self.prior_range_ref or not self.new_mapping_ref:
            raise StateContractError("a rekey names both mappings")
        if not self.qualifying_event_ref:
            raise StateContractError("a rekey names its qualifying event")
        if not self.new_state:
            raise StateContractError("a rekey names its new state")
        if not self.eligibility_change:
            raise StateContractError("a rekey names its eligibility change")
        if not self.closed:
            raise StateContractError(
                "a rekey always closes/replaces the prior mapping"
            )

    @property
    def model_id(self) -> str:
        return self.decision.model_id

    @property
    def model_version(self) -> str:
        return self.decision.model_version

    @property
    def event_time(self) -> datetime:
        return self.decision.event_time

    def to_payload(self) -> dict:
        return {
            "rekey_id": self.rekey_id,
            "model_id": self.decision.model_id,
            "model_version": self.decision.model_version,
            "prior_range_ref": self.prior_range_ref,
            "prior_state": self.decision.prior_state,
            "qualifying_event_ref": self.qualifying_event_ref,
            "rule_id": self.decision.rule_id,
            "rule_version": self.decision.rule_version,
            "rule_source_ref": self.decision.rule_source_ref,
            "new_mapping_ref": self.new_mapping_ref,
            "new_state": self.new_state,
            "eligibility_change": self.eligibility_change,
            "replaces": self.replaces,
            "closed": self.closed,
            "prior_lineage": list(self.prior_lineage),
            "event_time": self.event_time,
        }


def plan_rekey(
    *,
    snapshot: StateSnapshot,
    rule: TransitionRule,
    qualifying_event_ref: str,
    new_mapping_ref: str,
    new_state: str,
    eligibility_change: str,
    event_time: datetime,
    structural: bool,
    anchor_status: AnchorStatus | None = None,
    prior_range_ref: str | None = None,
    prior_lineage: tuple[str, ...] = (),
    evidence_refs: tuple[str, ...] = (),
    rekey_id: str | None = None,
    resulting_state_id: str | None = None,
) -> RekeyRecord:
    """Plan one structural rekey; every guard is earned, none is assumed."""

    if not isinstance(snapshot, StateSnapshot):
        raise StateContractError("plan_rekey requires a prior snapshot")
    if not structural:
        raise RekeyNotStructuralError(
            "a rekey requires a qualifying structural event; a touch or a "
            "threshold crossing alone does not authorize a remapping"
        )
    if anchor_status is not None:
        if not isinstance(anchor_status, AnchorStatus):
            raise StateContractError("anchor_status uses the frozen III.2 vocabulary")
        if anchor_status in _NON_STRUCTURAL_ANCHOR_STATES:
            raise RekeyFromUnresolvedAnchorError(
                f"anchor status {anchor_status.value} cannot authorize a rekey"
            )

    authority = authority_for(snapshot.model_id, snapshot.model_version)
    if authority.family == "EUR_DAILY" and new_state not in EUR_DAILY_LADDER:
        raise StateContractError(
            f"{new_state!r} is not a declared EUR Daily ladder state; the ladder "
            "steps are distinct and never collapsed"
        )

    decision = evaluate_transition(
        TransitionRequest(
            kind=TransitionKind.REKEY,
            prior_snapshot=snapshot,
            rule=rule,
            event_time=event_time,
            resulting_state=new_state,
            resulting_state_id=resulting_state_id or f"STATE.{new_state}",
            conditions=frozenset({Condition.STRUCTURAL_EVENT}),
            evidence_refs=evidence_refs,
            payload=(("qualifying_event", qualifying_event_ref),),
        )
    )

    lineage = tuple(prior_lineage)
    if not lineage:
        lineage = (snapshot.snapshot_id, snapshot.active_state)

    resolved_prior_range = prior_range_ref or (
        snapshot.active_ranges[0] if snapshot.active_ranges else ""
    )
    if not resolved_prior_range:
        raise StateContractError(
            "a rekey requires the prior range reference it replaces"
        )

    return RekeyRecord(
        rekey_id=rekey_id or f"REKEY.{snapshot.model_id}.{new_state}",
        decision=decision,
        prior_range_ref=resolved_prior_range,
        qualifying_event_ref=qualifying_event_ref,
        new_mapping_ref=new_mapping_ref,
        new_state=new_state,
        eligibility_change=eligibility_change,
        replaces=resolved_prior_range,
        closed=True,
        prior_lineage=lineage,
    )
