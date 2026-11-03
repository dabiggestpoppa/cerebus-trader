"""Bounded refusal vocabulary for the Bloc III.4 state/path engine.

Every refusal is an explicit coded error.  There is no partial output, no
silent fallback and no default rule anywhere in this package.

Upstream codes are **reused**, never redefined: ``RULE_NOT_MATERIALIZED``,
``MODEL_VERSION_UNAVAILABLE``, ``PRIOR_STATE_MISMATCH``,
``DATA_QUALITY_BLOCKED``, ``NO_CALCULATION`` and ``REPLAY_HASH_MISMATCH``
belong to Bloc III.3 and mean the same thing here, so the classes are
imported from ``app.forge.model_runtime`` and re-exported.  III.4's own
refusals get their own codes below.
"""

from __future__ import annotations

from app.forge.model_runtime import (
    DataQualityBlockedError,
    ModelVersionUnavailableError,
    NoCalculationError,
    PriorStateMismatchError,
    ReplayHashMismatchError,
    RuleNotMaterializedError,
)

__all__ = [
    "STATE_ENGINE_CODES",
    "AcceptWithoutTouchError",
    "AmbiguousPathError",
    "CompressionWithoutFailureError",
    "ConsumedStateReopenedError",
    "ConsumedTargetRequotedError",
    "DataQualityBlockedError",
    "EligibilityWithoutAuthorityError",
    "EvidenceRequiredError",
    "FailureGrammarNotDeclaredError",
    "FailureWithoutAcceptanceError",
    "HistoryChainMismatchError",
    "HistorySequenceGapError",
    "LayerHandoffDirectionError",
    "LayerOwnershipViolationError",
    "ModelVersionUnavailableError",
    "NoCalculationError",
    "PriorStateMismatchError",
    "PromotionWithoutAuthorityError",
    "ReleaseWithoutCompressionError",
    "RekeyFromUnresolvedAnchorError",
    "RekeyNotStructuralError",
    "ReleaseWithoutCompressionError",
    "ReplayHashMismatchError",
    "ReplayReconstructionMismatchError",
    "RepairWithoutFailureError",
    "RuleNotMaterializedError",
    "SourceLineageMissingError",
    "StateContractError",
    "StateEngineError",
    "TargetNotDeclaredError",
    "TransitionAuthorityMismatchError",
    "TransitionNotInFamilyVocabularyError",
    "TransitionNotEarnedError",
    "TransitionNoOpError",
    "TransitionOrderAmbiguousError",
    "TransitionPairForbiddenError",
    "UnconditionalFrequencyRefusedError",
]


class StateEngineError(Exception):
    """Base class for every III.4 refusal."""

    code = "STATE_ENGINE_ERROR"

    def __init__(self, message: str = "") -> None:
        super().__init__(message or self.code)


class StateContractError(StateEngineError):
    """A record or request violates the frozen III.4 contract."""

    code = "STATE_CONTRACT"


class SourceLineageMissingError(StateEngineError):
    """The transition has no valid source lineage (unfinalized/absent)."""

    code = "SOURCE_LINEAGE_MISSING"


class TransitionNotInFamilyVocabularyError(StateEngineError):
    """The kind is outside the family's declared transition vocabulary."""

    code = "TRANSITION_NOT_IN_FAMILY_VOCABULARY"


class TransitionNotEarnedError(StateEngineError):
    """The prior state does not qualify, or no rule earns the transition."""

    code = "TRANSITION_NOT_EARNED"


class TransitionAuthorityMismatchError(StateEngineError):
    """A rule/source belonging to another family or model was applied."""

    code = "TRANSITION_AUTHORITY_MISMATCH"


class TransitionNoOpError(StateEngineError):
    """The transition would not change the state."""

    code = "TRANSITION_NO_OP"


class TransitionOrderAmbiguousError(StateEngineError):
    """Two events share an event time without a declared order."""

    code = "TRANSITION_ORDER_AMBIGUOUS"


class TransitionPairForbiddenError(StateEngineError):
    """The (prior state, resulting state) pair is canonically forbidden."""

    code = "TRANSITION_PAIR_FORBIDDEN"


class AcceptWithoutTouchError(StateEngineError):
    """Acceptance claimed without a qualifying touched fact (invariant #6)."""

    code = "ACCEPT_WITHOUT_TOUCH"


class FailureWithoutAcceptanceError(StateEngineError):
    """Failure claimed without a prior valid acceptance."""

    code = "FAILURE_WITHOUT_ACCEPTANCE"


class RepairWithoutFailureError(StateEngineError):
    """Repair claimed without a prior failure."""

    code = "REPAIR_WITHOUT_FAILURE"


class CompressionWithoutFailureError(StateEngineError):
    """Compression claimed without a prior failure/repair."""

    code = "COMPRESSION_WITHOUT_FAILURE"


class ReleaseWithoutCompressionError(StateEngineError):
    """Release claimed without a prior compression."""

    code = "RELEASE_WITHOUT_COMPRESSION"


class FailureGrammarNotDeclaredError(StateEngineError):
    """The family/generation declares no failure/repair grammar."""

    code = "FAILURE_GRAMMAR_NOT_DECLARED"


class RekeyNotStructuralError(StateEngineError):
    """A bare touch/threshold crossing is not a structural rekey."""

    code = "REKEY_NOT_STRUCTURAL"


class RekeyFromUnresolvedAnchorError(StateEngineError):
    """Rekey from an unresolved/invalidated anchor is not authorized."""

    code = "REKEY_FROM_UNRESOLVED_ANCHOR"


class LayerHandoffDirectionError(StateEngineError):
    """A handoff skipped or reversed the L3 -> L2 -> L1 direction."""

    code = "LAYER_HANDOFF_DIRECTION"


class LayerOwnershipViolationError(StateEngineError):
    """A lower layer attempted to own or mutate a higher-layer record."""

    code = "LAYER_OWNERSHIP_VIOLATION"


class AmbiguousPathError(StateEngineError):
    """Intrabar ordering cannot be resolved from the supplied evidence."""

    code = "AMBIGUOUS_PATH"


class TargetNotDeclaredError(StateEngineError):
    """A delivery was recorded for a target that was never declared."""

    code = "TARGET_NOT_DECLARED"


class UnconditionalFrequencyRefusedError(StateEngineError):
    """An unconditional historical frequency was offered as range-left."""

    code = "UNCONDITIONAL_FREQUENCY_REFUSED"


class ConsumedTargetRequotedError(StateEngineError):
    """A consumed target was offered again as available."""

    code = "CONSUMED_TARGET_REQUOTED"


class ConsumedStateReopenedError(StateEngineError):
    """An exhausted state was silently re-opened."""

    code = "CONSUMED_STATE_REOPENED"


class EvidenceRequiredError(StateEngineError):
    """The family's rule requires evidence references on this transition."""

    code = "EVIDENCE_REQUIRED"


class EligibilityWithoutAuthorityError(StateEngineError):
    """A stand-down state was followed by an eligibility-bearing transition."""

    code = "ELIGIBILITY_WITHOUT_AUTHORITY"


class PromotionWithoutAuthorityError(StateEngineError):
    """A promotion was claimed without evidence and a declared rule."""

    code = "PROMOTION_WITHOUT_AUTHORITY"


class HistorySequenceGapError(StateEngineError):
    """The append-only sequence is not gapless/ordered."""

    code = "HISTORY_SEQUENCE_GAP"


class HistoryChainMismatchError(StateEngineError):
    """The hash chain does not reproduce (reorder/insert/rewrite)."""

    code = "HISTORY_CHAIN_MISMATCH"


class ReplayReconstructionMismatchError(StateEngineError):
    """Replaying the ledger did not reproduce the recorded state."""

    code = "REPLAY_RECONSTRUCTION_MISMATCH"


#: The complete III.4-owned code set (upstream codes excluded on purpose).
STATE_ENGINE_CODES: tuple[str, ...] = (
    "STATE_ENGINE_ERROR",
    "STATE_CONTRACT",
    "SOURCE_LINEAGE_MISSING",
    "TRANSITION_NOT_IN_FAMILY_VOCABULARY",
    "TRANSITION_NOT_EARNED",
    "TRANSITION_AUTHORITY_MISMATCH",
    "TRANSITION_NO_OP",
    "TRANSITION_ORDER_AMBIGUOUS",
    "TRANSITION_PAIR_FORBIDDEN",
    "ACCEPT_WITHOUT_TOUCH",
    "FAILURE_WITHOUT_ACCEPTANCE",
    "REPAIR_WITHOUT_FAILURE",
    "COMPRESSION_WITHOUT_FAILURE",
    "RELEASE_WITHOUT_COMPRESSION",
    "FAILURE_GRAMMAR_NOT_DECLARED",
    "REKEY_NOT_STRUCTURAL",
    "REKEY_FROM_UNRESOLVED_ANCHOR",
    "LAYER_HANDOFF_DIRECTION",
    "LAYER_OWNERSHIP_VIOLATION",
    "AMBIGUOUS_PATH",
    "TARGET_NOT_DECLARED",
    "UNCONDITIONAL_FREQUENCY_REFUSED",
    "CONSUMED_TARGET_REQUOTED",
    "CONSUMED_STATE_REOPENED",
    "ELIGIBILITY_WITHOUT_AUTHORITY",
    "EVIDENCE_REQUIRED",
    "PROMOTION_WITHOUT_AUTHORITY",
    "HISTORY_SEQUENCE_GAP",
    "HISTORY_CHAIN_MISMATCH",
    "REPLAY_RECONSTRUCTION_MISMATCH",
)
