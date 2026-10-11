# BOOK II — CROSS-BLOC ADVERSARIAL INTEGRATION & VERIFICATION — EVIDENCE.md

Status: EVIDENCE (append-only packet for Book II implementation-order step 7)
Date: 2026-10-11
Start SHA: `fdf5b0747a7afb18cc7ce96bb1255aab30a92fb9`
Planning freeze head: `60e067547b9d9165d94e4f074e0db0ba58e59e24` (ancestor of
HEAD, verified with `git merge-base --is-ancestor`).

**Scope statement:** this packet does NOT ratify or freeze Book II. It proves
(or fails) the cross-bloc integration gate only. `GAP_ADR_001` is carried
forward unchanged and OPEN (verified: `git diff fdf5b07..HEAD -- "*GAP_ADR*"`
is empty).

---

## 1. Commit ladder (append-only: PLAN → ACCEPTANCE → TEST → REPAIRS)

| Step | Commit | Contents |
|---|---|---|
| PLAN + ACCEPTANCE | `6afd55a` | `cross_bloc/PLAN.md`, `cross_bloc/ACCEPTANCE.md` (committed before any test existed) |
| TEST IMPLEMENTATION | `b559ca4` | `tests/test_forge_cross_bloc.py` (56 gates), verified RED pre-repair (see §5) |
| REPAIRS | `4b2d4ae` | `app/forge/observability/events.py` — typed-event-field scrub (the single repair, §5) |

No amend, reset, rebase, squash or force-push was used. Diffs against the
start SHA cover exactly four files:

```
app/forge/observability/events.py                  |   12 +-
implementation/forge/book_ii/cross_bloc/ACCEPTANCE.md | 233 ++++
implementation/forge/book_ii/cross_bloc/PLAN.md       | 163 +++
tests/test_forge_cross_bloc.py                     | 1890 +++++
```

**Untouched (empty `git diff fdf5b07..HEAD -- <path>`):** `.github/`,
`planning/`, `corpus/canonical/`, `app/forge/persistence/` (migrations +
gateway), `tests/test_forge_postgres_integration.py`, every Book I packet,
every Bloc II.1–II.6 packet, every `GAP_ADR*` file. Frozen planning documents
and prior ratifications were read, never modified.

---

## 2. Requirements mapping (exact executable gates)

Full clause-by-clause table lives in `ACCEPTANCE.md` §A–§O. Summary:

| Scenario | Acceptance clauses | Frozen requirement | Blocs exercised | Tests |
|---|---|---|---|---|
| X1 Identity → Policy → Provider | A1–A7 | Ch II.3.4, II.3.8, II.4.7, II.5.1; gate §Identity §Policy | II.3 + II.4 + II.5 | 7 |
| X2 Policy → Retrieval → Observability | B1–B5 | Ch II.4.4, II.4.7, II.6.1, II.6.2, II.6.5; gate §Policy §Observability | II.4 + I.4 + II.6 | 5 |
| X3 Provider → Failure → Policy | C1–C4 | Ch II.5.7, II.5.8, II.6.7; gate §Providers | II.5 + II.6 + II.4 | 4 |
| X4 Persistence → Concurrency → Audit | D1–D5 | Ch II.2.7, II.2.10; gate §Database | II.2 + II.6 | 5 |
| X5 QA → Provider → Evidence | E1–E4 | Book I claim/evidence law + Ch II.5.1; gate §Evidence pack | I.5 + II.5 | 4 |
| X6 Commerce → Identity → Entitlement | F1–F4 | Ch II.4.3, II.5.3, II.6.6; gate §Policy | II.3 + II.4 + II.5 | 4 |
| X7 Observability → Error → Security | G1–G5 | Ch II.6.2, II.6.7, II.6.8; gate §Observability | II.6 + II.5 + I.4 | 5 |
| X8 Provider Replacement → Domain Stability | H1–H3 | Ch II.5.6, II.5.9, II.5.10; gate §Providers | II.5 vs I/II.2/II.4/I.5 | 3 |
| X9 Lifecycle → Readiness → Failure | I1–I4 | Ch II.1.5, II.5.6; gate §Runtime | II.1 + II.5 + II.6 | 4 |
| F1–F12 failure injection | J1–J12 | Ch II.5.7, II.5.8, II.2.7, II.6.1, II.6.8 | all six Blocs | 12 |
| Phase 5 laws | K1–K7 | gate §Observability + epistemic laws | structural (AST) | 6 |

Frozen Book II acceptance-gate coverage map (Runtime / Database / Identity /
Policy / Providers / Observability / Evidence pack) is `ACCEPTANCE.md` §L:
each row is satisfied either by this packet or by a ratified prior suite
(II.1–II.6 + Book I), so no gate row is dropped.

All 19 acceptance-named classes/tests were verified to exist in the collected
suite (programmatic `ACCEPTANCE.md` ↔ `pytest --collect-only` cross-check:
missing = none).

---

## 3. Exact test execution (local, packet SHA)

Baseline carried forward: **890 passed, 19 skipped** (19 = the declared
`FORGE_TEST_DATABASE_URL` integration gap).

| # | Command | Result |
|---|---|---|
| 1 | `python -m pytest tests/test_forge_cross_bloc.py -q` | **56 passed** |
| 2 | Book II focused suites (`test_forge_service_composition, test_forge_persistence, test_forge_identity, test_forge_policy, test_forge_providers, test_forge_observability, test_forge_cross_bloc`) | **478 passed** |
| 3 | Book I canonical/retrieval/QA (`canonical, schemas, provenance, backfill, backfill_more, retrieval, qa, corpus_qa`) | **420 passed** |
| 4 | Signal Guard (`duplicate_signal, flip_logic, ghost_signal, state_engine, vision_confirm, vision_mcp`) | **48 passed** |
| 5 | Full local regression (`python -m pytest -q`) | **946 passed, 19 skipped** |
| 6 | PostgreSQL integration, approved local env (§4) | **19 passed** |
| 7 | Full suite under CI postgres-job semantics (live PostgreSQL) | **965 passed, 0 skipped** |

Deviation analysis: 946 = 890 baseline + 56 new cross-bloc gates; the 19
skips are unchanged (the declared PG gap, closed separately by runs 6–7).
No test was removed, weakened, skipped or xfailed.

Provider contract tests (`tests/provider_contract.py`) is a helper module
with no collected tests (it is imported by `test_forge_providers.py`, which
passes inside run 2). Observability redaction tests: `test_forge_observability.py`
= 104 passed (inside run 2). Persistence/concurrency tests:
`test_forge_persistence.py` (inside run 2).

---

## 4. PostgreSQL verification recovery (Phase 4 — the open gap)

### 4.1 Original failure preserved (verbatim)

Run `37989879501` (head `fec9be0`), job `postgres` = failure; job `test` =
success on the same run.

```
##[command]/usr/bin/docker pull postgres:16
Error response from daemon: toomanyrequests: You have reached your unauthenticated pull rate limit. https://www.docker.com/increase-rate-limit
##[warning]Docker pull failed with exit code 1, back off 4.684 seconds before retry.
##[command]/usr/bin/docker pull postgres:16
Error response from daemon: toomanyrequests: You have reached your unauthenticated pull rate limit. ...
##[command]/usr/bin/docker pull postgres:16
Error response from daemon: toomanyrequests: You have reached your unauthenticated pull rate limit. ...
##[error]Docker pull failed with exit code 1
```

(Run `37991271771`, head `0efc4de`, failed the same way: `postgres` =
failure, `test` = success.)

### 4.2 Classification

**Registry/network initialization failure, not an application or test
failure.** The GitHub Actions service container never started: zero tests
were collected or executed in the failed `postgres` jobs (the failure is at
the `docker pull` step, before checkout-dependent test execution), while the
`test` job on the same SHA passed. No migration, schema, gateway or test
code is implicated by these logs.

### 4.3 Retry of the existing job (unchanged workflow)

`gh run rerun 37991458041 --failed` → run `37991458041`, attempt 2, head
`fdf5b0747a7afb18cc7ce96bb1255aab30a92fb9`, conclusion **success**
(https://github.com/dabiggestpoppa/cerebus-trader/actions/runs/37991458041).

PostgreSQL job counts on that SHA:

| CI step | Result |
|---|---|
| Full suite against live PostgreSQL | **909 passed** |
| PostgreSQL integration evidence (`-v tests/test_forge_postgres_integration.py`) | **19 passed** |
| PostgreSQL II.3 identity & session evidence (`-k TestPostgresIdentitySession`) | **7 passed, 12 deselected** |
| `test` job (same run) | **890 passed, 19 skipped** |

### 4.4 Approved local PostgreSQL 16 environment (alternate runner)

Because CI rate-limit failures are repeatable, the unmodified suite was also
executed against a local PostgreSQL 16 server (CI-equivalent URL shape and
role):

```
FORGE_TEST_DATABASE_URL="postgresql+psycopg2://forge:forge_ci_password@127.0.0.1:5432/forge_test"
python -m pytest tests/test_forge_postgres_integration.py -q      -> 19 passed
FORGE_DATABASE_ENABLED=1 FORGE_DATABASE_URL=... FORGE_TEST_DATABASE_URL=... \
FORGE_MIGRATION_COMPATIBILITY_REQUIRED=1 python -m pytest -q     -> 965 passed, 0 skipped
```

Counts: **19 passed** (integration module), **965 passed / 0 skipped**
(full suite with the PG gap closed). SHA tested: this packet's HEAD (same
tree as §3; see `VERIFICATION.md` for the exact packet SHA).

Migration and test semantics were not changed: no migration file and no PG
test file appears in the diff (§1). No SQLite result is substituted for
PostgreSQL proof — the SQLite runs (§3) are supplemental, and the PostgreSQL
gate rests on §4.3 + §4.4.

### 4.5 Gate status

PostgreSQL executed successfully by two independent routes (CI service
container + approved local server). **The PostgreSQL verification gate is
not BLOCKED.**

---

## 5. Failure-injection matrix results (F1–F12, `TestFailureInjection`)

| ID | Injected failure | Verified outcome |
|---|---|---|
| F1 | Timeout (`FakeBehavior(latency>budget)`) | `ProviderTimeoutError`, no response object, decision matrix byte-identical, provider call counted but produced nothing |
| F2 | Retry/alternate | retryable ⇒ exactly one alternate delegation; non-retryable ⇒ raises, alternate never invoked |
| F3 | Duplicate commerce events | two audited facts with the same `event_id`; **no grant state exists**; policy still denies |
| F4 | Out-of-order events | delivery order preserved as data; no authority derived from ordering; decision unchanged in both orders |
| F5 | Rate limit | `RATE_LIMIT` / HTTP 429, safe message `rate limited`; commerce checkout raises, no success object |
| F6 | Malformed response | `DATA_INTEGRITY` / HTTP 500, sentinel-free envelope and events |
| F7 | Invalid session (corrupted token) | `AuthenticationFailure`, guarded loader never invoked (0 calls) |
| F8 | Revocation | the same raw token stops authorizing immediately (`revoked_session`); loader count unchanged |
| F9 | Concurrent write (one `expected_version`) | deterministic across 3 repeats: version 2 winner + `StaleWriteConflict` loser, final state identical each time |
| F10 | Provider recovery | OPEN → half-open probe after injected clock advance → CLOSED; readiness flips back to `READY` |
| F11 | Telemetry sink failure | emit never raises; `dropped_events` increments; response unaffected |
| F12 | Invalid correlation context | unsafe/absent ids rejected (`None`), scope regenerates an `fg-` id, outside scope ⇒ `unattributed` |

Cross-cutting result: **no injected failure produced an unauthorized
successful state transition** anywhere in X1–X9 or F1–F12.

---

## 6. Security and authorization proof (Phase 5)

- **Authorization precedes content access (K1).** Across a full mixed
  retrieval run, the protected loader received *exactly* the allowed object
  set: anonymous = `()` loads; member = allowed set minus RESEARCH_LAB;
  denied ∩ loaded = ∅.
- **Identity cannot reach protected operations (A1–A5).** Expired, revoked,
  missing, malformed and unknown credentials all fail inside II.3 before the
  policy/provider boundary; disabled users fail closed; the loader/provider
  spy count never moves. Positive control A6: valid session + capability
  loads exactly once.
- **Denied content never leaves the boundary (B1–B4).** Anonymous and member
  retrievals never load, return, cite or serialize the restricted record;
  the denial entry carries exactly `{object_id, exposure, reason_code}`;
  the retrieval-access audit carries exactly the nine frozen II.6.5 fields
  with `canonical_object_ids=()` on deny and the scope-bound correlation id.
- **No secrets/protected corpus in logs or telemetry (G1–G4, K7).**
  Sentinel sweep over serialized sink events, structured log lines (caplog
  at DEBUG), audit trails, metrics snapshots, HTTP bodies and error
  responses: zero hits — after the §7 repair.
- **Provider failures never grant (C1–C4).** The decision matrix (280
  decisions: 2 principals × 7 contexts × 5 resources × 4 actions) is
  byte-identical before, during and after provider outages; open circuits
  short-circuit without invoking the provider; commerce fallback mode `none`
  raises rather than synthesizing success.
- **Provider/commerce facts grant no entitlement (F1–F3).** Provider-shaped
  atoms (customer/subscription ids, plan names, status values) are disjoint
  from `REGISTERED_CAPABILITIES` and deny with `ENTITLEMENT_MISSING`; admin
  atoms widen nothing; recording a `grant` audit event changes no decision;
  external-identity linking changes no decision and collides fail closed.
- **Epistemic laws (K4–K6).** Answer assertions report the record's own
  status (no promotion), `ASSERT` only ever implies `VALIDATED`, and
  RESEARCH_FLAG/CANDIDATE/FALSIFIED records are never plain-assertable; AST
  proof of import discipline (domain ⇒ no providers/observability/fastapi;
  providers ⇒ no fastapi/sqlalchemy/httpx/requests); no entitlement
  state machine exists in `app/`; no brokerage/order-execution function or
  class exists anywhere under `app/forge/`.

---

## 7. Observability / redaction proof — defect found and repaired

**Finding (repaired, commit `4b2d4ae`).** `ForgeEvent.__post_init__` bounded
typed string fields (`model_id`, `operation`, `object_id`, `reason_code`, …)
but never scrubbed them; only `attributes` were scrubbed. A secret-shaped
value passed through any typed field therefore reached in-memory sinks,
structured log lines and diagnostics — contradicting the II.6 redaction law
("redaction happens HERE, inside event construction, before any sink") and
the gate clause "secrets/protected corpus absent from normal logs".

**RED evidence (test committed first, run against pre-repair code):**

```
FAILED tests/test_forge_cross_bloc.py::TestX7ObservabilityErrorSecurity::test_metrics_and_snapshot_are_content_free
E   AssertionError: sentinel 'sk-live-crossbloc-A1b2C3d4E5f6Gh7 leaked
E   ... is contained here: ake-model sk-live-crossbloc-A1b2C3d4E5f6Gh7", ...
1 failed in 0.54s
```

**Repair:** apply `scrub_text()` to typed string fields at construction,
after the existing length bound (oversized values still fail closed exactly
as before). Field set, vocabularies, ordering, determinism and attribute
redaction are unchanged; non-secret id/label values pass through identical.

**GREEN evidence:** cross-bloc suite 56 passed; ratified
`tests/test_forge_observability.py` **104 passed** (no ratified expectation
changed); full regression 946 passed.

No other repair was required: every other gate passed on the first
functional run.

---

## 8. Persistence / concurrency, provider replacement, readiness proofs

- **Persistence → concurrency → audit (D1–D5).** Stale-version writes raise
  `StaleWriteConflict` and leave the winner's state byte-identical;
  duplicates raise `DuplicateCanonicalObject`; a two-writer race over one
  snapshot yields exactly one winner with exactly one `success` and one
  `failure` fact recorded; a failed transaction rolls back the entire batch
  (both in-batch exception and commit-validation rejection paths) with no
  success event; the rejected write is never recorded as a successful
  canonical mutation.
- **Provider replacement (H1–H3).** Swapping a frozen registry of healthy
  fakes for one bound to a failing fake changes nothing in: canonical
  records (byte-equal), the 280-decision policy matrix, QA answer payloads;
  both registries' LLM fakes record **0 calls** across QA and policy; the
  only legitimate delta is the readiness health disclosure
  (`READY` vs `UNAVAILABLE`) — description, never authority.
- **Lifecycle → readiness → failure (I1–I4).** Unwired telemetry =
  `NOT_CONFIGURED`, wired-but-failing-sink telemetry = `READY`, both
  `required: false`, readiness overall `ready` in both cases; a provider
  outage is disclosed as `UNAVAILABLE` (never `READY`) while the core stays
  `ready`; an unavailable *required* dependency (persistence ping down)
  yields `not_ready`; `/forge/v1/ready` returns 200 with a failing sink,
  leaks nothing, and counts the drop.

---

## 9. Exact tests and CI runs

- New suite: `tests/test_forge_cross_bloc.py` — 56 tests, 11 classes
  (`TestX1…TestX9`, `TestFailureInjection`, `TestSecurityEpistemicLaws`).
- Local results: §3 (946/19; PG-attached 965/0; PG module 19).
- CI on start SHA `fdf5b07`: run `37991458041` attempt 2 — `test` success
  (890/19), `postgres` success (909 / 19 / 7). Original failure runs
  preserved: `37989879501` (`fec9be0`), `37991271771` (`0efc4de`).
- CI on the packet SHA: recorded in `VERIFICATION.md` (push + final CI
  verification, Phase 8).

---

## 10. Remaining limitations (honest gaps)

1. **`GAP_ADR_001` phase-order vs bloc-dependency contradiction is OPEN.**
   Not resolved, not closed, carried unchanged; the Phase C gate question
   stays with the operator.
2. **Book II is not ratified/frozen by this packet.** Evidence-pack
   preparation and Book-level ratification require separate authorization.
3. **Concurrency proof is deterministic sequential interleave** (two writers
   holding one `expected_version`), plus repeated-race determinism; true
   multi-threaded SQL races are exercised by the II.2 suite against live
   PostgreSQL in CI, not re-derived here.
4. **CI `postgres` job is exposed to Docker Hub unauthenticated pull rate
   limits** (infra). Two independent successful executions (§4.3, §4.4)
   close the verification gap for this packet, but a future run can hit the
   same `toomanyrequests` failure; the failure mode and remedy (rerun) are
   documented in §4.
5. **Book VI licensing/entitlement mutation is intentionally absent**, so
   X6 proves the *boundary* (provider facts cannot grant), not real
   entitlement lifecycle behavior.
6. **No concrete vendor adapters exist at Book II** (fakes only), so
   replacement stability is proven at the neutral-port level (Ch II.5.10),
   not against live vendor SDKs.

---

## 11. Book II final-closure readiness

The cross-bloc adversarial gate is satisfied: every acceptance clause in
`ACCEPTANCE.md` §A–§O verified, the single defect found was repaired with
RED→GREEN evidence, PostgreSQL executed by two routes with exact counts, and
no frozen artifact was modified. This packet declares the **cross-bloc
integration step complete** and states that the Book II evidence-pack
preparation (step 8 of the frozen order) *can be considered for
authorization* — the decision, and the Book II ratification (step 9), remain
with the operator.
