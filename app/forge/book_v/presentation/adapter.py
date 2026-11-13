"""Deterministic presentation adapter between ratified Book IV output and
the read-only Book V interface consumer.

The adapter accepts only :class:`ValidatedAnswer` or
:class:`GovernedAnswerRefusal` (IV.5 DTOs). It never consumes raw
:class:`GatewayDraft` provider output, never recomputes statistics, never
changes eligibility, and never exposes internal provider or retrieval
material.
"""

from __future__ import annotations

from typing import Any

from app.forge.ask_cerebus.answer.enums import AnswerOutcome
from app.forge.ask_cerebus.answer.schema import GovernedAnswerRefusal, ValidatedAnswer

from .model import (
    BookVCitation,
    BookVClaim,
    BookVInterfaceResponse,
    BookVNumber,
    BookVSection,
)
from .versions import (
    BOOK_V_PRESENTATION_CONTRACT_V1,
    BOOK_V_PRESENTATION_SCHEMA_V1,
)


class PresentationRejectionError(ValueError):
    """Deterministic rejection of malformed or unauthorized input to the
    Book V presentation layer."""


class PresentationAdapter:
    """Read-only projection of IV.5 validated answers and governed refusals
    into the Book V interface model.

    All fields are copied verbatim from the IV.5 DTO. No field is inferred,
    recomputed, or supplemented. Internal provider/retrieval material is
    excluded from the projected ``record``.
    """

    #: Record keys safe to project to the interface consumer. Identity and
    #: verdict metadata only -- no provider, model, latency, cost, prompt,
    #: or authorization internals.
    _SAFE_RECORD_KEYS = frozenset(
        {
            "record_version",
            "answer_id",
            "outcome",
            "depth",
            "package_id",
            "manifest_id",
            "query_plan_id",
            "route_id",
            "route_policy_version",
            "cited_refs",
            "claim_statuses",
            "validation_codes",
            "answer_refusal_code",
            "as_of",
        }
    )

    def present(self, dto: ValidatedAnswer | GovernedAnswerRefusal) -> BookVInterfaceResponse:
        """Project an IV.5 DTO into the Book V interface model.

        Raises :class:`PresentationRejectionError` for any input that is not
        a ratified IV.5 answer or refusal DTO (including raw GatewayDraft
        provider output).
        """
        if isinstance(dto, ValidatedAnswer):
            return self._present_answer(dto)
        if isinstance(dto, GovernedAnswerRefusal):
            return self._present_refusal(dto)
        raise PresentationRejectionError(
            "Book V presentation accepts only ValidatedAnswer or "
            f"GovernedAnswerRefusal; got {type(dto).__name__!r}"
        )

    def _present_answer(self, answer: ValidatedAnswer) -> BookVInterfaceResponse:
        sections = tuple(
            BookVSection(
                section_id=section.section_id.value,
                heading=section.heading,
                bullets=section.bullets,
                claim_ids=section.claim_ids,
            )
            for section in answer.sections
        )
        claims = tuple(
            BookVClaim(
                claim_id=claim.claim_id,
                text=claim.text,
                section_id=claim.section_id.value,
                epistemic_label=claim.epistemic_label,
                layer=claim.layer,
                generation=claim.generation,
                source_refs=claim.source_refs,
                citation_ids=claim.citation_ids,
            )
            for claim in answer.claims
        )
        citations = tuple(
            BookVCitation(
                source_ref_id=citation.source_ref_id,
                source_ref_type=citation.source_ref_type,
                source_status=citation.source_status,
                provenance_refs=citation.provenance_refs,
                evidence_refs=citation.evidence_refs,
                generation=citation.generation,
            )
            for citation in answer.citations
        )
        numbers = tuple(
            BookVNumber(
                value_text=number.value_text,
                unit=number.unit,
                source_ref_id=number.source_ref_id,
                normalized=number.normalized,
            )
            for number in answer.numbers
        )
        record = self._safe_record(answer.record)
        return BookVInterfaceResponse(
            outcome=AnswerOutcome.VALIDATED_ANSWER.value,
            contract_version=BOOK_V_PRESENTATION_CONTRACT_V1,
            schema_version=BOOK_V_PRESENTATION_SCHEMA_V1,
            answer_id=answer.answer_id,
            depth=answer.depth.value,
            sections=sections,
            claims=claims,
            citations=citations,
            numbers=numbers,
            limitations=answer.limitations,
            as_of=answer.as_of,
            record=record,
        )

    def _present_refusal(self, refusal: GovernedAnswerRefusal) -> BookVInterfaceResponse:
        record = self._safe_record(refusal.record)
        return BookVInterfaceResponse(
            outcome=AnswerOutcome.GOVERNED_REFUSAL.value,
            contract_version=BOOK_V_PRESENTATION_CONTRACT_V1,
            schema_version=BOOK_V_PRESENTATION_SCHEMA_V1,
            answer_id=refusal.answer_id,
            depth=refusal.depth.value,
            code=refusal.code.value,
            detail=refusal.detail,
            findings=refusal.findings,
            limitations=refusal.limitations,
            record=record,
        )

    @staticmethod
    def _safe_record(record: Any) -> dict[str, Any]:
        """Project only safe, identity-level record metadata."""
        payload = record.payload()
        return {
            key: payload[key]
            for key in sorted(PresentationAdapter._SAFE_RECORD_KEYS)
            if key in payload
        }
