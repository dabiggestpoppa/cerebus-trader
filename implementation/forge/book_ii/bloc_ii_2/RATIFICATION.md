# BOOK II / BLOC II.2 — PERSISTENCE — RATIFICATION.md

Status: RATIFICATION
Date: 2026-10-07
Repository: dabiggestpoppa/cerebus-trader
Branch: forge
Freeze head: `60e067547b9d9165d94e4f074e0db0ba58e59e24` (ancestor, verified)
Dependency ratifications: I.1 `aca9438`, I.2 `5ce3246`, II.1 `598b34c` (all PASS)
Evidence basis: `implementation/forge/book_ii/bloc_ii_2/EVIDENCE.md` at the
evidence commit (see ladder below); executable gate run at IMPLEMENTATION
HEAD `56250e3`.

---

## Decision

**Book II / Bloc II.2 — Persistence
CLOSED — PASS**

POSTGRESQL INTEGRATION: **NOT EXECUTED locally / EXECUTED IN CI — VERIFIED**
(declared honestly; see "Integration evidence status"). The deferred proof
that this ratification assigned to the CI `postgres` job has since executed
successfully: run 37627625500 (commit `2d5a8e6`) shows both `test` and
`postgres` jobs SUCCESS, including the explicit integration module
(`tests/test_forge_postgres_integration.py`: migrations on live PostgreSQL,
round trip with hash preservation, real-constraint duplicate/FK rejections,
optimistic stale-conflict). First runs exposed and fixed real defects
(environment drift plus PostgreSQL transaction/DLL semantics) recorded in
EVIDENCE.md; the ratified evidence environment is now pinned in
requirements.txt.

## Acceptance verification (all clauses)

- **A. Port/injection/isolation** — PersistenceGateway protocol; explicit
  injection (tested); container structural guard (tested); domain modules
  persistence-free (AST-asserted); import opens no connection (tested).
- **B. Canonical storage** — full round-trip matrix over all 8 object types
  with identity/status/exposure/layer/references/metadata/payload/hash
  preserved (tested); object types never flattened (tested).
- **C. Specialized cards** — ModelCard / EvidenceCard / SetupOperatorCard
  round-trips validated against their canonical schema classes (tested);
  invalid payload rejected at boundary (tested); no second ontology
  (canonical vocabulary only).
- **D. Claim identity** — 8-dimension identity round-trips; results live only
  in metadata and provably do not alter population identity (tested).
- **E. Provenance** — artifact round-trip incl. reconstructable
  materialization state; all 6 typed edges round-trip; visual and
  conversation-derived sources remain non-empirical after storage (the I.2
  classifier re-classifies from restored data).
- **F. Integrity** — duplicate canonical ID / artifact / provenance edge
  rejected; self-reference rejected; dangling ordinary reference rejected;
  unresolved historical reference persisted verbatim with its flag (tested).
- **G. Writes** — CREATE/TRANSITION/CONFLICT/NOT_FOUND distinct (tested);
  duplicate identity fails deterministically; multi-record transaction is
  atomic — a failed seed leaves nothing committed (tested, defect #1 found
  and fixed by this test).
- **H. Reads** — domain records, never raw rows, are returned; round trips
  preserve governed fields (tested).
- **I. Transitions** — legal persists; illegal rejected before commit;
  terminal SUPERSEDED/FALSIFIED intact (tested).
- **J. Migrations** — reviewable SQL (001); deterministic ordering +
  ledger identity; OK/BEHIND/INCOMPATIBLE/AHEAD identity (tested); current =
  no-op (tested); import never migrates (tested); no destructive behavior
  (review).
- **K. Startup** — import never connects (tested); disabled ⇒ boots exactly
  as II.1 (tested); ping failure ⇒ readiness not_ready (tested); startup
  intentional, no lazy side effects.
- **L. Readiness** — all four honesty states verified by tests
  (NOT_CONFIGURED/False; READY/True; unavailable ⇒ not_ready/required;
  incompatible schema ⇒ not_ready; payloads leak nothing).
- **M. Configuration** — the three env names formalized with safe defaults;
  malformed values fail clearly; no credentials in meta/ready/logs/exceptions
  (tested + review).
- **N. Concurrency** — optimistic `persisted_version` check on objects and
  artifacts: stale writers rejected with nothing committed (tested).
- **O. Determinism** — content hashes round-trip unchanged; DB timestamps are
  persistence-owned and structurally excluded from canonical identity
  (tested + schema review).
- **P. Security** — parameterized-only SQL (review); no SQL from untrusted
  identifiers (only module-constant table names); no credentials in
  responses/logs (tested); no new public route — public surface remains
  exactly health/ready/meta (tested); no destructive/cascade hazards beyond
  aggregate children; no global session.
- **Q. Regression** — I.1 41 ✓, I.2 41 ✓, II.1 36 ✓, Signal Guard 48 ✓,
  full suite **217 passed / 0 failed / 0 errors / 0 skips**; +51 tests,
  none weakened or deleted.

## Scope discipline

No corpus backfill (the known SETUP./SET. Markdown mismatch is untouched —
I.3 owns it and the schema notes it only as a future registrable case); no
pgvector/embedding/RAG storage; no public CRUD/data routes; no
identity/policy/provider work. Frozen laws preserved (Persistence != Canonical
Authority; Artifact != Evidence; terminal statuses intact).

## Integration evidence status

- Local: **NOT EXECUTED** (no Docker/PostgreSQL in the environment) —
  declared, not implied away; the integration module skips locally with an
  explicit message.
- Deferred proof owner: `.github/workflows/forge-tests.yml` `postgres` job
  (Postgres 16 service; full suite with FORGE_DATABASE_* env).
- Deferred proof **EXECUTED AND PASSED**: run 37627625500, commit `2d5a8e6`,
  conclusion SUCCESS for both jobs. The full suite (217 tests) ran against
  live PostgreSQL, and the dedicated integration module executed its 6
  tests. Earlier runs (37623041116, 37627002127 failures) diagnosed real
  defects that were fixed on the append-only ladder; no failure was hidden.

## GAP/ADR

None required. All local decisions (SQLAlchemy Core, first-party migration
runner, in-memory gateway as unit-truth vehicle, SQLite as SQL-dialect
executor) fit the frozen plan's implementation-choice allowance and are
recorded in PLAN/EVIDENCE.

## Commit ladder (append-only from `598b34c`)

`10b8a5f` → `6b3e423` → `e080e9d` (implementation) → `1c0bf85` (integration)
→ `56250e3` (tests) → `cca3bd9` (evidence) → `438a35e` (ratification — this
file) → `5542105` (platform/CI) → `3c5564c` → `1b42dfb` → `1ba8ee1` →
`7a7347a` → `2d5a8e6` (repairs; CI SUCCESS both jobs). Exact SHAs recorded
in EVIDENCE.md and the final report.

## Next authorized packet

Book II / Bloc II.3 — Identity & Session Core inherits the port pattern,
migration discipline, readiness vocabulary and optimistic-concurrency
pattern. **This ratification does not itself authorize II.3 execution; II.3
requires its own handoff prompt.**
