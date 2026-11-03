# BOOK III / BLOC III.4 — STATE, PATH & TRANSITION ENGINE — ACCEPTANCE.md

Status: **PLANNING ONLY — frozen clause→test contract, committed before
any implementation.** This file authorizes nothing; it is the map any
future III.4 implementation must satisfy or explicitly deviate from.
Date: 2026-11-03
Branch: `forge` · Planning head: `2bd48917f969d57770516a039788ddc902a70a34`
Frozen source: `planning/forge/books/BOOK_III_CEREBUS_MARKET_INTELLIGENCE_PLAN_V1.md`
(`# BLOC III.4`, `# BOOK III CROSS-MODEL INVARIANTS`, `# BOOK III GOLDEN
FIXTURE PROGRAM`, `# BOOK III FAILURE BEHAVIOR`, `# BOOK III ACCEPTANCE /
RATIFICATION GATE`, `# BOOK III EXCLUSIONS`).

Clause IDs are local to this Bloc (`A1`, `B1`, …) exactly as III.1–III.3
did, and never collide with frozen chapter numbers. Proposed suite:
`tests/test_forge_state_engine.py`, groups **T1–T12**. Proposed fixture
directory: `implementation/forge/book_iii/bloc_iii_4/fixtures/`
(`BLOC_III_4.*.V1`). Every clause maps either to a proposed test or to an
explicit **governed review** — there are **zero silent exclusions**.

**Governing law for every clause below:** Observation → Measurement →
Model interpretation → State transition → Governed setup eligibility. A
terminal outcome must never erase how the market arrived there.

---

## A. State snapshot (Ch III.4.1)

- A1 Snapshot is **immutable**: no field mutate/assign/replace succeeds
  after construction (frozen dataclass + `FrozenInstanceError`) — test:
  `T1 test_snapshot_immutable`.
- A2 Snapshot is **versioned**: it carries `snapshot_id` and
  `snapshot_hash`, and every identity version (`model_id`,
  `model_version`, `model_runtime_version`, `state_engine_version`,
  `market_data_schema_version`, `clock_registry_version`,
  `session_registry_version`, `measurement_engine_version`) — test:
  `T1 test_snapshot_version_identity_complete`.
- A3 Snapshot carries the **model** identity and the **layer** typed as
  the frozen III.3 `Layer` enum (`L1`/`L2`/`L3`/`CROSS_LAYER`), echoed
  from the source output and never re-derived — test:
  `T1 test_snapshot_model_and_layer_from_source`.
- A4 Snapshot carries **timestamps**: injected `event_time` and
  `calculation_timestamp`, both timezone-aware, distinct fields, never
  wall clock — test: `T1 test_snapshot_timestamps_injected_not_wall`.
- A5 Snapshot carries the **active state** as the family-bounded
  `model_state` value, verbatim from the source `ModelOutput` — test:
  `T1 test_snapshot_active_state_verbatim`.
- A6 Snapshot carries **measurements by reference** (definition id +
  version + source window refs), never recomputed values; no
  measurement value is re-derived in III.4 — test:
  `T1 test_snapshot_measurements_referenced_not_recomputed` +
  `T1 test_no_measurement_subclassing`.
- A7 Snapshot carries **active ranges** and **active levels**
  (`TypedLevel`) with their canonical source refs, read-only — test:
  `T1 test_snapshot_active_ranges_and_levels`.
- A8 Snapshot carries **quality** in the frozen III.1 `DataOutcome`
  vocabulary — test: `T1 test_snapshot_quality_frozen_vocabulary`.
- A9 Snapshot carries **claim/evidence refs** as canonical IDs;
  `claim_refs` remains structurally empty (III.3 creates no claims) —
  test: `T1 test_snapshot_evidence_refs_read_only`.
- A10 Snapshot carries `production_authorization` **verbatim** and adds
  no eligibility field of its own — test:
  `T1 test_snapshot_authorization_verbatim` +
  `T11 test_snapshot_grants_no_eligibility`.
- A11 A snapshot derived from an unfinalized `ModelOutput` (empty
  `output_hash`), from an unregistered `(model_id, model_version)`, or
  from a foreign instrument refuses explicitly — test:
  `T1 test_snapshot_requires_finalized_source` +
  `T1 test_snapshot_rejects_unregistered_model`.
- A12 Snapshot **identity is deterministic**: same source + same injected
  timestamps ⇒ same `snapshot_hash`; changing any field changes it —
  test: `T1 test_snapshot_hash_deterministic`.
- A13 Snapshot supports **prior-state chaining** via
  `prior_snapshot_id`; the chained prior must belong to the same model
  key — test: `T1 test_snapshot_prior_chain_same_model_key`.

## B. Transition vocabulary (Ch III.4.2)

- B1 `TransitionKind` contains **exactly** these twelve members, no more
  and no fewer: `ENTER_STATE`, `ACCEPT`, `REJECT`, `FAIL`, `REPAIR`,
  `PROMOTE`, `DELIVER`, `REKEY`, `INVALIDATE`, `COMPRESS`, `RELEASE`,
  `STAND_DOWN` — test: `T2 test_vocabulary_exact_twelve`.
- B2 Models **may restrict** the vocabulary: every registered family
  declares an allowed set, and a kind outside it refuses
  (`TRANSITION_NOT_IN_FAMILY_VOCABULARY`) — test:
  `T2 test_family_restriction_enforced`.
- B3 No family may **expand** beyond the twelve; an attempt to register
  an additional kind fails structurally — test:
  `T2 test_no_vocabulary_expansion_possible`.
- B4 Every transition requires a **qualifying prior state**:
  `required_prior_states` must contain the prior `active_state`, and
  `forbidden_prior_states` must not; otherwise
  `TRANSITION_NOT_EARNED` — test:
  `T2 test_qualifying_prior_state_required`.
- B5 Every transition requires a **canonical rule**: `rule_id` +
  `rule_version` + canonical source ref; a missing rule refuses — test:
  `T2 test_canonical_rule_required`.
- B6 A rule whose `RuleMaterialization` is `NOT_MATERIALIZED` cannot earn
  a transition (`RULE_NOT_MATERIALIZED`, upstream code reused) — test:
  `T2 test_unmaterialized_rule_cannot_earn_transition`.
- B7 Every transition requires **valid source lineage**: the source
  `ModelOutput.output_hash` + `snapshot_id` must exist, be finalized and
  match the model key (`SOURCE_LINEAGE_MISSING` / `PRIOR_STATE_MISMATCH`)
  — test: `T2 test_source_lineage_required`.
- B8 A transition cannot be applied to a **different family's** state
  even when the numbers coincide (`TRANSITION_AUTHORITY_MISMATCH`) —
  test: `T2 test_cross_family_transition_refused`.
- B9 Transition **event time** is injected and ordered; two events at the
  same event time require an explicit declared order, else refuse — test:
  `T2 test_event_time_injected_and_ordered`.
- B10 `ACCEPT` requires prior `TOUCHED` evidence (invariant #6): touch is
  never coerced into acceptance — test:
  `T2 test_accept_requires_prior_touch` +
  `T10 test_touch_without_acceptance`.
- B11 Registered families' vocabulary sets are **stable and recorded**
  (the §5.2/§8 matrix in PLAN, mirrored by
  `model_family_transition_authority.json`) — test:
  `T2 test_family_authority_matrix_matches_fixture`.
- B12 `PROMOTE` requires an evidence ref and a declared eligibility rule;
  a promotion without authority refuses (`PROMOTION_WITHOUT_AUTHORITY`)
  — test: `T2 test_promote_requires_evidence_and_rule`.
- B13 `INVALIDATE` preserves the invalidated object's lineage (prior
  range/anchor ref) and never silently deletes history — test:
  `T2 test_invalidate_preserves_lineage`.
- B14 `COMPRESS`/`RELEASE` are available only to families that declare a
  compression grammar — test:
  `T2 test_compress_release_declared_only`.
- B15 No transition kind, enum value or payload key carries probability,
  confidence, signal, entry, target or execution semantics — test:
  `T11 test_vocabulary_carries_no_trading_semantics`.
- B16 A transition that would produce an **identical resulting state**
  from an identical prior state under the same rule is idempotent-refused
  as a no-op (`TRANSITION_NO_OP`) rather than silently appended — test:
  `T2 test_no_op_transition_refused`.

## C. First delivery (Ch III.4.3)

- C1 Ordered target/state delivery is recorded with a stable
  `order_index` over the declared target list — test:
  `T3 test_delivery_order_recorded`.
- C2 First **hit side** and its **timing** are recorded explicitly —
  test: `T3 test_first_hit_side_and_timing`.
- C3 **Both-side terminal reach does not erase** first-delivery sequence:
  a path that reaches A then B and one that reaches B then A produce
  different records even with identical terminal state — test:
  `T3 test_both_side_reach_preserves_sequence` +
  `T10 test_same_terminal_result_different_path`.
- C4 **First-delivery order reversal** is detected and represented, not
  normalized away — test: `T3 test_first_delivery_order_reversal`.
- C5 Target order is **stable**: re-running over the same inputs yields
  the identical `order_index` assignment — test:
  `T3 test_target_order_stable`.
- C6 Where the model **depends on first delivery**, a both-side hit
  *without* order is insufficient (`AMBIGUOUS_PATH`) — test:
  `T3 test_first_delivery_required_refuses_without_order`.
- C7 **Intrabar ambiguity**: when OHLC cannot resolve ordering within a
  bar, III.4 refuses (`AMBIGUOUS_PATH`) and never infers order from
  OHLC — test: `T3 test_ambiguous_intrabar_refuses` +
  `T10 test_ambiguous_intrabar_events`.
- C8 Delivery records reference the realizing bar (index/ref) supplied
  upstream; no bar is synthesized — test:
  `T3 test_delivery_references_source_bar`.
- C9 Delivery sequence survives serialization round-trip unchanged —
  test: `T3 test_delivery_sequence_roundtrip`.
- C10 Delivery carries **no win/expectancy/target-before-stop** field
  (invariant #7) — test:
  `T11 test_delivery_carries_no_performance_semantics`.
- C11 A delivery for an undeclared target refuses (`TARGET_NOT_DECLARED`)
  — test: `T3 test_undeclared_target_refused`.
- C12 Delivery timing uses injected event times and the canonical clock
  identity; unresolvable clock ⇒ `NO_CALCULATION` — test:
  `T3 test_delivery_clock_unresolvable_refuses`.

## D. Failure and repair (Ch III.4.4)

- D1 Failure/repair is available **only** for models/generations that
  declare it (`RuleMaterialization` CANONICAL/DECLARED); others refuse —
  test: `T4 test_failure_grammar_declared_only`.
- D2 The declared canonical chain is representable: valid acceptance →
  failure → midpoint repair → compression / reacceptance / opposite
  acceptance — test: `T4 test_declared_chain_representable`.
- D3 **Repair without a prior failure** refuses
  (`REPAIR_WITHOUT_FAILURE`) — test:
  `T4 test_repair_without_prior_failure_refused` +
  `T10 test_repair_without_prior_failure`.
- D4 **Failure without a prior valid acceptance** refuses
  (`FAILURE_WITHOUT_ACCEPTANCE`) — test:
  `T4 test_failure_without_acceptance_refused`.
- D5 Failure, **attempted repair**, **confirmed repair** and **new
  acceptance** are four distinct states; a repair attempt is never
  reported as a confirmed repair — test:
  `T4 test_failure_repair_acceptance_distinct`.
- D6 A **confirmed repair is not a new acceptance** and does not reset
  the acceptance lineage — test:
  `T4 test_confirmed_repair_not_new_acceptance`.
- D7 Historical **P90** failure/repair behavior is **never generalized**
  to unrelated models: an EUR-generation P90 grammar cannot be applied
  to XAU/BTC/Fib/JPY — test:
  `T4 test_p90_grammar_not_generalized`.
- D8 `COMPRESS` requires a preceding declared failure/repair state; a
  standalone compression refuses (`COMPRESSION_WITHOUT_FAILURE`) — test:
  `T4 test_compression_requires_failure`.
- D9 `RELEASE` requires a preceding compression and yields an explicit
  reacceptance or opposite acceptance — test:
  `T4 test_release_requires_compression`.
- D10 XAU 50–68 failure band / 68+ repair band transitions are
  evidence-linked and never presented as guarantees — test:
  `T4 test_xau_band_transitions_evidence_linked`.
- D11 Failure/repair states carry no recovery probability or expectancy
  field — test: `T11 test_repair_carries_no_probability`.
- D12 Repair/compression ordering survives serialization and replay —
  test: `T9 test_repair_chain_replays_identically`.

## E. Rekey (Ch III.4.5)

- E1 `REKEY` is a **structural remapping transition**, recorded with
  prior range/state ref, qualifying structural event, canonical rule
  id/version, new active mapping and eligibility change — test:
  `T5 test_rekey_record_complete`.
- E2 **A 132% touch alone does not authorize rekey**
  (`REKEY_NOT_STRUCTURAL`) — test:
  `T5 test_132_touch_alone_refuses_rekey` +
  `T10 test_invalid_rekey`.
- E3 Rekey **closes/replaces** the prior mapping according to the model:
  the old mapping is marked replaced (not deleted) and the new mapping
  becomes active — test: `T5 test_rekey_replaces_prior_mapping`.
- E4 EUR Daily ladder steps **100/125/132/168/185** remain **distinct**
  states; rekey does not collapse reach, violation and
  target-before-stop semantics — test:
  `T5 test_eur_ladder_steps_distinct`.
- E5 Rekey preserves **prior-state lineage** for reconstruction — test:
  `T5 test_rekey_preserves_lineage`.
- E6 A rekey from an `UNRESOLVED`/`NOT_ELIGIBLE` anchor refuses
  (`REKEY_FROM_UNRESOLVED_ANCHOR`) — test:
  `T5 test_rekey_from_unresolved_anchor_refuses`.
- E7 Fib structural rekey (`REKEY_REMAPPED`) requires a born/active
  range; coordinate availability alone is insufficient — test:
  `T5 test_fib_rekey_requires_born_range`.
- E8 XAU 132 rekey is structural and does **not** create a 168
  transition (132→168 NOT automatic) — test:
  `T5 test_xau_132_never_rekeys_to_168`.
- E9 BTC weekly/monthly rekey is `UNRESOLVED`/`NOT_MATERIALIZED`, never
  an invented remapping — test:
  `T5 test_btc_weekly_monthly_rekey_unresolved`.
- E10 Two rekeys within one event time without declared order refuse
  (`AMBIGUOUS_REKEY_ORDER`) — test:
  `T5 test_ambiguous_rekey_order_refuses`.
- E11 Rekey carries no probability of continuation field — test:
  `T11 test_rekey_carries_no_probability`.

## F. Layer handoff (Ch III.4.6)

- F1 Handoff direction is **L3 → L2 → L1 only**; any upward or skipping
  handoff refuses (`LAYER_HANDOFF_DIRECTION`) — test:
  `T6 test_handoff_direction_downward_only`.
- F2 Handoff preserves **L3 destination**, **L2 path/opportunity** and
  **L1 execution-context ownership** as three typed records — test:
  `T6 test_three_layer_records_typed`.
- F3 **No upward probability laundering**: no L1 fact can populate an L3
  field, and no field expresses a probability — test:
  `T6 test_no_upward_probability_laundering`.
- F4 **L1 cannot mutate L3 state** (`LAYER_OWNERSHIP_VIOLATION`) — test:
  `T6 test_l1_cannot_mutate_l3` + `T10 test_l1_mutation_of_l3`.
- F5 **No automatic entry eligibility** is created by a handoff (invariant
  #11/#12) — test: `T6 test_handoff_creates_no_entry_eligibility`.
- F6 **No monolithic confluence score**: a handoff with
  higher/lower-layer agreement emits facts only; no score field exists —
  test: `T6 test_no_monolithic_confluence_score`.
- F7 XAU L3/L2/L1 sub-states remain separately typed; L2 state is never
  a direct entry — test: `T6 test_xau_layers_separately_typed`.
- F8 EUR Higher Order L3 → Weekly L2 → Daily L1 chain is representable
  with ownership intact, and weekly path never populates L3 destination
  evidence — test: `T6 test_eur_l3_l2_l1_chain`.
- F9 Conflicting layers produce `MODEL_CONFLICT` facts (stand-down
  capable), never an invented resolution — test:
  `T6 test_layer_conflict_returns_facts`.
- F10 Handoff records reference upstream snapshot ids on both sides;
  a handoff from an unknown snapshot refuses — test:
  `T6 test_handoff_requires_both_snapshots`.
- F11 Handoff ownership survives serialization round-trip — test:
  `T6 test_handoff_roundtrip_preserves_ownership`.

## G. Range-left (Ch III.4.7)

- G1 Range-left is **conditional**: it carries `conditioned_on` with the
  consumed transition/state ids it depends on — test:
  `T7 test_range_left_conditional_on_consumed`.
- G2 It is **re-conditioned** after each of: delivery, acceptance,
  exhaustion, invalidation, rekey — test:
  `T7 test_range_left_updates_after_each_event`.
- G3 An **unconditional historical frequency** is refused as a substitute
  (`UNCONDITIONAL_FREQUENCY_REFUSED`) — test:
  `T7 test_unconditional_frequency_refused`.
- G4 Where no source-supported remaining measurement exists, the state is
  explicit `UNRESOLVED` with no value — test:
  `T7 test_range_left_unresolved_honest`.
- G5 Range-left never quotes a consumed target as still available — test:
  `T7 test_consumed_target_not_requoted`.
- G6 Range-left carries no probability-of-reach field — test:
  `T11 test_range_left_carries_no_probability`.
- G7 BTC slot×tier range-left re-conditioning is representable and
  clock-bound — test: `T7 test_btc_slot_tier_range_left`.
- G8 Sparse/consumed states cannot be re-opened by a later range-left
  record without an explicit declared transition — test:
  `T7 test_exhausted_state_not_reopened`.
- G9 Range-left value units are asset-native `NativeMagnitude`, never
  cross-unit and never float — test:
  `T7 test_range_left_native_units`.

## H. No-go / stand-down (Ch III.4.8)

- H1 `StandDownState` is bounded and machine-readable with exactly these
  six members: `DATA_QUALITY_FAILURE`, `INVALID_RANGE`,
  `UNRESOLVED_ANCHOR`, `MODEL_CONFLICT`, `PARKED_OR_EXHAUSTED`,
  `EVIDENCE_UNAVAILABLE` — test: `T8 test_stand_down_states_bounded`.
- H2 Each stand-down carries a bounded **reason** (no free text) and the
  blocking rule/capability ref — test:
  `T8 test_stand_down_reason_bounded`.
- H3 **No-go cannot silently become executable eligibility**: a
  transition out of a stand-down into an eligibility-bearing state
  refuses (`ELIGIBILITY_WITHOUT_AUTHORITY`) — test:
  `T8 test_no_go_blocks_eligibility` +
  `T10 test_no_go_does_not_allow_setup_eligibility`.
- H4 The stand-down record exposes an explicit `eligibility_lock` fact
  downstream setup layers must respect — test:
  `T8 test_stand_down_exposes_eligibility_lock`.
- H5 Parked/exhausted state cannot be cleared by any promotion or
  acceptance path — test: `T8 test_parked_state_not_cleared`.
- H6 Data-quality failure produces a stand-down (or explicit
  `DATA_QUALITY_BLOCKED`), never a fabricated transition — test:
  `T8 test_data_quality_failure_stand_down`.
- H7 `UNRESOLVED_ANCHOR` is reachable from an R15-unmaterialized state
  and blocks coordinates/eligibility — test:
  `T8 test_unresolved_anchor_stand_down`.
- H8 `EVIDENCE_UNAVAILABLE` blocks statistic-bearing output while
  permitting canonical-rule state facts — test:
  `T8 test_evidence_unavailable_blocks_statistics`.
- H9 BTC >$3,000 and JPY per-pair native no-go produce
  `INVALID_RANGE`/`DATA_QUALITY_FAILURE`-class stand-downs per family —
  test: `T8 test_family_no_go_maps_to_stand_down`.
- H10 Stand-down is a **stateful output with a reason**, not an error
  exception that erases the snapshot/history — test:
  `T8 test_stand_down_is_state_not_erasure`.

## I. Transition history (Ch III.4.9)

- I1 History is **append-only** and ordered: no update/delete API exists
  — test: `T9 test_history_append_only`.
- I2 `sequence` is gapless and strictly increasing; replay rejects a gap
  (`HISTORY_SEQUENCE_GAP`) — test: `T9 test_history_sequence_gapless`.
- I3 Every event carries **source**, **event time**, **rule/version** and
  **resulting-state identity** — test:
  `T9 test_event_required_fields`.
- I4 **Replay reconstructs the current state**: replaying from genesis
  reproduces the current snapshot byte-identically — test:
  `T9 test_replay_reconstructs_current_state`.
- I5 **Explanations** are ordered structured facts (event order + rule
  refs), never generated prose — test:
  `T9 test_explanation_is_ordered_facts_no_prose`.
- I6 **Research inspection** can query any historical state by sequence
  and return its snapshot — test: `T9 test_historical_state_queryable`.
- I7 **Event-order mutation** is detected by the hash chain
  (`HISTORY_CHAIN_MISMATCH`) — test:
  `T9 test_event_order_mutation_detected` +
  `T10 test_event_order_mutation`.
- I8 **Non-deterministic replay** is detected: two identical runs must
  produce identical `history_hash`; divergence raises
  `REPLAY_RECONSTRUCTION_MISMATCH` — test:
  `T9 test_replay_hash_deterministic` +
  `T10 test_non_deterministic_replay_detected`.
- I9 History preserves **negative evidence** and invalidated/rejected
  paths (invariant #15) — test:
  `T9 test_negative_evidence_queryable`.
- I10 History carries no performance metric per event — test:
  `T11 test_history_carries_no_performance_metric`.
- I11 History records are storage-agnostic in this Bloc: the logical
  append-only contract is tested in memory; durable persistence is
  III.4-GAP-10 — test: `T12 test_no_persistence_migration_added` +
  governed review (EVIDENCE §gaps).

## J. Path invariants (Ch III.4.10) + required adversarial matrix

- J1 **Terminal outcome cannot erase the path**: same terminal state with
  different paths yields different records/hashes — test:
  `T10 test_terminal_outcome_cannot_erase_path`.
- J2 **Target order stable** under replay and re-serialization — test:
  `T10 test_target_order_stable_under_replay`.
- J3 **Rekey closes/replaces the mapping** according to the model (not
  deleted, not left ambiguous) — test:
  `T10 test_rekey_closes_or_replaces_mapping`.
- J4 **No-go prevents setup eligibility** — test:
  `T10 test_no_go_does_not_allow_setup_eligibility`.
- J5 **L1 cannot mutate L3 state** — test: `T10 test_l1_mutation_of_l3`.
- J6 **Same terminal result, different path** produce different
  transition histories — test:
  `T10 test_same_terminal_result_different_path`.
- J7 **First-delivery order reversal** detected — test:
  `T10 test_first_delivery_order_reversal`.
- J8 **Ambiguous intrabar events** refused, never inferred — test:
  `T10 test_ambiguous_intrabar_events`.
- J9 **Touch without acceptance** never yields acceptance — test:
  `T10 test_touch_without_acceptance`.
- J10 **Invalid rekey** refused — test: `T10 test_invalid_rekey`.
- J11 **Repair without prior failure** refused — test:
  `T10 test_repair_without_prior_failure`.
- J12 **Parked XAU state promoting without authority** refused — test:
  `T10 test_parked_xau_promotion_refused`.
- J13 **BTC Game logic entering Tracker** refused (no Game transition in
  the Tracker family vocabulary) — test:
  `T10 test_btc_game_into_tracker_refused`.
- J14 **JPY equal-vote interpretation** impossible: no aggregate/vote
  kind or field exists — test: `T10 test_jpy_equal_vote_impossible`.
- J15 **Missing source evidence** refuses the transition — test:
  `T10 test_missing_source_evidence_refuses`.
- J16 **Nonfinal/poor-quality bars** cannot earn a final transition —
  test: `T10 test_nonfinal_or_poor_quality_bars_refuse`.
- J17 **Historical version drift** never substitutes current rules for a
  pinned generation (`MODEL_VERSION_UNAVAILABLE`/rule-version mismatch)
  — test: `T10 test_historical_version_drift_refused`.
- J18 **Event-order mutation** detected — test:
  `T10 test_event_order_mutation`.
- J19 **Non-deterministic replay** detected — test:
  `T10 test_non_deterministic_replay_detected`.
- J20 **No-go incorrectly allowing setup eligibility** refused — test:
  `T10 test_no_go_does_not_allow_setup_eligibility`.
- J21 **Unearned transitions** of any kind refuse (property-level: a
  transition without qualifying prior state / rule / lineage never
  succeeds) — test: `T10 test_unearned_transition_refused`.

## K. Acceptance III.4 (frozen clause set, verbatim drivers)

- K1 **Path replay reconstructs current state** — test:
  `T9 test_replay_reconstructs_current_state`.
- K2 **First-delivery order is preserved** — test:
  `T3 test_both_side_reach_preserves_sequence` +
  `T3 test_first_delivery_order_reversal`.
- K3 **Rekey is an explicit transition** — test:
  `T5 test_rekey_record_complete` + `T2 test_vocabulary_exact_twelve`.
- K4 **No monolithic confidence score appears unless a future canonical
  model explicitly defines one** — test:
  `T6 test_no_monolithic_confluence_score` +
  `T11 test_no_probability_confidence_or_performance_fields`.
- K5 Range-left updates after states are consumed (frozen gate §State/path)
  — test: `T7 test_range_left_updates_after_each_event`.
- K6 Layer handoff does not probability-launder (frozen gate §State/path)
  — test: `T6 test_no_upward_probability_laundering`.
- K7 Path replay is deterministic across platforms (LF canonical
  serialization) — test: `T9 test_history_hash_cross_platform_stable`.

## L. Book-level gate §State/path + final-record contributions

- L1 Gate §State/path: first-delivery order retained — test:
  `T3 test_both_side_reach_preserves_sequence`.
- L2 Gate §State/path: rekey transition explicit — test:
  `T5 test_rekey_record_complete`.
- L3 Gate §State/path: range-left updates correctly — test:
  `T7 test_range_left_updates_after_each_event`.
- L4 Gate §State/path: layer handoff does not probability-launder —
  test: `T6 test_no_upward_probability_laundering`.
- L5 Final-record contribution: `STATE_ENGINE_VERSION` exists and is
  stamped on every snapshot/event — test:
  `T12 test_state_engine_version_recorded`.
- L6 Final-record contribution: III.4 golden-fixture manifest hashes and
  test counts are reproducible and recorded at implementation time —
  test: `T12 test_fixture_manifest_hashes_reproduce` (implementation-time;
  plan: this file).
- L7 Setsups boundary (gate §Setups: "model state cannot create
  unsupported entry") — III.4 creates no setup object at all — test:
  `T11 test_no_setup_objects_exist`.

## M. Failure behavior (clauses landing on this layer)

- M1 Incomplete data ⇒ `DATA_QUALITY_FAILURE` stand-down or explicit
  `DATA_QUALITY_BLOCKED` — test: `T8 test_data_quality_failure_stand_down`.
- M2 Clock/session unresolvable ⇒ `NO_CALCULATION` — test:
  `T3 test_delivery_clock_unresolvable_refuses`.
- M3 Anchor unresolved ⇒ anchor-required transitions blocked — test:
  `T8 test_unresolved_anchor_stand_down`.
- M4 Model version missing ⇒ `MODEL_VERSION_UNAVAILABLE` — test:
  `T2 test_unknown_version_fails_closed`.
- M5 Evidence missing ⇒ state may exist for canonical rules, but no
  unsupported statistic is attached — test:
  `T8 test_evidence_unavailable_blocks_statistics` +
  `T11 test_missing_evidence_attaches_no_statistic`.
- M6 Higher/lower layer conflict ⇒ conflict facts, no confluence score —
  test: `T6 test_layer_conflict_returns_facts`.
- M7 Provider/feed failure ⇒ no feed path exists in III.4; stale serving
  is III.6 product policy — **governed review**: recorded in EVIDENCE.
- M8 Intrabar ordering unresolvable ⇒ explicit refusal (III.4-specific
  failure clause) — test: `T3 test_ambiguous_intrabar_refuses`.

## N. Cross-model invariants (#1–#18) + governance invariants

- N1 **#1 data clock is part of model identity** — snapshot/event carry
  clock/session registry identity versions — test:
  `T1 test_snapshot_version_identity_complete`.
- N2 **#2 asset calibration is local** — cross-asset transition transfer
  refuses — test: `T2 test_cross_family_transition_refused`.
- N3 **#3 range/anchor must exist before coordinates** — no coordinate
  transition without an earned range — test:
  `T5 test_fib_rekey_requires_born_range`.
- N4 **#4 tier is a compression, not a causal force** — III.4 adds no
  causal claim and no derived force field — test:
  `T11 test_no_new_derived_semantics`.
- N5 **#5 time weights state; time alone does not call the play** — a
  time checkpoint alone cannot earn a state transition — test:
  `T2 test_time_alone_cannot_earn_transition`.
- N6 **#6 touch ≠ acceptance** — test:
  `T10 test_touch_without_acceptance`.
- N7 **#7 reach ≠ trade win** — test:
  `T11 test_delivery_carries_no_performance_semantics`.
- N8 **#8 first delivery/path can matter more than terminal reach** —
  test: `T10 test_terminal_outcome_cannot_erase_path`.
- N9 **#9 rekey is a remapping transition** — test:
  `T5 test_rekey_replaces_prior_mapping`.
- N10 **#10 range-left updates conditional opportunity** — test:
  `T7 test_range_left_conditional_on_consumed`.
- N11 **#11 L3 ≠ L2 ≠ L1** — test:
  `T6 test_three_layer_records_typed`.
- N12 **#12 model state ≠ setup** — test:
  `T11 test_model_state_not_setup`.
- N13 **#13 setup ≠ automation approval** — III.4 grants no approval
  field — test: `T11 test_no_automation_approval_field`.
- N14 **#14 manual valid strategy coexists with failed parity** —
  `MANUAL_OPERATOR` preserved verbatim on JPY — test:
  `T11 test_manual_operator_preserved`.
- N15 **#15 negative evidence remains queryable** — test:
  `T9 test_negative_evidence_queryable`.
- N16 **#16 historical claims are never silently current performance** —
  no performance field exists; fixtures labeled — test:
  `T11 test_no_performance_claims_from_fixtures`.
- N17 **#17 news is a conditioner, not geometry replacement** — event
  facts cannot earn a geometry transition — test:
  `T2 test_event_fact_cannot_earn_geometry_transition`.
- N18 **#18 no deterministic rhetoric in status labels** — all labels are
  bounded enums; no free-text field anywhere — test:
  `T11 test_no_free_text_labels`.
- N19 Governance: no invented R15 Range Birth eligibility — test:
  `T8 test_unresolved_anchor_stand_down` + `T2 test_unmaterialized_rule_cannot_earn_transition`.
- N20 Governance: no JPY automation parity claim — test:
  `T11 test_manual_operator_preserved`.
- N21 Governance: no automatic BTC weekly/monthly state construction
  without canonical anchors — test:
  `T5 test_btc_weekly_monthly_rekey_unresolved` +
  `T10 test_btc_game_into_tracker_refused`.
- N22 Governance: no universalization of small-N XAU promotions — test:
  `T2 test_promote_requires_evidence_and_rule` +
  `T4 test_xau_band_transitions_evidence_linked`.
- N23 Governance: no ST/P90 automation promotion from historical
  evidence — test: `T4 test_p90_grammar_not_generalized` +
  `T11 test_no_automation_approval_field`.
- N24 Governance: no trading win rate or probability inferred from path
  events — test: `T11 test_no_probability_confidence_or_performance_fields`.

## O. Model-specific transition contracts (authorization §3)

- O1 **EUR Daily** — range consumption, extension, event conditioning and
  rekey transitions are family-bounded and ladder-distinct; event/news
  never replaces geometry — test:
  `T2 test_family_restriction_enforced` +
  `T5 test_eur_ladder_steps_distinct` +
  `T2 test_event_fact_cannot_earn_geometry_transition`.
- O2 **EUR Weekly** — seed ownership, timing and **outer-node promotion
  only**; `FROZEN` is static; weekly path never becomes L3 destination
  evidence — test: `T6 test_eur_l3_l2_l1_chain` +
  `T2 test_promote_requires_evidence_and_rule`.
- O3 **EUR Higher Order** — conditional destination and D3/M1/M2/M3
  handoffs; statistics referenced by evidence ID only — test:
  `T6 test_three_layer_records_typed` +
  `T8 test_evidence_unavailable_blocks_statistics`.
- O4 **XAU Game** — L3/L2/L1 separation, qualified promotion, repair and
  parked-state restrictions; 132→168 not automatic; blind touch blocked
  — test: `T6 test_xau_layers_separately_typed` +
  `T5 test_xau_132_never_rekeys_to_168` +
  `T10 test_parked_xau_promotion_refused`.
- O5 **BTC Tracker** — daily state sequence representable; unresolved
  weekly/monthly rules explicit; Tracker/Game isolation — test:
  `T5 test_btc_weekly_monthly_rekey_unresolved` +
  `T10 test_btc_game_into_tracker_refused`.
- O6 **Fib / Range Birth** — R15 unresolved gate, earned anchors,
  structural rekey — test: `T8 test_unresolved_anchor_stand_down` +
  `T5 test_fib_rekey_requires_born_range`.
- O7 **JPY Carry** — master/expression/confirmation roles, manual
  classification and veto conditions; no equal-vote; confirmation ≠
  entry — test: `T10 test_jpy_equal_vote_impossible` +
  `T11 test_manual_operator_preserved`.

## P. Gap and authority discipline (III.3-GAP-1…10, III.2-GAP-1…6, III.1 GAP-1…5)

- P1 **III.3-GAP-1 / III.2-GAP-1 / III.1 lineage — R15 not
  materialized.** Permitted: unresolved range-birth state, structural
  rekey/invalidation facts where canonical. Unresolved: transition into
  `RANGE_ACTIVE`. Research-only: explanation states. Downstream III.5
  restriction: no Fib production setup. — test:
  `T8 test_unresolved_anchor_stand_down` +
  `T2 test_unmaterialized_rule_cannot_earn_transition`.
- P2 **III.3-GAP-2 / III.2-GAP-2 — JPY parity.** Permitted: role-
  separated state transitions. Unresolved: per-pair tier interpretation
  beyond canonical. Research-only: parity claims. III.5 restriction: no
  automation. — test: `T11 test_manual_operator_preserved`.
- P3 **III.3-GAP-3 / III.2-GAP-3 — XAU calibration shape.** Permitted:
  evidence-linked promotion/repair states with sample flags. Unresolved:
  universal tier semantics. III.5 restriction: no guarantee language. —
  test: `T4 test_xau_band_transitions_evidence_linked`.
- P4 **III.3-GAP-4 / III.2-GAP-4 — no event calendar.** Permitted:
  event-conditioning facts. Unresolved: real-history conditioning claims.
  — test: `T2 test_event_fact_cannot_earn_geometry_transition`.
- P5 **III.3-GAP-5 / III.2-GAP-6 — higher-order statistics
  evidence-bound.** Permitted: structure/hierarchy transitions.
  Unresolved: numeric statistics. — test:
  `T8 test_evidence_unavailable_blocks_statistics`.
- P6 **III.3-GAP-6 / III.2-GAP-5 / III.1 GAP-1 — synthetic fixtures.**
  Permitted: deterministic contract fixtures. Prohibited: empirical
  claims. — test: `T11 test_no_performance_claims_from_fixtures`.
- P7 **III.3-GAP-7 / III.1 GAP-2…5 — sessions/clock/provider/parity.**
  Permitted: canonically defined sessions; explicit degradation.
  Unresolved: live-feed parity. — test:
  `T3 test_delivery_clock_unresolvable_refuses`.
- P8 **III.3-GAP-8 — BTC weekly/monthly.** Permitted: explicit
  unresolved interfaces. Prohibited: invented anchors/rekeys. — test:
  `T5 test_btc_weekly_monthly_rekey_unresolved`.
- P9 **III.3-GAP-9 — XAU parked/quarter-zone doctrine is III.5's.**
  III.4 enforces parked restriction only — test:
  `T8 test_parked_state_not_cleared`.
- P10 **III.3-GAP-10 — ST/P90 deferred to III.5.9/III.5.10.** III.4
  claims neither — **governed review** (recorded in EVIDENCE).
- P11 **III.4-GAP-10 — durable history storage undecided.** Logical
  contract only; no migration added — test:
  `T12 test_no_persistence_migration_added` + governed review.
- P12 **III.4-GAP-12 — first-delivery granularity bound.** Refusal where
  ordering is unresolvable; no tick-level claim — test:
  `T3 test_ambiguous_intrabar_refuses`.
- P13 Explicit **unresolved results are valid outcomes**: a family whose
  canonical authority is missing returns a bounded unresolved state, not
  an error and not an invention — test:
  `T5 test_btc_weekly_monthly_rekey_unresolved` +
  `T8 test_stand_down_states_bounded`.
- P14 No gap may be **closed by implementation convenience**: a
  transition cannot be enabled by widening a rule's materialization
  status at runtime — test:
  `T2 test_unmaterialized_rule_cannot_earn_transition`.
- P15 Carry-forward discipline: every III.4 gap names its upstream
  provenance and its downstream restriction — **governed review**:
  EVIDENCE §gaps must table all 12 III.4 gaps with the three columns
  (permitted / unresolved / downstream restriction).

## Q. Authority-model preservation (Book I Phase 3)

- Q1 No stage inherits the next stage's authority: III.4 defines no
  eligibility, setup, claim or authorization-creating field — test:
  `T11 test_snapshot_grants_no_eligibility`.
- Q2 `claim_refs` remains empty by construction; III.4 creates no claim —
  test: `T11 test_no_claims_created`.
- Q3 Evidence refs are read-only canonical IDs, never values or
  statistics — test: `T1 test_snapshot_evidence_refs_read_only`.
- Q4 Transition facts are not prose: every explanation is structured
  (fact id + rule + version + source ref + bounded payload) — test:
  `T9 test_explanation_is_ordered_facts_no_prose`.
- Q5 Serialized payloads carry no prediction/signal vocabulary — test:
  `T11 test_no_prediction_or_signal_vocabulary`.
- Q6 Immutability: snapshots, events and records cannot be mutated after
  construction (core law) — test: `T1 test_snapshot_immutable` +
  `T9 test_history_append_only`.
- Q7 `production_authorization` is passed through verbatim and never
  recomputed by III.4 — test:
  `T1 test_snapshot_authorization_verbatim`.

## R. Boundaries and security

- R1 Import discipline: only `app.forge.market_data`,
  `app.forge.measurements`, `app.forge.model_runtime` + stdlib; no
  Book II authority modules (`qa/`, `retrieval/`, `provenance.py`,
  `canonical.py`, `policy.py`, `service/`, `providers/`,
  `persistence/`, `observability/`, `backfill/`) — test:
  `T12 test_import_discipline`.
- R2 No legacy reuse: the package never imports `app.state_engine`
  (naive Signal Guard) — test: `T12 test_no_legacy_state_engine_import`.
- R3 No network: sockets refused under monkeypatched guards — test:
  `T12 test_no_network_access`.
- R4 No file I/O, no wall clock, no randomness in the package — test:
  `T12 test_no_io_or_wallclock`.
- R5 `ForgeServiceContainer` never appears in the package — test:
  `T12 test_no_composition_root_import`.
- R6 No corpus/ledger/audit write; no writes outside the package — test:
  `T12 test_no_corpus_or_ledger_writes`.
- R7 Migration baseline unchanged `[1, 2, 3, 4]`; no `005_*.sql` —
  test: `T12 test_no_persistence_migration_added`.
- R8 Readiness seam unchanged: `market_data` stays `NOT_CONFIGURED`,
  `required: False` — test: `T12 test_market_data_readiness_seam_unchanged`.
- R9 Frozen-surface integrity: Book I manifest + Book II 50 hashes + 23
  planning pins + III.1 11 + III.2 12 + III.3 13 module hashes unchanged
  after the suite — test: `T12 test_frozen_manifests_unchanged`.
- R10 No credentials/PII in the data path; no free-text payload —
  test: `T12 test_no_secrets_or_free_text`.
- R11 Deterministic repeat runs (two consecutive suite executions produce
  identical results) — test: `T12 test_deterministic_repeat_run`.
- R12 Outputs are `Decimal`/native units only; no float price anywhere —
  test: `T7 test_range_left_native_units` +
  `T12 test_no_float_prices`.

## S. Proposed fixture set (created only at implementation)

`implementation/forge/book_iii/bloc_iii_4/fixtures/` — twelve JSON
fixtures (`state_snapshots.json`, `transition_vocabulary_cases.json`,
`first_delivery_cases.json`, `failure_repair_cases.json`,
`rekey_cases.json`, `layer_handoff_cases.json`, `range_left_cases.json`,
`stand_down_cases.json`, `transition_history_cases.json`,
`path_invariants_cases.json`, `model_family_transition_authority.json`,
`replay_hashes.json`), plus `FIXTURE_MANIFEST.json` (LF-normalized
sha256, same convention as III.1–III.3), `README.md` provenance table and
`generate_fixtures.py`. All labeled `SYNTHETIC_FIXTURE` /
`CANONICAL_SOURCE_SLICE`; contract validation only, never empirical
trading evidence.

## T. Coverage statement

Every frozen III.4 clause (§A–§J above, i.e. Ch III.4.1–III.4.10 and
Acceptance III.4), every applicable Book III cross-model invariant
(#1–#18, §N), the Book-level gate §State/path (§L), the failure-behavior
clauses landing on this layer (§M), the seven model-specific transition
contracts (§O), the full carried gap register (§P), the authority-model
preservation rules (§Q) and the boundary/security surface (§R) are
mapped above.

- **Frozen chapters:** 10/10 mapped (A, B, C, D, E, F, G, H, I, J).
- **Acceptance III.4 drivers:** 4/4 mapped (K1–K4) plus the two
  gate-inherited drivers (K5–K6) and determinism (K7).
- **Cross-model invariants:** 18/18 mapped (N1–N18), plus 6 governance
  prohibitions (N19–N24).
- **Model families:** 7/7 mapped (O1–O7).
- **Carried gaps:** III.3-GAP-1…10, III.2-GAP-1…6, III.1 GAP-1…5 all
  dispositioned (P1–P10), plus new III.4-GAP-10/12 (P11–P12).
- **Silent exclusions:** none. The only non-test dispositions are the two
  explicitly governed reviews (M7 provider/stale-serving — owned by
  III.6; P10 ST/P90 — deferred to III.5.9/III.5.10) and the
  implementation-time evidence obligations (§S, §L6, §P15).
- **No implementation, code, test, fixture, generator, migration,
  provider or endpoint is authorized or created by this packet.**

## Known gaps

See `PLAN.md` §12.1: **III.4-GAP-1…12**, carrying III.3-GAP-1…10,
III.2-GAP-1…6 and III.1 GAP-1…5. None blocks planning or ratification of
this packet; each blocks only the specific downstream claim named.

## Stop conditions (report; never improvise)

1. A frozen clause that cannot be implemented without contradicting a
   Book I/II frozen contract, the ratified III.1/III.2/III.3 interfaces,
   or by inventing a non-canonical rule, transition or authority.
2. Any need to modify a frozen Book I/II file, any III.1/III.2/III.3
   module (any change to the PLAN §6 hashes), the container readiness
   seam, or to add a persistence migration.
3. Conflicting canonical sources (two failure/repair grammars or two
   rekey rules for one generation) → operator/governance ruling.
4. Any requirement to emit a probability, confluence score, confidence
   score, prediction, expectancy, win rate or performance metric.
5. Any transition that would grant setup eligibility or execution
   authority must remain a bounded interface proposal.
6. Being blocked on III.4 does **not** authorize beginning III.5 or any
   other Bloc without a new operator handoff.

## Ratification requirement

At implementation time this Bloc is DONE only with: implementation
commit ladder, focused + full test output, `EVIDENCE.md` (including the
§A–§R verifications, re-verification of **all three** interface baselines
from PLAN §6 — 11 III.1 + 12 III.2 + 13 III.3 module hashes — the Book II
50 hashes + 23 planning pins, the Book I manifest, the migration baseline
and the readiness seam), a gap-disposition table for III.4-GAP-1…12 and
every carried upstream gap, and a ratification record — per the frozen
Book III gate §Evidence pack. **STOP AFTER PLANNING: no implementation is
authorized by this packet.**

## III.5 handoff conditions (bounded interface proposal only)

- III.4 offers immutable `StateSnapshot`s, an append-only ordered
  `TransitionLedger` with reconstruction and chain hashes, the
  `stand_down` **eligibility lock**, conditional range-left with its
  conditioning set, and layer-ownership markers.
- III.5 may consume these facts to build governed setups; it may not
  re-derive model interpretation, convert a path event into a
  probability, or clear an eligibility lock without an explicit
  declared transition of its own.
- III.4 pre-authorizes nothing: no trigger, entry, invalidation or target
  semantics exist at this layer.
