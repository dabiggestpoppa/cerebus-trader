"""Independent refusal-limitation evaluation V1 (F-07).

The V1 corpus asserted a refusal's *code*. It did not assert that the refusal
preserved the restriction that produced it, so a refusal could return
``SETUP_NOT_ENCODED`` while dropping the sentence that says no validated setup
exists. This module asserts preservation of the applicable user-safe limitation
without requiring disclosure of internal rejection material.

Import law: evaluation enums/schema only. The observation is read off the answer
payload by duck typing.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

from app.forge.ask_cerebus.evaluation.matching import normalise, visible_text

REFUSAL_LIMITATION_EVALUATION_V1 = "ASK_EVALUATION_REFUSAL_LIMITATIONS_V1"

#: The frozen six-code refusal vocabulary plus the no-go limitation the IV.5
#: compiler emits alongside a code. No new production code is introduced here.
LIMITATION_CODES = (
    "NO_GO_ACTIVE",
    "ACCESS_NOT_ENTITLED",
    "AMBIGUOUS_SCOPE",
    "MODEL_VERSION_UNAVAILABLE",
    "CURRENT_DATA_UNAVAILABLE",
    "SETUP_NOT_ENCODED",
    "INSUFFICIENT_EVIDENCE",
)

#: User-safe wording that satisfies a limitation when the code itself is not in
#: the ``limitations`` tuple. These are the phrases the answer layer already
#: uses; the evaluator accepts either representation, never both silently.
LIMITATION_PHRASES: Mapping[str, tuple[str, ...]] = {
    "NO_GO_ACTIVE": ("no-go", "no go", "blocked by an active no-go", "blocked"),
    "ACCESS_NOT_ENTITLED": ("not entitled", "entitlement", "access"),
    "AMBIGUOUS_SCOPE": ("ambiguous", "does not resolve to one authorized scope"),
    "MODEL_VERSION_UNAVAILABLE": ("model version", "generation"),
    "CURRENT_DATA_UNAVAILABLE": (
        "current data",
        "current, adequately timestamped",
        "as of",
        "snapshot",
    ),
    "SETUP_NOT_ENCODED": ("no validated setup", "setup is not encoded", "setup"),
    "INSUFFICIENT_EVIDENCE": ("does not support", "insufficient", "evidence"),
}

#: Material that must never appear in a refusal's user-visible text. These are
#: internal identifiers or serialisation artefacts, not rejection reasons.
LEAK_MARKERS = (
    "sha256:",
    "artifact.",
    "row_id",
    "traceback",
    "file://",
    "mod.xau.secret",
    "canonical_object_record",
    "persistence.",
)


@dataclass(frozen=True)
class LimitationExpectation:
    """The limitations a case's refusal must preserve, and what it must not say."""

    case_id: str
    refusal_code: str | None
    required: tuple[str, ...]
    protected_markers: tuple[str, ...]
    authority: str

    @property
    def applicable(self) -> bool:
        return bool(self.required)

    def payload(self) -> dict[str, Any]:
        return {
            "case_id": self.case_id,
            "refusal_code": self.refusal_code,
            "required": list(self.required),
            "protected_markers": list(self.protected_markers),
            "authority": self.authority,
            "applicable": self.applicable,
        }


@dataclass(frozen=True)
class RefusalObservation:
    case_id: str
    outcome: str
    refusal_code: str | None
    limitations: tuple[str, ...]
    visible_text: str
    findings: tuple[str, ...]

    def payload(self) -> dict[str, Any]:
        return {
            "case_id": self.case_id,
            "outcome": self.outcome,
            "refusal_code": self.refusal_code,
            "limitations": list(self.limitations),
            "findings": list(self.findings),
        }


@dataclass(frozen=True)
class LimitationVerdict:
    case_id: str
    applicable: bool
    passed: bool
    required: tuple[str, ...]
    satisfied: tuple[str, ...]
    missing: tuple[str, ...]
    leaked: tuple[str, ...]

    def payload(self) -> dict[str, Any]:
        return {
            "case_id": self.case_id,
            "applicable": self.applicable,
            "passed": self.passed,
            "required": list(self.required),
            "satisfied": list(self.satisfied),
            "missing": list(self.missing),
            "leaked": list(self.leaked),
        }


def required_limitations(case: Any) -> tuple[str, ...]:
    """Derive the user-safe limitations a refusal must preserve.

    Every rule reads the frozen case record only -- never the answer, the draft
    or a previous report -- so the expectation cannot drift toward the output.
    """

    if getattr(case, "expected_outcome", None) is None:
        return ()
    outcome = str(getattr(case.expected_outcome, "value", case.expected_outcome))
    if outcome != "REFUSAL":
        return ()

    required: list[str] = []
    code = getattr(case, "expected_refusal_code", None)
    if code:
        required.append(str(code))

    eligibility = getattr(case, "expected_eligibility", None)
    if eligibility == "BLOCKED" and "NO_GO_ACTIVE" not in required:
        required.append("NO_GO_ACTIVE")

    family = str(getattr(getattr(case, "family", ""), "value", getattr(case, "family", "")))
    freshness = str(
        getattr(getattr(case, "expected_freshness", ""), "value", getattr(case, "expected_freshness", ""))
    )

    # A freshness refusal always owes the current-data limitation, whatever code
    # it chose. Other families do not: a generation-conflict case refused for
    # missing evidence must not be forced to claim a model-version problem.
    if family == "FRESHNESS" and "CURRENT_DATA_UNAVAILABLE" not in required:
        required.append("CURRENT_DATA_UNAVAILABLE")
    if family == "SETUP_ELIGIBILITY" and "SETUP_NOT_ENCODED" not in required:
        required.append("SETUP_NOT_ENCODED")
    return tuple(required)


def expectation_for(case: Any) -> LimitationExpectation:
    return LimitationExpectation(
        case_id=str(case.case_id),
        refusal_code=getattr(case, "expected_refusal_code", None),
        required=required_limitations(case),
        protected_markers=LEAK_MARKERS,
        authority=(
            "frozen case record: expected_refusal_code, expected_eligibility, "
            "family, time_scope, expected_freshness"
        ),
    )


def expectations_for(cases: Any) -> tuple[LimitationExpectation, ...]:
    return tuple(expectation_for(case) for case in cases)


def observe(execution: Any) -> RefusalObservation:
    artifacts: Mapping[str, Any] = getattr(execution, "artifacts", {}) or {}
    answer = artifacts.get("answer")
    payload = answer.payload() if hasattr(answer, "payload") else {}
    code = payload.get("answer_refusal_code")
    return RefusalObservation(
        case_id=str(getattr(execution, "case_id", "")),
        outcome=str(payload.get("outcome") or getattr(execution, "outcome", "")),
        refusal_code=str(code) if code else None,
        limitations=tuple(str(item) for item in (payload.get("limitations", ()) or ())),
        visible_text=visible_text(payload),
        findings=tuple(str(item) for item in (payload.get("findings", ()) or ())),
    )


def evaluate(
    expectation: LimitationExpectation,
    observation: RefusalObservation,
) -> LimitationVerdict:
    if expectation.case_id != observation.case_id:
        raise ValueError(
            f"expectation for {expectation.case_id} evaluated against {observation.case_id}"
        )
    if not expectation.applicable:
        return LimitationVerdict(
            case_id=expectation.case_id,
            applicable=False,
            passed=True,
            required=(),
            satisfied=(),
            missing=(),
            leaked=(),
        )

    text = normalise(observation.visible_text)
    limitations = {normalise(item) for item in observation.limitations}
    satisfied: list[str] = []
    missing: list[str] = []
    for code in expectation.required:
        if normalise(code) in limitations:
            satisfied.append(code)
            continue
        if any(normalise(phrase) in text for phrase in LIMITATION_PHRASES.get(code, ())):
            satisfied.append(code)
            continue
        missing.append(code)

    leaked = tuple(
        marker for marker in expectation.protected_markers if normalise(marker) in text
    )
    return LimitationVerdict(
        case_id=expectation.case_id,
        applicable=True,
        passed=not missing and not leaked,
        required=expectation.required,
        satisfied=tuple(satisfied),
        missing=tuple(missing),
        leaked=leaked,
    )


def evaluate_all(
    cases: Any, observations: Any
) -> tuple[LimitationVerdict, ...]:
    by_id = {observation.case_id: observation for observation in observations}
    out: list[LimitationVerdict] = []
    for case in cases:
        observation = by_id.get(case.case_id)
        if observation is None:
            continue
        out.append(evaluate(expectation_for(case), observation))
    return tuple(out)


__all__ = [
    "LEAK_MARKERS",
    "LIMITATION_CODES",
    "LIMITATION_PHRASES",
    "REFUSAL_LIMITATION_EVALUATION_V1",
    "LimitationExpectation",
    "LimitationVerdict",
    "RefusalObservation",
    "evaluate",
    "evaluate_all",
    "expectation_for",
    "expectations_for",
    "observe",
    "required_limitations",
]
