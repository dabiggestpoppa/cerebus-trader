"""Retrieval object contract for GLX FORGE Book I / Bloc I.4.

Machine counterpart of the frozen ``corpus/canonical/RETRIEVAL_OBJECT_SCHEMA_V1.md``
field set. A retrieval record is a *finding surface* over governed canonical
truth: it never becomes a competing source of canonical truth, never changes an
epistemic status, and never carries a protected body that policy has not
released.

Two structures, one law:

- :class:`RetrievalHeader` — SAFE metadata (identity + classification only).
  Constructible without loading any protected content; this is exactly what
  II.4 ``ResourcePolicyMetadata`` needs to decide before a body is loaded.
- :class:`RetrievalObject` — the full record, including ``retrieval_text`` and
  every content facet. Loaded ONLY through the II.4 deny-before-load primitive.

Facet law (frozen plan): only actual schema fields populate a facet. An
unstated dimension stays empty — it is never fabricated to look complete.
"""

from __future__ import annotations

import hashlib
import json

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.forge.canonical import (
    ClaimIdentity,
    EvidenceStatus,
    Layer,
    ObjectType,
    ProductExposure,
)

# Object types the frozen retrieval schema admits (MODEL | CLAIM | EVIDENCE |
# SETUP | DOCTRINE | TERM | LINEAGE). ARTIFACT is deliberately absent: source
# artifacts are provenance targets, never retrieval records.
RETRIEVAL_OBJECT_TYPES: frozenset[ObjectType] = frozenset(
    {
        ObjectType.MODEL,
        ObjectType.CLAIM,
        ObjectType.EVIDENCE,
        ObjectType.SETUP,
        ObjectType.DOCTRINE,
        ObjectType.TERM,
        ObjectType.LINEAGE,
    }
)

QUOTE_SCOPE_SYNTHESIS = "SYNTHESIS"
QUOTE_SCOPE_NONE = "NONE"

# ---------------------------------------------------------------------------
# Structured fields (frozen schema "Structured fields")
# ---------------------------------------------------------------------------


class StructuredFields(BaseModel):
    """Exact structured facets. Empty means "not stated by the source"."""

    model_config = ConfigDict(frozen=True)

    terms: tuple[str, ...] = ()
    aliases: tuple[str, ...] = ()
    clocks: tuple[str, ...] = ()
    states: tuple[str, ...] = ()
    events: tuple[str, ...] = ()
    levels: tuple[str, ...] = ()
    metrics: tuple[str, ...] = ()
    sample_n: int | None = None
    period: str | None = None
    implementation_ids: tuple[str, ...] = ()
    claim_identity: ClaimIdentity | None = None


# ---------------------------------------------------------------------------
# Routing metadata (frozen schema "Routing metadata")
# ---------------------------------------------------------------------------

# Compiler constant table encoding the frozen Answer Contract depth model
# (Beginner / Operator / Researcher). These are routing weights, never
# evidence authority: a weight cannot change a status, a support class, or a
# policy decision. Frozen by test.
ROUTING_WEIGHTS: dict[ObjectType, tuple[float, float, float]] = {
    ObjectType.MODEL: (0.9, 1.0, 1.0),
    ObjectType.CLAIM: (0.4, 0.6, 1.0),
    ObjectType.EVIDENCE: (0.3, 0.7, 1.0),
    ObjectType.SETUP: (0.6, 1.0, 0.7),
    ObjectType.DOCTRINE: (1.0, 0.6, 0.7),
    ObjectType.TERM: (1.0, 0.4, 0.4),
    ObjectType.LINEAGE: (0.7, 0.7, 1.0),
}


class RoutingMetadata(BaseModel):
    model_config = ConfigDict(frozen=True)

    beginner_weight: float
    operator_weight: float
    researcher_weight: float
    actionable: bool
    requires_setup_card: bool
    requires_evidence_card: bool


# ---------------------------------------------------------------------------
# Leakage metadata (frozen schema "Leakage metadata")
# ---------------------------------------------------------------------------


class LeakageMetadata(BaseModel):
    model_config = ConfigDict(frozen=True)

    contains_internal_method: bool = False
    contains_code: bool = False
    max_quote_scope: str = QUOTE_SCOPE_SYNTHESIS


# ---------------------------------------------------------------------------
# Conflict metadata (frozen schema "Conflict metadata")
# ---------------------------------------------------------------------------


class ConflictMetadata(BaseModel):
    model_config = ConfigDict(frozen=True)

    supersedes_ids: tuple[str, ...] = ()
    contradicts_ids: tuple[str, ...] = ()
    generation: str = ""


# ---------------------------------------------------------------------------
# Provenance / relationship extensions required by the frozen Provenance rule
# ---------------------------------------------------------------------------


class RelatedLink(BaseModel):
    """One typed object -> object reference (I.1 canonical reference)."""

    model_config = ConfigDict(frozen=True)

    relation: str
    target_id: str


class ProvenanceLink(BaseModel):
    """One artifact -> object provenance edge with safe artifact metadata.

    Content identity and locator are provenance routing facts (I.2), not body
    content; artifact file contents are never loaded by I.4 at all.
    """

    model_config = ConfigDict(frozen=True)

    artifact_id: str
    relation: str
    source_class: str
    source_state: str
    content_identity: str | None = None
    locator: str = ""


class SupportAssessment(BaseModel):
    """FOUND vs SUPPORTED, derived at build time from the ratified I.2
    ``classify_support`` over the resolved canonical chain.

    A boolean/classification only — never a claim of truth, never a number.
    """

    model_config = ConfigDict(frozen=True)

    supported: bool = False
    classification: str = "NO_SOURCE"
    evidence_ids: tuple[str, ...] = ()
    gaps: tuple[str, ...] = ()


# ---------------------------------------------------------------------------
# Header (safe) and full record (protected)
# ---------------------------------------------------------------------------


class RetrievalHeader(BaseModel):
    """Safe resource metadata: everything retrieval may know before deciding,
    nothing that requires loading a protected body."""

    model_config = ConfigDict(frozen=True)

    object_id: str
    object_type: ObjectType
    canonical_version: str
    status: EvidenceStatus
    # Optional so a corrupted/unknown exposure can exist and FAIL CLOSED
    # (II.4 denies UNKNOWN_EXPOSURE) instead of being coerced to a class.
    exposure: ProductExposure | None = None
    layer: Layer = Layer.NONE
    market_scope: tuple[str, ...] = ()
    model_family: str = ""
    source_artifact_ids: tuple[str, ...] = ()


class RetrievalObject(BaseModel):
    """One compiled retrieval record (frozen RETRIEVAL_OBJECT_SCHEMA_V1)."""

    model_config = ConfigDict(frozen=True)

    # identity / classification
    object_id: str
    object_type: ObjectType
    canonical_version: str
    title: str
    market_scope: tuple[str, ...] = ()
    layer: Layer = Layer.NONE
    status: EvidenceStatus
    exposure_class: ProductExposure | None = None
    parent_ids: tuple[str, ...] = ()
    source_artifact_ids: tuple[str, ...] = ()

    # content
    retrieval_text: str = ""
    structured: StructuredFields = Field(default_factory=StructuredFields)
    routing: RoutingMetadata
    leakage: LeakageMetadata = Field(default_factory=LeakageMetadata)
    conflict: ConflictMetadata = Field(default_factory=ConflictMetadata)
    support: SupportAssessment = Field(default_factory=SupportAssessment)

    # navigation
    related_ids: tuple[RelatedLink, ...] = ()
    provenance: tuple[ProvenanceLink, ...] = ()

    # index generation this record was compiled into
    generation: int = 1

    @field_validator("object_type")
    @classmethod
    def validate_retrieval_type(cls, value: ObjectType) -> ObjectType:
        if value not in RETRIEVAL_OBJECT_TYPES:
            raise ValueError(
                f"object type {value.value} is not a retrieval object type"
            )
        return value

    def header(self) -> RetrievalHeader:
        """The safe projection used for candidate selection and policy input."""

        return RetrievalHeader(
            object_id=self.object_id,
            object_type=self.object_type,
            canonical_version=self.canonical_version,
            status=self.status,
            exposure=self.exposure_class,
            layer=self.layer,
            market_scope=self.market_scope,
            model_family=_model_family(self.object_id),
            source_artifact_ids=self.source_artifact_ids,
        )

    def deterministic_payload(self) -> str:
        """Reference-order-normalized payload: identity never depends on the
        order in which relationships happen to be stored (I.3 limitation A).

        The index ``generation`` a record was published into is bookkeeping,
        not content: it is excluded so a rebuild reports only records whose
        governed content actually changed.
        """

        payload = self.model_dump(mode="json")
        payload.pop("generation", None)
        payload["related_ids"] = sorted(
            payload["related_ids"],
            key=lambda item: (item["relation"], item["target_id"]),
        )
        payload["provenance"] = sorted(
            payload["provenance"],
            key=lambda item: (item["artifact_id"], item["relation"]),
        )
        payload["source_artifact_ids"] = sorted(payload["source_artifact_ids"])
        payload["parent_ids"] = sorted(payload["parent_ids"])
        payload["structured"] = dict(payload["structured"])
        payload["structured"]["terms"] = sorted(payload["structured"]["terms"])
        payload["structured"]["aliases"] = sorted(payload["structured"]["aliases"])
        payload["structured"]["clocks"] = sorted(payload["structured"]["clocks"])
        payload["structured"]["states"] = sorted(payload["structured"]["states"])
        payload["structured"]["events"] = sorted(payload["structured"]["events"])
        payload["structured"]["levels"] = sorted(payload["structured"]["levels"])
        payload["structured"]["metrics"] = sorted(payload["structured"]["metrics"])
        payload["structured"]["implementation_ids"] = sorted(
            payload["structured"]["implementation_ids"]
        )
        return json.dumps(
            payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False
        )

    def content_hash(self) -> str:
        return hashlib.sha256(self.deterministic_payload().encode("utf-8")).hexdigest()


def _model_family(canonical_id: str) -> str:
    """Family token of the frozen canonical-id grammar (``MOD.EUR.…`` → ``EUR``).

    Derived from the id itself: no invented universal "family" field exists.
    """

    parts = canonical_id.split(".")
    return parts[1] if len(parts) > 2 else ""


def model_family_of(canonical_id: str) -> str:
    return _model_family(canonical_id)


__all__ = [
    "RETRIEVAL_OBJECT_TYPES",
    "QUOTE_SCOPE_SYNTHESIS",
    "QUOTE_SCOPE_NONE",
    "ROUTING_WEIGHTS",
    "StructuredFields",
    "RoutingMetadata",
    "LeakageMetadata",
    "ConflictMetadata",
    "RelatedLink",
    "ProvenanceLink",
    "SupportAssessment",
    "RetrievalHeader",
    "RetrievalObject",
    "model_family_of",
]
