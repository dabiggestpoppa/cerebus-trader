# BOOK II / BLOC II.2 — PERSISTENCE — EVIDENCE.md

Status: EVIDENCE
Date: 2026-10-07
Repository: dabiggestpoppa/cerebus-trader
Branch: forge
Starting remote/dependency head: `598b34c` (II.1 ratification)

---

## Commit ladder (append-only from `598b34c`)

1. `10b8a5f` II.2 plan: add PLAN.md
2. `6b3e423` II.2 plan: add ACCEPTANCE.md
3. `e080e9d` II.2 persistence: add port, records, in-memory gateway and SQL
   migration contract (IMPLEMENTATION)
4. `1c0bf85` II.2 integration: wire persistence into container, lifecycle and
   readiness
5. `56250e3` II.2 tests: add persistence acceptance suite; governed artifact
   transitions
6. `II.2 evidence:` — this file (EVIDENCE COMMIT)
7. `II.2 ratification: PASS — persistence gate closed` (see RATIFICATION.md)

IMPLEMENTATION HEAD (the executable gate below ran at this commit)
= `56250e3` — the last commit on which all recorded test results were produced.
Distinct from the EVIDENCE COMMIT (added after execution) and the RATIFICATION
COMMIT (added after evidence). No SHA was fabricated before a commit existed.

Freeze ancestry re-verified this bloc (`merge-base --is-ancestor` OK).
Dependency ratifications verified present: I.1 `aca9438`, I.2 `5ce3246`,
II.1 `598b34c`.

## Environment

- Windows 10; Python 3.11.9; pytest 9.0.3; pydantic 2.13.4;
  fastapi 0.136.1; uvicorn 0.47.0
- Added-to-environment (already present locally, now added to
  requirements.txt): SQLAlchemy 2.0.49, psycopg2-binary 2.9.12,
  alembic 1.18.4 (alembic installed-but-unused; first-party runner chosen)
- GitHub Actions: `tests/postgres` job added to forge-tests.yml (Postgres
  16 service, postgresql client, `FORGE_DATABASE_*` env, full suite). Zero CI
  runs exist for branch forge as of evidence date; this workflow version has
  NOT yet executed remotely — first push of this ladder is its first trigger.

## What was built

- **Port**: `app/forge/persistence/port.py` — `PersistenceGateway` Protocol
  (runtime-checkable), deterministic typed exceptions
  (`DuplicateCanonicalObject`, `DuplicateArtifact`, `DuplicateProvenanceEdge`,
  `SelfReferenceForbidden`, `DanglingReference`, `IllegalStatusTransition`,
  `StaleWriteConflict`, `ObjectNotFound`, `InvalidRecord`,
  `PersistenceUnavailable`, `MigrationIncompatible`), `MigrationOutcome`
  identity, `result_identity` helper.
- **Records**: `records.py` — `CanonicalObjectRecord` (references tuple +
  optional 8-dimension `ClaimIdentity`), `ArtifactRecord`,
  `ProvenanceEdgeRecord`, `WriteResult`. Pure dataclasses; explicit
  `from_domain`/`to_domain` conversions; no DB/HTTP imports.
- **In-memory gateway**: `memory.py` — real port implementation enforcing
  every integrity rule; deferred-conflict transactions (validated at commit,
  nothing applied on exception → atomicity); governed
  `transition_artifact_state` reusing the frozen I.2 source-state machine
  including the MISSING-cannot-carry-content-identity rule.
- **SQL gateway**: `sql/gateway.py` — SQLAlchemy 2.0 Core, explicit
  `text()`-wrapped parameterized SQL, no ORM sessions, no identity map, no
  f-string/concatenated SQL. `_exists` takes module-constant table names only.
  Driver errors normalized to `PersistenceUnavailable(<ExceptionClassName>)`
  — never a URL/credential/raw message.
- **Migrations**: `sql/migrations.py` + `sql/001_initial_schema.sql` —
  ordered immutable `.sql` files; conservative statement splitter (comment-
  aware); `forge_schema_migrations` ledger (`version`, `identity`,
  `applied_at`); `check_compatibility()` → OK/BEHIND/INCOMPATIBLE/AHEAD;
  re-apply is an explicit no-op returning `CURRENT`; execution is a
  deliberate API call, never an import side effect.
- **Schema 001** (portable DDL; PostgreSQL production target):
  `canonical_objects` (canonical_id PK — identity IS the key; type/status/
  exposure/layer CHECK enums; metadata + claim_identity JSON; stored
  deterministic_payload + content_hash; persistence_version counter),
  `canonical_references` (child rows, FK parent ON DELETE CASCADE, **no FK on
  target_id by design** — unresolved historical refs are legitimate data),
  `claim identity` 8 dimensions inside canonical_objects JSON, `artifacts`
  (id PK, source_state; version counter), `provenance_edges`
  (artifact+object+relation PK; CHECK on 6 relations; FKs CASCADE).
- **Integration**: `container.py` persistence seam typed as the port with a
  structural-conformance guard (non-port objects still rejected — II.1 guard
  principle preserved under the II.2 contract it announced); policy/providers
  rejections now say II.4/II.5. `lifecycle.py` startup: ping → apply
  migrations → compatibility; every failure normalized and recorded on the
  container; **no DB text in logs**. `health.py` readiness computed over
  required deps: postgresql READY/required=True when enabled+healthy+
  compatible; UNAVAILABLE or SCHEMA_BEHIND/SCHEMA_INCOMPATIBLE (not-ready,
  required) otherwise; NOT_CONFIGURED/not-required when disabled.
- **requirements.txt**: added `SQLAlchemy>=2.0`, `psycopg2-binary>=2.9`.
- **CI**: `forge-tests.yml` gains a `postgres` integration job (runtime
  Postgres 16; install requirements incl. SQLAlchemy/psycopg2; export
  FORGE_DATABASE_ENABLED=1, FORGE_DATABASE_URL=postgres://...; run full
  pytest) — the exact PostgreSQL evidence branch deferred below.

## PostgreSQL integration evidence

**POSTGRESQL INTEGRATION: NOT EXECUTED (local)** — the local environment has
no Docker and no PostgreSQL server; no live Postgres evidence was produced
locally and none is claimed. The frozen deferred-proof rule is honored by:
(1) the port-level unit/contract evidence below (in-memory gateway is a real
port implementation, not a Postgres mock); (2) SQLite execution of the
portable SQL migration contract (schema/dialect truth, explicitly NOT claimed
as production-Postgres equivalence); (3) the new CI `postgres` job that
executes the real integration proof on push. Ratification declares this the
same way: deferred proof, named owner (forge-tests.yml `postgres` job),
first-push trigger.

## Exact executable results (IMPLEMENTATION HEAD `56250e3`)

| Suite | Command | Result |
|---|---|---|
| Focused II.2 | `python -m pytest -q tests/test_forge_persistence.py` | **51 passed**, 2 warnings, 1.41s |
| I.1 regression | `python -m pytest -q tests/test_forge_canonical.py tests/test_forge_schemas.py` | **41 passed**, 0.28s |
| I.2 regression | `python -m pytest -q tests/test_forge_provenance.py` | **41 passed**, 0.25s |
| II.1 regression | `python -m pytest -q tests/test_forge_service_composition.py` | **36 passed**, 0.89s |
| Signal Guard | `python -m pytest -q tests/test_state_engine.py tests/test_flip_logic.py tests/test_duplicate_signal.py tests/test_ghost_signal.py tests/test_vision_confirm.py tests/test_vision_mcp.py` | **48 passed**, 2.64s |
| Full suite | `python -m pytest -q` | **217 passed**, 2 warnings, 4.54s |

0 failures / 0 errors / 0 skips across the full run. Test counts grew exactly
+51 (166 → 217); no test weakened, deleted, or made conditional-on-weakness
(the two pre-existing skipifs — SQLAlchemy presence — are environment guards,
same pattern as before; SQLAlchemy is present so none actually skip).

## Security / boundary review (executed)

| Check | Result | Evidence |
|---|---|---|
| Raw SQL string building (f-strings/concat/format into SQL) | CLEAN | grep over app/forge/persistence: NONE; all statements wrapped `text()` with bound params |
| SQL from user-influenced identifiers | CLEAN | `_exists()` called only with module-constant table names; keys always bound params |
| Connection/engine at import or module level | CLEAN | grep: none; composition root builds gateway only when enabled |
| Credentials/URL in logs | CLEAN | lifecycle logs exception *class names* and migration outcomes only |
| Credentials/URL in /forge/v1/meta, /forge/v1/ready | CLEAN | test asserts `sqlite`/`postgres` absent from payloads |
| New public routes | NONE | route set still exactly {/forge/v1/health, /forge/v1/meta, /forge/v1/ready}; forbidden route 404 assertions |
| Destructive migration behavior | CLEAN | 001 is CREATE-only, additive, `IF NOT EXISTS` ledger; forward-only runner; no drop/recreate anywhere |
| Cascade-delete hazards | BOUNDED | cascades only on aggregate-child rows (references, provenance edges) — documented schema choice, not object-level delete |
| Hidden singleton / global session | CLEAN | gateway instances constructed per composition root; container is the only holder |
| Domain import purity | CLEAN | canonical/schemas/provenance: zero diff; AST/grep: no sqlalchemy/psycopg/alembic imports in domain |
| Transition bypass | CLEAN | gateways call `validate_status_transition` / `validate_source_state_transition` before commit; SUPERSEDED/FALSIFIED remain terminal (tested) |

## Defects discovered and repaired during this bloc (all pre-commit)

1. **Atomicity violation in in-memory transactions** — the first
   `create_object` inside `transaction()` applied immediately instead of
   buffering (truthy-buffer check), so a failed multi-record seed left the
   first object committed. Caught by the transaction-rollback test; repaired
   with an explicit `_in_transaction` flag + explicit rollback on exception.
2. **Stale-version check on absent rows was asymmetric** —
   `create_*` with `expected_version` on a non-existent row silently created
   instead of conflict-failing. Repaired: `StaleWriteConflict` when an
   expected version is supplied for a missing row.
3. **Artifact state had no governed mutation path** — the port could create
   artifacts but never advance source state, making II.1-style optimistic
   concurrency untestable on artifacts and freezing source states forever.
   Repaired: `transition_artifact_state` added to the port and BOTH gateways,
   reusing the frozen I.2 state machine (illegal/MISSING-with-content
   transitions rejected; version-checked).
4. **II.1 container test had codified the temporary prohibition** — updated
   to the II.2 contract (port-conformant wiring accepted; non-port rejected)
   without weakening any other II.1 assertion.
5. **Lifespan/portal-thread discovery (test-infrastructure only)** —
   SQLite connections created on the main thread cannot execute when TestClient
   drives lifespan handlers on its portal thread; production code was already
   thread-agnostic. Tests construct engines with
   `check_same_thread=False`; a comment documents that real PostgreSQL is
   unaffected (psycopg2 connections are threaded via the engine pool).

## Known gaps / honest limitations

1. POSTGRESQL INTEGRATION: NOT EXECUTED locally (see above) — deferred to the
   CI postgres job; first remote CI execution still pending as of this
   evidence commit.
2. No connection pooling/lifecycle hardening yet: the gateway wraps one
   engine/connection injected by the deployment; production pooling belongs
   to the II.3+ runtime hardening pass.
3. Backup/restore drill is Book VIII; II.2 provides migration-replayable
   schema only.
4. `AHEAD` compatibility (server newer than code) is reported but not
   gate-blocking; behavior documented in PLAN.
5. Alembic remains installed but unused (first-party runner chosen); removal
   from the environment is out of scope.

## II.3 handoff assumptions

- Identity/Session (II.3) may add account/license tables via a new ordered
  migration (002+); the runner, ledger, and compatibility check already
  support it.
- The container seam pattern (typed port + structural guard) is the model
  for II.3's identity/session port.
- Readiness vocabulary extends without redesign: add the new dependency's
  honest entry when II.3 wires it.
- Optimistic concurrency pattern (`persisted_version` + StaleWriteConflict)
  is established for reuse on identity rows.
