# BOOK III — END-TO-END INTEGRATION ACCEPTANCE

**Book:** III · **Packet:** BA-23 Rung 1 (planning only)
**Status:** PROPOSED — binding only after a separately authorized implementation rung
**Depends on:** `implementation/forge/book_iii/integration/PLAN.md`
**Proposed suite:** `tests/test_forge_book_iii_integration.py`
**Proposed test count:** **96** (T1–T12)

This document does not modify any bloc's frozen `ACCEPTANCE.md`. It defines the
cross-bloc program those bloc suites cannot cover.

---

## 1. Acceptance matrix

| Family | Clauses | Proposed tests | Proves |
|---|---|---:|---|
| T1 full lineage | IN-1…10 | 10 | one identity through observation → snapshot |
| T2 quality/failure propagation | IN-11…19 | 9 | bounded failure semantics at every edge |
| T3 model-family isolation | IN-20…28 | 9 | family/layer/calibration cannot leak |
| T4 path and first delivery | IN-29…36 | 8 | ordered history survives composition |
| T5 setup and no-go governance | IN-37…45 | 9 | eligibility cannot be manufactured |
| T6 Book II authorization | IN-46…52 | 7 | deny before protected composition |
| T7 snapshot determinism | IN-53…60 | 8 | identical inputs, identical bytes |
| T8 historical generation | IN-61…68 | 8 | pinned replay, honest unavailability |
| T9 canonical-source compatibility | IN-69…76 | 8 | card defect reproduced, not repaired |
| T10 consumer compatibility | IN-77…83 | 7 | DTO is sufficient and non-authoritative |
| T11 security and cache | IN-84…90 | 7 | no leakage or widening |
| T12 regression and frozen integrity | IN-91…96 | 6 | nothing upstream moved |
| **Total** | **96** | **96** | |

---

## 2. Proposed executable names

### T1 — Full lineage (10)

1. `test_integration_observation_reaches_measurement`
2. `test_integration_measurement_reaches_model_output`
3. `test_integration_model_output_reaches_state_snapshot`
4. `test_integration_state_reaches_transition_ledger`
5. `test_integration_transition_reaches_setup_evaluation`
6. `test_integration_setup_reaches_snapshot`
7. `test_integration_snapshot_preserves_model_and_layer`
8. `test_integration_single_identity_through_all_six_blocs`
9. `test_integration_clock_identity_survives_every_boundary`
10. `test_integration_no_bloc_recomputes_upstream_fact`

### T2 — Quality and failure propagation (9)

11. `test_integration_missing_provider_blocks_current_snapshot`
12. `test_integration_nonfinal_bar_cannot_reach_model`
13. `test_integration_blocked_quality_propagates_to_setup`
14. `test_integration_unresolved_clock_blocks_calculation`
15. `test_integration_mixed_cutoff_refused`
16. `test_integration_missing_model_version_refused`
17. `test_integration_missing_measurement_refused`
18. `test_integration_no_go_is_not_provider_failure`
19. `test_integration_stale_is_labelled_not_current`

### T3 — Model-family isolation (9)

20. `test_integration_eur_layers_keep_ownership`
21. `test_integration_xau_l1_l2_l3_do_not_merge`
22. `test_integration_btc_tracker_has_no_game_setup`
23. `test_integration_fib_stays_research_only`
24. `test_integration_jpy_roles_are_not_a_vote`
25. `test_integration_cross_asset_tier_cannot_leak`
26. `test_integration_model_family_preserved_in_view`
27. `test_integration_layer_conflict_is_fact_not_score`
28. `test_integration_no_confluence_field_exists`

### T4 — Path and first-delivery integrity (8)

29. `test_integration_path_order_survives_composition`
30. `test_integration_reversed_paths_hash_differently`
31. `test_integration_terminal_outcome_does_not_erase_path`
32. `test_integration_rekey_is_explicit_transition`
33. `test_integration_range_left_updates_after_consumption`
34. `test_integration_intrabar_ambiguity_refused`
35. `test_integration_first_delivery_preserved_in_payload`
36. `test_integration_transition_sequence_is_monotonic`

### T5 — Setup and no-go governance (9)

37. `test_integration_stand_down_blocks_eligible_setup`
38. `test_integration_model_state_alone_cannot_create_setup`
39. `test_integration_xau_blind_touch_blocked`
40. `test_integration_fib_unresolved_anchor_blocked`
41. `test_integration_jpy_equal_vote_impossible`
42. `test_integration_research_setup_cannot_be_production`
43. `test_integration_setup_carries_no_execution_authority`
44. `test_integration_manual_setup_keeps_automation_false`
45. `test_integration_eligibility_verbatim_in_snapshot`

### T6 — Book II authorization (7)

46. `test_integration_denial_prevents_composition`
47. `test_integration_denial_reveals_no_identifier`
48. `test_integration_anonymous_cannot_read_operator_snapshot`
49. `test_integration_research_exposure_cannot_become_public`
50. `test_integration_policy_failure_fails_closed`
51. `test_integration_audit_records_every_decision`
52. `test_integration_correlation_id_propagates`

### T7 — Snapshot determinism (8)

53. `test_integration_same_inputs_same_snapshot_id`
54. `test_integration_same_inputs_same_bytes`
55. `test_integration_changed_cutoff_changes_identity`
56. `test_integration_changed_model_version_changes_identity`
57. `test_integration_changed_clock_changes_identity`
58. `test_integration_payload_roundtrip_preserves_decimals`
59. `test_integration_no_float_coercion_in_prices`
60. `test_integration_component_hashes_are_ordered`

### T8 — Historical generation (8)

61. `test_integration_historical_replay_reproduces_hash`
62. `test_integration_historical_never_upgrades_version`
63. `test_integration_historical_missing_inputs_unavailable`
64. `test_integration_historical_outside_retention_explicit`
65. `test_integration_historical_version_drift_refused`
66. `test_integration_historical_view_labelled`
67. `test_integration_historical_evidence_status_preserved`
68. `test_integration_current_and_historical_are_distinct`

### T9 — Canonical-source compatibility (8)

69. `test_integration_three_cards_fail_machine_validation`
70. `test_integration_card_failure_is_exactly_three_errors`
71. `test_integration_card_ids_carried_verbatim`
72. `test_integration_card_status_not_promoted`
73. `test_integration_strict_card_operation_refused`
74. `test_integration_verbatim_view_is_lossless`
75. `test_integration_no_set_star_id_minted`
76. `test_integration_adr_deferral_recorded`

### T10 — Consumer compatibility (7)

77. `test_integration_consumer_dto_fields_present`
78. `test_integration_consumer_cannot_mutate_snapshot`
79. `test_integration_consumer_sees_eligibility_verbatim`
80. `test_integration_consumer_sees_no_authority_fields`
81. `test_integration_consumer_quality_flags_visible`
82. `test_integration_consumer_warnings_and_refusals_visible`
83. `test_integration_consumer_requires_no_recalculation`

### T11 — Security and cache boundaries (7)

84. `test_integration_cache_hit_still_authorized`
85. `test_integration_cache_does_not_cross_principals`
86. `test_integration_cache_invalidated_on_exposure_change`
87. `test_integration_refusal_has_no_payload`
88. `test_integration_no_source_or_module_disclosure`
89. `test_integration_no_network_during_composition`
90. `test_integration_response_is_bounded`

### T12 — Regression and frozen integrity (6)

91. `test_integration_all_bloc_suites_still_green`
92. `test_integration_book_ii_fifty_hashes`
93. `test_integration_nineteen_module_baselines`
94. `test_integration_migrations_unchanged`
95. `test_integration_provider_seam_unchanged`
96. `test_integration_no_production_claim`

---

## 3. Golden fixtures

Proposed integration fixture set (committed only in the implementation rung):

| Fixture | Purpose | Pinned |
|---|---|---|
| `full_eur_lineage` | observation → snapshot over EUR daily | schema, model, measurement, engine versions |
| `xau_promotion_chain` | promotion state through setup context | XAU model/version |
| `btc_tracker_no_game` | tracker output with no setup | BTC model/version |
| `fib_unresolved_anchor` | research-only gate end to end | Fib model/version |
| `jpy_basket_roles` | role-preserving basket | JPY model/version |
| `stand_down_lock` | lock through setup and snapshot | III.4 engine version |
| `provider_missing` | `PROVIDER_NOT_CONFIGURED` end to end | schema version |
| `historical_pinned_replay` | replay hash equality | record id + hash |
| `card_schema_incompatible` | three machine errors | corpus commit |
| `restricted_exposure` | denial with no payload | policy version |

Requirements: byte-identical regeneration, LF-normalised SHA-256 manifest,
independent expected values, and explicit `SYNTHETIC_FIXTURE` labelling.

---

## 4. Frozen-integrity checks

| Check | Expected |
|---|---|
| Book I freeze manifest | unchanged |
| Book II 50 hashes | 50/50 match |
| III.1 / III.2 / III.3 / III.4 / III.5 / III.6 module hashes | 11/12/13/13/16/14 match |
| Migrations | `001`–`004`, no addition |
| Provider seam | unchanged, `NOT_CONFIGURED` |
| Frozen PLAN/ACCEPTANCE files | byte-identical |
| Route freeze | `routes.py` hash unchanged |

Any mismatch stops the packet before assertions run.

---

## 5. Negative and adversarial scenarios

1. Protected snapshot requested by anonymous principal.
2. Composer spy proves zero load after denial.
3. Model version swapped between request and record.
4. Cutoff moved while identity held fixed.
5. Nonfinal bar offered as final.
6. Two observations in one bar with ordering unresolvable.
7. Stand-down lock present while setup would otherwise be eligible.
8. Fib setup requested on production surface.
9. JPY equal-vote aggregation attempted.
10. Card projected through strict schema.
11. Cache reused across principals or exposure classes.
12. Refusal inspected for protected identifiers.
13. Historical request with no retained inputs.
14. Payload round-trip with high-precision prices.
15. Fixture relabelled as empirical evidence.
16. Production GO claim attempted from a green suite.

---

## 6. Ratification criteria

The integration packet may be ratified only when all of the following hold at
the published head:

1. 96/96 proposed names exist and pass; 0 skipped, 0 xfail, 0 weakened.
2. Every clause IN-1…96 maps to a test or a recorded review.
3. Fixtures reproduce byte-identically from the manifest.
4. Frozen-integrity checks pass with zero mismatches.
5. Full repository regression is green.
6. Both CI jobs pass at the final head.
7. Gaps remain classified and open; no gap is closed by a passing test.

Ratification means the system's **contracts** compose. It does not mean the
system is production-ready, and it does not authorize Books IV–VIII.
