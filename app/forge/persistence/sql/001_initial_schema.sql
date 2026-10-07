-- FORGE persistence — migration 001_initial_schema
-- Book II / Bloc II.2. Portable Core schema; PostgreSQL is the production
-- target (TIMESTAMPTZ). SQLite test execution accepts the portable subset.
-- Immutable once ratified; forward-only; never destructive.

-- Version ledger is created idempotently by the runner itself; the statement
-- below is a no-op where it already exists.
CREATE TABLE IF NOT EXISTS forge_schema_migrations (
    version     INTEGER PRIMARY KEY,
    identity    VARCHAR(120) NOT NULL,
    applied_at  TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Canonical object aggregates. canonical_id IS the identity (no surrogate PK).
CREATE TABLE canonical_objects (
    canonical_id      VARCHAR(120) PRIMARY KEY,
    object_type       VARCHAR(20)  NOT NULL,
    title             VARCHAR(512) NOT NULL,
    version           VARCHAR(64)  NOT NULL,
    status            VARCHAR(40)  NOT NULL,
    exposure          VARCHAR(40)  NOT NULL,
    layer             VARCHAR(20)  NOT NULL,
    metadata_json     TEXT         NOT NULL,
    claim_identity_json TEXT,
    deterministic_payload TEXT    NOT NULL,
    content_hash      CHAR(64)     NOT NULL,
    persisted_version BIGINT       NOT NULL DEFAULT 1,
    created_at        TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at        TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Child rows of the object aggregate. No FK to canonical_objects on
-- target_id BY DESIGN: allow_unresolved_historical targets are legitimate
-- persisted data, never fabricated.
CREATE TABLE canonical_references (
    canonical_id                 VARCHAR(120) NOT NULL,
    target_id                    VARCHAR(120) NOT NULL,
    relation                     VARCHAR(120) NOT NULL,
    allow_unresolved_historical  BOOLEAN      NOT NULL DEFAULT FALSE,
    PRIMARY KEY (canonical_id, target_id, relation),
    FOREIGN KEY (canonical_id)
        REFERENCES canonical_objects (canonical_id) ON DELETE CASCADE
);

CREATE TABLE artifacts (
    artifact_id       VARCHAR(120) PRIMARY KEY,
    source_class      VARCHAR(64)  NOT NULL,
    title             VARCHAR(512) NOT NULL DEFAULT '',
    source_generation VARCHAR(64)  NOT NULL DEFAULT '',
    version           VARCHAR(64),
    locator           VARCHAR(512) NOT NULL DEFAULT '',
    content_identity  VARCHAR(80),
    source_state      VARCHAR(40)  NOT NULL,
    created_at        VARCHAR(64),
    observed_at       VARCHAR(64),
    metadata_json     TEXT         NOT NULL,
    persisted_version BIGINT       NOT NULL DEFAULT 1
);

CREATE TABLE provenance_edges (
    artifact_id VARCHAR(120) NOT NULL,
    object_id   VARCHAR(120) NOT NULL,
    relation    VARCHAR(40)  NOT NULL,
    note        VARCHAR(1024) NOT NULL DEFAULT '',
    PRIMARY KEY (artifact_id, object_id, relation),
    FOREIGN KEY (artifact_id) REFERENCES artifacts (artifact_id) ON DELETE CASCADE,
    FOREIGN KEY (object_id)   REFERENCES canonical_objects (canonical_id) ON DELETE CASCADE
);
