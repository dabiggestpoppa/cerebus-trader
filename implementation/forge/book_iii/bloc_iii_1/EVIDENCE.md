# BOOK III / BLOC III.1 — MARKET DATA & CLOCK CONTRACTS — EVIDENCE.md

Status: EVIDENCE
Date: 2026-10-13
Authority: BA-17 Rung 2 (operator-directed implementation, Bloc III.1 ONLY)
Start SHA: `6a14e78acd321d75ebb6850bca871e6dc21de052` (= `origin/forge` at start; HEAD == remote, tree clean except pre-existing untracked scratch dirs incl. `.bu_tmp/`, preserved untouched)
Planning inputs: PLAN.md + ACCEPTANCE.md committed at `fcad720`/`6a14e78`; planning freeze `60e0675`; Book I I.5 ratification `686faa7` (CLOSED); Book II G-F7 `e45d233` (contracts frozen, 50-file manifest)
Implementation head: `8b43cb423cb84ed58a21613da288bf3162cd4333`
CI on implementation head: FORGE Tests run `38446736874` — **completed / success** (jobs `test` + `postgres` both green)

## 1. Source and test file inventory

New package `app/forge/market_data/` (PLAN §7 module map + two support modules):

| Module | Chapter | Contents |
|---|---|---|
| `__init__.py` | — | export surface |
| `versions.py` | M5 | `MARKET_DATA_SCHEMA_VERSION` (clock-registry version lives with `ClockIdentity`, session-registry version with `SessionRegistry`) |
| `errors.py` | — | bounded refusal vocabulary (coded `MarketDataError` family) |
| `instruments.py` | III.1.1 | frozen `Instrument`, `NativeUnit` (PIP/POINT/DOLLAR), `NativePrice`, cross-unit refusal, alias/provider tables with fail-closed collision detection |
| `bars.py` | III.1.2, III.1.6 | frozen `Bar` (exact frozen fields + provenance + schema version), finality gate, `reconcile` (deterministic dedupe + explicit `REVISED`), `missing_opens`/`GapMarker`, `final_state_input` (F3/J-c), provider-excluded `content_digest` |
| `clocks.py` | III.1.3 | `ClockIdentity` (timezone rule, DST policy, rule epoch, registry version), IANA `zoneinfo` engine, `EST_NO_DST`-style fixed artifacts, fold-deterministic session math |
| `research_day.py` | III.1.4 | lineage-declared evening-shift rule; `(lineage, instrument, bar close time) -> research day`; unknown lineage ⇒ explicit `UNRESOLVED` |
| `sessions.py` | III.1.5, III.1.6 | versioned `SessionRegistry` keyed (model_id, model_version, session_id); 7-family vocabulary with documented-gap coverage; half-open/inclusive boundaries; exact-instant `CHECKPOINT` kind; `final_bar_open_utc` (M5 02:55) |
| `quality.py` | III.1.7 | exact 8-flag vocabulary, `QualityPolicy` block-vs-warn declarations (complete or refuse), outcome enums `OK/DEGRADED/DATA_QUALITY_BLOCKED/NO_CALCULATION` |
| `normalize.py` | III.1.8 | scripted provider field maps (fake_alpha/fake_beta), raw→contract mapping, bounded `RefusalReason` enum, feed assembly with gap detection |
| `parity.py` | III.1.9 | `replay_historical` / `stream_live` runners, `bar_ownership` (session + research day), `compare_parity` (I2/I3) |

Fixtures: `implementation/forge/book_iii/bloc_iii_1/fixtures/` — `eurusd_m5_slice.json`, `btcusd_m5_slice.json`, `raw_feed_fake_alpha.json`, `raw_feed_fake_beta.json`, `raw_feed_btcusd_fake_alpha.json`, `sessions_canonical.json`, `FIXTURE_MANIFEST.json`, `generate_fixtures.py`, `README.md`.

Focused suite: `tests/test_forge_market_data.py` — **65 tests**, all frozen T1–T11 clause names implemented verbatim plus gained adversarial tests (tests may be gained, never lost).

**No other file was touched.** No frozen Book I/II file, no planning file, no CI workflow, no migration, no container/service file appears in the ladder (§4 verifies).

## 2. Clause → test results (every mapped acceptance condition)

| Clause | Test(s) | Result |
|---|---|---|
| A1 frozen instrument fields | `test_instrument_schema_has_all_frozen_fields` | PASS |
| A2 native units; cross-unit refuses; no global constant | `test_native_unit_enum_per_instrument`, `test_cross_native_unit_arithmetic_refuses`, `test_no_global_unit_constant` | PASS |
| A3 alias → one canonical id (collision fails closed) | `test_alias_resolves_to_single_canonical_id` | PASS |
| A4 precision + quote/base enforced | `test_price_precision_and_quote_base_enforced` | PASS |
| A5 declared clocks/timeframes only | `test_declared_clocks_only` | PASS |
| B1 exact frozen bar fields | `test_bar_contract_frozen_fields` | PASS |
| B2 future/incomplete never final | `test_future_incomplete_bar_never_final` | PASS |
| B3 deterministic duplicates | `test_duplicate_bars_deterministic_single_result` | PASS |
| B4 explicit revisions | `test_revision_is_explicit_revised` | PASS |
| B5 missing bars visible, never synthesized | `test_missing_bar_is_gap_never_synthesized` | PASS |
| C1 IANA named-zone session math | `test_session_math_uses_iana_named_zone` | PASS |
| C2 fixed EST artifact retains identity | `test_fixed_offset_artifact_retains_clock_identity` | PASS |
| C3 spring-forward boundary | `test_dst_spring_forward_session_boundary` | PASS |
| C4 fall-back boundary (repeated hour deterministic) | `test_dst_fall_back_session_boundary` | PASS |
| D1 explicit assignment, never `date()` | `test_research_day_assignment_explicit` | PASS |
| D2 EUR/BTC evening → following research day (cited; no silent inheritance) | `test_evening_bar_following_research_day` | PASS |
| D3 differs from naive calendar date | `test_research_day_differs_from_naive_calendar_date` | PASS |
| D4 deterministic | `test_research_day_deterministic` | PASS |
| D5 ambiguous lineage fails closed | `test_ambiguous_lineage_fails_closed` | PASS |
| E1 session families covered (gaps disclosed, never invented) | `test_registry_covers_canonical_session_families` | PASS |
| E2 bound to model/calibration version | `test_session_bound_to_model_and_version` | PASS |
| E3 registry version recorded | `test_session_registry_version_recorded` | PASS |
| E4 unknown session ⇒ `NO_CALCULATION` | `test_unknown_session_no_calculation` | PASS |
| F1 inclusive/exclusive edges | `test_boundary_inclusive_exclusive_edges` | PASS |
| F2 canonical M5 02:55 final bar (cited) | `test_canonical_m5_0255_final_bar` | PASS |
| F3 nonfinal excluded from final state | `test_nonfinal_excluded_from_final_state` | PASS |
| G1 exact 8-flag vocabulary | `test_quality_flag_vocabulary_exact` | PASS |
| G2 block-vs-warning declaration | `test_blocking_vs_warning_declaration_honored` | PASS |
| G3 blocking ⇒ `DATA_QUALITY_BLOCKED`; warning ⇒ degraded | `test_blocking_vs_degraded_outcomes` | PASS |
| G4 unsupported clock fails closed, never remapped | `test_unsupported_clock_never_silently_remapped`, `test_unsupported_clock_fails_closed` | PASS |
| G5 bounded enums, no free text | `test_quality_flags_bounded_no_free_text` | PASS |
| H1 raw feeds normalize to contract | `test_raw_feed_normalizes_to_contract` | PASS |
| H2 provider fields absent from output | `test_no_provider_fields_in_normalized_output` | PASS |
| H3 deterministic normalization | `test_fake_feeds_normalize_identically` | PASS |
| H4 provider-normalization parity | `test_provider_normalization_parity` | PASS |
| I1 fixture manifest hash recorded | `test_fixture_manifest_hash_recorded` | PASS |
| I2 replay ≡ streaming session ownership | `test_replay_streaming_session_parity` | PASS |
| I3 replay ≡ streaming quality state | `test_replay_streaming_quality_parity` | PASS |
| J-a DST/session adversarial suite | `test_dst_adversarial_suite` | PASS |
| J-b research-day ownership deterministic | T4 group (D1–D4) | PASS |
| J-c nonfinal cannot contaminate final state | `test_nonfinal_cannot_contaminate_final_state` | PASS |
| J-d provider aliases → canonical id | `test_provider_alias_normalizes_to_canonical_id` | PASS |
| J-e missing/ambiguous ⇒ explicit state, zero invented bars | `test_missing_or_ambiguous_never_invents_bars` | PASS |
| K1/K2/K3 book-gate data/clock | J-a+J-b / J-c+B5 / H4+I2+I3 | PASS |
| L1/L2/L3 failure behavior | G3 / E4+G4 / B5+H1 (truncated-feed tail-gap test) | PASS |
| M1 clock identity first class | `test_clock_identity_is_first_class_value` | PASS |
| M2 asset calibration local | A2 group | PASS |
| M3 factual status labels | `test_status_labels_factual_enum_only` | PASS |
| M4 core law: immutable, versioned redefinition | `test_market_data_records_immutable` | PASS |
| M5 final-record fields owned by III.1 | `test_market_data_schema_version_recorded` | PASS |
| N1 no Book I authority imports | `test_no_book1_authority_imports` | PASS |
| N2 no corpus writes | `test_no_corpus_writes` | PASS |
| N3 historical ≠ current | `test_fixtures_labeled_historical` | PASS |
| N4 synthetic labeled at creation | `test_synthetic_fixture_labeled_at_creation` | PASS |
| N7 no trading/game concepts; sessions from canonical definitions only | `test_no_trading_or_game_concepts` | PASS |
| N8 quarantined sources absent | `test_quarantined_sources_absent` | PASS |
| O1 no network | `test_suite_makes_no_network_calls` | PASS |
| O2 migrations unchanged `[1,2,3,4]` | `test_discover_migrations_unchanged` | PASS |
| O3 readiness seam untouched | `test_market_data_readiness_seam_unchanged` | PASS |
| O4 frozen surfaces unmodified | `test_frozen_manifests_unchanged`, `test_planning_pins_unchanged` | PASS |
| O5 no credentials in data path | `test_no_credentials_in_data_path` | PASS |
| O7 deterministic, no wall clock | `test_deterministic_repeat_runs` | PASS |
| Extra (gained) | `test_final_bar_rules_not_generalized_beyond_canonical`, `test_unknown_provider_and_symbol_refused`, `test_streaming_arrival_order_independence` | PASS |

Zero unmapped clauses; zero failures. O6 (no Book I/II test weakened/deleted) and O8 (diff limited to PLAN §7 package) verified by diff scope: the ladder adds only `app/forge/market_data/`, `tests/test_forge_market_data.py` and `implementation/forge/book_iii/bloc_iii_1/` paths.

## 3. Test results

- Focused suite `tests/test_forge_market_data.py`: **65 passed** (Python 3.11.9, local Windows) and **65 passed** in CI.
- Full suite: **1081 passed, 29 skipped** (pre-existing skips: optional PostgreSQL-service cases) — 1016 prior + 65 new; Book I and Book II suites remain green with zero modifications.
- CI: run `38446736874` on `8b43cb4` — success, both jobs (`test`, `postgres`).

## 4. Frozen-file and integration integrity

- Book II contract freeze: **50/50 hashes** verified in-suite (EOL-tolerant comparison; PASS in worktree and in CI checkout).
- Planning freeze: **23/23 pins** verified locally (pin commit objects reachable: each pinned path compared EOL-normalized against its pinned commit); in shallow CI (checkout depth 1) the pin objects are unreachable and the test honestly verifies existence only — disclosed limitation.
- Book I freeze manifest: byte-identical to HEAD version after the suite (git comparison in-suite).
- `corpus/` tracked tree: unmodified (`git status` in-suite + no corpus I/O exists in the package by source scan).
- Migration discovery: `[1, 2, 3, 4]`; no `005_*.sql` exists; no migration added.
- Readiness seam `market_data: {NOT_CONFIGURED, required=False}` asserted **identical** to the frozen disclosure; the package imports nothing from the service composition root.

## 5. Historical / scripted-streaming parity results

EUR slice (99 records → 97 normalized bars after deterministic dedupe/revision): replay vs streaming — session parity ✓, quality parity ✓, bar-content parity ✓, outcome parity ✓; ownership maps byte-identical (95 `RESOLVED` on research day 2026-03-03 under `EUR_DAILY.ASIAN_RANGE`; 2 explicit `NO_SESSION`: the pre-boundary 18:55-local bar and the 03:00-local open). BTC slice: parity ✓ with checkpoint ownership on the exact 12:00 NY close. Provider parity: fake_alpha vs fake_beta (different symbol spellings, timestamp conventions, key names **and** arrival order) yield identical `content_digest`. Arrival-order independence proven for replay and streaming via rotations.

Disclosures: this is a **scripted streaming runner over committed fixtures**, not a live feed (I4; GAP-4/GAP-5). Measurement-result parity is out of scope here and belongs to III.2 (I5).

## 6. Boundary and DST adversarial results

- Spring-forward (2026-03-07→08): session UTC span 7h vs 8h wall; final-bar instant `2026-03-08T06:55Z` exists even though the local `02:55` wall label does not exist that day.
- Fall-back (2026-10-31→11-01): UTC span 9h (repeated hour); fold=0/fold=1 deterministic (05:30Z / 06:30Z) and stable across calls.
- Fixed `EST_NO_DST` artifact: identity round-trips; instants diverge from the named zone exactly at DST (no silent reinterpretation in either direction).
- Edges: window start inclusive, end exclusive; `end_inclusive` honored when declared; checkpoint matches exactly one wall time; a bar closing exactly at 19:00 stays on its research date (strict `>` on the boundary).
- Adversarial: ambiguous alias + provider-alias collision (fail closed), cross-unit arithmetic (refused), revision ordering permutations, interior and tail gaps (never synthesized), unsupported clock (explicit flag, no remap), shuffled feed orders.

## 7. Source and fixture provenance

- Bar slices and raw feeds: `SYNTHETIC_FIXTURE` — deterministic generated values, labeled at creation, and constructor-enforced incapable of carrying an evidence reference (N4 test). **Not empirical market evidence; cannot support performance claims.**
- `sessions_canonical.json`: `CANONICAL_SOURCE_SLICE` — every session definition and research-day lineage record cites its frozen corpus source (`EUR_DAILY_PHASE1_CALIBRATION_EVIDENCE_V1.md` evidence id `EV.EUR.DAILY.PHASE1_TIERS.V1`, `EUR_DAILY_NEWS_REKEY_MODEL_CARD_V1.md`, `BTC_DAILY_WEEKLY_MONTHLY_TRACKER_MODEL_CARD_V1.md`, plus PLAN Ch III.1.6 for the plan-canonical M5 rule); all cited paths verified to exist; the cited evidence id verified present in the corpus.
- Quarantined sources: 9/9 Book I quarantined paths verified absent from every fixture; their documented reasons re-derived from the canonicalizer.
- Conventional (non-corpus) market assumptions, disclosed: EURUSD pip 0.0001 with 5-decimal precision; XAUUSD point = $1.00 (corpus XAU bands such as 25–50/68/100–132 read as dollar magnitudes — a reading, disclosed, not a corpus claim); BTC dollar domain, 2-decimal precision. Native-unit enums stay distinct and non-convertible regardless of numeric size.
- Implementation choices, disclosed: evening shift applies when bar close wall time is **strictly after** 19:00; repeated-hour default is fold=0; `DAILY_CHECKPOINT` is modeled as an exact-instant `CHECKPOINT` (no invented window duration); `STALE` exists in the vocabulary and policies but is never auto-set (no canonical staleness threshold exists).

## 8. Known gaps (carried from PLAN §10 G1–G5; none closed without evidence)

- **GAP-1** (no real historical bar slices in-repo): OPEN — synthetic labeled fixtures used; operator-supplied slices replace them with evidence refs.
- **GAP-2** (sessions only where canonical definitions exist): OPEN — London/MLR, weekly-seed intraday window, DT binding (JPY 12–4PM named but DT→Carry binding requires a crosswalk ruling), and month/quarter boundary frames remain disclosed gaps in registry coverage output.
- **GAP-3** (final-bar rules beyond the canonical M5 example): OPEN — not generalized; other lineages resolve `NO_CALCULATION` (tested).
- **GAP-4** (concrete provider selection/wiring): OPEN — readiness seam stays `NOT_CONFIGURED`.
- **GAP-5** (true live-feed parity): OPEN — deferred with GAP-4; scripted parity only.

## 9. Commit ladder and CI

| Rung | Commit | Content |
|---|---|---|
| 0 | `6a14e78acd321d75ebb6850bca871e6dc21de052` | start state (HEAD == origin/forge, clean tree) |
| 1 | `8a95b55c03c3bd4963dbaedd15a66054839c7497` | deterministic fixtures + generator + provenance README |
| 2 | `faea521b8d29fc4356be14e77985d998a9e70f90` | `app/forge/market_data/` package |
| 3 | `1d331a7e491933aec93c7bca995b66b24be2dd3e` | focused acceptance suite (65 tests) |
| 4 | `5127fa7461803afb2a5dfaca706a9abb7f5c6978` | repair A: EOL-normalize the manifest check (incomplete — the manifest itself still recorded CRLF hashes; kept for honesty, superseded) |
| 5 | `8b43cb423cb84ed58a21613da288bf3162cd4333` | repair B: generator records LF-normalized hashes (root cause) — implementation head; push `6a14e78..8b43cb4` fast-forward; CI run `38446736874` success (test + postgres) |
| 6 | (this rung) | EVIDENCE.md + RATIFICATION.md |

Repair note (recorded, not concealed): the fixture generator's text-mode writes emit CRLF on Windows, so rungs 1–3 recorded a manifest whose hashes could not verify on the LF Linux CI checkout. Rung 4 addressed only the reader; rung 5 fixed the root cause (LF-normalized hashing at generation) and verified CI-equivalence against index blobs before push. Both repairs are append-only and touch nothing outside III.1's own fixture directory and test file.

## 10. Ratification-relevant limitations

1. True live-provider parity, provider wiring and stale-serving policy remain GAP-4/GAP-5/III.6 concerns.
2. Session coverage is deliberately partial (GAP-2); coverage output itself carries the disclosed gaps.
3. Planning-pin content verification requires full history; CI verifies pin-file existence only (shallow checkout).
4. Market-convention unit sizes (pip/point/dollar) are disclosed conventions, not corpus claims; changing them is a recalibration decision, not an implementation detail.
5. A CI PASS is necessary but not sufficient: this evidence pack — clause map, provenance, integrity and gap disclosures — is the sufficiency record.
