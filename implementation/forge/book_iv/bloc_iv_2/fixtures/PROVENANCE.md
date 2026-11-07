# BOOK IV / BLOC IV.2 — FIXTURE PROVENANCE

**Base HEAD:** `38b322b562317fdd42ad8ea61a9866b2931966a7`

These eighteen retrieval fixtures are deterministic outputs of
`generate.py` over the synthetic Book I index in `_builders.py`.

They are **contract fixtures**, not market claims. They contain no fabricated
historical statistic, no production-approved setup and no live market state.
The synthetic claims exist only to exercise a claim/evidence join, a missing
evidence path, a conflict and a negative-evidence path.

## Reproduction

```
python implementation/forge/book_iv/bloc_iv_2/fixtures/generate.py
```

Regenerating must produce byte-identical `expected/Q2-*.json` and an identical
`FIXTURE_MANIFEST.json`.

## Scenario map

| ID | Contract exercised |
|---|---|
| Q2-01 | Exact canonical definition |
| Q2-02 | Model-description resolution |
| Q2-03 | Numerical claim with evidence |
| Q2-04 | Numerical claim lacking evidence |
| Q2-05 | BTC Game / BTC Tracker collision |
| Q2-06 | Historical P90 generation |
| Q2-07 | Current Gold with provider unavailable |
| Q2-08 | Setup with active no-go |
| Q2-09 | XAU setup without production approval |
| Q2-10 | Fib research-only eligibility |
| Q2-11 | JPY manual confirmation |
| Q2-12 | Contradictory evidence, same identity |
| Q2-13 | Incomparable evidence, different identity |
| Q2-14 | Negative/null research evidence |
| Q2-15 | Unauthorized direct ID |
| Q2-16 | Unauthorized semantic neighbour |
| Q2-17 | Historical snapshot unavailable |
| Q2-18 | Semantic text conflicting with canonical fact |

`FIXTURE_MANIFEST.json` records the LF SHA-256 and byte length of every
expected file. No secrets, protected bodies or provider credentials are
present.
