"""Human review plumbing.

A review record is evidence, never an approval. Absent records make the
agreement metric ``BLOCKED``; a disagreement opens a finding or proposes a
dataset change, and the corpus is only corrected by a versioned change (R99).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Mapping, Sequence

from app.forge.ask_cerebus.evaluation import enums
from app.forge.ask_cerebus.evaluation.schema import EvaluationFinding, HumanReviewRecord


@dataclass(frozen=True)
class ReviewRouting:
    review_id: str
    case_id: str
    verdict: enums.ReviewVerdict
    disposition: enums.DisagreementDisposition
    opens_finding: bool
    proposes_dataset_change: bool


def route(record: HumanReviewRecord) -> ReviewRouting:
    if record.verdict is enums.ReviewVerdict.AGREE:
        return ReviewRouting(
            review_id=record.review_id,
            case_id=record.case_id,
            verdict=record.verdict,
            disposition=enums.DisagreementDisposition.NONE,
            opens_finding=False,
            proposes_dataset_change=False,
        )
    disposition = record.disagreement_disposition
    if disposition is enums.DisagreementDisposition.NONE:
        disposition = (
            enums.DisagreementDisposition.OPEN_FINDING
            if record.verdict is enums.ReviewVerdict.DISAGREE_SYSTEM
            else enums.DisagreementDisposition.DATASET_CHANGE_PROPOSAL
        )
    return ReviewRouting(
        review_id=record.review_id,
        case_id=record.case_id,
        verdict=record.verdict,
        disposition=disposition,
        opens_finding=disposition is enums.DisagreementDisposition.OPEN_FINDING,
        proposes_dataset_change=disposition
        is enums.DisagreementDisposition.DATASET_CHANGE_PROPOSAL,
    )


def route_all(records: Iterable[HumanReviewRecord]) -> tuple[ReviewRouting, ...]:
    return tuple(route(record) for record in records)


def reviewer_independence_ok(record: HumanReviewRecord, *, author_roles: Sequence[str]) -> bool:
    """A reviewer may not audit a case the author also owns (R99)."""

    return record.reviewer_role not in set(author_roles)


def agreement(records: Iterable[HumanReviewRecord]) -> Mapping[str, object]:
    materialised = tuple(records)
    if not materialised:
        return {
            "status": enums.ScoreStatus.BLOCKED.value,
            "reviewed": 0,
            "agreed": 0,
            "agreement": None,
            "reason": "no human review record exists; agreement stays BLOCKED",
        }
    agreed = sum(1 for record in materialised if record.verdict is enums.ReviewVerdict.AGREE)
    return {
        "status": enums.ScoreStatus.MEASURED.value,
        "reviewed": len(materialised),
        "agreed": agreed,
        "agreement": round(agreed / len(materialised), 6),
        "reason": "",
    }


def review_findings(records: Iterable[HumanReviewRecord]) -> tuple[EvaluationFinding, ...]:
    from app.forge.ask_cerebus.evaluation import findings as finding_rules

    out: list[EvaluationFinding] = []
    for record in records:
        routing = route(record)
        if not routing.opens_finding:
            continue
        out.append(
            EvaluationFinding(
                finding_id=f"F-REVIEW-{record.review_id}",
                case_id=record.case_id,
                severity=enums.FindingSeverity.S2,
                code=enums.FindingCode.HUMAN_DISAGREEMENT.value,
                owner=record.disagreement_disposition
                and finding_rules.owner_for(enums.FindingCode.HUMAN_DISAGREEMENT),
                detail=record.notes,
                evidence_refs=(record.review_id, record.evidence_path),
            )
        )
    return tuple(out)


def review_status(records: Iterable[HumanReviewRecord]) -> str:
    materialised = tuple(records)
    if not materialised:
        return "BLOCKED"
    if any(route(record).opens_finding for record in materialised):
        return "OPEN_FINDINGS"
    return "RECORDED"
