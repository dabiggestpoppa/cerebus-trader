"""Immutable IV.3 context package and manifest types."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, replace
from typing import Any

from app.forge.ask_cerebus.context.enums import (
    ContextIssueCode,
    ContextOutcome,
    ContextRefusalCode,
    ContextSectionId,
    EpistemicLabel,
    SmallNFlag,
    TrustClass,
)
from app.forge.ask_cerebus.context.versions import (
    CONTEXT_CONTRACT_V1,
    CONTEXT_MANIFEST_V1,
    MANIFEST_DIGEST_PREFIX,
    PACKAGE_ID_LENGTH,
    PACKAGE_ID_PREFIX,
)


def canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


@dataclass(frozen=True)
class ContextFact:
    key: str
    value_text: str
    unit: str = ""

    def payload(self) -> dict[str, str]:
        return {"key": self.key, "value_text": self.value_text, "unit": self.unit}


@dataclass(frozen=True)
class ContextItem:
    item_id: str
    source_ref_id: str
    source_ref_type: str
    source_status: str
    epistemic_label: EpistemicLabel
    layer: str
    exposure: str
    generation: str
    trust_class: TrustClass
    facts: tuple[ContextFact, ...] = ()
    text: str | None = None
    quote_scope: str = "NONE"
    provenance_refs: tuple[str, ...] = ()
    evidence_refs: tuple[str, ...] = ()
    token_units: int = 0
    priority: int = 0
    mandatory: bool = False

    def control_payload(self) -> dict[str, Any]:
        return {
            "source_ref_id": self.source_ref_id,
            "source_ref_type": self.source_ref_type,
            "source_status": self.source_status,
            "epistemic_label": self.epistemic_label.value,
            "layer": self.layer,
            "exposure": self.exposure,
            "generation": self.generation,
            "trust_class": self.trust_class.value,
            "facts": [fact.payload() for fact in self.facts],
            "quote_scope": self.quote_scope,
            "provenance_refs": list(self.provenance_refs),
            "evidence_refs": list(self.evidence_refs),
            "priority": self.priority,
            "mandatory": self.mandatory,
        }

    def payload(self) -> dict[str, Any]:
        out = self.control_payload()
        out["item_id"] = self.item_id
        out["text"] = self.text
        out["text_sha256"] = (
            hashlib.sha256(self.text.encode("utf-8")).hexdigest()
            if self.text is not None
            else ""
        )
        out["token_units"] = self.token_units
        return out


@dataclass(frozen=True)
class ContextOmission:
    section_id: ContextSectionId
    reason: ContextIssueCode
    source_ref_id: str = ""
    estimated_units: int = 0

    def payload(self) -> dict[str, Any]:
        return {
            "section_id": self.section_id.value,
            "reason": self.reason.value,
            "source_ref_id": self.source_ref_id,
            "estimated_units": self.estimated_units,
        }


@dataclass(frozen=True)
class ContextIssue:
    code: ContextIssueCode
    section_id: ContextSectionId | None = None
    detail: str = ""

    def payload(self) -> dict[str, str]:
        return {
            "code": self.code.value,
            "section_id": self.section_id.value if self.section_id else "",
            "detail": self.detail,
        }


@dataclass(frozen=True)
class ContextRefusal:
    code: ContextRefusalCode
    detail: str = ""

    def payload(self) -> dict[str, str]:
        return {"code": self.code.value, "detail": self.detail}


@dataclass(frozen=True)
class TokenAccounting:
    estimator_version: str
    max_units: int
    reserve_units: int
    mandatory_units: int
    optional_units: int
    used_units: int
    trimmed_units: int

    def payload(self) -> dict[str, Any]:
        return {
            "estimator_version": self.estimator_version,
            "max_units": self.max_units,
            "reserve_units": self.reserve_units,
            "mandatory_units": self.mandatory_units,
            "optional_units": self.optional_units,
            "used_units": self.used_units,
            "trimmed_units": self.trimmed_units,
        }


@dataclass(frozen=True)
class ContextSection:
    section_id: ContextSectionId
    items: tuple[ContextItem, ...] = ()
    omissions: tuple[ContextOmission, ...] = ()
    estimated_units: int = 0
    mandatory_units: int = 0

    def payload(self) -> dict[str, Any]:
        return {
            "section_id": self.section_id.value,
            "items": [item.payload() for item in self.items],
            "omissions": [omission.payload() for omission in self.omissions],
            "estimated_units": self.estimated_units,
            "mandatory_units": self.mandatory_units,
        }


@dataclass(frozen=True)
class AuthorizedIntelligenceFact:
    snapshot_id: str
    field_path: str
    value_text: str
    unit: str = ""
    layer: str = ""
    quality: str = ""
    synthetic: bool = False


@dataclass(frozen=True)
class AuthorizedEvidenceStatistic:
    evidence_id: str
    metric: str
    event_identity: str
    conditioning_population: str
    sample_size: int | None = None
    research_period: str = ""
    small_n_flag: SmallNFlag = SmallNFlag.UNRESOLVED
    small_n_threshold_ref: str = ""
    oos_status: str = "UNAVAILABLE"


@dataclass(frozen=True)
class AuthorizedContextDetail:
    intelligence: tuple[AuthorizedIntelligenceFact, ...] = ()
    statistics: tuple[AuthorizedEvidenceStatistic, ...] = ()


@dataclass(frozen=True)
class AuthorizedContextManifest:
    manifest_version: str
    context_contract_version: str
    query_plan_id: str
    retrieval_bundle_id: str
    included_section_ids: tuple[str, ...]
    included_object_ids: tuple[str, ...]
    omitted_section_ids: tuple[str, ...]
    estimator_version: str
    estimated_units: int
    section_digests: tuple[tuple[str, str], ...]
    trust_boundary_hash: str
    manifest_digest: str = ""

    def payload(self, *, include_digest: bool = True) -> dict[str, Any]:
        out: dict[str, Any] = {
            "manifest_version": self.manifest_version,
            "context_contract_version": self.context_contract_version,
            "query_plan_id": self.query_plan_id,
            "retrieval_bundle_id": self.retrieval_bundle_id,
            "included_section_ids": list(self.included_section_ids),
            "included_object_ids": list(self.included_object_ids),
            "omitted_section_ids": list(self.omitted_section_ids),
            "estimator_version": self.estimator_version,
            "estimated_units": self.estimated_units,
            "section_digests": [list(item) for item in self.section_digests],
            "trust_boundary_hash": self.trust_boundary_hash,
        }
        if include_digest:
            out["manifest_digest"] = self.manifest_digest
        return out

    def compute_digest(self) -> str:
        digest = hashlib.sha256(
            canonical_json(self.payload(include_digest=False)).encode("utf-8")
        ).hexdigest()
        return MANIFEST_DIGEST_PREFIX + digest

    def finalized(self) -> "AuthorizedContextManifest":
        return replace(self, manifest_digest=self.compute_digest())


@dataclass(frozen=True)
class AuthorizedContextPackage:
    context_contract_version: str
    query_plan_id: str
    retrieval_bundle_id: str
    outcome: ContextOutcome
    sections: tuple[ContextSection, ...] = ()
    omissions: tuple[ContextOmission, ...] = ()
    issues: tuple[ContextIssue, ...] = ()
    refusals: tuple[ContextRefusal, ...] = ()
    token_accounting: TokenAccounting | None = None
    manifest: AuthorizedContextManifest | None = None
    package_id: str = ""

    def payload(self, *, include_id: bool = True) -> dict[str, Any]:
        out: dict[str, Any] = {
            "context_contract_version": self.context_contract_version,
            "query_plan_id": self.query_plan_id,
            "retrieval_bundle_id": self.retrieval_bundle_id,
            "outcome": self.outcome.value,
            "sections": [section.payload() for section in self.sections],
            "omissions": [omission.payload() for omission in self.omissions],
            "issues": [issue.payload() for issue in self.issues],
            "refusals": [refusal.payload() for refusal in self.refusals],
            "token_accounting": (
                self.token_accounting.payload() if self.token_accounting else None
            ),
            "manifest": self.manifest.payload() if self.manifest else None,
        }
        if include_id:
            out["package_id"] = self.package_id
        return out

    def compute_id(self) -> str:
        digest = hashlib.sha256(
            canonical_json(self.payload(include_id=False)).encode("utf-8")
        ).hexdigest()
        return PACKAGE_ID_PREFIX + digest[:PACKAGE_ID_LENGTH]

    def finalized(self) -> "AuthorizedContextPackage":
        manifest = self.manifest.finalized() if self.manifest else None
        draft = replace(self, manifest=manifest)
        return replace(draft, package_id=draft.compute_id())

    def to_json(self) -> str:
        return canonical_json(self.payload())


__all__ = [
    "ContextFact",
    "ContextItem",
    "ContextOmission",
    "ContextIssue",
    "ContextRefusal",
    "TokenAccounting",
    "ContextSection",
    "AuthorizedIntelligenceFact",
    "AuthorizedEvidenceStatistic",
    "AuthorizedContextDetail",
    "AuthorizedContextManifest",
    "AuthorizedContextPackage",
    "canonical_json",
]
