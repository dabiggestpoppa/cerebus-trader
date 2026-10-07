# BOOK II / BLOC II.1 — SERVICE SKELETON — EVIDENCE.md

Status: EVIDENCE
Date: 2026-10-07
Repository: dabiggestpoppa/cerebus-trader
Branch: forge

---

## Repository identity at II.1 start

- Starting local HEAD = starting remote `origin/forge` HEAD:
  `5ce3246e5ba661db21fa8856ef66073397cecaba`
  (Book I / Bloc I.2 ratification — I.2 evidence commit `1107d8b`)
- Planning freeze head `60e067547b9d9165d94e4f074e0db0ba58e59e24` verified ancestor of HEAD
  (`git merge-base --is-ancestor` → OK, re-verified this bloc).
- Dependency ratifications verified present:
  - Book I / Bloc I.1: `aca9438131a5171b23410da0669e12dbd9740029` (PASS)
  - Book I / Bloc I.2: `5ce3246e5ba661db21fa8856ef66073397cecaba` (PASS)
- Working tree at start: clean (`git status --porcelain` empty).
- Baseline suite at start: `python -m pytest -q` → **130 passed in 6.74s**.

## IMPLEMENTATION HEAD vs EVIDENCE COMMIT HEAD

- **IMPLEMENTATION HEAD** = the commit containing the final FORGE service
  skeleton code and tests, on which the executable gate below was run.
  See the commit ladder; it is the commit starting
  "II.1 tests: add service skeleton acceptance suite".
- **EVIDENCE COMMIT HEAD** = the commit adding THIS file (starts
  "II.1 evidence:"). Evidence is committed after implementation/testing, so
  the SHA is not fabricated in advance; the ladder is the authority.
- **RATIFICATION COMMIT** = the commit adding RATIFICATION.md, referencing
  the evidence commit.

## Runtime environment (exact)

- OS: Windows 10 (local execution; see "CI note" below)
- Python: 3.11.9
- pytest: 9.0.3
- pydantic: 2.13.4
- fastapi: 0.136.1
- uvicorn: 0.47.0
- httpx: 0.28.1

CI note: GitHub Actions API returned zero workflow runs for branch `forge`;
there is no remote CI evidence. `.github/workflows/forge-tests.yml`
(Python 3.11, `pip install -r requirements.txt`, `python -m pytest -q`)
remains the established CI command. **Local execution is the evidence record.**

## Exact commands and results (final gate, all run from repo root)

| # | Command | Result |
|---|---------|--------|
| 1 | `python -m pytest -q tests/test_forge_service_composition.py` | **36 passed**, 2 warnings, 1.23s |
| 2 | `python -m pytest -q tests/test_forge_canonical.py tests/test_forge_schemas.py` | **41 passed**, 0.30s |
| 3 | `python -m pytest -q tests/test_forge_provenance.py` | **41 passed**, 0.28s |
| 4 | `python -m pytest -q tests/test_state_engine.py tests/test_flip_logic.py tests/test_duplicate_signal.py tests/test_ghost_signal.py tests/test_vision_confirm.py tests/test_vision_mcp.py` | **48 passed**, 2.17s |
| 5 | `python -m pytest -q` (full suite) | **166 passed**, 2 warnings, 3.28s |

Failures: 0. Errors: 0. Skips: 0. No test was weakened or removed; the
existing 130-test baseline is fully preserved and 36 tests were added
(130 + 36 = 166).

Warning note: the 2 warnings are FastAPI `on_event is deprecated`
DeprecationWarnings, one of which is pre-existing Signal Guard code
(`app/main.py` `@app.on_event("startup")`, untouched); FORGE avoids
sub-router `on_event` entirely (lifecycle is wired via
`app.router.on_startup`/`on_shutdown` in the composition root).
Migrating Signal Guard to the lifespan API is Signal Guard's own
maintenance decision, out of II.1 scope.

## Changed files (this bloc)

Added:
- `implementation/forge/book_ii/bloc_ii_1/PLAN.md`
- `implementation/forge/book_ii/bloc_ii_1/ACCEPTANCE.md`
- `implementation/forge/book_ii/bloc_ii_1/EVIDENCE.md` (this file)
- `implementation/forge/book_ii/bloc_ii_1/RATIFICATION.md`
- `app/forge/config.py` (FORGE typed configuration boundary)
- `app/forge/service/__init__.py` (domain/service boundary marker)
- `app/forge/service/container.py` (composition seam / DI boundary)
- `app/forge/service/correlation.py` (bounded request-id boundary)
- `app/forge/service/errors.py` (FORGE error envelope)
- `app/forge/service/health.py` (honest health/readiness/meta service)
- `app/forge/service/lifecycle.py` (explicit startup/shutdown)
- `app/forge/service/routes.py` (FORGE router, `/forge/v1`)
- `tests/test_forge_service_composition.py` (36 tests)

Modified (purely additive):
- `app/main.py` — imports + `_build_forge_container()` + `_attach_forge_router()`
  + one module-level call. No existing line deleted, no route changed, no
  Signal Guard handler modified.

Not touched: `app/forge/canonical.py`, `app/forge/schemas.py`,
`app/forge/provenance.py` (zero diff this bloc); all Signal Guard modules;
`requirements.txt`; `Dockerfile`; `.github/workflows/forge-tests.yml`;
`corpus/`; `planning/`; all I.1/I.2 test files.

## Routes added (exact)

All under the FORGE namespace `/forge/v1` (local decision, recorded in PLAN §B):

1. `GET /forge/v1/health` — liveness. Returns `service`, `status="alive"`,
   `request_id`. Does not reference any future dependency.
2. `GET /forge/v1/ready` — readiness. Returns `service`, `status="ready"`
   (computed over REQUIRED dependencies only), `dependencies` (each entry:
   `status`, `required`, `note`), `request_id`.
3. `GET /forge/v1/meta` — build/version identity. Returns `service`,
   `api_version`, `application_version`, `environment`,
   `forge_domain_version`, `request_id`. No secrets, no env dump, no corpus
   paths, no provider credentials.

No other FORGE route exists. No canonical/evidence/setup/artifact/provenance/
corpus/statistics/research/Ask CEREBUS route was added.

## Configuration introduced

`app/forge/config.py`:
- Frozen dataclass `ForgeConfig` with safe LOCAL/TEST defaults:
  `service_name="glx-forge"`, `api_version="v1"`,
  `application_version` (env `FORGE_APPLICATION_VERSION`, default `1.0.0`),
  `environment` (derived from existing `ENVIRONMENT`, default local),
  `log_level`, `request_id_header`,
  `database_url=""`, `database_enabled=False`,
  `migration_compatibility_required=False`.
- `redacted_diagnostics()` returns booleans/flags only; never secret values,
  never raw env dump (tested: a `postgres://user:secret-password@db-host/...`
  URL does not appear in diagnostics).
- `forge_config_from_environment()` reads env with safe defaults; malformed
  integer env fails clearly (`invalid integer env`), tested.
- `forge_config_from_values()` for test construction without env mutation.
- **No provider credential configuration exists** (forbidden scope); a test
  asserts the dataclass has no OpenRouter/Whop/market-data fields.
- Existing `app/config.py` (Signal Guard) untouched.

## Dependencies added

**None.** `requirements.txt` unchanged. No new package, no vendor SDK, no
observability vendor, no ORM, no DB driver.

## Migrations added

**None.** No migration runner, no schema, no DDL. Migration compatibility is
represented only as a config flag (`migration_compatibility_required=False`)
and as the `postgresql: NOT_CONFIGURED` readiness entry; the runner belongs to
II.2.

## Provider/network behavior introduced

- Import-time: no network. AST/grep review: no `httpx`, `requests`, `socket`,
  `subprocess`, `urllib`, or provider client in `app/forge/**`.
- Startup: no network. `ForgeLifecycle.startup()` logs identity and flips a
  flag; it contacts nothing.
- Runtime: the three FORGE endpoints compute in-process dicts only. No
  outbound call anywhere in FORGE.
- No OpenRouter/Whop/market-data adapter, client, or credential exists in
  code. Provider *names* appear only as readiness dependency keys with
  `NOT_CONFIGURED`/`NOT_APPLICABLE` status (acceptance D3 disclosure).

## Signal Guard impact

- Existing behavior changed? **NO.**
- All existing routes remain: `/webhook`, `/health`, `/state`, `/reconcile`,
  `/logs`, `/screenshot` (asserted by test).
- Existing startup handler, error behavior, state engine, validator, trade
  log, vision modules: zero diff.
- The `app/main.py` diff is purely additive (verified by diff review).
- Existing Signal Guard tests: 48 passed (previously 48 in the 130 baseline).

## Defects discovered and repaired during this bloc (pre-commit)

1. `correlation.py` used `BaseModel` without importing it (`NameError` at
   import of `app.main`). Repaired; caught by import smoke test.
2. `ForgeLifecycle` was initially registered via `@router.on_event` —
   sub-router `on_event` handlers never fire once included, so lifecycle
   would silently never run. Repaired: composition root appends lifecycle to
   `app.router.on_startup`/`on_shutdown`; regression test proves it fires
   under a real TestClient lifespan.
3. Readiness reported `degraded` whenever any not-yet-existing dependency was
   listed — dishonest in the other direction. Repaired: readiness computes
   over `required` dependencies only; future deps are `required=False`,
   non-healthy, and never block or degrade II.1 readiness.
4. Route return annotations `Model | JSONResponse` made FastAPI raise
   `FastAPIError: Invalid args for response field`; repaired with
   `response_model=None` on the three routes (responses are already explicit
   models or the safe envelope).
5. `ForgeConfig` initially declared inert OpenRouter/Whop credential fields —
   provider configuration beyond II.1 need (forbidden scope). Repaired:
   fields removed; regression test asserts absence.
6. Dead code removed before commit: unused `app_hash()` source-digest helper,
   unused `reason` parameter, unused imports, unused `ForgeRequestContext`
   model, unused/buggy `tests/conftest.py` (deleted; it referenced `sys`
   without importing it and was no longer needed).

No defect was found in I.1/I.2 domain code; zero domain diff.

## Security / boundary review (executed)

Method: targeted grep/AST inspection of the full `app/forge/**` tree plus
line-by-line review of the `app/main.py` diff, before ratification.

| Check | Result | Evidence |
|---|---|---|
| FastAPI import in FORGE domain (`canonical.py`, `schemas.py`, `provenance.py`) | CLEAN | grep empty; AST test asserts no `fastapi` import |
| No domain import starts server/network | CLEAN | import smoke test; grep for subprocess/socket/httpx/urlopen empty |
| Provider coupling (OpenRouter/Whop clients) | CLEAN | no client/SDK anywhere; only readiness disclosure keys |
| Persistence introduced (SQLAlchemy/psycopg/redis/pgvector) | CLEAN | grep empty; `requirements.txt` unchanged |
| Corpus leakage endpoint | CLEAN | no file-serving route (`FileResponse`/`StaticFiles`/`open()` grep empty); only 3 JSON endpoints |
| Secret leakage in responses | CLEAN | diagnostics redaction tested; meta endpoint tested against `API_KEY`/`SECRET`/`DATABASE_URL`/`POSTGRES` strings |
| Stack-trace / raw-exception leak | CLEAN | fault-injection test: forced exception yields 500 envelope `FORGE_INTERNAL_ERROR` / `internal service error`; exception text (incl. fake secret + path) absent from body; only `type(exc).__name__` reaches logs |
| INTERNAL_METHOD / INTERNAL_CODE exposure route | CLEAN | no such route exists; no permissive object-by-ID route exists |
| Wildcard CORS / debug mode | CLEAN | no CORS middleware added, no `debug=True` |
| Global mutable registries in HTTP layer | CLEAN | domain registries untouched; container is instance-scoped, constructed at composition root |
| Inbound request-id trust | BOUNDED | `^[A-Za-z0-9][A-Za-z0-9_-]{0,63}$`; malformed ids ignored and replaced by generated `fg-<16 hex>` (tested) |
| Signal Guard behavioral change | NONE | diff purely additive; 48/48 Signal Guard tests pass; route-set assertion |

## Commit ladder (this bloc)

Append-only from `5ce3246` (I.2 ratification):

1. `II.1 plan: add PLAN.md` — frozen-plan translation to actual repo
2. `II.1 plan: add ACCEPTANCE.md` — executable acceptance clauses A–L
3. `II.1 implementation: add FORGE service skeleton` — config + service
   package + `app/main.py` composition (IMPLEMENTATION HEAD)
4. `II.1 tests: add service skeleton acceptance suite` — 36 tests
5. `II.1 evidence: record executable test results` — this file (EVIDENCE
   COMMIT HEAD)
6. `II.1 ratification: PASS — service skeleton gate closed`

Full ladder from freeze: `60e0675` (freeze) → 11 commits (I.1) → 6 commits
(I.2) → 6 commits (II.1) = 23 implementation commits; exact SHAs in the
final report / `git log`.

## Known gaps / honest limitations

1. No remote CI has ever executed this branch (zero GitHub Actions runs);
   evidence is local-execution only.
2. `ForgeConfig` database fields exist but no database layer exists (II.2);
   `database_enabled` defaults False and nothing reads it yet.
3. Request correlation is a FORGE-local boundary: it does not yet propagate
   into Signal Guard routes (intentional; Signal Guard correlation belongs to
   its own maintenance, not II.1).
4. The two FastAPI deprecation warnings remain (one pre-existing in Signal
   Guard); migration to the lifespan API is out of II.1 scope.
5. `/forge/v1` is a local implementation decision (frozen Book II does not
   pin a namespace); recorded in PLAN §B.

## II.2 handoff assumptions

- FORGE composition root and container are the seams II.2 wires persistence
  into: `ForgeServiceContainer.persistence` (currently rejects wiring),
  `config.database_url` / `database_enabled` /
  `migration_compatibility_required`.
- II.2 must flip the `postgresql` readiness entry from `NOT_CONFIGURED` to a
  real probe and set `required=True` once wired.
- II.2 owns the migration runner (Book II Ch II.1.6) and must place
  migration-compatibility checking before readiness.
- Domain modules (`canonical.py`, `schemas.py`, `provenance.py`) must remain
  transport-free; the AST test in the II.1 suite is the guard.
- No code in this bloc needs rework by II.2.
