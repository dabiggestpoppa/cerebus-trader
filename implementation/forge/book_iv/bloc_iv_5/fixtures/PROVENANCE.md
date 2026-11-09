# Q5 FIXTURE PROVENANCE

Every Q5 fixture is **synthetic and deterministic**. Nothing here is a market
observation, an empirical result, a provider response or a production
authorization.

## Chain

```
_builders.py  -> real IV.3 types (AuthorizedContextPackage, ContextItem,
                 ContextSection, AuthorizedContextManifest) + real IV.4 types
                 (GatewayDraft, DraftClaim, NumericLink) in UNVALIDATED state
scenarios.py  -> the 46 Q5 scenarios frozen by ACCEPTANCE.md
generate.py   -> runs the real IV.5 entry point and writes Q5-*.json
```

## Provenance map

| Fixture band | Builder | Provenance class |
|---|---|---|
| Q5-01, Q5-46 | `definition_package` | synthetic canonical term/model |
| Q5-02 | `general_package` | authorized general knowledge |
| Q5-03, Q5-04, Q5-45 | `operator_package` (ELIGIBLE / WATCH) | synthetic operator state + encoded setup |
| Q5-05, Q5-06 | `stat_package` (with negative evidence) | synthetic statistic, N=120, forward OOS |
| Q5-07–Q5-12, Q5-18 | `operator_package` / `stat_package` variants | intentional numerical divergence |
| Q5-13 | `stat_package(metric="simulation")` | simulated evidence class |
| Q5-14 | `stat_package(n="")` | statistic with N omitted |
| Q5-15–Q5-19 | `operator_package` / `stat_package` | citation defects |
| Q5-20–Q5-23 | `operator_package` / `stat_package(path_statistic)` | layer defects |
| Q5-24–Q5-29 | `operator_package` verdict variants | setup/action defects |
| Q5-30–Q5-33 | `candidate_package`, `historical_package`, `research_flag_package`, `parked_package` | status defects |
| Q5-34–Q5-36 | `operator_package` quality/clock variants | freshness defects |
| Q5-37–Q5-39 | `operator_package`, `corpus_package`, `untrusted_package` | leakage/injection defects |
| Q5-40–Q5-44 | empty draft and `unavailable_package` / `ambiguous_package` | refusal vocabulary |
| Q5-45 | `operator_package` | record completeness |

## Invariants

- `package.manifest.manifest_digest` and `package.package_id` are computed by
  the real IV.3 `finalized()` path.
- Every draft is `DraftStatus.UNVALIDATED` and bound to its own package,
  manifest and query plan.
- `FIXTURE_MANIFEST.json` records the SHA-256 of each written record; `A-73`
  re-derives the payload digest on every run.
- `generate.py` is the only writer; hand-editing a fixture fails the suite.
- No real market value, price, return or win rate is asserted anywhere.
