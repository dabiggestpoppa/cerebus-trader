# BOOK III / BLOC III.2 — MEASUREMENT & FEATURE ENGINE — ACCEPTANCE.md

Status: **PROPOSED — clause→test mapping frozen at planning time**
(before any implementation, per the Book III gate §Evidence pack order).
Date: 2026-10-13
Branch: `forge` · Planning head: `2aafef984d71777bf8ee7f25c37f7a3e26773e4a`
Frozen source of every clause below:
`planning/forge/books/BOOK_III_CEREBUS_MARKET_INTELLIGENCE_PLAN_V1.md`
(§BLOC III.2, Ch III.2.1–III.2.10 + Acceptance III.2;
§CROSS-MODEL INVARIANTS; §GOLDEN FIXTURE PROGRAM; §FAILURE BEHAVIOR;
§ACCEPTANCE/RATIFICATION GATE §Measurements + final-record fields;
§EXCLUSIONS) — pinned at `planning/forge/PLANNING_FREEZE_MANIFEST_V1.md`
line 35. Dependency ratifications relied on: Book I I.5 `686faa7`
(CLOSED), Book II final G-F7 `e45d233` (contracts frozen, 50-file
manifest), Bloc III.1 BA-17 `2aafef9` (PASS — CLOSED; 11-module
interface hashes recorded in III.2 PLAN.md §6), planning freeze head
`60e0675`.

Conventions (same as frozen Book II/III.1 blocs): **test** = executable
test proposed for the future focused suite
`tests/test_forge_measurements.py` with golden fixtures under
`implementation/forge/book_iii/bloc_iii_2/fixtures/` (authored only
under a separate implementation authorization); **review** = inspection
recorded in the future `EVIDENCE.md`. Test IDs `T1`–`T12` are the groups
defined in `PLAN.md` §8. This mapping may gain tests at implementation
time; it may never lose or weaken one — any deviation is reported, not
silently absorbed.

---

## A. Range engine (Ch III.2.1)

- A1 `RangeMeasurement` carries exactly the frozen fields — high/low,
  size, midpoint, direction, close location, consumed fraction,
  range-left, breakout/return state, plus provenance envelope — test:
  `T1 test_range_measurement_frozen_fields`.
- A2 Size and midpoint computed in asset-native units (Decimal; no
  float; cross-unit arithmetic refuses via III.1 `convert_native`
  authority only) — test: `T1 test_range_size_midpoint_native_units`.
- A3 Direction and close location are typed facts from the input bars,
  never opinions or scores — test: `T1 test_close_location_and_direction`.
- A4 Consumed fraction is bounded and explicit; unresolvable range ⇒
  explicit refusal, never a default — test:
  `T1 test_consumed_fraction_bounds`.
- A5 Range-left is remaining expected movement *as a measurement*; it is
  never synthesized from nothing and updates explicitly as states are
  consumed (invariant #10) — test: `T1 test_range_left_remaining_never_invented`
  + `T1 test_range_left_updates_after_consumption`.
- A6 Breakout/return state is an explicit enum value; no silent or
  default state — test: `T1 test_breakout_return_state_explicit`.
- A7 Incomplete/missing input bars ⇒ `DATA_QUALITY_BLOCKED` or
  model-declared degraded via III.1 `QualityPolicy` — never a fabricated
  measurement — test: `T1 test_range_input_quality_blocked`.

## B. Tier/AU calibration (Ch III.2.2)

- B1 Calibration tables are keyed by model + model version +
  calibration id + calibration version; lookup with any wrong/missing
  key refuses — test: `T2 test_tier_table_keyed_by_model_and_version`.
- B2 EUR Daily Phase1 tier boundaries reproduce exactly (T1 <20p, T2
  20–30p, T3 30–45p, >45p no-go; each boundary edge asserted
  individually; cited `EV.EUR.DAILY.PHASE1_TIERS.V1`) — test:
  `T2 test_eur_daily_phase1_tiers_reproduce`.
- B3 BTC native tier boundaries reproduce exactly (T1 <$750, T2
  $750–$1,700, T3 $1,700–$3,000, >$3,000 no-go; AU 205/545/1160;
  trigger_levels 246/654/1392; density zones 164–246 / 436–654 /
  928–1392; cited `BTC.TRACKER.DWM.V1`) — test:
  `T2 test_btc_native_tiers_reproduce`.
- B4 AU is the asset-native atomic distance (`ONTOLOGY_CROSSWALK_V1`:
  native atomic distance / centroid-derived asset scale) — test:
  `T2 test_au_scale_native_atomic_distance`.
- B5 No global universal tier constant exists anywhere in the package;
  cross-asset or cross-model tier transfer refuses (invariant #2) —
  test: `T2 test_no_global_tier_constant` +
  `T2 test_cross_asset_tier_transfer_refuses`.
- B6 Research calibrations (e.g., EUR Weekly expansion factors) carry
  explicit calibration status `RESEARCH` that travels with every output;
  frozen launch calibrations carry `FROZEN_LAUNCH`; status is never
  silently promotable — test: `T2 test_research_calibration_status_labeled`.
- B7 Tier output is a compression/classification of continuous
  behavior; it carries no directional, causal or force implication
  fields (invariant #4) — test: `T2 test_tier_is_compression_not_force`.
- B8 Unknown or out-of-band value ⇒ explicit unclassified refusal —
  never nearest-bucket guessing — test: `T2 test_unknown_tier_explicit_unclassified`.
- B9 Missing model/calibration version ⇒ `MODEL_VERSION_UNAVAILABLE` —
  test: `T2 test_missing_calibration_version_unavailable`.

## C. Coordinate engine (Ch III.2.3)

- C1 Coordinate families are bounded to the canonical set
  (50/61.8/68/72/80/82/100/120/125/132/168/185) plus model-declared
  extensions with source refs; unknown family refuses — test:
  `T3 test_coordinate_families_bounded`.
- C2 Projection requires an ELIGIBLE or ACTIVE anchor — test:
  `T3 test_projection_requires_eligible_anchor`.
- C3 Arbitrary pivot / anchorless projection is impossible (no anchor
  generator exists in the package; R11 fallback absent by
  construction) — test: `T3 test_arbitrary_pivot_rejected`.
- C4 No coordinate without an earned active range/anchor (invariant
  #3) — test: `T3 test_no_coordinate_without_earned_range`.
- C5 The 132/168/185 rekey ladder does not auto-extend; deeper
  coordinates appear only when the model declares and the range earns
  them — test: `T3 test_rekey_ladder_does_not_auto_extend`.

## D. Range Birth/anchor interface (Ch III.2.4)

- D1 Anchor-state vocabulary is exactly
  UNRESOLVED/ELIGIBLE/ACTIVE/INVALIDATED/REKEYED; unknown state refused
  — test: `T4 test_anchor_status_vocabulary_exact`.
- D2 Anchor eligibility is a first-class output (status + earned-range
  reference + rule id/version + refusal code) — test:
  `T4 test_anchor_eligibility_first_class_output`.
- D3 REKEYED is a remapping transition (invariant #9), never state
  destruction or silent replacement — test:
  `T4 test_rekeyed_is_remapping_transition`.
- D4 INVALIDATED/UNRESOLVED anchors block downstream projection with an
  explicit refusal — test: `T4 test_invalidated_anchor_blocks_projection`.
- D5 No R11 generic-pivot fallback exists as callable API — test:
  `T4 test_no_generic_pivot_fallback`.
- D6 The production R15 Range Birth rule is not materialized
  canonically; the engine applies rules only where a canonical rule
  exists, and is never presented as automation-ready (III.2-GAP-1) —
  review: recorded in EVIDENCE; automation gating remains III.5's
  governed concern.

## E. Clock/state-age engine (Ch III.2.5)

- E1 Elapsed-since-event/state measured against III.1 clock identities
  — test: `T5 test_state_age_elapsed_since_event`.
- E2 Checkpoint reached is a typed fact — test:
  `T5 test_checkpoint_reached`.
- E3 Acceptance duration measured — test:
  `T5 test_acceptance_duration`.
- E4 Failure age measured — test: `T5 test_failure_age`.
- E5 Time-to-delivery is elapsed vs a *scheduled* canonical
  checkpoint/session boundary only; it never encodes price or forecast
  semantics — test: `T5 test_time_to_delivery_scheduled_elapsed_only`.
- E6 Session/weekly/monthly phase derives from the III.1 session
  registry — test: `T5 test_session_weekly_monthly_phase`.
- E7 Unresolvable clock/session ⇒ `NO_CALCULATION` — test:
  `T5 test_unresolvable_clock_no_calculation`.
- E8 Time weights/ages state; it never manufactures state (invariant
  #5) — test: `T5 test_time_weights_never_manufactures_state`.

## F. Path measurements (Ch III.2.6)

- F1 MAE/MFE computed from the typed path — test:
  `T6 test_mae_mfe_from_path`.
- F2 First delivery retained with its order — test:
  `T6 test_first_delivery_order`.
- F3 Target order retained — test: `T6 test_target_order`.
- F4 Touch ≠ acceptance: distinct typed states; touch never coerces to
  acceptance (invariant #6) — test: `T6 test_touch_not_acceptance`.
- F5 Reach ≠ target-before-stop — test:
  `T6 test_reach_not_target_before_stop`.
- F6 Excursion, rejection, acceptance, close-beyond and re-entry are
  typed values — test: `T6 test_excursion_rejection_acceptance_typed`
  (+ close-beyond and re-entry cases in the same group).
- F7 Remaining distribution is explicit; it is never synthesized from
  nothing — test: `T6 test_remaining_distribution_never_synthesized`.
- F8 The touch/acceptance/path distinctions survive a serialization
  round-trip unchanged — test: `T6 test_path_distinctions_survive_serialization`.
- F9 Reach output carries no win/expectancy/RR fields (invariant #7) —
  test: `T6 test_reach_not_trade_win`.

## G. Event/news features (Ch III.2.7)

- G1 Normalized event carries currency/asset relevance and event family
  — test: `T7 test_event_relevance_and_family`.
- G2 Scheduled vs actual times are distinct fields — test:
  `T7 test_scheduled_and_actual_times_distinct`.
- G3 Band/size fields are optional-but-explicit; absence is disclosed,
  never default-zero — test: `T7 test_band_size_fields_explicit_when_absent`.
- G4 Consumed/residual budget arithmetic is subtractive (canonical EUR
  event doctrine: consumed movement reduces what remains) — test:
  `T7 test_consumed_residual_budget_subtractive`.
- G5 News conditions geometry; it never replaces it (invariant #17) —
  test: `T7 test_news_never_replaces_geometry`.

## H. Higher-order measurements (Ch III.2.8)

- H1 Month/quarter seed ranges measured — test:
  `T8 test_higher_order_seed_ranges`.
- H2 D1–D3 states, M1 scale and M2 shaping exist as explicit typed
  containers — test: `T8 test_d1d3_m1_m2_containers`.
- H3 Unfinished side is explicit — test:
  `T8 test_unfinished_side_explicit`.
- H4 Weekly seed/path measured — test: `T8 test_weekly_seed_and_path`.
- H5 Higher/lower layer conflict returns conflict/state facts; the
  output structure is incapable of emitting a confluence score — test:
  `T8 test_layer_conflict_no_confluence_score`.

## I. Measurement provenance (Ch III.2.9)

- I1 Every computed measurement carries definition id + definition
  version — test: `T9 test_definition_version_on_every_measurement`.
- I2 …source data window (UTC bounds + input-bar content digest) —
  test: `T9 test_source_window_present`.
- I3 …clock ID + session ID + their registry versions — test:
  `T9 test_clock_session_id_present`.
- I4 …instrument id — test: `T9 test_instrument_present`.
- I5 …calculation timestamp (injected, never wall clock) — test:
  `T9 test_calculation_timestamp_injected`.
- I6 …quality state in the frozen III.1 vocabulary — test:
  `T9 test_quality_state_present`.
- I7 …`measurement_engine_version` (Book III final-record field owned
  by this Bloc) — test: `T9 test_measurement_engine_version_recorded`.
- I8 No statistical/probability field exists on any measurement without
  an explicit evidence reference (evidence-missing clause) — test:
  `T9 test_no_unsupported_statistic_fields` + review in EVIDENCE.

## J. Golden measurement fixtures (Ch III.2.10)

- J1 EUR golden cases reproduce at the measurement layer (T1/T2/T3/no-go
  daily seed tiers; rekey-ladder coordinate family; event-conditioned
  residual budget; weekly outer-node projections labeled `RESEARCH`;
  higher-order D3/M1/M2/M3 structural handoff) — test:
  `T10 test_golden_eur_fixtures_reproduce`.
- J2 XAU golden cases reproduce (normal spatial-band state; 68+8h→80
  and 120+8h→132 measurement paths with small-N disclosure; 132 state
  proves no automatic 168; quarter-zone eligible vs blind-touch
  blocked) — test: `T10 test_golden_xau_fixtures_reproduce`.
- J3 BTC golden cases reproduce (all three native Asian tiers; >$3,000
  no-go; slot × tier range-left; Tracker measurement output contains no
  Game/setup object) — test: `T10 test_golden_btc_fixtures_reproduce`.
- J4 JPY golden cases at the measurement layer (12–4PM DT structures
  132/168/187.5 as JPY-declared family cited to the JPY card; per-pair
  clock; native tier where canonical; basket-role cases deferred and
  disclosed) — test: `T10 test_golden_jpy_fixtures_reproduce`.
- J5 Fib golden cases reproduce (valid born range ⇒ coordinates;
  unresolved anchor ⇒ refusal; rekey transition interface output;
  arbitrary local pivot rejected) — test:
  `T10 test_golden_fib_fixtures_reproduce`.
- J6 Fixture manifest hashes recorded (LF-normalized content hashes,
  EOL-independent per the BA-17 `8b43cb4` lesson) — test/review:
  `T10 test_fixture_manifest_hashes_recorded` + review in EVIDENCE.
- J7 Synthetic bars carry `SYNTHETIC_FIXTURE` from creation and can
  never satisfy an evidence-reference check — test:
  `T10 test_synthetic_fixtures_labeled`.
- J8 Golden-program cases that belong to later blocs (JPY basket-role
  aggregation "agree + confirm / confirm absent / no equal vote"; ST
  manual automation-flag false; P90 version identity) are deferred,
  never claimed here — review: disclosed in EVIDENCE.

## K. Acceptance III.2 (frozen clause set, verbatim drivers)

- K-a "measurements reproduce frozen fixtures" — test: `T10` J1–J5.
- K-b "no measurement API labels a value as prediction/trade signal" —
  test: `T11 test_no_prediction_or_signal_vocabulary` (enum members,
  field names and serialized payloads contain no prediction/signal/call/
  expectancy/win-rate vocabulary).
- K-c "coordinate generation requires eligible anchor/range" — test:
  `T3` C2–C4 + `T4` D4.
- K-d "touch/acceptance/path distinctions survive serialization" —
  test: `T6` F8 + `T11 test_serialization_roundtrip_preserves_distinctions`.
- K-e "measurement provenance is complete" — test: `T9` I1–I7.

## L. Book-level gate §Measurements

- L1 "golden ranges/tiers/AU/coordinates/clocks/path metrics reproduce"
  — test: `T10` J1–J5 + `T2` B2–B4 + `T5` E6 (+ session/phase over
  golden fixtures) + `T6` F1.
- L2 "provenance accompanies measurements" — test: `T9` I1–I7.
- L3 "no arbitrary anchor coordinate generation" — test: `T3` C2–C5 +
  `T4` D5.

## M. Failure behavior (clauses landing on this layer)

- M1 Incomplete data ⇒ `DATA_QUALITY_BLOCKED` or model-declared
  degraded — test: `T1` A7 + `T9` (no fabricated measurement).
- M2 Clock/session cannot be resolved ⇒ `NO_CALCULATION` — test:
  `T5` E7.
- M3 Anchor unresolved ⇒ coordinates blocked where anchor required —
  test: `T3` C2 + `T4` D4.
- M4 Model/calibration version missing ⇒ `MODEL_VERSION_UNAVAILABLE` —
  test: `T2` B9.
- M5 Evidence missing ⇒ measurement may exist when its rule is
  canonical, but no unsupported statistic is attached — test: `T9` I8.
- M6 Higher/lower layer conflict ⇒ conflict/state facts, no invented
  confluence score — test: `T8` H5.
- M7 Provider/feed failure ⇒ III.1's explicit-state contract (never
  invented bars) is consumed unchanged; stale *serving* is an III.6
  product-policy concern — review: recorded in EVIDENCE.

## N. Applicable cross-model invariants

- N1 Invariant #2 "asset calibration is local unless transfer is
  explicitly validated" — test: `T2` B5.
- N2 Invariant #3 "range/anchor must exist before coordinates" — test:
  `T3` C4.
- N3 Invariant #4 "tier is a compression of continuous behavior, not a
  causal force" — test: `T2` B7.
- N4 Invariant #5 "time weights/ages state; time alone does not call
  the play" — test: `T5` E8.
- N5 Invariant #6 "touch ≠ acceptance" — test: `T6` F4.
- N6 Invariant #7 "reach ≠ trade win" — test: `T6` F9.
- N7 Invariant #8 "first delivery/path can matter more than terminal
  both-side reach" — test: `T6` F2 (path facts retained independent of
  terminal outcome).
- N8 Invariant #9 "rekey is a remapping transition" — test: `T4` D3.
- N9 Invariant #10 "range-left updates conditional opportunity after
  states are consumed" — test: `T1` A5.
- N10 Invariant #17 "news is a measurable perturbation/conditioner, not
  a geometry replacement" — test: `T7` G5.
- N11 Invariant #18 "no deterministic rhetoric in runtime status
  labels" — test: `T11 test_status_labels_factual_enum_only` (no
  guaranteed/certain/victim/kill/slay-style outcome words exist in any
  enum set).

## O. Authority-model preservation (Book I, Phase 3)

- O1 Measurements are neither models, claims, evidence nor setups — the
  package imports nothing from `qa/`, `retrieval/`,
  `app/forge/provenance.py`, `canonical.py` — test:
  `T12 test_no_book1_authority_imports`.
- O2 III.2 never grants itself evidence authority — test:
  `T12 test_no_corpus_writes` (Book I freeze manifest hashes unchanged
  after the suite) + review: fixture evidence refs are read-only
  citations by id.
- O3 Historical observation ≠ current market state — test:
  `T12 test_fixtures_labeled_historical` (fixtures carry a
  historical/cutoff label; no API here serves them as current).
- O4 Simulation ≠ empirical performance — test: `T10` J7.
- O5 Provider output ≠ canonical truth — review: inputs arrive only via
  III.1's normalized, quality-flagged contract (no raw-feed path exists
  in this package) — recorded in EVIDENCE.
- O6 No trading/game concepts — test:
  `T12 test_no_trading_or_game_concepts` (module-level check; the
  canonical BTC `trigger_levels` calibration field is the single
  disclosed exception, preserved verbatim from `BTC.TRACKER.DWM.V1`
  per PLAN.md §6).

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
  `T12 test_frozen_manifests_unchanged` (Book II 50-file freeze hashes,
  23 planning pins, Book I freeze manifest) +
  `T12 test_iii1_interfaces_unchanged` (11 III.1 module hashes from
  PLAN.md §6).
- P5 No secrets/credentials/PII in the data path; quality/measurement
  enums are bounded with no free-text payload — test:
  `T11 test_bounded_enums_no_free_text` +
  `T12 test_no_credentials_in_data_path`.
- P6 No Book I/II/III.1 test weakened or deleted — test/review: full
  regression suite green unchanged + review of diff scope (only new
  `book_iii/bloc_iii_2/`, new `app/forge/measurements/`, new
  `tests/test_forge_measurements.py`) at implementation time.
- P7 Deterministic and offline — test:
  `T12 test_deterministic_repeat_runs` (injected clocks; two full runs
  produce identical results).
- P8 No production adapters or speculative runtime capabilities —
  review: implementation diff limited to the PLAN.md §7 package; no
  provider SDKs, credentials, or III.3–III.6 features.
- P9 Measurements are immutable; redefinition requires a new definition
  version (core law: downstream may consume, never silently redefine) —
  test: `T11 test_measurements_immutable`.

---

## Coverage statement

Every frozen acceptance clause is mapped: Ch III.2.1–III.2.10 → §A–§J;
Acceptance III.2 (a–e) → §K; Book gate §Measurements → §L; applicable
§FAILURE BEHAVIOR → §M; applicable cross-model invariants → §N;
authority-model preservation → §O; boundaries/security → §P; the
final-record fields III.2 owns (measurement engine version; III.2
golden-fixture manifest hashes feeding the book-level golden fixture
hashes) → §I I7 + §J J6. Zero unmapped clauses. Out-of-scope gate
sections (Models, State/path, Setups, API) and the remaining
final-record fields (model runtime versions/hashes, setup registry
version, full golden-fixture program across later blocs, test counts,
unresolved research gates) belong to III.3–III.6/Book-level close and
are not claimed here.

## Known gaps (PLAN.md §10, III.2-GAP-1…6 + carried III.1 GAP-1…5)

- III.2-GAP-1: R15 Range Birth eligibility rule not materialized in the
  corpus — interface implemented, rules only where canonical; automation
  gated (§D D6).
- III.2-GAP-2: JPY pair-native tier tables only partially canonical
  (12–4PM DT structures exist; full per-pair tier/AU tables absent) —
  implemented only where canonical.
- III.2-GAP-3: XAU calibration is spatial bands + promoted examples +
  doctrine, not an EUR-style tier table — encoded with explicit status,
  never invented.
- III.2-GAP-4: No event/news calendar in-repo — synthetic labeled events
  only; real history needs operator-supplied canonical slices.
- III.2-GAP-5: Golden fixtures build on synthetic bars (III.1 GAP-1
  carries) + canonical constant tables cited by ID; reproduction is a
  contract test, never performance evidence.
- III.2-GAP-6: Higher-order definitions are evidence-bound — structure
  implemented; statistical parameters referenced by evidence ID, never
  hardcoded.
- Carried: III.1 GAP-1…GAP-5 (synthetic fixtures; sessions only where
  canonically defined; M5 final-bar scoped to its source lineage;
  provider seam `NOT_CONFIGURED`; scripted-streaming parity only).

## Stop conditions (report; never improvise)

1. A frozen clause that cannot be implemented without contradicting a
   Book I/II frozen contract, the III.1 ratified interfaces, or by
   inventing a non-canonical calibration/session/anchor rule.
2. Any need to modify a frozen Book I/II file, any III.1 module, the
   container readiness seam, or add a persistence migration.
3. Conflicting canonical sources (e.g., two calibration tables for the
   same model+calibration version, or a golden-fixture number
   contradicting a canonical constant) → operator/governance ruling
   required.
4. Any requirement to emit a probability, confluence score, prediction,
   expectancy or performance metric from this layer.
5. Being blocked on III.2 does **not** authorize starting III.3 or any
   other Bloc without a new operator handoff.

## Ratification requirement

At implementation time this Bloc is DONE only with: implementation
commit ladder, focused + full test output, `EVIDENCE.md` (including the
§K–§P verifications, re-verification of the III.1 interface hashes from
PLAN.md §6, and disclosure of deferred golden-program cases per §J J8),
known-gaps list, and a ratification record — per the frozen Book III
gate §Evidence pack. **STOP AFTER PLANNING: no implementation is
authorized by this packet.**
