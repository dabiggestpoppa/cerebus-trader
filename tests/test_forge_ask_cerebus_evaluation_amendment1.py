"""Security amendment 1 (BA-32) — AM1-R25 and AM1-R26.

R25 reconciles the numerical populations without touching SCORING_V1. R26 makes
CHAIN evidence-path precision assertable, which the audit showed V1 never did.

R27 (cross-platform hash invariance) is DEFERRED: the 17 affected guards belong
to test infrastructure and need their own authorization. No driver here claims
that requirement, and nothing in this file normalises a broken guard.
"""

from __future__ import annotations

import sys
from functools import lru_cache
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.forge.ask_cerebus.evaluation import amendment, dataset, harness, matching, scoring

AM1_R27_STATUS = "DEFERRED — TEST INFRASTRUCTURE OWNER"


@lru_cache(maxsize=1)
def _v1_records():
    built = dataset.build_dataset("implementation/forge/book_iv/bloc_iv_6/fixtures")
    executions = harness.run_dataset(built)
    return scoring.records(built.cases, executions, matching.match_all(built.cases, executions))


def test_am1_r25_numeric_populations_reported_separately():
    populations = amendment.numeric_populations(_v1_records())
    assert populations["numbers_proposed_by_drafts"] == 29
    assert populations["numbers_admitted_in_validated_answers"] == 9
    assert populations["numbers_in_validated_answers"] == 9
    assert populations["numbers_rejected_by_numeric_codes"] == 9
    assert populations["numbers_rejected_by_other_codes"] == 11
    assert populations["numbers_emitted_in_governed_refusals"] == 0
    assert populations["unsupported_numbers_in_validated_answers"] == 0
    assert (
        populations["numbers_admitted_in_validated_answers"]
        + populations["numbers_rejected_by_numeric_codes"]
        + populations["numbers_rejected_by_other_codes"]
        == populations["numbers_proposed_by_drafts"]
    )

    scores = {score.metric_id: score for score in amendment.score_v2(populations, amendment.run_all())}
    rejection = scores[amendment.MetricIdV2.DRAFT_NUMERIC_PROPOSAL_REJECTION_RATE]
    unsupported = scores[amendment.MetricIdV2.VALIDATED_ANSWER_UNSUPPORTED_NUMBER_RATE]
    attribution = scores[amendment.MetricIdV2.NUMERIC_VALIDATOR_ATTRIBUTION_RATE]
    assert (rejection.numerator, rejection.denominator) == (20, 29)
    assert (unsupported.numerator, unsupported.denominator) == (0, 9)
    assert (attribution.numerator, attribution.denominator) == (9, 20)
    assert unsupported.value == 0.0
    assert rejection.value != unsupported.value


def test_am1_r26_chain_positives_assert_evidence_path():
    built = dataset.build_dataset("implementation/forge/book_iv/bloc_iv_6/fixtures")
    executions = {execution.case_id: execution for execution in harness.run_dataset(built)}
    chain_cases = [case for case in built.cases if case.execution_mode.value == "CHAIN"]
    assert len(chain_cases) == 5

    for case in chain_cases:
        execution = executions[case.case_id]
        assert execution.outcome == "VALIDATED_ANSWER"
        package = execution.artifacts["package"]
        package_refs = {
            item.source_ref_id
            for section in package.sections
            for item in section.items
            if item.source_ref_id
        }
        payload = execution.artifacts["answer"].payload()
        cited = {citation["source_ref_id"] for citation in payload.get("citations", ())}
        assert cited, f"{case.case_id} cites nothing"
        assert cited <= package_refs, f"{case.case_id} cites outside its package: {cited - package_refs}"

        if not case.model_ids:
            assert all(ref.startswith("PLAN.") for ref in cited), case.case_id

    #: The harness does expose a model-identity citation: EV-006 cites
    #: ``MOD.BTC.TRACKER.V1``, which contains its declared model id. That makes
    #: model-path precision observable at all. It does not make it *asserted* for
    #: the four cases that cite only the query-plan pseudo-item; that remaining
    #: gap is recorded as F-06 in SUPPLEMENTAL_EVALUATION.md and is deliberately
    #: not counted here, because a shape-only chain response is not evidence-path
    #: correctness.
    model_paths = 0
    for case in chain_cases:
        payload = executions[case.case_id].artifacts["answer"].payload()
        cited = {citation["source_ref_id"] for citation in payload.get("citations", ())}
        if any(ref.startswith("MOD.") for ref in cited):
            model_paths += 1
    assert model_paths == 1

    chained = amendment.run_case(
        next(case for case in amendment.cases() if case.execution_mode == amendment.CHAIN)
    )
    assert chained.passed, chained.reasons
    assert any(ref for ref in chained.package_refs)

    assert AM1_R27_STATUS.startswith("DEFERRED")
