"""Shared deterministic builders for III.5 fixtures and the acceptance suite.

The suite and the fixture generator import these builders, so a fixture
can never drift from the reproduction path (clause S3).  Every card
instance, model output, anchor and observation built here is
``SYNTHETIC_FIXTURE``; the identities, execution classes, statuses,
exposures, trigger names and evidence ids are ``CANONICAL_SOURCE_SLICE``
taken verbatim from the corpus.

No builder produces a win rate, expectancy, probability or risk/reward
figure, and none may be cited as empirical trading validation.
"""

from __future__ import annotations

import sys
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[5]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from app.forge.canonical import ClaimIdentity, EvidenceStatus
from app.forge.market_data import (
    CLOCK_REGISTRY_VERSION,
    MARKET_DATA_SCHEMA_VERSION,
    SESSION_REGISTRY_VERSION,
    DataOutcome,
)
from app.forge.measurements.anchors import (
    AnchorRecord,
    AnchorRule,
    AnchorStatus,
    RuleMaterialization,
    evaluate_anchor,
)
from app.forge.measurements.contracts import Provenance, SourceWindow
from app.forge.measurements.versions import MEASUREMENT_ENGINE_VERSION
from app.forge.model_runtime.contract import (
    DirectionBias,
    DirectionSide,
    InputIdentity,
    Layer,
    LevelKind,
    ModelOutput,
    NoGoReason,
    ProductionAuthorization,
    RangeLeftField,
    TypedLevel,
)
from app.forge.model_runtime.versions import MODEL_RUNTIME_VERSION
from app.forge.setup_engine import (
    DataQualityFacts,
    EvidenceReference,
    InvalidationEvents,
    ParameterBinding,
    ParameterMaterialization,
    PromotionCondition,
    SetupClock,
    SetupEvaluationRequest,
    SetupSurface,
    SetupTarget,
    TierBinding,
    TransitionRef,
    TriggerObservation,
    TriggerType,
    evaluate_setup,
)
from app.forge.setup_engine import fib_rekey, jpy_role_gate, xau_quarter_zone
from app.forge.state_engine.delivery import (
    DeclaredTarget,
    DeliveryObservation,
    DeliverySide,
    build_path,
)
from app.forge.state_engine.stand_down import stand_down_for_no_go

#: Injected clock — never wall time.
FIXED = datetime(2026, 1, 5, 14, 0, tzinfo=timezone.utc)

SOURCE_WINDOW = SourceWindow(
    window_open_utc=FIXED,
    window_close_utc=FIXED,
    input_digest="FIXTURE.INPUT.DIGEST.0001",
    bar_count=3,
)

PROVENANCE = Provenance(
    instrument_id="XAUUSD",
    clock_id="NY",
    session_id="NY_AM",
    calculation_timestamp=FIXED,
)

FIB_PROVENANCE = Provenance(
    instrument_id="CROSSASSET",
    clock_id="DAILY",
    session_id="DAILY",
    calculation_timestamp=FIXED,
)


# ---------------------------------------------------------------------------
# Typed levels and model outputs
# ---------------------------------------------------------------------------


def xau_zone_level() -> TypedLevel:
    return TypedLevel(
        level_id="XAU.QUARTER.ZONE",
        level_kind=LevelKind.COORDINATE,
        family="XAU.QUARTER.ZONE",
        level=Decimal("0.25"),
        price=None,
        active=True,
        source_ref="XAU_QUARTER_ZONE_OPERATOR_CARD_V1.md",
    )


def jpy_level() -> TypedLevel:
    return TypedLevel(
        level_id="JPY.PAIR.L1",
        level_kind=LevelKind.COORDINATE,
        family="JPY.PAIR.L1",
        level=Decimal("155.00"),
        price=None,
        active=True,
        source_ref="JPY_CARRY_ROLE_GATED_OPERATOR_CARD_V1.md",
    )


def fib_level() -> TypedLevel:
    return TypedLevel(
        level_id="FIB.REKEY.132",
        level_kind=LevelKind.COORDINATE,
        family="FIB.REKEY",
        level=Decimal("132"),
        price=None,
        active=True,
        source_ref="FIB_REKEY_OPERATOR_CARD_V1.md",
    )


def identity(instrument: str = "XAUUSD") -> InputIdentity:
    return InputIdentity(
        instrument_id=instrument,
        calibration_key=None,
        clock_id="NY",
        session_id="NY_AM",
        calculation_timestamp=FIXED,
        market_data_schema_version=MARKET_DATA_SCHEMA_VERSION,
        clock_registry_version=CLOCK_REGISTRY_VERSION,
        session_registry_version=SESSION_REGISTRY_VERSION,
        measurement_engine_version=MEASUREMENT_ENGINE_VERSION,
        model_runtime_version=MODEL_RUNTIME_VERSION,
        prior_state_ref="SNAPSHOT.0001",
    )


def model_output(
    model_id: str = "XAU.GAME.L1_L2_L3.V1",
    *,
    state: str = "NODE_DECLARED",
    layer: Layer = Layer.L1,
    side: DirectionSide | None = DirectionSide.UP,
    no_go: tuple[NoGoReason, ...] = (),
    quality: DataOutcome = DataOutcome.OK,
    levels: tuple[TypedLevel, ...] | None = None,
    version: str = "1.0",
    instrument: str = "XAUUSD",
) -> ModelOutput:
    return ModelOutput(
        model_id=model_id,
        model_version=version,
        model_runtime_version=MODEL_RUNTIME_VERSION,
        output_hash="",
        model_state=state,
        layer=layer,
        direction_bias=(
            DirectionBias.none()
            if side is None
            else DirectionBias(side=side, basis_fact_id="SETUP.FACT.BIAS")
        ),
        active_ranges=(),
        active_anchor_states=(),
        levels=levels if levels is not None else (xau_zone_level(),),
        range_left=RangeLeftField.unresolved(),
        no_go=no_go,
        warnings=(),
        claim_refs=(),
        evidence_refs=(),
        quality_state=quality,
        production_authorization=ProductionAuthorization.MANUAL_OPERATOR,
        explanation_facts=(),
        sub_states=(),
        identity=identity(instrument),
    )


# ---------------------------------------------------------------------------
# Anchors (built through III.2, never fabricated)
# ---------------------------------------------------------------------------


def fib_anchor(
    status: AnchorStatus = AnchorStatus.UNRESOLVED,
    materialization: RuleMaterialization = RuleMaterialization.NOT_MATERIALIZED,
):
    record = AnchorRecord(
        anchor_id="ANCHOR.FIB.RANGE_BIRTH.0001",
        model_id="CROSSASSET.FIB.RANGE_BIRTH.V1",
        model_version="1.0",
        status=status,
        rule=AnchorRule(
            rule_id="CROSSASSET.FIB.RANGE_BIRTH.R15",
            rule_version="V1",
            materialization=materialization,
            source_ref="FIB_REKEY_OPERATOR_CARD_V1.md",
        ),
        invalidation_reason=(
            "ANCHOR_STATE_INVALIDATED"
            if status is AnchorStatus.INVALIDATED
            else None
        ),
    )
    return evaluate_anchor(
        record, provenance=FIB_PROVENANCE, source_window=SOURCE_WINDOW
    )


# ---------------------------------------------------------------------------
# Observations, parameters, tiers
# ---------------------------------------------------------------------------


def observation(
    kind: TriggerType,
    sequence: int,
    *,
    final_bar: bool = True,
    state_ref: str | None = None,
) -> TriggerObservation:
    return TriggerObservation(
        trigger_type=kind,
        bar_ref=f"BAR.{sequence:04d}",
        sequence_index=sequence,
        final_bar=final_bar,
        state_ref=state_ref,
        source_ref="SETUP.TRIGGER.OBSERVATION",
    )


def touch(sequence: int = 1) -> TriggerObservation:
    return observation(TriggerType.TOUCH, sequence)


def excursion(sequence: int = 1) -> TriggerObservation:
    return observation(TriggerType.EXCURSION, sequence)


def rejection(sequence: int = 2) -> TriggerObservation:
    return observation(TriggerType.REJECTION, sequence, state_ref="REJECTION.0001")


def close_final(sequence: int = 2) -> TriggerObservation:
    return observation(TriggerType.CLOSE, sequence)


def close_nonfinal(sequence: int = 2) -> TriggerObservation:
    return observation(TriggerType.CLOSE, sequence, final_bar=False)


def acceptance(sequence: int = 2, state_ref: str | None = "ACCEPT.0001"):
    return observation(TriggerType.ACCEPTANCE, sequence, state_ref=state_ref)


def sr_flip(sequence: int = 2, state_ref: str | None = "SR_FLIP.0001"):
    return observation(TriggerType.SR_FLIP, sequence, state_ref=state_ref)


def occ(sequence: int = 2, state_ref: str | None = "OCC.0001"):
    return observation(TriggerType.OCC, sequence, state_ref=state_ref)


def parameter(
    name: str,
    materialization: ParameterMaterialization = ParameterMaterialization.CANONICAL,
    value: str = "1",
) -> ParameterBinding:
    return ParameterBinding(
        name=name,
        materialization=materialization,
        value=None if materialization is ParameterMaterialization.ABSENT else Decimal(value),
        source_ref=(
            ""
            if materialization is ParameterMaterialization.ABSENT
            else f"{name}.SOURCE.V1"
        ),
    )


def canonical_xau_parameters() -> tuple[ParameterBinding, ...]:
    return (
        parameter("QUARTER_ZONE_MAPPING", ParameterMaterialization.CANONICAL, "25"),
        parameter("LADDER_INVALIDATION", ParameterMaterialization.CANONICAL, "5"),
    )


def declared_xau_parameters() -> tuple[ParameterBinding, ...]:
    return (
        parameter("QUARTER_ZONE_MAPPING", ParameterMaterialization.DECLARED, "25"),
        parameter("LADDER_INVALIDATION", ParameterMaterialization.DECLARED, "5"),
    )


def absent_xau_parameters() -> tuple[ParameterBinding, ...]:
    return (
        parameter("QUARTER_ZONE_MAPPING", ParameterMaterialization.ABSENT),
        parameter("LADDER_INVALIDATION", ParameterMaterialization.ABSENT),
    )


def xau_tier(native: bool = True, no_go: bool = False) -> TierBinding:
    return TierBinding(tier_id="XAU.QUARTER", native=native, no_go=no_go)


def jpy_tier(native: bool = True, no_go: bool = False) -> TierBinding:
    return TierBinding(tier_id="JPY.NATIVE", native=native, no_go=no_go)


# ---------------------------------------------------------------------------
# Requests
# ---------------------------------------------------------------------------


def xau_request(**overrides) -> SetupEvaluationRequest:
    base: dict[str, object] = dict(
        setup_id=xau_quarter_zone.SETUP_ID,
        setup_version="1.0",
        surface=SetupSurface.OPERATOR,
        parents=(model_output(),),
        clock=SetupClock(session_id="NY", checkpoint="AFTER_0300_NY"),
        tier=xau_tier(),
        parameters=canonical_xau_parameters(),
        observations=(excursion(1), close_final(2)),
    )
    base.update(overrides)
    return SetupEvaluationRequest(**base)  # type: ignore[arg-type]


def declared_xau_request(**overrides) -> SetupEvaluationRequest:
    overrides.setdefault("parameters", declared_xau_parameters())
    return xau_request(**overrides)


def fib_request(**overrides) -> SetupEvaluationRequest:
    base: dict[str, object] = dict(
        setup_id=fib_rekey.SETUP_ID,
        setup_version="1.0",
        surface=SetupSurface.RESEARCH,
        parents=(
            model_output(
                model_id="CROSSASSET.FIB.RANGE_BIRTH.V1",
                state="RANGE_ACTIVE",
                instrument="CROSSASSET",
                levels=(fib_level(),),
            ),
        ),
        anchors=(fib_anchor(),),
        tier=TierBinding(tier_id="FIB.NATIVE"),
        observations=(close_final(1),),
    )
    base.update(overrides)
    return SetupEvaluationRequest(**base)  # type: ignore[arg-type]


def jpy_request(**overrides) -> SetupEvaluationRequest:
    base: dict[str, object] = dict(
        setup_id=jpy_role_gate.SETUP_ID,
        setup_version="1.0",
        surface=SetupSurface.OPERATOR,
        parents=(
            model_output(
                model_id="JPY.CARRY_GAME.L1_L3.V1",
                state="BASKET_AGREE_CONFIRM",
                instrument="USDJPY",
                levels=(jpy_level(),),
            ),
        ),
        tier=jpy_tier(),
        observations=(excursion(1), close_final(2)),
    )
    base.update(overrides)
    return SetupEvaluationRequest(**base)  # type: ignore[arg-type]


# ---------------------------------------------------------------------------
# Support objects for later clauses
# ---------------------------------------------------------------------------


def stand_down_record():
    return stand_down_for_no_go(
        NoGoReason.NATIVE_TIER_NO_GO,
        blocking_rule_ref="JPY.CARRY.L1.NATIVE_TIER",
        snapshot_id="SNAPSHOT.0001",
    )


def delivery_path():
    targets = (
        DeclaredTarget("TARGET.NEXT_QUARTER", DeliverySide.ABOVE, 0),
        DeclaredTarget("TARGET.CONFIRM_5", DeliverySide.BELOW, 1),
    )
    observations = (
        DeliveryObservation("TARGET.CONFIRM_5", FIXED, "BAR.0001"),
        DeliveryObservation("TARGET.NEXT_QUARTER", FIXED, "BAR.0002"),
    )
    return build_path(clock_id="NY", targets=targets, observations=observations)


def transition(transition_id: str = "TRANSITION.L1.CONFIRMED") -> TransitionRef:
    return TransitionRef(
        transition_id=transition_id,
        from_state="NODE_DECLARED",
        to_state="L1_CONFIRMED",
        event_ref="EVENT.0001",
    )


def promotion(condition_id: str = "SETUP.XAU.PROMOTE.NEXT_QUARTER") -> PromotionCondition:
    return PromotionCondition(
        condition_id=condition_id,
        required_transition="L1_CONFIRMED",
        source_ref="XAU_QUARTER_ZONE_OPERATOR_CARD_V1.md",
        authority_ref="SETUP.XAU.QUARTER_ZONE.V1",
    )


def xau_targets() -> tuple[SetupTarget, ...]:
    return xau_quarter_zone.card().targets


def claim_identity(market: str = "XAUUSD") -> ClaimIdentity:
    return ClaimIdentity(
        market=market,
        event_definition="PROMOTION_INTO_ZONE",
        conditioning_event="QUARTER_ZONE",
        clock_origin="AFTER_0300_NY",
        horizon="NEXT_QUARTER",
        tolerance="IN_ZONE",
        eligibility="OPERATOR_ONLY",
        implementation_semantics="SETUP_ENGINE_V1",
    )


def xau_evidence() -> EvidenceReference:
    return EvidenceReference(
        evidence_id="EV.XAU.PROMOTION.68_80.V1",
        status=EvidenceStatus.VALIDATED,
        claim_id="CL.XAU.PROMOTION.68_80",
        population_key="XAU.PROMOTION",
    )


def jpy_relationship_evidence() -> EvidenceReference:
    return EvidenceReference(
        evidence_id="EV.JPY.CARRY.BASKET_RELATION.V1",
        status=EvidenceStatus.VALIDATED,
        claim_id="CL.JPY.CARRY.ROLE_RELATION",
        population_key="JPY.BASKET.ROLE",
        relationship=True,
    )


def unclaimed_evidence() -> EvidenceReference:
    return EvidenceReference(
        evidence_id="EV.XAU.PROMOTION.120_132.V1",
        status=EvidenceStatus.RESEARCH_FLAG,
        population_key="XAU.PROMOTION",
    )


def run(request: SetupEvaluationRequest):
    return evaluate_setup(request)
