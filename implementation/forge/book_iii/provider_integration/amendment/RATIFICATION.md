# III.1 PROVIDER COMPATIBILITY AMENDMENT — RATIFICATION

**Decision:** **PASS** (amendment only)
**Rung:** BA-25 Rung 2 · **Implementation:** `937de27`
**Base:** `f47741f` · **Authority:** operator authorization of G1/G2, C1–C5

---

## 1. Verdict

The III.1 field map now represents Twelve Data, Polygon Currencies and Kraken
records without fabricating source fields, without changing `Bar`, quality,
finality, sessions, clocks or research-day ownership, and without promoting any
instrument into the production default registry.

Verdict scope is the **amendment contract**. It is not a live-feed verdict and
does not grant WP-3C.

---

## 2. Checklist

- [x] 49/49 amendment tests green; no skip/xfail.
- [x] 24/24 requirements covered (R1–R24).
- [x] 65/65 III.1 tests green, unmodified.
- [x] 66/66 WP-3B tests green, unmodified.
- [x] 96/96 Book III integration green.
- [x] Full repository green (2078 passed, 29 skipped).
- [x] Only `normalize.py` and `market_data/__init__.py` changed among sources.
- [x] Fake schemas byte-identical in behavior and key order.
- [x] No new `RefusalReason`, `QualityFlag` or `Bar` field.
- [x] `MARKET_DATA_SCHEMA_VERSION` unchanged; `PROVIDER_SCHEMAS_V2` exposed.
- [x] Old and new hashes recorded (`FREEZE_DELTA_V2.md`).
- [x] Twelve WP-3B fixtures reproduce byte-identically.
- [x] Seam remains `market_data: NOT_CONFIGURED`.
- [x] No credential, network or vendor account used.
- [x] CI `test` and `postgres` green — run `42383847897` at head `ea5bf0a`.

---

## 3. What was ratified

1. `CloseTimeRule.SOURCE` / `OPEN_PLUS_TIMEFRAME`; derived close is UTC
   arithmetic over the declared timeframe and never overwrites
   `source_timestamp`.
2. Optional `close_time` and optional `clock` on `ProviderFieldMap`; required
   keys are conditional, preserving existing fake-schema order.
3. `TimestampStyle.EPOCH_MILLISECONDS` with integer-only parsing and refusal of
   values below `10^12` (a seconds value in disguise), never rescaled.
4. Immutable schema table with `twelvedata`, `polygon`, `kraken` entries, all
   `clock=None` and derived close.
5. Additive exports only.

---

## 4. What is not ratified

- R21 production default-registry promotion — operator decision outstanding.
- R22 JPY canonical precision/pip/tick authority — provisional.
- R23 higher-timeframe rollup — no rule; rollup remains refused.
- R24 vendor licensing/redistribution — no terms recorded.
- Any live provider connection, cost, latency or history-depth claim.

These F4 items do not block the field-map amendment; they continue to block
WP-3C and any production promotion.

---

## 5. WP-3B effect

WP-3B may now be reconsidered. The supporting supplemental verdict is
`../RATIFICATION_WP3B_SUPPLEMENT_V2.md`; the original
`../RATIFICATION_WP3B.md` is not edited.

---

## 6. WP-3C gate

**WP-3C — NOT EXECUTED.** The six external tests remain unauthorised.
Execution still requires operator vendor ratification, recorded licence terms,
environment-injected credentials, licensed `SOURCE_SLICE` captures with
`licence_ref`/`source_ref`, and a separate written authorization. No fake vendor
evidence may stand in for them, and the readiness seam must not be switched.

---

## 7. CI

Run `42383847897` at head `ea5bf0aa` completed with both jobs green: `test`
success, `postgres` success. The subsequent CI-receipt commit is documentation
only and was re-verified by its own run; no source or test changed after
`ea5bf0a`.
