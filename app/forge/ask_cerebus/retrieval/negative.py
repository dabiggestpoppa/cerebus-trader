"""Negative-evidence retention."""

from __future__ import annotations

from app.forge.canonical import EvidenceStatus
from app.forge.retrieval.objects import RetrievalObject

from .refs import Limitation, NegativeRef

NEGATIVE_STATUSES = frozenset(
    {
        EvidenceStatus.PARKED,
        EvidenceStatus.SUPERSEDED,
        EvidenceStatus.FALSIFIED,
        EvidenceStatus.NO_GO,
        EvidenceStatus.INTERNAL_CONTRADICTION,
        EvidenceStatus.IMPLEMENTATION_NOT_PARITY_SAFE,
    }
)


def is_negative(record: RetrievalObject) -> bool:
    if record.status in NEGATIVE_STATUSES:
        return True
    card = record.structured
    return "NEGATIVE_EVIDENCE" in card.metrics or "NEGATIVE_EVIDENCE" in card.terms


def build_negative_refs(
    records: tuple[RetrievalObject, ...],
) -> tuple[NegativeRef, ...]:
    refs = [
        NegativeRef(
            object_id=record.object_id,
            status=record.status.value,
            generation=record.conflict.generation,
        )
        for record in records
        if is_negative(record)
    ]
    return tuple(sorted(refs, key=lambda ref: ref.object_id))


def negative_limitations(
    refs: tuple[NegativeRef, ...],
) -> tuple[Limitation, ...]:
    from .enums import LimitationCode

    return tuple(
        Limitation(LimitationCode.NEGATIVE_EVIDENCE, ref.object_id)
        for ref in refs
    )


__all__ = ["NEGATIVE_STATUSES", "is_negative", "build_negative_refs", "negative_limitations"]
