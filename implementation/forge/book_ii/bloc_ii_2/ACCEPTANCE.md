# BOOK II / BLOC II.2 — PERSISTENCE — ACCEPTANCE.md

Status: ACCEPTANCE
Date: 2026-10-07
Freeze head: 60e067547b9d9165d94e4f074e0db0ba58e59e24
Dependency ratifications: I.1 `aca9438`, I.2 `5ce3246`, II.1 `598b34c`

Each clause names its verification. "test" = focused II.2 test
(`tests/test_forge_persistence.py`); "review" = executable inspection recorded
in EVIDENCE.md.

## A. Persistence port

- A1 Port, not provider-global connection — test: service/route code resolves
  persistence only through the injected `PersistenceGateway`.
- A2 Explicit injection — test: `ForgeServiceContainer(persistence=...)`
  accepted; composition root builds it only when configured.
- A3 No hidden mutable DB singleton — review: no module-level connection /
  session / engine in `app/forge/**`; container holds the only reference.
- A4 Domain modules persistence-library-free — review: zero diff to
  `canonical.py`/`schemas.py`/`provenance.py`; no sqlalchemy/psycopg import
  anywhere in `app/forge/canonical.py`, `schemas.py`, `provenance.py`.
- A5 Import performs no DB work — test: importing `app.main` (persistence
  disabled) and `app.forge.persistence.*` opens no connection.

## B. Canonical object storage

- B1 Round trip preserves: canonical ID, object_type, title, version,
  status, exposure, layer, references, metadata, deterministic payload +
  content hash — test: full round-trip matrix over ALL 8 object types
  (Model/Claim/Evidence/Setup/Doctrine/Term/Lineage/Artifact) with per-type
  identity assertions.
- B2 No flattening of Model/Claim/Evidence/Setup/Artifact — test: object_type
  enum equality after round trip; distinct fixtures per type.

## C. Specialized contract storage

- C1 ModelCard round trip — test: stored as structured JSON payload, validated
  against the canonical schema class at write and read boundaries.
- C2 EvidenceCard round trip — test: same.
- C3 SetupOperatorCard round trip — test: same.
- C4 No second ontology — review: specialized payload columns reuse the
  I.1 `CanonicalId`/`EvidenceStatus`/`ProductExposure` vocabulary only.
- C5 Invalid card rejected at boundary — test: a card payload violating its
  schema fails the write.

## D. Claim identity

- D1 8 identity dimensions round trip — test.
- D2 Results never become population identity — test: two claims differing
  ONLY in result/statistic produce identical population identity; claim
  identity table has no result column (review).

## E. Provenance

- E1 Artifact round trip preserves: id, source_class, content_identity,
  locator, source_state, materialization-reconstructable state — test
  (materialization state re-derived by the I.2 rule after round trip).
- E2 Typed edges round trip for all 6 relations — test.
- E3 Visual sources remain non-empirical after round trip — test: stored
  artifact + edge → `classify_support` still VISUAL_ONLY.
- E4 Conversation-derived remains non-empirical after round trip — test.

## F. References / integrity

- F1 Duplicate canonical ID rejected — test.
- F2 Duplicate artifact identity rejected — test.
- F3 Duplicate provenance edge rejected — test.
- F4 Forbidden self-reference rejected — test.
- F5 Dangling ordinary reference rejected — test.
- F6 Unresolved historical reference PRESERVED (no fabricated FK object) —
  test: object with `allow_unresolved_historical=True` reference to a
  non-existent ID round-trips with the flag and target intact.

## G. Write semantics

- G1 CREATE / transition / conflict / NOT FOUND are distinct deterministic
  outcomes — test.
- G2 No silent upsert of canonical truth — review + test: re-adding an
  existing canonical ID raises `DuplicateCanonicalObject`.
- G3 Multi-record logical write is atomic — test: transaction seeding two
  objects where the second violates integrity rolls back the first.
- G4 Duplicate identity fails deterministically — test.

## H. Read semantics

- H1 Round trip object→persistence→object preserves governed fields — test
  (B1). Reads return domain records, never raw rows — review.
- H2 Artifact/provenance round trips — test (E1/E2).

## I. Status transitions

- I1 Legal transition persists — test.
- I2 Illegal transition rejected BEFORE commit — test.
- I3 Terminal (SUPERSEDED/FALSIFIED) rejects further transitions — test.

## J. Migrations

- J1 Initial migration exists and is reviewable SQL — review.
- J2 Deterministic ordering + schema/version identity — test: versions sorted,
  identity recorded in `forge_schema_migrations`.
- J3 Compatibility check returns OK / BEHIND / INCOMPATIBLE / AHEAD — test.
- J4 Current schema ⇒ no-op migration — test.
- J5 Incompatible/older schema ⇒ clear failure — test.
- J6 Migration execution separate from import — test: import never runs
  migrations; runner invoked explicitly.
- J7 No destructive startup behavior — review of migration SQL + runner.

## K. Startup

- K1 Import does not connect — test.
- K2 Persistence disabled ⇒ app boots as II.1 — test.
- K3 Persistence enabled + ping failure ⇒ readiness not_ready — test.
- K4 Startup is intentional (no lazy side effects) — review.

## L. Readiness

- L1 DB disabled ⇒ `postgresql NOT_CONFIGURED, required=False` — test.
- L2 Enabled+healthy+compatible ⇒ `postgresql READY, required=True`,
  overall `ready` — test.
- L3 Enabled but unavailable ⇒ status != READY, required=True, overall
  `not_ready` — test.
- L4 Enabled but schema incompatible/behind ⇒ not_ready — test.
- L5 No credentials/URLs/raw DB exceptions in readiness payloads — test.

## M. Configuration

- M1 `FORGE_DATABASE_URL` / `FORGE_DATABASE_ENABLED` /
  `FORGE_MIGRATION_COMPATIBILITY_REQUIRED` formalized with safe defaults — test.
- M2 Malformed configuration fails clearly — test.
- M3 No DB credentials in meta/ready/logs/exception bodies — test + review.

## N. Concurrency

- N1 Optimistic version check: stale `expected_version` ⇒
  `StaleWriteConflict`, nothing committed — test (object, artifact, and
  status-transition paths).

## O. Determinism

- O1 Deterministic payload/hash survive round trip — test (B1).
- O2 DB timestamps excluded from canonical identity — review (schema: created/
  updated are persistence-owned columns, not domain fields).

## P. Security

- P1 Parameterized operations only — review of all SQL construction.
- P2 No SQL from canonical IDs/metadata by string concatenation — review.
- P3 No credentials in responses — test (L5).
- P4 No credentials in logs — review.
- P5 No arbitrary-table / SQL / raw-row / corpus-dump / persistence-debug
  endpoint — review + route-set test (public surface unchanged).
- P6 No cascade-delete hazards beyond aggregate-child rows — review (schema).

## Q. Regression

- Q1 I.1 green (exact count recorded in EVIDENCE).
- Q2 I.2 green.
- Q3 II.1 green (incl. container guard update: persistence now accepted,
  policy/providers still rejected).
- Q4 Signal Guard green.
- Q5 Full suite green.
- Q6 No test weakened/deleted.

## PostgreSQL integration evidence

Live PostgreSQL is NOT available in the local environment (no docker, no
psql). The frozen contract is satisfied by: unit truth through the port +
SQL-dialect migration contract executed on SQLite, with
**POSTGRESQL INTEGRATION: NOT EXECUTED (local)** recorded as a named gap in
EVIDENCE and covered by a CI workflow step (Postgres service container) so
the integration proof executes on push. Ratification states the gap
explicitly and does not claim live-Postgres verification locally.

## Explicit non-goals

No public CRUD/data routes; no corpus ingestion; no pgvector/embeddings/RAG;
no identity/policy; no I.3 Markdown-card fixes.
