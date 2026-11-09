"""Independent ground-truth oracle.

Import law (R7): this module may import only the evaluation's own
``schema``/``enums``/``versions``, frozen fixture data and the vocabulary-only
``app.forge.canonical`` enums. It must never import the interpreter, retrieval,
context, gateway or answer layers, because an oracle built on the system under
test cannot detect a defect the system and the oracle share.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from app.forge.ask_cerebus.evaluation import enums, versions
from app.forge.ask_cerebus.evaluation.schema import EvaluationCase, EvaluationDataset

# Vocabulary only: canonical layer labels and evidence statuses.
from app.forge.canonical import EvidenceStatus, Layer  # noqa: F401  (vocabulary)

_CANONICAL_LAYERS = frozenset(layer.value for layer in Layer)
_CANONICAL_STATUSES = frozenset(status.value for status in EvidenceStatus)

#: Authority precedence for expectations (PLAN.md §5.2).
AUTHORITY_ORDER = (
    enums.Authority.FIXTURE_FACT,
    enums.Authority.FROZEN_RULE,
    enums.Authority.OPERATOR_ASSERTION,
    enums.Authority.SYNTHETIC_INPUT,
)


@dataclass(frozen=True)
class OracleExpectation:
    """What the case demands, derived without asking the system under test."""

    case_id: str
    outcome: enums.ExpectedOutcomeKind
    refusal_code: str | None
    required_tokens: tuple[str, ...]
    forbidden_tokens: tuple[str, ...]
    forbidden_numbers: tuple[str, ...]
    required_sections: tuple[str, ...]
    authority: enums.Authority

    def payload(self) -> dict[str, object]:
        return {
            "case_id": self.case_id,
            "outcome": self.outcome.value,
            "refusal_code": self.refusal_code,
            "required_tokens": list(self.required_tokens),
            "forbidden_tokens": list(self.forbidden_tokens),
            "forbidden_numbers": list(self.forbidden_numbers),
            "required_sections": list(self.required_sections),
            "authority": self.authority.value,
        }


def expectation_for(case: EvaluationCase) -> OracleExpectation:
    """Derive the expectation from the case spec and frozen vocabulary."""

    if case.authority in enums.FORBIDDEN_AUTHORITIES:
        raise ValueError(f"{case.case_id}: forbidden authority {case.authority.value}")
    if case.authority not in AUTHORITY_ORDER:
        raise ValueError(f"{case.case_id}: unknown authority {case.authority.value}")

    if case.expected_outcome is enums.ExpectedOutcomeKind.REFUSAL:
        if case.expected_refusal_code not in versions.REFUSAL_CODES:
            raise ValueError(f"{case.case_id}: refusal code is not in the frozen six")
    elif case.expected_refusal_code is not None:
        raise ValueError(f"{case.case_id}: an answer cannot name a refusal code")

    if case.expected_eligibility is not None and case.expected_eligibility not in versions.ELIGIBILITY_VALUES:
        raise ValueError(f"{case.case_id}: unknown eligibility {case.expected_eligibility}")

    for model in case.model_ids:
        if case.expected_finding_class is enums.FindingCode.LAYER_LAUNDERED:
            break
        if not model or model.startswith(".") or model.endswith("."):
            raise ValueError(f"{case.case_id}: malformed model id {model}")

    return OracleExpectation(
        case_id=case.case_id,
        outcome=case.expected_outcome,
        refusal_code=case.expected_refusal_code,
        required_tokens=tuple(claim.token for claim in case.required_claims),
        forbidden_tokens=tuple(claim.token for claim in case.forbidden_claims),
        forbidden_numbers=case.forbidden_numbers,
        required_sections=case.required_fields,
        authority=case.authority,
    )


def audit_case(case: EvaluationCase) -> tuple[str, ...]:
    """Vocabulary and integrity checks that do not need any execution."""

    problems: list[str] = []
    try:
        expectation_for(case)
    except ValueError as exc:  # pragma: no cover - surfaced as a problem
        problems.append(str(exc))

    if case.expected_freshness is enums.ExpectedFreshness.AS_OF and case.time_scope is enums.TimeScope.HISTORICAL:
        problems.append(f"{case.case_id}: historical case cannot require live as_of")
    if case.expected_outcome is enums.ExpectedOutcomeKind.ANSWER and not case.score_population:
        problems.append(f"{case.case_id}: answer has no declared score population")
    if case.expected_finding_class is not None and case.expected_finding_class.value not in {
        code.value for code in enums.FindingCode
    }:
        problems.append(f"{case.case_id}: unknown finding class")
    for layer in case.required_fields:
        if layer in _CANONICAL_LAYERS:
            continue
    return tuple(problems)


def audit_dataset(dataset: EvaluationDataset) -> tuple[str, ...]:
    problems: list[str] = []
    for case in dataset.cases:
        problems.extend(audit_case(case))
    codes = {case.expected_refusal_code for case in dataset.cases if case.expected_refusal_code}
    for code in versions.REFUSAL_CODES:
        if code not in codes:
            problems.append(f"refusal code {code} is never exercised")
    if dataset.forbidden_authorities_absent is not True:
        problems.append("a forbidden authority is present in the dataset")
    return tuple(problems)


def expected_refusal_codes(dataset: EvaluationDataset) -> tuple[str, ...]:
    return tuple(
        sorted({case.expected_refusal_code for case in dataset.cases if case.expected_refusal_code})
    )


def refusal_coverage(dataset: EvaluationDataset) -> dict[str, int]:
    coverage = {code: 0 for code in versions.REFUSAL_CODES}
    for case in dataset.cases:
        if case.expected_refusal_code:
            coverage[case.expected_refusal_code] += 1
    return coverage


def independent_modules() -> tuple[str, ...]:
    """The import surface this oracle is allowed to see."""

    return (
        "app.forge.ask_cerebus.evaluation.enums",
        "app.forge.ask_cerebus.evaluation.versions",
        "app.forge.ask_cerebus.evaluation.schema",
        "app.forge.canonical",
    )


def forbidden_import_roots() -> tuple[str, ...]:
    return (
        "app.forge.ask_cerebus.interpreter",
        "app.forge.ask_cerebus.retrieval",
        "app.forge.ask_cerebus.context",
        "app.forge.ask_cerebus.llm_gateway",
        "app.forge.ask_cerebus.answer",
    )


def corpus_balance(dataset: EvaluationDataset) -> dict[str, int]:
    positives = sum(1 for case in dataset.cases if case.is_positive)
    return {
        "cases": len(dataset.cases),
        "positive": positives,
        "refusal": len(dataset.cases) - positives,
        "kinds": len({case.kind.value for case in dataset.cases}),
    }


def tokens_in(text: str, tokens: Iterable[str]) -> tuple[str, ...]:
    """Casefolded substring presence, used by the matcher's independent side."""

    haystack = " ".join(str(text).casefold().split())
    return tuple(token for token in tokens if token.casefold() not in haystack)
