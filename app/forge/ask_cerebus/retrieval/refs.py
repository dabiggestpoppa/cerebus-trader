"""Immutable retrieval reference types.

References carry governed identity, status and bounded excerpts. They never
carry an answer, a verdict, an entitlement or a computed market number.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from app.forge.ask_cerebus.retrieval.enums import (
    EvidenceJoinStatus,
    LimitationCode,
    RefusalCode,
)


@dataclass(frozen=True)
class CanonicalRef:
    object_id: str
    object_type: str
    version: str
    status: str
    layer: str
    market_scope: tuple[str, ...]
    exposure: str
    support_classification: str = "NO_SOURCE"
    generation: str = ""

    def payload(self) -> dict[str, Any]:
        return {
            "object_id": self.object_id,
            "object_type": self.object_type,
            "version": self.version,
            "status": self.status,
            "layer": self.layer,
            "market_scope": list(self.market_scope),
            "exposure": self.exposure,
            "support_classification": self.support_classification,
            "generation": self.generation,
        }


@dataclass(frozen=True)
class ClaimRef:
    claim_id: str
    model_ids: tuple[str, ...]
    model_versions: tuple[str, ...]
    identity_key: tuple[str, ...] | None
    status: str
    evidence_ids: tuple[str, ...]
    generation: str = ""
    result_value: str | None = None
    join_status: EvidenceJoinStatus = EvidenceJoinStatus.UNSUPPORTED

    def payload(self) -> dict[str, Any]:
        return {
            "claim_id": self.claim_id,
            "model_ids": list(self.model_ids),
            "model_versions": list(self.model_versions),
            "identity_key": list(self.identity_key) if self.identity_key else None,
            "status": self.status,
            "evidence_ids": list(self.evidence_ids),
            "generation": self.generation,
            "result_value": self.result_value,
            "join_status": self.join_status.value,
        }


@dataclass(frozen=True)
class EvidenceRef:
    evidence_id: str
    claim_ids: tuple[str, ...]
    status: str
    provenance_ids: tuple[str, ...]
    support_classification: str
    gaps: tuple[str, ...] = ()
    oos_status: str = "UNAVAILABLE"

    def payload(self) -> dict[str, Any]:
        return {
            "evidence_id": self.evidence_id,
            "claim_ids": list(self.claim_ids),
            "status": self.status,
            "provenance_ids": list(self.provenance_ids),
            "support_classification": self.support_classification,
            "gaps": list(self.gaps),
            "oos_status": self.oos_status,
        }


@dataclass(frozen=True)
class IntelligenceRef:
    request_kind: str
    snapshot_id: str
    snapshot_hash: str
    view: str
    quality: str
    no_go: tuple[str, ...] = ()
    model_id: str = ""
    model_version: str = ""
    refusal: str = ""

    def payload(self) -> dict[str, Any]:
        return {
            "request_kind": self.request_kind,
            "snapshot_id": self.snapshot_id,
            "snapshot_hash": self.snapshot_hash,
            "view": self.view,
            "quality": self.quality,
            "no_go": list(self.no_go),
            "model_id": self.model_id,
            "model_version": self.model_version,
            "refusal": self.refusal,
        }


@dataclass(frozen=True)
class LineageRef:
    object_id: str
    generation: str
    relation: str = "lineage"
    claim_ids: tuple[str, ...] = ()

    def payload(self) -> dict[str, Any]:
        return {
            "object_id": self.object_id,
            "generation": self.generation,
            "relation": self.relation,
            "claim_ids": list(self.claim_ids),
        }


@dataclass(frozen=True)
class SemanticPassage:
    object_id: str
    text: str
    status: str
    quote_scope: str
    support_classification: str
    score: float = 0.0

    def payload(self) -> dict[str, Any]:
        return {
            "object_id": self.object_id,
            "text": self.text,
            "status": self.status,
            "quote_scope": self.quote_scope,
            "support_classification": self.support_classification,
            "score": self.score,
        }


@dataclass(frozen=True)
class NegativeRef:
    object_id: str
    status: str
    generation: str = ""
    reason: str = "NEGATIVE_EVIDENCE"

    def payload(self) -> dict[str, Any]:
        return {
            "object_id": self.object_id,
            "status": self.status,
            "generation": self.generation,
            "reason": self.reason,
        }


@dataclass(frozen=True)
class Limitation:
    code: LimitationCode
    object_id: str = ""
    detail: str = ""

    def payload(self) -> dict[str, str]:
        return {
            "code": self.code.value,
            "object_id": self.object_id,
            "detail": self.detail,
        }


@dataclass(frozen=True)
class Refusal:
    code: RefusalCode
    detail: str = ""

    def payload(self) -> dict[str, str]:
        return {"code": self.code.value, "detail": self.detail}


__all__ = [
    "CanonicalRef",
    "ClaimRef",
    "EvidenceRef",
    "IntelligenceRef",
    "LineageRef",
    "SemanticPassage",
    "NegativeRef",
    "Limitation",
    "Refusal",
]
