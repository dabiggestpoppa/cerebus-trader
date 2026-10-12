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
    from sqlalchemy import create_engine, text

    from app.forge.persistence.sql.gateway import SqlAlchemyPersistenceGateway

    engine = create_engine(DATABASE_URL)
    connection = engine.connect()
    gw = SqlAlchemyPersistenceGateway(connection)
    gw.apply_migrations()
    connection.commit()  # DDL durability: PostgreSQL rolls back uncommitted DDL
    # Fresh-database semantics for EVERY invocation: the CI postgres job runs
    # this module three times against one service container (full suite, then
    # two verbose evidence runs), and committed rows from a previous run must
    # never surface as duplicate-key failures. Data tables are truncated;
    # schema and the migration ledger are untouched; every test's write and
    # assertion still executes against the real server.
    tables = connection.execute(
        text(
            "SELECT tablename FROM pg_tables WHERE schemaname = 'public' "
            "AND tablename <> 'forge_schema_migrations'"
        )
    ).fetchall()
    if tables:
        connection.execute(
            text(
                "TRUNCATE "
                + ", ".join(f'"{row[0]}"' for row in tables)
                + " RESTART IDENTITY CASCADE"
            )
        )
    connection.commit()
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
        # 001 + 002 + 003 are all recorded on Postgres+pgvector; compatibility
        # is OK, re-run is a no-op
        from app.forge.persistence.sql.migrations import discover_migrations

        versions = [m.version for m in discover_migrations()]
        assert versions == [1, 2, 3]
        migrations = {m.version: m for m in discover_migrations()}
        assert migrations[3].identity == "003_vector_projection"
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


# ---------------------------------------------------------------------------
# Book I / Bloc I.3 — transaction batch semantics on real PostgreSQL
# (in-memory gateway parity: mutual references, in-batch duplicate ids,
#  atomic rollback of objects + artifacts + edges)
# ---------------------------------------------------------------------------


def _typed(cid: str, object_type, references=()):
    from app.forge.canonical import (
        CanonicalId,
        CanonicalObject,
        EvidenceStatus,
        Layer,
        ProductExposure,
    )
    from app.forge.persistence.records import CanonicalObjectRecord

    obj = CanonicalObject(
        canonical_id=CanonicalId(value=cid, object_type=object_type),
        title="I.3 batch probe",
        version="v1",
        status=EvidenceStatus.CANDIDATE,
        exposure=ProductExposure.SUBSCRIBER_MODEL,
        layer=Layer.NONE,
        references=tuple(references),
        metadata={"probe": "i3"},
    )
    return CanonicalObjectRecord.from_domain(obj)


class TestPostgresTransactionBatchSemantics:
    def test_mutual_references_commit_in_one_transaction(self, gateway) -> None:
        """I.3 repair A on PostgreSQL: mutually referencing CLAIM and
        EVIDENCE records commit as one unit; their ordinary references
        resolve after COMMIT."""
        from app.forge.canonical import CanonicalReference, ObjectType
        from app.forge.persistence.port import DanglingReference

        self._gw = gateway
        claim = _typed(
            "CL.PG.MUTUAL.V1",
            ObjectType.CLAIM,
            references=(
                CanonicalReference(
                    target_id="EV.PG.MUTUAL.V1", relation="supported_by"
                ),
            ),
        )
        evidence = _typed(
            "EV.PG.MUTUAL.V1",
            ObjectType.EVIDENCE,
            references=(
                CanonicalReference(
                    target_id="CL.PG.MUTUAL.V1", relation="evidence_for"
                ),
            ),
        )
        with gateway.transaction():
            gateway.create_object(claim)
            gateway.create_object(evidence)
        restored = gateway.get_object("CL.PG.MUTUAL.V1")
        restored_ev = gateway.get_object("EV.PG.MUTUAL.V1")
        assert restored is not None and restored_ev is not None
        for record in (restored, restored_ev):
            for ref in record.references:
                assert gateway.get_object(ref.target_id) is not None

        # The unit rule never becomes a blanket pass: a reference whose
        # target is absent from the batch and the store still fails.
        lone = _typed(
            "CL.PG.LONE.V1",
            ObjectType.CLAIM,
            references=(
                CanonicalReference(
                    target_id="EV.PG.ABSENT.V1", relation="supported_by"
                ),
            ),
        )
        with pytest.raises(DanglingReference):
            with gateway.transaction():
                gateway.create_object(lone)
        assert gateway.get_object("CL.PG.LONE.V1") is None

    def test_duplicate_canonical_id_within_batch_rejected(self, gateway) -> None:
        """I.3 repair B on PostgreSQL: a second record with a canonical id
        already inserted earlier in the SAME transaction is rejected (real
        primary key / eager existence check) and the batch rolls back."""
        from app.forge.canonical import ObjectType
        from app.forge.persistence.port import DuplicateCanonicalObject

        self._gw = gateway
        first = _typed("MOD.PG.BATCHDUP.V1", ObjectType.MODEL)
        second = _typed("MOD.PG.BATCHDUP.V1", ObjectType.MODEL)
        with pytest.raises(DuplicateCanonicalObject):
            with gateway.transaction():
                gateway.create_object(first)
                gateway.create_object(second)
        assert gateway.get_object("MOD.PG.BATCHDUP.V1") is None

    def test_failed_batch_rolls_back_objects_artifacts_edges(
        self, gateway
    ) -> None:
        """I.3 atomic rollback on PostgreSQL: an unresolved ordinary
        reference detected at commit rolls back objects, artifacts AND
        provenance edges from the same logical batch."""
        from app.forge.canonical import CanonicalReference, ObjectType
        from app.forge.persistence.port import DanglingReference
        from app.forge.persistence.records import ArtifactRecord, ProvenanceEdgeRecord

        self._gw = gateway
        artifact = ArtifactRecord(
            artifact_id="ART.MARKDOWN.DDCCF0123456789ABCDEFAB",
            source_class="MARKDOWN",
            content_identity="sha256:" + "d" * 64,
            source_state="VERIFIED",
            locator="corpus/probe.md",
        )
        good = _typed("MOD.PG.LEAK.V1", ObjectType.MODEL)
        bad = _typed(
            "MOD.PG.LEAKBAD.V1",
            ObjectType.MODEL,
            references=(
                CanonicalReference(
                    target_id="MOD.PG.GONE.V1", relation="SUPPORTS"
                ),
            ),
        )
        with pytest.raises(DanglingReference):
            with gateway.transaction():
                gateway.create_artifact(artifact)
                gateway.create_object(good)
                gateway.add_provenance_edge(
                    ProvenanceEdgeRecord(
                        artifact_id=artifact.artifact_id,
                        object_id=good.canonical_id,
                        relation="DEFINES",
                        note="rollback probe",
                    )
                )
                gateway.create_object(bad)
        assert gateway.get_object("MOD.PG.LEAK.V1") is None
        assert gateway.get_object("MOD.PG.LEAKBAD.V1") is None
        assert gateway.get_artifact(artifact.artifact_id) is None
        assert gateway.edges_for_object("MOD.PG.LEAK.V1") == ()

    def test_full_corpus_backfill_apply_on_postgres(self, gateway) -> None:
        """I.3 P1/P2/Q1 on real PostgreSQL: the full canonical corpus commits
        through the port in ONE transaction batch (mutual CLAIM<->EVIDENCE
        included), and a second apply over identical source state is a NO-OP
        with zero conflicts (no silent overwrite, no duplicate truth)."""
        from pathlib import Path

        from app.forge.backfill.canonicalizer import canonicalize_files
        from app.forge.backfill.runner import BackfillMode, load_corpus_files, run_backfill

        self._gw = gateway
        repo_root = Path(__file__).resolve().parents[1]
        plan = canonicalize_files(load_corpus_files(repo_root))
        assert len(plan.objects) == 30

        result = run_backfill(gateway, repo_root, BackfillMode.APPLY)
        assert result.report.migrated == 30
        assert result.report.conflicts == 0
        for record in plan.objects:
            restored = gateway.get_object(record.canonical_id)
            assert restored is not None, record.canonical_id
            assert restored.status is record.status
            assert restored.claim_identity == record.claim_identity
            # references preserve semantic content as an unordered set
            # (frozen schema PK = canonical_id + target_id + relation)
            assert {
                (r.target_id, r.relation, r.allow_unresolved_historical)
                for r in restored.references
            } == {
                (r.target_id, r.relation, r.allow_unresolved_historical)
                for r in record.references
            }
            assert restored.metadata == record.metadata
        # mutual reference pair present on PostgreSQL
        claim = gateway.get_object("CL.FIB.R11.GENERATOR_FAILURE")
        assert any(
            r.target_id == "EV.FIB.R11.ANCHOR_OVERGEN.V1" for r in claim.references
        )

        second = run_backfill(gateway, repo_root, BackfillMode.APPLY)
        assert second.report.unchanged == 30
        assert second.report.conflicts == 0
        assert len(gateway.list_object_ids()) >= 30

    def teardown_method(self, method) -> None:
        gw = getattr(self, "_gw", None)
        if gw is not None:
            try:
                gw.ping()
            except Exception:
                pass


# ---------------------------------------------------------------------------
# Book I / Bloc I.4 — retrieval index built from real PostgreSQL
# (cross-store index identity + freshness after a real transaction)
# ---------------------------------------------------------------------------


def _retrieval_probe_record():
    from app.forge.canonical import (
        CanonicalId,
        CanonicalObject,
        EvidenceStatus,
        Layer,
        ObjectType,
        ProductExposure,
    )
    from app.forge.persistence.records import CanonicalObjectRecord

    obj = CanonicalObject(
        canonical_id=CanonicalId(
            value="MOD.PG.RETRIEVAL.V1", object_type=ObjectType.MODEL
        ),
        title="Postgres retrieval index probe",
        version="v1",
        status=EvidenceStatus.CANDIDATE,
        exposure=ProductExposure.SUBSCRIBER_MODEL,
        layer=Layer.NONE,
        metadata={"provenance": "ci-i4"},
    )
    return CanonicalObjectRecord.from_domain(obj)


def _ensure_probe(gateway) -> None:
    if gateway.get_object("MOD.PG.RETRIEVAL.V1") is None:
        with gateway.transaction():
            gateway.create_object(_retrieval_probe_record())


class TestPostgresRetrievalIndex:
    """I.4 acceptance U1/U2 against the real PostgreSQL 16 CI service.

    U1: an index compiled from the PostgreSQL store is byte-identical to one
    compiled from the in-memory store over the same governed state (proof that
    reference order, JSON round-trips and persistence-owned fields never leak
    into record identity).
    U2: freshness is observable after a real transactional status transition
    and cleared by a rebuild.
    """

    def teardown_method(self, method) -> None:
        gw = getattr(self, "_gw", None)
        if gw is not None:
            try:
                gw.ping()
            except Exception:
                pass

    def test_index_builds_from_postgres_with_identical_hash_and_freshness(
        self, gateway
    ) -> None:
        from pathlib import Path

        from app.forge.backfill.runner import BackfillMode, run_backfill
        from app.forge.persistence.memory import InMemoryPersistenceGateway
        from app.forge.retrieval import (
            IndexBuildMode,
            IndexBuildOutcome,
            RetrievalIndex,
            run_index_build,
        )

        self._gw = gateway
        repo_root = Path(__file__).resolve().parents[1]

        # Both stores hold identical governed state: the applied corpus plus
        # every object/artifact/edge earlier tests left on this PostgreSQL
        # server (mirrored verbatim so the comparison is exact).
        run_backfill(gateway, repo_root, BackfillMode.APPLY)  # idempotent
        _ensure_probe(gateway)
        memory = InMemoryPersistenceGateway()
        run_backfill(memory, repo_root, BackfillMode.APPLY)
        with memory.transaction():
            for object_id in gateway.list_object_ids():
                if memory.get_object(object_id) is None:
                    memory.create_object(gateway.get_object(object_id))
            for object_id in gateway.list_object_ids():
                for edge in gateway.edges_for_object(object_id):
                    if memory.get_artifact(edge.artifact_id) is None:
                        memory.create_artifact(gateway.get_artifact(edge.artifact_id))
                    already = any(
                        existing.artifact_id == edge.artifact_id
                        and existing.object_id == edge.object_id
                        and existing.relation == edge.relation
                        for existing in memory.edges_for_object(object_id)
                    )
                    if not already:
                        memory.add_provenance_edge(edge)
        assert set(gateway.list_object_ids()) == set(memory.list_object_ids())

        pg_index = RetrievalIndex()
        pg_report = run_index_build(
            gateway, repo_root, IndexBuildMode.APPLY, pg_index
        )
        memory_index = RetrievalIndex()
        memory_report = run_index_build(
            memory, repo_root, IndexBuildMode.APPLY, memory_index
        )

        # U1 — cross-store identity
        assert pg_report.compiled == len(memory.list_object_ids())
        assert pg_report.compiled >= 31
        assert pg_report.index_hash == memory_report.index_hash
        assert pg_report.source_fingerprint == memory_report.source_fingerprint
        assert pg_index.require().content_hash() == memory_index.require().content_hash()
        assert pg_index.is_stale(gateway) is False

        # U2 — freshness after a real PostgreSQL status transition
        result = gateway.transition_status("MOD.PG.RETRIEVAL.V1", "PARKED")
        assert result.operation == "TRANSITION"
        assert pg_index.is_stale(gateway) is True

        rebuilt = run_index_build(gateway, repo_root, IndexBuildMode.APPLY, pg_index)
        assert rebuilt.outcome is IndexBuildOutcome.PUBLISHED
        assert rebuilt.changed == ("MOD.PG.RETRIEVAL.V1",)
        assert rebuilt.added == () and rebuilt.removed == ()
        assert rebuilt.generation == 2
        assert pg_index.is_stale(gateway) is False
        assert (
            pg_index.require()
            .record("MOD.PG.RETRIEVAL.V1")
            .status.value
            == "PARKED"
        )

        # an immediate second rebuild is a deterministic no-op
        again = run_index_build(gateway, repo_root, IndexBuildMode.APPLY, pg_index)
        assert again.outcome is IndexBuildOutcome.UNCHANGED
        assert again.index_hash == rebuilt.index_hash
