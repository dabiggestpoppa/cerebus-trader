"""I.5 answer authority (PLAN §4): when may an assertion be asserted.

Authority rules decide *how* something may be said — never *what the status
is*. A status, exposure, identity or evidence class is never modified here;
relevance, ranking and routing weights are never consulted.
"""
from __future__ import annotations

from app.forge.canonical import EvidenceStatus
from app.forge.qa.contract import Qualification, QualificationCode

# Frozen status authority (PLAN §4.1).
PLAIN = "PLAIN"                          # assertable without qualification
QUALIFIED = "QUALIFIED"                  # assertable only with qualification
DESCRIPTIVE_ONLY = "DESCRIPTIVE_ONLY"    # never a numerical assertion
NEGATIVE_ONLY = "NEGATIVE_ONLY"          # falsified/negative statements only

_PLAIN_STATUSES = frozenset({EvidenceStatus.VALIDATED})
_DESCRIPTIVE_STATUSES = frozenset({EvidenceStatus.DESCRIPTIVE})
_NEGATIVE_STATUSES = frozenset({EvidenceStatus.FALSIFIED})


def authority_for(status: str | EvidenceStatus) -> str:
    value = status.value if isinstance(status, EvidenceStatus) else status
    if value in {s.value for s in EvidenceStatus}:
        if value in {s.value for s in _PLAIN_STATUSES}:
            return PLAIN
        if value in {s.value for s in _DESCRIPTIVE_STATUSES}:
            return DESCRIPTIVE_ONLY
        if value in {s.value for s in _NEGATIVE_STATUSES}:
            return NEGATIVE_ONLY
    return QUALIFIED


_STATUS_QUALIFICATION_TEXT: dict[str, tuple[QualificationCode, str]] = {
    EvidenceStatus.FORWARD_OOS.value: (
        QualificationCode.FORWARD_OOS,
        "forward out-of-sample result; not a current production claim",
    ),
    EvidenceStatus.CANDIDATE.value: (
        QualificationCode.CANDIDATE_STATUS,
        "candidate status; not validated",
    ),
    EvidenceStatus.RESEARCH_FLAG.value: (
        QualificationCode.RESEARCH_FLAG,
        "research flag; research material, never production signal logic",
    ),
    EvidenceStatus.HISTORICAL.value: (
        QualificationCode.HISTORICAL_GENERATION,
        "historical generation; not current",
    ),
    EvidenceStatus.SUPERSEDED.value: (
        QualificationCode.SUPERSEDED,
        "superseded; a later generation governs",
    ),
    EvidenceStatus.PARKED.value: (
        QualificationCode.PARKED,
        "parked; not active guidance",
    ),
    EvidenceStatus.FALSIFIED.value: (
        QualificationCode.NEGATIVE_EVIDENCE,
        "falsified / negative evidence; never a positive trading rule",
    ),
}

_QUALIFIER_TEXT: dict[str, tuple[QualificationCode, str]] = {
    "SMALL_N": (
        QualificationCode.SMALL_N,
        "small-N governed sample; the sample size materially changes "
        "interpretation",
    ),
    "RESEARCH_SAMPLE": (
        QualificationCode.RESEARCH_SAMPLE,
        "validated within the recovered research sample; never forward-OOS",
    ),
    "RELATIONSHIP_STATISTIC": (
        QualificationCode.RELATIONSHIP_STATISTIC,
        "relationship statistic; never a trade win rate",
    ),
}

ACTION_GAP_TEXT = (
    "the model supplies context but a validated setup is not currently encoded"
)


def status_qualification(status: str | EvidenceStatus) -> Qualification | None:
    value = status.value if isinstance(status, EvidenceStatus) else status
    entry = _STATUS_QUALIFICATION_TEXT.get(value)
    if entry is None:
        return None
    code, text = entry
    return Qualification(code=code, text=text)


def qualifier_qualifications(
    qualifiers: tuple[str, ...],
    *,
    object_id: str,
    sample_n: int | None,
) -> tuple[Qualification, ...]:
    """Governed qualifier flags (compiler table) → mandatory qualifications.

    ``SMALL_N`` always carries N when the supporting evidence states one —
    the sample size travels with the claim (Answer Contract: always include
    N when small-N materially changes interpretation).
    """
    out: list[Qualification] = []
    for qualifier in qualifiers:
        entry = _QUALIFIER_TEXT.get(qualifier)
        if entry is None:
            continue
        code, text = entry
        if code is QualificationCode.SMALL_N:
            text = (
                f"{text} (N={sample_n})"
                if sample_n is not None
                else f"{text} (N not stated in source)"
            )
        out.append(Qualification(code=code, text=text, object_id=object_id))
    return tuple(out)


def no_label_qualification(status: str | EvidenceStatus) -> Qualification | None:
    """PLAN §2.2: a status with no frozen contract label must be qualified."""
    from app.forge.qa.contract import label_for_status

    value = status.value if isinstance(status, EvidenceStatus) else status
    if label_for_status(value) is None:
        return Qualification(
            code=QualificationCode.NO_CONTRACT_LABEL,
            text=(
                f"status {value} carries no frozen contract epistemic label; "
                "statement is a qualified limitation only"
            ),
        )
    return None


def identity_qualification() -> Qualification:
    return Qualification(
        code=QualificationCode.IDENTITY_UNSPECIFIED,
        text=(
            "identity dimensions marked NOT_SPECIFIED_IN_SOURCE travel "
            "verbatim; the statistic is population-bound as recorded"
        ),
    )


def status_authority_verdict(status: str | EvidenceStatus, *, numerical: bool) -> str:
    """ASSERT | QUALIFY | GAP for a supported assertion (PLAN §4.1)."""
    authority = authority_for(status)
    if authority is PLAIN:
        return "ASSERT"
    if authority is DESCRIPTIVE_ONLY:
        return "GAP" if numerical else "ASSERT"
    # QUALIFIED and NEGATIVE_ONLY are always assertable only with a
    # mandatory qualification — a supported CANDIDATE is never assertable
    # without one.
    return "QUALIFY"
