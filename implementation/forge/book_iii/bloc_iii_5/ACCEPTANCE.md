# BOOK III / BLOC III.5 — OPERATOR SETUP ENGINE — ACCEPTANCE.md

**Bloc:** III.5 · **Authority:** BA-21 Rung 1 (planning only)
**Planning head:** `825c24075249f631043b4cc36f479bffeef86532`
**Status:** FROZEN ACCEPTANCE CONTRACT — authoritative on clause ids,
test names and counts. `PLAN.md` describes intent; **this file binds the
future implementation**. Names may be **added** at implementation; none
may be deleted, weakened, skipped or xfailed.

**Clause count:** 250 across sections A–S. **Test count:** 162 across
groups T1–T12 (§T). Every clause names at least one driver.

**Core law under test:** a valid model state is not a valid setup; a
valid setup is not automation approval; a refusal is a recorded result.

---

## A. Common setup contract (Ch III.5 common contract)

- **A1.** A setup record is immutable after construction; every mutation
  attempt raises rather than silently rebinding. → `T1 test_setup_record_is_immutable`
- **A2.** A setup id must be a resolvable canonical `SET.*` identity; a
  synthesised or unknown id never yields a record. → `T1 test_setup_record_requires_canonical_id`
- **A3.** Every record carries `setup_contract_version` and the engine
  version; an unknown version fails closed. → `T1 test_setup_contract_version_stamped`
- **A4.** The exact frozen field set exists — id/version, execution class,
  eligibility, side, location, trigger requirement, three invalidations,
  ordered targets, promotion conditions, no-go refs, parent states,
  transition refs, evidence refs, manual status, automation flag,
  explanation facts. → `T1 test_setup_record_field_set_is_frozen`
- **A5.** A record field cannot carry free prose: any free-text payload is
  refused; explanation is structured facts only. → `T1 test_setup_record_rejects_free_text_field`
- **A6.** Eligibility is exactly `ELIGIBLE`, `WATCH`, `BLOCKED`,
  `UNRESOLVED` — no fifth value, no "strong/weak" variant. → `T2 test_eligibility_vocabulary_is_four`
- **A7.** A `WATCH` or `BLOCKED`/`UNRESOLVED` record carries at least one
  bounded reason code; `ELIGIBLE` without passing gates is impossible. → `T2 test_eligible_requires_every_gate`
- **A8.** Side is either a typed direction where the card declares one, or
  an explicit `NONE_DECLARED` form — never inferred from model state. → `T3 test_trigger_requirement_is_declared_not_inferred`
- **A9.** Location is a typed level/zone reference from III.2/III.3 or an
  explicit `UNRESOLVED`; a bare number is refused. → `T1 test_setup_record_field_set_is_frozen`
- **A10.** Each record carries its evidence refs **with status**; a bare
  numeric result is not a field. → `T10 test_evidence_refs_carry_status`
- **A11.** `manual_status` is a projection of the card execution class and
  can never exceed it. → `T1 test_registry_carries_execution_class_verbatim`
- **A12.** `automation_permitted` is `False` unless every automation gate
  passes; at this head it is `False` for the entire registry. → `T9 test_p90_automation_permitted_false_everywhere`
- **A13.** The record carries parent model id/version/state/layer/snapshot
  hash and transition refs verbatim, never a recomputation. → `T2 test_missing_parent_state_is_unresolved`
- **A14.** A record can be serialised canonically and re-read to an equal
  value with an identical `evaluation_hash`. → `T12 test_evaluation_hash_deterministic`

## B. Setup registry (Ch III.5.1)

- **B1.** Only canonically loaded cards enter the registry; a card not
  parsed by the canonical loader is absent, not guessed. → `T1 test_registry_loads_only_canonical_cards`
- **B2.** An unknown setup id resolves to `UNRESOLVED`, never to a default
  or a nearest match. → `T1 test_registry_refuses_unknown_setup_id`
- **B3.** Execution class is carried verbatim from the card. → `T1 test_registry_carries_execution_class_verbatim`
- **B4.** Card status is carried verbatim; no upward status normalisation. → `T1 test_registry_carries_status_verbatim`
- **B5.** A quarantined/unvalidated card cannot be served on a production
  or operator surface. → `T1 test_registry_refuses_quarantined_card`
- **B6.** A `PARKED` card is refused (`PARKED` ≠ "eligible later"). → `T1 test_registry_refuses_parked_card`
- **B7.** An `IMPLEMENTATION_NOT_PARITY_SAFE` card is refused. → `T1 test_registry_refuses_parity_unsafe_card`
- **B8.** Version resolution is explicit; the requested version must exist. → `T1 test_registry_resolves_explicit_version`
- **B9.** "Latest" is never implicit; without a version policy the request
  refuses. → `T1 test_registry_never_latest_without_policy`
- **B10.** Exactly three canonical setup cards are exposed at this head. → `T1 test_registry_exposes_three_canonical_cards`
- **B11.** No card in the registry is `AUTOMATION_APPROVED`. → `T1 test_registry_has_no_automation_approved_card`
- **B12.** A research-only card is present but can only ever be served as
  research. → `T7 test_fib_card_is_research_only`
- **B13.** A manual-operator card is present and never emitted as an
  automated signal. → `T6 test_xau_no_automation_permission`
- **B14.** Registry lookup is pure and deterministic across runs. → `T12 test_registry_snapshot_is_deterministic`
- **B15.** The registry exposes the card's exposure verbatim for Book II
  policy. → `T1 test_registry_carries_status_verbatim`
- **B16.** No registry operation writes to the corpus or the ledger. → `T12 test_no_filesystem_or_clock_access`

## C. Eligibility engine (Ch III.5.2)

- **C1.** Precedence is total and documented: `BLOCKED` > `UNRESOLVED` >
  `WATCH` > `ELIGIBLE`. → `T2 test_eligibility_precedence_is_total`
- **C2.** `ELIGIBLE` requires every gate to pass affirmatively; one open
  gate prevents it. → `T2 test_eligible_requires_every_gate`
- **C3.** A missing parent model output yields `UNRESOLVED`. → `T2 test_missing_parent_state_is_unresolved`
- **C4.** A model version mismatch yields `UNRESOLVED`
  (`MODEL_VERSION_UNAVAILABLE`), never a silent recalculation. → `T2 test_model_version_mismatch_is_unresolved`
- **C5.** A parent on the wrong layer yields `BLOCKED`. → `T2 test_wrong_layer_parent_is_blocked`
- **C6.** A model state the card does not declare yields `BLOCKED`. → `T2 test_state_not_declared_by_card_is_blocked`
- **C7.** An unresolved/invalidated anchor blocks an anchor-dependent
  setup. → `T2 test_anchor_unresolved_blocks_fib`
- **C8.** An anchor whose rule is `DECLARED`/`NOT_MATERIALIZED` caps at
  `UNRESOLVED` — never `ELIGIBLE`. → `T2 test_anchor_declared_rule_caps_at_unresolved`
- **C9.** An asset-foreign tier yields `BLOCKED` (`TIER_NOT_NATIVE`). → `T2 test_cross_asset_tier_is_blocked`
- **C10.** A native no-go tier yields `BLOCKED`. → `T2 test_native_tier_no_go_is_blocked`
- **C11.** An unresolvable clock/session yields `UNRESOLVED`. → `T2 test_unresolved_clock_is_unresolved`
- **C12.** A resolved clock whose checkpoint is not yet reached yields
  `WATCH` (armed, not entered). → `T2 test_unreached_clock_checkpoint_is_watch`
- **C13.** A higher-layer no-go blocks the setup. → `T2 test_higher_layer_no_go_blocks_setup`
- **C14.** A higher/lower-layer conflict reports conflict facts and yields
  `BLOCKED` — never a confluence number. → `T2 test_higher_layer_conflict_reports_facts`
- **C15.** A nonfinal bar yields `BLOCKED` (`DATA_QUALITY_BLOCKED`). → `T2 test_nonfinal_bar_is_data_quality_blocked`
- **C16.** Stale or gapped data yields `BLOCKED`. → `T2 test_stale_data_is_data_quality_blocked`
- **C17.** A `DECLARED` (non-canonical) numeric parameter caps the verdict
  at `WATCH`. → `T2 test_declared_parameter_caps_at_watch`
- **C18.** The eligibility resolver is the single authority: no caller may
  set or override a verdict directly. → `T2 test_eligibility_precedence_is_total`

## D. Trigger semantics (Ch III.5.3)

- **D1.** The trigger vocabulary is exactly `TOUCH`, `EXCURSION`,
  `REJECTION`, `ACCEPTANCE`, `CLOSE`, `SR_FLIP`, `OCC`. → `T3 test_trigger_vocabulary_is_seven`
- **D2.** `TOUCH` satisfies only `TOUCH`. → `T3 test_touch_satisfies_only_touch`
- **D3.** A touch cannot satisfy a `CLOSE` requirement. → `T3 test_touch_cannot_satisfy_close`
- **D4.** A touch cannot satisfy an `ACCEPTANCE` requirement. → `T3 test_touch_cannot_satisfy_acceptance`
- **D5.** A touch cannot satisfy a `REJECTION` requirement. → `T3 test_touch_cannot_satisfy_rejection`
- **D6.** `CLOSE` requires a final bar close beyond the level; a nonfinal
  bar never satisfies it. → `T3 test_close_requires_final_bar`
- **D7.** `ACCEPTANCE` requires the III.4 acceptance state, not proximity. → `T3 test_acceptance_requires_state_not_proximity`
- **D8.** `REJECTION` requires excursion then return, in that order. → `T3 test_rejection_requires_excursion_then_return`
- **D9.** `SR_FLIP` requires a declared flip fact, not a retest. → `T3 test_sr_flip_requires_declared_flip`
- **D10.** `OCC` requires a declared occurrence fact. → `T3 test_occ_requires_declared_occurrence`
- **D11.** An `ALL` combination requires every literal to be satisfied. → `T3 test_all_combination_requires_every_literal`
- **D12.** An `ANY` combination requires at least one literal — and only
  the declared literals. → `T3 test_any_combination_requires_one_literal`
- **D13.** The requirement and its combination are declared by the card;
  they are never inferred from observations. → `T3 test_trigger_requirement_is_declared_not_inferred`
- **D14.** An unsatisfied requirement yields `WATCH`, never `ELIGIBLE`. → `T3 test_unsatisfied_trigger_yields_watch`

## E. Invalidation (Ch III.5.4)

- **E1.** Price, structural and temporal invalidation are three separate
  typed fields. → `T4 test_invalidation_trichotomy_is_separate`
- **E2.** A price invalidation never substitutes for a temporal expiry. → `T4 test_price_invalidation_never_substitutes_temporal`
- **E3.** A temporal invalidation never substitutes for a price level. → `T4 test_temporal_invalidation_never_substitutes_price`
- **E4.** Structural invalidation is a typed state/rule condition. → `T4 test_structural_invalidation_is_typed`
- **E5.** An absent invalidation kind is `UNRESOLVED`, not empty-success. → `T4 test_absent_invalidation_kind_is_unresolved`
- **E6.** An active price invalidation yields `BLOCKED`. → `T4 test_active_price_invalidation_blocks`
- **E7.** An active invalidation dominates a satisfied trigger. → `T4 test_invalidation_dominates_satisfied_trigger`
- **E8.** An uncanonicalised ladder invalidation is `DECLARED` and caps the
  verdict at `WATCH`. → `T4 test_unmaterialized_ladder_invalidation_is_declared`
- **E9.** Every invalidation carries a canonical source reference. → `T4 test_invalidation_requires_source_ref`
- **E10.** Invalidation values are decimals in native magnitude, never
  floats or bare numbers. → `T4 test_invalidation_payload_is_decimal`

## F. Targets and promotions (Ch III.5.5)

- **F1.** Target order is the canonical order; it is never sorted by price
  or by distance. → `T5 test_target_order_is_canonical_not_sorted`
- **F2.** A deeper coordinate is not automatically an active target. → `T5 test_deeper_coordinate_is_not_auto_active`
- **F3.** A target becomes active only through its declared promotion
  condition. → `T5 test_promotion_requires_declared_condition`
- **F4.** Promotion without authority refuses
  (`TARGET_PROMOTION_WITHOUT_AUTHORITY`). → `T5 test_target_promotion_without_authority_refuses`
- **F5.** Targets preserve III.4 first-delivery order. → `T5 test_targets_preserve_first_delivery_order`
- **F6.** Conditional range-left conditioning is preserved, not
  re-unconditionalised. → `T5 test_range_left_conditioning_preserved`
- **F7.** Small confirmation moves are evidence states, not core targets. → `T5 test_confirmation_state_is_not_core_target`
- **F8.** Each target carries a canonical source reference. → `T5 test_target_requires_source_ref`
- **F9.** Target order is stable across repeated evaluation. → `T5 test_target_order_stable_across_runs`
- **F10.** Promotion requires a transition/observation reference. → `T5 test_target_promotion_requires_transition_ref`
- **F11.** A promoted target keeps its original declared order. → `T5 test_promoted_target_keeps_prior_order`
- **F12.** A target not declared by the card cannot be invented. → `T5 test_target_cannot_be_invented`

## G. XAU Quarter-Zone operator (Ch III.5.6)

- **G1.** `SETUP.XAU.QUARTER_ZONE.V1` is `MANUAL_OPERATOR` and stays so. → `T6 test_xau_card_is_manual_operator`
- **G2.** After-03:00 NY context is required. → `T6 test_xau_requires_after_three_context`
- **G3.** A blind touch of the zone is `BLOCKED`. → `T6 test_xau_blind_touch_blocked`
- **G4.** Entry requires an excursion **into** the quarter zone. → `T6 test_xau_requires_excursion_into_zone`
- **G5.** Confirmation must be rejection, a 5-minute close outside the zone,
  or a declared S/R flip. → `T6 test_xau_requires_rejection_or_close_or_flip`
- **G6.** An L3 destination alone is not an L1 entry. → `T6 test_xau_l3_destination_only_blocked`
- **G7.** A parked/no-go context blocks the setup. → `T6 test_xau_parked_state_blocked`
- **G8.** An automatic `132→168` promotion is refused. → `T6 test_xau_forbidden_132_168_promotion_blocked`
- **G9.** While the quarter mapping is `DECLARED`, the verdict caps at
  `WATCH`. → `T6 test_xau_zone_mapping_declared_caps_at_watch`
- **G10.** While the ladder invalidation is `DECLARED`, the verdict caps at
  `WATCH`. → `T6 test_xau_invalidation_declared_caps_at_watch`
- **G11.** Next-quarter doctrine is the primary target, first in order. → `T6 test_xau_targets_next_quarter_first`
- **G12.** `$5`/`$10` moves are confirmation/evidence states, not core
  doctrine. → `T6 test_xau_small_moves_are_confirmation_states`
- **G13.** No automation approval is emitted for the XAU operator. → `T6 test_xau_no_automation_permission`
- **G14.** The card's evidence refs describe promotions and are never
  restated as setup win rate. → `T6 test_xau_evidence_refs_are_promotion_only`

## H. Fib Rekey operator (Ch III.5.7)

- **H1.** `SETUP.FIB.REKEY.V1` is `RESEARCH_ONLY`. → `T7 test_fib_card_is_research_only`
- **H2.** A production/operator request for a research-only card is
  `BLOCKED`. → `T7 test_fib_production_request_blocked`
- **H3.** A valid active A–B Range Birth is mandatory. → `T7 test_fib_requires_valid_born_range`
- **H4.** An unresolved anchor yields `UNRESOLVED` (R15 gate). → `T7 test_fib_unresolved_anchor_unresolved`
- **H5.** No generic-pivot fallback exists anywhere. → `T7 test_fib_no_generic_pivot_fallback`
- **H6.** 132% is the primary rekey location. → `T7 test_fib_132_is_primary_rekey`
- **H7.** 168% is historical dual-entry research, not a default. → `T7 test_fib_168_is_dual_entry_research`
- **H8.** The 50–72% family is kept separate from rekey entry. → `T7 test_fib_50_72_family_not_conflated`
- **H9.** R11 frequency/hit-rate is never transferred into R15. → `T7 test_fib_r11_frequency_not_transferred`
- **H10.** The 132/168/185 lineage is explainable as bounded facts. → `T7 test_fib_lineage_explainable`
- **H11.** No automated Fib signal is emitted. → `T7 test_fib_no_automated_signal`
- **H12.** The R11 over-generation evidence is attached as negative
  evidence. → `T7 test_fib_negative_evidence_attached`

## I. JPY Role-Gated operator (Ch III.5.8)

- **I1.** `SETUP.JPY.CARRY_ROLE_GATE.V1` is `MANUAL_OPERATOR`. → `T8 test_jpy_card_is_manual_operator`
- **I2.** The role map is consumed verbatim: USDJPY master, AUDJPY
  expression, EURJPY confirmation/veto. → `T8 test_jpy_role_map_is_verbatim`
- **I3.** USDJPY carry-master state must resolve. → `T8 test_jpy_requires_usdjpy_master`
- **I4.** AUDJPY risk/expression state must resolve. → `T8 test_jpy_requires_audjpy_expression`
- **I5.** EURJPY is confirmation/veto only. → `T8 test_jpy_eurjpy_is_confirmation_veto`
- **I6.** Confirmation is never an entry trigger. → `T8 test_jpy_confirmation_is_not_entry`
- **I7.** Equal-vote majority is impossible by construction. → `T8 test_jpy_equal_vote_impossible`
- **I8.** The executed pair must have its own native tier. → `T8 test_jpy_pair_native_tier_required`
- **I9.** A pair in native-tier no-go is `BLOCKED`. → `T8 test_jpy_pair_no_go_blocked`
- **I10.** The local setup comes from the selected pair's L1 geometry. → `T8 test_jpy_local_setup_from_selected_pair`
- **I11.** No basket confidence/aggregate score field exists. → `T8 test_jpy_no_basket_confidence_field`
- **I12.** No automation approval is emitted while parity is unapproved. → `T8 test_jpy_no_automation_permission`
- **I13.** Historical 12-4 DT geometry is not auto-imported. → `T8 test_jpy_historical_dt_not_imported`
- **I14.** Basket role agreement (115/168, 103/115) is a state
  relationship, never a win rate. → `T8 test_jpy_relationship_not_win_rate`

## J. Historical/manual ST + P90 lineage (Ch III.5.9, Ch III.5.10)

- **J1.** ST/Tier→AU→Tier is a `MANUAL_HISTORICAL_FRAMEWORK`. → `T9 test_st_is_manual_historical_framework`
- **J2.** An ST automation request is `BLOCKED`. → `T9 test_st_automation_request_blocked`
- **J3.** The automation/perception gap is `UNRESOLVED`, disclosed. → `T9 test_st_perception_gap_unresolved`
- **J4.** The ST tier→AU→tier chain is explainable as facts. → `T9 test_st_tier_au_tier_explainable`
- **J5.** ST creates no `SET.*` identity (no card exists). → `T9 test_st_creates_no_setup_identity`
- **J6.** P90 lineage status is `UNVERIFIED` at this head. → `T9 test_p90_lineage_status_unverified`
- **J7.** P90 automation requires verified implementation parity. → `T9 test_p90_automation_requires_verification`
- **J8.** P90 requires an explicit version/implementation identity. → `T9 test_p90_requires_version_identity`
- **J9.** A historical P90 claim stays `HISTORICAL`. → `T9 test_p90_historical_claim_stays_historical`
- **J10.** A historical claim is never restated as current verified
  performance. → `T9 test_p90_no_current_performance_claim`
- **J11.** A lineage requires evidence refs with status. → `T9 test_p90_lineage_evidence_refs_required`
- **J12.** `automation_permitted` is `False` across the whole surface. → `T9 test_p90_automation_permitted_false_everywhere`

## K. Setup result vs setup statistics (Ch III.5.11)

- **K1.** The statistics surface exposes no numeric result type. → `T10 test_statistics_expose_no_numeric_result_type`
- **K2.** A statistic without a `CL.*` reference refuses
  (`UNSUPPORTED_STATISTIC`). → `T10 test_statistic_without_claim_ref_refuses`
- **K3.** A claim's population identity must match what is described. → `T10 test_claim_population_must_match`
- **K4.** Relationship evidence is labelled as a relationship. → `T10 test_relationship_evidence_labelled_as_relationship`
- **K5.** No win-rate field exists anywhere in the package. → `T10 test_no_win_rate_field_anywhere`
- **K6.** No expectancy or probability field exists. → `T10 test_no_expectancy_or_probability_field`
- **K7.** No risk/reward field exists. → `T10 test_no_risk_reward_field`
- **K8.** Every evidence reference carries its status. → `T10 test_evidence_refs_carry_status`
- **K9.** Unsupported statistics are refused by construction, not by
  convention. → `T10 test_unsupported_statistic_refused_by_construction`
- **K10.** A setup record payload contains no performance figure. → `T10 test_no_performance_payload_in_setup_record`

## L. Adversarial setup matrix (Ch III.5.12)

- **L1.** A level touched without the required rejection does not produce
  an entry (touch ≠ confirmation). → `T11 test_touch_without_rejection_refused`
- **L2.** A satisfied trigger under an active no-go lock stays `BLOCKED`. → `T11 test_valid_trigger_under_lock_blocked`
- **L3.** An L3 direction without L1 eligibility is refused. → `T11 test_l3_direction_without_l1_eligibility_blocked`
- **L4.** An unresolved R15 requested as production is refused. → `T11 test_unresolved_r15_requested_as_production_blocked`
- **L5.** A JPY equal-vote or automation request is refused. → `T11 test_jpy_equal_vote_request_blocked`
- **L6.** An ST automation request is refused; the manual framework
  exposes no automation path at all. → `T11 test_st_manual_framework_cannot_automate`
- **L7.** An unsupported P90 performance claim is refused. → `T11 test_unsupported_p90_claim_blocked`
- **L8.** Stale or nonfinal data cannot satisfy a setup. → `T11 test_stale_data_request_blocked`
- **L9.** A wrong asset tier is refused. → `T11 test_wrong_tier_request_blocked`
- **L10.** A parked XAU setup cannot be activated. → `T11 test_parked_xau_setup_blocked`
- **L11.** A missing Setup Card yields `UNRESOLVED`, never a synthesis. → `T11 test_missing_setup_card_unresolved`
- **L12.** Historical/current version drift is refused, not silently
  re-based. → `T11 test_version_drift_request_blocked`
- **L13.** An unauthorised target promotion is refused. → `T11 test_unauthorized_target_promotion_blocked`
- **L14.** An ambiguous intrabar first delivery cannot be resolved by
  assumption. → `T11 test_ambiguous_intrabar_first_delivery_blocked`
- **L15.** A model state serialised as a trade signal is refused. → `T11 test_model_state_serialized_as_signal_refused`
- **L16.** Refusals are recorded results with bounded codes, not raised
  exceptions escaping the caller. → `T11 test_refusals_are_recorded_not_raised`

## M. Acceptance III.5 (frozen clause set, verbatim drivers)

- **M1.** Model state alone cannot manufacture an entry. → `T2 test_eligible_requires_every_gate`
- **M2.** Every emitted production/operator setup maps to a canonical Setup
  Card. → `T1 test_registry_loads_only_canonical_cards`
- **M3.** Trigger, invalidation and target semantics are explicit and
  typed. → `T3 test_trigger_vocabulary_is_seven`
- **M4.** Manual / research / automation classification is preserved end to
  end. → `T1 test_registry_carries_execution_class_verbatim`
- **M5.** Unsupported win rate is never emitted. → `T10 test_no_win_rate_field_anywhere`
- **M6.** The four-way eligibility vocabulary is total and fail-closed. → `T2 test_eligibility_precedence_is_total`
- **M7.** A research-only setup cannot appear as a production signal. → `T7 test_fib_production_request_blocked`
- **M8.** The XAU blind-touch path is blocked and the JPY equal-vote path
  is impossible. → `T6 test_xau_blind_touch_blocked`

## N. Cross-model invariants (#1–#18) + governance invariants

- **N1.** Data clock is part of identity; a clock-less setup is
  `UNRESOLVED`. → `T2 test_unresolved_clock_is_unresolved`
- **N2.** Asset calibration is local; cross-asset reuse is refused. → `T2 test_cross_asset_tier_is_blocked`
- **N3.** A range/anchor must exist before coordinates are used. → `T7 test_fib_requires_valid_born_range`
- **N4.** Tier is a compression, not a cause — no tier→probability field. → `T10 test_no_expectancy_or_probability_field`
- **N5.** Time ages state; time alone never calls the play. → `T2 test_unreached_clock_checkpoint_is_watch`
- **N6.** Touch ≠ acceptance. → `T3 test_touch_cannot_satisfy_acceptance`
- **N7.** Reach ≠ trade win. → `T6 test_xau_evidence_refs_are_promotion_only`
- **N8.** First delivery can matter more than terminal reach; order is
  preserved. → `T5 test_targets_preserve_first_delivery_order`
- **N9.** Rekey is a remapping transition, not a touch. → `T7 test_fib_132_is_primary_rekey`
- **N10.** Range-left updates conditional opportunity after consumption. → `T5 test_range_left_conditioning_preserved`
- **N11.** L3 destination ≠ L2 path ≠ L1 entry. → `T6 test_xau_l3_destination_only_blocked`
- **N12.** Model state ≠ setup. → `T2 test_state_not_declared_by_card_is_blocked`
- **N13.** Setup ≠ automation approval. → `T9 test_p90_automation_permitted_false_everywhere`
- **N14.** A manual strategy can coexist with failed automation parity. → `T9 test_st_automation_request_blocked`
- **N15.** Negative evidence stays queryable. → `T7 test_fib_negative_evidence_attached`
- **N16.** Historical performance is never silently current. → `T9 test_p90_no_current_performance_claim`
- **N17.** News is a conditioner, not a geometry replacement. → `T2 test_higher_layer_conflict_reports_facts`
- **N18.** No deterministic rhetoric in status labels. → `T1 test_setup_record_rejects_free_text_field`
- **N19.** A no-go lock is binding for setup eligibility. → `T11 test_valid_trigger_under_lock_blocked`
- **N20.** No setup or model can manufacture brokerage execution
  authority. → `T11 test_model_state_serialized_as_signal_refused`

## O. Execution class, exposure and ownership (single-owner authority)

- **O1.** Book I owns card identity; III.5 never mints a `SET.*` id. → `T9 test_st_creates_no_setup_identity`
- **O2.** Book II owns authorization; III.5 emits no allow/deny of its own. → `T10 test_statistics_expose_no_numeric_result_type`
- **O3.** Exposure is carried verbatim and never widened. → `T1 test_registry_carries_status_verbatim`
- **O4.** `OPERATOR_ONLY` cards are not served on public surfaces. → `T1 test_registry_refuses_quarantined_card`
- **O5.** `RESEARCH_LAB` cards stay research even when authorized. → `T7 test_fib_production_request_blocked`
- **O6.** Manual validity never implies automation parity. → `T9 test_st_perception_gap_unresolved`
- **O7.** A research-only classification cannot silently promote. → `T1 test_registry_has_no_automation_approved_card`
- **O8.** A parked classification cannot be promoted by request. → `T11 test_parked_xau_setup_blocked`
- **O9.** Downstream surfaces render authorized results only. → `T12 test_no_provider_or_service_import`
- **O10.** The engine is pure: no global mutable state. → `T12 test_no_filesystem_or_clock_access`
- **O11.** Version pinning is explicit on every resolution. → `T1 test_registry_never_latest_without_policy`
- **O12.** The projection from card class to `manual_status` is total. → `T8 test_jpy_card_is_manual_operator`
- **O13.** No aggregate across models or roles exists. → `T8 test_jpy_no_basket_confidence_field`
- **O14.** No confluence score exists anywhere. → `T2 test_higher_layer_conflict_reports_facts`

## P. Gap and authority discipline (upstream registers)

- **P1.** R15 Range Birth production eligibility remains blocked. → `T7 test_fib_unresolved_anchor_unresolved`
- **P2.** III.4-GAP-10 (durable history) is carried, not closed. → `T12 test_migrations_unchanged`
- **P3.** III.4-GAP-11 (ST/P90) is answered here only as bounded
  framework/lineage. → `T9 test_st_is_manual_historical_framework`
- **P4.** III.4-GAP-12 (intrabar ambiguity) is respected, not resolved. → `T11 test_ambiguous_intrabar_first_delivery_blocked`
- **P5.** JPY manual parity restriction is carried. → `T8 test_jpy_no_automation_permission`
- **P6.** BTC weekly/monthly unresolved anchors are carried. → `T2 test_anchor_declared_rule_caps_at_unresolved`
- **P7.** XAU small-N promotions remain evidence-bound. → `T6 test_xau_evidence_refs_are_promotion_only`
- **P8.** Missing historical slices are declared, not invented. → `T7 test_fib_no_generic_pivot_fallback`
- **P9.** Provider wiring/live parity is out of scope and unchanged. → `T12 test_no_provider_or_service_import`
- **P10.** A missing canonical Setup Card is a gap, not a definition —
  notably no ST/P90 card exists. → `T9 test_st_creates_no_setup_identity`
- **P11.** An unresolved automation capability does not block its bounded
  operator representation. → `T9 test_st_tier_au_tier_explainable`
- **P12.** A DECLARED parameter never earns CANONICAL authority. → `T2 test_declared_parameter_caps_at_watch`
- **P13.** No gap is closed by widening a materialization status. → `T2 test_anchor_declared_rule_caps_at_unresolved`
- **P14.** Every gap has a documented disposition. → `T10 test_unsupported_statistic_refused_by_construction`

## Q. Authority-model preservation (Book I Phase 3)

- **Q1.** Observation/measurement/interpretation/transition/eligibility
  remain distinct stages. → `T2 test_state_not_declared_by_card_is_blocked`
- **Q2.** III.5 consumes upstream facts read-only. → `T12 test_import_direction_is_one_way`
- **Q3.** No `ModelOutput`/`Measurement` subclassing. → `T12 test_import_direction_is_one_way`
- **Q4.** No recomputation of a measurement. → `T12 test_no_legacy_state_engine_import`
- **Q5.** `model_state` and `production_authorization` stay distinct. → `T1 test_registry_carries_execution_class_verbatim`
- **Q6.** Explanation facts are structured, ordered and prose-free. → `T1 test_setup_record_rejects_free_text_field`
- **Q7.** Unearned eligibility is impossible. → `T11 test_unauthorized_target_promotion_blocked`
- **Q8.** A refusal is never an empty positive. → `T11 test_refusals_are_recorded_not_raised`
- **Q9.** Deterministic replay holds across runs. → `T12 test_cross_platform_hash_stability`
- **Q10.** No downstream authority is manufactured. → `T11 test_model_state_serialized_as_signal_refused`

## R. Boundaries and security

- **R1.** No network access anywhere in the package. → `T12 test_no_network_access`
- **R2.** No filesystem, wall clock or `datetime.now()`. → `T12 test_no_filesystem_or_clock_access`
- **R3.** No provider, service container or composition-root import. → `T12 test_no_provider_or_service_import`
- **R4.** Legacy `app/state_engine.py` is not imported. → `T12 test_no_legacy_state_engine_import`
- **R5.** No migration is added; `[1,2,3,4]` stands. → `T12 test_migrations_unchanged`
- **R6.** `market_data: NOT_CONFIGURED` readiness seam unchanged. → `T12 test_market_data_readiness_seam_unchanged`
- **R7.** Ratified upstream module hashes unchanged (11/12/13/13). → `T12 test_frozen_upstream_hashes_unchanged`
- **R8.** Import direction is one-way. → `T12 test_import_direction_is_one_way`
- **R9.** Engine version stamped on every record. → `T12 test_engine_version_stamped`
- **R10.** Evaluation hash deterministic. → `T12 test_evaluation_hash_deterministic`
- **R11.** Cross-platform hash stability (LF-normalised). → `T12 test_cross_platform_hash_stability`
- **R12.** No float in any payload. → `T12 test_no_float_in_payload`
- **R13.** No secret, credential or token in the package or fixtures. → `T12 test_no_secret_or_credential`
- **R14.** Registry snapshot deterministic. → `T12 test_registry_snapshot_is_deterministic`

## S. Proposed fixture set (created only at implementation)

- **S1.** 12 JSON fixtures + manifest + provenance README. → `T12 test_registry_snapshot_is_deterministic`
- **S2.** Fixtures reproduce an LF-normalised sha256 manifest. → `T12 test_cross_platform_hash_stability`
- **S3.** Fixtures are built by the same builders the suite uses. → `T12 test_evaluation_hash_deterministic`
- **S4.** Fixtures are provenance-labelled (`SYNTHETIC_FIXTURE` /
  `CANONICAL_SOURCE_SLICE`). → `T10 test_no_performance_payload_in_setup_record`
- **S5.** No fixture carries a performance figure. → `T10 test_no_win_rate_field_anywhere`
- **S6.** Registry fixtures cover all three canonical cards. → `T1 test_registry_exposes_three_canonical_cards`
- **S7.** Adversarial fixtures cover all 15 required classes. → `T11 test_refusals_are_recorded_not_raised`
- **S8.** Regeneration is idempotent. → `T12 test_registry_snapshot_is_deterministic`

## T. Coverage statement

**Clauses:** 250 (A14, B16, C18, D14, E10, F12, G14, H12, I14, J12,
K10, L16, M8, N20, O14, P14, Q10, R14, S8).

**Tests:** 162 unique names in 12 groups:

| Group | Tests | Frozen names |
|---|---|---|
| T1 setup contract + registry | 16 | `test_setup_record_is_immutable` … `test_registry_has_no_automation_approved_card` |
| T2 eligibility | 18 | `test_eligibility_vocabulary_is_four` … `test_declared_parameter_caps_at_watch` |
| T3 triggers | 14 | `test_trigger_vocabulary_is_seven` … `test_unsatisfied_trigger_yields_watch` |
| T4 invalidation | 10 | `test_invalidation_trichotomy_is_separate` … `test_invalidation_payload_is_decimal` |
| T5 targets | 12 | `test_target_order_is_canonical_not_sorted` … `test_target_cannot_be_invented` |
| T6 XAU | 14 | `test_xau_card_is_manual_operator` … `test_xau_evidence_refs_are_promotion_only` |
| T7 Fib | 12 | `test_fib_card_is_research_only` … `test_fib_negative_evidence_attached` |
| T8 JPY | 14 | `test_jpy_card_is_manual_operator` … `test_jpy_relationship_not_win_rate` |
| T9 ST + P90 | 12 | `test_st_is_manual_historical_framework` … `test_p90_automation_permitted_false_everywhere` |
| T10 statistics | 10 | `test_statistics_expose_no_numeric_result_type` … `test_no_performance_payload_in_setup_record` |
| T11 adversarial | 16 | `test_touch_without_rejection_refused` … `test_refusals_are_recorded_not_raised` |
| T12 boundaries | 14 | `test_no_network_access` … `test_registry_snapshot_is_deterministic` |
| **Total** | **162** | |

Every clause names a driver; every driver is reachable from at least one
clause. Implementation must reproduce all 162 names, may add tests, and
may never delete, weaken, skip or xfail one.

## Known gaps (authoritative list for this Bloc)

III.5-GAP-1 quarter-zone mapping uncanonicalised · III.5-GAP-2 no
canonical ST/P90 Setup Card · III.5-GAP-3 XAU ladder invalidation not
canonicalised · III.5-GAP-4 trigger observation vocabulary absent from
the measurement layer · III.5-GAP-5 no canonical setup statistics ·
III.5-GAP-6 setup/registry durability undecided (inherits III.4-GAP-10) ·
III.5-GAP-7 no live/feed parity. Carried: III.4-GAP-1…12,
III.3-GAP-1…10, III.2-GAP-1…6, III.1 GAP-1…5.

## Stop conditions (report; never improvise)

Missing/contradictory canonical card; ambiguous required upstream
contract; pressure to clear a III.4 lock; request for automation
approval, orders or sizing; need to modify a ratified module or add a
migration; need for network/clock/filesystem access.

## Ratification requirement

A future III.5 ratification requires all 162 tests green, no weakened
assertions, `EVIDENCE.md` + `RATIFICATION.md`, the new module-hash
baseline, gap dispositions, and CI green at the ratifying head. Green
tests alone are not ratification.

## III.6 handoff conditions (bounded interface proposal only)

III.6 may consume `setup_id`/`setup_version`/`evaluation_hash`,
`eligibility` + bounded reasons, typed location/trigger/invalidation/
targets, `manual_status`, `automation_permitted` (expected `False`),
parent states/snapshots, transition refs and evidence refs with status.
III.6 must apply Book II policy before release and may never upgrade an
`UNRESOLVED`/`BLOCKED` evaluation.
