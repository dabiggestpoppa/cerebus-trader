# BLOC III.1 — COMMITTED FIXTURES

Status: CANONICAL (Bloc III.1 implementation evidence, BA-17 Rung 2)
Regenerate: `python generate_fixtures.py` (byte-identical output; hashes in
`FIXTURE_MANIFEST.json` verify every JSON file in this directory).

## Provenance honesty (PLAN §10 G1 / ACCEPTANCE I1, N3, N4, O1)

| File | Provenance label | Meaning |
|---|---|---|
| `eurusd_m5_slice.json` | `SYNTHETIC_FIXTURE` | Deterministic generated M5 bars (fixed arithmetic, no randomness, no wall clock). **Not empirical market evidence**; cannot support strategy performance claims. |
| `btcusd_m5_slice.json` | `SYNTHETIC_FIXTURE` | Same, BTCUSD M5 checkpoint slice. |
| `raw_feed_fake_alpha.json` | `SYNTHETIC_FIXTURE` | Scripted offline provider encoding (epoch timestamps, `pair`/`tf`/`o`… keys) of the EUR slice. |
| `raw_feed_fake_beta.json` | `SYNTHETIC_FIXTURE` | Same slice in a second provider convention (ISO-offset timestamps, `sym`/`int`/`px_o`… keys) and a **rotated arrival order**, so normalization parity cannot come from ordering. |
| `raw_feed_btcusd_fake_alpha.json` | `SYNTHETIC_FIXTURE` | Scripted encoding of the BTC slice. |
| `sessions_canonical.json` | `CANONICAL_SOURCE_SLICE` | Session bounds, checkpoint instants, documented family gaps and research-day lineage rules **quoted from frozen canonical corpus sources** — every record carries its `source_ref`. |

The synthetic label is assigned at creation, inside the generator. A bar
built with `SYNTHETIC_FIXTURE` provenance cannot carry an evidence
reference (constructor-enforced), so synthetic data can never satisfy an
evidence-reference check.

## Canonical sources cited by `sessions_canonical.json`

- `corpus/canonical/evidence/EUR_DAILY_PHASE1_CALIBRATION_EVIDENCE_V1.md`
  (evidence id `EV.EUR.DAILY.PHASE1_TIERS.V1`) — 19:00–03:00 NY session,
  research-day ownership and final-bar convention are part of the claim.
- `corpus/canonical/models/EUR_DAILY_NEWS_REKEY_MODEL_CARD_V1.md` —
  Asian window 19:00–03:00 NY.
- `corpus/canonical/models/BTC_DAILY_WEEKLY_MONTHLY_TRACKER_MODEL_CARD_V1.md`
  — Asian window 19:00–03:00 NY research frame; daily checkpoint 12PM NY;
  weekend/weekly transitions require exact research-day ownership.
- `implementation/forge/book_iii/bloc_iii_1/PLAN.md` Ch III.1.6 — the
  plan-canonical M5 `02:55` final-bar convention.

## Documented gaps carried in `sessions_canonical.json`

Families with **no canonical definition** are disclosed, never invented:
London/MLR (no bounds in corpus), weekly seed (day-granularity only),
DT window (JPY 12–4PM named but DT→Carry binding forbidden without a
crosswalk ruling), month/quarter boundaries (hierarchy canonical, clock
frame unspecified). See PLAN §10 gaps G2/G3 and the fixture's own
`documented_gaps` block.

## Slice design (deterministic)

- EURUSD slice: contiguous M5 session bars from the 23:55Z context bar
  (local 18:55, before the boundary) through the canonical `02:55→03:00`
  final bar (07:55Z–08:00Z), with one **deliberate hole at 00:15Z**
  (visible `GAP`), a duplicate pair at 00:20Z, an explicit revision pair
  at 00:30Z, and one in-progress bar beyond the observation cutoff
  (`NONFINAL`). Observation cutoff `2026-03-03T08:03:00Z`.
- BTCUSD slice: an evening bar (research day +1), a mid-day bar outside
  any registered session, a bar closing exactly at the 12:00 NY
  checkpoint, and an in-progress `NONFINAL` bar. Cutoff
  `2026-03-03T17:00:30Z`.

No network, no credentials, no provider SDK exists anywhere in this
directory; the fake provider feeds are scripted offline encodings only.
