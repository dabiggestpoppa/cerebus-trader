"""Bloc III.5 — Operator Setup Engine: the binding acceptance suite.

162 frozen test names across T1–T12, reproducing ``ACCEPTANCE.md``
exactly.  No test is skipped or xfailed, and no assertion is weakened to
fit the implementation.

The suite proves the institutional law end to end:

    model state != setup eligibility != automation approval != execution
"""

from __future__ import annotations

import dataclasses
import hashlib
import importlib
import importlib.util
import inspect
import json
import re
import sys

from tests._support.canonical_bytes import canonical_bytes, canonical_sha256
from dataclasses import replace
from decimal import Decimal
from pathlib import Path

import pytest

_ROOT = Path(__file__).resolve().parents[1]
_FIXTURES = _ROOT / "implementation/forge/book_iii/bloc_iii_5/fixtures"
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

#: Load the shared builders by path under a unique name: the fixtures
#: directory must never enter ``sys.path``, or a sibling Bloc's
#: ``_builders`` import would resolve to this one.
_SPEC = importlib.util.spec_from_file_location(
    "bloc_iii_5_builders", _FIXTURES / "_builders.py"
)
B = importlib.util.module_from_spec(_SPEC)
sys.modules["bloc_iii_5_builders"] = B
_SPEC.loader.exec_module(B)

from app.forge.canonical import EvidenceStatus, ProductExposure, SetupClass  # noqa: E402
from app.forge.measurements.anchors import (  # noqa: E402
    AnchorStatus,
    RuleMaterialization,
)
from app.forge.model_runtime.contract import (  # noqa: E402
    DirectionSide,
    Layer,
    NoGoReason,
)
from app.forge.setup_engine import (  # noqa: E402
    CANONICAL_SETUP_IDS,
    FORBIDDEN_FIELD_NAMES,
    GATE_ORDER,
    NUMERIC_RESULT_TYPES,
    SETUP_ENGINE_MODULES,
    SETUP_ENGINE_VERSION,
    SETUP_RECORD_FIELDS,
    SETUP_REFUSAL_CODES,
    TRIGGER_TYPES,
    CardStatus,
    ClaimPopulationMismatchError,
    DataQualityFacts,
    EvidenceReference,
    InvalidationEvents,
    InvalidationKind,
    InvalidationSet,
    ParameterBinding,
    ParameterMaterialization,
    PriceInvalidation,
    PromotionCondition,
    SEVERITY_ORDER,
    SETUP_CONTRACT_VERSION,
    SetupClock,
    SetupContractError,
    SetupEligibility,
    SetupEvaluationRequest,
    SetupRecord,
    SetupRefusalCode,
    SetupRegistry,
    SetupRegistryError,
    SetupSurface,
    SetupTarget,
    StructuralInvalidation,
    TargetPromotionRefused,
    TemporalInvalidation,
    TierBinding,
    TriggerCombination,
    TriggerLiteral,
    TriggerObservation,
    TriggerRequirement,
    TriggerType,
    UnsupportedStatisticError,
    worst_verdict,
)
from app.forge.setup_engine import (  # noqa: E402
    contracts,
    fib_rekey,
    invariants,
    jpy_role_gate,
    p90_lineage,
    registry as registry_module,
    statistics,
    st_manual,
    targets as targets_module,
    triggers,
    versions,
    xau_quarter_zone,
)
from app.forge.setup_engine.eligibility import evaluate_setup  # noqa: E402
from app.forge.state_engine.delivery import (  # noqa: E402
    DeclaredTarget,
    DeliveryObservation,
    DeliverySide,
    build_path,
)
from app.forge.state_engine.errors import AmbiguousPathError  # noqa: E402

_PACKAGE = _ROOT / "app" / "forge" / "setup_engine"


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------


def _record(request=None) -> SetupRecord:
    evaluation = evaluate_setup(B.xau_request() if request is None else request)
    assert evaluation.record is not None
    return evaluation.record


def _sources() -> dict[str, str]:
    return {
        path.name: path.read_text(encoding="utf-8")
        for path in sorted(_PACKAGE.glob("*.py"))
    }


def _requirement(*kinds, any_of=(), combination=TriggerCombination.ALL):
    return TriggerRequirement(
        source_ref="TEST.TRIGGER.REQUIREMENT",
        literals=tuple(TriggerLiteral(kind) for kind in kinds),
        any_of=tuple(TriggerLiteral(kind) for kind in any_of),
        combination=combination,
    )


def _satisfied(requirement, observations) -> bool:
    return triggers.satisfies(requirement, observations).satisfied


def _package_dataclass_fields() -> set[str]:
    names: set[str] = set()
    for module_name in SETUP_ENGINE_MODULES:
        module = importlib.import_module(f"app.forge.setup_engine.{module_name}")
        for value in vars(module).values():
            if dataclasses.is_dataclass(value) and isinstance(value, type):
                names.update(field.name for field in dataclasses.fields(value))
    return names


# ---------------------------------------------------------------------------
# T1 — setup contract + registry (16)
# ---------------------------------------------------------------------------


class TestT1ContractAndRegistry:
    def test_setup_record_is_immutable(self):
        record = _record()
        with pytest.raises(dataclasses.FrozenInstanceError):
            record.setup_id = "SETUP.XAU.QUARTER_ZONE.V9"  # type: ignore[misc]

    def test_setup_record_requires_canonical_id(self):
        record = _record()
        for bogus in ("XAU_QUARTER_ZONE", "SET.XAU.QUARTER_ZONE.V1", ""):
            with pytest.raises(SetupContractError):
                replace(record, setup_id=bogus)

    def test_setup_contract_version_stamped(self):
        record = _record()
        assert record.setup_contract_version == SETUP_CONTRACT_VERSION
        assert record.engine_version == SETUP_ENGINE_VERSION
        with pytest.raises(SetupContractError):
            replace(record, setup_contract_version="SETUP_CONTRACT.V0")
        with pytest.raises(SetupContractError):
            replace(record, engine_version="SETUP_ENGINE.V0")

    def test_setup_record_field_set_is_frozen(self):
        names = {field.name for field in dataclasses.fields(SetupRecord)}
        assert names == set(SETUP_RECORD_FIELDS)
        assert len(SETUP_RECORD_FIELDS) == 25

    def test_setup_record_rejects_free_text_field(self):
        record = _record()
        with pytest.raises(SetupContractError):
            replace(record, side="bullish and likely")
        with pytest.raises(SetupContractError):
            replace(record, eligibility_reasons=("looks strong",))

    def test_registry_carries_execution_class_verbatim(self):
        expected = {
            "SETUP.XAU.QUARTER_ZONE.V1": SetupClass.MANUAL_OPERATOR,
            "SETUP.FIB.REKEY.V1": SetupClass.RESEARCH_ONLY,
            "SETUP.JPY.CARRY_ROLE_GATE.V1": SetupClass.MANUAL_OPERATOR,
        }
        registry = SetupRegistry()
        for setup_id, execution_class in expected.items():
            card = registry.card(setup_id)
            assert card.execution_class is execution_class
        record = _record()
        assert record.execution_class is SetupClass.MANUAL_OPERATOR
        assert record.manual_status is SetupClass.MANUAL_OPERATOR

    def test_registry_carries_status_verbatim(self):
        registry = SetupRegistry()
        assert (
            registry.card("SETUP.XAU.QUARTER_ZONE.V1").status.value
            == "CANONICALIZATION_CANDIDATE"
        )
        assert (
            registry.card("SETUP.FIB.REKEY.V1").status.value
            == "RESEARCH_OPERATOR_CANDIDATE"
        )
        assert (
            registry.card("SETUP.XAU.QUARTER_ZONE.V1").exposure
            is ProductExposure.OPERATOR_ONLY
        )
        assert (
            registry.card("SETUP.FIB.REKEY.V1").exposure
            is ProductExposure.RESEARCH_LAB
        )
        assert (
            registry_module.project_status(CardStatus.CANONICALIZATION_CANDIDATE)
            is EvidenceStatus.CANDIDATE
        )

    def test_registry_refuses_parity_unsafe_card(self):
        registry = SetupRegistry().with_status(
            xau_quarter_zone.SETUP_ID, CardStatus.IMPLEMENTATION_NOT_PARITY_SAFE
        )
        evaluation = evaluate_setup(B.xau_request(), registry=registry)
        assert evaluation.eligibility is SetupEligibility.BLOCKED
        assert SetupRefusalCode.SETUP_NOT_CANONICAL_FOR_SURFACE in evaluation.reasons

    def test_registry_refuses_parked_card(self):
        registry = SetupRegistry().with_status(
            xau_quarter_zone.SETUP_ID, CardStatus.PARKED
        )
        evaluation = evaluate_setup(B.xau_request(), registry=registry)
        assert evaluation.eligibility is SetupEligibility.BLOCKED
        assert SetupRefusalCode.SETUP_NOT_CANONICAL_FOR_SURFACE in evaluation.reasons

    def test_registry_refuses_quarantined_card(self):
        registry = SetupRegistry().with_status(
            xau_quarter_zone.SETUP_ID, CardStatus.INTERNAL_CONTRADICTION
        )
        evaluation = evaluate_setup(B.xau_request(), registry=registry)
        assert evaluation.eligibility is SetupEligibility.BLOCKED
        assert SetupRefusalCode.SETUP_NOT_CANONICAL_FOR_SURFACE in evaluation.reasons

    def test_registry_refuses_unknown_setup_id(self):
        resolution = SetupRegistry().resolve(
            "SETUP.XAU.QUARTER_ZONE.V9", "1.0", SetupSurface.OPERATOR
        )
        assert resolution.verdict is SetupEligibility.UNRESOLVED
        assert resolution.code is SetupRefusalCode.SETUP_CARD_UNRESOLVED
        assert resolution.card is None
        evaluation = evaluate_setup(
            B.xau_request(setup_id="SETUP.XAU.QUARTER_ZONE.V9")
        )
        assert evaluation.eligibility is SetupEligibility.UNRESOLVED
        assert evaluation.record is None

    def test_registry_resolves_explicit_version(self):
        registry = SetupRegistry()
        card = registry.card(xau_quarter_zone.SETUP_ID)
        resolved = registry.resolve(card.setup_id, card.version, SetupSurface.OPERATOR)
        assert resolved.resolved
        assert resolved.code is None
        drift = registry.resolve(card.setup_id, "0.9", SetupSurface.OPERATOR)
        assert drift.verdict is SetupEligibility.BLOCKED
        assert drift.code is SetupRefusalCode.SETUP_VERSION_DRIFT

    def test_registry_loads_only_canonical_cards(self):
        registry = SetupRegistry()
        assert registry.ids() == tuple(sorted(CANONICAL_SETUP_IDS))
        card = registry.card(xau_quarter_zone.SETUP_ID)
        with pytest.raises(SetupRegistryError):
            SetupRegistry((replace(card, setup_id="SETUP.XAU.INVENTED.V1"),))

    def test_registry_never_latest_without_policy(self):
        resolution = SetupRegistry().resolve(
            xau_quarter_zone.SETUP_ID, None, SetupSurface.OPERATOR
        )
        assert resolution.verdict is SetupEligibility.UNRESOLVED
        assert resolution.code is SetupRefusalCode.SETUP_VERSION_UNRESOLVED
        assert resolution.card is None

    def test_registry_exposes_three_canonical_cards(self):
        registry = SetupRegistry()
        assert len(registry.cards()) == 3
        assert set(registry.ids()) == {
            "SETUP.XAU.QUARTER_ZONE.V1",
            "SETUP.FIB.REKEY.V1",
            "SETUP.JPY.CARRY_ROLE_GATE.V1",
        }

    def test_registry_has_no_automation_approved_card(self):
        for card in SetupRegistry().cards():
            assert card.execution_class is not SetupClass.AUTOMATION_APPROVED
            assert card.automation_permitted is False
            evaluation = evaluate_setup(
                B.xau_request(
                    setup_id=card.setup_id,
                    setup_version=card.version,
                    surface=SetupSurface.RESEARCH,
                )
            )
            assert evaluation.automation_permitted is False


# ---------------------------------------------------------------------------
# T2 — eligibility engine (18)
# ---------------------------------------------------------------------------


class TestT2Eligibility:
    def test_eligibility_vocabulary_is_four(self):
        assert {value.value for value in SetupEligibility} == {
            "ELIGIBLE",
            "WATCH",
            "BLOCKED",
            "UNRESOLVED",
        }

    def test_eligibility_precedence_is_total(self):
        assert [value.severity for value in SEVERITY_ORDER] == [3, 2, 1, 0]
        assert worst_verdict((SetupEligibility.WATCH, SetupEligibility.UNRESOLVED)) is (
            SetupEligibility.UNRESOLVED
        )
        assert worst_verdict(tuple(SetupEligibility)) is SetupEligibility.BLOCKED
        parameters = inspect.signature(evaluate_setup).parameters
        assert "verdict" not in parameters and "eligibility" not in parameters

    def test_eligible_requires_every_gate(self):
        assert evaluate_setup(B.xau_request()).eligibility is SetupEligibility.ELIGIBLE
        broken = (
            B.xau_request(parents=()),
            B.xau_request(stand_down=B.stand_down_record()),
            B.xau_request(parents=(B.model_output(state="UNKNOWN_STATE"),)),
            B.xau_request(tier=B.xau_tier(native=False)),
            B.xau_request(clock=None),
            B.xau_request(data_quality=DataQualityFacts(stale=True)),
            B.xau_request(parameters=B.absent_xau_parameters()),
            B.xau_request(observations=()),
            B.xau_request(invalidation_events=InvalidationEvents(price_fired=True)),
        )
        for request in broken:
            assert evaluate_setup(request).eligibility is not SetupEligibility.ELIGIBLE

    def test_missing_parent_state_is_unresolved(self):
        evaluation = evaluate_setup(B.xau_request(parents=()))
        assert evaluation.eligibility is SetupEligibility.UNRESOLVED
        assert SetupRefusalCode.PARENT_STATE_MISSING in evaluation.reasons

    def test_model_version_mismatch_is_unresolved(self):
        evaluation = evaluate_setup(
            B.xau_request(parents=(B.model_output(version="0.9"),))
        )
        assert evaluation.eligibility is SetupEligibility.UNRESOLVED
        assert SetupRefusalCode.MODEL_VERSION_UNAVAILABLE in evaluation.reasons

    def test_wrong_layer_parent_is_blocked(self):
        card = xau_quarter_zone.card()
        requirement = registry_module.ParentRequirement(
            model_id="XAU.GAME.L1_L2_L3.V1",
            model_version="1.0",
            allowed_states=card.parent_requirements[0].allowed_states,
            required_layer=Layer.L2,
        )
        registry = SetupRegistry((replace(card, parent_requirements=(requirement,)),))
        evaluation = evaluate_setup(B.xau_request(), registry=registry)
        assert evaluation.eligibility is SetupEligibility.BLOCKED
        assert SetupRefusalCode.WRONG_LAYER_PARENT in evaluation.reasons

    def test_state_not_declared_by_card_is_blocked(self):
        evaluation = evaluate_setup(
            B.xau_request(parents=(B.model_output(state="UNKNOWN_STATE"),))
        )
        assert evaluation.eligibility is SetupEligibility.BLOCKED
        assert SetupRefusalCode.STATE_NOT_DECLARED in evaluation.reasons

    def test_anchor_unresolved_blocks_fib(self):
        invalidated = evaluate_setup(
            B.fib_request(anchors=(B.fib_anchor(status=AnchorStatus.INVALIDATED),))
        )
        assert invalidated.eligibility is SetupEligibility.BLOCKED
        assert SetupRefusalCode.ANCHOR_INVALIDATED in invalidated.reasons
        unresolved = evaluate_setup(B.fib_request())
        assert unresolved.eligibility is not SetupEligibility.ELIGIBLE

    def test_anchor_declared_rule_caps_at_unresolved(self):
        evaluation = evaluate_setup(
            B.fib_request(
                anchors=(B.fib_anchor(materialization=RuleMaterialization.DECLARED),)
            )
        )
        assert evaluation.eligibility is SetupEligibility.UNRESOLVED
        assert evaluation.eligibility is not SetupEligibility.ELIGIBLE

    def test_cross_asset_tier_is_blocked(self):
        evaluation = evaluate_setup(B.xau_request(tier=B.xau_tier(native=False)))
        assert evaluation.eligibility is SetupEligibility.BLOCKED
        assert SetupRefusalCode.TIER_NOT_NATIVE in evaluation.reasons

    def test_native_tier_no_go_is_blocked(self):
        evaluation = evaluate_setup(B.xau_request(tier=B.xau_tier(no_go=True)))
        assert evaluation.eligibility is SetupEligibility.BLOCKED
        assert SetupRefusalCode.NATIVE_TIER_NO_GO in evaluation.reasons

    def test_unresolved_clock_is_unresolved(self):
        evaluation = evaluate_setup(
            B.xau_request(clock=SetupClock("NY", "AFTER_0300_NY", resolved=False))
        )
        assert evaluation.eligibility is SetupEligibility.UNRESOLVED
        assert SetupRefusalCode.CLOCK_UNRESOLVED in evaluation.reasons

    def test_unreached_clock_checkpoint_is_watch(self):
        evaluation = evaluate_setup(
            B.xau_request(
                clock=SetupClock("NY", "AFTER_0300_NY", checkpoint_reached=False)
            )
        )
        assert evaluation.eligibility is SetupEligibility.WATCH
        assert SetupRefusalCode.CHECKPOINT_NOT_REACHED in evaluation.reasons

    def test_higher_layer_no_go_blocks_setup(self):
        extra = B.model_output(
            model_id="XAU.GAME.L3_CONTEXT.V1",
            layer=Layer.L3,
            no_go=(NoGoReason.ASIAN_RANGE_NO_GO,),
        )
        evaluation = evaluate_setup(B.xau_request(parents=(B.model_output(), extra)))
        assert evaluation.eligibility is SetupEligibility.BLOCKED
        assert SetupRefusalCode.HIGHER_LAYER_NO_GO in evaluation.reasons

    def test_higher_layer_conflict_reports_facts(self):
        extra = B.model_output(
            model_id="XAU.GAME.L3_CONTEXT.V1",
            layer=Layer.L3,
            side=DirectionSide.DOWN,
        )
        evaluation = evaluate_setup(B.xau_request(parents=(B.model_output(), extra)))
        assert evaluation.eligibility is SetupEligibility.BLOCKED
        assert SetupRefusalCode.LAYER_CONFLICT in evaluation.reasons
        fact_ids = {fact.fact_id for fact in evaluation.record.explanation_facts}
        assert "SETUP.ELIGIBILITY" in fact_ids
        assert not any(
            "conflict_score" in key
            for fact in evaluation.record.explanation_facts
            for key, _value in fact.payload
        )

    def test_nonfinal_bar_is_data_quality_blocked(self):
        evaluation = evaluate_setup(
            B.xau_request(data_quality=DataQualityFacts(final_bar=False))
        )
        assert evaluation.eligibility is SetupEligibility.BLOCKED
        assert SetupRefusalCode.DATA_QUALITY_BLOCKED in evaluation.reasons

    def test_stale_data_is_data_quality_blocked(self):
        evaluation = evaluate_setup(
            B.xau_request(data_quality=DataQualityFacts(stale=True))
        )
        assert evaluation.eligibility is SetupEligibility.BLOCKED
        assert SetupRefusalCode.DATA_QUALITY_BLOCKED in evaluation.reasons

    def test_declared_parameter_caps_at_watch(self):
        evaluation = evaluate_setup(B.declared_xau_request())
        assert evaluation.eligibility is SetupEligibility.WATCH
        assert SetupRefusalCode.PARAMETER_DECLARED_ONLY in evaluation.reasons


# ---------------------------------------------------------------------------
# T3 — trigger semantics (14)
# ---------------------------------------------------------------------------


class TestT3Triggers:
    def test_trigger_vocabulary_is_seven(self):
        assert {value.value for value in TriggerType} == {
            "TOUCH",
            "EXCURSION",
            "REJECTION",
            "ACCEPTANCE",
            "CLOSE",
            "SR_FLIP",
            "OCC",
        }
        assert TRIGGER_TYPES == tuple(TriggerType)

    def test_touch_satisfies_only_touch(self):
        assert _satisfied(_requirement(TriggerType.TOUCH), (B.touch(1),))
        assert not _satisfied(_requirement(TriggerType.TOUCH), (B.excursion(1),))
        assert not _satisfied(_requirement(TriggerType.EXCURSION), (B.touch(1),))

    def test_touch_cannot_satisfy_close(self):
        assert not _satisfied(_requirement(TriggerType.CLOSE), (B.touch(1),))

    def test_touch_cannot_satisfy_acceptance(self):
        assert not _satisfied(_requirement(TriggerType.ACCEPTANCE), (B.touch(1),))

    def test_touch_cannot_satisfy_rejection(self):
        assert not _satisfied(_requirement(TriggerType.REJECTION), (B.touch(1),))

    def test_close_requires_final_bar(self):
        assert not _satisfied(
            _requirement(TriggerType.CLOSE), (B.close_nonfinal(1),)
        )
        assert _satisfied(_requirement(TriggerType.CLOSE), (B.close_final(1),))

    def test_acceptance_requires_state_not_proximity(self):
        assert not _satisfied(
            _requirement(TriggerType.ACCEPTANCE), (B.acceptance(1, state_ref=None),)
        )
        assert _satisfied(
            _requirement(TriggerType.ACCEPTANCE),
            (B.acceptance(1, state_ref="ACCEPT.0001"),),
        )

    def test_rejection_requires_excursion_then_return(self):
        assert _satisfied(
            _requirement(TriggerType.REJECTION),
            (B.excursion(1), B.touch(2)),
        )
        assert not _satisfied(
            _requirement(TriggerType.REJECTION),
            (B.excursion(2), B.touch(1)),
        )
        assert _satisfied(_requirement(TriggerType.REJECTION), (B.rejection(1),))

    def test_sr_flip_requires_declared_flip(self):
        assert not _satisfied(
            _requirement(TriggerType.SR_FLIP), (B.sr_flip(1, state_ref=None),)
        )
        assert _satisfied(_requirement(TriggerType.SR_FLIP), (B.sr_flip(1),))

    def test_occ_requires_declared_occurrence(self):
        assert not _satisfied(
            _requirement(TriggerType.OCC), (B.occ(1, state_ref=None),)
        )
        assert _satisfied(_requirement(TriggerType.OCC), (B.occ(1),))

    def test_all_combination_requires_every_literal(self):
        requirement = _requirement(TriggerType.TOUCH, TriggerType.CLOSE)
        assert not _satisfied(requirement, (B.touch(1),))
        assert _satisfied(requirement, (B.touch(1), B.close_final(2)))

    def test_any_combination_requires_one_literal(self):
        requirement = _requirement(
            TriggerType.TOUCH, TriggerType.CLOSE, combination=TriggerCombination.ANY
        )
        assert _satisfied(requirement, (B.touch(1),))
        assert not _satisfied(requirement, (B.excursion(1),))

    def test_trigger_requirement_is_declared_not_inferred(self):
        card = xau_quarter_zone.card()
        assert card.trigger_requirement.source_ref.endswith("#Entry")
        assert TriggerType.EXCURSION in card.trigger_requirement.declared_types
        assert not hasattr(triggers, "infer_requirement")
        before = card.trigger_requirement.to_payload()
        triggers.satisfies(card.trigger_requirement, (B.excursion(1),))
        assert card.trigger_requirement.to_payload() == before

    def test_unsatisfied_trigger_yields_watch(self):
        evaluation = evaluate_setup(B.xau_request(observations=()))
        assert evaluation.eligibility is SetupEligibility.WATCH
        assert SetupRefusalCode.TRIGGER_NOT_SATISFIED in evaluation.reasons


# ---------------------------------------------------------------------------
# T4 — invalidation (10)
# ---------------------------------------------------------------------------


class TestT4Invalidation:
    def test_invalidation_trichotomy_is_separate(self):
        names = {field.name for field in dataclasses.fields(InvalidationSet)}
        assert names == {"price", "structural", "temporal"}
        with pytest.raises(SetupContractError):
            InvalidationSet(
                temporal=PriceInvalidation(
                    value=Decimal("5"),
                    magnitude_unit="XAU_POINTS",
                    materialization=ParameterMaterialization.DECLARED,
                    source_ref="XAU_QUARTER_ZONE_OPERATOR_CARD_V1.md",
                )
            )

    def test_price_invalidation_never_substitutes_temporal(self):
        resolved = InvalidationSet(
            price=PriceInvalidation(
                value=Decimal("5"),
                magnitude_unit="XAU_POINTS",
                materialization=ParameterMaterialization.DECLARED,
                source_ref="XAU_QUARTER_ZONE_OPERATOR_CARD_V1.md",
            )
        )
        assert "TEMPORAL" in resolved.unresolved_kinds()
        assert not isinstance(resolved.price, TemporalInvalidation)

    def test_temporal_invalidation_never_substitutes_price(self):
        resolved = InvalidationSet(
            temporal=TemporalInvalidation(
                bound_id="TEMP.SESSION.END",
                checkpoint="AFTER_0300_NY_END",
                source_ref="XAU_QUARTER_ZONE_OPERATOR_CARD_V1.md",
            )
        )
        assert "PRICE" in resolved.unresolved_kinds()
        assert not isinstance(resolved.temporal, PriceInvalidation)

    def test_structural_invalidation_is_typed(self):
        structural = StructuralInvalidation(
            condition_id="XAU.LADDER.80_FAMILY",
            state_ref="XAU.STRUCTURAL.80",
            source_ref="XAU_QUARTER_ZONE_OPERATOR_CARD_V1.md",
        )
        assert not hasattr(structural, "value")
        assert structural.condition_id == "XAU.LADDER.80_FAMILY"

    def test_absent_invalidation_kind_is_unresolved(self):
        assert InvalidationSet().unresolved_kinds() == (
            "PRICE",
            "STRUCTURAL",
            "TEMPORAL",
        )

    def test_active_price_invalidation_blocks(self):
        evaluation = evaluate_setup(
            B.xau_request(invalidation_events=InvalidationEvents(price_fired=True))
        )
        assert evaluation.eligibility is SetupEligibility.BLOCKED
        assert SetupRefusalCode.SETUP_INVALIDATED in evaluation.reasons

    def test_invalidation_dominates_satisfied_trigger(self):
        request = B.xau_request(
            invalidation_events=InvalidationEvents(structural_fired=True)
        )
        assert _satisfied(
            xau_quarter_zone.card().trigger_requirement, request.observations
        )
        evaluation = evaluate_setup(request)
        assert evaluation.eligibility is SetupEligibility.BLOCKED
        assert SetupRefusalCode.SETUP_INVALIDATED in evaluation.reasons

    def test_unmaterialized_ladder_invalidation_is_declared(self):
        price = xau_quarter_zone.card().default_invalidation_price
        assert price.materialization is ParameterMaterialization.DECLARED
        evaluation = evaluate_setup(B.declared_xau_request())
        assert evaluation.eligibility is SetupEligibility.WATCH

    def test_invalidation_requires_source_ref(self):
        with pytest.raises(SetupContractError):
            PriceInvalidation(
                value=Decimal("5"),
                magnitude_unit="XAU_POINTS",
                materialization=ParameterMaterialization.CANONICAL,
                source_ref="",
            )

    def test_invalidation_payload_is_decimal(self):
        with pytest.raises(SetupContractError):
            PriceInvalidation(
                value=1.5,  # type: ignore[arg-type]
                magnitude_unit="XAU_POINTS",
                materialization=ParameterMaterialization.DECLARED,
                source_ref="XAU_QUARTER_ZONE_OPERATOR_CARD_V1.md",
            )
        payload = _record().to_payload()
        assert isinstance(payload["invalidation_price"]["value"], str)
        assert invariants.contains_float(payload) is False


# ---------------------------------------------------------------------------
# T5 — targets and promotion (12)
# ---------------------------------------------------------------------------


class TestT5Targets:
    def test_target_order_is_canonical_not_sorted(self):
        declared = xau_quarter_zone.card().targets
        assert [target.declared_order_index for target in declared] == [0, 1, 2, 3]
        ordered = targets_module.order_targets(tuple(reversed(declared)))
        assert [target.target_id for target in ordered] == [
            target.target_id for target in declared
        ]

    def test_deeper_coordinate_is_not_auto_active(self):
        assert all(target.active is False for target in xau_quarter_zone.card().targets)

    def test_promotion_requires_declared_condition(self):
        confirmation = xau_quarter_zone.confirmation_targets()[0]
        with pytest.raises(TargetPromotionRefused):
            targets_module.promote_target(
                confirmation,
                transition_ref="TRANSITION.L1.CONFIRMED",
                transitions=(B.transition(),),
            )

    def test_target_promotion_without_authority_refuses(self):
        with pytest.raises(TargetPromotionRefused):
            targets_module.promote_target(
                xau_quarter_zone.primary_target(),
                transition_ref="TRANSITION.NOT_RECORDED",
                transitions=(B.transition(),),
            )

    def test_targets_preserve_first_delivery_order(self):
        order = targets_module.first_delivery_order(B.delivery_path())
        assert order == ("TARGET.CONFIRM_5", "TARGET.NEXT_QUARTER")

    def test_range_left_conditioning_preserved(self):
        extension = [
            target
            for target in fib_rekey.card().targets
            if target.target_id == "SETUP.FIB.TARGET.EXTENSION_185"
        ][0]
        assert extension.range_left_conditioned_on == ("FIB.REKEY.TRIGGERED",)

    def test_confirmation_state_is_not_core_target(self):
        for target in xau_quarter_zone.confirmation_targets():
            assert target.confirmation_only is True
            assert target.active is False
        with pytest.raises(TargetPromotionRefused):
            targets_module.promote_target(
                xau_quarter_zone.confirmation_targets()[0],
                transition_ref="TRANSITION.L1.CONFIRMED",
                transitions=(B.transition(),),
            )

    def test_target_requires_source_ref(self):
        with pytest.raises(SetupContractError):
            SetupTarget(target_id="SETUP.XAU.TARGET.X", declared_order_index=0, source_ref="")

    def test_target_order_stable_across_runs(self):
        first = targets_module.order_targets(xau_quarter_zone.card().targets)
        second = targets_module.order_targets(xau_quarter_zone.card().targets)
        assert [t.to_payload() for t in first] == [t.to_payload() for t in second]

    def test_target_promotion_requires_transition_ref(self):
        with pytest.raises(TargetPromotionRefused):
            targets_module.promote_target(xau_quarter_zone.primary_target())

    def test_promoted_target_keeps_prior_order(self):
        promoted = targets_module.promote_target(
            xau_quarter_zone.primary_target(),
            transition_ref="TRANSITION.L1.CONFIRMED",
            transitions=(B.transition(),),
        )
        assert promoted.declared_order_index == 0
        assert promoted.active is True
        assert promoted.transition_ref == "TRANSITION.L1.CONFIRMED"

    def test_target_cannot_be_invented(self):
        invented = SetupTarget(
            target_id="SETUP.XAU.TARGET.INVENTED",
            declared_order_index=0,
            source_ref="XAU_QUARTER_ZONE_OPERATOR_CARD_V1.md",
        )
        with pytest.raises(SetupContractError):
            evaluate_setup(B.xau_request(targets=(invented,)))


# ---------------------------------------------------------------------------
# T6 — XAU quarter-zone operator (14)
# ---------------------------------------------------------------------------


class TestT6Xau:
    def test_xau_card_is_manual_operator(self):
        card = xau_quarter_zone.card()
        assert card.execution_class is SetupClass.MANUAL_OPERATOR
        assert _record().manual_status is SetupClass.MANUAL_OPERATOR

    def test_xau_requires_after_three_context(self):
        card = xau_quarter_zone.card()
        assert card.requires_after_three_context is True
        assert card.required_clock_checkpoint == "AFTER_0300_NY"
        evaluation = evaluate_setup(
            B.xau_request(clock=SetupClock("NY", "BEFORE_0300_NY"))
        )
        assert evaluation.eligibility is SetupEligibility.UNRESOLVED
        assert SetupRefusalCode.CLOCK_UNRESOLVED in evaluation.reasons

    def test_xau_blind_touch_blocked(self):
        evaluation = evaluate_setup(B.xau_request(observations=(B.touch(1),)))
        assert evaluation.eligibility is SetupEligibility.BLOCKED
        assert SetupRefusalCode.BLIND_TOUCH_REFUSED in evaluation.reasons

    def test_xau_requires_excursion_into_zone(self):
        card = xau_quarter_zone.card()
        assert TriggerType.EXCURSION in card.trigger_requirement.declared_types
        assert not _satisfied(card.trigger_requirement, (B.close_final(1),))
        assert _satisfied(
            card.trigger_requirement, (B.excursion(1), B.close_final(2))
        )

    def test_xau_requires_rejection_or_close_or_flip(self):
        card = xau_quarter_zone.card()
        alternatives = {literal.trigger_type for literal in card.trigger_requirement.any_of}
        assert alternatives == {
            TriggerType.REJECTION,
            TriggerType.CLOSE,
            TriggerType.SR_FLIP,
        }
        for confirmation in (B.rejection(2), B.close_final(2), B.sr_flip(2)):
            assert _satisfied(card.trigger_requirement, (B.excursion(1), confirmation))

    def test_xau_l3_destination_only_blocked(self):
        extra = B.model_output(
            model_id="XAU.GAME.L3_DESTINATION.V1",
            layer=Layer.L3,
            side=DirectionSide.DOWN,
        )
        evaluation = evaluate_setup(B.xau_request(parents=(B.model_output(), extra)))
        assert evaluation.eligibility is SetupEligibility.BLOCKED

    def test_xau_parked_state_blocked(self):
        evaluation = evaluate_setup(
            B.xau_request(parents=(B.model_output(state="PARKED"),))
        )
        assert evaluation.eligibility is SetupEligibility.BLOCKED
        assert SetupRefusalCode.PARKED_STATE in evaluation.reasons

    def test_xau_forbidden_132_168_promotion_blocked(self):
        with pytest.raises(TargetPromotionRefused):
            xau_quarter_zone.assert_no_forbidden_promotion(
                Decimal("132"), Decimal("168")
            )
        xau_quarter_zone.assert_no_forbidden_promotion(
            Decimal("25"), Decimal("50")
        )

    def test_xau_zone_mapping_declared_caps_at_watch(self):
        evaluation = evaluate_setup(B.declared_xau_request())
        assert evaluation.eligibility is SetupEligibility.WATCH
        assert SetupRefusalCode.PARAMETER_DECLARED_ONLY in evaluation.reasons

    def test_xau_invalidation_declared_caps_at_watch(self):
        assert (
            xau_quarter_zone.card().default_invalidation_price.materialization
            is ParameterMaterialization.DECLARED
        )
        evaluation = evaluate_setup(B.declared_xau_request())
        assert evaluation.eligibility is SetupEligibility.WATCH

    def test_xau_targets_next_quarter_first(self):
        ordered = targets_module.order_targets(xau_quarter_zone.card().targets)
        assert ordered[0].target_id == xau_quarter_zone.PRIMARY_TARGET_ID
        assert xau_quarter_zone.primary_target().declared_order_index == 0

    def test_xau_small_moves_are_confirmation_states(self):
        confirmation = xau_quarter_zone.confirmation_targets()
        assert {target.target_id for target in confirmation} == set(
            xau_quarter_zone.CONFIRMATION_TARGET_IDS
        )
        assert all(target.confirmation_only for target in confirmation)
        assert all(not target.confirmation_only for target in [xau_quarter_zone.primary_target()])

    def test_xau_no_automation_permission(self):
        assert _record().automation_permitted is False
        evaluation = evaluate_setup(B.xau_request(surface=SetupSurface.AUTOMATION))
        assert evaluation.eligibility is SetupEligibility.BLOCKED
        assert SetupRefusalCode.AUTOMATION_NOT_APPROVED in evaluation.reasons

    def test_xau_evidence_refs_are_promotion_only(self):
        refs = xau_quarter_zone.evidence_refs()
        assert {ref.evidence_id for ref in refs} == {
            "EV.XAU.PROMOTION.68_80.V1",
            "EV.XAU.PROMOTION.120_132.V1",
        }
        for ref in refs:
            assert ref.claim_id is not None
            assert ref.population_key == "XAU.PROMOTION"
            assert ref.status in (EvidenceStatus.VALIDATED, EvidenceStatus.RESEARCH_FLAG)


# ---------------------------------------------------------------------------
# T7 — Fib Rekey operator (12)
# ---------------------------------------------------------------------------


class TestT7Fib:
    def test_fib_card_is_research_only(self):
        card = fib_rekey.card()
        assert card.execution_class is SetupClass.RESEARCH_ONLY
        assert card.exposure is ProductExposure.RESEARCH_LAB

    def test_fib_production_request_blocked(self):
        evaluation = evaluate_setup(B.fib_request(surface=SetupSurface.PRODUCTION))
        assert evaluation.eligibility is SetupEligibility.BLOCKED
        assert SetupRefusalCode.RESEARCH_ONLY_NOT_PRODUCTION in evaluation.reasons

    def test_fib_requires_valid_born_range(self):
        card = fib_rekey.card()
        assert card.requires_anchor is True
        assert set(card.parent_requirements[0].allowed_states) == {
            "RANGE_BORN",
            "RANGE_ACTIVE",
        }

    def test_fib_unresolved_anchor_unresolved(self):
        evaluation = evaluate_setup(B.fib_request())
        assert evaluation.eligibility is SetupEligibility.UNRESOLVED
        assert SetupRefusalCode.ANCHOR_UNRESOLVED in evaluation.reasons

    def test_fib_no_generic_pivot_fallback(self):
        assert fib_rekey.GENERIC_PIVOT_FALLBACK_AVAILABLE is False
        assert not any(
            callable(getattr(fib_rekey, name, None)) and "pivot" in name.lower()
            for name in dir(fib_rekey)
        )

    def test_fib_132_is_primary_rekey(self):
        assert fib_rekey.PRIMARY_REKEY == Decimal("132")
        first = targets_module.order_targets(fib_rekey.card().targets)[0]
        assert first.target_id == "SETUP.FIB.TARGET.REKEY_132"
        assert first.coordinate == Decimal("132")

    def test_fib_168_is_dual_entry_research(self):
        assert fib_rekey.HISTORICAL_DUAL_ENTRY == Decimal("168")
        target = [
            item
            for item in fib_rekey.card().targets
            if item.target_id == "SETUP.FIB.TARGET.DUAL_ENTRY_168"
        ][0]
        assert target.declared_order_index == 1
        assert target.active is False

    def test_fib_50_72_family_not_conflated(self):
        rekey_coordinates = {coordinate for _name, coordinate in fib_rekey.rekey_levels()}
        assert fib_rekey.RETRACE_FAMILY == ("RETRACE_50", "RETRACE_61", "RETRACE_72")
        assert not any("RETRACE" in name for name, _coordinate in fib_rekey.rekey_levels())
        assert Decimal("50") not in rekey_coordinates
        assert Decimal("72") not in rekey_coordinates

    def test_fib_r11_frequency_not_transferred(self):
        assert fib_rekey.R11_FREQUENCY_TRANSFER_ALLOWED is False
        facts = {fact.fact_id: dict(fact.payload) for fact in fib_rekey.lineage_facts()}
        assert facts["SETUP.FIB.R15"]["r11_frequency_transferred"] == "NO"

    def test_fib_lineage_explainable(self):
        facts = fib_rekey.lineage_facts()
        assert len(facts) == 3
        for fact in facts:
            assert re.match(r"^[A-Z][A-Z0-9_.]*$", fact.fact_id)
            for _key, value in fact.payload:
                assert " " not in value

    def test_fib_no_automated_signal(self):
        assert fib_rekey.AUTOMATION_PERMITTED is False
        evaluation = evaluate_setup(B.fib_request())
        assert evaluation.automation_permitted is False

    def test_fib_negative_evidence_attached(self):
        refs = fib_rekey.evidence_refs()
        assert len(refs) == 1
        assert refs[0].evidence_id == "EV.FIB.R11.ANCHOR_OVERGEN.V1"
        assert refs[0].status is EvidenceStatus.NO_GO
        assert refs[0].claim_id == "CL.FIB.R11.GENERATOR_FAILURE"


# ---------------------------------------------------------------------------
# T8 — JPY role-gated operator (14)
# ---------------------------------------------------------------------------


class TestT8Jpy:
    def test_jpy_card_is_manual_operator(self):
        card = jpy_role_gate.card()
        assert card.execution_class is SetupClass.MANUAL_OPERATOR
        assert _record(B.jpy_request()).manual_status is SetupClass.MANUAL_OPERATOR

    def test_jpy_role_map_is_verbatim(self):
        from app.forge.model_runtime.jpy_carry import ROLE_MAP

        assert jpy_role_gate.PAIR_ROLES == ROLE_MAP == {
            "USDJPY": "CARRY_MASTER",
            "AUDJPY": "RISK_EXPRESSION",
            "EURJPY": "CONFIRMATION_VETO",
        }

    def test_jpy_requires_usdjpy_master(self):
        assert jpy_role_gate.role_for("USDJPY") == "CARRY_MASTER"
        assert jpy_role_gate.PRIMARY_AGREEMENT[0] == "USDJPY"

    def test_jpy_requires_audjpy_expression(self):
        assert jpy_role_gate.role_for("AUDJPY") == "RISK_EXPRESSION"
        assert jpy_role_gate.PRIMARY_AGREEMENT[1] == "AUDJPY"

    def test_jpy_eurjpy_is_confirmation_veto(self):
        assert jpy_role_gate.role_for("EURJPY") == "CONFIRMATION_VETO"
        assert jpy_role_gate.CONFIRMATION_PAIR == "EURJPY"

    def test_jpy_confirmation_is_not_entry(self):
        card = jpy_role_gate.card()
        assert jpy_role_gate.CONFIRMATION_PAIR not in {
            kind.name for kind in card.trigger_requirement.declared_types
        }
        assert TriggerType.EXCURSION in card.trigger_requirement.declared_types

    def test_jpy_equal_vote_impossible(self):
        assert jpy_role_gate.equal_vote_supported() is False
        assert jpy_role_gate.AGGREGATE_FIELDS == ()
        assert not any(
            "vote" in field or "aggregate" in field
            for field in _package_dataclass_fields()
        )

    def test_jpy_pair_native_tier_required(self):
        evaluation = evaluate_setup(B.jpy_request(tier=B.jpy_tier(native=False)))
        assert evaluation.eligibility is SetupEligibility.BLOCKED
        assert SetupRefusalCode.TIER_NOT_NATIVE in evaluation.reasons

    def test_jpy_pair_no_go_blocked(self):
        evaluation = evaluate_setup(B.jpy_request(tier=B.jpy_tier(no_go=True)))
        assert evaluation.eligibility is SetupEligibility.BLOCKED
        assert SetupRefusalCode.NATIVE_TIER_NO_GO in evaluation.reasons

    def test_jpy_local_setup_from_selected_pair(self):
        request = B.jpy_request()
        level = jpy_role_gate.local_geometry(request, "USDJPY")
        assert level is not None
        assert level.level_id == "JPY.PAIR.L1"
        record = evaluate_setup(request).record
        assert record.location is not None

    def test_jpy_no_basket_confidence_field(self):
        payload = _record(B.jpy_request()).to_payload()
        assert not any("confidence" in key for key in payload)
        assert not any("basket_score" in key for key in payload)

    def test_jpy_no_automation_permission(self):
        assert jpy_role_gate.AUTOMATION_PERMITTED is False
        assert _record(B.jpy_request()).automation_permitted is False

    def test_jpy_historical_dt_not_imported(self):
        assert jpy_role_gate.HISTORICAL_DT_IMPORTED is False

    def test_jpy_relationship_not_win_rate(self):
        refs = jpy_role_gate.evidence_refs()
        assert len(refs) == 1
        assert refs[0].relationship is True
        assert refs[0].status is EvidenceStatus.VALIDATED
        claim = statistics.describe_relationship(
            claim_id="CL.JPY.CARRY.ROLE_RELATION",
            population_key="JPY.BASKET.ROLE",
            identity=B.claim_identity("USDJPY"),
            evidence=refs[0],
        )
        assert claim.relationship is True
        assert "win_rate" not in {field.name for field in dataclasses.fields(claim)}


# ---------------------------------------------------------------------------
# T9 — historical/manual ST + P90 lineage (12)
# ---------------------------------------------------------------------------


class TestT9StP90:
    def test_st_is_manual_historical_framework(self):
        framework = st_manual.framework()
        assert framework.framework_id == "ST.TIER_TO_AU_TO_TIER"
        assert framework.tier_chain == ("TIER", "AU", "TIER")
        assert framework.automation_permitted is False

    def test_st_automation_request_blocked(self):
        verdict, code = st_manual.automation_request_refused()
        assert verdict is SetupEligibility.BLOCKED
        assert code is SetupRefusalCode.AUTOMATION_NOT_APPROVED

    def test_st_perception_gap_unresolved(self):
        assert st_manual.framework().perception_gap == "UNRESOLVED"
        assert st_manual.PERCEPTION_GAP == "UNRESOLVED"

    def test_st_tier_au_tier_explainable(self):
        facts = {fact.fact_id: dict(fact.payload) for fact in st_manual.explain()}
        assert facts["SETUP.ST.CHAIN"]["chain"] == "TIER_TO_AU_TO_TIER"
        assert facts["SETUP.ST.AUTOMATION"]["automation_permitted"] == "NO"

    def test_st_creates_no_setup_identity(self):
        assert st_manual.framework().setup_identity is None
        assert not hasattr(st_manual, "SETUP_ID")
        with pytest.raises(ValueError):
            st_manual.ManualHistoricalFramework(setup_identity="SETUP.ST.V1")

    def test_p90_lineage_status_unverified(self):
        item = p90_lineage.lineage()
        assert item.status is p90_lineage.LineageStatus.UNVERIFIED
        assert item.automation_permitted is False

    def test_p90_automation_requires_verification(self):
        verified_but_unparified = p90_lineage.AutomationLineage(
            lineage_id="P90.TEST",
            version="V1",
            implementation_ref="app/forge/state_engine/failure_repair.py",
            parity_status="UNVERIFIED",
            evidence_refs=p90_lineage.lineage().evidence_refs,
            status=p90_lineage.LineageStatus.VERIFIED,
        )
        assert verified_but_unparified.automation_permitted is False
        verified = p90_lineage.AutomationLineage(
            lineage_id="P90.TEST",
            version="V1",
            implementation_ref="app/forge/state_engine/failure_repair.py",
            parity_status="PARITY_ESTABLISHED",
            evidence_refs=p90_lineage.lineage().evidence_refs,
            status=p90_lineage.LineageStatus.VERIFIED,
        )
        assert verified.automation_permitted is True

    def test_p90_requires_version_identity(self):
        with pytest.raises(SetupContractError):
            p90_lineage.AutomationLineage(
                lineage_id="P90.TEST",
                version="",
                implementation_ref="app/forge/state_engine/failure_repair.py",
                parity_status="UNVERIFIED",
                evidence_refs=p90_lineage.lineage().evidence_refs,
            )

    def test_p90_historical_claim_stays_historical(self):
        assert p90_lineage.historical_claim().status is EvidenceStatus.HISTORICAL

    def test_p90_no_current_performance_claim(self):
        with pytest.raises(SetupContractError):
            p90_lineage.restate_as_current(p90_lineage.historical_claim())

    def test_p90_lineage_evidence_refs_required(self):
        with pytest.raises(SetupContractError):
            p90_lineage.AutomationLineage(
                lineage_id="P90.TEST",
                version="V1",
                implementation_ref="app/forge/state_engine/failure_repair.py",
                parity_status="UNVERIFIED",
                evidence_refs=(),
            )

    def test_p90_automation_permitted_false_everywhere(self):
        assert p90_lineage.lineage().automation_permitted is False
        for card in SetupRegistry().cards():
            assert card.automation_permitted is False
        for evaluation in (
            evaluate_setup(B.xau_request()),
            evaluate_setup(B.fib_request()),
            evaluate_setup(B.jpy_request()),
        ):
            assert evaluation.automation_permitted is False


# ---------------------------------------------------------------------------
# T10 — setup result vs statistics (10)
# ---------------------------------------------------------------------------


class TestT10Statistics:
    def test_statistics_expose_no_numeric_result_type(self):
        assert NUMERIC_RESULT_TYPES == ()
        assert statistics.NUMERIC_RESULT_TYPES == ()

    def test_statistic_without_claim_ref_refuses(self):
        with pytest.raises(UnsupportedStatisticError):
            statistics.describe_statistic(
                claim_id=None,
                population_key="XAU.PROMOTION",
                identity=B.claim_identity(),
                evidence=B.unclaimed_evidence(),
            )

    def test_claim_population_must_match(self):
        with pytest.raises(ClaimPopulationMismatchError):
            statistics.describe_statistic(
                claim_id="CL.XAU.PROMOTION.120_132",
                population_key="XAU.PROMOTION",
                identity=B.claim_identity(),
                evidence=B.xau_evidence(),
            )
        with pytest.raises(ClaimPopulationMismatchError):
            statistics.describe_statistic(
                claim_id="CL.XAU.PROMOTION.68_80",
                population_key="XAU.OTHER",
                identity=B.claim_identity(),
                evidence=B.xau_evidence(),
            )

    def test_relationship_evidence_labelled_as_relationship(self):
        claim = statistics.describe_relationship(
            claim_id="CL.JPY.CARRY.ROLE_RELATION",
            population_key="JPY.BASKET.ROLE",
            identity=B.claim_identity("USDJPY"),
            evidence=B.jpy_relationship_evidence(),
        )
        assert claim.relationship is True
        with pytest.raises(UnsupportedStatisticError):
            statistics.describe_relationship(
                claim_id="CL.XAU.PROMOTION.68_80",
                population_key="XAU.PROMOTION",
                identity=B.claim_identity(),
                evidence=B.xau_evidence(),
            )

    def test_no_win_rate_field_anywhere(self):
        assert "win_rate" in FORBIDDEN_FIELD_NAMES
        assert "win_rate" not in _package_dataclass_fields()
        assert invariants.forbidden_keys(_record().to_payload()) == ()

    def test_no_expectancy_or_probability_field(self):
        assert "expectancy" not in _package_dataclass_fields()
        assert "probability" not in _package_dataclass_fields()
        assert invariants.forbidden_keys(_record().to_payload()) == ()

    def test_no_risk_reward_field(self):
        assert "risk_reward" not in _package_dataclass_fields()
        assert invariants.forbidden_keys(_record().to_payload()) == ()

    def test_evidence_refs_carry_status(self):
        refs = _record().evidence_refs
        assert refs
        for ref in refs:
            assert isinstance(ref.status, EvidenceStatus)
            assert isinstance(ref, EvidenceReference)

    def test_unsupported_statistic_refused_by_construction(self):
        with pytest.raises(UnsupportedStatisticError):
            statistics.SetupStatisticClaim(
                claim_id=None,  # type: ignore[arg-type]
                population_key="XAU.PROMOTION",
                identity=B.claim_identity(),
                evidence=B.xau_evidence(),
            )

    def test_no_performance_payload_in_setup_record(self):
        payload = _record().to_payload()
        assert invariants.forbidden_keys(payload) == ()
        assert invariants.contains_float(payload) is False


# ---------------------------------------------------------------------------
# T11 — adversarial setup matrix (16)
# ---------------------------------------------------------------------------


class TestT11Adversarial:
    def test_touch_without_rejection_refused(self):
        evaluation = evaluate_setup(B.xau_request(observations=(B.touch(1),)))
        assert evaluation.eligibility is SetupEligibility.BLOCKED
        assert SetupRefusalCode.BLIND_TOUCH_REFUSED in evaluation.reasons

    def test_valid_trigger_under_lock_blocked(self):
        request = B.xau_request(stand_down=B.stand_down_record())
        assert _satisfied(
            xau_quarter_zone.card().trigger_requirement, request.observations
        )
        evaluation = evaluate_setup(request)
        assert evaluation.eligibility is SetupEligibility.BLOCKED
        assert SetupRefusalCode.STAND_DOWN_LOCKED in evaluation.reasons
        assert "SETUP_ELIGIBILITY" in request.stand_down.capabilities_locked

    def test_l3_direction_without_l1_eligibility_blocked(self):
        extra = B.model_output(
            model_id="XAU.GAME.L3_CONTEXT.V1",
            layer=Layer.L3,
            side=DirectionSide.DOWN,
        )
        evaluation = evaluate_setup(B.xau_request(parents=(B.model_output(), extra)))
        assert evaluation.eligibility is SetupEligibility.BLOCKED
        assert SetupRefusalCode.LAYER_CONFLICT in evaluation.reasons

    def test_unresolved_r15_requested_as_production_blocked(self):
        evaluation = evaluate_setup(B.fib_request(surface=SetupSurface.PRODUCTION))
        assert evaluation.eligibility is SetupEligibility.BLOCKED
        assert SetupRefusalCode.RESEARCH_ONLY_NOT_PRODUCTION in evaluation.reasons

    def test_jpy_equal_vote_request_blocked(self):
        assert jpy_role_gate.equal_vote_supported() is False
        assert jpy_role_gate.AGGREGATE_FIELDS == ()
        payload = _record(B.jpy_request()).to_payload()
        assert not any("vote" in key or "score" in key for key in payload)

    def test_st_manual_framework_cannot_automate(self):
        verdict, code = st_manual.automation_request_refused()
        assert (verdict, code) == (
            SetupEligibility.BLOCKED,
            SetupRefusalCode.AUTOMATION_NOT_APPROVED,
        )
        with pytest.raises(ValueError):
            st_manual.ManualHistoricalFramework(automation_permitted=True)

    def test_unsupported_p90_claim_blocked(self):
        with pytest.raises(SetupContractError):
            p90_lineage.restate_as_current(p90_lineage.historical_claim())
        assert p90_lineage.lineage().status is p90_lineage.LineageStatus.UNVERIFIED

    def test_stale_data_request_blocked(self):
        evaluation = evaluate_setup(
            B.xau_request(data_quality=DataQualityFacts(stale=True))
        )
        assert evaluation.eligibility is SetupEligibility.BLOCKED
        assert SetupRefusalCode.DATA_QUALITY_BLOCKED in evaluation.reasons

    def test_wrong_tier_request_blocked(self):
        evaluation = evaluate_setup(B.xau_request(tier=B.xau_tier(native=False)))
        assert evaluation.eligibility is SetupEligibility.BLOCKED
        assert SetupRefusalCode.TIER_NOT_NATIVE in evaluation.reasons

    def test_parked_xau_setup_blocked(self):
        evaluation = evaluate_setup(
            B.xau_request(parents=(B.model_output(state="PARKED"),))
        )
        assert evaluation.eligibility is SetupEligibility.BLOCKED
        registry = SetupRegistry().with_status(
            xau_quarter_zone.SETUP_ID, CardStatus.PARKED
        )
        assert (
            evaluate_setup(B.xau_request(), registry=registry).eligibility
            is SetupEligibility.BLOCKED
        )

    def test_missing_setup_card_unresolved(self):
        evaluation = evaluate_setup(
            B.xau_request(setup_id="SETUP.XAU.QUARTER_ZONE.V9")
        )
        assert evaluation.eligibility is SetupEligibility.UNRESOLVED
        assert evaluation.card is None
        assert evaluation.record is None

    def test_version_drift_request_blocked(self):
        evaluation = evaluate_setup(B.xau_request(setup_version="0.9"))
        assert evaluation.eligibility is SetupEligibility.BLOCKED
        assert SetupRefusalCode.SETUP_VERSION_DRIFT in evaluation.reasons

    def test_unauthorized_target_promotion_blocked(self):
        with pytest.raises(TargetPromotionRefused):
            targets_module.promote_target(
                xau_quarter_zone.primary_target(),
                transition_ref="TRANSITION.L1.CONFIRMED",
            )
        invented = SetupTarget(
            target_id="SETUP.XAU.TARGET.INVENTED",
            declared_order_index=0,
            source_ref="XAU_QUARTER_ZONE_OPERATOR_CARD_V1.md",
        )
        with pytest.raises(SetupContractError):
            evaluate_setup(B.xau_request(targets=(invented,)))

    def test_ambiguous_intrabar_first_delivery_blocked(self):
        targets = (
            DeclaredTarget("TARGET.A", DeliverySide.ABOVE, 0),
            DeclaredTarget("TARGET.B", DeliverySide.BELOW, 1),
        )
        observations = (
            DeliveryObservation("TARGET.A", B.FIXED, "BAR.0001"),
            DeliveryObservation("TARGET.B", B.FIXED, "BAR.0001"),
        )
        with pytest.raises(AmbiguousPathError):
            build_path(
                clock_id="NY",
                targets=targets,
                observations=observations,
                intrabar_order_resolvable=False,
                requires_first_delivery=True,
            )
        assert not hasattr(targets_module, "resolve_intrabar_order")

    def test_model_state_serialized_as_signal_refused(self):
        payload = _record().to_payload()
        assert invariants.forbidden_keys(payload) == ()
        assert not any(key.endswith("_signal") for key in payload)
        assert not hasattr(contracts.SetupRecord, "to_signal")

    def test_refusals_are_recorded_not_raised(self):
        requests = (
            B.xau_request(observations=()),
            B.xau_request(parents=()),
            B.xau_request(tier=B.xau_tier(native=False)),
            B.xau_request(stand_down=B.stand_down_record()),
            B.xau_request(setup_version="0.9"),
            B.fib_request(surface=SetupSurface.PRODUCTION),
            B.jpy_request(tier=B.jpy_tier(no_go=True)),
        )
        for request in requests:
            evaluation = evaluate_setup(request)
            assert evaluation.eligibility is not SetupEligibility.ELIGIBLE
            assert evaluation.reasons
            assert set(code.value for code in evaluation.reasons) <= SETUP_REFUSAL_CODES


# ---------------------------------------------------------------------------
# T12 — boundaries, frozen integrity, security (14)
# ---------------------------------------------------------------------------


class TestT12Boundaries:
    def test_cross_platform_hash_stability(self):
        first = evaluate_setup(B.xau_request()).record
        second = evaluate_setup(B.xau_request()).record
        assert first.evaluation_hash == second.evaluation_hash
        assert "\r" not in first.to_json()
        manifest = json.loads(
            (_FIXTURES / "FIXTURE_MANIFEST.json").read_text(encoding="utf-8")
        )
        assert manifest["normalization"] == "LF"
        for name, digest in manifest["files"].items():
            assert canonical_sha256(_FIXTURES / name) == digest

    def test_engine_version_stamped(self):
        assert _record().engine_version == SETUP_ENGINE_VERSION
        assert versions.SETUP_ENGINE_VERSION == SETUP_ENGINE_VERSION

    def test_evaluation_hash_deterministic(self):
        payload = _record().to_payload()
        restored = SetupRecord.from_payload(payload)
        assert restored.evaluation_hash == _record().evaluation_hash
        assert restored.to_payload() == payload
        changed = evaluate_setup(B.declared_xau_request()).record
        assert changed.evaluation_hash != _record().evaluation_hash

    def test_frozen_upstream_hashes_unchanged(self):
        baseline = json.loads(
            (_FIXTURES / "FROZEN_BASELINE.json").read_text(encoding="utf-8")
        )
        assert baseline["module_counts"] == {
            "app/forge/market_data": 11,
            "app/forge/measurements": 12,
            "app/forge/model_runtime": 13,
            "app/forge/state_engine": 13,
        }
        for relative, expected in baseline["files"].items():
            assert canonical_sha256(_ROOT / relative) == expected, relative

    def test_import_direction_is_one_way(self):
        for package in (
            "app/forge/market_data",
            "app/forge/measurements",
            "app/forge/model_runtime",
            "app/forge/state_engine",
        ):
            for module in (_ROOT / package).glob("*.py"):
                assert "setup_engine" not in module.read_text(encoding="utf-8"), module
        allowed = (
            "app.forge.canonical",
            "app.forge.market_data",
            "app.forge.measurements",
            "app.forge.model_runtime",
            "app.forge.state_engine",
            "app.forge.schemas",
        )
        for name, source in _sources().items():
            for line in source.splitlines():
                if line.startswith("from app.") or line.startswith("import app."):
                    assert any(line.startswith(f"from {root}") for root in allowed), (
                        name,
                        line,
                    )

    def test_market_data_readiness_seam_unchanged(self):
        health = (_ROOT / "app/forge/service/health.py").read_text(encoding="utf-8")
        assert "NOT_CONFIGURED" in health
        assert "required=False" in health

    def test_migrations_unchanged(self):
        sql = _ROOT / "app/forge/persistence/sql"
        names = sorted(path.name for path in sql.glob("*.sql"))
        assert names == [
            "001_initial_schema.sql",
            "002_identity_session.sql",
            "003_vector_projection.sql",
            "004_audit_ledger.sql",
        ]
        assert not list(sql.glob("005_*.sql"))

    def test_no_filesystem_or_clock_access(self):
        patterns = (
            r"\bdatetime\b",
            r"\btime\.time\b",
            r"\bpathlib\b",
            r"open\(",
            r"\bos\.",
        )
        for name, source in _sources().items():
            for pattern in patterns:
                assert re.search(pattern, source) is None, (name, pattern)

    def test_no_float_in_payload(self):
        payload = _record().to_payload()
        assert invariants.contains_float(payload) is False
        assert "float" not in json.dumps(payload)

    def test_no_legacy_state_engine_import(self):
        for name, source in _sources().items():
            assert "app.state_engine" not in source, name
            assert "from app.state_engine" not in source, name

    def test_no_network_access(self):
        for name, source in _sources().items():
            for token in ("socket", "requests", "httpx", "urllib", "http://", "https://"):
                assert token not in source, (name, token)

    def test_no_provider_or_service_import(self):
        for name, source in _sources().items():
            assert "app.forge.service" not in source, name
            assert "app.forge.providers" not in source, name
            assert "app.services" not in source, name

    def test_no_secret_or_credential(self):
        for name, source in _sources().items():
            for token in ("api_key", "secret", "password", "bearer", "credential"):
                assert token not in source, (name, token)

    def test_registry_snapshot_is_deterministic(self):
        first = SetupRegistry().snapshot_hash()
        second = SetupRegistry().snapshot_hash()
        assert first == second
        fixtures = [
            path
            for path in _FIXTURES.glob("*.json")
            if path.name not in ("FIXTURE_MANIFEST.json", "FROZEN_BASELINE.json")
        ]
        assert len(fixtures) == 12
        generated = json.loads(
            (_FIXTURES / "setup_registry_cases.json").read_text(encoding="utf-8")
        )
        assert generated["provenance"] == "SYNTHETIC_FIXTURE"
        assert generated["canonical_source_slice"] == "CANONICAL_SOURCE_SLICE"
