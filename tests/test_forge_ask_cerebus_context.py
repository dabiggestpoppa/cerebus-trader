"""Book IV / Bloc IV.3 acceptance drivers (C-01 through C-92)."""

from __future__ import annotations

import ast
import hashlib
import importlib.util
import json
import sys

from tests._support.canonical_bytes import canonical_bytes, canonical_sha256
from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace

from app.forge.ask_cerebus.context import (
    AuthorizedContextDetail,
    AuthorizedIntelligenceFact,
    ContextBudget,
    ContextIssueCode,
    ContextPackager,
    ContextRefusalCode,
    ContextSectionId,
    EpistemicLabel,
    SmallNFlag,
    TokenizerPort,
    TrustClass,
    Utf8QuarterTokenizer,
)
from app.forge.ask_cerebus.context.budgeting import (
    estimate_item,
    select_within_budget,
)
from app.forge.ask_cerebus.context.compression import facts as make_facts
from app.forge.ask_cerebus.context.compression import item as make_item
from app.forge.ask_cerebus.context.enums import SECTION_ORDER
from app.forge.ask_cerebus.context.labels import map_status
from app.forge.ask_cerebus.context.schema import canonical_json
from app.forge.ask_cerebus.context.trust import ALLOWED_FACT_KEYS, ALLOWED_EXPOSURES
from app.forge.ask_cerebus.context.versions import (
    CONTEXT_CONTRACT_V1,
    CONTEXT_MANIFEST_V1,
    ESTIMATOR_VERSION,
)
from app.forge.ask_cerebus.interpreter.enums import Intent
from app.forge.ask_cerebus.retrieval import (
    EvidenceJoinStatus,
    Refusal,
    RefusalCode,
    SemanticPassage,
)
from app.forge.ask_cerebus.retrieval.enums import LimitationCode
from app.forge.persistence.sql.migrations import discover_migrations

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "implementation/forge/book_iv/bloc_iv_3/fixtures"


def _load_builders():
    name = "iv3_test_builders"
    spec = importlib.util.spec_from_file_location(name, FIXTURES / "_builders.py")
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


B = _load_builders()


def _pack(name: str, *, detail=None, budget=None):
    _, p, b, d, default_budget = B.case(name)
    return ContextPackager().pack(
        p,
        b,
        detail=d if detail is None else detail,
        budget=default_budget if budget is None else budget,
    )


def _sections(package):
    return {section.section_id: section for section in package.sections}


def _section(package, section_id):
    return _sections(package).get(section_id)


def _items(package, section_id):
    section = _section(package, section_id)
    return section.items if section else ()


def _fact_map(item):
    return {fact.key: fact.value_text for fact in item.facts}


def _all_items(package):
    return tuple(item for section in package.sections for item in section.items)


def _codes(package):
    return {issue.code.value for issue in package.issues}


def _serialized(package):
    return package.to_json()


def _sha(path: Path) -> str:
    """Canonical content identity; see tests/_support/canonical_bytes.py."""
    return canonical_sha256(path)


def _simple_bundle():
    p = B.plan(model_ids=("XAU.GAME",))
    ref = B.canonical("MOD.XAU.GAME.V1", "MODEL", status="CANONICAL", support="CANONICAL")
    return p, B.bundle(p, canonical_refs=(ref,)), ref


# T1 — context sections -------------------------------------------------


def test_c01_packages_only_applicable_sections():
    package = _pack("Q3-01")
    assert [section.section_id for section in package.sections] == [
        ContextSectionId.QUERY_CONTRACT,
        ContextSectionId.CANONICAL_MODEL,
        ContextSectionId.LINEAGE_TERMS,
    ]
    assert all(section.items for section in package.sections)
    assert package.manifest.included_section_ids == (
        "QUERY_CONTRACT",
        "CANONICAL_MODEL",
        "LINEAGE_TERMS",
    )
    assert "CURRENT_INTELLIGENCE" in package.manifest.omitted_section_ids


def test_c02_preserves_query_contract_without_reinterpretation():
    package = _pack("Q3-01")
    facts = _fact_map(_items(package, ContextSectionId.QUERY_CONTRACT)[0])
    assert facts["intent"] == "DEFINITION"
    assert facts["time_scope"] == "GENERAL"
    assert facts["depth"] == "OPERATOR"
    assert facts["actionable"] == "False"
    assert package.query_plan_id.startswith("PLAN.")


def test_c03_packages_typed_current_intelligence_refs():
    package = _pack("Q3-03")
    item = _items(package, ContextSectionId.CURRENT_INTELLIGENCE)[0]
    facts = _fact_map(item)
    assert facts["snapshot_id"] == "SNAP.EUR.SYNTH.V1"
    assert facts["quality"] == "SYNTHETIC_FIXTURE"
    assert facts["state"] == "RANGE"
    assert facts["levels"] == "1.0800/1.0900"
    assert item.source_status == "SYNTHETIC_FIXTURE"


def test_c04_packages_canonical_model_without_body_text():
    package = _pack("Q3-01")
    item = next(
        item
        for item in _items(package, ContextSectionId.CANONICAL_MODEL)
        if _fact_map(item)["identity"] == "MOD.FIB.REKEY.V1"
    )
    assert item.text is None
    assert "BODY" not in _serialized(package)
    assert _fact_map(item)["version"] == "V1"


def test_c05_preserves_setup_identity_and_surface_verbatim():
    package = _pack("Q3-11")
    item = _items(package, ContextSectionId.SETUP)[0]
    facts = _fact_map(item)
    assert facts["setup_id"] == "SETUP.XAU.QUARTER_ZONE.V1"
    assert facts["setup_version"] == "V1"
    assert facts["surface"] == "OPERATOR"
    assert facts["eligibility"] == "WATCH"


def test_c06_pairs_claims_with_authorized_evidence():
    package = _pack("Q3-06")
    claim = _items(package, ContextSectionId.CLAIMS)[0]
    evidence = _items(package, ContextSectionId.EVIDENCE)[0]
    assert claim.evidence_refs == ("EV.XAU.GAME.001",)
    assert evidence.source_ref_id == "EV.XAU.GAME.001"
    assert _fact_map(claim)["join_status"] == "VERIFIED"


def test_c07_separates_lineage_and_terms():
    package = _pack("Q3-01")
    canonical_ids = {
        _fact_map(item)["identity"]
        for item in _items(package, ContextSectionId.CANONICAL_MODEL)
    }
    lineage_ids = {
        _fact_map(item)["identity"]
        for item in _items(package, ContextSectionId.LINEAGE_TERMS)
    }
    assert "TERM.REKEY" in lineage_ids
    assert "TERM.REKEY" not in canonical_ids
    assert "MOD.FIB.REKEY.V1" in canonical_ids


def test_c08_retains_limitations_and_negative_evidence():
    package = _pack("Q3-11")
    statuses = {
        item.source_status
        for item in _items(package, ContextSectionId.LIMITATIONS_NEGATIVE)
    }
    assert {"NO_GO_ACTIVE", "SETUP_NOT_ELIGIBLE"} <= statuses
    assert all(
        item.mandatory
        for item in _items(package, ContextSectionId.LIMITATIONS_NEGATIVE)
    )


def test_c09_general_knowledge_is_a_bounded_allowance_only():
    p = B.plan(intent=Intent.GENERAL_MARKET_KNOWLEDGE)
    package = ContextPackager().pack(p, B.bundle(p))
    general = _items(package, ContextSectionId.GENERAL_KNOWLEDGE)
    assert len(general) == 1
    assert set(_fact_map(general[0])) == {"general_knowledge_allowed"}
    assert _fact_map(general[0])["general_knowledge_allowed"] == "true"


def test_c10_prefers_canonical_refs_over_source_text():
    package = _pack("Q3-18")
    canonical = next(
        item for item in _items(package, ContextSectionId.CANONICAL_MODEL)
        if item.trust_class is TrustClass.TRUSTED_CONTROL
    )
    semantic = next(
        item for item in _items(package, ContextSectionId.CANONICAL_MODEL)
        if item.trust_class is TrustClass.UNTRUSTED_DATA
    )
    assert canonical.priority < semantic.priority
    assert "IGNORE" not in canonical_json(canonical.payload())
    assert "IGNORE" in semantic.text


def test_c11_includes_semantic_excerpt_only_when_authorized_and_bounded():
    package = _pack("Q3-18")
    semantic = next(
        item for item in _all_items(package)
        if item.trust_class is TrustClass.UNTRUSTED_DATA
    )
    assert semantic.source_ref_id == "MOD.XAU.GAME.V1"
    assert semantic.text is not None
    assert semantic.quote_scope == "BOUNDED"
    assert len(semantic.text) <= 1000


def test_c12_omits_raw_source_when_canonical_item_suffices():
    package = _pack("Q3-18")
    canonical = next(
        item for item in _all_items(package)
        if item.trust_class is TrustClass.TRUSTED_CONTROL
        and item.source_ref_id == "MOD.XAU.GAME.V1"
    )
    assert canonical.text is None
    assert "result_value" not in _fact_map(canonical)


def test_c13_preserves_quote_scope_and_exposure_on_excerpts():
    package = _pack("Q3-18")
    semantic = next(
        item for item in _all_items(package)
        if item.trust_class is TrustClass.UNTRUSTED_DATA
    )
    assert semantic.quote_scope == "BOUNDED"
    assert semantic.exposure == "OPERATOR_ONLY"


def test_c14_orders_items_deterministically():
    package = _pack("Q3-18")
    assert [section.section_id for section in package.sections] == [
        ContextSectionId.QUERY_CONTRACT,
        ContextSectionId.CANONICAL_MODEL,
    ]
    ids = [item.item_id for item in _items(package, ContextSectionId.CANONICAL_MODEL)]
    assert ids == sorted(ids)
    for section in package.sections:
        assert [item.priority for item in section.items] == sorted(
            item.priority for item in section.items
        )


def test_c15_deduplicates_identity_without_merging_facts():
    p, _, ref = _simple_bundle()
    package = ContextPackager().pack(
        p, B.bundle(p, canonical_refs=(ref, replace(ref, status="SUPERSEDED")))
    )
    models = [
        item for item in _items(package, ContextSectionId.CANONICAL_MODEL)
        if item.source_ref_id == ref.object_id
    ]
    assert len(models) == 1
    assert ContextIssueCode.DUPLICATE_SUPPRESSED.value in _codes(package)
    assert _fact_map(models[0])["status"] == "CANONICAL"


def test_c16_compression_preserves_source_and_provenance_refs():
    package = _pack("Q3-06")
    evidence = _items(package, ContextSectionId.EVIDENCE)[0]
    assert evidence.source_ref_id == "EV.XAU.GAME.001"
    assert evidence.provenance_refs == ("sha256:" + "a" * 64,)


# T2/T3 — budget and estimator -----------------------------------------


def test_c17_estimator_is_versioned_and_reproducible():
    first = _pack("Q3-06")
    second = _pack("Q3-06")
    assert first.token_accounting.estimator_version == ESTIMATOR_VERSION
    assert first.token_accounting.used_units == sum(
        section.estimated_units for section in first.sections
    )
    assert first.to_json() == second.to_json()


def test_c18_tokenizer_port_is_replaceable_without_accuracy_claim():
    item = _pack("Q3-06").sections[0].items[0]
    port = Utf8QuarterTokenizer()
    assert isinstance(port, TokenizerPort)
    assert port.version == ESTIMATOR_VERSION
    assert port.estimate_item(item) == estimate_item(item)
    assert "tokenizer" in Path(
        "app/forge/ask_cerebus/context/budgeting.py"
    ).read_text(encoding="utf-8").lower()


def test_c19_budget_input_is_explicit_and_defaulted():
    assert ContextBudget().max_units == 4096
    assert ContextBudget().reserve_units == 512
    assert ContextBudget(max_units=100, reserve_units=10).available_units == 90
    package = _pack("Q3-06")
    assert package.token_accounting.max_units == 4096
    assert package.token_accounting.reserve_units == 512


def test_c20_budget_priority_order_is_frozen():
    q = make_item(
        section="QUERY_CONTRACT",
        source_ref_id="PLAN",
        source_ref_type="QUERY_PLAN",
        source_status="PLAN",
        label=EpistemicLabel.CANONICAL,
        facts=make_facts(("identity", "PLAN", "")),
        priority=0,
        mandatory=True,
    )
    claim = make_item(
        section="CLAIMS",
        source_ref_id="CL",
        source_ref_type="CLAIM",
        source_status="VALIDATED",
        label=EpistemicLabel.VALIDATED,
        priority=2,
    )
    model = make_item(
        section="CANONICAL_MODEL",
        source_ref_id="MOD",
        source_ref_type="MODEL",
        source_status="CANONICAL",
        label=EpistemicLabel.CANONICAL,
        priority=3,
    )
    setup = make_item(
        section="SETUP",
        source_ref_id="SETUP",
        source_ref_type="SETUP",
        source_status="CANDIDATE",
        label=EpistemicLabel.CANDIDATE,
        priority=4,
    )
    semantic = make_item(
        section="CANONICAL_MODEL",
        source_ref_id="MOD",
        source_ref_type="SEMANTIC_SUPPORT",
        source_status="SUPPORT_ONLY",
        label=EpistemicLabel.INSUFFICIENT_EVIDENCE,
        priority=7,
        text="support",
    )
    grouped = {
        ContextSectionId.QUERY_CONTRACT: [q],
        ContextSectionId.CLAIMS: [claim],
        ContextSectionId.CANONICAL_MODEL: [model, semantic],
        ContextSectionId.SETUP: [setup],
    }
    available = estimate_item(q) + estimate_item(claim) + 1
    budget = ContextBudget(max_units=available + 1, reserve_units=1)
    kept, trimmed, _ = select_within_budget(grouped, budget)
    assert q in kept[ContextSectionId.QUERY_CONTRACT]
    assert claim in kept[ContextSectionId.CLAIMS]
    assert model not in kept[ContextSectionId.CANONICAL_MODEL]
    assert trimmed[0][1] is semantic


def test_c21_mandatory_safety_items_cannot_be_dropped():
    q = make_item(
        section="QUERY_CONTRACT",
        source_ref_id="PLAN",
        source_ref_type="QUERY_PLAN",
        source_status="PLAN",
        label=EpistemicLabel.CANONICAL,
        priority=0,
        mandatory=True,
    )
    no_go = make_item(
        section="LIMITATIONS_NEGATIVE",
        source_ref_id="",
        source_ref_type="LIMITATION",
        source_status="NO_GO_ACTIVE",
        label=EpistemicLabel.NEGATIVE_EVIDENCE,
        priority=0,
        mandatory=True,
    )
    optional = make_item(
        section="CANONICAL_MODEL",
        source_ref_id="MOD",
        source_ref_type="MODEL",
        source_status="CANONICAL",
        label=EpistemicLabel.CANONICAL,
        priority=3,
    )
    grouped = {
        ContextSectionId.QUERY_CONTRACT: [q],
        ContextSectionId.LIMITATIONS_NEGATIVE: [no_go],
        ContextSectionId.CANONICAL_MODEL: [optional],
    }
    available = estimate_item(q) + estimate_item(no_go) + 1
    kept, trimmed, _ = select_within_budget(
        grouped, ContextBudget(max_units=available + 1, reserve_units=1)
    )
    assert no_go in kept[ContextSectionId.LIMITATIONS_NEGATIVE]
    assert q in kept[ContextSectionId.QUERY_CONTRACT]
    assert optional not in kept[ContextSectionId.CANONICAL_MODEL]


def test_c22_trimming_is_deterministic_and_stable():
    p = B.plan(model_ids=("XAU.GAME",), intent=Intent.MODEL_DESCRIPTION)
    b = B.bundle(
        p,
        canonical_refs=(B.canonical("MOD.XAU.GAME.V1", "MODEL", status="CANONICAL", support="CANONICAL"),),
        semantic=tuple(
            SemanticPassage(
                "MOD.XAU.GAME.V1", f"support text {index}", "SUPPORT_ONLY", "BOUNDED", "SEMANTIC_SUPPORT", 0.1
            )
            for index in range(12)
        ),
    )
    budget = ContextBudget(max_units=240, reserve_units=1)
    one = ContextPackager().pack(p, b, budget=budget)
    two = ContextPackager().pack(p, b, budget=budget)
    assert one.to_json() == two.to_json()
    assert [o.payload() for o in one.omissions] == [o.payload() for o in two.omissions]


def test_c23_omission_ledger_accounts_for_truncation():
    p = B.plan(model_ids=("XAU.GAME",), intent=Intent.MODEL_DESCRIPTION)
    b = B.bundle(
        p,
        canonical_refs=(B.canonical("MOD.XAU.GAME.V1", "MODEL", status="CANONICAL", support="CANONICAL"),),
        semantic=tuple(
            SemanticPassage(
                "MOD.XAU.GAME.V1", f"bounded support {index}", "SUPPORT_ONLY", "BOUNDED", "SEMANTIC_SUPPORT", 0.1
            )
            for index in range(20)
        ),
    )
    clean = B.bundle(
        p,
        canonical_refs=(B.canonical("MOD.XAU.GAME.V1", "MODEL", status="CANONICAL", support="CANONICAL"),),
    )
    baseline = ContextPackager().pack(p, clean)
    package = ContextPackager().pack(
        p,
        b,
        budget=ContextBudget(
            max_units=baseline.token_accounting.used_units + 1,
            reserve_units=1,
        ),
    )
    assert any(
        omission.reason is ContextIssueCode.CONTEXT_BUDGET_TRIMMED
        for omission in package.omissions
    )


def test_c24_mandatory_overflow_refuses_context():
    package = _pack("Q3-20")
    assert package.outcome.value == "REFUSED"
    assert package.refusals[0].code is ContextRefusalCode.CONTEXT_BUDGET_EXCEEDED
    assert package.sections == ()


# T4 — epistemic labels --------------------------------------------------


def test_c25_uses_closed_epistemic_label_set():
    allowed = {label.value for label in EpistemicLabel}
    for name in ("Q3-01", "Q3-06", "Q3-11", "Q3-18"):
        for item in _all_items(_pack(name)):
            assert item.epistemic_label.value in allowed


def test_c26_preserves_source_status_separately():
    package = _pack("Q3-06")
    claim = _items(package, ContextSectionId.CLAIMS)[0]
    assert claim.source_status == "CANDIDATE"
    assert claim.epistemic_label is EpistemicLabel.CANDIDATE


def test_c27_maps_status_to_epistemic_label_without_promotion():
    assert map_status("VALIDATED") is EpistemicLabel.VALIDATED
    assert map_status("CANDIDATE") is EpistemicLabel.CANDIDATE
    assert map_status("FALSIFIED") is EpistemicLabel.NEGATIVE_EVIDENCE
    assert map_status("OBSERVED") is EpistemicLabel.INSUFFICIENT_EVIDENCE


def test_c28_canonical_identity_is_not_validation():
    package = _pack("Q3-01")
    item = next(
        item
        for item in _items(package, ContextSectionId.CANONICAL_MODEL)
        if item.source_ref_id == "MOD.FIB.REKEY.V1"
    )
    assert item.epistemic_label is EpistemicLabel.CANONICAL
    assert "result_value" not in _fact_map(item)


def test_c29_no_label_is_promoted_by_packaging():
    package = _pack("Q3-06")
    claim = _items(package, ContextSectionId.CLAIMS)[0]
    assert claim.source_status == "CANDIDATE"
    assert claim.epistemic_label is not EpistemicLabel.VALIDATED


def test_c30_negative_statuses_remain_negative():
    package = _pack("Q3-17")
    negative = next(
        item for item in _all_items(package)
        if item.source_status == "FALSIFIED"
    )
    assert negative.epistemic_label is EpistemicLabel.NEGATIVE_EVIDENCE


def test_c31_inference_label_is_not_emitted():
    for name in ("Q3-01", "Q3-06", "Q3-15", "Q3-18"):
        assert "INFERENCE" not in _serialized(_pack(name))


def test_c32_general_knowledge_cannot_carry_cerebus_fact():
    p = B.plan(intent=Intent.GENERAL_MARKET_KNOWLEDGE)
    package = ContextPackager().pack(p, B.bundle(p))
    assert all(
        set(_fact_map(item)) == {"general_knowledge_allowed"}
        for item in _items(package, ContextSectionId.GENERAL_KNOWLEDGE)
    )


def test_c33_unmapped_status_fails_closed_without_number():
    p = B.plan(model_ids=("XAU.GAME",), intent=Intent.STATISTIC_EVIDENCE)
    ev = B.evidence("EV.UNMAPPED", claim_ids=("CL.UNMAPPED",))
    cl = B.claim(
        "CL.UNMAPPED",
        status="OBSERVED",
        evidence_ids=("EV.UNMAPPED",),
        join=EvidenceJoinStatus.VERIFIED,
        result="99%",
    )
    package = ContextPackager().pack(
        p, B.bundle(p, claim_refs=(cl,), evidence_refs=(ev,))
    )
    claim = _items(package, ContextSectionId.CLAIMS)[0]
    assert claim.epistemic_label is EpistemicLabel.INSUFFICIENT_EVIDENCE
    assert "result_value" not in _fact_map(claim)


# T5 — layers ------------------------------------------------------------


def test_c34_preserves_source_layer_exactly():
    claim = _items(_pack("Q3-06"), ContextSectionId.CLAIMS)[0]
    setup = _items(_pack("Q3-11"), ContextSectionId.SETUP)[0]
    assert claim.layer == "L3"
    assert setup.layer == "L1"


def test_c35_l3_statistic_cannot_fill_l1_setup_field():
    package = _pack("Q3-10")
    setup = _items(package, ContextSectionId.SETUP)[0]
    assert "result_value" not in _fact_map(setup)
    assert all(item.layer != "L3" for item in _items(package, ContextSectionId.SETUP))


def test_c36_l2_path_fact_is_not_entry_authority():
    setup = _items(_pack("Q3-11"), ContextSectionId.SETUP)[0]
    payload = canonical_json(setup.payload()).lower()
    assert "entry" not in payload
    assert "authority" not in payload


def test_c37_historical_fact_is_not_packaged_as_current():
    package = _pack("Q3-15")
    assert _section(package, ContextSectionId.CURRENT_INTELLIGENCE) is None
    claim = _items(package, ContextSectionId.CLAIMS)[0]
    assert claim.layer == "L2"
    assert claim.generation == "P90.ORIGINAL"


def test_c38_jpy_manual_state_is_not_execution_permission():
    package = _pack("Q3-13")
    setup = _items(package, ContextSectionId.SETUP)[0]
    facts = _fact_map(setup)
    assert facts["setup_class"] == "MANUAL_OPERATOR"
    serialized = _serialized(package).lower()
    assert "execution_permission" not in serialized
    assert "order_intent" not in serialized


def test_c39_fib_research_state_is_not_production_setup():
    package = _pack("Q3-12")
    setup = _items(package, ContextSectionId.SETUP)[0]
    assert _fact_map(setup)["setup_class"] == "RESEARCH_ONLY"
    assert _fact_map(setup).get("surface", "") != "PRODUCTION"
    assert "RESEARCH_ONLY_NOT_PRODUCTION" in _serialized(package)


def test_c40_cross_layer_facts_are_not_conflated():
    package = _pack("Q3-06")
    assert "confluence" not in _serialized(package).lower()
    claim = _items(package, ContextSectionId.CLAIMS)[0]
    assert claim.layer == "L3"


# T6/T7 — evidence and missing evidence --------------------------------


def test_c41_preserves_governed_metric_population_sample_and_period():
    package = _pack("Q3-06")
    facts = _fact_map(_items(package, ContextSectionId.EVIDENCE)[0])
    assert facts["metric"] == "completion_rate"
    assert facts["conditioning_population"].startswith("XAUUSD")
    assert facts["sample_size"] == "20"
    assert facts["research_period"] == "2018-01-01/2024-12-31"


def test_c42_never_invents_sample_size():
    package = _pack("Q3-09")
    evidence = _items(package, ContextSectionId.EVIDENCE)[0]
    assert "sample_size" not in _fact_map(evidence)
    assert "sample_size" not in _serialized(package).replace("N_NOT_PROVIDED", "")


def test_c43_never_invents_small_n_threshold():
    package = _pack("Q3-09")
    assert "small_n_threshold_ref" not in _serialized(package)
    assert "SMALLN.POLICY.V1" not in _serialized(package)


def test_c44_marks_small_n_unresolved_when_threshold_absent():
    package = _pack("Q3-09")
    assert ContextIssueCode.SMALL_N_UNRESOLVED.value in _codes(package)


def test_c45_preserves_evidence_status_and_provenance():
    package = _pack("Q3-06")
    evidence = _items(package, ContextSectionId.EVIDENCE)[0]
    assert evidence.source_status == "VALIDATED"
    assert evidence.provenance_refs == ("sha256:" + "a" * 64,)


def test_c46_preserves_oos_and_reproduction_state():
    package = _pack("Q3-06")
    facts = _fact_map(_items(package, ContextSectionId.EVIDENCE)[0])
    assert facts["oos_status"] == "FORWARD_OOS"


def test_c47_preserves_model_generation_on_claims():
    package = _pack("Q3-06")
    facts = _fact_map(_items(package, ContextSectionId.CLAIMS)[0])
    assert facts["version"] == "V1"
    assert facts["generation"] == "XAU.GAME"


def test_c48_retains_both_sides_of_conflicting_evidence():
    package = _pack("Q3-16")
    ids = {
        _fact_map(item)["identity"]
        for item in _items(package, ContextSectionId.CLAIMS)
    }
    assert {"CL.CONFLICT.A", "CL.CONFLICT.B"} <= ids
    assert "EVIDENCE_CONFLICT" in _serialized(package)


def test_c49_unsupported_claim_cannot_emit_number():
    package = _pack("Q3-05")
    claim = _items(package, ContextSectionId.CLAIMS)[0]
    assert "result_value" not in _fact_map(claim)
    assert "132%" not in _serialized(package)


def test_c50_missing_evidence_emits_explicit_instruction():
    package = _pack("Q3-05")
    missing = [
        item for item in _all_items(package)
        if item.source_ref_type == "MISSING_EVIDENCE"
    ]
    assert missing
    assert missing[0].mandatory
    assert _fact_map(missing[0])["status"] == "MISSING_EVIDENCE"


def test_c51_missing_evidence_retains_known_model_context():
    package = _pack("Q3-07")
    assert _items(package, ContextSectionId.CANONICAL_MODEL)
    assert _items(package, ContextSectionId.CLAIMS)


def test_c52_missing_evidence_never_uses_model_intuition():
    package = _pack("Q3-07")
    assert "result_value" not in _serialized(package)


def test_c53_missing_evidence_cannot_be_replaced_by_semantic_text():
    package = _pack("Q3-18")
    assert "result_value" not in _serialized(package)
    assert "132%" not in _serialized(package)


def test_c54_missing_evidence_cannot_be_replaced_by_history():
    package = _pack("Q3-15")
    assert _section(package, ContextSectionId.CURRENT_INTELLIGENCE) is None
    assert "FORWARD_OOS" not in _serialized(package)


def test_c55_missing_evidence_package_is_partial_not_verified():
    package = _pack("Q3-05")
    assert package.outcome.value == "PARTIAL"
    assert "VALIDATED" not in _serialized(package)


# T8 — injection ---------------------------------------------------------


def test_c56_retrieved_text_is_typed_as_untrusted_data():
    package = _pack("Q3-18")
    semantic = next(
        item for item in _all_items(package)
        if item.trust_class is TrustClass.UNTRUSTED_DATA
    )
    assert semantic.text is not None
    assert semantic.source_ref_id == "MOD.XAU.GAME.V1"


def test_c57_control_and_data_blocks_are_separated():
    package = _pack("Q3-18")
    for item in _all_items(package):
        if item.trust_class is TrustClass.TRUSTED_CONTROL:
            assert item.text is None
        else:
            assert item.text is not None


def test_c58_source_text_cannot_override_instructions():
    package = _pack("Q3-18")
    clean_plan = B.plan(model_ids=("XAU.GAME",), intent=Intent.MODEL_DESCRIPTION)
    clean = B.bundle(clean_plan, canonical_refs=(B.canonical("MOD.XAU.GAME.V1", "MODEL", status="CANONICAL", support="CANONICAL"),))
    clean_package = ContextPackager().pack(clean_plan, clean)
    assert _fact_map(_items(package, ContextSectionId.QUERY_CONTRACT)[0]) == _fact_map(
        _items(clean_package, ContextSectionId.QUERY_CONTRACT)[0]
    )


def test_c59_source_text_cannot_grant_entitlement():
    package = _pack("Q3-18")
    control = [
        item for item in _all_items(package)
        if item.trust_class is TrustClass.TRUSTED_CONTROL
    ]
    assert all("entitlement" not in canonical_json(item.payload()).lower() for item in control)
    assert "ENTITLEMENT_GRANT" not in _serialized(package)


def test_c60_source_text_cannot_change_status_or_layer():
    package = _pack("Q3-18")
    semantic = next(
        item for item in _all_items(package)
        if item.trust_class is TrustClass.UNTRUSTED_DATA
    )
    assert semantic.epistemic_label is EpistemicLabel.INSUFFICIENT_EVIDENCE
    assert semantic.layer == ""
    control = [
        item for item in _all_items(package)
        if item.trust_class is TrustClass.TRUSTED_CONTROL
    ]
    assert all("VALIDATED" not in canonical_json(item.payload()) for item in control)


def test_c61_source_text_cannot_insert_identity_or_statistic():
    package = _pack("Q3-18")
    assert "result_value" not in _serialized(package)
    assert "INSERTED" not in _serialized(package)


def test_c62_source_text_cannot_promote_setup_or_clear_no_go():
    package = _pack("Q3-18")
    assert _section(package, ContextSectionId.SETUP) is None
    assert "NO_GO_ACTIVE" not in _serialized(package)
    assert "ELIGIBLE" not in _serialized(package)


def test_c63_injection_payload_is_data_hashed_not_executed():
    package = _pack("Q3-18")
    semantic = next(
        item for item in _all_items(package)
        if item.trust_class is TrustClass.UNTRUSTED_DATA
    )
    payload = semantic.payload()
    assert payload["text_sha256"] == hashlib.sha256(
        semantic.text.encode("utf-8")
    ).hexdigest()
    assert "IGNORE ALL PRIOR INSTRUCTIONS" in semantic.text


# T9 — exposure ----------------------------------------------------------


def test_c64_internal_method_and_code_never_enter_package():
    package = _pack("Q3-19")
    assert package.refusals[0].code is ContextRefusalCode.CONTEXT_EXPOSURE_VIOLATION
    assert package.sections == ()
    assert "INTERNAL_METHOD" not in _serialized(package)


def test_c65_denied_identifiers_never_enter_package_or_manifest():
    package = _pack("Q3-19")
    assert "SECRET" not in _serialized(package)
    assert package.manifest.included_object_ids == ()
    assert set(package.manifest.omitted_section_ids) <= {
        section.value for section in SECTION_ORDER
    }


def test_c66_exposure_is_never_widened():
    package = _pack("Q3-03")
    model = next(
        item for item in _all_items(package)
        if item.source_ref_id == "MOD.EUR.GAME.V1"
    )
    assert model.exposure == "OPERATOR_ONLY"
    assert model.exposure in ALLOWED_EXPOSURES


def test_c67_item_fields_obey_allowlist():
    for name in ("Q3-01", "Q3-06", "Q3-11", "Q3-18"):
        for item in _all_items(_pack(name)):
            assert {fact.key for fact in item.facts} <= ALLOWED_FACT_KEYS


def test_c68_excerpt_length_is_bounded():
    p = B.plan(model_ids=("XAU.GAME",))
    b = B.bundle(
        p,
        canonical_refs=(B.canonical("MOD.XAU.GAME.V1", "MODEL", status="CANONICAL", support="CANONICAL"),),
        semantic=(
            SemanticPassage(
                "MOD.XAU.GAME.V1", "x" * 2000, "SUPPORT_ONLY", "BOUNDED", "SEMANTIC_SUPPORT"
            ),
        ),
    )
    package = ContextPackager().pack(p, b)
    semantic = next(
        item for item in _all_items(package)
        if item.trust_class is TrustClass.UNTRUSTED_DATA
    )
    assert len(semantic.text) == 1000


def test_c69_secrets_and_unrestricted_bodies_are_excluded():
    p = B.plan(model_ids=("XAU.GAME",))
    b = B.bundle(
        p,
        canonical_refs=(B.canonical("MOD.XAU.GAME.V1", "MODEL", status="CANONICAL", support="CANONICAL"),),
        semantic=(
            SemanticPassage(
                "MOD.XAU.GAME.V1",
                "API_KEY=super-secret password=value",
                "SUPPORT_ONLY",
                "BOUNDED",
                "SEMANTIC_SUPPORT",
            ),
        ),
    )
    package = ContextPackager().pack(p, b)
    assert "super-secret" not in _serialized(package)
    assert "password=value" not in _serialized(package)


def test_c70_consumer_manifest_contains_no_forbidden_names():
    package = _pack("Q3-19")
    manifest = canonical_json(package.manifest.payload())
    assert "SECRET" not in manifest
    assert "INTERNAL" not in manifest


def test_c71_omission_metadata_is_bounded_and_safe():
    package = _pack("Q3-18")
    allowed = {item.source_ref_id for item in _all_items(package)}
    for omission in package.omissions:
        assert omission.reason in ContextIssueCode
        assert omission.source_ref_id == "" or omission.source_ref_id in allowed


# T10 — manifest ---------------------------------------------------------


def test_c72_manifest_binds_query_plan_and_bundle():
    package = _pack("Q3-06")
    assert package.manifest.query_plan_id == package.query_plan_id
    assert package.manifest.retrieval_bundle_id == package.retrieval_bundle_id
    assert package.query_plan_id.startswith("PLAN.")
    assert package.retrieval_bundle_id.startswith("BUNDLE.")


def test_c73_manifest_binds_context_contract_version():
    package = _pack("Q3-06")
    assert package.manifest.context_contract_version == CONTEXT_CONTRACT_V1
    assert package.manifest.manifest_version == CONTEXT_MANIFEST_V1
    assert package.manifest.estimator_version == ESTIMATOR_VERSION


def test_c74_manifest_lists_included_sections_and_object_ids():
    package = _pack("Q3-06")
    assert "CLAIMS" in package.manifest.included_section_ids
    assert "EVIDENCE" in package.manifest.included_section_ids
    assert "CL.XAU.GAME.001" in package.manifest.included_object_ids
    assert "EV.XAU.GAME.001" in package.manifest.included_object_ids


def test_c75_manifest_lists_omitted_sections():
    package = _pack("Q3-06")
    assert "CURRENT_INTELLIGENCE" in package.manifest.omitted_section_ids
    assert "SETUP" in package.manifest.omitted_section_ids
    assert "GENERAL_KNOWLEDGE" in package.manifest.omitted_section_ids


def test_c76_package_hash_is_deterministic():
    one = _pack("Q3-06")
    two = _pack("Q3-06")
    assert one.package_id.startswith("PKG.")
    assert one.package_id == two.package_id


def test_c77_manifest_digest_is_deterministic():
    one = _pack("Q3-06")
    two = _pack("Q3-06")
    assert one.manifest.manifest_digest.startswith("MFD.")
    assert one.manifest.manifest_digest == two.manifest.manifest_digest


def test_c78_serialization_is_canonical():
    package = _pack("Q3-06")
    assert json.loads(package.to_json()) == package.payload()
    assert package.to_json() == canonical_json(package.payload())


def test_c79_no_wall_clock_or_random_input_enters_hash():
    package = _pack("Q3-06")
    serialized = _serialized(package)
    for forbidden in ("timestamp", "created_at", "random", "pid", "file_path"):
        assert forbidden not in serialized
    assert package.package_id == _pack("Q3-06").package_id


# T11 — failures ---------------------------------------------------------


def test_c80_unsupported_input_contract_is_refused():
    p = B.plan(model_ids=("XAU.GAME",))
    b = B.bundle(p)
    fake = SimpleNamespace(query_contract_version="ASK_QUERY_CONTRACT.V0", plan_id="PLAN.fake")
    package = ContextPackager().pack(fake, b)
    assert package.refusals[0].code is ContextRefusalCode.CONTEXT_CONTRACT_UNSUPPORTED


def test_c81_malformed_bundle_is_refused():
    p, b, _ = _simple_bundle()
    mismatched = replace(b, query_plan_id="PLAN.other")
    package = ContextPackager().pack(p, mismatched)
    assert package.refusals[0].code is ContextRefusalCode.CONTEXT_INPUT_MALFORMED


def test_c82_budget_overflow_is_a_bounded_refusal():
    package = _pack("Q3-20")
    assert package.refusals[0].code is ContextRefusalCode.CONTEXT_BUDGET_EXCEEDED
    assert package.sections == ()
    assert "NO_GO" not in _serialized(package)


def test_c83_exposure_violation_fails_closed():
    package = _pack("Q3-19")
    assert package.outcome.value == "REFUSED"
    assert package.sections == ()


def test_c84_upstream_refusal_is_propagated_safely():
    p = B.plan(model_ids=("XAU.GAME",), intent=Intent.CURRENT_STATE, scope=B.TimeScope.CURRENT)
    b = B.bundle(p, refusals=(Refusal(RefusalCode.PROVIDER_NOT_CONFIGURED),))
    package = ContextPackager().pack(p, b)
    assert package.outcome.value == "REFUSED"
    assert ContextIssueCode.UPSTREAM_REFUSAL.value in _codes(package)
    assert _section(package, ContextSectionId.CURRENT_INTELLIGENCE) is None


def test_c85_partial_bundle_preserves_all_limitations():
    package = _pack("Q3-11")
    statuses = {
        item.source_status
        for item in _items(package, ContextSectionId.LIMITATIONS_NEGATIVE)
    }
    assert {"NO_GO_ACTIVE", "SETUP_NOT_ELIGIBLE"} <= statuses


def test_c86_same_inputs_retry_to_same_package():
    first = _pack("Q3-18")
    second = _pack("Q3-18")
    assert first.package_id == second.package_id
    assert first.to_json() == second.to_json()


# T12 — frozen integrity -------------------------------------------------


def test_c87_frozen_iv1_plan_contract_unchanged():
    assert _sha(ROOT / "app/forge/ask_cerebus/interpreter/plan.py") == (
        "c43a34ba6ef085108743c2c87c1c1f13d85c134360a6e4e7f3067046f9fd344b"
    )


def test_c88_frozen_iv2_bundle_refs_trace_unchanged():
    expected = {
        "bundle.py": "b38b356e01b349fe0110ce7ebd518fd1b3e9d1c82a7f8b979ac088019acc3455",
        "refs.py": "bbe1b937d6aa0bd7d0c26c8e0f7f5ba7dfa2ecee7f816dc9461b620d0961daa2",
        "trace.py": "6f8f08009da67975017de9c86263a52d0a72753afacf58f74aff7a91ec92e44d",
        "service.py": "2d73737e1a20f61e3ff276f16dee31e8e880304a6473754224d8a5ceb67b3535",
    }
    for name, digest in expected.items():
        assert _sha(ROOT / "app/forge/ask_cerebus/retrieval" / name) == digest


def test_c89_frozen_book_i_ii_iii_contracts_unchanged():
    expected = {
        "app/forge/policy.py": "f10751e6ba6144d807abc151dbcbd7a06320a3d1ab82279fe1cac26b8a228fcc",
        "app/forge/service/policy_enforcement.py": "9ccc3b72f77fca0cb3fd0685128fd96a2f0ce8ca975b532d96646d285476e381",
        "app/forge/intelligence_api/contracts.py": "7d8f90adf8aeca993b94d473f61fe16ea13170a1cd977cb47fb186d64697d4f0",
    }
    for name, digest in expected.items():
        assert _sha(ROOT / name) == digest


def test_c90_no_llm_network_vector_or_tokenizer_import():
    forbidden = {
        "openai",
        "anthropic",
        "requests",
        "httpx",
        "socket",
        "faiss",
        "chromadb",
        "tiktoken",
        "transformers",
    }
    for path in (ROOT / "app/forge/ask_cerebus/context").glob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        imports = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imports.update(alias.name.split(".")[0] for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imports.add(node.module.split(".")[0])
        assert not (imports & forbidden), path


def test_c91_routes_migrations_and_provider_seam_unchanged():
    assert _sha(ROOT / "app/forge/service/routes.py") == (
        "145757e0f2b19e76e2274018075c4b0fa7f0642498d4580e7e5fa8ec33d190af"
    )
    assert [migration.version for migration in discover_migrations()] == [1, 2, 3, 4]


def test_c92_no_new_canonical_status_entitlement_or_market_fact():
    package = _pack("Q3-03")
    payload = package.payload()
    for key in ("answer", "recommendation", "order_intent", "position_size", "win_rate"):
        assert key not in payload
    assert "CANONICAL_STATUS" not in _serialized(package)
    assert "ENTITLEMENT_GRANT" not in _serialized(package)
    assert "CURRENT_PRICE" not in _serialized(package)


def test_fixture_manifest_reproduces_all_twenty():
    manifest = json.loads((FIXTURES / "FIXTURE_MANIFEST.json").read_text(encoding="utf-8"))
    files = B.build_all()
    assert manifest["fixture_count"] == 20
    assert set(manifest["fixtures"]) == {f"Q3-{index:02d}.json" for index in range(1, 21)}
    for name, text in files.items():
        expected = manifest["fixtures"][name]
        assert hashlib.sha256(text.encode("utf-8")).hexdigest() == expected["sha256"]
        assert len(text.encode("utf-8")) == expected["bytes"]
        assert (FIXTURES / "expected" / name).read_text(encoding="utf-8") == text
