"""SQLAlchemy Core persistence gateway — the PostgreSQL implementation.

Uses SQLAlchemy 2.0 Core with explicit parameterized SQL (no ORM sessions,
no identity map, no string-concatenated SQL — security clause P1/P2).
Locally, the portable migration contract can be exercised on SQLite for
schema/dialect truth; PostgreSQL remains the production target.
"""

from __future__ import annotations

import json
from typing import Any, Iterator

from sqlalchemy import text
from sqlalchemy.engine import Connection


def _sql(statement: str):
    """Wrap a literal SQL string for SQLAlchemy execution."""

    return text(statement)

from app.forge.canonical import ObjectType, validate_status_transition
from dataclasses import replace
from app.forge.identity import (
    ExternalIdentityLink,
    ForgeSession,
    ForgeUser,
    IdentityRole,
    UserState,
    validate_user_state_transition,
)
from app.forge.persistence.port import (
    DanglingReference,
    DuplicateArtifact,
    DuplicateCanonicalObject,
    DuplicateForgeUser,
    DuplicateIdentityLink,
    DuplicateProvenanceEdge,
    DuplicateSession,
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
from app.forge.persistence.sql.migrations import SqlMigrationRunner
from app.forge.persistence.records import CanonicalReference


def _op_error(exc: Exception) -> PersistenceUnavailable:
    """Normalize driver errors; never carry URLs/credentials in the detail."""

    return PersistenceUnavailable(type(exc).__name__)


class SqlAlchemyPersistenceGateway:
    """Gateway over one SQLAlchemy Connection/Engine (explicitly injected)."""

    def __init__(self, connection: Any, *, migrations_required: bool = True) -> None:
        self._connection = connection
        self._runner = SqlMigrationRunner(connection)
        self._migrations_required = migrations_required
        self._in_transaction = False

    # -- infrastructure -------------------------------------------------------
    def ping(self) -> None:
        try:
            self._connection.execute(text("SELECT 1"))
        except Exception as exc:
            raise _op_error(exc) from None

    def apply_migrations(self) -> str:
        try:
            return self._runner.apply_migrations()
        except Exception as exc:
            raise _op_error(exc) from None

    def check_compatibility(self) -> str:
        try:
            return self._runner.check_compatibility()
        except Exception as exc:
            raise _op_error(exc) from None

    # -- canonical objects ------------------------------------------------------
    def create_object(
        self, record: CanonicalObjectRecord, expected_version: int | None = None
    ) -> WriteResult:
        self._validate_references(record)
        exists = self._exists("canonical_objects", record.canonical_id)
        if exists and expected_version is not None:
            current = self._object_version(record.canonical_id)
            if expected_version != current:
                raise StaleWriteConflict(record.canonical_id, expected_version)
        if exists:
            raise DuplicateCanonicalObject(record.canonical_id)
        payload = record.to_domain().deterministic_payload()
        content_hash = record.to_domain().content_hash()
        self._connection.execute(
            text(
                "INSERT INTO canonical_objects (canonical_id, object_type, title, version,"
                " status, exposure, layer, metadata_json, claim_identity_json,"
                " deterministic_payload, content_hash, persisted_version)"
                " VALUES (:cid, :otype, :title, :cversion, :status, :exposure, :layer,"
                " :meta, :claim_identity, :payload, :chash, 1)"
            ),
            {
                "cid": record.canonical_id,
                "otype": record.object_type.value,
                "title": record.title,
                "cversion": record.version,
                "status": record.status.value,
                "exposure": record.exposure.value,
                "layer": record.layer.value,
                "meta": json.dumps(record.metadata, sort_keys=True),
                "claim_identity": (
                    json.dumps(
                        record.claim_identity.comparison_key_dict()
                        if hasattr(record.claim_identity, "comparison_key_dict")
                        else {},
                        sort_keys=True,
                    )
                    if record.claim_identity
                    else None
                ),
                "payload": payload,
                "chash": content_hash,
            },
        )
        for ref in record.references:
            self._insert_reference(record.canonical_id, ref)
        return WriteResult("CREATE", record.canonical_id, 1)

    def _insert_reference(self, canonical_id: str, ref: CanonicalReference) -> None:
        self._connection.execute(
            text(
                "INSERT INTO canonical_references (canonical_id, target_id, relation,"
                " allow_unresolved_historical)"
                " VALUES (:cid, :tid, :rel, :allow)"
            ),
            {
                "cid": canonical_id,
                "tid": ref.target_id,
                "rel": ref.relation,
                "allow": bool(ref.allow_unresolved_historical),
            },
        )

    def get_object(self, canonical_id: str) -> CanonicalObjectRecord | None:
        row = (
            self._connection.execute(
                text("SELECT * FROM canonical_objects WHERE canonical_id = :cid"),
                {"cid": canonical_id},
            )
            .mappings()
            .first()
        )
        if row is None:
            return None
        refs = self._connection.execute(
            text(
                "SELECT target_id, relation, allow_unresolved_historical"
                " FROM canonical_references WHERE canonical_id = :cid ORDER BY target_id, relation"
            ),
            {"cid": canonical_id},
        ).fetchall()
        import json as _json

        metadata = _json.loads(row["metadata_json"])
        claim_identity = None
        if row["object_type"] == "CLAIM" and row["claim_identity_json"]:
            from app.forge.canonical import ClaimIdentity

            dims = _json.loads(row["claim_identity_json"])
            claim_identity = ClaimIdentity(
                market=dims["market"],
                event_definition=dims["event_definition"],
                conditioning_event=dims["conditioning_event"],
                clock_origin=dims["clock_origin"],
                horizon=dims["horizon"],
                tolerance=dims["tolerance"],
                eligibility=dims["eligibility"],
                implementation_semantics=dims["implementation_semantics"],
            )
        return CanonicalObjectRecord(
            canonical_id=row["canonical_id"],
            object_type=ObjectType(row["object_type"]),
            title=row["title"],
            version=row["version"],
            status=record_status(row["status"]),
            exposure=record_exposure(row["exposure"]),
            layer=record_layer(row["layer"]),
            references=tuple(
                CanonicalReference(
                    target_id=r[0],
                    relation=r[1],
                    allow_unresolved_historical=bool(r[2]),
                )
                for r in refs
            ),
            metadata=metadata,
            claim_identity=claim_identity,
        )

    def list_object_ids(self) -> tuple[str, ...]:
        rows = self._connection.execute(
            text("SELECT canonical_id FROM canonical_objects ORDER BY canonical_id")
        ).fetchall()
        return tuple(r[0] for r in rows)

    def transition_status(
        self, canonical_id: str, target_status: str, expected_version: int | None = None
    ) -> WriteResult:
        record = self.get_object(canonical_id)
        if record is None:
            raise ObjectNotFound(canonical_id)
        from app.forge.canonical import EvidenceStatus

        target = EvidenceStatus(target_status)
        try:
            validate_status_transition(record.status, target)
        except ValueError as exc:
            raise IllegalStatusTransition(
                canonical_id, record.status.value, target_status
            ) from exc
        if expected_version is not None:
            current = self._object_version(canonical_id)
            if expected_version != current:
                raise StaleWriteConflict(canonical_id, expected_version)
        new_version = self._object_version(canonical_id) + 1
        self._connection.execute(
            text(
                "UPDATE canonical_objects SET status = :status, persisted_version = :pv,"
                " updated_at = CURRENT_TIMESTAMP WHERE canonical_id = :cid"
            ),
            {"status": target.value, "pv": new_version, "cid": canonical_id},
        )
        return WriteResult("TRANSITION", canonical_id, new_version)

    def _object_version(self, canonical_id: str) -> int:
        row = self._connection.execute(
            text("SELECT persisted_version FROM canonical_objects WHERE canonical_id = :cid"),
            {"cid": canonical_id},
        ).first()
        if row is None:
            raise ObjectNotFound(canonical_id)
        return int(row[0])

    def _validate_references(self, record: CanonicalObjectRecord) -> None:
        if record.claim_identity is not None and record.object_type is not ObjectType.CLAIM:
            raise ValueError("claim_identity is only valid on CLAIM objects")
        for ref in record.references:
            if ref.target_id == record.canonical_id:
                raise SelfReferenceForbidden(record.canonical_id)
            if not ref.allow_unresolved_historical and not self._exists(
                "canonical_objects", ref.target_id
            ):
                raise DanglingReference(record.canonical_id, ref.target_id)

    def _exists(self, table: str, key: str) -> bool:
        # table comes from module constants only, never user input (P2)
        row = self._connection.execute(
            text(f"SELECT 1 FROM {table} WHERE canonical_id = :cid"), {"cid": key}
        ).first()
        return row is not None

    # -- artifacts ----------------------------------------------------------------
    def create_artifact(
        self, record: ArtifactRecord, expected_version: int | None = None
    ) -> WriteResult:
        exists = self._artifact_exists(record.artifact_id)
        if exists and expected_version is not None:
            current = self._artifact_version(record.artifact_id)
            if expected_version != current:
                raise StaleWriteConflict(record.artifact_id, expected_version)
        if exists:
            raise DuplicateArtifact(record.artifact_id)
        self._connection.execute(
            text(
                "INSERT INTO artifacts (artifact_id, source_class, title, source_generation,"
                " version, locator, content_identity, source_state, created_at, observed_at,"
                " metadata_json, persisted_version)"
                " VALUES (:aid, :sclass, :title, :sgen, :aversion, :locator, :cident,"
                " :sstate, :cat, :oat, :meta, 1)"
            ),
            {
                "aid": record.artifact_id,
                "sclass": record.source_class,
                "title": record.title,
                "sgen": record.source_generation,
                "aversion": record.version,
                "locator": record.locator,
                "cident": record.content_identity,
                "sstate": record.source_state,
                "cat": record.created_at,
                "oat": record.observed_at,
                "meta": json.dumps(record.metadata, sort_keys=True),
            },
        )
        return WriteResult("CREATE", record.artifact_id, 1)

    def _artifact_exists(self, artifact_id: str) -> bool:
        row = self._connection.execute(
            text("SELECT 1 FROM artifacts WHERE artifact_id = :aid"), {"aid": artifact_id}
        ).first()
        return row is not None

    def _artifact_version(self, artifact_id: str) -> int:
        row = self._connection.execute(
            text("SELECT persisted_version FROM artifacts WHERE artifact_id = :aid"),
            {"aid": artifact_id},
        ).first()
        if row is None:
            raise ObjectNotFound(artifact_id)
        return int(row[0])

    def get_artifact(self, artifact_id: str) -> ArtifactRecord | None:
        row = (
            self._connection.execute(
                text("SELECT * FROM artifacts WHERE artifact_id = :aid"),
                {"aid": artifact_id},
            )
            .mappings()
            .first()
        )
        if row is None:
            return None
        return ArtifactRecord(
            artifact_id=row["artifact_id"],
            source_class=row["source_class"],
            title=row["title"],
            source_generation=row["source_generation"],
            version=row["version"],
            locator=row["locator"],
            content_identity=row["content_identity"],
            source_state=row["source_state"],
            created_at=row["created_at"],
            observed_at=row["observed_at"],
            metadata=json.loads(row["metadata_json"]),
        )

    def transition_artifact_state(
        self, artifact_id: str, target_state: str, expected_version: int | None = None
    ) -> WriteResult:
        """Governed artifact source-state transition (I.2 machine) with
        optimistic version check."""

        from app.forge.provenance import SourceState, validate_source_state_transition

        record = self.get_artifact(artifact_id)
        if record is None:
            raise ObjectNotFound(artifact_id)
        if expected_version is not None:
            current = self._artifact_version(artifact_id)
            if expected_version != current:
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
        new_version = self._artifact_version(artifact_id) + 1
        self._connection.execute(
            text(
                "UPDATE artifacts SET source_state = :state, persisted_version = :pv"
                " WHERE artifact_id = :aid"
            ),
            {"state": target.value, "pv": new_version, "aid": artifact_id},
        )
        return WriteResult("TRANSITION", artifact_id, new_version)

    # -- provenance -----------------------------------------------------------------
    def add_provenance_edge(self, record: ProvenanceEdgeRecord) -> None:
        if not self._artifact_exists(record.artifact_id):
            raise DanglingReference("provenance_edge", record.artifact_id)
        if not self._exists("canonical_objects", record.object_id):
            raise DanglingReference("provenance_edge", record.object_id)
        try:
            self._connection.execute(
                text(
                    "INSERT INTO provenance_edges (artifact_id, object_id, relation, note)"
                    " VALUES (:aid, :oid, :rel, :note)"
                ),
                {
                    "aid": record.artifact_id,
                    "oid": record.object_id,
                    "rel": record.relation,
                    "note": record.note,
                },
            )
        except Exception as exc:
            # A failed statement poisons the DB transaction; roll it back so
            # the connection remains usable (PostgreSQL semantics), then map
            # the error to the port's deterministic identity.
            self._safe_rollback()
            if _is_unique_violation(exc):
                raise DuplicateProvenanceEdge(
                    record.artifact_id, record.object_id, record.relation
                ) from None
            raise

    def _safe_rollback(self) -> None:
        try:
            self._connection.rollback()
        except Exception:  # pragma: no cover - rollback is best-effort
            pass

    def _edge_key_set(self, object_id: str) -> set[tuple[str, str, str]]:
        rows = self._connection.execute(
            text(
                "SELECT artifact_id, object_id, relation FROM provenance_edges"
                " WHERE object_id = :oid"
            ),
            {"oid": object_id},
        ).fetchall()
        return {(r[0], r[1], r[2]) for r in rows}

    def edges_for_object(self, object_id: str) -> tuple[ProvenanceEdgeRecord, ...]:
        rows = self._connection.execute(
            text(
                "SELECT artifact_id, object_id, relation, note FROM provenance_edges"
                " WHERE object_id = :oid ORDER BY artifact_id, relation"
            ),
            {"oid": object_id},
        ).fetchall()
        return tuple(
            ProvenanceEdgeRecord(artifact_id=r[0], object_id=r[1], relation=r[2], note=r[3])
            for r in rows
        )

    def edges_from_artifact(self, artifact_id: str) -> tuple[ProvenanceEdgeRecord, ...]:
        rows = self._connection.execute(
            text(
                "SELECT artifact_id, object_id, relation, note FROM provenance_edges"
                " WHERE artifact_id = :aid ORDER BY object_id, relation"
            ),
            {"aid": artifact_id},
        ).fetchall()
        return tuple(
            ProvenanceEdgeRecord(artifact_id=r[0], object_id=r[1], relation=r[2], note=r[3])
            for r in rows
        )

    # -- transactions ------------------------------------------------------------------
    def transaction(self) -> Any:
        return _SqlConnectionTransaction(self._connection)

    # -- identity / session (Book II / Bloc II.3) ---------------------------------
    def create_user(
        self, user: ForgeUser, expected_version: int | None = None
    ) -> WriteResult:
        if self._user_exists(user.user_id):
            if expected_version is not None:
                current = self._user_version(user.user_id)
                if expected_version != current:
                    raise StaleWriteConflict(user.user_id, expected_version)
            raise DuplicateForgeUser(user.user_id)
        try:
            self._connection.execute(
                text(
                    "INSERT INTO forge_users (user_id, state, roles_json, email,"
                    " display_label, persisted_version)"
                    " VALUES (:uid, :state, :roles, :email, :label, 1)"
                ),
                {
                    "uid": user.user_id,
                    "state": user.state.value,
                    "roles": self._roles_to_json(user.roles),
                    "email": user.email,
                    "label": user.display_label,
                },
            )
        except Exception as exc:
            self._safe_rollback()
            raise self._identity_write_error("forge_user", exc) from None
        return WriteResult("CREATE", user.user_id, 1)

    def get_user(self, user_id: str) -> ForgeUser | None:
        row = self._connection.execute(
            text(
                "SELECT user_id, state, roles_json, email, display_label"
                " FROM forge_users WHERE user_id = :uid"
            ),
            {"uid": user_id},
        ).first()
        if row is None:
            return None
        return ForgeUser(
            user_id=row[0],
            state=UserState(row[1]),
            roles=self._roles_from_json(row[2]),
            email=row[3],
            display_label=row[4],
        )

    def transition_user_state(
        self, user_id: str, target_state: str, expected_version: int | None = None
    ) -> WriteResult:
        user = self.get_user(user_id)
        if user is None:
            raise UserNotFound(user_id)
        if expected_version is not None:
            current = self._user_version(user_id)
            if expected_version != current:
                raise StaleWriteConflict(user_id, expected_version)
        target = UserState(target_state)
        try:
            validate_user_state_transition(user.state, target)
        except ValueError as exc:
            raise IllegalUserStateTransition(
                user_id, user.state.value, target_state
            ) from exc
        new_version = self._user_version(user_id) + 1
        self._connection.execute(
            text(
                "UPDATE forge_users SET state = :state, persisted_version = :pv"
                " WHERE user_id = :uid"
            ),
            {"state": target.value, "pv": new_version, "uid": user_id},
        )
        return WriteResult("TRANSITION", user_id, new_version)

    def create_identity_link(self, link: ExternalIdentityLink) -> None:
        if not self._user_exists(link.forge_user_id):
            raise UserNotFound(link.forge_user_id)
        # Pre-check uniqueness BEFORE the INSERT: a failed INSERT would poison
        # the shared connection's open transaction (rollback would discard
        # uncommitted prior writes). The except-branch remains as the
        # concurrent-writer backstop.
        existing = self.get_identity_link(link.provider, link.provider_subject)
        if existing is not None:
            raise DuplicateIdentityLink(link.provider, link.provider_subject)
        try:
            self._connection.execute(
                text(
                    "INSERT INTO external_identity_links (provider,"
                    " provider_subject, forge_user_id)"
                    " VALUES (:provider, :subject, :uid)"
                ),
                {
                    "provider": link.provider,
                    "subject": link.provider_subject,
                    "uid": link.forge_user_id,
                },
            )
        except Exception as exc:
            self._safe_rollback()
            if _is_unique_violation(exc):
                raise DuplicateIdentityLink(
                    link.provider, link.provider_subject
                ) from None
            raise self._identity_write_error("identity_link", exc) from None

    def get_identity_link(
        self, provider: str, provider_subject: str
    ) -> ExternalIdentityLink | None:
        row = self._connection.execute(
            text(
                "SELECT provider, provider_subject, forge_user_id"
                " FROM external_identity_links"
                " WHERE provider = :provider AND provider_subject = :subject"
            ),
            {"provider": provider, "subject": provider_subject},
        ).first()
        if row is None:
            return None
        return ExternalIdentityLink(
            provider=row[0], provider_subject=row[1], forge_user_id=row[2]
        )

    def identity_links_for_user(
        self, user_id: str
    ) -> tuple[ExternalIdentityLink, ...]:
        rows = self._connection.execute(
            text(
                "SELECT provider, provider_subject, forge_user_id"
                " FROM external_identity_links WHERE forge_user_id = :uid"
                " ORDER BY provider, provider_subject"
            ),
            {"uid": user_id},
        ).fetchall()
        return tuple(
            ExternalIdentityLink(
                provider=r[0], provider_subject=r[1], forge_user_id=r[2]
            )
            for r in rows
        )

    def delete_identity_link(self, provider: str, provider_subject: str) -> None:
        result = self._connection.execute(
            text(
                "DELETE FROM external_identity_links"
                " WHERE provider = :provider AND provider_subject = :subject"
            ),
            {"provider": provider, "subject": provider_subject},
        )
        if getattr(result, "rowcount", 0) == 0:
            raise IdentityLinkNotFound(provider, provider_subject)
        # Deliberately touches ONLY the link row: the FORGE user survives.

    def create_session(
        self, session: ForgeSession, expected_version: int | None = None
    ) -> WriteResult:
        if self._session_exists(session.session_id):
            if expected_version is not None:
                current = self._session_version(session.session_id)
                if expected_version != current:
                    raise StaleWriteConflict(session.session_id, expected_version)
            raise DuplicateSession(session.session_id)
        if not self._user_exists(session.user_id):
            raise UserNotFound(session.user_id)
        # Pre-check digest uniqueness BEFORE the INSERT (see create_identity_link:
        # a failed INSERT poisons the connection's open transaction).
        if self.find_session_by_token_digest(session.token_digest) is not None:
            raise DuplicateSession("token_digest")
        try:
            self._connection.execute(
                text(
                    "INSERT INTO forge_sessions (session_id, user_id,"
                    " token_digest, expires_at, persisted_version)"
                    " VALUES (:sid, :uid, :digest, :expires, 1)"
                ),
                {
                    "sid": session.session_id,
                    "uid": session.user_id,
                    "digest": session.token_digest,
                    "expires": session.expires_at,
                },
            )
        except Exception as exc:
            self._safe_rollback()
            if _is_unique_violation(exc):
                raise DuplicateSession("token_digest") from None
            raise self._identity_write_error("forge_session", exc) from None
        return WriteResult("CREATE", session.session_id, 1)

    def get_session(self, session_id: str) -> ForgeSession | None:
        row = self._connection.execute(
            text(
                "SELECT session_id, user_id, token_digest, created_at,"
                " expires_at, revoked_at FROM forge_sessions"
                " WHERE session_id = :sid"
            ),
            {"sid": session_id},
        ).first()
        if row is None:
            return None
        return self._session_from_row(row)

    def find_session_by_token_digest(
        self, token_digest: str
    ) -> ForgeSession | None:
        row = self._connection.execute(
            text(
                "SELECT session_id, user_id, token_digest, created_at,"
                " expires_at, revoked_at FROM forge_sessions"
                " WHERE token_digest = :digest"
            ),
            {"digest": token_digest},
        ).first()
        if row is None:
            return None
        return self._session_from_row(row)

    def revoke_session(
        self, session_id: str, expected_version: int | None = None
    ) -> WriteResult:
        row = self._connection.execute(
            text(
                "SELECT session_id, user_id, token_digest, created_at,"
                " expires_at, revoked_at, persisted_version FROM forge_sessions"
                " WHERE session_id = :sid"
            ),
            {"sid": session_id},
        ).first()
        if row is None:
            raise SessionNotFound(session_id)
        if expected_version is not None and expected_version != int(row[6]):
            raise StaleWriteConflict(session_id, expected_version)
        if row[5] is not None:
            return WriteResult("NO_CHANGE", session_id, int(row[6]))
        new_version = int(row[6]) + 1
        self._connection.execute(
            text(
                "UPDATE forge_sessions SET revoked_at = CURRENT_TIMESTAMP,"
                " persisted_version = :pv WHERE session_id = :sid"
            ),
            {"pv": new_version, "sid": session_id},
        )
        return WriteResult("TRANSITION", session_id, new_version)

    def revoke_all_sessions(self, user_id: str) -> int:
        if not self._user_exists(user_id):
            raise UserNotFound(user_id)
        result = self._connection.execute(
            text(
                "UPDATE forge_sessions SET revoked_at = CURRENT_TIMESTAMP,"
                " persisted_version = persisted_version + 1"
                " WHERE user_id = :uid AND revoked_at IS NULL"
            ),
            {"uid": user_id},
        )
        return int(getattr(result, "rowcount", 0) or 0)

    # -- identity helpers -----------------------------------------------------
    def _session_from_row(self, row: Any) -> ForgeSession:
        created = row[3]
        expires = row[4]
        revoked = row[5]
        return ForgeSession(
            session_id=row[0],
            user_id=row[1],
            token_digest=row[2],
            created_at=created.isoformat() if hasattr(created, "isoformat") else (str(created) if created else None),
            expires_at=(expires.isoformat() if hasattr(expires, "isoformat") else str(expires)) if expires else "",
            revoked_at=(revoked.isoformat() if hasattr(revoked, "isoformat") else str(revoked)) if revoked is not None else None,
        )

    @staticmethod
    def _roles_to_json(roles: frozenset[IdentityRole]) -> str:
        import json

        return json.dumps(sorted(role.value for role in roles))

    @staticmethod
    def _roles_from_json(raw: str) -> frozenset[IdentityRole]:
        import json

        try:
            values = json.loads(raw or "[]")
        except ValueError:
            values = []
        return frozenset(IdentityRole(v) for v in values if v)

    def _identity_write_error(self, what: str, exc: Exception) -> PersistenceUnavailable:
        # Normalized; never carries SQL text, URLs or credentials.
        return PersistenceUnavailable(f"{type(exc).__name__}")

    def _user_exists(self, user_id: str) -> bool:
        return (
            self._connection.execute(
                text("SELECT 1 FROM forge_users WHERE user_id = :uid"),
                {"uid": user_id},
            ).first()
            is not None
        )

    def _session_exists(self, session_id: str) -> bool:
        return (
            self._connection.execute(
                text("SELECT 1 FROM forge_sessions WHERE session_id = :sid"),
                {"sid": session_id},
            ).first()
            is not None
        )

    def _user_version(self, user_id: str) -> int:
        row = self._connection.execute(
            text(
                "SELECT persisted_version FROM forge_users WHERE user_id = :uid"
            ),
            {"uid": user_id},
        ).first()
        return int(row[0]) if row else 0

    def _session_version(self, session_id: str) -> int:
        row = self._connection.execute(
            text(
                "SELECT persisted_version FROM forge_sessions"
                " WHERE session_id = :sid"
            ),
            {"sid": session_id},
        ).first()
        return int(row[0]) if row else 0

    # -- compatibility: not part of the port contract below ----------------------------
    def _unused(self) -> None:  # pragma: no cover - keeps import list honest
        return None


def _is_unique_violation(exc: Exception) -> bool:
    # SQLite: IntegrityError with UNIQUE constraint; PostgreSQL: unique_violation.
    name = type(exc).__name__.lower()
    text_exc = str(exc).lower()
    return "integrityerror" in name or "unique" in text_exc or "23505" in text_exc


def _is_fk_violation(exc: Exception) -> bool:
    # PostgreSQL fk_violation (23503); SQLite foreign-key IntegrityError.
    name = type(exc).__name__.lower()
    text_exc = str(exc).lower()
    return (
        "23503" in text_exc
        or "foreign key" in text_exc
        or ("integrityerror" in name and "foreign" in text_exc)
    )


def record_status(value: str):
    from app.forge.canonical import EvidenceStatus

    return EvidenceStatus(value)


def record_exposure(value: str):
    from app.forge.canonical import ProductExposure

    return ProductExposure(value)


def record_layer(value: str):
    from app.forge.canonical import Layer

    return Layer(value)


class _SqlConnectionTransaction:
    """Explicit transaction wrapper over a SQLAlchemy connection."""

    def __init__(self, connection: Connection) -> None:
        self._connection = connection

    def __enter__(self) -> "_SqlConnectionTransaction":
        self._connection.execute(text("BEGIN"))
        return self

    def __exit__(self, exc_type: Any, exc: Any, tb: Any) -> None:
        if exc_type is None:
            self._connection.execute(text("COMMIT"))
        else:
            self._connection.execute(text("ROLLBACK"))
