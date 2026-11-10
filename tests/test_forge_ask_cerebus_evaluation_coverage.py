"""BA-34 acceptance drivers: F-06 evidence paths and F-07 refusal limitations.

Requirement inventory (EC-01..EC-30) is declared in
``implementation/forge/book_iv/security_amendment_1/EVALUATION_COVERAGE_SUPPLEMENT_V1.md``.
No driver fabricates an expectation from a live run: expectations come from the
frozen case records and the Book I catalog, and the negative controls are
constructed observations, not weakened assertions.
"""

from __future__ import annotations

import ast
import json
from dataclasses import replace
from pathlib import Path

import pytest

from app.forge.ask_cerebus.evaluation import (
    amendment,
    corpus,
    coverage_scoring,
    enums,
    evidence_path,
    harness,
    limitations,
)
from app.forge.ask_cerebus.evaluation.dataset import build_dataset

ROOT = Path(__file__).resolve().parents[1]
V1_FIXTURES = ROOT / "implementation/forge/book_iv/bloc_iv_6/fixtures"
SECURITY_DIR = ROOT / "implementation/forge/book_iv/security_amendment_1"

V1_CHAIN_IDS = ("EV-001", "EV-002", "EV-006", "EV-007", "EV-010")


@pytest.fixture(scope="module")
def v1_dataset():
    return build_dataset(V1_FIXTURES)


@pytest.fixture(scope="module")
def v1_runs(v1_dataset):
    return {case.case_id: harness.run_case(case) for case in v1_dataset.cases}


@pytest.fixture(scope="module")
def v2_cases():
    return corpus.cases()


@pytest.fixture(scope="module")
def v2_runs(v2_cases):
    return {case.case_id: harness.run_case(case) for case in v2_cases}


def _verdict(case_id, runs, expectation=None):
    expectation = expectation or evidence_path.expectation_for(case_id)
    return evidence_path.evaluate(expectation, evidence_path.observe(runs[case_id]))


# ---------------------------------------------------------------------------
# EC-01..EC-05  baseline and V1 CHAIN reconciliation
# ---------------------------------------------------------------------------


def test_ec01_declared_expectations_cover_the_v1_chain_population(v1_dataset):
    chain = [
        case.case_id
        for case in v1_dataset.cases
        if case.execution_mode is enums.ExecutionMode.CHAIN
    ]
    assert tuple(chain) == V1_CHAIN_IDS
    assert {item.case_id for item in evidence_path.V1_CHAIN_EXPECTATIONS} == set(chain)


def test_ec02_v1_population_is_five_chain_and_one_hundred_fifteen_sealed(v1_dataset):
    modes = [case.execution_mode for case in v1_dataset.cases]
    assert len(modes) == 120
    assert modes.count(enums.ExecutionMode.CHAIN) == 5
    assert modes.count(enums.ExecutionMode.SEALED) == 115


def test_ec03_ev006_walks_the_declared_canonical_path(v1_runs):
    verdict = _verdict("EV-006", v1_runs)
    assert verdict.reconciliation == evidence_path.CANONICAL_PATH
    assert verdict.applicable
    assert verdict.passed, verdict.failures
    assert dict(verdict.checks)["model_selected_in_trace"]


def test_ec04_ev001_and_ev002_are_definitional_plan_sources(v1_runs):
    for case_id in ("EV-001", "EV-002"):
        verdict = _verdict(case_id, v1_runs)
        assert verdict.reconciliation == evidence_path.DEFINITIONAL_PLAN_SOURCE
        assert not verdict.applicable
        assert verdict.passed, verdict.failures
        observation = evidence_path.observe(v1_runs[case_id])
        assert observation.citations
        assert all(ref.startswith("PLAN.") for ref in observation.citations)
        assert not any(ref.startswith("MOD.") for ref in observation.citations)


def test_ec05_ev007_and_ev010_are_recorded_as_corpus_absent(v1_runs):
    for case_id in ("EV-007", "EV-010"):
        expectation = evidence_path.expectation_for(case_id)
        assert expectation.reconciliation == evidence_path.CORPUS_ABSENT
        observation = evidence_path.observe(v1_runs[case_id])
        verdict = evidence_path.evaluate(expectation, observation, scored=False)
        assert verdict.passed
        assert "corpus_evidence_available" in verdict.failed_checks()
        assert not verdict.applicable


# ---------------------------------------------------------------------------
# EC-06..EC-08  additive corpus integrity
# ---------------------------------------------------------------------------


def test_ec06_v2_corpus_digest_matches_its_frozen_manifest():
    assert corpus.verify() == ()
    manifest = corpus.frozen_manifest()
    assert manifest["dataset_version"] == "ASK_EVALUATION_DATASET_V2"
    assert manifest["case_count"] == len(corpus.cases())
    assert manifest["digest"] == corpus.digest()


def test_ec07_every_v2_case_declares_an_independent_path(v2_cases):
    declared = {item.case_id: item for item in evidence_path.V2_EXPECTATIONS}
    assert set(declared) == {case.case_id for case in v2_cases}
    for case in v2_cases:
        expectation = declared[case.case_id]
        assert expectation.authority
        assert expectation.reconciliation in evidence_path.RECONCILIATIONS
        if expectation.applicable:
            assert expectation.authority.startswith("Book I catalog")
            assert case.expected_citations == (expectation.canonical_model,)


def test_ec08_v2_corpus_passes_end_to_end(v2_cases, v2_runs):
    verdicts = [evidence_path.evaluate(evidence_path.expectation_for(case.case_id), evidence_path.observe(v2_runs[case.case_id])) for case in v2_cases]
    failures = [(verdict.case_id, verdict.failures) for verdict in verdicts if not verdict.passed]
    assert not failures, failures
    assert len(verdicts) == 10
    assert sum(1 for verdict in verdicts if verdict.applicable) == 9


# ---------------------------------------------------------------------------
# EC-09..EC-16  wrong-reference negative controls
# ---------------------------------------------------------------------------


def test_ec09_wrong_canonical_model_is_detected(v2_runs):
    observation = evidence_path.observe(v2_runs["EV-147"])
    wrong = replace(
        observation,
        trace_ids=("MOD.BASE80.V1",),
        package_ids=("MOD.BASE80.V1",),
        manifest_ids=("MOD.BASE80.V1",),
        claim_sources=(("MOD.BASE80.V1",),),
        citations=("MOD.BASE80.V1",),
    )
    verdict = evidence_path.evaluate(evidence_path.expectation_for("EV-147"), wrong)
    assert not verdict.passed
    assert "model_selected_in_trace" in verdict.failures
    assert "citation_supports_expected_source" in verdict.failures


def test_ec10_plan_substitution_is_detected(v2_runs):
    observation = evidence_path.observe(v2_runs["EV-146"])
    substituted = replace(
        observation,
        package_ids=tuple(item for item in observation.package_ids if not item.startswith("EV.")),
        citations=("PLAN.aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",),
    )
    verdict = evidence_path.evaluate(evidence_path.expectation_for("EV-146"), substituted)
    assert not verdict.passed
    assert "not_plan_only" in verdict.failures
    assert "citation_supports_expected_source" in verdict.failures


def test_ec11_generation_mismatch_is_detected(v2_runs):
    observation = replace(
        evidence_path.observe(v2_runs["EV-147"]), claim_generations=("XAU.GAME.2024",)
    )
    expectation = replace(evidence_path.expectation_for("EV-147"), generation="P90.V1")
    verdict = evidence_path.evaluate(expectation, observation)
    assert not verdict.passed
    assert "generation_matches" in verdict.failures


def test_ec12_irrelevant_authorized_citation_is_detected(v2_runs):
    observation = evidence_path.observe(v2_runs["EV-153"])
    irrelevant = replace(
        observation,
        package_ids=observation.package_ids + ("MOD.BASE80.V1",),
        manifest_ids=observation.manifest_ids + ("MOD.BASE80.V1",),
        trace_ids=observation.trace_ids + ("MOD.BASE80.V1",),
        citations=("MOD.BASE80.V1",),
    )
    verdict = evidence_path.evaluate(evidence_path.expectation_for("EV-153"), irrelevant)
    assert not verdict.passed
    assert "citation_supports_expected_source" in verdict.failures


def test_ec13_missing_expected_evidence_is_detected(v2_runs):
    observation = evidence_path.observe(v2_runs["EV-146"])
    stripped = replace(
        observation,
        package_ids=tuple(item for item in observation.package_ids if item != "EV.XAU.SUPPORTED.V1"),
        manifest_ids=tuple(item for item in observation.manifest_ids if item != "EV.XAU.SUPPORTED.V1"),
    )
    verdict = evidence_path.evaluate(evidence_path.expectation_for("EV-146"), stripped)
    assert not verdict.passed
    assert "evidence_refs_packaged" in verdict.failures


def test_ec14_context_omission_is_detected(v2_runs):
    observation = evidence_path.observe(v2_runs["EV-146"])
    omitted = replace(
        observation,
        package_ids=tuple(item for item in observation.package_ids if item != "MOD.XAU.GAME.V1"),
        manifest_ids=tuple(item for item in observation.manifest_ids if item != "MOD.XAU.GAME.V1"),
        claim_sources=tuple(tuple(ref for ref in sources if ref != "MOD.XAU.GAME.V1") for sources in observation.claim_sources),
        citations=tuple(item for item in observation.citations if item != "MOD.XAU.GAME.V1"),
    )
    verdict = evidence_path.evaluate(evidence_path.expectation_for("EV-146"), omitted)
    assert not verdict.passed
    assert "model_packaged" in verdict.failures
    assert "model_in_manifest" in verdict.failures


def test_ec15_dropped_citation_is_detected(v2_runs):
    observation = evidence_path.observe(v2_runs["EV-145"])
    dropped = replace(observation, citations=())
    verdict = evidence_path.evaluate(evidence_path.expectation_for("EV-145"), dropped)
    assert not verdict.passed
    assert "citation_supports_expected_source" in verdict.failures
    assert "not_plan_only" in verdict.failures


def test_ec16_unauthorized_package_evidence_is_detected(v2_runs):
    observation = evidence_path.observe(v2_runs["EV-145"])
    widened = replace(
        observation,
        package_ids=observation.package_ids + ("MOD.XAU.SECRET.V1",),
        manifest_ids=observation.manifest_ids + ("MOD.XAU.SECRET.V1",),
    )
    verdict = evidence_path.evaluate(evidence_path.expectation_for("EV-145"), widened)
    assert not verdict.passed
    assert "no_unauthorized_package_evidence" in verdict.failures


def test_ec17_evidence_path_oracle_keeps_its_import_law():
    forbidden = evidence_path.forbidden_import_roots()
    for name in ("evidence_path", "limitations"):
        source = (ROOT / "app/forge/ask_cerebus/evaluation" / f"{name}.py").read_text(encoding="utf-8")
        tree = ast.parse(source)
        imported: list[str] = []
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module:
                imported.append(node.module)
            elif isinstance(node, ast.Import):
                imported.extend(alias.name for alias in node.names)
        for module in imported:
            assert not any(module.startswith(root) for root in forbidden), (name, module)


# ---------------------------------------------------------------------------
# EC-18..EC-23  refusal limitation coverage
# ---------------------------------------------------------------------------


def test_ec18_refusal_expectations_cover_all_seventy_two(v1_dataset):
    refusals = [case for case in v1_dataset.cases if not case.is_positive]
    expectations = [
        limitations.expectation_for(case) for case in refusals
    ]
    assert len(refusals) == 72
    assert len(expectations) == 72
    assert all(expectation.applicable for expectation in expectations)
    assert all(expectation.required for expectation in expectations)


def test_ec19_every_v1_refusal_preserves_its_applicable_limitations(v1_dataset, v1_runs):
    cases = [case for case in v1_dataset.cases if not case.is_positive]
    verdicts = limitations.evaluate_all(
        cases, [limitations.observe(v1_runs[case.case_id]) for case in cases]
    )
    broken = [(verdict.case_id, verdict.missing, verdict.leaked) for verdict in verdicts if not verdict.passed]
    assert not broken, broken
    assert len(verdicts) == 72


def test_ec20_missing_limitation_is_detected(v1_runs):
    observation = limitations.observe(v1_runs["EV-032"])
    stripped = replace(observation, limitations=(), visible_text="")
    verdict = limitations.evaluate(limitations.expectation_for(
        next(case for case in build_dataset(V1_FIXTURES).cases if case.case_id == "EV-032")
    ), stripped)
    assert not verdict.passed
    assert "SETUP_NOT_ENCODED" in verdict.missing


def test_ec21_protected_leak_is_detected(v1_runs):
    case = next(case for case in build_dataset(V1_FIXTURES).cases if case.case_id == "EV-062")
    observation = limitations.observe(v1_runs["EV-062"])
    leaked = replace(observation, visible_text=observation.visible_text + " sha256:deadbeef")
    verdict = limitations.evaluate(limitations.expectation_for(case), leaked)
    assert not verdict.passed
    assert verdict.leaked == ("sha256:",)


def test_ec22_no_go_is_required_where_eligibility_is_blocked(v1_dataset):
    blocked = [
        case for case in v1_dataset.cases if case.expected_eligibility == "BLOCKED"
    ]
    assert blocked
    for case in blocked:
        assert "NO_GO_ACTIVE" in limitations.required_limitations(case)


def test_ec23_freshness_refusals_require_the_current_data_limitation(v1_dataset):
    freshness = [
        case for case in v1_dataset.cases if case.family is enums.CaseFamily.FRESHNESS
    ]
    assert len(freshness) == 5
    refusals = [case for case in freshness if not case.is_positive]
    assert len(refusals) == 4
    for case in refusals:
        assert "CURRENT_DATA_UNAVAILABLE" in limitations.required_limitations(case)
    positive = [case for case in freshness if case.is_positive]
    assert len(positive) == 1
    assert limitations.required_limitations(positive[0]) == ()


# ---------------------------------------------------------------------------
# EC-24..EC-30  false refusals, scoring, historical integrity, additivity
# ---------------------------------------------------------------------------


def test_ec24_false_refusal_rate_is_zero_over_fifty_eight_positives(v1_dataset, v1_runs, v2_cases, v2_runs):
    positives = [case.case_id for case in v1_dataset.cases if case.is_positive] + [
        case.case_id for case in v2_cases
    ]
    assert len(positives) == 58
    refused = [
        case_id
        for case_id, execution in {**v1_runs, **v2_runs}.items()
        if execution.outcome != "VALIDATED_ANSWER" and case_id in positives
    ]
    score = coverage_scoring.false_refusal_rate(positives, refused)
    assert score.status == coverage_scoring.MEASURED
    assert (score.numerator, score.denominator) == (0, 58)


def test_ec25_blocking_an_action_does_not_block_explanation():
    educational = next(case for case in amendment.cases() if case.case_id == "EV-139")
    result = amendment.run_case(educational)
    assert result.outcome == "VALIDATED_ANSWER"
    assert result.passed, result.reasons


def test_ec26_scores_declare_denominators_and_exclusions(v1_dataset, v1_runs, v2_cases, v2_runs):
    path_verdicts = [
        _verdict(case.case_id, v1_runs)
        for case in v1_dataset.cases
        if case.case_id in V1_CHAIN_IDS
    ] + [
        evidence_path.evaluate(
            evidence_path.expectation_for(case.case_id), evidence_path.observe(v2_runs[case.case_id])
        )
        for case in v2_cases
    ]
    refusals = [case for case in v1_dataset.cases if not case.is_positive]
    limitation_verdicts = limitations.evaluate_all(
        refusals, [limitations.observe(v1_runs[case.case_id]) for case in refusals]
    )
    positives = [case.case_id for case in v1_dataset.cases if case.is_positive] + [
        case.case_id for case in v2_cases
    ]
    scores = coverage_scoring.coverage_scores(
        path_verdicts=path_verdicts,
        limitation_verdicts=limitation_verdicts,
        positive_case_ids=positives,
        refused_case_ids=(),
    )
    by_id = {score.metric_id: score for score in scores}
    assert len(scores) == 5
    for score in scores:
        assert score.version == coverage_scoring.COVERAGE_SCORING_V1
        if score.status == coverage_scoring.MEASURED:
            assert score.denominator == len(score.eligible_case_ids)
    path = by_id[coverage_scoring.CHAIN_EVIDENCE_PATH_CORRECTNESS]
    assert path.denominator == 10
    assert path.numerator == 10
    assert {case_id for case_id, _ in path.excluded} == {
        "EV-001",
        "EV-002",
        "EV-007",
        "EV-010",
        "EV-154",
    }
    assert by_id[coverage_scoring.REFUSAL_LIMITATION_CORRECTNESS].denominator == 72
    assert by_id[coverage_scoring.PROTECTED_REFUSAL_LEAKAGE_RATE].numerator == 0


def test_ec27_historical_dataset_digests_are_unchanged(v1_dataset):
    assert v1_dataset.digest == "74bc217bd3908fbbb9984d316182c70ca904878c2299709567cca5a82cbd31a8"
    assert amendment.dataset_digest() == "881e8403fdd9ec868530f4a0ab42f809ae458e3965233469d988784721492339"
    assert len(v1_dataset.cases) == 120
    assert len(amendment.cases()) == 24


def test_ec28_frozen_versions_and_metric_surface_are_untouched():
    from app.forge.ask_cerebus.evaluation import versions

    assert versions.CASE_COUNT == 120
    assert versions.DRIVER_COUNT == 112
    assert versions.SCORING_V1 == "ASK_EVALUATION_SCORING_V1"
    assert versions.SUPPORTED_DATASET_VERSIONS == ("ASK_EVALUATION_DATASET_V1",)
    assert len(list(enums.MetricId)) == 20
    assert evidence_path.EVIDENCE_PATH_EVALUATION_V2 == "ASK_EVALUATION_EVIDENCE_PATH_V2"
    assert limitations.REFUSAL_LIMITATION_EVALUATION_V1 == "ASK_EVALUATION_REFUSAL_LIMITATIONS_V1"


def test_ec29_manifest_identity_is_checked(v2_runs):
    observation = replace(evidence_path.observe(v2_runs["EV-145"]), manifest_id="")
    verdict = evidence_path.evaluate(evidence_path.expectation_for("EV-145"), observation)
    assert not verdict.passed
    assert "manifest_identity_recorded" in verdict.failures


def test_ec30_plan_only_citation_fails_when_a_model_is_required(v2_runs):
    observation = evidence_path.observe(v2_runs["EV-145"])
    plan_only = replace(
        observation,
        package_ids=("PLAN.bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",),
        manifest_ids=("PLAN.bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",),
        claim_sources=(("PLAN.bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",),),
        citations=("PLAN.bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",),
    )
    verdict = evidence_path.evaluate(evidence_path.expectation_for("EV-145"), plan_only)
    assert not verdict.passed
    assert "not_plan_only" in verdict.failures
    assert "model_packaged" in verdict.failures
