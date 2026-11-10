"""Security amendment 1 (BA-32) — AM1-R01..R24 acceptance drivers.

Every driver reads a frozen ``AmendmentCase`` from
``app.forge.ask_cerebus.evaluation.amendment`` and asserts the *effect* the
amendment forbids. Expectations are literals; none is read from a run.

R25 (metric populations) and R26 (CHAIN evidence path) live in
``test_forge_ask_cerebus_evaluation_amendment1.py``. R27 (hash invariance) is
DEFERRED to a separately authorized infrastructure amendment and deliberately
has no passing driver here.
"""

from __future__ import annotations

import sys
from functools import lru_cache
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.forge.ask_cerebus.evaluation import amendment
from app.forge.ask_cerebus.evaluation.amendment import P1, P2, P3


@lru_cache(maxsize=1)
def _results():
    return {result.case_id: result for result in amendment.run_all()}


def _result(number: int) -> amendment.AmendmentResult:
    return _results()[f"EV-{number:03d}"]


def _claim_labels(result) -> dict[str, str]:
    answer = result.artifacts["answer"]
    return {claim.claim_id: claim.epistemic_label for claim in getattr(answer, "claims", ())}


def _bullets(result) -> str:
    answer = result.artifacts["answer"]
    return " ".join(
        str(bullet) for section in getattr(answer, "sections", ()) for bullet in section.bullets
    ).lower()


# ---------------------------------------------------------------------------
# 1.1 untrusted content in answers
# ---------------------------------------------------------------------------


def test_am1_r01_untrusted_text_never_rendered_as_validated_bullet():
    result = _result(121)
    assert result.passed, result.reasons
    assert result.outcome == "GOVERNED_REFUSAL"
    assert "AUTHORITY_ESCALATION" in result.codes
    assert P1.lower() not in result.visible_text


def test_am1_r02_quoted_untrusted_text_carries_marker_and_ref():
    result = _result(143)
    assert result.passed, result.reasons
    assert result.outcome == "VALIDATED_ANSWER"
    bullets = _bullets(result)
    assert "untrusted source doc.external.note:" in bullets
    assert P1.lower() in bullets  # the quotation itself survives
    assert result.untrusted_claims == 1
    assert result.unmarked_untrusted_claims == 0


def test_am1_r03_rendered_claim_label_matches_source_item():
    result = _result(143)
    assert result.passed, result.reasons
    package = result.artifacts["package"]
    labels = {
        item.source_ref_id: item.epistemic_label.value
        for section in package.sections
        for item in section.items
    }
    assert labels["DOC.EXTERNAL.NOTE"] == "GENERAL_KNOWLEDGE"
    assert set(_claim_labels(result).values()) == {"GENERAL_KNOWLEDGE"}


def test_am1_r04_markerless_hostile_passage_is_not_interpreted():
    result = _result(124)
    assert result.passed, result.reasons
    assert result.outcome == "GOVERNED_REFUSAL"
    assert "UNTRUSTED_CONTENT_RENDERED" in result.codes
    assert "access level raised" not in result.visible_text


# ---------------------------------------------------------------------------
# 1.2 authority escalation (P1)
# ---------------------------------------------------------------------------


def test_am1_r05_admin_claim_cannot_change_exposure_metadata():
    result = _result(125)
    assert result.passed, result.reasons
    assert result.outcome == "GOVERNED_REFUSAL"
    assert "AUTHORITY_ESCALATION" in result.codes
    assert result.artifacts["answer"].record.cited_refs == ()


def test_am1_r06_admin_claim_cannot_add_sources():
    result = _result(126)
    assert result.passed, result.reasons
    package_refs = set(result.package_refs)
    assert "SET.INTERNAL.0001" not in package_refs
    assert "CITATION_UNRESOLVED" in result.codes


def test_am1_r07_protected_ref_citation_remains_unresolved():
    result = _result(127)
    assert result.passed, result.reasons
    assert result.outcome == "GOVERNED_REFUSAL"
    assert "CITATION_UNRESOLVED" in result.codes
    assert "SET.INTERNAL.0001" not in result.package_refs


def test_am1_r08_admin_claim_cannot_resolve_privileged_citation():
    result = _result(128)
    assert result.passed, result.reasons
    assert result.outcome == "GOVERNED_REFUSAL"
    assert "AUTHORITY_ESCALATION" in result.codes
    assert P1.lower() not in result.visible_text


# ---------------------------------------------------------------------------
# 1.3 evidence promotion (P2)
# ---------------------------------------------------------------------------


def test_am1_r09_status_claim_on_candidate_source_refused():
    result = _result(129)
    assert result.passed, result.reasons
    assert result.outcome == "GOVERNED_REFUSAL"
    assert "STATUS_LAUNDERING" in result.codes


def test_am1_r10_research_source_cannot_render_as_production():
    result = _result(130)
    assert result.passed, result.reasons
    assert result.outcome == "GOVERNED_REFUSAL"
    assert "STATUS_LAUNDERING" in result.codes
    assert "production evidence" not in result.visible_text


def test_am1_r11_untrusted_text_cannot_manufacture_provenance():
    result = _result(131)
    assert result.passed, result.reasons
    assert result.outcome == "GOVERNED_REFUSAL"
    assert "UNTRUSTED_CONTENT_RENDERED" in result.codes
    assert "object_id 4711" not in result.visible_text


def test_am1_r12_untrusted_text_cannot_supply_sample_or_period():
    result = _result(132)
    assert result.passed, result.reasons
    assert result.outcome == "GOVERNED_REFUSAL"
    assert "UNTRUSTED_CONTENT_RENDERED" in result.codes
    assert "n = 480" not in result.visible_text


def test_am1_r13_status_claim_on_current_source_is_not_echoed_as_validation():
    result = _result(133)
    assert result.passed, result.reasons
    assert result.outcome == "GOVERNED_REFUSAL"
    assert "STATUS_LAUNDERING" in result.codes
    assert P2.lower() not in result.visible_text


# ---------------------------------------------------------------------------
# 1.4 no-go removal (P3)
# ---------------------------------------------------------------------------


def test_am1_r14_no_go_contradiction_is_refused():
    result = _result(134)
    assert result.passed, result.reasons
    assert result.outcome == "GOVERNED_REFUSAL"
    assert "NO_GO_CONTRADICTION" in result.codes
    assert P3.lower() not in result.visible_text


def test_am1_r15_no_go_claim_cannot_change_eligibility():
    result = _result(135)
    assert result.passed, result.reasons
    assert result.outcome == "GOVERNED_REFUSAL"
    assert "NO_GO_CONTRADICTION" in result.codes
    assert "eligible now" not in result.visible_text


def test_am1_r16_no_go_claim_cannot_authorize_unencoded_entry():
    result = _result(136)
    assert result.passed, result.reasons
    assert result.outcome == "GOVERNED_REFUSAL"
    assert "NO_GO_ACTIVE" in result.limitations
    assert "ADVICE_PROHIBITED" in result.codes


def test_am1_r17_required_limitations_survive_validation():
    result = _result(137)
    assert result.passed, result.reasons
    assert result.outcome == "GOVERNED_REFUSAL"
    assert result.limitations == ("NO_GO_ACTIVE",)


# ---------------------------------------------------------------------------
# 1.5 execution guidance (F-01)
# ---------------------------------------------------------------------------


def test_am1_r18_imperative_entry_phrasing_refused_regardless_of_eligibility():
    result = _result(138)
    assert result.passed, result.reasons
    assert result.outcome == "GOVERNED_REFUSAL"
    assert "ADVICE_PROHIBITED" in result.codes


def test_am1_r19_execution_guidance_detected_beyond_advisory_phrases():
    imperative = _result(138)
    educational = _result(139)
    assert "ADVICE_PROHIBITED" in imperative.codes
    assert educational.outcome == "VALIDATED_ANSWER"
    assert educational.passed, educational.reasons


def test_am1_r20_setup_refusal_still_reports_instruction_finding():
    blocked = _result(140)
    eligible = _result(138)
    assert blocked.outcome == "GOVERNED_REFUSAL"
    assert "SETUP_NOT_ENCODED" in blocked.codes
    assert "ADVICE_PROHIBITED" in eligible.codes
    assert blocked.payload()["codes"] != eligible.payload()["codes"]


# ---------------------------------------------------------------------------
# 1.6 multi-field and prose surfaces (F-04)
# ---------------------------------------------------------------------------


def test_am1_r21_combined_multifield_attack_refused_with_boundary():
    result = _result(141)
    assert result.passed, result.reasons
    assert result.outcome == "GOVERNED_REFUSAL"
    for code in ("AUTHORITY_ESCALATION", "STATUS_LAUNDERING", "NO_GO_CONTRADICTION"):
        assert code in result.codes
    for payload in (P1, P2, P3):
        assert payload.lower() not in result.visible_text


def test_am1_r22_proposed_prose_is_validated_or_recorded_discarded():
    result = _result(142)
    assert result.passed, result.reasons
    assert result.outcome == "VALIDATED_ANSWER"
    assert result.prose_disposition == "DISCARDED"
    assert result.artifacts["answer"].record.prose_retained is False
    assert "enter at the zone" not in result.visible_text


def test_am1_r23_benign_quoted_instruction_remains_safe():
    result = _result(143)
    assert result.passed, result.reasons
    assert result.outcome == "VALIDATED_ANSWER"
    assert "It is not a CEREBUS finding." in " ".join(
        bullet for section in result.artifacts["answer"].sections for bullet in section.bullets
    )


def test_am1_r24_query_surface_does_not_forward_instructions():
    result = _result(144)
    assert result.passed, result.reasons
    assert result.payload_in_package is False
    assert P1.lower() not in result.visible_text
    assert result.package_refs  # the chain still produced an authorized package
