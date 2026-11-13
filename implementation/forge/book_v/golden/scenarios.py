"""Book V golden presentation scenarios.

Each scenario maps to a frozen Q5 scenario (Book IV bloc IV.5 fixture) and
records the input digest, expected outcome, expected presentation fields,
requirement mapping, and test mapping. Scenarios are read-only; Book V must
not edit them and must not mutate EV-001–EV-178 or Q1–Q5.

Input digest = SHA-256 of the canonical JSON of the IV.5 DTO payload
(ValidatedAnswer or GovernedAnswerRefusal), computed at fixture-authoring
time and pinned here as a regression guard.
"""

from __future__ import annotations

import hashlib
import importlib.util
import json
import sys
from dataclasses import replace
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[4]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

spec = importlib.util.spec_from_file_location(
    "q5_scenarios_golden",
    ROOT / "implementation/forge/book_iv/bloc_iv_5/fixtures/scenarios.py",
)
assert spec is not None and spec.loader is not None
q5_module = importlib.util.module_from_spec(spec)
sys.modules["q5_scenarios_golden"] = q5_module
spec.loader.exec_module(q5_module)

from app.forge.ask_cerebus.answer import validate_answer  # noqa: E402
from app.forge.ask_cerebus.answer.enums import (  # noqa: E402
    AnswerDepth,
    AnswerOutcome,
    AnswerRefusalCode,
)
from app.forge.ask_cerebus.answer.schema import (  # noqa: E402
    FinalResponseRecord,
    GovernedAnswerRefusal,
    ValidatedAnswer,
)
from app.forge.ask_cerebus.answer.versions import (  # noqa: E402
    ANSWER_RECORD_V1,
    ANSWER_SECTION_SCHEMA_V1,
    ASK_ANSWER_CONTRACT_V1,
    VALIDATOR_SET_V1,
)

Q5_CASES = {scenario.id: scenario for scenario in q5_module.cases()}


def _dto(case_id: str) -> ValidatedAnswer | GovernedAnswerRefusal:
    return validate_answer(Q5_CASES[case_id].draft, Q5_CASES[case_id].package)


def _digest(dto: ValidatedAnswer | GovernedAnswerRefusal) -> str:
    payload = dto.payload(include_record=True)
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _record(
    *,
    outcome: AnswerOutcome,
    answer_id: str,
    depth: str,
    refusal_code: AnswerRefusalCode | None = None,
) -> FinalResponseRecord:
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
        query_plan_id="QP.GOLDEN",
        route_id="ROUTE.GOLDEN",
        route_policy_version="POL.V1",
        prompt_id="PROMPT.GOLDEN",
        prompt_version="V1",
        provider="fake",
        model="fake-model-1",
        answer_refusal_code=refusal_code.value if refusal_code else "",
        as_of="",
    )


# ---------------------------------------------------------------------------
# Golden scenario inventory
#
# Each entry:
#   id            - unique scenario ID
#   q5_case       - source Q5 scenario ID (None if synthetic DTO)
#   input_digest  - SHA-256 of the IV.5 DTO payload (pinned)
#   expected_outcome - "VALIDATED_ANSWER" or "GOVERNED_REFUSAL"
#   expected_code - refusal code (refusals only)
#   expected_depth - BEGINNER / OPERATOR / RESEARCHER
#   expected_fields - presentation fields that must be present
#   requirement_ids - admitted requirement IDs covered
#   test_names - test names covering this scenario
# ---------------------------------------------------------------------------

GOLDEN_SCENARIOS: list[dict[str, Any]] = [
    # --- Three valid depths -----------------------------------------------
    {
        "id": "BV-GOLDEN-01",
        "q5_case": "Q5-01",
        "input_digest": _digest(_dto("Q5-01")),
        "expected_outcome": "VALIDATED_ANSWER",
        "expected_code": None,
        "expected_depth": "BEGINNER",
        "expected_fields": [
            "answer_id", "depth", "sections", "claims", "citations",
            "limitations", "as_of", "record",
        ],
        "requirement_ids": ["BV-F1-01", "BV-F1-03", "BV-F1-04", "BV-F1-05", "BV-F1-06"],
        "test_names": ["test_bv_renders_validated_answer", "test_bv_displays_answer_id", "test_bv_depth_layout"],
    },
    {
        "id": "BV-GOLDEN-02",
        "q5_case": "Q5-03",
        "input_digest": _digest(_dto("Q5-03")),
        "expected_outcome": "VALIDATED_ANSWER",
        "expected_code": None,
        "expected_depth": "OPERATOR",
        "expected_fields": [
            "answer_id", "depth", "sections", "claims", "citations", "numbers",
            "limitations", "as_of", "record",
        ],
        "requirement_ids": ["BV-F1-01", "BV-F1-03", "BV-F1-04", "BV-F1-05", "BV-F1-06", "BV-F1-07"],
        "test_names": ["test_bv_renders_validated_answer", "test_bv_shows_setup_verdict", "test_bv_depth_layout"],
    },
    {
        "id": "BV-GOLDEN-03",
        "q5_case": "Q5-05",
        "input_digest": _digest(_dto("Q5-05")),
        "expected_outcome": "VALIDATED_ANSWER",
        "expected_code": None,
        "expected_depth": "RESEARCHER",
        "expected_fields": [
            "answer_id", "depth", "sections", "claims", "citations", "numbers",
            "limitations", "as_of", "record",
        ],
        "requirement_ids": ["BV-F1-01", "BV-F1-04", "BV-F1-05", "BV-F1-06"],
        "test_names": ["test_bv_renders_validated_answer", "test_bv_citation_shows_generation", "test_bv_shows_epistemic_label", "test_bv_depth_layout"],
    },

    # --- Six refusal codes -------------------------------------------------
    {
        "id": "BV-GOLDEN-04",
        "q5_case": "Q5-43",
        "input_digest": _digest(_dto("Q5-43")),
        "expected_outcome": "GOVERNED_REFUSAL",
        "expected_code": "ACCESS_NOT_ENTITLED",
        "expected_depth": "OPERATOR",
        "expected_fields": ["answer_id", "code", "detail", "findings", "limitations", "depth", "record"],
        "requirement_ids": ["BV-F1-02", "BV-F1-09", "BV-F2-01"],
        "test_names": ["test_bv_renders_governed_refusal", "test_bv_refusal_component", "test_bv_preserves_limitations", "test_bv_six_code_refusal_preservation"],
    },
    {
        "id": "BV-GOLDEN-05",
        "q5_case": "Q5-44",
        "input_digest": _digest(_dto("Q5-44")),
        "expected_outcome": "GOVERNED_REFUSAL",
        "expected_code": "AMBIGUOUS_SCOPE",
        "expected_depth": "BEGINNER",
        "expected_fields": ["answer_id", "code", "detail", "findings", "limitations", "depth", "record"],
        "requirement_ids": ["BV-F1-02", "BV-F2-01"],
        "test_names": ["test_bv_renders_governed_refusal", "test_bv_refusal_component", "test_bv_six_code_refusal_preservation"],
    },
    {
        "id": "BV-GOLDEN-06",
        "q5_case": "Q5-42",
        "input_digest": _digest(_dto("Q5-42")),
        "expected_outcome": "GOVERNED_REFUSAL",
        "expected_code": "MODEL_VERSION_UNAVAILABLE",
        "expected_depth": "RESEARCHER",
        "expected_fields": ["answer_id", "code", "detail", "findings", "limitations", "depth", "record"],
        "requirement_ids": ["BV-F1-02", "BV-F2-01"],
        "test_names": ["test_bv_renders_governed_refusal", "test_bv_refusal_component", "test_bv_six_code_refusal_preservation"],
    },
    {
        "id": "BV-GOLDEN-07",
        "q5_case": "Q5-41",
        "input_digest": _digest(_dto("Q5-41")),
        "expected_outcome": "GOVERNED_REFUSAL",
        "expected_code": "CURRENT_DATA_UNAVAILABLE",
        "expected_depth": "OPERATOR",
        "expected_fields": ["answer_id", "code", "detail", "findings", "limitations", "depth", "record"],
        "requirement_ids": ["BV-F1-02", "BV-F2-01"],
        "test_names": ["test_bv_renders_governed_refusal", "test_bv_refusal_component", "test_bv_six_code_refusal_preservation"],
    },
    {
        "id": "BV-GOLDEN-08",
        "q5_case": "Q5-25",
        "input_digest": _digest(_dto("Q5-25")),
        "expected_outcome": "GOVERNED_REFUSAL",
        "expected_code": "SETUP_NOT_ENCODED",
        "expected_depth": "OPERATOR",
        "expected_fields": ["answer_id", "code", "detail", "findings", "limitations", "depth", "record"],
        "requirement_ids": ["BV-F1-02", "BV-F1-07", "BV-F1-09", "BV-F2-01"],
        "test_names": ["test_bv_renders_governed_refusal", "test_bv_shows_setup_verdict", "test_bv_refusal_component", "test_bv_six_code_refusal_preservation"],
    },
    {
        "id": "BV-GOLDEN-09",
        "q5_case": "Q5-07",
        "input_digest": _digest(_dto("Q5-07")),
        "expected_outcome": "GOVERNED_REFUSAL",
        "expected_code": "INSUFFICIENT_EVIDENCE",
        "expected_depth": "OPERATOR",
        "expected_fields": ["answer_id", "code", "detail", "findings", "limitations", "depth", "record"],
        "requirement_ids": ["BV-F1-02", "BV-F1-08", "BV-F2-01"],
        "test_names": ["test_bv_renders_governed_refusal", "test_bv_refuses_unsupported_statistic", "test_bv_refusal_component", "test_bv_six_code_refusal_preservation"],
    },

    # --- Historical model explanation -------------------------------------
    {
        "id": "BV-GOLDEN-10",
        "q5_case": "Q5-31",
        "input_digest": _digest(_dto("Q5-31")),
        "expected_outcome": "GOVERNED_REFUSAL",
        "expected_code": "CURRENT_DATA_UNAVAILABLE",
        "expected_depth": "BEGINNER",
        "expected_fields": ["answer_id", "code", "detail", "depth", "record"],
        "requirement_ids": ["BV-F1-02", "BV-F2-01"],
        "test_names": ["test_bv_no_historical_to_current_promotion", "test_bv_six_code_refusal_preservation"],
    },

    # --- Current-data unavailable -----------------------------------------
    {
        "id": "BV-GOLDEN-11",
        "q5_case": "Q5-34",
        "input_digest": _digest(_dto("Q5-34")),
        "expected_outcome": "GOVERNED_REFUSAL",
        "expected_code": "CURRENT_DATA_UNAVAILABLE",
        "expected_depth": "OPERATOR",
        "expected_fields": ["answer_id", "code", "detail", "depth", "record"],
        "requirement_ids": ["BV-F1-02", "BV-F2-01"],
        "test_names": ["test_bv_six_code_refusal_preservation"],
    },

    # --- Unsupported statistics -------------------------------------------
    {
        "id": "BV-GOLDEN-12",
        "q5_case": "Q5-08",
        "input_digest": _digest(_dto("Q5-08")),
        "expected_outcome": "GOVERNED_REFUSAL",
        "expected_code": "INSUFFICIENT_EVIDENCE",
        "expected_depth": "RESEARCHER",
        "expected_fields": ["answer_id", "code", "detail", "findings", "numbers", "depth", "record"],
        "requirement_ids": ["BV-F1-02", "BV-F1-08"],
        "test_names": ["test_bv_refuses_unsupported_statistic", "test_bv_no_fabricated_numerical_claims", "test_bv_six_code_refusal_preservation"],
    },

    # --- No-go active ------------------------------------------------------
    {
        "id": "BV-GOLDEN-13",
        "q5_case": "Q5-25",
        "input_digest": _digest(_dto("Q5-25")),
        "expected_outcome": "GOVERNED_REFUSAL",
        "expected_code": "SETUP_NOT_ENCODED",
        "expected_depth": "OPERATOR",
        "expected_fields": ["answer_id", "code", "detail", "limitations", "depth", "record"],
        "requirement_ids": ["BV-F1-02", "BV-F1-07", "BV-F1-09"],
        "test_names": ["test_bv_no_go_preserved", "test_bv_six_code_refusal_preservation"],
    },

    # --- Access not entitled -----------------------------------------------
    {
        "id": "BV-GOLDEN-14",
        "q5_case": "Q5-43",
        "input_digest": _digest(_dto("Q5-43")),
        "expected_outcome": "GOVERNED_REFUSAL",
        "expected_code": "ACCESS_NOT_ENTITLED",
        "expected_depth": "OPERATOR",
        "expected_fields": ["answer_id", "code", "detail", "depth", "record"],
        "requirement_ids": ["BV-F1-02", "BV-F2-01"],
        "test_names": ["test_bv_entitlement_preserved", "test_bv_six_code_refusal_preservation"],
    },

    # --- Safe citation presentation ----------------------------------------
    {
        "id": "BV-GOLDEN-15",
        "q5_case": "Q5-05",
        "input_digest": _digest(_dto("Q5-05")),
        "expected_outcome": "VALIDATED_ANSWER",
        "expected_code": None,
        "expected_depth": "RESEARCHER",
        "expected_fields": ["citations", "claims", "sections"],
        "requirement_ids": ["BV-F1-01", "BV-F1-04"],
        "test_names": ["test_bv_renders_validated_answer", "test_bv_citation_shows_generation", "test_bv_dto_surfaces_are_read_only"],
    },

    # --- Missing citation rejection (IV.5 governs; Book V preserves) ------
    {
        "id": "BV-GOLDEN-16",
        "q5_case": "Q5-19",
        "input_digest": _digest(_dto("Q5-19")),
        "expected_outcome": "GOVERNED_REFUSAL",
        "expected_code": "INSUFFICIENT_EVIDENCE",
        "expected_depth": "OPERATOR",
        "expected_fields": ["answer_id", "code", "detail", "findings", "depth", "record"],
        "requirement_ids": ["BV-F1-02"],
        "test_names": ["test_bv_six_code_refusal_preservation"],
    },

    # --- Generation mismatch rejection (IV.5 governs; Book V preserves) --
    # Synthetic DTO: claim generation does not match source generation.
    {
        "id": "BV-GOLDEN-17",
        "q5_case": None,
        "input_digest": None,  # computed below for synthetic DTO
        "expected_outcome": "GOVERNED_REFUSAL",
        "expected_code": "INSUFFICIENT_EVIDENCE",
        "expected_depth": "RESEARCHER",
        "expected_fields": ["answer_id", "code", "detail", "depth", "record"],
        "requirement_ids": ["BV-F1-02"],
        "test_names": ["test_bv_six_code_refusal_preservation"],
    },

    # --- Untrusted-source containment -------------------------------------
    {
        "id": "BV-GOLDEN-18",
        "q5_case": "Q5-39",
        "input_digest": _digest(_dto("Q5-39")),
        "expected_outcome": "GOVERNED_REFUSAL",
        "expected_code": "ACCESS_NOT_ENTITLED",
        "expected_depth": "OPERATOR",
        "expected_fields": ["answer_id", "code", "detail", "depth", "record"],
        "requirement_ids": ["BV-F1-02", "BV-F2-01"],
        "test_names": ["test_bv_entitlement_preserved", "test_bv_six_code_refusal_preservation"],
    },

    # --- Prompt-injection containment -------------------------------------
    # Synthetic DTO: raw GatewayDraft is rejected by the adapter.
    {
        "id": "BV-GOLDEN-19",
        "q5_case": None,
        "input_digest": None,  # n/a — input is a GatewayDraft, not an IV.5 DTO
        "expected_outcome": "PRESENTATION_REJECTED",
        "expected_code": None,
        "expected_depth": None,
        "expected_fields": [],
        "requirement_ids": ["BV-F1-10"],
        "test_names": ["test_bv_no_raw_draft_in_ui", "test_bv_malformed_input_rejection"],
    },
]

# Compute digest for the synthetic generation-mismatch scenario.
for _scenario in GOLDEN_SCENARIOS:
    if _scenario["id"] == "BV-GOLDEN-17":
        _synthetic = GovernedAnswerRefusal(
            answer_id="ANS." + "0" * 32,
            code=AnswerRefusalCode.INSUFFICIENT_EVIDENCE,
            detail="Claim generation does not match the source record's generation.",
            depth=AnswerDepth.RESEARCHER,
            findings=("GENERATION_LAUNDERING",),
            record=_record(
                outcome=AnswerOutcome.GOVERNED_REFUSAL,
                answer_id="ANS." + "0" * 32,
                depth="RESEARCHER",
                refusal_code=AnswerRefusalCode.INSUFFICIENT_EVIDENCE,
            ),
            limitations=(),
        )
        _scenario["input_digest"] = _digest(_synthetic)


def scenarios() -> tuple[dict[str, Any], ...]:
    return tuple(GOLDEN_SCENARIOS)


def scenario(scenario_id: str) -> dict[str, Any]:
    for s in GOLDEN_SCENARIOS:
        if s["id"] == scenario_id:
            return s
    raise KeyError(scenario_id)


def ids() -> tuple[str, ...]:
    return tuple(s["id"] for s in GOLDEN_SCENARIOS)


__all__ = ["scenarios", "scenario", "ids", "GOLDEN_SCENARIOS"]
