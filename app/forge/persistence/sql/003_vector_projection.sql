-- FORGE persistence — migration 003_vector_projection
-- Book II closure repair (GAP-01) implementing frozen Ch II.2.4
-- retrieval/embedding storage. Forward-only, additive, never destructive:
-- 001 and 002 are untouched and remain immutable.
-- STORAGE != INTELLIGENCE: Book II stores and validates vectors. Embedding
-- generation and model selection belong to Book VII; canonical/retrieval
-- authority remains Book I; similarity never grants authority; protected
-- rows stay exposure-governed.
-- ENVIRONMENT: requires Postgres+pgvector — the frozen G-D1 environment
-- ("empty Postgres+pgvector -> current schema"). On a server without the
-- pgvector package this migration FAILS LOUDLY instead of silently forking
-- the schema across environments.
-- SPLIT-SAFETY: no semicolons inside statements (runner splits on ';').
-- FORGE dialect: postgresql

CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE retrieval_vectors (
    object_id         VARCHAR(120) NOT NULL,
    object_version    VARCHAR(64)  NOT NULL,
    payload_json      TEXT         NOT NULL,
    semantic_text     TEXT         NOT NULL,
    embedding         vector       NOT NULL,
    embedding_dim     INTEGER      NOT NULL,
    embedding_model   VARCHAR(120) NOT NULL,
    embedding_version VARCHAR(64)  NOT NULL,
    exposure_class    VARCHAR(40)  NOT NULL,
    canonical_hash    CHAR(64)     NOT NULL,
    owner_user_id     VARCHAR(120),
    generated_at      TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP,
    persisted_version BIGINT       NOT NULL DEFAULT 1,
    CONSTRAINT retrieval_vectors_pkey PRIMARY KEY (object_id),
    CONSTRAINT retrieval_vectors_dim_check CHECK (
        embedding_dim > 0
        AND embedding_dim <= 16000
        AND vector_dims(embedding) = embedding_dim
    ),
    CONSTRAINT retrieval_vectors_canonical_fkey FOREIGN KEY (object_id)
        REFERENCES canonical_objects (canonical_id) ON DELETE CASCADE,
    CONSTRAINT retrieval_vectors_owner_fkey FOREIGN KEY (owner_user_id)
        REFERENCES forge_users (user_id) ON DELETE RESTRICT
);

CREATE INDEX idx_retrieval_vectors_exposure ON retrieval_vectors (exposure_class);

CREATE INDEX idx_retrieval_vectors_owner ON retrieval_vectors (owner_user_id);
