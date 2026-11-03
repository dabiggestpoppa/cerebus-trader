"""No-go / stand-down states (Ch III.4.8).

A stand-down is a **stateful output with a reason**, not an exception and
not an empty result.  It carries the bounded state, the bounded reason,
the blocking rule reference and an explicit *eligibility lock* that
downstream setup layers must respect.

The lock is a structural fact: III.4 never converts a no-go into setup
eligibility, and :func:`assert_setup_eligibility_allowed` refuses rather
than warns.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Mapping

from app.forge.model_runtime import NoGoReason

from .errors import (
    EligibilityWithoutAuthorityError,
    StateContractError,
)

__all__ = [
    "CAPABILITIES_LOCKED",
    "NO_GO_MAPPING",
    "StandDownReason",
    "StandDownRecord",
    "StandDownState",
    "assert_setup_eligibility_allowed",
    "stand_down_for_no_go",
]


class StandDownState(str, Enum):
    """The six bounded stand-down states (frozen Ch III.4.8 set)."""

    DATA_QUALITY_FAILURE = "DATA_QUALITY_FAILURE"
    INVALID_RANGE = "INVALID_RANGE"
    UNRESOLVED_ANCHOR = "UNRESOLVED_ANCHOR"
    MODEL_CONFLICT = "MODEL_CONFLICT"
    PARKED_OR_EXHAUSTED = "PARKED_OR_EXHAUSTED"
    EVIDENCE_UNAVAILABLE = "EVIDENCE_UNAVAILABLE"


#: Every stand-down state, as the transition guards see them.
STAND_DOWN_STATES: frozenset[str] = frozenset(state.value for state in StandDownState)


class StandDownReason(str, Enum):
    """Bounded reasons (no free text anywhere — invariant #18)."""

    RANGE_TOO_LARGE = "RANGE_TOO_LARGE"
    DATA_BAD = "DATA_BAD"
    ANCHOR_UNRESOLVED = "ANCHOR_UNRESOLVED"
    CONFLICTING_RULE = "CONFLICTING_RULE"
    EXHAUSTED_OR_PARKED = "EXHAUSTED_OR_PARKED"
    INSUFFICIENT_EVIDENCE = "INSUFFICIENT_EVIDENCE"


#: Capabilities a stand-down locks.  Structural, not advisory.
CAPABILITIES_LOCKED: frozenset[str] = frozenset(
    {"SETUP_ELIGIBILITY", "EXECUTION_AUTHORITY"}
)

#: Frozen III.3 no-go vocabulary mapped onto III.4 stand-down states.
NO_GO_MAPPING: Mapping[NoGoReason, tuple[StandDownState, StandDownReason]] = {
    NoGoReason.AR_SOURCE_NO_GO: (
        StandDownState.INVALID_RANGE,
        StandDownReason.RANGE_TOO_LARGE,
    ),
    NoGoReason.ASIAN_RANGE_NO_GO: (
        StandDownState.INVALID_RANGE,
        StandDownReason.RANGE_TOO_LARGE,
    ),
    NoGoReason.NATIVE_TIER_NO_GO: (
        StandDownState.INVALID_RANGE,
        StandDownReason.RANGE_TOO_LARGE,
    ),
    NoGoReason.RULE_NOT_MATERIALIZED: (
        StandDownState.UNRESOLVED_ANCHOR,
        StandDownReason.ANCHOR_UNRESOLVED,
    ),
    NoGoReason.PROMOTION_PARKED: (
        StandDownState.PARKED_OR_EXHAUSTED,
        StandDownReason.EXHAUSTED_OR_PARKED,
    ),
}


@dataclass(frozen=True)
class StandDownRecord:
    """A recorded stand-down, with its reason and capability lock."""

    state: StandDownState
    reason: StandDownReason
    blocking_rule_ref: str
    snapshot_id: str
    capabilities_locked: frozenset[str] = CAPABILITIES_LOCKED

    def __post_init__(self) -> None:
        if not isinstance(self.state, StandDownState):
            raise StateContractError("a stand-down carries a bounded state")
        if not isinstance(self.reason, StandDownReason):
            raise StateContractError("a stand-down carries a bounded reason")
        if not self.blocking_rule_ref:
            raise StateContractError("a stand-down names its blocking rule")
        if not self.snapshot_id:
            raise StateContractError("a stand-down names its snapshot")
        if not self.capabilities_locked:
            raise StateContractError("a stand-down always locks capabilities")

    @property
    def eligibility_lock(self) -> bool:
        """The downstream eligibility lock — always true for a stand-down."""

        return "SETUP_ELIGIBILITY" in self.capabilities_locked

    def to_payload(self) -> dict:
        return {
            "state": self.state.value,
            "reason": self.reason.value,
            "blocking_rule_ref": self.blocking_rule_ref,
            "snapshot_id": self.snapshot_id,
            "capabilities_locked": sorted(self.capabilities_locked),
            "eligibility_lock": self.eligibility_lock,
        }


def stand_down_for_no_go(
    reason: NoGoReason,
    *,
    blocking_rule_ref: str,
    snapshot_id: str,
) -> StandDownRecord:
    """Map a frozen III.3 no-go code onto a bounded III.4 stand-down."""

    try:
        state, mapped = NO_GO_MAPPING[reason]
    except KeyError:  # pragma: no cover - defensive, enum is closed
        raise StateContractError(f"unmapped no-go reason {reason!r}") from None
    return StandDownRecord(
        state=state,
        reason=mapped,
        blocking_rule_ref=blocking_rule_ref,
        snapshot_id=snapshot_id,
    )


def assert_setup_eligibility_allowed(record: StandDownRecord | None) -> None:
    """Refuse eligibility while a stand-down lock is in force.

    A ``None`` record means no stand-down is active; anything else is a
    lock and therefore a refusal (invariant: no-go cannot silently become
    executable eligibility).
    """

    if record is None:
        return
    if not isinstance(record, StandDownRecord):
        raise StateContractError("expected a StandDownRecord or None")
    raise EligibilityWithoutAuthorityError(
        f"stand-down {record.state.value} ({record.reason.value}) locks "
        f"setup eligibility via {record.blocking_rule_ref}"
    )
