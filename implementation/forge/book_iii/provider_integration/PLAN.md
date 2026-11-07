# BOOK III — WP-3 MARKET DATA PROVIDER INTEGRATION — PLAN

**Book:** III · **Packet:** BA-24 Rung 1 (WP-3A planning)
**Starting head:** `c6bb05a2b9abec460a12af03f4d28679e9215329`
**Status:** PROPOSED — planning only. No provider is connected, configured or
contracted by this document.
**Companions:** `ACCEPTANCE.md`, `PROVIDER_DECISION_MATRIX.md`,
`DEPENDENCY_HANDOFF.md`

---

## 1. Mission and scope

WP-3 moves Book III from deterministic synthetic inputs toward verified
real-market operation by defining one integration boundary between external
market-data providers and the frozen III.1 contracts.

In scope: provider selection analysis, instrument/data requirements derived
from the canonical model cards, adapter architecture, normalization ownership,
historical/live/reconnect parity, quality and provenance, readiness transition,
security/licensing/cost, acceptance-test design and work-packet separation.

Out of scope and **not authorized by this rung**: provider accounts, API keys,
network calls, adapter code, tests, fixtures, migrations, environment changes,
route registration, readiness-seam edits, Book I/II changes and any claim that
live data exists. `market_data` remains `NOT_CONFIGURED`.

---

## 2. Phase 0 — foundation verification (measured)

| Check | Method | Result |
|---|---|---|
| Local head equals remote | `git rev-parse HEAD` / `origin/forge` | both `c6bb05a2b9abec460a12af03f4d28679e9215329` |
| Branch / ancestry | `git rev-parse --abbrev-ref`, `merge-base --is-ancestor` | `forge`; `9f423a4` is an ancestor; append-only ladder intact |
| Book I corpus | directory inspection | 7 canonical model cards, 2 setup cards, evidence slices present; untouched |
| Book II freeze | `ratification/CONTRACT_FREEZE_MANIFEST_V1.md` + recomputed route hash | 50-hash manifest present; `routes.py` sha256 `145757e0f2b19e76…` (git blob `e83fa101…`) |
| III.1–III.6 modules | sha256 over each package's `*.py` | 11 / 12 / 13 / 13 / 16 / 14 = **79** |
| Migrations | `app/forge/persistence/sql` | `001_initial_schema`, `002_identity_session`, `003_vector_projection`, `004_audit_ledger` |
| Readiness seam | `service/container.py` | `market_data: {"status": "NOT_CONFIGURED", "required": False}` |
| Bloc ratifications | `implementation/forge/book_iii/bloc_iii_*/RATIFICATION.md` | six present; integration ratification + feasibility gate present |
| Starting-head CI | `gh run list --branch forge` | run `42316097257` success, jobs `test` + `postgres` |
| Working tree | `git status --porcelain` | clean except pre-existing `?? .bu_tmp/` |

Package digests recorded at this head (first 16 hex):
`market_data 28d14ae61de9d189`, `measurements bd8675a7eb5669fc`,
`model_runtime 0f532c18cb63ea26`, `state_engine 3860388238e0a7ca`,
`setup_engine da9a5058fec2f001`, `intelligence_api cb3a4ab04ebdd03f`.

---

## 3. Canonical data requirements (from model cards, not invented)

All CEREBUS lineages share one structural frame: an M5 observation stream, the
19:00–03:00 New York research frame, explicit research-day ownership and a
final-bar rule that is part of model identity. Lookbacks below are the *minimum*
span implied by the cited sample sizes, rounded up; they are requirements for
research parity, not vendor promises.

| Instrument | Canonical source | Granularity | Minimum lookback | Session / clock | Model-specific finality |
|---|---|---|---|---|---|
| EURUSD | `EUR_DAILY_NEWS_REKEY_MODEL_CARD_V1`; Phase1 calibration (`995` research days) | M5 primary; D1/W1 rollup | ≈ 4 years (995 research days) | 19:00–03:00 NY frame; research day shifts after the 19:00 close; `America/New_York` (IANA DST) | M5 bar opening 02:55 local, close 03:00 |
| XAUUSD | `XAU_GAME_L1_L2_L3_MODEL_CARD_V1`; weekly sample `238` | M5 primary; D1/W1 rollup | ≈ 5 years (238 weeks) | Gold Game uses an Asian range and an “After 3AM” entry lineage; **no canonical session bounds are registered** | Not canonically stated beyond the shared M5 convention |
| USDJPY | `JPY_CARRY_GAME_MODEL_CARD_V1`; `182` common basket weeks | M5 primary | ≈ 4 years | JPY 12–4PM DT window is *named*; DT→Carry binding is forbidden without a crosswalk ruling | Not canonically stated |
| AUDJPY | same card (risk/execution expression) | M5 primary | ≈ 4 years | as above; role-gated, never an equal vote | Not canonically stated |
| EURJPY | same card (confirmation/veto) | M5 primary | ≈ 4 years | as above | Not canonically stated |
| BTCUSD | `BTC_DAILY_WEEKLY_MONTHLY_TRACKER_MODEL_CARD_V1` | M5 primary; D1/W1 rollup | ≈ 3 years minimum; 10 years desirable for weekly/monthly context | 19:00–03:00 NY research frame; 12:00 NY checkpoint; 24/7 continuous, no weekend gap | 12:00 checkpoint is an exact instant; daily/weekly anchors remain `UNRESOLVED` (III.3-GAP-8) |
| SPX, DXY | none of the frozen cards require them for WP-3 | — | — | — | **Deferred coverage**, not a WP-3 requirement. DXY is a cross-rate construction and would need its own canonical definition before ingestion. |

Mandatory per-observation fields (already in `market_data/bars.py::Bar`):
provider, source symbol, canonical instrument id, source event timestamp,
canonical open/close time, OHLC (+ volume when supplied), source revision or
finality marker, quality flags, provenance kind, source reference,
normalization/schema version and a deterministic digest.

**Registry finding.** `build_default_registry()` currently declares only
`EURUSD`, `XAUUSD`, `BTCUSD`. The three JPY pairs are required by the JPY card
but are **not registered**. Adding them (precision 3, pip size 0.01, same
timeframes/clocks) is an additive WP-3B change requiring explicit
authorization; it is not performed here.

---

## 4. Provider landscape — recommendation summary

Full comparison, URLs and uncertainty labels: `PROVIDER_DECISION_MATRIX.md`.
Prices and capabilities were read from official pages on **2026-11-07** and are
subject to change; nothing was purchased or authenticated.

**Primary recommendation — Twelve Data, business tier (Venture or above).**
One contract covers all six required instruments (FX v2 majors and crosses
including USD/JPY, AUD/JPY, EUR/JPY, precious metals including XAU, and crypto
BTC/USD), M1–1month candles including M5 and H1, WebSocket streaming and
aggregated pricing from 60+ liquidity providers. Business tiers allow
commercial display subject to exchange licensing; redistribution needs a
separate written agreement.

**Independent verification / fallback — Polygon Currencies (business) plus
Kraken for BTC/USD.**
Polygon exposes `C:XAUUSD` through its forex endpoints, 10+ years of history on
Currencies Starter and WebSocket aggregates; its business tier is the licensed
path for redistribution. Kraken offers a true `BTC/USD` pair (not USDT) with
public OHLC and a downloadable full OHLCVT history, but REST returns only the
720 most recent candles, so backfill must use the CSV archive or Trade
pagination.

**Internal research and parity source only — OANDA v20.**
Excellent FX/metals depth (history from 2005, 5000 candles per page, explicit
`complete` flag), but its API License Agreement restricts use to internal use
and forbids transmitting, displaying or providing the licensed material to any
third party, including clients. OANDA therefore **cannot** be the customer-facing
source without written permission; it remains valuable for internal cross-checks.

**Not selected:** Binance (BTCUSDT is USDT-denominated, a basis risk against the
canonical BTCUSD; redistribution terms unverified), Coinbase/Dukascopy (no
official documentation verified in this pass).

---

## 5. Existing-code interface map (actual, not inferred)

| Surface | Path | Role in WP-3 |
|---|---|---|
| Bar contract, finality, reconciliation, digests | `app/forge/market_data/bars.py` (`Bar`, `assess_finality`, `reconcile`, `finalize_for_cutoff`, `missing_opens`, `content_digest`) | Canonical output and the **only** owner of finality and dedupe |
| Normalization | `market_data/normalize.py` (`ProviderFieldMap`, `PROVIDER_SCHEMAS`, `normalize_record`, `normalize_feed`) | Quarantines raw field names/symbols/clock styles; extend additively per provider |
| Instrument identity | `market_data/instruments.py` (`Instrument`, `InstrumentRegistry`, `build_default_registry`) | Symbol/alias resolution, precision, native unit sizes |
| Clocks | `market_data/clocks.py` (`ClockIdentity`, `session_bounds_utc`, `local_wall`) | Versioned time identity; adapters must never convert zones themselves |
| Sessions | `market_data/sessions.py` (`SessionRegistry`, `SessionDefinition`) | Versioned, source-cited session definitions; unknown → `NO_CALCULATION` |
| Research day | `market_data/research_day.py` | Explicit lineage rule; unknown → `UNRESOLVED` |
| Parity runners | `market_data/parity.py` (`PipelineContext`, `replay_historical`, `stream_live`, `compare_parity`) | Reused unchanged for provider slices |
| Quality vocabulary | `market_data/quality.py` (8 flags, `QualityPolicy`, `DataOutcome`) | No new flags; disagreement maps to `OUTLIER_SOURCE` |
| Readiness | `app/forge/service/container.py` (`market_data` dependency entry), `service/health.py` | Vocabulary `READY`/`DEGRADED`/`UNAVAILABLE`/`NOT_CONFIGURED`; `required` flips only when consumed |
| Provider doctrine/ports | `app/forge/providers/` (`doctrine.py`, `registry.py`, `resilience.py`) | Eight-element contract, caller-owned retries, circuit breaker; market data is a **new port**, not one of the four II.5 ports |
| Frozen routes | `app/forge/service/routes.py` | Must not change; WP-3 exposes no route |
| Migrations | `app/forge/persistence/sql/001`–`004` | No new migration in WP-3A/B |

**Ownership law.** Adapters deliver observations. They never compute CEREBUS
geometry, session membership, research days, finality, aggregation or
eligibility. Those remain III.1/III.2 responsibilities.

---

## 6. Adapter architecture

Proposed package (new, additive): `app/forge/market_data_ingest/`

```
contract.py     # MarketDataProvider port, RawCandle, CandleRequest/Page, SourceWindow
symbols.py      # provider symbol tables (data only; resolution stays in III.1)
capture.py      # source-slice capture, provenance labels, stable window digests
backfill.py     # windowed pagination, checkpoint/resume, idempotent re-ingest
stream.py       # live polling/streaming loop, reconnect, late arrivals
health.py       # provider health -> ProviderHealth vocabulary, budgets
providers/twelvedata.py
providers/polygon.py
providers/kraken.py
```

`MarketDataProvider` (proposed port, mirroring II.5 doctrine):

- `provider_id: str`
- `capabilities() -> ProviderCapabilities` (instruments, timeframes, history
  depth, streaming mode, revision support)
- `fetch(request: CandleRequest) -> CandlePage` — one bounded page; never loops
- `stream(request: CandleRequest) -> Iterator[RawCandle]` — caller owns the loop
- `health() -> ProviderHealth` — pure, no network on call
- `close() -> None`

`RawCandle` is provider-neutral: `provider_id`, `source_symbol`, `timeframe`,
`open_time` (aware UTC), `close_time` (aware UTC), OHLC as `Decimal`, `volume`,
`source_timestamp`, `source_revision`, `finality_hint`, `raw_digest`. Raw key
names and symbol spellings never leave the adapter.

**Normalization path.** The adapter emits `RawCandle`; a thin mapper builds the
provider payload dict keyed to a new additive `ProviderFieldMap` entry in
`PROVIDER_SCHEMAS`; `normalize_record` produces `Bar`. This keeps one
normalization implementation and one quality vocabulary.

**Additive III.1 edits required in WP-3B (each separately authorized):**

1. `PROVIDER_SCHEMAS` entries for `twelvedata`, `polygon`, `kraken`.
2. `provider_mappings` for those providers on each instrument.
3. Registration of `USDJPY`, `AUDJPY`, `EURJPY` (precision 3, pip 0.01).
4. Optional: a kernel-owned M5→H1/D1/W1 rollup if a consumer needs higher
   timeframes. Adapters must not aggregate; provider-native H1 is accepted only
   as a *cross-check*, never as the canonical higher-timeframe series.

No signature, enum, refusal code or quality flag changes. If any of these four
edits is rejected, WP-3B stops rather than contorting the contract.

---

## 7. Symbol, session and research-day mapping

- Provider spellings are data: Twelve Data `EUR/USD`, `XAU/USD`, `USD/JPY`,
  `AUD/JPY`, `EUR/JPY`, `BTC/USD`; Polygon `C:EURUSD`, `C:XAUUSD`,
  `C:USDJPY`, `C:AUDJPY`, `C:EURJPY`, `C:BTCUSD`; Kraken `BTC/USD` (legacy
  `XXBTZUSD`).
- Mapping changes are versioned and detected: a provider symbol that resolves
  to two instruments fails closed (`AMBIGUOUS_ALIAS`); an unresolved symbol is
  `UNKNOWN_SYMBOL` before any network call.
- Session identity is **not** assigned by adapters. EUR and BTC binding already
  exists; XAU has no canonical session definition (III.1-GAP-2) and must return
  `NO_CALCULATION` rather than borrow EUR bounds. JPY DT binding requires the
  crosswalk ruling; until then the adapter may deliver bars but ownership stays
  unresolved.
- Research-day ownership stays a lineage-declared rule; no calendar fallback.

---

## 8. Timestamp and finality ownership

- Every timestamp crossing the boundary is timezone-aware UTC. Naive provider
  timestamps are refused (`INCOMPLETE_RECORD`, `GAP`), never guessed.
- `source_timestamp` (when the provider says the event was observed) is stored
  separately from `open_time`/`close_time` (what the bar represents).
- Provider finality hints are recorded as provenance facts only
  (`finality_hint`, `finality_disagreement`). The authoritative decision is
  `assess_finality(close_time, observation_cutoff)`. A provider `complete` flag
  can never finalize a bar whose close lies beyond the platform cutoff.
- OANDA's documented divergence between historical base-price candles and
  account-specific live pricing is treated as a parity hazard, not a detail.

---

## 9. Backfill, live ingest, replay and parity

**Backfill.** Windowed requests with explicit `[start, end)` and per-page
limits; deterministic pagination; checkpoint on the last committed close time;
re-ingest is idempotent because `reconcile` is order-independent and revisions
win only by later `source_timestamp`. A provider page that returns fewer rows
than claimed, or a window that cannot advance, fails closed rather than looping.

**Live ingest.** Poll or stream into the same normalizer; provisional bars carry
`NONFINAL`; terminal reconciliation runs the batch rules. Reconnect requests
the missed window and reconciles, so a gap is either filled from source or
reported as a gap — never synthesized.

**Parity contract (three-way).** For identical source events and an identical
normalization version, historical backfill, live ingest and reconnect replay
must produce:

1. identical canonical bar content (`content_digest`, provider excluded),
2. identical session/research-day ownership,
3. identical quality flags and `DataOutcome`,
4. identical missing-bar set,
5. identical `source_window_digest` at the raw layer.

Documented exceptions: provider-side restatements change raw input and therefore
must surface as `REVISED`; a provider that does not emit a bar during a quiet
window produces `GAP` rather than a flat bar.

**Source-window digest.** SHA-256 over canonically sorted raw observations
(source symbol, interval bounds, OHLC, volume, source timestamp, revision),
excluding provider identity, so two vendors of the same slice can be compared
without conflating provenance.

---

## 10. Quality, provenance and multi-provider behaviour

- Frozen vocabulary only: `COMPLETE`, `GAP`, `DUPLICATE`, `REVISED`, `STALE`,
  `NONFINAL`, `OUTLIER_SOURCE`, `UNSUPPORTED_CLOCK`.
- Mapping: outage → `DATA_QUALITY_BLOCKED`; no final bars → `DATA_QUALITY_BLOCKED`;
  some nonfinal excluded → `DEGRADED`; unknown clock → `UNSUPPORTED_CLOCK` and
  `NO_CALCULATION`; cross-source disagreement beyond one native tick →
  `OUTLIER_SOURCE` with a blocking policy.
- `STALE` is carried, never invented: no canonical staleness threshold exists
  (III.6-GAP-4), so the provider supplies timestamps and the label stays
  unresolved.
- Provenance: `SOURCE_SLICE` bars require a `source_ref`; `SYNTHETIC_FIXTURE`
  bars cannot carry one (constructor-enforced). Captured real slices are
  labelled `SOURCE_SLICE` with licence and capture metadata; synthetic fixtures
  remain `SYNTHETIC_FIXTURE` and can never satisfy an evidence check.
- Multi-provider: a per-instrument `SourcePolicy` orders sources. Failover is
  allowed only on retryable failures (timeout/unavailable/rate-limited). A
  canonical series must not silently interleave providers; a deliberate switch
  creates a declared boundary and is disclosed per bar. Cross-source agreement
  is checked at the raw layer before normalization.

---

## 11. Readiness and operational states

`market_data` moves `NOT_CONFIGURED → READY` only through ten evidence gates
(detailed in `ACCEPTANCE.md` §6): authorized configuration, valid credentials
without leakage, successful bounded source requests, verified clock/session
normalization, final-bar quality, historical/live parity, replay
reproducibility, source health, failure/recovery drill, and a Book II
amendment for the readiness surface.

A successful ping or one fetched candle proves none of these. Until every gate
has an artifact, the seam stays non-healthy and the honest status is
`NOT_CONFIGURED` (no credentials) or `UNAVAILABLE` (credentials present, gates
incomplete). `required` stays `False` until a serving path consumes market data;
flipping it is a Book II decision, not a Book III one.

Failure behaviour: provider errors map through the II.5 taxonomy; the caller
owns retries and backoff; the circuit breaker opens after consecutive retryable
failures; serving continues on the last canonical state with disclosure, or
refuses with `DATA_QUALITY_BLOCKED`. No false positive health.

---

## 12. Security, licensing and cost

- Secrets arrive only through environment injection
  (`FORGE_MARKET_DATA_PROVIDER`, `FORGE_MARKET_DATA_TWELVE_DATA_API_KEY`,
  `FORGE_MARKET_DATA_POLYGON_API_KEY`; Kraken public data needs none). Values are
  `repr=False`, never logged, never in fixtures, never in diagnostics — only
  `*_configured` booleans, matching the II.5 redaction law.
- Rotation without code change; separate credentials per environment; no
  production key in local/test; egress restricted to provider hosts.
- Request budgets, token buckets, bounded backoff with jitter and a hard monthly
  call ceiling; cost alarms on usage, not on price.
- Licensing is a **gate, not a detail**. OANDA forbids third-party display.
  Twelve Data individual plans are personal/non-display and redistribution
  requires a separate agreement. Polygon requires a business product for
  redistribution and its individual terms forbid commercial use. Any
  customer-facing display therefore needs a business/enterprise agreement and,
  where applicable, exchange approvals before beta.
- Indicative monthly cost at planning time: Twelve Data Venture `$149`,
  Ultra `$329`, Enterprise from `$1,099`; Polygon Currencies Starter `$49`
  (individual, non-commercial); Kraken `$0` public data. Business/enterprise
  pricing for Polygon currencies was not published on the pages read
  (`UNVERIFIED`). No purchase is authorized.

---

## 13. Acceptance test design

72 proposed names across T1–T10, enumerated with source-backed conditions in
`ACCEPTANCE.md` §3. Split by evidence class:

- **Contract tests (mock adapter, no network):** T1–T7, T8 credentials/logging,
  T9 state machine, T10 integrity — 66 names.
- **External acceptance (real provider, licensed capture):** 6 names requiring
  credentials or captured slices, all in T2/T3/T5, marked so they cannot run by
  accident and cannot be satisfied by a mock.

A passing mock suite is contract evidence only. It is never evidence that a
provider works, that its data is licensed, or that live parity holds.

---

## 14. Golden fixture strategy

12 cases plus manifest and frozen baseline (14 files), all `SYNTHETIC_FIXTURE`
with deterministic LF-normalized hashes, generated by a single script that
reproduces byte-identically:

normal FX sequence · XAU session transition · BTC 24/7 sequence · FX DST
spring-forward · duplicate bars · out-of-order bars · missing-bar window ·
nonfinal→final update · corrected source candle · disconnect/reconnect ·
historical/live parity pair · source-discrepancy refusal.

Real acceptance uses separately captured, licensed `SOURCE_SLICE` data with
capture metadata; those files are never described as synthetic and never
committed without a licence note.

---

## 15. Work packets and order

| Packet | Content | Depends on | Parallel with |
|---|---|---|---|
| **WP-3A** | Provider selection, contract terms, this plan + acceptance ratification | WP-1 (done) | WP-4, WP-5, Book IV/V planning |
| **WP-3B** | Adapter implementation against synthetic fixtures; additive instrument/schema registrations; readiness untouched | WP-3A approval | WP-4, WP-5, Book IV/V prototyping |
| **WP-3C** | Credentials, licensed real slices, external acceptance | WP-3B; operator licensing | WP-4 |
| **WP-3D** | Live parity window, reconnect/failover drills, readiness transition (Book II amendment) | WP-3C; WP-4 for retained slices; WP-2 for consumption | — |

Critical path: WP-3A → WP-3B → WP-3C → WP-3D. WP-2 (routes) and WP-4
(durability) are not blockers for 3A/3B but are blockers for 3D and for any
customer-visible use. No packet may edit `routes.py`, `container.py`,
`health.py`, Book I/II contracts or III.1–III.6 semantics without its own
governed amendment.

---

## 16. Frozen integrity baselines (must hold at every WP-3 rung)

Book II 50 hashes; III.1–III.6 79 modules with the digests in §2; migrations
`001`–`004`; `routes.py` `145757e0…`; `market_data: NOT_CONFIGURED`; Book I
corpus unchanged; no new refusal codes or quality flags.

---

## 17. Open-gap dispositions

| Gap | WP-3 effect | Owner / closure |
|---|---|---|
| III.1-GAP-1 no real historical slices | Fixtures stay synthetic until 3C captures licensed slices | Operator / WP-3C |
| III.1-GAP-4 no provider wiring | This packet selects; 3B/3C/3D implement and prove | WP-3 |
| III.1-GAP-5 live parity unproven | Parity contract defined (§9); proof only in 3D | WP-3D |
| III.1-GAP-2 session families undefined | XAU/JPY ownership stays `NO_CALCULATION`/`UNRESOLVED` | Book I / research |
| III.1-GAP-3 final-bar rules beyond M5 | Only the canonical M5 rule is claimed | Research |
| III.6-GAP-2 provider not configured | Unchanged until 3D evidence | WP-3D + Book II |
| III.6-GAP-4 no staleness threshold | `STALE` carried, never auto-set | Product / governance |
| III.5-GAP-7 no live/feed parity | Stays `UNVERIFIED` for setups | WP-3D |
| III.4-GAP-10 / III.6-GAP-1 durability | 3C/3D slices need retention → WP-4 | Book II durability |
| III.5-GAP-4 trigger vocabulary | Not addressed by market data | III.2 / operator |
| III.3-GAP-8 BTC weekly/monthly anchors | Data can arrive; classification stays unresolved | Research |

---

## 18. Stop conditions

Stop and report, never improvise, if: no provider offers a licensed path to
customer display; a provider's terms forbid the intended use; parity exceeds one
native tick without a documented cause; a provider changes its schema or symbol
mapping mid-window; a credential would have to enter the repository or logs; a
frozen hash, migration set or seam changes; or an implementation needs a III.1
semantic change rather than an additive registration.

---

## 19. Verification performed for this rung

Foundation re-measured (§2); model requirements traced to card text; provider
claims read from official pages on 2026-11-07 and labelled `VERIFIED` /
`UNVERIFIED` in the decision matrix; test inventory counted and de-duplicated
(72); PLAN/ACCEPTANCE cross-checked for the same counts, packet names and gate
vocabulary; `git status` confirms no code, test, fixture, migration or
environment change. This document asserts no live capability.
