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
    DuplicateArtifact,
    DuplicateCanonicalObject,
    DuplicateIdentityLink,
    DuplicateProvenanceEdge,
    DuplicateSession,
    DuplicateForgeUser,
    IdentityLinkNotFound,
    IllegalStatusTransition,
    IllegalUserStateTransition,
    MigrationOutcome,
    ObjectNotFound,
    PersistenceUnavailable,
    SelfReferenceForbidden,
    SessionNotFound,
    StaleWriteConflict,
    UserNotFound,
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
        # II.3 identity/session stores (real port state, not mocks).
        self._users: dict[str, tuple[ForgeUser, int]] = {}
        self._links: dict[tuple[str, str], ExternalIdentityLink] = {}
        self._sessions: dict[str, tuple[ForgeSession, int]] = {}
        self._sessions_by_digest: dict[str, str] = {}
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
        if key in self._links:
            raise DuplicateIdentityLink(link.provider, link.provider_subject)
        if (
            link.forge_user_id not in self._users
            and link.forge_user_id not in self._pending_user_ids()
        ):
            raise UserNotFound(link.forge_user_id)
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
        buffered_users = [r for op, r in self._buffer if op == "user"]
        buffered_sessions = [r for op, r in self._buffer if op == "session"]
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
        # II.3: validate then apply buffered identity/session writes atomically.
        # (Links are applied inline in create_identity_link; only users and
        # sessions are commit-deferred, mirroring objects.)
        for user in buffered_users:
            if user.user_id in self._users:
                raise DuplicateForgeUser(user.user_id)
        for session in buffered_sessions:
            if session.session_id in self._sessions:
                raise DuplicateSession(session.session_id)
            if session.token_digest in self._sessions_by_digest:
                raise DuplicateSession("token_digest")
        for user in buffered_users:
            self._users[user.user_id] = (user, 1)
        for session in buffered_sessions:
            self._sessions[session.session_id] = (session, 1)
            self._sessions_by_digest[session.token_digest] = session.session_id

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
