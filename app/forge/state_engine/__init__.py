"""CEREBUS State, Path & Transition Engine (Book III / Bloc III.4).

This package records **how** model state moved, not merely where it
ended.  It consumes Bloc III.3 model outputs read-only and adds:

* immutable, versioned ``StateSnapshot`` records (Ch III.4.1);
* the frozen twelve-kind transition vocabulary with earned-transition
  guards — qualifying prior state, canonical rule, valid source lineage
  and model-specific authority (Ch III.4.2);
* ordered first-delivery recording that never invents intrabar
  chronology (Ch III.4.3);
* a declared failure/repair grammar (Ch III.4.4);
* structural rekey as an explicit remapping (Ch III.4.5);
* formal L3 -> L2 -> L1 handoffs with typed ownership (Ch III.4.6);
* conditional range-left (Ch III.4.7);
* bounded no-go/stand-down states with an eligibility lock (Ch III.4.8);
* an append-only ordered transition history with replay hashing
  (Ch III.4.9);
* path-invariant assertions (Ch III.4.10).

Boundaries: no model interpretation, no measurement, no setup, no
execution, no probability or confidence field, no API surface, no
persistence migration, no provider, no network, no wall clock.  Model
state is never trade eligibility, and a transition never manufactures the
authority of a downstream layer.
"""

from __future__ import annotations

from .versions import STATE_ENGINE_VERSION
from .errors import (
    STATE_ENGINE_CODES,
    AcceptWithoutTouchError,
    AmbiguousPathError,
    CompressionWithoutFailureError,
    ConsumedStateReopenedError,
    ConsumedTargetRequotedError,
    DataQualityBlockedError,
    EligibilityWithoutAuthorityError,
    EvidenceRequiredError,
    FailureGrammarNotDeclaredError,
    FailureWithoutAcceptanceError,
    HistoryChainMismatchError,
    HistorySequenceGapError,
    LayerHandoffDirectionError,
    LayerOwnershipViolationError,
    ModelVersionUnavailableError,
    NoCalculationError,
    PriorStateMismatchError,
    PromotionWithoutAuthorityError,
    RekeyFromUnresolvedAnchorError,
    RekeyNotStructuralError,
    ReleaseWithoutCompressionError,
    ReplayHashMismatchError,
    ReplayReconstructionMismatchError,
    RepairWithoutFailureError,
    RuleNotMaterializedError,
    SourceLineageMissingError,
    StateContractError,
    StateEngineError,
    TargetNotDeclaredError,
    TransitionAuthorityMismatchError,
    TransitionNotEarnedError,
    TransitionNotInFamilyVocabularyError,
    TransitionNoOpError,
    TransitionOrderAmbiguousError,
    TransitionPairForbiddenError,
    UnconditionalFrequencyRefusedError,
)
from .snapshot import (
    MeasurementRef,
    StateSnapshot,
    finalize_snapshot,
    snapshot_payload,
)
from .stand_down import (
    CAPABILITIES_LOCKED,
    NO_GO_MAPPING,
    STAND_DOWN_STATES,
    StandDownReason,
    StandDownRecord,
    StandDownState,
    assert_setup_eligibility_allowed,
    stand_down_for_no_go,
)
from .vocabulary import (
    FAMILY_STATES,
    TRANSITION_AUTHORITY,
    Condition,
    QualifyingPriorState,
    TransitionAuthority,
    TransitionDecision,
    TransitionKind,
    TransitionRequest,
    TransitionRule,
    authority_for,
    evaluate_transition,
)
from .delivery import (
    DeclaredTarget,
    DeliveryObservation,
    DeliveryPath,
    DeliveryRecord,
    DeliverySide,
    FirstDelivery,
    TerminalReach,
    build_path,
    path_hash,
    target_order,
)
from .failure_repair import (
    FAILURE_GRAMMARS,
    FailureGrammar,
    FailureRecord,
    FailureState,
    advance_failure,
    failure_grammar_for,
    start_failure_chain,
)
from .rekey import EUR_DAILY_LADDER, RekeyRecord, plan_rekey
from .handoff import (
    HandoffAgreement,
    LayerHandoff,
    OwnershipScope,
    build_handoff,
    layer_conflict_facts,
)
from .range_left import (
    ConditionalRangeLeft,
    ConsumedEvent,
    RangeLeftCondition,
    from_historical_frequency,
    recompute_range_left,
)
from .history import (
    NEGATIVE_KINDS,
    TransitionEvent,
    TransitionLedger,
    append_event,
    explain,
    history_hash,
    open_ledger,
    reconstruct_state,
    replay_events,
    state_at,
    verify_history,
)
from .invariants import (
    assert_deterministic_replay,
    assert_layer_isolation,
    assert_no_go_blocks_eligibility,
    assert_paths_differ_under_reversal,
    assert_rekey_explicit,
    assert_target_order_stable,
    assert_terminal_does_not_erase_path,
    assert_unearned_refused,
)

__all__ = [
    "CAPABILITIES_LOCKED",
    "EUR_DAILY_LADDER",
    "FAILURE_GRAMMARS",
    "FAMILY_STATES",
    "NEGATIVE_KINDS",
    "NO_GO_MAPPING",
    "STAND_DOWN_STATES",
    "STATE_ENGINE_CODES",
    "STATE_ENGINE_VERSION",
    "TRANSITION_AUTHORITY",
    "AcceptWithoutTouchError",
    "AmbiguousPathError",
    "CompressionWithoutFailureError",
    "Condition",
    "ConditionalRangeLeft",
    "ConsumedEvent",
    "ConsumedStateReopenedError",
    "ConsumedTargetRequotedError",
    "DataQualityBlockedError",
    "DeclaredTarget",
    "DeliveryObservation",
    "DeliveryPath",
    "DeliveryRecord",
    "DeliverySide",
    "EligibilityWithoutAuthorityError",
    "EvidenceRequiredError",
    "FailureGrammar",
    "FailureGrammarNotDeclaredError",
    "FailureRecord",
    "FailureState",
    "FailureWithoutAcceptanceError",
    "FirstDelivery",
    "HandoffAgreement",
    "HistoryChainMismatchError",
    "HistorySequenceGapError",
    "LayerHandoff",
    "LayerHandoffDirectionError",
    "LayerOwnershipViolationError",
    "MeasurementRef",
    "ModelVersionUnavailableError",
    "NoCalculationError",
    "OwnershipScope",
    "PromotionWithoutAuthorityError",
    "PriorStateMismatchError",
    "QualifyingPriorState",
    "RangeLeftCondition",
    "RekeyFromUnresolvedAnchorError",
    "RekeyNotStructuralError",
    "RekeyRecord",
    "ReleaseWithoutCompressionError",
    "ReplayHashMismatchError",
    "ReplayReconstructionMismatchError",
    "RepairWithoutFailureError",
    "RuleNotMaterializedError",
    "SourceLineageMissingError",
    "StandDownReason",
    "StandDownRecord",
    "StandDownState",
    "StateContractError",
    "StateEngineError",
    "StateSnapshot",
    "TargetNotDeclaredError",
    "TerminalReach",
    "TransitionAuthority",
    "TransitionAuthorityMismatchError",
    "TransitionDecision",
    "TransitionEvent",
    "TransitionKind",
    "TransitionLedger",
    "TransitionNoOpError",
    "TransitionNotEarnedError",
    "TransitionNotInFamilyVocabularyError",
    "TransitionOrderAmbiguousError",
    "TransitionPairForbiddenError",
    "TransitionRequest",
    "TransitionRule",
    "UnconditionalFrequencyRefusedError",
    "advance_failure",
    "append_event",
    "assert_deterministic_replay",
    "assert_layer_isolation",
    "assert_no_go_blocks_eligibility",
    "assert_paths_differ_under_reversal",
    "assert_rekey_explicit",
    "assert_setup_eligibility_allowed",
    "assert_target_order_stable",
    "assert_terminal_does_not_erase_path",
    "assert_unearned_refused",
    "authority_for",
    "build_handoff",
    "build_path",
    "evaluate_transition",
    "explain",
    "failure_grammar_for",
    "finalize_snapshot",
    "from_historical_frequency",
    "history_hash",
    "layer_conflict_facts",
    "open_ledger",
    "path_hash",
    "plan_rekey",
    "recompute_range_left",
    "reconstruct_state",
    "replay_events",
    "snapshot_payload",
    "stand_down_for_no_go",
    "start_failure_chain",
    "state_at",
    "target_order",
    "verify_history",
]
