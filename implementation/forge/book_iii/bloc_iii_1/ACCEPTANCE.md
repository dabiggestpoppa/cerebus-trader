# BOOK III / BLOC III.1 — MARKET DATA & CLOCK CONTRACTS — ACCEPTANCE.md

Status: **PROPOSED — clause→test mapping frozen at planning time**
(before any implementation, per the Book III gate §Evidence pack order).
Date: 2026-10-12
Branch: `forge` · Planning head: `9b343b6c8f3d62084ff1d995e40dc9d91a60a0ed`
Frozen source of every clause below:
`planning/forge/books/BOOK_III_CEREBUS_MARKET_INTELLIGENCE_PLAN_V1.md`
(§BLOC III.1, Ch III.1.1–III.1.9 + Acceptance III.1; §CROSS-MODEL
INVARIANTS; §FAILURE BEHAVIOR; §ACCEPTANCE/RATIFICATION GATE §Data/clock;
§EXCLUSIONS) — pinned at `planning/forge/PLANNING_FREEZE_MANIFEST_V1.md`.
Dependency ratifications relied on: Book I I.5 `686faa7` (CLOSED),
Book II final G-F7 `e45d233` (contracts frozen, 50-file manifest),
planning freeze head `60e0675`.

Conventions (same as frozen Book II blocs): **test** = executable test
proposed for the future focused suite `tests/test_forge_market_data.py`
with fixtures under `implementation/forge/book_iii/bloc_iii_1/fixtures/`
(authored only under a separate implementation authorization);
**review** = inspection recorded in the future `EVIDENCE.md`. Test IDs
`T1`–`T11` are the groups defined in `PLAN.md` §8. This mapping may gain
tests at implementation time; it may never lose or weaken one — any
deviation is reported, not silently absorbed.

---

## A. Instrument identity (Ch III.1.1)

- A1 Canonical schema has all frozen fields — instrument_id, symbol/
  provider aliases, asset class, quote/base conventions, tick/pip/point
  unit, price precision, supported clocks/timeframes, provider mappings —
  test: `T1 test_instrument_schema_has_all_frozen_fields`.
- A2 Asset-native units mandatory — test: `T1 test_native_unit_enum_per_instrument`;
  EUR pip vs Gold point vs BTC dollar cross-unit arithmetic **refuses**
  (`T1 test_cross_native_unit_arithmetic_refuses`); no global unit
  constant exists (`T1 test_no_global_unit_constant`).
- A3 Aliases resolve to exactly one canonical instrument — test:
  `T1 test_alias_resolves_to_single_canonical_id` (symbol and provider
  alias tables; collision fails closed).
- A4 Price precision and quote/base conventions enforced — test:
  `T1 test_price_precision_and_quote_base_enforced` (values outside the
  declared precision/convention fail closed, never silent rounding).
- A5 Supported clocks/timeframes are declared per instrument; an
  unsupported clock is refused — test: `T1 test_declared_clocks_only`
  + `T7 test_unsupported_clock_fails_closed` (→ G4).

## B. Bar contract (Ch III.1.2)

- B1 Normalized bar carries exactly the frozen fields — instrument,
  timeframe, open_time, close_time, OHLC, volume when available,
  provider, finality, source timestamp, quality flags — test:
  `T2 test_bar_contract_frozen_fields`.
- B2 No future/incomplete bar treated as final — test:
  `T2 test_future_incomplete_bar_never_final`.
- B3 Duplicate bars deterministic — test:
  `T2 test_duplicate_bars_deterministic_single_result` (same input order
  permutations ⇒ identical output).
- B4 Revisions explicit — test: `T2 test_revision_is_explicit_revised`
  (replacement emits `REVISED`; silent overwrite impossible).
- B5 Missing bars visible — test: `T2 test_missing_bar_is_gap_never_synthesized`.

## C. Timezone/DST engine (Ch III.1.3)

- C1 Named (IANA) timezone semantics used for live/session calculation —
  test: `T3 test_session_math_uses_iana_named_zone` (stdlib `zoneinfo`,
  no fixed-offset arithmetic in the live path).
- C2 Fixed EST/no-DST research artifacts retain their original clock
  identity — test: `T3 test_fixed_offset_artifact_retains_clock_identity`
  (a `EST_NO_DST`-style identity round-trips; **no silent conversion** to
  named-zone time).
- C3 Spring-forward boundary — test:
  `T3 test_dst_spring_forward_session_boundary`.
- C4 Fall-back boundary — test:
  `T3 test_dst_fall_back_session_boundary` (repeated hour resolves
  deterministically).

## D. Research-day ownership (Ch III.1.4)

- D1 Explicit session-day assignment (function of lineage + bar close
  time, never `date()`), test: `T4 test_research_day_assignment_explicit`.
- D2 Known EUR/BTC evening bars assign to the following research day
  where the canonical source specifies — test:
  `T4 test_evening_bar_following_research_day` (cited to the canonical
  model-card/evidence id; no other lineage silently inherits the rule).
- D3 No calendar-date assumption — test:
  `T4 test_research_day_differs_from_naive_calendar_date` (lineage
  fixture where assignment ≠ UTC/calendar date).
- D4 Deterministic — test: `T4 test_research_day_deterministic`
  (identical input ⇒ identical research day; pure function).
- D5 Ambiguous lineage fails closed — test:
  `T4 test_ambiguous_lineage_fails_closed` (explicit unresolved state,
  never a default calendar guess).

## E. Session definitions (Ch III.1.5)

- E1 Versioned session objects exist for the frozen list — Asian range,
  London/MLR, daily checkpoints, weekly seed windows, model-specific DT
  windows, month/quarter boundaries — test:
  `T5 test_registry_covers_canonical_session_families` (only where a
  canonical definition exists; absent definitions are disclosed gaps —
  PLAN §10 gap G2, never invented).
- E2 Session definitions belong to model/calibration versions — test:
  `T5 test_session_bound_to_model_and_version` (lookup key includes
  model_id + model_version; cross-version reuse fails).
- E3 Registry is versioned — test:
  `T5 test_session_registry_version_recorded` (`session_registry_version`
  emitted with any derived state; feeds the Book III final record).
- E4 Unknown/unresolvable session ⇒ `NO_CALCULATION` — test:
  `T5 test_unknown_session_no_calculation` (explicit outcome, never
  empty-success; matches §FAILURE BEHAVIOR).

## F. Final-bar semantics (Ch III.1.6)

- F1 Exact inclusive/exclusive boundaries encoded — test:
  `T6 test_boundary_inclusive_exclusive_edges` (each edge asserted
  individually).
- F2 Canonical example: M5 `02:55` is the final bar of the 19:00–03:00
  construction where the canonical source specifies it — test:
  `T6 test_canonical_m5_0255_final_bar` (cited to its canonical source;
  other models' rules come from their canonical sources or remain
  disclosed gaps — PLAN §10 gap G3).
- F3 Finality is distinct from `NONFINAL`; a nonfinal bar cannot enter a
  final-state calculation — test: `T6 test_nonfinal_excluded_from_final_state`
  (duplicates Acceptance III.1-c below as its direct mechanism).

## G. Data quality (Ch III.1.7)

- G1 Exactly the frozen flag vocabulary exists — COMPLETE, GAP,
  DUPLICATE, REVISED, STALE, NONFINAL, OUTLIER_SOURCE,
  UNSUPPORTED_CLOCK — test: `T7 test_quality_flag_vocabulary_exact`
  (no additions/renames; unknown flag refused).
- G2 Models declare which flags block calculation vs warn — test:
  `T7 test_blocking_vs_warning_declaration_honored`.
- G3 Blocking flag ⇒ `DATA_QUALITY_BLOCKED`; warning flag ⇒ explicit
  degraded state — test: `T7 test_blocking_vs_degraded_outcomes`
  (matches §FAILURE BEHAVIOR; degraded is disclosed, not silent).
- G4 `UNSUPPORTED_CLOCK` fails closed, never silently remaps — test:
  `T7 test_unsupported_clock_never_silently_remapped`.
- G5 Flags are bounded enums with no free-text payload — test:
  `T7 test_quality_flags_bounded_no_free_text` (security: no
  credential/PII carrier in the data path).

## H. Provider normalization (Ch III.1.8)

- H1 Provider adapters map raw feeds into the normalized contract — test:
  `T8 test_raw_feed_normalizes_to_contract` (scripted fake raw feeds
  only; **no network, no real provider SDK** — PLAN §3).
- H2 Provider-specific timestamps/symbols never enter model logic —
  test: `T8 test_no_provider_fields_in_normalized_output` (raw provider
  key/field names absent from serialized normalized objects).
- H3 Deterministic normalization — test:
  `T8 test_fake_feeds_normalize_identically` (repeated runs byte-equal).
- H4 Provider-normalization parity (Book III gate §Data/clock) — test:
  `T8+T9 test_provider_normalization_parity` (alias-converted and
  native-converted feeds of the same slice yield identical canonical
  bars).

## I. Historical/live parity fixtures (Ch III.1.9)

- I1 Known source slices committed as frozen fixtures — test/review:
  `T9 fixture manifest hash recorded` + review: each real-slice fixture
  cites its canonical evidence id; synthetic bars carry
  `SYNTHETIC_FIXTURE` (PLAN §10 gap G1).
- I2 Replay ≡ live-style streaming on normalized session ownership —
  test: `T9 test_replay_streaming_session_parity`.
- I3 Replay ≡ live-style streaming on quality state — test:
  `T9 test_replay_streaming_quality_parity`.
- I4 "Live-style streaming" is a scripted streaming runner over
  fixtures; true live-feed parity requires provider selection (PLAN
  gaps G4/G5, deferred) — review: disclosed in EVIDENCE, never claimed as done.
- I5 Scoping note (honest boundary): III.1.9's word *measurements* is
  satisfied here at the session-ownership/quality-state layer only;
  measurement parity itself (Ch III.2) is tested in III.2 — review
  recorded in EVIDENCE; III.1 must not implement a measurement engine.

## J. Acceptance III.1 (frozen clause set, verbatim drivers)

- J-a "DST/session adversarial suite passes" — test: `T3` group
  (C1–C4) **plus** adversarial cases `T3 test_dst_adversarial_suite`
  (session spanning the transition, boundary-time bars, fixed-offset
  artifact alongside named-zone data in one slice) and `T5` E4.
- J-b "research-day ownership deterministic" — test: `T4` D1–D4.
- J-c "nonfinal bars cannot contaminate final-state calculations" —
  test: `T2` B2 + `T6` F3
  (`T6 test_nonfinal_cannot_contaminate_final_state` end-to-end).
- J-d "provider aliases normalize to canonical instrument IDs" — test:
  `T1` A3 + `T8` H1
  (`T8 test_provider_alias_normalizes_to_canonical_id`).
- J-e "missing/ambiguous data produces explicit quality state, not
  invented bars" — test: `T2` B5 + `T4` D5 + `T7` G3
  (`T2 test_missing_or_ambiguous_never_invents_bars`, asserting the
  output contains a quality state and zero synthesized OHLC).

## K. Book-level gate §Data/clock

- K1 "session/DST/research-day tests pass" — test: J-a + J-b.
- K2 "nonfinal/missing bars handled explicitly" — test: J-c + B5.
- K3 "provider-normalization parity passes" — test: §H H4 + §I I2/I3.

## L. Failure behavior (clauses landing on this layer)

- L1 Incomplete data ⇒ `DATA_QUALITY_BLOCKED` or model-declared
  degraded — test: `T2` B5 + `T7` G3.
- L2 Clock/session unresolvable ⇒ `NO_CALCULATION` — test: `T5` E4 +
  `T7` G4.
- L3 Provider/feed fails (or fixture feed ends) ⇒ explicit state, never
  invented bars — test: `T2` B5 + `T8` H1; stale *serving* with data
  cutoff is an III.6 product-policy concern and is **out of scope**
  here (PLAN §3) — review in EVIDENCE.
- L4 §FAILURE BEHAVIOR clauses for anchor unresolved, model version
  missing, evidence missing, layer conflict — **N/A at III.1** (they
  belong to III.2–III.5 model/state layers) — review: scope exclusion
  recorded; III.1 must not pre-implement them.

## M. Applicable cross-model invariants

- M1 Invariant #1 "Data clock is part of model identity" — test:
  `T3 test_clock_identity_is_first_class_value` (`ClockIdentity` is a
  versioned, serializable value that travels with derived state).
- M2 Invariant #2 "Asset calibration is local unless transfer is
  validated" — test: `T1` A2 (`test_no_global_unit_constant`; no
  cross-asset unit or session rule transfer exists at this layer).
- M3 Invariant #18 "No deterministic rhetoric in runtime status labels"
  — test: `T10 test_status_labels_factual_enum_only` (flags/outcomes
  are factual enums; vocabulary checked; no outcome words like
  "guaranteed/certain" exist in the enum set).
- M4 Core law "downstream may consume, never silently redefine" —
  test: `T10 test_market_data_records_immutable` (frozen dataclasses;
  mutation raises; redefinition requires a new version field).
- M5 Book III final-record fields owned by this Bloc — market-data
  schema version + session/clock registry version — test:
  `T10 test_market_data_schema_version_recorded` (every serialized
  normalized object/set carries `market_data_schema_version`; the
  clock-registry version travels with `ClockIdentity`, complementing
  E3's `session_registry_version`; both feed the frozen Book III final
  record).

## N. CEREBUS authority-model preservation (Phase 3)

- N1 Model ≠ Claim ≠ Evidence ≠ Setup ≠ Artifact — III.1 emits only
  normalized data facts; no claim/evidence/setup/model object exists —
  test: `T11 test_no_book1_authority_imports` (no imports from
  `qa/`, `retrieval/`, `provenance/`, `canonical.py`).
- N2 III.1 never grants itself evidence authority — test/review:
  `T11 test_no_corpus_writes` (Book I freeze manifest hashes unchanged
  after the suite) + review: fixture evidence refs are read-only
  citations by id.
- N3 Historical observation ≠ current market state — test:
  `T11 test_fixtures_labeled_historical` (replay fixtures carry a
  historical/cutoff label; no API here serves them as current — III.6
  owns serving).
- N4 Simulation ≠ empirical performance — test:
  `T11 test_synthetic_fixture_labeled_at_creation`
  (`SYNTHETIC_FIXTURE` present from creation; such a bar cannot satisfy
  an evidence-reference check).
- N5 Provider output ≠ canonical truth — test: `T8` H2 + `T7` G1
  (every normalized observation is quality-flagged; raw feed state is
  never copied as a canonical status).
- N6 Semantic similarity ≠ evidence authority — N/A by construction —
  review: no retrieval/vector code in this Bloc (see N1 test).
- N7 BTC Tracker ≠ BTC Game; manual-parity/L3-L2-L1/ST-vs-P90
  distinctions — test: `T11 test_no_trading_or_game_concepts`
  (module-level check: no `game`/`setup`/`trigger`/`entry`/`win_rate`
  symbols in `app/forge/market_data/`; session names come from canonical
  session definitions only).
- N8 No promotion of quarantined sources — test:
  `T11 test_quarantined_sources_absent` (the 9 quarantined Book I
  source ids never appear in fixtures).

## O. Boundaries and security

- O1 No network anywhere in the suite — test:
  `T11 test_suite_makes_no_network_calls` (socket refusal guard +
  fixture-only inputs).
- O2 No new persistence migration — test:
  `T11 test_discover_migrations_unchanged` (`discover_migrations() ==
  [1, 2, 3, 4]` exactly; no `005_*` added).
- O3 Container readiness seam untouched — test:
  `T11 test_market_data_readiness_seam_unchanged`
  (`market_data: NOT_CONFIGURED` disclosure identical; composition root
  not rewired).
- O4 Frozen surfaces unmodified — test:
  `T11 test_frozen_manifests_unchanged` (Book II 50-file freeze hashes,
  23 planning pins, and Book I freeze manifest all verify after the
  suite runs).
- O5 No secrets/credentials/PII in the data path; any emitted events go
  through Book II redaction — test: `T7` G5 +
  `T11 test_no_credentials_in_data_path`.
- O6 No Book I/II test weakened or deleted — test/review: full
  regression suite green unchanged + review of diff scope (only new
  `book_iii/` + new test file) at implementation time.
- O7 Deterministic and offline — test: `T11 test_deterministic_repeat_runs`
  (two full runs produce identical results; injected clock, no
  wall-clock dependence).
- O8 No production adapters or speculative runtime capabilities —
  review: implementation diff limited to the PLAN §7 package; concrete
  provider SDKs, credentials and Book IV–VIII features absent.

---

## Coverage statement

Every frozen acceptance clause is mapped: Ch III.1.1–III.1.9 → §A–§I;
Acceptance III.1 (a–e) → §J; Book gate §Data/clock → §K; applicable
§FAILURE BEHAVIOR → §L; applicable cross-model invariants → §M;
authority-model and boundary/security clauses → §N–§O; the Book-gate
final-record fields III.1 owns (market-data schema version +
session/clock registry version) → §M M5 + §E E3. Zero unmapped
clauses. Out-of-scope gate sections (Measurements, Models, State/path,
Setups, API) and the remaining final-record fields (measurement engine
version, model runtime versions/hashes, setup registry version, golden
fixture program hashes, test counts, unresolved research gates) belong
to III.2–III.6/Book-level close and are not claimed here.

## Known gaps (carried from PLAN §10, where they are labelled G1–G5;
re-keyed here as GAP-1…GAP-5 to avoid collision with clause IDs)

- GAP-1 (§10 G1): no real historical bar slices in-repo — synthetic
  fixtures labeled, cited refs when operator supplies slices.
- GAP-2 (§10 G2): sessions implemented only where a canonical
  definition exists.
- GAP-3 (§10 G3): final-bar rules beyond the canonical M5 example come
  from canonical sources or stay gaps.
- GAP-4 (§10 G4): concrete provider selection/wiring undetermined
  (seam stays `NOT_CONFIGURED`).
- GAP-5 (§10 G5): live parity proven against a scripted runner; true
  live-feed parity deferred with GAP-4.

## Stop conditions (report; never improvise)

1. A frozen clause that cannot be implemented without contradicting a
   Book I/II frozen contract or inventing a non-canonical session rule.
2. Any need to modify a frozen Book I/II file, the container readiness
   seam, or add a persistence migration.
3. Conflicting canonical sources (e.g., two session definitions for the
   same model/version) → operator/governance ruling required.
4. Being blocked on III.1 does **not** authorize starting III.2 or any
   other Bloc without a new operator handoff.

## Ratification requirement

At implementation time this Bloc is DONE only with: implementation
commit ladder, focused + full test output, `EVIDENCE.md` (including the
§J–§O verifications and every gap above), known-gaps list, and a
ratification record — per the frozen Book III gate §Evidence pack.
**STOP AFTER PLANNING: no implementation is authorized by this packet.**
