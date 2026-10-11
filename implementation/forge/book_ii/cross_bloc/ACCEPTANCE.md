# BOOK II — CROSS-BLOC ADVERSARIAL INTEGRATION & VERIFICATION — ACCEPTANCE.md

Status: ACCEPTANCE (committed before test implementation)
Date: 2026-10-10
Start SHA: `fdf5b0747a7afb18cc7ce96bb1255aab30a92fb9`
Planning freeze head: `60e067547b9d9165d94e4f074e0db0ba58e59e24`
Dependency ratifications: I.1 `cdde1fd`, I.2 `5ce3246`, I.3 `26e8635`,
I.4 `017fc96`, I.5 `686faa7`, II.1 `598b34c`, II.2 `438a35e`, II.3 `ea1ca46`,
II.4 `ebda556`, II.5 `1496c16`, II.6 `fec9be0`.

Each clause names its executable verification. "test" = a test in the cross-bloc
suite `tests/test_forge_cross_bloc.py`; "prior suite" = a test in a ratified
Book I / Book II suite cited by name; "review" = inspection recorded with
evidence in EVIDENCE.md. Gates are PASS only if every clause verifies.

## A. Identity → Policy → Provider (X1; Ch II.3.4, II.3.8, II.4.7, II.5.1)

- A1 Expired session cannot reach a protected operation — test:
  `TestX1IdentityPolicyProvider.test_expired_session_cannot_reach_protected_operation`
  (injected clock past `expires_at` ⇒ `AuthenticationFailure(expired_session)`;
  guarded loader/provider spy never invoked).
- A2 Revoked session cannot reach a protected operation — test:
  `TestX1IdentityPolicyProvider.test_revoked_session_cannot_reach_protected_operation`.
- A3 Missing credential resolves to anonymous and is denied by policy before
  any load — test:
  `TestX1IdentityPolicyProvider.test_missing_credential_denied_before_load`.
- A4 Unknown/invalid bearer token fails closed — test:
  `TestX1IdentityPolicyProvider.test_invalid_bearer_token_fails_closed`.
- A5 Disabled user cannot authenticate nor pass enforcement — test:
  `TestX1IdentityPolicyProvider.test_disabled_user_fails_closed`.
- A6 Positive control: valid session + admitting capability authorizes and the
  loader/provider is invoked exactly once — test:
  `TestX1IdentityPolicyProvider.test_valid_session_and_capability_authorize_once`.
- A7 Decision reason and content-free audit available for both outcomes — test:
  `TestX1IdentityPolicyProvider.test_decisions_are_audited_content_free`.

## B. Policy → Retrieval → Observability (X2; Ch II.4.4, II.4.7, II.6.2, II.6.5)

- B1 Denied content is never loaded (deny-before-load is pre-retrieval) — test:
  `TestX2PolicyRetrievalObservability.test_denied_content_is_never_loaded`.
- B2 Denied content is never returned: no payload, no citation, denied reason
  recorded — test:
  `TestX2PolicyRetrievalObservability.test_denied_content_is_never_returned`.
- B3 Denied/allowed content is never logged or emitted: protected-body and
  restricted-research sentinels absent from serialized sinks, audit trails and
  captured logs — test:
  `TestX2PolicyRetrievalObservability.test_denied_content_never_reaches_telemetry`.
- B4 Retrieval access audit is ids/exposure/decision only, with the
  scope-bound correlation id (Ch II.6.1 + II.6.5) — test:
  `TestX2PolicyRetrievalObservability.test_retrieval_audit_is_content_free_and_correlated`.
- B5 Positive control: an authorized retrieval is served and audited — test:
  `TestX2PolicyRetrievalObservability.test_authorized_retrieval_is_served_and_audited`.

## C. Provider → Failure → Policy (X3; Ch II.5.7, II.5.8, II.6.7)

- C1 Provider timeout/outage cannot change or grant a policy decision — test:
  `TestX3ProviderFailurePolicy.test_provider_failure_never_changes_a_policy_decision`.
- C2 Provider failures normalize to the frozen taxonomy with `origin=provider`
  and no internals — test:
  `TestX3ProviderFailurePolicy.test_provider_failures_normalize_without_leaking`.
- C3 Commerce fallback never fabricates success — test:
  `TestX3ProviderFailurePolicy.test_commerce_outage_never_produces_success`.
- C4 Open circuit short-circuits without invoking the provider, and no access
  is granted — test:
  `TestX3ProviderFailurePolicy.test_open_circuit_grants_nothing_and_skips_provider`.

## D. Persistence → Concurrency → Audit (X4; Ch II.2.7, II.2.10)

- D1 Stale-version write is rejected and canonical state is unchanged — test:
  `TestX4PersistenceConcurrencyAudit.test_stale_write_is_rejected_and_state_unchanged`.
- D2 Duplicate critical records are rejected — test:
  `TestX4PersistenceConcurrencyAudit.test_duplicate_create_is_rejected`.
- D3 Concurrent writers with one expected version: exactly one winner, the
  loser never recorded as a successful mutation — test:
  `TestX4PersistenceConcurrencyAudit.test_concurrent_writes_have_exactly_one_winner`.
- D4 A failed multi-record transaction rolls back completely — test:
  `TestX4PersistenceConcurrencyAudit.test_failed_transaction_rolls_back_all_writes`.
- D5 A rejected write is never claimed as a successful canonical mutation by
  any event or audit record — test:
  `TestX4PersistenceConcurrencyAudit.test_rejected_write_is_never_recorded_as_success`.

## E. QA → Provider → Evidence (X5; Book I claim/evidence law, Ch II.5.1)

- E1 Provider/LLM-supplied text cannot promote a claim into validated
  empirical evidence: verdict follows evidence status only, and the canonical
  status is unchanged by asking — test:
  `TestX5QaProviderEvidence.test_generated_content_cannot_promote_a_claim`.
- E2 QA claim authority is provider-independent: identical answers with no
  registry vs. a wired fake registry; zero provider calls occur — test:
  `TestX5QaProviderEvidence.test_qa_answers_do_not_consult_providers`.
- E3 Denied objects are never cited in an answer while still being audited —
  test:
  `TestX5QaProviderEvidence.test_denied_objects_are_never_cited`.
- E4 FOUND stays distinct from SUPPORTED and research status is not promoted —
  test (plus prior suite `test_forge_retrieval`/`test_forge_qa`):
  `TestX5QaProviderEvidence.test_found_is_not_supported_and_status_is_not_promoted`.

## F. Commerce → Identity → Entitlement (X6; Ch II.4.3, II.5.3, II.6.6)

- F1 Provider customer/subscription facts cannot independently grant a FORGE
  entitlement: unregistered/provider-shaped capability atoms grant nothing —
  test:
  `TestX6CommerceIdentityEntitlement.test_provider_facts_cannot_grant_entitlement`.
- F2 Recording an entitlement-grant audit event grants nothing (entitlement
  audit is record-only; Book VI owns mutation) — test:
  `TestX6CommerceIdentityEntitlement.test_entitlement_audit_event_grants_nothing`.
- F3 Linking an external identity changes no capability and no decision —
  test:
  `TestX6CommerceIdentityEntitlement.test_identity_link_grants_nothing`.
- F4 No Book VI licensing is implemented in this packet — review: no
  entitlement mutator/state machine exists outside audit records
  (`TestSecurityEpistemicLaws.test_no_entitlement_state_machine_exists`).

## G. Observability → Error → Security (X7; Ch II.6.2, II.6.7, II.6.8)

- G1 Error paths never reveal credentials, tokens or protected bodies — test:
  `TestX7ObservabilityErrorSecurity.test_error_paths_never_reveal_secrets`.
- G2 Metrics/snapshot/events are content-free — test:
  `TestX7ObservabilityErrorSecurity.test_metrics_and_snapshot_are_content_free`.
- G3 A failing FORGE endpoint returns only the safe envelope; the log carries
  the exception class name only — test:
  `TestX7ObservabilityErrorSecurity.test_route_failure_returns_safe_envelope_only`.
- G4 Restricted research content never reaches logs at any level — test:
  `TestX7ObservabilityErrorSecurity.test_restricted_research_never_reaches_logs`.
- G5 Security audit stays distinct from provenance (separate trails, no
  cross-authority) — review + test:
  `TestSecurityEpistemicLaws.test_security_audit_is_distinct_from_provenance`.

## H. Provider Replacement → Domain Stability (X8; Ch II.5.6, II.5.9, II.5.10)

- H1 Replacing the fake registry changes no canonical record, policy decision
  or answer — test:
  `TestX8ProviderReplacementStability.test_registry_swap_changes_nothing`.
- H2 Fakes can be swapped without domain change (gate §Providers) — test:
  `TestX8ProviderReplacementStability.test_fake_llm_swap_changes_no_domain_output`.
- H3 Import discipline holds: domain modules never import providers,
  observability or transport; providers never import FastAPI/SQL — test:
  `TestSecurityEpistemicLaws.test_import_discipline`.

## I. Lifecycle → Readiness → Failure (X9; Ch II.1.5, II.5.6)

- I1 Telemetry outage/absence never blocks readiness — test:
  `TestX9LifecycleReadinessFailure.test_telemetry_never_blocks_readiness`.
- I2 Provider unavailability is disclosed as UNAVAILABLE and never masquerades
  as READY; core serving still ready (required=False) — test:
  `TestX9LifecycleReadinessFailure.test_provider_outage_never_masquerades_as_healthy`.
- I3 An unavailable *required* dependency (persistence) refuses readiness —
  test:
  `TestX9LifecycleReadinessFailure.test_required_dependency_failure_blocks_readiness`.
- I4 Readiness endpoint answers correctly with a failing telemetry sink and
  leaks nothing — test:
  `TestX9LifecycleReadinessFailure.test_ready_endpoint_survives_sink_failure`.

## J. Failure injection (F1–F12, `TestFailureInjection`)

- J1 Timeout F1: `test_timeout_fails_closed`.
- J2 Retry/alternate F2: `test_retry_delegates_to_alternate_once`.
- J3 Duplicate events F3: `test_duplicate_events_create_no_grant_state`.
- J4 Out-of-order events F4: `test_out_of_order_events_derive_no_authority`.
- J5 Rate limit F5: `test_rate_limit_maps_to_429_and_no_success`.
- J6 Malformed response F6: `test_malformed_response_fails_closed`.
- J7 Invalid session F7: `test_invalid_session_cannot_enter_guard`.
- J8 Revocation F8: `test_revocation_takes_effect_immediately`.
- J9 Concurrent write F9: `test_concurrent_write_conflict_is_deterministic`.
- J10 Provider recovery F10: `test_provider_recovery_restores_service`.
- J11 Telemetry sink failure F11: `test_sink_failure_is_isolated`.
- J12 Invalid correlation context F12: `test_invalid_correlation_context_is_replaced`.

## K. Security and epistemic laws (Phase 5, `TestSecurityEpistemicLaws`)

- K1 Authorization precedes protected content access (enforcement ordering is
  structural) — test: `test_authorization_precedes_content_access`.
- K2 Provider transport stays separate from domain authority (no provider
  import in domain) — covered by `test_import_discipline`.
- K3 Canonical identity stays separate from provider identifiers (linking
  cannot override a FORGE id) — test: `test_canonical_identity_beats_provider_ids`.
- K4 Claim/evidence/source traceability intact after cross-bloc use — prior
  suites + E4.
- K5 Entitlement audit distinct from commercial authority — covered by F2/F4.
- K6 No brokerage execution anywhere in FORGE — review: no order/trade
  execution API exists in `app/forge` (grep evidence in EVIDENCE.md).
- K7 No logging of protected content — covered by B3/G4.

## L. Frozen Book II acceptance gate — cross-bloc mapping

Every gate row must be satisfied by a ratified prior suite or a clause above;
this table is the completeness check demanded by Phase 2.

| Gate row | Satisfied by |
|---|---|
| Runtime: boot, readiness refuses critical deps, graceful shutdown, no prod test bypass | I1–I4 + prior II.1 suite (`test_forge_service_*`) |
| Database: empty PG → current schema, migration verify, projections, backup/restore smoke, duplicate/dangling fail | D1–D5 + prior II.2 suite + PostgreSQL integration runs |
| Identity: provider-independent identity, expiry/revocation, role escalation fails, collision/linking | A1–A7 + prior II.3 suite |
| Policy: deny-by-default, filtered before provider boundary, direct-ID/alias/historical/vector fail closed, prompt revocation, reason/audit | A3–A7, B1–B2 + prior II.4 suite |
| Providers: core runs on fakes, fake LLM swappable without domain change, commerce swappable, outage never grants access | C1–C4, H1–H3 |
| Observability: correlation end-to-end, protected access auditable, secrets absent from logs, dependency failures normalize | B3–B4, C2, G1–G4 |
| Evidence pack: PLAN/ACCEPTANCE/ladder/test output/EVIDENCE/unresolved issues/ratification | this packet supplies PLAN, ACCEPTANCE, ladder, test output, EVIDENCE, limitations — **ratification record is out of scope (separate authorization)** |

## M. Regression and verification (Phase 6)

- M1 Full local regression passes with baseline explained — 890 passed,
  19 skipped (skips = declared `FORGE_TEST_DATABASE_URL` gap); any deviation
  recorded and explained in EVIDENCE.md.
- M2 All six Book II focused suites, Book I canonical/retrieval/QA suites,
  provider contract, observability redaction, persistence/concurrency, Signal
  Guard pass on the packet SHA.
- M3 PostgreSQL integration suite executes against live PostgreSQL with exact
  counts and SHA recorded (approved local environment and/or CI job).

## N. PostgreSQL verification gate (Phase 4 — the open gap)

- N1 Original failure evidence preserved (run id, job, exact log lines) —
  EVIDENCE.md.
- N2 Failure classified as registry/network initialization (image pull), not
  application/test failure — EVIDENCE.md, from CI logs.
- N3 Existing PostgreSQL job retried unchanged and passing — EVIDENCE.md
  (run id + job conclusions on the tested SHA).
- N4 Approved local PostgreSQL 16 execution of the unmodified suite with exact
  counts — EVIDENCE.md.
- N5 Workflow, migrations and test semantics unchanged (empty `git diff` for
  `.github/`, migrations, PG test file) — EVIDENCE.md.
- If PostgreSQL cannot be executed by any route, the cross-bloc verification
  gate is **BLOCKED**, not PASS.

## O. Governance (Phase 8)

- O1 Append-only ladder: PLAN → ACCEPTANCE → TEST → REPAIRS → EVIDENCE →
  VERIFICATION; no amend/reset/rebase/squash/force-push; fast-forward push
  only.
- O2 No frozen planning document, prior ratification, workflow or migration is
  modified.
- O3 `GAP_ADR_001` carried forward unchanged and OPEN; no Book II ratification
  or freeze is issued by this packet.
