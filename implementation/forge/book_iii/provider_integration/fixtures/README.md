# WP-3B — OFFLINE PROVIDER FIXTURES

Status: SYNTHETIC CONTRACT FIXTURES (WP-3B, offline only)
Regenerate: `python generate.py` (byte-identical, LF-normalized)
Verify: `python generate.py --check`

## Provenance

Every case is `SYNTHETIC_FIXTURE`: deterministic arithmetic, no randomness, no
wall clock, no network, no vendor response captured from a live call. Nothing
here is market evidence, and no fixture may be cited as real history.

Real acceptance requires separately captured, licensed `SOURCE_SLICE` data with
a `licence_ref` and `source_ref`; that belongs to WP-3C and is not present.

## Files

| File | Purpose |
|---|---|
| `_builders.py` | deterministic payload builders (stdlib only) |
| `generate.py` | writes cases + manifest + baseline; `--check` verifies |
| `fix_01…fix_12*.json` | twelve cases |
| `FIXTURE_MANIFEST.json` | SHA-256 per file, LF-normalized |
| `FROZEN_BASELINE.json` | adapter version + per-case digest and expectation |

## Cases

1. `FIX-01` normal EURUSD M5 sequence.
2. `FIX-02` XAUUSD across the 19:00 NY transition — no canonical session is
   invented, so ownership stays `NO_SESSION`.
3. `FIX-03` BTCUSD Saturday sequence — 24/7, no weekend gap.
4. `FIX-04` EURUSD spring-forward — the final-bar instant exists even though the
   local 02:55 wall label does not.
5. `FIX-05` duplicate rows — one survivor, `DUPLICATE`.
6. `FIX-06` out-of-order arrivals — identical canonical result.
7. `FIX-07` missing-bar window — visible `GAP`, `DEGRADED`, never filled.
8. `FIX-08` nonfinal-to-final — the in-progress bar is excluded.
9. `FIX-09` corrected candle — later `source_timestamp` wins, `REVISED`.
10. `FIX-10` disconnect/reconnect — state preserved, buffered replay.
11. `FIX-11` synthetic historical/live parity pair.
12. `FIX-12` cross-provider discrepancy beyond one native tick.

## Honesty rules

- A synthetic candle cannot carry an evidence reference (constructor-enforced).
- A licensed capture cannot be synthesized; the capture path refuses synthetic
  input.
- Provider payload shapes follow the documented field names used by the offline
  adapters; they are not a promise that a live vendor returns exactly this.
