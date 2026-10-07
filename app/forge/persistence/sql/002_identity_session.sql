-- FORGE persistence — migration 002_identity_session
-- Book II / Bloc II.3. Adds FORGE-owned internal identity and runtime
-- sessions. Forward-only, immutable once ratified, never destructive.
-- IDENTITY != ENTITLEMENT: no plan/license/entitlement/capability table
-- exists here or may ever be added by identity. SESSION != LICENSE.
-- PROVIDER ID != FORGE ID: provider identifiers live only on links.

-- FORGE internal users. user_id IS the authoritative identity (no surrogate,
-- no email key, no provider key). email is an optional untrusted attribute:
-- deliberately NOT unique, never a lookup key.
CREATE TABLE forge_users (
    user_id           VARCHAR(120) PRIMARY KEY,
    state             VARCHAR(20)  NOT NULL CHECK (state IN ('ACTIVE', 'DISABLED')),
    roles_json        TEXT         NOT NULL DEFAULT '[]',
    email             VARCHAR(320),
    display_label     VARCHAR(200),
    persisted_version BIGINT       NOT NULL DEFAULT 1,
    created_at        TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at        TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Typed external identity links: (provider, provider_subject) -> forge_user_id.
-- Composite PK enforces uniqueness of the provider mapping. FK to users is
-- ON DELETE RESTRICT: identity history is never erased by a cascade, and II.3
-- offers no user deletion at all (disable + revoke are the removal paths).
CREATE TABLE external_identity_links (
    provider         VARCHAR(64)  NOT NULL,
    provider_subject VARCHAR(255) NOT NULL,
    forge_user_id    VARCHAR(120) NOT NULL,
    linked_at        TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (provider, provider_subject),
    FOREIGN KEY (forge_user_id)
        REFERENCES forge_users (user_id) ON DELETE RESTRICT
);

CREATE INDEX idx_external_identity_links_user
    ON external_identity_links (forge_user_id);

-- Runtime sessions. session_id is FORGE-owned and distinct from user_id.
-- token_digest is the SHA-256 hex of the opaque bearer token: the raw token
-- is NEVER stored. The unique index is the authentication lookup path.
-- FK to users is ON DELETE RESTRICT (conservative; no cascades over
-- audit-relevant identity history).
CREATE TABLE forge_sessions (
    session_id        VARCHAR(120) PRIMARY KEY,
    user_id           VARCHAR(120) NOT NULL,
    token_digest      CHAR(64)     NOT NULL,
    created_at        TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP,
    expires_at        TIMESTAMP    NOT NULL,
    revoked_at        TIMESTAMP,
    persisted_version BIGINT       NOT NULL DEFAULT 1,
    FOREIGN KEY (user_id)
        REFERENCES forge_users (user_id) ON DELETE RESTRICT
);

CREATE UNIQUE INDEX idx_forge_sessions_token_digest
    ON forge_sessions (token_digest);

CREATE INDEX idx_forge_sessions_user
    ON forge_sessions (user_id);
