"""Ch II.2.4 vector projection — Book II closure repair (GAP-01) acceptance.

Two layers, deliberately separate:

- ``TestVectorProjectionContract`` — gateway-independent contract rules on
  the in-memory reference double plus dialect truth for the SQL gateway.
  Runs everywhere. This layer is NEVER claimed as pgvector proof.
- ``TestPostgresVectorProjection`` — authoritative proof on real PostgreSQL
  with pgvector (CI ``postgres`` job; skips elsewhere with an explicit
  reason). Acceptance for G-D1 / G-D4 / the G-P3 vector sub-clause lives
  here.

Synthetic vectors are deterministic and every component is exactly
representable in float32 (pgvector stores single precision), so round trips
are exact. No embedding generation exists anywhere in this file or in
``app/`` — Book VII owns that.
"""

from __future__ import annotations

import os
from dataclasses import replace as dc_replace

import pytest

from app.forge.canonical import EvidenceStatus, Layer, ObjectType, ProductExposure
from app.forge.persistence.memory import InMemoryPersistenceGateway
from app.forge.persistence.port import (
    InvalidRecord,
    PersistenceUnavailable,
    VECTOR_MAX_DIMS,
)
from app.forge.persistence.records import (
    CanonicalObjectRecord,
    VectorProjectionRecord,
)

DATABASE_URL = os.getenv("FORGE_TEST_DATABASE_URL", "")


def _canonical(
    canonical_id: str,
    *,
    exposure: ProductExposure = ProductExposure.PUBLIC_TEACHING,
    version: str = "v1",
) -> CanonicalObjectRecord:
    return CanonicalObjectRecord(
        canonical_id=canonical_id,
        object_type=ObjectType.MODEL,
        title=f"title {canonical_id}",
        version=version,
        status=EvidenceStatus.OBSERVED,
        exposure=exposure,
        layer=Layer.NONE,
    )


def _projection(
    canonical: CanonicalObjectRecord,
    *,
    embedding: tuple[float, ...] = (1.0, 0.0, 0.0, 0.0),
    model: str = "synthetic-embed",
    model_version: str = "syn-1",
    owner: str | None = None,
    payload: str = '{"layer": "synthetic"}',
) -> VectorProjectionRecord:
    return VectorProjectionRecord(
        object_id=canonical.canonical_id,
        object_version=canonical.version,
        payload_json=payload,
        semantic_text="synthetic safe semantic text",
        embedding=embedding,
        embedding_dim=len(embedding),
        embedding_model=model,
        embedding_version=model_version,
        exposure_class=canonical.exposure,
        canonical_hash=canonical.to_domain().content_hash(),
        owner_user_id=owner,
    )


def _fingerprint(record: VectorProjectionRecord) -> dict:
    data = {
        "object_id": record.object_id,
        "object_version": record.object_version,
        "payload_json": record.payload_json,
        "semantic_text": record.semantic_text,
        "embedding": record.embedding,
        "embedding_dim": record.embedding_dim,
        "embedding_model": record.embedding_model,
        "embedding_version": record.embedding_version,
        "exposure_class": record.exposure_class.value,
        "canonical_hash": record.canonical_hash,
        "owner_user_id": record.owner_user_id,
        # generated_at is persistence-owned: excluded from identity by design
        # (the same rule as created_at on canonical records).
    }
    return data


ALL_EXPOSURES = tuple(ProductExposure)


class TestVectorProjectionContract:
    """Executable contract rules on the reference double (+ dialect truth)."""

    def _seeded(self) -> tuple[InMemoryPersistenceGateway, CanonicalObjectRecord]:
        gateway = InMemoryPersistenceGateway()
        canonical = _canonical("MOD.TEST.VEC.CONTRACT.V1")
        gateway.create_object(canonical)
        return gateway, canonical

    # -- B1 round trip -------------------------------------------------------
    def test_roundtrip_preserves_every_frozen_field(self) -> None:
        gateway, canonical = self._seeded()
        record = _projection(canonical)
        gateway.put_vector_projection(record)
        loaded = gateway.get_vector_projection(
            canonical.canonical_id, allowed_exposures=ALL_EXPOSURES
        )
        assert loaded is not None
        assert _fingerprint(loaded) == _fingerprint(record)
        assert loaded.generated_at is not None  # stamped by the store

    # -- B2 validation -------------------------------------------------------
    @pytest.mark.parametrize(
        "mutation, field",
        [
            ({"embedding": (0.5, 0.25), "embedding_dim": 4}, "dim mismatch"),
            ({"embedding": (0.5, 0.25, 0.5, 0.75), "embedding_dim": 0}, "dim 0"),
            (
                {"embedding_dim": VECTOR_MAX_DIMS + 1, "embedding": (0.5,)},
                "dim over ceiling",
            ),
            ({"embedding": (0.5, float("nan"), 0.25, 0.75)}, "nan"),
            ({"embedding": (0.5, float("inf"), 0.25, 0.75)}, "inf"),
            ({"embedding": (0.0, 0.0, 0.0, 0.0)}, "zero vector"),
            ({"embedding_model": "  "}, "empty model"),
            ({"embedding_version": ""}, "empty version"),
            ({"canonical_hash": "not-a-hash"}, "bad hash"),
            ({"canonical_hash": "A" * 64}, "uppercase hash"),
            ({"exposure_class": "PUBLIC_TEACHING"}, "raw string exposure"),
            ({"payload_json": "not json{"}, "invalid payload json"),
            ({"owner_user_id": "   "}, "blank owner"),
            ({"object_id": ""}, "empty object id"),
            ({"object_version": ""}, "empty object version"),
        ],
    )
    def test_validation_rejects_and_writes_nothing(self, mutation, field) -> None:
        gateway, canonical = self._seeded()
        record = dc_replace(_projection(canonical), **mutation)
        with pytest.raises(InvalidRecord):
            gateway.put_vector_projection(record)
        assert gateway._vectors == {}  # nothing written (15 rejection paths)

    # -- B3 canonical cross-checks -------------------------------------------
    def test_unknown_canonical_reference_rejected(self) -> None:
        gateway = InMemoryPersistenceGateway()
        orphan = _projection(_canonical("MOD.TEST.VEC.MISSING.V1"))
        with pytest.raises(InvalidRecord):
            gateway.put_vector_projection(orphan)
        assert gateway._vectors == {}

    def test_version_exposure_and_hash_mismatches_rejected(self) -> None:
        gateway, canonical = self._seeded()
        base = _projection(canonical)
        for bad in (
            dc_replace(base, object_version="v2"),
            dc_replace(base, exposure_class=ProductExposure.OPERATOR_ONLY),
            dc_replace(base, canonical_hash="0" * 64),
        ):
            with pytest.raises(InvalidRecord):
                gateway.put_vector_projection(bad)
        assert gateway._vectors == {}

    # -- B4 provider/model identity stability --------------------------------
    def test_model_change_replaces_attributes_not_identity(self) -> None:
        gateway, canonical = self._seeded()
        gateway.put_vector_projection(_projection(canonical, model="model-a"))
        gateway.put_vector_projection(
            _projection(canonical, model="model-b", model_version="syn-2")
        )
        assert len(gateway._vectors) == 1
        loaded = gateway.get_vector_projection(
            canonical.canonical_id, allowed_exposures=ALL_EXPOSURES
        )
        assert loaded is not None
        assert loaded.object_id == canonical.canonical_id
        assert (loaded.embedding_model, loaded.embedding_version) == (
            "model-b",
            "syn-2",
        )

    # -- C1/C3 rebuild determinism and stale removal --------------------------
    def test_rebuild_is_deterministic_and_removes_stale(self) -> None:
        gateway = InMemoryPersistenceGateway()
        keep_a, keep_b = _canonical("MOD.TEST.VEC.KEEP_A.V1"), _canonical(
            "MOD.TEST.VEC.KEEP_B.V1"
        )
        stale = _canonical("MOD.TEST.VEC.STALE.V1")
        for canonical in (keep_a, keep_b, stale):
            gateway.create_object(canonical)
        source = [_projection(keep_a), _projection(keep_b)]
        gateway.put_vector_projection(_projection(stale))  # stale row exists

        wrote, removed = gateway.rebuild_vector_projection(source)
        assert (wrote, removed) == (2, 1)  # stale row removed, source upserted
        first = {
            record.object_id: _fingerprint(record)
            for record, _version in gateway._vectors.values()  # type: ignore[attr-defined]
        }
        assert set(first) == {keep_a.canonical_id, keep_b.canonical_id}

        wrote, removed = gateway.rebuild_vector_projection(source)
        assert (wrote, removed) == (2, 0)  # idempotent: nothing left to remove
        second = {
            record.object_id: _fingerprint(record)
            for record, _version in gateway._vectors.values()  # type: ignore[attr-defined]
        }
        assert first == second  # deterministic replacement rebuild

    # -- C2 independence: projection deletable/rebuildable, canonical intact --
    def test_rebuild_is_independent_of_canonical_truth(self) -> None:
        gateway, canonical = self._seeded()
        record = _projection(canonical)
        gateway.put_vector_projection(record)
        ids_before = gateway.list_object_ids()
        canonical_before = gateway.get_object(canonical.canonical_id)
        edges_before = gateway.edges_for_object(canonical.canonical_id)
        assert canonical_before is not None

        # wipe every projection row
        for object_id in list(gateway._vectors):
            gateway.delete_vector_projection(object_id)
        assert gateway._vectors == {}

        # canonical truth is byte-identical after total projection loss
        assert gateway.get_object(canonical.canonical_id) == canonical_before
        assert gateway.list_object_ids() == ids_before
        assert gateway.edges_for_object(canonical.canonical_id) == edges_before

        # full restoration from the authorized source set
        wrote, removed = gateway.rebuild_vector_projection([record])
        assert (wrote, removed) == (1, 0)
        restored = gateway.get_vector_projection(
            canonical.canonical_id, allowed_exposures=ALL_EXPOSURES
        )
        assert restored is not None
        assert _fingerprint(restored) == _fingerprint(record)

    # -- C4 corruption recovery ------------------------------------------------
    def test_rebuild_recovers_corrupted_projection(self) -> None:
        gateway, canonical = self._seeded()
        record = _projection(canonical)
        gateway.put_vector_projection(record)
        # corrupt the stored row (simulates projection damage)
        damaged = dc_replace(record, embedding=(0.9, 0.9, 0.9, 0.9))
        gateway._vectors[canonical.canonical_id] = (damaged, 1)
        gateway.rebuild_vector_projection([record])
        recovered = gateway.get_vector_projection(
            canonical.canonical_id, allowed_exposures=ALL_EXPOSURES
        )
        assert recovered is not None
        assert _fingerprint(recovered) == _fingerprint(record)

    # -- C5 audit records survive projection operations ------------------------
    def test_audit_trail_survives_projection_rebuild(self) -> None:
        from app.forge.observability.audit import BoundedAuditTrail

        gateway, canonical = self._seeded()
        record = _projection(canonical)
        gateway.put_vector_projection(record)
        trail = BoundedAuditTrail()
        trail.append({"stream": "security_audit", "seq": 1})
        trail.append({"stream": "policy", "seq": 2})
        snapshot = trail.records()
        for object_id in list(gateway._vectors):
            gateway.delete_vector_projection(object_id)
        gateway.rebuild_vector_projection([record])
        assert trail.records() == snapshot  # rebuild never touches audit state
        assert len(trail) == 2

    # -- D1/D2/D3/D5 isolation matrix ------------------------------------------
    def test_isolation_matrix_zero_leakage(self) -> None:
        from app.forge.identity import ForgeUser

        gateway = InMemoryPersistenceGateway()
        gateway.create_user(ForgeUser.create(user_id="user_a"))  # tenant owner (FK parity)
        public = _canonical("MOD.TEST.VEC.M_PUBLIC.V1")
        operator = _canonical(
            "MOD.TEST.VEC.M_OPERATOR.V1", exposure=ProductExposure.OPERATOR_ONLY
        )
        tenant_owned = _canonical("MOD.TEST.VEC.M_TENANT.V1")
        for canonical in (public, operator, tenant_owned):
            gateway.create_object(canonical)
        gateway.put_vector_projection(_projection(public))
        gateway.put_vector_projection(_projection(operator))
        gateway.put_vector_projection(_projection(tenant_owned, owner="user_a"))

        def get(oid, allow, tenant=None):
            return gateway.get_vector_projection(
                oid, allowed_exposures=allow, tenant=tenant
            )

        public_allow = {ProductExposure.PUBLIC_TEACHING}
        operator_allow = {ProductExposure.OPERATOR_ONLY}

        # D1 cross-exposure denial is indistinguishable from missing
        assert get(operator.canonical_id, public_allow) is None
        assert get("MOD.TEST.VEC.NOT_A_ROW.V1", public_allow) is None
        # D2 tenant isolation: shared row visible, owned row strictly scoped
        assert get(public.canonical_id, public_allow) is not None
        assert get(tenant_owned.canonical_id, public_allow) is None  # anon
        assert get(tenant_owned.canonical_id, public_allow, tenant="user_b") is None
        assert get(tenant_owned.canonical_id, public_allow, tenant="user_a") is not None
        # shared row never visible through the wrong exposure, even for its tenant
        assert get(operator.canonical_id, operator_allow, tenant="user_a") is not None
        assert get(operator.canonical_id, public_allow, tenant="user_a") is None
        # D3 empty allow-set fails closed
        assert get(public.canonical_id, set()) is None
        assert get(operator.canonical_id, set(), tenant="user_a") is None

        # D5 search matrix: exact authorized row-id sets, zero leakage
        query = (1.0, 0.0, 0.0, 0.0)
        def ids(allow, tenant=None):
            return [
                record.object_id
                for record in gateway.search_vectors(
                    query, allowed_exposures=allow, tenant=tenant, limit=10
                )
            ]

        assert ids(public_allow) == [public.canonical_id]
        assert ids(public_allow, tenant="user_a") == [
            public.canonical_id,
            tenant_owned.canonical_id,
        ]
        assert ids(public_allow, tenant="user_b") == [public.canonical_id]
        assert ids(operator_allow) == [operator.canonical_id]
        assert ids(set()) == []

    # -- D4 search ordering / limits / dimension guard --------------------------
    def test_search_orders_by_distance_and_honors_limit(self) -> None:
        gateway = InMemoryPersistenceGateway()
        exact = _canonical("MOD.TEST.VEC.S_EXACT.V1")
        near = _canonical("MOD.TEST.VEC.S_NEAR.V1")
        far = _canonical("MOD.TEST.VEC.S_FAR.V1")
        other_dim = _canonical("MOD.TEST.VEC.S_DIM.V1")
        for canonical in (exact, near, far, other_dim):
            gateway.create_object(canonical)
        gateway.put_vector_projection(_projection(exact, embedding=(1.0, 0.0, 0.0, 0.0)))
        gateway.put_vector_projection(_projection(near, embedding=(0.75, 0.25, 0.0, 0.0)))
        gateway.put_vector_projection(_projection(far, embedding=(0.0, 1.0, 0.0, 0.0)))
        gateway.put_vector_projection(
            _projection(other_dim, embedding=(1.0, 0.0, 0.0, 0.0, 0.5, 0.5))
        )

        results = gateway.search_vectors(
            (1.0, 0.0, 0.0, 0.0), allowed_exposures=ALL_EXPOSURES, limit=10
        )
        assert [r.object_id for r in results] == [
            exact.canonical_id,
            near.canonical_id,
            far.canonical_id,
        ]
        # dimension-divergent rows are skipped, never compared
        assert other_dim.canonical_id not in {r.object_id for r in results}
        assert [r.object_id for r in gateway.search_vectors(
            (1.0, 0.0, 0.0, 0.0), allowed_exposures=ALL_EXPOSURES, limit=2
        )] == [exact.canonical_id, near.canonical_id]

    def test_search_rejects_invalid_queries(self) -> None:
        gateway, _canonical_record = self._seeded()
        for bad in ([], [0.0, 0.0], [float("nan"), 1.0], [float("inf"), 1.0]):
            with pytest.raises(InvalidRecord):
                gateway.search_vectors(bad, allowed_exposures=ALL_EXPOSURES)
        assert gateway.search_vectors(
            (1.0, 0.0), allowed_exposures=ALL_EXPOSURES, limit=0
        ) == ()

    # -- D6 similarity never grants authority (structural) -----------------------
    def test_persistence_never_imports_policy_authority(self) -> None:
        import pathlib

        root = pathlib.Path("app") / "forge" / "persistence"
        for path in sorted(root.rglob("*.py")):
            source = path.read_text(encoding="utf-8")
            assert "from app.forge.policy" not in source, path
            assert "import app.forge.policy" not in source, path

    # -- dialect truth (local) ---------------------------------------------------
    def test_migration_003_declares_postgresql_only(self) -> None:
        from app.forge.persistence.sql.migrations import discover_migrations

        migrations = {m.version: m for m in discover_migrations()}
        # 004 = GAP-05 durable audit/event ledger (Build Agent #14 packet);
        # it is PORTABLE (unlike 003) — the SQLite subset must include it.
        assert [m.version for m in migrations.values()] == [1, 2, 3, 4]
        assert migrations[3].identity == "003_vector_projection"
        assert migrations[4].identity == "004_audit_ledger"
        assert migrations[1].postgresql_only is False
        assert migrations[2].postgresql_only is False
        assert migrations[3].postgresql_only is True
        assert migrations[4].postgresql_only is False

    def test_sqlite_portable_subset_has_no_vector_table_and_fails_closed(self) -> None:
        from sqlalchemy import create_engine, text

        from app.forge.persistence.sql.gateway import SqlAlchemyPersistenceGateway

        engine = create_engine("sqlite://")
        connection = engine.connect()
        gateway = SqlAlchemyPersistenceGateway(connection)
        assert gateway.apply_migrations() == "APPLIED"
        assert gateway.check_compatibility() == "OK"
        tables = {
            row[0]
            for row in connection.execute(
                text("SELECT name FROM sqlite_master WHERE type='table'")
            )
        }
        assert "retrieval_vectors" not in tables  # portable subset (001 header)
        with pytest.raises(PersistenceUnavailable):
            gateway.put_vector_projection(
                _projection(_canonical("MOD.TEST.VEC.SQLITE.V1"))
            )


# ---------------------------------------------------------------------------
# Authoritative pgvector proof (CI postgres job)
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def pg_gateway():
    from sqlalchemy import create_engine, text

    from app.forge.persistence.sql.gateway import SqlAlchemyPersistenceGateway

    engine = create_engine(DATABASE_URL)
    connection = engine.connect()
    gw = SqlAlchemyPersistenceGateway(connection)
    gw.apply_migrations()
    connection.commit()  # DDL durability (same pattern as II.2 integration)
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
    yield gw
    connection.close()


@pytest.fixture(scope="module")
def pg_connection(pg_gateway):
    return pg_gateway._connection


@pytest.mark.skipif(
    not DATABASE_URL,
    reason="FORGE_TEST_DATABASE_URL not set — pgvector acceptance executes on CI Postgres+pgvector only (local pgvector infra gap recorded, never substituted)",
)
class TestPostgresVectorProjection:
    @pytest.fixture(autouse=True)
    def _clean_transaction(self, pg_connection):
        # Every test starts from a clean transaction: a failed statement in
        # one test must never poison the next (InFailedSqlTransaction).
        pg_connection.rollback()
        yield
        pg_connection.rollback()

    def _seed(self, gateway, canonical) -> None:
        gateway.create_object(canonical)

    # -- A2/A3 schema ----------------------------------------------------------
    def test_empty_database_applies_pgvector_schema(self, pg_gateway, pg_connection) -> None:
        from sqlalchemy import text

        gateway, connection = pg_gateway, pg_connection

        extension = connection.execute(
            text("SELECT extname FROM pg_extension WHERE extname = 'vector'")
        ).fetchall()
        assert extension, "CREATE EXTENSION vector did not run (G-D1)"
        table = connection.execute(
            text("SELECT tablename FROM pg_tables WHERE tablename = 'retrieval_vectors'")
        ).fetchall()
        assert table
        constraints = {
            row[0]
            for row in connection.execute(
                text(
                    "SELECT conname FROM pg_constraint WHERE conrelid = "
                    "'retrieval_vectors'::regclass"
                )
            ).fetchall()
        }
        assert "retrieval_vectors_dim_check" in constraints
        assert "retrieval_vectors_canonical_fkey" in constraints
        assert "retrieval_vectors_owner_fkey" in constraints
        assert gateway.check_compatibility() == "OK"
        assert gateway.apply_migrations() == "CURRENT"

    # -- B1/B3 round trip + cross-checks ---------------------------------------
    def test_roundtrip_and_canonical_cross_checks(self, pg_gateway) -> None:
        gateway = pg_gateway
        canonical = _canonical("MOD.TEST.VEC.PG_ROUND.V1")
        self._seed(gateway, canonical)
        record = _projection(canonical)
        gateway.put_vector_projection(record)
        loaded = gateway.get_vector_projection(
            canonical.canonical_id, allowed_exposures=ALL_EXPOSURES
        )
        assert loaded is not None
        assert _fingerprint(loaded) == _fingerprint(record)
        assert loaded.generated_at is not None

        for bad in (
            dc_replace(record, object_version="v9"),
            dc_replace(record, exposure_class=ProductExposure.RESEARCH_LAB),
            dc_replace(record, canonical_hash="f" * 64),
            dc_replace(record, embedding=(0.5, 0.25), embedding_dim=4),
        ):
            with pytest.raises(InvalidRecord):
                gateway.put_vector_projection(bad)
        # the failed writes left the original row intact
        still = gateway.get_vector_projection(
            canonical.canonical_id, allowed_exposures=ALL_EXPOSURES
        )
        assert still is not None
        assert _fingerprint(still) == _fingerprint(record)

    # -- A3 database-enforced constraints (raw SQL, bypassing the gateway) -----
    def test_database_enforces_dimension_and_foreign_key(
        self, pg_gateway, pg_connection
    ) -> None:
        from sqlalchemy import text

        gateway, connection = pg_gateway, pg_connection
        canonical = _canonical("MOD.TEST.VEC.PG_CONST.V1")
        canonical2 = _canonical("MOD.TEST.VEC.PG_CONST2.V1")
        self._seed(gateway, canonical)
        self._seed(gateway, canonical2)  # FK-valid target for the CHECK test
        record = _projection(canonical)
        gateway.put_vector_projection(record)
        connection.commit()  # persist before the expected-failure probes below

        with pytest.raises(Exception) as dim_error:
            connection.execute(
                text(
                    "INSERT INTO retrieval_vectors (object_id, object_version,"
                    " payload_json, semantic_text, embedding, embedding_dim,"
                    " embedding_model, embedding_version, exposure_class,"
                    " canonical_hash) VALUES"
                    " (:oid, 'v1', '{}', 'x', CAST(:emb AS vector), 9,"
                    " 'm', '1', 'PUBLIC_TEACHING', :chash)"
                ),
                {"oid": "MOD.TEST.VEC.PG_CONST2.V1", "emb": "[1,0,0,0]", "chash": "0" * 64},
            )
        assert "retrieval_vectors_dim_check" in str(dim_error.value)
        connection.rollback()  # a failed statement aborts the transaction

        with pytest.raises(Exception) as fk_error:
            connection.execute(
                text(
                    "INSERT INTO retrieval_vectors (object_id, object_version,"
                    " payload_json, semantic_text, embedding, embedding_dim,"
                    " embedding_model, embedding_version, exposure_class,"
                    " canonical_hash) VALUES"
                    " ('MOD.TEST.VEC.PG_DANGLING.V1', 'v1', '{}', 'x',"
                    " CAST('[1,0,0,0]' AS vector), 4, 'm', '1',"
                    " 'PUBLIC_TEACHING', :chash)"
                ),
                {"chash": "0" * 64},
            )
        assert "retrieval_vectors_canonical_fkey" in str(fk_error.value)
        connection.rollback()  # leave the connection clean for later tests

    # -- B4 identity stability on PostgreSQL ------------------------------------
    def test_model_change_keeps_identity_on_postgres(self, pg_gateway) -> None:
        gateway = pg_gateway
        canonical = _canonical("MOD.TEST.VEC.PG_MODEL.V1")
        self._seed(gateway, canonical)
        gateway.put_vector_projection(_projection(canonical, model="model-a"))
        gateway.put_vector_projection(
            _projection(canonical, model="model-b", model_version="syn-2")
        )
        row_count = len(
            gateway.search_vectors(
                (1.0, 0.0, 0.0, 0.0), allowed_exposures=ALL_EXPOSURES, limit=50
            )
        )
        loaded = gateway.get_vector_projection(
            canonical.canonical_id, allowed_exposures=ALL_EXPOSURES
        )
        assert loaded is not None
        assert (loaded.embedding_model, loaded.embedding_version) == (
            "model-b",
            "syn-2",
        )
        assert row_count >= 1

    # -- G-D4 rebuild proofs ------------------------------------------------------
    def test_rebuild_deterministic_stale_and_corruption_recovery(
        self, pg_gateway, pg_connection
    ) -> None:
        from sqlalchemy import text

        gateway, connection = pg_gateway, pg_connection

        keep_a = _canonical("MOD.TEST.VEC.PG_KEEP_A.V1")
        keep_b = _canonical("MOD.TEST.VEC.PG_KEEP_B.V1")
        stale = _canonical("MOD.TEST.VEC.PG_STALE.V1")
        for canonical in (keep_a, keep_b, stale):
            self._seed(gateway, canonical)
        source = [_projection(keep_a), _projection(keep_b)]

        connection.execute(text("TRUNCATE retrieval_vectors"))
        connection.commit()

        # independent rebuild from an empty projection
        wrote, removed = gateway.rebuild_vector_projection(source)
        assert (wrote, removed) == (2, 0)
        first = {
            record.object_id: _fingerprint(record)
            for record in gateway.search_vectors(
                (1.0, 0.0, 0.0, 0.0), allowed_exposures=ALL_EXPOSURES, limit=50
            )
        }
        # deterministic: second rebuild yields the identical set
        wrote, removed = gateway.rebuild_vector_projection(source)
        assert (wrote, removed) == (2, 0)
        second = {
            record.object_id: _fingerprint(record)
            for record in gateway.search_vectors(
                (1.0, 0.0, 0.0, 0.0), allowed_exposures=ALL_EXPOSURES, limit=50
            )
        }
        assert first == second

        # a stale row written outside the source set is removed by rebuild
        gateway.put_vector_projection(_projection(stale))
        wrote, removed = gateway.rebuild_vector_projection(source)
        assert (wrote, removed) == (2, 1)

        # corruption recovery: damage the row, rebuild restores it
        connection.execute(
            text(
                "UPDATE retrieval_vectors SET embedding = CAST('[0.9,0.9,0.9,0.9]'"
                " AS vector), canonical_hash = 'f' WHERE object_id = :oid"
            ),
            {"oid": keep_a.canonical_id},
        )
        connection.commit()
        gateway.rebuild_vector_projection(source)
        recovered = gateway.get_vector_projection(
            keep_a.canonical_id, allowed_exposures=ALL_EXPOSURES
        )
        assert recovered is not None
        assert _fingerprint(recovered) == _fingerprint(_projection(keep_a))

        # canonical truth untouched by the whole sequence
        assert gateway.get_object(keep_a.canonical_id) is not None
        assert gateway.get_object(keep_b.canonical_id) is not None
        assert gateway.get_object(stale.canonical_id) is not None

    # -- G-P3 vector leakage: isolation proven on real PostgreSQL ---------------
    def test_isolation_matrix_on_postgres(self, pg_gateway, pg_connection) -> None:
        from sqlalchemy import text

        from app.forge.identity import ForgeUser

        gateway, connection = pg_gateway, pg_connection
        # isolation starts from a clean projection so the id sets are exact
        connection.execute(text("TRUNCATE retrieval_vectors"))
        connection.commit()
        gateway.create_user(ForgeUser.create(user_id="user_a"))  # tenant owner FK
        public = _canonical("MOD.TEST.VEC.PG_PUBLIC.V1")
        operator = _canonical(
            "MOD.TEST.VEC.PG_OPERATOR.V1", exposure=ProductExposure.OPERATOR_ONLY
        )
        tenant_owned = _canonical("MOD.TEST.VEC.PG_TENANT.V1")
        for canonical in (public, operator, tenant_owned):
            self._seed(gateway, canonical)
        gateway.put_vector_projection(_projection(public))
        gateway.put_vector_projection(_projection(operator))
        gateway.put_vector_projection(_projection(tenant_owned, owner="user_a"))

        def get(oid, allow, tenant=None):
            return gateway.get_vector_projection(
                oid, allowed_exposures=allow, tenant=tenant
            )

        public_allow = {ProductExposure.PUBLIC_TEACHING}
        operator_allow = {ProductExposure.OPERATOR_ONLY}

        # denied ≡ missing: identical return, zero content
        assert get(operator.canonical_id, public_allow) is None
        assert get("MOD.TEST.VEC.PG_NOPE.V1", public_allow) is None
        assert get(tenant_owned.canonical_id, public_allow) is None
        assert get(tenant_owned.canonical_id, public_allow, tenant="user_b") is None
        assert get(tenant_owned.canonical_id, public_allow, tenant="user_a") is not None
        assert get(operator.canonical_id, operator_allow, tenant="user_a") is not None
        assert get(operator.canonical_id, public_allow, tenant="user_a") is None
        assert get(public.canonical_id, set()) is None

        # search: exact authorized id sets; denied rows never selected
        query = (1.0, 0.0, 0.0, 0.0)

        def ids(allow, tenant=None):
            return [
                record.object_id
                for record in gateway.search_vectors(
                    query, allowed_exposures=allow, tenant=tenant, limit=50
                )
            ]

        assert ids(public_allow) == [public.canonical_id]
        assert ids(public_allow, tenant="user_a") == [
            public.canonical_id,
            tenant_owned.canonical_id,
        ]
        assert ids(public_allow, tenant="user_b") == [public.canonical_id]
        assert ids(operator_allow) == [operator.canonical_id]
        assert ids(set()) == []
        # ranking within the authorized set: exact match first
        assert ids(public_allow, tenant="user_a")[0] == public.canonical_id
        assert ids(public_allow, tenant="user_a") == [
            public.canonical_id,
            tenant_owned.canonical_id,
        ]  # tie broken by object_id, no content from other exposures

    # -- Ch II.2.4 identity stability across provider/model change ---------------
    def test_projection_deletion_leaves_canonical_truth_intact(
        self, pg_gateway, pg_connection
    ) -> None:
        from sqlalchemy import text

        gateway, connection = pg_gateway, pg_connection

        canonical = _canonical("MOD.TEST.VEC.PG_WIPE.V1")
        self._seed(gateway, canonical)
        record = _projection(canonical)
        gateway.put_vector_projection(record)
        content_before = connection.execute(
            text(
                "SELECT content_hash, status FROM canonical_objects"
                " WHERE canonical_id = :cid"
            ),
            {"cid": canonical.canonical_id},
        ).fetchall()
        gateway.delete_vector_projection(canonical.canonical_id)
        assert (
            gateway.get_vector_projection(
                canonical.canonical_id, allowed_exposures=ALL_EXPOSURES
            )
            is None
        )
        content_after = connection.execute(
            text(
                "SELECT content_hash, status FROM canonical_objects"
                " WHERE canonical_id = :cid"
            ),
            {"cid": canonical.canonical_id},
        ).fetchall()
        assert content_before == content_after
        # and the projection can be fully restored
        wrote, removed = gateway.rebuild_vector_projection([record])
        assert (wrote, removed) == (1, 0)
        restored = gateway.get_vector_projection(
            canonical.canonical_id, allowed_exposures=ALL_EXPOSURES
        )
        assert restored is not None
        assert _fingerprint(restored) == _fingerprint(record)
