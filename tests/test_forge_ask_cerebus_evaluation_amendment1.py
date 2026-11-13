"""Security amendment 1 (BA-32) — AM1-R25, AM1-R26 and AM1-R27.

R25 reconciles the numerical populations without touching SCORING_V1. R26 makes
CHAIN evidence-path precision assertable, which the audit showed V1 never did.

R27 (cross-platform hash invariance) is implemented here under BA-33 after the
seventeen historical guards were moved onto the shared canonical helper. The
driver proves the repaired behaviour rather than two constant byte literals:
it re-derives every governed digest from canonical content, shows the identity
is invariant under a simulated opposite-encoding checkout, shows a one-byte
content change is still detected, keeps Git object identity distinct from
content identity, and then executes all seventeen guards in the running
environment.
"""

from __future__ import annotations

import hashlib
import json
import sys
from functools import lru_cache
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.forge.ask_cerebus.evaluation import amendment, dataset, harness, matching, scoring
from tests._support.canonical_bytes import (
    canonical_bytes,
    canonical_bytes_of,
    canonical_git_blob_sha1,
    canonical_sha256,
    committed_blob_id,
)

AM1_R27_STATUS = "PASS — BA-33 canonical hash repair"

#: Constants declared inline inside the historical guards (suffix-governed).
_INLINE_GUARDED = {
    "app/forge/ask_cerebus/interpreter/plan.py": "c43a34ba6ef085108743c2c87c1c1f13d85c134360a6e4e7f3067046f9fd344b",
    "app/forge/ask_cerebus/retrieval/bundle.py": "b38b356e01b349fe0110ce7ebd518fd1b3e9d1c82a7f8b979ac088019acc3455",
    "app/forge/ask_cerebus/retrieval/refs.py": "bbe1b937d6aa0bd7d0c26c8e0f7f5ba7dfa2ecee7f816dc9461b620d0961daa2",
    "app/forge/ask_cerebus/retrieval/trace.py": "6f8f08009da67975017de9c86263a52d0a72753afacf58f74aff7a91ec92e44d",
    "app/forge/ask_cerebus/retrieval/service.py": "2d73737e1a20f61e3ff276f16dee31e8e880304a6473754224d8a5ceb67b3535",
    "app/forge/policy.py": "f10751e6ba6144d807abc151dbcbd7a06320a3d1ab82279fe1cac26b8a228fcc",
    "app/forge/service/policy_enforcement.py": "9ccc3b72f77fca0cb3fd0685128fd96a2f0ce8ca975b532d96646d285476e381",
    "app/forge/intelligence_api/contracts.py": "7d8f90adf8aeca993b94d473f61fe16ea13170a1cd977cb47fb186d64697d4f0",
    "app/forge/service/routes.py": "145757e0f2b19e76e2274018075c4b0fa7f0642498d4580e7e5fa8ec33d190af",
    "app/forge/ask_cerebus/context/schema.py": "499dbdfb0054d6b1c7c41f61d6f91a2fdd15cad36346eb4297790e13b7cfc2c0",
    "app/forge/market_data/normalize.py": "9b7ea855a3a90994ae325c44af40898e842a6fbef838a6dc5490b5a505919c24",
    "app/forge/market_data/__init__.py": "94c88cd73abd03053ac2ba0b90ee95f7d204929e4206ffce04606fb111015f0f",
    "app/forge/market_data/instruments.py": "8c6d6ad05db973122265bca76ea6b3c0c3e248974fa26cb6409ef4cce67ed94d",
    "app/forge/market_data/bars.py": "97fc99e44c7abab0545a33e2b0fbf0b3d354ae5bae2b4c6e446ff3b336666366",
    "app/forge/market_data/quality.py": "6b77c6dfa11e6b22013b7f128e0d6b8095b5e035b660c93c309df220bcb58687",
    "app/forge/persistence/sql/001_initial_schema.sql": "d91c2ea2ec45de5f89f64b56acab80316339f68a53fd28a88c3c7ea0b7662f14",
}

_BASELINES = (
    "implementation/forge/book_iii/bloc_iii_5/fixtures/FROZEN_BASELINE.json",
)


@lru_cache(maxsize=1)
def governed_files() -> dict[str, str]:
    expected = dict(_INLINE_GUARDED)
    for relative in _BASELINES:
        baseline = json.loads((ROOT / relative).read_text(encoding="utf-8"))
        expected.update(baseline["files"])
    for relative in (
        "app/forge/ask_cerebus/llm_gateway/draft.py",
        "app/forge/ask_cerebus/llm_gateway/enums.py",
        "app/forge/ask_cerebus/llm_gateway/versions.py",
        "app/forge/ask_cerebus/context/enums.py",
        "app/forge/ask_cerebus/context/versions.py",
    ):
        expected.setdefault(relative, None)
    return expected


def _guard_callables() -> dict[str, object]:
    from tests import (
        test_forge_ask_cerebus_answer as iv5,
        test_forge_ask_cerebus_context as iv3,
        test_forge_ask_cerebus_gateway as iv4,
        test_forge_intelligence_api as iii_boundary,
        test_forge_market_data_provider_compatibility as md_compat,
        test_forge_market_data_provider_integration as md_integration,
        test_forge_policy as book_ii,
        test_forge_retrieval as book_i,
        test_forge_setup_engine as setup_engine,
    )

    return {
        "tests/test_forge_ask_cerebus_answer.py::test_a74_frozen_upstream_hashes_routes_and_migrations_unchanged": iv5.test_a74_frozen_upstream_hashes_routes_and_migrations_unchanged,
        "tests/test_forge_ask_cerebus_context.py::test_c87_frozen_iv1_plan_contract_unchanged": iv3.test_c87_frozen_iv1_plan_contract_unchanged,
        "tests/test_forge_ask_cerebus_context.py::test_c88_frozen_iv2_bundle_refs_trace_unchanged": iv3.test_c88_frozen_iv2_bundle_refs_trace_unchanged,
        "tests/test_forge_ask_cerebus_context.py::test_c89_frozen_book_i_ii_iii_contracts_unchanged": iv3.test_c89_frozen_book_i_ii_iii_contracts_unchanged,
        "tests/test_forge_ask_cerebus_context.py::test_c91_routes_migrations_and_provider_seam_unchanged": iv3.test_c91_routes_migrations_and_provider_seam_unchanged,
        "tests/test_forge_ask_cerebus_gateway.py::test_a55_same_golden_suite_runs_against_candidate_provider": iv4.test_a55_same_golden_suite_runs_against_candidate_provider,
        "tests/test_forge_ask_cerebus_gateway.py::test_a70_frozen_iv3_context_contract_unchanged": iv4.test_a70_frozen_iv3_context_contract_unchanged,
        "tests/test_forge_ask_cerebus_gateway.py::test_a71_routes_migrations_and_provider_seams_unchanged": iv4.test_a71_routes_migrations_and_provider_seams_unchanged,
        "tests/test_forge_intelligence_api.py::test_boundary_frozen_upstream_hashes_unchanged": iii_boundary.test_boundary_frozen_upstream_hashes_unchanged,
        "tests/test_forge_market_data_provider_compatibility.py::test_hash_record_updated": md_compat.test_hash_record_updated,
        "tests/test_forge_market_data_provider_compatibility.py::test_only_authorized_frozen_files_changed": md_compat.test_only_authorized_frozen_files_changed,
        "tests/test_forge_market_data_provider_compatibility.py::test_wp3b_contract_suite_green": md_compat.test_wp3b_contract_suite_green,
        "tests/test_forge_market_data_provider_integration.py::test_routes_hash_unchanged": md_integration.test_routes_hash_unchanged,
        "tests/test_forge_policy.py::TestScopeGuards::test_001_and_002_unchanged": book_ii.TestScopeGuards().test_001_and_002_unchanged,
        "tests/test_forge_retrieval.py::TestInternalMaterial::test_policy_module_is_untouched": book_i.TestInternalMaterial().test_policy_module_is_untouched,
        "tests/test_forge_setup_engine.py::TestT12Boundaries::test_cross_platform_hash_stability": setup_engine.TestT12Boundaries().test_cross_platform_hash_stability,
        "tests/test_forge_setup_engine.py::TestT12Boundaries::test_frozen_upstream_hashes_unchanged": setup_engine.TestT12Boundaries().test_frozen_upstream_hashes_unchanged,
    }


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


def test_am1_r27_hash_guards_are_checkout_encoding_invariant():
    # 1. All seventeen historical guards exist and are wired to the helper.
    guards = _guard_callables()
    assert len(guards) == 17
    for test_id, guard in guards.items():
        module = sys.modules[guard.__self__.__class__.__module__] if hasattr(guard, "__self__") else sys.modules[guard.__module__]
        assert "canonical_bytes" in Path(module.__file__).read_text(encoding="utf-8"), test_id

    # 2. Every governed digest re-derives from canonical content, never from the
    #    incidental encoding this checkout happens to use.
    expected = governed_files()
    assert len(expected) >= 60
    for relative, digest in expected.items():
        if digest is None:
            continue
        data = canonical_bytes(ROOT / relative)
        assert hashlib.sha256(data).hexdigest() == digest, relative

        # 3. Opposite-encoding invariance, proven per file rather than declared.
        if b"\n" in data:
            opposite = data.replace(b"\n", b"\r\n")
            assert canonical_bytes_of(opposite) == data, relative
            assert hashlib.sha256(opposite).hexdigest() != digest, relative

        # 4. A genuine one-byte content change is still detected.
        mutated = bytearray(data)
        mutated[0] = 0x23 if mutated[0] != 0x23 else 0x24
        assert hashlib.sha256(bytes(mutated)).hexdigest() != digest, relative

    # 5. Git object identity is not the content identity, and the sanctioned
    #    bridge between them holds for committed-as-is content.
    routes = ROOT / "app/forge/service/routes.py"
    assert committed_blob_id(routes) == canonical_git_blob_sha1(routes)
    assert canonical_sha256(routes) != committed_blob_id(routes)

    # 6. All seventeen guards actually execute and pass in this environment.
    failures = []
    for test_id, guard in guards.items():
        try:
            guard()
        except AssertionError as exc:  # pragma: no cover - reported below
            failures.append(f"{test_id}: {exc}")
    assert failures == [], failures
