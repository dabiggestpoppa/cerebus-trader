"""The single eligibility authority (Ch III.5.2).

Eleven ordered gates, one total precedence, no caller-settable verdict:

1 registry → 2 III.4 stand-down lock → 3 model state → 4 anchor →
5 tier → 6 clock/session → 7 higher layer → 8 data quality →
9 parameter materialisation → 10 trigger → 11 invalidation.

Precedence is ``BLOCKED > UNRESOLVED > WATCH > ELIGIBLE``.  Every gate
that produces a non-positive verdict contributes a bounded reason code,
and the result is the most severe gate verdict — so ``ELIGIBLE`` is
reachable only when *every* gate passes affirmatively.

The III.4 lock is invoked first-class through
:func:`app.forge.state_engine.stand_down.assert_setup_eligibility_allowed`
and can never be downgraded to a warning.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal

from app.forge.market_data import DataOutcome
from app.forge.measurements.anchors import AnchorEligibility, AnchorStatus, RuleMaterialization
from app.forge.model_runtime.contract import (
    DirectionBias,
    DirectionSide,
    Layer,
    ModelOutput,
)
from app.forge.state_engine.errors import EligibilityWithoutAuthorityError
from app.forge.state_engine.stand_down import (
    StandDownRecord,
    assert_setup_eligibility_allowed,
)

from .contracts import (
    EvidenceReference,
    InvalidationKind,
    ParameterMaterialization,
    ParentStateRef,
    SetupEligibility,
    SetupRecord,
    SetupSurface,
    SetupTarget,
    TransitionRef,
    TriggerType,
    worst_verdict,
)
from .errors import SetupContractError, SetupRefusalCode
from .invalidation import (
    InvalidationEvents,
    InvalidationSet,
    resolve_invalidations,
)
from .registry import CanonicalSetupCard, SetupRegistry
from .targets import order_targets
from .triggers import TriggerObservation, satisfies

__all__ = [
    "GATE_ORDER",
    "DataQualityFacts",
    "GateOutcome",
    "SetupClock",
    "SetupEvaluation",
    "SetupEvaluationRequest",
    "TierBinding",
    "evaluate_setup",
]

#: The ordered gate chain (documented order, asserted by the suite).
GATE_ORDER: tuple[str, ...] = (
    "REGISTRY",
    "STAND_DOWN",
    "MODEL_STATE",
    "ANCHOR",
    "TIER",
    "CLOCK",
    "HIGHER_LAYER",
    "DATA_QUALITY",
    "PARAMETERS",
    "TRIGGER",
    "INVALIDATION",
)

_PASS = SetupEligibility.ELIGIBLE


@dataclass(frozen=True)
class SetupClock:
    """The injected session/checkpoint state (never wall time)."""

    session_id: str
    checkpoint: str
    resolved: bool = True
    checkpoint_reached: bool = True

    def __post_init__(self) -> None:
        if not self.session_id or not self.checkpoint:
            raise SetupContractError("a clock names its session and checkpoint")


@dataclass(frozen=True)
class TierBinding:
    """The tier the setup is evaluated against, and its native status."""

    tier_id: str
    native: bool = True
    no_go: bool = False

    def __post_init__(self) -> None:
        if not self.tier_id:
            raise SetupContractError("a tier binding names its tier")


@dataclass(frozen=True)
class DataQualityFacts:
    """Bar/data quality facts supplied by the governed source."""

    final_bar: bool = True
    stale: bool = False
    gapped: bool = False

    @property
    def acceptable(self) -> bool:
        return self.final_bar and not self.stale and not self.gapped


@dataclass(frozen=True)
class GateOutcome:
    """One gate's recorded outcome."""

    gate: str
    verdict: SetupEligibility
    codes: tuple[SetupRefusalCode, ...] = ()

    @property
    def passed(self) -> bool:
        return self.verdict is SetupEligibility.ELIGIBLE


@dataclass(frozen=True)
class SetupEvaluationRequest:
    """Everything one evaluation may read — a closed, immutable envelope."""

    setup_id: str
    setup_version: str | None
    surface: SetupSurface
    parents: tuple[ModelOutput, ...] = ()
    anchors: tuple[AnchorEligibility, ...] = ()
    stand_down: StandDownRecord | None = None
    clock: SetupClock | None = None
    data_quality: DataQualityFacts = field(default_factory=DataQualityFacts)
    data_outcome: DataOutcome | None = None
    parameters: tuple[object, ...] = ()
    observations: tuple[TriggerObservation, ...] = ()
    invalidation_events: InvalidationEvents = field(default_factory=InvalidationEvents)
    targets: tuple[SetupTarget, ...] = ()
    transitions: tuple[TransitionRef, ...] = ()
    evidence: tuple[EvidenceReference, ...] = ()
    tier: TierBinding | None = None
    evaluation_time: str = "1970-01-01T00:00:00Z"

    def parameter(self, name: str) -> object | None:
        for binding in self.parameters:
            if getattr(binding, "name", None) == name:
                return binding
        return None

    def primary_parent(self, card: CanonicalSetupCard) -> ModelOutput | None:
        for parent in self.parents:
            if parent.model_id in card.parent_model_ids:
                return parent
        return None


@dataclass(frozen=True)
class SetupEvaluation:
    """The recorded evaluation: verdict, bounded reasons, per-gate outcomes."""

    setup_id: str
    setup_version: str | None
    surface: SetupSurface
    card: CanonicalSetupCard | None
    eligibility: SetupEligibility
    reasons: tuple[SetupRefusalCode, ...]
    gates: tuple[GateOutcome, ...]
    record: SetupRecord | None

    @property
    def automation_permitted(self) -> bool:
        return False if self.record is None else self.record.automation_permitted


# ---------------------------------------------------------------------------
# Gates
# ---------------------------------------------------------------------------


def _stand_down_gate(record: StandDownRecord | None) -> GateOutcome:
    try:
        assert_setup_eligibility_allowed(record)
    except EligibilityWithoutAuthorityError:
        return GateOutcome(
            "STAND_DOWN",
            SetupEligibility.BLOCKED,
            (SetupRefusalCode.STAND_DOWN_LOCKED,),
        )
    return GateOutcome("STAND_DOWN", _PASS)


def _model_state_gate(
    card: CanonicalSetupCard, request: SetupEvaluationRequest
) -> GateOutcome:
    codes: list[SetupRefusalCode] = []
    verdict = _PASS
    for requirement in card.parent_requirements:
        parent = next(
            (item for item in request.parents if item.model_id == requirement.model_id),
            None,
        )
        if parent is None:
            codes.append(SetupRefusalCode.PARENT_STATE_MISSING)
            verdict = worst_verdict((verdict, SetupEligibility.UNRESOLVED))
            continue
        if parent.model_version != requirement.model_version:
            codes.append(SetupRefusalCode.MODEL_VERSION_UNAVAILABLE)
            verdict = worst_verdict((verdict, SetupEligibility.UNRESOLVED))
            continue
        if (
            requirement.required_layer is not None
            and parent.layer is not requirement.required_layer
        ):
            codes.append(SetupRefusalCode.WRONG_LAYER_PARENT)
            verdict = worst_verdict((verdict, SetupEligibility.BLOCKED))
            continue
        if parent.model_state == "UNRESOLVED":
            codes.append(SetupRefusalCode.PARENT_STATE_UNRESOLVED)
            verdict = worst_verdict((verdict, SetupEligibility.UNRESOLVED))
            continue
        if parent.model_state == "PARKED":
            codes.append(SetupRefusalCode.PARKED_STATE)
            verdict = worst_verdict((verdict, SetupEligibility.BLOCKED))
            continue
        if parent.model_state not in requirement.allowed_states:
            codes.append(SetupRefusalCode.STATE_NOT_DECLARED)
            verdict = worst_verdict((verdict, SetupEligibility.BLOCKED))
    return GateOutcome("MODEL_STATE", verdict, tuple(codes))


def _anchor_gate(
    card: CanonicalSetupCard, request: SetupEvaluationRequest
) -> GateOutcome:
    if not card.requires_anchor:
        return GateOutcome("ANCHOR", _PASS)
    anchor = next(
        (
            item
            for item in request.anchors
            if item.model_id in card.parent_model_ids
        ),
        None,
    )
    if anchor is None:
        return GateOutcome(
            "ANCHOR", SetupEligibility.UNRESOLVED, (SetupRefusalCode.ANCHOR_UNRESOLVED,)
        )
    if anchor.status is AnchorStatus.INVALIDATED:
        return GateOutcome(
            "ANCHOR", SetupEligibility.BLOCKED, (SetupRefusalCode.ANCHOR_INVALIDATED,)
        )
    if anchor.status in (AnchorStatus.UNRESOLVED, AnchorStatus.REKEYED):
        return GateOutcome(
            "ANCHOR", SetupEligibility.UNRESOLVED, (SetupRefusalCode.ANCHOR_UNRESOLVED,)
        )
    if anchor.rule_materialization is not RuleMaterialization.CANONICAL:
        return GateOutcome(
            "ANCHOR",
            SetupEligibility.UNRESOLVED,
            (SetupRefusalCode.ANCHOR_RULE_NOT_CANONICAL,),
        )
    return GateOutcome("ANCHOR", _PASS)


def _tier_gate(request: SetupEvaluationRequest) -> GateOutcome:
    tier = request.tier
    if tier is None:
        return GateOutcome(
            "TIER", SetupEligibility.UNRESOLVED, (SetupRefusalCode.TIER_UNRESOLVED,)
        )
    if not tier.native:
        return GateOutcome(
            "TIER", SetupEligibility.BLOCKED, (SetupRefusalCode.TIER_NOT_NATIVE,)
        )
    if tier.no_go:
        return GateOutcome(
            "TIER", SetupEligibility.BLOCKED, (SetupRefusalCode.NATIVE_TIER_NO_GO,)
        )
    return GateOutcome("TIER", _PASS)


def _clock_gate(
    card: CanonicalSetupCard, request: SetupEvaluationRequest
) -> GateOutcome:
    if card.required_clock_checkpoint is None:
        return GateOutcome("CLOCK", _PASS)
    clock = request.clock
    if clock is None or not clock.resolved:
        return GateOutcome(
            "CLOCK", SetupEligibility.UNRESOLVED, (SetupRefusalCode.CLOCK_UNRESOLVED,)
        )
    if clock.checkpoint != card.required_clock_checkpoint:
        return GateOutcome(
            "CLOCK", SetupEligibility.UNRESOLVED, (SetupRefusalCode.CLOCK_UNRESOLVED,)
        )
    if not clock.checkpoint_reached:
        return GateOutcome(
            "CLOCK",
            SetupEligibility.WATCH,
            (SetupRefusalCode.CHECKPOINT_NOT_REACHED,),
        )
    return GateOutcome("CLOCK", _PASS)


def _higher_layer_gate(
    card: CanonicalSetupCard, request: SetupEvaluationRequest
) -> GateOutcome:
    extras = tuple(
        parent
        for parent in request.parents
        if parent.model_id not in card.parent_model_ids
    )
    codes: list[SetupRefusalCode] = []
    verdict = _PASS
    for parent in extras:
        if parent.no_go:
            codes.append(SetupRefusalCode.HIGHER_LAYER_NO_GO)
            verdict = worst_verdict((verdict, SetupEligibility.BLOCKED))
    primary = request.primary_parent(card)
    if primary is not None and primary.direction_bias.side is not None:
        for parent in extras:
            if parent.layer not in (Layer.L2, Layer.L3):
                continue
            side = parent.direction_bias.side
            if side is not None and side is not primary.direction_bias.side:
                codes.append(SetupRefusalCode.LAYER_CONFLICT)
                verdict = worst_verdict((verdict, SetupEligibility.BLOCKED))
    return GateOutcome("HIGHER_LAYER", verdict, tuple(codes))


def _data_quality_gate(
    card: CanonicalSetupCard, request: SetupEvaluationRequest
) -> GateOutcome:
    facts = request.data_quality
    if not isinstance(facts, DataQualityFacts):
        raise SetupContractError("data quality facts are typed")
    if not facts.acceptable:
        return GateOutcome(
            "DATA_QUALITY",
            SetupEligibility.BLOCKED,
            (SetupRefusalCode.DATA_QUALITY_BLOCKED,),
        )
    outcome = request.data_outcome
    if outcome is None:
        primary = request.primary_parent(card)
        outcome = None if primary is None else primary.quality_state
    if outcome is not None and not isinstance(outcome, DataOutcome):
        raise SetupContractError("data outcome uses the frozen III.1 vocabulary")
    if outcome in (DataOutcome.DATA_QUALITY_BLOCKED, DataOutcome.NO_CALCULATION):
        return GateOutcome(
            "DATA_QUALITY",
            SetupEligibility.BLOCKED,
            (SetupRefusalCode.DATA_QUALITY_BLOCKED,),
        )
    return GateOutcome("DATA_QUALITY", _PASS)


def _parameter_gate(
    card: CanonicalSetupCard, request: SetupEvaluationRequest
) -> GateOutcome:
    codes: list[SetupRefusalCode] = []
    verdict = _PASS
    for name in card.required_parameters:
        binding = request.parameter(name)
        if binding is None:
            codes.append(SetupRefusalCode.PARAMETER_UNRESOLVED)
            verdict = worst_verdict((verdict, SetupEligibility.UNRESOLVED))
            continue
        materialization = getattr(binding, "materialization", None)
        if materialization is ParameterMaterialization.ABSENT:
            codes.append(SetupRefusalCode.PARAMETER_UNRESOLVED)
            verdict = worst_verdict((verdict, SetupEligibility.UNRESOLVED))
        elif materialization is ParameterMaterialization.DECLARED:
            codes.append(SetupRefusalCode.PARAMETER_DECLARED_ONLY)
            verdict = worst_verdict((verdict, SetupEligibility.WATCH))
    return GateOutcome("PARAMETERS", verdict, tuple(codes))


def _trigger_gate(
    card: CanonicalSetupCard, request: SetupEvaluationRequest
) -> GateOutcome:
    outcome = satisfies(card.trigger_requirement, request.observations)
    if outcome.satisfied:
        return GateOutcome("TRIGGER", _PASS)
    if outcome.blind_touch:
        return GateOutcome(
            "TRIGGER", SetupEligibility.BLOCKED, (SetupRefusalCode.BLIND_TOUCH_REFUSED,)
        )
    return GateOutcome(
        "TRIGGER", SetupEligibility.WATCH, (SetupRefusalCode.TRIGGER_NOT_SATISFIED,)
    )


def _invalidation_gate(
    card: CanonicalSetupCard,
    request: SetupEvaluationRequest,
    invalidations: InvalidationSet,
) -> GateOutcome:
    missing = tuple(
        kind
        for kind in card.required_invalidation_kinds
        if invalidations.kind(InvalidationKind(kind)) is None
    )
    if missing:
        return GateOutcome(
            "INVALIDATION",
            SetupEligibility.UNRESOLVED,
            (SetupRefusalCode.INVALIDATION_UNDECLARED,),
        )
    if invalidations.any_active:
        return GateOutcome(
            "INVALIDATION", SetupEligibility.BLOCKED, (SetupRefusalCode.SETUP_INVALIDATED,)
        )
    return GateOutcome("INVALIDATION", _PASS)


# ---------------------------------------------------------------------------
# Evaluation
# ---------------------------------------------------------------------------


def _record_side(
    card: CanonicalSetupCard, request: SetupEvaluationRequest
) -> DirectionBias:
    parent = request.primary_parent(card)
    if parent is None:
        return DirectionBias.none()
    return parent.direction_bias


def _record_location(card: CanonicalSetupCard, request: SetupEvaluationRequest):
    parent = request.primary_parent(card)
    if parent is None:
        return None
    for level in parent.levels:
        if level.active:
            return level
    return None


def _merge_evidence(
    card: CanonicalSetupCard, request: SetupEvaluationRequest
) -> tuple[EvidenceReference, ...]:
    merged: list[EvidenceReference] = []
    seen: set[str] = set()
    for reference in card.evidence_refs + request.evidence:
        if not isinstance(reference, EvidenceReference):
            raise SetupContractError("evidence refs carry their status")
        if reference.evidence_id in seen:
            continue
        seen.add(reference.evidence_id)
        merged.append(reference)
    return tuple(merged)


def _facts(
    card: CanonicalSetupCard,
    evaluation_codes: tuple[SetupRefusalCode, ...],
    verdict: SetupEligibility,
    trigger_satisfied: bool,
    observed: tuple[TriggerType, ...],
    invalidations: InvalidationSet,
) -> tuple[object, ...]:
    from app.forge.model_runtime.contract import make_fact

    facts = [
        make_fact(
            "SETUP.ELIGIBILITY",
            "SETUP.ELIGIBILITY.GATES",
            card.setup_id,
            (
                ("verdict", verdict.value),
                (
                    "reasons",
                    ",".join(code.value for code in evaluation_codes) or "NONE",
                ),
            ),
        ),
        make_fact(
            "SETUP.TRIGGER",
            "SETUP.TRIGGER.DECLARED",
            card.setup_id,
            (
                ("satisfied", "YES" if trigger_satisfied else "NO"),
                (
                    "observed",
                    ",".join(kind.value for kind in observed) or "NONE",
                ),
            ),
        ),
        make_fact(
            "SETUP.INVALIDATION",
            "SETUP.INVALIDATION.TRICHOTOMY",
            card.setup_id,
            (
                ("active", "YES" if invalidations.any_active else "NO"),
                (
                    "declared",
                    ",".join(invalidations.declared_kinds()) or "NONE",
                ),
            ),
        ),
        make_fact(
            "SETUP.AUTHORITY",
            "SETUP.AUTHORITY.SEPARATION",
            card.setup_id,
            (
                ("execution_class", card.execution_class.value),
                ("automation_permitted", "NO"),
            ),
        ),
    ]
    return tuple(facts)


def evaluate_setup(
    request: SetupEvaluationRequest, *, registry: SetupRegistry | None = None
) -> SetupEvaluation:
    """Evaluate one setup request — the only place a verdict is produced."""

    if not isinstance(request, SetupEvaluationRequest):
        raise SetupContractError("evaluation consumes a typed request")
    if not isinstance(request.surface, SetupSurface):
        raise SetupContractError("evaluation names a frozen surface")

    active_registry = SetupRegistry() if registry is None else registry
    resolution = active_registry.resolve(
        request.setup_id, request.setup_version, request.surface
    )
    registry_gate = GateOutcome(
        "REGISTRY",
        resolution.verdict,
        () if resolution.code is None else (resolution.code,),
    )
    if resolution.card is None:
        return SetupEvaluation(
            setup_id=request.setup_id,
            setup_version=request.setup_version,
            surface=request.surface,
            card=None,
            eligibility=resolution.verdict,
            reasons=() if resolution.code is None else (resolution.code,),
            gates=(registry_gate,),
            record=None,
        )

    card = resolution.card
    invalidations = resolve_invalidations(
        price=card.default_invalidation_price,
        structural=card.default_invalidation_structural,
        temporal=card.default_invalidation_temporal,
        events=request.invalidation_events,
    )
    trigger_outcome = satisfies(card.trigger_requirement, request.observations)

    gates = (
        registry_gate,
        _stand_down_gate(request.stand_down),
        _model_state_gate(card, request),
        _anchor_gate(card, request),
        _tier_gate(request),
        _clock_gate(card, request),
        _higher_layer_gate(card, request),
        _data_quality_gate(card, request),
        _parameter_gate(card, request),
        _trigger_gate(card, request),
        _invalidation_gate(card, request, invalidations),
    )
    verdict = worst_verdict(gate.verdict for gate in gates)
    codes: list[SetupRefusalCode] = []
    for gate in gates:
        for code in gate.codes:
            if code not in codes:
                codes.append(code)
    reasons = tuple(codes)

    declared = card.targets
    requested_targets = order_targets(request.targets) if request.targets else declared
    declared_ids = {target.target_id for target in declared}
    for target in requested_targets:
        if target.target_id not in declared_ids:
            raise SetupContractError(
                f"target is not declared by the card: {target.target_id}"
            )

    parent_states = tuple(_parent_ref(parent) for parent in request.parents)

    record = SetupRecord(
        setup_id=card.setup_id,
        setup_version=card.version,
        source_card_ref=card.source_card_ref,
        execution_class=card.execution_class,
        product_exposure=card.exposure,
        eligibility=verdict,
        eligibility_reasons=reasons,
        side=_record_side(card, request),
        location=_record_location(card, request),
        trigger_requirement=card.trigger_requirement,
        invalidation_price=invalidations.price,
        invalidation_structural=invalidations.structural,
        invalidation_temporal=invalidations.temporal,
        targets=requested_targets,
        promotion_conditions=tuple(
            target.promotion for target in requested_targets if target.promotion
        ),
        no_go_refs=tuple(
            reason for parent in request.parents for reason in parent.no_go
        ),
        parent_states=parent_states,
        transition_refs=request.transitions,
        evidence_refs=_merge_evidence(card, request),
        manual_status=card.execution_class,
        automation_permitted=card.automation_permitted,
        explanation_facts=_facts(
            card,
            reasons,
            verdict,
            trigger_outcome.satisfied,
            trigger_outcome.observed,
            invalidations,
        ),
        evaluation_time=request.evaluation_time,
    )
    return SetupEvaluation(
        setup_id=card.setup_id,
        setup_version=card.version,
        surface=request.surface,
        card=card,
        eligibility=verdict,
        reasons=reasons,
        gates=gates,
        record=record,
    )


def _parent_ref(parent: ModelOutput) -> ParentStateRef:
    return ParentStateRef(
        model_id=parent.model_id,
        model_version=parent.model_version,
        model_state=parent.model_state,
        layer=parent.layer,
        output_hash=parent.output_hash,
        snapshot_ref=parent.identity.prior_state_ref or "",
    )
