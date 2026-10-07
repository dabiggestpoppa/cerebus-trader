"""In-memory persistence gateway — a real implementation of the port.

It enforces every FORGE integrity rule (uniqueness, provenance-edge
uniqueness, lifecycle legality, optimistic version checks, atomic
transactions). It is NOT a fake of PostgreSQL and makes no pretense of
durability; it exists so unit truth never requires a database server.
"""

from __future__ import annotations

from dataclasses import replace
from typing import Any, Iterator

from app.forge.canonical import validate_status_transition
from app.forge.persistence.port import (
    DuplicateArtifact,
    DuplicateCanonicalObject,
    DuplicateProvenanceEdge,
    DanglingReference,
    IllegalStatusTransition,
    MigrationOutcome,
    ObjectNotFound,
    PersistenceUnavailable,
    SelfReferenceForbidden,
    StaleWriteConflict,
)
from app.forge.persistence.records import (
    ArtifactRecord,
    CanonicalObjectRecord,
    ProvenanceEdgeRecord,
    WriteResult,
)

MIGRATION_VERSIONS: tuple[int, ...] = (1,)


class _Transaction:
    """Deferred-conflict transaction: validates and applies at commit."""

    def __init__(self, gateway: "InMemoryPersistenceGateway") -> None:
        self._gateway = gateway

    def __enter__(self) -> "_Transaction":
        self._gateway._in_transaction = True
        return self

    def __exit__(self, exc_type: Any, exc: Any, tb: Any) -> None:
        if exc_type is not None:
            self._gateway._rollback_buffer()
            return
        self._gateway._commit_buffer()


class InMemoryPersistenceGateway:
    def __init__(self, *, simulate_unavailable: bool = False) -> None:
        self._objects: dict[str, tuple[CanonicalObjectRecord, int]] = {}
        self._artifacts: dict[str, tuple[ArtifactRecord, int]] = {}
        self._edges: dict[tuple[str, str, str], ProvenanceEdgeRecord] = {}
        self._buffer: list[tuple[str, Any]] = []
        self._in_transaction: bool = False
        self._simulate_unavailable = simulate_unavailable
        self._migrations_applied: tuple[int, ...] = MIGRATION_VERSIONS

    # -- integrity helpers ---------------------------------------------------
    def _validate_references(self, record: CanonicalObjectRecord) -> None:
        if record.claim_identity is not None and record.object_type.value != "CLAIM":
            raise ValueError("claim_identity is only valid on CLAIM objects")
        for ref in record.references:
            if ref.target_id == record.canonical_id:
                raise SelfReferenceForbidden(record.canonical_id)
            # allow_unresolved_historical references may dangle by design;
            # ordinary references must resolve against persisted objects.
            if not ref.allow_unresolved_historical and ref.target_id not in self._objects:
                raise DanglingReference(record.canonical_id, ref.target_id)

    def _check_version(
        self, key: str, expected: int | None, store: dict[str, tuple[Any, int]]
    ) -> int:
        if key not in store:
            if expected is not None:
                raise StaleWriteConflict(key, expected)
            return 0
        current = store[key][1]
        if expected is not None and expected != current:
            raise StaleWriteConflict(key, expected)
        return current

    # -- canonical objects ---------------------------------------------------
    def create_object(
        self, record: CanonicalObjectRecord, expected_version: int | None = None
    ) -> WriteResult:
        if record.canonical_id in self._objects:
            raise DuplicateCanonicalObject(record.canonical_id)
        self._validate_references(record)
        if self._in_transaction:
            self._buffer.append(("object", record))
            return WriteResult("CREATE", record.canonical_id, -1)
        version = self._check_version(record.canonical_id, expected_version, self._objects) + 1
        self._objects[record.canonical_id] = (record, version)
        return WriteResult("CREATE", record.canonical_id, version)

    def get_object(self, canonical_id: str) -> CanonicalObjectRecord | None:
        entry = self._objects.get(canonical_id)
        return entry[0] if entry else None

    def list_object_ids(self) -> tuple[str, ...]:
        return tuple(sorted(self._objects))

    def transition_status(
        self, canonical_id: str, target_status: str, expected_version: int | None = None
    ) -> WriteResult:
        if canonical_id not in self._objects:
            raise ObjectNotFound(canonical_id)
        record, version = self._objects[canonical_id]
        if expected_version is not None and expected_version != version:
            raise StaleWriteConflict(canonical_id, expected_version)
        from app.forge.canonical import EvidenceStatus

        target = EvidenceStatus(target_status)
        try:
            validate_status_transition(record.status, target)
        except ValueError as exc:
            raise IllegalStatusTransition(
                canonical_id, record.status.value, target_status
            ) from exc
        updated = CanonicalObjectRecord(
            canonical_id=record.canonical_id,
            object_type=record.object_type,
            title=record.title,
            version=record.version,
            status=target,
            exposure=record.exposure,
            layer=record.layer,
            references=record.references,
            metadata=record.metadata,
            claim_identity=record.claim_identity,
        )
        self._objects[canonical_id] = (updated, version + 1)
        return WriteResult("TRANSITION", canonical_id, version + 1)

    # -- artifacts -----------------------------------------------------------
    def create_artifact(
        self, record: ArtifactRecord, expected_version: int | None = None
    ) -> WriteResult:
        if record.artifact_id in self._artifacts:
            raise DuplicateArtifact(record.artifact_id)
        version = self._check_version(record.artifact_id, expected_version, self._artifacts) + 1
        self._artifacts[record.artifact_id] = (record, version)
        return WriteResult("CREATE", record.artifact_id, version)

    def get_artifact(self, artifact_id: str) -> ArtifactRecord | None:
        entry = self._artifacts.get(artifact_id)
        return entry[0] if entry else None

    def transition_artifact_state(
        self, artifact_id: str, target_state: str, expected_version: int | None = None
    ) -> WriteResult:
        """Governed artifact source-state transition (I.2 machine) with
        optimistic version check. Reuses the frozen domain transition rules."""

        from app.forge.provenance import SourceState, validate_source_state_transition

        if artifact_id not in self._artifacts:
            raise ObjectNotFound(artifact_id)
        record, version = self._artifacts[artifact_id]
        if expected_version is not None and expected_version != version:
            raise StaleWriteConflict(artifact_id, expected_version)
        target = SourceState(target_state)
        try:
            validate_source_state_transition(SourceState(record.source_state), target)
            if target is SourceState.MISSING and record.content_identity is not None:
                raise ValueError("a MISSING source cannot carry content identity")
        except ValueError as exc:
            raise IllegalStatusTransition(
                artifact_id, record.source_state, target_state
            ) from exc
        updated = replace(record, source_state=target.value)
        self._artifacts[artifact_id] = (updated, version + 1)
        return WriteResult("TRANSITION", artifact_id, version + 1)

    # -- provenance ----------------------------------------------------------
    def add_provenance_edge(self, record: ProvenanceEdgeRecord) -> None:
        key = (record.artifact_id, record.object_id, record.relation)
        if key in self._edges:
            raise DuplicateProvenanceEdge(*key)
        if record.artifact_id not in self._artifacts:
            raise DanglingReference("provenance_edge", record.artifact_id)
        if record.object_id not in self._objects:
            raise DanglingReference("provenance_edge", record.object_id)
        self._edges[key] = record

    def edges_for_object(self, object_id: str) -> tuple[ProvenanceEdgeRecord, ...]:
        return tuple(
            self._edges[key]
            for key in sorted(self._edges)
            if key[1] == object_id
        )

    def edges_from_artifact(self, artifact_id: str) -> tuple[ProvenanceEdgeRecord, ...]:
        return tuple(
            self._edges[key]
            for key in sorted(self._edges)
            if key[0] == artifact_id
        )

    # -- transactions ----------------------------------------------------------
    def transaction(self) -> _Transaction:
        return _Transaction(self)

    def _commit_buffer(self) -> None:
        buffered_objects = [r for op, r in self._buffer if op == "object"]
        self._buffer.clear()
        self._in_transaction = False
        # Validate ALL buffered objects against pre-commit state (atomicity).
        for record in buffered_objects:
            if record.canonical_id in self._objects:
                raise DuplicateCanonicalObject(record.canonical_id)
            for ref in record.references:
                if ref.target_id == record.canonical_id:
                    raise SelfReferenceForbidden(record.canonical_id)
                if not ref.allow_unresolved_historical and ref.target_id not in self._objects:
                    raise DanglingReference(record.canonical_id, ref.target_id)
        for record in buffered_objects:
            version = self._objects[record.canonical_id][1] + 1 if record.canonical_id in self._objects else 1
            self._objects[record.canonical_id] = (record, version)

    def _rollback_buffer(self) -> None:
        self._buffer.clear()
        self._in_transaction = False

    # -- infrastructure --------------------------------------------------------
    def ping(self) -> None:
        if self._simulate_unavailable:
            raise PersistenceUnavailable("simulated_backend_down")

    def apply_migrations(self) -> str:
        self._migrations_applied = MIGRATION_VERSIONS
        return MigrationOutcome.CURRENT

    def check_compatibility(self) -> str:
        return "OK"

    # -- test helpers ----------------------------------------------------------
    def object_version(self, canonical_id: str) -> int:
        return self._objects[canonical_id][1]

    def artifact_version(self, artifact_id: str) -> int:
        return self._artifacts[artifact_id][1]
