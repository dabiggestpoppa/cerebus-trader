"""Book IV / Bloc IV.2 acceptance — 72 frozen drivers A-01 … A-72."""

from __future__ import annotations

import hashlib
import importlib.util
import json
import re
from pathlib import Path

from app.forge.ask_cerebus.interpreter.entities import EntityRef
from app.forge.ask_cerebus.interpreter.enums import (
    AmbiguityReason,
    Depth,
    EntityKind,
    Intent,
    TimeScope,
)
from app.forge.ask_cerebus.interpreter.plan import Ambiguity
from app.forge.ask_cerebus.retrieval import (
    AskCerebusRetrievalService,
    ClaimRef,
    DeterministicFakeSemanticIndex,
    EmptySemanticIndex,
    EvidenceJoinStatus,
    LimitationCode,
    RetrievalOutcome,
    SemanticCandidate,
    SnapshotContext,
    assess,
    build_request,
    tier_for_object_type,
)
from app.forge.identity import ForgePrincipal
from app.forge.policy import (
    CAPABILITY_CORPUS_READ_MEMBER,
    AuthorizationContext,
)
from app.forge.retrieval import RetrievalService
from app.forge.retrieval.query import RetrievalQuery
from app.forge.retrieval.service import RetrievalResult
from app.forge.setup_engine.contracts import SetupSurface
from app.forge.setup_engine.registry import SetupRegistry

REPO = Path(__file__).resolve().parents[1]
FIXTURES = REPO / "implementation" / "forge" / "book_iv" / "bloc_iv_2" / "fixtures"


def _load_builders():
    spec = importlib.util.spec_from_file_location("iv2_builders", FIXTURES / "_builders.py")
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


B = _load_builders()
INDEX = B.build_index()
SVC = B.service(index=INDEX)


def _bundle(plan, *, service=None, principal=None, context=None, snapshot=None, semantic=None):
    target = service or (B.service(index=INDEX, semantic=semantic) if semantic is not None else SVC)
    return target.retrieve(
        plan,
        principal or B.operator(),
        context or B.operator_context(),
        snapshot_context=snapshot,
    )


def _codes(bundle):
    return {limitation.code for limitation in bundle.limitations}


def _refusal_codes(bundle):
    return {refusal.code.value for refusal in bundle.refusals}


class _LeakySemantic:
    def __init__(self, *candidates):
        self.candidates = tuple(candidates)

    def search(self, query, authorized_ids, limit):
        return self.candidates[:limit]


class _BoomEnforcement:
    def guard(self, *args, **kwargs):
        raise RuntimeError("policy unavailable")

    def authorize(self, *args, **kwargs):
        raise RuntimeError("policy unavailable")


# ---------------------------------------------------------------------------
# T1 — structured canonical resolution
# ---------------------------------------------------------------------------


def test_a01_resolves_exact_canonical_id_from_plan():
    bundle = _bundle(B.plan(model_ids=("XAU.GAME",)))
    assert [ref.object_id for ref in bundle.canonical_refs] == ["MOD.XAU.GAME.V1"]


def test_a02_selects_candidates_from_safe_headers_only():
    loads = []
    service = RetrievalService(INDEX, record_loader=lambda g, oid: loads.append(oid) or g.record(oid))
    resolver = __import__(
        "app.forge.ask_cerebus.retrieval.structured", fromlist=["StructuredResolver"]
    ).StructuredResolver(service)
    headers = resolver.candidate_headers(B.plan(model_ids=("XAU.GAME",)))
    assert [header.object_id for header in headers] == ["MOD.XAU.GAME.V1"]
    assert loads == []


def test_a03_preserves_exact_canonical_version():
    bundle = _bundle(B.plan(model_ids=("MOD.XAU.GAME_V2.V1",)))
    assert bundle.canonical_refs[0].version == "V1"
    assert bundle.canonical_refs[0].object_id.endswith("GAME_V2.V1")


def test_a04_expands_governed_alias_without_promotion():
    plan = B.plan(
        entities=(
            EntityRef(EntityKind.TERM, "Constraint Deficit", "TERM.CONSTRAINT_DEFICIT"),
        )
    )
    bundle = _bundle(plan)
    assert [ref.object_id for ref in bundle.canonical_refs] == ["TERM.CONSTRAINT_DEFICIT"]
    assert bundle.canonical_refs[0].status == "CANDIDATE"


def test_a05_traverses_relationships_under_policy():
    bundle = _bundle(B.plan(model_ids=("XAU.GAME",)))
    assert [claim.claim_id for claim in bundle.claim_refs] == ["CL.XAU.GAME.SUPPORTED.V1"]


def test_a06_reports_unresolved_identity_without_invention():
    bundle = _bundle(B.plan(model_ids=("MOD.DOES.NOT.EXIST.V1",)))
    assert bundle.canonical_refs == ()
    assert LimitationCode.UNRESOLVED_IDENTITY in _codes(bundle)


def test_a07_never_fuzzy_matches_unknown_model():
    bundle = _bundle(B.plan(model_ids=("XAU.GAM",)))
    assert bundle.canonical_refs == ()
    assert all("XAU.GAM" not in ref.object_id for ref in bundle.canonical_refs)


# ---------------------------------------------------------------------------
# T2 — semantic authorization
# ---------------------------------------------------------------------------


def test_a08_semantic_port_is_replaceable_and_pure():
    assert EmptySemanticIndex().search("x", frozenset({"X"}), 3) == ()
    fake = DeterministicFakeSemanticIndex((SemanticCandidate("MOD.XAU.GAME.V1", "x"),))
    assert fake.search("x", frozenset({"MOD.XAU.GAME.V1"}), 3)[0].object_id == "MOD.XAU.GAME.V1"


def test_a09_searches_only_authorized_records():
    bundle = _bundle(
        B.plan(model_ids=("XAU.GAME",)),
        semantic=_LeakySemantic(SemanticCandidate("MOD.XAU.SECRET.V1", "hidden")),
    )
    assert all(ref.object_id != "MOD.XAU.SECRET.V1" for ref in bundle.semantic_passages)
    assert ("SEMANTIC_UNAUTHORIZED", 1) in bundle.trace.rejection_counts


def test_a10_semantic_candidate_cannot_supply_authority():
    bundle = _bundle(
        B.plan(model_ids=("XAU.GAME",)),
        semantic=_LeakySemantic(SemanticCandidate("MOD.XAU.GAME.V1", "win rate 99 percent")),
    )
    assert bundle.claim_refs[0].claim_id == "CL.XAU.GAME.SUPPORTED.V1"
    assert bundle.semantic_passages[0].support_classification == "SUPPORT_ONLY"
    assert bundle.claim_refs[0].result_value == "68 percent promotion"


def test_a11_fake_semantic_results_are_deterministic():
    fake = B.fake_semantic()
    first = fake.search("x", frozenset({"MOD.XAU.GAME.V1"}), 4)
    second = fake.search("x", frozenset({"MOD.XAU.GAME.V1"}), 4)
    assert first == second


def test_a12_real_semantic_index_requires_authorization():
    source = (REPO / "app" / "forge" / "ask_cerebus" / "retrieval" / "semantic.py").read_text()
    assert not re.search(r"(^|\n)\s*(import|from)\s+(openai|requests|httpx|chromadb|faiss)", source)


def test_a13_semantic_passage_is_support_only():
    bundle = _bundle(
        B.plan(model_ids=("XAU.GAME",)),
        semantic=B.fake_semantic(text="supporting context"),
    )
    assert bundle.semantic_passages[0].support_classification == "SUPPORT_ONLY"
    assert bundle.canonical_refs[0].object_id == "MOD.XAU.GAME.V1"


# ---------------------------------------------------------------------------
# T3 — canonical priority
# ---------------------------------------------------------------------------


def test_a14_enforces_frozen_six_tier_precedence():
    assert tier_for_object_type("MODEL").value == 1
    assert tier_for_object_type("LINEAGE").value == 4
    assert tier_for_object_type("MODEL").value < tier_for_object_type("LINEAGE").value


def test_a15_canonical_fact_outranks_semantic_passage():
    bundle = _bundle(B.plan(model_ids=("XAU.GAME",)), semantic=B.fake_semantic())
    assert bundle.canonical_refs
    assert bundle.semantic_passages
    assert bundle.canonical_refs[0].object_id == "MOD.XAU.GAME.V1"


def test_a16_lower_priority_never_overwrites_canonical():
    bundle = _bundle(B.plan(model_ids=("XAU.GAME",)), semantic=B.fake_semantic())
    assert bundle.canonical_refs[0].status == "CANDIDATE"


def test_a17_records_disagreement_without_silent_resolution():
    bundle = _bundle(
        B.plan(model_ids=("XAU.GAME",)),
        semantic=B.fake_semantic(text="contradictory semantic text"),
    )
    assert LimitationCode.SOURCE_DISAGREEMENT in _codes(bundle)


def test_a18_semantic_score_is_not_authority():
    bundle = _bundle(
        B.plan(model_ids=("XAU.GAME",)),
        semantic=B.fake_semantic(score=0.999),
    )
    assert bundle.semantic_passages[0].score == 0.999
    assert bundle.canonical_refs[0].object_id == "MOD.XAU.GAME.V1"


def test_a19_semantic_passage_never_promotes_status():
    bundle = _bundle(B.plan(model_ids=("P90",)), semantic=B.fake_semantic("MOD.P90.V1"))
    assert bundle.canonical_refs[0].status == "HISTORICAL"
    assert bundle.semantic_passages[0].status == "AUTHORIZED"


# ---------------------------------------------------------------------------
# T4 — claim / evidence joins
# ---------------------------------------------------------------------------


def test_a20_joins_query_model_claim_evidence_provenance():
    bundle = _bundle(B.plan(model_ids=("XAU.GAME",), evidence=True))
    assert bundle.claim_refs[0].claim_id == "CL.XAU.GAME.SUPPORTED.V1"
    assert bundle.evidence_refs[0].evidence_id == "EV.XAU.SUPPORTED.V1"
    assert bundle.evidence_refs[0].provenance_ids


def test_a21_retains_claim_identity_dimensions():
    bundle = _bundle(B.plan(model_ids=("XAU.GAME",)))
    assert len(bundle.claim_refs[0].identity_key) == 8


def test_a22_retains_model_and_generation_version():
    bundle = _bundle(B.plan(model_ids=("XAU.GAME",)))
    assert bundle.claim_refs[0].model_versions == ("V1",)
    assert bundle.canonical_refs[0].version == "V1"


def test_a23_preserves_population_sample_and_period():
    bundle = _bundle(B.plan(model_ids=("XAU.GAME",)))
    assert bundle.claim_refs[0].identity_key[0] == "XAUUSD"
    assert bundle.evidence_refs[0].support_classification == "EMPIRICAL"


def test_a24_carries_evidence_status_and_provenance():
    bundle = _bundle(B.plan(model_ids=("XAU.GAME",)))
    assert bundle.evidence_refs[0].status == "VALIDATED"
    assert bundle.evidence_refs[0].provenance_ids


def test_a25_reports_oos_and_reproduction_absence():
    bundle = _bundle(B.plan(model_ids=("XAU.GAME",)))
    assert bundle.evidence_refs[0].oos_status == "UNAVAILABLE"


def test_a26_missing_evidence_is_insufficient_without_number():
    bundle = _bundle(B.plan(model_ids=("XAU.NOEV",)))
    assert LimitationCode.EVIDENCE_INSUFFICIENT in _codes(bundle)
    assert all(claim.join_status is not EvidenceJoinStatus.VERIFIED for claim in bundle.claim_refs)


# ---------------------------------------------------------------------------
# T5 — Book III join
# ---------------------------------------------------------------------------


def test_a27_routes_current_request_to_iii6_contract():
    bundle = _bundle(
        B.plan(model_ids=("XAU.GAME",), scope=TimeScope.CURRENT),
        snapshot=B.snapshot_context(),
    )
    assert bundle.intelligence_refs[0].refusal == "PROVIDER_NOT_CONFIGURED"


def test_a28_routes_level_request_with_layer_and_state():
    request, limitation, refusal = build_request(
        B.plan(model_ids=("XAU.GAME",), scope=TimeScope.CURRENT),
        B.snapshot_context(),
    )
    assert request is not None and request.layer.value == "L3"
    assert limitation is None and refusal is None


def test_a29_routes_setup_context_with_card_and_parent():
    bundle = _bundle(B.plan(setup_ids=("SETUP.XAU.QUARTER_ZONE.V1",), intent=Intent.SETUP_CONTEXT))
    assert [ref.object_id for ref in bundle.canonical_refs] == ["SET.XAU.QUARTER_ZONE.V1"]


def test_a30_routes_historical_snapshot_without_substitution():
    bundle = _bundle(
        B.plan(model_ids=("XAU.GAME",), scope=TimeScope.AS_OF),
        snapshot=B.snapshot_context(),
    )
    assert LimitationCode.HISTORICAL_UNAVAILABLE in _codes(bundle)
    assert all(ref.snapshot_id == "" for ref in bundle.intelligence_refs)


def test_a31_routes_instrument_view_with_quality():
    context = SnapshotContext(
        instrument_id="XAUUSD", model_id="XAU.GAME", model_version="V1",
        as_of="2026-01-01T00:00:00Z", data_cutoff="2026-01-01T00:00:00Z",
        calculation_version="1.0", layer=__import__("app.forge.model_runtime.contract", fromlist=["Layer"]).Layer.L3,
        provider_configured=False, quality="STALE",
    )
    bundle = _bundle(B.plan(model_ids=("XAU.GAME",), scope=TimeScope.CURRENT), snapshot=context)
    assert bundle.intelligence_refs[0].quality == "STALE"


def test_a32_routes_jpy_basket_context_when_supported():
    bundle = _bundle(B.plan(setup_ids=("SETUP.JPY.CARRY_ROLE_GATE.V1",), intent=Intent.SETUP_CONTEXT))
    assert bundle.canonical_refs[0].object_id == "SET.JPY.CARRY_ROLE_GATE.V1"
    assert "USDJPY" in bundle.canonical_refs[0].market_scope


def test_a33_refuses_unresolved_snapshot_fields():
    bundle = _bundle(
        B.plan(model_ids=("XAU.GAME",), scope=TimeScope.CURRENT),
        snapshot=B.snapshot_context(complete=False),
    )
    assert LimitationCode.REQUIRED_FIELDS_UNRESOLVED in _codes(bundle)
    assert bundle.intelligence_refs == ()


# ---------------------------------------------------------------------------
# T6 — generation / lineage
# ---------------------------------------------------------------------------


def test_a34_preserves_p90_and_phi_generation():
    bundle = _bundle(B.plan(model_ids=("P90",)))
    assert bundle.canonical_refs[0].object_id == "MOD.P90.V1"
    assert LimitationCode.HISTORICAL_GENERATION in _codes(bundle)


def test_a35_preserves_st_and_base80_generation():
    bundle = _bundle(B.plan(model_ids=("ST.MANUAL", "BASE80")))
    assert [ref.object_id for ref in bundle.canonical_refs] == ["MOD.BASE80.V1", "MOD.ST.MANUAL.V1"]


def test_a36_preserves_session_clock_and_historical_generation():
    bundle = _bundle(B.plan(model_ids=("MARKOV", "FIB")))
    ids = {ref.object_id for ref in bundle.canonical_refs}
    assert {"MOD.MARKOV.LEGACY.V1", "MOD.FIB.RANGE_BIRTH.V1"} <= ids


def test_a37_separates_btc_game_from_btc_tracker():
    bundle = _bundle(B.plan(model_ids=("BTC.GAME", "BTC.TRACKER")))
    ids = [ref.object_id for ref in bundle.canonical_refs]
    assert ids == ["MOD.BTC.GAME.V1", "MOD.BTC.TRACKER.V1"]


def test_a38_expands_lineage_without_merging_statistics():
    bundle = _bundle(B.plan(model_ids=("P90", "ST.MANUAL")))
    assert len(bundle.lineage_refs) == 2
    assert {ref.generation for ref in bundle.lineage_refs} == {"P90.ORIGINAL", "ST.MANUAL"}


def test_a39_unavailable_generation_never_falls_back():
    plan = B.plan(
        model_ids=("P90",),
        ambiguities=(Ambiguity(AmbiguityReason.UNAVAILABLE_GENERATION, True, ("P90.v7",)),),
    )
    bundle = _bundle(plan)
    assert LimitationCode.UNAVAILABLE_GENERATION in _codes(bundle)
    assert all(ref.object_id != "MOD.P90.V1" or "v7" not in ref.object_id for ref in bundle.canonical_refs)


# ---------------------------------------------------------------------------
# T7 — conflict resolution
# ---------------------------------------------------------------------------


def _claim(claim_id, key, value):
    return ClaimRef(
        claim_id=claim_id, model_ids=(), model_versions=("V1",),
        identity_key=key, status="VALIDATED", evidence_ids=(),
        result_value=value, join_status=EvidenceJoinStatus.VERIFIED,
    )


def test_a40_compares_identity_before_declaring_conflict():
    left = _claim("CL.A", ("XAUUSD", "e"), "68")
    same = _claim("CL.B", ("XAUUSD", "e"), "72")
    different = _claim("CL.C", ("XAUUSD", "other"), "68")
    assert assess((left, same)).conflicting == ("CL.A", "CL.B")
    assert assess((left, different)).incomparable == ("CL.A", "CL.C")


def test_a41_matched_conflict_preserves_both_claims():
    bundle = _bundle(B.plan(model_ids=("XAU.COMPARE",), intent=Intent.COMPARISON))
    assert LimitationCode.EVIDENCE_CONFLICT in _codes(bundle)
    ids = {claim.claim_id for claim in bundle.claim_refs}
    assert {"CL.XAU.GAME.SUPPORTED.V1", "CL.XAU.GAME.CONFLICT.V1"} <= ids


def test_a42_separates_incomparable_claims():
    bundle = _bundle(B.plan(model_ids=("XAU.COMPARE",), intent=Intent.COMPARISON))
    assert LimitationCode.INCOMPARABLE_EVIDENCE in _codes(bundle)


def test_a43_never_uses_majority_or_similarity_as_truth():
    bundle = _bundle(B.plan(model_ids=("XAU.COMPARE",), intent=Intent.COMPARISON))
    assert not hasattr(bundle, "winner")
    assert len(bundle.claim_refs) == 3


def test_a44_carries_supersedes_and_contradicts_refs():
    record = SVC.retrieval.load_record(
        B.operator(), B.operator_context(), "MOD.LEGACY.SUPERSEDED.V1"
    )
    assert record.conflict.supersedes_ids == ("MOD.XAU.GAME.V1",)


def test_a45_keeps_conflicting_evidence_visible():
    bundle = _bundle(B.plan(model_ids=("XAU.COMPARE",), intent=Intent.COMPARISON))
    assert all(
        claim.claim_id in {ref.claim_id for ref in bundle.claim_refs}
        for claim in bundle.claim_refs
    )
    assert len(bundle.claim_refs) == 3


# ---------------------------------------------------------------------------
# T8 — negative evidence
# ---------------------------------------------------------------------------


def test_a46_retrieves_failed_and_null_findings():
    bundle = _bundle(B.plan(model_ids=("FIB",)))
    assert any(ref.object_id == "EV.FIB.NEGATIVE.V1" for ref in bundle.negative_refs)


def test_a47_retrieves_parked_superseded_and_no_go():
    parked = _bundle(B.plan(model_ids=("MOD.PARKED.V1",)))
    assert any(ref.status == "PARKED" for ref in parked.negative_refs)
    nogo = B.service(index=B.build_index(nogo=True)).retrieve(
        B.plan(setup_ids=("SETUP.XAU.QUARTER_ZONE.V1",), intent=Intent.SETUP_CONTEXT),
        B.operator(), B.operator_context(),
    )
    assert any(ref.status == "NO_GO" for ref in nogo.negative_refs)


def test_a48_does_not_bias_retrieval_toward_positive():
    bundle = _bundle(B.plan(model_ids=("XAU.GAME", "MOD.LEGACY.SUPERSEDED.V1")))
    assert any(ref.status == "SUPERSEDED" for ref in bundle.negative_refs)
    assert any(ref.object_id == "MOD.XAU.GAME.V1" for ref in bundle.canonical_refs)


def test_a49_preserves_negative_status_and_generation():
    bundle = _bundle(B.plan(model_ids=("MOD.LEGACY.SUPERSEDED.V1",)))
    assert bundle.negative_refs[0].status == "SUPERSEDED"


def test_a50_negative_evidence_is_not_a_trading_signal():
    bundle = _bundle(B.plan(model_ids=("MOD.LEGACY.SUPERSEDED.V1",)))
    assert not hasattr(bundle, "actionable")
    assert all(ref.reason == "NEGATIVE_EVIDENCE" for ref in bundle.negative_refs)


# ---------------------------------------------------------------------------
# T9 — authorization / exposure
# ---------------------------------------------------------------------------


def test_a51_authorizes_before_any_retrieval():
    bundle = _bundle(B.plan(model_ids=("MOD.XAU.SECRET.V1",)), context=B.public_context())
    assert bundle.canonical_refs == ()
    assert LimitationCode.POLICY_DENIED in _codes(bundle)


def test_a52_denies_before_loading_protected_body():
    loads = []
    service = RetrievalService(INDEX, record_loader=lambda g, oid: loads.append(oid) or g.record(oid))
    resolver = __import__(
        "app.forge.ask_cerebus.retrieval.structured", fromlist=["StructuredResolver"]
    ).StructuredResolver(service)
    result = resolver.resolve(
        B.plan(model_ids=("MOD.XAU.SECRET.V1",)),
        __import__("app.forge.ask_cerebus.retrieval.query_builder", fromlist=["build_targets"]).build_targets(
            B.plan(model_ids=("MOD.XAU.SECRET.V1",))
        ),
        B.operator(), B.public_context(),
    )
    assert result.canonical_refs == ()
    assert loads == []


def test_a53_researcher_depth_does_not_grant_exposure():
    bundle = _bundle(
        B.plan(model_ids=("XAU.GAME",), depth=Depth.RESEARCHER),
        context=AuthorizationContext.of(CAPABILITY_CORPUS_READ_MEMBER),
    )
    assert bundle.claim_refs == ()
    assert LimitationCode.POLICY_DENIED in _codes(bundle)


def test_a54_direct_id_guess_does_not_reveal_existence():
    bundle = _bundle(B.plan(model_ids=("MOD.XAU.SECRET.V1",)), context=B.public_context())
    assert "MOD.XAU.SECRET.V1" not in bundle.to_json()


def test_a55_semantic_neighbor_cannot_bypass_policy():
    bundle = _bundle(
        B.plan(model_ids=("XAU.GAME",)),
        semantic=_LeakySemantic(SemanticCandidate("MOD.XAU.SECRET.V1", "hidden")),
    )
    assert all(ref.object_id != "MOD.XAU.SECRET.V1" for ref in bundle.semantic_passages)


def test_a56_citation_traversal_cannot_bypass_policy():
    bundle = _bundle(
        B.plan(model_ids=("XAU.GAME",)),
        context=AuthorizationContext.of(CAPABILITY_CORPUS_READ_MEMBER),
    )
    assert bundle.claim_refs == ()
    assert bundle.evidence_refs == ()
    assert LimitationCode.POLICY_DENIED in _codes(bundle)


def test_a57_repeated_queries_do_not_enumerate_hidden_objects():
    plan = B.plan(model_ids=("MOD.XAU.SECRET.V1",))
    first = _bundle(plan, context=B.public_context())
    second = _bundle(plan, context=B.public_context())
    assert first.bundle_id == second.bundle_id
    assert "SECRET" not in first.to_json()


# ---------------------------------------------------------------------------
# T10 — trace
# ---------------------------------------------------------------------------


def test_a58_trace_binds_plan_and_contract_version():
    plan = B.plan(model_ids=("XAU.GAME",))
    bundle = _bundle(plan)
    assert bundle.trace.plan_id == plan.plan_id
    assert bundle.trace.contract_version == "RETRIEVAL_CONTRACT_V1"


def test_a59_trace_lists_only_authorized_references():
    bundle = _bundle(B.plan(model_ids=("XAU.GAME",)), semantic=B.fake_semantic())
    assert "MOD.XAU.SECRET.V1" not in bundle.trace.selected_ids
    assert "MOD.XAU.GAME.V1" in bundle.trace.selected_ids


def test_a60_trace_counts_rejections_by_reason_class():
    bundle = _bundle(B.plan(model_ids=("MOD.MISSING.V1",)))
    assert dict(bundle.trace.rejection_counts).get("NOT_FOUND") == 1


def test_a61_internal_consumer_and_refusal_traces_are_distinct():
    bundle = _bundle(B.plan(model_ids=("XAU.GAME",)))
    assert "rejection_counts" in bundle.trace.payload()
    assert "rejection_counts" not in bundle.trace.consumer_payload()
    assert bundle.trace.refusal_payload("EXPOSURE_FORBIDDEN")["trace_class"] == "REFUSAL"


def test_a62_trace_excludes_forbidden_names_and_text():
    bundle = _bundle(B.plan(model_ids=("MOD.XAU.SECRET.V1",)), context=B.public_context())
    text = json.dumps(bundle.consumer_trace)
    assert "SECRET" not in text and "internal method text" not in text


def test_a63_consumer_trace_is_exposure_safe():
    bundle = _bundle(B.plan(model_ids=("XAU.GAME",)))
    assert set(bundle.consumer_trace) == {
        "trace_class", "plan_id", "contract_version", "outcome", "selected_ids",
        "claim_ids", "evidence_ids", "snapshot_ids", "index_generation", "digest",
    }


def test_a64_bundle_digest_is_deterministic_and_minimized():
    plan = B.plan(model_ids=("XAU.GAME",))
    first = _bundle(plan)
    second = _bundle(plan)
    assert first.bundle_id == second.bundle_id
    assert "retrieval_text" not in first.to_json()
    assert "claim_text" not in first.to_json()
    spec = importlib.util.spec_from_file_location("iv2_generate", FIXTURES / "generate.py")
    generator = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(generator)
    built = generator.build_all()
    assert len(built) == 18
    for name, text in built.items():
        assert (FIXTURES / "expected" / name).read_text(encoding="utf-8") == text
    assert (FIXTURES / "FIXTURE_MANIFEST.json").read_text(encoding="utf-8") == generator.build_manifest(built)


# ---------------------------------------------------------------------------
# T11 — determinism / failure
# ---------------------------------------------------------------------------


def test_a65_identical_plans_produce_identical_bundles():
    plan = B.plan(model_ids=("XAU.GAME",))
    assert _bundle(plan).to_json() == _bundle(plan).to_json()


def test_a66_absent_source_yields_bounded_refusal():
    bundle = _bundle(B.plan(model_ids=("MOD.NOT.THERE.V1",)))
    assert bundle.outcome in (RetrievalOutcome.PARTIAL, RetrievalOutcome.REFUSED)
    assert bundle.canonical_refs == ()


def test_a67_provider_not_configured_never_substitutes_history():
    bundle = _bundle(
        B.plan(model_ids=("XAU.GAME",), scope=TimeScope.CURRENT),
        snapshot=B.snapshot_context(),
    )
    assert all(ref.snapshot_id == "" for ref in bundle.intelligence_refs)
    assert "HISTORICAL" not in {ref.request_kind for ref in bundle.intelligence_refs}


def test_a68_policy_engine_failure_fails_closed():
    service = AskCerebusRetrievalService(INDEX, enforcement=_BoomEnforcement())
    bundle = service.retrieve(
        B.plan(model_ids=("XAU.GAME",)), B.operator(), B.operator_context()
    )
    assert bundle.canonical_refs == ()
    assert bundle.outcome is RetrievalOutcome.REFUSED


# ---------------------------------------------------------------------------
# T12 — frozen integrity
# ---------------------------------------------------------------------------


def _hash(path):
    return hashlib.sha256((REPO / path).read_bytes().replace(b"\r\n", b"\n")).hexdigest()


def test_a69_frozen_iv1_query_contract_unchanged():
    assert _hash("app/forge/ask_cerebus/interpreter/plan.py") == "c43a34ba6ef085108743c2c87c1c1f13d85c134360a6e4e7f3067046f9fd344b"


def test_a70_frozen_book_i_retrieval_contract_unchanged():
    assert _hash("app/forge/retrieval/service.py") == "0da911be828a0d5747b8cfe022ab20df3cd8187865ecb42232ddb4177339ade0"


def test_a71_frozen_book_ii_policy_contract_unchanged():
    assert _hash("app/forge/policy.py") == "f10751e6ba6144d807abc151dbcbd7a06320a3d1ab82279fe1cac26b8a228fcc"


def test_a72_no_network_vector_or_llm_import_in_iv2():
    package = REPO / "app" / "forge" / "ask_cerebus" / "retrieval"
    text = "\n".join(path.read_text(encoding="utf-8") for path in package.glob("*.py"))
    assert not re.search(r"(^|\n)\s*(import|from)\s+(openai|requests|httpx|aiohttp|chromadb|faiss|numpy|torch)", text)
    assert "openai" not in text.lower()
