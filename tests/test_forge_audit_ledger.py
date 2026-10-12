"""GAP-05 durable audit/event ledger — Book II frozen Ch II.2.6.

Executed evidence for the Build Agent #14 packet (plan+acceptance committed
first: implementation/forge/book_ii/closure_repair_gap05/). Covers:

- migration 004 schema contract on SQLite (dialect truth) and, gated on
  `FORGE_TEST_DATABASE_URL`, on real PostgreSQL (CI postgres job);
- write/read round trip through the five Ch II.2.6 observation seams
  (policy decisions, protected retrieval access, entitlement change
  records, provider usage events, authentication/security events);
- bounded caches, append-only order, idempotent event_id;
- redaction-before-storage (no secrets or corpus content in the store);
- failure injection + recovery evidence (missing table, closed connection,
  best_effort containment vs require_durable typed failure, restart
  survival on a file database);
- composition fail-closed config and the frozen container seam;
- architecture guards: persistence never imports observability, no Book VI
  business tables, durable streams stay inside the frozen STREAMS
  vocabulary.

Nothing here ratifies or freezes Book II.
"""

from __future__ import annotations

import ast
import json
import os
import uuid
from pathlib import Path
from types import SimpleNamespace

import pytest

from app.forge.config import AuditDurableConfig, ForgeConfig
from app.forge.observability.audit_ledger import (
    AUTHENTICATION_EVENT_TYPES,
    AUDIT_WRITE_POLICIES,
    DurableAuditLedger,
    DurableAuditWriteError,
)
from app.forge.observability.events import OUTCOMES, STREAMS
from app.forge.observability.service import (
    ForgeObservabilityService,
    observability_from_config,
)
from app.forge.persistence.records import AuditEventRecord
from app.forge.service.policy_enforcement import PolicyAuditRecord

SQLA_AVAILABLE = True
try:
    from sqlalchemy import create_engine, text
except Exception:  # pragma: no cover - environment guard
    SQLA_AVAILABLE = False

pytestmark = pytest.mark.skipif(not SQLA_AVAILABLE, reason="SQLAlchemy not installed")

PG_URL = os.getenv("FORGE_TEST_DATABASE_URL", "")

_EXPECTED_SQLITE_TABLES = {
    "forge_schema_migrations",
    "canonical_objects",
    "canonical_references",
    "artifacts",
    "provenance_edges",
    "forge_users",
    "external_identity_links",
    "forge_sessions",
    "forge_audit_events",
}

# Book VI authority (GOVERNANCE §2): never created by Book II.
_FORBIDDEN_BUSINESS_TABLES = {
    "entitlements",
    "licenses",
    "plans",
    "products",
    "subscriptions",
    "policies",
    "policy_decisions",
}


def _policy_record(allowed: bool, *, at: str = "2026-10-12T00:00:00+00:00"):
    return PolicyAuditRecord(
        correlation_id="req-policy",
        principal_id="user-1",
        authenticated=True,
        action="read",
        resource_type="CANONICAL",
        resource_id="MOD.TEST.AUDIT",
        exposure="INTERNAL",
        allowed=allowed,
        reason_code="MATCH" if allowed else "NO_MATCH",
        at=at,
    )


def _durable_config(**overrides) -> AuditDurableConfig:
    base = {"enabled": True, "database_url": "sqlite://"}
    base.update(overrides)
    return AuditDurableConfig(**base)


@pytest.fixture()
def env():
    """In-memory SQLite gateway + observability service with durable ledger."""

    engine = create_engine("sqlite://")
    connection = engine.connect()
    from app.forge.persistence.sql.gateway import SqlAlchemyPersistenceGateway

    gateway = SqlAlchemyPersistenceGateway(connection)
    assert gateway.apply_migrations() == "APPLIED"
    connection.commit()  # clean transaction state for later explicit BEGINs
    config = ForgeConfig(
        environment="test",
        observability_log_sinks=False,
        audit_durable=_durable_config(),
    )
    service = observability_from_config(config, persistence=gateway)
    yield SimpleNamespace(
        engine=engine, connection=connection, gateway=gateway, service=service
    )
    engine.dispose()


@pytest.fixture()
def plain_service():
    """Unwired service: pre-GAP-05 behavior must be byte-identical."""

    return observability_from_config(
        ForgeConfig(environment="test", observability_log_sinks=False)
    )


def _drop_audit_schema(gateway, connection) -> None:
    """Simulate a backend that lost the ledger schema (fault injection)."""

    connection.execute(text("DROP TABLE forge_audit_events"))
    connection.execute(
        text("DELETE FROM forge_schema_migrations WHERE version = 4")
    )
    connection.commit()


# ---------------------------------------------------------------------------
# A — migration 004 schema contract (SQLite dialect truth)
# ---------------------------------------------------------------------------


@pytest.mark.skipif(not SQLA_AVAILABLE, reason="SQLAlchemy not installed")
class TestMigration004Schema:
    def test_discover_includes_portable_004(self) -> None:
        from app.forge.persistence.sql.migrations import discover_migrations

        migrations = {m.version: m for m in discover_migrations()}
        assert [m.version for m in migrations.values()] == [1, 2, 3, 4]
        assert migrations[4].identity == "004_audit_ledger"
        assert migrations[4].postgresql_only is False

    def test_fresh_sqlite_schema_exact_table_set(self) -> None:
        engine = create_engine("sqlite://")
        connection = engine.connect()
        from app.forge.persistence.sql.gateway import SqlAlchemyPersistenceGateway

        gateway = SqlAlchemyPersistenceGateway(connection)
        gateway.apply_migrations()
        tables = {
            row[0]
            for row in connection.execute(
                text("SELECT name FROM sqlite_master WHERE type='table'")
            )
        }
        assert tables == _EXPECTED_SQLITE_TABLES
        assert not (tables & _FORBIDDEN_BUSINESS_TABLES)
        engine.dispose()

    def test_columns_not_null_and_uniqueness(self) -> None:
        engine = create_engine("sqlite://")
        connection = engine.connect()
        from app.forge.persistence.sql.gateway import SqlAlchemyPersistenceGateway

        gateway = SqlAlchemyPersistenceGateway(connection)
        gateway.apply_migrations()
        columns = {
            row[1]: (row[2], bool(row[3]), bool(row[5]))  # (type, notnull, pk)
            for row in connection.execute(text("PRAGMA table_info(forge_audit_events)"))
        }
        # required columns present
        for name in (
            "seq",
            "event_id",
            "stream",
            "event_type",
            "severity",
            "environment",
            "occurred_at",
            "request_id",
            "actor_type",
            "actor_id",
            "resource",
            "outcome",
            "reason",
            "details_json",
            "created_at",
        ):
            assert name in columns, name
        for required in (
            "seq",
            "event_id",
            "stream",
            "event_type",
            "severity",
            "occurred_at",
            "actor_type",
            "outcome",
            "details_json",
            "created_at",
        ):
            assert columns[required][1] is True, f"{required} must be NOT NULL"
        assert columns["seq"][2] is True  # PRIMARY KEY (seq)
        # UNIQUE(event_id) via unique index
        unique_indexes = {
            row[1]
            for row in connection.execute(
                text("PRAGMA index_list(forge_audit_events)")
            )
            if bool(row[2])
        }
        index_columns = set()
        for name in unique_indexes:
            index_columns.update(
                row[2]
                for row in connection.execute(text(f'PRAGMA index_info("{name}")'))
            )
        assert "event_id" in index_columns
        # the four helpful indexes exist
        index_names = {
            row[0]
            for row in connection.execute(
                text(
                    "SELECT name FROM sqlite_master WHERE type='index'"
                    " AND tbl_name='forge_audit_events'"
                )
            )
        }
        for expected in (
            "idx_forge_audit_events_stream_time",
            "idx_forge_audit_events_type_time",
            "idx_forge_audit_events_request",
            "idx_forge_audit_events_actor",
        ):
            assert expected in index_names, expected
        engine.dispose()

    def test_legacy_environment_behind_then_ok(self) -> None:
        """Pre-004 database: BEHIND -> apply -> OK (forward-only, no AHEAD)."""

        engine = create_engine("sqlite://")
        connection = engine.connect()
        from app.forge.persistence.sql.gateway import SqlAlchemyPersistenceGateway

        gateway = SqlAlchemyPersistenceGateway(connection)
        gateway.apply_migrations()
        connection.execute(text("DROP TABLE forge_audit_events"))
        connection.execute(
            text("DELETE FROM forge_schema_migrations WHERE version = 4")
        )
        connection.commit()
        assert gateway.check_compatibility() == "BEHIND"
        assert gateway.apply_migrations() == "APPLIED"
        assert gateway.check_compatibility() == "OK"
        assert gateway.apply_migrations() == "CURRENT"
        engine.dispose()

    def test_migration_runner_import_runs_nothing(self) -> None:
        import app.main  # noqa: F401  (import must stay side-effect free)

        from app.main import _build_forge_container

        container = _build_forge_container()
        assert container.persistence is None
        if container.observability is not None:
            assert container.observability.audit_ledger is None


# ---------------------------------------------------------------------------
# B — durable round trip through the Ch II.2.6 observation seams
# ---------------------------------------------------------------------------


class TestDurableRoundTrip:
    def test_policy_decision_rows(self, env) -> None:
        env.service.record_policy_decision(_policy_record(allowed=False))
        env.service.record_policy_decision(_policy_record(allowed=True))
        rows = env.service.durable_audit_events()
        assert [r.event_type for r in rows] == ["policy.deny", "policy.allow"]
        assert all(r.stream == "security_audit" for r in rows)
        deny = rows[0]
        assert deny.severity == "WARNING"
        assert deny.outcome == "denied"
        assert deny.reason == "NO_MATCH"
        assert deny.request_id == "req-policy"
        assert deny.resource == "CANONICAL:MOD.TEST.AUDIT"
        assert deny.actor_id == "user-1"
        # the FACT time (caller-supplied policy record) wins over the clock
        assert deny.occurred_at == "2026-10-12T00:00:00+00:00"
        assert json.loads(deny.details_json) == {"authenticated": True}
        assert deny.seq is not None and deny.created_at

    def test_retrieval_access_row(self, env) -> None:
        env.service.record_retrieval_access(
            principal_id="user-1",
            service="retrieval",
            capability="read",
            canonical_object_ids=("MOD.A", "MOD.B"),
            retrieval_object_ids=("RET.1",),
            exposure="INTERNAL",
            decision="ALLOW",
            correlation_id="req-ret",
            at="2026-10-12T00:01:00+00:00",
        )
        env.service.record_retrieval_access(
            principal_id="anonymous",
            service="retrieval",
            capability="read",
            exposure="RESTRICTED",
            decision="DENY",
            correlation_id="req-ret-2",
        )
        rows = env.service.durable_audit_events()
        assert [r.event_type for r in rows] == ["retrieval.access", "retrieval.access"]
        allow, deny = rows
        assert allow.stream == "security_audit"
        assert allow.outcome == "success"
        assert allow.resource == "INTERNAL"
        details = json.loads(allow.details_json)
        assert details["canonical_object_ids"] == "MOD.A, MOD.B"
        assert details["retrieval_object_ids"] == "RET.1"
        assert deny.outcome == "denied"
        assert deny.actor_id == "anonymous"

    def test_entitlement_record_row(self, env) -> None:
        env.service.record_entitlement_event(
            event_type="grant",
            principal_id="user-1",
            entitlement_id="ent-9",
            source_event_id="src-1",
            provider_type="whop",
            provider_name="fake",
            correlation_id="req-ent",
            at="2026-10-12T00:02:00+00:00",
        )
        row = env.service.durable_audit_events()[0]
        assert row.stream == "entitlement_audit"
        assert row.event_type == "entitlement.grant"
        assert row.resource == "ent-9"
        assert row.outcome == "recorded"
        details = json.loads(row.details_json)
        assert details["source_event_id"] == "src-1"
        assert details["provider_name"] == "fake"

    def test_provider_usage_row(self, env) -> None:
        env.service.record_usage(
            provider_type="llm",
            provider_name="fake",
            model_id="model-1",
            input_tokens=11,
            output_tokens=7,
            normalized_cost=0.01,
            latency_ms=42.0,
            success=True,
        )
        row = env.service.durable_audit_events()[0]
        assert row.stream == "usage_ledger"
        assert row.event_type == "provider.usage"
        assert row.resource == "llm:fake"
        details = json.loads(row.details_json)
        assert details["input_tokens"] == 11
        assert details["output_tokens"] == 7
        assert details["model_id"] == "model-1"

    def test_authentication_events_all_vocabulary_members(self, env) -> None:
        for index, event_type in enumerate(AUTHENTICATION_EVENT_TYPES):
            ok = env.service.record_authentication_event(
                event_type=event_type,
                actor_id="user-1",
                resource=f"sess-{index}",
                reason="test",
                at=f"2026-10-12T00:0{index}:00+00:00",
            )
            assert ok is True
        rows = env.service.durable_audit_events()
        assert [r.event_type for r in rows] == list(AUTHENTICATION_EVENT_TYPES)
        assert all(r.stream == "security_audit" for r in rows)

    def test_authentication_vocabulary_and_outcome_fail_closed(self, env) -> None:
        with pytest.raises(ValueError):
            env.service.record_authentication_event(event_type="made_up_event")
        with pytest.raises(ValueError):
            env.service.record_authentication_event(
                event_type="session_opened", outcome="kinda"
            )
        assert env.service.durable_audit_events() == ()

    def test_seq_monotonic_event_ids_unique(self, env) -> None:
        for index in range(5):
            env.service.record_authentication_event(
                event_type="session_opened", resource=f"s-{index}"
            )
        rows = env.service.durable_audit_events()
        seqs = [r.seq for r in rows]
        assert seqs == sorted(seqs)
        assert len(set(seqs)) == 5
        assert len({r.event_id for r in rows}) == 5
        for row in rows:
            uuid.UUID(row.event_id)  # RFC 4122 form fits VARCHAR(36)

    def test_recorded_before_readable(self, env) -> None:
        """GAP-03 seam semantics: an observed fact is readable once written."""

        before = len(env.service.durable_audit_events())
        env.service.record_authentication_event(
            event_type="session_revoked",
            actor_id="user-1",
            resource="sess-rev",
            at="2026-10-12T00:03:00+00:00",
        )
        rows = env.service.durable_audit_events()
        assert len(rows) == before + 1
        assert rows[-1].resource == "sess-rev"
        assert rows[-1].occurred_at == "2026-10-12T00:03:00+00:00"

    def test_duplicate_event_id_is_idempotent(self, env) -> None:
        record = AuditEventRecord(
            event_id=str(uuid.uuid4()),
            stream="security_audit",
            event_type="session_opened",
            severity="INFO",
            occurred_at="2026-10-12T00:04:00+00:00",
        )
        assert env.gateway.append_audit_event(record) is True
        assert env.gateway.append_audit_event(record) is False
        rows = env.gateway.list_audit_events()
        assert len(rows) == 1
        assert rows[0].seq == 1

    def test_list_is_bounded_filtered_and_ordered(self, env) -> None:
        for index in range(4):
            env.service.record_authentication_event(
                event_type="session_opened", resource=f"n-{index}"
            )
        env.service.record_policy_decision(_policy_record(allowed=False))
        assert len(env.gateway.list_audit_events(limit=2)) == 2
        ordered = env.gateway.list_audit_events(limit=100)
        assert [r.seq for r in ordered] == sorted(r.seq for r in ordered)
        policy_only = env.gateway.list_audit_events(
            limit=100, stream="security_audit"
        )
        # both seams write security_audit; filter by event_type instead
        assert all(r.stream == "security_audit" for r in policy_only)
        entitlement = env.gateway.list_audit_events(
            limit=100, stream="entitlement_audit"
        )
        assert entitlement == ()

    def test_unwired_service_behavior_unchanged(self, plain_service) -> None:
        assert plain_service.audit_ledger is None
        assert "durable_audit" not in plain_service.snapshot()
        assert plain_service.durable_audit_events() == ()
        # every mirror is a no-op, never an exception, when unwired
        plain_service.record_policy_decision(_policy_record(allowed=False))
        plain_service.record_retrieval_access(
            principal_id="user-1",
            service="retrieval",
            capability="read",
            decision="ALLOW",
        )
        plain_service.record_entitlement_event(
            event_type="revoke", principal_id="user-1", entitlement_id="ent-1"
        )
        plain_service.record_usage(provider_type="llm", provider_name="fake")
        assert plain_service.record_authentication_event(
            event_type="session_opened"
        ) is None

    def test_append_inside_explicit_transaction(self, env) -> None:
        with env.gateway.transaction():
            env.gateway.append_audit_event(
                AuditEventRecord(
                    event_id=str(uuid.uuid4()),
                    stream="security_audit",
                    event_type="session_opened",
                    severity="INFO",
                    occurred_at="2026-10-12T00:05:00+00:00",
                )
            )
        rows = env.gateway.list_audit_events()
        assert len(rows) == 1


# ---------------------------------------------------------------------------
# C — bounded caches (append-only, oldest evicted)
# ---------------------------------------------------------------------------


class TestBoundedBehavior:
    def test_cache_bounded_fifo_store_append_only(self, env) -> None:
        ledger = DurableAuditLedger(env.gateway, capacity=3, environment="test")
        for index in range(5):
            ledger.append_event(
                stream="security_audit",
                event_type="session_opened",
                resource=f"b-{index}",
            )
        cached = ledger.records()
        assert len(cached) == 3
        assert [c.resource for c in cached] == ["b-2", "b-3", "b-4"]
        # the durable store kept every append (append-oriented)
        assert len(env.gateway.list_audit_events(limit=100)) == 5
        assert ledger.snapshot()["durable_appends"] == 5

    def test_fallback_trail_bounded_with_totals(self) -> None:
        broken = SimpleNamespace(
            append_audit_event=lambda record: (_ for _ in ()).throw(
                RuntimeError("backend_down")
            ),
            list_audit_events=lambda **kwargs: (),
        )
        ledger = DurableAuditLedger(broken, capacity=3, environment="test")
        for _ in range(5):
            assert ledger.append_event(
                stream="security_audit", event_type="session_opened"
            ) is False
        assert len(ledger.fallbacks()) == 3
        snapshot = ledger.snapshot()
        assert snapshot["fallback_appends"] == 5
        assert snapshot["status"] == "NOT_OK"
        assert snapshot["last_error_kind"] == "RuntimeError"

    def test_capacity_and_policy_validation(self, env) -> None:
        with pytest.raises(ValueError):
            DurableAuditLedger(env.gateway, capacity=0)
        with pytest.raises(ValueError):
            DurableAuditLedger(env.gateway, write_policy="whatever")
        with pytest.raises(ValueError):
            DurableAuditLedger(None)
        assert set(AUDIT_WRITE_POLICIES) == {"best_effort", "require_durable"}


# ---------------------------------------------------------------------------
# D — redaction before storage (Ch II.2.6: no secrets, no corpus content)
# ---------------------------------------------------------------------------


class TestRedactionBeforeStorage:
    _SECRET_FRAGMENTS = (
        "sk-abcdef1234567890",
        "supersecretvalue1234567890",
        "hunter2hunter2hunter2hunter2hunter2hunter2",
    )

    def test_secrets_never_reach_the_store(self, env) -> None:
        env.service.record_authentication_event(
            event_type="authentication_failed",
            outcome="failure",
            reason="unknown_credential",
            resource="sk-abcdef1234567890",
            details={
                "note": "token=supersecretvalue1234567890",
                "header": "Bearer abcdefghijklmnopqrstuvwx",
                "opaque": "hunter2hunter2hunter2hunter2hunter2hunter2",
            },
        )
        row = env.service.durable_audit_events()[0]
        blob = " ".join(
            [
                row.details_json,
                row.reason,
                row.resource,
                row.actor_id or "",
                row.request_id or "",
            ]
        )
        for fragment in self._SECRET_FRAGMENTS:
            assert fragment not in blob
        assert "[redacted]" in blob

    def test_non_scalar_details_collapsed_not_dumped(self, env) -> None:
        env.service.record_authentication_event(
            event_type="session_opened",
            details={"payload": {"body": "protected corpus content"}},
        )
        row = env.service.durable_audit_events()[0]
        details = json.loads(row.details_json)
        assert details == {"_details": "details_rejected_not_scalar_or_too_many"}
        assert "protected corpus content" not in row.details_json

    def test_attribute_overflow_collapsed(self, env) -> None:
        env.service.record_authentication_event(
            event_type="session_opened",
            details={f"k{index}": index for index in range(17)},
        )
        row = env.service.durable_audit_events()[0]
        assert json.loads(row.details_json) == {
            "_details": "details_rejected_not_scalar_or_too_many"
        }

    def test_oversized_value_omitted_entirely(self, env) -> None:
        long_value = "PROTECTED CORPUS LINE " * 30  # > 256 chars, not secret-shaped
        env.service.record_authentication_event(
            event_type="session_opened", details={"body": long_value}
        )
        row = env.service.durable_audit_events()[0]
        details = json.loads(row.details_json)
        assert details["body"].startswith("[truncated]")
        assert "PROTECTED CORPUS LINE" not in details["body"]

    def test_secret_scrub_wins_before_bound(self, env) -> None:
        """A secret-shaped run is scrubbed even when it is also oversized."""

        long_secret = "PROTECTED-CORPUS-LINE-" * 40  # one 40+ base64url run
        env.service.record_authentication_event(
            event_type="session_opened", details={"body": long_secret}
        )
        row = env.service.durable_audit_events()[0]
        details = json.loads(row.details_json)
        assert details["body"] == "[redacted]"
        assert "PROTECTED-CORPUS-LINE" not in row.details_json


# ---------------------------------------------------------------------------
# E — failure injection + recovery evidence
# ---------------------------------------------------------------------------


class TestFailureInjection:
    def test_missing_table_contained_then_recovered(self, env) -> None:
        _drop_audit_schema(env.gateway, env.connection)
        result = env.service.record_authentication_event(
            event_type="session_opened", resource="fault-1"
        )
        assert result is False
        snapshot = env.service.snapshot()["durable_audit"]
        assert snapshot["status"] == "NOT_OK"
        assert snapshot["fallback_appends"] == 1
        assert snapshot["last_error_kind"]  # redacted cause, class-name only
        fallbacks = env.service.audit_ledger.fallbacks()
        assert len(fallbacks) == 1
        assert fallbacks[0].event_type == "session_opened"
        assert fallbacks[0].stream == "security_audit"
        # recovery: re-apply migration, ledger returns to OK
        assert env.gateway.apply_migrations() == "APPLIED"
        assert env.gateway.check_compatibility() == "OK"
        recovered = env.service.record_authentication_event(
            event_type="session_opened", resource="fault-2"
        )
        assert recovered is True
        assert env.service.snapshot()["durable_audit"]["status"] == "OK"
        rows = env.service.durable_audit_events()
        assert [r.resource for r in rows] == ["fault-2"]

    def test_closed_connection_contained(self, env) -> None:
        env.connection.close()
        result = env.service.record_authentication_event(
            event_type="session_opened"
        )
        assert result is False
        snapshot = env.service.snapshot()["durable_audit"]
        assert snapshot["status"] == "NOT_OK"
        assert snapshot["fallback_appends"] == 1

    def test_require_durable_raises_typed_error(self, env) -> None:
        strict_config = ForgeConfig(
            environment="test",
            observability_log_sinks=False,
            audit_durable=_durable_config(write_policy="require_durable"),
        )
        strict = observability_from_config(strict_config, persistence=env.gateway)
        _drop_audit_schema(env.gateway, env.connection)
        with pytest.raises(DurableAuditWriteError) as excinfo:
            strict.record_authentication_event(event_type="session_opened")
        assert excinfo.value.kind  # redacted token only
        assert "sqlite" not in str(excinfo.value).lower()
        # restore schema so fixture teardown stays coherent
        assert env.gateway.apply_migrations() == "APPLIED"

    def test_memory_gateway_parity_and_fault(self) -> None:
        from app.forge.persistence.memory import InMemoryPersistenceGateway

        memory = InMemoryPersistenceGateway()
        ledger = DurableAuditLedger(memory, environment="test")
        assert (
            ledger.append_event(
                stream="security_audit",
                event_type="policy.deny",
                details={"authenticated": False},
            )
            is True
        )
        # idempotent read-back parity with SQL: bounded, ordered
        rows = memory.list_audit_events()
        assert len(rows) == 1 and rows[0].seq == 1

        broken = InMemoryPersistenceGateway(simulate_unavailable=True)
        faulty = DurableAuditLedger(broken, environment="test")
        assert (
            faulty.append_event(
                stream="security_audit", event_type="policy.deny"
            )
            is False
        )
        assert faulty.snapshot()["status"] == "NOT_OK"
        assert faulty.snapshot()["last_error_kind"]

    def test_config_fail_closed_matrix(self, monkeypatch) -> None:
        with pytest.raises(ValueError):
            AuditDurableConfig(enabled=True)  # no URL
        with pytest.raises(ValueError):
            AuditDurableConfig(enabled=True, database_url="sqlite://", capacity=0)
        with pytest.raises(ValueError):
            AuditDurableConfig(
                enabled=True, database_url="sqlite://", write_policy="nope"
            )
        with pytest.raises(ValueError):
            AuditDurableConfig(write_policy="require_durable")  # not enabled
        with pytest.raises(ValueError):
            ForgeConfig(
                observability_enabled=False,
                audit_durable=_durable_config(),
            )
        # env-driven: enabled without any URL fails closed at config build
        monkeypatch.setenv("FORGE_AUDIT_DURABLE_ENABLED", "1")
        monkeypatch.delenv("FORGE_AUDIT_DURABLE_URL", raising=False)
        monkeypatch.delenv("FORGE_DATABASE_URL", raising=False)
        from app.forge.config import forge_config_from_environment

        with pytest.raises(ValueError):
            forge_config_from_environment()
        # factory: enabled without a persistence port fails closed
        monkeypatch.delenv("FORGE_AUDIT_DURABLE_ENABLED", raising=False)
        enabled = ForgeConfig(audit_durable=_durable_config())
        with pytest.raises(ValueError):
            observability_from_config(enabled, persistence=None)


# ---------------------------------------------------------------------------
# F — restart recovery (durability evidence on a file database)
# ---------------------------------------------------------------------------


class TestRestartRecovery:
    def test_rows_survive_process_restart(self, tmp_path) -> None:
        path = tmp_path / "audit_restart.db"
        url = f"sqlite:///{path}"
        from app.forge.persistence.sql.gateway import SqlAlchemyPersistenceGateway

        engine_one = create_engine(url)
        conn_one = engine_one.connect()
        gw_one = SqlAlchemyPersistenceGateway(conn_one)
        assert gw_one.apply_migrations() == "APPLIED"
        service_one = observability_from_config(
            ForgeConfig(
                environment="test",
                observability_log_sinks=False,
                audit_durable=_durable_config(database_url=url),
            ),
            persistence=gw_one,
        )
        assert service_one.record_authentication_event(
            event_type="session_revoked",
            actor_id="user-1",
            resource="restart-proof",
            details={"count": 1},
            at="2026-10-12T00:10:00+00:00",
        ) is True
        original = service_one.durable_audit_events()[0]
        engine_one.dispose()  # process death

        engine_two = create_engine(url)
        conn_two = engine_two.connect()
        gw_two = SqlAlchemyPersistenceGateway(conn_two)
        assert gw_two.apply_migrations() == "CURRENT"  # replay is a no-op
        assert gw_two.check_compatibility() == "OK"
        rows = gw_two.list_audit_events()
        assert len(rows) == 1
        survived = rows[0]
        assert survived.event_id == original.event_id
        assert survived.seq == original.seq == 1
        assert survived.resource == "restart-proof"
        assert survived.occurred_at == "2026-10-12T00:10:00+00:00"
        # next append after restart continues the sequence
        service_two = observability_from_config(
            ForgeConfig(
                environment="test",
                observability_log_sinks=False,
                audit_durable=_durable_config(database_url=url),
            ),
            persistence=gw_two,
        )
        assert service_two.record_authentication_event(
            event_type="session_opened", resource="after-restart"
        ) is True
        assert gw_two.list_audit_events()[1].seq == 2
        engine_two.dispose()

    def test_migration_fault_then_reopen_recovers(self, tmp_path) -> None:
        """Partial-schema fault across a restart: apply repairs, write resumes."""

        path = tmp_path / "audit_fault.db"
        url = f"sqlite:///{path}"
        from app.forge.persistence.sql.gateway import SqlAlchemyPersistenceGateway

        engine_one = create_engine(url)
        conn_one = engine_one.connect()
        gw_one = SqlAlchemyPersistenceGateway(conn_one)
        gw_one.apply_migrations()
        conn_one.execute(text("DROP TABLE forge_audit_events"))
        conn_one.execute(text("DELETE FROM forge_schema_migrations WHERE version = 4"))
        conn_one.commit()
        engine_one.dispose()

        engine_two = create_engine(url)
        conn_two = engine_two.connect()
        gw_two = SqlAlchemyPersistenceGateway(conn_two)
        assert gw_two.check_compatibility() == "BEHIND"
        assert gw_two.apply_migrations() == "APPLIED"
        assert gw_two.check_compatibility() == "OK"
        assert gw_two.append_audit_event(
            AuditEventRecord(
                event_id=str(uuid.uuid4()),
                stream="security_audit",
                event_type="session_opened",
                severity="INFO",
                occurred_at="2026-10-12T00:11:00+00:00",
            )
        ) is True
        assert len(gw_two.list_audit_events()) == 1
        engine_two.dispose()


# ---------------------------------------------------------------------------
# G — architecture guards (security isolation / authority separation)
# ---------------------------------------------------------------------------

_REPO_ROOT = Path(__file__).resolve().parents[1]


def _imports_of(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            names.add(node.module)
    return names


class TestArchitectureGuards:
    def test_persistence_never_imports_observability(self) -> None:
        """Dependency direction: observability -> persistence, never back.

        This is what makes failure containment possible: a SQL fault cannot
        recurse through observability, because the failover sink lives on
        the observability side of the boundary.
        """

        root = _REPO_ROOT / "app" / "forge" / "persistence"
        offenders = []
        for path in sorted(root.rglob("*.py")):
            imports = _imports_of(path)
            for name in imports:
                if name == "app.forge.observability" or name.startswith(
                    "app.forge.observability."
                ):
                    offenders.append((str(path), name))
        assert offenders == []

    def test_domain_modules_never_import_audit_ledger(self) -> None:
        """Book I domain + Book VI authority surfaces stay ledger-free."""

        forbidden_prefixes = (
            "app/forge/canonical.py",
            "app/forge/schemas.py",
            "app/forge/provenance.py",
            "app/forge/policy.py",
            "app/forge/identity.py",
            "app/forge/qa/",
            "app/forge/backfill/",
            "app/forge/retrieval/",
            "app/forge/providers/",
        )
        offenders = []
        forge_root = _REPO_ROOT / "app" / "forge"
        for path in sorted(forge_root.rglob("*.py")):
            rel = str(path.relative_to(_REPO_ROOT)).replace(os.sep, "/")
            if not any(rel.startswith(prefix) for prefix in forbidden_prefixes):
                continue
            if "audit_ledger" in _imports_of(path):
                offenders.append(rel)
        assert offenders == []

    def test_no_book_vi_business_tables_created(self) -> None:
        engine = create_engine("sqlite://")
        connection = engine.connect()
        from app.forge.persistence.sql.gateway import SqlAlchemyPersistenceGateway

        gateway = SqlAlchemyPersistenceGateway(connection)
        gateway.apply_migrations()
        tables = {
            row[0]
            for row in connection.execute(
                text("SELECT name FROM sqlite_master WHERE type='table'")
            )
        }
        assert not (tables & _FORBIDDEN_BUSINESS_TABLES)
        engine.dispose()

    def test_durable_streams_stay_in_frozen_vocabulary(self, env) -> None:
        env.service.record_policy_decision(_policy_record(allowed=False))
        env.service.record_retrieval_access(
            principal_id="user-1",
            service="retrieval",
            capability="read",
            decision="ALLOW",
        )
        env.service.record_entitlement_event(
            event_type="grant", principal_id="user-1", entitlement_id="ent-1"
        )
        env.service.record_usage(provider_type="llm", provider_name="fake")
        env.service.record_authentication_event(event_type="session_opened")
        streams = {row.stream for row in env.service.durable_audit_events()}
        assert streams <= set(STREAMS), streams

    def test_authentication_vocabulary_is_frozen(self) -> None:
        assert AUTHENTICATION_EVENT_TYPES == (
            "session_opened",
            "session_revoked",
            "sessions_revoked_all",
            "authentication_failed",
            "identity_linked",
        )
        assert set(AUTHENTICATION_EVENT_TYPES) & set(OUTCOMES) == set()

    def test_port_export_discipline(self) -> None:
        from app.forge.persistence import port

        assert "AuditEventPort" in port.__all__
        assert "AuditEventRecord" in port.__all__
        # runtime_checkable protocol structural check on both gateways
        from app.forge.persistence.memory import InMemoryPersistenceGateway
        from app.forge.persistence.sql.gateway import SqlAlchemyPersistenceGateway

        assert isinstance(InMemoryPersistenceGateway(), port.AuditEventPort)
        engine = create_engine("sqlite://")
        gateway = SqlAlchemyPersistenceGateway(engine.connect())
        assert isinstance(gateway, port.AuditEventPort)
        engine.dispose()


# ---------------------------------------------------------------------------
# H — composition root (fail-closed wiring; frozen container seam)
# ---------------------------------------------------------------------------


class TestCompositionRoot:
    def test_default_env_keeps_container_seam_untouched(self, monkeypatch) -> None:
        monkeypatch.delenv("FORGE_AUDIT_DURABLE_ENABLED", raising=False)
        monkeypatch.delenv("FORGE_AUDIT_DURABLE_URL", raising=False)
        import app.main

        container = app.main._build_forge_container()
        assert container.persistence is None  # frozen seam (II.2 decision)
        if container.observability is not None:
            assert container.observability.audit_ledger is None

    def test_enabled_env_wires_ledger_without_container_persistence(
        self, monkeypatch
    ) -> None:
        monkeypatch.setenv("FORGE_AUDIT_DURABLE_ENABLED", "1")
        monkeypatch.setenv("FORGE_AUDIT_DURABLE_URL", "sqlite://")
        import app.main

        container = app.main._build_forge_container()
        assert container.persistence is None
        assert container.observability is not None
        assert container.observability.audit_ledger is not None
        assert container.observability.snapshot()["durable_audit"]["status"] == "OK"
        diagnostics = container.redacted_diagnostics()
        assert diagnostics["config"]["audit_durable_enabled"] is True
        assert diagnostics["config"]["audit_durable_configured"] is True
        # the URL itself never appears in diagnostics
        assert "sqlite://" not in json.dumps(diagnostics, default=str)

    def test_enabled_without_url_fails_closed_at_startup(self, monkeypatch) -> None:
        monkeypatch.setenv("FORGE_AUDIT_DURABLE_ENABLED", "1")
        monkeypatch.delenv("FORGE_AUDIT_DURABLE_URL", raising=False)
        monkeypatch.delenv("FORGE_DATABASE_URL", raising=False)
        import app.main

        with pytest.raises(ValueError):
            app.main._build_forge_container()


# ---------------------------------------------------------------------------
# I — real PostgreSQL (CI postgres job only)
# ---------------------------------------------------------------------------


@pytest.mark.skipif(
    not PG_URL,
    reason="FORGE_TEST_DATABASE_URL not set — PostgreSQL ledger proof executes in CI",
)
class TestPostgresAuditLedger:
    def _gateway(self):
        from app.forge.persistence.sql.gateway import SqlAlchemyPersistenceGateway

        engine = create_engine(PG_URL)
        connection = engine.connect()
        gateway = SqlAlchemyPersistenceGateway(connection)
        gateway.apply_migrations()
        connection.commit()  # DDL durability (same pattern as II.2 integration)
        connection.execute(
            text("TRUNCATE forge_audit_events RESTART IDENTITY CASCADE")
        )
        connection.commit()
        return SimpleNamespace(
            engine=engine, connection=connection, gateway=gateway
        )

    def test_pg_round_trip_order_and_idempotency(self) -> None:
        ctx = self._gateway()
        try:
            service = observability_from_config(
                ForgeConfig(
                    environment="test",
                    observability_log_sinks=False,
                    audit_durable=AuditDurableConfig(
                        enabled=True, database_url=PG_URL
                    ),
                ),
                persistence=ctx.gateway,
            )
            for index in range(3):
                assert service.record_authentication_event(
                    event_type="session_opened",
                    resource=f"pg-{index}",
                    at=f"2026-10-12T01:0{index}:00+00:00",
                ) is True
            service.record_policy_decision(_policy_record(allowed=False))
            rows = service.durable_audit_events(limit=100)
            assert len(rows) == 4
            assert [r.seq for r in rows] == sorted(r.seq for r in rows)
            assert [r.event_type for r in rows][:3] == ["session_opened"] * 3
            # idempotency on the real unique constraint
            first = rows[0]
            from dataclasses import replace

            assert ctx.gateway.append_audit_event(replace(first, seq=None)) is False
            assert len(ctx.gateway.list_audit_events(limit=100)) == 4
            # durability: committed rows visible on a second connection
            other = ctx.engine.connect()
            try:
                visible = other.execute(
                    text("SELECT count(*) FROM forge_audit_events")
                ).scalar()
                assert int(visible) == 4
            finally:
                other.close()
        finally:
            ctx.connection.close()
            ctx.engine.dispose()

    def test_pg_schema_indexes_and_columns(self) -> None:
        ctx = self._gateway()
        try:
            indexes = {
                row[0]
                for row in ctx.connection.execute(
                    text(
                        "SELECT indexname FROM pg_indexes"
                        " WHERE schemaname = 'public'"
                        " AND tablename = 'forge_audit_events'"
                    )
                )
            }
            for expected in (
                "forge_audit_events_pkey",
                "forge_audit_events_event_id_key",
                "idx_forge_audit_events_stream_time",
                "idx_forge_audit_events_type_time",
                "idx_forge_audit_events_request",
                "idx_forge_audit_events_actor",
            ):
                assert expected in indexes, expected
            columns = {
                row[0]
                for row in ctx.connection.execute(
                    text(
                        "SELECT column_name FROM information_schema.columns"
                        " WHERE table_name = 'forge_audit_events'"
                    )
                )
            }
            assert {"seq", "event_id", "stream", "event_type", "details_json"} <= columns
            # idempotent re-apply on PostgreSQL: no-op, no AHEAD
            assert ctx.gateway.apply_migrations() == "CURRENT"
            assert ctx.gateway.check_compatibility() == "OK"
        finally:
            ctx.connection.close()
            ctx.engine.dispose()
