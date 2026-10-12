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

import json
import math
import re
from typing import Any, Iterable, Protocol, runtime_checkable

from app.forge.canonical import ProductExposure
from app.forge.identity import ExternalIdentityLink, ForgeSession, ForgeUser
from app.forge.persistence.records import (
    ArtifactRecord,
    AuditEventRecord,
    CanonicalObjectRecord,
    ProvenanceEdgeRecord,
    VectorProjectionRecord,
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


# -- identity/session exceptions (Book II / Bloc II.3) -----------------------


class DuplicateForgeUser(PersistenceError):
    def __init__(self, user_id: str) -> None:
        super().__init__("DUPLICATE_FORGE_USER", f"duplicate forge user: {user_id}")


class UserNotFound(PersistenceError):
    def __init__(self, user_id: str) -> None:
        super().__init__("USER_NOT_FOUND", f"forge user not found: {user_id}")


class IllegalUserStateTransition(PersistenceError):
    def __init__(self, user_id: str, current: str, target: str) -> None:
        super().__init__(
            "ILLEGAL_USER_STATE_TRANSITION",
            f"illegal user state transition for {user_id}: {current} -> {target}",
        )


class DuplicateIdentityLink(PersistenceError):
    def __init__(self, provider: str, provider_subject: str) -> None:
        super().__init__(
            "DUPLICATE_IDENTITY_LINK",
            f"duplicate identity link: {provider}:{provider_subject}",
        )


class IdentityLinkNotFound(PersistenceError):
    def __init__(self, provider: str, provider_subject: str) -> None:
        super().__init__(
            "IDENTITY_LINK_NOT_FOUND",
            f"identity link not found: {provider}:{provider_subject}",
        )


class DuplicateSession(PersistenceError):
    def __init__(self, detail: str) -> None:
        super().__init__("DUPLICATE_SESSION", f"duplicate session: {detail}")


class SessionNotFound(PersistenceError):
    def __init__(self, session_id: str) -> None:
        super().__init__("SESSION_NOT_FOUND", f"forge session not found: {session_id}")


class MigrationOutcome:
    """Deterministic migration result identity."""

    APPLIED = "APPLIED"
    CURRENT = "CURRENT"
    INCOMPATIBLE = "INCOMPATIBLE"


# -- vector projection contract (frozen Ch II.2.4, Book II closure repair) ---

VECTOR_MAX_DIMS = 16000  # pgvector storage ceiling; Book VII owns model choice

_CANONICAL_HASH_RE = re.compile(r"^[0-9a-f]{64}$")


def exposure_allowlist(allowed_exposures: Iterable[Any]) -> tuple[str, ...]:
    """Normalized, sorted exposure allow-set; empty means fail closed."""

    values = {
        getattr(item, "value", item) if isinstance(item, ProductExposure) else str(item)
        for item in allowed_exposures
    }
    return tuple(sorted(values))


def validate_vector_projection(record: VectorProjectionRecord) -> None:
    """Shared write-path validation — byte-identical rules on every gateway.

    STORAGE != INTELLIGENCE: Book II validates shape, dimension, provenance
    fields and vocabulary membership; embedding generation/model selection is
    Book VII, canonical truth is Book I.
    """

    if not record.object_id or not record.object_id.strip():
        raise InvalidRecord("vector projection requires a non-empty object_id")
    if not record.object_version or not record.object_version.strip():
        raise InvalidRecord("vector projection requires a non-empty object_version")
    if record.embedding_dim <= 0 or record.embedding_dim > VECTOR_MAX_DIMS:
        raise InvalidRecord(
            f"embedding_dim must be in 1..{VECTOR_MAX_DIMS}, got {record.embedding_dim}"
        )
    if len(record.embedding) != record.embedding_dim:
        raise InvalidRecord(
            f"embedding length {len(record.embedding)} != embedding_dim {record.embedding_dim}"
        )
    for value in record.embedding:
        try:
            numeric = float(value)
        except (TypeError, ValueError):
            raise InvalidRecord("embedding values must be numeric") from None
        if not math.isfinite(numeric):
            raise InvalidRecord("embedding values must be finite")
    if all(float(value) == 0.0 for value in record.embedding):
        raise InvalidRecord("embedding must be non-zero (cosine similarity domain)")
    if not record.embedding_model or not record.embedding_model.strip():
        raise InvalidRecord("embedding_model is required (stored, never selected here)")
    if not record.embedding_version or not record.embedding_version.strip():
        raise InvalidRecord("embedding_version is required")
    if not _CANONICAL_HASH_RE.match(record.canonical_hash or ""):
        raise InvalidRecord("canonical_hash must be a 64-char lowercase hex digest")
    if not isinstance(record.exposure_class, ProductExposure):
        raise InvalidRecord(
            "exposure_class must be a frozen ProductExposure member (fail closed)"
        )
    try:
        json.loads(record.payload_json)
    except (TypeError, ValueError):
        raise InvalidRecord("payload_json must be valid JSON") from None
    if record.owner_user_id is not None and not record.owner_user_id.strip():
        raise InvalidRecord("owner_user_id must be None or a non-empty user id")


def validate_similarity_query(embedding: Iterable[Any]) -> tuple[float, ...]:
    """Validate a caller-supplied query vector before it reaches any backend."""

    try:
        query = tuple(float(value) for value in embedding)
    except (TypeError, ValueError):
        raise InvalidRecord("query embedding must be numeric") from None
    if not query:
        raise InvalidRecord("query embedding must be non-empty")
    if len(query) > VECTOR_MAX_DIMS:
        raise InvalidRecord(f"query embedding exceeds {VECTOR_MAX_DIMS} dimensions")
    if any(not math.isfinite(value) for value in query):
        raise InvalidRecord("query embedding must be finite")
    if all(value == 0.0 for value in query):
        raise InvalidRecord("query embedding must be non-zero (cosine similarity domain)")
    return query


def cosine_distance(a: tuple[float, ...], b: tuple[float, ...]) -> float:
    """1 - cosine similarity, matching the pgvector `<=>` operator domain."""

    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(y * y for y in b))
    if na == 0.0 or nb == 0.0:
        return 1.0
    similarity = dot / (na * nb)
    # Numeric clamp: cosine is defined on [-1, 1].
    if similarity > 1.0:
        similarity = 1.0
    elif similarity < -1.0:
        similarity = -1.0
    return 1.0 - similarity


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

    def transition_artifact_state(
        self, artifact_id: str, target_state: str, expected_version: int | None = None
    ) -> WriteResult:
        """Governed artifact source-state transition with optimistic check."""

        ...

    # -- provenance --------------------------------------------------------
    def add_provenance_edge(self, record: ProvenanceEdgeRecord) -> None: ...

    def edges_for_object(self, object_id: str) -> tuple[ProvenanceEdgeRecord, ...]: ...

    def edges_from_artifact(self, artifact_id: str) -> tuple[ProvenanceEdgeRecord, ...]: ...

    # -- identity / session (Book II / Bloc II.3) ---------------------------
    # Reads return FORGE domain records (app.forge.identity), never raw rows.
    # No method here carries entitlement/plan/license semantics: IDENTITY !=
    # ENTITLEMENT.

    def create_user(
        self, user: ForgeUser, expected_version: int | None = None
    ) -> WriteResult: ...

    def get_user(self, user_id: str) -> ForgeUser | None: ...

    def transition_user_state(
        self, user_id: str, target_state: str, expected_version: int | None = None
    ) -> WriteResult:
        """Governed user lifecycle transition with optimistic check."""

        ...

    def create_identity_link(self, link: ExternalIdentityLink) -> None: ...

    def get_identity_link(
        self, provider: str, provider_subject: str
    ) -> ExternalIdentityLink | None: ...

    def identity_links_for_user(
        self, user_id: str
    ) -> tuple[ExternalIdentityLink, ...]: ...

    def delete_identity_link(self, provider: str, provider_subject: str) -> None:
        """Remove one link. The FORGE user always survives an unlink."""

        ...

    def create_session(
        self, session: ForgeSession, expected_version: int | None = None
    ) -> WriteResult: ...

    def get_session(self, session_id: str) -> ForgeSession | None: ...

    def find_session_by_token_digest(
        self, token_digest: str
    ) -> ForgeSession | None:
        """Resolve a SHA-256 token digest to its session (lookup path)."""

        ...

    def revoke_session(
        self, session_id: str, expected_version: int | None = None
    ) -> WriteResult:
        """Permanently revoke one session (sets revoked_at, bumps version)."""

        ...

    def revoke_all_sessions(self, user_id: str) -> int:
        """Atomically revoke every active session of a user; returns count."""

        ...

    # -- vector projection (frozen Ch II.2.4; GAP-01 closure) ---------------
    def put_vector_projection(self, record: VectorProjectionRecord) -> None:
        """Validate and upsert one projection row.

        Identity = object_id (a model/version change replaces attributes and
        never identity); canonical cross-checks (version/exposure/hash) must
        pass or InvalidRecord is raised with nothing written.
        """

        ...

    def get_vector_projection(
        self,
        object_id: str,
        *,
        allowed_exposures: Iterable[Any],
        tenant: str | None = None,
    ) -> VectorProjectionRecord | None:
        """Deny-before-content-load: exposure allow-set and tenant scope are
        part of the lookup itself; denied and missing are both None (no
        content returned, no existence oracle)."""

        ...

    def search_vectors(
        self,
        embedding: Iterable[Any],
        *,
        allowed_exposures: Iterable[Any],
        tenant: str | None = None,
        limit: int = 10,
    ) -> tuple[VectorProjectionRecord, ...]:
        """Cosine-distance candidates with exposure+tenant filtering applied
        BEFORE any content is selected. Similarity never grants authority:
        persistence decides nothing about entitlement or policy."""

        ...

    def delete_vector_projection(self, object_id: str) -> None:
        """Delete one projection row; canonical truth is never touched."""

        ...

    def rebuild_vector_projection(
        self, records: Iterable[VectorProjectionRecord]
    ) -> tuple[int, int]:
        """Independent deterministic replacement rebuild from authorized
        source records: (rows_written, rows_removed). Projection-only —
        never reads or writes canonical tables beyond cross-checks."""

        ...

    # -- transaction / infrastructure --------------------------------------
    def transaction(self) -> Any:
        """Context manager committing a multi-record logical write atomically."""

    def ping(self) -> None:
        """Raise PersistenceUnavailable if the backend cannot serve reads/writes."""

    def apply_migrations(self) -> str:
        """Apply pending migrations; returns MigrationOutcome identity."""

    def check_compatibility(self) -> str:
        """Return OK / BEHIND / INCOMPATIBLE / AHEAD schema identity."""


@runtime_checkable
class AuditEventPort(Protocol):
    """Durable audit/event ledger port (Book II GAP-05, frozen Ch II.2.6).

    Deliberately SEPARATE from `PersistenceGateway`: the ledger is an
    append-oriented operational/security surface, not part of the canonical/
    identity domain contract, and the dependency direction stays
    observability -> persistence (persistence never imports observability,
    and the frozen K5/K7 law forbids observability importing persistence —
    so `record` is accepted as ANY record-shaped envelope and coerced here
    via `coerce_audit_event`; returns are persistence-side records read back
    duck-typed). Implementations: the SQL gateway (PostgreSQL/SQLite) and
    the in-memory gateway (bounded reference double).
    """

    def append_audit_event(self, record: Any) -> bool:
        """Append one event row. Returns True when newly stored, False when
        the same `event_id` already exists (idempotent, never raises for a
        repeat). Raises PersistenceUnavailable on backend faults."""

        ...

    def list_audit_events(
        self, *, limit: int = 100, stream: str | None = None
    ) -> tuple[AuditEventRecord, ...]:
        """Bounded, seq-ordered (append order) read-back of stored events."""

        ...


_AUDIT_EVENT_FIELDS = (
    "event_id",
    "stream",
    "event_type",
    "severity",
    "occurred_at",
    "details_json",
    "request_id",
    "actor_type",
    "actor_id",
    "resource",
    "outcome",
    "reason",
    "environment",
)

_AUDIT_REQUIRED_FIELDS = ("event_id", "stream", "event_type", "severity", "occurred_at")


def coerce_audit_event(record: Any) -> AuditEventRecord:
    """Normalize any record-shaped audit envelope into `AuditEventRecord`.

    The frozen K5/K7 import law forbids the observability package from
    importing persistence types, so the durable ledger hands over its own
    duck-shaped `LedgerEvent` (identical field names) or a plain mapping.
    Coercion happens HERE, on the persistence side of the boundary; unknown
    shapes fail closed with `InvalidRecord`. `seq`/`created_at` are
    persistence-owned: caller-supplied values are ignored, never trusted.
    """

    if isinstance(record, AuditEventRecord):
        return record
    if isinstance(record, dict):
        values = {name: record.get(name) for name in _AUDIT_EVENT_FIELDS}
    else:
        values = {
            name: getattr(record, name, None) for name in _AUDIT_EVENT_FIELDS
        }
    missing = [name for name in _AUDIT_REQUIRED_FIELDS if not values[name]]
    if missing:
        raise InvalidRecord(f"audit event missing required fields: {missing}")
    return AuditEventRecord(
        **{name: values[name] for name in _AUDIT_EVENT_FIELDS if values[name] is not None}
    )


def result_identity(result: WriteResult) -> tuple[str, str, int]:
    """Deterministic identity for write outcomes (used by tests)."""
    return (result.operation, result.canonical_id, result.persisted_version)


__all__ = [
    "PersistenceGateway",
    "AuditEventPort",
    "AuditEventRecord",
    "coerce_audit_event",
    "VectorProjectionRecord",
    "VECTOR_MAX_DIMS",
    "validate_vector_projection",
    "validate_similarity_query",
    "exposure_allowlist",
    "cosine_distance",
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
    "DuplicateForgeUser",
    "UserNotFound",
    "IllegalUserStateTransition",
    "DuplicateIdentityLink",
    "IdentityLinkNotFound",
    "DuplicateSession",
    "SessionNotFound",
    "result_identity",
]
