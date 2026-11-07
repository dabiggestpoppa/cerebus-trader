"""Immutable authorized retrieval bundle and deterministic identity."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, replace
from typing import Any

from app.forge.ask_cerebus.retrieval.enums import (
    LimitationCode,
    RetrievalOutcome,
)
from app.forge.ask_cerebus.retrieval.refs import (
    CanonicalRef,
    ClaimRef,
    EvidenceRef,
    IntelligenceRef,
    Limitation,
    LineageRef,
    NegativeRef,
    Refusal,
    SemanticPassage,
)
from app.forge.ask_cerebus.retrieval.trace import RetrievalTrace
from app.forge.ask_cerebus.retrieval.versions import (
    BUNDLE_ID_LENGTH,
    BUNDLE_ID_PREFIX,
    RETRIEVAL_CONTRACT_V1,
)


def canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


@dataclass(frozen=True)
class AuthorizedRetrievalBundle:
    query_plan_id: str
    retrieval_contract_version: str
    canonical_refs: tuple[CanonicalRef, ...] = ()
    claim_refs: tuple[ClaimRef, ...] = ()
    evidence_refs: tuple[EvidenceRef, ...] = ()
    intelligence_refs: tuple[IntelligenceRef, ...] = ()
    lineage_refs: tuple[LineageRef, ...] = ()
    semantic_passages: tuple[SemanticPassage, ...] = ()
    negative_refs: tuple[NegativeRef, ...] = ()
    limitations: tuple[Limitation, ...] = ()
    refusals: tuple[Refusal, ...] = ()
    trace: RetrievalTrace | None = None
    selected_generation: int = 0
    selected_index_hash: str = ""
    bundle_id: str = ""

    def __post_init__(self) -> None:
        if not isinstance(self.query_plan_id, str) or not self.query_plan_id:
            raise ValueError("query_plan_id is required")
        if self.retrieval_contract_version != RETRIEVAL_CONTRACT_V1:
            raise ValueError("unsupported retrieval contract version")
        for name in (
            "canonical_refs",
            "claim_refs",
            "evidence_refs",
            "intelligence_refs",
            "lineage_refs",
            "semantic_passages",
            "negative_refs",
            "limitations",
            "refusals",
        ):
            if not isinstance(getattr(self, name), tuple):
                raise ValueError(f"{name} must be a tuple")
        if self.bundle_id and not self.bundle_id.startswith(BUNDLE_ID_PREFIX):
            raise ValueError("bundle_id must use the BUNDLE. prefix")

    @property
    def outcome(self) -> RetrievalOutcome:
        if self.refusals and not self.canonical_refs:
            return RetrievalOutcome.REFUSED
        if any(
            limitation.code
            in (
                LimitationCode.PROVIDER_NOT_CONFIGURED,
                LimitationCode.HISTORICAL_UNAVAILABLE,
                LimitationCode.RETRIEVAL_UNAVAILABLE,
            )
            for limitation in self.limitations
        ) and not self.canonical_refs:
            return RetrievalOutcome.UNAVAILABLE
        if self.limitations or self.refusals:
            return RetrievalOutcome.PARTIAL
        return RetrievalOutcome.RESOLVED

    @property
    def consumer_trace(self) -> dict[str, Any] | None:
        return self.trace.consumer_payload() if self.trace is not None else None

    def payload(self, *, include_id: bool = True) -> dict[str, Any]:
        out: dict[str, Any] = {
            "query_plan_id": self.query_plan_id,
            "retrieval_contract_version": self.retrieval_contract_version,
            "canonical_refs": [item.payload() for item in self.canonical_refs],
            "claim_refs": [item.payload() for item in self.claim_refs],
            "evidence_refs": [item.payload() for item in self.evidence_refs],
            "intelligence_refs": [
                item.payload() for item in self.intelligence_refs
            ],
            "lineage_refs": [item.payload() for item in self.lineage_refs],
            "semantic_passages": [
                item.payload() for item in self.semantic_passages
            ],
            "negative_refs": [item.payload() for item in self.negative_refs],
            "limitations": [item.payload() for item in self.limitations],
            "refusals": [item.payload() for item in self.refusals],
            "trace": self.trace.payload() if self.trace is not None else None,
            "selected_generation": self.selected_generation,
            "selected_index_hash": self.selected_index_hash,
        }
        if include_id:
            out["bundle_id"] = self.bundle_id
        return out

    def compute_id(self) -> str:
        digest = hashlib.sha256(
            canonical_json(self.payload(include_id=False)).encode("utf-8")
        ).hexdigest()
        return BUNDLE_ID_PREFIX + digest[:BUNDLE_ID_LENGTH]

    def finalized(self) -> "AuthorizedRetrievalBundle":
        trace = self.trace.finalized() if self.trace is not None else None
        draft = replace(self, trace=trace)
        return replace(draft, bundle_id=draft.compute_id())

    def to_json(self) -> str:
        return canonical_json(self.payload())


__all__ = ["AuthorizedRetrievalBundle", "canonical_json"]
