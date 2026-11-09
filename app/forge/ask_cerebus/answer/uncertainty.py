"""Governed refusal selection and safe wording.

Only the six frozen answer refusal codes exist. When several validators fail,
the highest-precedence code wins and every failing validator code stays
inspectable on the refusal.
"""

from __future__ import annotations

from app.forge.ask_cerebus.answer.enums import (
    FINDING_REFUSAL,
    REFUSAL_RANK,
    SETUP_NOT_ENCODED_SENTENCE,
    AnswerRefusalCode,
    ValidationCode,
)
from app.forge.ask_cerebus.answer.validators import Finding

_DETAILS = {
    AnswerRefusalCode.INSUFFICIENT_EVIDENCE: (
        "The authorized context does not support this answer as asked."
    ),
    AnswerRefusalCode.CURRENT_DATA_UNAVAILABLE: (
        "CEREBUS cannot establish a current, adequately timestamped state for this question."
    ),
    AnswerRefusalCode.MODEL_VERSION_UNAVAILABLE: (
        "The requested model version is not encoded in the authorized context."
    ),
    AnswerRefusalCode.SETUP_NOT_ENCODED: SETUP_NOT_ENCODED_SENTENCE,
    AnswerRefusalCode.ACCESS_NOT_ENTITLED: (
        "The requested scope is not entitled in the authorized context."
    ),
    AnswerRefusalCode.AMBIGUOUS_SCOPE: (
        "The question does not resolve to one authorized scope."
    ),
}


def failure_codes(findings: tuple[Finding, ...]) -> tuple[str, ...]:
    out: list[str] = []
    for finding in findings:
        value = finding.code.value
        if value not in out:
            out.append(value)
    return tuple(out)


def refusal_for(findings: tuple[Finding, ...]) -> AnswerRefusalCode:
    """Highest-precedence refusal implied by the findings."""

    if not findings:
        return AnswerRefusalCode.INSUFFICIENT_EVIDENCE
    codes: list[AnswerRefusalCode] = []
    for finding in findings:
        mapped = FINDING_REFUSAL.get(finding.code)
        if mapped is not None:
            codes.append(mapped)
    if not codes:
        return AnswerRefusalCode.INSUFFICIENT_EVIDENCE
    return min(codes, key=lambda code: REFUSAL_RANK[code])


def refusal_detail(code: AnswerRefusalCode, findings: tuple[Finding, ...]) -> str:
    base = _DETAILS[code]
    supporting = [
        finding.detail
        for finding in findings
        if FINDING_REFUSAL.get(finding.code) is code
    ]
    if not supporting:
        return base
    return f"{base} {supporting[0]}"


def is_setup_only(findings: tuple[Finding, ...]) -> bool:
    codes = {finding.code for finding in findings}
    return codes == {ValidationCode.SETUP_NOT_ENCODED}


__all__ = ["failure_codes", "refusal_for", "refusal_detail", "is_setup_only"]
