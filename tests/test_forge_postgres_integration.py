"""Real-PostgreSQL integration evidence for Bloc II.2.

These tests execute ONLY when a live PostgreSQL URL is provided via
`FORGE_TEST_DATABASE_URL` (CI postgres job). Locally they skip with a clear
message; the skip is the declared integration gap, not hidden coverage.

What they prove against the real server:
- migrations apply on empty PostgreSQL and are a no-op when current;
- canonical round trip preserves identity/hash on PostgreSQL;
- typed provenance edges persist with real FK/PK constraints;
- duplicate object/artifact/edge rejections surface from actual constraints;
- optimistic-concurrency conflicts surface from real versions.
"""

from __future__ import annotations

import os

import pytest

DATABASE_URL = os.getenv("FORGE_TEST_DATABASE_URL", "")

pytestmark = pytest.mark.skipif(
    not DATABASE_URL,
    reason="FORGE_TEST_DATABASE_URL not set — real PostgreSQL integration is NOT EXECUTED locally (deferred to CI)",
)


@pytest.fixture(scope="module")
def gateway():
    from sqlalchemy import create_engine

    from app.forge.persistence.sql.gateway import SqlAlchemyPersistenceGateway

    engine = create_engine(DATABASE_URL)
    connection = engine.connect()
    gw = SqlAlchemyPersistenceGateway(connection)
    gw.apply_migrations()
    connection.commit()  # DDL durability: PostgreSQL rolls back uncommitted DDL
    # expose to teardown helper
    TestPostgresIntegration._gw = gw
    yield gw
    TestPostgresIntegration._gw = None
    connection.close()
    engine.dispose()


def _model(cid="MOD.PG.INTEG.V1"):
    from app.forge.canonical import (
        CanonicalId,
        CanonicalObject,
        EvidenceStatus,
        Layer,
        ObjectType,
        ProductExposure,
    )

    return CanonicalObject(
        canonical_id=CanonicalId(value=cid, object_type=ObjectType.MODEL),
        title="Postgres integration",
        version="v1",
        status=EvidenceStatus.CANDIDATE,
        exposure=ProductExposure.SUBSCRIBER_MODEL,
        layer=Layer.L3,
        metadata={"provenance": "ci"},
    )


class TestPostgresIntegration:
    def test_migrations_applied_and_current(self, gateway) -> None:
        assert gateway.check_compatibility() == "OK"
        assert gateway.apply_migrations() == "CURRENT"

    def test_ping(self, gateway) -> None:
        gateway.ping()  # must not raise

    def test_canonical_round_trip_on_postgres(self, gateway) -> None:
        from app.forge.canonical import ObjectType
        from app.forge.persistence.records import CanonicalObjectRecord

        obj = _model()
        result = gateway.create_object(CanonicalObjectRecord.from_domain(obj))
        assert result.operation == "CREATE"
        restored = gateway.get_object("MOD.PG.INTEG.V1").to_domain()
        assert restored.content_hash() == obj.content_hash()
        assert restored.canonical_id.object_type is ObjectType.MODEL

    def test_duplicate_rejected_by_real_constraint(self, gateway) -> None:
        from app.forge.persistence.records import CanonicalObjectRecord
        from app.forge.persistence.port import DuplicateCanonicalObject

        record = CanonicalObjectRecord.from_domain(_model())
        with pytest.raises(DuplicateCanonicalObject):
            gateway.create_object(record)

    def test_status_transition_and_stale_conflict(self, gateway) -> None:
        from app.forge.persistence.port import StaleWriteConflict

        result = gateway.transition_status("MOD.PG.INTEG.V1", "PARKED")
        assert result.operation == "TRANSITION"
        with pytest.raises(StaleWriteConflict):
            gateway.transition_status(
                "MOD.PG.INTEG.V1", "CANDIDATE", expected_version=1
            )

    def test_provenance_edge_with_real_fk(self, gateway) -> None:
        from app.forge.persistence.port import DuplicateProvenanceEdge, DanglingReference
        from app.forge.persistence.records import ArtifactRecord, ProvenanceEdgeRecord

        artifact = ArtifactRecord(
            artifact_id="ART.MARKDOWN.BBAAF0123456789ABCDEFAB",
            source_class="MARKDOWN",
            content_identity="sha256:" + "c" * 64,
            source_state="VERIFIED",
        )
        gateway.create_artifact(artifact)
        gateway.add_provenance_edge(
            ProvenanceEdgeRecord(
                artifact_id=artifact.artifact_id,
                object_id="MOD.PG.INTEG.V1",
                relation="SUPPORTS",
            )
        )
        with pytest.raises(DuplicateProvenanceEdge):
            gateway.add_provenance_edge(
                ProvenanceEdgeRecord(
                    artifact_id=artifact.artifact_id,
                    object_id="MOD.PG.INTEG.V1",
                    relation="SUPPORTS",
                )
            )

    def test_provenance_edge_dangling_object_rejected(self, gateway) -> None:
        """PostgreSQL FK: edge to a non-existent object fails as DanglingReference.

        Isolated from the test above because a failed INSERT aborts the
        PostgreSQL transaction; each rejection runs on a fresh connection
        state via the gateway's safe rollback.
        """

        from app.forge.persistence.port import DanglingReference
        from app.forge.persistence.records import ProvenanceEdgeRecord

        with pytest.raises(DanglingReference):
            gateway.add_provenance_edge(
                ProvenanceEdgeRecord(
                    artifact_id="ART.MARKDOWN.BBAAF0123456789ABCDEFAB",
                    object_id="MOD.PG.NONEXISTENT.V1",
                    relation="SUPPORTS",
                )
            )

    def teardown_method(self, method) -> None:
        """Roll back any aborted transaction so later tests get a clean state."""

        gw = getattr(self, "_gw", None)
        if gw is not None:
            try:
                gw.ping()
            except Exception:
                pass


# ---------------------------------------------------------------------------
# Book II / Bloc II.3 — identity & session on real PostgreSQL
# ---------------------------------------------------------------------------


def _iso(dt) -> str:
    from app.forge.identity import utc_now_iso

    return utc_now_iso(dt)


class TestPostgresIdentitySession:
    """II.3 acceptance T1–T6 against the real PostgreSQL 16 CI service."""

    def teardown_method(self, method) -> None:
        gw = getattr(self, "_gw", None)
        if gw is not None:
            try:
                gw.ping()
            except Exception:
                pass

    def test_identity_migration_chain_and_noop(self, gateway) -> None:
        self._gw = gateway
        # 001 + 002 are both recorded; compatibility is OK, re-run is a no-op
        from app.forge.persistence.sql.migrations import discover_migrations

        versions = [m.version for m in discover_migrations()]
        assert versions == [1, 2]
        assert gateway.check_compatibility() == "OK"
        assert gateway.apply_migrations() == "CURRENT"

    def test_user_persistence_and_duplicate_rejection(self, gateway) -> None:
        from app.forge.identity import ForgeUser
        from app.forge.persistence.port import DuplicateForgeUser

        self._gw = gateway
        user = ForgeUser.create(email="pg-integ@example.com")
        assert gateway.create_user(user).operation == "CREATE"
        fetched = gateway.get_user(user.user_id)
        assert fetched.user_id == user.user_id
        assert fetched.email == "pg-integ@example.com"
        with pytest.raises(DuplicateForgeUser):
            gateway.create_user(user)

    def test_provider_identity_mapping_and_uniqueness(self, gateway) -> None:
        from app.forge.identity import ExternalIdentityLink, ForgeUser
        from app.forge.persistence.port import DuplicateIdentityLink

        self._gw = gateway
        user = ForgeUser.create()
        gateway.create_user(user)
        gateway.create_identity_link(
            ExternalIdentityLink(
                provider="whop", provider_subject="pg-subject-1", forge_user_id=user.user_id
            )
        )
        resolved = gateway.get_identity_link("whop", "pg-subject-1")
        assert resolved.forge_user_id == user.user_id
        # real composite-PK constraint surfaces the duplicate
        with pytest.raises(DuplicateIdentityLink):
            gateway.create_identity_link(
                ExternalIdentityLink(
                    provider="whop",
                    provider_subject="pg-subject-1",
                    forge_user_id=user.user_id,
                )
            )

    def test_session_persistence_and_token_digest_lookup(self, gateway) -> None:
        from datetime import timedelta

        from app.forge.identity import ForgeUser
        from app.forge.service.authentication import ForgeAuthenticationService

        self._gw = gateway
        user = ForgeUser.create()
        gateway.create_user(user)
        auth = ForgeAuthenticationService(gateway)
        issued = auth.open_session(user, ttl=timedelta(minutes=10))
        found = gateway.find_session_by_token_digest(
            __import__("app.forge.identity", fromlist=["token_digest"]).token_digest(
                issued.bearer_token
            )
        )
        assert found.session_id == issued.session.session_id
        principal = auth.authenticate_bearer(f"Bearer {issued.bearer_token}")
        assert principal.authenticated is True
        assert principal.forge_user_id == user.user_id

    def test_session_fk_enforced_by_real_constraint(self, gateway) -> None:
        from datetime import timedelta

        from app.forge.identity import (
            ForgeSession,
            ForgeUser,
            new_forge_session_id,
            token_digest,
            new_session_token,
            utc_now_iso,
        )
        from app.forge.persistence.port import UserNotFound

        self._gw = gateway
        ghost = ForgeUser.create(user_id="ghost-user-pg")
        session = ForgeSession(
            session_id=new_forge_session_id(),
            user_id=ghost.user_id,
            token_digest=token_digest(new_session_token()),
            expires_at=utc_now_iso(),
        )
        with pytest.raises(UserNotFound):
            gateway.create_session(session)

    def test_revocation_and_revoke_all(self, gateway) -> None:
        from datetime import timedelta

        from app.forge.identity import ForgeUser
        from app.forge.service.authentication import (
            AuthenticationFailure,
            ForgeAuthenticationService,
        )

        self._gw = gateway
        user = ForgeUser.create()
        gateway.create_user(user)
        auth = ForgeAuthenticationService(gateway)
        a = auth.open_session(user, ttl=timedelta(minutes=10))
        b = auth.open_session(user, ttl=timedelta(minutes=10))
        assert gateway.revoke_all_sessions(user.user_id) == 2
        for token in (a.bearer_token, b.bearer_token):
            with pytest.raises(AuthenticationFailure):
                auth.authenticate_bearer(f"Bearer {token}")

    def test_optimistic_concurrency_on_identity(self, gateway) -> None:
        from app.forge.identity import ForgeUser
        from app.forge.persistence.port import StaleWriteConflict

        self._gw = gateway
        user = ForgeUser.create()
        gateway.create_user(user)
        gateway.transition_user_state(user.user_id, "DISABLED")  # version 2
        with pytest.raises(StaleWriteConflict):
            gateway.transition_user_state(
                user.user_id, "ACTIVE", expected_version=1
            )
