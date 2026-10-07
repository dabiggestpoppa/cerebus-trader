"""Persistable FORGE record types.

These records mirror the Book I domain contracts for durable storage. They
are pure dataclasses: no DB library imports, no HTTP imports. Conversion
domain->record->domain is explicit and lossless for governed fields.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

# Importing domain modules from persistence is allowed (dependency direction:
# service/persistence -> domain). Domain never imports persistence.
from app.forge.canonical import (
    CanonicalId,
    CanonicalObject,
    CanonicalReference,
    ClaimIdentity,
    EvidenceStatus,
    Layer,
    ObjectType,
    ProductExposure,
)


@dataclass(frozen=True)
class CanonicalObjectRecord:
    """Durable representation of a canonical object aggregate.

    The references tuple and optional claim identity preserve the I.1
    aggregate exactly; created_at/updated_at/persisted_version are
    persistence-owned and are NOT part of canonical identity.
    """

    canonical_id: str
    object_type: ObjectType
    title: str
    version: str
    status: EvidenceStatus
    exposure: ProductExposure
    layer: Layer
    references: tuple[CanonicalReference, ...] = ()
    metadata: dict[str, Any] = field(default_factory=dict)
    claim_identity: ClaimIdentity | None = None

    @classmethod
    def from_domain(cls, obj: CanonicalObject) -> "CanonicalObjectRecord":
        return cls(
            canonical_id=obj.canonical_id.value,
            object_type=obj.canonical_id.object_type,
            title=obj.title,
            version=obj.version,
            status=obj.status,
            exposure=obj.exposure,
            layer=obj.layer,
            references=tuple(obj.references),
            metadata=dict(obj.metadata),
        )

    def to_domain(self) -> CanonicalObject:
        return CanonicalObject(
            canonical_id=CanonicalId(value=self.canonical_id, object_type=self.object_type),
            title=self.title,
            version=self.version,
            status=self.status,
            exposure=self.exposure,
            layer=self.layer,
            references=self.references,
            metadata=dict(self.metadata),
        )


@dataclass(frozen=True)
class ArtifactRecord:
    """Durable representation of an I.2 artifact."""

    artifact_id: str
    source_class: str
    title: str = ""
    source_generation: str = ""
    version: str | None = None
    locator: str = ""
    content_identity: str | None = None
    source_state: str = "LOCATED"
    created_at: str | None = None
    observed_at: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_domain(cls, artifact: Any) -> "ArtifactRecord":
        # `artifact` is app.forge.provenance.Artifact; typed loosely to keep
        # this module free of a provenance import cycle in annotations.
        return cls(
            artifact_id=artifact.artifact_id,
            source_class=artifact.source_class,
            title=artifact.title,
            source_generation=artifact.source_generation,
            version=artifact.version,
            locator=artifact.locator,
            content_identity=artifact.content_identity,
            source_state=artifact.source_state.value,
            created_at=artifact.created_at,
            observed_at=artifact.observed_at,
            metadata=dict(artifact.metadata),
        )

    def to_domain(self) -> Any:
        from app.forge.provenance import Artifact, SourceState

        return Artifact(
            artifact_id=self.artifact_id,
            source_class=self.source_class,
            title=self.title,
            source_generation=self.source_generation,
            version=self.version,
            locator=self.locator,
            content_identity=self.content_identity,
            source_state=SourceState(self.source_state),
            created_at=self.created_at,
            observed_at=self.observed_at,
            metadata=dict(self.metadata),
        )


@dataclass(frozen=True)
class ProvenanceEdgeRecord:
    """Durable representation of a typed provenance edge."""

    artifact_id: str
    object_id: str
    relation: str
    note: str = ""


@dataclass(frozen=True)
class WriteResult:
    """Deterministic write outcome."""

    operation: str  # CREATE | TRANSITION | UPDATE | NO_CHANGE
    canonical_id: str
    persisted_version: int
