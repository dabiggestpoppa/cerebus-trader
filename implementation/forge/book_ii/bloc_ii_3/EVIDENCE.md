# BOOK II / BLOC II.3 — IDENTITY & SESSION — EVIDENCE.md

Status: EVIDENCE
Date: 2026-10-07
Bloc head: `f28721b6e41c2caa11845237cc8f1d6e5c39d826`

## Lineage

- Starting remote HEAD: `772a0d2d3f4f8b617ba02d85000333a42cad4c48` (II.2 final)
- Implementation/test HEAD: `f28721b6e41c2caa11845237cc8f1d6e5c39d826`
- Planning freeze head `60e067547b9d9165d94e4f074e0db0ba58e59e24`: verified
  ancestor of `772a0d2` via `git merge-base --is-ancestor` at Phase 0.
- Dependency ratifications (all verified ancestors at Phase 0):
  - I.1 `aca9438131a5171b23410da0669e12dbd9740029`
  - I.2 `5ce3246e5ba661db21fa8856ef66073397cecaba`
  - II.1 `598b34c3af7b7bebc681099e7f87f17020da2f27`
  - II.2 `772a0d2d3f4f8b617ba02d85000333a42cad4c48`
- Local branch `forge` at start: clean tree, HEAD == `origin/forge` ==
  `772a0d2` (verified via `git ls-remote origin refs/heads/forge`).

## Exact runtime

- Windows 10, Python 3.11.9, pytest 9.0.3, pydantic 2.13.4, fastapi 0.136.1,
  starlette 1.0.0, SQLAlchemy 2.0.49, uvicorn 0.47.0, httpx 0.28.1.
- No Docker, no local PostgreSQL server; PostgreSQL evidence is CI-executed
  (below). No auth library installed or added: stdlib only
  (`hashlib`, `hmac`, `secrets`, `uuid`, `datetime`).

## Phase 0 baseline (recorded)

- `python -m pytest -q` at `772a0d2`: **217 passed, 7 skipped** (skips =
  PostgreSQL integration module only — local machine has no PG server).
- No existing authentication/session code anywhere in the repository
  (grep-verified); no auth libraries in `requirements.txt`.
- Signal Guard contains no identity/auth concepts; `app/trade_log.py`
  "session" is a trading-session label, unrelated. **Zero Signal Guard
  modification.**

## Identity model

- `ForgeUserId` — FORGE-generated `uuid.uuid4().hex` (opaque 32-hex). Never
  derived from provider IDs or email. `new_forge_user_id()` in
  `app/forge/identity.py`.
- `UserState` — exactly `ACTIVE` / `DISABLED`. Governed transitions
  (both directions, no same-state, no invented terminals) validated by
  `validate_user_state_transition`; persistence maps violations to
  `IllegalUserStateTransition`.
- `IdentityRole` — `USER`, `RESEARCH_ADMIN`, `SUPPORT_ADMIN`,
  `SYSTEM_ADMIN`, `SERVICE` (frozen Ch II.3.6). Identity primitives only:
  carried as data on users/principals, never consulted by any II.3 code for
  an access decision, no generic ADMIN bypass. Enforcement is II.4's.
- `ForgeUser` — `user_id`, `state`, `roles`, optional untrusted `email`
  attribute (never a key, never unique, no lookup path — no
  `get_user_by_email` exists anywhere), optional `display_label`,
  created/updated audit timestamps.

## Session model

- `ForgeSessionId` — FORGE-generated `uuid.uuid4().hex`; distinct from user
  ID and from any provider session concept (none exists in II.3).
- `ForgeSession` — `session_id`, `user_id` (exactly one user, FK-enforced),
  `token_digest` (64-hex SHA-256, validated at construction), `created_at`,
  `expires_at`, `revoked_at`, `is_expired(now)` against an injected clock.
- Lifecycle: valid until `expires_at` unless revoked; expired ⇒ cannot
  authenticate; revoked ⇒ cannot authenticate (permanent — new session must
  be issued); disabled user ⇒ cannot authenticate through an otherwise-valid
  session.
- **Absolute expiry only.** No idle/sliding expiry — frozen contract requires
  expiration + revocation; explicitly not added.
- No entitlement snapshot is stored on or trusted from a session.

## Token strategy

- **Opaque bearer tokens**: `secrets.token_urlsafe(32)` — 256 bits of CSPRNG
  entropy, URL-safe. No JWT, no signed tokens (nothing frozen requires them;
  documented decision, not omission).
- Issuance boundary: `ForgeAuthenticationService.open_session(user, ttl)`
  returns `IssuedCredential(bearer_token, session)` — the raw token exists
  ONLY here and at the request-extraction moment
  (`authenticate_bearer` local variable). It is never persisted, logged,
  echoed, or returned by any endpoint.
- **Digest storage**: only `SHA-256(token)` hex (64 chars) is persisted.
  Lookup is by exact digest (unique index in SQL; dict in memory).
  `digests_equal` (`hmac.compare_digest`) is provided and used as the
  security-sensitive comparison primitive. Threat note: lookup-by-digest
  exposes no raw-token timing oracle — the attacker never controls a
  comparison against the secret; the digest of a 256-bit CSPRNG token is not
  invertible or brute-forceable.
- **No server-side pepper.** Explicit design decision (permitted by handoff):
  256-bit CSPRNG tokens make digest storage safe without pepper; adding one
  would create secret-management burden with no threat-model gain at II.3.

## Migration added

- `app/forge/persistence/sql/002_identity_session.sql` — forward-only,
  discovered automatically by the existing first-party runner (versions now
  `[1, 2]`). `001_initial_schema.sql` untouched: pinned by executable test
  (SHA-256 `d91c2ea2ec45de5f89f64b56acab80316339f68a53fd28a88c3c7ea0b7662f14`).

## Tables / constraints / indexes

- `forge_users`: PK `user_id`; `state` CHECK IN (`ACTIVE`,`DISABLED`);
  `roles_json`; `email` VARCHAR(320) NULL — deliberately NOT unique;
  `display_label`; `persisted_version`; created/updated timestamps.
- `external_identity_links`: composite PK `(provider, provider_subject)`
  (uniqueness of the provider mapping); FK `forge_user_id` →
  `forge_users` **ON DELETE RESTRICT**; index on `forge_user_id`.
- `forge_sessions`: PK `session_id`; FK `user_id` → `forge_users`
  **ON DELETE RESTRICT**; `token_digest` CHAR(64) NOT NULL with UNIQUE index
  `idx_forge_sessions_token_digest` (the auth lookup path); index on
  `user_id`; `expires_at` NOT NULL; `revoked_at` NULL;
  `persisted_version`.
- **No entitlement/license/plan/product table exists** — asserted by
  executable test (`test_no_entitlement_or_license_table_created`).
- Delete semantics: RESTRICT on both FKs, no cascade over audit-relevant
  identity history, no user-deletion API (disable + revoke only).

## Persistence methods added (port)

`create_user`, `get_user`, `transition_user_state`, `create_identity_link`,
`get_identity_link`, `identity_links_for_user`, `delete_identity_link`,
`create_session`, `get_session`, `find_session_by_token_digest`,
`revoke_session`, `revoke_all_sessions` — on the `PersistenceGateway`
protocol, implemented by `InMemoryPersistenceGateway` and
`SqlAlchemyPersistenceGateway`. New deterministic exceptions:
`DuplicateForgeUser`, `UserNotFound`, `IllegalUserStateTransition`,
`DuplicateIdentityLink`, `IdentityLinkNotFound`, `DuplicateSession`,
`SessionNotFound` (all `PersistenceError` subclasses).

## Transaction semantics

- In-memory: users, sessions AND links are commit-deferred inside
  `transaction()`; `_commit_buffer` validates-then-applies all buffered
  writes atomically; failure ⇒ nothing survives. (Defect found and fixed
  during II.3 testing: links were originally applied inline, so a rollback
  left a link whose user was rolled back — see Defects.)
- SQL: identity writes execute on the gateway's connection inside
  `_SqlConnectionTransaction` (explicit BEGIN/COMMIT/ROLLBACK) for logical
  multi-write operations. Duplicate pre-checks raise BEFORE INSERT so a
  failed INSERT cannot poison the shared connection's open transaction (the
  except-branch unique-violation mapping remains as the concurrent-writer
  backstop).
- `revoke_all_sessions` is a single atomic operation (one UPDATE in SQL;
  one dict sweep in memory) returning the revoked count.

## Concurrency semantics

- Optimistic concurrency via II.2 `persisted_version`/`expected_version` +
  `StaleWriteConflict` governs user-state mutation and session revocation —
  newer identity state is never silently overwritten (tested on memory and
  SQL; PG test asserts the real version columns).
- Uniqueness surfaces deterministically: in-memory dict checks; SQL
  PK/CHECK/UNIQUE constraints (duplicate pre-check + constraint backstop).

## Authentication service behavior

`app/forge/service/authentication.py` — `ForgeAuthenticationService`:

- `authenticate_bearer(credential, allow_anonymous)`:
  no credential ⇒ anonymous principal (when allowed) / uniform failure;
  `Bearer <token>` ⇒ SHA-256 digest → session by digest → revocation check
  → expiry check (injected clock) → user lookup → user state ACTIVE check →
  `ForgePrincipal.for_session(user, session)`.
- `open_session(user, ttl)` — issuance boundary (ACTIVE users only).
- `link_external_identity(principal, provider, provider_subject)` — requires
  an authenticated principal (frozen Ch II.3.5 verified-proof rule); rejects
  collision with a different user; email never consulted (no takeover path).
- `revoke_session`, `revoke_all_sessions(principal)`.
- **No credential ⇒ anonymous** where the route allows it; anonymous is the
  structural singleton `ANONYMOUS_PRINCIPAL`.
- **Uniform failure contract**: every invalid credential — unknown token,
  malformed header, empty bearer, expired, revoked, disabled user — raises
  `AuthenticationFailure` with the single constant
  `AUTHENTICATION_FAILURE_MESSAGE = "authentication failed"`. Internal
  `kind` exists for tests/ops only. No user enumeration, no
  disabled-vs-invalid distinction, no raw DB/provider errors.
- The service performs NO authorization/plan/license/entitlement/capability/
  exposure/product check (AUTHENTICATION != AUTHORIZATION; II.4/VI own those).
- Composed onto `ForgeServiceContainer` (explicit injection; auto-built from
  the injected persistence gateway when omitted; type-guarded).

## Anonymous behavior

- `ForgePrincipal.anonymous()` / `ANONYMOUS_PRINCIPAL`:
  `authenticated=False`, `forge_user_id=None`, `session_id=None`,
  `roles=∅`. Structurally enforced: an unauthenticated principal cannot
  carry user/session identity; an authenticated one must carry a user.
- Anonymous is never a persisted fake user; no user row is created by
  anonymous authentication (tested).

## HTTP changes

- **None.** No new public route: route set remains exactly
  `/forge/v1/health`, `/forge/v1/ready`, `/forge/v1/meta` (asserted by
  test). No user/session CRUD API, no session dump endpoint. The
  authentication boundary is service-layer; II.4 will wire enforcement.
- `/meta` and `/ready` bodies verified free of any presented bearer token
  (executable test).
- Container gains the additive `authentication` field; readiness
  dependencies unchanged — no fake `identity` readiness entry (asserted).

## Configuration changes

- **None.** `ForgeConfig` untouched; no credential fields, no new env vars,
  no session-TTL secret surface (TTL is a service parameter). Config-level
  redaction rules unchanged.

## PostgreSQL evidence

- Local: PostgreSQL integration module **skips** (14 tests) — no local PG
  server; the skip is the declared gap, not hidden coverage.
- CI (`.github/workflows/forge-tests.yml`, postgres job, PostgreSQL 16
  service): full suite runs against live PG, then the integration module,
  then the dedicated II.3 step
  `pytest -v tests/test_forge_postgres_integration.py -k TestPostgresIdentitySession`
  proving: migration chain 001→002 + no-op; user persistence + real-PK
  duplicate rejection; provider mapping + composite-PK uniqueness; session
  persistence + token-digest lookup + full authentication round trip;
  FK rejection for session of unknown user; revocation + revoke-all;
  optimistic-concurrency conflict on identity mutation.
- CI run for the bloc head: **run 37686152520 (SUCCESS — both jobs)** for
  repair head `6f2e5492dd221317a1d41202608283d4a5ce3286`:
  - `postgres` job: full suite against live PostgreSQL 16 — **297 passed**;
    integration module — **14 passed in 0.20s**, including ALL 7
    `TestPostgresIdentitySession` tests PASSED (migration chain, user
    persistence + real-PK duplicate, provider mapping + composite-PK
    uniqueness, session persistence + digest lookup + authentication round
    trip, real-FK rejection, revocation + revoke-all, optimistic
    concurrency);
  - `test` job: SUCCESS.
- Honest repair note: the FIRST push (run 37685834508, `ea1ca46`) FAILED in
  the postgres job — CI exposed `DanglingReference` import missing in the
  SQL gateway (same clobber class as the memory.py repair) and a missing
  `ForgeUser` import in a new PG identity test. Repaired append-only at
  `6f2e549`, re-pushed fast-forward, re-run to SUCCESS. Local suites were
  blind to both because the PG module skips without a live server.

## Exact tests

- II.3 focused (`tests/test_forge_identity.py`): **66 passed**.
- I.1 regression (`test_forge_canonical.py` + `test_forge_schemas.py`):
  **41 passed**.
- I.2 regression (`test_forge_provenance.py`): **41 passed**.
- II.1 regression (`test_forge_service_composition.py`): **36 passed**.
- II.2 regression (`test_forge_persistence.py`): **51 passed**.
- Signal Guard regression (6 signal test files, run separately): **48 passed**.
- PostgreSQL integration module: **14 skipped** locally (no PG server; CI
  executes them against live PostgreSQL 16).
- Full repository: **283 passed, 14 skipped** (baseline 217+7 + 66 II.3;
  skips = PG integration modules by design).

## Security review (Phase 8 findings)

Scanned: raw tokens in DB (none — digest only, tested); tokens in logs
(caplog test clean); tokens in exceptions (constant message only); provider
secrets (none stored anywhere); plaintext passwords (none); weak randomness
(none — `secrets.token_urlsafe(32)`); insecure equality (`hmac.compare_digest`
provided/used; digest lookup carries no raw-token timing oracle); SQL
injection (all SQL `text()`-wrapped parameterized — grep-verified); auth
bypass (disabled/expired/revoked all fail closed, uniform); session fixation
(session IDs are FORGE-generated CSPRNG uuid4, never client-supplied);
provider ID as PK (never — provider data lives on links only); entitlement
fields in principal (none — field-set test); public identity dump (no such
route); unsafe cascade delete (RESTRICT, no deletes); import-time
connections (subprocess-isolated import probe test); migration mutation of
001 (SHA-256 pinned test). **No findings outstanding.**

## Changed files

- `implementation/forge/book_ii/bloc_ii_3/PLAN.md` (new)
- `implementation/forge/book_ii/bloc_ii_3/ACCEPTANCE.md` (new)
- `app/forge/identity.py` (new — pure domain)
- `app/forge/persistence/port.py` (identity section)
- `app/forge/persistence/memory.py` (identity stores)
- `app/forge/persistence/sql/gateway.py` (identity implementation)
- `app/forge/persistence/sql/002_identity_session.sql` (new)
- `app/forge/service/authentication.py` (new)
- `app/forge/service/container.py` (additive authentication field)
- `tests/test_forge_identity.py` (new, 66 tests)
- `tests/test_forge_postgres_integration.py` (II.3 class added)
- `.github/workflows/forge-tests.yml` (dedicated II.3 evidence step)

## Defects discovered / repaired (append-only)

1. In-memory transaction applied identity links inline, so a rollback left a
   link whose user was rolled back — links made commit-deferred; regression
   test added (`test_create_user_plus_link_transaction_rolls_back`).
2. SQL duplicate INSERTs would poison the connection's open transaction
   (shared-connection model + `_safe_rollback` discards prior uncommitted
   writes) — duplicates now pre-checked before INSERT; except-branch kept as
   concurrency backstop.
3. `DanglingReference` import clobbered during the memory.py import rewrite
   → 2 II.2 regressions caught by the gate — restored, committed honestly.

## Known gaps

- Local PostgreSQL execution impossible (no server): PG evidence is
  CI-executed; local module skips by design.
- No HTTP enforcement of authentication exists yet — deliberate: frozen II.3
  builds the boundary; route protection is II.4 (authorization) ownership.
- No idle/sliding session expiry — deliberate non-feature (frozen contract).
- No role-enforcement anywhere in II.3 — deliberate (roles are primitives).

## II.4 handoff assumptions

II.4 receives: `ForgePrincipal` (identity + roles only), explicit anonymous,
`ForgeAuthenticationService` on the container, session validity as
authentication truth, governed user-state/revocation mutations. II.4 owns:
policy decisions, entitlement evaluation, capability checks, exposure
enforcement, gating which routes require authenticated principals. Nothing
in II.3 grants or implies any entitlement.
