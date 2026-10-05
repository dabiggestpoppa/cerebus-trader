"""Canonical Registry Kernel for GLX FORGE Book I / Bloc I.1.

This module owns canonical identity/validation only. It intentionally contains no
persistence, retrieval, market calculation, LLM, commerce, or UI behavior.
"""
from __future__ import annotations

import hashlib
import json
import re
from enum import Enum
from typing import Any, Iterable

from pydantic import BaseModel, ConfigDict, Field, model_validator


class ObjectType(str, Enum):
    MODEL = "MODEL"
    CLAIM = "CLAIM"
    EVIDENCE = "EVIDENCE"
    SETUP = "SETUP"
    DOCTRINE = "DOCTRINE"
    TERM = "TERM"
    LINEAGE = "LINEAGE"
    ARTIFACT = "ARTIFACT"


class EvidenceStatus(str, Enum):
    OBSERVED = "OBSERVED"
    VALIDATED = "VALIDATED"
    FORWARD_OOS = "FORWARD_OOS"
    CANDIDATE = "CANDIDATE"
    RESEARCH_FLAG = "RESEARCH_FLAG"
    DESCRIPTIVE = "DESCRIPTIVE"
    HISTORICAL = "HISTORICAL"
    PARKED = "PARKED"
    SUPERSEDED = "SUPERSEDED"
    FALSIFIED = "FALSIFIED"
    NO_GO = "NO_GO"
    REPRODUCTION_REQUIRED = "REPRODUCTION_REQUIRED"
    INTERNAL_CONTRADICTION = "INTERNAL_CONTRADICTION"
    IMPLEMENTATION_NOT_PARITY_SAFE = "IMPLEMENTATION_NOT_PARITY_SAFE"


class ProductExposure(str, Enum):
    PUBLIC_TEACHING = "PUBLIC_TEACHING"
    SUBSCRIBER_MODEL = "SUBSCRIBER_MODEL"
    OPERATOR_ONLY = "OPERATOR_ONLY"
    RESEARCH_LAB = "RESEARCH_LAB"
    INTERNAL_METHOD = "INTERNAL_METHOD"
    INTERNAL_CODE = "INTERNAL_CODE"


class Layer(str, Enum):
    L1 = "L1"
    L2 = "L2"
    L3 = "L3"
    CROSS_LAYER = "CROSS_LAYER"
    NONE = "NONE"


class SetupClass(str, Enum):
    MANUAL_OPERATOR = "MANUAL_OPERATOR"
    AUTOMATION_APPROVED = "AUTOMATION_APPROVED"
    RESEARCH_ONLY = "RESEARCH_ONLY"


class EvidenceType(str, Enum):
    RAW_BACKTEST = "RAW_BACKTEST"
    SCIENTIFIC_RETEST = "SCIENTIFIC_RETEST"
    FORWARD_OOS = "FORWARD_OOS"
    LIVE_OPERATOR = "LIVE_OPERATOR"
    HISTORICAL_REPORT = "HISTORICAL_REPORT"
    SIMULATION = "SIMULATION"
    DERIVED_ALGEBRA = "DERIVED_ALGEBRA"
    VISUAL_CONSTANT = "VISUAL_CONSTANT"
    NEGATIVE_EVIDENCE = "NEGATIVE_EVIDENCE"


_ID_PREFIX = {
    ObjectType.MODEL: "MOD",
    ObjectType.CLAIM: "CL",
    ObjectType.EVIDENCE: "EV",
    ObjectType.SETUP: "SET",
    ObjectType.DOCTRINE: "DOC",
    ObjectType.TERM: "TERM",
    ObjectType.LINEAGE: "LIN",
    ObjectType.ARTIFACT: "ART",
}
_PREFIX_TYPE = {v: k for k, v in _ID_PREFIX.items()}
_ID_RE = re.compile(r"^(MOD|CL|EV|SET|DOC|TERM|LIN|ART)\.[A-Z0-9][A-Z0-9_.-]*$")


class CanonicalId(BaseModel):
    """Stable canonical identifier with a type-bearing prefix."""

    model_config = ConfigDict(frozen=True)

    value: str
    object_type: ObjectType

    @model_validator(mode="after")
    def validate_identity(self) -> "CanonicalId":
        if not _ID_RE.fullmatch(self.value):
            raise ValueError("invalid canonical id format")
        prefix = self.value.split(".", 1)[0]
        if _PREFIX_TYPE[prefix] != self.object_type:
            raise ValueError("canonical id prefix does not match object_type")
        return self

    @classmethod
    def parse(cls, value: str) -> "CanonicalId":
        if not _ID_RE.fullmatch(value):
            raise ValueError("invalid canonical id format")
        prefix = value.split(".", 1)[0]
        return cls(value=value, object_type=_PREFIX_TYPE[prefix])


class CanonicalReference(BaseModel):
    model_config = ConfigDict(frozen=True)

    target_id: str
    relation: str = Field(min_length=1)
    allow_unresolved_historical: bool = False

    @model_validator(mode="after")
    def validate_target(self) -> "CanonicalReference":
        CanonicalId.parse(self.target_id)
        return self


class CanonicalObject(BaseModel):
    """Minimum representation shared by canonical registry objects."""

    model_config = ConfigDict(frozen=True)

    canonical_id: CanonicalId
    title: str = Field(min_length=1)
    version: str = Field(min_length=1)
    status: EvidenceStatus
    exposure: ProductExposure
    layer: Layer = Layer.NONE
    references: tuple[CanonicalReference, ...] = ()
    metadata: dict[str, Any] = Field(default_factory=dict)

    def deterministic_payload(self) -> str:
        payload = self.model_dump(mode="json")
        return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)

    def content_hash(self) -> str:
        return hashlib.sha256(self.deterministic_payload().encode("utf-8")).hexdigest()


class ClaimIdentity(BaseModel):
    """Dimensions that define whether two claim results address the same population.

    The result itself (rate, probability, count, etc.) is intentionally absent.
    """

    model_config = ConfigDict(frozen=True)

    market: str = Field(min_length=1)
    event_definition: str = Field(min_length=1)
    conditioning_event: str = Field(min_length=1)
    clock_origin: str = Field(min_length=1)
    horizon: str = Field(min_length=1)
    tolerance: str = Field(min_length=1)
    eligibility: str = Field(min_length=1)
    implementation_semantics: str = Field(min_length=1)

    def comparison_key(self) -> tuple[str, ...]:
        return (
            self.market,
            self.event_definition,
            self.conditioning_event,
            self.clock_origin,
            self.horizon,
            self.tolerance,
            self.eligibility,
            self.implementation_semantics,
        )


class ClaimComparison(str, Enum):
    SAME_POPULATION = "SAME_POPULATION"
    PARALLEL = "PARALLEL"


def compare_claim_identity(left: ClaimIdentity, right: ClaimIdentity) -> ClaimComparison:
    return (
        ClaimComparison.SAME_POPULATION
        if left.comparison_key() == right.comparison_key()
        else ClaimComparison.PARALLEL
    )


_TERMINAL = {
    EvidenceStatus.SUPERSEDED,
    EvidenceStatus.FALSIFIED,
}

# V1 lifecycle is intentionally conservative. Absence from this map means the
# transition is forbidden until governance explicitly expands the contract.
_ALLOWED_TRANSITIONS: dict[EvidenceStatus, set[EvidenceStatus]] = {
    EvidenceStatus.OBSERVED: {
        EvidenceStatus.CANDIDATE,
        EvidenceStatus.DESCRIPTIVE,
        EvidenceStatus.HISTORICAL,
        EvidenceStatus.PARKED,
        EvidenceStatus.FALSIFIED,
        EvidenceStatus.REPRODUCTION_REQUIRED,
    },
    EvidenceStatus.CANDIDATE: {
        EvidenceStatus.VALIDATED,
        EvidenceStatus.FORWARD_OOS,
        EvidenceStatus.RESEARCH_FLAG,
        EvidenceStatus.PARKED,
        EvidenceStatus.FALSIFIED,
        EvidenceStatus.REPRODUCTION_REQUIRED,
        EvidenceStatus.INTERNAL_CONTRADICTION,
    },
    EvidenceStatus.RESEARCH_FLAG: {
        EvidenceStatus.CANDIDATE,
        EvidenceStatus.VALIDATED,
        EvidenceStatus.PARKED,
        EvidenceStatus.FALSIFIED,
        EvidenceStatus.REPRODUCTION_REQUIRED,
    },
    EvidenceStatus.REPRODUCTION_REQUIRED: {
        EvidenceStatus.CANDIDATE,
        EvidenceStatus.VALIDATED,
        EvidenceStatus.PARKED,
        EvidenceStatus.FALSIFIED,
    },
    EvidenceStatus.VALIDATED: {
        EvidenceStatus.FORWARD_OOS,
        EvidenceStatus.SUPERSEDED,
        EvidenceStatus.FALSIFIED,
        EvidenceStatus.INTERNAL_CONTRADICTION,
        EvidenceStatus.IMPLEMENTATION_NOT_PARITY_SAFE,
    },
    EvidenceStatus.FORWARD_OOS: {
        EvidenceStatus.SUPERSEDED,
        EvidenceStatus.FALSIFIED,
        EvidenceStatus.INTERNAL_CONTRADICTION,
        EvidenceStatus.IMPLEMENTATION_NOT_PARITY_SAFE,
    },
    EvidenceStatus.DESCRIPTIVE: {
        EvidenceStatus.HISTORICAL,
        EvidenceStatus.SUPERSEDED,
    },
    EvidenceStatus.HISTORICAL: {
        EvidenceStatus.SUPERSEDED,
        EvidenceStatus.INTERNAL_CONTRADICTION,
    },
    EvidenceStatus.PARKED: {
        EvidenceStatus.CANDIDATE,
        EvidenceStatus.SUPERSEDED,
        EvidenceStatus.FALSIFIED,
    },
    EvidenceStatus.NO_GO: {
        EvidenceStatus.SUPERSEDED,
    },
    EvidenceStatus.INTERNAL_CONTRADICTION: {
        EvidenceStatus.REPRODUCTION_REQUIRED,
        EvidenceStatus.PARKED,
        EvidenceStatus.SUPERSEDED,
        EvidenceStatus.FALSIFIED,
    },
    EvidenceStatus.IMPLEMENTATION_NOT_PARITY_SAFE: {
        EvidenceStatus.CANDIDATE,
        EvidenceStatus.PARKED,
        EvidenceStatus.SUPERSEDED,
    },
}


def validate_status_transition(current: EvidenceStatus, target: EvidenceStatus) -> None:
    if current == target:
        return
    if current in _TERMINAL or target not in _ALLOWED_TRANSITIONS.get(current, set()):
        raise ValueError(f"illegal canonical status transition: {current.value} -> {target.value}")


class CanonicalRegistry:
    """In-memory integrity kernel. Persistence belongs to Book II."""

    def __init__(self, objects: Iterable[CanonicalObject] = ()) -> None:
        self._objects: dict[str, CanonicalObject] = {}
        for obj in objects:
            self.add(obj)

    def add(self, obj: CanonicalObject) -> None:
        key = obj.canonical_id.value
        if key in self._objects:
            raise ValueError(f"duplicate canonical id: {key}")
        for ref in obj.references:
            if ref.target_id == key:
                raise ValueError(f"self reference is not permitted: {key}")
        self._objects[key] = obj

    def get(self, canonical_id: str) -> CanonicalObject:
        try:
            return self._objects[canonical_id]
        except KeyError as exc:
            raise KeyError(f"unknown canonical id: {canonical_id}") from exc

    def validate_references(self) -> None:
        ids = set(self._objects)
        errors: list[str] = []
        for obj in self._objects.values():
            for ref in obj.references:
                if ref.target_id not in ids and not (
                    obj.status == EvidenceStatus.HISTORICAL
                    and ref.allow_unresolved_historical
                ):
                    errors.append(
                        f"{obj.canonical_id.value} -> {ref.target_id} ({ref.relation})"
                    )
        if errors:
            raise ValueError("dangling canonical references: " + "; ".join(sorted(errors)))

    def transition(self, canonical_id: str, target: EvidenceStatus) -> CanonicalObject:
        current = self.get(canonical_id)
        validate_status_transition(current.status, target)
        updated = current.model_copy(update={"status": target})
        self._objects[canonical_id] = updated
        return updated

    def ids(self) -> tuple[str, ...]:
        return tuple(sorted(self._objects))
