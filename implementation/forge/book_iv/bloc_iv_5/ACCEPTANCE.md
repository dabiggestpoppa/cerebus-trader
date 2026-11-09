# BOOK IV / BLOC IV.5 — ACCEPTANCE
## BA-30 RUNG 1

**Contract:** `ASK_ANSWER_CONTRACT_V1` (proposed)
**Base HEAD:** `b6018bb1c3923093981ffb4646a7798abf45b922`
**Proposed test file:** `tests/test_forge_ask_cerebus_answer.py`
**Requirement count:** **76** (`R1`–`R76`)
**Proposed test count:** **86** (`A-01`–`A-86`)
**Golden scenario count:** **46** (`Q5-01`–`Q5-46`)
**Mode:** planning only; no test or implementation exists yet.

---

## 1. ACCEPTANCE LAW

IV.5 is accepted only when all of the following hold:

1. The compiler consumes exactly one `GatewayDraft(status=UNVALIDATED)` with
   its originating package and manifest.
2. Draft/package/manifest identity is re-verified and the manifest digest is
   recomputed.
3. Every material claim resolves to package-local evidence and user-facing
   provenance.
4. Every number equals an authorized value; no invented, altered, rescaled or
   substituted number passes.
5. Metric and evidence-class conversions are blocked.
6. Layer authority is preserved; no layer lends authority to another.
7. Actionable language requires an eligible encoded setup.
8. Status, generation and freshness cannot be upgraded or hidden.
9. Internal material, corpus dumps and enumeration are vetoed.
10. Exactly one of six refusal codes is emitted when the answer cannot be
    supported, with deterministic precedence.
11. Every outcome produces a safe, deterministic `FinalResponseRecord`.
12. No network, model, provider or retrieval call occurs inside IV.5.

A green deterministic run is **not** production acceptance.

---

## 2. REQUIREMENT INVENTORY

### T1 — Input admission and answer authority (R1–R6)

| ID | Requirement | Class |
|---|---|---|
| R1 | Consume exactly one `GatewayDraft(status=UNVALIDATED)` with its originating `AuthorizedContextPackage` and `AuthorizedContextManifest`; admit no other input. | F1 |
| R2 | Refuse `DRAFT_NOT_UNVALIDATED` for any status other than `UNVALIDATED`, and `ANSWER_IDENTITY_MISMATCH` when package/manifest/query identity disagrees with the draft. | F1 |
| R3 | Re-verify `CONTEXT_CONTRACT_V1`, manifest presence and `manifest_digest`; refuse `ANSWER_CONTEXT_REFUSED` or `ANSWER_MANIFEST_INVALID`. | F1 |
| R4 | Re-resolve every draft reference inside the same package; never re-retrieve, re-plan, regenerate or call a model. | F1 |
| R5 | Repair presentation only: section assembly, ordering and wording may change; no fact, number, status, layer, eligibility, entitlement or metric may be added or altered. | F2 |
| R6 | Emit exactly one terminal outcome — `ValidatedAnswer` xor `GovernedAnswerRefusal`; no partial success and no "probably correct". | F2 |

### T2 — Beginner compiler (R7–R11)

| ID | Requirement | Class |
|---|---|---|
| R7 | Produce `WHAT IT MEANS` from cited package meaning. | F2 |
| R8 | Produce `WHAT CEREBUS SEES`, distinguishing encoded model context from live data. | F2 |
| R9 | Produce `WHAT IT DOES NOT MEAN`, including every upstream limitation, no-go, unresolved marker and non-prediction caveat. | F2 |
| R10 | Produce `NEXT RELEVANT STATE/LEVEL`, or an explicit not-encoded statement. | F2 |
| R11 | Headings may be compressed for UX, but all four beginner semantics must remain identifiable and stable in the record; depth comes from the draft, never from prose inference. | F2 |

### T3 — Operator compiler (R12–R17)

| ID | Requirement | Class |
|---|---|---|
| R12 | Render `MODEL/LAYER` and `CURRENT STATE` only from cited canonical facts, with unresolved states explicit. | F2 |
| R13 | Reproduce the four-valued `ELIGIBILITY` verdict with `BLOCKED > UNRESOLVED > WATCH > ELIGIBLE` precedence. | F1 |
| R14 | Render `ACTIVE RANGE/ANCHOR`, `CLOCK`, `PATH/RANGE LEFT` and `LEVELS` with explicit `UNRESOLVED`, never a default or zero. | F2 |
| R15 | Render `TRIGGER`, `INVALIDATION` and `TARGETS` only where the package encodes them. | F2 |
| R16 | Preserve `NO-GO` in meaning; it cannot be dropped or softened by cost, latency or formatting. | F1 |
| R17 | Attach `EVIDENCE STATUS` with the governing epistemic label to each operator field group. | F2 |

### T4 — Researcher compiler (R18–R23)

| ID | Requirement | Class |
|---|---|---|
| R18 | Expose model/version and implementation identity from the package. | F1 |
| R19 | Expose claim ID and event identity. | F1 |
| R20 | Expose conditioning population, N and small-N flag, including `N_NOT_PROVIDED` and `SMALL_N_UNRESOLVED`. | F1 |
| R21 | Expose period and source generation. | F1 |
| R22 | Expose metric/result without substitution, plus OOS/reproduction status. | F2 |
| R23 | Surface contradictions and negative evidence present in the package; a researcher answer may not omit a conflict. | F2 |

### T5 — Citation and provenance renderer (R24–R29)

| ID | Requirement | Class |
|---|---|---|
| R24 | Require at least one resolvable citation for every material claim; a missing citation refuses `CITATION_REQUIRED`. | F2 |
| R25 | Resolve every citation to a package item/evidence/source ref; an unresolvable citation refuses the whole answer with `CITATION_UNRESOLVED`. | F1 |
| R26 | Render a user-facing provenance reference, never an internal row, table, SQL fragment, endpoint or hidden object ID (`LEAKAGE_INTERNAL_MATERIAL`). | F3 |
| R27 | Order and de-duplicate citations deterministically without losing distinct evidence paths. | F2 |
| R28 | Require a numeric claim's citation to resolve to the same source as its `NumericLink` (`CITATION_NUMERIC_MISMATCH`). | F2 |
| R29 | Never introduce a fabricated citation to satisfy coverage; a coverage shortfall is a refusal. | F2 |

### T6 — Numerical validator (R30–R36)

| ID | Requirement | Class |
|---|---|---|
| R30 | Accept a number only when it equals an authorized `value_text` under explicit normalization; no value-changing rounding. | F2 |
| R31 | Reject an invented number with `NUMERIC_EVIDENCE_MISSING`. | F1 |
| R32 | Reject an altered or value-changing rounded number with `NUMERIC_MISMATCH`. | F2 |
| R33 | Reject an absent unit/scale change with `NUMERIC_UNIT_MISMATCH`. | F2 |
| R34 | Reject correlation→probability, target-completion→win-rate, basket-confirmation→win-rate and simulation→empirical conversions with `METRIC_SUBSTITUTION` or `EVIDENCE_CLASS_LAUNDERING`. | F2 |
| R35 | Reject a statistic claim that omits required N/status with `STATISTIC_INCOMPLETE`. | F1 |
| R36 | Require every numeric claim to appear in the draft `numbers` set with an admissible link (`NUMERIC_EVIDENCE_MISSING`). | F1 |

### T7 — Layer validator (R37–R41)

| ID | Requirement | Class |
|---|---|---|
| R37 | Reject an L3 destination used as a direct L1 entry with `LAYER_LAUNDERING`. | F2 |
| R38 | Reject an L2 path statistic presented as setup win rate with `LAYER_LAUNDERING`. | F2 |
| R39 | Reject an L1 trigger overriding a higher-layer no-go without an encoded rule with `LAYER_AUTHORITY_VIOLATION`. | F3 |
| R40 | Require a claim's layer to equal its source item's layer and attribute each claim in a mixed-layer answer to its own layer. | F1 |
| R41 | Accept only frozen layer vocabulary; reject cross-layer inference presented as canonical. | F1 |

### T8 — Setup and action validator (R42–R47)

| ID | Requirement | Class |
|---|---|---|
| R42 | Require an `ELIGIBLE` encoded setup for actionable language; `WATCH` permits observation only; `UNRESOLVED`/`BLOCKED` forbid action. | F1 |
| R43 | Emit the fixed `SETUP_NOT_ENCODED` sentence when no setup is encoded; never invent one. | F1 |
| R44 | Enforce `BLOCKED > UNRESOLVED > WATCH > ELIGIBLE` when multiple setup verdicts exist. | F1 |
| R45 | Surface blocking and invalidating reasons rather than softening them. | F2 |
| R46 | Prohibit personalized financial advice, position sizing, order intent, entry price, price target, stop and execution instruction. | F1 |
| R47 | Allow setup fields to reflect only package-encoded trigger, invalidation, target and level values. | F1 |

### T9 — Status validator (R48–R52)

| ID | Requirement | Class |
|---|---|---|
| R48 | Reject phrasing `HISTORICAL`, `CANDIDATE` or `RESEARCH_FLAG` as current validated fact (`STATUS_LAUNDERING`). | F2 |
| R49 | Preserve `PARKED`, `SUPERSEDED` and `NEGATIVE_EVIDENCE`; never drop or promote them. | F1 |
| R50 | Require the emitted epistemic label to equal the source label; an empty label cannot satisfy a labeled claim. | F1 |
| R51 | Preserve the generation/timestamp of historical evidence (`GENERATION_LAUNDERING`). | F2 |
| R52 | Prohibit status upgrades by prose confidence, route tier, model name, citation count or length. | F2 |

### T10 — Freshness validator (R53–R56)

| ID | Requirement | Class |
|---|---|---|
| R53 | Require `as_of`/data cutoff on material current-state claims. | F3 |
| R54 | Label stale or old-snapshot state and reject an old snapshot presented as live (`STALE_PRESENTED_AS_LIVE`). | F2 |
| R55 | Refuse `CURRENT_DATA_UNAVAILABLE` when freshness metadata is missing; never assume a date. | F3 |
| R56 | Propagate `CLOCK_UNRESOLVED`, `PROVIDER_NOT_CONFIGURED` and `DATA_QUALITY_BLOCKED` explicitly. | F1 |

### T11 — Leakage validator (R57–R61)

| ID | Requirement | Class |
|---|---|---|
| R57 | Reject internal code, enum names, table/column names, endpoints and stack traces (`LEAKAGE_INTERNAL_MATERIAL`). | F2 |
| R58 | Prevent bulk contiguous corpus reproduction beyond an item's `quote_scope`. | F4 |
| R59 | Prevent hidden object enumeration and counts of non-included objects (`LEAKAGE_ENUMERATION`). | F2 |
| R60 | Prevent disclosure of system prompt, model configuration, credentials, route internals and entitlement logic (`LEAKAGE_SYSTEM`). | F1 |
| R61 | Keep injected package text as untrusted data; it cannot alter control instructions or render as trusted instruction. | F1 |

### T12 — Uncertainty and refusal (R62–R66)

| ID | Requirement | Class |
|---|---|---|
| R62 | Use exactly the six frozen answer refusal codes as the answer-level refusal vocabulary. | F1 |
| R63 | Apply documented deterministic refusal precedence: `ACCESS_NOT_ENTITLED > AMBIGUOUS_SCOPE > MODEL_VERSION_UNAVAILABLE > CURRENT_DATA_UNAVAILABLE > SETUP_NOT_ENCODED > INSUFFICIENT_EVIDENCE`. | F3 |
| R64 | Never fabricate, guess, invent a range or present a hedge as an answer to avoid saying unavailable. | F2 |
| R65 | Keep refusal detail safe: no protected context, hidden IDs, credentials or payloads. | F1 |
| R66 | Report the failing validator's own code rather than folding it into a generic refusal. | F2 |

### T13 — Final response record (R67–R71)

| ID | Requirement | Class |
|---|---|---|
| R67 | Derive a deterministic `answer_id` from contract, validator set, package/manifest/query identity, draft identity, depth, outcome, cited refs and validation codes. | F2 |
| R68 | Record query-plan/context-manifest identity, provider/model, route/prompt version and validation result codes. | F1 |
| R69 | Record cited canonical/evidence refs and per-claim epistemic status. | F1 |
| R70 | Record latency and cost without prompts, secrets or account identifiers. | F1 |
| R71 | Persist safe metadata only by default; full protected prose requires an approved retention policy. | F4 |

### T14 — Cross-cutting invariance (R72–R76)

| ID | Requirement | Class |
|---|---|---|
| R72 | Perform no network, model, provider or retrieval call inside IV.5. | F1 |
| R73 | Produce byte-identical answer/refusal payloads for identical draft, package, manifest and clock. | F2 |
| R74 | Leave frozen upstream contract hashes, routes and migrations unchanged. | F1 |
| R75 | Keep answer, refusal and record payloads free of secrets, credentials, headers and protected context. | F1 |
| R76 | Prevent configuration from disabling, reordering or bypassing validators to produce a validated answer; fake-green is contract evidence only. | F2 |

**Counts:** F1=34, F2=35, F3=5, F4=2; total 76.

---

## 3. EXACT PROPOSED TEST NAMES

### 3.1 Base drivers A-01–A-76

| Test | Exact name | Req |
|---|---|---|
| A-01 | `test_a01_consumes_unvalidated_gateway_draft_with_originating_package` | R1 |
| A-02 | `test_a02_refuses_non_unvalidated_draft_or_identity_mismatch` | R2 |
| A-03 | `test_a03_reverifies_context_contract_and_manifest_digest` | R3 |
| A-04 | `test_a04_reresolves_references_without_retrieval_or_model_call` | R4 |
| A-05 | `test_a05_repair_is_presentation_only` | R5 |
| A-06 | `test_a06_emits_exactly_one_terminal_outcome` | R6 |
| A-07 | `test_a07_beginner_compiles_what_it_means` | R7 |
| A-08 | `test_a08_beginner_compiles_what_cerebus_sees` | R8 |
| A-09 | `test_a09_beginner_compiles_what_it_does_not_mean` | R9 |
| A-10 | `test_a10_beginner_compiles_next_relevant_state_or_level` | R10 |
| A-11 | `test_a11_beginner_headings_may_compress_but_semantics_remain` | R11 |
| A-12 | `test_a12_operator_renders_model_layer_and_current_state` | R12 |
| A-13 | `test_a13_operator_eligibility_uses_four_valued_precedence` | R13 |
| A-14 | `test_a14_operator_range_anchor_clock_and_path_left_are_explicit` | R14 |
| A-15 | `test_a15_operator_trigger_invalidation_and_targets_come_from_package` | R15 |
| A-16 | `test_a16_operator_no_go_is_preserved` | R16 |
| A-17 | `test_a17_operator_evidence_status_is_attached` | R17 |
| A-18 | `test_a18_researcher_exposes_model_version_and_implementation_identity` | R18 |
| A-19 | `test_a19_researcher_exposes_claim_and_event_identity` | R19 |
| A-20 | `test_a20_researcher_exposes_population_n_and_small_n` | R20 |
| A-21 | `test_a21_researcher_exposes_period_and_source_generation` | R21 |
| A-22 | `test_a22_researcher_exposes_metric_oos_and_reproduction` | R22 |
| A-23 | `test_a23_researcher_surfaces_contradictions_and_negative_evidence` | R23 |
| A-24 | `test_a24_every_material_claim_has_a_resolvable_citation` | R24 |
| A-25 | `test_a25_unresolvable_citation_refuses_the_whole_answer` | R25 |
| A-26 | `test_a26_rendered_citations_use_user_facing_provenance` | R26 |
| A-27 | `test_a27_citation_order_and_identity_are_deterministic` | R27 |
| A-28 | `test_a28_numeric_claim_citation_matches_numeric_link_source` | R28 |
| A-29 | `test_a29_no_fabricated_citation_satisfies_coverage` | R29 |
| A-30 | `test_a30_numbers_must_equal_authorized_value_text` | R30 |
| A-31 | `test_a31_invented_number_refuses` | R31 |
| A-32 | `test_a32_altered_or_rounded_number_refuses` | R32 |
| A-33 | `test_a33_unit_or_scale_change_refuses` | R33 |
| A-34 | `test_a34_metric_and_evidence_class_substitution_refuses` | R34 |
| A-35 | `test_a35_statistic_claim_requires_n_and_status` | R35 |
| A-36 | `test_a36_numeric_claim_requires_admissible_numeric_link` | R36 |
| A-37 | `test_a37_l3_destination_cannot_be_direct_l1_entry` | R37 |
| A-38 | `test_a38_l2_path_statistic_cannot_be_setup_win_rate` | R38 |
| A-39 | `test_a39_l1_trigger_cannot_override_higher_layer_no_go` | R39 |
| A-40 | `test_a40_claim_layer_matches_source_and_attribution` | R40 |
| A-41 | `test_a41_layer_labels_use_frozen_vocabulary` | R41 |
| A-42 | `test_a42_action_language_requires_eligible_setup` | R42 |
| A-43 | `test_a43_missing_setup_emits_setup_not_encoded_sentence` | R43 |
| A-44 | `test_a44_setup_precedence_is_blocked_unresolved_watch_eligible` | R44 |
| A-45 | `test_a45_blocking_and_invalidating_reasons_are_surfaced` | R45 |
| A-46 | `test_a46_no_personalized_financial_advice_or_execution_instruction` | R46 |
| A-47 | `test_a47_setup_fields_reflect_only_encoded_values` | R47 |
| A-48 | `test_a48_historical_candidate_and_research_flag_cannot_read_as_current` | R48 |
| A-49 | `test_a49_parked_superseded_and_negative_evidence_are_preserved` | R49 |
| A-50 | `test_a50_epistemic_label_must_equal_source_label` | R50 |
| A-51 | `test_a51_generation_and_timestamp_are_preserved` | R51 |
| A-52 | `test_a52_status_cannot_be_upgraded_by_prose_confidence_or_citations` | R52 |
| A-53 | `test_a53_current_state_exposes_as_of_or_data_cutoff` | R53 |
| A-54 | `test_a54_stale_snapshot_cannot_be_presented_as_live` | R54 |
| A-55 | `test_a55_missing_freshness_metadata_refuses_current_data_unavailable` | R55 |
| A-56 | `test_a56_clock_unresolved_propagates` | R56 |
| A-57 | `test_a57_internal_codes_tables_endpoints_and_traces_are_not_rendered` | R57 |
| A-58 | `test_a58_bulk_contiguous_corpus_reproduction_is_blocked` | R58 |
| A-59 | `test_a59_hidden_object_enumeration_is_blocked` | R59 |
| A-60 | `test_a60_system_prompt_credentials_and_config_are_not_disclosed` | R60 |
| A-61 | `test_a61_injected_package_text_remains_untrusted_data` | R61 |
| A-62 | `test_a62_six_frozen_answer_refusal_codes_are_exhaustive` | R62 |
| A-63 | `test_a63_refusal_precedence_is_deterministic` | R63 |
| A-64 | `test_a64_refusal_never_fabricates_or_hedges_into_an_answer` | R64 |
| A-65 | `test_a65_refusal_payload_is_safe_and_bounded` | R65 |
| A-66 | `test_a66_validator_failure_reports_its_own_code` | R66 |
| A-67 | `test_a67_answer_id_is_deterministic` | R67 |
| A-68 | `test_a68_record_carries_identity_model_and_validation_codes` | R68 |
| A-69 | `test_a69_record_carries_citations_and_epistemic_status` | R69 |
| A-70 | `test_a70_record_carries_latency_and_cost_without_secrets` | R70 |
| A-71 | `test_a71_prose_persistence_requires_retention_policy` | R71 |
| A-72 | `test_a72_no_network_model_or_retrieval_call_inside_answer_layer` | R72 |
| A-73 | `test_a73_answer_layer_is_byte_deterministic` | R73 |
| A-74 | `test_a74_frozen_upstream_hashes_routes_and_migrations_unchanged` | R74 |
| A-75 | `test_a75_answer_and_record_payloads_contain_no_secrets` | R75 |
| A-76 | `test_a76_validators_cannot_be_disabled_or_bypassed` | R76 |

### 3.2 Cross-cutting drivers A-77–A-86

| Test | Exact name | Reqs |
|---|---|---|
| A-77 | `test_a77_numerical_validator_runs_before_rendering` | R30, R36 |
| A-78 | `test_a78_status_and_layer_validators_run_before_citation_rendering` | R37, R48 |
| A-79 | `test_a79_setup_and_freshness_gate_actionable_claims` | R42, R53 |
| A-80 | `test_a80_leakage_validator_runs_last_and_can_veto` | R57, R60 |
| A-81 | `test_a81_beginner_operator_researcher_share_one_validation_core` | R11, R12, R18 |
| A-82 | `test_a82_refusal_outranks_partial_answer` | R6, R64 |
| A-83 | `test_a83_same_draft_and_package_reproduce_identical_outcome` | R73, R67 |
| A-84 | `test_a84_changed_package_manifest_identity_refuses` | R2, R3 |
| A-85 | `test_a85_no_answer_path_omits_the_response_record` | R68, R69 |
| A-86 | `test_a86_fake_green_is_contract_evidence_only` | R76, R72 |

All 86 names are unique. Base tests A-01–A-76 map one-to-one to R1–R76;
A-77–A-86 are additional cross-cutting acceptance drivers.

---

## 4. FORTY-SIX GOLDEN SCENARIOS

The Q5 harness is planning-visible and uses only deterministic IV.3/IV.4
fixtures. "Draft" means `GatewayDraft(status=UNVALIDATED)`. "Refusal" means
`GovernedAnswerRefusal` with exactly one of the six frozen codes.

### 4.1 Valid controls (Q5-01–Q5-06)

| ID | Scenario | Depth | Required outcome | Must not |
|---|---|---|---|---|
| Q5-01 | Canonical definition with a resolved package and full citation path | BEGINNER | `ValidatedAnswer`; four beginner semantics present | Add an unsupported fact |
| Q5-02 | General market-knowledge question with no CEREBUS claim | BEGINNER | Answer marked general; no CEREBUS citation invented | Claim CEREBUS evidence |
| Q5-03 | Full operator field set with an `ELIGIBLE` encoded setup | OPERATOR | All applicable fields cited; `NO-GO` and `EVIDENCE STATUS` present | Omit `NO-GO` |
| Q5-04 | Operator `WATCH` setup | OPERATOR | Observation language only; eligibility reproduced | Use entry language |
| Q5-05 | Researcher statistic with N, OOS and generation | RESEARCHER | Population/N/period/OOS/generation all rendered | Present candidate as validated |
| Q5-06 | Researcher answer containing contradiction and negative evidence | RESEARCHER | Both surfaced with labels | Suppress the conflict |

### 4.2 Numerical (Q5-07–Q5-14)

| ID | Scenario | Depth | Required outcome | Must not |
|---|---|---|---|---|
| Q5-07 | Draft invents a numeric value | OPERATOR | Refusal `INSUFFICIENT_EVIDENCE` with `NUMERIC_EVIDENCE_MISSING` recorded | Accept the number |
| Q5-08 | Draft alters/rounds a retrieved number | RESEARCHER | Refusal recording `NUMERIC_MISMATCH` | Silently re-round |
| Q5-09 | Draft changes bps to percent | OPERATOR | Refusal recording `NUMERIC_UNIT_MISMATCH` | Normalize the scale |
| Q5-10 | Correlation presented as probability | RESEARCHER | Refusal recording `METRIC_SUBSTITUTION` | Conflate metrics |
| Q5-11 | Target completion presented as win rate | OPERATOR | Refusal recording `METRIC_SUBSTITUTION` | Conflate metrics |
| Q5-12 | Basket confirmation presented as win rate | RESEARCHER | Refusal recording `METRIC_SUBSTITUTION` | Conflate metrics |
| Q5-13 | Simulation presented as empirical result | RESEARCHER | Refusal recording `EVIDENCE_CLASS_LAUNDERING` | Drop the simulation caveat |
| Q5-14 | Statistic claim omits required N | RESEARCHER | Refusal recording `STATISTIC_INCOMPLETE` | Render a default N |

### 4.3 Citation (Q5-15–Q5-19)

| ID | Scenario | Depth | Required outcome | Must not |
|---|---|---|---|---|
| Q5-15 | Material claim carries no citation | OPERATOR | Refusal `INSUFFICIENT_EVIDENCE` with `CITATION_REQUIRED` | Emit uncited claim |
| Q5-16 | Citation points to a foreign/unauthorized item | RESEARCHER | Refusal recording `CITATION_UNRESOLVED` | Render foreign content |
| Q5-17 | Citation is an internal object ID | OPERATOR | Refusal recording `LEAKAGE_INTERNAL_MATERIAL` | Render the internal ID |
| Q5-18 | Numeric claim's citation differs from its numeric link source | RESEARCHER | Refusal recording `CITATION_NUMERIC_MISMATCH` | Swap the source |
| Q5-19 | Draft fabricates a citation to satisfy coverage | OPERATOR | Refusal recording `CITATION_UNRESOLVED` | Accept invented provenance |

### 4.4 Layer (Q5-20–Q5-23)

| ID | Scenario | Depth | Required outcome | Must not |
|---|---|---|---|---|
| Q5-20 | L3 destination used as a direct L1 entry | BEGINNER | Refusal recording `LAYER_LAUNDERING` | Rewrite L1 from L3 |
| Q5-21 | L2 path statistic presented as setup win rate | OPERATOR | Refusal recording `LAYER_LAUNDERING` | Treat path stat as setup WR |
| Q5-22 | L1 trigger overrides a higher-layer no-go | OPERATOR | Refusal recording `LAYER_AUTHORITY_VIOLATION` | Override without a rule |
| Q5-23 | Mixed-layer answer attributes a claim to the wrong layer | RESEARCHER | Refusal recording `LAYER_LAUNDERING` | Flatten layers |

### 4.5 Setup and action (Q5-24–Q5-29)

| ID | Scenario | Depth | Required outcome | Must not |
|---|---|---|---|---|
| Q5-24 | Action requested, no setup encoded | OPERATOR | Refusal `SETUP_NOT_ENCODED` with the fixed sentence | Invent a setup |
| Q5-25 | `BLOCKED` setup asked to be actionable | OPERATOR | Refusal `SETUP_NOT_ENCODED`; blocking reason surfaced | Soften the block |
| Q5-26 | `UNRESOLVED` setup with observation language | OPERATOR | Observation only, or refusal; unresolved reason shown | Treat as `WATCH` |
| Q5-27 | Request for position size and entry price | OPERATOR | Refusal; no advice or sizing | Provide sizing |
| Q5-28 | Conflicting verdicts `WATCH` and `BLOCKED` | OPERATOR | `BLOCKED` prevails; action refused | Pick the milder verdict |
| Q5-29 | Setup fields disagree with encoded trigger/target values | OPERATOR | Refusal recording `SETUP_FIELD_MISMATCH` | Render invented levels |

### 4.6 Status and generation (Q5-30–Q5-33)

| ID | Scenario | Depth | Required outcome | Must not |
|---|---|---|---|---|
| Q5-30 | `CANDIDATE` phrased as validated | RESEARCHER | Refusal recording `STATUS_LAUNDERING` | Promote status |
| Q5-31 | `HISTORICAL` presented as current | BEGINNER | Refusal recording `STATUS_LAUNDERING` | Drop generation |
| Q5-32 | `RESEARCH_FLAG` presented as production | OPERATOR | Refusal recording `STATUS_LAUNDERING` | Promote to production |
| Q5-33 | `PARKED`/`SUPERSEDED`/`NEGATIVE_EVIDENCE` dropped | RESEARCHER | Refusal recording `STATUS_LAUNDERING` | Omit the label |

### 4.7 Freshness (Q5-34–Q5-36)

| ID | Scenario | Depth | Required outcome | Must not |
|---|---|---|---|---|
| Q5-34 | Stale snapshot presented as live | OPERATOR | Refusal `CURRENT_DATA_UNAVAILABLE` recording `STALE_PRESENTED_AS_LIVE` | Present as live |
| Q5-35 | Current-state answer with no freshness metadata | BEGINNER | Refusal `CURRENT_DATA_UNAVAILABLE` | Assume a date |
| Q5-36 | Clock unresolved in the package | OPERATOR | `CLOCK_UNRESOLVED` propagated into the answer or refusal | Substitute a clock |

### 4.8 Leakage (Q5-37–Q5-39)

| ID | Scenario | Depth | Required outcome | Must not |
|---|---|---|---|---|
| Q5-37 | Draft includes internal enum/table/endpoint names | RESEARCHER | Refusal recording `LEAKAGE_INTERNAL_MATERIAL` | Render internals |
| Q5-38 | Draft reproduces bulk contiguous corpus text | RESEARCHER | Refusal recording `LEAKAGE_CORPUS` | Render the dump |
| Q5-39 | Draft enumerates hidden objects and leaks system/config text | OPERATOR | Refusal recording `LEAKAGE_ENUMERATION` and `LEAKAGE_SYSTEM` | Disclose either |

### 4.9 Refusal vocabulary (Q5-40–Q5-44)

| ID | Scenario | Depth | Required outcome | Must not |
|---|---|---|---|---|
| Q5-40 | Package supports no claim for the question | BEGINNER | Refusal `INSUFFICIENT_EVIDENCE` | Guess |
| Q5-41 | Package encodes a stale/unavailable current state | OPERATOR | Refusal `CURRENT_DATA_UNAVAILABLE` | Invent a current read |
| Q5-42 | Requested model/version absent from the package | RESEARCHER | Refusal `MODEL_VERSION_UNAVAILABLE` | Substitute another model |
| Q5-43 | Package encodes an access denial for the scope | OPERATOR | Refusal `ACCESS_NOT_ENTITLED` | Infer or claim access |
| Q5-44 | Query resolves to two incompatible scopes | BEGINNER | Refusal `AMBIGUOUS_SCOPE` | Pick one silently |

### 4.10 Record and determinism (Q5-45–Q5-46)

| ID | Scenario | Depth | Required outcome | Must not |
|---|---|---|---|---|
| Q5-45 | Valid answer produces a record | OPERATOR | Record carries identity, citations, per-claim labels, validation codes, latency/cost | Persist protected prose |
| Q5-46 | Same draft/package/clock replayed | ALL | Byte-identical answer or refusal and identical `answer_id` | Drift or non-determinism |

### 4.11 Fixture families

- Valid controls: Q5-01–Q5-06.
- Numerical: Q5-07–Q5-14.
- Citation: Q5-15–Q5-19.
- Layer: Q5-20–Q5-23.
- Setup/action: Q5-24–Q5-29.
- Status/generation: Q5-30–Q5-33.
- Freshness: Q5-34–Q5-36.
- Leakage: Q5-37–Q5-39.
- Refusal vocabulary: Q5-40–Q5-44.
- Record/determinism: Q5-45–Q5-46.

---

## 5. DEFINITION OF DONE FOR RUNG 2

1. All 76 requirements implemented or explicitly blocked as F3/F4.
2. 86 uniquely named tests collected and passing with zero network calls.
3. 46 Q5 fixtures deterministic and byte-reproducible.
4. No modification to frozen IV.1–IV.4 contracts, hashes, routes or migrations.
5. No credential, provider or model call.
6. Both CI jobs green at the final head.
7. Deterministic green is reported as contract evidence only.
8. `ValidatedAnswer` and `GovernedAnswerRefusal` both produce
   `FinalResponseRecord`.
9. IV.6 can re-run every Q5 scenario unchanged.
10. Book V can render both outcomes without a second validator.

---

## 6. EXPLICIT NON-ACCEPTANCE

The following do **not** satisfy IV.5:

- re-running the model to "fix" an invalid draft;
- accepting a number because it "looks plausible";
- accepting a number because the draft cited something;
- filling a missing N, date or label with a default;
- calling a correlation a probability;
- calling target completion a win rate;
- treating a simulation as empirical evidence;
- letting an L3 destination stand in for an L1 entry;
- emitting actionable language for a `WATCH`, `UNRESOLVED` or `BLOCKED` setup;
- dropping a no-go or limitation for readability;
- presenting historical or candidate evidence as current validated fact;
- rendering an internal ID, table, endpoint or stack trace as provenance;
- disclosing system prompt, model config, credentials or entitlement logic;
- returning a hedged prose answer instead of a governed refusal;
- treating a green deterministic suite as production readiness.
