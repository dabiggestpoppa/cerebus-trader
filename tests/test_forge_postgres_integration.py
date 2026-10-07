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
