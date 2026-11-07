# BOOK III — III.1 PROVIDER COMPATIBILITY AMENDMENT — ACCEPTANCE

**Packet:** BA-25 Rung 1 · **Status:** PROPOSED — binding only after explicit
implementation authorization
**Companion:** `PLAN.md`, `FEASIBILITY_GATE.md`, `CHANGE_CONTROL.md`
**Starting head:** `46dc2fb52cd1e7430c3de185a1ec5070ec0a3f4e`

---

## 1. What this acceptance covers

| Layer | Proves | Proves nothing about |
|---|---|---|
| Amendment contract (this document) | the extended III.1 field map can represent the three vendors without changing existing semantics | any live vendor call |
| Offline adapter (WP-3B, already green) | adapters obey the frozen contracts through injected transports | licensing, latency, history depth |
| External (WP-3C) | a licensed feed returns usable observations | production readiness |

A green amendment suite is not proof of a licensed feed. No layer borrows
another's verdict.

**Inventory: 24 requirements (R1–R24) and 49 tests (A-01–A-49).**
Counts are authoritative and machine-checked by §7.

---

## 2. Preconditions

1. This packet approved; `CHANGE_CONTROL.md` decisions 1–2 signed.
2. Separate written authorization to modify `normalize.py` and the
   `market_data` export surface.
3. `.bu_tmp/`, WP-3A/WP-3B evidence and the old hash baseline preserved.
4. No credential, network or vendor account present in the test environment.
5. Implementation limited to the two authorized frozen files plus the new test
   file.

If (2) is refused, the amendment is not implemented and WP-3B stays PARTIAL.

---

## 3. Requirement acceptance (R1–R24)

Legend — **F1** existing, **F2** additive adapter, **F3** frozen change,
**F4** source/operator block.

| ID | Requirement | Class | Acceptance condition | Tests |
|---|---|---|---|---|
| R1 | Provider identity survives normalization | F1 | every `Bar.provider` is the registered provider id | A-29 |
| R2 | Source symbol retained at the adapter boundary | F1 | raw observation keeps vendor spelling; canonical bar carries none | A-32 |
| R3 | Source timestamp preserved distinct from bar open | F1 | `Bar.source_timestamp` equals the raw source event time | A-31 |
| R4 | Volume optional when supplied | F1 | absent volume yields `None`, never `0` | A-18 |
| R5 | Unknown provider fails closed | F1 | `UnsupportedProviderError`; no schema invented | A-01, A-02, A-03, A-05, A-07, A-10, A-11, A-21, A-43 |
| R6 | Observation cutoff is the only finality authority | F1 | hints cannot finalize a bar; cutoff decides | A-16, A-35, A-36, A-37 |
| R7 | Revision ordering by later source timestamp | F1 | later row wins; survivor carries `REVISED` | A-30 |
| R8 | Twelve Data `values` envelope extraction | F2 | rows flatten before the kernel; no envelope key reaches it | A-06, A-18, A-24, A-28 |
| R9 | Polygon `results` envelope extraction | F2 | same, including `status` refusal | A-06, A-19, A-25, A-28 |
| R10 | Kraken array-row adaptation | F2 | positional row becomes named fields without loss | A-06, A-20, A-26, A-28 |
| R11 | Request-context symbol/timeframe injection | F2 | injected values are the declared request values, not guesses | A-06, A-11 |
| R12 | Source revision id extraction at the adapter | F2 | revision retained on the raw observation | A-06, A-30 |
| R13 | Trailing provisional hint | F2 | Kraken's last row is marked `NONFINAL` | A-06, A-34 |
| R14 | Envelope provenance retention | F2 | adapter version and source ref survive to the raw boundary | A-06, A-27, A-33 |
| R15 | Additive JPY registry composition | F2 | six instruments with mappings; default registry untouched | A-06, A-38, A-39 |
| R16 | Close-time derivation `OPEN_PLUS_TIMEFRAME` | F3 | deterministic boundary; source close wins when declared | A-13, A-14, A-15, A-16, A-17 |
| R17 | Conditional required keys | F3 | derived close and absent clock are not "missing fields" | A-15, A-45 |
| R18 | Optional clock key without remap | F3 | `clock=None` yields a bar with no clock claim; no substitution | A-42 |
| R19 | `TimestampStyle.EPOCH_MILLISECONDS` | F3 | ms parsed exactly; seconds not accepted as ms | A-08, A-09, A-12, A-19, A-44 |
| R20 | Provider schema entries for three vendors | F3 | three entries registered; fakes byte-identical; version exposed | A-01, A-02, A-04, A-05, A-07, A-08, A-10, A-18, A-19, A-20, A-21, A-22, A-43, A-46, A-47, A-48, A-49 |
| R21 | Promote instruments into the production default registry | F4 | operator decision + source authority; not required now | A-41 |
| R22 | Canonical authority for JPY precision/pip/tick | F4 | written confirmation before promotion | A-40 |
| R23 | Higher-timeframe rollup rule | F4 | absent rule; rollup remains refused | A-23 |
| R24 | Vendor licensing/redistribution authority | F4 | commercial terms recorded before WP-3C | A-49 |

---

## 4. Test inventory (A-01–A-49)

All tests are offline, deterministic and source-backed. No skipped or xfailed
binding test is permitted.

### T1 — Backward compatibility (6)

| ID | Name | Expected result |
|---|---|---|
| A-01 | `test_fake_alpha_schema_behavior_unchanged` | identical bar/refusal for a fixed record |
| A-02 | `test_fake_beta_schema_behavior_unchanged` | identical bar/refusal for a fixed record |
| A-03 | `test_unknown_provider_refused` | `UnsupportedProviderError` |
| A-04 | `test_schema_registry_version_exposed` | `PROVIDER_SCHEMAS_V2` importable and stable |
| A-05 | `test_existing_market_data_suite_green` | `test_forge_market_data.py` remains green |
| A-06 | `test_wp3b_contract_suite_green` | 66/66 unchanged |

### T2 — Timestamp interpretation (6)

| ID | Name | Expected result |
|---|---|---|
| A-07 | `test_epoch_seconds_unchanged` | `fake_alpha` epoch seconds parse as before |
| A-08 | `test_epoch_milliseconds_accepted` | `1_772_496_000_000` → `2026-03-03T00:00:00Z` |
| A-09 | `test_seconds_and_milliseconds_not_confused` | seconds value under ms style refuses |
| A-10 | `test_iso_offset_unchanged` | `fake_beta` ISO offset parses as before |
| A-11 | `test_naive_timestamp_refused` | naive input refuses, never assumes UTC |
| A-12 | `test_unsupported_timestamp_unit_refused` | non-integer ms and unknown style refuse |

### T3 — Derived close time (5)

| ID | Name | Expected result |
|---|---|---|
| A-13 | `test_derived_close_m5` | `open + 5min` exactly |
| A-14 | `test_derived_close_h1` | `open + 60min` exactly |
| A-15 | `test_source_close_preferred_over_derivation` | `SOURCE` rule ignores derivation |
| A-16 | `test_derived_close_is_not_finality` | bar at/after cutoff finalizes only by cutoff |
| A-17 | `test_derived_close_across_dst_instant` | UTC arithmetic; no local-wall assumption |

### T4 — Provider schema mappings (6)

| ID | Name | Expected result |
|---|---|---|
| A-18 | `test_twelvedata_schema_accepts_record` | canonical bar; absent volume → `None` |
| A-19 | `test_polygon_schema_accepts_record` | ms row accepted under `EPOCH_MILLISECONDS` |
| A-20 | `test_kraken_schema_accepts_record` | epoch-seconds row accepted |
| A-21 | `test_unregistered_provider_refused` | no fallback schema |
| A-22 | `test_schema_table_immutable` | mapping proxy / frozen entries |
| A-23 | `test_higher_timeframe_rollup_still_refused` | no rollup; unsupported timeframe refuses |

### T5 — Envelope and row adaptation (5)

| ID | Name | Expected result |
|---|---|---|
| A-24 | `test_twelvedata_envelope_flattened` | `values` rows only; no envelope key |
| A-25 | `test_polygon_envelope_flattened` | `results` rows; `status` refusal respected |
| A-26 | `test_kraken_array_rows_mapped` | array fields map without loss |
| A-27 | `test_envelope_provenance_retained` | adapter version + source ref preserved |
| A-28 | `test_malformed_envelope_refused` | bounded refusal, no bar |

### T6 — Source lineage (5)

| ID | Name | Expected result |
|---|---|---|
| A-29 | `test_provider_identity_per_bar` | every bar carries its provider |
| A-30 | `test_revision_ordering_preserved` | later source timestamp wins, `REVISED` |
| A-31 | `test_source_timestamp_preserved` | raw timestamp equals bar source timestamp |
| A-32 | `test_source_symbol_retained_at_adapter` | vendor symbol kept off the canonical bar |
| A-33 | `test_adapter_version_retained` | raw observation carries the version |

### T7 — Finality (4)

| ID | Name | Expected result |
|---|---|---|
| A-34 | `test_trailing_candle_nonfinal` | Kraken last row `NONFINAL` |
| A-35 | `test_vendor_final_hint_cannot_override_cutoff` | pre-cutoff close stays `NONFINAL` |
| A-36 | `test_candle_after_cutoff_final` | cutoff passed → `FINAL` |
| A-37 | `test_provider_cannot_set_finality` | no field/hint path can set `FINAL` |

### T8 — JPY instruments (4)

| ID | Name | Expected result |
|---|---|---|
| A-38 | `test_jpy_instruments_injected` | USDJPY/AUDJPY/EURJPY present with mappings |
| A-39 | `test_jpy_aliases_resolve` | provider spellings resolve to canonical ids |
| A-40 | `test_jpy_conventions_provisional` | 3 / 0.01 / 0.001 flagged provisional |
| A-41 | `test_default_registry_unchanged` | production default still 3 instruments |

### T9 — Refusal behavior (4)

| ID | Name | Expected result |
|---|---|---|
| A-42 | `test_missing_clock_fails_closed` | no clock claimed, no remap, bounded outcome |
| A-43 | `test_unsupported_timeframe_refused` | `UNSUPPORTED_TIMEFRAME` |
| A-44 | `test_malformed_timestamp_refused` | `INCOMPLETE_RECORD`, never a guessed time |
| A-45 | `test_absent_source_field_refused` | `INCOMPLETE_RECORD`, never a synthesized value |

### T10 — Frozen integrity (4)

| ID | Name | Expected result |
|---|---|---|
| A-46 | `test_book_i_and_ii_untouched` | diff empty |
| A-47 | `test_only_authorized_frozen_files_changed` | only `normalize.py` + `market_data/__init__.py` |
| A-48 | `test_hash_record_updated` | old and new digests both recorded |
| A-49 | `test_re_ratification_and_licence_gate_recorded` | amendment ratification + WP-3C licence gate present |

---

## 5. Traceability and coverage

Every requirement maps to at least one test; every test maps to at least one
requirement. Machine check: parse `R\d+` and `A-\d+` from this table.

- Requirements covered: 24/24.
- Tests mapped: 49/49.
- No test asserts external connectivity, latency, cost or licence rights.

---

## 6. Backward-compatibility acceptance

1. `fake_alpha` and `fake_beta` produce identical bars, refusals and flags for
   fixed inputs before and after the change.
2. `ProviderFieldMap.required_keys` for both fakes is unchanged in content and
   order.
3. `test_forge_market_data.py` stays green without edits.
4. WP-3B's 66 tests stay green without edits.
5. No new `RefusalReason`, `QualityFlag` or `Bar` field.
6. Unknown providers still fail closed.

Any failure here is a gate failure, not a test to adjust.

---

## 7. Count reconciliation

| Family | Tests | Requirements touched |
|---|---|---|
| T1 | 6 | R5, R8–R15, R20 |
| T2 | 6 | R5, R11, R19, R20 |
| T3 | 5 | R6, R16, R17 |
| T4 | 6 | R4, R5, R8, R9, R10, R19, R20, R23 |
| T5 | 5 | R8, R9, R10, R14 |
| T6 | 5 | R1, R2, R3, R7, R12, R14 |
| T7 | 4 | R6, R13 |
| T8 | 4 | R15, R21, R22 |
| T9 | 4 | R5, R17, R18, R19 |
| T10 | 4 | R20, R24 |
| **Total** | **49** | **24/24** |

---

## 8. Gate verdict semantics

- **Amendment PASS** = 49/49 green, fake schemas unchanged, only the two
  authorized frozen files changed, old baseline recorded, full regression green.
- **Amendment PARTIAL** = tests green but an F4 decision (registry promotion,
  JPY authority, rollup, licensing) is still absent. This does not block the
  field-map extension but keeps WP-3B at PARTIAL.
- **Amendment FAIL** = any fake-schema drift, refusal weakening, unauthorized
  file change, hash overwrite, or red test.

WP-3B becomes eligible for PASS only after Amendment PASS **and** a fresh WP-3B
evidence/ratification update; this document does not grant it.

---

## 9. Stop conditions

Report and stop if: authorization for the two files is refused; a fake schema
changes; a refusal is downgraded; `Bar` or `MARKET_DATA_SCHEMA_VERSION` must
change to satisfy the tests; a vendor connection is required; or the default
registry is promoted without R21 authority.
