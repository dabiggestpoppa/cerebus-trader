# BOOK II / BLOC II.5 — PROVIDER PORTS & ADAPTER BOUNDARIES — EVIDENCE.md

Status: EVIDENCE
Date: 2026-10-09

## 1. Phase 0 record (executed before any change)

- Authoritative starting remote HEAD: `218c521013a2c3513d4a4409aff69188965492ec`
  (verified `git fetch origin forge` ⇒ local HEAD == `origin/forge` == `218c521`,
  `git status --short --untracked-files=no` empty, 217 commits at start).
- Planning freeze head `60e067547b9d9165d94e4f074e0db0ba58e59e24` verified
  ancestor of the start SHA (Phase 0 of the accepted dependency audit; re-run
  `git merge-base --is-ancestor` this session: OK).
- All nine predecessor ratifications verified ancestors of the start SHA:

| Dependency | Ratification head | Ancestor check |
|---|---|---|
| I.1 Canonical Registry Kernel | `aca9438` | OK |
| I.2 Source & Provenance Fabric | `5ce3246` | OK |
| I.3 Canonical Backfill | `26e8635` | OK |
| I.4 Retrieval Compiler | `017fc96` | OK |
| I.5 Corpus QA/Freeze | `686faa7` | OK |
| II.1 Service Skeleton | `598b34c` | OK |
| II.2 Persistence | `772a0d2` | OK |
| II.3 Identity & Session | `cad9cd7` | OK |
| II.4 Policy & Access Control | `ebda556` | OK |

- Baseline local suite (pre-change, recorded by the accepted audit):
  `712 passed, 19 skipped` (the 19 skips are the PostgreSQL integration tests,
  CI-only).

## 2. Append-only ladder (this bloc)

| Rung | SHA | Content |
|---|---|---|
| plan + acceptance + GAP/ADR | `a6bdc9f` | PLAN.md, ACCEPTANCE.md, GAP_ADR_001 |
| provider ports | `eb6a7b8` | `app/forge/providers/` (10 modules) |
| composition seam | `11aa9cf` | config/container/lifecycle/app.main + 3 legacy supersessions |
| tests | `7c52ff1` | `tests/provider_contract.py`, `tests/test_forge_providers.py` |
| export fix | `90ede0f` | CHECKOUT_STATUSES export (staging miss; see §9) |

No amend/squash; predecessor artifacts untouched. `git status` clean between
rungs.

## 3. Exact test counts (local, Python 3.11.9, Windows)

- Focused II.5 suite `tests/test_forge_providers.py`: **74 passed, 0 failed**
  (planned ≥68; 1.4–2.0 s).

| Class (ACCEPTANCE clause) | Tests |
|---|---|
| TestContractDoctrine (A/B) | 7 |
| TestLLMPort (C) | 7 |
| TestCommercePort (D) | 10 |
| TestNotificationPort (E) | 3 |
| TestStoragePort (F) | 5 |
| TestRegistryFactory (G) | 7 |
| TestCircuitFallback (H) | 9 |
| TestFakeScenarios (I) | 5 |
| TestContainerReadiness (seam) | 8 |
| TestFrozenAcceptanceII5 (J) | 5 |
| TestReplacementContractMatrix (J5/II.5.10) | 8 |
| **Total** | **74** |

- Full local regression: **786 passed, 19 skipped, 0 failed** (10.9 s)
  = baseline 712 + 74 new; the 19 skips remain the CI-only PostgreSQL tests.
- Supersession-affected suites re-run after the seam change:
  `tests/test_forge_service_composition.py` + `tests/test_forge_persistence.py`
  + `tests/test_forge_retrieval.py` = **216 passed**.
- Full suite re-run after final edits: **786 passed, 19 skipped** (exit 0).

## 4. Ch II.5.9 scenario → test mapping ("one each")

| Scenario | Test |
|---|---|
| success | TestFakeScenarios::test_scenario_success_and_determinism_all_ports |
| latency | TestFakeScenarios::test_scenario_latency_simulated |
| timeout | TestLLMPort::test_timeout_uses_simulated_clock + TestFakeScenarios::test_scenario_timeout_notification |
| duplicate events | TestCommercePort::test_duplicate_events_collapse_on_event_id |
| out-of-order events | TestCommercePort::test_out_of_order_events_reduce_to_identical_state |
| invalid signature | TestCommercePort::test_invalid_signature_is_authentication_failed |
| invalid event shape | TestCommercePort::test_invalid_shape_is_invalid_request |
| rate limit | TestCommercePort::test_rate_limit_carries_retry_after + TestLLMPort::test_hard_failure_normalizes_and_never_retries |
| hard failure | TestFakeScenarios::test_scenario_hard_failure_all_ports (all 8 classes × 4 ports, `calls == 1` each ⇒ no internal retry) |

No real sleeping anywhere: all latency/timeouts run on `SimulatedClock`;
wall-clock assertions (< 0.5–1.0 s for 8–32 simulated seconds) enforce it.

## 5. Frozen Acceptance II.5 clauses (verbatim) → evidence

1. *core application passes with only fake providers* —
   `test_core_application_passes_with_only_fake_providers`: `app.main`
   composition builds only `fake` bindings; TestClient health/ready/meta all
   200; with `FORGE_OPENROUTER_API_KEY` set the selection stays `fake` and the
   sentinel never appears in diagnostics/repr.
2. *no provider identifier is required as core domain PK* —
   `test_no_provider_identifier_is_required_as_core_domain_pk` (AST scan of
   all domain modules for vendor string constants and vendor-named fields) +
   `test_domain_modules_never_import_providers` +
   `test_no_provider_identifier_branching_in_domain` (AST `Compare` scan).
3. *commerce outage cannot grant access* —
   `test_commerce_outage_cannot_grant_access`: grant flag never set under
   outage; default-deny decision unaffected; plus
   `test_commerce_outage_propagates_without_fabricated_success`.
4. *LLM outage cannot corrupt canonical state* —
   `test_llm_outage_cannot_corrupt_canonical_state`: canonical registry
   snapshot (content hashes + statuses) identical across a failed generate,
   plus structural isolation (canonical/schemas/provenance/persistence never
   import `app.forge.providers`).
5. *adapter replacement requires composition/config change, not domain rewrite* —
   `test_adapter_replacement_is_composition_change` (factory/config swap in
   both directions, domain modules never import the registry) +
   `TestReplacementContractMatrix` (the identical `tests/provider_contract.py`
   harness passes for every fake and every locally defined alternate adapter).

## 6. Honesty disclosures (seam semantics)

- Readiness entries for `llm`/`commerce`/`notification`/`storage` are
  `required=False` at II.5: no serving path consumes providers yet, so they
  are disclosed with live health (`READY`/`UNAVAILABLE`) but never block and
  are never claimed as required. The consuming Bloc flips the flag (same law
  II.1 applied to future dependencies). `openrouter`/`whop` remain
  `NOT_CONFIGURED` — concrete vendor adapters do not exist at II.5.
- Probe exceptions are absorbed as `UNAVAILABLE` with the exception class name
  only (test asserts a sentinel value never leaks).
- Credentials (`openrouter_api_key`, `whop_api_key`) are **carried, unread**:
  `repr=False`, absent from diagnostics (presence booleans only), absent from
  all logs; consumption belongs to the Book IV/VI adapters.
- Scan exemptions (test comments disclose them): composition roots
  (`app/main.py`, `app/forge/service/container.py`) may import the registry;
  `app/forge/config.py` is exempt from the *vendor-name* scan only (it names
  credential-presence flags after future vendors by design) and remains in the
  import-isolation scan.
- Legacy supersessions (in place, II.2/II.4 precedent, each with an explicit
  supersession docstring): `test_container_rejects_wired_providers_at_ii_1`
  (composition), `test_container_still_rejects_policy_and_providers`
  (persistence), `test_no_commercial_or_provider_object_is_created`
  (retrieval — composition root now wires deterministic in-process fakes; still
  no commercial vendor object, credential, or network client).

## 7. Deviations from PLAN.md (all recorded, none hidden)

- **§12 staging**: the three legacy supersession edits rode with the seam
  rung (`11aa9cf`) instead of the tests rung, so every ladder rung's tree is
  green. Content identical to PLAN §10.
- **Extra rung `90ede0f`**: `CHECKOUT_STATUSES` was not staged with `7c52ff1`
  (staging miss), so rung `7c52ff1` alone is not self-contained; the export
  rung follows immediately and the suite has been green from there on. Not
  amended (append-only law).
- **Counts**: focused total 74 vs planned ≥68; TestCircuitFallback 9 vs
  planned 7 (added failed-probe re-open and the all-policies
  never-fabricate property); TestFakeScenarios 5 vs planned 11 — the nine
  Ch II.5.9 scenarios are covered as a *spread* with the mapping in §4
  instead of concentrating duplicates in one class; total unaffected.

## 8. Exclusions held (review)

- No vendor adapter, SDK, HTTP client, socket, or SQL driver exists or is
  imported anywhere in `app/forge/providers/` (AST-enforced by
  `test_providers_package_import_purity`).
- No network call is made by any test (fakes in-process; `.invalid` /
  `fake-blob://` identifiers inert).
- No migration/schema change: `git diff 218c521..HEAD` touches no SQL, no
  `migrations/`, no planning/canonical corpus file.
- No observability/metrics/tracing (II.6), no entitlement mutation (Book VI),
  no prompt/retrieval intelligence (Book IV), no market-data ports (Book III).
- `GAP_ADR_001_PHASE_ORDER_VS_BLOC_DEPENDENCY.md` recorded **OPEN** — phase
  grouping vs dependency law is reported for operator/CC decision before
  Phase C, not resolved unilaterally.

## 9. Known limitations

- PostgreSQL integration tests (19) execute only in CI, as at I.5/II.4 —
  recorded as a limitation, not a pass.
- The "alternate adapters" proving Ch II.5.10 are test-local stand-ins, not
  real vendors; real-adapter contract runs happen when Book IV/VI add them to
  the matrix (zero suite changes required).
- Rung `7c52ff1` is not self-contained (§7); CI runs the final SHA only.

## 10. CI verification

Pushed and verified in the final verification-record rung (see git log after
this file's commit). Local exit statuses above were captured directly.
