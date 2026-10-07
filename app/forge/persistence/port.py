"""Persistence port for FORGE (Book II / Bloc II.2).

`PersistenceGateway` is the ONLY persistence surface FORGE services may use.
Implementations are explicitly injected; there is no module-level connection
or singleton anywhere in FORGE.

Implementations:
- `app.forge.persistence.memory.InMemoryPersistenceGateway` — real port
  implementation enforcing every FORGE integrity rule (unit truth).
- `app.forge.persistence.sql.SqlAlchemyPersistenceGateway` — PostgreSQL
  implementation over SQLAlchemy Core; executes its portable SQL migration
  contract (locally exercised on SQLite for dialect/schema truth only).
"""

from __future__ import annotations

from typing import Any, Iterable, Protocol, runtime_checkable

from app.forge.persistence.records import (
    ArtifactRecord,
    CanonicalObjectRecord,
    ProvenanceEdgeRecord,
    WriteResult,
)


class PersistenceError(Exception):
    """Base class for deterministic persistence failures."""

    def __init__(self, kind: str, message: str) -> None:
        super().__init__(message)
        self.kind = kind


class DuplicateCanonicalObject(PersistenceError):
    def __init__(self, canonical_id: str) -> None:
        super().__init__("DUPLICATE_CANONICAL_OBJECT", f"duplicate canonical object: {canonical_id}")
        self.canonical_id = canonical_id


class DuplicateArtifact(PersistenceError):
    def __init__(self, artifact_id: str) -> None:
        super().__init__("DUPLICATE_ARTIFACT", f"duplicate artifact: {artifact_id}")


class DuplicateProvenanceEdge(PersistenceError):
    def __init__(self, artifact_id: str, object_id: str, relation: str) -> None:
        super().__init__(
            "DUPLICATE_PROVENANCE_EDGE",
            f"duplicate provenance edge: {artifact_id} -[{relation}]-> {object_id}",
        )


class SelfReferenceForbidden(PersistenceError):
    def __init__(self, canonical_id: str) -> None:
        super().__init__("SELF_REFERENCE_FORBIDDEN", f"self reference is not permitted: {canonical_id}")


class DanglingReference(PersistenceError):
    def __init__(self, canonical_id: str, target_id: str) -> None:
        super().__init__(
            "DANGLING_REFERENCE",
            f"dangling reference: {canonical_id} -> {target_id}",
        )


class IllegalStatusTransition(PersistenceError):
    def __init__(self, canonical_id: str, current: str, target: str) -> None:
        super().__init__(
            "ILLEGAL_STATUS_TRANSITION",
            f"illegal status transition for {canonical_id}: {current} -> {target}",
        )


class StaleWriteConflict(PersistenceError):
    def __init__(self, canonical_id: str, expected_version: int) -> None:
        super().__init__(
            "STALE_WRITE_CONFLICT",
            f"stale write for {canonical_id}: expected version {expected_version}",
        )


class ObjectNotFound(PersistenceError):
    def __init__(self, canonical_id: str) -> None:
        super().__init__("OBJECT_NOT_FOUND", f"canonical object not found: {canonical_id}")


class InvalidRecord(PersistenceError):
    """A record violating a canonical schema was rejected at the boundary."""

    def __init__(self, message: str) -> None:
        super().__init__("INVALID_RECORD", message)


class PersistenceUnavailable(PersistenceError):
    """A gateway backend could not be reached (redacted details only)."""

    def __init__(self, kind: str) -> None:
        super().__init__("PERSISTENCE_UNAVAILABLE", f"persistence unavailable: {kind}")
        self.detail = kind


class MigrationIncompatible(PersistenceError):
    def __init__(self, detail: str) -> None:
        super().__init__("MIGRATION_INCOMPATIBLE", f"schema incompatible: {detail}")


class MigrationOutcome:
    """Deterministic migration result identity."""

    APPLIED = "APPLIED"
    CURRENT = "CURRENT"
    INCOMPATIBLE = "INCOMPATIBLE"


@runtime_checkable
class PersistenceGateway(Protocol):
    """The persistence port. Reads return FORGE records, never raw rows."""

    # -- canonical objects -------------------------------------------------
    def create_object(
        self, record: CanonicalObjectRecord, expected_version: int | None = None
    ) -> WriteResult: ...

    def get_object(self, canonical_id: str) -> CanonicalObjectRecord | None: ...

    def list_object_ids(self) -> tuple[str, ...]: ...

    def transition_status(
        self, canonical_id: str, target_status: str, expected_version: int | None = None
    ) -> WriteResult: ...

    # -- artifacts ---------------------------------------------------------
    def create_artifact(
        self, record: ArtifactRecord, expected_version: int | None = None
    ) -> WriteResult: ...

    def get_artifact(self, artifact_id: str) -> ArtifactRecord | None: ...

    # -- provenance --------------------------------------------------------
    def add_provenance_edge(self, record: ProvenanceEdgeRecord) -> None: ...

    def edges_for_object(self, object_id: str) -> tuple[ProvenanceEdgeRecord, ...]: ...

    def edges_from_artifact(self, artifact_id: str) -> tuple[ProvenanceEdgeRecord, ...]: ...

    # -- transaction / infrastructure --------------------------------------
    def transaction(self) -> Any:
        """Context manager committing a multi-record logical write atomically."""

    def ping(self) -> None:
        """Raise PersistenceUnavailable if the backend cannot serve reads/writes."""

    def apply_migrations(self) -> str:
        """Apply pending migrations; returns MigrationOutcome identity."""

    def check_compatibility(self) -> str:
        """Return OK / BEHIND / INCOMPATIBLE / AHEAD schema identity."""


def result_identity(result: WriteResult) -> tuple[str, str, int]:
    """Deterministic identity for write outcomes (used by tests)."""
    return (result.operation, result.canonical_id, result.persisted_version)


__all__ = [
    "PersistenceGateway",
    "PersistenceError",
    "DuplicateCanonicalObject",
    "DuplicateArtifact",
    "DuplicateProvenanceEdge",
    "SelfReferenceForbidden",
    "DanglingReference",
    "IllegalStatusTransition",
    "StaleWriteConflict",
    "ObjectNotFound",
    "InvalidRecord",
    "PersistenceUnavailable",
    "MigrationIncompatible",
    "MigrationOutcome",
    "result_identity",
]
