# ACCEPTANCE — GAP-05 Durable Audit / Event Ledger (Build Agent #14)

**Start SHA:** `689358d3d879aed46a42360de85fb059204e7b29` · **Branch:** `forge`
Every criterion below is externally checkable. If a criterion cannot be met, it is
recorded honestly in EVIDENCE.md / VERIFICATION.md — never weakened silently.

## A. Process rungs

- **A1.** PLAN.md and ACCEPTANCE.md exist in
  `implementation/forge/book_ii/closure_repair_gap05/` and are committed **before**
  the first implementation commit (commit order visible in `git log`).
- **A2.** No Book II ratification/freeze artifact is created or modified; no
  Book III+ file is created or modified; the six `bloc_ii_*/` ratified artifacts
  are untouched.
- **A3.** Work is append-only on evidence: no previously green test is deleted,
  skipped, or weakened to make the new code pass.

## B. Schema / migration (SQLite + PostgreSQL parity, forward-only)

- **B1.** Fresh environment: `discover_migrations() == [1, 2, 3, 4]`;
  `apply_migrations()` yields `check_compatibility() == "OK"`; re-apply is a no-op
  (`CURRENT`), never `AHEAD`.
- **B2.** Legacy environment (applied `[1, 2, 3]`): `check_compatibility() ==
  "BEHIND"` before apply, `"OK"` after; `forge_schema_migrations` records version
  `4` with its identity; no table other than `forge_audit_events` (+ PG-only
  indexes) is created or altered.
- **B3.** `forge_audit_events` has: `BIGINT` PK, `event_id VARCHAR(36) UNIQUE NOT
  NULL`, `seq BIGINT NOT NULL` (monotonic allocation + ordered lookup, same
  contract as `retrieval_contexts`), `event_type`, `severity`, `occurred_at`,
  `request_id`, `actor_type`, `actor_id`, `resource`, `outcome`, `reason`,
  `details_json TEXT NOT NULL`, `is_authoritative`/`is_evidence`/`is_view`
  booleans, `created_at` NOT NULL — all NOT NULL where listed; no business
  columns (payloads, secrets, tokens, prompt/response text).
- **B4.** PG-only SQL (partial/index DDL, advisory lock) is exclusively in
  `004_postgres_specific.sql` under `POSTGRES_ONLY_MIGRATIONS`; the shared
  `004_audit_ledger.sql` parses and applies under **both** SQLite and PostgreSQL.
- **B5.** PostgreSQL env-gated tests pass on a real PG: table + all four indexes
  present (pg_catalog query), round-trip write/read, advisory-locked apply,
  failure-injection behaviors identical to SQLite.

## C. Durable ledger behavior

- **C1.** `ForgeObservabilityService.append_audit_event(...)` with a wired ledger
  writes one row (all NOT NULL columns populated) **and** returns within the
  bounded cache; without a ledger (`audit_ledger=None`) behavior is byte-identical
  to `689358d` (frozen `BoundedAuditTrail` only).
- **C2.** `event_id` uniqueness enforced (duplicate = idempotent no-op, no
  exception escapes); `seq` strictly monotonic per database.
- **C3.** Bounded: cache never exceeds `audit_durable.capacity`; eviction is FIFO;
  durable reads (`list_audit_events`) are bounded and ordered by `seq`.
- **C4.** Redaction: every stored/fallback event passes the existing
  observability redaction path first — a leak scan over the table contents and
  fallback records for `sk-`, `token`, `secret`, `password`, `authorization`
  patterns finds nothing (same pattern set as the frozen ServiceB leak scan).
- **C5.** Restart recovery: append → engine dispose → reopen (same file/URL) →
  re-run migrations (no-op) → all rows present, snapshot counts restored, next
  append succeeds. Captured in EVIDENCE.md with actual row counts.
- **C6.** Failure injection, per matrix in PLAN.md: no exception escapes the
  service API under `best_effort`; each fault leaves a visible fallback marker
  carrying the cause; telemetry flips to `NOT_OK` on fault and back to `OK` on
  recovery; `require_durable` + fault raises a typed error; the unsafe
  `unsafe_no_failover_postgres` combination is rejected at config time unless
  explicitly set.

## D. Architecture / separation (security isolation)

- **D1.** `app/forge/persistence/**` imports no `app.forge.observability` module
  (new guard test in `test_forge_cross_bloc.py`); `persistence/port.py` export set
  otherwise unchanged (existing export-discipline test passes).
- **D2.** Domain/provider import guards unchanged and green: K2/H3
  `_DOMAIN_MODULES`, providers-forbidden list, canonical kernel allowlist.
- **D3.** Book I evidence provenance (`corpus/canonical/**`, `app/forge/qa/**`,
  provenance/backfill modules) and Book VI entitlement authority
  (`entitlement`/usage audit surfaces) are **not modified** —
  `git diff --name-only 689358d..HEAD` contains no such paths.
- **D4.** Write sites are limited to the three frozen observation seams (session
  invalidation, policy denial, external revocation observed); policy
  configuration and rejection authority stay in frozen policy code; the ledger
  mirrors, never decides.

## E. Verification

- **E1.** Full local regression `python -m pytest tests/ -q`: **all tests pass**,
  count ≥ baseline **797** (baseline from `689358d`); zero failures, zero new
  skips outside the env-gated PG pattern.
- **E2.** `python -m compileall app` clean; `ruff check app tests` clean if
  configured (repo has no ruff config — record honestly if absent).
- **E3.** Pushed to `origin/forge`; **all** GitHub workflows green on the exact
  final remote SHA (not an earlier SHA); final SHA reported verbatim.
- **E4.** Evidence pack updated append-only: `EVIDENCE.md` (recovery evidence +
  test counts + separation check), `G-P4_GAP-03_RECONCILIATION.md`,
  `OPEN_GAP_REGISTER.md` (GAP-05 status → closed with pointer to EVIDENCE.md; no
  other gap row altered), `RATIFICATION_CHECKLIST.md` (GAP-05 item → satisfied by
  this rung), final `VERIFICATION.md`.
- **E5.** G-P4/GAP-03 reconciled against the frozen source text: the report states
  (a) what the frozen requirement demands, (b) which code now satisfies it, and
  (c) any **operator decision still required** (retention/compaction policy on the
  ledger table, ledger capacity sizing, `require_durable` promotion for production)
  — explicitly documented, not silently decided.
- **E6.** Implementation report delivered with: exact remote SHA, per-suite test
  counts (local + CI), gap-register changes, and an explicit readiness statement
  for Book II final evidence re-audit — including anything still open.

## F. Explicit non-goals

- No Book II ratification/freeze; no Book III+ scoping, scaffolding, or tests.
- No new third-party service, vendor, credential, or network sink (in-process /
  local DB only, per Ch II.2.1-4).
- No change to entitlement/usage accounting semantics, no brokerage surface, no
  public API route added by this rung.

## G. Amendments (rung 2; supersedes the matching plan details)

Recorded after recon against the code as found; acceptance bar unchanged:

- **G1 (B3 columns)**: `forge_audit_events` columns are: `seq BIGINT PK`,
  `event_id VARCHAR(36) UNIQUE NOT NULL`, `stream`, `event_type`, `severity`,
  `environment`, `occurred_at VARCHAR(64) NOT NULL`, `request_id`,
  `actor_type NOT NULL DEFAULT 'system'`, `actor_id`, `resource`, `outcome`,
  `reason`, `details_json TEXT NOT NULL`, `created_at TIMESTAMP NOT NULL
  DEFAULT CURRENT_TIMESTAMP` + four portable `CREATE INDEX IF NOT EXISTS`
  indexes. The plan's `is_authoritative/is_evidence/is_view` columns are
  DROPPED (Book I evidence-authority semantics — out of scope by GOVERNANCE §2);
  `stream` is restricted to the frozen `STREAMS` vocabulary.
- **G2 (single migration file)**: one portable `004_audit_ledger.sql` (the
  runner allows one file per version; PG-only content would be unnecessary
  anyway). Applicable sets: `[1,2,4]` SQLite / `[1,2,3,4]` PostgreSQL.
- **G3 (composition)**: `container.persistence` stays `None` in the composition
  root (frozen test pins it); the ledger gets a dedicated gateway built only
  when `FORGE_AUDIT_DURABLE_ENABLED=1`. No container.py change.
- **G4 (config)**: gate = `FORGE_AUDIT_DURABLE_ENABLED` (default off), URL =
  `FORGE_AUDIT_DURABLE_URL` else `FORGE_DATABASE_URL`; enabled-without-URL and
  enabled-without-observability both raise at config build; write policy ∈
  {`best_effort`, `require_durable`}; no `unsafe_no_failover_postgres` flag and
  no configurable table name.
- **G5 (write sites)**: durable mirrors live on the II.6 facade methods
  (policy decision, retrieval access, entitlement record, usage, plus new
  `record_authentication_event` with frozen `AUTHENTICATION_EVENT_TYPES`);
  ratified II.3 authentication / II.4 enforcement modules stay byte-identical.
- **G6 (pins)**: the six exact `[1, 2, 3]` migration-list pins advance to
  `[1, 2, 3, 4]` (precedent: `6a426de` advanced `[1, 2]` → `[1, 2, 3]`); pins
  remain exact and none is removed.
