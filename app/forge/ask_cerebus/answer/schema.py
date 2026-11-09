"""Immutable IV.5 answer, refusal and record types."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from app.forge.ask_cerebus.answer.enums import (
    AnswerDepth,
    AnswerOutcome,
    AnswerRefusalCode,
    SectionId,
)
from app.forge.ask_cerebus.answer.versions import (
    ANSWER_RECORD_V1,
    ANSWER_SECTION_SCHEMA_V1,
    ASK_ANSWER_CONTRACT_V1,
    VALIDATOR_SET_V1,
)


@dataclass(frozen=True)
class CitationRef:
    """A user-facing provenance reference. Never an internal row or object id."""

    source_ref_id: str
    source_ref_type: str
    source_status: str
    provenance_refs: tuple[str, ...] = ()
    evidence_refs: tuple[str, ...] = ()
    generation: str = ""

    def payload(self) -> dict[str, Any]:
        return {
            "source_ref_id": self.source_ref_id,
            "source_ref_type": self.source_ref_type,
            "source_status": self.source_status,
            "provenance_refs": list(self.provenance_refs),
            "evidence_refs": list(self.evidence_refs),
            "generation": self.generation,
        }


@dataclass(frozen=True)
class AnswerNumber:
    value_text: str
    unit: str
    source_ref_id: str
    normalized: str

    def payload(self) -> dict[str, str]:
        return {
            "value_text": self.value_text,
            "unit": self.unit,
            "source_ref_id": self.source_ref_id,
            "normalized": self.normalized,
        }


@dataclass(frozen=True)
class AnswerClaim:
    claim_id: str
    text: str
    section_id: SectionId
    epistemic_label: str
    layer: str
    generation: str
    source_refs: tuple[str, ...]
    citation_ids: tuple[str, ...] = ()

    def payload(self) -> dict[str, Any]:
        return {
            "claim_id": self.claim_id,
            "text": self.text,
            "section_id": self.section_id.value,
            "epistemic_label": self.epistemic_label,
            "layer": self.layer,
            "generation": self.generation,
            "source_refs": list(self.source_refs),
            "citation_ids": list(self.citation_ids),
        }


@dataclass(frozen=True)
class AnswerSection:
    section_id: SectionId
    heading: str
    bullets: tuple[str, ...]
    claim_ids: tuple[str, ...] = ()

    def payload(self) -> dict[str, Any]:
        return {
            "section_id": self.section_id.value,
            "heading": self.heading,
            "bullets": list(self.bullets),
            "claim_ids": list(self.claim_ids),
        }


@dataclass(frozen=True)
class FinalResponseRecord:
    record_version: str
    outcome: AnswerOutcome
    answer_id: str
    answer_contract_version: str
    answer_schema_version: str
    validator_set_version: str
    depth: str
    package_id: str
    manifest_id: str
    query_plan_id: str
    route_id: str
    route_policy_version: str
    prompt_id: str
    prompt_version: str
    provider: str
    model: str
    cited_refs: tuple[str, ...] = ()
    claim_statuses: tuple[tuple[str, str], ...] = ()
    validation_codes: tuple[str, ...] = ()
    answer_refusal_code: str = ""
    as_of: str = ""
    latency_ms: float = 0.0
    cost_usd: float = 0.0
    cost_basis: str = ""
    prose_retained: bool = False

    def payload(self) -> dict[str, Any]:
        return {
            "record_version": self.record_version or ANSWER_RECORD_V1,
            "outcome": self.outcome.value,
            "answer_id": self.answer_id,
            "answer_contract_version": self.answer_contract_version,
            "answer_schema_version": self.answer_schema_version,
            "validator_set_version": self.validator_set_version,
            "depth": self.depth,
            "package_id": self.package_id,
            "manifest_id": self.manifest_id,
            "query_plan_id": self.query_plan_id,
            "route_id": self.route_id,
            "route_policy_version": self.route_policy_version,
            "prompt_id": self.prompt_id,
            "prompt_version": self.prompt_version,
            "provider": self.provider,
            "model": self.model,
            "cited_refs": list(self.cited_refs),
            "claim_statuses": [list(pair) for pair in self.claim_statuses],
            "validation_codes": list(self.validation_codes),
            "answer_refusal_code": self.answer_refusal_code,
            "as_of": self.as_of,
            "latency_ms": self.latency_ms,
            "cost_usd": self.cost_usd,
            "cost_basis": self.cost_basis,
            "prose_retained": self.prose_retained,
        }


@dataclass(frozen=True)
class ValidatedAnswer:
    answer_id: str
    depth: AnswerDepth
    sections: tuple[AnswerSection, ...]
    claims: tuple[AnswerClaim, ...]
    citations: tuple[CitationRef, ...]
    numbers: tuple[AnswerNumber, ...]
    limitations: tuple[str, ...]
    as_of: str
    record: FinalResponseRecord
    answer_contract_version: str = ASK_ANSWER_CONTRACT_V1
    answer_schema_version: str = ANSWER_SECTION_SCHEMA_V1
    validator_set_version: str = VALIDATOR_SET_V1
    outcome: AnswerOutcome = AnswerOutcome.VALIDATED_ANSWER

    def payload(self, *, include_record: bool = True) -> dict[str, Any]:
        out: dict[str, Any] = {
            "answer_contract_version": self.answer_contract_version,
            "answer_schema_version": self.answer_schema_version,
            "validator_set_version": self.validator_set_version,
            "outcome": self.outcome.value,
            "answer_id": self.answer_id,
            "depth": self.depth.value,
            "sections": [section.payload() for section in self.sections],
            "claims": [claim.payload() for claim in self.claims],
            "citations": [citation.payload() for citation in self.citations],
            "numbers": [number.payload() for number in self.numbers],
            "limitations": list(self.limitations),
            "as_of": self.as_of,
        }
        if include_record:
            out["record"] = self.record.payload()
        return out


@dataclass(frozen=True)
class GovernedAnswerRefusal:
    answer_id: str
    code: AnswerRefusalCode
    detail: str
    depth: AnswerDepth
    findings: tuple[str, ...]
    record: FinalResponseRecord
    limitations: tuple[str, ...] = ()
    answer_contract_version: str = ASK_ANSWER_CONTRACT_V1
    answer_schema_version: str = ANSWER_SECTION_SCHEMA_V1
    validator_set_version: str = VALIDATOR_SET_V1
    outcome: AnswerOutcome = AnswerOutcome.GOVERNED_REFUSAL

    def payload(self, *, include_record: bool = True) -> dict[str, Any]:
        out: dict[str, Any] = {
            "answer_contract_version": self.answer_contract_version,
            "answer_schema_version": self.answer_schema_version,
            "validator_set_version": self.validator_set_version,
            "outcome": self.outcome.value,
            "answer_id": self.answer_id,
            "answer_refusal_code": self.code.value,
            "detail": self.detail,
            "depth": self.depth.value,
            "findings": list(self.findings),
            "limitations": list(self.limitations),
        }
        if include_record:
            out["record"] = self.record.payload()
        return out


__all__ = [
    "CitationRef",
    "AnswerNumber",
    "AnswerClaim",
    "AnswerSection",
    "FinalResponseRecord",
    "ValidatedAnswer",
    "GovernedAnswerRefusal",
]
