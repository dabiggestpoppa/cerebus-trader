# EVIDENCE — GAP-05 Durable Audit / Event Ledger (Build Agent #14)

**Branch:** `forge` · **Start SHA:** `689358d3d879aed46a42360de85fb059204e7b29`
**Ladder (append-only):**

| Rung | SHA | Content |
|---|---|---|
| 1 (pre-implementation) | `6d1de17` | `PLAN.md` + `ACCEPTANCE.md` committed BEFORE any implementation (CI run 38255649571 green) |
| 2–4 (implementation + tests + local regression) | `3529a0da452c8cd1d94d2f1ee49640d29ce32288` | migration 004 + port/gateway/ledger/config/composition + `tests/test_forge_audit_ledger.py` + six pin advances + amended PLAN/ACCEPTANCE (rung-2 amendment appendix) |
| 5 (CI verification) | `3529a0d` | **run 38261712088 — BOTH jobs green** (details §8) |

Nothing here ratifies or freezes Book II; no Book III+ file is touched.

## 1. Frozen requirement executed

`BOOK_II_FORGE_CORE_PLATFORM_PLAN_V1.md` **Ch II.2.6 Audit/event ledger**:
append-oriented records for (i) authentication/security events, (ii) policy
decisions, (iii) protected retrieval access, (iv) entitlement changes,
(v) provider event ingestion/reconciliation, (vi) administrative mutations —
"payloads must avoid secrets and unnecessary corpus content".
Ownership split per `closure_repair/GOVERNANCE.md` §2: Book II owns durable
operational/security audit infrastructure; Book VI owns entitlement business
meaning; Book I owns evidence provenance.

**Mapping to this packet (all six classes durable):**

| Ch II.2.6 class | Durable write seam (`ForgeObservabilityService`) | stream / event_type |
|---|---|---|
| policy decisions | `record_policy_decision` mirror | `security_audit` / `policy.allow`, `policy.deny` |
| protected retrieval access | `record_retrieval_access` mirror | `security_audit` / `retrieval.access` |
| entitlement changes | `record_entitlement_event` mirror (RECORD only — II.6 RAT 4) | `entitlement_audit` / `entitlement.{grant,renew,grace,expire,revoke,admin_correction}` |
| provider events | `record_usage` mirror (counts/ids only) | `usage_ledger` / `provider.usage` |
| authentication/security events | new `record_authentication_event` (vocabulary-validated) | `security_audit` / `AUTHENTICATION_EVENT_TYPES` (session_opened, session_revoked, sessions_revoked_all, authentication_failed, identity_linked) |
| administrative mutations | session revocation via the authentication vocabulary above (admin/support revoke path, II.3 docstring) | `security_audit` |

Durable stream labels never leave the frozen `STREAMS` vocabulary
(`telemetry, security_audit, usage_ledger, entitlement_audit`) — enforced by
`test_durable_streams_stay_in_frozen_vocabulary`.

## 2. Architecture (as-built, incl. the frozen K5/K7 correction)

```
ForgeObservabilityService.record_*  (existing II.6 seams; ratify nothing new)
        │  _durable(...)  → DurableAuditLedger.append_event   [observability]
        │      redaction: safe_attributes/scrub/bounded (BEFORE storage)
        │      bounded replay cache (capacity, FIFO) + fallback markers
        ▼
AuditEventPort (persistence) — record handed over duck-shaped as `LedgerEvent`
        │  coerce_audit_event() normalizes at the boundary; seq/created_at
        │  are persistence-owned (caller values ignored)
        ▼
SqlAlchemyPersistenceGateway.append_audit_event  /  InMemoryPersistenceGateway
        │  seq = MAX(seq)+1 with bounded unique-violation retry; idempotent
        │  by event_id; own commit per append (record-before-read)
        ▼
forge_audit_events  (migration 004 — PORTABLE: SQLite + PostgreSQL)
```

**Frozen constraint discovered during implementation (K5/K7, XB
`test_security_audit_is_distinct_from_provenance`):** the observability
package may import NEITHER `app.forge.provenance` NOR `app.forge.persistence`.
The first implementation commit's pre-image violated this (type imports) and
the guard caught it in the full run; resolution: observability owns
`LedgerEvent` (same field names), persistence coerces via
`coerce_audit_event` (`port.py`), and `durable_audit_events()` returns
duck-typed records. Final tree: observability imports zero persistence or
provenance modules (guard green), persistence imports zero observability
modules (guard `test_persistence_never_imports_observability` green).
Failover lives on the observability side — a SQL fault cannot recurse.

## 3. Schema evidence (local, SQLite dialect truth)

- `discover_migrations() == [1, 2, 3, 4]`, `migrations[4].identity ==
  "004_audit_ledger"`, `postgresql_only is False` (004 is PORTABLE; only 003
  is PG-only). Applicable sets: SQLite `[1,2,4]`, PostgreSQL `[1,2,3,4]`;
  both `check_compatibility() == "OK"` after apply.
- Fresh SQLite exact table set (test-asserted equality):
  `{forge_schema_migrations, canonical_objects, canonical_references,
  artifacts, provenance_edges, forge_users, external_identity_links,
  forge_sessions, forge_audit_events}` — no `retrieval_vectors` (003 PG-only,
  pre-existing), **no Book VI business table** (`entitlements, licenses,
  plans, products, subscriptions, policies, policy_decisions` asserted absent).
- Columns (PRAGMA-asserted): `seq BIGINT PK`, `event_id VARCHAR(36) UNIQUE
  NOT NULL`, `stream/event_type/severity/environment/occurred_at/
  actor_type/outcome/details_json/created_at` NOT NULL as designed,
  `request_id/actor_id` nullable; four `CREATE INDEX IF NOT EXISTS` indexes
  present (`stream_time`, `type_time`, `request`, `actor`).
- Legacy upgrade path: applied `{1,2,3}`+no table → `BEHIND` → apply →
  `APPLIED` → `OK`; re-apply `CURRENT` (never `AHEAD`); import runs nothing.
- The plan's pre-recon schema drafts were amended (rung-2 appendix G1): the
  evidence-authority columns (`is_authoritative/is_evidence/is_view`) were
  REMOVED before implementation — Book I evidence semantics have no place in
  an operational audit table (GOVERNANCE §2 separation preserved).

## 4. Round-trip evidence (five seams, local)

`tests/test_forge_audit_ledger.py` (41 passed local + 2 PG-gated):

- All five seams write durable rows with expected stream, event_type,
  severity, fact-time `occurred_at` (caller time wins over clock), request
  id, actor, outcome, redacted `details_json` (e.g. policy deny row:
  `resource=CANONICAL:MOD.TEST.AUDIT`, `reason=NO_MATCH`,
  `details={"authenticated": true}`).
- seq strictly monotonic across appends; event_id UUID-unique (fits
  VARCHAR(36)); **duplicate append of a stored event_id → False, one row**
  (idempotency on the real unique constraint, SQL + PG).
- **recorded-before-read:** an appended fact is immediately returned by
  `durable_audit_events()` / `list_audit_events()` (GAP-03 seam semantics).
- Bounded: cache FIFO holds exactly `capacity` (newest survive; store keeps
  every append — append-oriented); `list` honors `limit` and `stream` filter;
  fallback trail bounded with `fallback_appends` totalling every fault.
- Unwired service (default): every mirror is a no-op, snapshot has NO
  `durable_audit` key, `durable_audit_events() == ()` — byte-identical
  pre-GAP-05 behavior (regression-pinned).

## 5. Redaction evidence (before storage — §1 payload rule)

| Input detail | Stored value (observed) |
|---|---|
| `note: "token=supersecretvalue1234567890"` | `"[redacted] [redacted]"` (both secrets scrubbed) |
| `header: "Bearer abcdefghijklmnopqrstuvwx"` | `[redacted]` |
| 42-char opaque run | `[redacted]` (≥40-char rule; scrub runs BEFORE bound) |
| `resource: "sk-abcdef1234567890"` | `[redacted]` |
| nested dict `{"payload": {...}}` | `{"_details": "details_rejected_not_scalar_or_too_many"}` — no corpus text |
| 17 attributes (>16 cap) | same collapse marker |
| 660-char non-secret string | `"[truncated] 660 chars"` — value omitted entirely, no partial content |

Leak-scan assertion over the whole stored row (`details_json + reason +
resource + actor_id + request_id`) finds no fragment of any planted secret.

## 6. Failure-injection matrix (executed locally, SQLite)

| # | Fault | Policy | Observed behavior |
|---|---|---|---|
| 1 | table missing (DROP + version row removed) | `best_effort` | append returns False; no exception; `status=NOT_OK`, `fallback_appends=1`, `last_error_kind=PERSISTENCE_UNAVAILABLE`; `FallbackAuditMarker(stream, event_type, cause_kind)` retained |
| 2 | recovery after #1 (`apply_migrations() → APPLIED`) | `best_effort` | next append True; `status=OK`; only the recovered event readable |
| 3 | connection closed | `best_effort` | same contained marker path (`ClosedConnection…`-class cause) |
| 4 | table missing | `require_durable` | typed `DurableAuditWriteError(kind)`; `kind` is a redacted token (asserted: no URL/db string in message) |
| 5 | memory gateway `simulate_unavailable` | `best_effort` | contained marker; parity path (healthy memory) stores with seq=1 |
| 6 | config: enabled w/o URL; enabled w/o observability; capacity 0; bad policy; `require_durable` w/o enabled; env enabled w/o any URL; factory enabled w/o port | config-time | all raise `ValueError` at build (fail closed — never silently in-memory) |
| 7 | ledger unwired (default) | n/a | mirrors no-op; snapshot shape unchanged |

`require_durable` promotion and `best_effort` are the ONLY policies (the
plan's draft `unsafe_no_failover_postgres` flag was dropped in rung-2
amendment G4 — no silent unsafe mode exists).

## 7. Restart-recovery evidence (durability proof)

File-backed SQLite (`tmp_path/audit_restart.db`):

1. fresh engine → `apply_migrations() == APPLIED` → service append
   (`session_revoked`, `resource=restart-proof`, fact time
   `2026-10-12T00:10:00+00:00`) → True;
2. `engine.dispose()` (process-death simulation);
3. new engine → `apply_migrations() == CURRENT`, `check_compatibility() == OK`
   → **row survives**: same `event_id`, `seq == 1`, same resource and
   fact-time; details round-trip;
4. next append after restart → True, `seq == 2` (sequence continues).

Migration-fault-across-restart variant: partial schema (table dropped,
version row gone) → reopen → `BEHIND` → apply → `APPLIED` → `OK` → append
succeeds. Both scenarios are test-asserted (`TestRestartRecovery`).

## 8. PostgreSQL execution (CI authority)

**Run 38261712088 on `3529a0d` — both jobs `success`:**

| Job | Result | Counts |
|---|---|---|
| `test` (no PG) | success | **1016 passed, 29 skipped** (29 = 27 baseline skips + this packet's 2 PG-gated tests) |
| `postgres` (live PG 16 + pgvector, `FORGE_MIGRATION_COMPATIBILITY_REQUIRED=1`) | success | **1045 passed, 0 skipped** (baseline at closure repair: 1002/0 → exact +43 = this packet's new tests) |
| postgres evidence rerun: `test_forge_postgres_integration.py` | success | 19 passed |
| postgres evidence rerun: `-k TestPostgresIdentitySession` | success | 7 passed |

PG-specific assertions executed on the live server
(`TestPostgresAuditLedger`): migrations apply with `004` recorded
(`[1,2,3,4]`, identity + `postgresql_only` pins), all six indexes exist
(`forge_audit_events_pkey`, `..._event_id_key`, four `idx_...`), round trip
with monotonic seq + idempotent duplicate + **cross-connection visibility**
(second engine connection counts the committed rows), re-apply `CURRENT`.

## 9. Test counts and baseline arithmetic

| Point | Command | Result |
|---|---|---|
| Baseline `689358d` (in-tree) | `python -m pytest -q` | **975 passed, 27 skipped** (1002 total) |
| This packet | `python -m pytest -q` | **1016 passed, 29 skipped** (1045 total; +41 passed +2 PG skips = new file) |
| CI `test` job @ `3529a0d` | `python -m pytest -q` | 1016 passed, 29 skipped |
| CI `postgres` job @ `3529a0d` | `python -m pytest -q` | 1045 passed, 0 skipped |
| New suite local | `pytest tests/test_forge_audit_ledger.py -q` | 41 passed, 2 skipped (PG-gated) |
| compile | `python -m compileall app` | clean |

Measurement note: a throwaway worktree at `689358d` reported 973+2 because a
fresh Windows checkout materializes CRLF and two file-hash pins
(`001_initial_schema.sql`, `policy.py`) are LF-pinned; in-tree and in CI
(LF checkouts) those tests pass — the in-tree baseline (975/27) is the
comparable figure. No lint config exists in the repo (no `pyproject.toml`/
`pytest.ini`/ruff setup) — recorded honestly; compile + full pytest are the
local gates. Six exact migration pins advanced `[1,2,3] → [1,2,3,4]`
(`test_forge_policy`, `test_forge_qa`, `test_forge_retrieval`,
`test_forge_vector_projection`, `test_forge_postgres_integration`,
`test_forge_backup_restore`) plus the `identities` dict pin — precedent:
closure-repair rung 4 advanced the same pins from `[1,2]` in commit
`6a426de` when 003 was added. No test was deleted, skipped or weakened.

## 10. Separation checks (Book I / Book VI / ratified Book II surfaces)

- `git diff --name-only 689358d..3529a0d`: 19 files — only
  `app/main.py` + `app/forge/config.py` (composition),
  `app/forge/observability/*` (ledger + mirrors), `app/forge/persistence/*`
  (record/port/gateways/ migration), 7 test files, and this packet's own
  directory.
  **Zero** paths under `corpus/`, `app/forge/qa/`, `app/forge/provenance*`,
  `app/forge/backfill/`, `app/forge/policy.py`,
  `app/forge/service/{authentication,policy_enforcement}.py`, and all six
  ratified `bloc_ii_*/` artifacts.
- Guard tests (new, green): persistence never imports observability (AST over
  `app/forge/persistence/**`); Book I/II domain+providers+qa+retrieval never
  import `audit_ledger`; no Book VI business table created; durable streams ⊆
  frozen `STREAMS`; `AUTHENTICATION_EVENT_TYPES` exact frozen set.
- Frozen K5/K7 law re-verified green after the rung-2 coercion refactor
  (`XB::test_security_audit_is_distinct_from_provenance`).
- Entitlement records are RECORDS ONLY (`entitlement_audit` stream rows);
  no entitlement state machine, resolver or business table exists (frozen
  XB `test_no_entitlement_state_machine_exists` green).
- Existing redaction/Service-B leak scans and the G-O3 suite remain green.

## 11. Known gaps, operator decisions still required

1. **Retention/compaction policy on `forge_audit_events` is NOT decided
   here.** The table is append-oriented; appends never rewrite history.
   When/if an operator adds a retention job, that needs its own authorized
   packet (immutability holds regardless of when old rows are archived).
2. **Production write policy:** default is `best_effort` (telemetry serves;
   faults are contained + visible as `NOT_OK`/fallback markers). Promoting
   `require_durable` (fail serving on audit-write failure) is an operator
   decision, explicit via `FORGE_AUDIT_DURABLE_WRITE_POLICY=require_durable`.
3. **Migration application is explicit** (frozen rule: never a startup/import
   side effect). An operator enabling `FORGE_AUDIT_DURABLE_ENABLED=1` must
   apply migration 004 first; until then appends degrade to bounded fallback
   markers with `NOT_OK` status — visible, never a crash, never silently
   in-memory-only.
4. **Container-level persistence seam stays unwired** (frozen test pins
   `_build_forge_container().persistence is None`); the ledger builds its own
   gateway. Wiring whole-app persistence/readiness (`ForgeLifecycle` ping +
   migration status) remains a separate operator-scoped decision.
5. **Fault matrix ran on SQLite locally** (executed in CI's `test` job too);
   PG CI execution covers schema/constraints/round-trip/idempotency/cross-
   connection visibility — the shared gateway fault paths are dialect-neutral
   and are additionally executed on PG by any future fault-suite extension.
6. **Book II remains UNRATIFIED**; the evidence pack verdict changes only on
   operator re-audit (GAP-05 row → C, re-audit pending).

## Exact commands

```bash
python -m compileall app                     # clean
python -m pytest tests/test_forge_audit_ledger.py -q   # 41 passed, 2 skipped (local)
python -m pytest -q                          # 1016 passed, 29 skipped (local)
# CI (fork of .github/workflows/forge-tests.yml), run 38261712088 on 3529a0d:
#   test job:      1016 passed, 29 skipped
#   postgres job:  1045 passed, 0 skipped  (+ 19 / 7 evidence reruns)
```
