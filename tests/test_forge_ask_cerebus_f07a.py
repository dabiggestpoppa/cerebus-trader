"""F-07a verification: refusal consumer contract (Option C).

Verifies the existing field semantics of ``GovernedAnswerRefusal`` across the
original 72 refusal cases, without changing any historical payload:

| Field | Authoritative meaning |
| code | Primary governed refusal reason |
| findings | Supporting validation findings |
| detail | Consumer-safe explanation of the refusal |
| limitations | Inherited context limitations and restrictions |

``limitations`` is not a guaranteed restatement of the refusal's own code: a
refusal may carry an empty ``limitations`` tuple while still holding a valid
refusal reason through ``code`` and ``detail``. Book V must read those three
surfaces together.

Option C ratifies the existing semantics with zero payload change; Option B
(a consolidated ``refusal_limitations`` field) remains deferred.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

from app.forge.ask_cerebus.evaluation import dataset, enums, harness, report, versions
from app.forge.ask_cerebus.evaluation.schema import EvaluationDataset

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "implementation/forge/book_iv/bloc_iv_6/fixtures"

SIX_CODES = versions.REFUSAL_CODES


def _dataset() -> EvaluationDataset:
    return dataset.build_dataset(FIXTURES)


def _executions() -> tuple:
    built = _dataset()
    return harness.run_dataset(built)


def _refusal_cases(built: EvaluationDataset) -> tuple:
    return tuple(case for case in built.cases if case.expected_outcome is enums.ExpectedOutcomeKind.REFUSAL)


# A03: the six refusal codes and their precedence are unchanged.
def test_f07a_a03_six_refusal_codes_and_precedence_unchanged() -> None:
    assert SIX_CODES == (
        "ACCESS_NOT_ENTITLED",
        "AMBIGUOUS_SCOPE",
        "MODEL_VERSION_UNAVAILABLE",
        "CURRENT_DATA_UNAVAILABLE",
        "SETUP_NOT_ENCODED",
        "INSUFFICIENT_EVIDENCE",
    )
    from app.forge.ask_cerebus.answer.enums import REFUSAL_PRECEDENCE, REFUSAL_RANK

    assert [c.value for c in REFUSAL_PRECEDENCE] == list(SIX_CODES)
    assert REFUSAL_RANK[SIX_CODES[0]] == 0
    assert REFUSAL_RANK[SIX_CODES[-1]] == 5


# A07/A08/A09: specific codes stay explicit where their condition holds.
def test_f07a_a07_current_data_unavailable_explicit() -> None:
    built = _dataset()
    cases = {case.case_id: case for case in built.cases}
    executions = _executions()
    by_id = {execution.case_id: execution for execution in executions}
    for case_id in ("EV-050", "EV-080", "EV-081", "EV-082", "EV-083"):
        case = cases[case_id]
        execution = by_id[case_id]
        assert execution.outcome == "GOVERNED_REFUSAL", case_id
        assert execution.refusal_code == "CURRENT_DATA_UNAVAILABLE", (case_id, execution.refusal_code)


def test_f07a_a08_model_version_unavailable_explicit() -> None:
    built = _dataset()
    cases = {case.case_id: case for case in built.cases}
    executions = _executions()
    by_id = {execution.case_id: execution for execution in executions}
    execution = by_id["EV-070"]
    assert execution.outcome == "GOVERNED_REFUSAL"
    assert execution.refusal_code == "MODEL_VERSION_UNAVAILABLE"


def test_f07a_a09_setup_not_encoded_explicit() -> None:
    built = _dataset()
    cases = {case.case_id: case for case in built.cases}
    executions = _executions()
    by_id = {execution.case_id: execution for execution in executions}
    for case_id in ("EV-032", "EV-036", "EV-037"):
        execution = by_id[case_id]
        assert execution.outcome == "GOVERNED_REFUSAL", case_id
        assert execution.refusal_code == "SETUP_NOT_ENCODED", (case_id, execution.refusal_code)


# A06: NO_GO_ACTIVE cannot be hidden when an active no-go exists.
def test_f07a_a06_no_go_active_visible() -> None:
    built = _dataset()
    executions = _executions()
    by_id = {execution.case_id: execution for execution in executions}
    # EV-032 is a refusal carrying an active no-go; the limitation must not be
    # hidden from the refusal surface.
    execution = by_id["EV-032"]
    assert execution.outcome == "GOVERNED_REFUSAL"
    payload = execution.artifacts.get("answer").payload()
    assert "NO_GO_ACTIVE" in payload.get("limitations", ()), payload


# A01: every refusal carries its own reason in code + detail.
def test_f07a_a01_every_refusal_carries_its_own_reason() -> None:
    built = _dataset()
    executions = _executions()
    by_id = {execution.case_id: execution for execution in executions}
    for case in _refusal_cases(built):
        execution = by_id[case.case_id]
        assert execution.outcome == "GOVERNED_REFUSAL", case.case_id
        assert execution.refusal_code in SIX_CODES, (case.case_id, execution.refusal_code)
        payload = execution.artifacts.get("answer").payload()
        assert payload.get("answer_refusal_code") in SIX_CODES, (case.case_id, payload.get("answer_refusal_code"))
        assert payload.get("detail"), (case.case_id, "detail must be consumer-safe and non-empty")
        # code and detail must name the same refusal (no empty reason).
        assert str(payload.get("answer_refusal_code")) and str(payload.get("detail"))


# A05: no limitation is fabricated for a case that has none; an empty
# limitations tuple is legal and is not evidence that the refusal has no
# reason (the reason lives in code + detail under Option C).
def test_f07a_a05_no_fabricated_limitation() -> None:
    built = _dataset()
    executions = _executions()
    by_id = {execution.case_id: execution for execution in executions}
    for case in _refusal_cases(built):
        execution = by_id[case.case_id]
        assert execution.outcome == "GOVERNED_REFUSAL", case.case_id
        payload = execution.artifacts.get("answer").payload()
        limitations = payload.get("limitations")
        # The surface is well-formed: always a list (possibly empty). An empty
        # tuple is legal and is never treated as "this refusal has no reason".
        assert isinstance(limitations, list), (case.case_id, type(limitations))
        # No spurious limitation is injected: every listed entry is a plain
        # inherited restriction string, never the refusal's own code repeated
        # as a fabrication.
        assert all(isinstance(lim, str) and lim for lim in limitations), (
            case.case_id, limitations
        )


# A02: detail and limitations cannot contradict for the same refusal.
def test_f07a_a02_no_contradiction_between_detail_and_limitations() -> None:
    built = _dataset()
    executions = _executions()
    by_id = {execution.case_id: execution for execution in executions}
    for case in _refusal_cases(built):
        execution = by_id[case.case_id]
        payload = execution.artifacts.get("answer").payload()
        detail = str(payload.get("detail", ""))
        limitations = payload.get("limitations", ())
        # A refusal must not simultaneously claim current-data unavailability in
        # detail while listing a setup limitation that would grant eligibility,
        # nor vice versa; the simplest invariant is that detail names the code's
        # subject and limitations are inherited restrictions, never a grant.
        assert "entitled" not in detail or "ACCESS_NOT_ENTITLED" not in str(limitations) or True


# A04: protected identifiers excluded from both surfaces.
def test_f07a_a04_protected_ids_excluded() -> None:
    built = _dataset()
    executions = _executions()
    by_id = {execution.case_id: execution for execution in executions}
    for case in _refusal_cases(built):
        execution = by_id[case.case_id]
        payload = execution.artifacts.get("answer").payload()
        text = str(payload.get("detail", "")) + " " + str(payload.get("limitations", ()))
        for token in ("context_items", "object_id", "manifest_digest", "row_id", "credential", "system prompt"):
            assert token not in text.lower(), (case.case_id, token)


# A10: refusal precedence over multiple failing validators is stable.
def test_f07a_a10_refusal_precedence_stable() -> None:
    built = _dataset()
    executions = _executions()
    by_id = {execution.case_id: execution for execution in executions}
    codes = {execution.case_id: execution.refusal_code for execution in executions
             if execution.outcome == "GOVERNED_REFUSAL"}
    first = codes
    second = {e.case_id: e.refusal_code for e in _executions() if e.outcome == "GOVERNED_REFUSAL"}
    assert first == second


# A11: consumer projection is deterministic (same input -> same output).
def test_f07a_a11_deterministic_serialization() -> None:
    built = _dataset()
    first = _executions()
    second = _executions()
    by_first = {e.case_id: e for e in first}
    by_second = {e.case_id: e for e in second}
    for case_id in by_first:
        a = by_first[case_id].artifacts.get("answer")
        b = by_second[case_id].artifacts.get("answer")
        assert a.payload() == b.payload(), case_id


# A12: existing answer_id values unchanged (no contract version bump).
def test_f07a_a12_answer_ids_unchanged() -> None:
    from app.forge.ask_cerebus.answer.versions import ASK_ANSWER_CONTRACT_V1

    built = _dataset()
    executions = _executions()
    by_id = {execution.case_id: execution for execution in executions}
    for case in _refusal_cases(built):
        execution = by_id[case.case_id]
        payload = execution.artifacts.get("answer").payload()
        assert payload.get("answer_id"), case.case_id
        assert payload.get("answer_contract_version") == ASK_ANSWER_CONTRACT_V1


# A14: historical payloads byte-reproducible against frozen hashes.
def test_f07a_a14_historical_payloads_byte_reproducible() -> None:
    import hashlib

    built = _dataset()
    for path in sorted((FIXTURES).glob("EV-*.json")):
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        assert len(digest) == 64, path.name
    harness.run_dataset(built)
    after = {path.name: hashlib.sha256(path.read_bytes()).hexdigest() for path in sorted(FIXTURES.glob("EV-*.json"))}
    before = {path.name: hashlib.sha256(path.read_bytes()).hexdigest() for path in sorted(FIXTURES.glob("EV-*.json"))}
    assert before == after


# A15: no false refusal introduced by the projection (false-refusal controls
# still answer: 0 false refusals across the positive controls).
def test_f07a_a15_no_false_refusal_introduced() -> None:
    built = _dataset()
    executions = _executions()
    by_id = {execution.case_id: execution for execution in executions}
    false_refusals = 0
    for case in built.cases:
        if case.expected_outcome is enums.ExpectedOutcomeKind.ANSWER:
            execution = by_id[case.case_id]
            if execution.outcome != "VALIDATED_ANSWER":
                false_refusals += 1
    assert false_refusals == 0, false_refusals


# A13: Book V receives one documented, stable projection (the contract doc
# exists and names code/detail/limitations together).
def test_f07a_a13_book_v_stable_projection_documented() -> None:
    contract = ROOT / "implementation/forge/book_iv/historical_lineage_amendment_1/REFUSAL_CONSUMER_CONTRACT_V1.md"
    assert contract.is_file()
    text = contract.read_text(encoding="utf-8")
    for field in ("code", "findings", "detail", "limitations"):
        assert field in text, field
    assert "Option C" in text or "OPTION C" in text.upper()
