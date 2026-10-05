import pytest
from pydantic import ValidationError

from app.forge.canonical import EvidenceStatus, EvidenceType, Layer, ProductExposure, SetupClass
from app.forge.schemas import EvidenceCard, ModelCard, SetupOperatorCard


def test_model_card_validates_typed_identity_and_evidence_refs():
    card = ModelCard(
        model_id="MOD.EUR.DAILY.V1", name="EUR Daily", version="1",
        status=EvidenceStatus.VALIDATED, market_scope=("EURUSD",), layer=Layer.L1,
        model_type="DISTRIBUTION", product_exposure=ProductExposure.SUBSCRIBER_MODEL,
        purpose="Estimate daily distribution.", evidence_card_ids=("EV.EUR.DAILY.TIERS.V1",),
        operator_interpretation="Context, not a guaranteed trade.",
        beginner_summary="Daily distribution context.", operator_summary="Use state and no-go.",
        researcher_summary="Evidence-bound model.", forbidden_overclaims=("Not deterministic.",)
    )
    assert card.model_id.startswith("MOD.")


def test_model_card_rejects_claim_id_as_model_id():
    with pytest.raises(ValidationError):
        ModelCard(
            model_id="CL.EUR.X.V1", name="x", version="1", status=EvidenceStatus.CANDIDATE,
            market_scope=("EURUSD",), layer=Layer.L1, model_type="STATE",
            product_exposure=ProductExposure.RESEARCH_LAB, purpose="x",
            operator_interpretation="x", beginner_summary="x", operator_summary="x",
            researcher_summary="x"
        )


def test_evidence_card_requires_evidence_and_claim_id_types():
    card = EvidenceCard(
        evidence_id="EV.EUR.HO.D3.V1", claim_id="CL.EUR.HO.D3.V1", title="D3 direction",
        status=EvidenceStatus.FORWARD_OOS, evidence_type=EvidenceType.SCIENTIFIC_RETEST,
        source_artifact="ART.EUR.HO.PDF.V1", source_generation="modern", market="EURUSD",
        data_period="2005Q3-2026Q2", sample_n=59, exact_claim="D3 aligned with quarter direction.",
        event_definition="D3 close direction", conditioning_event="complete quarter",
        clock_origin="quarter open", horizon="quarter close", tolerance="direction",
        eligibility_filter="complete quarters", numerator=41, denominator=59, metric="rate",
        result="69.5%", calculation_type="empirical", implementation_name="scientific review",
        version_or_hash="v1", execution_semantics="research", data_granularity="H1",
        session_definition="quarter", clock_mode="calendar", reproduction_status="reviewed",
        interpretation="Supports directional association.", does_not_support=("Trade WR.",),
        product_exposure=ProductExposure.SUBSCRIBER_MODEL
    )
    assert card.sample_n == 59


def test_setup_card_enforces_parent_reference_types():
    with pytest.raises(ValidationError):
        SetupOperatorCard(
            setup_id="SET.XAU.QUARTER.V1", name="Quarter Zone", version="1",
            status=EvidenceStatus.VALIDATED, market_scope=("XAUUSD",),
            execution_class=SetupClass.MANUAL_OPERATOR,
            parent_model_ids=("EV.XAU.BAD.V1",),
            product_exposure=ProductExposure.OPERATOR_ONLY,
            purpose="Operator location.", eligibility=("after 03 NY",), entry=("rejection",),
            invalidation=("current rule",), targets=("next quarter",), no_go=("invalid state",),
            l3_destination="quarter", l2_path="path", l1_execution="entry",
            failure_repair="stand down", manual_rule_source="canonical setup",
            automation_status="not approved", parity_status="manual",
            beginner_summary="manual setup", operator_instructions="follow rules",
            researcher_notes="evidence-bound"
        )
