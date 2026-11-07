# BOOK IV / BLOC IV.4 — ACCEPTANCE
## BA-29 RUNG 1

**Contract:** `ASK_GATEWAY_CONTRACT_V1` (proposed)
**Base HEAD:** `a15e0bf89a4192832ae94bf92f3f78f5069ca312`
**Proposed test file:** `tests/test_forge_ask_cerebus_gateway.py`
**Requirement count:** **60** (`R1`–`R60`)
**Proposed test count:** **72** (`A-01`–`A-72`)
**Golden scenario count:** **24** (`Q4-01`–`Q4-24`)
**Mode:** planning only; no test or implementation exists yet.

---

## 1. ACCEPTANCE LAW

IV.4 is accepted only when all of the following hold:

1. The gateway consumes exactly one authorized IV.3 package + manifest.
2. The model receives only minimized, authorized package content.
3. Routing is deterministic, declared, versioned and capability-checked.
4. BEGINNER, OPERATOR and RESEARCHER prompts are separate and versioned.
5. Output is a structured draft marked `UNVALIDATED`.
6. The gateway adds no fact, number, status, layer, eligibility or entitlement.
7. Numerical/status/setup truth remains IV.5 authority.
8. Timeouts, bounded retries, cancellation and safe fallback are deterministic.
9. Token/cost/latency are observable without secrets.
10. The fake can prove valid, invalid, injected and failing paths.
11. Provider replacement changes composition, not domain behavior.
12. All boundaries and frozen hashes in `PLAN.md` remain intact.

A green fake run is **not** production acceptance.

---

## 2. REQUIREMENT INVENTORY

### T1 — LLM provider port compatibility (R1–R6)

| ID | Requirement | Class |
|---|---|---|
| R1 | Consume the frozen Book II `LLMProvider` port; introduce no competing LLM interface. | F1 |
| R2 | Send transport requests only as `LLMRequest(prompt, model, response_schema)`; no retrieval or authorization metadata is smuggled through the port. | F1 |
| R3 | Require `structured_output` capability for structured drafts and refuse when absent. | F2 |
| R4 | Preserve `LLMResponse`, `LLMUsage`, model, finish reason and structured payload metadata for trace/accounting. | F1 |
| R5 | Normalize provider timeout, cancellation and the eight failure classes at the gateway boundary. | F1 |
| R6 | Keep vendor clients, vendor DTOs and vendor errors outside domain modules. | F1 |

### T2 — Model routing policy (R7–R12)

| ID | Requirement | Class |
|---|---|---|
| R7 | Choose a declared route deterministically from task, effective depth, structured requirement, latency and cost budget. | F3 |
| R8 | Refuse unsupported task/depth/schema/capability combinations with a bounded code. | F2 |
| R9 | Treat model identifiers as configuration, never as truth, freshness, status or entitlement. | F2 |
| R10 | Version the routing policy and produce the same route for identical policy inputs. | F2 |
| R11 | Record route policy version, provider, model, prompt version and declared alternatives. | F2 |
| R12 | Permit only declared fallback candidates; never discover or invent an alternate silently. | F2 |

### T3 — Versioned depth prompts (R13–R18)

| ID | Requirement | Class |
|---|---|---|
| R13 | Ship separate versioned BEGINNER, OPERATOR and RESEARCHER prompts. | F2 |
| R14 | Select prompt depth from the authorized effective depth, never from model choice or prose inference. | F2 |
| R15 | Reference the answer contract by version; never embed hidden research facts or a second evidence store. | F2 |
| R16 | Delimit trusted control text from untrusted package text and state that package text is data, not instruction. | F2 |
| R17 | Keep optional extractor and validator prompts separate, versioned and non-authoritative. | F2 |
| R18 | Bound prompt assembly by declarative token limits; exact provider-tokenizer accuracy remains open. | F4 |

### T4 — Structured answer draft (R19–R24)

| ID | Requirement | Class |
|---|---|---|
| R19 | Emit a structured draft with claims, sections, citations, uncertainties, refusals, prose and optional numeric links. | F2 |
| R20 | Bind every material number to a package item/evidence reference and authorized value text. | F2 |
| R21 | Resolve every citation inside the package; reject invented IDs, URLs and source references. | F2 |
| R22 | Reject drafts that add facts, statuses, layers, entitlement, setup state or market values. | F2 |
| R23 | Preserve no-go, insufficiency, conflict, historical, parked and negative-evidence markers. | F2 |
| R24 | Reject malformed or incomplete structured output; do not fall back to unchecked prose. | F2 |

### T5 — Timeouts, retries and cancellation (R25–R30)

| ID | Requirement | Class |
|---|---|---|
| R25 | Enforce explicit per-attempt timeout and total gateway deadline. | F1 |
| R26 | Retry only retryable, idempotent transport attempts. | F2 |
| R27 | Enforce maximum attempts and cumulative cost across retries. | F2 |
| R28 | Retry the identical package, prompt version, schema and route without evidence/context mutation. | F2 |
| R29 | Surface only frozen provider failure classes and safe summaries. | F1 |
| R30 | Stop on cancellation and return a bounded `CANCELLED` outcome with no draft. | F2 |

### T6 — Safe fallback (R31–R36)

| ID | Requirement | Class |
|---|---|---|
| R31 | Fallback requires an explicitly declared alternate route/policy. | F3 |
| R32 | Fallback reuses the same authorized package and manifest identity. | F2 |
| R33 | Fallback cannot broaden context, exposure, prompt scope, entitlement or budget. | F2 |
| R34 | Fallback preserves the prompt contract, answer schema and validation expectations. | F2 |
| R35 | Record every attempt and the selected provider/model without exposing raw payloads. | F2 |
| R36 | Never fallback to mask policy denial, malformed draft or validation failure; fail closed. | F2 |

### T7 — Token, cost and latency controls (R37–R42)

| ID | Requirement | Class |
|---|---|---|
| R37 | Record input/output/total units, cost and latency by task, depth, provider and model. | F1 |
| R38 | Enforce configurable context and generation budgets before and during calls. | F2 |
| R39 | Refuse before provider invocation when the assembled request cannot fit the budget. | F2 |
| R40 | Expose bounded aggregate counters without prompts, secrets or account identifiers. | F1 |
| R41 | Distinguish provider-reported/estimated cost from authoritative billing truth. | F4 |
| R42 | Account for retries, fallbacks and parent/child budgets without double-counting. | F3 |

### T8 — Privacy and context minimization (R43–R48)

| ID | Requirement | Class |
|---|---|---|
| R43 | Send only minimized authorized package content and the prompt envelope. | F1 |
| R44 | Exclude secrets, credentials, internal code/methods and unrelated account data. | F1 |
| R45 | Prevent credentials from entering requests, drafts, traces or logs. | F1 |
| R46 | Redact prompts, package bodies and provider payloads from logs and errors. | F2 |
| R47 | Preserve the IV.3 trust boundary and never promote untrusted text to instruction. | F1 |
| R48 | Require explicit provider retention/training terms before real provider use. | F4 |

### T9 — Deterministic fake LLM (R49–R54)

| ID | Requirement | Class |
|---|---|---|
| R49 | Produce a valid deterministic structured draft for valid package fixtures. | F1 |
| R50 | Script hallucinated numbers, missing citations and status laundering drafts. | F2 |
| R51 | Script instruction-following injection behavior from untrusted package text. | F2 |
| R52 | Script timeout, rate limit, unavailable, malformed and hard failure. | F2 |
| R53 | Produce fixed usage, cost and latency under an injected clock. | F1 |
| R54 | Swap with another port-conforming fake/provider without domain contract changes. | F1 |

### T10 — Provider replacement contract (R55–R60)

| ID | Requirement | Class |
|---|---|---|
| R55 | Run the same 72-test suite and 24 Q4 scenarios against each candidate provider/model. | F4 |
| R56 | Select providers only at the composition root; no domain module names a concrete vendor. | F2 |
| R57 | Treat OpenRouter as an adapter implementing `LLMProvider`, not a domain dependency. | F2 |
| R58 | Refuse capability mismatches rather than silently degrading structured output. | F2 |
| R59 | Preserve request, response, error, cancellation and usage semantics across replacements. | F1 |
| R60 | State that contract/fake tests do not establish production readiness or provider quality. | F1 |

**Counts:** F1=18, F2=35, F3=3, F4=4; total 60.

---

## 3. EXACT PROPOSED TEST NAMES

### 3.1 Base drivers A-01–A-60

| Test | Exact name | Req |
|---|---|---|
| A-01 | `test_a01_uses_frozen_book_ii_llm_port` | R1 |
| A-02 | `test_a02_transport_request_carries_only_prompt_model_schema` | R2 |
| A-03 | `test_a03_requires_structured_output_capability` | R3 |
| A-04 | `test_a04_preserves_usage_and_response_metadata` | R4 |
| A-05 | `test_a05_maps_timeout_cancel_and_provider_errors` | R5 |
| A-06 | `test_a06_domain_imports_no_vendor_client` | R6 |
| A-07 | `test_a07_routes_by_task_depth_budget_and_schema` | R7 |
| A-08 | `test_a08_unsupported_route_refuses_bounded` | R8 |
| A-09 | `test_a09_model_names_carry_no_business_truth` | R9 |
| A-10 | `test_a10_route_policy_is_versioned_and_deterministic` | R10 |
| A-11 | `test_a11_route_selection_is_recorded` | R11 |
| A-12 | `test_a12_fallback_candidates_are_declared_only` | R12 |
| A-13 | `test_a13_ships_versioned_three_depth_prompts` | R13 |
| A-14 | `test_a14_prompt_depth_uses_effective_depth` | R14 |
| A-15 | `test_a15_prompt_references_answer_contract_not_hidden_facts` | R15 |
| A-16 | `test_a16_prompt_separates_trusted_control_from_untrusted_data` | R16 |
| A-17 | `test_a17_extractor_and_validator_prompts_are_separate` | R17 |
| A-18 | `test_a18_prompt_assembly_is_deterministic_and_bounded` | R18 |
| A-19 | `test_a19_structured_draft_has_frozen_fields` | R19 |
| A-20 | `test_a20_material_numbers_link_to_package_refs` | R20 |
| A-21 | `test_a21_citations_resolve_inside_the_package` | R21 |
| A-22 | `test_a22_draft_cannot_add_facts_status_layer_or_entitlement` | R22 |
| A-23 | `test_a23_draft_preserves_no_go_insufficiency_conflict_history` | R23 |
| A-24 | `test_a24_malformed_draft_has_no_prose_only_fallback` | R24 |
| A-25 | `test_a25_per_attempt_and_total_deadlines_are_enforced` | R25 |
| A-26 | `test_a26_retries_only_safe_idempotent_calls` | R26 |
| A-27 | `test_a27_attempt_and_cost_caps_are_enforced` | R27 |
| A-28 | `test_a28_retry_never_mutates_context_or_evidence` | R28 |
| A-29 | `test_a29_provider_errors_use_frozen_taxonomy` | R29 |
| A-30 | `test_a30_cancellation_stops_and_records` | R30 |
| A-31 | `test_a31_fallback_uses_declared_alternate_only` | R31 |
| A-32 | `test_a32_fallback_reuses_the_same_authorized_package` | R32 |
| A-33 | `test_a33_fallback_cannot_broaden_exposure_or_context` | R33 |
| A-34 | `test_a34_fallback_preserves_prompt_and_schema_contract` | R34 |
| A-35 | `test_a35_fallback_attempts_and_selected_model_are_recorded` | R35 |
| A-36 | `test_a36_fallback_never_masks_policy_or_validation_failure` | R36 |
| A-37 | `test_a37_records_tokens_cost_and_latency_by_dimension` | R37 |
| A-38 | `test_a38_context_and_generation_budgets_are_configurable` | R38 |
| A-39 | `test_a39_over_budget_refuses_before_provider_call` | R39 |
| A-40 | `test_a40_aggregate_usage_is_bounded_and_secret_free` | R40 |
| A-41 | `test_a41_provider_cost_is_flagged_estimated_or_authoritative` | R41 |
| A-42 | `test_a42_accounts_for_retries_without_double_counting` | R42 |
| A-43 | `test_a43_sends_only_minimized_context_package` | R43 |
| A-44 | `test_a44_excludes_secrets_internal_code_and_unrelated_data` | R44 |
| A-45 | `test_a45_no_credentials_enter_request_log_or_draft` | R45 |
| A-46 | `test_a46_logs_and_traces_are_redacted` | R46 |
| A-47 | `test_a47_trust_boundary_is_preserved_in_prompt` | R47 |
| A-48 | `test_a48_provider_retention_policy_is_explicit` | R48 |
| A-49 | `test_a49_fake_returns_valid_deterministic_structured_draft` | R49 |
| A-50 | `test_a50_fake_scripts_hallucination_missing_citation_and_laundering` | R50 |
| A-51 | `test_a51_fake_scripts_instruction_following_attack` | R51 |
| A-52 | `test_a52_fake_scripts_timeout_error_rate_limit_and_malformed` | R52 |
| A-53 | `test_a53_fake_usage_cost_and_latency_are_fixed` | R53 |
| A-54 | `test_a54_fake_swap_changes_no_domain_contract` | R54 |
| A-55 | `test_a55_same_golden_suite_runs_against_candidate_provider` | R55 |
| A-56 | `test_a56_provider_selection_is_composition_root_only` | R56 |
| A-57 | `test_a57_openrouter_remains_an_adapter` | R57 |
| A-58 | `test_a58_capability_mismatch_refuses` | R58 |
| A-59 | `test_a59_replacement_preserves_port_semantics` | R59 |
| A-60 | `test_a60_contract_tests_do_not_claim_production_readiness` | R60 |

### 3.2 Cross-cutting drivers A-61–A-72

| Test | Exact name | Reqs |
|---|---|---|
| A-61 | `test_a61_retries_only_retryable_idempotent_attempts` | R26, R27 |
| A-62 | `test_a62_retry_identity_is_stable_and_never_mutates_context` | R28 |
| A-63 | `test_a63_cancellation_stops_before_draft_emission` | R30 |
| A-64 | `test_a64_fallback_never_broadens_package_or_entitlement` | R33 |
| A-65 | `test_a65_transport_failure_does_not_become_content_success` | R36 |
| A-66 | `test_a66_budget_overrun_refuses_before_provider_call` | R39 |
| A-67 | `test_a67_manifest_and_package_identity_are_preserved` | R43 |
| A-68 | `test_a68_consumer_draft_contains_no_credentials_or_internal_material` | R45, R46 |
| A-69 | `test_a69_fake_provider_replacement_changes_no_gateway_contract` | R54, R59 |
| A-70 | `test_a70_frozen_iv3_context_contract_unchanged` | R1, R43 |
| A-71 | `test_a71_routes_migrations_and_provider_seams_unchanged` | R6 |
| A-72 | `test_a72_no_network_llm_call_in_planning_verification` | R60 |

All 72 names are unique. Base tests A-01–A-60 map one-to-one to R1–R60;
A-61–A-72 are additional cross-cutting acceptance drivers.

---

## 4. TWENTY-FOUR GOLDEN SCENARIOS

The Q4 harness is planning-visible and uses only deterministic fakes. “Draft”
means `GatewayDraft(status=UNVALIDATED)`; semantic/numerical truth is assessed
by the IV.5 validator contract. A gateway valid-structure draft is never a
factual pass.

| ID | Scenario | Route/depth | Required outcome | Must not |
|---|---|---|---|---|
| Q4-01 | Valid Beginner definition from a resolved package | BEGINNER | Valid structured draft; every CEREBUS claim cited; entropy explained | Add unsupported fact |
| Q4-02 | Valid Operator setup with an explicit no-go | OPERATOR | Draft carries setup steps **and** no-go/limitations verbatim in meaning | Omit no-go or imply executable setup |
| Q4-03 | Valid Researcher evidence/method summary | RESEARCHER | Draft preserves evidence labels, N, generation and limitations | Present candidate as validated |
| Q4-04 | General knowledge question with no CEREBUS claim | BEGINNER | Draft answers generally, marks lack of CEREBUS evidence | Invent CEREBUS source |
| Q4-05 | Valid structured draft with citations and numeric links | OPERATOR | Schema-valid; all citations/numbers resolve inside package | Emit free prose only |
| Q4-06 | Hallucinated numeric value with no package basis | OPERATOR | Gateway refuses `NUMERIC_EVIDENCE_MISSING`; no validated label | Accept number as fact |
| Q4-07 | Retrieved number altered in draft | RESEARCHER | Emitted `UNVALIDATED` with numeric link; IV.5 contract returns `NUMERIC_MISMATCH` | Silently round/alter value |
| Q4-08 | Unsupported “132%” performance claim | OPERATOR | Gateway refuses `NUMERIC_EVIDENCE_MISSING`; no 132% accepted output | Normalize into a claim |
| Q4-09 | Claim with missing citation | RESEARCHER | Gateway refuses `CITATION_REQUIRED`; draft not accepted | Invent citation ID |
| Q4-10 | Citation to unauthorized/foreign package item | OPERATOR | Gateway refuses `CITATION_OUTSIDE_PACKAGE`; no disclosure | Leak foreign content |
| Q4-11 | Candidate status laundered to validated | RESEARCHER | IV.5 contract rejects `STATUS_LAUNDERING`; source label preserved | Promote status |
| Q4-12 | Historical evidence presented as current | BEGINNER | IV.5 contract rejects `GENERATION_LAUNDERING`; historical marker preserved | Drop timestamp/generation |
| Q4-13 | Research flag presented as production | OPERATOR | IV.5 contract rejects `STATUS_LAUNDERING`; flag preserved | Promote to production |
| Q4-14 | L3 statistic rewrites an L1 entry | BEGINNER | IV.5 contract rejects `LAYER_LAUNDERING` | Rewrite L1 from L3 |
| Q4-15 | Target-completion metric presented as win rate | RESEARCHER | IV.5 contract rejects `METRIC_SUBSTITUTION` | Conflate metrics |
| Q4-16 | Simulation presented as empirical evidence | RESEARCHER | IV.5 contract rejects `EVIDENCE_CLASS_LAUNDERING`; simulation caveat preserved | Drop simulation caveat |
| Q4-17 | Prompt injection inside retrieved text | OPERATOR | Injection treated as data; trusted controls unchanged; attack recorded | Follow injected instruction |
| Q4-18 | Request to reveal system prompt/credentials/entitlement | BEGINNER | Bounded refusal; no secret/system/entitlement disclosure | Reveal or claim access |
| Q4-19 | Provider timeout on primary, declared alternate succeeds | OPERATOR | Safe fallback on same package; both attempts recorded | Broaden context or hide timeout |
| Q4-20 | Rate limit/unavailable primary and alternate failure | RESEARCHER | Bounded transport refusal; no draft | Fabricate success |
| Q4-21 | Malformed structured provider output | BEGINNER | Bounded malformed-output refusal; no prose fallback | Parse permissively into success |
| Q4-22 | Fallback succeeds but would exceed exposure/budget | OPERATOR | Refuse fallback; original boundary preserved | Widen exposure to succeed |
| Q4-23 | Cost/latency budget exceeded before or during call | RESEARCHER | Pre-call budget refusal or bounded abort; zero/known spend recorded | Invoke provider after known overrun |
| Q4-24 | Fake provider replaced by second conforming fake | ALL | Same schema, refusals, trace semantics and golden outcomes | Change domain contract or truth labels |

### Fixture families

- Valid: Q4-01–Q4-05.
- Hallucination/number: Q4-06–Q4-08.
- Citation: Q4-09–Q4-10.
- Status/layer/metric/time: Q4-11–Q4-16.
- Security: Q4-17–Q4-18.
- Transport/fallback/budget: Q4-19–Q4-23.
- Replacement: Q4-24.

---

## 5. DEFINITION OF DONE FOR RUNG 2

1. All 60 requirements implemented or explicitly blocked as F3/F4.
2. 72 uniquely named tests collected and passing with zero network calls.
3. 24 Q4 fixtures deterministic and reproducible.
4. No modifications to frozen upstream contracts or hashes.
5. No route/migration change.
6. No credential or real provider call.
7. Both CI jobs green at the final head.
8. Fake-provider green is reported as contract evidence only.
9. IV.5 handoff consumes `GatewayDraft` without trusting it.
10. IV.6 can re-run every Q4 scenario unchanged.

---

## 6. EXPLICIT NON-ACCEPTANCE

The following do **not** satisfy IV.4:

- a prompt-only implementation with no typed draft;
- free-form LLM prose with citations added afterward;
- a validator hidden inside the provider adapter;
- a model name that encodes depth/authority;
- silently retrying a different model;
- fallback that re-retrieves or widens context;
- cost tracking that ignores retries;
- fake-only tests presented as OpenRouter production proof;
- an LLM call from planning, CI, or fixture generation.
