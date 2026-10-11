# BOOK II — CLOSURE REPAIR PLAN (GAP-01 / GAP-02 / GAP-05 / GAP_ADR_001)

Status: PLAN — committed BEFORE any implementation (append-only ladder rung 1)
Date: 2026-10-11
Start SHA: `eea25a35f15fea70df1b768d1e1a7c6db05d337f` (== `origin/forge`, tree clean)
Authorization: Build Agent #13 — Book II closure repair. **Does not ratify
Book II, does not amend any frozen plan, does not begin Book III/VII.**

## 1. Frozen requirements this packet executes

| ID | Frozen source (exact text location) | Requirement |
|---|---|---|
| Ch II.2.4 | Book II plan, Persistence chapters | Store retrieval object ID/version, structured payload, safe semantic text, embedding vector, embedding model/version, exposure class, canonical hash, generated-at; embedding provider/model change must not change canonical object identity |
| Persistence domains | Book II plan §Persistence domains | schemas/tables must distinguish `retrieval documents/embeddings` |
| Acceptance II.2 | Book II plan, Acceptance II.2 | vector data can be deleted/rebuilt without losing canonical truth; vector index rebuild without canonical loss; audit records survive normal projection rebuilds |
| G-D1 | Book II plan gate §Database | empty Postgres+pgvector → current schema |
| G-D4 | Book II plan gate §Database | vector projection rebuilds independently |
| G-D5 | Book II plan gate §Database | backup/restore smoke passes |
| G-P3 (vector sub-clause) | Book II plan gate §Policy | vector leakage tests fail closed |

Phase 0 classification: **storage infrastructure, not semantic intelligence.**
Book II stores/validates/projects vectors; embedding *generation* and model
*selection* are Book VII; canonical/retrieval *authority* is Book I; policy
*decisions* stay in II.4. Similarity never grants authority. No repair below
requires crossing a frozen ownership boundary → no Phase 0 stop condition met.

## 2. Environment truth (Phase 0b, recorded before design)

- Local: PostgreSQL **16.15** (Windows, `127.0.0.1:5432/forge_test`) —
  `pg_available_extensions` has **no `vector` package**; no Docker, no WSL
  distro, no MSVC toolchain; role `forge` has no `CREATEDB`.
- CI: workflow service image is `postgres:16` — **also no pgvector**.
- Consequence (frozen G-D1 names “Postgres+pgvector” as the schema
  environment): the CI service image changes to `pgvector/pgvector:pg16`
  (official pgvector image, same postgres:16 base, additive). This is a CI
  tooling change, not a frozen-planning change, and is recorded in EVIDENCE
  and the consolidated CI ledger. It weakens nothing: every existing test and
  env var is preserved.
- Local pgvector-dependent execution is an **infrastructure gap** (per
  operator directive: record the gap; do **not** substitute SQLite as
  proof). Locally runnable tests still run against the in-memory gateway and
  against plain local PostgreSQL where the schema head permits it; all
  pgvector acceptance executes on CI’s Postgres+pgvector (the project’s
  standing CI-only PostgreSQL pattern, extended honestly).
- Backup/restore smoke needs `pg_dump`/`pg_restore` + a fresh target
  database: executable in the CI postgres job (role is superuser there);
  skipped locally with an explicit reason (no `CREATEDB`, no pgvector).

## 3. Design — GAP-01 vector persistence substrate

**Migration `003_vector_projection.sql`** (forward-only, additive; 001/002
untouched and remain immutable):

- `CREATE EXTENSION IF NOT EXISTS vector;` (fails loudly where pgvector is
  absent — never a silent schema divergence; G-D1’s environment is
  Postgres+pgvector).
- Table `retrieval_vectors` keyed by `object_id` (PK), columns: the frozen
  Ch II.2.4 field set — `object_version`, `payload_json` (structured
  payload), `semantic_text` (safe semantic text), `embedding vector`,
  `embedding_dim` with `CHECK (vector_dims(embedding) = embedding_dim)`,
  `embedding_model`, `embedding_version`, `exposure_class`, `canonical_hash`,
  `generated_at`; plus `owner_user_id` (tenant scoping, NULL = shared
  corpus) and `persisted_version` (II.2 optimistic-versioning convention).
- Structural integrity: FK `object_id → canonical_objects(canonical_id) ON
  DELETE CASCADE` (stable canonical reference; deleting a projection can
  never touch canonical truth; no dangling projections), FK `owner_user_id
  → forge_users(user_id) ON DELETE RESTRICT` (identity-conservative, like
  002).
- One row per object: provider/model change *replaces attributes, never
  identity* (Ch II.2.4 “changing embedding provider/model does not change
  canonical object identity”).
- No ANN index in this packet (index family/dimension ceilings are tied to
  Book VII model selection; correctness first). Documented as a limitation.

**Typed contract** (`VectorProjectionRecord` in
`app/forge/persistence/records.py`, methods on `PersistenceGateway`):

- `put_vector_projection(record)` — validates then writes.
- `get_vector_projection(object_id, *, allowed_exposures, tenant)` —
  deny-before-content-load: one SQL statement filtered by exposure allow-set
  AND tenant scope; denied/absent both return `None` (no existence oracle,
  zero content leakage). Empty allow-set fails closed without a query.
- `search_vectors(embedding, *, allowed_exposures, tenant, limit)` —
  cosine-distance ordering; exposure+tenant filtering happens **in the SQL
  WHERE clause** so unauthorised rows are never selected/loaded.
- `delete_vector_projection(object_id)` — projection-only deletion.
- `rebuild_vector_projection(records)` — independent, deterministic
  replacement rebuild: upsert exactly the supplied authorized source set,
  remove stale rows, return counts; never touches canonical tables.

**Validation (shared, gateway-independent):** embedding finite floats,
`0 < dim ≤ 16000` (pgvector storage ceiling), `len == embedding_dim`,
model/version non-empty strings, `canonical_hash` 64-hex, exposure ∈ frozen
`ProductExposure` vocabulary. **Canonical cross-checks inside the write
path:** referenced canonical row must exist (FK + explicit check), and its
`version`, `exposure`, `content_hash` must equal the record’s
`object_version`, `exposure_class`, `canonical_hash` — a projection can
never re-label exposure or identity relative to canonical truth (no
laundering). Failures raise `InvalidRecord`; nothing is written.

**Two implementations, one contract:** SQL gateway (authoritative, real
pgvector) and in-memory gateway (deterministic reference double for local
tests — its vector behavior is explicitly NOT claimed as pgvector proof;
acceptance for storage/rebuild/isolation runs on PostgreSQL in CI).

## 4. Design — GAP-02 backup/restore smoke

`tests/test_forge_backup_restore.py`, gated on `FORGE_TEST_DATABASE_URL`
(and therefore CI postgres job only; explicit skip reason locally):

1. Capture source pre-dump counts + canonical `content_hash` multiset +
   migration head + vector fingerprint (independent connection).
2. `pg_dump` (custom format) to a temp file — credentials passed via
   subprocess env only, never argv, never logged.
3. `pg_restore` into a **fresh, empty database** (isolated from source).
4. Independent verification **on the restored database only**: table
   presence, per-table counts equal to source pre-dump values, canonical
   hash multiset equality, migration head == code head, projection rows with
   identical dimensions, canonical↔projection reconciliation
   (`canonical_hash` equals canonical `content_hash`), migration re-apply is
   a no-op (`CURRENT`), and source counts unchanged after the round trip.
5. Drop the restore database; no credentials/private data in any output.

A successful dump exit code alone is never claimed as proof — verification
is the round trip plus the independent checks.

## 5. Design — governance dispositions (Phase 1)

`GOVERNANCE.md` (rung 2) records, verbatim where quoted:

- **GAP_ADR_001:** operator interpretation — *executable dependency
  prerequisites govern authorization; phase labels do not override
  explicitly declared prerequisite contracts* — therefore Book II closure
  precedes Book III; frozen planning documents remain byte-identical
  (re-verified in VERIFICATION). The historical ADR file under `bloc_ii_5/`
  is NOT edited (append-only history); disposition is recorded here and in
  the consolidated gap register.
- **GAP-05 ownership** (verified against frozen contracts before use): Book
  II owns durable, content-minimized operational/security audit
  infrastructure where explicitly required (frozen Ch II.2.6 sits in Book
  II’s persistence chapters; §Persistence domains lists access/audit
  events); Book VI owns commercial entitlement decisions and their business
  meaning (Book II plan `# HANDOFF TO BOOK III / VI`); Book I owns evidence
  provenance (freeze-manifest invariants 2/7/20); Book II must not create an
  alternative licensing or evidence authority (invariants 18/19/20 — no
  license/entitlement truth tables exist; verified). No contradiction found
  → Phase 1 stop condition NOT met. Consequence recorded honestly: the
  durable audit/event-ledger implementation remains absent in code
  (in-process `BoundedAuditTrail`/`UsageLedger` only, no SQL audit writes) —
  the ownership question is resolved, the implementation is not, and the
  gap register is updated accordingly (never silently closed).

## 6. Test map (frozen requirement → executable test)

| Requirement | Test | Where it executes |
|---|---|---|
| G-D1 empty Postgres+pgvector → schema | `test_forge_postgres_integration.py` migration chain (updated `[1,2]`→`[1,2,3]`) + `TestPostgresVectorProjection::test_empty_database_creates_extension_and_table` | CI postgres job |
| Ch II.2.4 field set + validation | `tests/test_forge_vector_projection.py` contract class | local + CI |
| Model/provider change ≠ identity change | contract + PG: second model/version row replaces attributes, PK stable | local + CI |
| Canonical cross-checks (hash/exposure/version) | contract + PG mismatch-rejection tests | local + CI |
| G-D4 independent rebuild | PG: wipe projection → canonical intact → rebuild → identical fingerprint set | CI |
| Determinism / replacement / stale removal / corruption recovery | contract + PG rebuild tests | local + CI |
| G-P3 vector leakage fail closed | PG isolation class: cross-exposure, cross-tenant, empty allow-set, SQL-side filtered search, zero leakage | CI (memory-gate double also local) |
| Deny-before-content-load | PG: denied row ≡ missing row; content columns never returned | CI |
| Acceptance II.2 audit-survives-rebuild | PG: audit trail content unaffected by projection rebuild | CI |
| G-D5 backup/restore smoke | `tests/test_forge_backup_restore.py` | CI postgres job |
| Migration pins honesty | updated `[1,2,3]` asserts in policy/qa/retrieval/identity/pg-integration | local + CI |
| Existing behavior preserved | full existing suite unchanged otherwise (no test deleted, no assertion weakened) | local + CI |
| Exclusions | AST/text checks: no embedding generation, no new routes, no Book VII model logic | local + CI |

## 7. Boundaries and non-goals

- No Book-level ratification, no contract freeze, no frozen-plan edit, no
  Book III/IV/VI/VII implementation.
- No production embedding generation, no embedding APIs, no semantic
  reranking, no model intelligence (Book VII).
- No ANN index tuning; no new HTTP routes; no policy/entitlement changes;
  no durable audit-ledger implementation (GAP-05 ownership ruled, scope
  implementation remains and stays on the register).
- No deletion of or write to canonical Book I truth — projection storage is
  strictly downstream of canonical records.
- If CI cannot obtain pgvector (registry outage), record FAIL(infra) and
  stop — never declare PASS with an unexecuted blocker.

## 8. Ladder (append-only, Phase 6)

`PLAN/ACCEPTANCE` → `GOVERNANCE` → `IMPLEMENTATION` → `TESTS` → push + CI →
`EVIDENCE` (incl. justified evidence-pack updates) → `VERIFICATION` (final
push, final CI, frozen-file integrity). No amend/squash/rebase/reset/
force-push; fast-forward only.
