"""Path invariants (Ch III.4.10).

These are structural assertions over records that were already earned by
the guards.  They exist so that a terminal outcome can never quietly
erase the path that produced it, and so that replay determinism is
checked rather than assumed.
"""

from __future__ import annotations

from typing import Callable

from .delivery import DeliveryPath, TerminalReach
from .errors import StateContractError, TransitionNotEarnedError
from .handoff import LayerHandoff, OwnershipScope
from .history import TransitionLedger, history_hash, verify_history
from .rekey import RekeyRecord
from .stand_down import StandDownRecord, assert_setup_eligibility_allowed
from .vocabulary import TransitionKind

__all__ = [
    "assert_deterministic_replay",
    "assert_layer_isolation",
    "assert_no_go_blocks_eligibility",
    "assert_paths_differ_under_reversal",
    "assert_rekey_explicit",
    "assert_target_order_stable",
    "assert_terminal_does_not_erase_path",
    "assert_unearned_refused",
]


def assert_terminal_does_not_erase_path(path: DeliveryPath) -> None:
    """A terminal both-side reach must still carry its delivery sequence."""

    if not isinstance(path, DeliveryPath):
        raise StateContractError("expected a DeliveryPath")
    if path.terminal_reach is TerminalReach.BOTH_SIDES_REACHED:
        if len(path.deliveries) < 2:
            raise StateContractError(
                "a both-side terminal reach must retain both deliveries"
            )
        if path.first_delivery is None:
            raise StateContractError(
                "a both-side terminal reach must retain its first delivery"
            )
        if path.first_delivery.target_id != path.deliveries[0].target_id:
            raise StateContractError(
                "the retained first delivery must be the first ordered delivery"
            )


def assert_target_order_stable(first: DeliveryPath, second: DeliveryPath) -> None:
    """The declared target order must not drift between two recordings."""

    a = tuple(
        (target.target_id, target.declared_order_index) for target in first.targets
    )
    b = tuple(
        (target.target_id, target.declared_order_index) for target in second.targets
    )
    if a != b:
        raise StateContractError("declared target order drifted between recordings")


def assert_paths_differ_under_reversal(
    first: DeliveryPath, second: DeliveryPath, compute_hash: Callable[[dict], str]
) -> None:
    """Same terminal result, different order ⇒ different record."""

    assert_target_order_stable(first, second)
    if first.terminal_result != second.terminal_result:
        raise StateContractError(
            "reversal comparison requires the same terminal result"
        )
    if first.delivery_order == second.delivery_order:
        raise StateContractError("the two paths are not reversals")
    if compute_hash(first.to_payload()) == compute_hash(second.to_payload()):
        raise StateContractError(
            "reversed paths must not hash identically; the terminal result "
            "cannot erase the path"
        )


def assert_rekey_explicit(record: RekeyRecord) -> None:
    """A rekey must be an explicit, closed remapping with lineage."""

    if not isinstance(record, RekeyRecord):
        raise StateContractError("expected a RekeyRecord")
    if record.decision.kind is not TransitionKind.REKEY:
        raise StateContractError("a rekey record must wrap a REKEY decision")
    if not record.closed:
        raise StateContractError("a rekey must close/replace the prior mapping")
    if record.replaces != record.prior_range_ref:
        raise StateContractError("a rekey must replace the mapping it names")
    if record.prior_range_ref == record.new_mapping_ref:
        raise StateContractError("a rekey must produce a new mapping")
    if not record.prior_lineage:
        raise StateContractError("a rekey must preserve its prior-state lineage")


def assert_no_go_blocks_eligibility(record: StandDownRecord) -> None:
    """A stand-down record must lock eligibility, and eligibility must refuse."""

    if not isinstance(record, StandDownRecord):
        raise StateContractError("expected a StandDownRecord")
    if not record.eligibility_lock:
        raise StateContractError("a stand-down must carry the eligibility lock")
    assert_setup_eligibility_allowed(record)  # always raises


def assert_layer_isolation(handoff: LayerHandoff) -> None:
    """Ownership must be typed on the record and never upward."""

    if not isinstance(handoff, LayerHandoff):
        raise StateContractError("expected a LayerHandoff")
    if handoff.source_layer.value == "L1" and handoff.destination_layer.value in (
        "L2",
        "L3",
    ):
        raise StateContractError("L1 can never hand anything upward")
    expected = (
        OwnershipScope.PATH
        if handoff.destination_layer.value == "L2"
        else OwnershipScope.EXECUTION
    )
    if handoff.ownership is not expected:
        raise StateContractError(
            "handoff ownership must follow the destination layer"
        )


def assert_deterministic_replay(
    first: TransitionLedger, second: TransitionLedger
) -> None:
    """Two replays of identical ordered events must hash identically."""

    verify_history(first)
    verify_history(second)
    if first.event_hashes != second.event_hashes:
        raise StateContractError(
            "identical ordered events produced different event hashes"
        )
    if first.history_hash != second.history_hash:
        raise StateContractError("identical ordered events produced different hashes")
    if first.history_hash != history_hash(
        genesis_snapshot_hash=second.genesis_snapshot_hash, events=second.events
    ):
        raise StateContractError("history hash does not reproduce")


def assert_unearned_refused(action: Callable[[], object]) -> None:
    """A transition that cannot be earned must refuse, not degrade."""

    try:
        action()
    except TransitionNotEarnedError:
        return
    except Exception as exc:  # noqa: BLE001 - refusal by any coded error is fine
        if getattr(exc, "code", None):
            return
        raise
    raise TransitionNotEarnedError("an unearned transition was accepted")
