# BOOK IV / BLOC IV.3 — ACCEPTANCE
## CONTEXT PACKAGER — BA-28 RUNG 1

**Base HEAD:** `23b2b9e19f1b1dee59c4aa9379a35a1dfed981b7`
**Contract:** `CONTEXT_CONTRACT_V1` (proposed)
**Test file:** `tests/test_forge_ask_cerebus_context.py`
**Requirement count:** 92 (`R1`–`R92`)
**Test count:** 92 (`C-01`–`C-92`)
**Fixture count:** 20 (`Q3-01`–`Q3-20`)

This document binds IV.3 implementation. A test may not be skipped, xfailed,
renamed, merged or weakened. Each requirement has exactly one base driver.
T11/T12 add failure and frozen-integrity checks without changing R1–R92.

---

## 1. REQUIREMENT INVENTORY

### T1 — Context sections (R1–R9)

| ID | Requirement |
|---|---|
| R1 | Package only the nine applicable sections; absent sections are explicit, never fabricated. |
| R2 | Preserve the IV.1 query contract without reinterpretation; require matching `plan_id`. |
| R3 | Package typed current-intelligence references, quality, no-go and refusal without inventing values. |
| R4 | Package canonical model references without canonical body text. |
| R5 | Preserve setup identity, version, class, surface and eligibility verbatim. |
| R6 | Pair every included claim with its authorized evidence references. |
| R7 | Keep lineage and terms separate from current doctrine and current claims. |
| R8 | Retain limitations, refusals and negative evidence in their mandatory section. |
| R9 | Treat general knowledge as a bounded allowance only; never place CEREBUS facts, IDs or numbers in it. |

### T2 — Canonical compression (R10–R16)

| ID | Requirement |
|---|---|
| R10 | Prefer canonical references and allowlisted facts over source passages. |
| R11 | Include a semantic excerpt only when its object is authorized, bounded and scope-permitted. |
| R12 | Omit raw source when a canonical item already supplies the fact. |
| R13 | Preserve quote scope and exposure on every excerpt. |
| R14 | Order sections and items deterministically. |
| R15 | Deduplicate by source identity without merging facts across generations or layers. |
| R16 | Preserve source and provenance references through compression. |

### T3 — Token budgets (R17–R24)

| ID | Requirement |
|---|---|
| R17 | Use a versioned, reproducible estimator over canonical control facts and text. |
| R18 | Expose a replaceable tokenizer port; do not claim provider-specific accuracy. |
| R19 | Require explicit budget input with a documented default and safety reserve. |
| R20 | Enforce the frozen priority: current/restrictions > claim/evidence > model > setup > negative > lineage > semantic. |
| R21 | Never trim mandatory no-go, invalidation, refusal or evidence-insufficiency items. |
| R22 | Trim optional items deterministically in reverse priority with stable ordering. |
| R23 | Record every trimmed or omitted item in a bounded omission ledger. |
| R24 | Refuse with `CONTEXT_BUDGET_EXCEEDED` when the mandatory floor exceeds the budget. |

### T4 — Epistemic labels (R25–R33)

| ID | Requirement |
|---|---|
| R25 | Emit only the frozen epistemic label vocabulary. |
| R26 | Preserve the upstream source status verbatim alongside the label. |
| R27 | Map source status to epistemic label without promotion or invention. |
| R28 | Distinguish canonical source identity from numerical validation. |
| R29 | Never promote a label through packaging, compression or deduplication. |
| R30 | Keep parked, superseded, falsified and no-go evidence negative. |
| R31 | Do not emit `INFERENCE`; it is reserved for a later authorized layer. |
| R32 | Never place a CEREBUS fact under `GENERAL_KNOWLEDGE`. |
| R33 | Fail closed with no number when a source status cannot be mapped safely. |

### T5 — Layer ownership (R34–R40)

| ID | Requirement |
|---|---|
| R34 | Preserve the exact source layer on every item. |
| R35 | Prevent an L3 statistic from filling an L1 setup-performance field. |
| R36 | Prevent an L2 path fact from becoming entry authority. |
| R37 | Prevent a historical fact from being packaged as current. |
| R38 | Prevent JPY manual confirmation from becoming execution permission. |
| R39 | Prevent Fib research-only state from becoming a production setup. |
| R40 | Keep cross-layer facts separate; compute no confluence score. |

### T6 — Small-N and evidence integrity (R41–R49)

| ID | Requirement |
|---|---|
| R41 | Preserve metric, event, population, sample size and period when governed projections supply them. |
| R42 | Never invent or infer a sample size. |
| R43 | Never invent a small-N threshold. |
| R44 | Mark small-N unresolved when no governed threshold exists while retaining actual N. |
| R45 | Preserve evidence status and provenance references. |
| R46 | Preserve OOS/reproduction state when available. |
| R47 | Preserve model and generation identity on every claim. |
| R48 | Retain both sides of conflicting evidence with original statuses. |
| R49 | Omit a numerical result when evidence is absent, unsupported or epistemically inadmissible. |

### T7 — No-evidence path (R50–R55)

| ID | Requirement |
|---|---|
| R50 | Emit an explicit `MISSING_EVIDENCE` control instruction for a requested unsupported number. |
| R51 | Retain known model context when evidence is missing. |
| R52 | Never fill missing evidence from model intuition. |
| R53 | Never fill missing evidence from semantic passage text. |
| R54 | Never fill missing evidence from historical data. |
| R55 | Return `PARTIAL`, not verified, when evidence is missing. |

### T8 — Injection resistance (R56–R63)

| ID | Requirement |
|---|---|
| R56 | Type every retrieved passage as `UNTRUSTED_DATA`. |
| R57 | Separate trusted control metadata from untrusted data blocks. |
| R58 | Prevent source text from overriding instructions. |
| R59 | Prevent source text from granting entitlement or widening exposure. |
| R60 | Prevent source text from changing status, label or layer. |
| R61 | Prevent source text from inserting an identity or statistic. |
| R62 | Prevent source text from promoting a setup or clearing no-go. |
| R63 | Preserve instruction-like text only as hashed data; never execute it. |

### T9 — Exposure minimization (R64–R71)

| ID | Requirement |
|---|---|
| R64 | Exclude `INTERNAL_METHOD` and `INTERNAL_CODE` unconditionally. |
| R65 | Exclude denied identifiers from the package, manifest and omissions. |
| R66 | Never widen exposure beyond the authorized source. |
| R67 | Admit only allowlisted item and fact fields. |
| R68 | Bound every excerpt to 1,000 characters and 64 items per section. |
| R69 | Exclude secrets, source code and unrestricted corpus bodies. |
| R70 | Keep forbidden names and IDs out of the consumer manifest. |
| R71 | Bound omission metadata by section and reason code, not hidden identity. |

### T10 — Context manifest (R72–R79)

| ID | Requirement |
|---|---|
| R72 | Bind the manifest to the exact query-plan ID and retrieval bundle ID. |
| R73 | Bind the manifest to the context contract and manifest version. |
| R74 | List included section IDs and authorized object IDs. |
| R75 | List omitted section IDs explicitly. |
| R76 | Compute a deterministic package identity. |
| R77 | Compute a deterministic manifest digest. |
| R78 | Serialize canonically and reproducibly. |
| R79 | Exclude wall-clock, random, path and process values from hashes. |

### T11 — Failure and refusal behavior (R80–R86)

| ID | Requirement |
|---|---|
| R80 | Refuse an unsupported plan or bundle contract. |
| R81 | Refuse a malformed bundle or mismatched plan/bundle identity. |
| R82 | Return a bounded budget-overflow refusal. |
| R83 | Fail closed on internal or unauthorized exposure. |
| R84 | Propagate upstream refusals safely without inventing context. |
| R85 | Preserve every limitation and refusal from a partial bundle. |
| R86 | Reproduce the same package for identical inputs and retries. |

### T12 — Frozen integrity (R87–R92)

| ID | Requirement |
|---|---|
| R87 | Verify the IV.1 plan contract remains unchanged. |
| R88 | Verify IV.2 bundle, refs, trace and service contracts remain unchanged. |
| R89 | Verify Book I/II/III contracts used by IV.3 remain unchanged. |
| R90 | Import no LLM, network, vector or provider-tokenizer dependency. |
| R91 | Keep routes, migrations and the provider seam unchanged. |
| R92 | Introduce no canonical status, entitlement grant or current-market fact. |

---

## 2. EXACT TEST NAMES AND BINDINGS

| Test | Req | Exact executable name |
|---|---|---|
| C-01 | R1 | `test_c01_packages_only_applicable_sections` |
| C-02 | R2 | `test_c02_preserves_query_contract_without_reinterpretation` |
| C-03 | R3 | `test_c03_packages_typed_current_intelligence_refs` |
| C-04 | R4 | `test_c04_packages_canonical_model_without_body_text` |
| C-05 | R5 | `test_c05_preserves_setup_identity_and_surface_verbatim` |
| C-06 | R6 | `test_c06_pairs_claims_with_authorized_evidence` |
| C-07 | R7 | `test_c07_separates_lineage_and_terms` |
| C-08 | R8 | `test_c08_retains_limitations_and_negative_evidence` |
| C-09 | R9 | `test_c09_general_knowledge_is_a_bounded_allowance_only` |
| C-10 | R10 | `test_c10_prefers_canonical_refs_over_source_text` |
| C-11 | R11 | `test_c11_includes_semantic_excerpt_only_when_authorized_and_bounded` |
| C-12 | R12 | `test_c12_omits_raw_source_when_canonical_item_suffices` |
| C-13 | R13 | `test_c13_preserves_quote_scope_and_exposure_on_excerpts` |
| C-14 | R14 | `test_c14_orders_items_deterministically` |
| C-15 | R15 | `test_c15_deduplicates_identity_without_merging_facts` |
| C-16 | R16 | `test_c16_compression_preserves_source_and_provenance_refs` |
| C-17 | R17 | `test_c17_estimator_is_versioned_and_reproducible` |
| C-18 | R18 | `test_c18_tokenizer_port_is_replaceable_without_accuracy_claim` |
| C-19 | R19 | `test_c19_budget_input_is_explicit_and_defaulted` |
| C-20 | R20 | `test_c20_budget_priority_order_is_frozen` |
| C-21 | R21 | `test_c21_mandatory_safety_items_cannot_be_dropped` |
| C-22 | R22 | `test_c22_trimming_is_deterministic_and_stable` |
| C-23 | R23 | `test_c23_omission_ledger_accounts_for_truncation` |
| C-24 | R24 | `test_c24_mandatory_overflow_refuses_context` |
| C-25 | R25 | `test_c25_uses_closed_epistemic_label_set` |
| C-26 | R26 | `test_c26_preserves_source_status_separately` |
| C-27 | R27 | `test_c27_maps_status_to_epistemic_label_without_promotion` |
| C-28 | R28 | `test_c28_canonical_identity_is_not_validation` |
| C-29 | R29 | `test_c29_no_label_is_promoted_by_packaging` |
| C-30 | R30 | `test_c30_negative_statuses_remain_negative` |
| C-31 | R31 | `test_c31_inference_label_is_not_emitted` |
| C-32 | R32 | `test_c32_general_knowledge_cannot_carry_cerebus_fact` |
| C-33 | R33 | `test_c33_unmapped_status_fails_closed_without_number` |
| C-34 | R34 | `test_c34_preserves_source_layer_exactly` |
| C-35 | R35 | `test_c35_l3_statistic_cannot_fill_l1_setup_field` |
| C-36 | R36 | `test_c36_l2_path_fact_is_not_entry_authority` |
| C-37 | R37 | `test_c37_historical_fact_is_not_packaged_as_current` |
| C-38 | R38 | `test_c38_jpy_manual_state_is_not_execution_permission` |
| C-39 | R39 | `test_c39_fib_research_state_is_not_production_setup` |
| C-40 | R40 | `test_c40_cross_layer_facts_are_not_conflated` |
| C-41 | R41 | `test_c41_preserves_governed_metric_population_sample_and_period` |
| C-42 | R42 | `test_c42_never_invents_sample_size` |
| C-43 | R43 | `test_c43_never_invents_small_n_threshold` |
| C-44 | R44 | `test_c44_marks_small_n_unresolved_when_threshold_absent` |
| C-45 | R45 | `test_c45_preserves_evidence_status_and_provenance` |
| C-46 | R46 | `test_c46_preserves_oos_and_reproduction_state` |
| C-47 | R47 | `test_c47_preserves_model_generation_on_claims` |
| C-48 | R48 | `test_c48_retains_both_sides_of_conflicting_evidence` |
| C-49 | R49 | `test_c49_unsupported_claim_cannot_emit_number` |
| C-50 | R50 | `test_c50_missing_evidence_emits_explicit_instruction` |
| C-51 | R51 | `test_c51_missing_evidence_retains_known_model_context` |
| C-52 | R52 | `test_c52_missing_evidence_never_uses_model_intuition` |
| C-53 | R53 | `test_c53_missing_evidence_cannot_be_replaced_by_semantic_text` |
| C-54 | R54 | `test_c54_missing_evidence_cannot_be_replaced_by_history` |
| C-55 | R55 | `test_c55_missing_evidence_package_is_partial_not_verified` |
| C-56 | R56 | `test_c56_retrieved_text_is_typed_as_untrusted_data` |
| C-57 | R57 | `test_c57_control_and_data_blocks_are_separated` |
| C-58 | R58 | `test_c58_source_text_cannot_override_instructions` |
| C-59 | R59 | `test_c59_source_text_cannot_grant_entitlement` |
| C-60 | R60 | `test_c60_source_text_cannot_change_status_or_layer` |
| C-61 | R61 | `test_c61_source_text_cannot_insert_identity_or_statistic` |
| C-62 | R62 | `test_c62_source_text_cannot_promote_setup_or_clear_no_go` |
| C-63 | R63 | `test_c63_injection_payload_is_data_hashed_not_executed` |
| C-64 | R64 | `test_c64_internal_method_and_code_never_enter_package` |
| C-65 | R65 | `test_c65_denied_identifiers_never_enter_package_or_manifest` |
| C-66 | R66 | `test_c66_exposure_is_never_widened` |
| C-67 | R67 | `test_c67_item_fields_obey_allowlist` |
| C-68 | R68 | `test_c68_excerpt_length_is_bounded` |
| C-69 | R69 | `test_c69_secrets_and_unrestricted_bodies_are_excluded` |
| C-70 | R70 | `test_c70_consumer_manifest_contains_no_forbidden_names` |
| C-71 | R71 | `test_c71_omission_metadata_is_bounded_and_safe` |
| C-72 | R72 | `test_c72_manifest_binds_query_plan_and_bundle` |
| C-73 | R73 | `test_c73_manifest_binds_context_contract_version` |
| C-74 | R74 | `test_c74_manifest_lists_included_sections_and_object_ids` |
| C-75 | R75 | `test_c75_manifest_lists_omitted_sections` |
| C-76 | R76 | `test_c76_package_hash_is_deterministic` |
| C-77 | R77 | `test_c77_manifest_digest_is_deterministic` |
| C-78 | R78 | `test_c78_serialization_is_canonical` |
| C-79 | R79 | `test_c79_no_wall_clock_or_random_input_enters_hash` |
| C-80 | R80 | `test_c80_unsupported_input_contract_is_refused` |
| C-81 | R81 | `test_c81_malformed_bundle_is_refused` |
| C-82 | R82 | `test_c82_budget_overflow_is_a_bounded_refusal` |
| C-83 | R83 | `test_c83_exposure_violation_fails_closed` |
| C-84 | R84 | `test_c84_upstream_refusal_is_propagated_safely` |
| C-85 | R85 | `test_c85_partial_bundle_preserves_all_limitations` |
| C-86 | R86 | `test_c86_same_inputs_retry_to_same_package` |
| C-87 | R87 | `test_c87_frozen_iv1_plan_contract_unchanged` |
| C-88 | R88 | `test_c88_frozen_iv2_bundle_refs_trace_unchanged` |
| C-89 | R89 | `test_c89_frozen_book_i_ii_iii_contracts_unchanged` |
| C-90 | R90 | `test_c90_no_llm_network_vector_or_tokenizer_import` |
| C-91 | R91 | `test_c91_routes_migrations_and_provider_seam_unchanged` |
| C-92 | R92 | `test_c92_no_new_canonical_status_entitlement_or_market_fact` |

---

## 3. GOLDEN CONTEXT SCENARIOS

Fixtures live under
`implementation/forge/book_iv/bloc_iv_3/fixtures/`. They are synthetic
structural fixtures, never empirical market evidence. Expected manifest IDs
must be frozen after implementation and reproduced byte-identically.

| ID | Scenario / input | Authorized sections | Expected limitation/refusal | Forbidden | Manifest identity |
|---|---|---|---|---|---|
| Q3-01 | Rekey definition with term/lineage refs | QUERY_CONTRACT, CANONICAL_MODEL, LINEAGE_TERMS | none | Answer, setup, number | Includes term and generation; stable package ID |
| Q3-02 | Beginner Gold Game description | QUERY, CANONICAL_MODEL, CLAIMS, EVIDENCE, LIMITATIONS | `DETAIL_NOT_SUPPLIED` if stats absent | Internal method text; extra entitlement | Beginner depth does not alter IDs |
| Q3-03 | Synthetic authorized EUR snapshot | QUERY, CURRENT_INTELLIGENCE, CANONICAL_MODEL, LIMITATIONS | Synthetic marker | Empirical claim; historical substitution | Snapshot id/hash bound; stable package ID |
| Q3-04 | Current Gold unavailable | QUERY, LIMITATIONS_NEGATIVE | `PROVIDER_NOT_CONFIGURED` | Current levels; history-as-current | No snapshot ID |
| Q3-05 | Unsupported 132% probability | QUERY, CLAIMS, LIMITATIONS | `MISSING_EVIDENCE` | `132%`, estimate, confidence | Claim id only; no number |
| Q3-06 | Complete governed claim with detail | QUERY, CLAIMS, EVIDENCE | `SMALL_N_UNRESOLVED` if threshold absent | “VALIDATED” if status is candidate | Claim/evidence IDs and N bound |
| Q3-07 | Requested claim with missing evidence | QUERY, CANONICAL_MODEL, CLAIMS, LIMITATIONS | `MISSING_EVIDENCE` | Any statistic | No evidence ID invented |
| Q3-08 | Small N = 8 with governed threshold ref | QUERY, CLAIMS, EVIDENCE | none or explicit small-N issue | Invented threshold | N and threshold ref included |
| Q3-09 | Missing N | QUERY, CLAIMS, EVIDENCE, LIMITATIONS | `SMALL_N_UNRESOLVED`; `DETAIL_NOT_SUPPLIED` | Default N, guessed flag | No N value |
| Q3-10 | L3 probability plus L1 setup | QUERY, CLAIMS, SETUP, LIMITATIONS | Layer-separation issue if cross-filled | L1 win rate from L3 | Both layer IDs, no merged fact |
| Q3-11 | XAU WATCH with active no-go | QUERY, SETUP, LIMITATIONS_NEGATIVE | `NO_GO_ACTIVE`; `SETUP_NOT_ELIGIBLE` | `ELIGIBLE`, entry instruction | No-go ref mandatory |
| Q3-12 | Fib research-only setup | QUERY, SETUP, LIMITATIONS | `RESEARCH_ONLY_NOT_PRODUCTION` | Production approval | Research surface preserved |
| Q3-13 | JPY manual confirmation | QUERY, SETUP, LIMITATIONS | `AUTOMATION_NOT_APPROVED` if automation asked | Execution permission, order size | Manual class preserved |
| Q3-14 | BTC Game and BTC Tracker | QUERY, CANONICAL_MODEL, CLAIMS, EVIDENCE | none or `INCOMPARABLE_EVIDENCE` | Merged identity/statistic | Both model IDs present |
| Q3-15 | Historical P90 generation | QUERY, CANONICAL_MODEL, CLAIMS, LINEAGE_TERMS | `HISTORICAL_GENERATION` | Current status; newest fallback | P90 generation bound |
| Q3-16 | Contradictory evidence, same identity | QUERY, CLAIMS, EVIDENCE, LIMITATIONS | `EVIDENCE_CONFLICT` | Winner, majority result | Both claim/evidence IDs |
| Q3-17 | Negative/null research | QUERY, CLAIMS, EVIDENCE, LIMITATIONS | `NEGATIVE_EVIDENCE` | Trading signal, suppression | Negative ref retained |
| Q3-18 | Malicious retrieved text | QUERY, CANONICAL_MODEL, LIMITATIONS | Data-only issue; no privilege | Instruction execution, entitlement | Untrusted hash only; no control mutation |
| Q3-19 | Denied internal-method reference | none or QUERY only | `CONTEXT_EXPOSURE_VIOLATION` | Internal ID/name, payload | Denied ID absent from manifest |
| Q3-20 | Mandatory context exceeds budget | QUERY, LIMITATIONS only on refusal | `CONTEXT_BUDGET_EXCEEDED` | Partial narrative, trimmed no-go | Omission ledger has no hidden IDs |

---

## 4. DEFINITION OF DONE FOR RUNG 2

1. All 92 requirements map to all 92 exact tests.
2. Zero missing, renamed, skipped, xfailed or weakened tests.
3. All 20 fixtures reproduce byte-identically.
4. No internal or denied identifier appears in any package or manifest.
5. No-go, invalidation and insufficiency survive every budget case.
6. Package and manifest identities are deterministic and independent of wall
   clock/random/process state.
7. Full repository regression includes IV.1, IV.2, Book III and all prior suites.
8. Frozen hashes, routes, migrations and provider seam remain unchanged.
9. CI `test` and `postgres` jobs pass at the pushed head.
10. Evidence and ratification state the contract verdict separately from live,
    tokenizer, statistical and entitlement readiness.

---

## 5. NON-CLAIMS

A green IV.3 suite will not prove:

- provider tokenizer accuracy;
- live current market data;
- durable historical retrieval;
- complete statistical population/sample bodies;
- Book VI commercial entitlement;
- production LLM behavior;
- Book IV completion.
