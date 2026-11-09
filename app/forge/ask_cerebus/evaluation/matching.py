"""Claim, citation and value matching between expectations and observations.

Matching is deliberately independent of the answer compiler: it reads only the
public payload of a validated answer or governed refusal. It never recomputes a
claim, a number or a label; it compares them to the case's literal expectation.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import Any, Iterable, Mapping

from app.forge.ask_cerebus.evaluation import enums
from app.forge.ask_cerebus.evaluation.schema import EvaluationCase, EvaluationExecution

_WHITESPACE = re.compile(r"\s+")


def normalise(text: str) -> str:
    return _WHITESPACE.sub(" ", str(text).casefold()).strip()


def visible_text(payload: Mapping[str, Any]) -> str:
    """The text a reader would actually see, without record metadata."""

    parts: list[str] = []
    for key in ("detail", "outcome", "answer_refusal_code", "as_of", "depth"):
        value = payload.get(key)
        if isinstance(value, str) and value:
            parts.append(value)
    for section in payload.get("sections", ()):  # type: ignore[union-attr]
        if isinstance(section, Mapping):
            parts.extend(str(bullet) for bullet in section.get("bullets", ()))
    for claim in payload.get("claims", ()):  # type: ignore[union-attr]
        if isinstance(claim, Mapping):
            parts.append(str(claim.get("text", "")))
    parts.extend(str(item) for item in payload.get("limitations", ()))
    return normalise(" ".join(parts))


def payload_text(payload: Mapping[str, Any]) -> str:
    """Flatten an answer payload into searchable text (order-stable)."""

    parts: list[str] = []
    for key in ("detail", "prose", "as_of", "depth", "answer_refusal_code", "outcome"):
        value = payload.get(key)
        if isinstance(value, str) and value:
            parts.append(value)
    for section in payload.get("sections", ()):  # type: ignore[union-attr]
        if isinstance(section, Mapping):
            parts.append(str(section.get("section_id", "")))
            parts.extend(str(bullet) for bullet in section.get("bullets", ()))
    for claim in payload.get("claims", ()):  # type: ignore[union-attr]
        if isinstance(claim, Mapping):
            parts.append(str(claim.get("text", "")))
            parts.extend(str(ref) for ref in claim.get("source_refs", ()))
            parts.extend(str(ref) for ref in claim.get("citation_ids", ()))
            for key in ("epistemic_label", "layer", "generation", "section_id"):
                parts.append(str(claim.get(key, "")))
    for citation in payload.get("citations", ()):  # type: ignore[union-attr]
        if isinstance(citation, Mapping):
            parts.append(str(citation.get("source_ref_id", "")))
            parts.append(str(citation.get("generation", "")))
            parts.extend(str(ref) for ref in citation.get("provenance_refs", ()))
    parts.extend(str(item) for item in payload.get("limitations", ()))
    parts.extend(str(item) for item in payload.get("findings", ()))
    record = payload.get("record")
    if isinstance(record, Mapping):
        parts.append(json.dumps(record, sort_keys=True))
    return normalise(" ".join(parts))


@dataclass(frozen=True)
class CaseMatch:
    case_id: str
    passed: bool
    outcome_matches: bool
    refusal_code_matches: bool
    forbidden_numbers_absent: bool
    forbidden_claims_absent: bool
    required_claims_present: bool
    required_limitations_present: bool
    citations_present: bool
    fields_present: bool
    expected_finding_seen: bool
    observed_codes: tuple[str, ...]
    observed_finding_classes: tuple[str, ...]
    reasons: tuple[str, ...]

    def payload(self) -> dict[str, Any]:
        return {
            "case_id": self.case_id,
            "passed": self.passed,
            "outcome_matches": self.outcome_matches,
            "refusal_code_matches": self.refusal_code_matches,
            "forbidden_numbers_absent": self.forbidden_numbers_absent,
            "forbidden_claims_absent": self.forbidden_claims_absent,
            "required_claims_present": self.required_claims_present,
            "required_limitations_present": self.required_limitations_present,
            "citations_present": self.citations_present,
            "fields_present": self.fields_present,
            "expected_finding_seen": self.expected_finding_seen,
            "observed_codes": list(self.observed_codes),
            "observed_finding_classes": list(self.observed_finding_classes),
            "reasons": list(self.reasons),
        }


def _tokens_present(text: str, tokens: Iterable[str]) -> tuple[bool, tuple[str, ...]]:
    missing = tuple(token for token in tokens if normalise(token) not in text)
    return not missing, missing


def _tokens_absent(text: str, tokens: Iterable[str]) -> tuple[bool, tuple[str, ...]]:
    present = tuple(token for token in tokens if normalise(token) in text)
    return not present, present


def _payload(execution: EvaluationExecution) -> Mapping[str, Any]:
    answer = execution.artifacts.get("answer")
    return answer.payload() if hasattr(answer, "payload") else {}


def match_case(case: EvaluationCase, execution: EvaluationExecution) -> CaseMatch:
    payload = _payload(execution)
    text = payload_text(payload)
    visible = visible_text(payload)
    reasons: list[str] = []

    validated = execution.outcome == "VALIDATED_ANSWER"
    outcome_matches = validated == case.is_positive
    if not outcome_matches:
        reasons.append(
            "expected ANSWER, observed refusal"
            if case.is_positive
            else "expected REFUSAL, observed answer"
        )

    code = payload.get("answer_refusal_code")
    if case.is_positive:
        refusal_code_matches = code is None
    else:
        refusal_code_matches = code == case.expected_refusal_code
        if not refusal_code_matches:
            reasons.append(f"refusal code {code} != {case.expected_refusal_code}")

    numbers_absent, numbers_found = _tokens_absent(visible, case.forbidden_numbers)
    if not numbers_absent:
        reasons.append(f"forbidden numbers emitted: {numbers_found}")

    claims_absent, claims_found = _tokens_absent(
        visible, tuple(claim.token for claim in case.forbidden_claims)
    )
    if not claims_absent:
        reasons.append(f"forbidden claims emitted: {claims_found}")

    required_present, missing = _tokens_present(
        text, tuple(claim.token for claim in case.required_claims)
    )
    if not required_present:
        reasons.append(f"required claims missing: {missing}")

    limitations_present, missing_limits = _tokens_present(text, case.required_limitations)
    if not limitations_present:
        reasons.append(f"required limitations missing: {missing_limits}")

    citations = set()
    for citation in payload.get("citations", ()):  # type: ignore[union-attr]
        if isinstance(citation, Mapping) and citation.get("source_ref_id"):
            citations.add(str(citation["source_ref_id"]))
    for claim in payload.get("claims", ()):  # type: ignore[union-attr]
        if isinstance(claim, Mapping):
            citations.update(str(ref) for ref in claim.get("source_refs", ()))
    citations_present = all(ref in citations or normalise(ref) in text for ref in case.expected_citations)
    if not citations_present:
        missing_citations = tuple(ref for ref in case.expected_citations if ref not in citations and normalise(ref) not in text)
        reasons.append(f"expected citations missing: {missing_citations}")

    sections = {
        str(section.get("section_id"))
        for section in payload.get("sections", ())  # type: ignore[union-attr]
        if isinstance(section, Mapping)
    }
    if case.is_positive and case.required_fields:
        missing_fields = tuple(field for field in case.required_fields if field not in sections)
        fields_present = not missing_fields
        if missing_fields:
            reasons.append(f"required fields missing: {missing_fields}")
    else:
        fields_present = True

    observed_codes = tuple(str(item) for item in payload.get("findings", ()))
    classes = tuple(
        sorted(
            {code_for(value).value for value in observed_codes if code_for(value) is not None}
        )
    )
    expected_seen = (
        case.expected_finding_class is None
        or case.expected_finding_class.value in classes
        or case.expected_finding_class.value in observed_codes
    )
    if not expected_seen:
        reasons.append(
            f"expected finding class {case.expected_finding_class.value} not observed in {observed_codes}"
        )

    validation_declared = all(code_name in observed_codes for code_name in case.expected_validation_codes)
    if not validation_declared:
        missing_validation = tuple(
            name for name in case.expected_validation_codes if name not in observed_codes
        )
        reasons.append(f"expected validation codes missing: {missing_validation}")

    passed = all(
        (
            outcome_matches,
            refusal_code_matches,
            numbers_absent,
            claims_absent,
            required_present,
            limitations_present,
            citations_present,
            fields_present,
            expected_seen,
            validation_declared,
        )
    )
    return CaseMatch(
        case_id=case.case_id,
        passed=passed,
        outcome_matches=outcome_matches,
        refusal_code_matches=refusal_code_matches,
        forbidden_numbers_absent=numbers_absent,
        forbidden_claims_absent=claims_absent,
        required_claims_present=required_present,
        required_limitations_present=limitations_present,
        citations_present=citations_present,
        fields_present=fields_present,
        expected_finding_seen=expected_seen,
        observed_codes=observed_codes,
        observed_finding_classes=classes,
        reasons=tuple(reasons),
    )


def code_for(validation_code: str) -> enums.FindingCode | None:
    """Map a validation code to a finding class (ACCEPTANCE.md §3)."""

    from app.forge.ask_cerebus.evaluation.findings import finding_class_for

    return finding_class_for(validation_code)


def match_all(
    cases: Iterable[EvaluationCase], executions: Iterable[EvaluationExecution]
) -> tuple[CaseMatch, ...]:
    by_id = {execution.case_id: execution for execution in executions}
    matches = []
    for case in cases:
        execution = by_id.get(case.case_id)
        if execution is None:
            continue
        matches.append(match_case(case, execution))
    return tuple(matches)
