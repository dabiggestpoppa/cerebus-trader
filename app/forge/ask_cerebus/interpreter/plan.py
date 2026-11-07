"""Immutable, versioned IV.1 query plan.

The plan describes what was asked. It never carries an answer, verdict,
eligibility, exposure, execution class, statistic or snapshot identity.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, replace
from typing import Any

from app.forge.model_runtime.contract import Layer

from .entities import EntityRef
from .enums import (
    AmbiguityOutcome,
    AmbiguityReason,
    Depth,
    EntityKind,
    Intent,
    PlanConfidence,
    TimeScope,
)
from .versions import ASK_QUERY_CONTRACT_V1, SUPPORTED_QUERY_CONTRACT_VERSIONS

PLAN_ID_PREFIX = "PLAN."
PLAN_ID_LENGTH = 32
MAX_DETAIL = 64

_FROZEN_FIELDS = (
    "query_contract_version",
    "plan_id",
    "intent",
    "entities",
    "model_ids",
    "setup_ids",
    "market",
    "layer",
    "time_scope",
    "requested_depth",
    "effective_depth",
    "requires_live_intelligence",
    "requires_evidence",
    "requires_lineage",
    "requires_setup_context",
    "actionable",
    "requested_fields",
    "confidence",
    "ambiguities",
)


def canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


@dataclass(frozen=True)
class Ambiguity:
    code: AmbiguityReason
    material: bool = False
    candidates: tuple[str, ...] = ()
    detail: str = ""

    def __post_init__(self) -> None:
        if not isinstance(self.code, AmbiguityReason):
            raise ValueError("ambiguity code must be an AmbiguityReason")
        if not isinstance(self.material, bool):
            raise ValueError("material must be a bool")
        if not isinstance(self.candidates, tuple) or any(
            not isinstance(candidate, str) or not candidate for candidate in self.candidates
        ):
            raise ValueError("candidates must be a tuple of non-empty strings")
        if len(set(self.candidates)) != len(self.candidates):
            raise ValueError("candidates must be unique")
        if self.detail and (
            len(self.detail) > MAX_DETAIL or any(ch.isspace() for ch in self.detail)
        ):
            raise ValueError("detail must be a bounded code without whitespace")

    def payload(self) -> dict[str, Any]:
        return {
            "code": self.code.value,
            "material": self.material,
            "candidates": list(self.candidates),
            "detail": self.detail,
        }


@dataclass(frozen=True)
class AskCerebusQueryPlan:
    intent: Intent
    entities: tuple[EntityRef, ...]
    model_ids: tuple[str, ...]
    setup_ids: tuple[str, ...]
    market: str | None
    layer: Layer | None
    time_scope: TimeScope
    requested_depth: Depth
    effective_depth: Depth
    requires_live_intelligence: bool
    requires_evidence: bool
    requires_lineage: bool
    requires_setup_context: bool
    actionable: bool
    requested_fields: tuple[str, ...]
    confidence: PlanConfidence
    ambiguities: tuple[Ambiguity, ...]
    query_contract_version: str = ASK_QUERY_CONTRACT_V1
    plan_id: str = ""

    def __post_init__(self) -> None:
        if not isinstance(self.intent, Intent):
            raise ValueError("intent must be an Intent")
        if not isinstance(self.entities, tuple) or any(
            not isinstance(entity, EntityRef) for entity in self.entities
        ):
            raise ValueError("entities must be a tuple of EntityRef")
        for name in ("model_ids", "setup_ids", "requested_fields"):
            value = getattr(self, name)
            if not isinstance(value, tuple) or any(
                not isinstance(item, str) or not item or any(ch.isspace() for ch in item)
                for item in value
            ):
                raise ValueError(f"{name} must be a tuple of bounded tokens")
            if len(set(value)) != len(value):
                raise ValueError(f"{name} must be unique")
        if self.market is not None and (
            not isinstance(self.market, str)
            or not self.market
            or any(ch.isspace() for ch in self.market)
        ):
            raise ValueError("market must be a bounded token or None")
        if self.layer is not None and not isinstance(self.layer, Layer):
            raise ValueError("layer must be a Layer or None")
        if not isinstance(self.time_scope, TimeScope):
            raise ValueError("time_scope must be a TimeScope")
        if not isinstance(self.requested_depth, Depth) or not isinstance(
            self.effective_depth, Depth
        ):
            raise ValueError("depths must be Depth values")
        if self.effective_depth.rank > self.requested_depth.rank:
            raise ValueError("effective depth cannot exceed the requested depth")
        for name in (
            "requires_live_intelligence",
            "requires_evidence",
            "requires_lineage",
            "requires_setup_context",
            "actionable",
        ):
            if not isinstance(getattr(self, name), bool):
                raise ValueError(f"{name} must be a bool")
        if self.requires_live_intelligence != (self.time_scope is TimeScope.CURRENT):
            raise ValueError("live requirement must match CURRENT scope")
        if not isinstance(self.confidence, PlanConfidence):
            raise ValueError("confidence must be a PlanConfidence")
        if not isinstance(self.ambiguities, tuple) or any(
            not isinstance(entry, Ambiguity) for entry in self.ambiguities
        ):
            raise ValueError("ambiguities must be a tuple of Ambiguity")
        if self.query_contract_version not in SUPPORTED_QUERY_CONTRACT_VERSIONS:
            raise ValueError("unsupported query contract version")
        if self.plan_id and not self.plan_id.startswith(PLAN_ID_PREFIX):
            raise ValueError("plan_id must use the PLAN. prefix")

    # -- identity ------------------------------------------------------
    def payload(self, *, include_id: bool = True) -> dict[str, Any]:
        out: dict[str, Any] = {
            "query_contract_version": self.query_contract_version,
            "intent": self.intent.value,
            "entities": [entity.payload() for entity in self.entities],
            "model_ids": list(self.model_ids),
            "setup_ids": list(self.setup_ids),
            "market": self.market,
            "layer": self.layer.value if self.layer is not None else None,
            "time_scope": self.time_scope.value,
            "requested_depth": self.requested_depth.value,
            "effective_depth": self.effective_depth.value,
            "requires_live_intelligence": self.requires_live_intelligence,
            "requires_evidence": self.requires_evidence,
            "requires_lineage": self.requires_lineage,
            "requires_setup_context": self.requires_setup_context,
            "actionable": self.actionable,
            "requested_fields": list(self.requested_fields),
            "confidence": self.confidence.value,
            "ambiguities": [entry.payload() for entry in self.ambiguities],
        }
        if include_id:
            out["plan_id"] = self.plan_id
        return out

    def compute_id(self) -> str:
        digest = hashlib.sha256(
            canonical_json(self.payload(include_id=False)).encode("utf-8")
        ).hexdigest()
        return PLAN_ID_PREFIX + digest[:PLAN_ID_LENGTH]

    def finalized(self) -> "AskCerebusQueryPlan":
        return replace(self, plan_id=self.compute_id())

    def to_json(self) -> str:
        return canonical_json(self.payload())

    # -- interpretation outcome ---------------------------------------
    @property
    def outcome(self) -> AmbiguityOutcome:
        codes = {entry.code for entry in self.ambiguities}
        if AmbiguityReason.UNSUPPORTED_IDENTITY in codes:
            return AmbiguityOutcome.UNSUPPORTED_IDENTITY
        if AmbiguityReason.UNAVAILABLE_GENERATION in codes:
            return AmbiguityOutcome.UNAVAILABLE_GENERATION
        if AmbiguityReason.UNSUPPORTED_STATISTIC in codes:
            return AmbiguityOutcome.UNSUPPORTED_STATISTIC
        if any(entry.material for entry in self.ambiguities):
            return AmbiguityOutcome.MATERIAL_AMBIGUITY
        if self.confidence is PlanConfidence.EXPLICIT_SCOPE or any(
            entry.code is not AmbiguityReason.DEPTH_CAPPED
            for entry in self.ambiguities
        ):
            return AmbiguityOutcome.RESOLVED_WITH_EXPLICIT_SCOPE
        return AmbiguityOutcome.RESOLVED

    def unresolved_entities(self) -> tuple[EntityRef, ...]:
        return tuple(
            entity
            for entity in self.entities
            if entity.canonical_id is None
            and entity.kind in (EntityKind.MODEL, EntityKind.SETUP, EntityKind.INSTRUMENT)
        )


__all__ = [
    "PLAN_ID_PREFIX",
    "PLAN_ID_LENGTH",
    "Ambiguity",
    "AskCerebusQueryPlan",
    "canonical_json",
]
