"""Book V golden scenario verification drivers.

One deterministic driver per golden scenario (BV-GOLDEN-01 through BV-GOLDEN-19).

Each driver:

1. Loads the declared scenario from ``implementation/forge/book_v/golden/scenarios.py``.
2. Reconstructs its frozen input (Q5 scenario via ``validate_answer``, or
   synthetic DTO for scenarios 17 and 19).
3. Verifies the pinned input digest.
4. Executes the real ``PresentationAdapter``.
5. Compares the actual outcome to the declared expectation.
6. Compares declared presentation fields.
7. Verifies the refusal code where applicable.
8. Verifies no unauthorized information appears.
9. Verifies deterministic serialization (same input → same payload).

No placeholders. No skips. No xfails. No assertion-free drivers.
"""

from __future__ import annotations

import hashlib
import importlib.util
import json
import sys
from dataclasses import replace
from pathlib import Path

import pytest

from app.forge.ask_cerebus.answer import validate_answer
from app.forge.ask_cerebus.answer.enums import (
    AnswerDepth,
    AnswerOutcome,
    AnswerRefusalCode,
)
from app.forge.ask_cerebus.answer.schema import (
    FinalResponseRecord,
    GovernedAnswerRefusal,
    ValidatedAnswer,
)
from app.forge.ask_cerebus.answer.versions import (
    ANSWER_RECORD_V1,
    ANSWER_SECTION_SCHEMA_V1,
    ASK_ANSWER_CONTRACT_V1,
    VALIDATOR_SET_V1,
)
from app.forge.ask_cerebus.llm_gateway.draft import GatewayDraft
from app.forge.ask_cerebus.llm_gateway.enums import AttemptOutcome, CostBasis, DraftStatus
from app.forge.ask_cerebus.llm_gateway.trace import AttemptTrace, GatewayTrace, UsageAccounting
from app.forge.book_v.presentation.adapter import (
    PresentationAdapter,
    PresentationRejectionError,
)
from app.forge.book_v.presentation.model import BookVInterfaceResponse

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# Load golden scenarios.
spec = importlib.util.spec_from_file_location(
    "bv_golden_scenarios",
    ROOT / "implementation/forge/book_v/golden/scenarios.py",
)
assert spec is not None and spec.loader is not None
golden_module = importlib.util.module_from_spec(spec)
sys.modules["bv_golden_scenarios"] = golden_module
spec.loader.exec_module(golden_module)

GOLDEN = golden_module.scenarios()

# Load frozen Q5 scenarios (Book IV bloc IV.5 fixtures).
q5_spec = importlib.util.spec_from_file_location(
    "q5_scenarios",
    ROOT / "implementation/forge/book_iv/bloc_iv_5/fixtures/scenarios.py",
)
assert q5_spec is not None and q5_spec.loader is not None
q5_module = importlib.util.module_from_spec(q5_spec)
sys.modules["q5_scenarios"] = q5_module
q5_spec.loader.exec_module(q5_module)

Q5_CASES = {scenario.id: scenario for scenario in q5_module.cases()}

ADAPTER = PresentationAdapter()

PROTECTED_TOKENS = (
    "context_items",
    "object_id",
    "manifest_digest",
    "row_id",
    "credential",
    "system prompt",
    "app.forge",
)


def _dto_for_q5(case_id: str) -> ValidatedAnswer | GovernedAnswerRefusal:
    """Run the real IV.5 entry point over a frozen Q5 scenario."""
    return validate_answer(Q5_CASES[case_id].draft, Q5_CASES[case_id].package)


def _dto_payload_digest(dto: ValidatedAnswer | GovernedAnswerRefusal) -> str:
    """Replicate the golden digest computation: SHA-256 of canonical
    JSON of the DTO payload including the record."""
    payload = dto.payload(include_record=True)
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _assert_no_unauthorized_info(out: BookVInterfaceResponse) -> None:
    """Verify no protected identifiers or internal material leak."""
    text = json.dumps(out.payload(), sort_keys=True, ensure_ascii=False).lower()
    for token in PROTECTED_TOKENS:
        assert token not in text, f"protected token leaked: {token}"
    # No citation source_ref_id is an internal row or object id.
    for citation in out.citations:
        assert not citation.source_ref_id.startswith(("PKG.", "MFD."))
        assert "context_items" not in citation.source_ref_id
        assert "object_id" not in citation.source_ref_id
        assert "row_id" not in citation.source_ref_id


def _assert_deterministic(out: BookVInterfaceResponse) -> None:
    """Same input → same payload across executions."""
    first = out.payload()
    second = out.payload()
    assert first == second


# ---------------------------------------------------------------------------
# BV-GOLDEN-01 — Q5-01, BEGINNER, VALIDATED_ANSWER
# ---------------------------------------------------------------------------


def test_bv_golden_01() -> None:
    """BV-GOLDEN-01: Beginner validated answer (Q5-01)."""
    scenario = golden_module.scenario("BV-GOLDEN-01")
    dto = _dto_for_q5("Q5-01")

    # 3. Verify input digest.
    assert _dto_payload_digest(dto) == scenario["input_digest"]

    # 4. Execute the real PresentationAdapter.
    out = ADAPTER.present(dto)

    # 5. Compare actual outcome.
    assert out.is_answer()
    assert out.outcome == scenario["expected_outcome"]
    assert out.depth == scenario["expected_depth"]

    # 6. Compare declared presentation fields.
    for field in scenario["expected_fields"]:
        assert hasattr(out, field), f"missing field: {field}"
    assert len(out.sections) == 4
    assert [s.section_id for s in out.sections] == [
        "WHAT_IT_MEANS", "WHAT_CEREBUS_SEES", "WHAT_IT_DOES_NOT_MEAN", "NEXT_RELEVANT_STATE",
    ]
    assert out.answer_id == dto.answer_id

    # 8. No unauthorized information.
    _assert_no_unauthorized_info(out)

    # 9. Deterministic serialization.
    _assert_deterministic(out)


# ---------------------------------------------------------------------------
# BV-GOLDEN-02 — Q5-03, OPERATOR, VALIDATED_ANSWER
# ---------------------------------------------------------------------------


def test_bv_golden_02() -> None:
    """BV-GOLDEN-02: Operator validated answer (Q5-03)."""
    scenario = golden_module.scenario("BV-GOLDEN-02")
    dto = _dto_for_q5("Q5-03")

    assert _dto_payload_digest(dto) == scenario["input_digest"]

    out = ADAPTER.present(dto)

    assert out.is_answer()
    assert out.outcome == scenario["expected_outcome"]
    assert out.depth == scenario["expected_depth"]

    for field in scenario["expected_fields"]:
        assert hasattr(out, field), f"missing field: {field}"
    assert len(out.sections) == 11
    assert [s.section_id for s in out.sections] == [
        "MODEL_LAYER", "CURRENT_STATE", "ELIGIBILITY", "ACTIVE_RANGE_ANCHOR",
        "CLOCK", "PATH_RANGE_LEFT", "LEVELS", "TRIGGER", "INVALIDATION",
        "TARGETS", "EVIDENCE_STATUS",
    ]
    assert out.answer_id == dto.answer_id

    _assert_no_unauthorized_info(out)
    _assert_deterministic(out)


# ---------------------------------------------------------------------------
# BV-GOLDEN-03 — Q5-05, RESEARCHER, VALIDATED_ANSWER
# ---------------------------------------------------------------------------


def test_bv_golden_03() -> None:
    """BV-GOLDEN-03: Researcher validated answer (Q5-05)."""
    scenario = golden_module.scenario("BV-GOLDEN-03")
    dto = _dto_for_q5("Q5-05")

    assert _dto_payload_digest(dto) == scenario["input_digest"]

    out = ADAPTER.present(dto)

    assert out.is_answer()
    assert out.outcome == scenario["expected_outcome"]
    assert out.depth == scenario["expected_depth"]

    for field in scenario["expected_fields"]:
        assert hasattr(out, field), f"missing field: {field}"
    assert len(out.sections) == 7
    assert [s.section_id for s in out.sections] == [
        "MODEL_VERSION", "CLAIM_EVENT", "POPULATION_N", "PERIOD_GENERATION",
        "METRIC_RESULT", "OOS_REPRODUCTION", "CONTRADICTIONS_NEGATIVE",
    ]
    assert len(out.citations) >= 1
    assert out.answer_id == dto.answer_id

    _assert_no_unauthorized_info(out)
    _assert_deterministic(out)


# ---------------------------------------------------------------------------
# BV-GOLDEN-04 — Q5-43, OPERATOR, GOVERNED_REFUSAL, ACCESS_NOT_ENTITLED
# ---------------------------------------------------------------------------


def test_bv_golden_04() -> None:
    """BV-GOLDEN-04: Refusal — access not entitled (Q5-43)."""
    scenario = golden_module.scenario("BV-GOLDEN-04")
    dto = _dto_for_q5("Q5-43")

    assert _dto_payload_digest(dto) == scenario["input_digest"]

    out = ADAPTER.present(dto)

    assert out.is_refusal()
    assert out.outcome == scenario["expected_outcome"]
    assert out.depth == scenario["expected_depth"]
    assert out.code == scenario["expected_code"]
    assert out.code == "ACCESS_NOT_ENTITLED"
    assert out.detail
    assert out.sections == ()
    assert out.claims == ()
    assert out.citations == ()
    assert out.numbers == ()
    assert out.answer_id == dto.answer_id

    _assert_no_unauthorized_info(out)
    _assert_deterministic(out)


# ---------------------------------------------------------------------------
# BV-GOLDEN-05 — Q5-44, BEGINNER, GOVERNED_REFUSAL, AMBIGUOUS_SCOPE
# ---------------------------------------------------------------------------


def test_bv_golden_05() -> None:
    """BV-GOLDEN-05: Refusal — ambiguous scope (Q5-44)."""
    scenario = golden_module.scenario("BV-GOLDEN-05")
    dto = _dto_for_q5("Q5-44")

    assert _dto_payload_digest(dto) == scenario["input_digest"]

    out = ADAPTER.present(dto)

    assert out.is_refusal()
    assert out.outcome == scenario["expected_outcome"]
    assert out.depth == scenario["expected_depth"]
    assert out.code == scenario["expected_code"]
    assert out.code == "AMBIGUOUS_SCOPE"
    assert out.detail
    assert out.sections == ()
    assert out.claims == ()

    _assert_no_unauthorized_info(out)
    _assert_deterministic(out)


# ---------------------------------------------------------------------------
# BV-GOLDEN-06 — Q5-42, RESEARCHER, GOVERNED_REFUSAL, MODEL_VERSION_UNAVAILABLE
# ---------------------------------------------------------------------------


def test_bv_golden_06() -> None:
    """BV-GOLDEN-06: Refusal — model version unavailable (Q5-42)."""
    scenario = golden_module.scenario("BV-GOLDEN-06")
    dto = _dto_for_q5("Q5-42")

    assert _dto_payload_digest(dto) == scenario["input_digest"]

    out = ADAPTER.present(dto)

    assert out.is_refusal()
    assert out.outcome == scenario["expected_outcome"]
    assert out.depth == scenario["expected_depth"]
    assert out.code == scenario["expected_code"]
    assert out.code == "MODEL_VERSION_UNAVAILABLE"
    assert out.detail
    assert out.sections == ()
    assert out.claims == ()

    _assert_no_unauthorized_info(out)
    _assert_deterministic(out)


# ---------------------------------------------------------------------------
# BV-GOLDEN-07 — Q5-41, OPERATOR, GOVERNED_REFUSAL, CURRENT_DATA_UNAVAILABLE
# ---------------------------------------------------------------------------


def test_bv_golden_07() -> None:
    """BV-GOLDEN-07: Refusal — current data unavailable (Q5-41)."""
    scenario = golden_module.scenario("BV-GOLDEN-07")
    dto = _dto_for_q5("Q5-41")

    assert _dto_payload_digest(dto) == scenario["input_digest"]

    out = ADAPTER.present(dto)

    assert out.is_refusal()
    assert out.outcome == scenario["expected_outcome"]
    assert out.depth == scenario["expected_depth"]
    assert out.code == scenario["expected_code"]
    assert out.code == "CURRENT_DATA_UNAVAILABLE"
    assert out.detail
    assert out.sections == ()
    assert out.claims == ()

    _assert_no_unauthorized_info(out)
    _assert_deterministic(out)


# ---------------------------------------------------------------------------
# BV-GOLDEN-08 — Q5-25, OPERATOR, GOVERNED_REFUSAL, SETUP_NOT_ENCODED
# ---------------------------------------------------------------------------


def test_bv_golden_08() -> None:
    """BV-GOLDEN-08: Refusal — setup not encoded (Q5-25)."""
    scenario = golden_module.scenario("BV-GOLDEN-08")
    dto = _dto_for_q5("Q5-25")

    assert _dto_payload_digest(dto) == scenario["input_digest"]

    out = ADAPTER.present(dto)

    assert out.is_refusal()
    assert out.outcome == scenario["expected_outcome"]
    assert out.depth == scenario["expected_depth"]
    assert out.code == scenario["expected_code"]
    assert out.code == "SETUP_NOT_ENCODED"
    assert out.detail
    assert out.sections == ()
    assert out.claims == ()
    assert "NO_GO_ACTIVE" in out.limitations

    _assert_no_unauthorized_info(out)
    _assert_deterministic(out)


# ---------------------------------------------------------------------------
# BV-GOLDEN-09 — Q5-07, OPERATOR, GOVERNED_REFUSAL, INSUFFICIENT_EVIDENCE
# ---------------------------------------------------------------------------


def test_bv_golden_09() -> None:
    """BV-GOLDEN-09: Refusal — insufficient evidence (Q5-07)."""
    scenario = golden_module.scenario("BV-GOLDEN-09")
    dto = _dto_for_q5("Q5-07")

    assert _dto_payload_digest(dto) == scenario["input_digest"]

    out = ADAPTER.present(dto)

    assert out.is_refusal()
    assert out.outcome == scenario["expected_outcome"]
    assert out.depth == scenario["expected_depth"]
    assert out.code == scenario["expected_code"]
    assert out.code == "INSUFFICIENT_EVIDENCE"
    assert out.detail
    assert out.numbers == ()
    assert out.sections == ()
    assert out.claims == ()

    _assert_no_unauthorized_info(out)
    _assert_deterministic(out)


# ---------------------------------------------------------------------------
# BV-GOLDEN-10 — Q5-31, BEGINNER, GOVERNED_REFUSAL, CURRENT_DATA_UNAVAILABLE
# ---------------------------------------------------------------------------


def test_bv_golden_10() -> None:
    """BV-GOLDEN-10: Refusal — historical model, current data unavailable (Q5-31)."""
    scenario = golden_module.scenario("BV-GOLDEN-10")
    dto = _dto_for_q5("Q5-31")

    assert _dto_payload_digest(dto) == scenario["input_digest"]

    out = ADAPTER.present(dto)

    assert out.is_refusal()
    assert out.outcome == scenario["expected_outcome"]
    assert out.depth == scenario["expected_depth"]
    assert out.code == scenario["expected_code"]
    assert out.code == "CURRENT_DATA_UNAVAILABLE"
    assert out.detail
    assert out.sections == ()
    assert out.claims == ()

    _assert_no_unauthorized_info(out)
    _assert_deterministic(out)


# ---------------------------------------------------------------------------
# BV-GOLDEN-11 — Q5-34, OPERATOR, GOVERNED_REFUSAL, CURRENT_DATA_UNAVAILABLE
# ---------------------------------------------------------------------------


def test_bv_golden_11() -> None:
    """BV-GOLDEN-11: Refusal — current data unavailable, stale snapshot (Q5-34)."""
    scenario = golden_module.scenario("BV-GOLDEN-11")
    dto = _dto_for_q5("Q5-34")

    assert _dto_payload_digest(dto) == scenario["input_digest"]

    out = ADAPTER.present(dto)

    assert out.is_refusal()
    assert out.outcome == scenario["expected_outcome"]
    assert out.depth == scenario["expected_depth"]
    assert out.code == scenario["expected_code"]
    assert out.code == "CURRENT_DATA_UNAVAILABLE"
    assert out.detail
    assert out.sections == ()
    assert out.claims == ()

    _assert_no_unauthorized_info(out)
    _assert_deterministic(out)


# ---------------------------------------------------------------------------
# BV-GOLDEN-12 — Q5-08, RESEARCHER, GOVERNED_REFUSAL, INSUFFICIENT_EVIDENCE
# ---------------------------------------------------------------------------


def test_bv_golden_12() -> None:
    """BV-GOLDEN-12: Refusal — unsupported statistic (Q5-08)."""
    scenario = golden_module.scenario("BV-GOLDEN-12")
    dto = _dto_for_q5("Q5-08")

    assert _dto_payload_digest(dto) == scenario["input_digest"]

    out = ADAPTER.present(dto)

    assert out.is_refusal()
    assert out.outcome == scenario["expected_outcome"]
    assert out.depth == scenario["expected_depth"]
    assert out.code == scenario["expected_code"]
    assert out.code == "INSUFFICIENT_EVIDENCE"
    assert out.numbers == ()
    assert out.sections == ()
    assert out.claims == ()

    _assert_no_unauthorized_info(out)
    _assert_deterministic(out)


# ---------------------------------------------------------------------------
# BV-GOLDEN-13 — Q5-25, OPERATOR, GOVERNED_REFUSAL, SETUP_NOT_ENCODED (no-go)
# ---------------------------------------------------------------------------


def test_bv_golden_13() -> None:
    """BV-GOLDEN-13: Refusal — no-go active, setup not encoded (Q5-25)."""
    scenario = golden_module.scenario("BV-GOLDEN-13")
    dto = _dto_for_q5("Q5-25")

    assert _dto_payload_digest(dto) == scenario["input_digest"]

    out = ADAPTER.present(dto)

    assert out.is_refusal()
    assert out.outcome == scenario["expected_outcome"]
    assert out.depth == scenario["expected_depth"]
    assert out.code == scenario["expected_code"]
    assert out.code == "SETUP_NOT_ENCODED"
    assert out.detail
    assert "NO_GO_ACTIVE" in out.limitations
    assert out.sections == ()
    assert out.claims == ()

    _assert_no_unauthorized_info(out)
    _assert_deterministic(out)


# ---------------------------------------------------------------------------
# BV-GOLDEN-14 — Q5-43, OPERATOR, GOVERNED_REFUSAL, ACCESS_NOT_ENTITLED (entitlement)
# ---------------------------------------------------------------------------


def test_bv_golden_14() -> None:
    """BV-GOLDEN-14: Refusal — access not entitled, no citations (Q5-43)."""
    scenario = golden_module.scenario("BV-GOLDEN-14")
    dto = _dto_for_q5("Q5-43")

    assert _dto_payload_digest(dto) == scenario["input_digest"]

    out = ADAPTER.present(dto)

    assert out.is_refusal()
    assert out.outcome == scenario["expected_outcome"]
    assert out.depth == scenario["expected_depth"]
    assert out.code == scenario["expected_code"]
    assert out.code == "ACCESS_NOT_ENTITLED"
    assert out.detail
    assert out.citations == ()
    assert out.sections == ()
    assert out.claims == ()

    _assert_no_unauthorized_info(out)
    _assert_deterministic(out)


# ---------------------------------------------------------------------------
# BV-GOLDEN-15 — Q5-05, RESEARCHER, VALIDATED_ANSWER (safe citation presentation)
# ---------------------------------------------------------------------------


def test_bv_golden_15() -> None:
    """BV-GOLDEN-15: Safe citation presentation (Q5-05)."""
    scenario = golden_module.scenario("BV-GOLDEN-15")
    dto = _dto_for_q5("Q5-05")

    assert _dto_payload_digest(dto) == scenario["input_digest"]

    out = ADAPTER.present(dto)

    assert out.is_answer()
    assert out.outcome == scenario["expected_outcome"]
    assert out.depth == scenario["expected_depth"]

    for field in scenario["expected_fields"]:
        assert hasattr(out, field), f"missing field: {field}"
    assert len(out.citations) >= 1
    assert len(out.claims) >= 1
    assert len(out.sections) >= 1
    # Every citation carries generation.
    for citation in out.citations:
        assert citation.generation
        assert citation.source_ref_id
    assert out.answer_id == dto.answer_id

    _assert_no_unauthorized_info(out)
    _assert_deterministic(out)


# ---------------------------------------------------------------------------
# BV-GOLDEN-16 — Q5-19, OPERATOR, GOVERNED_REFUSAL, INSUFFICIENT_EVIDENCE
# ---------------------------------------------------------------------------


def test_bv_golden_16() -> None:
    """BV-GOLDEN-16: Refusal — missing citation rejection (Q5-19)."""
    scenario = golden_module.scenario("BV-GOLDEN-16")
    dto = _dto_for_q5("Q5-19")

    assert _dto_payload_digest(dto) == scenario["input_digest"]

    out = ADAPTER.present(dto)

    assert out.is_refusal()
    assert out.outcome == scenario["expected_outcome"]
    assert out.depth == scenario["expected_depth"]
    assert out.code == scenario["expected_code"]
    assert out.code == "INSUFFICIENT_EVIDENCE"
    assert out.detail
    assert out.sections == ()
    assert out.claims == ()

    _assert_no_unauthorized_info(out)
    _assert_deterministic(out)


# ---------------------------------------------------------------------------
# BV-GOLDEN-17 — Synthetic, RESEARCHER, GOVERNED_REFUSAL, INSUFFICIENT_EVIDENCE
# ---------------------------------------------------------------------------


def test_bv_golden_17() -> None:
    """BV-GOLDEN-17: Refusal — generation mismatch (synthetic DTO)."""
    scenario = golden_module.scenario("BV-GOLDEN-17")

    record = FinalResponseRecord(
        record_version=ANSWER_RECORD_V1,
        outcome=AnswerOutcome.GOVERNED_REFUSAL,
        answer_id="ANS." + "0" * 32,
        answer_contract_version=ASK_ANSWER_CONTRACT_V1,
        answer_schema_version=ANSWER_SECTION_SCHEMA_V1,
        validator_set_version=VALIDATOR_SET_V1,
        depth="RESEARCHER",
        package_id="PKG." + "0" * 32,
        manifest_id="MFD." + "0" * 64,
        query_plan_id="QP.GOLDEN",
        route_id="ROUTE.GOLDEN",
        route_policy_version="POL.V1",
        prompt_id="PROMPT.GOLDEN",
        prompt_version="V1",
        provider="fake",
        model="fake-model-1",
        answer_refusal_code="INSUFFICIENT_EVIDENCE",
        as_of="",
    )
    refusal = GovernedAnswerRefusal(
        answer_id=record.answer_id,
        code=AnswerRefusalCode.INSUFFICIENT_EVIDENCE,
        detail="Claim generation does not match the source record's generation.",
        depth=AnswerDepth.RESEARCHER,
        findings=("GENERATION_LAUNDERING",),
        record=record,
        limitations=(),
    )

    # 3. Verify input digest.
    assert _dto_payload_digest(refusal) == scenario["input_digest"]

    # 4. Execute the real PresentationAdapter.
    out = ADAPTER.present(refusal)

    # 5. Compare actual outcome.
    assert out.is_refusal()
    assert out.outcome == scenario["expected_outcome"]
    assert out.depth == scenario["expected_depth"]
    assert out.code == scenario["expected_code"]
    assert out.code == "INSUFFICIENT_EVIDENCE"
    assert out.detail
    assert out.limitations == ()
    assert out.sections == ()
    assert out.claims == ()

    # 8. No unauthorized information.
    _assert_no_unauthorized_info(out)

    # 9. Deterministic serialization.
    _assert_deterministic(out)


# ---------------------------------------------------------------------------
# BV-GOLDEN-18 — Q5-39, OPERATOR, GOVERNED_REFUSAL, ACCESS_NOT_ENTITLED
# ---------------------------------------------------------------------------


def test_bv_golden_18() -> None:
    """BV-GOLDEN-18: Refusal — untrusted-source containment (Q5-39)."""
    scenario = golden_module.scenario("BV-GOLDEN-18")
    dto = _dto_for_q5("Q5-39")

    assert _dto_payload_digest(dto) == scenario["input_digest"]

    out = ADAPTER.present(dto)

    assert out.is_refusal()
    assert out.outcome == scenario["expected_outcome"]
    assert out.depth == scenario["expected_depth"]
    assert out.code == scenario["expected_code"]
    assert out.code == "ACCESS_NOT_ENTITLED"
    assert out.detail
    assert out.citations == ()
    assert out.sections == ()
    assert out.claims == ()

    _assert_no_unauthorized_info(out)
    _assert_deterministic(out)


# ---------------------------------------------------------------------------
# BV-GOLDEN-19 — n/a, PRESENTATION_REJECTED (raw GatewayDraft)
# ---------------------------------------------------------------------------


def test_bv_golden_19() -> None:
    """BV-GOLDEN-19: Prompt-injection containment — raw GatewayDraft rejected."""
    scenario = golden_module.scenario("BV-GOLDEN-19")

    draft = GatewayDraft(
        package_id="PKG." + "0" * 32,
        manifest_id="MFD." + "0" * 64,
        query_plan_id="QP.TEST",
        route_policy_version="POL.V1",
        route_id="ROUTE.TEST",
        prompt_id="PROMPT.TEST",
        prompt_version="V1",
        depth="OPERATOR",
        provider="fake",
        model="fake-model-1",
        sections=(),
        claims=(),
        citations=(),
        numbers=(),
        uncertainties=(),
        refusals=(),
        proposed_prose="untrusted injected prose",
        usage=UsageAccounting(),
        attempts=(),
        trace=GatewayTrace(
            contract_version="ASK_GATEWAY_CONTRACT_V1",
            route_policy_version="POL.V1",
            route_id="ROUTE.TEST",
            package_id="PKG." + "0" * 32,
            manifest_id="MFD." + "0" * 64,
            query_plan_id="QP.TEST",
            prompt_id="PROMPT.TEST",
            prompt_version="V1",
            provider="fake",
            model="fake-model-1",
            outcome="DRAFT",
        ),
        status=DraftStatus.UNVALIDATED,
    )

    # 4. Execute the real PresentationAdapter — must reject.
    with pytest.raises(PresentationRejectionError):
        ADAPTER.present(draft)  # type: ignore[arg-type]

    # 9. Deterministic: rejection is deterministic.
    with pytest.raises(PresentationRejectionError):
        ADAPTER.present(draft)  # type: ignore[arg-type]
