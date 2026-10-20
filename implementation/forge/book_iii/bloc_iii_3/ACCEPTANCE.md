# BOOK III / BLOC III.3 — CEREBUS MODEL RUNTIME — ACCEPTANCE.md

Status: **PROPOSED — clause→test mapping frozen at planning time**
(before any implementation, per the Book III gate §Evidence pack order).
Date: 2026-10-20
Branch: `forge` · Planning head: `f9dce4f2d612f447bd8d2fa9c659a926cab65235`
Frozen source of every clause below:
`planning/forge/books/BOOK_III_CEREBUS_MARKET_INTELLIGENCE_PLAN_V1.md`
(§BLOC III.3 — common model contract + Ch III.3.1–III.3.9 +
Acceptance III.3; §CROSS-MODEL INVARIANTS; §GOLDEN FIXTURE PROGRAM;
§FAILURE BEHAVIOR; §ACCEPTANCE/RATIFICATION GATE §Models + final-record
fields; §EXCLUSIONS) — pinned at
`planning/forge/PLANNING_FREEZE_MANIFEST_V1.md` line 35. Dependency
ratifications relied on: Book I I.5 `686faa7` (CLOSED), Book II final
G-F7 `e45d233` (contracts frozen, 50-file manifest), Bloc III.1 BA-17
`2aafef9` (PASS — CLOSED; 11-module interface hashes), Bloc III.2
BA-18 `f9dce4f` (PASS — CLOSED; 12-module interface hashes, 87/87
focused, CI `39452676069` green), planning freeze head `60e0675`.
The BA-19 authorization itself (§2 common contract, §3 families, §4
governance invariants, §5 gap propagation, §6 test design) is the
operator directive this packet executes; where it restates frozen plan
clauses the frozen plan remains authority.

Conventions (same as frozen Book II/III.1/III.2 blocs): **test** =
executable test proposed for the future focused suite
`tests/test_forge_model_runtime.py` with golden fixtures under
`implementation/forge/book_iii/bloc_iii_3/fixtures/` (authored only
under a separate implementation authorization); **review** =
inspection recorded in the future `EVIDENCE.md`. Test IDs `T1`–`T12`
are the groups defined in `PLAN.md` §8. This mapping may gain tests at
implementation time; it may never lose or weaken one — any deviation is
reported, not silently absorbed.

---

## A. Common model contract (frozen §Common model contract + BA-19 §2)

- A1 Input: canonical model ID and explicit version on every request,
  both required, no default version anywhere — test:
  `T1 test_request_requires_explicit_model_and_version`.
- A2 Input: normalized measurements (III.2 objects only); a required
  measurement that is absent is never synthesized — test:
  `T1 test_inputs_are_measurements_only` +
  `T1 test_missing_required_measurement_refuses`.
- A3 Input: previous model state where applicable, version-checked
  against the request — test: `T1 test_prior_state_version_checked`
  + `T10` (PRIOR_STATE_MISMATCH cases).
- A4 Input: injected calculation timestamp — never wall time, never
  defaulted — test: `T1 test_calculation_timestamp_injected`.
- A5 Input: instrument and asset-native calibration lineage bound
  exactly as registered; cross-instrument transfer refuses — test:
  `T1 test_calibration_lineage_bound_to_request` +
  `T11 test_cross_asset_calibration_contamination_refuses`.
- A6 Input: data/clock/session/measurement engine versions asserted as
  identity, not inferred (invariant #1: data clock is part of model
  identity) — test: `T1 test_input_identity_versions_asserted`.
- A7 Output: model_state (family-bounded enum) and declared layer —
  test: `T1 test_output_state_and_layer_declared`.
- A8 Output: direction/bias only where canonically defined; explicit
  `NONE_DECLARED` otherwise (EUR Daily is not a direction oracle) —
  test: `T1 test_direction_only_where_defined`.
- A9 Output: active ranges and earned anchors reference III.2 outputs
  verbatim (anchor status vocabulary unchanged) — test:
  `T1 test_active_ranges_and_anchors_reference_measurements`.
- A10 Output: typed levels and coordinates with source refs — test:
  `T1 test_typed_levels_with_source_refs`.
- A11 Output: range-left/distribution fields only where
  source-supported, `UNRESOLVED` otherwise, conditioned on consumed
  states (invariant #10) — test: `T1 test_range_left_conditional_or_unresolved`.
- A12 Output: no-go and warning states as bounded codes (no free
  text) — test: `T1 test_no_go_and_warnings_bounded`.
- A13 Output: Claim/Evidence references read-only, by canonical ID —
  test: `T1 test_evidence_refs_read_only_ids` +
  `T11 test_missing_evidence_attaches_no_statistic`.
- A14 Output: quality state in the frozen III.1 vocabulary — test:
  `T1 test_quality_state_frozen_vocabulary`.
- A15 Output: model/version/hash (`model_id`, `model_version`,
  `model_runtime_version`, `output_hash`) on every output — test:
  `T1 test_output_carries_model_version_hash`.
- A16 Output: structured explanation facts (rule id + version + source
  ref + typed payload), **not generated prose** — test:
  `T1 test_explanation_facts_structured_no_prose`.
- A17 Descriptive state is structurally distinct from production
  authorization (`model_state` vs `production_authorization` fields);
  neither confers trade eligibility (invariants #3/#12/#13) — test:
  `T1 test_descriptive_state_vs_production_authorization` +
  `T11 test_model_state_not_trade_eligibility`.
- A18 No unsupported confidence scores, probabilities or performance
  metrics: no field of any output can carry probability, confidence,
  confluence, win-rate, expectancy, RR, prediction or signal semantics
  (AST + field + enum-value scan) — test:
  `T1 test_no_probability_confidence_or_performance_fields` +
  `T11 test_no_prediction_or_signal_vocabulary`.
- A19 Outputs immutable (core law: downstream may consume, never
  silently redefine) — test: `T1 test_outputs_immutable`.

## B. EUR Daily News + Rekey runtime (Ch III.3.1)

- B1 Chain: Asian seed → tier → distance/asymmetry → consumed states →
  event/news conditioning → rekey/extension → remaining distribution
  reproduces golden fixtures — test:
  `T3 test_eur_daily_state_chain_reproduces`.
- B2 Protect: **>45p source-generation no-go** reproduced at both
  boundary edges (>45 refuses; 45 exactly classifies per the frozen
  table) with `NoGoReason` code — test:
  `T3 test_eur_daily_source_no_go_boundary`.
- B3 Protect: 100/125/132/168/185 state identity — five distinct
  states, never collapsed or reordered — test:
  `T3 test_eur_daily_ladder_states_distinct`.
- B4 Protect: **news modifies conditional state; it never replaces
  geometry** — event conditioning changes only the conditional field;
  geometry fields (range, tier, ladder state) byte-identical with vs
  without the event — test:
  `T3 test_eur_daily_news_conditions_never_replaces_geometry`.
- B5 Protect: slot × tier / range-left semantics — remaining
  distribution is conditioned on consumed states and the active slot —
  test: `T3 test_eur_daily_slot_tier_range_left`.
- B6 Event budget consumed/residual arithmetic travels as facts;
  subtractive doctrine preserved (invariant #17) — test:
  `T3 test_eur_daily_event_budget_subtractive`.
- B7 Distance/asymmetry facts carry rule ids + versions (declared
  rules only; derived quantities via III.2 unit-safe helpers, never
  new measurement definitions) — test:
  `T3 test_eur_daily_derived_facts_rule_versioned`.
- B8 Clock/research-day identity (19:00–03:00 frame) is part of the
  state identity; unresolvable clock ⇒ `NO_CALCULATION` — test:
  `T3 test_eur_daily_clock_identity_required`.

## C. EUR Weekly Engine V1.1 runtime (Ch III.3.2)

- C1 Chain: Monday seed/range → weekly tier → route/range-left →
  hour × tier timing → outer-node state reproduces fixtures — test:
  `T4 test_eur_weekly_state_chain_reproduces`.
- C2 Protect: **outer-node promotion only** — a non-outer node can
  never reach the promoted state — test:
  `T4 test_eur_weekly_outer_node_promotion_only`.
- C3 Protect: static/frozen after defined completion — once OCC
  freezes the promoted structure, re-evaluation returns the identical
  frozen state — test: `T4 test_eur_weekly_frozen_after_completion`.
- C4 Protect: **weekly path is not promoted into higher-order
  destination evidence** — the destination field is structurally
  `NOT_THIS_LAYER` regardless of weekly facts — test:
  `T4 test_eur_weekly_path_not_destination_evidence`.
- C5 Recovered tier research (N=45/69/60 medians; expansion factors)
  is `RESEARCH` calibration status that travels with every output and
  is never emitted as runtime statistics (evidence ID
  `EV.EUR.WEEKLY.TIER_RANGE.V1` only) — test:
  `T4 test_eur_weekly_research_status_travels`.
- C6 Hour × tier timing derives from III.1 session/period phases;
  unresolvable timing ⇒ explicit unresolved, never invented — test:
  `T4 test_eur_weekly_hour_tier_timing_from_sessions`.
- C7 **Weekly route statistics are never inflated into trading win
  rates** — no win-rate/expectancy field exists; negative-evidence
  clause (weekly did not improve monthly destination) preserved as a
  recorded fact, not a score — test:
  `T4 test_eur_weekly_no_win_rate_fields` +
  `T11 test_no_performance_metric_vocabulary`.

## D. EUR Higher Order runtime (Ch III.3.3)

- D1 Chain: quarter seed → D3 prior → M1 scale → M2 shaping → M3
  resolution → weekly/local handoff reproduces fixtures — test:
  `T5 test_eur_higher_order_chain_reproduces`.
- D2 Protect: **L3 destination authority** — destination fields
  populate only from L3 inputs; weekly/Daily facts can never populate
  them (authority-leakage test) — test:
  `T5 test_eur_higher_order_l3_destination_authority` +
  `T11 test_l3_l2_l1_authority_leakage_impossible`.
- D3 Protect: **D3 agreement statistics ≠ trade win rate** — no
  percentage/win-rate field exists; direction prior is typed + basis
  fact + evidence refs (`EV.EUR.HO.D3_DIRECTION.V1`) — test:
  `T5 test_eur_higher_order_d3_prior_no_win_rate`.
- D4 Protect: **M1 correlation ≠ event probability** — no probability
  field exists; M1 scale is a typed magnitude fact with evidence ref
  (`EV.EUR.HO.M1_RANGE_CORR.V1`) — test:
  `T5 test_eur_higher_order_m1_not_probability`.
- D5 Protect: **unfinished-side completion as conditional destination
  evidence** — unfinished side ⇒ explicit conditional state with
  evidence ref (`EV.EUR.HO.UNFINISHED_M3.V1`), never a guarantee
  field — test:
  `T5 test_eur_higher_order_unfinished_side_conditional`.
- D6 M3 resolution and weekly handoff are explicit typed states with
  layer ownership preserved (handoff = routing context, not merged
  state) — test:
  `T5 test_eur_higher_order_m3_resolution_and_handoff`.
- D7 **Do not create missing statistical parameters** — an
  evidence-bound parameter with no materialized definition ⇒
  `UNRESOLVED` state, never an invented constant (III.3-GAP-5) — test:
  `T5 test_eur_higher_order_missing_parameter_unresolved`.
- D8 Layer conflict ⇒ `LayerConflictFact` list; the output structure
  is incapable of emitting a confluence score — test:
  `T5 test_eur_higher_order_conflict_facts_no_score`.

## E. XAU Game runtime (Ch III.3.4)

- E1 Three independent layers output separately (L3 destination/scale;
  L2 route/pace/distribution/delivery clocks; L1 Asian tier/relative
  consumption/execution context) — test:
  `T6 test_xau_three_layers_typed_separately`.
- E2 Protect: **68 + 8h → 80 eligible promotion** reproduced exactly
  (band 68 + injected elapsed ≥ 8h ⇒ eligible-promotion state; both
  conditions required; evidence ref `EV.XAU.PROMOTION.68_80.V1`; N with
  rate, never a WR) — test: `T6 test_xau_68_to_80_promotion_rule`.
- E3 Protect: **120 + 8h → 132 research/small-N promotion** — promoted
  state carries `RESEARCH_FLAG_SMALL_N` (`N=25`) preserved, never
  silently upgraded (`EV.XAU.PROMOTION.120_132.V1`) — test:
  `T6 test_xau_120_to_132_research_small_n`.
- E4 Protect: **132 → 168 is not automatic** — from the 132 state no
  transition to 168 exists; fixture asserts absence — test:
  `T6 test_xau_132_never_promotes_168`.
- E5 Protect: **L2 state ≠ direct entry** — L2 output contains no
  entry/execution/setup vocabulary or fields; touch-only context can
  never reach the confirmation state (blind touch blocked) — test:
  `T6 test_xau_l2_state_not_entry` +
  `T6 test_xau_blind_touch_cannot_confirm`.
- E6 Protect: **parked setups remain parked** — a parked input flag is
  never cleared by any promotion/aging path; output stays parked/no-go
  — test: `T6 test_xau_parked_stays_parked`.
- E7 Promotion aging uses III.2 `elapsed_since` + injected clock
  (invariant #5: time weights state, never manufactures it) — test:
  `T6 test_xau_promotion_aging_never_manufactures_state`.
- E8 The runtime does not execute quarter-zone trades — no
  quarter-zone execution object exists; `SETUP.XAU.QUARTER_ZONE.V1` is
  referenced for boundary statements only (III.5) — test:
  `T6 test_xau_no_quarter_zone_execution_objects`.
- E9 No imported EUR/BTC calibration into XAU states (invariant #2) —
  test: `T6 test_xau_no_cross_asset_calibration` +
  `T7 test_btc_calibration_contamination_refuses`.

## F. BTC Tracker runtime (Ch III.3.5)

- F1 Daily lineage: 19:00–03:00 NY source frame → native tiers/AU →
  03:00–19:00 slot × tier range-left reproduces fixtures — test:
  `T7 test_btc_daily_lineage_reproduces`.
- F2 All three native Asian tiers at boundary edges (T1 <$750, T2
  $750–$1,700, T3 $1,700–$3,000; AU/`trigger_levels` constants cited to
  `BTC.TRACKER.DWM.V1`) — test: `T7 test_btc_three_native_tiers`.
- F3 Protect: **>$3,000 Asian-range no-go** for the recovered native
  calibration — test: `T7 test_btc_3000_no_go_boundary`.
- F4 Protect: **BTC Tracker ≠ BTC Game** — a Game-like model request
  ⇒ `MODEL_VERSION_UNAVAILABLE`; Tracker output field scan contains no
  Game/setup object — test:
  `T7 test_btc_game_contamination_refused` +
  `T7 test_btc_tracker_output_has_no_game_objects`.
- F5 Protect: **no Gold Game setup import** — static import discipline
  (no XAU/JPY family module reachable from `btc_tracker.py`) and no
  XAU setup vocabulary in BTC outputs — test:
  `T7 test_btc_no_gold_game_import`.
- F6 Weekly/monthly: versioned anchor/rekey/tracker fields **only
  where canonical definitions exist** — otherwise explicit
  `UNRESOLVED`/`NOT_MATERIALIZED` interface, never invented anchors
  (III.3-GAP-8) — test:
  `T7 test_btc_weekly_monthly_unresolved_without_canonical`.
- F7 Cross-asset calibration leakage fails (BTC calibration refuses
  foreign instruments; foreign calibrations refuse BTC) — test:
  `T7 test_btc_cross_asset_calibration_refuses` +
  `T11 test_cross_asset_calibration_contamination_refuses`.
- F8 Slot × tier range-left is conditioned on consumed states
  (invariant #10) — test: `T7 test_btc_slot_tier_range_left_conditional`.

## G. Fib / Range Birth runtime (Ch III.3.6)

- G1 Chain: range-birth eligibility → A/B active range →
  Alpha/Beta/Gamma/Delta structure → coordinate/path → rekey/new range
  reproduces when the anchor is ELIGIBLE/ACTIVE — test:
  `T8 test_fib_range_birth_chain_reproduces`.
- G2 Protect: **unresolved R15 ⇒ `RULE_NOT_MATERIALIZED`** refusal for
  any eligibility-bearing request (canonical registry is empty at this
  head; III.3-GAP-1) — test: `T8 test_fib_unresolved_r15_refuses`.
- G3 Research/explanation states exist when supported and are labeled
  `RESEARCH_ONLY`/`NOT_AUTHORIZED` — never automation-adjacent — test:
  `T8 test_fib_research_states_labeled`.
- G4 Protect: **production setup generation remains blocked** — no
  eligibility-bearing production output can be produced while R15 is
  unmaterialized — test: `T8 test_fib_production_generation_blocked`.
- G5 Protect: **no generic-pivot fallback** — no anchor generator
  exists in the runtime package; arbitrary local pivots rejected — test:
  `T8 test_fib_no_generic_pivot_fallback` +
  `T11 test_arbitrary_pivot_rejected`.
- G6 Protect: **no automatic anchor invention** — absent anchor ⇒
  explicit unresolved state, never a synthesized anchor — test:
  `T8 test_fib_no_automatic_anchor_invention`.
- G7 Protect: **coordinate availability is not proof of structural
  eligibility** — a request with coordinates available but rule
  unmaterialized still refuses — test:
  `T8 test_fib_coordinate_availability_not_eligibility`.
- G8 Rekey is a structural remapping (prior range/state → rekey event
  → successor mapping), never "price touched 132" (invariant #9) —
  test: `T8 test_fib_rekey_structural_remapping`.
- G9 R11 negative evidence (`EV.FIB.R11.ANCHOR_OVERGEN.V1`) is
  referenced as the rationale; R11 frequency/hit statistics never
  transfer into runtime outputs — test:
  `T8 test_fib_r11_negative_evidence_no_transfer`.

## H. JPY Carry Game runtime (Ch III.3.7)

- H1 Distinct basket roles returned separately: USDJPY carry master,
  AUDJPY risk/execution expression, EURJPY confirmation/veto — test:
  `T9 test_jpy_roles_returned_separately`.
- H2 Agree + confirm case reproduces (master+expression agree, referee
  confirms) with evidence ref `EV.JPY.CARRY.BASKET_RELATION.V1` —
  test: `T9 test_jpy_agree_and_confirm_case`.
- H3 Confirm absent ⇒ explicit veto/absent state, never silent pass —
  test: `T9 test_jpy_confirm_absent_vetoes`.
- H4 Pair-native tier/no-go honored per executed pair; no-go pair
  cannot express local state (III.3-GAP-2: only where canonical) —
  test: `T9 test_jpy_native_tier_no_go_per_pair`.
- H5 Protect: **no equal-vote majority or invented aggregate score** —
  no score/majority/aggregate field exists in the output structure; a
  three-pair-vote request refuses — test:
  `T9 test_jpy_equal_vote_impossible` +
  `T9 test_jpy_equal_vote_request_refuses`.
- H6 Protect: **confirmation ≠ entry** — confirmation state never
  populates local execution state; local execution comes only from the
  selected pair's L1 facts — test:
  `T9 test_jpy_confirmation_not_entry`.
- H7 Protect: **historical 12–4 PM DT geometry not silently merged** —
  DT coordinate set/structures absent from carry outputs unless the
  request explicitly references the DT family — test:
  `T9 test_jpy_dt_geometry_not_auto_merged`.
- H8 Protect: **manual operator classification in force** until parity
  approved — `production_authorization = MANUAL_OPERATOR` preserved
  under every state (III.3-GAP-2) — test:
  `T9 test_jpy_manual_operator_classification_preserved`.
- H9 Per-pair pair-native calibration bindings; cross-pair transfer
  refuses — test: `T9 test_jpy_pair_native_calibration_binding`.

## I. Model registry / dispatch (Ch III.3.8)

- I1 Every request resolves `model_id + version` exactly, for all seven
  launch families — test: `T2 test_registry_resolves_all_families`.
- I2 Unknown or unavailable version ⇒ `MODEL_VERSION_UNAVAILABLE`, fail
  closed (no partial output, no fallback) — test:
  `T2 test_unknown_version_fails_closed`.
- I3 Unknown model_id ⇒ same fail-closed refusal — test:
  `T2 test_unknown_model_id_fails_closed`.
- I4 No implicit "latest" model fallback: no default-version parameter,
  no `latest` API anywhere in the package — test:
  `T2 test_no_latest_fallback_api`.
- I5 Historical calls support version-pinned generations: a pinned
  historical (registered) version resolves to its own registered
  runtime, never silently upgraded — test:
  `T2 test_version_pinned_historical_generation`.
- I6 Registry entries bind runtime version + calibration/coordinate
  keys exactly (mismatched binding refuses) — test:
  `T2 test_registry_entry_binding_exact`.
- I7 A separate governed version policy would be required to change
  resolution semantics — review: recorded in EVIDENCE (no policy
  mechanism exists in this package).

## J. Deterministic replay (Ch III.3.9)

- J1 Identical normalized inputs + identical model version ⇒ identical
  output hash (repeat full runs) — test:
  `T10 test_identical_inputs_identical_hash`.
- J2 Hash covers model key, runtime version, input identity versions,
  clock/session IDs, injected timestamp, prior-state ref and all
  output fields — test: `T10 test_hash_covers_full_identity`.
- J3 Ordered transitions: state-chain order is part of identity —
  reordered transitions produce a different state and hash — test:
  `T10 test_ordered_transitions_affect_hash`.
- J4 Version drift: same input pinned to a different registered
  version yields that version's output and hash; the two hashes differ
  — test: `T10 test_version_drift_pinned_outputs_differ`.
- J5 **Replay must not silently substitute current rules for historical
  versions** — unregistered version fails closed; registered historical
  version replays its own pinned rules — test:
  `T10 test_replay_never_substitutes_rules`.
- J6 Previous-state handling: mismatched prior state (version/identity
  drift) ⇒ `PRIOR_STATE_MISMATCH`; matched prior state chains
  deterministically — test: `T10 test_prior_state_mismatch_refuses`.
- J7 Clock identities: identical instants under a different clock
  identity produce a different identity/hash (invariant #1) — test:
  `T10 test_clock_identity_participates_in_hash`.
- J8 Evidence-link stability: evidence refs identical across repeat
  runs — test: `T10 test_evidence_link_stability`.
- J9 Replay verification detects tampering: mutated timestamp/prior
  state ⇒ `REPLAY_HASH_MISMATCH` — test:
  `T10 test_replay_detects_nondeterministic_input`.

## K. Acceptance III.3 (frozen clause set, verbatim drivers)

- K-a "all launch runtimes conform to common contract" — test: `T1`
  A1–A19 over every family + `T2` I1.
- K-b "model-specific golden fixtures pass" — test: `T10` J-fixture
  cases (all fixture files in PLAN §8) + `T3`–`T9` chain tests.
- K-c "cross-asset calibration leakage tests fail" — test: `T7` F7 +
  `T11 test_cross_asset_calibration_contamination_refuses` + `T9` H9.
- K-d "parked/noncanonical behavior cannot activate" — test: `T6` E6
  (parked stays parked) + `T8` G2–G4 (R15 unmaterialized ⇒ cannot
  activate) + `T9` H8 (manual classification cannot activate).
- K-e "deterministic replay hashes match" — test: `T10` J1–J9.

## L. Book-level gate §Models

- L1 "seven launch family runtimes conform to versioned contract" —
  test: `T2` I1 + `T1` A1–A19 (per-family).
- L2 "deterministic replay passes" — test: `T10` J1–J9.
- L3 "cross-asset calibration leakage fails" — test: `T11`
  (contamination suite) + `T7` F7.
- L4 "BTC Tracker/Game separation passes" — test: `T7` F4–F5.
- L5 "XAU frozen/parked rules pass" — test: `T6` E2–E6.
- L6 "JPY role hierarchy passes" — test: `T9` H1–H8.
- L7 Final-record fields III.3 owns: `model_runtime_version`
  (`MODEL_RUNTIME_V1`) + III.3 fixture manifest hashes + III.3 test
  counts — test: `T1 test_output_carries_model_version_hash` +
  `T10 test_fixture_manifest_hashes_recorded` (hashes) + review:
  counts recorded in EVIDENCE at implementation time.

## M. Failure behavior (clauses landing on this layer)

- M1 Incomplete data ⇒ `DATA_QUALITY_BLOCKED` or model-declared
  degraded — never a fabricated/default state — test: `T11`
  `test_nonfinal_source_data_blocks` + `T1` A2.
- M2 Clock/session cannot be resolved ⇒ `NO_CALCULATION` — test:
  `T3 test_eur_daily_clock_identity_required` + `T5` (session-bound
  cases).
- M3 Model version missing ⇒ `MODEL_VERSION_UNAVAILABLE` — test: `T2`
  I2–I3.
- M4 Evidence missing ⇒ state may exist when its rule is canonical, but
  no unsupported statistic is attached — test: `T11`
  `test_missing_evidence_attaches_no_statistic`.
- M5 Higher/lower layers conflict ⇒ conflict/state facts; never an
  invented confluence score — test: `T5` D8 + `T1` A18.
- M6 Anchor unresolved ⇒ coordinates/setup blocked where anchor
  required — test: `T8` G2/G6/G7 (III.2 refusal consumed, not
  redefined).
- M7 Provider/feed failure ⇒ no feed path exists in this package;
  stale serving is III.6 product policy — review: recorded in EVIDENCE.

## N. Applicable cross-model invariants (frozen #1–#18) + BA-19 §4 governance invariants

Frozen cross-model invariants:

- N1 #1 "data clock is part of model identity" — test: `T1` A6 +
  `T10` J7.
- N2 #2 "asset calibration is local unless transfer is explicitly
  validated" — test: `T7` F7 + `T11` contamination suite + `T9` H9.
- N3 #3 "range/anchor must exist before coordinates" — test: `T8`
  G1/G7 (III.2 authority consumed).
- N4 #4 "tier is a compression of continuous behavior, not a causal
  force" — test: `T3` B1 (tier enters as typed classification; no
  force/direction field derived).
- N5 #5 "time weights/ages state; time alone does not call the play" —
  test: `T6` E7.
- N6 #6 "touch ≠ acceptance" — test: `T6` E5 (blind touch cannot
  confirm; III.2 semantics consumed unchanged).
- N7 #7 "reach ≠ trade win" — test: `T4` C7 + `T5` D3 + `T11`
  (no performance fields).
- N8 #8 "first delivery/path can matter more than terminal both-side
  reach" — test/review: path facts preserved from III.2 inputs; no
  runtime field overrides path with terminal outcome — recorded in
  EVIDENCE + `T3` B5 (consumed states condition range-left).
- N9 #9 "rekey is a remapping transition" — test: `T8` G8 + `T3` B3
  (ladder states distinct through rekey).
- N10 #10 "range-left updates conditional opportunity after states are
  consumed" — test: `T1` A11 + `T3` B5 + `T7` F8.
- N11 #11 "L3 destination ≠ L2 path ≠ L1 entry" — test: `T5` D2 +
  `T11` `test_l3_l2_l1_authority_leakage_impossible` + `T6` E5.
- N12 #12 "model state ≠ setup" — test: `T1` A17 + `T11`
  `test_model_state_not_trade_eligibility`.
- N13 #13 "setup ≠ automation approval" — test: `T1` A17 + `T8` G3 +
  `T9` H8 (production authorization is classification, never grant).
- N14 #14 "manual valid strategy can coexist with failed automation
  parity" — test: `T9` H8 (MANUAL_OPERATOR preserved) + `T8` G3
  (RESEARCH_ONLY preserved).
- N15 #15 "negative evidence remains queryable" — test: `T8` G9 (R11
  negative evidence referenced) + `T4` C4 (weekly negative result
  recorded as fact).
- N16 #16 "historical high-performance claims are never silently
  treated as current verified performance" — test: `T11`
  `test_historical_statistics_never_current_performance` (statistics
  exist only as evidence refs; small-N flags preserved — `T6` E3).
- N17 #17 "news is a measurable perturbation/conditioner, not a
  geometry replacement" — test: `T3` B4.
- N18 #18 "no deterministic rhetoric in runtime status labels" — test:
  `T11 test_status_labels_factual_enum_only` (no guaranteed/certain/
  victim/kill/slay-style outcome words in any enum set).

BA-19 packet §4 governance invariants (operator directive; restated as
acceptance conditions):

- G1 "Model ≠ Claim ≠ Evidence ≠ Setup" — test/review: `T1` A13 +
  `T12` import/write discipline + EVIDENCE review (no claim/evidence/
  setup object exists in the package).
- G2 "Measurement ≠ Model interpretation" — test: `T1` A2 +
  `T12 test_no_measurement_redefinition` (runtime never wraps/mutates
  III.2 objects; no III.2 module file modified — hash baseline).
- G3 "Model state ≠ trade eligibility" — test: `T1` A17 + `T11`.
- G4 "L3 destination ≠ L2 path ≠ L1 entry" — test: N11 tests.
- G5 "Asset calibration remains model-local" — test: N2 tests.
- G6 "Anchors must be earned before coordinate activation" — test:
  `T8` G1/G7.
- G7 "Touch ≠ acceptance" — test: N6.
- G8 "Reach ≠ trading win" — test: N7.
- G9 "Rekey is structural remapping" — test: N9.
- G10 "Range-left is conditioned on consumed states" — test: N10.
- G11 "Manual strategy validity ≠ automation parity" — test: N14.
- G12 "Historical evidence ≠ verified current performance" — test:
  N16.
- G13 "News conditions geometry; it does not replace it" — test: N17.
- G14 "No unearned probability or deterministic rhetoric in status
  labels" — test: `T1` A18 + `T11` N18 test.
- G15 "Negative evidence and unresolved states remain visible" — test:
  `T11 test_unresolved_states_remain_visible` (no default-empty
  success; unresolved states serialize as explicit values) + `T8` G9.
- G16 (boundary) "any runtime action requiring III.4/III.5 ownership
  stays a bounded state/interface proposal" — test/review: `T12`
  diff-scope review + no persistence/service/HTTP surface + EVIDENCE.

## O. Authority-model preservation (Book I, Phase 3)

- O1 Model states are neither claims, evidence nor setups — the package
  imports nothing from `qa/`, `retrieval/`, `app/forge/provenance.py`,
  `canonical.py`, `policy.py`, `service/`, `providers/`, `persistence/`,
  `observability/`, `backfill/` — test:
  `T12 test_no_book1_authority_imports`.
- O2 The runtime never grants itself evidence authority — test:
  `T12 test_no_corpus_writes` (Book I freeze manifest vs HEAD + corpus
  tree clean) + review: evidence refs are read-only citations by ID.
- O3 Historical observation ≠ current market state — test:
  `T12 test_fixtures_labeled_historical` (fixtures carry
  historical/cutoff labels; no API here serves current state).
- O4 Simulation ≠ empirical performance — test/review: golden state
  fixtures are contract tests over synthetic-labeled inputs
  (`T10` fixture cases + `T12` labeling).
- O5 Provider output ≠ canonical truth — review: inputs arrive only
  via III.1/III.2 normalized contract objects (no raw-feed path) —
  recorded in EVIDENCE.
- O6 No trading/game concepts as package identifiers — test:
  `T12 test_no_trading_or_game_concepts` (module-level check; the
  canonical model-ID strings and the BTC `trigger_levels` field are the
  single disclosed literal-data exception per PLAN §6, mirroring the
  III.2 `trigger_levels` precedent).

## P. Boundaries and security

- P1 No network anywhere in the suite — test:
  `T12 test_no_network_calls` (socket refusal guard + fixture-only
  inputs).
- P2 No new persistence migration — test:
  `T12 test_discover_migrations_unchanged` (`discover_migrations() ==
  [1, 2, 3, 4]` exactly; no `005_*` added).
- P3 Container readiness seam untouched — test:
  `T12 test_market_data_readiness_seam_unchanged` (`market_data:
  NOT_CONFIGURED` disclosure identical; composition root not rewired).
- P4 Frozen surfaces unmodified — test:
  `T12 test_frozen_manifests_unchanged` (Book II 50-file freeze
  hashes, 23 planning pins, Book I freeze manifest) +
  `T12 test_iii1_interfaces_unchanged` (11 III.1 module hashes from
  PLAN §6) + `T12 test_iii2_interfaces_unchanged` (12 III.2 module
  hashes from PLAN §6).
- P5 No secrets/credentials/PII in the data path; state/authorization
  enums bounded with no free-text payload — test:
  `T11 test_bounded_enums_no_free_text` +
  `T12 test_no_credentials_in_data_path`.
- P6 No Book I/II/III.1/III.2 test weakened or deleted — test/review:
  full regression suite green unchanged + review of diff scope (only
  new `book_iii/bloc_iii_3/`, new `app/forge/model_runtime/`, new
  `tests/test_forge_model_runtime.py`) at implementation time.
- P7 Deterministic and offline — test:
  `T12 test_deterministic_repeat_runs` (injected clocks; two full runs
  produce identical results).
- P8 No production adapters or speculative runtime capabilities —
  review: implementation diff limited to the PLAN §7 package; no
  provider SDKs, credentials, or III.4–III.6 features.
- P9 Model outputs immutable; redefinition requires a new runtime
  version (core law) — test: `T1` A19 +
  `T10 test_version_drift_pinned_outputs_differ`.

---

## Coverage statement

Every frozen acceptance clause is mapped: common model contract (4
input + 11 output clauses) → §A A1–A19; Ch III.3.1–III.3.9 → §B–§J;
Acceptance III.3 (a–e) → §K; Book gate §Models (6 clauses) → §L L1–L6
(+ L7 final-record fields III.3 owns); applicable §FAILURE BEHAVIOR →
§M; all 18 cross-model invariants → §N N1–N18; the BA-19 packet's 15
governance invariants + III.4/III.5 boundary → §N G1–G16;
authority-model preservation → §O; boundaries/security → §P. Zero
unmapped clauses. Out-of-scope gate sections (Data/clock, Measurements,
State/path, Setups, API) and the remaining final-record fields
(setup registry version, session/clock registry version,
market-data schema version, measurement engine version, full
golden-fixture program across later blocs, book-level test counts,
unresolved research gates register) belong to III.1/III.2 (already
claimed there) or III.4–III.6/Book-level close and are not claimed
here.

## Known gaps (PLAN.md §10, III.3-GAP-1…10 + carried III.1 GAP-1…5 + III.2-GAP-1…6)

- III.3-GAP-1: R15 Range Birth eligibility rule not materialized —
  III.3.6 implements the chain behind the gate; eligibility-bearing
  requests refuse `RULE_NOT_MATERIALIZED`; production blocked (§G).
- III.3-GAP-2: JPY pair-native tier tables partial + parity not
  approved — role states/basket gating implementable; per-pair tiers
  only where canonical; `MANUAL_OPERATOR` stands (§H).
- III.3-GAP-3: XAU calibration is spatial bands + promoted examples +
  doctrine — promotions implement as evidence-linked, flag-preserving
  states, never guarantees (§E).
- III.3-GAP-4: no event/news calendar in-repo — conditioning states
  over synthetic labeled events only (§B).
- III.3-GAP-5: higher-order statistics evidence-bound — structure
  implementable; parameters referenced by evidence ID, never emitted
  (§D).
- III.3-GAP-6: no real bar slices — golden state fixtures are
  synthetic-labeled contract tests, never performance evidence (§J).
- III.3-GAP-7: sessions/final-bar rules/provider wiring/live parity as
  disclosed upstream — clock-bound inputs degrade to explicit
  `NO_CALCULATION` (§M).
- III.3-GAP-8: BTC weekly/monthly anchor/rekey definitions not
  materialized — unresolved interfaces only; never an invitation to
  import BTC Game (§F).
- III.3-GAP-9: XAU parked/quarter-zone confirmation semantics belong
  to III.5 — bounded input flags + L1 context states respected, never
  cleared or emitted as setups (§E).
- III.3-GAP-10: ST/P90 golden cases not runtime-representable —
  re-disclosed as deferred to III.5.9/III.5.10 (III.2 J8 lineage).
- Carried: III.1 GAP-1…5 and III.2-GAP-1…6, dispositioned per family in
  PLAN §5.2/§10; none blocks III.3 ratification, each blocks only the
  named downstream claim.

## Stop conditions (report; never improvise)

1. A frozen clause that cannot be implemented without contradicting a
   Book I/II frozen contract, the III.1/III.2 ratified interfaces, or
   by inventing a non-canonical rule/calibration/session/anchor.
2. Any need to modify a frozen Book I/II file, any III.1/III.2 module,
   the container readiness seam, or add a persistence migration.
3. Conflicting canonical sources (e.g., two rule definitions for the
   same family+version, or a fixture number contradicting a canonical
   constant) → operator/governance ruling required.
4. Any requirement to emit a probability, confluence score,
   confidence score, prediction, expectancy or performance metric from
   this layer.
5. Any runtime action that requires III.4 transition ownership or III.5
   setup authorization must remain a bounded state/interface proposal,
   not an unauthorized implementation.
6. Being blocked on III.3 does **not** authorize starting III.4 or any
   other Bloc without a new operator handoff.

## Ratification requirement

At implementation time this Bloc is DONE only with: implementation
commit ladder, focused + full test output, `EVIDENCE.md` (including the
§K–§P verifications, re-verification of **both** interface baselines
from PLAN §6 — 11 III.1 + 12 III.2 module hashes — and disclosure of
deferred golden-program cases per §8 of the PLAN: ST/P90 → III.5),
known-gaps list, and a ratification record — per the frozen Book III
gate §Evidence pack. **STOP AFTER PLANNING: no implementation is
authorized by this packet.**

## III.4 handoff conditions (bounded interface proposal only)

- Model outputs are immutable per-call facts; III.4 will own persistent
  transition vocabulary/history/snapshots. This bloc pre-authorizes
  nothing: rekey chains, promotion aging and completion/freeze are
  computed within a call over `prior_state` and are handed to III.4 as
  facts, not as a transition engine.
- The bounded interfaces offered to III.4/III.5: family state enums +
  declared layers, `no_go` reason codes, `production_authorization`
  classifications, structured `ExplanationFact`s, anchor/coordinate
  references (III.2 authority preserved), `PRIOR_STATE_MISMATCH`
  semantics and the canonical replay-hash identity.
- III.4 must not re-derive model interpretation (core law: downstream
  may consume, never silently redefine); any new transition state
  consumes these facts under its own versioned vocabulary.
- Automation approval, setup eligibility and stale-serving policy
  remain blocked/owned downstream (III.5/III.6) regardless of this
  packet.
