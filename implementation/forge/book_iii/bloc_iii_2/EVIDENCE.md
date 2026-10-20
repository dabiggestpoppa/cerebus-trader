# BOOK III / BLOC III.2 — MEASUREMENT & FEATURE ENGINE — EVIDENCE.md

Status: implementation evidence for the frozen clause→test map in
`ACCEPTANCE.md` (planning head `2aafef9`, packet head `9b7def3`).
Authority: BA-18 Rung 2 (operator-directed implementation, Bloc III.2
ONLY). Date: 2026-10-20. Branch: `forge`.

Operating principle verified throughout: **measurements are
deterministic market facts, not predictions, trading signals, model
decisions or evidence of profitability.**  Institutional law
preserved: observed data → deterministic measurement → versioned model
interpretation → governed operator eligibility.  No layer inherited
authority because the preceding layer returned a successful
calculation.

---

## 1. Source and test inventory

| Surface | Files | Notes |
|---|---|---|
| `app/forge/measurements/` | 12 modules, 5,312 lines | `contracts.py` (50 registered definitions, immutable `Measurement` envelope, `NativeMagnitude`, deterministic `encode_value`/`decode_value`), `ranges.py`, `calibration.py`, `coordinates.py`, `anchors.py`, `state_age.py`, `path_metrics.py`, `events.py`, `higher_order.py`, `errors.py` (bounded refusal codes), `versions.py` (`MEASUREMENT_ENGINE_V1`), `__init__.py` (export surface) |
| `implementation/forge/book_iii/bloc_iii_2/fixtures/` | generator + 9 fixtures + manifest + README | deterministic, committed, hash-verified |
| `tests/test_forge_measurements.py` | 3,931 lines, 87 tests | the 86 binding names of the frozen map + 1 gained J8 disclosure test |

Imports reach only `app.forge.market_data` (the III.1 ratified
contracts) and the Python standard library.  No `qa/`, `retrieval/`,
`app/forge/provenance.py`, `canonical.py`, `policy.py`, service
container, providers, persistence or observability module is imported
(T12 O1, executable).

Environment: Python 3.11.9, pytest 9.0.3, Windows worktree
(`core.autocrlf=true`), LF-normalized fixture hashes for CI parity.

## 2. Clause → test traceability (every frozen acceptance condition)

Every clause of `ACCEPTANCE.md` §A–§P is mapped to an executable test
in `tests/test_forge_measurements.py` or to a recorded review below.
Result column: **P** = passing executable test; **R** = recorded review
(this document).  Zero clauses unmapped; zero weakened, skipped or
xfailed.

### §A Range engine (Ch III.2.1)

| Clause | Driver | Test(s) | Result |
|---|---|---|---|
| A1 frozen field set + provenance envelope | Ch III.2.1 | `T1 test_range_measurement_frozen_fields` | P |
| A2 size/midpoint in native units; cross-unit refuses | Ch III.2.1 | `T1 test_range_size_midpoint_native_units` | P |
| A3 direction/close location are typed facts | Ch III.2.1 | `T1 test_close_location_and_direction` | P |
| A4 consumed fraction bounded; unresolvable ⇒ explicit refusal | Ch III.2.1 | `T1 test_consumed_fraction_bounds` | P |
| A5 range-left measured, never invented, updates on consumption | Ch III.2.1 | `T1 test_range_left_remaining_never_invented`, `T1 test_range_left_updates_after_consumption` | P |
| A6 breakout/return state explicit enum | Ch III.2.1 | `T1 test_breakout_return_state_explicit` | P |
| A7 incomplete input ⇒ blocked or model-declared degraded | Ch III.2.1 | `T1 test_range_input_quality_blocked` | P |

### §B Tier/AU calibration (Ch III.2.2)

| Clause | Test(s) | Result |
|---|---|---|
| B1 four-part key; any wrong/missing part refuses | `T2 test_tier_table_keyed_by_model_and_version` | P |
| B2 EUR Daily Phase1 edges reproduce exactly (T1 <20p, 20/30/45 edges, >45 no-go) | `T2 test_eur_daily_phase1_tiers_reproduce` | P |
| B3 BTC native tiers/AU/thresholds/density zones reproduce | `T2 test_btc_native_tiers_reproduce` | P |
| B4 AU = asset-native atomic distance | `T2 test_au_scale_native_atomic_distance` | P |
| B5 no global tier constant; cross-asset transfer refuses | `T2 test_no_global_tier_constant`, `T2 test_cross_asset_tier_transfer_refuses` | P |
| B6 RESEARCH/FROZEN_LAUNCH status travels with output; never promotable | `T2 test_research_calibration_status_labeled` | P |
| B7 tier is compression, no force/causal field | `T2 test_tier_is_compression_not_force` | P |
| B8 out-of-band ⇒ explicit unclassified refusal | `T2 test_unknown_tier_explicit_unclassified` | P |
| B9 missing model/calibration version ⇒ `MODEL_VERSION_UNAVAILABLE` | `T2 test_missing_calibration_version_unavailable` | P |

### §C Coordinate engine (Ch III.2.3)

| Clause | Test(s) | Result |
|---|---|---|
| C1 canonical family bound + declared extensions with source refs | `T3 test_coordinate_families_bounded` | P |
| C2 projection requires ELIGIBLE/ACTIVE anchor | `T3 test_projection_requires_eligible_anchor` | P |
| C3 arbitrary pivot/anchorless projection impossible | `T3 test_arbitrary_pivot_rejected` | P |
| C4 no coordinate without earned range (invariant #3) | `T3 test_no_coordinate_without_earned_range` | P |
| C5 rekey ladder never auto-extends | `T3 test_rekey_ladder_does_not_auto_extend` | P |

### §D Range Birth / anchor interface (Ch III.2.4)

| Clause | Test(s) | Result |
|---|---|---|
| D1 exact five-state vocabulary | `T4 test_anchor_status_vocabulary_exact` | P |
| D2 eligibility is a first-class output | `T4 test_anchor_eligibility_first_class_output` | P |
| D3 REKEYED is a remapping transition (invariant #9) | `T4 test_rekeyed_is_remapping_transition` | P |
| D4 INVALIDATED/UNRESOLVED block projection | `T4 test_invalidated_anchor_blocks_projection` | P |
| D5 no R11 generic-pivot fallback as callable API | `T4 test_no_generic_pivot_fallback` | P |
| D6 R15 rule not materialized; automation stays gated | review §6 + `T10 test_deferred_golden_program_cases_disclosed` | R |

### §E Clock / state-age (Ch III.2.5)

| Clause | Test(s) | Result |
|---|---|---|
| E1 elapsed-since-event against III.1 clocks | `T5 test_state_age_elapsed_since_event` | P |
| E2 checkpoint reached is typed | `T5 test_checkpoint_reached` | P |
| E3 acceptance duration measured | `T5 test_acceptance_duration` | P |
| E4 failure age measured | `T5 test_failure_age` | P |
| E5 time-to-delivery is schedule distance only | `T5 test_time_to_delivery_scheduled_elapsed_only` | P |
| E6 session/weekly/monthly phase from III.1 contracts | `T5 test_session_weekly_monthly_phase` | P |
| E7 unresolvable clock/session ⇒ `NO_CALCULATION` | `T5 test_unresolvable_clock_no_calculation` | P |
| E8 time never manufactures state (invariant #5) | `T5 test_time_weights_never_manufactures_state` | P |

### §F Path measurements (Ch III.2.6)

| Clause | Test(s) | Result |
|---|---|---|
| F1 MAE/MFE from the typed path | `T6 test_mae_mfe_from_path` | P |
| F2 first delivery retained with its order | `T6 test_first_delivery_order` | P |
| F3 target order retained | `T6 test_target_order` | P |
| F4 touch ≠ acceptance (invariant #6) | `T6 test_touch_not_acceptance` | P |
| F5 reach ≠ target-before-stop | `T6 test_reach_not_target_before_stop` | P |
| F6 excursion/rejection/acceptance/close-beyond/re-entry typed | `T6 test_excursion_rejection_acceptance_typed` | P |
| F7 remaining distribution never synthesized | `T6 test_remaining_distribution_never_synthesized` | P |
| F8 distinctions survive serialization | `T6 test_path_distinctions_survive_serialization` | P |
| F9 reach carries no win/expectancy/RR field (invariant #7) | `T6 test_reach_not_trade_win` | P |

### §G Event / news features (Ch III.2.7)

| Clause | Test(s) | Result |
|---|---|---|
| G1 relevance + family | `T7 test_event_relevance_and_family` | P |
| G2 scheduled vs actual distinct | `T7 test_scheduled_and_actual_times_distinct` | P |
| G3 band/size optional-but-explicit | `T7 test_band_size_fields_explicit_when_absent` | P |
| G4 consumed/residual budget subtractive | `T7 test_consumed_residual_budget_subtractive` | P |
| G5 news never replaces geometry (invariant #17) | `T7 test_news_never_replaces_geometry` | P |

### §H Higher-order measurements (Ch III.2.8)

| Clause | Test(s) | Result |
|---|---|---|
| H1 month/quarter seed ranges measured | `T8 test_higher_order_seed_ranges` | P |
| H2 D1–D3/M1/M2 explicit typed containers | `T8 test_d1d3_m1_m2_containers` | P |
| H3 unfinished side explicit | `T8 test_unfinished_side_explicit` | P |
| H4 weekly seed/path measured | `T8 test_weekly_seed_and_path` | P |
| H5 conflict facts; structurally no confluence score | `T8 test_layer_conflict_no_confluence_score` | P |

### §I Measurement provenance (Ch III.2.9)

| Clause | Test(s) | Result |
|---|---|---|
| I1 definition id + version on every measurement | `T9 test_definition_version_on_every_measurement` | P |
| I2 source window (UTC bounds + bar-content digest) | `T9 test_source_window_present` | P |
| I3 clock/session ids + registry versions | `T9 test_clock_session_id_present` | P |
| I4 instrument id | `T9 test_instrument_present` | P |
| I5 injected calculation timestamp | `T9 test_calculation_timestamp_injected` | P |
| I6 quality state in frozen III.1 vocabulary | `T9 test_quality_state_present` | P |
| I7 `measurement_engine_version` (Book III final-record field owned here) | `T9 test_measurement_engine_version_recorded` | P |
| I8 no unsupported statistic fields without evidence ref | `T9 test_no_unsupported_statistic_fields` + review §9 | P + R |

### §J Golden measurement fixtures (Ch III.2.10)

| Clause | Test(s) | Result |
|---|---|---|
| J1 EUR golden cases reproduce | `T10 test_golden_eur_fixtures_reproduce` | P |
| J2 XAU golden cases reproduce (bands, promotions disclosed, 132↛168, quarter-zone paths) | `T10 test_golden_xau_fixtures_reproduce` | P |
| J3 BTC golden cases reproduce (tiers, slot×tier range-left, no Game object) | `T10 test_golden_btc_fixtures_reproduce` | P |
| J4 JPY golden cases (declared DT families, tier refusal, basket deferral) | `T10 test_golden_jpy_fixtures_reproduce` | P |
| J5 Fib golden cases (born range, unresolved refusal, rekey, pivot rejection) | `T10 test_golden_fib_fixtures_reproduce` | P |
| J6 fixture manifest hashes recorded (LF-normalized) | `T10 test_fixture_manifest_hashes_recorded` + review §4 | P + R |
| J7 synthetic fixtures labeled; never evidence | `T10 test_synthetic_fixtures_labeled` | P |
| J8 later-bloc golden-program cases deferred, never claimed | `T10 test_deferred_golden_program_cases_disclosed` + review §5 | P + R |

### §K Acceptance III.2 (frozen clause set)

| Clause | Test(s) | Result |
|---|---|---|
| K-a measurements reproduce frozen fixtures | `T10` J1–J5 | P |
| K-b no prediction/signal vocabulary | `T11 test_no_prediction_or_signal_vocabulary` | P |
| K-c coordinate generation requires eligible anchor/range | `T3` C2–C4 + `T4` D4 | P |
| K-d distinctions survive serialization | `T6` F8 + `T11 test_serialization_roundtrip_preserves_distinctions` | P |
| K-e provenance complete | `T9` I1–I7 | P |

### §L Book-level gate §Measurements

| Clause | Test(s) | Result |
|---|---|---|
| L1 golden ranges/tiers/AU/coordinates/clocks/path reproduce | `T10` J1–J5 + `T2` B2–B4 + `T5` E6 + `T6` F1 | P |
| L2 provenance accompanies measurements | `T9` I1–I7 | P |
| L3 no arbitrary anchor coordinate generation | `T3` C2–C5 + `T4` D5 | P |

### §M Failure behavior (clauses landing on this layer)

| Clause | Test(s) | Result |
|---|---|---|
| M1 incomplete data ⇒ blocked/degraded, never fabricated | `T1` A7 + `T9` I6 | P |
| M2 clock/session unresolvable ⇒ `NO_CALCULATION` | `T5` E7 | P |
| M3 anchor unresolved ⇒ coordinates blocked | `T3` C2 + `T4` D4 | P |
| M4 version missing ⇒ `MODEL_VERSION_UNAVAILABLE` | `T2` B9 | P |
| M5 evidence missing ⇒ no unsupported statistic attached | `T9` I8 | P |
| M6 layer conflict ⇒ conflict facts, no confluence score | `T8` H5 | P |
| M7 provider/feed failure consumed unchanged via III.1 contract; stale serving is III.6 | review §8 | R |

### §N Cross-model invariants

| Clause | Test(s) | Result |
|---|---|---|
| N1 invariant #2 calibration is local | `T2` B5 | P |
| N2 invariant #3 range/anchor before coordinates | `T3` C4 | P |
| N3 invariant #4 tier is compression, not force | `T2` B7 | P |
| N4 invariant #5 time never calls the play | `T5` E8 | P |
| N5 invariant #6 touch ≠ acceptance | `T6` F4 | P |
| N6 invariant #7 reach ≠ trade win | `T6` F9 | P |
| N7 invariant #8 first delivery retained independent of terminal | `T6` F2 (+ F5) | P |
| N8 invariant #9 rekey is a remapping transition | `T4` D3 | P |
| N9 invariant #10 range-left updates as states consume | `T1` A5 | P |
| N10 invariant #17 news conditions, never replaces geometry | `T7` G5 | P |
| N11 invariant #18 no deterministic rhetoric in status labels | `T11 test_status_labels_factual_enum_only` | P |

### §O Authority-model preservation (Book I Phase 3)

| Clause | Test(s) | Result |
|---|---|---|
| O1 measurements are not models/claims/evidence/setups | `T12 test_no_book1_authority_imports` | P |
| O2 III.2 never grants itself evidence authority | `T12 test_no_corpus_writes` + review: fixture evidence refs are read-only citations by id | P + R |
| O3 historical observation ≠ current market state | `T12 test_fixtures_labeled_historical` | P |
| O4 simulation ≠ empirical performance | `T10` J7 | P |
| O5 provider output ≠ canonical truth (inputs only via III.1 contract) | review §8 | R |
| O6 no trading/game concepts (`trigger_levels` disclosed exception) | `T12 test_no_trading_or_game_concepts` | P |

### §P Boundaries and security

| Clause | Test(s) | Result |
|---|---|---|
| P1 no network anywhere | `T12 test_no_network_calls` (import scan + socket monkeypatch guard over the full pipeline) | P |
| P2 no new persistence migration (`[1, 2, 3, 4]`) | `T12 test_discover_migrations_unchanged` | P |
| P3 readiness seam untouched | `T12 test_market_data_readiness_seam_unchanged` | P |
| P4 frozen surfaces unmodified (Book II 50 hashes, 23 pins, Book I manifest, III.1 11 module hashes) | `T12 test_frozen_manifests_unchanged`, `T12 test_iii1_interfaces_unchanged` | P |
| P5 no secrets/credentials/PII; bounded enums | `T11 test_bounded_enums_no_free_text`, `T12 test_no_credentials_in_data_path` | P |
| P6 no Book I/II/III.1 test weakened or deleted | review §7 (diff scope) + full regression §10 | R |
| P7 deterministic and offline | `T12 test_deterministic_repeat_runs` | P |
| P8 no production adapters or speculative runtime | review §7 (diff scope) | R |
| P9 measurements immutable; redefinition needs a new version | `T11 test_measurements_immutable` | P |

## 3. Test-group results (T1–T12)

Focused suite `python -m pytest tests/test_forge_measurements.py -q`:
**87 passed, 0 failed, 0 skipped, 0 xfailed** (86 binding names + 1 gained
J8 test; the map may gain tests, never lose or weaken one).

| Group | Scope | Tests | Result |
|---|---|---|---|
| T1 | Range engine | 8 | PASS |
| T2 | Calibration | 10 | PASS |
| T3 | Coordinates | 5 | PASS |
| T4 | Anchors / Range Birth interface | 5 | PASS |
| T5 | Clock / state age | 8 | PASS |
| T6 | Path measurements | 9 | PASS |
| T7 | Event / news features | 5 | PASS |
| T8 | Higher order | 5 | PASS |
| T9 | Provenance | 8 | PASS |
| T10 | Golden fixtures | 8 (7 binding + J8 gain) | PASS |
| T11 | Label / serialization discipline | 5 | PASS |
| T12 | Boundaries / security | 11 | PASS |

## 4. Golden-fixture manifests and provenance

- `fixtures/FIXTURE_MANIFEST.json` records sha256 of all 9 fixtures over
  **LF-normalized** content, so the manifest verifies identically on the
  Windows CRLF worktree and the Linux LF CI checkout (the BA-17 `8b43cb4`
  lesson, re-applied at authoring time).  `T10
  test_fixture_manifest_hashes_recorded` verifies every recorded hash
  and the manifest↔disk file set.
- The committed `generate_fixtures.py` reproduces every fixture
  byte-for-byte; it is the single source of the golden numbers.
- Provenance labels travel on every record: bar slices and event
  records are `SYNTHETIC_FIXTURE` with a `data_classification` string
  that begins with the label and states "not empirical market evidence
  and never citable for performance claims"; calibration tables and
  doctrine (EUR Phase1 tiers, BTC Tracker tiers/AU/thresholds/zones,
  XAU bands, weekly tier medians, JPY DT structures) are
  `CANONICAL_SOURCE_SLICE` with `source_ref` + evidence id
  (`EV.EUR.DAILY.PHASE1_TIERS.V1`, `BTC.TRACKER.DWM.V1`,
  `EV.EUR.WEEKLY.TIER_RANGE.V1`, `XAU.GAME.L1_L2_L3.V1`,
  `JPY.CARRY_GAME.L1_L3.V1`, `EV.XAU.PROMOTION.*`).
- Synthetic fixtures are labeled at creation and structurally cannot
  become evidence: a III.1 `SYNTHETIC_FIXTURE` bar refuses any
  evidence `source_ref` at construction, and measurements over
  synthetic bars carry `evidence_refs == ()` (verified in T10 J7 and
  T9 I8).

## 5. Model-native calibration boundary tests

- **EUR Daily Phase1** (`EV.EUR.DAILY.PHASE1_TIERS.V1`,
  `FROZEN_LAUNCH`): every boundary edge asserted individually —
  0→T1, 19.999→T1, 20→T2, 29.999→T2, 30→T3, 44.999→T3, 45→T3
  (upper inclusive), 45.001→NO_GO, 120→NO_GO.  Expansion multipliers
  are deliberately not encoded (the card states them approximately and
  they are model-level expectations, not measurements).
- **BTC Tracker DWM** (`BTC.TRACKER.DWM.V1`, `FROZEN_LAUNCH`):
  749.99→T1, 750→T2, 1699.99→T2, 1700→T3, 3000→T3 (upper inclusive),
  3000.01→NO_GO; AU 205/545/1160 as **dollar counts** (BTC native step
  = $1); threshold levels 246/654/1392 (canonical name
  `trigger_levels` preserved verbatim, disclosed as thresholds not
  execution triggers per PLAN §6); density zones 164–246 / 436–654 /
  928–1392.
- **XAU Game** (`XAU.GAME.L1_L2_L3.V1`, `RESEARCH`): spatial bands, not
  an EUR-style tier table (III.2-GAP-3).  Probes: 30→NORMAL,
  50→FAILURE (lower-inclusive edge), 68→REPAIR (open-ended canonical
  "68+ repair" band), 105→SNAP (narrowest-band rule over the overlapping
  REPAIR band); 20→ explicit `UNCLASSIFIED_VALUE` refusal (no
  nearest-bucket guessing).  The promotion examples 68+8h→80 (42/48)
  and 120+8h→132 (24/25) exist only as fixture disclosures with
  small-N standing and the explicit text "not a trade win rate, not an
  entry probability and not an executable expectancy"; no calibration
  encodes them (asserted).
- **JPY Carry Game**: the card publishes DT structure levels
  132/168/187.5 and a 12–4PM research window but **no** per-pair
  tier/AU table (III.2-GAP-2); a JPY tier lookup refuses
  `MODEL_VERSION_UNAVAILABLE` instead of inventing a table.
- **Cross-asset locality**: an EUR pip magnitude against the BTC table
  (and vice versa, and a foreign unit against a familiar instrument)
  refuses `CALIBRATION_TRANSFER_REFUSED`; no global tier constant
  exists in the package; every lookup requires the explicit four-part
  key with no default.

## 6. Anchor / R15 limitation and refusal behavior

- `AnchorStatus` vocabulary is exactly
  `UNRESOLVED | ELIGIBLE | ACTIVE | INVALIDATED | REKEYED`; a plain
  string fails with `INVALID_ANCHOR_STATE`.
- The canonical R15 Range Birth eligibility rule is **not materialized**
  in the frozen corpus (III.2-GAP-1), therefore: `ANCHOR_RULE_REGISTRY`
  is **empty** (no production rule, no generic-pivot fallback), the
  package contains **no anchor generator** (AST scan: no pivot finder,
  no anchor synthesizer; bars never become anchors), an anchor is a
  *declared input*, and `evaluate_anchor` reports — never promotes —
  with `automation_ready` always `False`.
- Refusals are explicit and typed: non-earned states →
  `ANCHOR_NOT_EARNED` at projection; eligibility reports carry
  `ANCHOR_UNRESOLVED` / `ANCHOR_INVALIDATED` / `ANCHOR_REKEYED`;
  REKEYED is a remapping transition whose prior record is returned
  untouched (verified by before/after equality).
- Golden Fib fixture: born range → all 11 declared families project to
  the committed prices; unresolved/invalidated anchors refuse; the
  rekey transition carries its mapping; the arbitrary local pivot case
  refuses `ANCHOR_NOT_EARNED`.  The deferred automation case
  `FIB.R15.AUTOMATION_APPROVAL` is disclosed, never claimed (J8).
- The ladder never auto-extends: EUR declares exactly the card's
  100/125/132/168/185; asking a canonical-but-undeclared level refuses
  `COORDINATE_FAMILY_NOT_EARNED`; XAU's 132 projection never yields a
  168 (the set has no 168 family and the refusal is asserted).

## 7. Frozen-file and III.1 interface integrity (executable)

- **Diff scope** since the planning head `9b7def3`: exactly 25 new
  files — `app/forge/measurements/` (12), the III.2 fixtures directory
  (12) and `tests/test_forge_measurements.py`.  Zero modified or
  deleted tracked files; no Book I/II file, no III.1 module, no
  container wiring, no migration appears in the ladder.
- `T12 test_frozen_manifests_unchanged`: all **50** Book II frozen
  contract hashes still bind the worktree (raw/LF/CRLF candidate
  comparison); the Book I freeze manifest is byte-identical to HEAD;
  all **23** planning pins exist and — where the pinned commit objects
  are available locally — each pinned file still matches its committed
  content (shallow-clone limitation disclosed, same as III.1).
- `T12 test_iii1_interfaces_unchanged`: the **11** III.1 module
  prefix/suffix hash pairs recorded in III.2 PLAN §6 all verify against
  the current worktree (raw and EOL-normalized candidates), after this
  bloc's edits.
- `T12 test_discover_migrations_unchanged`: `discover_migrations() ==
  [1, 2, 3, 4]`; no `005_*.sql` exists.
- `T12 test_market_data_readiness_seam_unchanged`: the container's
  `market_data: NOT_CONFIGURED` disclosure is byte-identical and the
  measurements package imports no composition-root symbol.
- The focused suite itself asserts all of the above on every run, so
  regression against frozen surfaces is continuously executable.

## 8. Historical / replay determinism and layering

- `T12 test_deterministic_repeat_runs`: a full golden pipeline run
  twice (fresh constructions, injected clocks) produces byte-identical
  JSON; wall-clock APIs (`datetime.now`, `utcnow`, `time.time`,
  `random`) are absent from the package (regex scan, executed).
- Serialization determinism: `encode_value` output is stable and every
  sample measurement round-trips losslessly (`decode_value` equality),
  so the touch/acceptance/path distinctions survive JSON exactly
  (T11).
- All inputs arrive via III.1's normalized, finality-gated,
  quality-flagged `Bar` contract; the package contains no raw-feed path
  and no provider import (O5 review; T12 O1 executable).  III.1's
  provider-failure explicit-state contract is consumed unchanged;
  stale *serving* remains an III.6 product-policy concern (M7 review).
- Session/clock resolution reuses the III.1 registry unmodified: an
  unknown session or lineage refuses `NO_CALCULATION`; DST-sensitive
  assertions run against real IANA zone data (America/New_York,
  March-2026 pre-DST window plus an evening-boundary research-day
  shift).

## 9. Implementation defect record (found and fixed at cause)

Recorded for honesty; all fixed append-only, without touching any
frozen contract, and re-verified by the focused + full suites.

1. **Fixture generator (pre-commit)** — the EUR/FIB coordinate-ladder
   expectations added native pip counts to a price
   (`1.07900 + 25 = 26.079`), which is dimensionally invalid.  Root
   cause: the generator offset used `size_in_pips × level/100` instead
   of the price-space span.  Fixed to `low + (high − low) × level/100`
   and all fixtures + manifest hashes regenerated **before** the
   fixtures were committed; the engine's price-space projection was
   already correct.
2. **`state_age.SessionPhase`** — the measured-session field collided
   with the provenance envelope's `session_id` keyword (`TypeError`).
   Caught by T5 E6.  Fixed so the record's `session_id` is the
   *measured* session identity, overriding the envelope value.
3. **`calibration.classify_spatial_band`** — a value matching exactly
   one open-ended band (the canonical XAU "68+ repair" band) refused as
   "only open-ended bands".  Caught by the golden 68→REPAIR probe.  A
   single matching band is unambiguous; the narrowest-band rule now
   applies only when two or more bands match (equally narrow matches
   still refuse).
4. **`coordinates` family ids for 61.8** — entry families were declared
   `FIB_61.8`/`XAU_61.8` (dot) while the canonical-level resolver and
   the golden ladders spell the token `61_8`; the ladder lookup failed.
   Caught by the Fib/XAU golden ladders.  `_entry_families` now emits
   the underscore spelling for every model set.

No acceptance test was weakened, skipped, marked xfail or removed to
make anything pass; every fix is at the cause.

## 10. Regression and CI results

- **Focused suite** (`tests/test_forge_measurements.py`): 87 passed.
- **Full repository suite** (`python -m pytest -q`, the exact CI
  command): **1168 passed, 29 skipped** (the 29 skips are the
  pre-existing Postgres-gated integration tests that require the CI
  database service), 4 pre-existing FastAPI deprecation warnings, no
  failures, no errors.  Book I, Book II and the III.1 frozen suites are
  green and unchanged.
- **Postgres jobs** cannot run on this Windows worktree (no local
  Postgres service); they run in CI.  Nothing in this bloc touches
  persistence, so the Postgres jobs exercise unchanged code paths; the
  migration-baseline assertion (`[1, 2, 3, 4]`) is enforced locally and
  in the `test` job.
- **CI (final head `a49426e`, run `39452067887`):** both jobs green —
  `test` ✓ (26s) and `postgres` ✓ (53s, full suite against live
  pgvector Postgres).  The Linux LF checkout also re-verifies the
  fixture manifest's EOL-independent hashes (the BA-17 lesson
  validated across platforms).  Only pre-existing action-runner
  deprecation annotations (Node 20 / ubuntu-latest migration), no
  test failures.

## 11. Known gaps and dispositions

Each gap states what was implemented, what remains unresolved, what
evidence would resolve it, and whether it blocks this measurement
contract or only downstream automation/serving.

### III.2-GAP-1 — canonical R15 Range Birth eligibility rule not materialized

- **Implemented:** the full five-state anchor interface, first-class
  eligibility reporting with refusal codes, rekey transitions, and the
  structural guarantees that no anchor generator and no R11 fallback
  exist; `automation_ready` is hard-`False` at this layer.
- **Unresolved:** the canonical eligibility rule itself (which born
  ranges earn ELIGIBLE).
- **Resolving evidence:** a frozen canonical source materializing the
  R15 rule, ratified into the corpus, registered as `CANONICAL` in
  `ANCHOR_RULE_REGISTRY`.
- **Blocking scope:** does **not** block the III.2 measurement
  contract; blocks autonomous Range Birth determination and any III.3/5
  automation of eligibility.

### III.2-GAP-2 — JPY pair-native tier tables only partially canonical

- **Implemented:** JPY DT structure families (132/168/187.5, 187.5 as
  declared extension) from the JPY card, per-pair clock declarations,
  and the asset role map as a declaration; tier lookups refuse
  `MODEL_VERSION_UNAVAILABLE`.
- **Unresolved:** complete per-pair JPY tier/AU tables.
- **Resolving evidence:** canonical per-pair JPY calibration tables.
- **Blocking scope:** blocks JPY tier/AU classification downstream;
  JPY coordinate projection works today.

### III.2-GAP-3 — XAU calibration is spatial bands, not a tier table

- **Implemented:** the XAU spatial-band table with `RESEARCH` status,
  narrowest-band classification, boundary probes and refusal outside
  every band; promotion examples exist only as small-N disclosures.
- **Unresolved:** whether XAU will ever have an EUR-style tier table.
- **Resolving evidence:** a canonical XAU tier-table model card.
- **Blocking scope:** blocks EUR-style tier classification for XAU by
  design (a deliberate non-invention); XAU band measurement is live.

### III.2-GAP-4 — no event/news calendar in-repo

- **Implemented:** normalized event records (family, relevance,
  scheduled/actual times, optional band/size with explicit absence),
  subtractive residual budget arithmetic, refusal when neither size nor
  band is declared.
- **Unresolved:** real historical event data.
- **Resolving evidence:** operator-supplied canonical event slices.
- **Blocking scope:** blocks real-world event features downstream; the
  contract and arithmetic are tested over labeled synthetic events.

### III.2-GAP-5 — golden fixtures build on synthetic bars

- **Implemented:** deterministic labeled synthetic bar slices plus
  canonical constant tables cited by id; reproduction is a contract
  test.
- **Unresolved:** empirical reproduction over real market history.
- **Resolving evidence:** real historical bar slices under the Book III
  data-acquisition path (with III.1 GAP-1).
- **Blocking scope:** blocks any empirical/performance claim (none is
  made anywhere); does not block the measurement contract.

### III.2-GAP-6 — higher-order statistical definitions are evidence-bound

- **Implemented:** the structural containers (quarter/M1/M2/D1–D3
  seeds, unfinished side, weekly path, checkpoints, layer-conflict
  facts) with `UNRESOLVED` states where definitions are not
  materialized; statistical parameters referenced by evidence id, never
  hardcoded; no confluence score structurally possible.
- **Unresolved:** materialized statistical definitions (D3 prior
  strength, M1 correlation value, unfinished-side completion rate, M2
  shaping rule).
- **Resolving evidence:** canonical definitions travelling with their
  evidence cards.
- **Blocking scope:** blocks statistical higher-order parameters
  downstream; structural measurement is live.

### Carried III.1 gaps (unchanged, none blocks III.2)

- III.1 GAP-1 synthetic bar fixtures only (carried into III.2-GAP-5).
- III.1 GAP-2 sessions exist only where canonically defined; III.2
  consumes exactly those and refuses `NO_CALCULATION` otherwise
  (tested).
- III.1 GAP-3 the M5 final-bar rule is scoped to its source lineage.
- III.1 GAP-4 provider seam remains `NOT_CONFIGURED` (byte-identical,
  tested).
- III.1 GAP-5 scripted-streaming parity only; true live-feed parity
  deferred with GAP-4.
- Disclosed non-gaps: `STALE` is declared but never auto-set (no
  canonical staleness threshold); planning-pin content verification
  needs full history (CI is shallow — existence-only there).

## 12. Ratification recommendation and III.3 handoff conditions

**Recommendation: PASS — CLOSED (with carried gaps GAP-1…GAP-6).**

Grounds: every frozen clause of ACCEPTANCE §A–§P maps to a passing
executable test or a recorded review above; the 86 binding test names
all exist and pass (one test gained, none lost or weakened); the golden
fixtures reproduce at the measurement layer with hash-verified,
labeled provenance; all refusals are explicit and typed; the frozen
Book I/II/III.1 surfaces verify unchanged after the suite; the full
repository regression is green (1168 passed / 29 pre-existing
Postgres-gated skips); and the implementation diff is exactly the
authorized scope.  Notably **not** claimed: any strategy performance,
win rate, expectancy, probability or automation readiness — the record
is a measurement-contract sufficiency record only.

**III.3 prerequisite-readiness decision: READY under conditions.**

1. The III.2 measurement contracts (`MEASUREMENT_ENGINE_V1` plus the
   per-definition versioned records) are complete, deterministic,
   offline and provenance-complete, and may be consumed by the III.3
   model runtime as its measurement input layer.
2. III.3 must consume measurements as facts: it may layer versioned
   model interpretation on top, but may not redefine, re-round or
   re-derive any measurement (core law; immutability + definition
   version drift refusal are enforced).
3. Autonomous Range Birth eligibility remains gated: III.3 may declare
   anchors only where a `CANONICAL`-materialized rule exists; today
   none does (GAP-1), so anchor declaration stays fixture/governed
   input and `automation_ready` stays `False`.
4. III.3 must not convert any measurement (tier, coordinate, path
   event, promotion disclosure, conflict fact) into a prediction,
   signal, setup or expectancy without a separately ratified model
   card and evidence id.
5. This record does **not** authorize III.3 or any later bloc; a new
   operator handoff packet is required (authorization stop condition 5).
