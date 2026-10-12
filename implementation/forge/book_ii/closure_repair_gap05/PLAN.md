# PLAN — Book II Gap Closure: GAP-05 Durable Audit / Event Ledger

**Execution:** Build Agent #14 · **Branch:** `forge` · **Start SHA:** `689358d3d879aed46a42360de85fb059204e7b29`
**Scope:** the one substantive closure-repair gap — a durable (PostgreSQL) audit/event
ledger for Book II observability — plus the G-P4/GAP-03 reconciliation it unblocks.
Build Agent #13's closure-repair report is the accepted baseline; this plan does not
repeat it.

**Authorization / prohibitions (Book #14):**

- Start from `689358d` on `forge`; PLAN + ACCEPTANCE are committed **before** any
  implementation (same pre-implementation rung order as every prior rung).
- Follow the frozen Book II requirements — Ch II.2.6 (audit events as immutable,
  bounded, redacted observability records) — with no requirement drift.
- Preserve the three-way separation: **Book II audit infrastructure** (this work)
  vs **Book I evidence provenance** (corpus/qa, untouched) vs **Book VI entitlement
  authority** (entitlement audit trail, untouched — still book-external).
- Do **not** ratify or freeze Book II. Do **not** begin Book III or any later Book.
  Only Book II evidence-pack registers and this rung's own directory are edited.
- Return: implementation report, exact remote SHA, test counts, gap-register
  changes, and re-audit readiness.

## Problem

GAP-05 (OPEN_GAP_REGISTER.md): *"No PostgreSQL audit/event ledger — Book II audit
events are in-memory only, so audit history does not survive process restart."*
Freeze evidence confirmed the symptom: no `audit_events` (or equivalent) table in
migrations 001–003, and `ForgeObservabilityService` keeps audits in a bounded
in-memory `BoundedAuditTrail`. Related: **G-P4 / GAP-03** — *"External token
revocation observed promptly vs recorded-before-read (Spec §8)"* — cannot be
closed while the record has no durable home.

## Frozen requirements this satisfies

- **Ch II.2.6:** audit events — immutable, bounded, redacted; persistence as an
  *implementation choice* (SQLite/PostgreSQL) behind the bounded service.
- **Ch II.2.1-4 (credential discipline):** no plaintext credentials / payload dumps;
  the ledger stores only redacted event envelopes.
- **Ch II.6 / II.5 observability seams:** config selects wiring; readiness
  discloses disabled/failure honestly (telemetry `OK` / `NOT_OK`).
- **Book 0 Spec §8 (as summarized in frozen GAP-03 text):** an observed external
  revocation must be *recorded before it can be read back*.
- **SQLite/PostgreSQL parity + forward migration** (freeze rules): both dialects
  fully exercised; migration adds tables only, `BEHIND → OK`, `AHEAD` unreachable
  for in-range databases.

## Architecture decision (decided at recon, after restart)

**Observability → Persistence → SQL, with a failover sink.**

```
ForgeObservabilityService.append_audit_event(...)      (service.py, bounded)
        │  redact(envelope)  ← observability.redaction (existing)
        ▼
DurableAuditLedger.append(...)                         (observability/audit_ledger.py, new)
        │  replay-bounded cache  →  AuditEventRecord dataclass
        ▼                                                 (persistence/records.py)
AuditEventPort (persistence/port.py)  →  SQL gateway + memory gateway
        ▼
004 migration: forge_audit_events (+ 004_postgres_specific: indexes,
                PG advisory-locked apply)                  (persistence/sql/)
```

**Failure containment (the key call):** persistence never imports observability —
a SQL fault cannot recurse through observability, because the **fallback sink lives
in observability code** (`audit_ledger.py`), which receives the exception and
handles it per configured write policy: `best_effort` (append-only fallback records
carrying the cause, telemetry `NOT_OK`) or `require_durable` (propagates a typed
error only for the explicitly unsafe config `unsafe_no_failover_postgres`). The
durable attempt is never silently dropped: every fault leaves a marker. Decisions:

1. **Policy constant `AUDIT_WRITE_POLICY_FAIL` lives in observability** —
   persistence stays observability-free (re-verified against the frozen K2/H3
   import guards: `_DOMAIN_MODULES` does not include persistence modules, and no
   test forbids observability → persistence).
2. **Storage value type is `str` (`details_json`, JSON-encoded)** — the frozen
   dataclass contract carries storage-level primitives; the gateway reads/writes
   JSON explicitly so SQLite `TEXT` and PostgreSQL `VARCHAR` behave identically.
   No polymorphic `dict | str` in the record contract.
3. **PG-only SQL lives in `004_postgres_specific.sql`**, listed in
   `POSTGRES_ONLY_MIGRATIONS` (existing escape hatch): advisory-lock
   `CREATE INDEX IF NOT EXISTS` for PG. Base `004` uses portable
   `BEGIN/COMMIT` + `IF NOT EXISTS` for both dialects — never PG-only syntax in
   the shared file (SQLite has no `ON CONFLICT`, no partial indexes).
4. **Sequence semantics on SQLite vs PostgreSQL:** `SERIAL`/`nextval` semantics
   diverge from SQLite `AUTOINCREMENT` under concurrent backfill — the port's
   contract is *monotonic allocation*, not gap-freedom, exactly like the frozen
   `retrieval_contexts(seq)` precedent; gap-freedom is not a Book II requirement.
5. **The durable trail is a second, larger bounded buffer** (capacity from
   `audit_durable.capacity`, default 10 000) + the append-only table. The frozen
   `BoundedAuditTrail` (audit.py) stays byte-identical and remains exported —
   requirement "bounded" means *both* tiers are bounded; the table is the durable,
   restart-surviving record. Retention/compaction policy on the table is an
   explicit **operator decision** recorded in EVIDENCE.md (appends are never
   rewritten — immutability holds regardless of when a retention job runs).

## Deliverables (files)

| # | File | Change |
|---|------|--------|
| 1 | `app/forge/persistence/sql/004_audit_ledger.sql` | **new** — portable `CREATE TABLE IF NOT EXISTS forge_audit_events` (BIGINT PK, `event_id VARCHAR(36) UNIQUE NOT NULL`, `seq BIGINT NOT NULL` — same allocation/lookup contract as `retrieval_contexts` — `event_type`, `severity`, `occurred_at`, `request_id`, `actor_type`, `actor_id`, `resource`, `outcome`, `reason`, `details_json TEXT NOT NULL`, `is_authoritative`, `is_evidence`, `is_view` booleans, `created_at`) |
| 2 | `app/forge/persistence/sql/004_postgres_specific.sql` | **new** — PG-only: partial index on `seq`, indexes on `(event_type, occurred_at)`, `(request_id)`, `(actor_type, actor_id)`; listed in `POSTGRES_ONLY_MIGRATIONS` |
| 3 | `app/forge/persistence/sql/migrations.py` | add `4` to `MIGRATION_VERSIONS`, `"004_audit_ledger"`/`"004_postgres_specific"` identities, PG-only list wiring (mirror 003 exactly) |
| 4 | `app/forge/persistence/records.py` | `AuditEventRecord` dataclass + row codec (write bindings / read `to_audit_event`), storage-value `str` for `details_json` |
| 5 | `app/forge/persistence/port.py` | `AuditEventPort` ABC (`append_audit_event`, `list_audit_events`) + `MemoryPersistenceGateway` local-bounded impl — **export set otherwise untouched** (frozen export-discipline test) |
| 6 | `app/forge/persistence/sql/gateway.py` | SQL `append_audit_event` (INSERT, sequence allocation, idempotent by `event_id`) + `list_audit_events` (bounded, ordered); gateway imports no observability module |
| 7 | `app/forge/observability/audit_ledger.py` | **new** — `DurableAuditLedger`: envelope → redaction → port append → bounded replay cache; typed failure handling + failover markers; write-policy constants |
| 8 | `app/forge/observability/service.py` | `audit_ledger: DurableAuditLedger | None = None` (default None = current behavior); `append_audit_event(...)`/`durable_audit_events(...)` methods; snapshot gains `durable_audit_*` only when configured; `observability_from_config(config, persistence=None)` factory wires it when `config.audit_durable.enabled` |
| 9 | `app/forge/config.py` | `AuditDurableConfig` frozen dataclass: `enabled`, `database_url`, `table`, `capacity`, `write_policy`, `max_batch`; defaults: enabled only when `DATABASE_URL` set, `database_url` = `DATABASE_URL`, `capacity=10000`, `write_policy="best_effort"`, `unsafe_no_failover_postgres=False` |
| 10 | `app/forge/service/container.py` | optional `persistence: PersistencePort | None = None` field (defaulted; composition tests untouched) |
| 11 | `app/main.py` | composition root: build `observability_from_config(cfg, persistence)`; if `audit_durable.enabled` and no persistence → raise `ForgeConfigurationError` (fail-closed: never silently in-memory); SQLite file DB allowed, URL parsing decides dialect (existing gateway policy) |
| 12 | `app/forge/service/authentication.py` | **write site A** — session invalidation already records `session_invalidated` in the frozen trail; mirror into durable when wired |
| 13 | `app/forge/service/policy_enforcement.py` | **write site B** — policy denial (`policy_denied`) durable mirror; denial authority stays in frozen policy code |
| 14 | `app/forge/providers/registry.py` (or the existing revocation-detection site found at recon) | **write site C** — external token revocation *observed* → durable `external_token_revocation_observed` written **before** the observation is read back (GAP-03 semantics) |
| 15 | `tests/test_forge_audit_ledger.py` | **new** — see Testing |
| 16 | `tests/test_forge_persistence.py` / `test_forge_postgres_integration.py` | migration-registry `[1,2,3,4]`, schema check, PG env-gated ledger suite (mirror 003 patterns) |
| 17 | `tests/test_forge_cross_bloc.py` | two small guard additions: `persistence/records.py` + `persistence/port.py` import no `app.forge.observability` (locks architecture decision #1); ledger write sites stay in the frozen per-scope observation seam |
| 18 | `tests/test_forge_observability.py` | regression: default `observability_from_config(config)` unchanged behavior, snapshot shape when unconfigured |
| 19 | Evidence pack | `EVIDENCE.md` (recovery evidence + counts), `G-P4_GAP-03_RECONCILIATION.md`, `OPEN_GAP_REGISTER.md` GAP-05 → closed (append-only status column), `RATIFICATION_CHECKLIST.md` GAP-05 item updated, final `VERIFICATION.md` |

No file outside Book II implementation/ + Book II evidence-pack registers + this
rung's directory is modified. Corpus canonical (Book I), `app/forge/qa/*`,
entitlement/usage audit (Book VI), and all six `bloc_ii_*/` ratified artifacts are
untouched.

## Failure-injection matrix (tests must cover every row)

| Fault | Injection | Required behavior |
|-------|-----------|-------------------|
| Table missing | engine with migrations not applied | typed exception → failover marker (`best_effort`) / typed raise (`require_durable`); no crash of service API |
| SQL constraint error | `event_id` duplicate / bad binding | caught; duplicate = idempotent no-op, others = marker/typed raise |
| Connection dropped | gateway raises `OperationalError`-like | caught; marker records cause; telemetry `NOT_OK` |
| Ledger unwired | `audit_ledger=None` | append still records to frozen trail (exact current behavior) |
| Policy fail-closed | `require_durable` + fault | typed `ForgeConfigurationError`-family raise; app config-time precheck prevents unsafe combos (`unsafe_no_failover_postgres` gate) |
| Redaction failure | attributes carrying `sk-*`/tokens | secrets never reach table or fallback logs (leak scan) |
| Recovery | dispose engine → reopen → re-migrate | rows + bounded cache + snapshot counts survive; next append succeeds |

## Testing

- **New `tests/test_forge_audit_ledger.py`** (~20 tests): write/read round-trip,
  monotonic seq, unique `event_id`, bounded cache eviction, redaction before
  storage, unmapped envelope fallback path, write-site mirrors (authn, policy,
  revocation) via the same event-type table already used by frozen tests, full
  failure-injection matrix above, fail-closed config gate, restart-recovery
  evidence (fresh DB → append → dispose → reopen → rows visible).
- **Persistence suite**: migration registry `[1, 2, 3, 4]` on fresh *and* legacy
  (1,2,3) environments; `check_compatibility()` `BEHIND → OK`, `AHEAD`
  unreachable; idempotent re-apply; schema-table assertions unchanged.
- **PostgreSQL env-gated** (`FORGE_POSTGRES_TEST_URL` / `DATABASE_URL`, existing
  skip pattern): PG dialect table + PG-only indexes + advisory-locked apply,
  round-trip, failure-injection on real PG, existing 003 parity suite still green.
- **Regression:** full `python -m pytest tests/ -q` (baseline **797 passed** on
  `689358d`); `python -m compileall app` clean; `ruff check app tests` clean if
  configured. CI: `.github/workflows/forge-tests.yml` + all other workflows green
  on the final remote SHA.
- **Separation check:** `git diff --name-only 689358d..HEAD` shows no
  corpus/qa/entitlement/bloc artifact paths (asserted in the report).

## Rungs

1. **PLAN + ACCEPTANCE committed before implementation** (this commit).
2. Implementation — migration 004 (+ PG-specific), port/gateway/records, ledger,
   config/container/composition, three write sites.
3. Tests — new ledger suite + persistence/PG/observability regressions + guard
   additions; full local regression green.
4. Push + CI verification on the remote SHA; append-only iteration on failures.
5. Evidence — `EVIDENCE.md` (recovery evidence, counts), G-P4/GAP-03
   reconciliation, gap-register updates (GAP-05 closed; no other gap touched).
6. Final `VERIFICATION.md` + push + final CI on the remote SHA.
7. Implementation report: remote SHA, test counts, gap-register changes,
   re-audit readiness; explicit statement that Book II is **not** ratified here.

## Risks / mitigations

- **Dataclass field addition** in frozen `records.py` — append-only field, frozen
  export set untouched; exercised only by the new codec tests.
- **SQLite DDL in transaction** — mirrors the known-good 003 file byte-for-byte in
  structure; base file is pure portable SQL, PG-only statements quarantined.
- **Composition-root behavior change** — only when `DATABASE_URL` is set (opt-in
  durable); unset path is byte-identical to `689358d` (regression test pins it).
- **Postgres suite locally skipped** without an engine — CI's PG job is the
  authority; env-gated tests are written to the frozen skip pattern so they run
  there, and the report will state plainly which PG tests ran where.

## Amendments (rung 2, recorded before test/verification rungs)

Four pre-implementation assumptions were corrected against the code as found;
nothing below changes the acceptance bar, and every change is reflected in
ACCEPTANCE.md's amended criteria:

1. **Migration mechanism** — the runner discovers ONE file per version number
   (`^(\d{3})_…\.sql`, collision = RuntimeError) with a `-- FORGE dialect:
   postgresql` header as the dialect switch; there is no multi-file-per-version
   mechanism (the plan's separate `004_postgres_specific.sql` would collide).
   Decision: **one portable `004_audit_ledger.sql`** — table + `CREATE INDEX IF
   NOT EXISTS` indexes, all valid on SQLite and PostgreSQL — so SQLite (the
   local dialect-truth harness) exercises the full ledger schema. No PG-only
   DDL is needed; the advisory-lock idea was dropped (no frozen requirement,
   and the runner has no cross-dialect lock primitive). Note: 003 is PG-only,
   so applicable sets are `[1,2,4]` (SQLite) / `[1,2,3,4]` (PostgreSQL), both
   satisfying `check_compatibility() == OK`.
2. **Container seam** — `ForgeServiceContainer` already accepts `persistence`,
   and the frozen test `test_migration_runner_not_invoked_by_import` pins
   `_build_forge_container().persistence is None`. No container change: the
   composition root builds a **dedicated gateway for the ledger** only when
   `audit_durable.enabled`, without touching the container's persistence/readiness
   seam (wiring whole-app persistence remains a separate operator decision).
3. **Config gate** — enabled via `FORGE_AUDIT_DURABLE_ENABLED` (default OFF),
   URL from `FORGE_AUDIT_DURABLE_URL` falling back to `FORGE_DATABASE_URL`;
   enabled-without-URL raises at config build (fail closed). The invented
   `unsafe_no_failover_postgres` flag and the configurable `table` field were
   dropped: write policy is exactly `best_effort` (default) or
   `require_durable`, and the table name is the migration's constant
   `forge_audit_events`. Enabling with `observability_enabled=False` also
   raises (the ledger lives behind the observability seam).
4. **Schema vocabulary** — the plan's `is_authoritative/is_evidence/is_view`
   columns were dropped: those are Book I evidence-authority semantics and
   putting them in an operational audit table would blur the GOVERNANCE §2
   separation this packet exists to preserve. Added instead: `stream`
   (restricted to the frozen `STREAMS` vocabulary — `security_audit`,
   `usage_ledger`, `entitlement_audit`) + `environment`. Durable stream labels
   never invent tokens outside the frozen vocabulary; the Ch II.2.6 record
   classes are named by `event_type` (`policy.allow/deny`, `retrieval.access`,
   `entitlement.*`, `provider.usage`, authentication/security vocabulary
   `AUTHENTICATION_EVENT_TYPES`).
5. **Write sites** — deeper recon showed authentication, policy enforcement and
   routes hold NO observability wiring at all at Book II (audit bridging is
   test-driven today; serving paths arrive with later Books). Rather than
   injecting observability into the ratified II.3/II.4 modules, the durable
   mirrors live on the **II.6 service facade** (`record_policy_decision`,
   `record_retrieval_access`, `record_entitlement_event`, `record_usage`, plus
   a new vocabulary-validated `record_authentication_event`) — every stream's
   single existing observation seam. This keeps the ratified II.3/II.4 modules
   byte-identical and honors "the ledger mirrors, never decides".
6. **Version pins** — six existing tests pin the exact migration list
   `[1, 2, 3]` (policy/qa/retrieval/vector/postgres/backup); they advance to
   `[1, 2, 3, 4]`, exactly as closure-repair rung 4 advanced them from `[1, 2]`
   when 003 was added (precedent commit `6a426de`). Pins stay exact; none is
   weakened or removed.
7. **seq allocation** — no auto-increment idiom is portable across both
   dialects (001/002 use natural keys only), so `seq` is allocated as
   `MAX(seq)+1` by the gateway inside a bounded unique-violation retry, and
   each append commits its own durable unit (unless an explicit gateway
   transaction is open) — giving record-before-read and restart survival.
8. **G-P4/GAP-03 paraphrase corrected** — the Problem statement above
   paraphrased G-P4/GAP-03 as "external token revocation observed promptly
   vs recorded-before-read (Spec §8)". That wording is not in the frozen
   sources; the authoritative anchors are the Book II plan gate bullet
   "entitlement revocation observed promptly", ACCEPTANCE_MATRIX row G-P4
   (state Q), OPEN_GAP_REGISTER row GAP-03 (classification D, Book VI), and
   the RATIFICATION_CHECKLIST operator-confirmation item. The reconciliation
   against those anchors is `G-P4_GAP-03_RECONCILIATION.md` in this
   directory; no requirement relied on the incorrect paraphrase.
9. **K5/K7 import law (frozen)** — XB
   `test_security_audit_is_distinct_from_provenance` forbids the
   observability package from importing `app.forge.persistence` (as well as
   provenance). The pre-implementation assumption that observability could
   import `AuditEventRecord` was wrong; the built design hands the record
   duck-shaped (`LedgerEvent`) and persistence coerces it
   (`persistence.port.coerce_audit_event`), keeping observability
   persistence-free while the ledger stays in the observability package.
