# BOOK III — WP-3B — PROVIDER ADAPTER EVIDENCE

**Packet:** BA-24 Rung 2 · **Scope:** WP-3B only (offline, synthetic)
**Branch:** `forge` · **Starting head:** `c104945fc8011d0b613ebdca0ac9493eeffcc9d1`
**Implementation heads:** `07f010f` (fixtures), `023b87b` (adapter), `5c21b06` (tests)
**Verdict:** **PARTIAL** — offline adapter and 66/66 contract tests pass, but the
provider schema-table registration and the production default-registry
extension remain blocked on an unauthorized frozen III.1 amendment (see §3).
No live provider, credential, licence or network was used.

---

## 1. Phase 0 — foundation verification

| # | Check | Result |
|---|---|---|
| 1 | `forge` HEAD == `origin/forge` | PASS — both `c104945` |
| 2 | Append-only ancestry (`c6bb05a` ancestor) | PASS |
| 3 | Book I corpus freeze manifest present | PASS |
| 4 | Book II 50-hash manifest + 23 planning pins | PASS — ≥50 64-hex digests |
| 5 | Book III 79 modules | PASS — 11/12/13/13/16/14 |
| 6 | Integration acceptance suite (96 names) | PASS — green baseline |
| 7 | Migrations `001`–`004` | PASS |
| 8 | `service/routes.py` frozen | PASS — sha256 `145757e0…d190af` |
| 9 | III.1 contracts/registries intact | PASS — `git diff HEAD` empty |
| 10 | Market-data seam `NOT_CONFIGURED` | PASS — container + readiness |
| 11 | WP-3A head CI | PASS — run `42319328357`, jobs `test` + `postgres` |
| 12 | WP-3B prerequisite language | READ — ACCEPTANCE §2(2) requires written
authorization for schema entries, mappings and JPY instruments |

**Gate outcome:** mappings and JPY instruments have a genuine additive seam;
schema entries and the production default registry do not. The rung proceeds on
the permissible work and records the blocker rather than bending it.

## 2. Design selection and licensing boundary

Twelve Data is implemented as the **provisional primary interface target**;
Polygon Currencies and Kraken are separate secondary adapters. This is a
technical shape decision only. No subscription, account, key, licence term or
redistribution right is accepted or implied. Twelve Data's commercial
display/redistribution terms remain unverified and are labelled in adapter
capabilities.

## 3. Registration gate — classification and authority

| Need | Classification | Status |
|---|---|---|
| 1. Provider schema entries | **FROZEN AMENDMENT** | BLOCKED — not applied |
| 2. Provider-symbol mappings | **ADDITIVE** (`Instrument.provider_mappings`) | DONE |
| 3. USDJPY/AUDJPY/EURJPY instruments | **ADDITIVE** (`Instrument` ctor) | DONE |
| 4. Higher-timeframe rollup | **CANONICAL BLOCKER** | NOT IMPLEMENTED |

### 3.1 Why the schema table is a structural amendment

`app/forge/market_data/normalize.py` (sha256 `04c4ecfc…`) hard-codes
`PROVIDER_SCHEMAS` as a module-level dict with exactly two scripted fakes.
`ProviderFieldMap` requires a **literal raw key** for `symbol`, `timeframe`,
`open_time`, `close_time`, `open/high/low/close`, `volume`, `source_timestamp`
and `clock`, plus one of two `TimestampStyle` values. The real feeds do not fit
that shape:

- **Twelve Data** has no close-time column (it must be derived as
  `open + timeframe`), no clock id, and returns a `{"values": [...]}` envelope.
- **Polygon** returns epoch **milliseconds** (no such style), an envelope of
  `results`, and no close time, symbol or clock in each row.
- **Kraken** returns arrays, not mappings, under a result key, with a
  provisional trailing candle that the field map cannot express.

Three dict entries are therefore not sufficient. The minimum governed
amendment is:

1. `ProviderFieldMap.close_time_derivation` (e.g. `OPEN_PLUS_TIMEFRAME`) and
   make `close_time` optional when derived.
2. `TimestampStyle.EPOCH_MILLISECONDS`.
3. A declared per-provider **finality policy** (`NONE` / `TRAILING_PROVISIONAL`)
   so a hint cannot be mistaken for a finality decision.
4. Envelope/row adapters for `values`/`results`/`result[key]` and
   request-context injection for symbol/interval.
5. Hash impact: `normalize.py` digest changes; `instruments.py`
   (`8c6d6ad0…`) changes only if the production default registry is extended.
   `bars.py` (`97fc99e4…`) and `quality.py` (`6b77c6df…`) need no change.

Acceptance for that amendment: the frozen III.1 suite stays green, schema
round-trips are added for all three vendors, and the default registry still
resolves exactly one instrument per alias.

### 3.2 Additive path actually used

`market_data_ingest/registry.py` composes a new registry from the **public**
`Instrument`/`InstrumentRegistry` constructors: base instruments are copied with
`dataclasses.replace` to add `provider_mappings`, and the three JPYY pairs are
declared explicitly. `build_default_registry()` is untouched and still resolves
only EURUSD/XAUUSD/BTCUSD (verified: `USDJPY` remains an unknown alias there).

**Disclosure:** JPYY precision 3, pip 0.01 and tick 0.001 are market
conventions, not corpus claims. They require operator confirmation before any
real-feed acceptance.

### 3.3 Canonical blocker

No canonical higher-timeframe rollup/finalization rule exists in the corpus.
Nothing aggregates M5 into M15/H1/etc. inside the adapter; requests for
undeclared timeframes refuse. No bar is fabricated.

## 4. Implemented modules (18 files, additive package)

`app/forge/market_data_ingest/`:
`__init__`, `contract`, `symbols`, `registry`, `capture`, `canonical`,
`backfill`, `stream`, `health`, `replay`, `config`, `routing`, `disagreement`,
`providers/{__init__, transport, twelvedata, polygon, kraken}`.

Deviations from PLAN §6, disclosed:

- `normalize_feed`/`replay_historical`/`stream_live` cannot accept a real
  provider id without the blocked schema table. `canonical.py` therefore
  composes the **public** kernel (`Bar`, `assess_finality`, `reconcile`,
  `finalize_for_cutoff`, `missing_opens`, `content_digest`,
  `QualityPolicy.evaluate`); `replay.py` assembles `PipelineResult` and reuses
  the frozen `compare_parity`/`bar_ownership`. No III.1 rule is reimplemented.
- `disagreement.py` is an additional module (not named in PLAN) because
  cross-source comparison and clock-skew detection need one bounded home.
- `providers/transport.py` replaces the planned `providers/base.py`; it is the
  scripted transport, not a base class.

## 5. Contract-test reconciliation

`tests/test_forge_market_data_provider_integration.py` — 66 `def test_` names,
exactly the inventory, no renamed or added binding names.

| Group | Names | Result |
|---|---|---|
| T1 adapter contracts | 9 | 9 passed |
| T2 backfill (`M` half) | 6 | 6 passed |
| T3 streaming (`M` half) | 7 | 7 passed |
| T4 sessions/clocks | 8 | 8 passed |
| T5 parity (`M` half) | 4 | 4 passed |
| T6 quality | 7 | 7 passed |
| T7 multi-provider | 7 | 7 passed |
| T8 security | 6 | 6 passed |
| T9 readiness | 6 | 6 passed |
| T10 frozen integration | 6 | 6 passed |
| **Total** | **66** | **66 passed** |

Focused run: `66 passed in 4.16s`. No skips, xfails or placeholder assertions.
External names 10, 16, 25, 34, 36, 40 are absent by design (§11).

## 6. Fixtures — twelve cases, byte-identical reproduction

`implementation/forge/book_iii/provider_integration/fixtures/` holds 17 files:
12 cases + `FIXTURE_MANIFEST.json` + `FROZEN_BASELINE.json` + `_builders.py` +
`generate.py` + `README.md`.

`python generate.py --check` → **`fixtures reproduce byte-identically (14
files)`**. Every case is `SYNTHETIC_FIXTURE`; SHA-256 is LF-normalized.

| ID | Case | Outcome exercised |
|---|---|---|
| FIX-01 | normal EURUSD M5 | 6 bars, `COMPLETE` |
| FIX-02 | XAU 19:00 transition | ownership `NO_SESSION` (no invented session) |
| FIX-03 | BTC Saturday | no weekend gap |
| FIX-04 | EUR spring-forward | final bar opens `06:55Z`, local `01:55` |
| FIX-05 | duplicates | 2 bars, `DUPLICATE` |
| FIX-06 | out-of-order | order-independent digest |
| FIX-07 | missing bar | 1 `GAP`, `DEGRADED` |
| FIX-08 | nonfinal-to-final | 2 final, 1 excluded |
| FIX-09 | correction | later source timestamp wins, `REVISED` |
| FIX-10 | disconnect/reconnect | state preserved |
| FIX-11 | parity pair | `parity: true` |
| FIX-12 | provider discrepancy | `OUTLIER_SOURCE` |

The suite consumes FIX-07's `expected_opens` directly, so at least one fixture
participates in the binding assertions. No fixture claims vendor history depth.

## 7. Offline replay / parity

Five dimensions are asserted: canonical bar content, ownership, quality flags,
missing set and source-window digest. `offline_parity` reuses the frozen
`compare_parity`; content digests exclude provider identity, and the same
observation set delivered in reverse order yields an identical digest.
Disconnect/reconnect and late corrections preserve the committed state.

This is **synthetic** parity only. No historical/live external parity is
claimed; that is WP-3C/3D work.

## 8. Quality and finality

- The eight frozen flags are used unchanged; no new enum, no free text.
- Provider finality is a hint. `assess_finality`/`finalize_for_cutoff` decide;
  a provider `FINAL` hint before the cutoff still yields `NONFINAL`.
- Kraken's trailing candle is emitted `NONFINAL`.
- Missing bars stay visible (`GAP`); no price is ever synthesized.
- `STALE` is carried when supplied, never auto-set.
- Unsupported clock, unknown symbol, unsupported timeframe and precision
  violations refuse with the frozen `RefusalReason` values.

## 9. Secret and network isolation

- No adapter opens a socket; every transport is a scripted sequence.
- No API key, account or subscription exists in the repository.
- `MarketDataIngestConfig` keeps the key `repr=False`, exposes boolean presence
  only, and fails closed before any request.
- Credentials are injected by environment (`FORGE_MARKET_DATA_*`); rotation
  needs no code change.
- Tests scan fixtures and this packet for key-shaped strings; none present.

## 10. Frozen-interface integrity

| Artifact | Result |
|---|---|
| `git diff HEAD` for Book I/II, six III packages, SQL, routes | empty |
| `routes.py` sha256 | `145757e0f2b19e76…d190af` |
| III module counts | 11/12/13/13/16/14 = 79 |
| Migrations | `001`–`004` only |
| Default registry | still EURUSD/XAUUSD/BTCUSD (3) |
| Market-data seam | `NOT_CONFIGURED`, `required: false`; readiness `ready` |

`app/forge/market_data_ingest/` is a new top-level package beside
`app/forge/market_data/`; no frozen file or manifest was touched.

## 11. WP-3C — six external tests remain NOT EXECUTED

| # | Name | Status |
|---|---|---|
| 10 | `test_backfill_paginates_without_window_gaps` | NOT EXECUTED — WP-3C |
| 16 | `test_backfill_resume_equals_full_run` | NOT EXECUTED — WP-3C |
| 25 | `test_stream_reconnect_requests_missed_window` | NOT EXECUTED — WP-3C |
| 34 | `test_historical_and_live_parity_on_source_slice` | NOT EXECUTED — WP-3C |
| 36 | `test_parity_holds_across_reconnect` | NOT EXECUTED — WP-3C |
| 40 | `test_replay_reproduces_recorded_source_digest` | NOT EXECUTED — WP-3C |

None is present as a skipped or passing placeholder.

## 12. CI

Implementation head `5c21b06`: run `42321475881` (`FORGE Tests`) — **success**;
jobs `test` **success**, `postgres` **success**. Local focused run `66 passed`,
full regression `2029 passed, 29 skipped`.

Final documentation head: re-verified after the evidence/ratification commit and
reported in the final message.

## 13. Defects and root-cause repairs

| Defect | Root cause | Repair |
|---|---|---|
| Polygon close time used a fragile dynamic `timedelta` | incomplete import during drafting | explicit `timedelta` import and direct arithmetic |
| Kraken `isinstance(result, Mapping)` on `typing.Mapping` | wrong abstraction for runtime checks | `collections.abc.Mapping` |
| Adapter fixture values lacked `source_timestamp` | test builder omitted the documented field | builder now emits it; adapter preserves it |
| `assert_single_source` called with `Bar` objects | helper is typed for `RawCandle` | test passes raw observations |
| Revision test canonicalized only the surviving observation | buffer stores latest, not lineage | test reconciles the observation pair, which is where `REVISED` lives |
| Single-page transport reused for two fetches | test setup error | two scripted pages |

No production assertion was weakened to fix a test.

## 14. Full regression

`python -m pytest -q` → **2029 passed, 29 skipped** (baseline was 1963/29; the
+66 are this packet). Fixture check, focused suite and full suite were run at
the implementation head.

## 15. Remaining gaps

- Provider schema-table registration and default-registry extension: blocked
  on the amendment in §3.1.
- Higher-timeframe rollup: canonical blocker, absent by design.
- Vendor licensing, display/redistribution rights and commercial tiers:
  unverified; no acceptance implied.
- Real history depth, reconnect under real network conditions, latency and
  cost: unmeasured.
- JPYY precision/pip/tick: market conventions awaiting operator confirmation.
- Six external tests: WP-3C.

## 16. WP-3C readiness decision

WP-3C **may begin only after** the operator (a) ratifies a vendor in writing,
(b) authorizes and lands the §3.1 amendment (or accepts the offline-only
adapter), (c) supplies credentials through the environment, and (d) provides
licensed `SOURCE_SLICE` captures with `licence_ref` and `source_ref`.

Until then, the seam stays `market_data: NOT_CONFIGURED`, no provider is
contacted, and no live/parity/readiness claim is made. This packet closes the
**offline contract** portion of WP-3B only.
