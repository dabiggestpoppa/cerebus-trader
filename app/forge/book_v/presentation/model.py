"""Immutable Book V presentation model (read-only projection of IV.5 DTOs).

All fields are copied verbatim from the ratified IV.5 DTOs. No field is
inferred, recomputed, or supplemented. Internal provider or retrieval
material is never projected.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class BookVSection:
    """A presentation section, preserving depth section order."""

    section_id: str
    heading: str
    bullets: tuple[str, ...]
    claim_ids: tuple[str, ...] = ()


@dataclass(frozen=True)
class BookVClaim:
    """A presentation claim, preserving epistemic status and generation."""

    claim_id: str
    text: str
    section_id: str
    epistemic_label: str
    layer: str
    generation: str
    source_refs: tuple[str, ...]
    citation_ids: tuple[str, ...] = ()


@dataclass(frozen=True)
class BookVCitation:
    """A bounded, attributed citation projection. source_ref_id is never an
    internal row or object id.
    """

    source_ref_id: str
    source_ref_type: str
    source_status: str
    provenance_refs: tuple[str, ...] = ()
    evidence_refs: tuple[str, ...] = ()
    generation: str = ""


@dataclass(frozen=True)
class BookVNumber:
    """A numeric value that resolves to authorized package evidence."""

    value_text: str
    unit: str
    source_ref_id: str
    normalized: str


@dataclass(frozen=True)
class BookVInterfaceResponse:
    """Single read-only projection of a ValidatedAnswer or
    GovernedAnswerRefusal.

    The ``outcome`` field discriminates between the two shapes. Answer-only
    fields (sections, claims, citations, numbers, as_of) are empty for
    refusals; refusal-only fields (code, detail, findings) are empty for
    answers.
    """

    outcome: str  # "VALIDATED_ANSWER" | "GOVERNED_REFUSAL"
    contract_version: str
    schema_version: str
    answer_id: str
    depth: str
    sections: tuple[BookVSection, ...] = ()
    claims: tuple[BookVClaim, ...] = ()
    citations: tuple[BookVCitation, ...] = ()
    numbers: tuple[BookVNumber, ...] = ()
    limitations: tuple[str, ...] = ()
    as_of: str = ""
    code: str = ""
    detail: str = ""
    findings: tuple[str, ...] = ()
    record: dict[str, Any] = field(default_factory=dict)

    def is_answer(self) -> bool:
        return self.outcome == "VALIDATED_ANSWER"

    def is_refusal(self) -> bool:
        return self.outcome == "GOVERNED_REFUSAL"

    def payload(self) -> dict[str, Any]:
        """Deterministic serialization for UI consumers."""
        return {
            "contract_version": self.contract_version,
            "schema_version": self.schema_version,
            "outcome": self.outcome,
            "answer_id": self.answer_id,
            "depth": self.depth,
            "sections": [
                {
                    "section_id": s.section_id,
                    "heading": s.heading,
                    "bullets": list(s.bullets),
                    "claim_ids": list(s.claim_ids),
                }
                for s in self.sections
            ],
            "claims": [
                {
                    "claim_id": c.claim_id,
                    "text": c.text,
                    "section_id": c.section_id,
                    "epistemic_label": c.epistemic_label,
                    "layer": c.layer,
                    "generation": c.generation,
                    "source_refs": list(c.source_refs),
                    "citation_ids": list(c.citation_ids),
                }
                for c in self.claims
            ],
            "citations": [
                {
                    "source_ref_id": c.source_ref_id,
                    "source_ref_type": c.source_ref_type,
                    "source_status": c.source_status,
                    "provenance_refs": list(c.provenance_refs),
                    "evidence_refs": list(c.evidence_refs),
                    "generation": c.generation,
                }
                for c in self.citations
            ],
            "numbers": [
                {
                    "value_text": n.value_text,
                    "unit": n.unit,
                    "source_ref_id": n.source_ref_id,
                    "normalized": n.normalized,
                }
                for n in self.numbers
            ],
            "limitations": list(self.limitations),
            "as_of": self.as_of,
            "code": self.code,
            "detail": self.detail,
            "findings": list(self.findings),
            "record": dict(self.record),
        }
