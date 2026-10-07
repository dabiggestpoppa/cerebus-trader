# BOOK II / BLOC II.3 — IDENTITY & SESSION — ACCEPTANCE.md

Status: ACCEPTANCE
Date: 2026-10-07
Freeze head: `60e067547b9d9165d94e4f074e0db0ba58e59e24`
Dependency ratifications: I.1 `aca9438`, I.2 `5ce3246`, II.1 `598b34c`, II.2 `772a0d2`

Each clause names its verification. "test" = executable in the focused II.3
suites (`tests/test_forge_identity.py`, `tests/test_forge_persistence_identity.py`,
`tests/test_forge_postgres_integration.py`) or the pre-existing regression
suites; "review" = inspection recorded in EVIDENCE.md.

## A. Internal user identity

- A1 Stable internal identifier per user — test: user round trip preserves
  `user_id` exactly.
- A2 Identifier generated/owned by FORGE — test: `new_forge_user_id()` yields
  32-hex opaque IDs, distinct on successive calls; not derived from any input.
- A3 Provider IDs cannot be internal PKs — test: provider/provider_subject
  exist only on `ExternalIdentityLink`; `forge_users` PK is `user_id`;
  resolving a link returns a FORGE user_id distinct from the provider subject.
- A4 Email cannot be the immutable internal PK — test: user PK is `user_id`;
  `email` is an optional attribute with no uniqueness constraint and no
  lookup path (no `get_user_by_email` exists anywhere).
- A5 Identity survives provider-link changes — test: link + unlink cycles
  leave the user record intact.
- A6 Explicit lifecycle state — test: `UserState.ACTIVE/DISABLED` round trip;
  no other states exist.

## B. External identity links

- B1 Typed link `(provider, provider_subject) → forge_user_id` round trips —
  test.
- B2 `(provider, provider_subject)` uniqueness — test: duplicate link raises
  `DuplicateIdentityLink` (memory + real SQL PK on PostgreSQL).
- B3 Multiple providers may link to one user — test: two providers → same
  `forge_user_id`.
- B4 Unlinking does not delete the user — test: `delete_identity_link` leaves
  `get_user` intact.
- B5 Provider metadata is not authorization — review: no II.3 code reads
  provider fields for any decision.
- B6 No raw provider secrets stored — review: no provider credential field
  exists in records/tables/config.
- B7 Link creation requires authenticated proof / collision protection —
  test: `link_external_identity` with an anonymous principal raises;
  linking a subject already bound to a different user raises; no
  email-string-only takeover path exists (email never consulted).

## C. Principal

- C1 Principal carries forge_user_id, authenticated flag, session_id, roles —
  test.
- C2 Principal is runtime-only — review: never persisted (no record/table
  holds it); not HTTP-aware (no FastAPI import in identity domain).
- C3 Principal contains no entitlement/plan/license/product-tier/exposure
  field — test: `ForgePrincipal` field set asserted exactly; dataclasses.fields
  scan asserts absence of entitlement vocabulary.

## D. Anonymous identity

- D1 Anonymous is explicit and structurally distinct — test:
  `ForgePrincipal.anonymous()` has `authenticated=False`, `forge_user_id=None`,
  `session_id=None`.
- D2 No fake persisted user ID for anonymous — test: anonymous user_id is
  None and no `"anonymous"` user exists after anonymous authentication.
- D3 No credential yields anonymous where allowed — test.

## E. Session identity

- E1 Sessions have their own internal session ID — test: `session_id` is
  FORGE-generated and distinct from `user_id`.
- E2 Session binds exactly one user — test: `ForgeSession.user_id` fixed at
  creation; SQL FK enforces the user exists (PostgreSQL).
- E3 Session ID != provider session ID — review: no provider session concept
  exists in II.3.

## F. Session token

- F1 Cryptographically strong material — test: `new_session_token()` uses
  `secrets.token_urlsafe(32)` (256-bit entropy); successive tokens differ.
- F2 Persisted form does not require raw token — test: stored session carries
  digest only; DB row text contains no raw token substring.
- F3 Secure comparison — review + test: digest lookup + `hmac.compare_digest`
  on the security-sensitive verification path.
- F4 Revocable / expiring — tests F-G.
- F5 Token encodes no entitlement authority — review: opaque random bytes;
  nothing decodable.
- F6 No JWT introduced — review: no jwt import anywhere.

## G. Session expiry

- G1 Deterministic expiry — test: injected fixed clock; `expires_at` honored
  exactly at the boundary.
- G2 Expired session cannot authenticate — test.
- G3 Revoked session cannot authenticate — test.
- G4 Disabled user cannot authenticate through a valid session — test.
- G5 Idle expiry deliberately absent — review: absolute expiry only (frozen
  contract), documented in PLAN/EVIDENCE.

## H. Token storage

- H1 Only SHA-256 digest persisted — test: memory record + SQLite/PG row show
  64-hex digest; raw token absent.
- H2 Raw token only at issuance/request boundary — test: `open_session`
  returns raw token exactly once; later reads of the session (gateway, auth
  flow) expose no raw token.
- H3 Never logged — test: caplog scan for the raw token across auth flows.
- H4 Never returned by /meta or /ready — test: requests carrying a bearer
  header produce meta/ready bodies without the token.

## I. Persistence

- I1 `002_identity_session.sql` applies after 001 — test: fresh SQLite
  applies 001+002, compatibility OK; fresh PostgreSQL in CI does the same.
- I2 Migration no-op when current — test: second `apply_migrations` returns
  CURRENT.
- I3 Compatibility still detects behind/ahead/incompatible — test: existing
  II.2 migration tests stay green + 002-aware discovery identity.
- I4 `001_initial_schema.sql` unchanged — test: SHA-256 of 001 equals the
  pinned constant `d91c2ea2ec45de5f89f64b56acab80316339f68a53fd28a88c3c7ea0b7662f14`.

## J. Referential integrity

- J1 session → user and link → user FK enforced — test: SQL gateway rejects
  session/link for unknown user; PostgreSQL FK violation test in CI.
- J2 Conservative delete semantics — review: ON DELETE RESTRICT both FKs; no
  user-deletion API exists.

## K. Transactions

- K1 create-user + link (+ session) is atomic — test: failure inside the
  transaction rolls back the user too.
- K2 revoke_all_sessions is atomic and returns revoked count — test.

## L. Concurrency

- L1 Stale user-state mutation rejected — test: wrong `expected_version` ⇒
  `StaleWriteConflict`.
- L2 Stale session revocation rejected — test.
- L3 Duplicate link/session/user rejected deterministically — tests.

## M. Authentication boundary

- M1 Credential → digest → session → user → principal flow — test.
- M2 No credential ⇒ anonymous where allowed — test.
- M3 Persistence records never HTTP-aware — review: no FastAPI/HTTP import in
  `app/forge/persistence/**` or `app/forge/identity.py`.

## N. HTTP integration

- N1 No new public route — test: route set remains exactly
  `/forge/v1/health`, `/forge/v1/ready`, `/forge/v1/meta`; no `/users`,
  `/sessions`, `/admin/*` routes.
- N2 Service composed on container — test: container accepts/rejects
  authentication seam per port guard.

## O. Auth error contract

- O1 Uniform deterministic failure — test: expired, revoked, disabled,
  unknown-token failures raise the same `AuthenticationFailure` with one
  constant message.
- O2 No user enumeration — test: failure for unknown token is
  indistinguishable (same type/message) from failure for disabled user.
- O3 No raw DB/provider errors in auth failures — review + test: message is
  the fixed constant.

## P. Request correlation

- P1 No token in logs/exception context — test: caplog + exception scan.
- P2 II.1 correlation boundary untouched — review: correlation module
  unchanged; no auth failure path touches request IDs.

## Q. Readiness

- Q1 No new readiness dependency — test: readiness dependencies keys unchanged
  (forge, postgresql, pgvector, openrouter, ...); no `identity` key.
- Q2 Persistence readiness semantics unchanged — test: II.2 readiness tests
  stay green.

## R. Security review

- R1 No raw session token stored / logged / in exception / in meta/ready —
  tests H1–H4, O1, P1.
- R2 No provider secret / plaintext password / weak randomness — review +
  test (`secrets` module only).
- R3 No timing-naive raw-token equality on security-sensitive path — review +
  test (digest lookup; `hmac.compare_digest`).
- R4 No user enumeration through auth errors — test O2.
- R5 No entitlement data in principal — test C3.
- R6 No provider ID as internal PK — test A3.
- R7 No public arbitrary user lookup / session dump endpoint — test N1.
- R8 No unsafe cascade delete — test/review J1–J2.
- R9 No import-time connections or migrations — test: importing
  `app.main`, `app.forge.identity`, auth service performs no DB/auth network
  activity (existing II.2 pattern, extended).
- R10 No migration mutation of 001 — test I4.
- R11 No Whop API call exists — test: `whop` string absent (case-insensitive)
  from all II.3 modules.

## S. Regression

- S1 I.1 green (`tests/test_forge_canonical.py`, `tests/test_forge_schemas.py`).
- S2 I.2 green (`tests/test_forge_provenance.py`).
- S3 II.1 green (`tests/test_forge_service_composition.py`).
- S4 II.2 green (`tests/test_forge_persistence.py`).
- S5 Signal Guard green (48 tests, run separately).
- S6 Full repository green; no existing test weakened or removed.

## T. PostgreSQL integration (CI)

- T1 Migration chain 001→002 on real PostgreSQL 16.
- T2 User persistence + duplicate rejection by real PK.
- T3 Provider identity mapping + uniqueness constraint.
- T4 Session persistence + token-digest lookup.
- T5 Revocation + revoke-all.
- T6 Optimistic-concurrency conflict on identity mutation.
