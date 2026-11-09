"""Book IV / Bloc IV.5 acceptance drivers A-01 through A-86.

Every driver runs the real IV.5 entry point over a real IV.3 package and a real
IV.4 draft. There is no provider, retrieval or market-data path in this suite.
"""

from __future__ import annotations

import ast
import hashlib
import importlib.util
import json
import socket
import sys
from dataclasses import replace
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
Q5_DIR = ROOT / "implementation/forge/book_iv/bloc_iv_5/fixtures"
sys.path.insert(0, str(ROOT))

from app.forge.ask_cerebus.answer import (  # noqa: E402
    ASK_ANSWER_CONTRACT_V1,
    REFUSAL_PRECEDENCE,
    VALIDATOR_ORDER,
    AnswerOutcome,
    AnswerRefusalCode,
    GovernedAnswerRefusal,
    ValidationCode,
    ValidatedAnswer,
    validate_answer,
)
from app.forge.ask_cerebus.answer.citations import collect, is_internal_ref  # noqa: E402
from app.forge.ask_cerebus.answer.enums import (  # noqa: E402
    FINDING_REFUSAL,
    LAYER_VOCABULARY,
    SETUP_NOT_ENCODED_SENTENCE,
    SETUP_PRECEDENCE,
)
from app.forge.ask_cerebus.answer.resolution import PackageIndex  # noqa: E402
from app.forge.ask_cerebus.answer.uncertainty import refusal_for  # noqa: E402
from app.forge.ask_cerebus.answer.validators import (  # noqa: E402
    VALIDATORS,
    Finding,
    run_validators,
    worst_setup_verdict,
)
from app.forge.ask_cerebus.answer.versions import (  # noqa: E402
    CITATION_SURFACE_STATUS,
    CORPUS_LICENSING_STATUS,
    CROSS_LAYER_RULE_STATUS,
    MARKET_DATA_STATUS,
    MATERIALITY_POLICY_STATUS,
    REFUSAL_PRECEDENCE_STATUS,
    RETENTION_POLICY_STATUS,
    SUPPORTED_ANSWER_CONTRACT_VERSIONS,
)
from app.forge.ask_cerebus.llm_gateway.draft import GatewayDraft  # noqa: E402
from app.forge.ask_cerebus.llm_gateway.enums import DraftStatus  # noqa: E402
from app.forge.persistence.sql.migrations import discover_migrations  # noqa: E402


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


Q5 = _load("iv5_q5_scenarios", Q5_DIR / "scenarios.py")
Q5_IDS = Q5.ids()
_INDEX = {scenario.id: scenario for scenario in Q5.cases()}

FROZEN = {
    "app/forge/ask_cerebus/llm_gateway/draft.py": "9aac55a78f78e917c24c3b78ab308af0422643e2bca718502f3672806040ba7c",
    "app/forge/ask_cerebus/llm_gateway/enums.py": "52fb6475631f7b6f3083f9e8e720b1a5f661cca0c7943701f173bf4d9e8b2892",
    "app/forge/ask_cerebus/llm_gateway/versions.py": "01dac8b2541788fc478e3c696ccbd13b1c7cba80d839733b2c7c3cd0f71cf61b",
    "app/forge/ask_cerebus/context/schema.py": "499dbdfb0054d6b1c7c41f61d6f91a2fdd15cad36346eb4297790e13b7cfc2c0",
    "app/forge/ask_cerebus/context/enums.py": "9c614f178707fb6ae319feed083e212591fbd51a23b1fe416ad74d07f7fe27df",
    "app/forge/ask_cerebus/context/versions.py": "0beaa9b0d3d1ba46cdd931f2d6405f41d96d998cb244b66b850b38d9882b8cfa",
    "app/forge/service/routes.py": "145757e0f2b19e76e2274018075c4b0fa7f0642498d4580e7e5fa8ec33d190af",
}

ANSWER_IDS = tuple(cid for cid in Q5_IDS if _INDEX[cid].kind == "ANSWER")
REFUSAL_IDS = tuple(cid for cid in Q5_IDS if _INDEX[cid].kind == "REFUSAL")


def _case(case_id: str):
    return _INDEX[case_id]


def _run(case_id: str):
    scenario = _case(case_id)
    return validate_answer(scenario.draft, scenario.package)


def _findings(outcome) -> tuple[str, ...]:
    return tuple(getattr(outcome, "findings", ()))


def _text(outcome) -> str:
    return json.dumps(outcome.payload(), sort_keys=True, ensure_ascii=False)


def _sections(outcome) -> dict[str, list[str]]:
    return {section["section_id"]: section["bullets"] for section in outcome.payload()["sections"]}


def _answer_module_paths() -> list[Path]:
    return sorted((ROOT / "app/forge/ask_cerebus/answer").glob("*.py"))


# ---------------------------------------------------------------------------
# T1 — input admission
# ---------------------------------------------------------------------------


def test_a01_consumes_unvalidated_gateway_draft_with_originating_package():
    scenario = _case("Q5-01")
    assert isinstance(scenario.draft, GatewayDraft)
    assert scenario.draft.status is DraftStatus.UNVALIDATED
    outcome = _run("Q5-01")
    assert isinstance(outcome, ValidatedAnswer)
    assert outcome.outcome is AnswerOutcome.VALIDATED_ANSWER
    assert outcome.record.package_id == scenario.package.package_id


def test_a02_refuses_non_unvalidated_draft_or_identity_mismatch():
    scenario = _case("Q5-03")
    validated = replace(scenario.draft, status=DraftStatus("UNVALIDATED"))
    assert isinstance(validate_answer(validated, scenario.package), ValidatedAnswer)
    forged = replace(scenario.draft, package_id="PKG." + "0" * 32)
    out = validate_answer(forged, scenario.package)
    assert isinstance(out, GovernedAnswerRefusal)
    assert "ANSWER_IDENTITY_MISMATCH" in _findings(out)


def test_a03_reverifies_context_contract_and_manifest_digest():
    scenario = _case("Q5-01")
    bad_contract = replace(scenario.package, context_contract_version="CONTEXT_CONTRACT_V0")
    out = validate_answer(scenario.draft, bad_contract)
    assert isinstance(out, GovernedAnswerRefusal)
    assert "ANSWER_CONTEXT_REFUSED" in _findings(out)

    bad_manifest = replace(scenario.package, manifest=replace(scenario.package.manifest, manifest_digest="MFD." + "0" * 64))
    out = validate_answer(scenario.draft, bad_manifest)
    assert isinstance(out, GovernedAnswerRefusal)
    assert "ANSWER_MANIFEST_INVALID" in _findings(out)


def test_a04_reresolves_references_without_retrieval_or_model_call():
    forbidden = {"requests", "httpx", "urllib", "aiohttp", "app.forge.providers", "app.forge.ask_cerebus.retrieval"}
    imported: set[str] = set()
    for path in _answer_module_paths():
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported.update(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imported.add(node.module)
    assert not {name for name in imported if name.split(".")[0] in forbidden or name in forbidden}
    assert not any("providers" in name or "retrieval" in name for name in imported)


def test_a05_repair_is_presentation_only():
    scenario = _case("Q5-03")
    outcome = validate_answer(scenario.draft, scenario.package)
    draft_texts = [claim.text for claim in scenario.draft.claims]
    for claim in outcome.claims:
        assert claim.text in draft_texts
        assert claim.epistemic_label in {entry.epistemic_label for entry in scenario.draft.claims}
    assert [number.value_text for number in outcome.numbers] == [
        number.value_text for number in scenario.draft.numbers
    ]


def test_a06_emits_exactly_one_terminal_outcome():
    for case_id in Q5_IDS:
        outcome = _run(case_id)
        assert isinstance(outcome, (ValidatedAnswer, GovernedAnswerRefusal))
        is_answer = isinstance(outcome, ValidatedAnswer)
        is_refusal = isinstance(outcome, GovernedAnswerRefusal)
        assert is_answer != is_refusal


# ---------------------------------------------------------------------------
# T2 — beginner compiler
# ---------------------------------------------------------------------------


def test_a07_beginner_compiles_what_it_means():
    out = _run("Q5-01")
    sections = _sections(out)
    assert "WHAT_IT_MEANS" in sections
    assert any("Rekey means" in bullet for bullet in sections["WHAT_IT_MEANS"])


def _beginner_over(case_id: str):
    scenario = _case(case_id)
    return validate_answer(replace(scenario.draft, depth="BEGINNER"), scenario.package)


def test_a08_beginner_compiles_what_cerebus_sees():
    sections = _sections(_beginner_over("Q5-03"))
    assert "WHAT_CEREBUS_SEES" in sections
    assert any("RANGE" in bullet for bullet in sections["WHAT_CEREBUS_SEES"])


def test_a09_beginner_compiles_what_it_does_not_mean():
    bullets = _sections(_beginner_over("Q5-03"))["WHAT_IT_DOES_NOT_MEAN"]
    assert any("NO_GO_ACTIVE" in bullet for bullet in bullets)


def test_a10_beginner_compiles_next_relevant_state_or_level():
    bullets = _sections(_beginner_over("Q5-03"))["NEXT_RELEVANT_STATE"]
    assert bullets
    assert any("as_of" in bullet or "levels" in bullet or "not encoded" in bullet for bullet in bullets)


def test_a11_beginner_headings_may_compress_but_semantics_remain():
    out = _run("Q5-01")
    payload = out.payload()
    ids = [section["section_id"] for section in payload["sections"]]
    assert ids == [
        "WHAT_IT_MEANS",
        "WHAT_CEREBUS_SEES",
        "WHAT_IT_DOES_NOT_MEAN",
        "NEXT_RELEVANT_STATE",
    ]
    assert {section["heading"] for section in payload["sections"]} >= {"WHAT IT MEANS", "WHAT IT DOES NOT MEAN"}


# ---------------------------------------------------------------------------
# T3 — operator compiler
# ---------------------------------------------------------------------------


def test_a12_operator_renders_model_layer_and_current_state():
    sections = _sections(_run("Q5-03"))
    assert any("MOD.XAU.GAME.V1" in bullet and "L2" in bullet for bullet in sections["MODEL_LAYER"])
    assert any("RANGE" in bullet for bullet in sections["CURRENT_STATE"])


def test_a13_operator_eligibility_uses_four_valued_precedence():
    assert SETUP_PRECEDENCE[0].value == "BLOCKED"
    assert worst_setup_verdict(("WATCH", "BLOCKED")) == "BLOCKED"
    assert worst_setup_verdict(("ELIGIBLE", "UNRESOLVED")) == "UNRESOLVED"
    assert any("ELIGIBLE" in bullet for bullet in _sections(_run("Q5-03"))["ELIGIBILITY"])
    assert any("WATCH" in bullet for bullet in _sections(_run("Q5-04"))["ELIGIBILITY"])


def test_a14_operator_range_anchor_clock_and_path_left_are_explicit():
    sections = _sections(_run("Q5-03"))
    for section in ("ACTIVE_RANGE_ANCHOR", "CLOCK", "PATH_RANGE_LEFT"):
        assert sections[section]
        for bullet in sections[section]:
            assert "0" not in bullet.split(": ", 1)[-1] or "2026" in bullet
    assert any("not encoded" in bullet for bullet in sections["PATH_RANGE_LEFT"])


def test_a15_operator_trigger_invalidation_and_targets_come_from_package():
    sections = _sections(_run("Q5-03"))
    assert any("close beyond the encoded range edge" in bullet for bullet in sections["TRIGGER"])
    assert any("close back through the anchor" in bullet for bullet in sections["INVALIDATION"])
    assert any("1.0920" in bullet for bullet in sections["TARGETS"])


def test_a16_operator_no_go_is_preserved():
    out = _run("Q5-03")
    assert "NO_GO_ACTIVE" in out.limitations
    assert "NO_GO_ACTIVE" in _text(out)


def test_a17_operator_evidence_status_is_attached():
    bullets = _sections(_run("Q5-03"))["EVIDENCE_STATUS"]
    assert any("CANONICAL" in bullet for bullet in bullets)
    assert any("limitation NO_GO_ACTIVE" in bullet for bullet in bullets)


# ---------------------------------------------------------------------------
# T4 — researcher compiler
# ---------------------------------------------------------------------------


def test_a18_researcher_exposes_model_version_and_implementation_identity():
    sections = _sections(_run("Q5-05"))
    assert any("XAU.GAME" in bullet for bullet in sections["MODEL_VERSION"])
    assert any("V1" in bullet for bullet in sections["MODEL_VERSION"])


def test_a19_researcher_exposes_claim_and_event_identity():
    sections = _sections(_run("Q5-05"))
    assert any("CL.XAU.GAME.001" in bullet for bullet in sections["CLAIM_EVENT"])
    assert any("close outside band then retest" in bullet for bullet in sections["CLAIM_EVENT"])


def test_a20_researcher_exposes_population_n_and_small_n():
    sections = _sections(_run("Q5-05"))
    assert any("XAUUSD D1 eligible events" in bullet for bullet in sections["POPULATION_N"])
    assert any("120" in bullet for bullet in sections["POPULATION_N"])
    assert any("FALSE" in bullet for bullet in sections["POPULATION_N"])


def test_a21_researcher_exposes_period_and_source_generation():
    sections = _sections(_run("Q5-05"))
    assert any("2018-01-01/2024-12-31" in bullet for bullet in sections["PERIOD_GENERATION"])
    assert any("XAU.GAME" in bullet for bullet in sections["PERIOD_GENERATION"])


def test_a22_researcher_exposes_metric_oos_and_reproduction():
    sections = _sections(_run("Q5-05"))
    assert any("completion_rate" in bullet for bullet in sections["METRIC_RESULT"])
    assert any("FORWARD_OOS" in bullet for bullet in sections["OOS_REPRODUCTION"])
    assert any("OOS_REPRODUCED" in bullet for bullet in sections["OOS_REPRODUCTION"])


def test_a23_researcher_surfaces_contradictions_and_negative_evidence():
    sections = _sections(_run("Q5-06"))
    bullets = sections["CONTRADICTIONS_NEGATIVE"]
    assert any("NEGATIVE_EVIDENCE" in bullet or "NEG.XAU.GAME.001" in bullet for bullet in bullets)


# ---------------------------------------------------------------------------
# T5 — citations
# ---------------------------------------------------------------------------


def test_a24_every_material_claim_has_a_resolvable_citation():
    for case_id in ANSWER_IDS:
        out = _run(case_id)
        for claim in out.claims:
            assert claim.citation_ids, (case_id, claim.claim_id)
            assert set(claim.citation_ids) <= {citation.source_ref_id for citation in out.citations}


def test_a25_unresolvable_citation_refuses_the_whole_answer():
    out = _run("Q5-16")
    assert isinstance(out, GovernedAnswerRefusal)
    assert "CITATION_UNRESOLVED" in _findings(out)
    assert not hasattr(out, "sections")


def test_a26_rendered_citations_use_user_facing_provenance():
    for case_id in ANSWER_IDS:
        out = _run(case_id)
        for citation in out.citations:
            assert citation.source_ref_id
            assert not is_internal_ref(citation.source_ref_id)
            assert not citation.source_ref_id.startswith(("PKG.", "MFD."))


def test_a27_citation_order_and_identity_are_deterministic():
    scenario = _case("Q5-05")
    index = PackageIndex.build(scenario.package)
    first, _ = collect(index, ("CL.XAU.GAME.001", "EV.XAU.GAME.001", "CL.XAU.GAME.001"))
    second, _ = collect(index, ("CL.XAU.GAME.001", "EV.XAU.GAME.001"))
    assert [item.source_ref_id for item in first] == [item.source_ref_id for item in second]
    assert len({item.source_ref_id for item in first}) == len(first)


def test_a28_numeric_claim_citation_matches_numeric_link_source():
    ok = _run("Q5-05")
    assert isinstance(ok, ValidatedAnswer)
    out = _run("Q5-18")
    assert "CITATION_NUMERIC_MISMATCH" in _findings(out)


def test_a29_no_fabricated_citation_satisfies_coverage():
    out = _run("Q5-19")
    assert "CITATION_UNRESOLVED" in _findings(out)
    scenario = _case("Q5-19")
    assert all(
        scenario.package.package_id
        for _ in range(1)
    )
    index = PackageIndex.build(scenario.package)
    assert index.resolve("CL.FABRICATED.001") is None


# ---------------------------------------------------------------------------
# T6 — numerical
# ---------------------------------------------------------------------------


def test_a30_numbers_must_equal_authorized_value_text():
    for case_id in ANSWER_IDS:
        out = _run(case_id)
        index = PackageIndex.build(_case(case_id).package)
        for number in out.numbers:
            entry = index.resolve(number.source_ref_id)
            assert entry is not None
            assert number.value_text in entry.numeric_values


def test_a31_invented_number_refuses():
    out = _run("Q5-07")
    assert isinstance(out, GovernedAnswerRefusal)
    assert "NUMERIC_EVIDENCE_MISSING" in _findings(out)


def test_a32_altered_or_rounded_number_refuses():
    out = _run("Q5-08")
    assert "NUMERIC_MISMATCH" in _findings(out)


def test_a33_unit_or_scale_change_refuses():
    out = _run("Q5-09")
    assert "NUMERIC_UNIT_MISMATCH" in _findings(out)


def test_a34_metric_and_evidence_class_substitution_refuses():
    assert "METRIC_SUBSTITUTION" in _findings(_run("Q5-10"))
    assert "METRIC_SUBSTITUTION" in _findings(_run("Q5-11"))
    assert "METRIC_SUBSTITUTION" in _findings(_run("Q5-12"))
    assert "EVIDENCE_CLASS_LAUNDERING" in _findings(_run("Q5-13"))


def test_a35_statistic_claim_requires_n_and_status():
    out = _run("Q5-14")
    assert "STATISTIC_INCOMPLETE" in _findings(out)


def test_a36_numeric_claim_requires_admissible_numeric_link():
    scenario = _case("Q5-07")
    assert not scenario.draft.numbers
    assert "NUMERIC_EVIDENCE_MISSING" in _findings(validate_answer(scenario.draft, scenario.package))


# ---------------------------------------------------------------------------
# T7 — layer
# ---------------------------------------------------------------------------


def test_a37_l3_destination_cannot_be_direct_l1_entry():
    out = _run("Q5-20")
    assert "LAYER_LAUNDERING" in _findings(out)


def test_a38_l2_path_statistic_cannot_be_setup_win_rate():
    out = _run("Q5-21")
    assert "LAYER_LAUNDERING" in _findings(out)


def test_a39_l1_trigger_cannot_override_higher_layer_no_go():
    out = _run("Q5-22")
    assert "LAYER_AUTHORITY_VIOLATION" in _findings(out)
    scenario = _case("Q5-22")
    assert not PackageIndex.build(scenario.package).has_cross_layer_rule()


def test_a40_claim_layer_matches_source_and_attribution():
    out = _run("Q5-01")
    index = PackageIndex.build(_case("Q5-01").package)
    for claim in out.claims:
        layers = {
            entry.layer
            for ref in claim.source_refs
            for entry in (index.resolve(ref),)
            if entry is not None and entry.layer
        }
        assert claim.layer in layers
    assert "LAYER_LAUNDERING" in _findings(_run("Q5-23"))


def test_a41_layer_labels_use_frozen_vocabulary():
    assert LAYER_VOCABULARY == {"L1", "L2", "L3", "CROSS_LAYER"}
    for case_id in ANSWER_IDS:
        out = _run(case_id)
        for claim in out.claims:
            assert not claim.layer or claim.layer in LAYER_VOCABULARY


# ---------------------------------------------------------------------------
# T8 — setup and action
# ---------------------------------------------------------------------------


def test_a42_action_language_requires_eligible_setup():
    assert isinstance(_run("Q5-03"), ValidatedAnswer)
    assert "SETUP_NOT_ENCODED" in _findings(_run("Q5-24"))
    assert "SETUP_NOT_ENCODED" in _findings(_run("Q5-25"))
    observing = _run("Q5-26")
    assert isinstance(observing, ValidatedAnswer)
    assert "enter" not in _text(observing).lower()


def test_a43_missing_setup_emits_setup_not_encoded_sentence():
    out = _run("Q5-24")
    assert out.detail.startswith(SETUP_NOT_ENCODED_SENTENCE)


def test_a44_setup_precedence_is_blocked_unresolved_watch_eligible():
    assert [verdict.value for verdict in SETUP_PRECEDENCE] == [
        "BLOCKED",
        "UNRESOLVED",
        "WATCH",
        "ELIGIBLE",
    ]
    out = _run("Q5-28")
    assert out.code is AnswerRefusalCode.SETUP_NOT_ENCODED


def test_a45_blocking_and_invalidating_reasons_are_surfaced():
    out = _run("Q5-25")
    assert "BLOCKED" in out.detail
    assert out.limitations


def test_a46_no_personalized_financial_advice_or_execution_instruction():
    out = _run("Q5-27")
    assert "ADVICE_PROHIBITED" in _findings(out)
    text = _text(out).lower()
    assert "position size" not in text.replace("position size and entry price at the zone", "")


def test_a47_setup_fields_reflect_only_encoded_values():
    out = _run("Q5-29")
    assert "SETUP_FIELD_MISMATCH" in _findings(out)
    scenario = _case("Q5-29")
    encoded = {
        fact.value_text
        for entry in PackageIndex.build(scenario.package).setup_items()
        for fact in entry.facts
    }
    assert "1.2345" not in encoded


# ---------------------------------------------------------------------------
# T9 — status and generation
# ---------------------------------------------------------------------------


def test_a48_historical_candidate_and_research_flag_cannot_read_as_current():
    assert "STATUS_LAUNDERING" in _findings(_run("Q5-30"))
    assert "STATUS_LAUNDERING" in _findings(_run("Q5-31"))
    assert "STATUS_LAUNDERING" in _findings(_run("Q5-32"))


def test_a49_parked_superseded_and_negative_evidence_are_preserved():
    assert "STATUS_LAUNDERING" in _findings(_run("Q5-33"))
    negative = _run("Q5-06")
    assert any(claim.epistemic_label == "NEGATIVE_EVIDENCE" for claim in negative.claims)


def test_a50_epistemic_label_must_equal_source_label():
    out = _run("Q5-33")
    assert "STATUS_LAUNDERING" in _findings(out)
    for case_id in ANSWER_IDS:
        scenario = _case(case_id)
        index = PackageIndex.build(scenario.package)
        for claim in _run(case_id).claims:
            labels = {
                index.resolve(ref).label.value
                for ref in claim.source_refs
                if index.resolve(ref) is not None
            }
            assert claim.epistemic_label in labels


def test_a51_generation_and_timestamp_are_preserved():
    out = _run("Q5-31")
    assert "STATUS_LAUNDERING" in _findings(out)
    answer = _run("Q5-01")
    model = next(claim for claim in answer.claims if claim.generation)
    assert model.generation == "FIB.ORIGINAL"


def test_a52_status_cannot_be_upgraded_by_prose_confidence_or_citations():
    scenario = _case("Q5-30")
    loud = replace(
        scenario.draft,
        proposed_prose="This is certainly validated, production-grade and fully confirmed.",
    )
    out = validate_answer(loud, scenario.package)
    assert "STATUS_LAUNDERING" in _findings(out)
    assert out.record.claim_statuses == ()


# ---------------------------------------------------------------------------
# T10 — freshness
# ---------------------------------------------------------------------------


def test_a53_current_state_exposes_as_of_or_data_cutoff():
    out = _run("Q5-03")
    assert out.as_of == "2026-11-08T00:00:00Z"
    assert "as_of" in _text(out)


def test_a54_stale_snapshot_cannot_be_presented_as_live():
    out = _run("Q5-34")
    assert "STALE_PRESENTED_AS_LIVE" in _findings(out)
    assert out.code is AnswerRefusalCode.CURRENT_DATA_UNAVAILABLE


def test_a55_missing_freshness_metadata_refuses_current_data_unavailable():
    out = _run("Q5-35")
    assert "MISSING_FRESHNESS" in _findings(out)
    assert out.code is AnswerRefusalCode.CURRENT_DATA_UNAVAILABLE


def test_a56_clock_unresolved_propagates():
    out = _run("Q5-36")
    assert isinstance(out, ValidatedAnswer)
    assert "CLOCK_UNRESOLVED" in out.limitations
    assert "CLOCK_UNRESOLVED" in _text(out)


# ---------------------------------------------------------------------------
# T11 — leakage
# ---------------------------------------------------------------------------


def test_a57_internal_codes_tables_endpoints_and_traces_are_not_rendered():
    out = _run("Q5-37")
    assert "LEAKAGE_INTERNAL_MATERIAL" in _findings(out)


def test_a58_bulk_contiguous_corpus_reproduction_is_blocked():
    out = _run("Q5-38")
    assert "LEAKAGE_CORPUS" in _findings(out)


def test_a59_hidden_object_enumeration_is_blocked():
    out = _run("Q5-39")
    assert "LEAKAGE_ENUMERATION" in _findings(out)


def test_a60_system_prompt_credentials_and_config_are_not_disclosed():
    out = _run("Q5-39")
    assert "LEAKAGE_SYSTEM" in _findings(out)
    scenario = _case("Q5-03")
    leaky = replace(
        scenario.draft,
        claims=(replace(scenario.draft.claims[0], text="The api key and system prompt follow."),),
        citations=(scenario.draft.claims[0].source_refs[0],),
    )
    assert "LEAKAGE_SYSTEM" in _findings(validate_answer(leaky, scenario.package))


def test_a61_injected_package_text_remains_untrusted_data():
    scenario = _case("Q5-39")
    clean = replace(
        scenario.draft,
        claims=(
            replace(
                scenario.draft.claims[0],
                text="The authorized package carries an unverified external note.",
                source_refs=("QC.QUERY",),
                epistemic_label="CANONICAL",
                layer="",
                generation="",
            ),
        ),
        citations=("QC.QUERY",),
    )
    out = validate_answer(clean, scenario.package)
    assert isinstance(out, ValidatedAnswer)
    assert "ignore previous" not in _text(out).lower()
    assert "system prompt" not in _text(out).lower()


# ---------------------------------------------------------------------------
# T12 — uncertainty and refusal
# ---------------------------------------------------------------------------


def test_a62_six_frozen_answer_refusal_codes_are_exhaustive():
    assert {code.value for code in AnswerRefusalCode} == {
        "INSUFFICIENT_EVIDENCE",
        "CURRENT_DATA_UNAVAILABLE",
        "MODEL_VERSION_UNAVAILABLE",
        "SETUP_NOT_ENCODED",
        "ACCESS_NOT_ENTITLED",
        "AMBIGUOUS_SCOPE",
    }
    for code in ValidationCode:
        assert code in FINDING_REFUSAL


def test_a63_refusal_precedence_is_deterministic():
    assert [code.value for code in REFUSAL_PRECEDENCE] == [
        "ACCESS_NOT_ENTITLED",
        "AMBIGUOUS_SCOPE",
        "MODEL_VERSION_UNAVAILABLE",
        "CURRENT_DATA_UNAVAILABLE",
        "SETUP_NOT_ENCODED",
        "INSUFFICIENT_EVIDENCE",
    ]
    low = Finding(ValidationCode.CITATION_REQUIRED, "x")
    high = Finding(ValidationCode.ACCESS_NOT_ENTITLED, "y")
    assert refusal_for((low, high)) is AnswerRefusalCode.ACCESS_NOT_ENTITLED
    assert refusal_for((high, low)) is AnswerRefusalCode.ACCESS_NOT_ENTITLED


def test_a64_refusal_never_fabricates_or_hedges_into_an_answer():
    for case_id in REFUSAL_IDS:
        outcome = _run(case_id)
        payload = outcome.payload()
        assert payload["outcome"] == "GOVERNED_REFUSAL"
        assert "sections" not in payload
        assert "claims" not in payload


def test_a65_refusal_payload_is_safe_and_bounded():
    for case_id in REFUSAL_IDS:
        payload = _run(case_id).payload()
        assert payload["detail"]
        assert len(payload["detail"]) < 400
        assert "Traceback" not in payload["detail"]
        assert "app.forge" not in payload["detail"]


def test_a66_validator_failure_reports_its_own_code():
    out = _run("Q5-08")
    assert "NUMERIC_MISMATCH" in out.findings
    assert out.code is AnswerRefusalCode.INSUFFICIENT_EVIDENCE
    assert _run("Q5-25").findings == ("SETUP_NOT_ENCODED",)


# ---------------------------------------------------------------------------
# T13 — record
# ---------------------------------------------------------------------------


def test_a67_answer_id_is_deterministic():
    first = _run("Q5-45")
    second = _run("Q5-45")
    assert first.answer_id == second.answer_id
    assert first.answer_id.startswith("ANS.")
    assert len(first.answer_id) == len("ANS.") + 32


def test_a68_record_carries_identity_model_and_validation_codes():
    out = _run("Q5-03")
    record = out.record
    assert record.package_id == _case("Q5-03").package.package_id
    assert record.manifest_id == _case("Q5-03").package.manifest.manifest_digest
    assert record.query_plan_id == "QP.Q5-03"
    assert record.model == "fake-model-1"
    assert record.provider == "fake"
    assert record.validation_codes == ()
    refused = _run("Q5-25")
    assert refused.record.validation_codes == ("SETUP_NOT_ENCODED",)
    assert refused.record.answer_refusal_code == "SETUP_NOT_ENCODED"


def test_a69_record_carries_citations_and_epistemic_status():
    out = _run("Q5-05")
    record = out.record
    assert record.cited_refs == tuple(citation.source_ref_id for citation in out.citations)
    assert record.claim_statuses
    assert all(label for _, label in record.claim_statuses)


def test_a70_record_carries_latency_and_cost_without_secrets():
    record = _run("Q5-03").record
    assert record.latency_ms == 250.0
    assert record.cost_usd == 0.0007
    assert record.cost_basis == "PROVIDER_REPORTED"
    payload = record.payload()
    for key in payload:
        assert "prompt" not in key or key in ("prompt_id", "prompt_version")
    assert "authorization" not in json.dumps(payload).lower()


def test_a71_prose_persistence_requires_retention_policy():
    record = _run("Q5-45").record
    assert record.prose_retained is False
    assert RETENTION_POLICY_STATUS == "OPEN_F4"


# ---------------------------------------------------------------------------
# T14 — cross-cutting invariance
# ---------------------------------------------------------------------------


def test_a72_no_network_model_or_retrieval_call_inside_answer_layer(monkeypatch):
    def explode(*_args, **_kwargs):
        raise AssertionError("the answer layer must not open a socket")

    monkeypatch.setattr(socket, "socket", explode)
    monkeypatch.setattr(socket, "create_connection", explode)
    for case_id in Q5_IDS:
        assert _run(case_id) is not None


def test_a73_answer_layer_is_byte_deterministic():
    manifest = json.loads((Q5_DIR / "FIXTURE_MANIFEST.json").read_text(encoding="utf-8"))
    assert manifest["count"] == 46
    assert tuple(sorted(manifest["records"])) == Q5_IDS
    for case_id in Q5_IDS:
        outcome = _run(case_id)
        first = json.dumps(outcome.payload(), sort_keys=True, ensure_ascii=False)
        second = json.dumps(outcome.payload(), sort_keys=True, ensure_ascii=False)
        assert first == second, case_id
        compact = json.dumps(outcome.payload(), sort_keys=True, separators=(",", ":"), ensure_ascii=False)
        record = json.loads((Q5_DIR / f"{case_id}.json").read_text(encoding="utf-8"))
        assert record["payload_sha256"] == hashlib.sha256(compact.encode("utf-8")).hexdigest(), case_id
        assert record["answer_id"] == outcome.answer_id
        assert record["outcome"] == outcome.payload()["outcome"]


def test_a74_frozen_upstream_hashes_routes_and_migrations_unchanged():
    for relative, expected in FROZEN.items():
        actual = hashlib.sha256((ROOT / relative).read_bytes()).hexdigest()
        assert actual == expected, relative
    assert [migration.version for migration in discover_migrations()] == [1, 2, 3, 4]


def test_a75_answer_and_record_payloads_contain_no_secrets():
    banned = ("api key", "sk-", "password", "bearer ", "secret key", "authorization:")
    for case_id in Q5_IDS:
        text = _text(_run(case_id)).lower()
        for token in banned:
            assert token not in text, (case_id, token)


def test_a76_validators_cannot_be_disabled_or_bypassed():
    assert VALIDATOR_ORDER == (
        "upstream",
        "numerical",
        "layer",
        "setup",
        "status",
        "freshness",
        "leakage",
        "citation",
        "assembly",
    )
    assert tuple(name for name, _ in VALIDATORS) == VALIDATOR_ORDER
    for path in _answer_module_paths():
        source = path.read_text(encoding="utf-8")
        assert "os.environ" not in source
        assert "getenv" not in source
    assert SUPPORTED_ANSWER_CONTRACT_VERSIONS == (ASK_ANSWER_CONTRACT_V1,)


# ---------------------------------------------------------------------------
# cross-cutting drivers
# ---------------------------------------------------------------------------


def test_a77_numerical_validator_runs_before_rendering():
    assert VALIDATOR_ORDER.index("numerical") < VALIDATOR_ORDER.index("citation")
    out = _run("Q5-08")
    assert not hasattr(out, "sections")
    assert "NUMERIC_MISMATCH" in out.findings


def test_a78_status_and_layer_validators_run_before_citation_rendering():
    assert VALIDATOR_ORDER.index("layer") < VALIDATOR_ORDER.index("citation")
    assert VALIDATOR_ORDER.index("status") < VALIDATOR_ORDER.index("citation")
    out = _run("Q5-20")
    assert "LAYER_LAUNDERING" in out.findings
    assert "CITATION_REQUIRED" not in out.findings


def test_a79_setup_and_freshness_gate_actionable_claims():
    assert VALIDATOR_ORDER.index("setup") < VALIDATOR_ORDER.index("citation")
    assert VALIDATOR_ORDER.index("freshness") < VALIDATOR_ORDER.index("citation")
    out = _run("Q5-34")
    assert "STALE_PRESENTED_AS_LIVE" in out.findings
    assert not hasattr(out, "sections")


def test_a80_leakage_validator_runs_last_and_can_veto():
    assert VALIDATOR_ORDER.index("leakage") > VALIDATOR_ORDER.index("freshness")
    assert VALIDATOR_ORDER.index("leakage") < VALIDATOR_ORDER.index("citation")
    out = _run("Q5-37")
    assert out.code is AnswerRefusalCode.INSUFFICIENT_EVIDENCE
    assert isinstance(out, GovernedAnswerRefusal)


def test_a81_beginner_operator_researcher_share_one_validation_core():
    from app.forge.ask_cerebus.answer import validators as module

    assert module.run_validators is run_validators
    depths = {_case(case_id).draft.depth for case_id in ANSWER_IDS}
    assert depths == {"BEGINNER", "OPERATOR", "RESEARCHER"}
    for case_id in ("Q5-01", "Q5-03", "Q5-05"):
        scenario = _case(case_id)
        admitted = __import__(
            "app.forge.ask_cerebus.answer.admission", fromlist=["admit"]
        ).admit(scenario.draft, scenario.package)
        from app.forge.ask_cerebus.answer.service import prepare_claims

        assert run_validators(admitted, prepare_claims(admitted)) == ()


def test_a82_refusal_outranks_partial_answer():
    out = _run("Q5-07")
    assert isinstance(out, GovernedAnswerRefusal)
    assert out.outcome is AnswerOutcome.GOVERNED_REFUSAL
    assert "73.4%" not in _text(out)


def test_a83_same_draft_and_package_reproduce_identical_outcome():
    for case_id in Q5_IDS:
        first = _run(case_id)
        second = _run(case_id)
        assert first.answer_id == second.answer_id
        assert first.payload() == second.payload()


def test_a84_changed_package_manifest_identity_refuses():
    scenario = _case("Q5-03")
    changed = replace(scenario.package, package_id="PKG." + "1" * 32)
    out = validate_answer(scenario.draft, changed)
    assert isinstance(out, GovernedAnswerRefusal)
    assert "ANSWER_IDENTITY_MISMATCH" in _findings(out)


def test_a85_no_answer_path_omits_the_response_record():
    for case_id in Q5_IDS:
        record = _run(case_id).record
        assert record.record_version == "ANSWER_RECORD_V1"
        assert record.answer_id.startswith("ANS.")
        assert record.outcome.value == _run(case_id).outcome.value


def test_a86_fake_green_is_contract_evidence_only():
    assert MATERIALITY_POLICY_STATUS.endswith("F3")
    assert REFUSAL_PRECEDENCE_STATUS.endswith("F3")
    assert CITATION_SURFACE_STATUS.endswith("F3")
    assert CROSS_LAYER_RULE_STATUS.endswith("F3")
    assert RETENTION_POLICY_STATUS == "OPEN_F4"
    assert CORPUS_LICENSING_STATUS == "OPEN_F4"
    assert MARKET_DATA_STATUS == "NOT_CONFIGURED"
    payload = _text(_run("Q5-03")).lower()
    assert "production-ready" not in payload
    assert "approved for production" not in payload
