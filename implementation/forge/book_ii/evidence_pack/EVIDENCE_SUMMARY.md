# BOOK II — EVIDENCE SUMMARY (six Bloc records reconciled)

Evidence head: `ae35276`. Each Bloc record is reconciled from its committed
`PLAN.md` / `ACCEPTANCE.md` / `EVIDENCE.md` / `RATIFICATION.md`. Bloc
responsibilities are kept separate; nothing below is re-attributed across
Bloc boundaries.

## 1. Bloc dispositions (as committed)

| Bloc | Scope (frozen) | Verdict as committed | Ratification commit | Focused suite | Local counts at ratification |
|---|---|---|---|---|---|
| II.1 Service Skeleton | composition, namespace, config, health/readiness, errors, lifecycle | CLOSED — PASS | `598b34c` | `test_forge_service_composition.py` (36) | full repo 166/0 at II.1 |
| II.2 Persistence | port/injection, canonical storage, integrity, transactions, migrations, concurrency | CLOSED — PASS | `438a35e` | `test_forge_persistence.py` (56) + PG (19) | full repo 217/0 at II.2 |
| II.3 Identity & Session | identity model, sessions, tokens, linking, roles, revocation | CLOSED — PASS | `ea1ca46` | `test_forge_identity.py` (66) | full repo 283 passed/14 skipped |
| II.4 Policy & Access Control | exposure matrix, capability atoms, deny-by-default, pre-loader enforcement, audit | CLOSED — PASS | `ebda556` | `test_forge_policy.py` (86) | full repo 369/14 |
| II.5 Provider Ports | 4 typed ports, registry/factory, 8-class failures, resilience, fakes, contract harness | PASS — CLOSED | `1496c16` | `test_forge_providers.py` (74) + `tests/provider_contract.py` | full repo 786 green (EVID §3) |
| II.6 Observability | correlation, events, metrics, 4 audit streams, error contract, usage ledger | PASS — CLOSED | `fec9be0` | `test_forge_observability.py` (104) | full repo 890 passed/19 skipped |
| Cross-bloc packet (step 7) | X1–X9, F1–F12, laws | CROSS-BLOC VALIDATION — PASS (VERIFICATION.md) | *none by design* | `test_forge_cross_bloc.py` (56) | full repo 946/19; PG-attached 965/0 |

All seven append-only ladders are recorded in their packets; no amend,
squash, rebase or force-push occurred on `forge` (verified in
`CI_POSTGRESQL_LEDGER.md` §5).

## 2. Bloc-by-bloc reconciliation (frozen responsibilities kept separate)

### II.1 — Service Skeleton
- Owns: `/forge/v1` namespace, intentional composition (`include_router`),
  typed `ForgeConfig`, liveness/readiness/meta, safe error envelope,
  explicit `ForgeLifecycle`, container seam.
- Does NOT own (per its own non-goals): persistence, identity, policy,
  providers, canonical routes. Verified: S1 non-goal tests + later Blocs
  superseded the II.1 wiring guards fail-closed (documented in II.2/II.4/II.5
  ratifications).
- Reconciliation note: II.1’s readiness vocabulary (`NOT_CONFIGURED` /
  `NOT_APPLICABLE`, `required=False`) is the single honesty pattern reused by
  II.2/II.5/II.6 and re-verified cross-bloc (XB I1–I4).

### II.2 — Persistence
- Owns: `PersistenceGateway` port, explicit injection (no singleton), SQL
  gateway + first-party migrations (001, 002), integrity kernel
  (duplicate/self-reference/dangling/illegal-transition), optimistic
  `persisted_version`, atomic `transaction()`, readiness ping semantics.
- PostgreSQL: integration module executes in CI (and, since the cross-bloc
  packet, also in an approved local PostgreSQL 16 — ledger L-09).
- Declared non-goals: no pgvector/embeddings/RAG, no public CRUD routes, no
  identity/policy. **These non-goals overlap frozen chapters II.2.4 / II.2.6
  — surfaced as GAP-01 / GAP-05, not silently accepted.**

### II.3 — Identity & Session
- Owns: `ForgeUser`/`ForgeSession`/`ForgePrincipal`, opaque 256-bit tokens
  persisted only as SHA-256 digests, expiry against an injected clock,
  revocation (single + all), external-identity links with collision
  rejection, roles as data.
- Laws proven executable: IDENTITY ≠ ENTITLEMENT, AUTHENTICATION ≠
  AUTHORIZATION, SESSION ≠ LICENSE, PROVIDER ID ≠ FORGE ID.
- Qualifications: minimal user account only (org/billing account = Book VI);
  `SERVICE` role exists but no job/callback consumers yet (CH-II.3.7 Q).

### II.4 — Policy & Access Control
- Owns: one central exposure matrix, exact-match capability atoms,
  `DefaultDenyPolicyEngine`, `ForgePolicyEnforcementService` (authorize →
  then load), bounded content-free policy audit, reason codes.
- Does NOT own: identity construction (consumes II.3 principal), entitlement
  production (Book VI seam), retrieval status authority (Book I).
- Qualifications: entitlement resolver rules (expiration/grace) need Book VI
  state (GAP-03); explain = decision detail + audit records, no admin
  tooling; depth policy proven only as “depth never bypasses exposure”.

### II.5 — Provider Ports
- Owns: 4 neutral ports with 8-element contract specs, 8-class failure
  taxonomy with retry ownership, `ProviderRegistry`/`ProviderFactory`
  (config-selected, frozen after composition), per-port fallback modes
  (`llm=alternate`, `commerce=none`, `notification=record`, `storage=none`),
  9 scripted fake scenarios on a simulated clock, shared replacement
  harness `tests/provider_contract.py`.
- Does NOT own: vendor adapters (OpenRouter = Book IV, Whop = Book VI),
  network calls, credential use, entitlement state.
- GAP_ADR_001 recorded OPEN in this packet and carried unchanged since.

### II.6 — Observability
- Owns: correlation scope with disclosed fallback, bounded structured events
  (frozen field set), component/operation tracing vocabulary, frozen metric
  names, four distinct audit streams (telemetry / security / usage /
  entitlement), 9-class error taxonomy + `safe_error_response`, usage
  ledger — all in-process, no vendor, `required=False` always.
- Post-ratification change (cross-bloc step 7): typed-event-field scrub
  repair `4b2d4ae` after a RED adversarial finding; II.6’s ratified tests
  (104) stayed green — see `CROSS_BLOC_PROOF_INDEX.md` §4.
- Its recorded CI limitation (postgres job blocked by registry outage on the
  II.6 head) was subsequently recovered: ledger L-05…L-08.

## 3. Consolidated executable evidence (current head `ae35276`)

| Suite group | Command result |
|---|---|
| Cross-bloc | 56 passed |
| Six Book II suites (S1–S6) | 478 passed |
| Book I canonical/retrieval/QA | 420 passed |
| Signal Guard | 48 passed |
| Full local regression | **946 passed, 19 skipped** (baseline 890 + 56) |
| PostgreSQL integration (approved local PG 16) | 19 passed |
| Full suite with CI postgres-job env | **965 passed, 0 skipped** |
| CI `test` job @ `ae35276` | 946 passed, 19 skipped (run 38181284353) |
| CI `postgres` job @ `ae35276` | 965 passed; PG module 19; II.3 identity 7 (run 38181284353) |

Skips (19) are exclusively the `FORGE_TEST_DATABASE_URL`-gated module,
executed by both CI and the approved local PostgreSQL runs — never skipped
in the environments that claim PostgreSQL coverage.

## 4. Defects repaired on the Book II ladder (append-only, none hidden)

| Bloc / step | Defect | Repair commit |
|---|---|---|
| II.2 | failed-seed transaction not atomic (found by its own test); env-drift route-collection failures remotely (pinned fastapi/starlette/SQLAlchemy) | recorded in II.2 EVIDENCE §17 ladder (`cca3bd9`…`2d5a8e6`) |
| II.3 | in-memory identity-link rollback, SQL duplicate pre-checks, `DanglingReference` import | II.3 EVIDENCE §283 (ladder `6f2e549` etc.) |
| II.4 | kernel matrix fidelity; superseded II.2 guard test | `d768d87`, `7b9e2df` |
| II.5 | export fix rung | `90ede0f` |
| Cross-bloc | **typed event fields not scrubbed (secret-shaped value reached sinks)** — RED→GREEN proven | `4b2d4ae` |

## 5. Frozen Book II gate record status

`ACCEPTANCE_MATRIX.md` §A “Final Book II evidence records”: G-F1…G-F6
recorded at this head; G-F7 (Book II ratification commit) does not exist —
by design (ratification not authorized).

## 6. Known exclusions held (Book II plan `# BOOK II EXCLUSIONS`)

No market calculations/CEREBUS model logic; no TradingView indicators; no
production Whop-specific behavior; no pricing decisions; no frontend
dashboards; no research promotion workflows; no autonomous
trading/execution; no personalized financial advice; no final production
security certification (Book VIII). Exclusion reviews are recorded in each
bloc EVIDENCE §Exclusions and re-checked cross-bloc (XB `K6`, import
discipline).

## 7. What this summary does NOT claim

- Not production readiness (see `CONTRACT_FREEZE_READINESS.md` §8).
- Not Book-level ratification or contract freeze.
- Not satisfaction of every frozen gate bullet — unmet/qualified rows are
  itemised in `ACCEPTANCE_MATRIX.md` and classified in `OPEN_GAP_REGISTER.md`.
