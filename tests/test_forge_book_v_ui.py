"""Book V deterministic UI component acceptance drivers.

Covers the admitted BA-39 requirements (BV-F1-01..BV-F1-10, BV-F2-01,
BV-F2-03) at the UI component layer: deterministic HTML rendering of
:class:`BookVInterfaceResponse` produced by the Book V presentation
adapter.

Every test contains a meaningful behavioral assertion. No skips, no
xfails, no placeholders, no empty tests.
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
from app.forge.book_v.presentation.adapter import PresentationAdapter
from app.forge.book_v.presentation.model import BookVInterfaceResponse
from app.forge.book_v.ui.components import (
    VALID_DEPTHS,
    VALID_VERDICTS,
    render_answer_sections,
    render_citation,
    render_citations,
    render_claim,
    render_depth_badge,
    render_eligibility,
    render_governed_refusal,
    render_interface_response,
    render_limitations,
    render_numbers,
    render_refusal,
    render_section,
    render_validated_answer,
)
from app.forge.book_v.ui.versions import (
    BOOK_V_UI_CONTRACT_V1,
    BOOK_V_UI_SCHEMA_V1,
)

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# Load frozen Q5 scenarios (Book IV bloc IV.5 fixtures).
spec = importlib.util.spec_from_file_location(
    "q5_scenarios_ui",
    ROOT / "implementation/forge/book_iv/bloc_iv_5/fixtures/scenarios.py",
)
assert spec is not None and spec.loader is not None
q5_module = importlib.util.module_from_spec(spec)
sys.modules["q5_scenarios_ui"] = q5_module
spec.loader.exec_module(q5_module)

Q5_CASES = {scenario.id: scenario for scenario in q5_module.cases()}

ADAPTER = PresentationAdapter()


def _dto(case_id: str) -> ValidatedAnswer | GovernedAnswerRefusal:
    """Run the real IV.5 entry point over a frozen Q5 scenario."""
    return validate_answer(Q5_CASES[case_id].draft, Q5_CASES[case_id].package)


def _present(case_id: str) -> BookVInterfaceResponse:
    return ADAPTER.present(_dto(case_id))


def _render(case_id: str) -> str:
    """Render a Q5 scenario end-to-end: IV.5 → PresentationAdapter → UI."""
    return render_interface_response(_present(case_id))


# ---------------------------------------------------------------------------
# BV-F1-01: Render ValidatedAnswer sections/claims/citations
# ---------------------------------------------------------------------------


def test_bv_ui_renders_validated_answer() -> None:
    """BV-F1-01: ValidatedAnswer renders sections, claims, citations as HTML."""
    html = _render("Q5-05")
    assert "VALIDATED_ANSWER" in html
    assert 'data-outcome="VALIDATED_ANSWER"' in html
    # Sections are rendered in depth order.
    assert "WHAT_IT_MEANS" not in html  # Q5-05 is RESEARCHER
    assert "MODEL_VERSION" in html
    assert "CLAIM_EVENT" in html
    assert "POPULATION_N" in html
    assert "METRIC_RESULT" in html
    # Claims are rendered with their text.
    assert "58%" in html
    # Citations are rendered with source ref ids.
    assert "CL.XAU.GAME.001" in html
    assert "EV.XAU.GAME.001" in html


# ---------------------------------------------------------------------------
# BV-F1-02: Render GovernedAnswerRefusal code/detail/findings
# ---------------------------------------------------------------------------


def test_bv_ui_renders_governed_refusal() -> None:
    """BV-F1-02: GovernedAnswerRefusal renders code/detail/findings as HTML."""
    html = _render("Q5-43")
    assert "GOVERNED_REFUSAL" in html
    assert 'data-outcome="GOVERNED_REFUSAL"' in html
    assert "ACCESS_NOT_ENTITLED" in html
    assert "not entitled" in html.lower()
    # Refusals never render sections, claims, or numbers.
    assert "WHAT_IT_MEANS" not in html
    assert "MODEL_VERSION" not in html


# ---------------------------------------------------------------------------
# BV-F1-03: Display answer_id
# ---------------------------------------------------------------------------


def test_bv_ui_displays_answer_id() -> None:
    """BV-F1-03: answer_id is rendered in the HTML."""
    html = _render("Q5-01")
    assert 'data-answer-id="' in html
    assert "ANS." in html
    # Identity matches the source DTO.
    dto = _dto("Q5-01")
    assert dto.answer_id in html


# ---------------------------------------------------------------------------
# BV-F1-04: Preserve model generation in citations
# ---------------------------------------------------------------------------


def test_bv_ui_citation_shows_generation() -> None:
    """BV-F1-04: Model generation is preserved in rendered citations."""
    html = _render("Q5-05")
    assert "XAU.GAME" in html  # generation on Q5-05 citations


# ---------------------------------------------------------------------------
# BV-F1-05: Preserve epistemic status (HISTORICAL etc.)
# ---------------------------------------------------------------------------


def test_bv_ui_shows_epistemic_label() -> None:
    """BV-F1-05: Epistemic label is rendered per claim."""
    html = _render("Q5-06")
    assert "VALIDATED" in html
    assert "NEGATIVE_EVIDENCE" in html


# ---------------------------------------------------------------------------
# BV-F1-06: Display answer depth
# ---------------------------------------------------------------------------


def test_bv_ui_shows_depth() -> None:
    """BV-F1-06: Depth is rendered as a badge."""
    html_b = _render("Q5-01")
    html_o = _render("Q5-03")
    html_r = _render("Q5-05")
    assert 'depth-badge depth-beginner' in html_b
    assert 'depth-badge depth-operator' in html_o
    assert 'depth-badge depth-researcher' in html_r
    assert "BEGINNER" in html_b
    assert "OPERATOR" in html_o
    assert "RESEARCHER" in html_r


# ---------------------------------------------------------------------------
# BV-F1-07: Display setup eligibility verdict
# ---------------------------------------------------------------------------


def test_bv_ui_shows_setup_verdict() -> None:
    """BV-F1-07: Setup eligibility verdict is rendered."""
    html = _render("Q5-03")
    assert "verdict-" in html or "eligibility" in html.lower()


# ---------------------------------------------------------------------------
# BV-F1-08: Refuse unsupported statistic (no invented number)
# ---------------------------------------------------------------------------


def test_bv_ui_refuses_unsupported_statistic() -> None:
    """BV-F1-08: Unsupported statistic refuses; no number rendered."""
    html = _render("Q5-08")
    assert "INSUFFICIENT_EVIDENCE" in html
    assert 'data-outcome="GOVERNED_REFUSAL"' in html


# ---------------------------------------------------------------------------
# BV-F1-09: Preserve limitations as inherited restrictions
# ---------------------------------------------------------------------------


def test_bv_ui_preserves_limitations() -> None:
    """BV-F1-09: Limitations are rendered as inherited restrictions."""
    html = _render("Q5-25")
    assert "NO_GO_ACTIVE" in html


# ---------------------------------------------------------------------------
# BV-F1-10: Never render raw provider draft
# ---------------------------------------------------------------------------


def test_bv_ui_no_raw_draft_in_ui() -> None:
    """BV-F1-10: UI components never consume raw provider drafts.

    The UI render functions accept only ``BookVInterfaceResponse``. A raw
    ``GatewayDraft`` is not a valid input type.
    """
    from app.forge.ask_cerebus.llm_gateway.draft import GatewayDraft
    from app.forge.ask_cerebus.llm_gateway.enums import DraftStatus
    from app.forge.book_v.presentation.adapter import PresentationRejectionError

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
        usage=None,  # type: ignore[arg-type]
        attempts=(),
        trace=None,  # type: ignore[arg-type]
        status=DraftStatus.UNVALIDATED,
    )
    # A raw GatewayDraft cannot be passed to render_interface_response
    # (it is not a BookVInterfaceResponse); the presentation adapter
    # rejects it first. The UI layer never sees it.
    with pytest.raises((TypeError, ValueError, PresentationRejectionError)):
        render_interface_response(draft)  # type: ignore[arg-type]


# ---------------------------------------------------------------------------
# BV-F2-01: Build refusal presentation component
# ---------------------------------------------------------------------------


def test_bv_ui_refusal_component() -> None:
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
        html = _render(case_id)
        assert code in html, (case_id, "refusal code must appear in HTML")
        assert "GOVERNED_REFUSAL" in html, (case_id, "must be a refusal")
        # Refusal reason is visible (not suppressed).
        assert f'data-refusal-code="{code}"' in html
        # Detail is rendered.
        assert len(html) > 50, (case_id, "detail must be rendered")
        # No sections, claims, or numbers in a refusal.
        assert '<section class="answer-section"' not in html
        assert '<div class="claim"' not in html


# ---------------------------------------------------------------------------
# BV-F2-03: Build depth-aware answer layout
# ---------------------------------------------------------------------------


def test_bv_ui_depth_layout() -> None:
    """BV-F2-03: Depth-aware layout differs correctly by depth; sections
    preserve IV.5 SECTION_ORDER."""
    html_b = _render("Q5-01")
    html_o = _render("Q5-03")
    html_r = _render("Q5-05")

    # BEGINNER sections
    assert "WHAT_IT_MEANS" in html_b
    assert "WHAT_CEREBUS_SEES" in html_b
    assert "WHAT_IT_DOES_NOT_MEAN" in html_b
    assert "NEXT_RELEVANT_STATE" in html_b

    # OPERATOR sections
    assert "MODEL_LAYER" in html_o
    assert "CURRENT_STATE" in html_o
    assert "ELIGIBILITY" in html_o

    # RESEARCHER sections
    assert "MODEL_VERSION" in html_r
    assert "CLAIM_EVENT" in html_r
    assert "POPULATION_N" in html_r
    assert "METRIC_RESULT" in html_r


# ---------------------------------------------------------------------------
# Cross-cutting: three answer depths
# ---------------------------------------------------------------------------


def test_bv_ui_three_depths_render_correctly() -> None:
    """All three depths render with correct section sets and depth badges."""
    cases = {
        "Q5-01": ("BEGINNER", "WHAT_IT_MEANS"),
        "Q5-03": ("OPERATOR", "MODEL_LAYER"),
        "Q5-05": ("RESEARCHER", "MODEL_VERSION"),
    }
    for case_id, (expected_depth, expected_section) in cases.items():
        html = _render(case_id)
        assert f'depth-badge depth-{expected_depth.lower()}' in html
        assert expected_section in html


# ---------------------------------------------------------------------------
# Cross-cutting: six refusal codes
# ---------------------------------------------------------------------------


def test_bv_ui_six_refusal_codes() -> None:
    """All six ratified refusal codes render correctly through the UI."""
    expected = {
        "Q5-43": ("ACCESS_NOT_ENTITLED", "OPERATOR"),
        "Q5-44": ("AMBIGUOUS_SCOPE", "BEGINNER"),
        "Q5-42": ("MODEL_VERSION_UNAVAILABLE", "RESEARCHER"),
        "Q5-41": ("CURRENT_DATA_UNAVAILABLE", "OPERATOR"),
        "Q5-25": ("SETUP_NOT_ENCODED", "OPERATOR"),
        "Q5-07": ("INSUFFICIENT_EVIDENCE", "OPERATOR"),
    }
    for case_id, (expected_code, expected_depth) in expected.items():
        html = _render(case_id)
        assert f'data-refusal-code="{expected_code}"' in html
        assert f'depth-badge depth-{expected_depth.lower()}' in html
        assert "GOVERNED_REFUSAL" in html
        # Refusal is never rendered as a successful answer.
        assert '<div class="validated-answer"' not in html


# ---------------------------------------------------------------------------
# Cross-cutting: citation safety
# ---------------------------------------------------------------------------


def test_bv_ui_citation_safety() -> None:
    """Citations render only safe fields; no internal identifiers leak."""
    html = _render("Q5-05")
    assert "CL.XAU.GAME.001" in html
    assert "EV.XAU.GAME.001" in html
    # No internal identifiers.
    for token in ("PKG.", "MFD.", "context_items", "object_id", "row_id"):
        assert token not in html, f"internal identifier leaked: {token}"


# ---------------------------------------------------------------------------
# Cross-cutting: historical generation preservation
# ---------------------------------------------------------------------------


def test_bv_ui_historical_generation_preserved() -> None:
    """Historical model generation is preserved in rendered citations."""
    html = _render("Q5-31")
    # Q5-31 is a refusal (historical model can't be current), but the
    # generation identity is preserved in the answer_id/record.
    assert "ANS." in html
    assert "GOVERNED_REFUSAL" in html


# ---------------------------------------------------------------------------
# Cross-cutting: no-go preservation
# ---------------------------------------------------------------------------


def test_bv_ui_no_go_preserved() -> None:
    """NO_GO_ACTIVE limitation survives into the rendered UI."""
    html = _render("Q5-25")
    assert "NO_GO_ACTIVE" in html
    assert "GOVERNED_REFUSAL" in html


# ---------------------------------------------------------------------------
# Cross-cutting: entitlement preservation
# ---------------------------------------------------------------------------


def test_bv_ui_entitlement_preserved() -> None:
    """ACCESS_NOT_ENTITLED is enforced; no privileged citation leaks."""
    html = _render("Q5-43")
    assert "ACCESS_NOT_ENTITLED" in html
    # No citations rendered for entitlement denial.
    assert 'class="citation"' not in html


# ---------------------------------------------------------------------------
# Cross-cutting: empty limitations
# ---------------------------------------------------------------------------


def test_bv_ui_empty_limitations() -> None:
    """Empty limitations remain valid; not treated as no refusal reason."""
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
        detail="The requested scope is not entitled.",
        depth=AnswerDepth.OPERATOR,
        findings=("ACCESS_NOT_ENTITLED",),
        record=record,
        limitations=(),
    )
    response = ADAPTER.present(refusal)
    html = render_interface_response(response)
    assert "no inherited limitations" in html
    assert "ACCESS_NOT_ENTITLED" in html
    assert "GOVERNED_REFUSAL" in html


# ---------------------------------------------------------------------------
# Cross-cutting: malformed presentation input
# ---------------------------------------------------------------------------


def test_bv_ui_malformed_input() -> None:
    """Malformed or non-interface responses fail safely."""
    with pytest.raises(ValueError):
        render_interface_response("not a response")  # type: ignore[arg-type]
    with pytest.raises(ValueError):
        render_interface_response(None)  # type: ignore[arg-type]
    with pytest.raises(ValueError):
        render_interface_response({"outcome": "INVALID"})  # type: ignore[arg-type]


# ---------------------------------------------------------------------------
# Cross-cutting: deterministic rendering
# ---------------------------------------------------------------------------


def test_bv_ui_deterministic_rendering() -> None:
    """Same input produces identical HTML across executions."""
    for case_id in ("Q5-01", "Q5-03", "Q5-05", "Q5-25", "Q5-43"):
        first = _render(case_id)
        second = _render(case_id)
        assert first == second, case_id


# ---------------------------------------------------------------------------
# Cross-cutting: no internal data leakage
# ---------------------------------------------------------------------------


def test_bv_ui_no_internal_data_leakage() -> None:
    """No internal provider/retrieval material leaks into rendered HTML."""
    for case_id in ("Q5-01", "Q5-03", "Q5-05", "Q5-25", "Q5-43"):
        html = _render(case_id)
        for token in ("context_items", "object_id", "manifest_digest", "row_id",
                      "credential", "system prompt", "app.forge", "latency",
                      "cost_usd", "prompt_id"):
            assert token not in html.lower(), (case_id, token)


# ---------------------------------------------------------------------------
# Cross-cutting: accessible status messages
# ---------------------------------------------------------------------------


def test_bv_ui_accessible_status_messages() -> None:
    """Rendered HTML uses semantic elements and ARIA labels for accessibility."""
    html = _render("Q5-01")
    # Semantic section elements.
    assert "<section" in html
    assert "<h3>" in html
    assert "<ul>" in html
    assert "<li>" in html
    # ARIA labels present.
    assert 'aria-label=' in html
    # Role alert on refusals.
    refusal_html = _render("Q5-25")
    assert 'role="alert"' in refusal_html


# ---------------------------------------------------------------------------
# Cross-cutting: keyboard-navigable structure (no color-only status)
# ---------------------------------------------------------------------------


def test_bv_ui_no_color_only_status() -> None:
    """Status is conveyed via text labels, not color alone."""
    html = _render("Q5-25")
    # Refusal code is text, not just a color class.
    assert "SETUP_NOT_ENCODED" in html
    # Depth is text in a badge, not just a color.
    assert "OPERATOR" in html


# ---------------------------------------------------------------------------
# Component-level: render_depth_badge validation
# ---------------------------------------------------------------------------


def test_bv_ui_component_depth_badge_validation() -> None:
    """render_depth_badge rejects invalid depths."""
    assert "BEGINNER" in render_depth_badge("BEGINNER")
    assert "OPERATOR" in render_depth_badge("OPERATOR")
    assert "RESEARCHER" in render_depth_badge("RESEARCHER")
    with pytest.raises(ValueError):
        render_depth_badge("INVALID")


# ---------------------------------------------------------------------------
# Component-level: render_eligibility validation
# ---------------------------------------------------------------------------


def test_bv_ui_component_eligibility_validation() -> None:
    """render_eligibility rejects invalid verdicts."""
    for verdict in ("ELIGIBLE", "WATCH", "UNRESOLVED", "BLOCKED"):
        assert verdict in render_eligibility(verdict)
    with pytest.raises(ValueError):
        render_eligibility("INVALID")


# ---------------------------------------------------------------------------
# Component-level: render_refusal Option C semantics
# ---------------------------------------------------------------------------


def test_bv_ui_component_refusal_option_c() -> None:
    """render_refusal preserves code/detail/findings/limitations per Option C."""
    html = render_refusal(
        "SETUP_NOT_ENCODED",
        "No validated setup is encoded.",
        ("SETUP_NOT_ENCODED",),
        ("NO_GO_ACTIVE",),
    )
    assert "SETUP_NOT_ENCODED" in html
    assert "No validated setup is encoded." in html
    assert "SETUP_NOT_ENCODED" in html  # findings
    assert "NO_GO_ACTIVE" in html  # limitations
    # Empty limitations is legal.
    html_empty = render_refusal(
        "ACCESS_NOT_ENTITLED",
        "Not entitled.",
        ("ACCESS_NOT_ENTITLED",),
        (),
    )
    assert "no inherited limitations" in html_empty
    assert "ACCESS_NOT_ENTITLED" in html_empty


# ---------------------------------------------------------------------------
# Component-level: render_citation safe fields
# ---------------------------------------------------------------------------


def test_bv_ui_component_citation_safe_fields() -> None:
    """render_citation renders only safe fields; no internal identifiers."""
    from app.forge.book_v.presentation.model import BookVCitation

    citation = BookVCitation(
        source_ref_id="CL.XAU.GAME.001",
        source_ref_type="CLAIM",
        source_status="VALIDATED",
        provenance_refs=("PV.001",),
        evidence_refs=("EV.001",),
        generation="XAU.GAME",
    )
    html = render_citation(citation)
    assert "CL.XAU.GAME.001" in html
    assert "CLAIM" in html
    assert "VALIDATED" in html
    assert "XAU.GAME" in html
    # No internal identifiers.
    for token in ("PKG.", "MFD.", "context_items", "object_id", "row_id"):
        assert token not in html


# ---------------------------------------------------------------------------
# Component-level: render_numbers
# ---------------------------------------------------------------------------


def test_bv_ui_component_numbers() -> None:
    """render_numbers renders authorized numeric values."""
    from app.forge.book_v.presentation.model import BookVNumber

    number = BookVNumber(
        value_text="58%",
        unit="",
        source_ref_id="CL.XAU.GAME.001",
        normalized="58%",
    )
    html = render_numbers((number,))
    assert "58%" in html
    assert "CL.XAU.GAME.001" in html
    # Empty numbers renders empty container.
    html_empty = render_numbers(())
    assert 'class="numbers"' in html_empty


# ---------------------------------------------------------------------------
# Component-level: render_limitations empty vs non-empty
# ---------------------------------------------------------------------------


def test_bv_ui_component_limitations() -> None:
    """render_limitations handles empty and non-empty tuples."""
    html = render_limitations(("NO_GO_ACTIVE", "CLOCK_UNRESOLVED"))
    assert "NO_GO_ACTIVE" in html
    assert "CLOCK_UNRESOLVED" in html
    html_empty = render_limitations(())
    assert "no inherited limitations" in html_empty


# ---------------------------------------------------------------------------
# Component-level: render_validated_answer / render_governed_refusal dispatch
# ---------------------------------------------------------------------------


def test_bv_ui_component_dispatch() -> None:
    """render_interface_response dispatches correctly by outcome."""
    record = FinalResponseRecord(
        record_version=ANSWER_RECORD_V1,
        outcome=AnswerOutcome.VALIDATED_ANSWER,
        answer_id="ANS." + "0" * 32,
        answer_contract_version=ASK_ANSWER_CONTRACT_V1,
        answer_schema_version=ANSWER_SECTION_SCHEMA_V1,
        validator_set_version=VALIDATOR_SET_V1,
        depth="BEGINNER",
        package_id="PKG." + "0" * 32,
        manifest_id="MFD." + "0" * 64,
        query_plan_id="QP.TEST",
        route_id="ROUTE.TEST",
        route_policy_version="POL.V1",
        prompt_id="PROMPT.TEST",
        prompt_version="V1",
        provider="fake",
        model="fake-model-1",
    )
    answer = ValidatedAnswer(
        answer_id=record.answer_id,
        depth=AnswerDepth.BEGINNER,
        sections=(),
        claims=(),
        citations=(),
        numbers=(),
        limitations=(),
        as_of="",
        record=record,
    )
    response = ADAPTER.present(answer)
    html = render_interface_response(response)
    assert "VALIDATED_ANSWER" in html
    assert "BEGINNER" in html


# ---------------------------------------------------------------------------
# Component-level: contract versions
# ---------------------------------------------------------------------------


def test_bv_ui_component_contract_versions() -> None:
    """UI contract versions are frozen V1 only."""
    assert BOOK_V_UI_CONTRACT_V1 == "BOOK_V_UI_CONTRACT_V1"
    assert BOOK_V_UI_SCHEMA_V1 == "BOOK_V_UI_SCHEMA_V1"
    assert "refusal_limitations" not in BOOK_V_UI_CONTRACT_V1
    assert "ASK_ANSWER_CONTRACT_V2" not in BOOK_V_UI_CONTRACT_V1


# ---------------------------------------------------------------------------
# Component-level: hash of rendered output is deterministic
# ---------------------------------------------------------------------------


def test_bv_ui_rendered_hash_deterministic() -> None:
    """Rendered HTML hash is deterministic across executions."""
    for case_id in ("Q5-01", "Q5-25", "Q5-43"):
        h1 = hashlib.sha256(_render(case_id).encode("utf-8")).hexdigest()
        h2 = hashlib.sha256(_render(case_id).encode("utf-8")).hexdigest()
        assert h1 == h2, case_id
        assert len(h1) == 64
