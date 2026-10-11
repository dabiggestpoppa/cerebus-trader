# BOOK II — CROSS-BLOC ADVERSARIAL INTEGRATION & VERIFICATION — PLAN.md

Status: PLAN (committed before test implementation)
Date: 2026-10-10
Start SHA: `fdf5b0747a7afb18cc7ce96bb1255aab30a92fb9`
Planning freeze head: `60e067547b9d9165d94e4f074e0db0ba58e59e24`
Dependency ratifications (RATIFICATION.md commit per packet):
I.1 `cdde1fd`, I.2 `5ce3246`, I.3 `26e8635`, I.4 `017fc96`, I.5 `686faa7`,
II.1 `598b34c`, II.2 `438a35e`, II.3 `ea1ca46`, II.4 `ebda556`,
II.5 `1496c16`, II.6 `fec9be0`.

This packet is Book II plan implementation-order step 7 ("Cross-bloc adversarial
integration suite"). It is **not a Bloc**: it owns no production code, it
creates no frozen contract, and it **does not ratify or freeze Book II**. Book
II evidence-pack preparation and final Book-level ratification are separate,
later authorizations.

`GAP_ADR_001_PHASE_ORDER_VS_BLOC_DEPENDENCY.md` (II.5 packet) is carried
forward **unchanged and OPEN**. This packet neither resolves nor closes the
phase-order contradiction; that question stays with the operator.

## 1. Objective and governing law

Prove (or disprove) that the six Book II Blocs compose safely: that failures,
adversaries and replacements crossing Bloc boundaries can never produce an
unauthorized successful state transition, a fabricated commerce/evidence
success, or a protected-content leak.

Governing law for this packet:

> A failure injected anywhere in the system must fail **closed**: no state
> transition that was not authorized by the correct authorities may be
> recorded, logged, emitted or served — regardless of which Blocs are
> involved.

Authorities remain where the frozen plan put them:

- Identity creates principals (II.3). Policy decides (II.4). Neither is
  replaceable by the other.
- Persistence records; a rejected write is never a mutation (II.2).
- Providers transport; they never grant, decide, or establish truth (II.5).
- Observability describes; it never decides, grants, or mutates (II.6).
- Claim/evidence/source traceability and FOUND ≠ SUPPORTED stay Book I law.

## 2. Frozen authorities exercised (no document modified)

Source: frozen `planning/forge/books/BOOK_II_FORGE_CORE_PLATFORM_PLAN_V1.md`
(acceptance/ratification gate + Ch II.1–II.6) and the six ratified bloc
packets. This packet reads them; it edits none of them.

## 3. Cross-bloc scenario matrix (Phase 2)

| ID | Interaction | Requirement cite | Blocs |
|----|-------------|------------------|-------|
| X1 | Identity → Policy → Provider: expired / revoked / missing / invalid / disabled sessions cannot reach protected provider operations | Ch II.3.4, II.3.8, II.4.7, II.5.1; Gate §Identity, §Policy | II.3 + II.4 + II.5 |
| X2 | Policy → Retrieval → Observability: denied content is never loaded, returned, cited, logged, or emitted | Ch II.4.4, II.4.7, II.6.2, II.6.5; Gate §Policy, §Observability | II.4 + I.3 retrieval + II.6 |
| X3 | Provider → Failure → Policy: timeouts, rate limits, outages cannot grant access or fabricate commerce success | Ch II.5.7, II.5.8, II.6.7; Gate §Providers | II.5 + II.6 + II.4 |
| X4 | Persistence → Concurrency → Audit: conflicting versions / rejected writes are never recorded as successful canonical mutations | Ch II.2.7, II.2.10; Gate §Database | II.2 + II.6 |
| X5 | QA → Provider → Evidence: generated or provider-supplied content cannot promote an unsupported claim into validated empirical evidence | Book I claim/evidence law + Ch II.5.1; Gate §Evidence pack | I.4/I.5 + II.5 |
| X6 | Commerce → Identity → Entitlement: provider customer/subscription data cannot independently grant a FORGE entitlement | Ch II.4.3, II.5.3, II.6.6; Gate §Policy | II.3 + II.4 + II.5 (no Book VI licensing) |
| X7 | Observability → Error → Security: errors, traces, metrics, audits never reveal credentials, tokens, protected bodies, restricted research | Ch II.6.2, II.6.7, II.6.8; Gate §Observability | II.6 + II.5 + I.3 |
| X8 | Provider Replacement → Domain Stability: replacing fakes changes no canonical record, policy decision, or claim authority | Ch II.5.6, II.5.9, II.5.10; Gate §Providers | II.5 vs I/II.2/II.4/I.5 |
| X9 | Lifecycle → Readiness → Failure: optional provider/telemetry outages never masquerade as healthy nor incorrectly block the core service | Ch II.1.5, II.5.6; Gate §Runtime | II.1 + II.5 + II.6 |

## 4. Failure-injection matrix (Phase 3)

Deterministic only: injected clocks (`SimulatedClock`, injectable `clock=`,
`now=`), scripted fake behaviors (`FakeBehavior`), local raising stubs, and
in-process sinks. No sleeps, no network, no randomness without a seed.

| ID | Injected failure | Mechanism | Must not happen |
|----|------------------|-----------|-----------------|
| F1 | Timeout | `ProviderTimeoutError` from scripted fake | access granted; internals leaked |
| F2 | Retry / alternate | retryable error under `run_with_fallback(mode=alternate)` | non-retryable retried; synthesized success |
| F3 | Duplicate events | same commerce event delivered twice | grant state derived from duplicates |
| F4 | Out-of-order events | reversed event delivery | ordering-derived authority |
| F5 | Rate limit | `ProviderRateLimitedError` | commerce success fabricated; allow decision changed |
| F6 | Malformed response | `ProviderMalformedResponseError` | internals/payload leaked in error path |
| F7 | Invalid session | bogus/malformed/unknown bearer | protected loader or provider invoked |
| F8 | Revocation | revoke after issuance | previously-valid token still authorizes |
| F9 | Concurrent write | two writers, one `expected_version` | loser recorded as success; state corrupted |
| F10 | Provider recovery | circuit OPEN → clock advance → probe success | stale UNAVAILABLE masquerading as READY (or vice versa) |
| F11 | Telemetry sink failure | sink raising inside emitter | serving path affected; exception text exposed |
| F12 | Invalid correlation context | malformed/absent request id, no scope | unbounded user input trusted; empty id served |

## 5. Test implementation plan

Single new file: `tests/test_forge_cross_bloc.py` (Book II cross-bloc suite).
No production code changes are planned. If a scenario exposes a defect, the
defect is repaired in a **separate, justified commit** after the failing test
is committed (append-only: PLAN → ACCEPTANCE → TEST → REPAIRS → EVIDENCE).

Suite classes (one per matrix row, so each acceptance clause maps to exactly
one class):

- `TestX1IdentityPolicyProvider`, `TestX2PolicyRetrievalObservability`,
  `TestX3ProviderFailurePolicy`, `TestX4PersistenceConcurrencyAudit`,
  `TestX5QaProviderEvidence`, `TestX6CommerceIdentityEntitlement`,
  `TestX7ObservabilityErrorSecurity`, `TestX8ProviderReplacementStability`,
  `TestX9LifecycleReadinessFailure`
- `TestFailureInjection` (F1–F12)
- `TestSecurityEpistemicLaws` (Phase 5: import-discipline AST checks and
  API-surface proofs for the laws that are structural)

Harness rules:

- Build on the real composition seams: `InMemoryPersistenceGateway`,
  `ForgeAuthenticationService` (injected clock), `DefaultDenyPolicyEngine`,
  `ForgePolicyEnforcementService`, `RetrievalService`/`QAService` (Book I),
  `ProviderRegistry` + II.5 fakes, `ForgeObservabilityService` with an
  in-memory sink, `ForgeServiceContainer` + `create_forge_router` for HTTP.
- Positive controls accompany every negative assertion (a deny that is
  merely unexercised proves nothing): each scenario proves the same wiring
  ALLOWs when legitimately authorized.
- Leak assertions use unique sentinels (credentials, raw session token,
  protected corpus body, restricted research marker) asserted absent from
  serialized sinks, audit records, metrics snapshots, HTTP bodies and
  captured logs — never from object identity alone.

## 6. PostgreSQL verification recovery plan (Phase 4)

Open gap: the II.6-era `postgres` CI job failed before test execution while
pulling `postgres:16` (Docker Hub unauthenticated pull rate limit,
`toomanyrequests`) — an infrastructure/registry failure, not an application or
test failure.

1. Preserve the original failure evidence (run ids + exact log lines) in
   EVIDENCE.md.
2. Classify from logs: service container never started ⇒ zero tests executed.
3. Retry the existing job unchanged (`gh run rerun --failed`) — no workflow
   edit, no skip, no SQLite substitution.
4. Additionally execute the unmodified PostgreSQL integration suite against an
   approved local PostgreSQL 16 environment with CI-equivalent URL shape
   (`FORGE_TEST_DATABASE_URL=postgresql+psycopg2://forge:…@127.0.0.1:5432/forge_test`),
   recording exact counts and SHA. Semantics of migrations and tests are not
   touched.
5. If neither path executes PostgreSQL, the cross-bloc gate is **BLOCKED**,
   not PASS.

## 7. Execution order (Phase 6) and evidence (Phase 7)

1. Cross-bloc suite (new).
2. Six Book II focused suites (`test_forge_service_*.py`,
   `test_forge_persistence*.py`, `test_forge_postgres_integration.py`,
   `test_forge_policy.py`, `test_forge_providers.py`,
   `test_forge_observability.py`).
3. Book I canonical / retrieval / QA suites; provider contract tests;
   observability redaction tests; persistence/concurrency tests; Signal Guard.
4. Full local regression; PostgreSQL integration suite (local approved env).
5. Final CI on the exact pushed SHA (both jobs).

Baseline carried forward: **890 passed, 19 skipped locally** (19 skips = the
declared `FORGE_TEST_DATABASE_URL` integration gap, which is additionally
closed by the dedicated PostgreSQL runs). Any deviation must be explained in
EVIDENCE.md.

## 8. Governance (Phase 8)

Append-only ladder: PLAN → ACCEPTANCE → TEST IMPLEMENTATION → REPAIRS →
EVIDENCE → VERIFICATION. No amend, reset, rebase, squash or force-push; fast
forward push only; remote SHA and final CI verified. No frozen planning
document, prior ratification, workflow, or migration is modified by this
packet.
