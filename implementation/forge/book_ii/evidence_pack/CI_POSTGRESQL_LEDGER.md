# BOOK II — CI / POSTGRESQL VERIFICATION LEDGER

Evidence head: `ae35276`. Every row is a real `gh` query result recorded in
this assignment or quoted verbatim from the committed bloc packets.
Workflow under test throughout: `.github/workflows/forge-tests.yml` (two
jobs: `test` = plain suite; `postgres` = live PostgreSQL 16 service,
`FORGE_TEST_DATABASE_URL` set, full suite + `-v` integration module +
`-k TestPostgresIdentitySession`). **Since the closure repair (rows L-15+) the
service image is `pgvector/pgvector:pg16`** — the frozen gate G-D1 names
"empty Postgres+pgvector → current schema", so the acceptance database must
be Postgres WITH pgvector; same jobs, same env vars, same tests (see
`closure_repair/PLAN.md` §2).

## 1. Classification key

- **PASS** — job completed `success`; tests actually executed.
- **FAIL(app)** — job failed because of application/test defects (repaired
  append-only; never claimed as a pass).
- **FAIL(infra)** — job failed before any test executed (runner/registry);
  recorded as an open gap for that head, never claimed as a pass.
- “PG executed” claims appear only where the `postgres` job succeeded or the
  approved local PostgreSQL run executed the tests.

## 2. Ledger

| ID | Run | Head | Jobs | Counts (executed) | Classification / note |
|---|---|---|---|---|---|
| L-01 | 37627625500 | `2d5a8e6` (II.2 repairs) | `test` ✅ `postgres` ✅ | full suite 217; PG module **6 executed** | PASS — first live-PG proof for II.2 (II.2 RATIFICATION, “Integration evidence status”) |
| L-02 | 37685834508 | `ea1ca46` (II.3 first push) | `postgres` ❌ | PG tests **not executed** | **FAIL(app)** — CI-exposed import defects invisible locally; repaired on the ladder → L-03 (II.3 RATIFICATION “CI evidence”) |
| L-03 | 37686152520 | `6f2e549` (II.3 repair) | `test` ✅ `postgres` ✅ | PG full suite 297; integration **14**; identity/session **7** | PASS — append-only repair, no amend/squash |
| L-04 | 37686814842 | `cad9cd7` (II.4) | `test` ✅ `postgres` ✅ | (II.4 suite green; counts per II.4 EVIDENCE §16) | PASS — re-queried in this assignment |
| L-05 | 37966955527 | `1496c16` (II.5) | `test` ✅ `postgres` ✅ | postgres **805 passed** incl. PG module 19 | PASS (II.5 RATIFICATION “Limitations carried forward”) |
| L-06 | 37967280111 | `0b88b47` (II.6 start) | `test` ✅ `postgres` ✅ | postgres **805 passed** | PASS — last green PG run before the registry outage (II.6 EVIDENCE §5) |
| L-07 | 37989879501 | `fec9be0` (II.6 final) | `test` ✅ **`postgres` ❌ (attempt 6)** | `test` **890 passed, 19 skipped** executed; **PG tests: 0 executed** | **FAIL(infra)** — `toomanyrequests` at `docker pull postgres:16` (verbatim §3). Recorded as open gap by II.6, not as a pass |
| L-08 | 37991271771 | `0efc4de` (II.6 evidence head) | `test` ✅ `postgres` ❌ | `test` 890/19 executed; **PG tests: 0 executed** | **FAIL(infra)** — same pull failure across runners (II.6 EVIDENCE §5) |
| L-09 | 37991458041 | `fdf5b07` (step-7 start) | attempt 1: `postgres` ❌ → attempt 2: both ✅ | `test` **890/19**; PG: full suite **909 passed**, integration **19**, identity/session **7 (12 deselected)** | PASS on attempt 2 via **unchanged-workflow rerun** (`gh run rerun --failed`); attempt-1 failure = same registry pattern; verbatim evidence from L-07/L-08 |
| L-10 | 38180835563 | `cfd69d0` (step-7 EVIDENCE) | `test` ✅ `postgres` ✅ | `test` **946/19**; PG **965**, integration **19**, identity **7** | PASS |
| L-11 | 38180999390 | `5c58414` (step-7 VERIFICATION) | `test` ✅ `postgres` ✅ | doc-only rung; counts not re-extracted (identical suite to L-10/L-12) | PASS |
| L-12 | 38181284353 | **`ae35276` (EVIDENCE HEAD)** | `test` ✅ `postgres` ✅ | `test` **946 passed, 19 skipped**; PG full **965**, integration **19**, identity/session **7** | PASS — CI green on the exact authorized evidence SHA |
| L-13 | local run (this packet) | `ae35276` tree | approved local PostgreSQL 16 (`forge@127.0.0.1:5432/forge_test`) | PG module **19 passed**; full suite under CI postgres env **965 passed, 0 skipped** | PASS — independent non-CI PostgreSQL execution (step-7 ledger, reproduced) |
| L-14 | 38183868608 | `cbeac2e` (this evidence pack, rung 3 — post-push verification) | `test` ✅ `postgres` ✅ | `test` **946 passed, 19 skipped**; PG full **965 passed**, integration **19**, identity/session **7** | PASS — CI green on the pushed evidence-pack head (Phase 9 remote-SHA verification) |
| L-15 | 38187591174 | `6a426de` (closure repair rung 4) | `test` ✅ `postgres` ❌ | `test` 975/27 executed; `postgres` **995 passed, 6 failed, 1 error** | **FAIL(app)** — closure-repair test/gateway defects (RowMapping access, txn-abort cascade, backup fixture field); repaired append-only → L-16. Never claimed as a pass |
| L-16 | 38187953980 | `9f44d81` (closure repair rung 5) | `test` ✅ `postgres` ❌ | `test` 975/27 executed; `postgres` **1000 passed, 2 failed** | **FAIL(app)** — tenant projection referenced an unseeded user (003 owner FK working as designed) + one swallowed `def`; repaired append-only → L-17 |
| L-17 | 38188302328 | **`914cc04` (closure-repair evidence head)** | `test` ✅ `postgres` ✅ | `test` **975 passed, 27 skipped**; PG full **1002 passed, 0 skipped**; integration **19**; identity/session **7** | PASS — closure-repair acceptance executed: pgvector schema + rebuild + isolation + backup/restore smoke all green on the changed service image `pgvector/pgvector:pg16` (required by frozen G-D1; jobs/env unchanged) |
| L-18 | 38261712088 | **`3529a0d` (GAP-05 code rung)** | `test` ✅ `postgres` ✅ | `test` **1016 passed, 29 skipped**; PG full **1045 passed, 0 skipped**; integration **19**; identity/session **7** | PASS — GAP-05 durable audit/event ledger acceptance executed (BA-14 EVIDENCE §8; +43 over L-17 = this packet's new tests) |
| L-19 | 38262811797 | `7ae6dba` (GAP-05 evidence/registers rung) | `test` ✅ `postgres` ✅ | doc/registers rung; suite identical to L-18 | PASS |
| L-20 | 38263059238 | `0d9cd85` (GAP-05 VERIFICATION rung) | `test` ✅ `postgres` ✅ | doc rung; suite identical to L-18 | PASS |
| L-21 | 38263395142 | **`1041787` (BA-14 final head = BA-15 re-audit start head)** | `test` ✅ `postgres` ✅ | `test` **1016 passed, 29 skipped**; PG full **1045 passed, 0 skipped**; integration **19**; identity/session **7** | PASS — re-queried live by the BA-15 re-audit; CI green on the exact re-audit head |

Book I-era green runs for context only (not Book II coverage):
`37861618933` (`017fc96`), `37861865244` (`b61a29c`), `37872174840`
(`686faa7`), `37872287646` (`218c521`) — all `success`.

## 3. The PostgreSQL initialization failure (verbatim, preserved)

From `37989879501`, job `postgres`, before any test executed:

```
##[command]/usr/bin/docker pull postgres:16
Error response from daemon: toomanyrequests: You have reached your unauthenticated pull rate limit. https://www.docker.com/increase-rate-limit
##[warning]Docker pull failed with exit code 1, back off 4.684 seconds before retry.
##[command]/usr/bin/docker pull postgres:16
Error response from daemon: toomanyrequests: You have reached your unauthenticated pull rate limit. ...
##[error]Docker pull failed with exit code 1
```

**Classification: registry/network initialization failure (Docker Hub
unauthenticated rate limit), not an application or test failure.**
Evidence for the classification: the failure occurs at the image-pull step
before checkout-dependent tests run; the `test` job passed on the same SHAs
(L-07, L-08); five retries over ~10 minutes plus a fresh run on a different
head failed identically across runners (II.6 EVIDENCE §5); the workflow file
was unchanged (`git diff 0b88b47..HEAD -- .github/` empty); the same job
passed on the adjacent heads L-06 and L-09.

**What this does NOT claim:** runs `37989879501` and `37991271771` did not
pass; no PostgreSQL test executed in those runs; no PostgreSQL coverage is
attributed to them. Their `test` jobs did pass (890/19 each).

## 4. Recovery (two independent routes)

1. **Unchanged-workflow rerun** — L-09 attempt 2 on `fdf5b07`: both jobs
   success, PG counts 909 / 19 / 7. No workflow, migration or PG-test change
   (`git diff fdf5b07..HEAD -- .github app/forge/persistence
   tests/test_forge_postgres_integration.py planning` = empty).
2. **Approved local PostgreSQL 16** — L-13: unmodified suite executed
   against a local server with CI-equivalent URL and role; 19 passed, and
   the full suite under CI postgres-job env: 965 passed / 0 skipped.

Both routes executed the same committed tests at committed SHAs; SQLite is
never offered as a substitute for PostgreSQL proof.

## 5. Append-only / push integrity (no amend, squash, rebase, force-push)

Observed push outputs on `forge` during steps 7–8 (all fast-forwards):

```
fdf5b07..cfd69d0  forge -> forge   (step 7 evidence)
cfd69d0..5c58414  forge -> forge   (step 7 verification)
5c58414..ae35276  forge -> forge   (step 7 evidence-count correction)
```

`git ls-remote origin refs/heads/forge` = `ae35276…` = local HEAD at Phase 0
of this assignment; working tree clean. Bloc ladders recorded in their own
packets (e.g. II.5 `218c521 → … → 1496c16`, II.6 `0b88b47 → … → fec9be0`).

## 6. Skipped-test accounting (never a hidden gap)

- Local runs without `FORGE_TEST_DATABASE_URL`: **19 skipped** — exactly
  the `tests/test_forge_postgres_integration.py` module, with an explicit
  skip reason declaring it unexecuted locally.
- Environments claiming PostgreSQL coverage (CI `postgres` job L-01…L-12,
  local L-13) run with **0 skipped** and record exact PG counts.
- No test is marked skip/xfail by this packet; baseline 890/19 → 946/19
  (+56 cross-bloc gates; skips unchanged).
