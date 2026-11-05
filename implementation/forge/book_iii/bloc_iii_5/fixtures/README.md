# BOOK III / BLOC III.5 — GOLDEN FIXTURES

**Bloc:** III.5 (Operator Setup Engine) · **Authority:** BA-21 Rung 2
**Generator:** `generate.py` (deterministic, `--check` reproduces bytes)

## What these files are

Twelve JSON fixtures, one LF-normalised SHA-256 manifest, one frozen
upstream baseline, and this provenance note.

| File | Covers |
|---|---|
| `setup_registry_cases.json` | registry resolution, refusals, three-card surface |
| `setup_contract_cases.json` | frozen record shape, canonical payload, replay |
| `eligibility_cases.json` | the eleven gates and the total precedence |
| `trigger_cases.json` | seven trigger types and declared combinations |
| `invalidation_cases.json` | price/structural/temporal firing |
| `target_promotion_cases.json` | canonical order, first delivery, promotion |
| `xau_quarter_zone_cases.json` | XAU operator, blind touch, parking, caps |
| `fib_rekey_cases.json` | research-only surface, R15 anchor gate |
| `jpy_role_gate_cases.json` | role gate, native tier, no aggregation |
| `st_p90_cases.json` | manual ST framework, unverified P90 lineage |
| `statistics_cases.json` | claim-bound statistics, relationship labelling |
| `setup_authority_matrix.json` | execution class × surface resolution |

## Provenance

* `SYNTHETIC_FIXTURE` — every card instance, model output, anchor, bar
  reference, observation and clock value. None of it is market data.
* `CANONICAL_SOURCE_SLICE` — the three setup ids, execution classes,
  lifecycle statuses, exposures, the seven trigger names, and the
  evidence/claim ids with their frozen statuses. These are copied
  verbatim from `corpus/canonical/`.

Fixtures are built by `_builders.py`, which the acceptance suite imports
as well, so a fixture cannot drift from the reproduction path. Each case
is evaluated at generation time and compared against the expectation
declared in `generate.py`; a disagreement fails generation.

## Honest limits

* No fixture carries a win rate, expectancy, probability, risk/reward or
  position size, and **no fixture may be cited as empirical trading
  validation.**
* A Fib evaluation never reaches `ELIGIBLE` here: the canonical R15 Range
  Birth rule is not materialised (III.2-GAP-1), and this Bloc does not
  fabricate an earned range to manufacture a positive verdict.
* XAU reaches `WATCH` at most with the mapping/ladder declared, and
  `ELIGIBLE` only when both are supplied as canonical parameter bindings
  — which the corpus does not yet provide (III.5-GAP-1 / III.5-GAP-3).

## Reproduction

```bash
python implementation/forge/book_iii/bloc_iii_5/fixtures/generate.py
python implementation/forge/book_iii/bloc_iii_5/fixtures/generate.py --check
```

`--check` exits non-zero if any fixture, the manifest or the frozen
baseline differs from what the builders produce.
