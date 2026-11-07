# BOOK IV / BLOC IV.2 — ACCEPTANCE
## HYBRID RETRIEVAL & EVIDENCE ROUTING — BA-27 RUNG 1

**Base HEAD:** `238c4da970f6d213053d6cae0c679d1dda404912`
**Contract:** `RETRIEVAL_CONTRACT_V1` (proposed)
**Test file:** `tests/test_forge_ask_cerebus_retrieval.py`
**Test count:** 72 (`A-01`–`A-72`)
**Requirement count:** 64 (`R1`–`R64`)

This document binds implementation. A test may not be skipped, xfailed,
renamed, merged or weakened. Every requirement has one base driver; T11/T12 add
cross-cutting checks.

---

## 1. REQUIREMENT INVENTORY

### T1 — Structured canonical resolution (R1–R7)

| ID | Requirement |
|---|---|
| R1 | Resolve an exact canonical object id from the query plan without lexical approximation. |
| R2 | Select candidates from safe `RetrievalHeader` metadata before any protected body is loaded. |
| R3 | Preserve the exact requested canonical version/generation; never resolve `latest`/`current` tokens. |
| R4 | Expand governed aliases exactly, without promoting status, version or exposure. |
| R5 | Traverse typed object relationships only through policy-guarded retrieval. |
| R6 | Return an explicit unresolved outcome when no canonical object matches. |
| R7 | Never invent, fuzzy-match or nearest-neighbour a missing canonical object. |

### T2 — Semantic resolution (R8–R13)

| ID | Requirement |
|---|---|
| R8 | Provide a replaceable semantic-retrieval port with no canonical authority. |
| R9 | Search only records that already passed the Book II policy filter. |
| R10 | Semantic results cannot establish identity, version, status, win rate, probability, eligibility or exposure. |
| R11 | Use deterministic fake semantic results for the first implementation. |
| R12 | Require later authorization before connecting a real embedding/vector service. |
| R13 | Treat a semantic passage as supporting context only, never as authority. |

### T3 — Canonical priority (R14–R19)

| ID | Requirement |
|---|---|
| R14 | Enforce the frozen six-tier source precedence. |
| R15 | A direct canonical fact outranks every semantic passage. |
| R16 | A lower-priority passage cannot overwrite a higher-priority fact. |
| R17 | Record disagreement instead of silently resolving it. |
| R18 | A semantic relevance score does not imply canonical authority. |
| R19 | A semantic passage cannot promote a research or historical status. |

### T4 — Claim/evidence joins (R20–R26)

| ID | Requirement |
|---|---|
| R20 | Join Query → Model → Claim → Evidence → Provenance exactly. |
| R21 | Retain claim identity dimensions. |
| R22 | Retain the model and generation version that produced a statistic. |
| R23 | Retain metric, conditioning population, sample size, period and event definition when governed fields provide them. |
| R24 | Retain evidence status and provenance references. |
| R25 | Report OOS/reproduction status when available and its absence honestly. |
| R26 | Missing evidence yields `EVIDENCE_INSUFFICIENT` and no numerical answer. |

### T5 — Book III live intelligence join (R27–R33)

| ID | Requirement |
|---|---|
| R27 | Route `CURRENT` through the typed III.6 snapshot contract. |
| R28 | Route level/coordinate requests with layer, level kind and state. |
| R29 | Route setup context with canonical card id, version and parent-state requirements. |
| R30 | Route historical snapshots with explicit model version and cutoff; never substitute current. |
| R31 | Route instrument views with quality outcome and source cutoffs. |
| R32 | Route JPY basket context only where the typed basket request supports it. |
| R33 | Refuse when required snapshot fields are unresolved; never invent version, cutoff, calculation version, clock or hash. |

### T6 — Generation and lineage (R34–R39)

| ID | Requirement |
|---|---|
| R34 | Preserve P90 / P90P / PHI generation identity. |
| R35 | Preserve ST / Base80 generation; ST manual is never automated. |
| R36 | Preserve session, clock and historical Markov/Fib generation tags. |
| R37 | Keep BTC Game and BTC Tracker as distinct identities. |
| R38 | Expand lineage without merging claims or statistics across generations. |
| R39 | Never resolve an unavailable original generation to the newest model. |

### T7 — Conflict resolution (R40–R45)

| ID | Requirement |
|---|---|
| R40 | Compare instrument, market, event, population, model/version, clock, horizon, metric, tolerance and period before declaring conflict. |
| R41 | Same identity with conflicting evidence preserves both claims and downgrades the conclusion. |
| R42 | Different identities are separated as incomparable, not contradictory. |
| R43 | Never use majority vote or semantic similarity as the numerical winner. |
| R44 | Retain `supersedes` and `contradicts` metadata. |
| R45 | Keep conflicting evidence visible with original statuses. |

### T8 — Negative evidence (R46–R50)

| ID | Requirement |
|---|---|
| R46 | Retrieve failed hypotheses and null findings. |
| R47 | Retrieve parked, superseded, falsified and no-go objects as negative references. |
| R48 | Do not bias candidate generation toward positive outcomes. |
| R49 | Preserve negative evidence status and generation. |
| R50 | Negative research evidence is not a current trading signal. |

### T9 — Authorization and exposure (R51–R57)

| ID | Requirement |
|---|---|
| R51 | Authorize before any retrieval exposure. |
| R52 | Deny before loading a protected body for every object and hop. |
| R53 | Researcher depth does not grant exposure or entitlement. |
| R54 | Guessing a hidden object id does not reveal its existence. |
| R55 | Semantic neighbours cannot bypass the policy filter. |
| R56 | Citation/source traversal cannot bypass policy. |
| R57 | Repeated queries cannot enumerate hidden objects. |

### T10 — Retrieval trace (R58–R64)

| ID | Requirement |
|---|---|
| R58 | Bind the trace to the exact query-plan id and retrieval contract version. |
| R59 | List only authorized selected object, claim, evidence and snapshot references. |
| R60 | Report rejection counts by bounded reason class. |
| R61 | Keep internal audit, consumer-safe and refusal traces distinct. |
| R62 | Exclude forbidden object names, protected text and secrets from traces. |
| R63 | Emit an exposure-safe, replay-stable consumer projection. |
| R64 | Compute a deterministic manifest digest and avoid indefinite protected retention. |

---

## 2. EXACT TEST NAMES AND BINDINGS

| Test | Requirement | Exact executable name |
|---|---|---|
| A-01 | R1 | `test_a01_resolves_exact_canonical_id_from_plan` |
| A-02 | R2 | `test_a02_selects_candidates_from_safe_headers_only` |
| A-03 | R3 | `test_a03_preserves_exact_canonical_version` |
| A-04 | R4 | `test_a04_expands_governed_alias_without_promotion` |
| A-05 | R5 | `test_a05_traverses_relationships_under_policy` |
| A-06 | R6 | `test_a06_reports_unresolved_identity_without_invention` |
| A-07 | R7 | `test_a07_never_fuzzy_matches_unknown_model` |
| A-08 | R8 | `test_a08_semantic_port_is_replaceable_and_pure` |
| A-09 | R9 | `test_a09_searches_only_authorized_records` |
| A-10 | R10 | `test_a10_semantic_candidate_cannot_supply_authority` |
| A-11 | R11 | `test_a11_fake_semantic_results_are_deterministic` |
| A-12 | R12 | `test_a12_real_semantic_index_requires_authorization` |
| A-13 | R13 | `test_a13_semantic_passage_is_support_only` |
| A-14 | R14 | `test_a14_enforces_frozen_six_tier_precedence` |
| A-15 | R15 | `test_a15_canonical_fact_outranks_semantic_passage` |
| A-16 | R16 | `test_a16_lower_priority_never_overwrites_canonical` |
| A-17 | R17 | `test_a17_records_disagreement_without_silent_resolution` |
| A-18 | R18 | `test_a18_semantic_score_is_not_authority` |
| A-19 | R19 | `test_a19_semantic_passage_never_promotes_status` |
| A-20 | R20 | `test_a20_joins_query_model_claim_evidence_provenance` |
| A-21 | R21 | `test_a21_retains_claim_identity_dimensions` |
| A-22 | R22 | `test_a22_retains_model_and_generation_version` |
| A-23 | R23 | `test_a23_preserves_population_sample_and_period` |
| A-24 | R24 | `test_a24_carries_evidence_status_and_provenance` |
| A-25 | R25 | `test_a25_reports_oos_and_reproduction_absence` |
| A-26 | R26 | `test_a26_missing_evidence_is_insufficient_without_number` |
| A-27 | R27 | `test_a27_routes_current_request_to_iii6_contract` |
| A-28 | R28 | `test_a28_routes_level_request_with_layer_and_state` |
| A-29 | R29 | `test_a29_routes_setup_context_with_card_and_parent` |
| A-30 | R30 | `test_a30_routes_historical_snapshot_without_substitution` |
| A-31 | R31 | `test_a31_routes_instrument_view_with_quality` |
| A-32 | R32 | `test_a32_routes_jpy_basket_context_when_supported` |
| A-33 | R33 | `test_a33_refuses_unresolved_snapshot_fields` |
| A-34 | R34 | `test_a34_preserves_p90_and_phi_generation` |
| A-35 | R35 | `test_a35_preserves_st_and_base80_generation` |
| A-36 | R36 | `test_a36_preserves_session_clock_and_historical_generation` |
| A-37 | R37 | `test_a37_separates_btc_game_from_btc_tracker` |
| A-38 | R38 | `test_a38_expands_lineage_without_merging_statistics` |
| A-39 | R39 | `test_a39_unavailable_generation_never_falls_back` |
| A-40 | R40 | `test_a40_compares_identity_before_declaring_conflict` |
| A-41 | R41 | `test_a41_matched_conflict_preserves_both_claims` |
| A-42 | R42 | `test_a42_separates_incomparable_claims` |
| A-43 | R43 | `test_a43_never_uses_majority_or_similarity_as_truth` |
| A-44 | R44 | `test_a44_carries_supersedes_and_contradicts_refs` |
| A-45 | R45 | `test_a45_keeps_conflicting_evidence_visible` |
| A-46 | R46 | `test_a46_retrieves_failed_and_null_findings` |
| A-47 | R47 | `test_a47_retrieves_parked_superseded_and_no_go` |
| A-48 | R48 | `test_a48_does_not_bias_retrieval_toward_positive` |
| A-49 | R49 | `test_a49_preserves_negative_status_and_generation` |
| A-50 | R50 | `test_a50_negative_evidence_is_not_a_trading_signal` |
| A-51 | R51 | `test_a51_authorizes_before_any_retrieval` |
| A-52 | R52 | `test_a52_denies_before_loading_protected_body` |
| A-53 | R53 | `test_a53_researcher_depth_does_not_grant_exposure` |
| A-54 | R54 | `test_a54_direct_id_guess_does_not_reveal_existence` |
| A-55 | R55 | `test_a55_semantic_neighbor_cannot_bypass_policy` |
| A-56 | R56 | `test_a56_citation_traversal_cannot_bypass_policy` |
| A-57 | R57 | `test_a57_repeated_queries_do_not_enumerate_hidden_objects` |
| A-58 | R58 | `test_a58_trace_binds_plan_and_contract_version` |
| A-59 | R59 | `test_a59_trace_lists_only_authorized_references` |
| A-60 | R60 | `test_a60_trace_counts_rejections_by_reason_class` |
| A-61 | R61 | `test_a61_internal_consumer_and_refusal_traces_are_distinct` |
| A-62 | R62 | `test_a62_trace_excludes_forbidden_names_and_text` |
| A-63 | R63 | `test_a63_consumer_trace_is_exposure_safe` |
| A-64 | R64 | `test_a64_bundle_digest_is_deterministic_and_minimized` |
| A-65 | T11 | `test_a65_identical_plans_produce_identical_bundles` |
| A-66 | T11 | `test_a66_absent_source_yields_bounded_refusal` |
| A-67 | T11 | `test_a67_provider_not_configured_never_substitutes_history` |
| A-68 | T11 | `test_a68_policy_engine_failure_fails_closed` |
| A-69 | T12 | `test_a69_frozen_iv1_query_contract_unchanged` |
| A-70 | T12 | `test_a70_frozen_book_i_retrieval_contract_unchanged` |
| A-71 | T12 | `test_a71_frozen_book_ii_policy_contract_unchanged` |
| A-72 | T12 | `test_a72_no_network_vector_or_llm_import_in_iv2` |

---

## 3. GOLDEN RETRIEVAL FIXTURES

18 scenarios, `Q2-01`–`Q2-18`, stored under
`implementation/forge/book_iv/bloc_iv_2/fixtures/`.

| ID | Scenario | Expected selection / outcome | Required refusal or limitation | Forbidden |
|---|---|---|---|---|
| Q2-01 | Exact canonical definition | Direct model reference | None | Semantic override |
| Q2-02 | Model-description resolution | Model + bounded purpose text | `LIMITED_QUOTE_SCOPE` if internal markers | Internal method text |
| Q2-03 | Numerical claim with evidence | Claim → Evidence → Artifact | None | Number without provenance |
| Q2-04 | Numerical claim lacking evidence | Claim as `FOUND_UNSUPPORTED` | `EVIDENCE_INSUFFICIENT` | Any fabricated statistic |
| Q2-05 | BTC Game / Tracker collision | `BTC.GAME` and `BTC.TRACKER` refs | `MATERIAL_AMBIGUITY` if unresolved | Merged identity |
| Q2-06 | Historical P90 generation | Exact generation-tagged refs | `HISTORICAL_GENERATION` | Newest-version fallback |
| Q2-07 | Current Gold, provider unavailable | No current market ref | `PROVIDER_NOT_CONFIGURED` | Historical snapshot as current |
| Q2-08 | Setup request with active no-go | Setup ref + `NO_GO_ACTIVE` | `SETUP_BLOCKED` | Eligibility grant |
| Q2-09 | XAU Quarter-Zone WATCH | Setup ref, status `WATCH` | `SETUP_NOT_ELIGIBLE` | Production approval |
| Q2-10 | Fib research-only | Fib ref on research surface | `RESEARCH_ONLY_NOT_PRODUCTION` | Production eligibility |
| Q2-11 | JPY manual confirmation | JPY ref, manual class | `AUTOMATION_NOT_APPROVED` if automation asked | Automated execution |
| Q2-12 | Contradictory evidence, same identity | Both claims + evidence | `EVIDENCE_CONFLICT` | Majority winner |
| Q2-13 | Incomparable evidence, different identity | Separated refs | `INCOMPARABLE_EVIDENCE` | Manufactured contradiction |
| Q2-14 | Negative/null research evidence | Negative ref retained | `NEGATIVE_EVIDENCE` | Suppression or signal |
| Q2-15 | Unauthorized direct ID | No payload | `EXPOSURE_FORBIDDEN` | Existence disclosure |
| Q2-16 | Unauthorized semantic neighbour | No payload | `EXPOSURE_FORBIDDEN` | Neighbour leakage |
| Q2-17 | Historical snapshot unavailable | No snapshot | `HISTORICAL_UNAVAILABLE` | Current substitution |
| Q2-18 | Semantic text conflicts with canonical fact | Canonical ref first | `SOURCE_DISAGREEMENT` | Semantic overwrite |

Each fixture records input plan id, available objects, principal/policy context,
Book III availability, expected refs, refusals, forbidden outputs, evidence
status and deterministic trace digest. No fixture may contain a fabricated
historical statistic or a production-approved setup.

---

## 4. ACCEPTANCE DEFINITION OF DONE

Implementation is accepted only when:

1. All 72 named tests exist and pass, with zero skips/xfails.
2. Every R1–R64 maps to its base driver.
3. All 18 fixtures reproduce byte-identical payloads and bundle ids.
4. Book I, II and III suites remain green.
5. No upstream source, migration, route or provider is modified.
6. `CURRENT` remains unavailable under `NOT_CONFIGURED`, with no substitution.
7. No LLM, embedding, vector or network dependency is added.
8. EVIDENCE and RATIFICATION record measured results separately from this plan.

Passing these tests does not close F3/F4 capabilities or declare Book IV
complete.
