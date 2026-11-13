"""Adversarial presentation boundary tests.

Tests the PresentationAdapter against inputs that attempt to cross security
trust boundaries. Determines which cases are prevented by upstream immutable
schemas versus which require presentation-boundary checks.

Cases already prevented by upstream (frozen dataclasses, IV.5 validation):
- Unexpected extra fields (frozen dataclass, no __dict__)
- Malformed citation structure (CitationRef requires all fields)
- Missing answer identity (answer_id is required on DTOs)
- Contradictory status labels (IV.5 validates epistemic labels match source)

Cases requiring presentation-boundary checks:
- Raw GatewayDraft input rejected
- Non-DTO types rejected
- Historical labels preserved (never upgraded to CANONICAL/VALIDATED)
- Empty limitations preserved (never synthesized)
- No fields added by adapter (pure pass-through)
- Answer never becomes refusal; refusal never becomes answer
- Deterministic serialization under repeated execution
- No internal provider/retrieval material in projected record
"""

from __future__ import annotations

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
from app.forge.ask_cerebus.llm_gateway.enums import (
    AttemptOutcome,
    CostBasis,
    DraftStatus,
)
from app.forge.ask_cerebus.llm_gateway.trace import (
    AttemptTrace,
    GatewayTrace,
    UsageAccounting,
)
from app.forge.book_v.presentation.adapter import (
    PresentationAdapter,
    PresentationRejectionError,
)
from app.forge.book_v.presentation.model import BookVInterfaceResponse

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import importlib.util

spec = importlib.util.spec_from_file_location(
    "q5_scenarios_adv",
    ROOT / "implementation/forge/book_iv/bloc_iv_5/fixtures/scenarios.py",
)
assert spec is not None and spec.loader is not None
q5_module = importlib.util.module_from_spec(spec)
sys.modules["q5_scenarios_adv"] = q5_module
spec.loader.exec_module(q5_module)

Q5_CASES = {scenario.id: scenario for scenario in q5_module.cases()}

ADAPTER = PresentationAdapter()


def _dto(case_id: str) -> ValidatedAnswer | GovernedAnswerRefusal:
    return validate_answer(Q5_CASES[case_id].draft, Q5_CASES[case_id].package)


def _make_draft() -> GatewayDraft:
    return GatewayDraft(
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


def _record(*, outcome: AnswerOutcome, answer_id: str, depth: str,
            refusal_code: AnswerRefusalCode | None = None) -> FinalResponseRecord:
    return FinalResponseRecord(
        record_version=ANSWER_RECORD_V1,
        outcome=outcome,
        answer_id=answer_id,
        answer_contract_version=ASK_ANSWER_CONTRACT_V1,
        answer_schema_version=ANSWER_SECTION_SCHEMA_V1,
        validator_set_version=VALIDATOR_SET_V1,
        depth=depth,
        package_id="PKG." + "0" * 32,
        manifest_id="MFD." + "0" * 64,
        query_plan_id="QP.TEST",
        route_id="ROUTE.TEST",
        route_policy_version="POL.V1",
        prompt_id="PROMPT.TEST",
        prompt_version="V1",
        provider="fake",
        model="fake-model-1",
        answer_refusal_code=refusal_code.value if refusal_code else "",
        as_of="",
    )


# ---------------------------------------------------------------------------
# 1. Raw GatewayDraft input rejected
# ---------------------------------------------------------------------------


def test_adversarial_raw_gateway_draft_rejected() -> None:
    """A raw GatewayDraft (provider output) must never reach the UI."""
    with pytest.raises(PresentationRejectionError):
        ADAPTER.present(_make_draft())  # type: ignore[arg-type]


# ---------------------------------------------------------------------------
# 2. Non-DTO types rejected
# ---------------------------------------------------------------------------


def test_adversarial_non_dto_types_rejected() -> None:
    """Any input that is not a ValidatedAnswer or GovernedAnswerRefusal is
    rejected deterministically."""
    for bad in (None, "string", 42, ["list"], {"dict": 1}, _make_draft()):
        with pytest.raises(PresentationRejectionError):
            ADAPTER.present(bad)  # type: ignore[arg-type]


# ---------------------------------------------------------------------------
# 3. Historical labels preserved (never upgraded)
# ---------------------------------------------------------------------------


def test_adversarial_historical_labels_preserved() -> None:
    """Q5-06 carries NEGATIVE_EVIDENCE epistemic labels. The adapter must
    preserve them verbatim and never upgrade them to CANONICAL or VALIDATED."""
    answer = ADAPTER.present(_dto("Q5-06"))
    assert answer.is_answer()
    labels = {claim.epistemic_label for claim in answer.claims}
    assert "NEGATIVE_EVIDENCE" in labels
    for claim in answer.claims:
        assert claim.epistemic_label in ("VALIDATED", "NEGATIVE_EVIDENCE")
        assert claim.epistemic_label not in ("CANONICAL", "FORWARD_OOS")

    # Q5-31 is a refusal for a HISTORICAL model — the refusal is preserved,
    # never converted to an answer.
    out = ADAPTER.present(_dto("Q5-31"))
    assert out.is_refusal()
    assert out.code == "CURRENT_DATA_UNAVAILABLE"


# ---------------------------------------------------------------------------
# 4. Empty limitations preserved (never synthesized)
# ---------------------------------------------------------------------------


def test_adversarial_empty_limitations_preserved() -> None:
    """A refusal with an empty limitations tuple must keep it empty. The
    adapter must not synthesize limitations."""
    record = _record(
        outcome=AnswerOutcome.GOVERNED_REFUSAL,
        answer_id="ANS." + "0" * 32,
        depth="OPERATOR",
        refusal_code=AnswerRefusalCode.ACCESS_NOT_ENTITLED,
    )
    refusal = GovernedAnswerRefusal(
        answer_id=record.answer_id,
        code=AnswerRefusalCode.ACCESS_NOT_ENTITLED,
        detail="The requested scope is not entitled.",
        depth=AnswerDepth.OPERATOR,
        findings=("ACCESS_NOT_ENTITLED",),
        record=record,
        limitations=(),
    )
    out = ADAPTER.present(refusal)
    assert out.limitations == ()
    assert out.code == "ACCESS_NOT_ENTITLED"
    assert out.detail


# ---------------------------------------------------------------------------
# 5. No fields added by adapter (pure pass-through)
# ---------------------------------------------------------------------------


def test_adversarial_no_fields_added() -> None:
    """The adapter must not add sections, claims, citations, or numbers that
    are not present in the source DTO."""
    answer = _dto("Q5-01")
    out = ADAPTER.present(answer)
    assert len(out.sections) == len(answer.sections)
    assert len(out.claims) == len(answer.claims)
    assert len(out.citations) == len(answer.citations)
    assert len(out.numbers) == len(answer.numbers)
    # Section IDs match exactly, in order.
    assert [s.section_id for s in out.sections] == [
        s.section_id.value for s in answer.sections
    ]


# ---------------------------------------------------------------------------
# 6. Answer never becomes refusal; refusal never becomes answer
# ---------------------------------------------------------------------------


def test_adversarial_outcome_never_flips() -> None:
    """A ValidatedAnswer must project as VALIDATED_ANSWER; a
    GovernedAnswerRefusal must project as GOVERNED_REFUSAL. The adapter
    never flips the outcome."""
    answer_out = ADAPTER.present(_dto("Q5-01"))
    assert answer_out.is_answer()
    assert not answer_out.is_refusal()
    assert answer_out.outcome == "VALIDATED_ANSWER"

    refusal_out = ADAPTER.present(_dto("Q5-25"))
    assert refusal_out.is_refusal()
    assert not refusal_out.is_answer()
    assert refusal_out.outcome == "GOVERNED_REFUSAL"

    # Answer shape has no refusal-only fields populated.
    assert answer_out.code == ""
    assert answer_out.detail == ""
    assert answer_out.findings == ()
    # Refusal shape has no answer-only fields populated.
    assert refusal_out.sections == ()
    assert refusal_out.claims == ()
    assert refusal_out.citations == ()
    assert refusal_out.numbers == ()


# ---------------------------------------------------------------------------
# 7. Deterministic serialization under repeated execution
# ---------------------------------------------------------------------------


def test_adversarial_deterministic_serialization() -> None:
    """Repeated presentation of the same DTO produces byte-identical
    payloads."""
    for case_id in ("Q5-01", "Q5-03", "Q5-05", "Q5-25", "Q5-43"):
        first = ADAPTER.present(_dto(case_id)).payload()
        second = ADAPTER.present(_dto(case_id)).payload()
        assert first == second, case_id


# ---------------------------------------------------------------------------
# 8. No internal provider/retrieval material in projected record
# ---------------------------------------------------------------------------


def test_adversarial_no_internal_material_in_record() -> None:
    """The projected record must exclude provider, model, latency, cost,
    prompt, and authorization internals."""
    out = ADAPTER.present(_dto("Q5-03"))
    record = out.record
    for key in ("provider", "model", "latency_ms", "cost_usd", "cost_basis",
                "prompt_id", "prompt_version"):
        assert key not in record, f"internal field leaked: {key}"
    # Safe identity keys are present.
    for key in ("answer_id", "outcome", "depth", "package_id", "manifest_id",
                "query_plan_id", "route_id", "cited_refs", "claim_statuses",
                "validation_codes", "answer_refusal_code", "as_of"):
        assert key in record, f"missing safe field: {key}"


# ---------------------------------------------------------------------------
# 9. No-go preserved (cannot be cleared)
# ---------------------------------------------------------------------------


def test_adversarial_no_go_cannot_be_cleared() -> None:
    """Q5-25 carries NO_GO_ACTIVE in limitations. The adapter must preserve
    it and never strip it."""
    out = ADAPTER.present(_dto("Q5-25"))
    assert out.is_refusal()
    assert out.code == "SETUP_NOT_ENCODED"
    assert "NO_GO_ACTIVE" in out.limitations


# ---------------------------------------------------------------------------
# 10. Entitlement not widened (no privileged citation leak)
# ---------------------------------------------------------------------------


def test_adversarial_entitlement_not_widened() -> None:
    """Q5-43 is an ACCESS_NOT_ENTITLED refusal. No citations are rendered,
    and no protected identifiers appear in detail or limitations."""
    out = ADAPTER.present(_dto("Q5-43"))
    assert out.is_refusal()
    assert out.code == "ACCESS_NOT_ENTITLED"
    assert out.citations == ()
    text = out.detail + " " + " ".join(out.limitations)
    for token in ("context_items", "object_id", "manifest_digest", "row_id",
                  "credential", "system prompt"):
        assert token not in text.lower()


# ---------------------------------------------------------------------------
# 11. Unsupported numerical claim not rendered (Q5-08 refuses, no numbers)
# ---------------------------------------------------------------------------


def test_adversarial_unsupported_number_not_rendered() -> None:
    """Q5-08 has a numeric mismatch. The refusal must render no numbers."""
    out = ADAPTER.present(_dto("Q5-08"))
    assert out.is_refusal()
    assert out.code == "INSUFFICIENT_EVIDENCE"
    assert out.numbers == ()
    payload = out.payload()
    assert payload["numbers"] == []


# ---------------------------------------------------------------------------
# 12. No ASK_ANSWER_CONTRACT_V2 introduced
# ---------------------------------------------------------------------------


def test_adversarial_no_v2_contract() -> None:
    """The adapter never emits ASK_ANSWER_CONTRACT_V2 or a
    refusal_limitations field (Option B deferred)."""
    for case_id in ("Q5-01", "Q5-25"):
        payload = ADAPTER.present(_dto(case_id)).payload()
        assert payload["contract_version"] == "BOOK_V_PRESENTATION_CONTRACT_V1"
        assert "refusal_limitations" not in payload
        assert "ASK_ANSWER_CONTRACT_V2" not in str(payload)


# ---------------------------------------------------------------------------
# 13. Frozen dataclass prevents field mutation (upstream protection)
# ---------------------------------------------------------------------------


def test_adversarial_frozen_dto_prevents_mutation() -> None:
    """IV.5 DTOs are frozen dataclasses. Fields cannot be mutated after
    construction, so the adapter always sees a consistent input."""
    answer = _dto("Q5-01")
    with pytest.raises(Exception):
        answer.depth = "TAMPERED"  # type: ignore[misc]
    with pytest.raises(Exception):
        answer.answer_id = "TAMPERED"  # type: ignore[misc]


# ---------------------------------------------------------------------------
# 14. Nested mutable data — record dict is a fresh copy each projection
# ---------------------------------------------------------------------------


def test_adversarial_record_is_fresh_copy() -> None:
    """Each projection produces a fresh record dict. Mutating one projection's
    record does not affect another."""
    out1 = ADAPTER.present(_dto("Q5-01"))
    out2 = ADAPTER.present(_dto("Q5-01"))
    assert out1.record is not out2.record
    assert out1.record == out2.record
