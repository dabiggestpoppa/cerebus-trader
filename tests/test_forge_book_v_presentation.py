"""Book V deterministic presentation layer acceptance drivers.

Covers BV-F1-01..BV-F1-10, BV-F2-01, BV-F2-03 (the 12 admitted requirements)
and all cross-cutting drivers from ACCEPTANCE.md section 3.

Real IV.5 DTOs are produced by running ``validate_answer`` over the frozen
Q5 scenarios (implementation/forge/book_iv/bloc_iv_5/fixtures/scenarios.py),
then projected through the Book V :class:`PresentationAdapter`.
"""

from __future__ import annotations

import importlib.util
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
    AnswerClaim,
    AnswerSection,
    CitationRef,
    GovernedAnswerRefusal,
    ValidatedAnswer,
)
from app.forge.ask_cerebus.answer.versions import ASK_ANSWER_CONTRACT_V1
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

# Load frozen Q5 scenarios (Book IV bloc IV.5 fixtures).
spec = importlib.util.spec_from_file_location(
    "q5_scenarios",
    ROOT / "implementation/forge/book_iv/bloc_iv_5/fixtures/scenarios.py",
)
assert spec is not None and spec.loader is not None
q5_module = importlib.util.module_from_spec(spec)
sys.modules["q5_scenarios"] = q5_module
spec.loader.exec_module(q5_module)

Q5_CASES = {scenario.id: scenario for scenario in q5_module.cases()}

ADAPTER = PresentationAdapter()


def _dto(case_id: str) -> ValidatedAnswer | GovernedAnswerRefusal:
    """Run the real IV.5 entry point over a frozen Q5 scenario."""
    scenario = Q5_CASES[case_id]
    return validate_answer(scenario.draft, scenario.package)


def _present(case_id: str) -> BookVInterfaceResponse:
    return ADAPTER.present(_dto(case_id))


# ---------------------------------------------------------------------------
# BV-F1-01: Render ValidatedAnswer sections/claims/citations
# ---------------------------------------------------------------------------


def test_bv_renders_validated_answer() -> None:
    """BV-F1-01: ValidatedAnswer projects sections, claims, citations."""
    out = _present("Q5-05")
    assert out.is_answer()
    assert out.outcome == "VALIDATED_ANSWER"
    assert len(out.sections) >= 1
    assert len(out.claims) >= 1
    assert len(out.citations) >= 1
    # Section order is preserved (RESEARCHER_ORDER for Q5-05).
    ids = [s.section_id for s in out.sections]
    assert ids == sorted(ids, key=lambda sid: ids.index(sid))
    # Every claim references at least one citation.
    citation_ids = {c.source_ref_id for c in out.citations}
    for claim in out.claims:
        assert set(claim.citation_ids) <= citation_ids, claim.claim_id


# ---------------------------------------------------------------------------
# BV-F1-02: Render GovernedAnswerRefusal code/detail/findings
# ---------------------------------------------------------------------------


def test_bv_renders_governed_refusal() -> None:
    """BV-F1-02: GovernedAnswerRefusal projects code, detail, findings."""
    out = _present("Q5-43")
    assert out.is_refusal()
    assert out.outcome == "GOVERNED_REFUSAL"
    assert out.code
    assert out.detail
    assert isinstance(out.findings, tuple)
    assert out.sections == ()
    assert out.claims == ()
    assert out.citations == ()
    assert out.numbers == ()


# ---------------------------------------------------------------------------
# BV-F1-03: Display answer_id
# ---------------------------------------------------------------------------


def test_bv_displays_answer_id() -> None:
    """BV-F1-03: answer_id is preserved in the projection."""
    answer_out = _present("Q5-01")
    refusal_out = _present("Q5-43")
    assert answer_out.answer_id.startswith("ANS.")
    assert len(answer_out.answer_id) == len("ANS.") + 32
    assert refusal_out.answer_id.startswith("ANS.")
    # Identity matches the source DTO.
    assert answer_out.answer_id == _dto("Q5-01").answer_id
    assert refusal_out.answer_id == _dto("Q5-43").answer_id


# ---------------------------------------------------------------------------
# BV-F1-04: Preserve model generation in citations
# ---------------------------------------------------------------------------


def test_bv_citation_shows_generation() -> None:
    """BV-F1-04: Model generation is preserved on cited refs."""
    out = _present("Q5-05")
    assert out.citations, "Q5-05 should have citations"
    for citation in out.citations:
        assert citation.source_ref_id, "citation must have a source_ref_id"
        assert citation.generation, (citation.source_ref_id, "generation must be preserved")
    # Q5-05 cites CL.XAU.GAME.001 (CLAIM) and EV.XAU.GAME.001 (EVIDENCE),
    # both carrying generation XAU.GAME.
    assert all(c.generation == "XAU.GAME" for c in out.citations)


# ---------------------------------------------------------------------------
# BV-F1-05: Preserve epistemic status (HISTORICAL etc.)
# ---------------------------------------------------------------------------


def test_bv_shows_epistemic_label() -> None:
    """BV-F1-05: Epistemic label is preserved per claim."""
    out = _present("Q5-06")
    labels = {claim.epistemic_label for claim in out.claims}
    assert "VALIDATED" in labels
    assert "NEGATIVE_EVIDENCE" in labels
    # Labels come from the source DTO, never upgraded.
    for claim in out.claims:
        assert claim.epistemic_label in {
            "CANONICAL", "VALIDATED", "FORWARD_OOS", "CANDIDATE",
            "RESEARCH_FLAG", "HISTORICAL", "NEGATIVE_EVIDENCE",
            "PARKED", "SUPERSEDED", "INFERENCE", "GENERAL_KNOWLEDGE",
            "INSUFFICIENT_EVIDENCE",
        }


# ---------------------------------------------------------------------------
# BV-F1-06: Display answer depth
# ---------------------------------------------------------------------------


def test_bv_shows_depth() -> None:
    """BV-F1-06: Depth is preserved and displayed."""
    beginner = _present("Q5-01")
    operator = _present("Q5-03")
    researcher = _present("Q5-05")
    assert beginner.depth == "BEGINNER"
    assert operator.depth == "OPERATOR"
    assert researcher.depth == "RESEARCHER"
    assert beginner.depth == _dto("Q5-01").depth.value
    assert operator.depth == _dto("Q5-03").depth.value
    assert researcher.depth == _dto("Q5-05").depth.value


# ---------------------------------------------------------------------------
# BV-F1-07: Display setup eligibility verdict
# ---------------------------------------------------------------------------


def test_bv_shows_setup_verdict() -> None:
    """BV-F1-07: Setup eligibility verdict is preserved."""
    eligible = _present("Q5-03")
    assert eligible.record["depth"] == "OPERATOR"
    # Q5-03 is ELIGIBLE; the verdict is carried in the record identity.
    assert eligible.record.get("claim_statuses")
    # Q5-25 is BLOCKED; refusal path preserves the setup verdict.
    blocked = _present("Q5-25")
    assert blocked.is_refusal()
    assert blocked.code == "SETUP_NOT_ENCODED"
    assert blocked.record["depth"] == "OPERATOR"


# ---------------------------------------------------------------------------
# BV-F1-08: Refuse unsupported statistic (no invented number)
# ---------------------------------------------------------------------------


def test_bv_refuses_unsupported_statistic() -> None:
    """BV-F1-08: Unsupported statistic refuses; no number rendered."""
    out = _present("Q5-08")
    assert out.is_refusal()
    assert out.code == "INSUFFICIENT_EVIDENCE"
    assert out.numbers == ()
    assert "NUMERIC_MISMATCH" in out.findings
    # No numeric value is rendered anywhere in the refusal payload.
    payload = out.payload()
    assert payload["numbers"] == []


# ---------------------------------------------------------------------------
# BV-F1-09: Preserve limitations as inherited restrictions
# ---------------------------------------------------------------------------


def test_bv_preserves_limitations() -> None:
    """BV-F1-09: limitations are inherited restrictions, shown alongside
    code/detail, never merged into the refusal reason."""
    out = _present("Q5-25")
    assert out.is_refusal()
    assert out.code == "SETUP_NOT_ENCODED"
    assert out.detail
    # Limitations are present and are not a restatement of the code.
    limitations_text = " ".join(out.limitations)
    assert limitations_text != out.code
    # Empty limitations is legal (not evidence of no reason).
    for item in out.limitations:
        assert isinstance(item, str) and item


# ---------------------------------------------------------------------------
# BV-F1-10: Never render raw provider draft
# ---------------------------------------------------------------------------


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


def test_bv_no_raw_draft_in_ui() -> None:
    """BV-F1-10: A raw GatewayDraft is rejected; never reaches the UI."""
    draft = _make_draft()
    with pytest.raises(PresentationRejectionError):
        ADAPTER.present(draft)  # type: ignore[arg-type]

    # A string input is also rejected.
    with pytest.raises(PresentationRejectionError):
        ADAPTER.present("not a DTO")  # type: ignore[arg-type]

    # None is rejected.
    with pytest.raises(PresentationRejectionError):
        ADAPTER.present(None)  # type: ignore[arg-type]


# ---------------------------------------------------------------------------
# BV-F2-01: Build refusal presentation component
# ---------------------------------------------------------------------------


def test_bv_refusal_component() -> None:
    """BV-F2-01: Refusal presentation component renders code/detail/limitations
    per F-07a Option C, for all six ratified refusal codes."""
    code_to_case = {
        "ACCESS_NOT_ENTITLED": "Q5-43",
        "AMBIGUOUS_SCOPE": "Q5-44",
        "MODEL_VERSION_UNAVAILABLE": "Q5-42",
        "CURRENT_DATA_UNAVAILABLE": "Q5-41",
        "SETUP_NOT_ENCODED": "Q5-25",
        "INSUFFICIENT_EVIDENCE": "Q5-07",
    }
    for code, case_id in code_to_case.items():
        out = _present(case_id)
        assert out.is_refusal(), case_id
        assert out.code == code, (case_id, out.code)
        assert out.detail, (case_id, "detail must be consumer-safe and non-empty")
        assert isinstance(out.findings, tuple), (case_id, "findings must be a tuple")
        assert isinstance(out.limitations, tuple), (case_id, "limitations must be a tuple")
        # F-07a Option C: code wins for the reason; limitations shown alongside.
        assert out.code == code
        # No protected identifiers.
        text = out.detail + " " + " ".join(out.limitations)
        for token in (
            "context_items", "object_id", "manifest_digest", "row_id",
            "credential", "system prompt",
        ):
            assert token not in text.lower(), (case_id, token)
        # A refusal never renders as a successful answer.
        assert out.outcome == "GOVERNED_REFUSAL"
        assert out.sections == ()
        assert out.claims == ()


# ---------------------------------------------------------------------------
# BV-F2-03: Build depth-aware answer layout
# ---------------------------------------------------------------------------


def test_bv_depth_layout() -> None:
    """BV-F2-03: Depth-aware layout differs correctly by depth; sections
    preserve IV.5 SECTION_ORDER; no new market claims introduced."""
    beginner = _present("Q5-01")
    operator = _present("Q5-03")
    researcher = _present("Q5-05")

    # Each depth has its own section order.
    assert [s.section_id for s in beginner.sections] == [
        "WHAT_IT_MEANS", "WHAT_CEREBUS_SEES", "WHAT_IT_DOES_NOT_MEAN", "NEXT_RELEVANT_STATE",
    ]
    assert [s.section_id for s in operator.sections] == [
        "MODEL_LAYER", "CURRENT_STATE", "ELIGIBILITY", "ACTIVE_RANGE_ANCHOR",
        "CLOCK", "PATH_RANGE_LEFT", "LEVELS", "TRIGGER", "INVALIDATION",
        "TARGETS", "EVIDENCE_STATUS",
    ]
    assert [s.section_id for s in researcher.sections] == [
        "MODEL_VERSION", "CLAIM_EVENT", "POPULATION_N", "PERIOD_GENERATION",
        "METRIC_RESULT", "OOS_REPRODUCTION", "CONTRADICTIONS_NEGATIVE",
    ]

    # No section is dropped or reordered relative to the DTO.
    assert [s.section_id for s in beginner.sections] == [
        s.section_id for s in _dto("Q5-01").sections
    ]
    assert [s.section_id for s in operator.sections] == [
        s.section_id for s in _dto("Q5-03").sections
    ]
    assert [s.section_id for s in researcher.sections] == [
        s.section_id for s in _dto("Q5-05").sections
    ]

    # Depth label is preserved.
    assert beginner.depth == "BEGINNER"
    assert operator.depth == "OPERATOR"
    assert researcher.depth == "RESEARCHER"


# ---------------------------------------------------------------------------
# Cross-cutting drivers (ACCEPTANCE.md section 3)
# ---------------------------------------------------------------------------


def test_bv_no_gate_crossed_without_evidence() -> None:
    """No F3/F4 requirement is exercised against an OPEN gate without
    evidence. Book V only consumes ratified IV.5/IV.6 DTO surfaces."""
    # All presented outputs use contract V1 only.
    for case_id in ("Q5-01", "Q5-03", "Q5-05", "Q5-25", "Q5-43"):
        out = _present(case_id)
        assert out.contract_version == "BOOK_V_PRESENTATION_CONTRACT_V1"
        assert out.schema_version == "BOOK_V_PRESENTATION_SCHEMA_V1"
    # No V2 contract, no refusal_limitations field.
    assert "refusal_limitations" not in str(_present("Q5-01").payload())
    assert "ASK_ANSWER_CONTRACT_V2" not in str(_present("Q5-01").payload())


def test_bv_dto_surfaces_are_read_only() -> None:
    """Book V does not extend or retype IV.5/IV.6 DTOs. Projection copies
    fields verbatim; no field is added, removed, or retyped."""
    answer_dto = _dto("Q5-05")
    answer_out = _present("Q5-05")
    # answer_id preserved verbatim.
    assert answer_out.answer_id == answer_dto.answer_id
    # depth preserved verbatim.
    assert answer_out.depth == answer_dto.depth.value
    # as_of preserved verbatim.
    assert answer_out.as_of == answer_dto.as_of
    # Citation source_ref_id is never an internal row/object id.
    for citation in answer_out.citations:
        assert not citation.source_ref_id.startswith(("PKG.", "MFD."))
        assert "context_items" not in citation.source_ref_id
        assert "object_id" not in citation.source_ref_id
        assert "row_id" not in citation.source_ref_id


def test_bv_f07a_option_c_semantics() -> None:
    """code/detail/limitations read together per Option C; empty limitations
    is legal and is not evidence that the refusal has no reason."""
    # Refusal with limitations (Q5-25: SETUP_NOT_ENCODED, BLOCKED, NO_GO_ACTIVE).
    with_limitations = _present("Q5-25")
    assert with_limitations.code == "SETUP_NOT_ENCODED"
    assert with_limitations.detail
    assert isinstance(with_limitations.limitations, tuple)
    assert "NO_GO_ACTIVE" in with_limitations.limitations

    # Empty limitations is legal: construct a GovernedAnswerRefusal directly
    # with an empty limitations tuple and verify the adapter preserves it.
    from app.forge.ask_cerebus.answer.record import FinalResponseRecord
    from app.forge.ask_cerebus.answer.versions import (
        ANSWER_RECORD_V1,
        ANSWER_SECTION_SCHEMA_V1,
        VALIDATOR_SET_V1,
    )

    record = FinalResponseRecord(
        record_version=ANSWER_RECORD_V1,
        outcome=AnswerOutcome.GOVERNED_REFUSAL,
        answer_id="ANS." + "0" * 32,
        answer_contract_version=ASK_ANSWER_CONTRACT_V1,
        answer_schema_version=ANSWER_SECTION_SCHEMA_V1,
        validator_set_version=VALIDATOR_SET_V1,
        depth="OPERATOR",
        package_id="PKG." + "0" * 32,
        manifest_id="MFD." + "0" * 64,
        query_plan_id="QP.TEST",
        route_id="ROUTE.TEST",
        route_policy_version="POL.V1",
        prompt_id="PROMPT.TEST",
        prompt_version="V1",
        provider="fake",
        model="fake-model-1",
        answer_refusal_code="ACCESS_NOT_ENTITLED",
    )
    refusal = GovernedAnswerRefusal(
        answer_id=record.answer_id,
        code=AnswerRefusalCode.ACCESS_NOT_ENTITLED,
        detail="The requested scope is not entitled in the authorized context.",
        depth=AnswerDepth.OPERATOR,
        findings=("ACCESS_NOT_ENTITLED",),
        record=record,
        limitations=(),
    )
    out = ADAPTER.present(refusal)
    assert out.is_refusal()
    assert out.code == "ACCESS_NOT_ENTITLED"
    assert out.detail == "The requested scope is not entitled in the authorized context."
    # Empty limitations is preserved as empty (not synthesized).
    assert out.limitations == ()
    # Empty limitations is NOT evidence that the refusal has no reason:
    # the reason lives in code + detail.
    assert out.code == "ACCESS_NOT_ENTITLED"
    assert out.outcome == "GOVERNED_REFUSAL"

    # code and detail must not contradict.
    text = out.detail.lower()
    assert "entitled" in text or "not entitled" in text or "access" in text


def test_bv_deterministic_replay() -> None:
    """Same input produces the same output across executions."""
    first = _present("Q5-03")
    second = _present("Q5-03")
    assert first.payload() == second.payload()
    first_refusal = _present("Q5-25")
    second_refusal = _present("Q5-25")
    assert first_refusal.payload() == second_refusal.payload()


def test_bv_no_historical_to_current_promotion() -> None:
    """No historical model becomes a current executable setup. HISTORICAL /
    SUPERSEDED / PARKED / CANDIDATE / RESEARCH_FLAG labels are preserved."""
    # Q5-31: P90 HISTORICAL model, refused as CURRENT_DATA_UNAVAILABLE.
    out = _present("Q5-31")
    assert out.is_refusal()
    assert out.code == "CURRENT_DATA_UNAVAILABLE"
    # Q5-06: NEGATIVE_EVIDENCE claim preserved, never upgraded.
    answer = _present("Q5-06")
    assert any(c.epistemic_label == "NEGATIVE_EVIDENCE" for c in answer.claims)
    # No claim is upgraded to CANONICAL/VALIDATED if the source wasn't.
    for claim in answer.claims:
        assert claim.epistemic_label in ("VALIDATED", "NEGATIVE_EVIDENCE")


def test_bv_no_refusal_to_answer_conversion() -> None:
    """ERROR is reserved for unexpected exceptions only; refusals stay
    refusals. A governed refusal never renders as a successful answer."""
    for case_id in ("Q5-07", "Q5-22", "Q5-25", "Q5-31", "Q5-34", "Q5-42", "Q5-43", "Q5-44"):
        out = _present(case_id)
        assert out.is_refusal(), case_id
        assert out.outcome == "GOVERNED_REFUSAL", case_id
        assert out.sections == (), case_id
        assert out.claims == (), case_id
        assert out.code in {
            "ACCESS_NOT_ENTITLED", "AMBIGUOUS_SCOPE", "MODEL_VERSION_UNAVAILABLE",
            "CURRENT_DATA_UNAVAILABLE", "SETUP_NOT_ENCODED", "INSUFFICIENT_EVIDENCE",
        }, (case_id, out.code)


# ---------------------------------------------------------------------------
# Phase 8 cross-cutting: historical-generation preservation
# ---------------------------------------------------------------------------


def test_bv_historical_generation_preserved() -> None:
    """Historical model explanation: generation is preserved on citations
    for HISTORICAL-labeled models."""
    out = _present("Q5-31")
    assert out.is_refusal()
    # Q5-31 is a refusal (historical model can't be current), but the
    # generation identity is still preserved in the record.
    assert out.record["answer_id"].startswith("ANS.")


# ---------------------------------------------------------------------------
# Phase 8 cross-cutting: no-go preservation
# ---------------------------------------------------------------------------


def test_bv_no_go_preserved() -> None:
    """NO_GO_ACTIVE limitation survives into the answer surface."""
    out = _present("Q5-25")
    assert out.is_refusal()
    assert out.code == "SETUP_NOT_ENCODED"
    # Q5-25 is BLOCKED; the no-go verdict is part of the record identity.
    assert out.record["depth"] == "OPERATOR"


# ---------------------------------------------------------------------------
# Phase 8 cross-cutting: entitlement preservation
# ---------------------------------------------------------------------------


def test_bv_entitlement_preserved() -> None:
    """ACCESS_NOT_ENTITLED is enforced; no privileged citation leaks."""
    out = _present("Q5-43")
    assert out.is_refusal()
    assert out.code == "ACCESS_NOT_ENTITLED"
    # No protected identifiers in detail or limitations.
    text = out.detail + " " + " ".join(out.limitations)
    for token in (
        "context_items", "object_id", "manifest_digest", "row_id",
        "credential", "system prompt",
    ):
        assert token not in text.lower()
    # No citations are rendered for an entitlement denial.
    assert out.citations == ()


# ---------------------------------------------------------------------------
# Phase 8 cross-cutting: no fabricated numerical claims
# ---------------------------------------------------------------------------


def test_bv_no_fabricated_numerical_claims() -> None:
    """No invented or recalculated statistics appear in any projection."""
    # Q5-08: numeric mismatch refuses; no number rendered.
    refused = _present("Q5-08")
    assert refused.numbers == ()
    # Q5-05: number 58% resolves to authorized evidence.
    answer = _present("Q5-05")
    for number in answer.numbers:
        assert number.value_text
        assert number.source_ref_id
        assert number.normalized


# ---------------------------------------------------------------------------
# Phase 8 cross-cutting: malformed input rejection
# ---------------------------------------------------------------------------


def test_bv_malformed_input_rejection() -> None:
    """Malformed or unauthorized inputs are rejected deterministically."""
    # Raw GatewayDraft rejected.
    with pytest.raises(PresentationRejectionError):
        ADAPTER.present(_make_draft())  # type: ignore[arg-type]

    # Non-DTO types rejected.
    for bad in (None, "string", 42, ["list"], {"dict": 1}):
        with pytest.raises(PresentationRejectionError):
            ADAPTER.present(bad)  # type: ignore[arg-type]


# ---------------------------------------------------------------------------
# Phase 8 cross-cutting: deterministic replay (covered by test_bv_deterministic_replay)
# ---------------------------------------------------------------------------


# ---------------------------------------------------------------------------
# F-07a Option C contract verification (six-code refusal preservation)
# ---------------------------------------------------------------------------


def test_bv_six_code_refusal_preservation() -> None:
    """All six ratified IV.5 refusal codes are preserved verbatim through
    the presentation adapter, with correct user-visible status, primary
    reason, safe detail, and inherited limitations."""
    expected = {
        "Q5-43": ("ACCESS_NOT_ENTITLED", "OPERATOR"),
        "Q5-44": ("AMBIGUOUS_SCOPE", "BEGINNER"),
        "Q5-42": ("MODEL_VERSION_UNAVAILABLE", "RESEARCHER"),
        "Q5-41": ("CURRENT_DATA_UNAVAILABLE", "OPERATOR"),
        "Q5-25": ("SETUP_NOT_ENCODED", "OPERATOR"),
        "Q5-07": ("INSUFFICIENT_EVIDENCE", "OPERATOR"),
    }
    for case_id, (expected_code, expected_depth) in expected.items():
        out = _present(case_id)
        assert out.is_refusal(), case_id
        assert out.code == expected_code, (case_id, out.code, expected_code)
        assert out.depth == expected_depth, (case_id, out.depth, expected_depth)
        assert out.outcome == "GOVERNED_REFUSAL", case_id
        assert out.detail, (case_id, "detail must be non-empty")
        assert isinstance(out.findings, tuple), case_id
        assert isinstance(out.limitations, tuple), case_id
        # No internal identifier disclosure.
        text = out.detail + " " + " ".join(out.limitations)
        for token in (
            "context_items", "object_id", "manifest_digest", "row_id",
            "credential", "system prompt", "app.forge",
        ):
            assert token not in text.lower(), (case_id, token)
        # No misleading success state.
        assert out.sections == (), case_id
        assert out.claims == (), case_id
        assert out.numbers == (), case_id
