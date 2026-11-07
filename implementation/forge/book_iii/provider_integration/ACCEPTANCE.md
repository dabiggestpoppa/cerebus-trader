# BOOK III — WP-3 PROVIDER INTEGRATION — ACCEPTANCE

**Packet:** BA-24 Rung 1 (WP-3A) · **Companions:** `PLAN.md`,
`PROVIDER_DECISION_MATRIX.md`, `DEPENDENCY_HANDOFF.md`
**Status:** PROPOSED — binding only after an authorized WP-3B rung.

---

## 1. What acceptance means here

WP-3 has four acceptance layers, and they are **not interchangeable**:

| Layer | Proves | Proves nothing about |
|---|---|---|
| **A — selection** (this rung) | a defensible vendor decision with sources, terms and tradeoffs | that any vendor works |
| **B — contract** (mock adapter, no network) | the adapter obeys the frozen contracts and the parity/quality laws | live data, licensing, latency, cost |
| **C — external** (real credentials, licensed slices) | the real vendor returns usable, licensed observations | production readiness |
| **D — operational** | parity over a real window, recovery, readiness evidence | commercial launch (Book VIII) |

A green mock suite is never evidence that a provider works. A successful
connection is never evidence of readiness. No layer may borrow another's
verdict.

**Inventory: 72 unique test names** across T1–T10 — 66 contract (`M`) and 6
external (`X`). The count is authoritative: every name below appears exactly
once, and `PLAN.md` §13 quotes the same total.

---

## 2. Preconditions for any WP-3B execution

1. WP-3A decision ratified by the operator (`PROVIDER_DECISION_MATRIX.md` §5).
2. Additive III.1 registrations authorized in writing: three `PROVIDER_SCHEMAS`
   entries, provider mappings, and the three JPY instruments.
3. Frozen baselines re-verified: Book II 50 hashes, 79 modules, migrations
   `001`–`004`, `routes.py` `145757e0…`, `market_data: NOT_CONFIGURED`.
4. No credentials present, no network access in the test environment.

If (2) is refused, WP-3B does not begin; the contract is not bent to fit a
vendor.

---

## 3. Test inventory

Legend — **M**: mock/contract, no network, no credentials. **X**: external,
requires a licensed capture or credentials and runs only in a governed
environment. Source column cites the authority the assertion comes from.

### T1 — Adapter contracts (9)

| # | Test | Class | Source-backed condition |
|---|---|---|---|
| 1 | `test_adapter_identity_is_stable_per_provider` | M | III.1 `Bar.provider` is required and serialized; provider identity is provenance, not content |
| 2 | `test_adapter_capabilities_declare_instruments_and_timeframes` | M | III.1 `Instrument.supported_timeframes`; adapters must not claim undeclared coverage |
| 3 | `test_adapter_returns_provider_neutral_raw_candles` | M | III.1 Ch III.1.8: raw keys/symbols never reach normalized output |
| 4 | `test_adapter_refuses_naive_timestamps` | M | `normalize._parse_timestamp` refuses naive values; `Bar` requires tz-aware |
| 5 | `test_adapter_preserves_source_timestamp_separately` | M | `Bar.source_timestamp` distinct from `open_time`/`close_time` |
| 6 | `test_adapter_does_not_compute_sessions` | M | `sessions.SessionRegistry` is the sole session authority |
| 7 | `test_adapter_does_not_compute_research_day` | M | `research_day.assign_research_day` is lineage-declared |
| 8 | `test_adapter_does_not_aggregate_timeframes` | M | `bars.TIMEFRAME_MINUTES`; rollup is kernel scope (PLAN §6.4) |
| 9 | `test_adapter_rejects_unknown_symbol_before_network` | M | `InstrumentRegistry.resolve_provider` → `UnknownAliasError`/`UNKNOWN_SYMBOL` |

### T2 — Historical backfill (8)

| # | Test | Class | Source-backed condition |
|---|---|---|---|
| 10 | `test_backfill_paginates_without_window_gaps` | X | Provider pagination contracts (Polygon limit 50,000; OANDA 5,000/page; Kraken 720) |
| 11 | `test_backfill_reingest_is_idempotent` | M | `bars.reconcile` is order-independent |
| 12 | `test_backfill_window_digest_is_order_independent` | M | PLAN §9 source-window digest law |
| 13 | `test_backfill_duplicate_rows_reconcile_deterministically` | M | `QualityFlag.DUPLICATE`, stable tie-break |
| 14 | `test_backfill_revision_replaces_by_source_timestamp` | M | `QualityFlag.REVISED`; older rows never overwrite newer |
| 15 | `test_backfill_missing_window_is_reported_not_filled` | M | `missing_opens`; `GapMarker` never synthesizes OHLC |
| 16 | `test_backfill_resume_equals_full_run` | X | PLAN §9 checkpoint law |
| 17 | `test_backfill_stalled_window_fails_closed` | M | Stop on non-advancing window; no infinite loop |

### T3 — Live streaming/polling (8)

| # | Test | Class | Source-backed condition |
|---|---|---|---|
| 18 | `test_stream_marks_trailing_candle_nonfinal` | M | `assess_finality`; Kraken trailing candle is uncommitted |
| 19 | `test_stream_finality_transition_is_kernel_owned` | M | `finalize_for_cutoff` is the only finalizer |
| 20 | `test_stream_provider_complete_hint_cannot_override_cutoff` | M | OANDA `complete` is a hint; cutoff governs |
| 21 | `test_stream_late_correction_emits_revision` | M | `REVISED` by later source timestamp |
| 22 | `test_stream_out_of_order_arrivals_match_batch_order` | M | III.1 replay ≡ streaming |
| 23 | `test_stream_duplicate_delivery_is_suppressed` | M | `DUPLICATE` survivor rule |
| 24 | `test_stream_disconnect_preserves_last_canonical_state` | M | No partial bar promoted on disconnect |
| 25 | `test_stream_reconnect_requests_missed_window` | X | PLAN §9 reconnect law; provider `since`/range parameters |

### T4 — Sessions and clocks (8)

| # | Test | Class | Source-backed condition |
|---|---|---|---|
| 26 | `test_eur_research_day_shifts_after_1900_close` | M | `research_day` docs; EUR card 19:00–03:00 frame |
| 27 | `test_eur_spring_forward_final_bar_instant_exists` | M | III.1 EVIDENCE spring-forward result |
| 28 | `test_eur_fall_back_repeated_hour_is_deterministic` | M | `clocks.to_utc(fold=...)` |
| 29 | `test_btc_continuous_market_has_no_weekend_gap` | M | BTC card: 24/7, weekend transitions require ownership |
| 30 | `test_btc_checkpoint_matches_exact_1200_close` | M | BTC card 12PM NY checkpoint; `CHECKPOINT` semantics |
| 31 | `test_xau_session_ownership_refuses_without_canonical_definition` | M | III.1-GAP-2; XAU card names an entry lineage, not bounds |
| 32 | `test_jpy_dt_binding_refuses_without_crosswalk` | M | JPY card: DT→Carry binding forbidden without crosswalk |
| 33 | `test_adapter_does_not_invent_holiday_calendar` | M | No holiday calendar in corpus; silence → `GAP` |

### T5 — Parity (7)

| # | Test | Class | Source-backed condition |
|---|---|---|---|
| 34 | `test_historical_and_live_parity_on_source_slice` | X | III.1 I2/I3; PLAN §9 five-way parity |
| 35 | `test_parity_survives_delivery_permutation` | M | Order-independence of `reconcile` |
| 36 | `test_parity_holds_across_reconnect` | X | PLAN §9 reconnect equivalence |
| 37 | `test_parity_digest_excludes_provider_identity` | M | `content_digest` replaces provider with `<normalized>` |
| 38 | `test_parity_detects_injected_bar_drift` | M | Perturbed OHLC must change the digest |
| 39 | `test_parity_detects_missing_bar_difference` | M | `missing` participates in bar parity |
| 40 | `test_replay_reproduces_recorded_source_digest` | X | Recorded source slice hash equality |

### T6 — Quality propagation (7)

| # | Test | Class | Source-backed condition |
|---|---|---|---|
| 41 | `test_provider_outage_yields_data_quality_blocked` | M | `QualityPolicy` blocking; `DATA_QUALITY_BLOCKED` |
| 42 | `test_missing_source_window_yields_no_calculation` | M | `NO_CALCULATION` for unresolvable session/clock |
| 43 | `test_nonfinal_source_cannot_reach_final_state` | M | `final_state_input` excludes nonfinal; `NonFinalError` |
| 44 | `test_stale_label_is_carried_not_invented` | M | `STALE` declared, never auto-set (III.6-GAP-4) |
| 45 | `test_incomplete_history_degrades_with_gap` | M | `DEGRADED` when some bars excluded; `GAP` visible |
| 46 | `test_unsupported_clock_fails_closed` | M | `RefusalReason.UNSUPPORTED_CLOCK`; never remapped |
| 47 | `test_quality_outcome_reaches_snapshot_unchanged` | M | III.6 snapshot freshness/refusal passthrough |

### T7 — Multi-provider disagreement (7)

| # | Test | Class | Source-backed condition |
|---|---|---|---|
| 48 | `test_secondary_source_is_recorded_per_bar` | M | `Bar.provider` per observation; no anonymous blending |
| 49 | `test_source_disagreement_beyond_tick_blocks` | M | `OUTLIER_SOURCE` + blocking policy → `DATA_QUALITY_BLOCKED` |
| 50 | `test_source_agreement_within_tick_is_accepted` | M | Instrument `tick_size` tolerance |
| 51 | `test_failover_does_not_blend_providers_in_one_series` | M | PLAN §10 boundary disclosure |
| 52 | `test_failover_requires_retryable_failure` | M | II.5 taxonomy: only timeout/unavailable/rate-limited |
| 53 | `test_symbol_mapping_change_is_detected` | M | `AmbiguousAliasError`; mapping version |
| 54 | `test_source_clock_drift_is_detected` | M | Source timestamp vs canonical close skew |

### T8 — Security and credentials (6)

| # | Test | Class | Source-backed condition |
|---|---|---|---|
| 55 | `test_credentials_never_appear_in_logs_or_diagnostics` | M | II.5 redaction law; `redacted_diagnostics` booleans only |
| 56 | `test_missing_credentials_fail_closed_before_network` | M | Fail closed, no anonymous fallback |
| 57 | `test_provider_configuration_is_environment_isolated` | M | One credential per environment |
| 58 | `test_secret_rotation_requires_no_code_change` | M | Config-injected secrets |
| 59 | `test_request_budget_and_backoff_are_bounded` | M | Bounded retries, jitter, hard ceiling |
| 60 | `test_no_secret_material_in_fixtures_or_reports` | M | Fixtures are synthetic; scans for key-shaped strings |

### T9 — Readiness and recovery (6)

| # | Test | Class | Source-backed condition |
|---|---|---|---|
| 61 | `test_connection_success_alone_does_not_claim_readiness` | M | Readiness needs R1–R10 evidence |
| 62 | `test_readiness_requires_parity_evidence` | M | §6 R6 |
| 63 | `test_degraded_health_is_disclosed` | M | `DEGRADED` vocabulary, never hidden |
| 64 | `test_recovery_returns_to_ready_only_with_evidence` | M | Circuit half-open → close only after success |
| 65 | `test_shutdown_closes_stream_and_flushes_state` | M | Deterministic shutdown |
| 66 | `test_readiness_vocabulary_is_frozen` | M | `NOT_CONFIGURED`/`READY`/`DEGRADED`/`UNAVAILABLE` only |

### T10 — Frozen integration (6)

| # | Test | Class | Source-backed condition |
|---|---|---|---|
| 67 | `test_no_book_i_or_ii_file_changed` | M | Book I/II freeze |
| 68 | `test_book_iii_module_hashes_unchanged` | M | 79 modules, six package digests |
| 69 | `test_migration_set_unchanged` | M | `001`–`004` only |
| 70 | `test_routes_hash_unchanged` | M | `routes.py` `145757e0…` |
| 71 | `test_provider_seam_stays_not_configured_until_wp3d` | M | Seam flips only in 3D with Book II amendment |
| 72 | `test_cross_bloc_suite_still_green` | M | 96 integration tests + full regression |

---

## 4. Consolidated counts

| Group | Tests | M | X |
|---|---|---|---|
| T1 adapter contracts | 9 | 9 | 0 |
| T2 backfill | 8 | 6 | 2 |
| T3 live/stream | 8 | 7 | 1 |
| T4 sessions/clocks | 8 | 8 | 0 |
| T5 parity | 7 | 4 | 3 |
| T6 quality | 7 | 7 | 0 |
| T7 multi-provider | 7 | 7 | 0 |
| T8 security | 6 | 6 | 0 |
| T9 readiness | 6 | 6 | 0 |
| T10 frozen | 6 | 6 | 0 |
| **Total** | **72** | **66** | **6** |

External names: 10, 16, 25, 34, 36, 40.

---

## 5. Fixture acceptance

14 files: 12 cases + `FIXTURE_MANIFEST.json` + `FROZEN_BASELINE.json`.

| ID | Case | Provenance |
|---|---|---|
| FIX-01 | normal FX M5 sequence | `SYNTHETIC_FIXTURE` |
| FIX-02 | XAU session transition | `SYNTHETIC_FIXTURE` |
| FIX-03 | BTC 24/7 sequence | `SYNTHETIC_FIXTURE` |
| FIX-04 | FX DST spring-forward | `SYNTHETIC_FIXTURE` |
| FIX-05 | duplicate bars | `SYNTHETIC_FIXTURE` |
| FIX-06 | out-of-order bars | `SYNTHETIC_FIXTURE` |
| FIX-07 | missing-bar window | `SYNTHETIC_FIXTURE` |
| FIX-08 | nonfinal→final update | `SYNTHETIC_FIXTURE` |
| FIX-09 | corrected source candle | `SYNTHETIC_FIXTURE` |
| FIX-10 | disconnect/reconnect | `SYNTHETIC_FIXTURE` |
| FIX-11 | historical/live parity pair | `SYNTHETIC_FIXTURE` |
| FIX-12 | source-discrepancy refusal | `SYNTHETIC_FIXTURE` |

Rules: generation is deterministic and byte-identical (LF-normalized hashing);
`SYNTHETIC_FIXTURE` bars cannot carry an evidence reference; real acceptance
data is `SOURCE_SLICE` with a `source_ref`, licence note and capture timestamp.
No fixture may be described as real market history.

---

## 6. Readiness transition gate (WP-3D)

| Gate | Requirement | Evidence artifact | If absent |
|---|---|---|---|
| R1 | Authorized provider selection + written terms | ratified decision record | `NOT_CONFIGURED` |
| R2 | Credentials injected per environment, none leaked | secret inventory + scan | `NOT_CONFIGURED` |
| R3 | Bounded source requests succeed for every required instrument | capture log with timestamps | `UNAVAILABLE` |
| R4 | Clock/session normalization verified on real bars | ownership report | `DEGRADED` |
| R5 | Final-bar checks pass over a real window | finality report | `DEGRADED` |
| R6 | Historical/live/reconnect parity within tolerance | parity report (5-way) | `DEGRADED` |
| R7 | Replay reproduces recorded digests | digest comparison | `DEGRADED` |
| R8 | Source health observed across an outage | health timeline | `UNAVAILABLE` |
| R9 | Failure/recovery drill passes | drill record | `UNAVAILABLE` |
| R10 | Book II amendment authorizes the seam change | amendment receipt | seam unchanged |

Any missing gate keeps the status non-healthy. `required` flips only when a
serving path consumes market data, which is a Book II decision (WP-2/3D).

---

## 7. Gate verdict semantics

- **WP-3A PASS** = four documents committed, decision sourced and labelled,
  inventory counted, no code/credentials touched. Does not authorize data.
- **WP-3B PASS** = 66 contract tests green against synthetic fixtures, frozen
  integrity intact, seam still `NOT_CONFIGURED`.
- **WP-3C PASS** = 6 external tests green on licensed captures, keys absent from
  artifacts, terms recorded.
- **WP-3D PASS** = R1–R10 satisfied over a real window; readiness change
  authorized by Book II.

---

## 8. Traceability to the assignment

| Assignment clause | Where satisfied |
|---|---|
| §2 market coverage | PLAN §3; matrix §2 |
| §3 provider discovery/comparison | matrix §2–§4 |
| §4 adapter architecture | PLAN §6–§8 |
| §5 historical/live parity | PLAN §9; T5 |
| §6 quality/provenance | PLAN §10; T6 |
| §7 readiness | PLAN §11; §6 above; T9 |
| §8 security/licensing/cost | PLAN §12; T8 |
| §9 acceptance tests | §3 above (72) |
| §10 fixtures | §5 above (12) |
| §11 work packets | PLAN §15; `DEPENDENCY_HANDOFF.md` |
| §12 deliverables | exactly four documents |

---

## 9. Stop conditions

Report and stop if: the operator does not ratify a vendor; licensing forbids the
intended display; a required registration is refused; a frozen hash or the seam
changes; parity fails beyond one native tick without a documented cause; a
credential would enter the repository, logs or fixtures; or an external test can
only be made to pass by weakening an assertion.

---

## 10. Count reconciliation

`grep`-verifiable uniqueness: 72 `test_*` names, no duplicates, distributed
9/8/8/8/7/7/7/6/6/6; 66 `M` + 6 `X`. `PLAN.md` §13 states the same total and
split. No test is skipped, xfailed or weakened by design; external names are
gated by environment, not by assertion strength.
