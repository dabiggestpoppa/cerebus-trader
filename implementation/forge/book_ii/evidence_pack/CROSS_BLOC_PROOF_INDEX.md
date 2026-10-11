# BOOK II — CROSS-BLOC PROOF INDEX (step 7 integrated)

Points at the committed cross-bloc packet
(`implementation/forge/book_ii/cross_bloc/`, ladder `6afd55a` → `b559ca4` →
`4b2d4ae` → `cfd69d0` → `5c58414` → `ae35276`). Every proof below was
re-verified at the evidence head: the 56 named gates exist, are collected,
and pass (Phase 8 integrity check).

Suite: `tests/test_forge_cross_bloc.py` — **56 tests, 11 classes.**

## 1. X1–X9 adversarial scenarios (ACCEPTANCE §A–§I)

| ID | Boundary crossed | Gate tests (exact) | Core claim proven | Evidence ref |
|---|---|---|---|---|
| X1 | Identity → Policy → Provider | `TestX1IdentityPolicyProvider`: `test_expired_session_cannot_reach_protected_operation`, `test_revoked_session_cannot_reach_protected_operation`, `test_missing_credential_denied_before_load`, `test_invalid_bearer_token_fails_closed`, `test_disabled_user_fails_closed`, `test_valid_session_and_capability_authorize_once`, `test_decisions_are_audited_content_free` | expired/revoked/missing/invalid/disabled credentials fail inside II.3 before any loader/provider call; valid session + capability loads exactly once; audit is content-free | XB EVID §6 A1–A7 |
| X2 | Policy → Retrieval → Observability | `TestX2PolicyRetrievalObservability`: `test_denied_content_is_never_loaded`, `test_denied_content_is_never_returned`, `test_denied_content_never_reaches_telemetry`, `test_retrieval_audit_is_content_free_and_correlated`, `test_authorized_retrieval_is_served_and_audited` | denied content never loaded/returned/cited/emitted; retrieval audit = 9 frozen fields, empty ids on deny, correlation-bound | XB EVID §6 B1–B5 |
| X3 | Provider → Failure → Policy | `TestX3ProviderFailurePolicy`: `test_provider_failure_never_changes_a_policy_decision`, `test_provider_failures_normalize_without_leaking`, `test_commerce_outage_never_produces_success`, `test_open_circuit_grants_nothing_and_skips_provider` | 280-decision matrix identical across outages; commerce `mode=none` raises (no synthesized success); open circuit skips provider and grants nothing | XB EVID §6 C1–C4 |
| X4 | Persistence → Concurrency → Audit | `TestX4PersistenceConcurrencyAudit`: `test_stale_write_is_rejected_and_state_unchanged`, `test_duplicate_create_is_rejected`, `test_concurrent_writes_have_exactly_one_winner`, `test_failed_transaction_rolls_back_all_writes`, `test_rejected_write_is_never_recorded_as_success` | rejected writes never mutate state or appear as success facts; batch rollback atomic | XB EVID §8 D1–D5 |
| X5 | QA → Provider → Evidence | `TestX5QaProviderEvidence`: `test_generated_content_cannot_promote_a_claim`, `test_qa_answers_do_not_consult_providers`, `test_denied_objects_are_never_cited`, `test_found_is_not_supported_and_status_is_not_promoted` | verdicts follow evidence status only; asking mutates nothing; provider registry has zero influence (0 calls); denied objects never cited but audited | XB EVID §6 E1–E4 |
| X6 | Commerce → Identity → Entitlement | `TestX6CommerceIdentityEntitlement`: `test_provider_facts_cannot_grant_entitlement`, `test_entitlement_audit_event_grants_nothing`, `test_identity_link_grants_nothing` | provider-shaped atoms are disjoint from `REGISTERED_CAPABILITIES` and deny; recording a grant event grants nothing; linking grants nothing (collision fails closed) | XB EVID §6 F1–F3 |
| X7 | Observability → Error → Security | `TestX7ObservabilityErrorSecurity`: `test_error_paths_never_reveal_secrets`, `test_metrics_and_snapshot_are_content_free`, `test_route_failure_returns_safe_envelope_only`, `test_restricted_research_never_reaches_logs` | error/telemetry paths leak no credential/token/protected body; 500 = safe envelope only; restricted research absent from logs at DEBUG | XB EVID §6–7 G1–G4 |
| X8 | Provider Replacement → Domain Stability | `TestX8ProviderReplacementStability`: `test_registry_swap_changes_nothing`, `test_fake_llm_swap_changes_no_domain_output` | healthy→failing registry swap leaves canonical records, decision matrix, answer payloads byte-identical; only readiness disclosure changes; both fakes = 0 calls | XB EVID §8 H1–H2 |
| X9 | Lifecycle → Readiness → Failure | `TestX9LifecycleReadinessFailure`: `test_telemetry_never_blocks_readiness`, `test_provider_outage_never_masquerades_as_healthy`, `test_required_dependency_failure_blocks_readiness`, `test_ready_endpoint_survives_sink_failure` | telemetry optional (`required=False`), outage disclosed `UNAVAILABLE` never `READY`, required dependency failure refuses readiness, failing sink absorbed | XB EVID §8 I1–I4 |

## 2. F1–F12 failure injections (ACCEPTANCE §J — `TestFailureInjection`)

| ID | Failure | Gate test | Outcome proven |
|---|---|---|---|
| F1 | timeout | `test_timeout_fails_closed` | classified raise, no output, decisions unchanged |
| F2 | retry/alternate | `test_retry_delegates_to_alternate_once` | retryable ⇒ 1 alternate delegation; non-retryable ⇒ no alternate |
| F3 | duplicate events | `test_duplicate_events_create_no_grant_state` | 2 audited facts, **no grant state exists**, policy still denies |
| F4 | out-of-order events | `test_out_of_order_events_derive_no_authority` | order preserved as data; no ordering-derived authority |
| F5 | rate limit | `test_rate_limit_maps_to_429_and_no_success` | RATE_LIMIT/429; commerce never succeeds |
| F6 | malformed response | `test_malformed_response_fails_closed` | DATA_INTEGRITY/500, sentinel-free |
| F7 | invalid session | `test_invalid_session_cannot_enter_guard` | loader never invoked (0 calls) |
| F8 | revocation | `test_revocation_takes_effect_immediately` | same raw token denies instantly; load count frozen |
| F9 | concurrent write | `test_concurrent_write_conflict_is_deterministic` | 3/3 repeats: one winner, `StaleWriteConflict`, identical final state |
| F10 | provider recovery | `test_provider_recovery_restores_service` | OPEN → half-open probe → CLOSED; readiness returns `READY` |
| F11 | telemetry sink failure | `test_sink_failure_is_isolated` | emit never raises; drops counted |
| F12 | invalid correlation context | `test_invalid_correlation_context_is_replaced` | unsafe/absent ids rejected; `fg-` regeneration; `unattributed` fallback |

**Cross-cutting invariant proven:** no injected failure produced an
unauthorized successful state transition (XB EVID §5).

## 3. Security / epistemic laws (ACCEPTANCE §K — `TestSecurityEpistemicLaws`)

| Law | Gate test | Mechanism |
|---|---|---|
| Authorization precedes content access | `test_authorization_precedes_content_access` | loader set == allowed set exactly across a mixed run; anonymous = `()` |
| Import discipline (providers ⇂ domain, transport) | `test_import_discipline` | AST over 10 domain modules + `app/forge/providers/*` |
| Canonical identity beats provider ids | `test_canonical_identity_beats_provider_ids` | collision rejected; `ForgeUser.create` has no provider parameter |
| Security audit ≠ provenance | `test_security_audit_is_distinct_from_provenance` | audit writes leave provenance edges untouched; AST both directions |
| No entitlement state machine | `test_no_entitlement_state_machine_exists` | AST: no entitlement mutators outside `record_entitlement_event`; `ForgePrincipal` field set exact |
| No brokerage execution surface | `test_no_brokerage_execution_api` | AST over `app/forge`: no order/position execution symbol |

Plus the ACCEPTANCE-referenced suites outside the file: prior Book I QA/
retrieval suites for K4 traceability (E4 references `test_forge_qa` /
`test_forge_retrieval`).

## 4. Redaction repair (RED → GREEN)

| Step | Evidence |
|---|---|
| RED (test committed first, run against pre-repair code) | `TestX7…test_metrics_and_snapshot_are_content_free` FAILED: sentinel `sk-live-crossbloc-…` present in serialized event via typed field `model_id` (XB EVID §7, verbatim output) |
| Repair | `4b2d4ae` — `scrub_text()` applied to typed string fields at construction (after the existing bound; field set/vocab/determinism unchanged) |
| GREEN | XB 56 passed; `test_forge_observability.py` 104 passed (no ratified expectation changed); re-verified at `ae35276` (108 passed for X7+obs) |

## 5. Provider replacement / readiness proofs (index)

- Replacement: X8 H1–H2 + S5 contract harness (`tests/provider_contract.py`
  imported by `test_forge_providers.py`) — neutral-port level only; real
  vendor SDKs absent (GAP-06).
- Identity/policy/provider isolation: X1 + X3 + `test_import_discipline`.
- Persistence/concurrency/audit: X4 + F9 (+ II.2 suite for SQL-level races).
- QA/evidence authority: X5 (+ Book I `test_g7…`, `test_c6…` status-law tests).
- Readiness under optional-provider failure: X9 + F10/F11.
- Correlation under denial: X2 B3/B4 (scope-bound audit ids).

## 6. Verification of this index (Phase 8)

- All 56 `Class.test_name` tokens referenced by
  `cross_bloc/ACCEPTANCE.md` were programmatic-extracted and intersected
  with `pytest --collect-only`: 56/56 collected (4 non-gate tokens are
  suite-file references). Recorded in `cross_bloc/EVIDENCE.md` §2 and
  re-run at the evidence head (`CONTRACT_FREEZE_READINESS.md` §9).
- Full cross-bloc suite re-run at `ae35276`: **56 passed** (local), and in
  CI `test` job (946 total).
