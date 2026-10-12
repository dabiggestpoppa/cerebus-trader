"""In-memory persistence gateway — a real implementation of the port.

It enforces every FORGE integrity rule (uniqueness, provenance-edge
uniqueness, lifecycle legality, optimistic version checks, atomic
transactions). It is NOT a fake of PostgreSQL and makes no pretense of
durability; it exists so unit truth never requires a database server.
"""

from __future__ import annotations

from dataclasses import replace
from datetime import datetime
from typing import Any, Iterable, Iterator

from app.forge.canonical import validate_status_transition
from app.forge.identity import (
    ExternalIdentityLink,
    ForgeSession,
    ForgeUser,
    IdentityRole,
    UserState,
    utc_now_iso,
    validate_user_state_transition,
)
from app.forge.persistence.port import (
    DanglingReference,
    DuplicateArtifact,
    DuplicateCanonicalObject,
    DuplicateIdentityLink,
    DuplicateProvenanceEdge,
    DuplicateSession,
    DuplicateForgeUser,
    IdentityLinkNotFound,
    IllegalStatusTransition,
    IllegalUserStateTransition,
    InvalidRecord,
    MigrationOutcome,
    ObjectNotFound,
    PersistenceUnavailable,
    SelfReferenceForbidden,
    SessionNotFound,
    StaleWriteConflict,
    UserNotFound,
    coerce_audit_event,
    cosine_distance,
    exposure_allowlist,
    validate_similarity_query,
    validate_vector_projection,
)
from app.forge.persistence.records import (
    ArtifactRecord,
    AuditEventRecord,
    CanonicalObjectRecord,
    ProvenanceEdgeRecord,
    VectorProjectionRecord,
    WriteResult,
)

MIGRATION_VERSIONS: tuple[int, ...] = (1,)

# Durable audit/event ledger double (frozen Ch II.2.6, GAP-05): the memory
# gateway stores audit events in a bounded FIFO (the durable store in SQL is
# append-oriented; the memory reference double stays bounded per the memory
# doctrine — both are append-only and never rewrite history).
AUDIT_LEDGER_CAPACITY: int = 10_000


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
        # II.3 identity/session stores (real port state, not mocks).
        self._users: dict[str, tuple[ForgeUser, int]] = {}
        self._links: dict[tuple[str, str], ExternalIdentityLink] = {}
        self._sessions: dict[str, tuple[ForgeSession, int]] = {}
        self._sessions_by_digest: dict[str, str] = {}
        # Ch II.2.4 vector projection store (closure repair GAP-01). The
        # in-memory implementation is the deterministic reference double:
        # authoritative pgvector proof executes on PostgreSQL (CI).
        self._vectors: dict[str, tuple[VectorProjectionRecord, int]] = {}
        self._vector_versions: dict[str, int] = {}
        self._buffer: list[tuple[str, Any]] = []
        self._in_transaction: bool = False
        self._simulate_unavailable = simulate_unavailable
        self._migrations_applied: tuple[int, ...] = MIGRATION_VERSIONS
        # Durable audit/event ledger double (Ch II.2.6, GAP-05): append-only,
        # monotonic seq, idempotent by event_id, bounded FIFO.
        self._audit_events: list[AuditEventRecord] = []
        self._audit_event_ids: set[str] = set()
        self._audit_seq: int = 0

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
        # Inside a transaction, reference resolution is deferred to the atomic
        # commit check (which validates the whole batch together, matching SQL
        # semantics where earlier inserts in the open transaction are visible).
        if not self._in_transaction:
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
        if self._in_transaction:
            # Buffered like objects: a duplicate within the SAME batch is
            # rejected too (SQL's primary key would reject it), and a failed
            # batch must not leave artifacts behind (rollback parity).
            if any(
                a.artifact_id == record.artifact_id
                for op, a in self._buffer
                if op == "artifact"
            ):
                raise DuplicateArtifact(record.artifact_id)
            self._buffer.append(("artifact", record))
            return WriteResult("CREATE", record.artifact_id, -1)
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
        # Edge endpoints may be buffered batch members (artifacts/objects
        # created earlier in the same open transaction); the write itself is
        # buffered so a failed batch rolls back without leaking edges, and
        # duplicates WITHIN the batch are rejected (SQL PK parity).
        buffered_artifacts = {
            a.artifact_id for op, a in self._buffer if op == "artifact"
        }
        buffered_objects = {
            r.canonical_id for op, r in self._buffer if op == "object"
        }
        if record.artifact_id not in self._artifacts and record.artifact_id not in buffered_artifacts:
            raise DanglingReference("provenance_edge", record.artifact_id)
        if record.object_id not in self._objects and record.object_id not in buffered_objects:
            raise DanglingReference("provenance_edge", record.object_id)
        if self._in_transaction:
            if any(
                e.artifact_id == record.artifact_id
                and e.object_id == record.object_id
                and e.relation == record.relation
                for op, e in self._buffer
                if op == "edge"
            ):
                raise DuplicateProvenanceEdge(*key)
            self._buffer.append(("edge", record))
            return
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

    # -- identity / session (Book II / Bloc II.3) ---------------------------
    def create_user(
        self, user: ForgeUser, expected_version: int | None = None
    ) -> WriteResult:
        if user.user_id in self._users:
            raise DuplicateForgeUser(user.user_id)
        if self._in_transaction:
            self._buffer.append(("user", user))
            return WriteResult("CREATE", user.user_id, -1)
        version = self._check_version(user.user_id, expected_version, self._users) + 1
        self._users[user.user_id] = (user, version)
        return WriteResult("CREATE", user.user_id, version)

    def get_user(self, user_id: str) -> ForgeUser | None:
        entry = self._users.get(user_id)
        return entry[0] if entry else None

    def transition_user_state(
        self, user_id: str, target_state: str, expected_version: int | None = None
    ) -> WriteResult:
        if user_id not in self._users:
            raise UserNotFound(user_id)
        user, version = self._users[user_id]
        if expected_version is not None and expected_version != version:
            raise StaleWriteConflict(user_id, expected_version)
        target = UserState(target_state)
        try:
            validate_user_state_transition(user.state, target)
        except ValueError as exc:
            raise IllegalUserStateTransition(
                user_id, user.state.value, target_state
            ) from exc
        updated = replace(user, state=target)
        self._users[user_id] = (updated, version + 1)
        return WriteResult("TRANSITION", user_id, version + 1)

    def _pending_user_ids(self) -> set[str]:
        """User IDs staged inside the open transaction (commit-deferred)."""

        return {r.user_id for op, r in self._buffer if op == "user"}

    def create_identity_link(self, link: ExternalIdentityLink) -> None:
        key = (link.provider, link.provider_subject)
        pending_links = {
            (r.provider, r.provider_subject)
            for op, r in self._buffer
            if op == "link"
        }
        if key in self._links or key in pending_links:
            raise DuplicateIdentityLink(link.provider, link.provider_subject)
        if (
            link.forge_user_id not in self._users
            and link.forge_user_id not in self._pending_user_ids()
        ):
            raise UserNotFound(link.forge_user_id)
        if self._in_transaction:
            # Commit-deferred so a rollback discards the link atomically.
            self._buffer.append(("link", link))
            return
        self._links[key] = link

    def get_identity_link(
        self, provider: str, provider_subject: str
    ) -> ExternalIdentityLink | None:
        return self._links.get((provider, provider_subject))

    def identity_links_for_user(
        self, user_id: str
    ) -> tuple[ExternalIdentityLink, ...]:
        return tuple(
            self._links[key]
            for key in sorted(self._links)
            if key and self._links[key].forge_user_id == user_id
        )

    def delete_identity_link(self, provider: str, provider_subject: str) -> None:
        key = (provider, provider_subject)
        if key not in self._links:
            raise IdentityLinkNotFound(provider, provider_subject)
        # Deliberately touches ONLY the link: the FORGE user survives unlink.
        del self._links[key]

    def create_session(
        self, session: ForgeSession, expected_version: int | None = None
    ) -> WriteResult:
        if session.session_id in self._sessions:
            raise DuplicateSession(session.session_id)
        if session.token_digest in self._sessions_by_digest:
            raise DuplicateSession("token_digest")
        if (
            session.user_id not in self._users
            and session.user_id not in self._pending_user_ids()
        ):
            raise UserNotFound(session.user_id)
        if self._in_transaction:
            self._buffer.append(("session", session))
            return WriteResult("CREATE", session.session_id, -1)
        version = (
            self._check_version(session.session_id, expected_version, self._sessions) + 1
        )
        self._sessions[session.session_id] = (session, version)
        self._sessions_by_digest[session.token_digest] = session.session_id
        return WriteResult("CREATE", session.session_id, version)

    def get_session(self, session_id: str) -> ForgeSession | None:
        entry = self._sessions.get(session_id)
        return entry[0] if entry else None

    def find_session_by_token_digest(
        self, token_digest: str
    ) -> ForgeSession | None:
        session_id = self._sessions_by_digest.get(token_digest)
        if session_id is None:
            return None
        return self._sessions[session_id][0]

    def revoke_session(
        self, session_id: str, expected_version: int | None = None
    ) -> WriteResult:
        if session_id not in self._sessions:
            raise SessionNotFound(session_id)
        session, version = self._sessions[session_id]
        if expected_version is not None and expected_version != version:
            raise StaleWriteConflict(session_id, expected_version)
        if session.is_revoked:
            return WriteResult("NO_CHANGE", session_id, version)
        updated = replace(session, revoked_at=utc_now_iso())
        self._sessions[session_id] = (updated, version + 1)
        return WriteResult("TRANSITION", session_id, version + 1)

    def revoke_all_sessions(self, user_id: str) -> int:
        if user_id not in self._users:
            raise UserNotFound(user_id)
        count = 0
        for sid, (session, version) in list(self._sessions.items()):
            if session.user_id == user_id and not session.is_revoked:
                self._sessions[sid] = (
                    replace(session, revoked_at=utc_now_iso()),
                    version + 1,
                )
                count += 1
        return count

    # -- transactions ----------------------------------------------------------
    def transaction(self) -> _Transaction:
        return _Transaction(self)

    def _commit_buffer(self) -> None:
        buffered_objects = [r for op, r in self._buffer if op == "object"]
        buffered_artifacts = [r for op, r in self._buffer if op == "artifact"]
        buffered_edges = [r for op, r in self._buffer if op == "edge"]
        buffered_users = [r for op, r in self._buffer if op == "user"]
        buffered_sessions = [r for op, r in self._buffer if op == "session"]
        buffered_links = [r for op, r in self._buffer if op == "link"]
        self._buffer.clear()
        self._in_transaction = False
        # ---- PHASE 1: validate the WHOLE batch as one unit. Nothing is
        # applied yet, so any failure below leaves the store untouched and
        # _Transaction.__exit__ propagates it (atomic rollback parity with
        # SQL, where every statement shares one rolled-back DB transaction).
        #
        # I.3 repair (mutual references): the batch's OWN objects count as
        # resolvable targets — SQL validates inside the open transaction
        # where earlier inserts are visible, and legitimate aggregates
        # reference each other mutually, e.g. CLAIM <-> EVIDENCE. Eager
        # per-insert checks remain active outside transactions and for the
        # no-transaction path below. Unresolved ordinary references are
        # still forbidden after commit.
        batch_ids = {record.canonical_id for record in buffered_objects}
        batch_artifact_ids = {a.artifact_id for a in buffered_artifacts}
        seen_batch: set[str] = set()
        for record in buffered_objects:
            # I.3 repair: duplicates WITHIN the batch are rejected too — a
            # second same-id record must never silently overwrite the first
            # (SQL's primary key would reject it).
            if record.canonical_id in self._objects or record.canonical_id in seen_batch:
                raise DuplicateCanonicalObject(record.canonical_id)
            seen_batch.add(record.canonical_id)
            for ref in record.references:
                if ref.target_id == record.canonical_id:
                    raise SelfReferenceForbidden(record.canonical_id)
                if not ref.allow_unresolved_historical and ref.target_id not in self._objects and ref.target_id not in batch_ids:
                    raise DanglingReference(record.canonical_id, ref.target_id)
        seen_artifacts: set[str] = set()
        for artifact in buffered_artifacts:
            if artifact.artifact_id in self._artifacts or artifact.artifact_id in seen_artifacts:
                raise DuplicateArtifact(artifact.artifact_id)
            seen_artifacts.add(artifact.artifact_id)
        seen_edges: set[tuple[str, str, str]] = set()
        for edge in buffered_edges:
            key = (edge.artifact_id, edge.object_id, edge.relation)
            if key in self._edges or key in seen_edges:
                raise DuplicateProvenanceEdge(*key)
            seen_edges.add(key)
            if edge.artifact_id not in self._artifacts and edge.artifact_id not in batch_artifact_ids:
                raise DanglingReference("provenance_edge", edge.artifact_id)
            if edge.object_id not in self._objects and edge.object_id not in batch_ids:
                raise DanglingReference("provenance_edge", edge.object_id)
        for user in buffered_users:
            if user.user_id in self._users:
                raise DuplicateForgeUser(user.user_id)
        for session in buffered_sessions:
            if session.session_id in self._sessions:
                raise DuplicateSession(session.session_id)
            if session.token_digest in self._sessions_by_digest:
                raise DuplicateSession("token_digest")

        # ---- PHASE 2: apply. Pure dict writes over already-validated data;
        # cannot fail, so no partial state is possible here.
        for artifact in buffered_artifacts:
            self._artifacts[artifact.artifact_id] = (artifact, 1)
        for record in buffered_objects:
            self._objects[record.canonical_id] = (record, 1)
        for edge in buffered_edges:
            self._edges[(edge.artifact_id, edge.object_id, edge.relation)] = edge
        for user in buffered_users:
            self._users[user.user_id] = (user, 1)
        for session in buffered_sessions:
            self._sessions[session.session_id] = (session, 1)
            self._sessions_by_digest[session.token_digest] = session.session_id
        for link in buffered_links:
            self._links[(link.provider, link.provider_subject)] = link

    def _rollback_buffer(self) -> None:
        self._buffer.clear()
        self._in_transaction = False

    # -- vector projection (frozen Ch II.2.4; GAP-01 closure) ---------------
    def _validate_projection_references(self, record: VectorProjectionRecord) -> None:
        """Cross-check a projection against canonical truth and the tenant
        owner; never re-labels version/exposure/hash, never references a
        user row that does not exist (parity with the SQL FKs)."""

        entry = self._objects.get(record.object_id)
        if entry is None:
            raise InvalidRecord(
                f"vector projection references unknown canonical object {record.object_id}"
            )
        if record.owner_user_id is not None and record.owner_user_id not in self._users:
            raise InvalidRecord(
                f"vector projection references unknown user {record.owner_user_id}"
            )
        canonical = entry[0]
        if record.object_version != canonical.version:
            raise InvalidRecord(
                "vector projection object_version does not match canonical version"
            )
        if record.exposure_class != canonical.exposure:
            raise InvalidRecord(
                "vector projection exposure_class does not match canonical exposure"
            )
        if record.canonical_hash != canonical.to_domain().content_hash():
            raise InvalidRecord(
                "vector projection canonical_hash does not match canonical content hash"
            )

    def put_vector_projection(self, record: VectorProjectionRecord) -> None:
        validate_vector_projection(record)
        self._validate_projection_references(record)
        version = self._vector_versions.get(record.object_id, 0) + 1
        stamped = replace(record, generated_at=datetime.now())
        self._vectors[record.object_id] = (stamped, version)
        self._vector_versions[record.object_id] = version

    def get_vector_projection(
        self,
        object_id: str,
        *,
        allowed_exposures: Iterable[Any],
        tenant: str | None = None,
    ) -> VectorProjectionRecord | None:
        exposures = exposure_allowlist(allowed_exposures)
        if not object_id or not exposures:
            return None  # fail closed: no allow-set, no content
        entry = self._vectors.get(object_id)
        if entry is None:
            return None
        record = entry[0]
        if record.exposure_class.value not in exposures:
            return None  # denied is indistinguishable from missing
        if record.owner_user_id is not None and record.owner_user_id != tenant:
            return None
        return record

    def search_vectors(
        self,
        embedding: Iterable[Any],
        *,
        allowed_exposures: Iterable[Any],
        tenant: str | None = None,
        limit: int = 10,
    ) -> tuple[VectorProjectionRecord, ...]:
        query = validate_similarity_query(embedding)
        exposures = exposure_allowlist(allowed_exposures)
        if not exposures or limit <= 0:
            return ()
        results: list[tuple[float, str, VectorProjectionRecord]] = []
        for object_id, (record, _version) in self._vectors.items():
            if record.exposure_class.value not in exposures:
                continue  # never selected, never loaded by the caller
            if record.owner_user_id is not None and record.owner_user_id != tenant:
                continue
            if record.embedding_dim != len(query):
                continue  # similarity is defined within one dimension only
            distance = cosine_distance(query, record.embedding)
            results.append((distance, object_id, record))
        results.sort(key=lambda item: (item[0], item[1]))
        return tuple(record for _distance, _object_id, record in results[: int(limit)])

    def delete_vector_projection(self, object_id: str) -> None:
        self._vectors.pop(object_id, None)
        self._vector_versions.pop(object_id, None)

    def rebuild_vector_projection(
        self, records: Iterable[VectorProjectionRecord]
    ) -> tuple[int, int]:
        batch = tuple(records)
        object_ids = [record.object_id for record in batch]
        if len(set(object_ids)) != len(object_ids):
            raise InvalidRecord("duplicate object_id in rebuild batch")
        # Validate the whole batch before mutating (mirrors SQL transaction).
        for record in batch:
            validate_vector_projection(record)
            self._validate_projection_references(record)
        keep = set(object_ids)
        for record in batch:
            version = self._vector_versions.get(record.object_id, 0) + 1
            self._vectors[record.object_id] = (
                replace(record, generated_at=datetime.now()),
                version,
            )
            self._vector_versions[record.object_id] = version
        stale = [key for key in list(self._vectors) if key not in keep]
        for key in stale:
            del self._vectors[key]
            self._vector_versions.pop(key, None)
        return (len(batch), len(stale))

    # -- infrastructure --------------------------------------------------------
    def ping(self) -> None:
        if self._simulate_unavailable:
            raise PersistenceUnavailable("simulated_backend_down")

    # -- durable audit/event ledger (frozen Ch II.2.6; GAP-05) -----------------

    def append_audit_event(self, record: Any) -> bool:
        if self._simulate_unavailable:
            raise PersistenceUnavailable("simulated_backend_down")
        # Coerce at the boundary: observability may not import persistence
        # types (frozen K5/K7 law), so envelopes arrive duck-shaped.
        record = coerce_audit_event(record)
        if record.event_id in self._audit_event_ids:
            return False  # idempotent by event_id
        self._audit_seq += 1
        stored = replace(record, seq=self._audit_seq)
        self._audit_events.append(stored)
        self._audit_event_ids.add(record.event_id)
        if len(self._audit_events) > AUDIT_LEDGER_CAPACITY:
            evicted = self._audit_events.pop(0)
            self._audit_event_ids.discard(evicted.event_id)
        return True

    def list_audit_events(
        self, *, limit: int = 100, stream: str | None = None
    ) -> tuple[AuditEventRecord, ...]:
        if self._simulate_unavailable:
            raise PersistenceUnavailable("simulated_backend_down")
        bound = max(1, min(int(limit), AUDIT_LEDGER_CAPACITY))
        selected = [
            record
            for record in self._audit_events
            if stream is None or record.stream == stream
        ]
        return tuple(selected[:bound])

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
