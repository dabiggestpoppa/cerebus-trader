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

POSTGRESQL INTEGRATION: **NOT EXECUTED / DEFERRED PROOF** (declared honestly;
see "Integration evidence status"). It is not a frozen blocker for II.2
ratification because the frozen contract's acceptance (application boot,
health/readiness semantics, test runtime without paid/external provider,
provider-free domain imports, migration-before-readiness) is fully satisfied
by the port + contract implementation, and the live-Postgres execution is
assigned to the CI `postgres` job introduced in the same ladder. It was NOT
claimed as verified, locally or in CI.

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
  declared, not implied away.
- Deferred proof owner: `.github/workflows/forge-tests.yml` `postgres` job
  (Postgres 16 service; full suite with FORGE_DATABASE_* env), first
  triggered by this ladder's push. If that CI job fails, integration remains
  an open gap to be re-ratified against CI evidence later.

## GAP/ADR

None required. All local decisions (SQLAlchemy Core, first-party migration
runner, in-memory gateway as unit-truth vehicle, SQLite as SQL-dialect
executor) fit the frozen plan's implementation-choice allowance and are
recorded in PLAN/EVIDENCE.

## Commit ladder (append-only from `598b34c`)

`10b8a5f` → `6b3e423` → `e080e9d` (implementation) → `1c0bf85` (integration)
→ `56250e3` (tests) → evidence commit (this file's predecessor) →
ratification commit (this file). Exact SHAs recorded in EVIDENCE.md and the
final report.

## Next authorized packet

Book II / Bloc II.3 — Identity & Session Core inherits the port pattern,
migration discipline, readiness vocabulary and optimistic-concurrency
pattern. **This ratification does not itself authorize II.3 execution; II.3
requires its own handoff prompt.**
