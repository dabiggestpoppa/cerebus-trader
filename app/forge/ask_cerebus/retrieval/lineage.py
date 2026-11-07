"""Generation and lineage retention without cross-generation merging."""

from __future__ import annotations

from app.forge.canonical import EvidenceStatus
from app.forge.retrieval.objects import RetrievalObject

from .enums import LimitationCode
from .refs import Limitation, LineageRef


def build_lineage_refs(records: tuple[RetrievalObject, ...]) -> tuple[LineageRef, ...]:
    refs: list[LineageRef] = []
    for record in records:
        generation = record.conflict.generation
        historical = record.status is EvidenceStatus.HISTORICAL or generation.startswith(
            ("P90", "ST.", "BASE80", "MARKOV", "FIB")
        )
        if not historical and record.object_type.value != "LINEAGE":
            continue
        refs.append(
            LineageRef(
                object_id=record.object_id,
                generation=generation or "LINEAGE",
                relation="lineage",
                claim_ids=tuple(
                    link.target_id
                    for link in record.related_ids
                    if link.target_id.startswith("CL.")
                ),
            )
        )
    return tuple(sorted(refs, key=lambda ref: (ref.generation, ref.object_id)))


def lineage_limitations(
    records: tuple[RetrievalObject, ...],
) -> tuple[Limitation, ...]:
    out: list[Limitation] = []
    for record in records:
        generation = record.conflict.generation
        if record.status is EvidenceStatus.HISTORICAL or generation.startswith(
            ("P90", "ST.", "BASE80", "MARKOV", "FIB")
        ):
            out.append(
                Limitation(
                    LimitationCode.HISTORICAL_GENERATION,
                    record.object_id,
                    generation or record.status.value,
                )
            )
    return tuple(out)


__all__ = ["build_lineage_refs", "lineage_limitations"]
