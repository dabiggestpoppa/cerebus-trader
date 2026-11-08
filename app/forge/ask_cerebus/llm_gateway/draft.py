"""Structured gateway draft and structural admission guard.

This module checks schema shape, package-local references, mandatory limitation
preservation and forbidden authority fields. It intentionally does not decide
whether a factual claim is true; IV.5 owns that judgement.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

from app.forge.ask_cerebus.context.enums import EpistemicLabel
from app.forge.ask_cerebus.llm_gateway.enums import (
    DRAFT_FORBIDDEN_FIELDS,
    CostBasis,
    DraftStatus,
    GatewayOutcome,
    GatewayRefusalCode,
)
from app.forge.ask_cerebus.llm_gateway.request import (
    Admission,
    numeric_ref_is_admissible,
)
from app.forge.ask_cerebus.llm_gateway.trace import (
    AttemptTrace,
    GatewayTrace,
    UsageAccounting,
)
from app.forge.ask_cerebus.llm_gateway.versions import (
    ASK_GATEWAY_CONTRACT_V1,
    ASK_GATEWAY_DRAFT_SCHEMA_V1,
)


DRAFT_REQUIRED_FIELDS = (
    "sections",
    "claims",
    "citations",
    "uncertainties",
    "refusals",
    "proposed_prose",
)
DRAFT_TOP_FIELDS = frozenset(DRAFT_REQUIRED_FIELDS + ("numbers",))


def draft_schema() -> dict[str, Any]:
    return {
        "type": "object",
        "additionalProperties": False,
        "required": list(DRAFT_REQUIRED_FIELDS),
        "properties": {
            "sections": {
                "type": "array",
                "items": {
                    "type": "object",
                    "required": ["heading", "bullets"],
                    "additionalProperties": False,
                    "properties": {
                        "heading": {"type": "string"},
                        "bullets": {"type": "array", "items": {"type": "string"}},
                    },
                },
            },
            "claims": {
                "type": "array",
                "items": {
                    "type": "object",
                    "required": ["text", "source_refs"],
                    "additionalProperties": False,
                    "properties": {
                        "text": {"type": "string"},
                        "source_refs": {"type": "array", "items": {"type": "string"}},
                        "epistemic_label": {"type": "string"},
                        "layer": {"type": "string"},
                        "generation": {"type": "string"},
                    },
                },
            },
            "citations": {"type": "array", "items": {"type": "string"}},
            "numbers": {
                "type": "array",
                "items": {
                    "type": "object",
                    "required": ["value_text", "source_ref_id"],
                    "additionalProperties": False,
                    "properties": {
                        "value_text": {"type": "string"},
                        "source_ref_id": {"type": "string"},
                        "unit": {"type": "string"},
                    },
                },
            },
            "uncertainties": {"type": "array", "items": {"type": "string"}},
            "refusals": {"type": "array", "items": {"type": "string"}},
            "proposed_prose": {"type": "string"},
        },
    }


@dataclass(frozen=True)
class DraftSection:
    heading: str
    bullets: tuple[str, ...]

    def payload(self) -> dict[str, Any]:
        return {"heading": self.heading, "bullets": list(self.bullets)}


@dataclass(frozen=True)
class DraftClaim:
    text: str
    source_refs: tuple[str, ...]
    epistemic_label: str = ""
    layer: str = ""
    generation: str = ""

    def payload(self) -> dict[str, Any]:
        return {
            "text": self.text,
            "source_refs": list(self.source_refs),
            "epistemic_label": self.epistemic_label,
            "layer": self.layer,
            "generation": self.generation,
        }


@dataclass(frozen=True)
class NumericLink:
    value_text: str
    source_ref_id: str
    unit: str = ""

    def payload(self) -> dict[str, str]:
        return {
            "value_text": self.value_text,
            "source_ref_id": self.source_ref_id,
            "unit": self.unit,
        }


@dataclass(frozen=True)
class GatewayDraft:
    package_id: str
    manifest_id: str
    query_plan_id: str
    route_policy_version: str
    route_id: str
    prompt_id: str
    prompt_version: str
    depth: str
    provider: str
    model: str
    sections: tuple[DraftSection, ...]
    claims: tuple[DraftClaim, ...]
    citations: tuple[str, ...]
    numbers: tuple[NumericLink, ...]
    uncertainties: tuple[str, ...]
    refusals: tuple[str, ...]
    proposed_prose: str
    usage: UsageAccounting
    attempts: tuple[AttemptTrace, ...]
    trace: GatewayTrace
    status: DraftStatus = DraftStatus.UNVALIDATED

    def payload(self) -> dict[str, Any]:
        return {
            "gateway_contract_version": ASK_GATEWAY_CONTRACT_V1,
            "draft_schema_version": ASK_GATEWAY_DRAFT_SCHEMA_V1,
            "status": self.status.value,
            "package_id": self.package_id,
            "manifest_id": self.manifest_id,
            "query_plan_id": self.query_plan_id,
            "route_policy_version": self.route_policy_version,
            "route_id": self.route_id,
            "prompt_id": self.prompt_id,
            "prompt_version": self.prompt_version,
            "depth": self.depth,
            "provider": self.provider,
            "model": self.model,
            "sections": [section.payload() for section in self.sections],
            "claims": [claim.payload() for claim in self.claims],
            "citations": list(self.citations),
            "numbers": [number.payload() for number in self.numbers],
            "uncertainties": list(self.uncertainties),
            "refusals": list(self.refusals),
            "proposed_prose": self.proposed_prose,
            "usage": self.usage.payload(),
            "attempts": [attempt.payload() for attempt in self.attempts],
            "trace": self.trace.payload(),
        }


@dataclass(frozen=True)
class GatewayRefusal:
    outcome: GatewayOutcome
    code: GatewayRefusalCode
    detail: str
    package_id: str
    manifest_id: str
    query_plan_id: str
    route_policy_version: str
    route_id: str
    prompt_id: str
    prompt_version: str
    depth: str
    provider: str
    model: str
    usage: UsageAccounting
    attempts: tuple[AttemptTrace, ...]
    trace: GatewayTrace

    def payload(self) -> dict[str, Any]:
        return {
            "gateway_contract_version": ASK_GATEWAY_CONTRACT_V1,
            "outcome": self.outcome.value,
            "code": self.code.value,
            "detail": self.detail,
            "package_id": self.package_id,
            "manifest_id": self.manifest_id,
            "query_plan_id": self.query_plan_id,
            "route_policy_version": self.route_policy_version,
            "route_id": self.route_id,
            "prompt_id": self.prompt_id,
            "prompt_version": self.prompt_version,
            "depth": self.depth,
            "provider": self.provider,
            "model": self.model,
            "usage": self.usage.payload(),
            "attempts": [attempt.payload() for attempt in self.attempts],
            "trace": self.trace.payload(),
        }


@dataclass(frozen=True)
class DraftFailure:
    code: GatewayRefusalCode
    detail: str


def _invalid(detail: str) -> tuple[None, DraftFailure]:
    return None, DraftFailure(GatewayRefusalCode.DRAFT_SCHEMA_INVALID, detail)


def parse_draft(
    structured: Mapping[str, Any] | None,
    admission: Admission,
) -> tuple[dict[str, Any] | None, DraftFailure | None]:
    if not isinstance(structured, Mapping):
        return None, DraftFailure(
            GatewayRefusalCode.PROVIDER_MALFORMED,
            "provider returned no structured object",
        )
    keys = set(structured)
    forbidden = keys & DRAFT_FORBIDDEN_FIELDS
    if forbidden:
        return None, DraftFailure(
            GatewayRefusalCode.POLICY_DENIED,
            "draft introduced a forbidden authority field",
        )
    if keys - DRAFT_TOP_FIELDS:
        return _invalid("draft contains an unknown top-level field")
    if any(field not in keys for field in DRAFT_REQUIRED_FIELDS):
        return _invalid("draft is missing a required field")

    sections = structured["sections"]
    claims = structured["claims"]
    citations = structured["citations"]
    numbers = structured.get("numbers", [])
    uncertainties = structured["uncertainties"]
    refusals = structured["refusals"]
    prose = structured["proposed_prose"]
    if not isinstance(sections, list) or not isinstance(claims, list):
        return _invalid("sections/claims must be lists")
    if not isinstance(citations, list) or not all(isinstance(v, str) for v in citations):
        return _invalid("citations must be strings")
    if not isinstance(numbers, list):
        return _invalid("numbers must be a list")
    if not all(isinstance(v, str) for v in uncertainties + refusals):
        return _invalid("uncertainties/refusals must be strings")
    if not isinstance(prose, str):
        return _invalid("proposed_prose must be a string")

    parsed_sections: list[DraftSection] = []
    for section in sections:
        if not isinstance(section, Mapping) or set(section) != {"heading", "bullets"}:
            return _invalid("section shape is invalid")
        if not isinstance(section["heading"], str) or not isinstance(section["bullets"], list):
            return _invalid("section field types are invalid")
        if not all(isinstance(b, str) for b in section["bullets"]):
            return _invalid("section bullets must be strings")
        parsed_sections.append(DraftSection(section["heading"], tuple(section["bullets"])))

    parsed_claims: list[DraftClaim] = []
    allowed_claim_fields = {
        "text",
        "source_refs",
        "epistemic_label",
        "layer",
        "generation",
    }
    for claim in claims:
        if not isinstance(claim, Mapping) or set(claim) - allowed_claim_fields:
            return _invalid("claim contains an unknown field")
        if "text" not in claim or "source_refs" not in claim:
            return _invalid("claim is missing text/source_refs")
        if not isinstance(claim["text"], str) or not isinstance(claim["source_refs"], list):
            return _invalid("claim field types are invalid")
        if not all(isinstance(ref, str) for ref in claim["source_refs"]):
            return _invalid("claim refs must be strings")
        if not claim["source_refs"]:
            return None, DraftFailure(
                GatewayRefusalCode.CITATION_REQUIRED,
                "claim has no package-local citation",
            )
        label = claim.get("epistemic_label", "")
        if label:
            if label == EpistemicLabel.INFERENCE.value:
                return None, DraftFailure(
                    GatewayRefusalCode.POLICY_DENIED,
                    "INFERENCE is reserved and may not be emitted",
                )
            if label not in {value.value for value in EpistemicLabel}:
                return _invalid("claim label is not in the frozen vocabulary")
        for ref in claim["source_refs"]:
            if ref not in admission.allowed_refs:
                return None, DraftFailure(
                    GatewayRefusalCode.CITATION_OUTSIDE_PACKAGE,
                    "claim citation is outside the authorized package",
                )
        parsed_claims.append(
            DraftClaim(
                text=claim["text"],
                source_refs=tuple(claim["source_refs"]),
                epistemic_label=label,
                layer=str(claim.get("layer", "")),
                generation=str(claim.get("generation", "")),
            )
        )

    for citation in citations:
        if citation not in admission.allowed_refs:
            return None, DraftFailure(
                GatewayRefusalCode.CITATION_OUTSIDE_PACKAGE,
                "citation is outside the authorized package",
            )
    for claim in parsed_claims:
        if not set(claim.source_refs).issubset(set(citations)):
            return None, DraftFailure(
                GatewayRefusalCode.CITATION_REQUIRED,
                "claim reference is absent from citations",
            )

    parsed_numbers: list[NumericLink] = []
    for number in numbers:
        if not isinstance(number, Mapping) or set(number) - {
            "value_text",
            "source_ref_id",
            "unit",
        }:
            return _invalid("number link shape is invalid")
        if "value_text" not in number or "source_ref_id" not in number:
            return _invalid("number link is missing value/source")
        if not isinstance(number["value_text"], str) or not isinstance(
            number["source_ref_id"], str
        ):
            return _invalid("number link field types are invalid")
        ref = number["source_ref_id"]
        if ref not in admission.allowed_refs:
            return None, DraftFailure(
                GatewayRefusalCode.CITATION_OUTSIDE_PACKAGE,
                "numeric link is outside the authorized package",
            )
        if not numeric_ref_is_admissible(admission.package, ref):
            return None, DraftFailure(
                GatewayRefusalCode.NUMERIC_EVIDENCE_MISSING,
                "numeric link does not resolve to admissible evidence",
            )
        parsed_numbers.append(
            NumericLink(number["value_text"], ref, str(number.get("unit", "")))
        )

    combined = " ".join(uncertainties + refusals)
    for status in admission.limitations:
        if status and status not in combined:
            return None, DraftFailure(
                GatewayRefusalCode.MANDATORY_RESTRICTION_MISSING,
                "mandatory upstream restriction was dropped",
            )

    return (
        {
            "sections": tuple(parsed_sections),
            "claims": tuple(parsed_claims),
            "citations": tuple(citations),
            "numbers": tuple(parsed_numbers),
            "uncertainties": tuple(uncertainties),
            "refusals": tuple(refusals),
            "proposed_prose": prose,
        },
        None,
    )


def build_trace(
    *,
    route_policy_version: str,
    route_id: str,
    package_id: str,
    manifest_id: str,
    query_plan_id: str,
    prompt_id: str,
    prompt_version: str,
    provider: str,
    model: str,
    outcome: GatewayOutcome,
    attempts: tuple[AttemptTrace, ...],
    refusal_code: GatewayRefusalCode | None = None,
) -> GatewayTrace:
    return GatewayTrace(
        contract_version=ASK_GATEWAY_CONTRACT_V1,
        route_policy_version=route_policy_version,
        route_id=route_id,
        package_id=package_id,
        manifest_id=manifest_id,
        query_plan_id=query_plan_id,
        prompt_id=prompt_id,
        prompt_version=prompt_version,
        provider=provider,
        model=model,
        outcome=outcome.value,
        attempts=attempts,
        refusal_code=refusal_code.value if refusal_code else None,
    )


__all__ = [
    "DRAFT_REQUIRED_FIELDS",
    "DRAFT_TOP_FIELDS",
    "draft_schema",
    "DraftSection",
    "DraftClaim",
    "NumericLink",
    "GatewayDraft",
    "GatewayRefusal",
    "DraftFailure",
    "parse_draft",
    "build_trace",
]
