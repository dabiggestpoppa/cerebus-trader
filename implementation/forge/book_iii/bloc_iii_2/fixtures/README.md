# Bloc III.2 — Golden Measurement Fixtures

Deterministic committed fixtures for the Measurement & Feature Engine
focused suite (`tests/test_forge_measurements.py`, groups T1–T12).

## Files

| File | Content | Provenance |
|---|---|---|
| `generate_fixtures.py` | The generator that produced every JSON file below (single source; rerunning it reproduces the committed bytes). | tool |
| `eur_daily_tier_seeds.json` | EUR Daily Phase1 T1/T2/T3/no-go seed ranges with independently computed golden range facts and tier expectations. | `SYNTHETIC_FIXTURE` bars + `CANONICAL_SOURCE_SLICE` calibration quote |
| `eur_rekey_ladder.json` | EUR Daily 100/125/132/168/185 coordinate ladder over the T2 earned range. | `SYNTHETIC_FIXTURE` |
| `eur_event_budget.json` | Synthetic scheduled/actual events with historical band/size and the subtractive residual expectation (plus an explicit refusal case). | `SYNTHETIC_FIXTURE` |
| `eur_weekly_outer_nodes.json` | EUR Weekly tier medians and sample sizes quoted from the frozen evidence card (research standing). | `CANONICAL_SOURCE_SLICE` |
| `eur_higher_order.json` | Quarter/M1/M2/D1–D3 seed windows for the higher-order structural handoff. | `SYNTHETIC_FIXTURE` |
| `xau_spatial_bands.json` | XAU spatial band table + probes, coordinate ladder, promotion-example disclosures (small-N, never executable) and quarter-zone eligible vs blind-touch path cases. | `CANONICAL_SOURCE_SLICE` (bands, promotions) + `SYNTHETIC_FIXTURE` (bars) |
| `btc_tier_seeds.json` | BTC Tracker native T1/T2/T3/no-go seeds, AU values, threshold levels, density zones and the slot × tier range-left surface. | `SYNTHETIC_FIXTURE` bars + `CANONICAL_SOURCE_SLICE` calibration quote |
| `jpy_dt_structures.json` | JPY 12–4PM DT structure families (132/168/187.5), research window, asset role map; basket-role cases disclosed as deferred. | `CANONICAL_SOURCE_SLICE` |
| `fib_anchor_cases.json` | Fib R15 anchor cases (born range, unresolved, invalidated, rekey transition), the coordinate ladder and the rejected arbitrary-pivot case. | `SYNTHETIC_FIXTURE` |
| `FIXTURE_MANIFEST.json` | sha256 of every JSON file above, recorded over **LF-normalized** content so the manifest verifies identically on Windows (CRLF worktrees) and Linux CI (LF checkouts) — the BA-17 `8b43cb4` lesson. | manifest |

## Discipline

- Every synthetic file carries `provenance: SYNTHETIC_FIXTURE`, a
  `data_classification` string that begins with `SYNTHETIC_FIXTURE` and
  states "not empirical market evidence and never citable for
  performance claims", and `historical: true` with explicit observation
  cutoffs where a bar window exists.
- A `SYNTHETIC_FIXTURE` III.1 bar structurally cannot carry an evidence
  reference (`app/forge/market_data/bars.py` refuses at construction), so
  a synthetic fixture can never satisfy an evidence-reference check
  (ACCEPTANCE J7 / O4).
- Canonical numerical constants inside these files (tier boundaries, AU
  values, threshold levels, weekly medians, DT structure levels) are
  quoted from the frozen corpus and keep their `source_ref` /
  evidence-id lineage on every record.
- Coordinate-ladder expectations are computed in **price units**
  (`projected = low + span × level / 100`); native-unit counts (pips,
  points, dollars) are never added to a price.
- Reproduction of these fixtures is a **contract test**, never empirical
  strategy-performance validation (III.2-GAP-5).

## Regeneration

```
python implementation/forge/book_iii/bloc_iii_2/fixtures/generate_fixtures.py
```

The run rewrites every fixture and `FIXTURE_MANIFEST.json`
deterministically.  Any diff against the committed bytes is a fixture
change and must be reviewed under the acceptance clause it supports.
