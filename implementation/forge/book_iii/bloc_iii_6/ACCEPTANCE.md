# BOOK III / BLOC III.6 — INTELLIGENCE API & SNAPSHOT SERVICE — ACCEPTANCE.md

**Bloc:** III.6 · **Authority:** BA-22 Rung 1 (planning only)
**Planning head:** `d74f10a503177a7fc6b3f8699c0781102125f6ce`
**Status:** FROZEN ACCEPTANCE CONTRACT — authoritative on clause ids,
test names and counts. `PLAN.md` describes intent; **this file binds the
future implementation**. Names may be **added** at implementation; none
may be deleted, weakened, skipped or xfailed.

**Clause count:** 300 across sections A–T. **Test count:** 258 across
groups T1–T14. Every clause names at least one driver; several clauses
share one driver where the frozen condition is a single observable.

**Core law under test:** the API transports governed intelligence — it
never manufactures market truth, setup eligibility, exposure authority or
execution authority. A deterministic payload is not proof that an upstream
schema inconsistency has been resolved.

**Chapters covered (frozen):** Ch III.6.1–III.6.12 and Acceptance III.6,
verbatim from
`planning/forge/books/BOOK_III_CEREBUS_MARKET_INTELLIGENCE_PLAN_V1.md`.

---

## A. Snapshot identity (Ch III.6.1)

- **A1.** A snapshot key carries exactly: instrument, model id, model
  version, layer, `as_of`, data cutoff, calculation version. → `T1 test_snapshot_key_field_set_is_frozen`
- **A2.** `snapshot_id` is derived from the key by the service, never
  accepted from a caller. → `T1 test_snapshot_id_is_derived_not_supplied`
- **A3.** The key additionally pins clock id and session id, because data
  clock is part of model identity (invariant #1). → `T1 test_clock_and_session_are_part_of_identity`
- **A4.** `snapshot_hash` is computed over the whole canonical payload,
  not over a subset. → `T1 test_snapshot_hash_covers_every_component`
- **A5.** Component hashes are folded in a fixed order; reordering inputs
  changes nothing about the hash. → `T1 test_component_hash_order_is_canonical`
- **A6.** Identical key + identical inputs ⇒ identical `snapshot_id` and
  `snapshot_hash`. → `T1 test_same_key_same_snapshot_id`
- **A7.** A different `as_of` yields a different identity. → `T1 test_different_as_of_changes_identity`
- **A8.** A different data cutoff yields a different identity. → `T1 test_different_data_cutoff_changes_identity`
- **A9.** A different model version yields a different identity. → `T1 test_model_version_is_part_of_identity`
- **A10.** A different calculation version yields a different identity. → `T1 test_calculation_version_is_part_of_identity`
- **A11.** A different layer yields a different identity; layers are never
  folded into one snapshot. → `T1 test_layer_is_part_of_identity`
- **A12.** Principal identity is **not** part of the logical snapshot
  identity; authorization is applied outside the snapshot. → `T1 test_identity_excludes_principal`
- **A13.** A snapshot is immutable once built; mutation raises. → `T1 test_snapshot_is_immutable`
- **A14.** Every populated field is source-backed by an upstream
  reference; an unsourceable field is absent, not guessed. → `T1 test_snapshot_requires_source_backing`
- **A15.** A missing section is explicit (`UNAVAILABLE` + reason), never an
  empty container that reads as "nothing to report". → `T1 test_missing_section_is_explicit_not_empty`
- **A16.** The provenance block lists source registry versions, engine
  versions and fixture/lineage identities. → `T1 test_snapshot_provenance_block_is_complete`
- **A17.** Engine versions consumed are recorded verbatim (III.1 schema,
  clock and session registries, III.2 engine, III.3 runtime, III.4 state
  engine, III.5 setup engine). → `T1 test_engine_versions_recorded`
- **A18.** Canonical JSON serialisation is stable across processes and
  runs (sorted keys, no floats, no timestamps added at serve time). → `T1 test_snapshot_serialization_is_stable_across_runs`
- **A19.** No field accepts free prose; explanations are structured facts. → `T1 test_snapshot_carries_no_free_prose`
- **A20.** An unknown `schema_version` fails closed. → `T1 test_snapshot_refuses_unknown_schema_version`

## B. Current state service (Ch III.6.2)

- **B1.** The current-state surface returns only authorized fields: state,
  layer, direction/bias, active range/tier, clocks, quality, no-go. → `T2 test_current_state_returns_authorized_fields`
- **B2.** Layer ownership travels with each state value. → `T2 test_current_state_carries_layer_ownership`
- **B3.** Direction/bias appears only where the model defines it. → `T2 test_direction_bias_only_where_defined`
- **B4.** Active range and tier are reported as references to III.2/III.3
  artefacts, not recomputed numbers. → `T2 test_active_range_and_tier_reported`
- **B5.** Clock and session lineage are reported with their registry
  versions. → `T2 test_clocks_reported_with_session_lineage`
- **B6.** Quality is carried verbatim in the frozen III.1 vocabulary. → `T2 test_quality_state_reported_verbatim`
- **B7.** A no-go state is a legitimate factual result, not an error, and
  is distinguishable from unavailable data. → `T2 test_no_go_reported_as_fact_not_error`
- **B8.** An unregistered model or version is refused; no default model is
  substituted. → `T2 test_current_state_requires_registered_model`
- **B9.** A rule that is declared but not materialised is reported as such
  and never approximated. → `T2 test_current_state_refuses_unmaterialized_rule`
- **B10.** The payload marks itself `CURRENT` explicitly and carries its
  data cutoff. → `T2 test_current_state_marks_current_explicitly`
- **B11.** No confidence, probability or score field exists. → `T2 test_current_state_includes_no_confidence_field`
- **B12.** No order, size, allocation, entry price or execution instruction
  field exists. → `T2 test_current_state_payload_has_no_execution_fields`
- **B13.** An active stand-down/lock is reported as a locked capability
  fact, not silently omitted. → `T2 test_current_state_carries_layer_ownership`
- **B14.** The current-state surface is derived from the same composer as
  the full snapshot (no second path). → `T2 test_current_state_returns_authorized_fields`
- **B15.** `as_of`/cutoff/calculation timestamps remain distinct fields. → `T2 test_current_state_marks_current_explicitly`
- **B16.** Degraded quality is surfaced, not hidden behind a successful
  response shape. → `T2 test_quality_state_reported_verbatim`

## C. Levels service (Ch III.6.3)

- **C1.** Levels are typed: measurement, decision, target, invalidation,
  rekey, promotion, zone. → `T3 test_levels_are_typed_by_kind`
- **C2.** The level-kind vocabulary is closed; an unknown kind is refused. → `T3 test_level_kind_vocabulary_is_frozen`
- **C3.** Every level carries its source model id and version. → `T3 test_each_level_carries_source_model_and_version`
- **C4.** Every level carries an active/inactive state. → `T3 test_levels_carry_active_flag`
- **C5.** A level without a canonical source reference is refused. → `T3 test_level_without_source_ref_refused`
- **C6.** Measurement levels and decision levels remain distinguishable. → `T3 test_measurement_level_distinct_from_decision_level`
- **C7.** Target levels preserve declared order; the service never sorts
  them by price or proximity. → `T3 test_target_levels_preserve_declared_order`
- **C8.** Invalidation levels are carried separately from targets. → `T3 test_invalidation_level_carried_separately`
- **C9.** A zone level without canonical mapping is reported as declared
  and capped (`WATCH`), never as an eligible zone. → `T3 test_zone_level_requires_canonical_mapping_or_watch`
- **C10.** The service never reprices or resamples an upstream
  measurement. → `T3 test_levels_never_reprice_upstream_measurement`
- **C11.** Prices are `Decimal`-backed and serialised exactly. → `T3 test_each_level_carries_source_model_and_version`
- **C12.** A level referencing an unresolved anchor is refused for
  coordinate families that require one. → `T3 test_level_without_source_ref_refused`
- **C13.** Levels carry no probability, hit-rate or reward field. → `T3 test_levels_carry_active_flag`
- **C14.** An empty level set is explicit and reason-bearing. → `T3 test_measurement_level_distinct_from_decision_level`

## D. Path service (Ch III.6.4)

- **D1.** The path surface reports the current path as consumed states. → `T4 test_path_reports_consumed_states`
- **D2.** First-delivery history is reported in recorded order. → `T4 test_path_reports_first_delivery_history`
- **D3.** Range-left is reported as a conditional field, with what it is
  conditioned on. → `T4 test_path_reports_range_left`
- **D4.** The transition sequence summary is ordered and bounded. → `T4 test_path_transition_summary_is_ordered`
- **D5.** The service never sorts, dedupes or re-sequences history. → `T4 test_path_never_sorts_history`
- **D6.** Reversing the delivery order produces a different path payload. → `T4 test_path_reversal_produces_different_path`
- **D7.** Terminal reach does not erase the path that produced it. → `T4 test_path_terminal_does_not_erase_path`
- **D8.** Ambiguous intrabar ordering is reported as unresolved, never
  invented. → `T4 test_path_reports_unresolved_ordering`
- **D9.** The path surface recomputes no transitions; it reads III.4. → `T4 test_path_reuse_does_not_recompute_transitions`
- **D10.** No win-rate, hit-ratio or expectancy field exists. → `T4 test_path_carries_no_win_rate_or_hit_ratio`
- **D11.** Consumed states are not reopened by the API. → `T4 test_path_reports_consumed_states`
- **D12.** A rekey appears as an explicit remap, not a touch. → `T4 test_path_transition_summary_is_ordered`
- **D13.** Range-left conditioned on historical frequency keeps its
  provenance and cannot be restated as current performance. → `T4 test_path_reports_range_left`
- **D14.** Layer of each path element is explicit (L3/L2/L1). → `T4 test_path_terminal_does_not_erase_path`

## E. Setup-context service (Ch III.6.5)

- **E1.** Setup context consumes `evaluate_setup` verbatim; it applies no
  second eligibility rule. → `T5 test_setup_context_consumes_iii5_evaluation`
- **E2.** The four-valued verdict is preserved exactly. → `T5 test_setup_context_preserves_four_valued_eligibility`
- **E3.** The API can never raise `WATCH`/`BLOCKED`/`UNRESOLVED` to
  `ELIGIBLE`. → `T5 test_setup_context_never_elevates_eligibility`
- **E4.** The canonical setup payload is returned with its verbatim
  identity, version, class and exposure. → `T5 test_setup_context_exposes_canonical_setup_payload`
- **E5.** Book II policy is evaluated **before** the setup payload is
  composed. → `T5 test_setup_context_policy_checked_before_composition`
- **E6.** A denied request returns no setup fields at all. → `T5 test_setup_context_denied_returns_no_setup_fields`
- **E7.** XAU keeps its `WATCH` ceiling when parameters are declared. → `T5 test_setup_context_xau_caps_at_watch`
- **E8.** Fib remains `RESEARCH_ONLY`; a production request is refused. → `T5 test_setup_context_fib_stays_research_only`
- **E9.** JPY remains `MANUAL_OPERATOR`; automation is refused. → `T5 test_setup_context_jpy_stays_manual_operator`
- **E10.** An active stand-down lock is preserved in the served context. → `T5 test_setup_context_lock_preserved`
- **E11.** `automation_permitted` is `False` registry-wide and cannot be
  set by request. → `T5 test_setup_context_automation_false_registry_wide`
- **E12.** An unresolvable setup identity yields no record and an explicit
  `UNRESOLVED` context. → `T5 test_setup_context_unresolved_identity_returns_no_record`
- **E13.** Reasons are bounded codes, never prose. → `T5 test_setup_context_reasons_are_bounded_codes`
- **E14.** A card that fails the Book I machine schema is served with an
  explicit `SCHEMA_INCOMPATIBLE` qualification, not coerced. → `T5 test_setup_context_schema_incompatible_card_refused`
- **E15.** Eligibility is not automation authority in the payload: separate
  fields, separate meanings. → `T5 test_setup_context_automation_false_registry_wide`
- **E16.** No-go references travel with the setup context. → `T5 test_setup_context_lock_preserved`
- **E17.** Trigger/invalidation/target fields are typed, not prose. → `T5 test_setup_context_reasons_are_bounded_codes`
- **E18.** The setup context carries evidence references with status. → `T5 test_setup_context_exposes_canonical_setup_payload`

## F. Evidence link service (Ch III.6.6)

- **F1.** Evidence linking returns IDs and status only. → `T6 test_evidence_links_return_ids_only`
- **F2.** Status is carried verbatim from the frozen vocabulary. → `T6 test_evidence_links_carry_status`
- **F3.** The endpoint never embeds the corpus or full evidence bodies. → `T6 test_evidence_links_do_not_embed_corpus`
- **F4.** Negative and `NO_GO` evidence remain queryable. → `T6 test_evidence_links_preserve_negative_evidence`
- **F5.** A numerical claim without a claim/evidence identity is not served
  as a claim. → `T6 test_evidence_links_require_claim_for_numeric_claim`
- **F6.** An unsupported statistic is refused rather than attached. → `T6 test_evidence_links_refuse_unsupported_statistic`
- **F7.** Historical evidence is labelled `HISTORICAL` and never becomes a
  current performance claim. → `T6 test_evidence_links_historical_not_current`
- **F8.** Evidence links are exposure-filtered before release. → `T6 test_evidence_links_exposure_filtered`
- **F9.** `RESEARCH_LAB` evidence is served as research even when
  authorized. → `T6 test_evidence_links_exposure_filtered`
- **F10.** Missing evidence is explicit, not an empty list that implies
  "no evidence exists". → `T6 test_evidence_links_return_ids_only`
- **F11.** Claim → evidence → source chains are reported with their
  resolution status. → `T6 test_evidence_links_carry_status`
- **F12.** Evidence identifiers cannot be used to enumerate restricted
  objects. → `T6 test_evidence_links_do_not_embed_corpus`

## G. Historical snapshot / replay (Ch III.6.7)

- **G1.** A historical request must pin model version and data cutoff. → `T7 test_historical_request_requires_pinned_version`
- **G2.** An unknown historical version is refused. → `T7 test_historical_unknown_version_refused`
- **G3.** `latest` is never substituted for an explicit version. → `T7 test_historical_never_substitutes_latest`
- **G4.** If exact reconstruction is unavailable, the response says
  `HISTORICAL_UNAVAILABLE`. → `T7 test_historical_unavailable_is_explicit`
- **G5.** Reconstruction from retained inputs reproduces the original
  `snapshot_hash`. → `T7 test_historical_reconstruction_matches_original_hash`
- **G6.** Reconstruction is deterministic across runs. → `T7 test_historical_reconstruction_deterministic`
- **G7.** Replay uses the pinned rules, not current ones. → `T7 test_historical_replay_uses_pinned_rules`
- **G8.** A mixed-generation request (v1 model, v2 rules) is refused. → `T7 test_historical_mixed_generation_refused`
- **G9.** Current and historical are explicit, distinguishable states in the
  payload. → `T7 test_historical_distinguishes_current_from_historical`
- **G10.** No silent recomputation under current rules. → `T7 test_historical_no_current_rules_silently`
- **G11.** A broken lineage chain is reported, not patched. → `T7 test_historical_lineage_break_reported`
- **G12.** Data outside retention is reported as unavailable, with the
  retention boundary. → `T7 test_historical_out_of_retention_explicit`
- **G13.** Historical responses carry the same schema version discipline as
  current ones. → `T7 test_historical_reconstruction_deterministic`
- **G14.** Historical replay exposes no performance claim. → `T7 test_historical_distinguishes_current_from_historical`
- **G15.** A historical request for another principal's private payload is
  refused by policy. → `T7 test_historical_unknown_version_refused`
- **G16.** Unavailability never degrades into an empty success payload. → `T7 test_historical_unavailable_is_explicit`

## H. Multi-model instrument view (Ch III.6.8)

- **H1.** The view composes up to three layers (L3/L2/L1) as separate
  sections. → `T8 test_multimodel_composes_three_layers`
- **H2.** Layer ownership is preserved per section. → `T8 test_multimodel_preserves_layer_ownership`
- **H3.** No monolithic confluence score exists. → `T8 test_multimodel_has_no_confluence_score`
- **H4.** L3 destination, L2 path and L1 entry stay distinct. → `T8 test_multimodel_l3_destination_not_l2_path`
- **H5.** Layer conflict is reported as facts, not resolved by averaging. → `T8 test_multimodel_conflict_reported_as_facts`
- **H6.** A missing layer is explicit and does not invalidate the others. → `T8 test_multimodel_missing_layer_is_explicit`
- **H7.** Cross-asset calibration leakage is refused. → `T8 test_multimodel_cross_asset_leak_refused`
- **H8.** Section order is canonical (L3, L2, L1), not request order. → `T8 test_multimodel_order_is_canonical`
- **H9.** Each layer section references its own snapshot; composition does
  not merge snapshots. → `T8 test_multimodel_reuses_single_layer_snapshot`
- **H10.** Model states are never merged across layers. → `T8 test_multimodel_does_not_merge_states`
- **H11.** The view reports its own identity and hash over component
  snapshot ids. → `T8 test_multimodel_composes_three_layers`
- **H12.** A view request naming a non-layer model is refused. → `T8 test_multimodel_missing_layer_is_explicit`
- **H13.** The view does not create a synthetic "overall bias". → `T8 test_multimodel_has_no_confluence_score`
- **H14.** Unresolved higher-layer checkpoint is reported, not filled. → `T8 test_multimodel_conflict_reported_as_facts`

## I. Basket view (Ch III.6.9)

- **I1.** The basket payload reports per-pair roles verbatim. → `T9 test_basket_roles_verbatim`
- **I2.** No average score, net bias or aggregate confidence exists. → `T9 test_basket_has_no_average_score`
- **I3.** EURJPY is confirmation/veto only, never an equal vote. → `T9 test_basket_eurjpy_is_confirmation_only`
- **I4.** Equal-vote aggregation is impossible by construction. → `T9 test_basket_equal_vote_impossible`
- **I5.** A no-go native tier on one pair is reported for that pair. → `T9 test_basket_no_go_pair_reported`
- **I6.** A missing pair is explicit, not silently omitted. → `T9 test_basket_missing_pair_is_explicit`
- **I7.** Each pair carries its own layer/role ownership. → `T9 test_basket_reports_role_per_pair`
- **I8.** Basket exposure filtering is applied per pair before release. → `T9 test_basket_exposure_filters_roles`
- **I9.** The basket view cannot be flattened by a client-requested
  `flatten` flag. → `T9 test_basket_has_no_average_score`
- **I10.** Basket composition does not create a setup or eligibility. → `T9 test_basket_no_go_pair_reported`
- **I11.** Basket identity and hash are deterministic over pair snapshots. → `T9 test_basket_reports_role_per_pair`
- **I12.** No basket-level probability or expectancy field. → `T9 test_basket_has_no_average_score`

## J. Response schemas (Ch III.6.10)

- **J1.** Every response carries `schema_version`. → `T10 test_response_schema_version_stamped`
- **J2.** Every response carries `model_version` (or an explicit
  multi-model map). → `T10 test_response_model_version_stamped`
- **J3.** The envelope shape is frozen and identical across surfaces. → `T10 test_response_envelope_shape_frozen`
- **J4.** Serialisation is canonical JSON (sorted, compact, UTF-8). → `T10 test_response_json_is_canonical`
- **J5.** Prices are strings/`Decimal`; floats are refused. → `T10 test_response_no_nan_or_float_price`
- **J6.** Unknown request fields are refused, not ignored. → `T10 test_response_unknown_field_refused`
- **J7.** Errors use the existing FORGE service envelope and codes. → `T10 test_response_error_envelope_matches_service`
- **J8.** Refusal codes are a closed vocabulary; an unlisted code cannot be
  emitted. → `T10 test_response_refusal_code_is_closed`
- **J9.** A schema hash is recorded so consumers can detect drift. → `T10 test_response_schema_hash_recorded`
- **J10.** Field removal requires a new schema version (declared policy). → `T10 test_response_deprecated_field_policy_declared`
- **J11.** Content type and encoding are explicit and stable. → `T10 test_response_content_type_is_json`
- **J12.** Collections are ordered deterministically, never dict-iteration
  order. → `T10 test_response_json_is_canonical`
- **J13.** `null` and `UNAVAILABLE` mean different things and are not
  conflated. → `T10 test_response_envelope_shape_frozen`
- **J14.** No field name carries rhetorical determinism. → `T10 test_response_schema_version_stamped`
- **J15.** Response size is bounded; large histories are paginated or
  refused. → `T10 test_response_pagination_absent_or_bounded`
- **J16.** The schema is version-pinned per snapshot, not per deploy. → `T10 test_response_schema_hash_recorded`

## K. Caching (Ch III.6.11)

- **K1.** The cache key is the snapshot identity, not a URL or principal. → `T11 test_cache_keyed_by_snapshot_identity`
- **K2.** A new final bar invalidates the entry. → `T11 test_cache_invalidated_on_new_final_bar`
- **K3.** A model version change invalidates the entry. → `T11 test_cache_invalidated_on_model_version_change`
- **K4.** A calibration change invalidates the entry. → `T11 test_cache_invalidated_on_calibration_change`
- **K5.** Corrected/revised data invalidates the entry. → `T11 test_cache_invalidated_on_corrected_data`
- **K6.** An exposure/entitlement change invalidates filtered views. → `T11 test_cache_invalidated_on_exposure_change`
- **K7.** Cache entries never cross principals. → `T11 test_cache_never_crosses_principals`
- **K8.** A cache hit is served only after a fresh policy decision. → `T11 test_cache_hit_still_requires_policy_decision`
- **K9.** A stale entry is never presented as current. → `T11 test_cache_never_serves_stale_as_current`
- **K10.** A miss recomposes deterministically to the same hash. → `T11 test_cache_miss_recomposes_deterministically`
- **K11.** A denied request does not populate or read the response cache. → `T11 test_cache_denied_entry_not_returned`
- **K12.** No cache path can grant access a fresh decision would deny. → `T11 test_cache_does_not_grant_access`
- **K13.** The composition cache (internal) and response cache (per
  principal) are separate tiers. → `T11 test_cache_never_crosses_principals`
- **K14.** Cache entries record the policy fingerprint they were built
  under. → `T11 test_cache_invalidated_on_exposure_change`
- **K15.** Cache eviction is deterministic and bounded. → `T11 test_cache_keyed_by_snapshot_identity`
- **K16.** A cache hit and a cold composition return byte-identical
  payloads. → `T11 test_cache_miss_recomposes_deterministically`

## L. Security and observability (Ch III.6.12)

- **L1.** Authentication/principal comes from II.3; the API creates none. → `T12 test_security_uses_book_ii_principal`
- **L2.** Policy runs before composition (deny-before-load). → `T12 test_security_deny_before_composition`
- **L3.** Internal feature engineering is never exposed. → `T12 test_security_no_internal_feature_exposure`
- **L4.** Source code and internal module paths are never exposed. → `T12 test_security_no_source_code_exposure`
- **L5.** Denials are content-free and uniform. → `T12 test_security_denial_is_content_free`
- **L6.** Denials do not reveal object existence or restricted ids. → `T12 test_security_denial_does_not_leak_ids`
- **L7.** Every decision produces a content-free audit record. → `T12 test_security_audit_record_per_decision`
- **L8.** Audit records carry no payload, token or evidence body. → `T12 test_security_audit_has_no_payload`
- **L9.** Correlation/request ids propagate through snapshot and audit. → `T12 test_security_correlation_id_propagated`
- **L10.** Rate limiting is not authorization and cannot widen access. → `T12 test_security_rate_limit_not_authorization`
- **L11.** Error messages never echo tokens, ids or payload fragments. → `T12 test_security_error_never_echoes_token`
- **L12.** `INTERNAL_METHOD`/`INTERNAL_CODE` require the internal atom. → `T12 test_security_internal_exposure_only_forge_internal`
- **L13.** Research-authorized views keep research status. → `T12 test_security_research_view_keeps_research_status`
- **L14.** `OPERATOR_ONLY` content is not served publicly. → `T12 test_security_operator_only_not_public`
- **L15.** Metrics are bounded counters with no payload labels. → `T12 test_security_observability_metrics_bounded`
- **L16.** Telemetry never blocks or degrades serving. → `T12 test_security_telemetry_never_blocks_serving`
- **L17.** Audit trail is bounded and deterministic under load. → `T12 test_security_audit_record_per_decision`
- **L18.** A policy-engine failure denies (fail-closed). → `T12 test_security_deny_before_composition`

## M. Acceptance III.6 (frozen clause set, verbatim drivers)

- **M1.** Same snapshot identity returns a deterministic payload. → `T13 test_acceptance_same_identity_deterministic_payload`
- **M2.** Current/historical distinction is explicit. → `T13 test_acceptance_current_historical_distinct`
- **M3.** L3/L2/L1 composition preserves layer ownership. → `T13 test_acceptance_layer_composition_preserves_ownership`
- **M4.** Evidence/status accompanies statistical or model claims. → `T13 test_acceptance_claims_carry_evidence_status`
- **M5.** Policy filters protected outputs. → `T13 test_acceptance_policy_filters_protected_outputs`
- **M6.** No monolithic confidence score appears unless a future canonical
  model explicitly defines one. → `T13 test_acceptance_no_monolithic_confidence_score`

## N. Cross-model invariants (#1–#18)

- **N1.** Data clock is part of model identity. → `T13 test_inv_clock_part_of_identity`
- **N2.** Asset calibration is local unless transfer is validated. → `T13 test_inv_asset_calibration_local`
- **N3.** Range/anchor must exist before coordinates. → `T13 test_inv_anchor_before_coordinates`
- **N4.** Tier is a compression, not a causal force. → `T13 test_inv_tier_not_causal`
- **N5.** Time ages state; time alone does not call the play. → `T13 test_inv_time_ages_not_calls`
- **N6.** Touch ≠ acceptance. → `T13 test_inv_touch_not_acceptance`
- **N7.** Reach ≠ trade win. → `T13 test_inv_reach_not_win`
- **N8.** First delivery/path can matter more than terminal reach. → `T13 test_inv_first_delivery_preserved`
- **N9.** Rekey is a remapping transition. → `T13 test_inv_rekey_is_remap`
- **N10.** Range-left updates after states are consumed. → `T13 test_inv_range_left_after_consumption`
- **N11.** L3 destination ≠ L2 path ≠ L1 entry. → `T13 test_inv_layer_destination_path_entry`
- **N12.** Model state ≠ setup. → `T13 test_inv_model_state_not_setup`
- **N13.** Setup ≠ automation approval. → `T13 test_inv_setup_not_automation`
- **N14.** Manual validity can coexist with failed automation parity. → `T13 test_inv_manual_coexists_with_failed_parity`
- **N15.** Negative evidence remains queryable. → `T13 test_inv_negative_evidence_queryable`
- **N16.** Historical high-performance claims are never silently current. → `T13 test_inv_historical_not_current_performance`
- **N17.** News is a conditioner, not a geometry replacement. → `T13 test_inv_news_is_conditioner`
- **N18.** No deterministic rhetoric in status labels. → `T13 test_inv_no_deterministic_rhetoric`

## O. Canonical schema discontinuity and authority (mandatory review §2)

- **O1.** The three Book I validation failures are reproduced at the
  planning head and recorded. → `T13 test_card_schema_defect_reproduced`
- **O2.** The API does not silently coerce `SETUP.*` ids into another form. → `T13 test_card_schema_defect_not_silently_coerced`
- **O3.** Served setup identity is the corpus identity, verbatim. → `T13 test_card_identity_served_verbatim`
- **O4.** Served card status is verbatim; no promotion on projection. → `T13 test_card_status_served_verbatim`
- **O5.** A `SCHEMA_INCOMPATIBLE` governed refusal exists for operations that
  require a machine-valid card. → `T13 test_card_schema_incompatible_refusal_code`
- **O6.** No downstream status promotion occurs anywhere in the projection. → `T13 test_card_no_status_promotion_in_projection`
- **O7.** No identifier renaming occurs (no synthesised `SET.*`). → `T13 test_card_no_id_renaming`
- **O8.** Exposure metadata comes from Book I only. → `T13 test_exposure_metadata_from_book_i_only`
- **O9.** Policy decisions come from Book II only. → `T13 test_policy_decision_from_book_ii_only`
- **O10.** Setup eligibility comes from III.5 only. → `T13 test_eligibility_from_iii5_only`
- **O11.** The API invents no authority of any kind. → `T13 test_api_invents_no_authority`
- **O12.** Unknown exposure denies by default. → `T13 test_api_refuses_unknown_exposure`
- **O13.** Unknown action/route denies by default. → `T13 test_api_never_default_allows`
- **O14.** The schema incompatibility is a launch/integration risk in the
  register, not a closed item. → `T13 test_api_schema_incompatible_is_governed_refusal`
- **O15.** A Book I repair requires a separate ADR + operator authorization. → `T13 test_api_adr_required_before_repair`
- **O16.** This packet mutates no Book I file or schema. → `T13 test_api_no_book_i_mutation`

## P. Freshness, quality and version semantics

- **P1.** With no market provider, the service refuses live intelligence
  with `PROVIDER_NOT_CONFIGURED`. → `T13 test_provider_not_configured_refusal`
- **P2.** No response claims live data while the provider seam is
  `NOT_CONFIGURED`. → `T13 test_no_live_claim_without_provider`
- **P3.** A nonfinal bar blocks the snapshot. → `T13 test_nonfinal_bar_refused`
- **P4.** Stale input is labelled `STALE` with its cutoff. → `T13 test_stale_input_labelled`
- **P5.** Bad-quality source data is refused with the frozen quality code. → `T13 test_bad_quality_refused`
- **P6.** Unresolved clock/session yields `NO_CALCULATION`. → `T13 test_clock_unresolved_no_calculation`
- **P7.** Mixed component cutoffs are refused rather than reconciled
  silently. → `T13 test_mixed_cutoff_refused`
- **P8.** Any staleness threshold must come from a versioned policy. → `T13 test_staleness_policy_versioned_only`
- **P9.** No staleness threshold is invented in this Bloc. → `T13 test_no_invented_staleness_threshold`
- **P10.** Quality vocabulary is the frozen III.1 set. → `T13 test_quality_vocabulary_verbatim`
- **P11.** Version drift between request, snapshot and components is
  refused. → `T13 test_version_drift_refused`
- **P12.** Unknown versions fail closed. → `T13 test_unknown_version_fail_closed`
- **P13.** Non-retained history is explicit. → `T13 test_history_not_retained_is_explicit`
- **P14.** Degraded state is reported, never masked. → `T13 test_degraded_state_reported_not_hidden`
- **P15.** "Data unavailable" and "market no-go" are different outcomes. → `T13 test_data_unavailable_distinct_from_no_go`
- **P16.** Source-window digests are preserved in the payload. → `T13 test_source_window_digest_preserved`

## Q. Adversarial matrix (16 classes)

- **Q1.** Arbitrary `as_of` value cannot select a favourable past state. → `T13 test_adv_request_arbitrary_as_of`
- **Q2.** A foreign instrument id is refused. → `T13 test_adv_request_foreign_instrument`
- **Q3.** Hidden layer substitution (L2 payload labelled L1) is refused. → `T13 test_adv_request_hidden_layer_substitution`
- **Q4.** Setup eligibility cannot be requested as execution authorization. → `T13 test_adv_request_setup_as_authorization`
- **Q5.** Research content cannot be requested as production. → `T13 test_adv_request_research_as_production`
- **Q6.** Manual content cannot be requested as automation. → `T13 test_adv_request_manual_as_automation`
- **Q7.** Stale data cannot be requested as current. → `T13 test_adv_request_stale_as_current`
- **Q8.** Missing components cannot be padded to look complete. → `T13 test_adv_request_partial_payload_fabrication`
- **Q9.** A score request is refused. → `T13 test_adv_request_score_request_refused`
- **Q10.** A probability request is refused. → `T13 test_adv_request_probability_request_refused`
- **Q11.** An order/size request is refused. → `T13 test_adv_request_order_request_refused`
- **Q12.** Another principal's snapshot id is refused. → `T13 test_adv_request_other_users_snapshot`
- **Q13.** Error text cannot be used to probe protected content. → `T13 test_adv_request_error_message_probing`
- **Q14.** Cache poisoning via crafted keys is refused. → `T13 test_adv_request_cache_poisoning`
- **Q15.** Version confusion (same id, mixed versions) is refused. → `T13 test_adv_request_version_confusion`
- **Q16.** Basket flattening into one score is refused. → `T13 test_adv_request_basket_flattening`

## R. Boundaries and purity

- **R1.** No upstream calculation is duplicated. → `T14 test_boundary_no_upstream_recalculation`
- **R2.** Layout/geometry is not recomputed. → `T14 test_boundary_no_duplicate_geometry`
- **R3.** Eligibility is not recomputed. → `T14 test_boundary_no_duplicate_eligibility`
- **R4.** Authorization is not recomputed. → `T14 test_boundary_no_duplicate_policy`
- **R5.** No provider or network import in the composition path. → `T14 test_boundary_no_provider_import`
- **R6.** No socket/network access. → `T14 test_boundary_no_network`
- **R7.** No wall-clock read inside composition. → `T14 test_boundary_no_wall_clock_in_composition`
- **R8.** No filesystem writes. → `T14 test_boundary_no_filesystem_write`
- **R9.** No persistence or migration is created by this Bloc. → `T14 test_boundary_no_persistence_migration`
- **R10.** Domain modules do not import the service framework. → `T14 test_boundary_no_service_framework_in_domain`
- **R11.** Import direction is one-way from `intelligence_api` to the five
  ratified packages. → `T14 test_boundary_import_direction_one_way`
- **R12.** Snapshots are immutable after serving. → `T14 test_boundary_snapshot_immutable_after_serve`
- **R13.** No global mutable state. → `T14 test_boundary_no_global_mutable_state`
- **R14.** Frozen upstream hashes are unchanged by this Bloc. → `T14 test_boundary_frozen_upstream_hashes_unchanged`

## S. Gap and governance discipline

- **S1.** The carried gap register is complete and dispositioned. → `T14 test_gap_register_complete`
- **S2.** XAU quarter mapping and ladder invalidation remain open. → `T14 test_gap_xau_mapping_open`
- **S3.** Fib R15 remains unresolved. → `T14 test_gap_fib_r15_open`
- **S4.** JPY automated parity remains unapproved. → `T14 test_gap_jpy_parity_open`
- **S5.** BTC weekly/monthly anchor definitions remain unresolved. → `T14 test_gap_btc_anchor_open`
- **S6.** Market-data provider remains `NOT_CONFIGURED`. → `T14 test_gap_provider_not_configured`
- **S7.** Durable transition/setup history remains undecided. → `T14 test_gap_history_storage_undecided`
- **S8.** Research/backtest figures cannot become live performance claims. → `T14 test_gap_performance_claims_bound`
- **S9.** No gap closes because a DTO can represent its absence. → `T14 test_gap_no_gap_closed_by_dto`
- **S10.** III.5-DEFECT-1/REC-1/REC-2 are carried, not closed. → `T14 test_gap_iii5_defect_carried`
- **S11.** All upstream gap registers are carried with dispositions. → `T14 test_gap_carried_upstream_registers`
- **S12.** Refusal and reason vocabularies are closed and bounded. → `T14 test_gap_refusal_codes_bounded`
- **S13.** This planning rung creates no API, fixture, test or migration. → `T14 test_gap_planner_no_implementation`
- **S14.** No new migration is authorized by this packet. → `T14 test_gap_no_new_migration_authorized`

## T. Book III final integration gate

- **T1.** Observation → measurement → model → transition → setup →
  snapshot integrity is demonstrated end-to-end. → `T14 test_final_observation_to_snapshot_integrity`
- **T2.** Policy-aware exposure is demonstrated on the composed snapshot. → `T14 test_final_policy_aware_exposure`
- **T3.** Cross-model coherence is demonstrated (EUR L3/L2/L1, XAU, JPY). → `T14 test_final_cross_model_coherence`
- **T4.** Replay consistency is demonstrated. → `T14 test_final_replay_consistency`
- **T5.** Data-quality behaviour is demonstrated. → `T14 test_final_data_quality_behavior`
- **T6.** Provider-not-configured behaviour is demonstrated. → `T14 test_final_provider_not_configured_behavior`
- **T7.** Setup/no-go preservation is demonstrated end-to-end. → `T14 test_final_setup_no_go_preservation`
- **T8.** Consumer contract compatibility (Book IV/V handoff) is
  demonstrated. → `T14 test_final_consumer_contract_compatibility`
- **T9.** No production GO is claimed by this packet. → `T14 test_final_no_production_go_claim`
- **T10.** Book III ratification requires all six Blocs at PASS/CLOSED. → `T14 test_final_ratification_requires_all_six_blocs`
- **T11.** The final evidence pack is required and enumerated. → `T14 test_final_evidence_pack_required`
- **T12.** The version registry (data/clock/session/measurement/runtime/
  state/setup) is recorded. → `T14 test_final_version_registry_recorded`
- **T13.** Test counts and fixture hashes are recorded in the final record. → `T14 test_final_test_counts_recorded`
- **T14.** Deployment-readiness limitations are disclosed. → `T14 test_final_deployment_limitations_disclosed`

---

## Test group index

| Group | Scope | Tests |
|---|---|---|
| T1 | snapshot identity/composition (§A) | 20 |
| T2 | current state (§B) | 12 |
| T3 | levels (§C) | 10 |
| T4 | path (§D) | 10 |
| T5 | setup context (§E) | 14 |
| T6 | evidence links (§F) | 8 |
| T7 | history (§G) | 12 |
| T8 | multi-model (§H) | 10 |
| T9 | basket (§I) | 8 |
| T10 | response schemas (§J) | 12 |
| T11 | caching (§K) | 12 |
| T12 | security/observability (§L) | 16 |
| T13 | acceptance/invariants/schema/freshness/adversarial (§M–§Q) | 72 |
| T14 | boundaries/gaps/final gate (§R–§T) | 42 |
| **Total** | | **258** |

Proposed suite path: `tests/test_forge_intelligence_api.py`.

## What this contract does NOT authorize

Implementation of the API, fixtures, tests, migrations, provider adapters,
cache storage, network wiring, Book IV/V work, or any Book I schema repair.
Rung 2 requires its own authorization.
