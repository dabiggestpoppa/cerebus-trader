# BOOK III — WP-3 PROVIDER DECISION MATRIX

**Packet:** BA-24 Rung 1 (WP-3A) · **Decision date:** 2026-11-07
**Status:** RECOMMENDATION — requires operator approval before WP-3B/3C.

All statements below were read from official provider pages on the decision
date. Labels: **VERIFIED** = stated on an official page read during this pass;
**UNVERIFIED** = plausible but not confirmed from an official source;
**UNKNOWN** = no evidence gathered. Prices change; nothing was purchased,
registered or authenticated.

---

## 1. Decision

| Role | Provider | Why |
|---|---|---|
| **Primary** | **Twelve Data** (business tier: Venture minimum; Enterprise if distribution/SLA required) | Single contract for all six required instruments, M5/H1 candles, WebSocket, 60+ liquidity providers, explicit commercial-display tier |
| **Independent verification / fallback** | **Polygon Currencies (business)** for FX + XAU + crypto; **Kraken** for BTC/USD | Second independent source with `C:XAUUSD`, 10+ years, WS; Kraken gives a true USD crypto pair and full historical CSV |
| **Internal research/parity only** | **OANDA v20** | Deep FX/metals history and explicit `complete` flag, but licence forbids third-party display |
| **Rejected for now** | Binance, Coinbase, Dukascopy | USDT basis risk / no official terms verified in this pass |

Fallback is per-instrument, not per-vendor wholesale: if the primary fails a
specific instrument's licensing or parity gate, that instrument routes to the
secondary source rather than silently degrading the whole feed.

---

## 2. Coverage matrix

| Requirement | Twelve Data | Polygon | OANDA v20 | Kraken |
|---|---|---|---|---|
| EURUSD | **VERIFIED** (FX v2, 1,500+ pairs) | **VERIFIED** (`C:EURUSD`) | **VERIFIED** (all tradable pairs) | not offered |
| XAUUSD | **VERIFIED** (precious metals XAU/XAG in FX v2) | **VERIFIED** (`C:XAUUSD` via forex endpoints; “Gold” listed) | **VERIFIED** (XAU/USD is a tradable pair) | not offered |
| USDJPY / AUDJPY / EURJPY | **VERIFIED** (majors/minors) | **VERIFIED** (forex tickers) | **VERIFIED** | not offered |
| BTCUSD | **VERIFIED** (crypto, BTC/USD) | **VERIFIED** (crypto pairs) | not offered | **VERIFIED** (`BTC/USD`, legacy `XXBTZUSD`) |
| M5 candles | **VERIFIED** (1m–1month) | **VERIFIED** (minute aggregates) | **VERIFIED** (`M5` in interval list) | **VERIFIED** (interval 5) |
| H1 candles | **VERIFIED** | **VERIFIED** | **VERIFIED** (`H1`) | **VERIFIED** (interval 60) |
| D1 / W1 | **VERIFIED** (to 1month) | **VERIFIED** | **VERIFIED** (`D`, `W`) | **VERIFIED** (1440 / 10080) |
| Historical depth | **VERIFIED** depth varies by plan (“deep historical” on higher tiers; exact per-instrument depth **UNVERIFIED**) | **VERIFIED** 2 years Basic, **10+ years** Currencies Starter | **VERIFIED** back to 2005 | **VERIFIED** full OHLCVT archive through 2026-09-30; REST only last **720** candles |
| Streaming | **VERIFIED** WebSocket (Pro+; Venture 500 WS credits) | **VERIFIED** WebSocket aggregates + quotes | **VERIFIED** streaming pricing sockets | **VERIFIED** WS v2 `ohlc` channel |
| Candle finality signal | **UNVERIFIED** (no documented `complete` flag found) | **UNVERIFIED** (aggregates carry window timestamps; no completion flag documented) | **VERIFIED** `complete` boolean (ending time not in future) | **VERIFIED** last REST entry is current, not-yet-committed |
| Revisions / restatements | **UNVERIFIED** | **UNVERIFIED** | **VERIFIED** historical vs live pricing differ by pricing group | **UNVERIFIED** (archive is a periodic snapshot) |
| Timestamp basis | **UNVERIFIED** (UTC assumed, not confirmed) | **VERIFIED** aggregates in UTC | **VERIFIED** RFC3339 with timezone | **VERIFIED** epoch seconds (UTC) |
| Rate limits | **VERIFIED** credit-based per minute + WS credits | **VERIFIED** 5 calls/min Basic; unlimited on Starter+ | **VERIFIED** 5,000 candles/page; per-account limits | **VERIFIED** public ~1 req/sec |
| Commercial display | **VERIFIED** business plans allow commercial display subject to exchange licensing | **VERIFIED** business products required for redistribution | **FORBIDDEN** by API licence (internal use only; no display to clients) | **UNVERIFIED** terms not read in this pass |
| Redistribution | **VERIFIED** separate written agreement required | **VERIFIED** business plan + agreement | **FORBIDDEN** without written permission | **UNVERIFIED** |
| Cost (planning) | **VERIFIED** Grow $29/$49/$79; Pro $99; Venture $149; Ultra $329; Enterprise from $1,099 | **VERIFIED** Currencies Basic $0, Starter $49; currencies business price **UNVERIFIED** | **VERIFIED** requires a v20 account; no separate API fee found | **VERIFIED** public data free |

---

## 3. Criteria-by-criteria assessment

1. **FX spot coverage.** Twelve Data and Polygon both cover the six pairs and
   the metals; OANDA covers FX/metals only. Kraken is crypto-only.
2. **XAUUSD and price conventions.** Polygon documents `C:XAUUSD` as gold
   through forex endpoints; Twelve Data documents XAU as a precious metal; OANDA
   quotes XAU/USD as a pair. Convention risk is real: spot gold has no single
   consolidated tape, so the platform must record the provider's price basis and
   never blend vendors inside one canonical series.
3. **Crypto coverage.** Twelve Data and Polygon provide BTC/USD. Kraken provides
   the cleanest true-USD pair with a free full-history archive; Binance's
   BTCUSDT is USDT-denominated and would introduce a stablecoin basis the
   canonical BTCUSD contract does not declare.
4. **Historical intraday depth.** OANDA (2005), Polygon (10+ years on Starter),
   Kraken (full CSV archive), Twelve Data (plan-dependent; exact depth
   `UNVERIFIED`). Minimum model lookbacks are ≈4–5 years, so all four can
   satisfy research needs in principle.
5. **M5 and H1 availability.** All four support both. Kraken's REST cap of 720
   candles per call makes multi-year M5 backfill a CSV/pagination exercise.
6. **Realtime streaming or polling.** All four stream. Twelve Data's WS is
   credit-metered; Polygon's FX aggregates are quote-derived, not trade-derived.
7. **Candle finalization.** OANDA is the only vendor with a documented
   `complete` flag. Kraken documents that the trailing candle is provisional.
   For Twelve Data and Polygon the platform must rely on its own cutoff, which
   the III.1 kernel already owns — acceptable, but it means finality cannot be
   delegated to the vendor.
8. **Corrections and restatements.** OANDA explicitly documents historical vs
   live divergence; the others do not document revision semantics. The platform
   must treat any later `source_timestamp` as a revision and never overwrite
   silently (already enforced by `reconcile`).
9. **Timestamp quality.** Polygon (UTC), OANDA (RFC3339), Kraken (epoch
   seconds) are documented. Twelve Data's exact timestamp basis is `UNVERIFIED`;
   the adapter must require an explicit UTC offset and refuse naive values.
10. **API reliability.** All publish status/limit documentation; none offers a
    contractual SLA at the individual tier. Twelve Data Enterprise advertises
    99.99% SLA.
11. **Rate limits.** Polygon Currencies Starter removes call limits; Twelve Data
    uses per-minute credits; Kraken throttles public calls near 1/sec; OANDA
    paginates 5,000 candles. Backfill must be budgeted, not brute-forced.
12. **Historical backfill.** Polygon and Kraken offer file downloads; OANDA
    paginates; Twelve Data offers API pagination. File-based backfill is
    preferred for determinism and cost.
13. **Licensing / redistribution.** Decisive axis: OANDA forbids third-party
    display; Twelve Data and Polygon require business tiers and a separate
    redistribution agreement; Kraken's display terms were not verified.
14. **Account / credentials.** OANDA needs a v20 account + token; Twelve Data and
    Polygon need API keys; Kraken public data needs none but authenticated tiers
    need keys.
15. **Integration complexity.** One aggregator (Twelve Data) minimizes moving
    parts; a two-vendor FX/crypto split adds independent verification but doubles
    the symbol, revision and licensing surface.
16. **Cost.** Planning envelope: `$149–$329/month` for the primary alone;
    adding a Polygon business plan is `UNVERIFIED` but material. Cost is not the
    binding constraint — licensing is.
17. **Suitability for customer-facing financial software.** Only business tiers
    are suitable, and only with written confirmation that the intended display
    (derived CEREBUS states, not raw redistribution) is covered.

---

## 4. Recommendation and tradeoffs

**Primary: Twelve Data business tier.** Best single-contract coverage of the
exact instrument set, documented commercial-display path, M5/H1, streaming and a
60+ liquidity-provider aggregation model that suits a canonical series better
than one broker's book.

Tradeoffs and mitigations:

- *Aggregator concentration.* Mitigate with Polygon/Kraken verification and a
  per-instrument fallback policy rather than a second always-on feed.
- *Young FX v2 product (released October 2025).* Mitigate with a parity window
  and revision monitoring before readiness.
- *Foreign-exchange and metals licensing can require approvals.* Treat written
  confirmation as a WP-3C gate; do not assume the plan alone suffices.
- *Finality not documented.* Keep finality kernel-owned; never trust a vendor
  flag.

**Fallback: Polygon Currencies business** for FX/XAU/crypto, and **Kraken** for
BTC/USD verification. Polygon's FX aggregates derive from quotes rather than
trades and omit bars in quiet windows — the platform must map silence to `GAP`,
not to a flat bar.

**Excluded from customer display: OANDA.** Its API licence grants internal use
and prohibits transmitting, publishing or providing the licensed material to any
third party, including clients. It remains acceptable for internal research and
parity checks under that licence, and would require written permission to serve.

---

## 5. Operator decisions required

1. **Approve the primary vendor and tier** (Twelve Data Venture or Enterprise).
2. **Approve the secondary/fallback vendors** (Polygon business, Kraken public).
3. **Confirm the licensing posture**: derived intelligence display to paying
   users is permitted under the chosen agreement; raw redistribution is not
   intended.
4. **Authorize credential provisioning** in the deployment environment only
   (never in the repository or chat).
5. **Confirm cost ceiling** and whether Polygon business pricing should be
   pursued in parallel.

Until 1–4 are answered, WP-3B may proceed only against synthetic fixtures with
no credentials and no network.

---

## 6. Sources (read 2026-11-07)

- OANDA v20 introduction: https://developer.oanda.com/rest-live-v20/introduction
- OANDA API comparison (intervals, 5,000/page, 2005 history):
  https://developer.oanda.com/rest-live-v20/api-comparison/
- OANDA candle `complete` flag:
  https://developer.oanda.com/rest-live-v20/instrument-df
- OANDA historical vs live divergence:
  https://help.oanda.com/us/en/faqs/rest-v20-api-troubleshooting-guide.htm
- OANDA API License Agreement (internal use; no third-party display):
  https://legal.oanda.com/oc/api_license_agreement_oc/en
- Twelve Data pricing: https://twelvedata.com/pricing and
  https://twelvedata.com/pricing-business
- Twelve Data commercial/personal usage and redistribution:
  https://support.twelvedata.com/en/articles/5332349-commercial-and-personal-usage
- Twelve Data Forex API v2 (60+ providers, metals, 1m–1month):
  https://support.twelvedata.com/en/articles/12520817-forex-api-v2
- Polygon currencies pricing: https://polygon.io/pricing?product=currencies
- Polygon commodities/XAUUSD: https://polygon.io/knowledge-base/article/does-polygon-support-commoditie-data
- Polygon redistribution: https://polygon.io/knowledge-base/article/how-can-i-redistribute-polygons-market-data
- Polygon business terms: https://polygon.io/businesses-terms-of-service
- Kraken OHLC: https://docs.kraken.com/api/docs/rest-api/get-ohlc-data
- Kraken historical data guide: https://docs.kraken.com/exchange/guides/general/historical-data
- Kraken downloadable OHLCVT: https://support.kraken.com/articles/360047124832-downloadable-historical-ohlcvt-open-high-low-close-volume-trades-data
- Kraken rate limits: https://support.kraken.com/articles/206548367-what-are-the-api-rate-limits-
- Binance klines and market-data-only endpoints:
  https://developers.binance.com/docs/binance-spot-api-docs/rest-api/market-data-endpoints
  and https://developers.binance.com/docs/binance-spot-api-docs/faqs/market_data_only
