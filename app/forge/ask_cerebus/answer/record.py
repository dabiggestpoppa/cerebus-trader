"""Deterministic answer identity and the safe final response record."""

from __future__ import annotations

import hashlib
import json
from typing import Any

from app.forge.ask_cerebus.answer.admission import Admission
from app.forge.ask_cerebus.answer.enums import AnswerOutcome, AnswerRefusalCode
from app.forge.ask_cerebus.answer.schema import (
    AnswerClaim,
    CitationRef,
    FinalResponseRecord,
)
from app.forge.ask_cerebus.answer.versions import (
    ANSWER_ID_LENGTH,
    ANSWER_ID_PREFIX,
    ANSWER_RECORD_V1,
    ANSWER_SECTION_SCHEMA_V1,
    ASK_ANSWER_CONTRACT_V1,
    VALIDATOR_SET_V1,
)


def canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def draft_fingerprint(admission: Admission) -> str:
    """Stable identity of the draft's substance, excluding latency and usage."""

    draft = admission.draft
    payload = {
        "depth": draft.depth,
        "claims": [
            {
                "text": claim.text,
                "refs": list(claim.source_refs),
                "label": claim.epistemic_label,
                "layer": claim.layer,
                "generation": claim.generation,
            }
            for claim in draft.claims
        ],
        "citations": list(draft.citations),
        "numbers": [number.payload() for number in draft.numbers],
        "sections": [section.payload() for section in draft.sections],
    }
    return hashlib.sha256(canonical_json(payload).encode("utf-8")).hexdigest()


def answer_id(
    *,
    admission: Admission,
    outcome: AnswerOutcome,
    cited_refs: tuple[str, ...],
    validation_codes: tuple[str, ...],
) -> str:
    payload = {
        "answer_contract_version": ASK_ANSWER_CONTRACT_V1,
        "answer_schema_version": ANSWER_SECTION_SCHEMA_V1,
        "validator_set_version": VALIDATOR_SET_V1,
        "policy_version": admission.policy.version,
        "package_id": admission.draft.package_id,
        "manifest_id": admission.draft.manifest_id,
        "query_plan_id": admission.draft.query_plan_id,
        "draft_fingerprint": draft_fingerprint(admission),
        "depth": admission.depth.value,
        "outcome": outcome.value,
        "cited_refs": list(cited_refs),
        "validation_codes": list(validation_codes),
    }
    digest = hashlib.sha256(canonical_json(payload).encode("utf-8")).hexdigest()
    return ANSWER_ID_PREFIX + digest[:ANSWER_ID_LENGTH]


def build_record(
    *,
    admission: Admission,
    outcome: AnswerOutcome,
    identifier: str,
    citations: tuple[CitationRef, ...],
    claims: tuple[AnswerClaim, ...] = (),
    validation_codes: tuple[str, ...] = (),
    refusal_code: AnswerRefusalCode | None = None,
) -> FinalResponseRecord:
    draft = admission.draft
    return FinalResponseRecord(
        record_version=ANSWER_RECORD_V1,
        outcome=outcome,
        answer_id=identifier,
        answer_contract_version=ASK_ANSWER_CONTRACT_V1,
        answer_schema_version=ANSWER_SECTION_SCHEMA_V1,
        validator_set_version=VALIDATOR_SET_V1,
        depth=admission.depth.value,
        package_id=draft.package_id,
        manifest_id=draft.manifest_id,
        query_plan_id=draft.query_plan_id,
        route_id=draft.route_id,
        route_policy_version=draft.route_policy_version,
        prompt_id=draft.prompt_id,
        prompt_version=draft.prompt_version,
        provider=draft.provider,
        model=draft.model,
        cited_refs=tuple(citation.source_ref_id for citation in citations),
        claim_statuses=tuple(
            (claim.claim_id, claim.epistemic_label) for claim in claims
        ),
        validation_codes=validation_codes,
        answer_refusal_code=refusal_code.value if refusal_code else "",
        as_of=as_of_value(admission),
        latency_ms=round(float(getattr(draft.usage, "latency_seconds", 0.0)) * 1000.0, 6),
        cost_usd=round(float(getattr(draft.usage, "cost_usd", 0.0)), 12),
        cost_basis=getattr(getattr(draft.usage, "cost_basis", ""), "value", ""),
        prose_retained=False,
    )


def as_of_value(admission: Admission) -> str:
    values = admission.index.as_of_values()
    return values[0] if values else ""


__all__ = [
    "canonical_json",
    "draft_fingerprint",
    "answer_id",
    "build_record",
    "as_of_value",
]
