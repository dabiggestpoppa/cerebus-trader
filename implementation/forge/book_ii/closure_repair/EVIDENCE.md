# BOOK II — CLOSURE REPAIR EVIDENCE (GAP-01 / GAP-02 / GAP-05 / GAP_ADR_001)

Status: EVIDENCE (ladder rung 7) — executed results only. Not a
ratification; not a Book-level PASS.
Start SHA: `eea25a35f15fea70df1b768d1e1a7c6db05d337f`.
Evidence head at writing: `914cc04` (CI green, §5).

## 1. Ladder (append-only, no amend/squash/rebase/reset/force-push)

| Rung | SHA | Content |
|---|---|---|
| 0 | `eea25a3` | authorized start (== origin/forge, tree clean) |
| 1 | `85bf2ed` | PLAN + ACCEPTANCE (committed BEFORE implementation) |
| 2 | `3e7ae66` | GOVERNANCE record (GAP_ADR_001 + GAP-05 dispositions) |
| 3 | `fdfd098` | IMPLEMENTATION: migration 003, typed contract, both gateways, CI pgvector image |
| 4 | `6a426de` | TESTS: vector projection suites + backup/restore smoke + honest `[1,2,3]` pins |
| 5 | `9f44d81` | CI round-1 FAIL(app) repairs (RowMapping, txn hygiene, fixture fields) |
| 6 | `914cc04` | CI round-2 FAIL(app) repairs (owner-FK parity, clean-txn fixture, collection restore) |

## 2. Phase 0 environment truth (recorded before design)

- Local PostgreSQL 16.15 (Windows): **no `vector` package** in
  `pg_available_extensions`; no Docker, no WSL distro, no MSVC toolchain;
  role `forge` has no `CREATEDB`.
- CI at start: service image `postgres:16` — also no pgvector.
- Frozen G-D1 names "empty Postgres+pgvector → current schema" → the CI
  service image changed to `pgvector/pgvector:pg16` (official pgvector image,
  same postgres:16 base; jobs/env/tests unchanged) — the only workflow diff.
- Consequence, per operator instruction: local pgvector-dependent execution
  is an **infrastructure gap, recorded — SQLite (or any non-pgvector store)
  is never substituted as proof**. The SQL gateway enforces this in code
  (`vector_storage_requires_postgresql` fail-closed guard, proven by
  `test_sqlite_portable_subset_has_no_vector_table_and_fails_closed`).

## 3. Frozen requirement → executed proof

| Frozen requirement | Executable proof | Executed result |
|---|---|---|
| Ch II.2.4 field set (id/version, structured payload, safe semantic text, embedding vector, model/version, exposure class, canonical hash, generated-at) | `tests/test_forge_vector_projection.py` `test_roundtrip_preserves_every_frozen_field` (contract) + `TestPostgresVectorProjection::test_roundtrip_and_canonical_cross_checks` | pass, local + CI (postgres job) |
| Provider/model change ≠ identity change | `test_model_change_replaces_attributes_not_identity` + `test_model_change_keeps_identity_on_postgres` | pass (single PK row, attributes replaced) |
| G-D1 empty Postgres+pgvector → current schema | migration `003_vector_projection.sql`; `test_empty_database_applies_pgvector_schema` (extension, table, `retrieval_vectors_dim_check`, `_canonical_fkey`, `_owner_fkey`, compat OK, re-apply CURRENT); migration-chain pins `[1,2,3]` | pass on CI Postgres+pgvector; **15 validation rejections + canonical cross-checks** (`test_validation_rejects_and_writes_nothing`, `test_*_mismatches_rejected`) pass locally and on CI |
| G-D4 vector projection rebuilds independently | `test_rebuild_is_independent_of_canonical_truth` (wipe → canonical byte-identical → rebuild restores), `test_rebuild_is_deterministic_and_removes_stale`, `test_rebuild_recovers_corrupted_projection` (contract) + `test_rebuild_deterministic_stale_and_corruption_recovery` (PG: truncate→rebuild (2,0), idempotent second rebuild, stale (2,1), raw-SQL corruption recovery, canonical intact) | pass, CI postgres job |
| Acceptance II.2 "vector data deleted/rebuilt without losing canonical truth" | `test_projection_deletion_leaves_canonical_truth_intact` (PG: delete → canonical content_hash/status unchanged → rebuild restores) | pass, CI |
| Acceptance II.2 "audit records survive projection rebuilds" | `test_audit_trail_survives_projection_rebuild` (II.6 `BoundedAuditTrail` snapshot identical across wipe+rebuild) | pass |
| G-P3 vector leakage fails closed | `test_isolation_matrix_zero_leakage` (contract, 12 deny/allow cells + exact search id sets) and `test_isolation_matrix_on_postgres` (PG: cross-exposure, cross-tenant, anon vs user_a, empty allow-set ≡ missing, search id sets exact, tie-break by object_id) | pass on CI Postgres+pgvector |
| Deny-before-content-load | single filtered SELECT in `get_vector_projection`; denied row and missing row both return `None` (asserted both layers) — no existence oracle, no content column ever returned for a denied row | pass |
| Search filters before content (SQL-side) | `search_vectors`: exposure + tenant + dimension filters live in the WHERE clause; ordering `(embedding <=> q) ASC, object_id ASC`; `test_search_orders_by_distance_and_honors_limit` | pass (contract locally, SQL path CI) |
| G-D5 backup/restore smoke passes | `tests/test_forge_backup_restore.py::TestBackupRestoreSmoke::test_backup_restore_roundtrip_verified_independently` — pg_dump `-Fc` → restore into fresh `forge_restore_smoke` DB → verification **on the restored DB only**: table set, per-table counts, canonical hash multiset, migration head `[1,2,3]`, vector rows/dims/model/hash/owner preserved, canonical↔projection reconciliation (0 divergent rows), `vector_dims == embedding_dim`, forbidden business tables absent, migration re-apply `CURRENT`; source counts/hashes unchanged after round trip | pass, CI postgres job |
| D6 similarity never grants authority | `test_persistence_never_imports_policy_authority` (persistence package imports no policy module); policy decisions stay in II.4 | pass |
| Migration discipline (SQLite portable subset) | dialect-aware runner: `test_migration_003_declares_postgresql_only` + `test_sqlite_portable_subset_has_no_vector_table_and_fails_closed`; existing SQLite apply/OK/CURRENT tests unchanged and green | pass |
| Preservation | full existing suite green: local `975 passed, 27 skipped`; CI `test` job `975 passed, 27 skipped`; CI `postgres` job `1002 passed` (0 skipped) | pass |

## 4. GAP-01 disposition

**CLOSED BY REPAIR (implementation, option A of the register).** Frozen
Ch II.2.4 storage substrate exists: `retrieval_vectors` (pgvector, FK-stable
canonical reference `ON DELETE CASCADE`, dimension CHECK, tenant owner
`ON DELETE RESTRICT`), typed `VectorProjectionRecord`, shared validation,
canonical cross-checks (version/exposure/hash — a projection cannot re-label
canonical truth), deny-before-content-load reads, SQL-side filtered cosine
search, deterministic independent replacement rebuild. Embedding generation,
model selection and ANN index tuning are NOT implemented (Book VII ownership
— excluded by PLAN §7 and verified by the exclusion scans). The historical
II.2 "no pgvector" non-goal stands as the recorded deviation that GAP-01
tracked; frozen Ch II.2.4 governs (GOVERNANCE §3).

## 5. CI / PostgreSQL verification history (this packet)

| Run | Head | `test` job | `postgres` job | Classification |
|---|---|---|---|---|
| 38187591174 | `6a426de` (rung 4) | ✅ 975/27 | ❌ 995 passed, 6 failed, 1 error | **FAIL(app)** — RowMapping access, txn-abort cascade, backup fixture field typo; repaired append-only (rung 5). Never claimed as a pass. |
| 38187953980 | `9f44d81` (rung 5) | ✅ 975/27 | ❌ 1000 passed, 2 failed | **FAIL(app)** — tenant projection referenced an unseeded user (003 owner FK working as designed) + one swallowed `def`; repaired append-only (rung 6). |
| 38188302328 | `914cc04` (rung 6) | ✅ **975 passed, 27 skipped** | ✅ **1002 passed** (full suite), integration evidence **19 passed**, identity evidence **7 passed** | **PASS** — both jobs green; every PG-dependent test executed (0 skipped in the postgres job), including the backup/restore smoke and all 7 pgvector acceptance tests. |
| 43442454742 | `28bb1a6` (BA-40A start) | ✅ local 2,754/0/29 | ❌ `pg_restore` exit 1: `transaction_timeout` unrecognized | **FAIL(infra)** — runner `pg_dump`/`pg_restore` (PG 17+) vs PostgreSQL 16 server; jobs completed in ~3s with no steps executed; repaired in BA-40A by installing `postgresql-client-16` and adding a version-assertion step (see §11) |

The 27 local/`test`-job skips are the declared environment split: 19
integration + 7 pgvector + 1 backup/restore, all executed in the postgres
job. `pg_dump`/`pg_restore` credentials travel only in subprocess
environments (asserted: password absent from argv and output).

## 6. GAP-02 disposition

**CLOSED BY REPAIR (executed smoke).** The round trip ran for real in the
postgres job (run 38188302328): dump → restore into a fresh database →
independent verification on the restored database → source-unchanged check.
Seeded coverage: 2 canonical objects + reference, artifact + provenance
edge, user + session, one vector projection row. Local execution is an
**infrastructure gap** (no `CREATEDB`, no local pgvector) — recorded, not
substituted (ACCEPTANCE E5). Launch-scale drills remain Book VIII (frozen
plan split unchanged).

## 7. GAP-05 disposition

**Ownership INTERPRETATION RECORDED AND VERIFIED** (`GOVERNANCE.md` §2):
clause-by-clause check against frozen contracts found no contradiction (no
Phase-1 stop). Honest consequence unchanged from GOVERNANCE §2: the durable
Book II audit/event ledger is **not implemented** (in-process
`BoundedAuditTrail`/`UsageLedger` only; no SQL audit writes) — the register
reclassifies it from "operator pending" to an explicit Book II open item.
This packet did not implement it (Phase 2/3 scope is GAP-01/GAP-02 only).

## 8. GAP_ADR_001 disposition

**DISPOSED** (`GOVERNANCE.md` §1): operator interpretation recorded verbatim
— *executable dependency prerequisites govern authorization; phase labels do
not override explicitly declared prerequisite contracts* — Book II closure
precedes Book III; frozen planning documents remain byte-identical
(re-verified in `VERIFICATION.md`); the historical ADR file under
`bloc_ii_5/` is untouched (append-only history).

## 9. Security / isolation findings

- Exposure and tenant filters are enforced **in SQL** before any content
  column is selected; denied ≡ missing (no existence oracle).
- 003 constraints are DB-enforced, not just code-enforced: raw-SQL probes
  prove `retrieval_vectors_dim_check` and `retrieval_vectors_canonical_fkey`
  fire (`test_database_enforces_dimension_and_foreign_key`), and the owner
  FK rejected an unseeded tenant user in CI (round-2 failure — constraint
  working; test data fixed, constraint untouched).
- No new routes, no policy/identity semantics change, no credentials in
  evidence, no embedding generation anywhere (`app/` scan in PLAN §7).

## 10. Remaining limitations (carried, never closed here)

1. **Local pgvector execution** — infra gap: local server has no pgvector
   package; all pgvector acceptance executes on CI (recorded per operator
   directive).
2. **Durable audit/event ledger (post-GAP-05 ruling)** — Book II scope,
   unimplemented; on the register as a Book II open item.
3. **Backup/restore scope** — smoke runs on the CI database instance
   (restore target is a separate database on the same server, not a
   separate host); host-level drills remain Book VIII.
4. **No ANN index** — index family/dimension ceilings deferred with Book VII
   model selection; correctness (exact cosine ordering) proven instead.
5. **Synthetic embeddings only** — float32-exact deterministic components;
   no production embedding generation, reranking or external embedding APIs.
6. **GAP-07/GAP-09/GAP-08-class items** — unchanged from the consolidated
register (dedicated alias-bypass adversarial test, true SQL writer-race
suite, registry-rate-limit exposure — now also pulling
`pgvector/pgvector:pg16`).

## 11. BA-40A — PostgreSQL 16 client/server compatibility repair

**Original failure.** GitHub Actions run `43442454742` at head SHA
`28bb1a65678affe713cb1bb370ece5a8bbefc7b5` (branch `forge`). The
`postgres` job ran the backup/restore smoke
(`tests/test_forge_backup_restore.py::TestBackupRestoreSmoke::test_backup_restore_roundtrip_verified_independently`)
and reported:

```
pg_restore failed (exit 1)
ERROR: unrecognized configuration parameter "transaction_timeout"
```

Both jobs (`test`, `postgres`) completed in ~3 seconds with zero execution
steps recorded — a GitHub Actions runner/startup failure, not an application
test failure. The `test` job passes independently.

**Root cause.** The GitHub-hosted runner's `pg_dump`/`pg_restore` client
binaries are PostgreSQL 17+. `pg_dump` 17 emits `SET transaction_timeout = 0;`
(`transaction_timeout` is a PostgreSQL 17+ configuration parameter) into its
custom-format dump. `pg_restore` executing that dump against the PostgreSQL
16 server (`pgvector/pgvector:pg16` service image, frozen per G-D1) rejects
`transaction_timeout` as an unrecognized configuration parameter. No
application schema, migration, or acceptance expectation was involved — the
`test` job (same database, same migrations) passes.

**Repair.** Minimal workflow change in `.github/workflows/forge-tests.yml`
(postgres job, inserted after `pip install -r requirements.txt`):

1. **Install PostgreSQL 16 client tools** — `postgresql-client-16` via apt;
   append `/usr/lib/postgresql/16/bin` to `$GITHUB_PATH` so `pg_dump` and
   `pg_restore` resolve to the PostgreSQL 16 binaries before any runner-default
   (newer) client.
2. **Assert PostgreSQL 16 client/server compatibility** — a deterministic step
   that prints `pg_dump --version`, `pg_restore --version`, and the server's
   `SHOW server_version`, parses each major version, and exits non-zero unless
   all three equal 16. This fails explicitly if client/server version
   compatibility drifts in the future.

No application source, migration, route, schema, frozen fixture, or
acceptance-expectation change. The backup/restore test is unweakened;
`--exit-on-error` is retained; no SQL is filtered from backups; no
pg_restore failures are suppressed.

**Verification.** Local full regression: **2,754 passed / 0 failed / 29
skipped** (unchanged from baseline). Targeted suites (Book V presentation,
golden, adversarial, Book IV answer): **143 passed / 1 skipped** (the single
skip is the backup/restore smoke, which correctly skips locally — it requires
`FORGE_TEST_DATABASE_URL` and executes only on the CI Postgres+pgvector job,
per its explicit skip reason and PLAN §4).

The repair is validated by CI: the `postgres` job at the final HEAD must
report both `test: SUCCESS` and `postgres: SUCCESS`, with the version-assertion
step passing (server 16, pg_dump 16, pg_restore 16).
