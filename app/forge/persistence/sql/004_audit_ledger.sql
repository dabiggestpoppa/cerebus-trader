-- FORGE persistence — migration 004_audit_ledger
-- Book II GAP-05 closure implementing frozen Ch II.2.6 (Audit/event ledger).
-- Forward-only, additive, never destructive: 001/002/003 are untouched and
-- remain immutable. Ownership (closure_repair/GOVERNANCE §2): Book II owns
-- durable, content-minimized operational and security audit infrastructure;
-- Book I owns evidence provenance; Book VI owns entitlement business meaning.
--
-- Append-oriented records for authentication/security events, policy
-- decisions, protected retrieval access, entitlement change records,
-- provider events and administrative mutations. Audit payloads avoid
-- secrets and unnecessary corpus content (details_json holds only bounded,
-- redacted scalars produced by the observability redaction path).
--
-- Dialect truth: PORTABLE — applies on both PostgreSQL and SQLite (like
-- 001/002). seq is gateway-allocated (monotonic, unique; PRIMARY KEY) so no
-- dialect-specific auto-increment syntax is needed; event_id is UNIQUE and
-- doubles as the idempotency key. No semicolons inside statements (runner
-- splits on ';'). No FK: an audit record must survive the deletion of the
-- rows it references (durability of history, not referential authority).
CREATE TABLE IF NOT EXISTS forge_audit_events (
    seq          BIGINT       NOT NULL,
    event_id     VARCHAR(36)  NOT NULL,
    stream       VARCHAR(64)  NOT NULL,
    event_type   VARCHAR(120) NOT NULL,
    severity     VARCHAR(16)  NOT NULL,
    environment  VARCHAR(32)  NOT NULL DEFAULT 'local',
    occurred_at  VARCHAR(64)  NOT NULL,
    request_id   VARCHAR(120),
    actor_type   VARCHAR(32)  NOT NULL DEFAULT 'system',
    actor_id     VARCHAR(120),
    resource     VARCHAR(256) NOT NULL DEFAULT '',
    outcome      VARCHAR(32)  NOT NULL,
    reason       VARCHAR(120) NOT NULL DEFAULT '',
    details_json TEXT         NOT NULL,
    created_at   TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (seq),
    UNIQUE (event_id)
);

CREATE INDEX IF NOT EXISTS idx_forge_audit_events_stream_time
    ON forge_audit_events (stream, occurred_at);

CREATE INDEX IF NOT EXISTS idx_forge_audit_events_type_time
    ON forge_audit_events (event_type, occurred_at);

CREATE INDEX IF NOT EXISTS idx_forge_audit_events_request
    ON forge_audit_events (request_id);

CREATE INDEX IF NOT EXISTS idx_forge_audit_events_actor
    ON forge_audit_events (actor_type, actor_id);
