"""GLX FORGE Operator Setup Engine (Book III / Bloc III.5).

Consumes III.1 market data, III.2 measurements, III.3 model states and
III.4 state/path/locks **read-only**, and answers exactly one question:
may this canonical setup be considered eligible on this surface, under
these facts?

It answers with a four-valued, fail-closed verdict — ``ELIGIBLE``,
``WATCH``, ``BLOCKED`` or ``UNRESOLVED`` — plus bounded reasons, typed
triggers, three independent invalidations, ordered targets and evidence
references with status.

It never issues an order, a size, an allocation, a probability, a win
rate or an automation approval.  A valid model state is not a setup; a
valid setup is not automation authority; a refusal is a recorded result.
"""

from __future__ import annotations

from .contracts import (
    SEVERITY_ORDER,
    SETUP_RECORD_FIELDS,
    EvidenceReference,
    InvalidationKind,
    ParameterBinding,
    ParameterMaterialization,
    ParentStateRef,
    PriceInvalidation,
    PromotionCondition,
    SetupEligibility,
    SetupRecord,
    SetupSurface,
    SetupTarget,
    StructuralInvalidation,
    TemporalInvalidation,
    TransitionRef,
    TriggerCombination,
    TriggerLiteral,
    TriggerRequirement,
    TriggerType,
    payload_hash,
    worst_verdict,
)
from .eligibility import (
    GATE_ORDER,
    DataQualityFacts,
    GateOutcome,
    SetupClock,
    SetupEvaluation,
    SetupEvaluationRequest,
    TierBinding,
    evaluate_setup,
)
from .errors import (
    SETUP_REFUSAL_CODES,
    ClaimPopulationMismatchError,
    SetupContractError,
    SetupEngineError,
    SetupRefusalCode,
    SetupRegistryError,
    TargetPromotionRefused,
    UnsupportedStatisticError,
)
from .invalidation import (
    InvalidationEvents,
    InvalidationSet,
    active_kinds,
    resolve_invalidations,
)
from .registry import (
    CANONICAL_CARD_SOURCES,
    CANONICAL_SETUP_CARDS,
    CANONICAL_SETUP_IDS,
    CardStatus,
    CanonicalSetupCard,
    ParentRequirement,
    RegistryResolution,
    SetupRegistry,
    load_canonical_cards,
    project_status,
)
from .statistics import (
    FORBIDDEN_FIELD_NAMES,
    NUMERIC_RESULT_TYPES,
    SetupStatisticClaim,
    describe_relationship,
    describe_statistic,
)
from .targets import (
    first_delivery_order,
    order_targets,
    promote_target,
    validate_declared_targets,
)
from .triggers import TRIGGER_TYPES, TriggerObservation, TriggerSatisfaction, satisfies
from .versions import (
    SETUP_CONTRACT_VERSION,
    SETUP_ENGINE_MODULES,
    SETUP_ENGINE_VERSION,
    SETUP_ID_PATTERN,
    SETUP_INVALIDATION_VERSION,
    SETUP_TARGET_VERSION,
    SETUP_TRIGGER_VERSION,
)

__all__ = [
    "CANONICAL_CARD_SOURCES",
    "CANONICAL_SETUP_CARDS",
    "CANONICAL_SETUP_IDS",
    "CardStatus",
    "CanonicalSetupCard",
    "ClaimPopulationMismatchError",
    "DataQualityFacts",
    "EvidenceReference",
    "FORBIDDEN_FIELD_NAMES",
    "GATE_ORDER",
    "GateOutcome",
    "InvalidationEvents",
    "InvalidationKind",
    "InvalidationSet",
    "NUMERIC_RESULT_TYPES",
    "ParameterBinding",
    "ParameterMaterialization",
    "ParentRequirement",
    "ParentStateRef",
    "PriceInvalidation",
    "PromotionCondition",
    "RegistryResolution",
    "SEVERITY_ORDER",
    "SETUP_CONTRACT_VERSION",
    "SETUP_ENGINE_MODULES",
    "SETUP_ENGINE_VERSION",
    "SETUP_ID_PATTERN",
    "SETUP_INVALIDATION_VERSION",
    "SETUP_RECORD_FIELDS",
    "SETUP_REFUSAL_CODES",
    "SETUP_TARGET_VERSION",
    "SETUP_TRIGGER_VERSION",
    "SetupClock",
    "SetupContractError",
    "SetupEligibility",
    "SetupEngineError",
    "SetupEvaluation",
    "SetupEvaluationRequest",
    "SetupRecord",
    "SetupRefusalCode",
    "SetupRegistry",
    "SetupRegistryError",
    "SetupStatisticClaim",
    "SetupSurface",
    "SetupTarget",
    "StructuralInvalidation",
    "TRIGGER_TYPES",
    "TargetPromotionRefused",
    "TemporalInvalidation",
    "TierBinding",
    "TransitionRef",
    "TriggerCombination",
    "TriggerLiteral",
    "TriggerObservation",
    "TriggerRequirement",
    "TriggerSatisfaction",
    "TriggerType",
    "UnsupportedStatisticError",
    "active_kinds",
    "describe_relationship",
    "describe_statistic",
    "evaluate_setup",
    "first_delivery_order",
    "load_canonical_cards",
    "order_targets",
    "payload_hash",
    "project_status",
    "promote_target",
    "resolve_invalidations",
    "satisfies",
    "validate_declared_targets",
    "worst_verdict",
]
