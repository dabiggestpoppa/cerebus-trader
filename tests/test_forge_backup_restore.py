"""GAP-02 backup/restore smoke — Book II closure repair.

Executes ONLY when `FORGE_TEST_DATABASE_URL` is set (CI `postgres` job,
which runs on Postgres+pgvector). Locally it skips with an explicit reason:
role `forge` has no CREATEDB and the local server has no pgvector package —
an infrastructure gap that is recorded, never substituted. See
`implementation/forge/book_ii/closure_repair/PLAN.md` §4.

The smoke is a real round trip: `pg_dump` (custom format) of the live test
database → `pg_restore` into a **fresh, empty database** → every assertion
reads the RESTORED database only. A successful dump exit code is never
claimed as proof; verification is the round trip plus the independent
checks. Credentials travel only in the child process environment (never in
argv, never in output, never in evidence).
"""

from __future__ import annotations

import hashlib
import os
import shutil
import subprocess
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from app.forge.canonical import EvidenceStatus, Layer, ObjectType, ProductExposure
from app.forge.persistence.records import (
    ArtifactRecord,
    CanonicalObjectRecord,
    CanonicalReference,
    ProvenanceEdgeRecord,
    VectorProjectionRecord,
)

DATABASE_URL = os.getenv("FORGE_TEST_DATABASE_URL", "")
RESTORE_DB = "forge_restore_smoke"

pytestmark = pytest.mark.skipif(
    not DATABASE_URL,
    reason="FORGE_TEST_DATABASE_URL not set — backup/restore smoke NOT EXECUTED locally (no CREATEDB, no local pgvector); executes on CI Postgres+pgvector",
)

EXPECTED_TABLES = {
    "forge_schema_migrations",
    "canonical_objects",
    "canonical_references",
    "artifacts",
    "provenance_edges",
    "forge_users",
    "external_identity_links",
    "forge_sessions",
    "retrieval_vectors",
    # GAP-05 durable audit/event ledger (Ch II.2.6): part of the backed-up
    # surface — content-minimized, append-oriented, no business columns.
    "forge_audit_events",
}
FORBIDDEN_BUSINESS_TABLES = {
    "policies",
    "policy_decisions",
    "entitlements",
    "licenses",
    "plans",
    "products",
    "subscriptions",
}


def _url_parts():
    from sqlalchemy.engine.url import make_url

    url = make_url(DATABASE_URL)
    return {
        "host": url.host or "127.0.0.1",
        "port": str(url.port or 5432),
        "user": url.username or "",
        "password": url.password or "",
        "database": url.database or "",
    }


def _run_client(binary: str, args: list[str], parts: dict[str, str]) -> str:
    """Run pg_dump/pg_restore with credentials in the environment only."""
    if shutil.which(binary) is None:
        pytest.fail(f"{binary} not available — the backup/restore smoke CANNOT execute")
    env = dict(os.environ)
    if parts["password"]:
        env["PGPASSWORD"] = parts["password"]
    result = subprocess.run(
        [binary, "-h", parts["host"], "-p", parts["port"], "-U", parts["user"], *args],
        env=env,
        capture_output=True,
        text=True,
        timeout=300,
    )
    output = (result.stdout or "") + (result.stderr or "")
    if parts["password"]:
        assert parts["password"] not in output, "credential leaked into output"
        assert parts["password"] not in " ".join(result.args), "credential leaked into argv"
    if result.returncode != 0:
        pytest.fail(f"{binary} failed (exit {result.returncode}): {output[:800]}")
    return output


def _connect(dbname: str):
    import psycopg2

    parts = _url_parts()
    return psycopg2.connect(
        host=parts["host"],
        port=parts["port"],
        user=parts["user"],
        password=parts["password"],
        dbname=dbname,
        connect_timeout=10,
    )


def _admin_connect():
    import psycopg2

    parts = _url_parts()
    conn = psycopg2.connect(
        host=parts["host"],
        port=parts["port"],
        user=parts["user"],
        password=parts["password"],
        dbname="postgres",
        connect_timeout=10,
    )
    conn.autocommit = True  # CREATE/DROP DATABASE cannot run in a transaction
    return conn


def _snapshot(dbname: str) -> dict:
    """Independent counts/hashes/head taken over the given database."""
    conn = _connect(dbname)
    try:
        cur = conn.cursor()
        cur.execute(
            "SELECT tablename FROM pg_tables WHERE schemaname = 'public' ORDER BY tablename"
        )
        tables = [row[0] for row in cur.fetchall()]
        counts: dict[str, int] = {}
        for table in tables:
            cur.execute(f'SELECT count(*) FROM "{table}"')
            counts[table] = cur.fetchone()[0]
        cur.execute(
            "SELECT content_hash FROM canonical_objects ORDER BY canonical_id"
        )
        hashes = [row[0] for row in cur.fetchall()]
        cur.execute("SELECT version FROM forge_schema_migrations ORDER BY version")
        head = [row[0] for row in cur.fetchall()]
        cur.execute(
            "SELECT object_id, embedding_dim, embedding_model, embedding_version,"
            " canonical_hash, exposure_class, owner_user_id FROM retrieval_vectors"
            " ORDER BY object_id"
        )
        vectors = [tuple(row) for row in cur.fetchall()]
        cur.execute("SELECT count(*) FROM pg_extension WHERE extname = 'vector'")
        has_vector = bool(cur.fetchone()[0])
        return {
            "tables": set(tables),
            "counts": counts,
            "hashes": hashes,
            "head": head,
            "vectors": vectors,
            "has_vector": has_vector,
        }
    finally:
        conn.close()


@pytest.fixture(scope="module")
def seeded_gateway():
    from sqlalchemy import create_engine, text

    from app.forge.identity import (
        ForgeSession,
        ForgeUser,
        new_forge_session_id,
        token_digest,
        utc_now_iso,
    )
    from app.forge.persistence.sql.gateway import SqlAlchemyPersistenceGateway

    engine = create_engine(DATABASE_URL)
    connection = engine.connect()
    gateway = SqlAlchemyPersistenceGateway(connection)
    gateway.apply_migrations()
    connection.commit()

    # deterministic fresh state (same pattern as the II.2 integration module)
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

    # -- seed: canonical objects + reference, artifact + provenance edge ----
    primary = CanonicalObjectRecord(
        canonical_id="MOD.EUR.BACKUP.V1",
        object_type=ObjectType.MODEL,
        title="backup smoke model",
        version="v1",
        status=EvidenceStatus.OBSERVED,
        exposure=ProductExposure.PUBLIC_TEACHING,
        layer=Layer.NONE,
        references=(
            CanonicalReference(
                target_id="MOD.EUR.BACKUP.SUPPORT.V1",
                relation="SUPPORTS",
                allow_unresolved_historical=False,
            ),
        ),
    )
    support = CanonicalObjectRecord(
        canonical_id="MOD.EUR.BACKUP.SUPPORT.V1",
        object_type=ObjectType.MODEL,
        title="backup smoke support",
        version="v1",
        status=EvidenceStatus.OBSERVED,
        exposure=ProductExposure.OPERATOR_ONLY,
        layer=Layer.NONE,
    )
    gateway.create_object(support)
    gateway.create_object(primary)
    artifact = ArtifactRecord(
        artifact_id="ART.BACKUP.SMOKE.V1",
        source_class="TEST_FIXTURE",
        title="backup smoke artifact",
        source_generation="gen-1",
        version="v1",
        locator="tests/test_forge_backup_restore.py",
        content_identity="sha256:" + hashlib.sha256(b"backup-smoke").hexdigest(),
        source_state="LOCATED",
        metadata={},
    )
    gateway.create_artifact(artifact)
    gateway.add_provenance_edge(
        ProvenanceEdgeRecord(
            artifact_id=artifact.artifact_id,
            object_id=primary.canonical_id,
            relation="SUPPORTS",
            note="backup smoke provenance",
        )
    )

    # -- identity/session data -------------------------------------------------
    user = ForgeUser.create(user_id="backup-smoke-user")
    gateway.create_user(user)
    session = ForgeSession(
        session_id=new_forge_session_id(),
        user_id=user.user_id,
        token_digest=token_digest("backup-restore-smoke-token"),
        expires_at=utc_now_iso(datetime.now(timezone.utc) + timedelta(days=1)),
    )
    gateway.create_session(session)

    # -- vector projection row (Ch II.2.4) ------------------------------------
    projection = VectorProjectionRecord(
        object_id=primary.canonical_id,
        object_version=primary.version,
        payload_json='{"smoke": "backup"}',
        semantic_text="synthetic safe semantic text",
        embedding=(0.5, 0.25, 0.75, 1.0),
        embedding_dim=4,
        embedding_model="synthetic-embed",
        embedding_version="syn-1",
        exposure_class=primary.exposure,
        canonical_hash=primary.to_domain().content_hash(),
        owner_user_id=None,
    )
    gateway.put_vector_projection(projection)
    connection.commit()  # everything above MUST be committed before pg_dump

    yield gateway

    connection.close()


class TestBackupRestoreSmoke:
    def test_backup_restore_roundtrip_verified_independently(
        self, seeded_gateway
    ) -> None:
        connection = seeded_gateway._connection

        connection.commit()  # end any read transaction before dumping
        source_before = _snapshot(_url_parts()["database"])

        # -------- dump ------------------------------------------------------
        parts = _url_parts()
        with tempfile.TemporaryDirectory(prefix="forge_backup_") as tmp:
            dump_file = Path(tmp) / "forge_dump.dump"
            _run_client("pg_dump", ["-Fc", "-d", parts["database"], "-f", str(dump_file)], parts)
            assert dump_file.exists() and dump_file.stat().st_size > 0

            # -------- restore into a fresh, isolated database ---------------
            admin = _admin_connect()
            try:
                admin.cursor().execute(f'DROP DATABASE IF EXISTS "{RESTORE_DB}"')
                admin.cursor().execute(f'CREATE DATABASE "{RESTORE_DB}"')
            finally:
                admin.close()

            try:
                _run_client(
                    "pg_restore",
                    ["--exit-on-error", "--no-owner", "--no-privileges",
                     "-d", RESTORE_DB, str(dump_file)],
                    parts,
                )

                # -------- verify ONLY the restored database -----------------
                restored = _snapshot(RESTORE_DB)
                assert restored["has_vector"], "extension missing after restore"
                assert EXPECTED_TABLES <= restored["tables"]
                assert restored["counts"] == source_before["counts"]
                assert restored["hashes"] == source_before["hashes"]
                assert restored["head"] == [1, 2, 3, 4]
                assert restored["vectors"] == source_before["vectors"]

                # projection <-> canonical reconciliation in the restored DB
                verify = _connect(RESTORE_DB)
                try:
                    cur = verify.cursor()
                    cur.execute(
                        "SELECT count(*) FROM retrieval_vectors v"
                        " JOIN canonical_objects c ON c.canonical_id = v.object_id"
                        " WHERE v.canonical_hash <> c.content_hash"
                        " OR v.exposure_class <> c.exposure"
                        " OR v.object_version <> c.version"
                    )
                    assert cur.fetchone()[0] == 0, "restored projection diverges"
                    cur.execute(
                        "SELECT embedding_dim, vector_dims(embedding) FROM retrieval_vectors"
                    )
                    for declared, actual in cur.fetchall():
                        assert declared == actual
                    cur.execute(
                        "SELECT tablename FROM pg_tables WHERE schemaname = 'public'"
                    )
                    restored_tables = {row[0] for row in cur.fetchall()}
                    # policy/commerce state has no tables BY DESIGN (II.2/II.4):
                    # there is no policy truth to back up in Book II.
                    assert not (restored_tables & FORBIDDEN_BUSINESS_TABLES)
                finally:
                    verify.close()

                # migration re-apply on the restored DB is a no-op (E4)
                from sqlalchemy import create_engine
                from sqlalchemy.engine.url import URL

                from app.forge.persistence.sql.gateway import SqlAlchemyPersistenceGateway

                restored_url = URL.create(
                    "postgresql+psycopg2",
                    username=parts["user"],
                    password=parts["password"],
                    host=parts["host"],
                    port=int(parts["port"]),
                    database=RESTORE_DB,
                )
                restored_engine = create_engine(restored_url)
                restored_connection = restored_engine.connect()
                try:
                    restored_gateway = SqlAlchemyPersistenceGateway(restored_connection)
                    assert restored_gateway.check_compatibility() == "OK"
                    assert restored_gateway.apply_migrations() == "CURRENT"
                finally:
                    restored_connection.close()
                    restored_engine.dispose()
            finally:
                admin = _admin_connect()
                try:
                    admin.cursor().execute(f'DROP DATABASE IF EXISTS "{RESTORE_DB}"')
                finally:
                    admin.close()

        # -------- source untouched by the round trip -------------------------
        source_after = _snapshot(parts["database"])
        assert source_after["counts"] == source_before["counts"]
        assert source_after["hashes"] == source_before["hashes"]
        assert source_after["head"] == source_before["head"]
        assert source_after["vectors"] == source_before["vectors"]
        assert "retrieval_vectors" in source_after["tables"]

        # sanity: the seeded data itself is real (not an empty-database pass)
        assert source_before["counts"]["canonical_objects"] >= 2
        assert source_before["counts"]["forge_users"] >= 1
        assert source_before["counts"]["forge_sessions"] >= 1
        assert source_before["counts"]["provenance_edges"] >= 1
        assert len(source_before["vectors"]) >= 1
