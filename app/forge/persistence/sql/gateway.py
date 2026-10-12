"""SQLAlchemy Core persistence gateway — the PostgreSQL implementation.

Uses SQLAlchemy 2.0 Core with explicit parameterized SQL (no ORM sessions,
no identity map, no string-concatenated SQL — security clause P1/P2).
Locally, the portable migration contract can be exercised on SQLite for
schema/dialect truth; PostgreSQL remains the production target.
"""

from __future__ import annotations

import json
from typing import Any, Iterable, Iterator

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
    InvalidRecord,
    MigrationOutcome,
    ObjectNotFound,
    PersistenceError,
    PersistenceUnavailable,
    SelfReferenceForbidden,
    SessionNotFound,
    StaleWriteConflict,
    UserNotFound,
    coerce_audit_event,
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
        # I.3: records created inside an open transaction whose ordinary
        # reference targets may still be pending in the SAME batch. Their
        # dangling check is deferred to commit and validated as one unit
        # (parity with the in-memory gateway; mutual CLAIM <-> EVIDENCE
        # references inside a batch are legal, unresolved ordinary
        # references after commit are not).
        self._pending_records: list[CanonicalObjectRecord] = []

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
        if self._in_transaction:
            # Defer only the ordinary dangling check to commit: the batch's
            # remaining records may not be inserted yet (mutual references).
            # Self-reference and claim_identity rules stay eager.
            self._validate_references(record, check_dangling=False)
        else:
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
                        {
                            "market": record.claim_identity.market,
                            "event_definition": record.claim_identity.event_definition,
                            "conditioning_event": record.claim_identity.conditioning_event,
                            "clock_origin": record.claim_identity.clock_origin,
                            "horizon": record.claim_identity.horizon,
                            "tolerance": record.claim_identity.tolerance,
                            "eligibility": record.claim_identity.eligibility,
                            "implementation_semantics": (
                                record.claim_identity.implementation_semantics
                            ),
                        },
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
        if self._in_transaction:
            self._pending_records.append(record)
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
            # Empty dict = identity never persisted (legacy rows written by an
            # older serializer): surface as ABSENT identity, never fabricate
            # dimension values and never crash the read path.
            if dims:
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

    def _validate_references(
        self, record: CanonicalObjectRecord, *, check_dangling: bool = True
    ) -> None:
        if record.claim_identity is not None and record.object_type is not ObjectType.CLAIM:
            raise ValueError("claim_identity is only valid on CLAIM objects")
        for ref in record.references:
            if ref.target_id == record.canonical_id:
                raise SelfReferenceForbidden(record.canonical_id)
            if (
                check_dangling
                and not ref.allow_unresolved_historical
                and not self._exists("canonical_objects", ref.target_id)
            ):
                raise DanglingReference(record.canonical_id, ref.target_id)

    def _validate_pending_references(self) -> None:
        """I.3 unit validation at commit: every ordinary reference of every
        record created in this transaction must resolve against the open
        transaction's visible state (earlier inserts in the same batch are
        visible, so mutual references resolve). Runs BEFORE COMMIT; a failure
        rolls the whole batch back."""
        for record in self._pending_records:
            for ref in record.references:
                if ref.allow_unresolved_historical or ref.target_id == record.canonical_id:
                    continue
                if not self._exists("canonical_objects", ref.target_id):
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
        return _SqlGatewayTransaction(self)

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

    # -- vector projection (frozen Ch II.2.4; GAP-01 closure) ---------------
    # Storage substrate only: Book II stores/validates/projects; embedding
    # generation and model selection are Book VII; canonical truth is Book
    # I. Acceptance proof executes on PostgreSQL+pgvector (CI); the gateway
    # fails closed where pgvector storage cannot exist — SQLite is never
    # substituted as vector proof.

    _VECTOR_SELECT = (
        "object_id, object_version, payload_json, semantic_text,"
        " embedding::text AS embedding, embedding_dim, embedding_model,"
        " embedding_version, exposure_class, canonical_hash, owner_user_id,"
        " generated_at, persisted_version"
    )

    def _require_postgresql_vector(self) -> None:
        dialect = getattr(getattr(self._connection, "dialect", None), "name", "") or ""
        if dialect and dialect != "postgresql":
            raise PersistenceUnavailable("vector_storage_requires_postgresql")

    def _canonical_projection_reference(self, record: VectorProjectionRecord) -> None:
        """Cross-check against canonical truth; a projection can never re-label
        version, exposure or identity."""

        row = self._connection.execute(
            _sql(
                "SELECT version, exposure, content_hash FROM canonical_objects"
                " WHERE canonical_id = :cid"
            ),
            {"cid": record.object_id},
        ).first()
        if row is None:
            raise InvalidRecord(
                f"vector projection references unknown canonical object {record.object_id}"
            )
        if record.object_version != row[0]:
            raise InvalidRecord(
                "vector projection object_version does not match canonical version"
            )
        if record.exposure_class.value != row[1]:
            raise InvalidRecord(
                "vector projection exposure_class does not match canonical exposure"
            )
        if record.canonical_hash != str(row[2]).strip():
            raise InvalidRecord(
                "vector projection canonical_hash does not match canonical content hash"
            )

    @staticmethod
    def _vector_row(row: Any) -> VectorProjectionRecord:
        # `row` is a SQLAlchemy RowMapping (execute(...).mappings()): string
        # keys are the stable interface — plain Row objects reject str keys.
        raw = str(row["embedding"]).strip()
        if raw.startswith("[") and raw.endswith("]"):
            raw = raw[1:-1]
        embedding = tuple(float(part) for part in raw.split(",")) if raw else ()
        return VectorProjectionRecord(
            object_id=row["object_id"],
            object_version=row["object_version"],
            payload_json=row["payload_json"],
            semantic_text=row["semantic_text"],
            embedding=embedding,
            embedding_dim=int(row["embedding_dim"]),
            embedding_model=row["embedding_model"],
            embedding_version=row["embedding_version"],
            exposure_class=record_exposure(row["exposure_class"]),
            canonical_hash=str(row["canonical_hash"]).strip(),
            owner_user_id=row["owner_user_id"],
            generated_at=row["generated_at"],
        )

    @staticmethod
    def _embedding_literal(embedding: Iterable[float]) -> str:
        return "[" + ",".join(repr(float(value)) for value in embedding) + "]"

    def put_vector_projection(self, record: VectorProjectionRecord) -> None:
        self._require_postgresql_vector()
        validate_vector_projection(record)
        self._canonical_projection_reference(record)
        try:
            self._connection.execute(
                _sql(
                    "INSERT INTO retrieval_vectors (object_id, object_version,"
                    " payload_json, semantic_text, embedding, embedding_dim,"
                    " embedding_model, embedding_version, exposure_class,"
                    " canonical_hash, owner_user_id, generated_at)"
                    " VALUES (:oid, :over, :payload, :semtext, CAST(:emb AS vector),"
                    " :edim, :emodel, :ever, :exp, :chash, :owner, CURRENT_TIMESTAMP)"
                    " ON CONFLICT (object_id) DO UPDATE SET"
                    " object_version = EXCLUDED.object_version,"
                    " payload_json = EXCLUDED.payload_json,"
                    " semantic_text = EXCLUDED.semantic_text,"
                    " embedding = EXCLUDED.embedding,"
                    " embedding_dim = EXCLUDED.embedding_dim,"
                    " embedding_model = EXCLUDED.embedding_model,"
                    " embedding_version = EXCLUDED.embedding_version,"
                    " exposure_class = EXCLUDED.exposure_class,"
                    " canonical_hash = EXCLUDED.canonical_hash,"
                    " owner_user_id = EXCLUDED.owner_user_id,"
                    " generated_at = CURRENT_TIMESTAMP,"
                    " persisted_version = retrieval_vectors.persisted_version + 1"
                ),
                {
                    "oid": record.object_id,
                    "over": record.object_version,
                    "payload": record.payload_json,
                    "semtext": record.semantic_text,
                    "emb": self._embedding_literal(record.embedding),
                    "edim": record.embedding_dim,
                    "emodel": record.embedding_model,
                    "ever": record.embedding_version,
                    "exp": record.exposure_class.value,
                    "chash": record.canonical_hash,
                    "owner": record.owner_user_id,
                },
            )
        except Exception as exc:
            if _is_fk_violation(exc):
                detail = str(exc)
                if "retrieval_vectors_owner_fkey" in detail:
                    raise InvalidRecord(
                        f"vector projection references unknown user {record.owner_user_id}"
                    ) from None
                raise InvalidRecord(
                    f"vector projection references unknown canonical object {record.object_id}"
                ) from None
            raise _op_error(exc) from None

    def get_vector_projection(
        self,
        object_id: str,
        *,
        allowed_exposures: Iterable[Any],
        tenant: str | None = None,
    ) -> VectorProjectionRecord | None:
        self._require_postgresql_vector()
        exposures = exposure_allowlist(allowed_exposures)
        if not object_id or not exposures:
            return None  # fail closed: no allow-set, no content
        params: dict[str, Any] = {"oid": object_id, "tenant": tenant}
        marks: list[str] = []
        for index, value in enumerate(exposures):
            params[f"e{index}"] = value
            marks.append(f":e{index}")
        row = self._connection.execute(
            _sql(
                "SELECT "
                + self._VECTOR_SELECT
                + " FROM retrieval_vectors WHERE object_id = :oid"
                + f" AND exposure_class IN ({', '.join(marks)})"
                + " AND (owner_user_id IS NULL OR owner_user_id = :tenant)"
                + " LIMIT 1"
            ),
            params,
        ).mappings().first()
        if row is None:
            return None  # denied is indistinguishable from missing
        return self._vector_row(row)

    def search_vectors(
        self,
        embedding: Iterable[Any],
        *,
        allowed_exposures: Iterable[Any],
        tenant: str | None = None,
        limit: int = 10,
    ) -> tuple[VectorProjectionRecord, ...]:
        self._require_postgresql_vector()
        query = validate_similarity_query(embedding)
        exposures = exposure_allowlist(allowed_exposures)
        if not exposures or int(limit) <= 0:
            return ()
        params: dict[str, Any] = {
            "q": self._embedding_literal(query),
            "qdim": len(query),
            "tenant": tenant,
            "lim": int(limit),
        }
        marks: list[str] = []
        for index, value in enumerate(exposures):
            params[f"e{index}"] = value
            marks.append(f":e{index}")
        rows = self._connection.execute(
            _sql(
                "SELECT "
                + self._VECTOR_SELECT
                + " FROM retrieval_vectors"
                + f" WHERE exposure_class IN ({', '.join(marks)})"
                + " AND (owner_user_id IS NULL OR owner_user_id = :tenant)"
                + " AND vector_dims(embedding) = :qdim"
                + " ORDER BY (embedding <=> CAST(:q AS vector)) ASC, object_id ASC"
                + " LIMIT :lim"
            ),
            params,
        ).mappings().fetchall()
        # Exposure/tenant filtering happened in the WHERE clause: denied rows
        # were never selected, so their content columns never leave the DB.
        return tuple(self._vector_row(row) for row in rows)

    def delete_vector_projection(self, object_id: str) -> None:
        self._require_postgresql_vector()
        try:
            self._connection.execute(
                _sql("DELETE FROM retrieval_vectors WHERE object_id = :oid"),
                {"oid": object_id},
            )
        except Exception as exc:
            raise _op_error(exc) from None

    def rebuild_vector_projection(
        self, records: Iterable[VectorProjectionRecord]
    ) -> tuple[int, int]:
        """Independent deterministic replacement rebuild (G-D4): every source
        row upserted, stale rows removed, canonical tables untouched."""

        self._require_postgresql_vector()
        batch = tuple(records)
        object_ids = [record.object_id for record in batch]
        if len(set(object_ids)) != len(object_ids):
            raise InvalidRecord("duplicate object_id in rebuild batch")
        for record in batch:  # validate the whole batch before mutating
            validate_vector_projection(record)
            self._canonical_projection_reference(record)
        for record in batch:
            self.put_vector_projection(record)
        keep = set(object_ids)
        rows = self._connection.execute(
            _sql("SELECT object_id FROM retrieval_vectors")
        ).fetchall()
        stale = [row[0] for row in rows if row[0] not in keep]
        if stale:
            self._connection.execute(
                _sql("DELETE FROM retrieval_vectors WHERE object_id = ANY(:stale)"),
                {"stale": stale},
            )
        return (len(batch), len(stale))

    # -- durable audit/event ledger (frozen Ch II.2.6; GAP-05) -----------------

    def append_audit_event(self, record: Any) -> bool:
        """Append one durable audit/event row (idempotent by `event_id`).

        Any record-shaped envelope is coerced to the storage record at this
        boundary (`coerce_audit_event`) — the observability package is
        forbidden from importing persistence types (frozen K5/K7 law).

        `seq` is persistence-owned: allocated as MAX(seq)+1 in the same
        write, with a bounded retry when a concurrent writer wins the unique
        race (monotonic allocation, not gap-freedom — the same ordering
        contract as the frozen in-process trails). Each successful append
        commits its own durable unit unless an explicit gateway transaction
        is open, so an audit fact is recorded before it can be read back and
        survives process restart. Repeat append of a stored `event_id`
        returns False and writes nothing; backend faults raise
        PersistenceUnavailable (redacted details only).
        """

        try:
            record = coerce_audit_event(record)
            if self._audit_event_exists(record.event_id):
                return False
            for _attempt in range(3):
                seq = self._next_audit_seq()
                try:
                    self._connection.execute(
                        _sql(
                            "INSERT INTO forge_audit_events (seq, event_id, stream,"
                            " event_type, severity, environment, occurred_at, request_id,"
                            " actor_type, actor_id, resource, outcome, reason, details_json)"
                            " VALUES (:seq, :eid, :stream, :etype, :severity, :env,"
                            " :occurred, :rid, :atype, :aid, :resource, :outcome, :reason,"
                            " :details)"
                        ),
                        {
                            "seq": seq,
                            "eid": record.event_id,
                            "stream": record.stream,
                            "etype": record.event_type,
                            "severity": record.severity,
                            "env": record.environment,
                            "occurred": record.occurred_at,
                            "rid": record.request_id,
                            "atype": record.actor_type,
                            "aid": record.actor_id,
                            "resource": record.resource,
                            "outcome": record.outcome,
                            "reason": record.reason,
                            "details": record.details_json,
                        },
                    )
                except Exception as exc:
                    self._safe_rollback()
                    if _is_unique_violation(exc):
                        # Either the idempotency key (already stored — no-op)
                        # or a concurrent seq allocation (retry with a fresh
                        # allocation).
                        if self._audit_event_exists(record.event_id):
                            return False
                        continue
                    raise _op_error(exc) from None
                if not self._in_transaction:
                    try:
                        self._connection.commit()
                    except Exception as exc:
                        raise _op_error(exc) from None
                return True
            raise _op_error(RuntimeError("audit seq allocation race"))
        except PersistenceError:
            raise
        except Exception as exc:
            raise _op_error(exc) from None

    def list_audit_events(
        self, *, limit: int = 100, stream: str | None = None
    ) -> tuple[AuditEventRecord, ...]:
        """Bounded, append-ordered read-back of stored audit/event rows."""

        try:
            bound = max(1, min(int(limit), 1000))
            params: dict[str, Any] = {"lim": bound}
            where = ""
            if stream:
                where = " WHERE stream = :stream"
                params["stream"] = stream
            rows = self._connection.execute(
                _sql(
                    "SELECT seq, event_id, stream, event_type, severity, environment,"
                    " occurred_at, request_id, actor_type, actor_id, resource, outcome,"
                    " reason, details_json, created_at FROM forge_audit_events"
                    + where
                    + " ORDER BY seq ASC LIMIT :lim"
                ),
                params,
            ).mappings().fetchall()
            return tuple(_audit_row(row) for row in rows)
        except PersistenceError:
            raise
        except Exception as exc:
            raise _op_error(exc) from None

    def _audit_event_exists(self, event_id: str) -> bool:
        row = self._connection.execute(
            _sql("SELECT 1 FROM forge_audit_events WHERE event_id = :eid"),
            {"eid": event_id},
        ).fetchone()
        return row is not None

    def _next_audit_seq(self) -> int:
        row = self._connection.execute(
            _sql("SELECT COALESCE(MAX(seq), 0) + 1 FROM forge_audit_events")
        ).fetchone()
        return int(row[0])


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


def _audit_row(row: Any) -> AuditEventRecord:
    """Map one forge_audit_events row to its record (storage values out)."""

    created = row["created_at"]
    if created is not None and not isinstance(created, str):
        created = str(created)  # dialect TIMESTAMP -> storage string
    return AuditEventRecord(
        seq=int(row["seq"]),
        event_id=str(row["event_id"]),
        stream=str(row["stream"]),
        event_type=str(row["event_type"]),
        severity=str(row["severity"]),
        environment=str(row["environment"]),
        occurred_at=str(row["occurred_at"]),
        request_id=row["request_id"],
        actor_type=str(row["actor_type"]),
        actor_id=row["actor_id"],
        resource=str(row["resource"]),
        outcome=str(row["outcome"]),
        reason=str(row["reason"]),
        details_json=str(row["details_json"]),
        created_at=created,
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


class _SqlGatewayTransaction:
    """Gateway-aware transaction (Book I / Bloc I.3 repair).

    Opens the deferred-validation window on the gateway, then on clean exit
    validates the WHOLE pending record unit before COMMIT — so mutually
    referencing records in one batch (e.g. CLAIM <-> EVIDENCE) commit
    together, while any unresolved ordinary reference still rolls the batch
    back atomically. On exception: ROLLBACK, no partial truth.
    """

    def __init__(self, gateway: "SqlAlchemyPersistenceGateway") -> None:
        self._gateway = gateway

    def __enter__(self) -> "_SqlGatewayTransaction":
        self._gateway._connection.execute(text("BEGIN"))
        self._gateway._in_transaction = True
        self._gateway._pending_records = []
        return self

    def __exit__(self, exc_type: Any, exc: Any, tb: Any) -> None:
        gateway = self._gateway
        gateway._in_transaction = False
        try:
            if exc_type is None:
                try:
                    gateway._validate_pending_references()
                except Exception:
                    # Unit validation failed: roll back the whole batch.
                    gateway._connection.execute(text("ROLLBACK"))
                    raise
                gateway._connection.execute(text("COMMIT"))
            else:
                gateway._connection.execute(text("ROLLBACK"))
        finally:
            gateway._pending_records = []
