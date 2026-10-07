# BOOK II / BLOC II.2 — PERSISTENCE — PLAN.md

Status: PLAN
Date: 2026-10-07
Freeze head: 60e067547b9d9165d94e4f074e0db0ba58e59e24 (ancestor, verified)
Dependency ratifications: I.1 `aca9438`, I.2 `5ce3246`, II.1 `598b34c` (all PASS)

---

## Ownership

Bloc II.2 owns the durable-truth substrate for canonical objects, specialized
cards, claim identity, artifacts and provenance — nothing else. It does not
ingest the corpus (I.3), compile retrieval objects (I.4), authorize (II.4), or
expose any data API.

## Governing laws carried into storage

- Persistence != Canonical Authority: the DB stores canonical state; it never
  redefines canonical semantics, never silently promotes, never reinterprets.
- Model != Claim != Evidence != Setup != Artifact: `object_type` and
  `artifact.source_class` are persisted and round-trip-faithful.
- Artifact != Evidence: provenance edges stay typed and physical-source-only.
- Lifecycle: all status changes pass `validate_status_transition`; SUPERSEDED
  and FALSIFIED remain terminal.
- Unresolved historical references are preserved as data; never fabricated
  into objects to satisfy a foreign key.

## Database technology

PostgreSQL (frozen Book II). Production target: PostgreSQL + psycopg2 driver.

## Driver/ORM decision (local decision, recorded)

Use **SQLAlchemy 2.0 Core** (no declarative ORM models, no session/identity
map): explicit Core `Table` metadata, parameterized SQL, explicit
transactions. Rationale: the repository boundary returns FORGE domain records,
never ORM rows; Core keeps SQL reviewable, avoids hidden identity-map
semantics that could silently mutate "canonical truth", and satisfies the
parameterized-binding security clause. `psycopg2-binary` is the driver.

The II.1 handoff guard (`container.__post_init__` rejecting persistence) is
deliberately **replaced** by II.2: persistence is explicitly injected via the
constructor; the guard now rejects only *unauthorized* future seams (policy,
providers). No hidden module-level DB singleton exists.

## Test/local strategy (no live Postgres required for unit truth)

The persistence **port** (`PersistenceGateway` protocol) is the contract. The
**same FORGE record types** are persisted by:

1. `InMemoryPersistenceGateway` — a real implementation of the port (not a
   mock of Postgres): enforces every FORGE integrity rule (uniqueness,
   provenance-edge uniqueness, transition legality, optimistic version
   check). Unit tests exercise full round-trips through the port.
2. `SqlAlchemyPersistenceGateway` — the PostgreSQL implementation, executed
   against **SQLite in-memory** in the ordinary suite **only as a
   SQL-migration/schema-contract executor**. The SQL dialect contract is
   written portable (see schema notes); SQLite execution proves the SQL
   migration applies, is idempotent, and rejects incompatible heads — it does
   **not** prove PostgreSQL server semantics, which is recorded as
   **POSTGRESQL INTEGRATION: NOT EXECUTED (local)** and executed in CI.

This satisfies the handoff constraint: unit truth never requires a developer
to run a Postgres server; production code never fakes Postgres (both
gateways are honest implementations of one port; SQLite is used only to
execute the portable SQL contract, never treated as production-equivalent).

## Migration framework (local decision, recorded)

Frozen II.1/II.2 requires an explicit, ordered, immutable, reviewable
migration mechanism. Alembic is installed but pins an autogenerate-heavy
workflow; the smaller production-suitable choice is a **first-party versioned
SQL migration runner** (`app/forge/persistence/migrations/`):

- each migration = ordered `.sql` file with a numeric prefix + identity comment;
- deterministic ordering, forward-only (immutable once ratified);
- runner records applied versions in `forge_schema_migrations`;
- `check_compatibility()` returns `OK / BEHIND / INCOMPATIBLE / AHEAD`;
- never destructive; no drop/recreate at startup; execution is a separate
  explicit command/API, never a side effect of import.

Migration **001** creates the full initial schema (reviewable SQL, no
framework noise: no ORM bookkeeping tables, no implicit cascades).

## Schema (initial migration 001 — summary)

- `forge_schema_migrations` — version PK, applied stamps.
- `canonical_objects` — `canonical_id` PK (canonical identity IS the
  identity; no surrogate), `object_type` CHECK enum, `title`, `version`,
  `status` CHECK enum, `exposure` CHECK enum, `layer` CHECK enum, `metadata`
  JSON, `deterministic_payload` TEXT, `content_hash` CHAR(64),
  `created_at`/`updated_at` TIMESTAMPTZ (persistence-owned, UTC; never part
  of canonical identity or content hash), `persisted_version` BIGINT
  (monotonic writer counter for optimistic concurrency).
- `canonical_references` — child rows: `(canonical_id, target_id, relation)`
  PK; FK to parent `ON DELETE CASCADE` (child-rows of the aggregate root);
  `allow_unresolved_historical` BOOLEAN preserved verbatim — **no FK to
  canonical_objects**, unresolved historical targets are legitimate data.
- `claim_identities` — 1:1 with CLAIM objects; the 8 frozen identity
  dimensions as columns; results/statistics are NOT columns here (they live
  in object `metadata`), so a result can never mutate population identity.
- `artifacts` — `artifact_id` PK, `source_class` (registry-validated at the
  domain boundary), `title`, `source_generation`, `version`, `locator`,
  `content_identity` (`sha256:<64hex>` format), `source_state` CHECK enum,
  `created_at`/`observed_at` TEXT (domain-owned as in I.2), `metadata` JSON,
  `persisted_version` BIGINT.
- `provenance_edges` — `(artifact_id, object_id, relation)` PK; FK artifact;
  FK object `ON DELETE CASCADE`; CHECK relation ∈ the 6 frozen relations.

No pgvector, no embedding/chunk tables, no RAG storage — deferred to the
owning later Bloc (I.4/VII.5) per frozen order.

## Transaction boundary

One logical write = one transaction: object + reference rows (+ claim
identity row) commit atomically; artifact + nothing else is one row;
provenance edge insert is one transaction. The gateway exposes
`transaction()` as the atomic multi-record primitive (e.g. seeding two
objects); the port documents that the in-memory gateway honors it (deferring
conflict checks to commit, like a real DB transaction).

## Concurrency strategy (frozen option: optimistic version check)

Writes carry `expected_version` (the `persisted_version` the caller last
read). Mismatch ⇒ `StaleWriteConflict` raised, nothing committed. Terminal
statuses reject all further transitions via the domain rule (enforced in the
gateway write path **before** commit).

## Serialization strategy

Domain → record mapping is explicit dataclass conversion (no model_dump into
the DB). `deterministic_payload`/`content_hash` are computed by the I.1
kernel and persisted verbatim; DB timestamps are persistence-owned metadata
and are excluded from canonical identity by construction (they are not fields
of `CanonicalObject`), so round-trip content hashes are unchanged.

## Repository boundary

`app/forge/persistence/records.py` (FORGE-persistable record types, zero DB
imports) + `port.py` (`PersistenceGateway` protocol + typed exceptions +
`result_identity`) + `memory.py` + `sql/` (schema, migration, gateway).
Domain modules (`canonical.py`, `schemas.py`, `provenance.py`) remain
persistence-free — they are unchanged this bloc (zero diff).

## Startup / readiness / migration-compatibility behavior

- Import: never connects. Composition root builds the gateway only when
  `FORGE_DATABASE_ENABLED=true`.
- Lifecycle startup: if persistence injected, `gateway.ping()` (SELECT 1);
  failure ⇒ startup context reports it and **readiness must be not_ready**.
- Migration compatibility is checked **before** readiness when enabled:
  `BEHIND`/`INCOMPATIBLE` ⇒ readiness not_ready (frozen II.1.6 law).
  `AHEAD` ⇒ degraded-but-servable (server older than code); recorded.
- When DB disabled/not required: `postgresql` stays `NOT_CONFIGURED` /
  `required=False`; app boots exactly as II.1.
- When enabled+healthy+compatible: `postgresql READY, required=True`,
  overall readiness `ready`.

## Configuration (formalized)

`FORGE_DATABASE_URL` (default empty), `FORGE_DATABASE_ENABLED` (default
false), `FORGE_MIGRATION_COMPATIBILITY_REQUIRED` (default true when
persistence enabled). Malformed values fail clearly. No credential ever
reaches `/forge/v1/meta`, `/forge/v1/ready`, logs, or exception bodies —
connection errors are normalized to `PersistenceUnavailable` with a redacted
`kind` only.

## Local/test vs production

- LOCAL/TEST default: persistence disabled → II.1 boot path unchanged.
- TEST with persistence: in-memory gateway (unit) + SQLite-executed SQL
  contract (dialect tests, tagged so they can be skipped where no SQL layer).
- STAGING/PRODUCTION: PostgreSQL; migration runner invoked explicitly
  (deploy step), never at import.

## Backup/restore assumptions

Mechanism defined by II.2; launch-grade drills are Book VIII (frozen).
II.2 ships: the schema is fully reconstructable from migrations
(`forge_schema_migrations` verifies version identity after restore);
canonical tables hold no ephemerality that a plain dump/restore loses.

## Security assumptions

SQLAlchemy Core parameter binding everywhere (no f-string SQL, no string
concatenation of IDs/metadata); no new public route (public surface stays
`/forge/v1/health|ready|meta`); no credentials in responses/logs; no
arbitrary-SQL, raw-row, corpus-dump or persistence-debug endpoint.

## II.3 handoff boundary

II.3 Identity/Session inherits: the persistence port + Postgres schema
foundation (account/license tables are II.2+II.3 schema work — II.2 delivers
the canonical/provenance half and the runner), optimistic-concurrency
pattern, migration discipline, and readiness contract. II.2 delivers no
identity semantics.

## Explicit non-goals

No corpus backfill; no Markdown ID/status fixes (I.3 owns them; II.2 merely
makes such objects persistable later); no pgvector/embeddings/RAG; no CRUD
HTTP routes; no identity/policy; no provider adapters.
